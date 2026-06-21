#!/usr/bin/env python3
"""ハンドラモジュール内の公開関数を五十音順に並び替えるスクリプト。

使い方:
    python scripts/sort_handlers.py src/jpoke/handlers/ability.py
    python scripts/sort_handlers.py src/jpoke/handlers/move_status.py src/jpoke/handlers/item.py

引数を省略すると主要ハンドラファイルを全て対象にする。

処理内容:
- 日本語（ひらがな・カタカナ）から始まる公開ハンドラ関数をソート対象とする
- アンダースコアまたは英数字から始まる関数・変数はヘッダーに留める
- ただし、ソート対象の日本語関数の直前に置かれたモジュールレベル変数定義は
  その関数チャンクに含める（依存関係を保持する）
- カタカナ＝ひらがな同一視で五十音順ソートする
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ひらがな・カタカナのコードポイント範囲
_HIRAGANA_START = 0x3041  # ぁ
_HIRAGANA_END = 0x3096    # ゖ
_KATAKANA_START = 0x30A1  # ァ
_KATAKANA_END = 0x30F6    # ヶ


def is_japanese_start(name: str) -> bool:
    """関数名がひらがな・カタカナで始まるかを返す。"""
    if not name:
        return False
    cp = ord(name[0])
    return (
        _HIRAGANA_START <= cp <= _HIRAGANA_END
        or _KATAKANA_START <= cp <= _KATAKANA_END
    )


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


def sort_key(func_name: str) -> str:
    """五十音順ソートキーを返す。カタカナ＝ひらがな同一視。"""
    return katakana_to_hiragana(func_name)


def sort_file(target: Path) -> None:
    source = target.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    tree = ast.parse(source)

    # トップレベルノードを行順に収集
    top_nodes = sorted(tree.body, key=lambda n: n.lineno)

    # ソート対象の日本語関数を特定する（0-indexed の行番号）
    # (func_name, start_line_0, end_line_0)
    jp_funcs: list[tuple[str, int, int]] = []
    for node in top_nodes:
        if not isinstance(node, ast.FunctionDef):
            continue
        if not is_japanese_start(node.name):
            continue
        start_0 = (
            node.decorator_list[0].lineno
            if node.decorator_list
            else node.lineno
        ) - 1
        end_0 = node.end_lineno - 1
        jp_funcs.append((node.name, start_0, end_0))

    if not jp_funcs:
        print(f"スキップ: 日本語始まりの関数が見つかりません → {target}")
        return

    jp_funcs.sort(key=lambda x: x[1])

    # ソート対象の日本語関数が占める行の集合
    jp_line_set: set[int] = set()
    for _, start, end in jp_funcs:
        jp_line_set.update(range(start, end + 1))

    first_jp_start = jp_funcs[0][1]
    last_jp_end = jp_funcs[-1][2]

    # ── ヘッダー（最初のソート対象関数より前）──
    # インポート、定数、プライベート関数、英数字始まり関数をすべて含む
    header_lines: list[str] = []
    i = 0
    while i < first_jp_start:
        header_lines.append(lines[i])
        i += 1

    # ── 関数チャンクを構築する ──
    # ソート対象関数の間に挟まるモジュールレベルコード（変数定義等）を
    # 直後の日本語関数チャンクに前置きとして含める
    #
    # 方針:
    #   1. jp_funcs[0] 〜 jp_funcs[-1] の範囲を走査する
    #   2. jp_line_set に含まれない行（= 関数間のコード）は「待機中の前置き」として蓄積する
    #   3. 次の日本語関数が始まったらその前置きをそのチャンクの先頭に付与する

    # まず各日本語関数のチャンクを収集する（前置きなし）
    raw_chunks: list[tuple[str, str]] = []  # (func_name, chunk_text)
    for name, start, end in jp_funcs:
        raw_chunks.append((name, "".join(lines[start : end + 1]).rstrip()))

    # 関数間のコードを「どの日本語関数の直後にあるか」でまとめる
    # interleaved[i] = jp_funcs[i] の直後（jp_funcs[i+1] の直前）にある行群
    interleaved: list[list[str]] = [[] for _ in range(len(jp_funcs))]

    i = first_jp_start
    current_jp_idx = 0
    while i <= last_jp_end:
        if i in jp_line_set:
            # ソート対象関数の行 — jp_idx を更新する
            # jp_funcs のどれに属するか特定する
            for idx, (_, s, e) in enumerate(jp_funcs):
                if s <= i <= e:
                    current_jp_idx = idx
                    break
            i += 1
        else:
            # 関数間のコード — 現在の jp 関数の後に属するとして蓄積
            interleaved[current_jp_idx].append(lines[i])
            i += 1

    # ── フッター（最後のソート対象関数より後）──
    footer_lines = lines[last_jp_end + 1 :]

    def normalize_blank_lines(text: str) -> str:
        return re.sub(r"\n{3,}", "\n\n", text)

    header_text = normalize_blank_lines("".join(header_lines)).rstrip()

    # チャンクをソートする
    # ただし interleaved（前置きコード）は元の位置関係を保つために
    # 各チャンクにどの interleaved を前置きするかを決める。
    #
    # 設計:
    #   - interleaved[i] は jp_funcs[i] の直後のコード
    #   - ソート後、jp_funcs[i] が別の位置に移動しても、
    #     interleaved[i] はそれに追従する（セットにする）
    #
    # つまり各チャンクに (前置きコード, 関数コード) を持たせる。
    # ただし前置きコードは「次の日本語関数の直前」にあると見なし、
    # 並び替え後も次の関数の前に配置される。
    #
    # より単純なアプローチ:
    #   interleaved[i] を jp_funcs[i+1] の前置きとして扱う
    #   interleaved[最後] はフッターに移す

    # 各チャンクのテキスト構築（前置き付き）
    # prefix[i] = jp_funcs[i] の前に来るべき interleaved コード
    # prefix[0] は interleaved[-1_before_first] = 存在しない（ヘッダーに入っている）
    # prefix[i] = interleaved[i-1]  （i >= 1）

    # ソート対象チャンク: (sort_key, prefix_text, func_text)
    sorted_chunks: list[tuple[str, str, str]] = []
    for idx, (name, func_text) in enumerate(raw_chunks):
        prefix_text = ""
        if idx > 0:
            prefix_lines = interleaved[idx - 1]
            prefix_text = normalize_blank_lines("".join(prefix_lines)).strip()
        sorted_chunks.append((sort_key(name), prefix_text, func_text))

    # 末尾の interleaved（最後の関数の後）はフッターに追加
    trailing_interleaved = interleaved[-1]
    trailing_text = "".join(trailing_interleaved).strip()

    # 五十音順でソート
    sorted_chunks.sort(key=lambda x: x[0])

    # ── 出力組み立て ──
    parts = [header_text]
    for _, prefix_text, func_text in sorted_chunks:
        if prefix_text:
            parts.append("\n\n\n" + prefix_text)
        parts.append("\n\n\n" + func_text)

    # フッター
    footer_text_base = trailing_text
    footer_rest = "".join(footer_lines).strip()
    combined_footer = "\n\n".join(
        t for t in [footer_text_base, footer_rest] if t
    )
    if combined_footer:
        parts.append("\n\n\n" + combined_footer + "\n")
    else:
        parts.append("\n")

    target.write_text("".join(parts), encoding="utf-8")
    print(f"並び替え完了: {len(sorted_chunks)} 関数 → {target}")


DEFAULT_TARGETS = [
    "src/jpoke/handlers/ability.py",
    "src/jpoke/handlers/item.py",
    "src/jpoke/handlers/move_status.py",
    "src/jpoke/handlers/move_attack.py",
    "src/jpoke/handlers/volatile.py",
]


def main() -> None:
    args = sys.argv[1:]
    if args:
        targets = [Path(a) for a in args]
    else:
        targets = [ROOT / t for t in DEFAULT_TARGETS]

    for t in targets:
        if not t.is_absolute():
            t = ROOT / t
        if not t.exists():
            print(f"エラー: ファイルが見つかりません → {t}", file=sys.stderr)
            sys.exit(1)
        sort_file(t)


if __name__ == "__main__":
    main()
