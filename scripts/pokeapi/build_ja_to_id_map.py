"""和名 -> PokeAPI ID 変換テーブルを生成するスクリプト。

出力先:
    src/jpoke/data/pokeapi/ja_to_id_map.json

入力:
    - src/jpoke/data/pokeapi/id_map.json
    - src/jpoke/data/ps-champ-ja/pokedex.json
    - src/jpoke/data/langmap/item_langmap.csv
"""

from __future__ import annotations

import csv
import json
import ast
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ID_MAP_PATH = ROOT / "src" / "jpoke" / "data" / "pokeapi" / "id_map.json"
POKEDEX_PATH = ROOT / "src" / "jpoke" / "data" / "ps-champ-ja" / "pokedex.json"
ITEM_LANGMAP_PATH = ROOT / "src" / "jpoke" / "data" / "langmap" / "item_langmap.csv"
ITEM_PY_PATH = ROOT / "src" / "jpoke" / "data" / "item.py"

OUTPUT_PATH = ROOT / "src" / "jpoke" / "data" / "pokeapi" / "ja_to_id_map.json"

NON_ALNUM = re.compile(r"[^a-z0-9]+")

# item_langmap.csv だけでは slug 化できない例外。
ITEM_SLUG_OVERRIDES: dict[str, str] = {
    "ながねぎ": "leek",
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def normalize_item_english_name(english_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", english_name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    # 所有格アポストロフィ（King's Rock -> kings-rock）はダッシュを挟まず除去する。
    ascii_text = ascii_text.replace("'", "")
    ascii_text = ascii_text.lower().replace("&", " and ").replace("+", " plus ")
    slug = NON_ALNUM.sub("-", ascii_text).strip("-")
    return slug


def normalize_showdown_name(showdown_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", showdown_name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().replace("&", " and ").replace("+", " plus ")
    slug = NON_ALNUM.sub("-", ascii_text).strip("-")
    return slug


def build_pokemon_map(pokedex: dict, pokemon_name_to_id: dict[str, int]) -> tuple[dict[str, int], list[dict]]:
    ja_to_id: dict[str, int] = {}
    unresolved: list[dict] = []

    for ja_name, entry in pokedex.items():
        showdown_id = entry.get("showdown_id")
        showdown_name = entry.get("showdown_name")
        if not showdown_id:
            unresolved.append({"ja_name": ja_name, "reason": "showdown_id_missing"})
            continue

        candidates = [showdown_id]
        if showdown_name:
            candidates.append(normalize_showdown_name(showdown_name))

        pokeapi_id = None
        resolved_key = None
        for c in candidates:
            pokeapi_id = pokemon_name_to_id.get(c)
            if pokeapi_id is not None:
                resolved_key = c
                break

        if pokeapi_id is None:
            unresolved.append(
                {
                    "ja_name": ja_name,
                    "reason": "pokeapi_name_not_found",
                    "showdown_id": showdown_id,
                    "showdown_name": showdown_name,
                    "candidates": candidates,
                }
            )
            continue

        ja_to_id[ja_name] = pokeapi_id

    return dict(sorted(ja_to_id.items())), unresolved


def build_item_map(item_name_to_id: dict[str, int]) -> tuple[dict[str, int], list[dict]]:
    ja_to_en = load_item_langmap_ja_to_en()

    ja_to_id: dict[str, int] = {}
    unresolved: list[dict] = []

    for ja_name, en_name in ja_to_en.items():
        slug = ITEM_SLUG_OVERRIDES.get(ja_name) or normalize_item_english_name(en_name)
        pokeapi_id = item_name_to_id.get(slug)

        if pokeapi_id is None:
            unresolved.append(
                {
                    "ja_name": ja_name,
                    "en_name": en_name,
                    "normalized_slug": slug,
                    "reason": "pokeapi_name_not_found",
                }
            )
            continue

        ja_to_id[ja_name] = pokeapi_id

    return dict(sorted(ja_to_id.items())), unresolved


def load_item_langmap_ja_to_en() -> dict[str, str]:
    ja_to_en: dict[str, str] = {}
    with ITEM_LANGMAP_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ja_name = (row.get("日本語") or "").strip()
            en_name = (row.get("英語") or "").strip()

            if not ja_name or not en_name:
                continue

            if ja_name not in ja_to_en:
                ja_to_en[ja_name] = en_name

    return ja_to_en


def extract_jpoke_item_names() -> list[str]:
    source = ITEM_PY_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(isinstance(t, ast.Name) and t.id == "ITEMS" for t in node.targets):
                continue
        elif isinstance(node, ast.AnnAssign):
            if not (isinstance(node.target, ast.Name) and node.target.id == "ITEMS"):
                continue
        else:
            continue

        if node.value is None or not isinstance(node.value, ast.Dict):
            continue

        keys: list[str] = []
        for key_node in node.value.keys:
            if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                keys.append(key_node.value)
        return keys

    raise ValueError("ITEMS 辞書が item.py 内で見つかりません")


def build_jpoke_item_map(item_name_to_id: dict[str, int]) -> tuple[dict[str, int], list[dict]]:
    ja_to_en = load_item_langmap_ja_to_en()
    target_items = extract_jpoke_item_names()

    ja_to_id: dict[str, int] = {}
    unresolved: list[dict] = []

    for ja_name in target_items:
        if ja_name == "":
            continue

        en_name = ja_to_en.get(ja_name)
        if en_name is None and ja_name not in ITEM_SLUG_OVERRIDES:
            unresolved.append(
                {
                    "ja_name": ja_name,
                    "reason": "langmap_not_found",
                }
            )
            continue

        slug = ITEM_SLUG_OVERRIDES.get(ja_name) or normalize_item_english_name(en_name or "")
        pokeapi_id = item_name_to_id.get(slug)
        if pokeapi_id is None:
            unresolved.append(
                {
                    "ja_name": ja_name,
                    "en_name": en_name,
                    "normalized_slug": slug,
                    "reason": "pokeapi_name_not_found",
                }
            )
            continue

        ja_to_id[ja_name] = pokeapi_id

    return dict(sorted(ja_to_id.items())), unresolved


def main() -> None:
    id_map = load_json(ID_MAP_PATH)
    pokedex = load_json(POKEDEX_PATH)

    pokemon_name_to_id = id_map["sections"]["pokemon"]["by_name"]
    item_name_to_id = id_map["sections"]["item"]["by_name"]

    pokemon_ja_to_id, pokemon_unresolved = build_pokemon_map(pokedex, pokemon_name_to_id)
    item_ja_to_id, item_unresolved = build_item_map(item_name_to_id)
    jpoke_item_ja_to_id, jpoke_item_unresolved = build_jpoke_item_map(item_name_to_id)

    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": {
            "id_map": str(ID_MAP_PATH.relative_to(ROOT)).replace("\\", "/"),
            "pokedex": str(POKEDEX_PATH.relative_to(ROOT)).replace("\\", "/"),
            "item_langmap": str(ITEM_LANGMAP_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "sections": {
            "pokemon": {
                "count": len(pokemon_ja_to_id),
                "by_ja_name": pokemon_ja_to_id,
                "unresolved": pokemon_unresolved,
            },
            "item": {
                "count": len(item_ja_to_id),
                "by_ja_name": item_ja_to_id,
                "unresolved": item_unresolved,
            },
            "item_jpoke": {
                "count": len(jpoke_item_ja_to_id),
                "by_ja_name": jpoke_item_ja_to_id,
                "unresolved": jpoke_item_unresolved,
            },
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"generated: {OUTPUT_PATH}")
    print(f"  - pokemon resolved: {len(pokemon_ja_to_id)}")
    print(f"  - pokemon unresolved: {len(pokemon_unresolved)}")
    print(f"  - item resolved: {len(item_ja_to_id)}")
    print(f"  - item unresolved: {len(item_unresolved)}")
    print(f"  - item_jpoke resolved: {len(jpoke_item_ja_to_id)}")
    print(f"  - item_jpoke unresolved: {len(jpoke_item_unresolved)}")


if __name__ == "__main__":
    main()
