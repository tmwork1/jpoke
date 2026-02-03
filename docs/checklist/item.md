# Item ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## コア効果

| 名前 | 効果 | イベント | ハンドラ名 | 処理 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| いのちのたま | 攻撃技で1/8反動ダメージ | ON_HIT | いのちのたま | ✅ | ❌ | ❌ |  |
| だっしゅつボタン | ダメージ時に強制交代 | ON_DAMAGE | だっしゅつボタン | ✅ | ❌ | ❌ |  |
| だっしゅつパック | 能力ダウン時に自動交代 | ON_MODIFY_STAT | だっしゅつパック | ✅ | ❌ | ❌ |  |
| ちからのハチマキ | 物理技1.1倍 | ON_CALC_POWER_MODIFIER | ちからのハチマキ | ✅ | ❌ | ❌ |  |
| ものしりメガネ | 特殊技1.1倍 | ON_CALC_POWER_MODIFIER | ものしりメガネ | ✅ | ❌ | ❌ |  |
| シルクのスカーフ | ノーマル技1.2倍 | ON_CALC_POWER_MODIFIER | シルクのスカーフ | ✅ | ❌ | ❌ |  |
| つめたいいわ | 未実装 | ON_CALC_POWER_MODIFIER | つめたいいわ | ❌ | ❌ | ❌ | return False のみ |
| もくたん | 炎技1.2倍 | ON_CALC_POWER_MODIFIER | もくたん | ✅ | ❌ | ❌ |  |
| ぎんのこな | 未実装 | ON_CALC_POWER_MODIFIER | ぎんのこな | ❌ | ❌ | ❌ | return False のみ |

## 木の実

| 名前 | 効果 | イベント | ハンドラ名 | 処理 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| オボンのみ | HP50%以下で25%回復 | ON_BEFORE_ACTION | オボンのみ | ❌ | ❌ | ❌ | return False のみ |
| クラボのみ | まひ状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| カゴのみ | ねむり状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| モモンのみ | どく状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| チーゴのみ | やけど状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| ナナシのみ | こおり状態時に治す | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
| キーのみ | こんらん状態時に治す | ON_BEFORE_ACTION | キーのみ | ❌ | ❌ | ❌ | return False のみ |
| ヒメリのみ | 未実装 | ON_BEFORE_ACTION | ヒメリのみ | ❌ | ❌ | ❌ | return False のみ |
| オレンのみ | 未実装 | ON_BEFORE_ACTION | オレンのみ | ❌ | ❌ | ❌ | return False のみ |
| ひかりごけ | 未実装 | ON_BEFORE_ACTION | ひかりごけ | ❌ | ❌ | ❌ | return False のみ |
| きゅうこん | 未実装 | ON_BEFORE_ACTION | きゅうこん | ❌ | ❌ | ❌ | return False のみ |
| ラムのみ | 全状態異常回復 | ON_BEFORE_ACTION | common.cure_ailment | ✅ | ❌ | ❌ |  |
