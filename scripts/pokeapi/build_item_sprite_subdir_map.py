"""アイテム画像スプライトのサブディレクトリ対応表を生成するスクリプト。

PokeAPI/sprites リポジトリの `sprites/items/` 直下には全アイテムの画像が
置かれているわけではなく、一部（第8世代・第9世代で追加されたアイテムの
うち反映が遅れているもの）は `gen8/` `gen9/` サブディレクトリ配下に置かれて
いる。この対応関係はリポジトリ側の構成に依存し自動生成できないため、GitHub
API でディレクトリ一覧を取得し、JSON として書き出しておく。

`get_item_image_url` はこの対応表を参照し、直下に無いアイテムは対応する
サブディレクトリを補ってURLを組み立てる。

出力先:
    src/jpoke/data/pokeapi/item_sprite_subdir_map.json
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "src" / "jpoke" / "data" / "pokeapi" / "item_sprite_subdir_map.json"

# 対応表の対象とするサブディレクトリ。この順に探索し、直下に存在しないアイテム
# の画像を捜す。新しいサブディレクトリが追加された場合はここに追記する。
SUBDIRS = ["gen8", "gen9"]

API_BASE = "https://api.github.com/repos/PokeAPI/sprites/contents/sprites/items"


def fetch_json(url: str) -> list[dict]:
    request = Request(
        url,
        headers={"User-Agent": "jpoke-item-sprite-subdir-map-builder", "Accept": "application/vnd.github+json"},
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310
        return json.load(response)


def list_png_slugs(subdir: str) -> list[str]:
    entries = fetch_json(f"{API_BASE}/{subdir}")
    return sorted(
        entry["name"][: -len(".png")]
        for entry in entries
        if entry["type"] == "file" and entry["name"].endswith(".png")
    )


def main() -> None:
    slug_to_subdir: dict[str, str] = {}

    for subdir in SUBDIRS:
        for slug in list_png_slugs(subdir):
            slug_to_subdir[slug] = subdir

    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "https://github.com/PokeAPI/sprites/tree/master/sprites/items",
        "slug_to_subdir": dict(sorted(slug_to_subdir.items())),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"generated: {OUTPUT_PATH}")
    print(f"  - entries: {len(slug_to_subdir)}")


if __name__ == "__main__":
    main()
