"""PokeAPI のエンティティ名と ID の対応表を生成するスクリプト。

現在は pokemon と item を対象に、以下を出力する。
- name -> id
- id -> name

出力先:
    src/jpoke/data/pokeapi/id_map.json
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "src" / "jpoke" / "data" / "pokeapi" / "id_map.json"

ENDPOINTS = {
    "pokemon": "https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0",
    "item": "https://pokeapi.co/api/v2/item?limit=100000&offset=0",
}

ID_PATTERN = re.compile(r"/(\\d+)/?$")


def fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "jpoke-pokeapi-id-map-builder"})
    with urlopen(request, timeout=20) as response:  # noqa: S310
        return json.load(response)


def parse_id_from_url(url: str) -> int:
    match = ID_PATTERN.search(url)
    if match is None:
        raise ValueError(f"ID を抽出できない URL: {url}")
    return int(match.group(1))


def build_section(endpoint_url: str) -> dict:
    payload = fetch_json(endpoint_url)
    name_to_id: dict[str, int] = {}

    for row in payload.get("results", []):
        name = row["name"]
        entity_id = parse_id_from_url(row["url"])
        name_to_id[name] = entity_id

    id_to_name = {str(entity_id): name for name, entity_id in name_to_id.items()}

    return {
        "count": payload.get("count", len(name_to_id)),
        "by_name": dict(sorted(name_to_id.items())),
        "by_id": dict(sorted(id_to_name.items(), key=lambda x: int(x[0]))),
    }


def main() -> None:
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "https://pokeapi.co/",
        "sections": {},
    }

    for name, url in ENDPOINTS.items():
        result["sections"][name] = build_section(url)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"generated: {OUTPUT_PATH}")
    for section_name in ENDPOINTS:
        count = result["sections"][section_name]["count"]
        print(f"  - {section_name}: {count}")


if __name__ == "__main__":
    main()
