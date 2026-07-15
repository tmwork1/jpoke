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
