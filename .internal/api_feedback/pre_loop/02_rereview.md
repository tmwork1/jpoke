# 再レビュー指摘（2026-07-12 Fableサブエージェント、PR #38差分）

[← 目次に戻る](../README.md)

- [x] `tests/moves_attack/test_move_ha.py` の `test_はたきおとす_相手のアイテムがないとき威力補正なし` が同種のflakiness（急所のブレでダメージ比較が逆転しうる）を持つとMonte Carlo実測（300回中8回失敗）で指摘 → `fix_random()` を追加して解消
- [x] `Battle.roll_damage()` の `int(random() * len(damages))` が `random()==1.0` の境界（一部テストが `battle.random.random = lambda: 1.0` を使用）でIndexErrorになり得ると指摘 → `min(index, len(damages)-1)` のクランプを追加
- [x] `examples/README.md` の01の説明が `Pokemon` importなし化に追従していなかったと指摘 → 修正
- [x] `n_selected` 自動調整のdocstringに「チーム間で手持ち数が異なっても両者に同じ値が適用される」旨の追記が必要と指摘 → 追記
- [x] `battle_against` のdocstringに「複数opponent指定時は対戦通番がopponentごとにリセットされ、同じseed系列を使い回す」旨の追記が必要と指摘 → 追記
- [x] （付随発見・スコープ外）`tests/abilities/test_ability_a.py:667`（いかりのつぼ）で `random()==1.0` 固定時に技自体がミスして意図せず空虚に合格する既存の問題を発見 → 今回の変更が原因ではなく、examples APIフィードバック対応のスコープ外のため見送り確定


### 実施記録

### 2026-07-12 再レビュー対応

PR #38 の差分に対して再度Fableモデルでレビューを受け、上記「再レビュー指摘」の内容を修正した。

