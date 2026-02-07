# Item ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## コア効果

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| いのちのたま | 攻撃技で1/8反動ダメージ | ON_HIT | いのちのたま | ✅ | ✅ | ❌ | test_item.py |
| だっしゅつボタン | ダメージ時に強制交代 | ON_DAMAGE_1 | だっしゅつボタン | ✅ | ✅ | ❌ | test_item.py |
| だっしゅつパック | 能力ダウン時に自動交代 | ON_MODIFY_STAT | だっしゅつパック | ✅ | ✅ | ❌ | test_item.py |
| ちからのハチマキ | 物理技1.1倍 | ON_CALC_POWER_MODIFIER | ちからのハチマキ | ✅ | ❌ | ❌ |  |
| ものしりメガネ | 特殊技1.1倍 | ON_CALC_POWER_MODIFIER | ものしりメガネ | ✅ | ❌ | ❌ |  |
| シルクのスカーフ | ノーマル技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| つめたいいわ | 未実装 | ON_CHECK_DURATION | つめたいいわ | ❌ | ❌ | ❌ | handler未登録 |
| もくたん | 炎技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| ぎんのこな | むし技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |

## タイプ強化アイテム

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| かたいいし | いわ技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| きせきのたね | くさ技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| くろおび | あく技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| じしゃく | でんき技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| しんぴのしずく | みず技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| するどいくちばし | ひこう技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| せいれいプレート | フェアリー技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| どくバリ | どく技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| とけないこおり | こおり技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| ノーマルジュエル | ノーマル技1.5倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| のろいのおふだ | ゴースト技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| まがったスプーン | エスパー技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| メタルコート | はがね技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| やわらかいすな | じめん技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| ようせいのハネ | フェアリー技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |
| りゅうのキバ | ドラゴン技1.2倍 | ON_CALC_POWER_MODIFIER | modify_power_by_type | ✅ | ✅ | ❌ | test_item.py |

## 木の実

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| オボンのみ | HP50%以下で25%回復 | ON_BEFORE_ACTION | オボンのみ | ❌ | ❌ | ❌ | 未実装 |
| クラボのみ | まひ状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| カゴのみ | ねむり状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| モモンのみ | どく状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| チーゴのみ | やけど状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| ナナシのみ | こおり状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| キーのみ | こんらん状態時に治す | ON_BEFORE_ACTION | キーのみ | ❌ | ❌ | ❌ | 未実装 |
| ヒメリのみ | 未実装 | ON_BEFORE_ACTION | ヒメリのみ | ❌ | ❌ | ❌ | 未実装 |
| オレンのみ | 未実装 | ON_BEFORE_ACTION | オレンのみ | ❌ | ❌ | ❌ | 未実装 |
| ひかりごけ | 未実装 | ON_BEFORE_ACTION | ひかりごけ | ❌ | ❌ | ❌ | 未実装 |
| きゅうこん | 未実装 | ON_BEFORE_ACTION | きゅうこん | ❌ | ❌ | ❌ | 未実装 |
| ラムのみ | 全状態異常回復 | ON_BEFORE_ACTION | ラムのみ | ❌ | ❌ | ❌ | handler未登録 |

## タイプ半減実

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| ホズのみ | ノーマル技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| リンドのみ | くさ技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| オッカのみ | ほのお技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| イトケのみ | みず技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ソクノのみ | でんき技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| カシブのみ | ゴースト技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ヨロギのみ | いわ技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| タンガのみ | むし技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ウタンのみ | エスパー技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| バコウのみ | ひこう技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| シュカのみ | じめん技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ビアーのみ | どく技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ヨプのみ | かくとう技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ヤチェのみ | こおり技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| リリバのみ | はがね技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ナモのみ | あく技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ハバンのみ | ドラゴン技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
| ロゼルのみ | フェアリー技ダメージ0.5倍 | ON_CALC_DAMAGE_MODIFIER | modify_super_effective_damage | ✅ | ✅ | ❌ | test_item.py |
