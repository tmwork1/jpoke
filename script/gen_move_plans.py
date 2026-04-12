"""plan/move/ ディレクトリに全技の実装計画ファイルを生成するスクリプト。"""

from __future__ import annotations

import ast
from pathlib import Path


def load_moves_and_implemented(move_data_path: Path) -> list[tuple[str, bool]]:
    """move.py をAST解析して、技名と handlers 明示有無を取得する。"""
    source = move_data_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    moves: list[tuple[str, bool]] = []

    for node in tree.body:
        target = None
        value = None

        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                continue
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        else:
            continue

        if not isinstance(target, ast.Name) or target.id != "MOVES":
            continue
        if not isinstance(value, ast.Dict):
            raise ValueError("MOVES が dict リテラルではありません")

        for key_node, value_node in zip(value.keys, value.values, strict=False):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                continue

            name = key_node.value
            implemented = False

            if isinstance(value_node, ast.Call):
                for keyword in value_node.keywords:
                    if keyword.arg == "handlers":
                        implemented = True
                        break

            moves.append((name, implemented))
        return moves

    raise ValueError("MOVES 定義が見つかりませんでした")


def spec_line(name: str, has_spec: set[str]) -> str:
    if name in has_spec:
        return f"- 仕様書: `spec/move/{name}.md`"
    return f"- 仕様書: 未作成（`spec/move/{name}.md` が未整備）"


def plan_implemented(name: str, has_spec: set[str], has_test: bool) -> str:
    test_line = "- テスト: ○ 名前一致あり" if has_test else "- テスト: 未実装"
    return f"""# {name} 実装計画

## スコープ
- 優先度: -
- {spec_line(name, has_spec)[2:]}
- 実装状態: **実装済み**

## 実装済み内容
- `src/jpoke/data/move.py` の `{name}` に `handlers` を登録済み。
- `src/jpoke/handlers/move.py` に本体処理を実装済み。
- {test_line[2:]}

## 今後の対応
- 仕様書がない場合は `spec/move/{name}.md` を追加し、詳細仕様を記録する。
- テストが未実装の場合は `tests/test_move.py` に検証ケースを追加する。
- 仕様書の例外条件・相互作用が実装に反映されているか確認する。
"""


def plan_not_implemented(name: str, has_spec: set[str]) -> str:
    if name in has_spec:
        spec_task = f"`spec/move/{name}.md` の仕様を確認し、実装に反映するイベント候補を明示する。"
    else:
        spec_task = f"`spec/move/{name}.md` を追加し、効果/発動条件/無効化条件/解除条件を記述する。"

    return f"""# {name} 実装計画

## スコープ
- 優先度: -
- {spec_line(name, has_spec)[2:]}
- 実装方針: 先に仕様書を作成し、仕様確定後にハンドラ実装する。

## 先行タスク
1. {spec_task}
2. 世代差分がある場合は対象バージョン（SV基準など）を明記する。
3. 実装に使うイベント候補を仕様書に明示する。

## 実装フロー（仕様確定後）
1. `src/jpoke/data/move.py` の `{name}` に `handlers` を登録する。
2. `src/jpoke/handlers/move.py` に本体処理を実装する。
3. `tests/test_move.py` に発動/非発動/解除/相互作用テストを追加する。

## テスト観点
- 発動条件を満たすケース。
- 発動条件を満たさないケース。
- 無効化または解除条件のケース。
- 交代・場状態・特性無効化との相互作用ケース。
"""


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    move_data_path = root / "src" / "jpoke" / "data" / "move.py"
    spec_dir = root / "spec" / "move"
    test_move_path = root / "tests" / "test_move.py"
    out_dir = root / "plan" / "move"

    moves = load_moves_and_implemented(move_data_path)
    has_spec = {path.stem for path in spec_dir.glob("*.md")}
    test_text = test_move_path.read_text(encoding="utf-8") if test_move_path.exists() else ""

    out_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for name, implemented in moves:
        path = out_dir / f"{name}.md"
        if path.exists():
            skipped += 1
            continue

        has_test = name in test_text
        if implemented:
            content = plan_implemented(name, has_spec, has_test)
        else:
            content = plan_not_implemented(name, has_spec)

        path.write_text(content, encoding="utf-8")
        created += 1

    print(f"作成: {created} ファイル, スキップ（既存）: {skipped} ファイル")
    print(f"出力先: {out_dir}")


if __name__ == "__main__":
    main()
