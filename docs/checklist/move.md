# Move ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## チェックリスト

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| PP消費 | PP消費を処理 | ON_BEFORE_EXECUTE | consume_pp | ✅ | ❌ | ❌ |  |
| とんぼがえり | 攻撃後に交代 | ON_HIT | pivot | ✅ | ✅ | ❌ | test_move.py |
| ボルトチェンジ | 攻撃後に交代 | ON_HIT | pivot | ✅ | ✅ | ❌ | test_move.py |
| クイックターン | 攻撃後に交代 | ON_HIT | pivot | ✅ | ❌ | ❌ |  |
| すてゼリフ | 攻撃後に交代 | ON_HIT | pivot | ✅ | ❌ | ❌ |  |
| ほえる | 相手を強制交代 | ON_HIT | blow | ✅ | ❌ | ❌ |  |
| ふきとばし | 相手を強制交代 | ON_HIT | blow | ✅ | ❌ | ❌ |  |
| ドラゴンテール | 相手を強制交代 | ON_HIT | blow | ✅ | ❌ | ❌ |  |
| ともえなげ | 相手を強制交代 | ON_HIT | blow | ✅ | ❌ | ❌ |  |
| アクロバット | 持ち物なしで威力2倍 | ON_CALC_POWER_MODIFIER | acrobatics | ✅ | ❌ | ❌ |  |
| からげんき | 状態異常時に威力2倍 | ON_CALC_POWER_MODIFIER | from_rage | ✅ | ❌ | ❌ |  |
| うっぷんばらし | 同一ターン技を受けると威力2倍 | ON_CALC_POWER_MODIFIER | upset | ⚠️ | ❌ | ❌ | TODO: 同一ターン被弾情報 |
| しっぺがえし | 後攻時に威力2倍 | ON_CALC_POWER_MODIFIER | payback | ⚠️ | ❌ | ❌ | TODO: 攻撃順序の判定 |
| ダメおし | 前ターンダメージ対象に威力2倍 | ON_CALC_POWER_MODIFIER | assurance | ⚠️ | ❌ | ❌ | TODO: ダメージ履歴 |

## 備考
- upset（うっぷんばらし）: 同一ターンに技を受けたかのコンテキスト情報が必要
- payback（しっぺがえし）: 攻撃順序の情報に基づく判定が必要
- assurance（ダメおし）: 前ターン以降のダメージ履歴トラッキングが必要
