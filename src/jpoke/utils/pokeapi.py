"""PokeAPI URL 生成ユーティリティ。"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Literal, overload
from urllib.request import Request, urlopen

from jpoke.exceptions import PokeApiResolveError
from jpoke.types import PokemonName, ItemName, Type

PokeApiCategory = Literal["pokemon", "item"]
PokemonImageType = Literal[
    "front-default",
    "front-female",
    "front-shiny",
    "front-shiny-female",
    "back-default",
    "back-female",
    "back-shiny",
    "back-shiny-female",
    "official-artwork",
    "official-artwork-shiny",
    "dream-world",
    "dream-world-female",
    "home",
    "home-female",
    "home-shiny",
    "home-shiny-female",
    "showdown-front-default",
    "showdown-front-shiny",
    "showdown-back-default",
    "showdown-back-shiny",
]

POKEAPI_BASE = "https://pokeapi.co/api/v2"
SPRITES_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites"

# タイプ画像は世代・作品ごとにディレクトリが分かれており、Gen9（スカーレット・バイオレット）配下に
# 通常タイプバッジ（*.png）とテラスタルタイプアイコン（Tera/*.png）が両方存在する。
TYPE_SPRITES_DIR = "types/generation-ix/scarlet-violet"

# 和名タイプ -> PokeAPI type ID。19種類のみのため、専用のマップファイルは持たずコード内に直接持たせる。
# "" (タイプなし) は対応する画像が存在しないため含めない。
TYPE_NAME_TO_ID: dict[str, int] = {
    "ノーマル": 1,
    "かくとう": 2,
    "ひこう": 3,
    "どく": 4,
    "じめん": 5,
    "いわ": 6,
    "むし": 7,
    "ゴースト": 8,
    "はがね": 9,
    "ほのお": 10,
    "みず": 11,
    "くさ": 12,
    "でんき": 13,
    "エスパー": 14,
    "こおり": 15,
    "ドラゴン": 16,
    "あく": 17,
    "フェアリー": 18,
    "ステラ": 19,
}


@overload
def get_pokeapi_url(name_ja: PokemonName, category: Literal["pokemon"] = "pokemon") -> str:
    ...


@overload
def get_pokeapi_url(name_ja: ItemName, category: Literal["item"] = "item") -> str:
    ...


def get_pokeapi_url(name_ja: PokemonName | ItemName, category: PokeApiCategory = "pokemon") -> str:
    """和名からPokeAPIエンドポイントURLを返す。"""
    entity_id = _resolve_pokeapi_id(name_ja=name_ja, category=category)
    return f"{POKEAPI_BASE}/{category}/{entity_id}/"


def get_pokemon_image_url(
    name_ja: PokemonName,
    image_type: PokemonImageType = "official-artwork",
) -> str:
    """和名からポケモン画像URLを返す。"""
    entity_id = _resolve_pokeapi_id(name_ja=name_ja, category="pokemon")

    path_by_kind: dict[PokemonImageType, str] = {
        "front-default": f"pokemon/{entity_id}.png",
        "front-female": f"pokemon/female/{entity_id}.png",
        "front-shiny": f"pokemon/shiny/{entity_id}.png",
        "front-shiny-female": f"pokemon/shiny/female/{entity_id}.png",
        "back-default": f"pokemon/back/{entity_id}.png",
        "back-female": f"pokemon/back/female/{entity_id}.png",
        "back-shiny": f"pokemon/back/shiny/{entity_id}.png",
        "back-shiny-female": f"pokemon/back/shiny/female/{entity_id}.png",
        "official-artwork": f"pokemon/other/official-artwork/{entity_id}.png",
        "official-artwork-shiny": f"pokemon/other/official-artwork/shiny/{entity_id}.png",
        "dream-world": f"pokemon/other/dream-world/{entity_id}.svg",
        "dream-world-female": f"pokemon/other/dream-world/female/{entity_id}.svg",
        "home": f"pokemon/other/home/{entity_id}.png",
        "home-female": f"pokemon/other/home/female/{entity_id}.png",
        "home-shiny": f"pokemon/other/home/shiny/{entity_id}.png",
        "home-shiny-female": f"pokemon/other/home/shiny/female/{entity_id}.png",
        "showdown-front-default": f"pokemon/other/showdown/{entity_id}.gif",
        "showdown-front-shiny": f"pokemon/other/showdown/shiny/{entity_id}.gif",
        "showdown-back-default": f"pokemon/other/showdown/back/{entity_id}.gif",
        "showdown-back-shiny": f"pokemon/other/showdown/back/shiny/{entity_id}.gif",
    }

    return f"{SPRITES_BASE}/{path_by_kind[image_type]}"


def get_item_image_url(name_ja: ItemName) -> str:
    """和名からアイテム画像URLを返す。"""
    entity_id = _resolve_pokeapi_id(name_ja=name_ja, category="item")
    item_name = _resolve_item_pokeapi_name(entity_id)
    subdir = _load_item_sprite_subdir_map().get(item_name)
    path = f"{subdir}/{item_name}.png" if subdir else f"{item_name}.png"
    return f"{SPRITES_BASE}/items/{path}"


def get_type_image_url(type_name: Type) -> str:
    """和名タイプ名から通常タイプバッジ画像URLを返す。"""
    entity_id = _resolve_type_id(type_name)
    return f"{SPRITES_BASE}/{TYPE_SPRITES_DIR}/{entity_id}.png"


def get_tera_type_image_url(type_name: Type) -> str:
    """和名タイプ名からテラスタルタイプアイコン画像URLを返す。"""
    entity_id = _resolve_type_id(type_name)
    return f"{SPRITES_BASE}/{TYPE_SPRITES_DIR}/Tera/{entity_id}.png"


def download_pokemon_image(
    name_ja: PokemonName,
    dest: str | Path,
    image_type: PokemonImageType = "official-artwork",
) -> Path:
    """和名からポケモン画像をダウンロードし、指定パスに保存して返す。"""
    url = get_pokemon_image_url(name_ja, image_type=image_type)
    return _download_binary(url, Path(dest))


def download_item_image(name_ja: ItemName, dest: str | Path) -> Path:
    """和名からアイテム画像をダウンロードし、指定パスに保存して返す。"""
    url = get_item_image_url(name_ja)
    return _download_binary(url, Path(dest))


def _download_binary(url: str, dest: Path) -> Path:
    request = Request(url, headers={"User-Agent": "jpoke-pokeapi-image-downloader"})
    with urlopen(request, timeout=20) as response:  # noqa: S310
        data = response.read()

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


@lru_cache(maxsize=1)
def _load_ja_to_id_map() -> dict:
    with resources.files("jpoke").joinpath("data", "pokeapi", "ja_to_id_map.json").open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_id_map() -> dict:
    with resources.files("jpoke").joinpath("data", "pokeapi", "id_map.json").open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_item_sprite_subdir_map() -> dict[str, str]:
    path = resources.files("jpoke").joinpath("data", "pokeapi", "item_sprite_subdir_map.json")
    with path.open(encoding="utf-8") as f:
        return json.load(f)["slug_to_subdir"]


def _resolve_pokeapi_id(name_ja: PokemonName | ItemName, category: PokeApiCategory) -> int:
    data = _load_ja_to_id_map()

    if category == "pokemon":
        section = data["sections"]["pokemon"]
    else:
        # jpoke実装対象を優先し、無ければ全量マップにフォールバックする。
        section = data["sections"].get("item_jpoke", data["sections"]["item"])

    by_ja_name = section["by_ja_name"]
    entity_id = by_ja_name.get(name_ja)

    if entity_id is None and category == "item":
        fallback = data["sections"]["item"]["by_ja_name"]
        entity_id = fallback.get(name_ja)

    if entity_id is None:
        raise PokeApiResolveError(
            f"PokeAPI {category} のIDを解決できません: {name_ja}"
        )

    return int(entity_id)


def _resolve_item_pokeapi_name(item_id: int) -> str:
    by_id = _load_id_map()["sections"]["item"]["by_id"]
    item_name = by_id.get(str(item_id))
    if item_name is None:
        raise PokeApiResolveError(f"PokeAPI item 名を解決できません: id={item_id}")
    return item_name


def _resolve_type_id(type_name: Type) -> int:
    entity_id = TYPE_NAME_TO_ID.get(type_name)
    if entity_id is None:
        raise PokeApiResolveError(f"PokeAPI type のIDを解決できません: {type_name}")
    return entity_id
