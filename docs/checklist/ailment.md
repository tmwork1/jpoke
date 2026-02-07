# Ailment ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## すべて

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| どく | ターン終了時に1/8ダメージ | ON_TURN_END_3 | common.modify_hp | ✅ | ✅ | ❌ | test_ailment.py |
| もうどく | ターン終了時にダメージ | ON_TURN_END_3 | もうどく | ✅ | ✅ | ❌ | test_ailment.py |
| まひ | 素早さを半減 | ON_CALC_SPEED | まひ_speed | ✅ | ✅ | ❌ | test_ailment.py |
| まひ | 行動不能（25%） | ON_TRY_ACTION | まひ_action | ✅ | ✅ | ❌ | test_ailment.py |
| やけど | ターン終了時1/16ダメージ | ON_TURN_END_3 | やけど_damage | ✅ | ✅ | ❌ | test_ailment.py |
| やけど | 物理技ダメージ半減 | ON_CALC_BURN_MODIFIER | やけど_burn | ✅ | ✅ | ❌ | test_ailment.py |
| ねむり | 行動不能 | ON_TRY_ACTION | ねむり_action | ✅ | ✅ | ❌ | test_ailment.py |
| こおり | 行動不能（20%で解凍） | ON_TRY_ACTION | こおり_action | ✅ | ✅ | ❌ | test_ailment.py |
