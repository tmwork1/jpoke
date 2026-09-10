"""ps-champ-ja の data_jp/learnsets.json を同梱データにそのまま配置する。

事前に download.py を実行してデータをミラーしておくこと。
置き換え前後の種族名の差分（消滅／新規）と技リストの変更件数を表示する。
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OLD_LEARNSETS = ROOT / "src/jpoke/data/ps-champ-ja/learnsets.json"
NEW_LEARNSETS_SOURCE = ROOT / "ps-champ-ja/data_jp/learnsets.json"


def main() -> None:
    with open(OLD_LEARNSETS, encoding='utf-8') as f:
        old = json.load(f)
    with open(NEW_LEARNSETS_SOURCE, encoding='utf-8') as f:
        new = json.load(f)

    old_names = set(old.keys())
    new_names = set(new.keys())
    removed = sorted(old_names - new_names)
    added = sorted(new_names - old_names)
    common = old_names & new_names
    changed = sum(sorted(old[name]) != sorted(new[name]) for name in common)

    with open(OLD_LEARNSETS, "w", encoding='utf-8') as f:
        json.dump(new, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"変化なし: {len(common) - changed}件")
    print(f"技リスト変更（既存種族）: {changed}件")
    print(f"消滅（旧側のみ）: {len(removed)}件")
    for name in removed:
        print(f"  - {name}")
    print(f"新規（新側のみ）: {len(added)}件")
    for name in added:
        print(f"  + {name}")


if __name__ == "__main__":
    main()
