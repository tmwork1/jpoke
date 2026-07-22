"""poke-langmap (https://github.com/tmwork1/poke-langmap) の csv/ を
src/jpoke/data/langmap/ にダウンロードする。

特性・技・アイテム・ポケモン名の多言語対応表の基盤として使う。
"""
import os
from pathlib import Path

import requests

REPO = "tmwork1/poke-langmap"
BRANCH = "main"
SOURCE_DIR = "csv"

ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = ROOT / "src" / "jpoke" / "data" / "langmap"

API_URL = f"https://api.github.com/repos/{REPO}/contents/{SOURCE_DIR}"
HEADERS = {
    "User-Agent": "jpoke-langmap-downloader",
    "Accept": "application/vnd.github+json",
}
if token := os.environ.get("GITHUB_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {token}"


def list_files() -> list[dict]:
    response = requests.get(API_URL, headers=HEADERS, params={"ref": BRANCH}, timeout=10)
    response.raise_for_status()
    return [entry for entry in response.json() if entry["type"] == "file"]


def download_file(entry: dict, output_dir: Path) -> Path:
    response = requests.get(entry["download_url"], headers=HEADERS, timeout=10)
    response.raise_for_status()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / entry["name"]
    output_path.write_bytes(response.content)

    return output_path


def main():
    files = list_files()

    for entry in files:
        try:
            path = download_file(entry, OUTPUT_DIR)
            print(f"{path}")
        except Exception as e:
            print(f"[failed] {entry['name']} ({e})")


if __name__ == "__main__":
    main()
