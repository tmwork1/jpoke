"""PokeAPI URL生成ユーティリティのテスト。"""

import pytest

from jpoke import (
    get_pokeapi_url,
    get_pokemon_image_url,
    get_item_image_url,
    get_type_image_url,
    get_tera_type_image_url,
)
from jpoke.exceptions import PokeApiResolveError


def test_get_item_image_url_アイテム画像URLを返す():
    assert get_item_image_url("たべのこし") == (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/leftovers.png"
    )


def test_get_pokeapi_url_ポケモン和名からエンドポイントURLを返す():
    assert get_pokeapi_url("ピカチュウ") == "https://pokeapi.co/api/v2/pokemon/25/"


def test_get_pokeapi_url_未解決名は例外を送出する():
    with pytest.raises(PokeApiResolveError):
        get_pokeapi_url("存在しない名前")


def test_get_pokemon_image_url_ポケモン公式アートワークURLを返す():
    assert get_pokemon_image_url("ピカチュウ") == (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png"
    )


def test_get_pokemon_image_url_指定種別のURLを返す():
    assert get_pokemon_image_url("ピカチュウ", image_type="showdown-back-shiny") == (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/shiny/25.gif"
    )


def test_get_tera_type_image_url_ステラタイプの画像URLを返す():
    assert get_tera_type_image_url("ステラ") == (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/"
        "types/generation-ix/scarlet-violet/Tera/19.png"
    )


def test_get_tera_type_image_url_テラスタルタイプアイコン画像URLを返す():
    assert get_tera_type_image_url("ほのお") == (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/"
        "types/generation-ix/scarlet-violet/Tera/10.png"
    )


def test_get_type_image_url_ステラタイプの画像URLを返す():
    assert get_type_image_url("ステラ") == (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/"
        "types/generation-ix/scarlet-violet/19.png"
    )


def test_get_type_image_url_タイプなしは例外を送出する():
    with pytest.raises(PokeApiResolveError):
        get_type_image_url("")


def test_get_type_image_url_タイプバッジ画像URLを返す():
    assert get_type_image_url("ほのお") == (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/"
        "types/generation-ix/scarlet-violet/10.png"
    )
