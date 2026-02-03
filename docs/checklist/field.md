# Field ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## 天候（Weather）ハンドラ

| 名前 | 効果 | イベント | ハンドラ名 | 処理実装 | テスト実装 | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| はれ | 炎技1.5倍、水技0.5倍 | ON_CALC_POWER_MODIFIER | はれ_power_modifier | ✅ | ❌ | ❌ |  |
| はれ | かみなり・ぼうふう50%に低下 | ON_CALC_ACCURACY | はれ_accuracy | ✅ | ❌ | ❌ |  |
| あめ | 水技1.5倍、炎技0.5倍 | ON_CALC_POWER_MODIFIER | あめ_power_modifier | ✅ | ❌ | ❌ |  |
| あめ | かみなり・ぼうふう必中化 | ON_CALC_ACCURACY | あめ_accuracy | ✅ | ❌ | ❌ |  |
| すなあらし | 1/16ダメージ | ON_TURN_END | すなあらし_damage | ✅ | ❌ | ❌ |  |
| すなあらし | いわタイプ特防1.5倍 | ON_CALC_SPDEF | すなあらし_spdef_boost | ✅ | ❌ | ❌ |  |
| ゆき | こおりタイプ防御1.5倍 | ON_CALC_DEF | ゆき_def_boost | ✅ | ❌ | ❌ |  |
| ゆき | ふぶき必中化 | ON_CALC_ACCURACY | ゆき_accuracy | ✅ | ❌ | ❌ |  |

## 地形（Terrain）ハンドラ

| 名前 | 効果 | イベント | ハンドラ名 | 処理実装 | テスト実装 | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| エレキフィールド | 電気技1.3倍 | ON_CALC_POWER_MODIFIER | エレキフィールド_power_modifier | ✅ | ❌ | ❌ |  |
| エレキフィールド | ねむり無効 | ON_BEFORE_APPLY_AILMENT | エレキフィールド_prevent_sleep | ✅ | ❌ | ❌ |  |
| エレキフィールド | 出場時のねむり回復 | ON_SWITCH_IN | エレキフィールド_cure_sleep | ✅ | ❌ | ❌ |  |
| グラスフィールド | 草技1.3倍 | ON_CALC_POWER_MODIFIER | グラスフィールド_power_modifier | ✅ | ❌ | ❌ |  |
| グラスフィールド | ターン終了時1/16回復 | ON_TURN_END | グラスフィールド_heal | ✅ | ❌ | ❌ |  |
| サイコフィールド | エスパー技1.3倍 | ON_CALC_POWER_MODIFIER | サイコフィールド_power_modifier | ✅ | ❌ | ❌ |  |
| サイコフィールド | 先制技無効 | ON_CHECK_PRIORITY | サイコフィールド_block_priority | ✅ | ❌ | ❌ |  |
| ミストフィールド | ドラゴン技0.5倍 | ON_CALC_POWER_MODIFIER | ミストフィールド_power_modifier | ✅ | ❌ | ❌ |  |
| ミストフィールド | 状態異常無効 | ON_BEFORE_APPLY_AILMENT | ミストフィールド_prイベント_ailment | ✅ | ❌ | ❌ |  |

## グローバルフィールドハンドラ

| 名前 | 効果 | イベント | ハンドラ名 | 処理実装 | テスト実装 | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| じゅうりょく | 命中率5/3倍 | ON_CALC_ACCURACY | じゅうりょく_accuracy | ✅ | ❌ | ❌ |  |
| じゅうりょく | 全て地面に接地 | ON_CHECK_GROUNDED | じゅうりょく_grounded | ✅ | ❌ | ❌ |  |
| トリックルーム | 素早さ反転 | ON_CALC_SPEED | トリックルーム_reverse_speed | ✅ | ❌ | ❌ |  |

## サイドフィールドハンドラ

| 名前 | 効果 | イベント | ハンドラ名 | 処理実装 | テスト実装 | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| リフレクター | 物理技ダメージ0.5倍 | ON_CALC_DAMAGE | リフレクター_reduce_damage | ✅ | ❌ | ❌ |  |
| ひかりのかべ | 特殊技ダメージ0.5倍 | ON_CALC_DAMAGE | ひかりのかべ_reduce_damage | ✅ | ❌ | ❌ |  |
| しんぴのまもり | 状態異常無効 | ON_BEFORE_APPLY_AILMENT | しんぴのまもり_prイベント_ailment | ✅ | ❌ | ❌ |  |
| おいかぜ | 素早さ2倍 | ON_CALC_SPEED | おいかぜ_speed_boost | ✅ | ❌ | ❌ |  |
| まきびし | 出場時にダメージ | ON_SWITCH_IN | まきびし_damage | ✅ | ❌ | ❌ |  |
| どくびし | 出場時に毒付与 | ON_SWITCH_IN | どくびし_poison | ✅ | ❌ | ❌ |  |
| ステルスロック | 出場時に岩弱点ダメージ | ON_SWITCH_IN | ステルスロック_damage | ✅ | ❌ | ❌ |  |
| ねばねばネット | 出場時に素早さ-1 | ON_SWITCH_IN | ねばねばネット_speed_drop | ✅ | ❌ | ❌ |  |
