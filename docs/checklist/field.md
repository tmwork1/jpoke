# Field ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## 天候（Weather）ハンドラ

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| はれ | 炎技1.5倍、水梗0.5倍 | ON_CALC_POWER_MODIFIER | はれ_power_modifier | ✅ | ✅ | ❌ | test_field.py |
| はれ | かみなり・ぼうふう命中補正 | ON_CALC_ACCURACY | はれ_accuracy | ❌ | ❌ | ❌ | MoveHandler側で個別対応 |
| あめ | 水梗1.5倍、炎梗0.5倍 | ON_CALC_POWER_MODIFIER | あめ_power_modifier | ✅ | ✅ | ❌ | test_field.py |
| あめ | かみなり・ぼうふう必中化 | ON_CALC_ACCURACY | あめ_accuracy | ❌ | ❌ | ❌ | MoveHandler側で個別対応 |
| すなあらし | 1/16ダメージ | ON_TURN_END_2 | すなあらし_damage | ✅ | ✅ | ❌ | test_field.py |
| すなあらし | いわタイプ特防1.5倍 | ON_CALC_DEF_MODIFIER | すなあらし_spdef_boost | ✅ | ❌ | ❌ |  |
| ゆき | こおりタイプ防御1.5倍 | ON_CALC_DEF_MODIFIER | ゆき_def_boost | ✅ | ❌ | ❌ |  |
| ゆき | ふぶき必中化 | ON_CALC_ACCURACY | ゆき_accuracy | ❌ | ❌ | ❌ | MoveHandler側で個別対応 |

## 地形（Terrain）ハンドラ

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| エレキフィールド | 電気梗1.3倍 | ON_CALC_POWER_MODIFIER | エレキフィールド_power_modifier | ✅ | ✅ | ❌ | test_field.py |
| エレキフィールド | ねむり無効 | ON_BEFORE_APPLY_AILMENT | エレキフィールド_prevent_sleep | ✅ | ❌ | ❌ |  |
| エレキフィールド | 出場時のねむり回復 | ON_SWITCH_IN | エレキフィールド_cure_sleep | ✅ | ❌ | ❌ |  |
| グラスフィールド | 草梗1.3倍 | ON_CALC_POWER_MODIFIER | グラスフィールド_power_modifier | ✅ | ✅ | ❌ | test_field.py |
| グラスフィールド | ターン終了時1/16回復 | ON_TURN_END_2 | グラスフィールド_heal | ✅ | ❌ | ❌ |  |
| サイコフィールド | エスパー梗1.3倍 | ON_CALC_POWER_MODIFIER | サイコフィールド_power_modifier | ✅ | ✅ | ❌ | test_field.py |
| サイコフィールド | 先制技無効 | ON_CHECK_PRIORITY_VALID | サイコフィールド_block_priority | ✅ | ❌ | ❌ |  |
| ミストフィールド | ドラゴン梗0.5倍 | ON_CALC_POWER_MODIFIER | ミストフィールド_power_modifier | ✅ | ✅ | ❌ | test_field.py |
| ミストフィールド | 状態異常無効 | ON_BEFORE_APPLY_AILMENT | ミストフィールド_prevent_ailment | ✅ | ❌ | ❌ |  |
| ミストフィールド | こんらん無効 | ON_BEFORE_APPLY_VOLATILE | ミストフィールド_prevent_volatile | ✅ | ❌ | ❌ |  |

## グローバルフィールドハンドラ

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| じゅうりょく | 命中率5/3倍 | ON_CALC_ACCURACY | じゅうりょく_accuracy | ✅ | ❌ | ❌ |  |
| じゅうりょく | 全て地面に接地 | ON_CHECK_FLOATING | じゅうりょく_grounded | ✅ | ❌ | ❌ |  |
| トリックルーム | 素早さ反転 | ON_CALC_ACTION_SPEED | トリックルーム_reverse_speed | ✅ | ❌ | ❌ |  |

## サイドフィールドハンドラ

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| リフレクター | 物理技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | リフレクター_reduce_damage | ✅ | ✅ | ❌ | test_field.py |
| ひかりのかべ | 特殊技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | ひかりのかべ_reduce_damage | ✅ | ✅ | ❌ | test_field.py |
| しんぴのまもり | 状態異常無効 | ON_BEFORE_APPLY_AILMENT | しんぴのまもり_prevent_ailment | ✅ | ✅ | ❌ | test_field.py |
| しろいきり | 能力ランク低下防止 | ON_BEFORE_MODIFY_STAT | しろいきり_prevent_stat_drop | ✅ | ✅ | ❌ | test_field.py |
| おいかぜ | 素早さ2倍 | ON_CALC_SPEED | おいかぜ_speed_boost | ✅ | ✅ | ❌ | test_field.py |
| ねがいごと | 次ターン終了時HP回復 | ON_TURN_END_3 | ねがいごと_heal | ✅ | ✅ | ❌ | test_field.py |
| まきびし | 出場時にダメージ | ON_SWITCH_IN | まきびし_damage | ✅ | ✅ | ❌ | test_field.py |
| どくびし | 出場時に毒付与 | ON_SWITCH_IN | どくびし_poison | ✅ | ✅ | ❌ | test_field.py |
| ステルスロック | 出場時に岩弱点ダメージ | ON_SWITCH_IN | ステルスロック_damage | ✅ | ✅ | ❌ | test_field.py |
| ねばねばネット | 出場時に素早さ-1 | ON_SWITCH_IN | ねばねばネット_speed_drop | ✅ | ✅ | ❌ | test_field.py |
| オーロラベール | 物理・特殊技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | オーロラベール_reduce_damage | ✅ | ✅ | ❌ | test_field.py |
