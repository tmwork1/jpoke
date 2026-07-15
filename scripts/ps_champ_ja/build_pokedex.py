"""ps-champ-ja (https://github.com/tmwork1/ps-champ-ja) の data_jp/pokedex.json を、
src/jpoke/data/pokedex.json にそのまま配置する。

事前に download.py を実行して ps-champ-ja/data_jp/pokedex.json をミラーしておくこと。
実行すると、置き換え前後の名前一覧の差分（消滅／新規）を標準出力に表示する。
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OLD_POKEDEX = ROOT / "src/jpoke/data/pokedex.json"
NEW_POKEDEX_SOURCE = ROOT / "ps-champ-ja/data_jp/pokedex.json"


def load_old_names() -> set[str]:
    with open(OLD_POKEDEX, encoding='utf-8') as f:
        data = json.load(f)
    return {entry["name"] for entry in data.values()}


def main():
    old_names = load_old_names()

    with open(NEW_POKEDEX_SOURCE, encoding='utf-8') as f:
        new_data = json.load(f)
    new_names = set(new_data.keys())

    with open(OLD_POKEDEX, "w", encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    removed = sorted(old_names - new_names)
    added = sorted(new_names - old_names)
    unchanged = old_names & new_names

    print(f"変化なし: {len(unchanged)}件")
    print(f"消滅（旧側のみ）: {len(removed)}件")
    for name in removed:
        print(f"  - {name}")
    print(f"新規（新側のみ）: {len(added)}件")
    for name in added:
        print(f"  + {name}")


if __name__ == "__main__":
    main()
