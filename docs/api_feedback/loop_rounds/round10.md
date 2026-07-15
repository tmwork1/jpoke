# 第10ラウンド（apiループ）

[← 目次に戻る](../README.md)

- [x] アイテム操作系API（`gain_item`/`remove_item`/`set_item`/`take_item`/`consume_item`/
  `swap_items`）が`examples/`にも`docs/api/README.md`にも一度も登場しない（id: r10-1）
  → 対応内容 (2026-07-15): `src/jpoke/core/battle.py`には6メソッドが揃っており
  （`ItemManager`への薄い委譲、docstringもr5-3で統一済み）実装自体に問題は無かったが、
  状態異常・揮発性状態・天候・地形にはそれぞれ`set_ailment`/`set_volatile`/`set_weather`/
  `set_terrain`用のサンプルと`docs/api/README.md`「シナリオ構築系」表の掲載があるのに、
  持ち物操作系だけ丸ごと欠落していた。`docs/api/README.md`「シナリオ構築系」表に6メソッドを
  追記し、コード例に`gain_item`/`set_item`/`remove_item`の3行を追加した。あわせて
  `examples/03_damage_calc/12_item_manipulation.py`を新設し、6メソッドを技を介さず単体で
  動かして成功/失敗条件の違い（`gain_item`は持ち物なしが前提、`take_item`は
  `target`＝奪われる側・相手（foe）が持ち物なしの場合のみ成功、`swap_items`は
  `take_item`と異なり双方が持ち物を持っていても実行できる、等）を確認できるサンプルにした。
  `examples/README.md`の一覧表にも1行追加した。`src/jpoke`の実装コード自体の変更は無い。
  `PYTHONUTF8=1 python examples/03_damage_calc/12_item_manipulation.py`を実行し、
  各メソッドの戻り値・持ち物の変化・`last_lost_item_name`・`ate_berry`の出力が
  docstring・コメントの説明と一致することを確認した。`tests/test_examples_smoke.py`は
  `examples/**/*.py`を自動収集するため新規サンプルも自動でスモーク対象になり、
  `python -m pytest tests/ -v`で全件パスを確認した。
- [x] `Battle.swap_items()`が`ItemManager.swap_items()`の`source`引数を落としており、
  公開APIだけでは「すりかえ」相当の挙動を再現できない（id: r10-2）
  → 対応内容 (2026-07-15): `Battle.swap_items()`に`source: Pokemon | None = None`引数を
  追加し`ItemManager.swap_items()`へそのまま委譲するようにした（既定値`None`のため既存
  呼び出しの挙動は変わらない）。`docs/api/README.md`「シナリオ構築系」表と`CHANGELOG.md`を
  更新した。`handlers/move_status.py`内部の「すりかえ」実装は既存慣習（内部ハンドラは
  `battle.item_manager.<method>()`を直接呼ぶ）に合わせ意図的に変更していない。
  `tests/abilities/test_ability_na.py`に`battle.swap_items(source=...)`を使った回帰テストを
  2件追加し、`source`に対象自身を渡した場合は自分のねんちゃくが無視されて交換が成立すること、
  `source`に対象以外（交換元となった相手側）を渡した場合はねんちゃくによる交換阻止が
  通常どおり機能することを確認した。`python -m pytest tests/ -v`で全件パスを確認した。
