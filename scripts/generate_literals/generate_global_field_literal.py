#!/usr/bin/env python3
"""GlobalFieldName の Literal 定義を data/field/global_field.py の GLOBAL_FIELD 辞書から自動生成するスクリプト。

使い方:
    python scripts/generate_literals/generate_global_field_literal.py

処理内容:
- src/jpoke/data/field/global_field.py を AST 解析し、GLOBAL_FIELD 辞書のトップレベルキーを
  定義順のまま抽出する（実行時 import は行わない）
- src/jpoke/types/global_field.py 内の `GlobalFieldName = Literal[...]` の行を
  抽出したキーから再構築した内容で置換する
- 冪等に実行できる（再実行しても同じ結果になる）
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
GLOBAL_FIELD_PY = ROOT / "src/jpoke/data/field/global_field.py"
TYPE_DEFS_PY = ROOT / "src/jpoke/types/global_field.py"

GENERATED_COMMENT = (
    "# 自動生成: python scripts/generate_literals/generate_global_field_literal.py で更新"
    "（元: src/jpoke/data/field/global_field.py）"
)


def extract_global_field_keys(target: Path) -> list[str]:
    """GLOBAL_FIELD辞書のトップレベルキーを定義順に抽出する。"""
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(
                isinstance(t, ast.Name) and t.id == "GLOBAL_FIELD"
                for t in node.targets
            ):
                continue
        elif isinstance(node, ast.AnnAssign):
            if not (isinstance(node.target, ast.Name) and node.target.id == "GLOBAL_FIELD"):
                continue
        else:
            continue

        if node.value is None or not isinstance(node.value, ast.Dict):
            continue

        keys = []
        for key_node in node.value.keys:
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                print("エラー: GLOBAL_FIELD辞書に文字列以外のキーがあります", file=sys.stderr)
                sys.exit(1)
            keys.append(key_node.value)

        return keys

    print("エラー: GLOBAL_FIELD辞書が見つかりません", file=sys.stderr)
    sys.exit(1)


def build_literal_line(keys: list[str]) -> str:
    """GlobalFieldName = Literal[...] 形式の行を生成する。"""
    items = ", ".join(f'"{k}"' for k in keys)
    return f"GlobalFieldName = Literal[{items}]  {GENERATED_COMMENT}"


def update_literal_file(target: Path, new_line: str) -> None:
    """types/global_field.py内のGlobalFieldName定義行を置換する。"""
    content = target.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    target_index = -1
    for i, line in enumerate(lines):
        if line.startswith("GlobalFieldName = Literal["):
            target_index = i
            break

    if target_index == -1:
        print("エラー: GlobalFieldName定義行が見つかりません", file=sys.stderr)
        sys.exit(1)

    if lines[target_index] == new_line:
        print("変更なし: GlobalFieldName定義は既に最新です")
        return

    lines[target_index] = new_line
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"更新: {target} の {target_index + 1} 行目")


def main() -> None:
    keys = extract_global_field_keys(GLOBAL_FIELD_PY)
    print(f"抽出したキー: {keys}")

    new_line = build_literal_line(keys)
    update_literal_file(TYPE_DEFS_PY, new_line)


if __name__ == "__main__":
    main()
