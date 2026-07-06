#!/usr/bin/env python3
"""MoveName の Literal 定義を data/move.py（+ data/moves/*.py）の MOVES 辞書から自動生成するスクリプト。

使い方:
    python scripts/generate_literals/generate_move_literal.py

処理内容:
- src/jpoke/data/move.py を AST 解析し、MOVES 辞書のトップレベルキーを
  定義順のまま抽出する（実行時 import は行わない）。
  技データは五十音の行ごとに data/moves/move_<行>.py に分割されているため、
  `MOVES = {**MOVES_A, **MOVES_KA, ...}` のような dict 展開も解決し、
  import 元のファイルを辿って各行のキーを再帰的に抽出する。
- src/jpoke/types/move.py 内の `MoveName = Literal[...]` の
  複数行ブロックを、抽出したキーから再構築した内容（1行1要素）で置換する
- 冪等に実行できる（再実行しても同じ結果になる）
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
MOVE_PY = ROOT / "src/jpoke/data/move.py"
TYPE_DEFS_PY = ROOT / "src/jpoke/types/move.py"

GENERATED_COMMENT = (
    "    # 自動生成: python scripts/generate_literals/generate_move_literal.py で更新"
    "（元: src/jpoke/data/move.py）"
)


def _build_import_map(tree: ast.Module) -> dict[str, Path]:
    """モジュール内の `from .xxx.yyy import NAME` を { NAME: 解決先ファイルパス } に変換する。

    相対importのみ対応する（本スクリプトが対象とするdata/配下のファイルは全て相対import のため）。
    """
    import_map: dict[str, Path] = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level < 1:
            continue
        base = MOVE_PY.parent
        for _ in range(node.level - 1):
            base = base.parent
        if node.module:
            base = base.joinpath(*node.module.split("."))
        module_path = base.with_suffix(".py")
        for alias in node.names:
            name = alias.asname or alias.name
            import_map[name] = module_path
    return import_map


def _find_dict_assign(tree: ast.Module, dict_name: str) -> ast.Dict | None:
    """トップレベルの `<dict_name>: dict[...] = {...}` / `<dict_name> = {...}` を探す。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(isinstance(t, ast.Name) and t.id == dict_name for t in node.targets):
                continue
        elif isinstance(node, ast.AnnAssign):
            if not (isinstance(node.target, ast.Name) and node.target.id == dict_name):
                continue
        else:
            continue

        if node.value is not None and isinstance(node.value, ast.Dict):
            return node.value
    return None


def _extract_keys_from_dict_node(
    dict_node: ast.Dict, target: Path, import_map: dict[str, Path]
) -> list[str]:
    """Dict ノードからキーを抽出する。`**NAME` 形式の展開は import 元ファイルを辿って再帰解決する。"""
    keys: list[str] = []
    for key_node, value_node in zip(dict_node.keys, dict_node.values):
        if key_node is None:
            # `**NAME` による dict 展開（五十音の行ごとの分割ファイル）
            if not isinstance(value_node, ast.Name):
                print(f"エラー: MOVES辞書の dict 展開が変数参照ではありません（{target}）", file=sys.stderr)
                sys.exit(1)
            sub_path = import_map.get(value_node.id)
            if sub_path is None or not sub_path.exists():
                print(f"エラー: {value_node.id} の import 元が解決できません（{target}）", file=sys.stderr)
                sys.exit(1)
            keys.extend(extract_move_keys(sub_path, dict_name=value_node.id))
            continue

        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            print("エラー: MOVES辞書に文字列以外のキーがあります", file=sys.stderr)
            sys.exit(1)
        keys.append(key_node.value)
    return keys


def extract_move_keys(target: Path, dict_name: str = "MOVES") -> list[str]:
    """MOVES辞書（または分割先の MOVES_<行> 辞書）のトップレベルキーを定義順に抽出する。"""
    source = target.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    dict_node = _find_dict_assign(tree, dict_name)
    if dict_node is None:
        print(f"エラー: {dict_name}辞書が見つかりません（{target}）", file=sys.stderr)
        sys.exit(1)

    import_map = _build_import_map(tree)
    return _extract_keys_from_dict_node(dict_node, target, import_map)


def build_literal_block(keys: list[str]) -> list[str]:
    """MoveName = Literal[...] 形式の複数行ブロックを生成する。"""
    lines = ["MoveName = Literal[", GENERATED_COMMENT]
    lines.extend(f'    "{k}",' for k in keys)
    lines.append("]")
    return lines


def update_literal_file(target: Path, new_block: list[str]) -> None:
    """types/move.py内のMoveName定義ブロックを置換する。"""
    content = target.read_text(encoding="utf-8-sig")
    lines = content.splitlines(keepends=False)

    start_index = -1
    for i, line in enumerate(lines):
        if line == "MoveName = Literal[":
            start_index = i
            break

    if start_index == -1:
        print("エラー: MoveName定義ブロックが見つかりません", file=sys.stderr)
        sys.exit(1)

    end_index = -1
    for i in range(start_index + 1, len(lines)):
        if lines[i] == "]":
            end_index = i
            break

    if end_index == -1:
        print("エラー: MoveName定義ブロックの終端が見つかりません", file=sys.stderr)
        sys.exit(1)

    current_block = lines[start_index:end_index + 1]
    if current_block == new_block:
        print("変更なし: MoveName定義は既に最新です")
        return

    lines[start_index:end_index + 1] = new_block
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"更新: {target} の {start_index + 1}〜{start_index + len(new_block)} 行目")


def main() -> None:
    keys = extract_move_keys(MOVE_PY)
    print(f"抽出したキー数: {len(keys)}")

    new_block = build_literal_block(keys)
    update_literal_file(TYPE_DEFS_PY, new_block)


if __name__ == "__main__":
    main()
