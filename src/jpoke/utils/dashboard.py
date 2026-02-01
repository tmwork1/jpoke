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


def has_handlers(data: Any) -> bool:
    """ハンドラが実装されているかを判定する。

    Args:
        data: データオブジェクト（AbilityData, ItemData など）

    Returns:
        ハンドラが実装されている場合 True
    """
    if not hasattr(data, 'handlers') or not data.handlers:
        return False

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

    for name, data in data_dict.items():
        if not name:  # 空文字列はスキップ
            continue

        # ハンドラの有無をチェック
        has_impl = has_handlers(data)

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
        "field": (FIELDS, "src/jpoke/data/field.py"),
        "volatile": (VOLATILES, "src/jpoke/data/volatile.py"),
        "ailment": (AILMENTS, "src/jpoke/data/ailment.py"),
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


if __name__ == "__main__":
    main()
