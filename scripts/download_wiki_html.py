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


def read_names(file_path: Path) -> list[str]:
    with file_path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


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
    file = f"docs/data/{target}.txt"
    output_dir = Path(f"docs/wiki_html/{target}/")

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    names = read_names(Path(file))
    for name in names:
        try:
            path = download_html(name, output_dir)
            print(f"saved: {path}")
        except Exception as e:
            print(f"failed: {name} ({e})")


if __name__ == "__main__":
    # main("abilities")
    # main("items")
    main("status_moves")
