"""実装状況ダッシュボードを生成するモジュール。

各種データファイル（特性、技、アイテム、フィールド効果など）の
実装状況を集計し、JSON形式で出力します。
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jpoke.data.ability import ABILITIES
from jpoke.data.item import ITEMS
from jpoke.data.field import FIELDS
from jpoke.data.volatile import VOLATILES
from jpoke.data.ailment import AILMENTS
from jpoke.data.move import MOVES


def has_handlers(data: Any, exclude_common: bool = False) -> bool:
    """ハンドラが実装されているかを判定する。

    Args:
        data: データオブジェクト（AbilityData, ItemData など）
        exclude_common: 共通ハンドラ（ON_CONSUME_PP）を除外するか

    Returns:
        ハンドラが実装されている場合 True
    """
    if not hasattr(data, 'handlers'):
        return False

    # handlersが空でないことを確認（Noneまたは空のdictはFalse）
    if not data.handlers:
        return False

    # 技の場合、共通ハンドラ（ON_CONSUME_PP）を除外
    if exclude_common:
        from jpoke.core import Event
        handlers = {k: v for k, v in data.handlers.items() if k != Event.ON_CONSUME_PP}
        return len(handlers) > 0

    # ハンドラが空の辞書でないことを確認
    return len(data.handlers) > 0


def check_todo_in_file(filepath: str, name: str) -> bool:
    """ファイル内に該当項目のTODOコメントがあるかを確認する。

    Args:
        filepath: ファイルパス
        name: 項目名

    Returns:
        TODOコメントがある場合 True
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # TODO: <項目名> のパターンを検索
            pattern = rf'#\s*TODO:.*{re.escape(name)}'
            return bool(re.search(pattern, content, re.IGNORECASE))
    except (FileNotFoundError, IOError):
        return False


def analyze_category(
    data_dict: Dict[str, Any],
    category_name: str,
    data_file: str
) -> Tuple[List[str], List[str]]:
    """カテゴリのデータを分析する。

    Args:
        data_dict: データの辞書
        category_name: カテゴリ名
        data_file: データファイルのパス

    Returns:
        (実装済みリスト, 未実装リスト) のタプル
    """
    implemented = []
    not_implemented = []

    # 技の場合は共通ハンドラを除外
    exclude_common = (category_name == "move")

    for name, data in data_dict.items():
        if not name:  # 空文字列はスキップ
            continue

        # ハンドラの有無をチェック
        has_impl = has_handlers(data, exclude_common=exclude_common)

        # TODOコメントの有無をチェック
        has_todo = check_todo_in_file(data_file, name)

        if has_impl and not has_todo:
            implemented.append(name)
        else:
            not_implemented.append(name)

    return implemented, not_implemented


def generate_dashboard() -> Dict[str, Any]:
    """実装状況ダッシュボードを生成する。

    Returns:
        ダッシュボードデータの辞書
    """
    categories = {
        "ability": (ABILITIES, "src/jpoke/data/ability.py"),
        "item": (ITEMS, "src/jpoke/data/item.py"),
        "move": (MOVES, "src/jpoke/data/move.py"),
        "ailment": (AILMENTS, "src/jpoke/data/ailment.py"),
        "volatile": (VOLATILES, "src/jpoke/data/volatile.py"),
        "field": (FIELDS, "src/jpoke/data/field.py"),
    }

    summary = {}
    details = {}

    for category, (data_dict, filepath) in categories.items():
        implemented, not_implemented = analyze_category(
            data_dict, category, filepath
        )

        total = len(implemented) + len(not_implemented)
        percentage = (len(implemented) / total * 100) if total > 0 else 0

        summary[category] = {
            "total": total,
            "implemented": len(implemented),
            "not_implemented": len(not_implemented),
            "percentage": round(percentage, 2)
        }

        details[category] = {
            "implemented": sorted(implemented),
            "not_implemented": sorted(not_implemented)
        }

    return {
        "summary": summary,
        "details": details
    }


def main():
    """ダッシュボードを生成してJSONファイルに出力する。"""
    dashboard = generate_dashboard()

    output_file = "dashboard.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    print(f"Dashboard generated: {output_file}")
    print("\n=== Summary ===")
    for category, stats in dashboard["summary"].items():
        print(f"{category:12s}: {stats['implemented']:4d}/{stats['total']:4d} "
              f"({stats['percentage']:5.1f}%)")

    # README.mdを更新
    update_readme(dashboard)


def update_readme(dashboard: Dict[str, Any]):
    """README.mdの実装状況セクションを更新する。"""
    from datetime import datetime

    readme_path = "README.md"

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Warning: {readme_path} not found")
        return

    # 日付を更新
    now = datetime.now()
    today = f"{now.year}年{now.month}月{now.day}日"

    # サマリーテーブルを生成
    summary = dashboard["summary"]

    # カテゴリ名の日本語マッピング
    category_names = {
        "ability": "特性",
        "item": "アイテム",
        "move": "技",
        "ailment": "状態異常",
        "volatile": "揮発性状態",
        "field": "フィールド効果",
    }

    # カテゴリの順序（進捗率の高い順）
    sorted_categories = sorted(
        summary.keys(),
        key=lambda x: summary[x]['percentage'],
        reverse=True
    )

    table_lines = ["| カテゴリ | 実装済み | 総数 | 進捗率 |", "|---------|---------|------|--------|"]

    for category in sorted_categories:
        stats = summary[category]
        jp_name = category_names.get(category, category)
        percentage = stats['percentage']

        # 100%の場合は✅を追加
        display_name = f"**{jp_name}**"
        if percentage == 100.0:
            progress = f"**{percentage:.1f}%** ✅"
        else:
            progress = f"{percentage:.1f}%"

        table_lines.append(
            f"| {display_name} | {stats['implemented']} | {stats['total']} | {progress} |"
        )

    table_content = "\n".join(table_lines)

    # README内の実装状況セクションを置換
    import re

    # 見出しと日付を更新
    pattern = r'## 実装状況（\d+年\d+月\d+日時点）'
    replacement = f'## 実装状況（{today}時点）'
    content = re.sub(pattern, replacement, content)

    # テーブルを更新
    pattern = r'\| カテゴリ \| 実装済み \| 総数 \| 進捗率 \|.*?\n(?=\n###|\n##|$)'
    replacement = table_content + "\n"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # ファイルに書き込み
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✓ README.md updated with latest implementation status")


if __name__ == "__main__":
    main()
