#!/usr/bin/env python3
"""ItemName の Literal 定義を data/item.py の ITEMS 辞書から自動生成するスクリプト。

使い方:
    python scripts/generate_literals/generate_item_literal.py

処理内容:
- src/jpoke/data/item.py を AST 解析し、ITEMS 辞書のトップレベルキーを
  定義順のまま抽出する（実行時 import は行わない）
- src/jpoke/data/megaevol.py の MEGA_STONES は pokedex.json（requiredItem）から実行時に
  動的に構築されるため、実際に import して辞書キー（メガストーン名）を抽出する。
  メガストーンは common_setup() 内の _add_mega_stones() で実行時に ITEMS 辞書へ追加されるため、
  静的な ITEMS 辞書リテラルには含まれず、別途抽出して末尾に連結する
- src/jpoke/types/item.py 内の `ItemName = Literal[...]` の
  複数行ブロックを、抽出したキーから再構築した内容（1行1要素）で置換する
- 冪等に実行できる（再実行しても同じ結果になる）
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
ITEM_PY = ROOT / "src/jpoke/data/item.py"
TYPE_DEFS_PY = ROOT / "src/jpoke/types/item.py"

GENERATED_COMMENT = (
    "    # 自動生成: python scripts/generate_literals/generate_item_literal.py で更新"
    "（元: src/jpoke/data/item.py）"
)


def extract_item_keys(target: Path) -> list[str]:
    """ITEMS辞書のトップレベルキーを定義順に抽出する。"""
    source = target.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(
                isinstance(t, ast.Name) and t.id == "ITEMS"
                for t in node.targets
            ):
                continue
        elif isinstance(node, ast.AnnAssign):
            if not (isinstance(node.target, ast.Name) and node.target.id == "ITEMS"):
                continue
        else:
            continue

        if node.value is None or not isinstance(node.value, ast.Dict):
            continue

        keys = []
        for key_node in node.value.keys:
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                print("エラー: ITEMS辞書に文字列以外のキーがあります", file=sys.stderr)
                sys.exit(1)
            keys.append(key_node.value)

        return keys

    print("エラー: ITEMS辞書が見つかりません", file=sys.stderr)
    sys.exit(1)


def extract_mega_stone_keys() -> list[str]:
    """MEGA_STONES辞書（pokedex.jsonから実行時に構築される）のキーを定義順に抽出する。"""
    from jpoke.data.megaevol import MEGA_STONES
    return list(MEGA_STONES.keys())


def build_literal_block(keys: list[str]) -> list[str]:
    """ItemName = Literal[...] 形式の複数行ブロックを生成する。"""
    lines = ["ItemName = Literal[", GENERATED_COMMENT]
    lines.extend(f'    "{k}",' for k in keys)
    lines.append("]")
    return lines


def update_literal_file(target: Path, new_block: list[str]) -> None:
    """types/item.py内のItemName定義ブロックを置換する。"""
    content = target.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    start_index = -1
    for i, line in enumerate(lines):
        if line == "ItemName = Literal[":
            start_index = i
            break

    if start_index == -1:
        print("エラー: ItemName定義ブロックが見つかりません", file=sys.stderr)
        sys.exit(1)

    end_index = -1
    for i in range(start_index + 1, len(lines)):
        if lines[i] == "]":
            end_index = i
            break

    if end_index == -1:
        print("エラー: ItemName定義ブロックの終端が見つかりません", file=sys.stderr)
        sys.exit(1)

    current_block = lines[start_index:end_index + 1]
    if current_block == new_block:
        print("変更なし: ItemName定義は既に最新です")
        return

    lines[start_index:end_index + 1] = new_block
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"更新: {target} の {start_index + 1}〜{start_index + len(new_block)} 行目")


def main() -> None:
    keys = extract_item_keys(ITEM_PY)
    mega_stone_keys = extract_mega_stone_keys()
    # メガストーンは common_setup() 実行時に ITEMS 辞書へ追加されるため、末尾に連結する
    all_keys = keys + mega_stone_keys
    print(f"抽出したキー数: {len(keys)} + メガストーン数: {len(mega_stone_keys)} = {len(all_keys)}")

    new_block = build_literal_block(all_keys)
    update_literal_file(TYPE_DEFS_PY, new_block)


if __name__ == "__main__":
    main()
