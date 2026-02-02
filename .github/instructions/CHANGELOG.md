# 変更履歴

## 2026年2月1日

### フィールドシステムの日本語化と tick_fields 追加

- type_defs.py: GlobalField/SideField を日本語化
- field_manager.py: 辞書キーを日本語に変更
- tick_fields 関数追加（tests/test_utils.py）
- サイドフィールド効果を修正（EventManager、ねばねばネット）
- test_utils.start_battle に ally_side_field, foe_side_field, global_field パラメータ追加
- テストコード大幅簡略化（3-5行短縮/テスト）

**影響ファイル:** src/jpoke/utils/, src/jpoke/core/, src/jpoke/handlers/field.py, tests/

## テンプレート

### YYYY年MM月DD日

**修正内容:**
- 変更1

**影響ファイル:**
- ファイル1
