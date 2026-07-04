from pathlib import Path
from urllib.parse import quote

import requests


BASE_URL = "https://wiki.pokemonwiki.com/wiki/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    )
}

# 進捗表の1列目から名前を取得する対象（進捗表にある名前がそのままwikiページ名になるもののみ）
PROGRESS_FILES = {
    "abilities": "docs/progress/ability.md",
    "items": "docs/progress/item.md",
    "moves": "docs/progress/move.md",
}


def read_names_from_progress(progress_path: Path) -> list[str]:
    with progress_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.split("\t")[0] for line in lines[1:] if line.strip()]


def read_names_from_list(file_path: Path) -> list[str]:
    with file_path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def read_names(target: str) -> list[str]:
    if target in PROGRESS_FILES:
        return read_names_from_progress(Path(PROGRESS_FILES[target]))
    return read_names_from_list(Path(f"docs/wiki/_list/{target}.txt"))


def download_html(name: str, output_dir: Path) -> Path:
    encoded_name = quote(name)
    url = f"{BASE_URL}{encoded_name}"

    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"{name}.html"
    output_path.write_text(response.text, encoding="utf-8")

    return output_path


def main(target: str):
    output_dir = Path(f"docs/wiki/{target}/")

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    names = read_names(target)
    for name in names:
        try:
            path = download_html(name, output_dir)
            print(f"{path}")
        except Exception as e:
            print(f"[failed] {name} ({e})")


if __name__ == "__main__":
    targets = [
        # "abilities",
        "items",
        "moves",
        # "ailments",
        # "volatiles",
        # "fields",
    ]

    for target in targets:
        main(target)
