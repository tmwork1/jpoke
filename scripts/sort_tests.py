#!/usr/bin/env python3
"""テストモジュールの test_ 関数を五十音順に並び替えるスクリプト。

使い方:
    python scripts/sort_tests.py tests/test_ability.py
    python scripts/sort_tests.py tests/test_move.py tests/test_item.py

引数を省略すると tests/test_ability.py を対象にする。

処理内容:
- タイトルブロック（# ──── 区切り線）を除去する
- 関数間のモジュールレベル変数定義をヘッダー末尾にまとめる
- test_ 関数をカタカナ＝ひらがな同一視で五十音順ソートする
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

TITLE_SEP_RE = re.compile(r"^# [─]{10,}")


def katakana_to_hiragana(text: str) -> str:
    result = []
    for ch in text:
        cp = ord(ch)
        if 0x30A1 <= cp <= 0x30F6:
            result.append(chr(cp - 0x60))
        else:
            result.append(ch)
    return "".join(result)


def sort_key(func_name: str) -> str:
    return katakana_to_hiragana(func_name.removeprefix("test_"))


def sort_file(target: Path) -> None:
    source = target.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    tree = ast.parse(source)

    # トップレベルの test_ 関数を収集（0-indexed, inclusive）
    test_funcs: list[tuple[str, int, int]] = []  # (name, start, end)
    for node in tree.body:
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
            continue
        start_0 = (node.decorator_list[0].lineno if node.decorator_list else node.lineno) - 1
        end_0 = node.end_lineno - 1

        # AST はコメントを認識しない。末尾のインデント行（# コメント等）も関数に含める。
        while end_0 + 1 < len(lines) and lines[end_0 + 1].startswith((" ", "\t")):
            end_0 += 1

        test_funcs.append((node.name, start_0, end_0))

    if not test_funcs:
        print(f"スキップ: test_ 関数が見つかりません → {target}")
        return

    test_funcs.sort(key=lambda x: x[1])

    test_line_set: set[int] = set()
    for _, start, end in test_funcs:
        test_line_set.update(range(start, end + 1))

    first_test_start = test_funcs[0][1]
    last_test_end = test_funcs[-1][2]

    def skip_title_block(idx: int, limit: int) -> int:
        """セパレータ行から始まるタイトルブロックを読み飛ばし、次の行番号を返す"""
        idx += 1
        while idx < limit:
            if TITLE_SEP_RE.match(lines[idx].rstrip()):
                return idx + 1
            idx += 1
        return idx

    # ── ヘッダー（最初のテスト関数より前）──
    header_lines: list[str] = []
    i = 0
    while i < first_test_start:
        line = lines[i]
        if TITLE_SEP_RE.match(line.rstrip()):
            i = skip_title_block(i, first_test_start)
        else:
            header_lines.append(line)
            i += 1

    # ── 関数間のモジュールレベルコード（変数定義等）──
    mid_lines: list[str] = []
    i = first_test_start
    while i <= last_test_end:
        if i in test_line_set:
            i += 1
            continue
        line = lines[i]
        if TITLE_SEP_RE.match(line.rstrip()):
            i = skip_title_block(i, last_test_end + 1)
        else:
            mid_lines.append(line)
            i += 1

    # ── フッター（最後のテスト関数より後）──
    footer_lines = lines[last_test_end + 1:]

    def normalize_blank_lines(text: str) -> str:
        return re.sub(r"\n{3,}", "\n\n", text)

    header_text = normalize_blank_lines(
        "".join(header_lines) + "".join(mid_lines)
    ).rstrip()

    # テスト関数チャンクを抽出して五十音順ソート
    func_chunks = [
        (name, "".join(lines[start : end + 1]).rstrip())
        for name, start, end in test_funcs
    ]
    func_chunks.sort(key=lambda x: sort_key(x[0]))

    # ── 出力組み立て ──
    parts = [header_text]
    for _, chunk in func_chunks:
        parts.append("\n\n\n" + chunk)

    footer_text = "".join(footer_lines).strip()
    if footer_text:
        parts.append("\n\n\n" + footer_text + "\n")
    else:
        parts.append("\n")

    target.write_text("".join(parts), encoding="utf-8")
    print(f"並び替え完了: {len(func_chunks)} 関数 → {target}")


def main() -> None:
    args = sys.argv[1:]
    targets = [Path(a) for a in args] if args else [ROOT / "tests" / "test_ability.py"]
    for t in targets:
        if not t.is_absolute():
            t = ROOT / t
        if not t.exists():
            print(f"エラー: ファイルが見つかりません → {t}", file=sys.stderr)
            sys.exit(1)
        sort_file(t)


if __name__ == "__main__":
    main()
