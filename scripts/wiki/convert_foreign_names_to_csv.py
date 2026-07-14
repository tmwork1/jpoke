#!/usr/bin/env python3
"""
docs/wiki/others/ の外国語名一覧HTML（ポケモン・とくせい・わざ・アイテム）のテーブル部分を読み込み、
docs/translation/ 配下のCSVに変換する。
"""

import csv
from pathlib import Path

from bs4 import BeautifulSoup

PROJECT_DIR = Path(__file__).parent.parent.parent
WIKI_DIR = PROJECT_DIR / "docs" / "wiki" / "others"
TRANSLATION_DIR = PROJECT_DIR / "docs" / "translation"

TARGETS = [
    ("ポケモンの外国語名一覧 - ポケモンWiki.html", "graytable", "foreign_names.csv"),
    ("とくせいの外国語名一覧 - ポケモンWiki.html", "bluetable", "ability_foreign_names.csv"),
    ("わざの外国語名一覧 - ポケモンWiki.html", "bluetable", "move_foreign_names.csv"),
    ("アイテムの外国語名一覧 - ポケモンWiki.html", "graytable", "item_foreign_names.csv"),
]


def extract_rows(html_path: Path, table_class: str) -> list[list[str]]:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    rows: list[list[str]] = []
    header: list[str] | None = None
    for table in soup.find_all("table", class_=table_class):
        for i, tr in enumerate(table.find_all("tr")):
            cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
            if i == 0:
                if header is None:
                    header = cells
                    rows.append(header)
                continue
            rows.append(cells)

    return rows


def main():
    for html_name, table_class, csv_name in TARGETS:
        html_path = WIKI_DIR / html_name
        csv_path = TRANSLATION_DIR / csv_name

        rows = extract_rows(html_path, table_class)

        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"{csv_path} ({len(rows) - 1} 件)")


if __name__ == "__main__":
    main()
