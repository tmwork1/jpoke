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
- [x] `build_observation()`が実戦の全ターンで対戦履歴を毎回まるごと`deepcopy`し、r7-8で導入済みの
  `copy_logs=False`最適化の恩恵を受けていない（id: r10-5）
  → 対応内容 (2026-07-15): `src/jpoke/core/observation_builder.py`の`build(battle, observer,
  copy_logs: bool = True)`に引数を追加し、`Battle.copy()`と同じ「複製元の`event_logger`/
  `command_log`を一時的に空へ差し替えてから`deepcopy`し、完了後直ちに`finally`で復元する」方式を
  再利用した。`src/jpoke/core/battle.py`の`Battle.build_observation(observer, copy_logs: bool =
  True)`にも引数を追加して`observation_builder.build()`へ委譲し、`is_observation()`が真の分岐
  （`self.copy(...)`を呼ぶ経路）にも`copy_logs`を伝播させた。`command_manager.py`/
  `turn_controller.py`の`build_observation()`呼び出し元は意図的に変更していない
  （方策実装の`choose_command()`/`choose_selection()`がログを参照するかどうかを汎用の呼び出し
  経路からは判断できないため、既定`True`を維持し安全側に倒した）。`TreeSearchPlayer`は元々
  `battle.copy(reseed=True, copy_logs=False)`を直接使っており`build_observation()`経由ではない
  ため変更不要。`docs/api/README.md`「対戦進行系」表の`build_observation`行と`CHANGELOG.md`を
  更新した。`tests/test_observation.py`に`test_copy.py`と同じ命名・検証パターンで回帰テストを
  4件追加し、(1) `copy_logs=False`指定時に複製先の`event_logger.logs`/`command_log`が空になり
  かつ複製元と別オブジェクトであること、(2) `copy_logs=False`後も複製元のログ内容が変わらず
  複製先への書き込みが複製元へ波及しないこと、(3) `copy_logs`省略時（既定`True`）は従来通り
  全履歴が引き継がれること、(4) 既に`is_observation()`が真の盤面（観測用コピー済みの`Battle`）
  に対して`build_observation()`を呼んだ場合も`self.copy(copy_logs=copy_logs)`経由で`copy_logs`
  が正しく伝播すること、を確認した。`python -m pytest tests/ -v`で全件パス（5950 passed, 1
  skipped）を確認した。
- [x] 全examplesファイル冒頭の`from __future__ import annotations`が一度も説明されておらず、
  ポケモンには詳しいPython初心者が「これは消してよいのか、必須なのか」を判断できない
  （id: r10-6）
  → 対応内容 (2026-07-15): `examples/`配下30ファイル全てが`from __future__ import
  annotations`をモジュールdocstring直後の最初の文として持っており（構文上docstring以外の
  文より前に置く必要があるPythonの制約に従う位置）、既存コード自体に問題は無かったが、
  この1行が何のためにあるか・削除してよいかを説明する記述が`examples/README.md`にも
  `docs/api/README.md`にも存在しなかった。`examples/README.md`冒頭に「型アノテーションの
  前方参照を有効にするためのおまじないで、動作に必要なので消さずにそのまま残してよい」旨を
  3行追加した。`src/jpoke`の実装コード・examplesファイル自体の変更は無い（ドキュメントのみの
  変更）。再発防止のため`tests/test_code_conventions.py`に
  `test_examplesが全ファイルでfrom_future_import_annotationsを冒頭に持つ`を追加し、
  `examples/`配下の全`*.py`が（モジュールdocstringがあればその直後の）最初の文として
  `from __future__ import annotations`を持つことをast経由で機械的に検査するようにした。
  `python -m pytest tests/ -v`で全件パス（5953 passed, 1 skipped）を確認した。
