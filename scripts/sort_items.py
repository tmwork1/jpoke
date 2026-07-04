#!/usr/bin/env python3
"""ITEMS辞書の定義を五十音順に並び替えるスクリプト。

使い方:
    python scripts/sort_items.py

処理内容:
- ITEMS辞書の各エントリ（key: ItemData(...)）を抽出する
- 特殊エントリ（空文字キー""）を先頭に固定する
- 通常エントリを五十音順（カタカナ＝ひらがな同一視）にソートする
- 各ItemData定義内の空行を除去する
- ITEMS辞書の範囲のみを書き換え、それ以外はそのまま保持する
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
ITEM_PY = ROOT / "src/jpoke/data/item.py"

# カタカナのコードポイント範囲
_KATAKANA_START = 0x30A1  # ァ
_KATAKANA_END = 0x30F6    # ヶ


def katakana_to_hiragana(text: str) -> str:
    """カタカナをひらがなに変換する（ソートキー用）。"""
    result = []
    for ch in text:
        cp = ord(ch)
        if _KATAKANA_START <= cp <= _KATAKANA_END:
            result.append(chr(cp - 0x60))
        else:
            result.append(ch)
    return "".join(result)


def sort_key(name: str) -> tuple:
    """五十音順ソートキーを返す。

    優先順位:
      0: 空文字キー（特殊エントリ）
      1: その他（五十音順）
    """
    if name == "":
        return (0, "")
    return (1, katakana_to_hiragana(name))


def parse_entries(
    lines: list[str], start: int, end: int
) -> list[tuple[str, list[str]]]:
    """ITEMS辞書本体からエントリを抽出する。

    Args:
        lines: ファイル全行（0-indexed、改行なし）
        start: ITEMS = { 行の次の行インデックス（0-indexed）
        end: } 行のインデックス（0-indexed、exclusive）

    Returns:
        list of (key, entry_lines) タプルのリスト
    """
    entries = []
    entry_pattern = re.compile(r'^    "([^"]*)": ItemData\(')
    i = start

    while i < end:
        line = lines[i]
        m = entry_pattern.match(line)
        if m:
            key = m.group(1)
            entry_lines = [line]
            # カッコの深さを追跡してエントリの終端を探す
            depth = line.count("(") - line.count(")")
            i += 1
            while i < end and depth > 0:
                cur = lines[i]
                entry_lines.append(cur)
                depth += cur.count("(") - cur.count(")")
                i += 1
            entries.append((key, entry_lines))
        else:
            # 空行やコメントはスキップ（再構築時に除去される）
            i += 1

    return entries


def remove_blank_lines(entry_lines: list[str]) -> list[str]:
    """エントリ内の空行を除去する。"""
    return [line for line in entry_lines if line.strip() != ""]


def sort_items(target: Path) -> None:
    """ITEMS辞書を五十音順に並び替えてファイルを書き換える。

    Note:
        ITEMS辞書にはメガストーンが common_setup() 実行時に動的追加されるため、
        静的定義（ファイル上のエントリ）のみを並び替え対象とする。
    """
    content = target.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    # ITEMS辞書の開始行を探す（0-indexed）
    dict_start = -1
    for i, line in enumerate(lines):
        if line.startswith("ITEMS: dict[") and line.rstrip().endswith("ItemData] = {"):
            dict_start = i
            break
    if dict_start == -1:
        print("エラー: ITEMS辞書が見つかりません", file=sys.stderr)
        sys.exit(1)

    # ITEMS辞書の終了行を探す（インデントなしの '}' 行）
    dict_end = -1
    for i in range(dict_start + 1, len(lines)):
        if lines[i] == "}":
            dict_end = i
            break
    if dict_end == -1:
        print("エラー: ITEMS辞書の終端が見つかりません", file=sys.stderr)
        sys.exit(1)

    print(f"ITEMS辞書: 行 {dict_start + 1} 〜 {dict_end + 1} ({dict_end - dict_start - 1} 行)")

    # エントリを抽出
    entries = parse_entries(lines, dict_start + 1, dict_end)
    print(f"エントリ数: {len(entries)}")

    # 空行数のカウント（除去前）
    blank_count = sum(
        sum(1 for ln in entry_lines if ln.strip() == "")
        for _, entry_lines in entries
    )
    print(f"除去する空行数: {blank_count}")

    # 各エントリの空行を除去
    entries = [(key, remove_blank_lines(entry_lines)) for key, entry_lines in entries]

    # 五十音順にソート
    entries.sort(key=lambda x: sort_key(x[0]))

    # ITEMS辞書本体を再構築
    dict_body_lines: list[str] = []
    for _key, entry_lines in entries:
        dict_body_lines.extend(entry_lines)

    # ファイルを再構築
    header = "\n".join(lines[: dict_start + 1])
    body = "\n".join(dict_body_lines)
    footer = "\n".join(lines[dict_end:])

    new_content = header + "\n" + body + "\n" + footer + "\n"

    target.write_text(new_content, encoding="utf-8")
    print(f"完了: {len(entries)} エントリを並び替え → {target}")


def main() -> None:
    sort_items(ITEM_PY)


if __name__ == "__main__":
    main()
