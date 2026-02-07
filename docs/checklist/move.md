# Move ハンドラ実装チェックリスト

- ✅: 実装済み
- ⚠️: 部分的に実装
- ❌: 未実装

## チェックリスト

| 名前 | 効果 | イベント | ハンドラ名 | 実装 | テスト | ユーザー確認 | 備考 |
|------|------|---------|-----------|----------|----------|--------------|------|
| PP消費 | PP消費を処理 | ON_CONSUME_PP | consume_pp | ✅ | ❌ | ❌ |  |
| とんぼがえり | 攻撃後に交代 | ON_HIT | pivot | ✅ | ✅ | ❌ | test_move.py |
| ボルトチェンジ | 攻撃後に交代 | ON_HIT | pivot | ❌ | ✅ | ❌ | MoveData未登録; test_move.py要確認 |
| クイックターン | 攻撃後に交代 | ON_HIT | pivot | ❌ | ❌ | ❌ | MoveData未登録 |
| すてゼリフ | 攻撃後に交代 | ON_HIT | pivot | ❌ | ❌ | ❌ | MoveData未登録 |
| ほえる | 相手を強制交代 | ON_HIT | blow | ❌ | ❌ | ❌ | MoveData未登録 |
| ふきとばし | 相手を強制交代 | ON_HIT | blow | ✅ | ❌ | ❌ |  |
| ドラゴンテール | 相手を強制交代 | ON_HIT | blow | ❌ | ❌ | ❌ | MoveData未登録 |
| ともえなげ | 相手を強制交代 | ON_HIT | blow | ❌ | ❌ | ❌ | MoveData未登録 |
| アクロバット | 持ち物なしで威力2倍 | ON_CALC_POWER_MODIFIER | acrobatics | ❌ | ❌ | ❌ | 未実装 |
| からげんき | 状態異常時に威力2倍 | ON_CALC_POWER_MODIFIER | from_rage | ❌ | ❌ | ❌ | 未実装 |
| うっぷんばらし | 同一ターン技を受けると威力2倍 | ON_CALC_POWER_MODIFIER | upset | ❌ | ❌ | ❌ | 未実装 |
| しっぺがえし | 後攻時に威力2倍 | ON_CALC_POWER_MODIFIER | payback | ❌ | ❌ | ❌ | 未実装 |
| ダメおし | 前ターンダメージ対象に威力2倍 | ON_CALC_POWER_MODIFIER | assurance | ❌ | ❌ | ❌ | 未実装 |
| かみなり | 雨で必中/晴れで50% | ON_CALC_ACCURACY | かみなり_accuracy | ✅ | ❌ | ❌ |  |
| ぼうふう | 雨で必中/晴れで50% | ON_CALC_ACCURACY | ぼうふう_accuracy | ✅ | ❌ | ❌ |  |
| ふぶき | 雪で必中 | ON_CALC_ACCURACY | ふぶき_accuracy | ✅ | ❌ | ❌ |  |

## 備考
- upset（うっぷんばらし）: 同一ターンに技を受けたかのコンテキスト情報が必要
- payback（しっぺがえし）: 攻撃順序の情報に基づく判定が必要
- assurance（ダメおし）: 前ターン以降のダメージ履歴トラッキングが必要
