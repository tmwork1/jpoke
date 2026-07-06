#!/usr/bin/env python3
"""MOVES辞書の定義を五十音順に並び替えるスクリプト（分割後レイアウト対応）。

使い方:
    python scripts/sort_data/sort_moves.py
    python scripts/sort_data/sort_moves.py --check

処理内容:
- 技データは `src/jpoke/data/moves/move_<行>.py`（あ行〜わ行 + 記号・英数字）に
  分割されている。各ファイル内の `MOVES_<行>: dict[...] = {...}` を五十音順に
  並び替える（`data/move.py` 自体は分割ファイルを統合するだけの薄いファイルのため対象外）
- 記号・英数字ファイル（move_symbol.py）のみ「わるあがき」→「_で始まるエントリ」→
  その他の優先順位で並び替える。それ以外の行ファイルは単純に五十音順
- 各MoveData定義内の空行を除去する
- 辞書の範囲のみを書き換え、それ以外（import文等）はそのまま保持する
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
MOVES_DIR = ROOT / "src/jpoke/data/moves"

# (行キー, ファイル名, 辞書変数名) のリスト。data/move.py の import 順と一致させる。
ROW_FILES = [
    ("symbol", "move_symbol.py", "MOVES_SYMBOL"),
    ("a", "move_a.py", "MOVES_A"),
    ("ka", "move_ka.py", "MOVES_KA"),
    ("sa", "move_sa.py", "MOVES_SA"),
    ("ta", "move_ta.py", "MOVES_TA"),
    ("na", "move_na.py", "MOVES_NA"),
    ("ha", "move_ha.py", "MOVES_HA"),
    ("ma", "move_ma.py", "MOVES_MA"),
    ("ya", "move_ya.py", "MOVES_YA"),
    ("ra", "move_ra.py", "MOVES_RA"),
    ("wa", "move_wa.py", "MOVES_WA"),
]

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


def sort_key(name: str, row: str) -> tuple:
    """五十音順ソートキーを返す。

    move_symbol.py のみ特殊な優先順位を持つ:
      0: わるあがき（特殊技）
      1: _で始まるエントリ（内部用）
      2: その他（五十音順）
    それ以外の行ファイルは五十音順のみでソートする。
    """
    if row == "symbol":
        if name == "わるあがき":
            return (0, "")
        if name.startswith("_"):
            return (1, katakana_to_hiragana(name))
        return (2, katakana_to_hiragana(name))
    return (0, katakana_to_hiragana(name))


def parse_entries(
    lines: list[str], start: int, end: int
) -> list[tuple[str, list[str]]]:
    """MOVES_<行>辞書本体からエントリを抽出する。

    Args:
        lines: ファイル全行（0-indexed、改行なし）
        start: MOVES_<行> = { 行の次の行インデックス（0-indexed）
        end: } 行のインデックス（0-indexed、exclusive）

    Returns:
        list of (key, entry_lines) タプルのリスト
    """
    entries = []
    entry_pattern = re.compile(r'^    "([^"]+)": MoveData\(')
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


def build_sorted_content(target: Path, dict_name: str, row: str) -> str:
    """MOVES_<行>辞書を五十音順に並び替えた新しいファイル内容を返す（書き込みはしない）。"""
    content = target.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    dict_prefix = f"{dict_name}: dict["

    # 辞書の開始行を探す（0-indexed）
    dict_start = -1
    for i, line in enumerate(lines):
        if line.startswith(dict_prefix) and line.rstrip().endswith("MoveData] = {"):
            dict_start = i
            break
    if dict_start == -1:
        print(f"エラー: {dict_name}辞書が見つかりません（{target}）", file=sys.stderr)
        sys.exit(1)

    # 辞書の終了行を探す（インデントなしの '}' 行）
    dict_end = -1
    for i in range(dict_start + 1, len(lines)):
        if lines[i] == "}":
            dict_end = i
            break
    if dict_end == -1:
        print(f"エラー: {dict_name}辞書の終端が見つかりません（{target}）", file=sys.stderr)
        sys.exit(1)

    # エントリを抽出
    entries = parse_entries(lines, dict_start + 1, dict_end)

    # 各エントリの空行を除去
    entries = [(key, remove_blank_lines(entry_lines)) for key, entry_lines in entries]

    # 五十音順にソート
    entries.sort(key=lambda x: sort_key(x[0], row))

    # 辞書本体を再構築
    dict_body_lines: list[str] = []
    for _key, entry_lines in entries:
        dict_body_lines.extend(entry_lines)

    # ファイルを再構築
    header = "\n".join(lines[: dict_start + 1])
    body = "\n".join(dict_body_lines)
    footer = "\n".join(lines[dict_end:])

    new_content = header + "\n" + body + "\n" + footer + "\n"
    return new_content


def sort_row_file(row: str, filename: str, dict_name: str) -> None:
    """1つの行ファイルを並び替えてファイルを書き換える。"""
    target = MOVES_DIR / filename
    if not target.exists():
        print(f"エラー: ファイルが見つかりません → {target}", file=sys.stderr)
        sys.exit(1)
    new_content = build_sorted_content(target, dict_name, row)
    target.write_text(new_content, encoding="utf-8")
    print(f"完了: 並び替え → {target}")


def check_row_file(row: str, filename: str, dict_name: str) -> bool:
    """1つの行ファイルの並びが崩れていないかを判定する（ファイルは変更しない）。"""
    target = MOVES_DIR / filename
    if not target.exists():
        print(f"エラー: ファイルが見つかりません → {target}", file=sys.stderr)
        sys.exit(1)
    original = target.read_text(encoding="utf-8")
    new_content = build_sorted_content(target, dict_name, row)
    return new_content == original


def sort_moves() -> None:
    """全ての行ファイルを並び替える。"""
    for row, filename, dict_name in ROW_FILES:
        sort_row_file(row, filename, dict_name)


def check_moves() -> bool:
    """全ての行ファイルの並びを確認する。"""
    ok = True
    for row, filename, dict_name in ROW_FILES:
        if not check_row_file(row, filename, dict_name):
            print(f"未整列: {MOVES_DIR / filename}")
            ok = False
    return ok


def main() -> None:
    if "--check" in sys.argv[1:]:
        if check_moves():
            print(f"OK: {len(ROW_FILES)} ファイルとも整列済み")
        else:
            sys.exit(1)
        return

    sort_moves()


if __name__ == "__main__":
    main()
