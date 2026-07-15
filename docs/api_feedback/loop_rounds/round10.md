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
- [x] `examples/02_ai/05_opponent_estimation.py`が`battle.player_states[opponent].active`
  という未文書化の内部属性に直接アクセスする書き方に逆戻りしていた（id: r10-3）
  → 対応内容 (2026-07-15): `examples/02_ai/05_opponent_estimation.py:24`を
  `battle.get_active(opponent)`に置き換えた（挙動は同一、公開API変更なし）。`get_active()`は
  既に`docs/api/README.md`「シナリオ構築系」表に掲載済みのため、ドキュメント側の追記は不要と
  判断した。再発防止のため`tests/test_code_conventions.py`に
  `test_examplesがplayer_states経由で内部属性に直接アクセスしていない`を追加し、
  `examples/`配下に`player_states[`の使用が無いことを機械的に検査するようにした。
  `PYTHONUTF8=1 python examples/02_ai/05_opponent_estimation.py`を実行し修正前と同じ出力
  （1ターン目のノード数8、以降のログ）になることを確認したうえで、
  `python -m pytest tests/ -v`で全件パスを確認した。なお`battle.get_active()`は型注釈上
  `Pokemon | None`だが実装は`active_index`が`None`の場合に`None`を返さず`ValueError`を
  送出する既存の不一致があり、これは今回の修正対象外として次ラウンド以降のfinding候補に
  留める。
- [x] `examples/03_damage_calc/10_testing_helpers.py:25-26`が`battle.actives[0]`/
  `battle.actives[1]`という未文書化の内部プロパティに直接アクセスする書き方を使っていた
  （id: r10-4）
  → 対応内容 (2026-07-15): `battle.actives`（`src/jpoke/core/battle.py`の`@property`）は
  「現在場に出ているポケモンのリスト」を返すが、瀕死・交代中で場が空いているプレイヤーが
  いると要素がその分詰まってリストの長さが2未満になり得るため、`battle.actives[0]`/`[1]`は
  プレイヤーとインデックスの対応が崩れる危険な書き方であり、かつ`docs/api/README.md`にも
  一度も掲載されていなかった。`examples/03_damage_calc/10_testing_helpers.py`を
  `player0, player1 = battle.players`でPlayerインスタンスを取得したうえで
  `battle.get_active(player0)`/`battle.get_active(player1)`に置き換えた（挙動は同一、
  公開API変更なし）。`battle.players`（`Battle.__init__`で`self.players: tuple[Player,
  ...] = players`として公開されている参加プレイヤーのタプル）自体は
  `docs/api/README.md`のコンストラクタ引数説明には言及があったが、インスタンス属性としての
  「対戦進行系」表への掲載が漏れていたため1行追加した。再発防止のため
  `tests/test_code_conventions.py`に
  `test_examplesがactives経由でインデックスアクセスしていない`を追加し、
  `examples/`配下に`.actives[`の使用が無いことを機械的に検査するようにした。
  `PYTHONUTF8=1 python examples/03_damage_calc/10_testing_helpers.py`を実行し修正前と同じ
  出力（致死率・防御側の状態異常・HP変化のログ）になることを確認したうえで、
  `python -m pytest tests/ -v`で全件パスを確認した（実行中1回だけ
  `tests/moves_attack/test_move_sa.py`の確率検定テストが単発で失敗したが、今回の変更対象
  ファイルとは無関係で単独再実行・全体再実行とも再現せず、既存の確率的flakyテストと判断し
  今回の対応範囲には含めていない）。
