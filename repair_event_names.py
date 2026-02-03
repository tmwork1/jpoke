#!/usr/bin/env python3
"""イベント名置換を正しく修復するスクリプト"""

import re
from pathlib import Path

# 置換ルール
REPLACEMENTS = [
    # インポート
    (r'from jpoke\.utils\.enums import イベント', 'from jpoke.utils.enums import Event'),
    (r'from jpoke\.core\.event import イベント', 'from jpoke.core.event import Event'),

    # クラス/型定義
    (r'class イベントLog', 'class EventLog'),
    (r': list\[イベントLog\]', ': list[EventLog]'),
    (r'イベントLog\(', 'EventLog('),

    # メソッド名
    (r'def (get_|add_)イベント(_logs?)\(', r'def \1event\2('),
    (r'\.get_イベント_logs\(', '.get_event_logs('),
    (r'\.add_イベント_log\(', '.add_event_log('),
    (r'self\.logger\.(get_|add_)イベント(_logs?)\(', r'self.logger.\1event\2('),

    # 変数名
    (r'イベント_logs', 'event_logs'),

    # イベント定数（最も複雑）
    # これは最後に処理する
]


def fix_event_constants(content: str) -> str:
    """イベント定数を修復 (最後に実施)"""
    # イベント.ON_* パターン
    content = re.sub(r'イベント\.([A-Z_]+)', r'Event.\1', content)

    # イベント.on() / イベント.emit()
    content = re.sub(r'イベント\.on\(', 'Event.on(', content)
    content = re.sub(r'イベント\.emit\(', 'Event.emit(', content)

    # イベント(…) コンストラクタはないが、念のため
    content = re.sub(r'イベント\(', 'Event(', content)

    return content


def repair_files():
    """すべてのPythonファイルを修復"""
    base = Path('c:/Users/tmtmp/Documents/pokemon/jpoke')

    for py_file in list(base.glob('src/**/*.py')) + list(base.glob('tests/**/*.py')):
        if '__pycache__' in str(py_file):
            continue

        print(f"処理中: {py_file.relative_to(base)}")

        content = py_file.read_text(encoding='utf-8')
        original = content

        # 通常の置換
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)

        # イベント定数の修復
        content = fix_event_constants(content)

        if content != original:
            py_file.write_text(content, encoding='utf-8')
            print(f"  ✓ 更新しました")
        else:
            print(f"  (変更なし)")


if __name__ == '__main__':
    repair_files()
    print("\n修復完了！")
