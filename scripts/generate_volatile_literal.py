#!/usr/bin/env python3
"""VolatileName の Literal 定義を data/volatile.py の VOLATILES 辞書から自動生成するスクリプト。

使い方:
    python scripts/generate_volatile_literal.py

処理内容:
- src/jpoke/data/volatile.py を AST 解析し、VOLATILES 辞書のトップレベルキーを
  定義順のまま抽出する（実行時 import は行わない）
- src/jpoke/types/volatile.py 内の `VolatileName = Literal[...]` の
  複数行ブロックを、抽出したキーから再構築した内容（1行1要素）で置換する
- 冪等に実行できる（再実行しても同じ結果になる）
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
VOLATILE_PY = ROOT / "src/jpoke/data/volatile.py"
TYPE_DEFS_PY = ROOT / "src/jpoke/types/volatile.py"

GENERATED_COMMENT = (
    "    # 自動生成: python scripts/generate_volatile_literal.py で更新"
    "（元: src/jpoke/data/volatile.py）"
)


def extract_volatile_keys(target: Path) -> list[str]:
    """VOLATILES辞書のトップレベルキーを定義順に抽出する。"""
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(
                isinstance(t, ast.Name) and t.id == "VOLATILES"
                for t in node.targets
            ):
                continue
        elif isinstance(node, ast.AnnAssign):
            if not (isinstance(node.target, ast.Name) and node.target.id == "VOLATILES"):
                continue
        else:
            continue

        if node.value is None or not isinstance(node.value, ast.Dict):
            continue

        keys = []
        for key_node in node.value.keys:
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                print("エラー: VOLATILES辞書に文字列以外のキーがあります", file=sys.stderr)
                sys.exit(1)
            keys.append(key_node.value)

        return keys

    print("エラー: VOLATILES辞書が見つかりません", file=sys.stderr)
    sys.exit(1)


def build_literal_block(keys: list[str]) -> list[str]:
    """VolatileName = Literal[...] 形式の複数行ブロックを生成する。"""
    lines = ["VolatileName = Literal[", GENERATED_COMMENT]
    lines.extend(f'    "{k}",' for k in keys)
    lines.append("]")
    return lines


def update_literal_file(target: Path, new_block: list[str]) -> None:
    """types/volatile.py内のVolatileName定義ブロックを置換する。"""
    content = target.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    start_index = -1
    for i, line in enumerate(lines):
        if line == "VolatileName = Literal[":
            start_index = i
            break

    if start_index == -1:
        print("エラー: VolatileName定義ブロックが見つかりません", file=sys.stderr)
        sys.exit(1)

    end_index = -1
    for i in range(start_index + 1, len(lines)):
        if lines[i] == "]":
            end_index = i
            break

    if end_index == -1:
        print("エラー: VolatileName定義ブロックの終端が見つかりません", file=sys.stderr)
        sys.exit(1)

    current_block = lines[start_index:end_index + 1]
    if current_block == new_block:
        print("変更なし: VolatileName定義は既に最新です")
        return

    lines[start_index:end_index + 1] = new_block
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"更新: {target} の {start_index + 1}〜{start_index + len(new_block)} 行目")


def main() -> None:
    keys = extract_volatile_keys(VOLATILE_PY)
    print(f"抽出したキー数: {len(keys)}")
    print(f"抽出したキー: {keys}")

    new_block = build_literal_block(keys)
    update_literal_file(TYPE_DEFS_PY, new_block)


if __name__ == "__main__":
    main()
