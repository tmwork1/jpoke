#!/usr/bin/env python3
"""TerrainName の Literal 定義を data/field/terrain.py の TERRAIN 辞書から自動生成するスクリプト。

使い方:
    python scripts/generate_literals/generate_terrain_literal.py

処理内容:
- src/jpoke/data/field/terrain.py を AST 解析し、TERRAIN 辞書のトップレベルキーを
  定義順のまま抽出する（実行時 import は行わない）
- TERRAIN 辞書には「地形なし」を表す `""` キーが含まれていない
  （FIELDS 辞書の組み立て時に別途追加される）ため、抽出したキーの先頭に `""` を追加する
- src/jpoke/types/terrain.py 内の `TerrainName = Literal[...]` の行を
  抽出したキーから再構築した内容で置換する
- 冪等に実行できる（再実行しても同じ結果になる）
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
TERRAIN_PY = ROOT / "src/jpoke/data/field/terrain.py"
TYPE_DEFS_PY = ROOT / "src/jpoke/types/terrain.py"

GENERATED_COMMENT = (
    "# 自動生成: python scripts/generate_literals/generate_terrain_literal.py で更新"
    "（元: src/jpoke/data/field/terrain.py）"
)


def extract_terrain_keys(target: Path) -> list[str]:
    """TERRAIN辞書のトップレベルキーを定義順に抽出する。"""
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(
                isinstance(t, ast.Name) and t.id == "TERRAIN"
                for t in node.targets
            ):
                continue
        elif isinstance(node, ast.AnnAssign):
            if not (isinstance(node.target, ast.Name) and node.target.id == "TERRAIN"):
                continue
        else:
            continue

        if node.value is None or not isinstance(node.value, ast.Dict):
            continue

        keys = []
        for key_node in node.value.keys:
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                print("エラー: TERRAIN辞書に文字列以外のキーがあります", file=sys.stderr)
                sys.exit(1)
            keys.append(key_node.value)

        return keys

    print("エラー: TERRAIN辞書が見つかりません", file=sys.stderr)
    sys.exit(1)


def build_literal_line(keys: list[str]) -> str:
    """TerrainName = Literal[...] 形式の行を生成する。

    TERRAIN辞書には「地形なし」を表す `""` キーが含まれていないため、先頭に追加する。
    """
    all_keys = [""] + keys
    items = ", ".join(f'"{k}"' for k in all_keys)
    return f"TerrainName = Literal[{items}]  {GENERATED_COMMENT}"


def update_literal_file(target: Path, new_line: str) -> None:
    """types/terrain.py内のTerrainName定義行(単一/複数行)を置換する。"""
    content = target.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    start_index = -1
    for i, line in enumerate(lines):
        if line.startswith("TerrainName = Literal["):
            start_index = i
            break

    if start_index == -1:
        print("エラー: TerrainName定義行が見つかりません", file=sys.stderr)
        sys.exit(1)

    # 複数行に折り返されている場合、"]"を含む行まで探して置換範囲とする
    end_index = start_index
    for i in range(start_index, len(lines)):
        if "]" in lines[i]:
            end_index = i
            break

    if lines[start_index:end_index + 1] == [new_line]:
        print("変更なし: TerrainName定義は既に最新です")
        return

    lines[start_index:end_index + 1] = [new_line]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"更新: {target} の {start_index + 1} 行目")


def main() -> None:
    keys = extract_terrain_keys(TERRAIN_PY)
    print(f"抽出したキー: {keys}")

    new_line = build_literal_line(keys)
    update_literal_file(TYPE_DEFS_PY, new_line)


if __name__ == "__main__":
    main()