- [x] README「型アノテーションは Python 3.10+ の構文を使用する」の一文が`pip install`直後に
  脈絡なく置かれており、ポケモンには詳しいPython初心者にとって「jpoke を使う上で自分が
  何をすべき指示なのか」が読み取れない（id: r10-7）
  → 対応内容 (2026-07-15): `README.md`の該当文（`requires-python = ">=3.10"`。型アノテーション
  は Python 3.10+ の構文（`X | Y`, `list[X]`）を使用する。）に続けて
  「（関数の引数・戻り値の型を書く目印であり、jpoke を利用するだけなら読み飛ばしてよい）。」を
  追記し、この一文が実行時に必須の設定ではなく開発者向けの補足情報であることを明示した。
  ドキュメントのみの変更で`src/jpoke`・`examples/`のコード変更は無い。挙動変更が無いため
  回帰テストの追加は不要と判断した。`python -m pytest tests/ -v`で全件パス（5953 passed,
  1 skipped）を確認した。
- [x] README「モンキーパッチ」という用語が未解説のまま使われている（id: r10-8）
  → 対応内容 (2026-07-15): `README.md`「テストヘルパーを使った検証」節の
  `fix_damage`/`fix_random`の説明文（「対戦オブジェクトの内部属性を直接差し替えるモンキー
  パッチのため、テスト・デバッグ専用であり本番の対戦進行では使わないこと。」）は元々
  「内部属性を直接差し替える」という言い換えを伴っていたが、それだけでは「モンキー
  パッチ」という一般的なプログラミング用語を知らないポケモンには詳しいPython初心者に
  とって、具体的に何が起こり得るのかまでは読み取れなかった。続けて「（本来の実装を
  無視して値を強制的に上書きするため、通常のゲームルールでは起こらない状態になり得る）」
  を追記し、r10-7と同じ「用語の直後に括弧書きで実務上の意味・注意点を補足する」文体に
  揃えた。`docs/api/README.md`側（`fix_damage()`/`fix_random()`の節、表内の「デバッグ専用
  モンキーパッチ」表記）は同じ`fix_damage`/`fix_random`について既に「デバッグ用の
  ユーティリティであり、本番の対戦進行（bot 運用等）では使わないこと」という説明があり
  今回の指摘（README.md）の対象外のため変更していない。ドキュメントのみの変更で
  `src/jpoke`・`examples/`のコード変更は無く挙動変更も無いため、回帰テストの追加は不要と
  判断した。`python -m pytest tests/ -v`で全件パス（5953 passed, 1 skipped）を確認した。
- [x] `examples/05_benchmark/01_step_time_benchmark.py`が`player.team`への直接代入で
  `add_pokemon()`規約から外れている（id: r10-9）
  → 対応内容 (2026-07-15): `run_benchmark()`内の`player1.team = build_random_team(...)`/
  `player2.team = build_random_team(...)`は、`build_random_pokemon()`が種族・性別・性格・
  レベル・特性・持ち物・技などすべてをその場で乱数生成して`Pokemon`インスタンスを組み立てる
  ため、「種族名を渡して`Player`側に構築させる」`add_pokemon(name, ...)`の名前渡し
  インターフェースでは表現できないという理由によるものだった。理由が自明でなく初心者が
  規約違反と誤解しかねないため、直前に「`build_random_pokemon()`は種族・技構成をその場で
  ランダム生成するため、名前を渡して構築する`add_pokemon()`では表現できず、`team`へ直接
  代入する」旨の1行コメントを追加した。挙動変更は無い（コメント追加のみ）。
  `PYTHONIOENCODING=utf-8 python examples/05_benchmark/01_step_time_benchmark.py --n-battles 5
  --max-turns 20 --seed 42`を修正前後で実行し、`perf_counter`計測値そのもの以外
  （バトル数・stepサンプル数・seed）が完全一致することを確認した。コメントのみの変更で
  挙動変更が無いため回帰テストの追加は不要と判断した。`python -m pytest tests/ -v`で全件
  パス（5953 passed, 1 skipped）を確認した。これで第10ラウンドの9件すべてが対応済みになった。
