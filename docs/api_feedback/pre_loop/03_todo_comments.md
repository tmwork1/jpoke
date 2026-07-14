# 3度目のレビュー指摘（2026-07-12、ユーザー記入のexamples内TODOコメント + Fableサブエージェント）

[← 目次に戻る](../README.md)

ユーザーが教材執筆中に気づいた疑問を `examples/*.py` に直接 `# TODO:` コメントとして書き込んだため、
それをFableサブエージェントにレビューさせ、自身でも実装コードを確認して裏付けを取った。

- [x] `Battle.finished`（`battle.py:868`、poke-env互換プロパティ）は `self.winner is not None` を見るだけで、
  `self.winner` は `judge_winner()` 内でのみ遅延設定・キャッシュされる（`battle.py:171` で初期値 `None`）。
  そのため **`judge_winner()` を一度も呼ばずに `battle.finished` だけを見ると、TODスコアにより実際には
  決着している対戦でも `False` が返り続ける**という潜在バグがある（Fableの指摘を検証し、単なる
  「頑健化した方がよい」ではなく実際の不整合と確認）。`return self.judge_winner() is not None` に
  変更して解消する
  → 対応内容 (2026-07-12): `Battle.finished` を `return self.judge_winner() is not None` に変更した
- [x] 01/03/05で「`battle.start()` → `while judge_winner() is None and turn < N: battle.step()`」という
  ほぼ同一の定型ループが繰り返されている（01 L22/L23/L29の根本原因はこれ）。`Battle.play_out(max_turns=100)
  -> Player | None` のような、最後まで進めて勝者を返す便宜メソッドを追加する。`Player.battle_against()`
  内部ループもこれに置き換えられる。01は「手動でstep()する」ことを学ぶ教材のため、ループ自体は残しつつ
  `battle.finished` を使う形に簡素化する（`play_out()` の存在は末尾コメント等で軽く触れる程度に留める）
  → 対応内容 (2026-07-12): `Battle.play_out(max_turns=100) -> Player | None` を新設し、
  `Player.battle_against()` の内部ループを置き換えた。01/03/05は `while battle.judge_winner() is None`
  を `while not battle.finished` に変更（01はループ自体は維持し、末尾に `play_out()` へのコメントを追加）
- [x] 02の「ループ条件で `judge_winner() is None` を見た直後、ループを抜けてから再度 `judge_winner()` を
  呼ぶ」二重呼び出し（L38）は、`battle.finished` / `battle.winner` を使えば1回の呼び出しで済み解消する
  （上記2項目とセットで対応）
  → 対応内容 (2026-07-12): ループ条件を `not battle.finished` に、ループ後の `judge_winner()` 再呼び出しを
  `battle.winner` 参照に変更し、該当TODOコメントを削除した
- [x] `battle.print_logs(turn)` / `get_log_lines(turn)` は指定ターン（省略時は現在ターン）のみを返すため、
  01で「決着までの全ターンのログを見たい」（L37）にはユーザー側でforループが必要になる。
  `turn: int | None | Literal["all"]` を受け付け、`"all"` で1ターン目〜現在ターンを一括出力できるようにする
  （既存の `None`＝現在ターンの意味は変更しない。02のターンごと出力は非破壊）
  → 対応内容 (2026-07-12): `get_log_lines`/`print_logs` の `turn` を `int | None | Literal["all"]` に拡張し、
  `"all"` 指定時は1ターン目から現在ターンまでの全ログを返すようにした。01の `battle.print_logs()` を
  `battle.print_logs("all")` に変更し、該当TODOコメントを削除した
- [x] `Command` から技実体への到達（03 L25、`mon.moves[command.index]`）は、既に公開済みの
  `battle.command_to_move(player, command)` で解決できる。新規実装は不要で、
  `examples/03_custom_player.py` を書き換えるだけでよい（→ 上記「公開APIの使い勝手」節の訂正参照）
  → 対応内容 (2026-07-12): `examples/03_custom_player.py` の `mon.moves[command.index]` を
  `battle.command_to_move(self, command)` に書き換え（未使用になった `mon` 変数も削除）、該当TODOコメントを
  削除した。`Battle.command_to_move` のdocstringに用途（方策実装でコマンドから技を引く）を追記した
- [x] `Battle.calc_lethal`（`battle.py:352`）に **docstring が一切ない**（委譲先の `core/lethal.py:157`
  にはある）。戻り値 `list[LethalResult]` の構造（1要素=1ヒット、`hp_dist`はそのヒット適用後のHP分布、
  最終致死率は `results[-1].lethal_probability`）が呼び出し側から読み取れない（04 L38の指摘）。
  `Battle.calc_lethal` にdocstringを追加して解消する
  → 対応内容 (2026-07-12): `Battle.calc_lethal` に、戻り値の構造（1要素=1ヒット、`hp_dist` はそのヒット
  適用後のHP分布、最終致死率は `results[-1].lethal_probability`）を明記したdocstringを追加した
- [x] `calc_lethal(moves=...)` が `Move` インスタンスを要求し、`Move(move_name)` のラップが必要（04 L27）。
  `moves` の型を `MoveName | Move | tuple[MoveName | Move, int] | list[...]` に広げ、文字列なら内部で
  `Move(name)` に正規化する（既存呼び出しは非破壊）
  → 対応内容 (2026-07-12): `Battle.calc_lethal` / `core.lethal.calc_lethal` の `moves` 型を
  `MoveName | Move | tuple[MoveName | Move, int] | list[...]` に拡張し、文字列は内部で `Move(name)` に
  正規化するようにした（`Move` インスタンス渡しの既存挙動は非破壊）。`examples/04_damage_calculation.py` の
  `moves=Move(move_name)` を `moves=move_name` に変更し、未使用になった `Move` importと該当TODOコメントを
  削除した
- [x] `Battle.__init__(players: tuple[Player, ...], ...)` はタプルで渡す必要があり、`Battle((player1,
  player2), seed=1)` という二重括弧が初見で読みにくい（01 L21）。呼び出し箇所を全リポジトリ検索した結果
  位置引数でのタプル外の渡し方は存在せず、`Player.battle_against(*opponents, ...)` は既に可変長引数化
  されている。`Battle.__init__(self, *players: Player, n_selected=None, ...)` に変更し、
  `Battle(player1, player2, seed=1)` と書けるようにする（内部呼び出し・examples・scripts・testsの
  該当16ファイルを合わせて修正するため、破壊的変更としてCHANGELOGに明記する）
  → 対応内容 (2026-07-12): `Battle.__init__` を `*players: Player` の可変長引数に変更した。
  リポジトリ全体を再検索した結果、当初想定の16ファイルに加えて `Battle(players, ...)` /
  `Battle([p0, p1], ...)` / `Battle(tuple(players), ...)` のようにタプル/リストを事前に組み立てて
  渡す非明示的なパターンが `tests/test_utils.py`・`tests/test_fuzz_regressions.py`・
  `tests/test_replay_fuzz.py`・`src/jpoke/core/replay.py`・`scripts/random_1on1.py`・
  `scripts/fuzz_battle.py`・`scripts/replay_fuzz_battle.py`・`scripts/janken_nash.py` の8ファイルにも
  見つかり、全て `Battle(*players, ...)` 形式に修正した（合計24ファイルを修正）。
  破壊的変更として `CHANGELOG.md` の `### Changed` に明記した
- [x] 05の `KOFocusedPlayer("TreeSearchAI", max_plies=1, max_nodes=50)` は `max_plies` が変更可能な
  パラメータであることが伝わりにくい（L18）。API変更は不要で、行コメント（`max_plies=2にすると相手の
  応手まで読む。分岐は自手数×相手手数で乗算的に増える`、等）と「試してみよう」への追記で解消する
  → 対応内容 (2026-07-12): `KOFocusedPlayer(...)` 行の直前に `max_plies` の意味と増やした場合の
  分岐増加について行コメントを追加し、「試してみよう」に `max_plies` を変えて `nodes_expanded`
  （展開ノード数）の変化を比較する誘導を追記した。あわせて、同趣旨の解消済みTODOコメント
  （「ユーザーからは木探索の深さ設定が見えてこない。」）を削除した
- [x] 02のRandomPlayer化（L10）: 01は1体・1技構成で選択の余地がなくRandomPlayer化しても観測できる差が
  ないため見送り、最小構成のPlayerのまま維持する。02は3体チームで瀕死時の交代コマンドに複数の選択肢が
  あるため、両陣営をRandomPlayerにすると「瀕死→自動交代」のシナリオがより実戦的になる。examples限定の
  軽微な変更として対応する
  → 対応内容 (2026-07-12): `examples/02_team_battle.py` の Team A / Team B を `Player` から
  `jpoke.players.RandomPlayer` に変更し、`from jpoke import Battle, Player` の `Player` importを
  削除して `from jpoke.players import RandomPlayer` を追加した。docstringの
  「既定の `Player.choose_command()` は...」という記述を実態（両陣営とも RandomPlayer を使うため、
  交代コマンドの選択肢が複数あるときはランダムに選ばれる）に合わせて更新し、02側の解消済みTODO
  （「RandomPlayer を使う。」）を削除した。01は本項目の分析どおり変更せず、01側のTODOコメントも
  そのまま残した（見送り確定のため）
- [x] 技名のひらがな入力対応（02 L14、"ぎがどれいん"→"ギガドレイン"）は、`MoveName` Literalの拡張が
  技以外（ポケモン名・特性名・アイテム名）にも波及する広範な変更のため見送り確定。代替として
  `MOVES[name]` のKeyError時にdifflibで近い技名候補を提示するエラーメッセージ改善は費用対効果が
  見合うが優先度は低く、今回は見送り（気になれば別途着手）
- [x] `TreeSearchPlayer` を `MinimaxPlayer` に改名する案（05 L17）は、本クラスがミニマックスだけでなく
  `max_nodes`打ち切り・`fallback`・`opponent_estimator`・`configure_sim`を備えた探索フレームワーク基底
  であるため見送り確定。改名はscripts/tree_search/・tests・docsへの波及が大きく、実態（探索フレームワーク）
  ともTreeSearchの方が合っている
- [x] 01 L26 `# TODO: start()が` は文が途中で切れており意図不明で **ユーザーに確認が必要**としていたが、
  その後ユーザーが記入を完成させ「`# TODO: ユーザー視点だとstart()で何をしているのかわからない`」で
  確定した。`battle.start()` の呼び出し1行だけでは「選出と初期繰り出しを行う」ことが教材コードから
  読み取れない、という指摘。`Battle.start()` 自体のdocstringには既に説明があるため、examples/01側に
  コメントを1行添えるだけで解消できる（API変更は不要）
  → 対応内容 (2026-07-12): `examples/01_quickstart.py` の `battle.start()` 呼び出し行の直前に、
  `Battle.start()` のdocstringを踏まえた説明コメント（`# 選出と初期繰り出しを行い、対戦を開始する`）を
  追加し、該当TODOコメントを削除した


### 実施記録

### 2026-07-12 3度目のレビュー対応（一部）

「3度目のレビュー指摘」のうち、`Battle.finished`・`play_out()`・ループ簡素化・
`print_logs`/`get_log_lines`の`turn="all"`対応・`command_to_move()`活用・
`calc_lethal`のdocstring・`calc_lethal`の技名文字列対応の7項目に対応した
（`Battle.__init__`可変長引数化、05のmax_pliesコメント、02のRandomPlayer化、
01 L26の意図不明TODOはこのタスクの対象外として触れていない）。

- `Battle.finished` を `self.winner is not None` から `self.judge_winner() is not None`
  に変更。`judge_winner()`未呼び出しのままTODスコアで決着した対戦を見逃さないようにした
- `Battle.play_out(max_turns=100) -> Player | None` を新設し、
  `start()` → `while not battle.finished and battle.turn < N: battle.step()` という
  定型ループを1メソッドに集約。`Player.battle_against()` の内部ループをこれに置き換えた
- `examples/01_quickstart.py`: ループ条件を `not battle.finished` に、
  `winner = battle.judge_winner()` を `winner = battle.winner` に変更。手動`step()`を
  学ぶ教材のためループ自体は維持し、末尾に `play_out()` の存在を一言だけ添えるコメントを追加。
  `battle.print_logs()` を `battle.print_logs("all")` に変更。対応済みTODO
  （step()の戻り値をbool化する案、全ターンログ表示）を削除
- `examples/02_team_battle.py`: ループ条件を `not battle.finished` に変更し、
  ループ後の二重 `judge_winner()` 呼び出しを `battle.winner` 参照に変更。該当TODOコメントを削除
- `examples/05_tree_search_ai.py`: ループ条件を `not battle.finished` に変更
- `Battle.get_log_lines` / `Battle.print_logs` の `turn` を `int | None | Literal["all"]` に拡張。
  `"all"` 指定時は1ターン目から現在ターンまでの全ログをターン番号昇順で返す
  （既存の `None`＝現在ターンの挙動は変更なし）
- `examples/03_custom_player.py`: `mon.moves[command.index]` を
  `battle.command_to_move(self, command)` に書き換え（未使用になった `mon` 変数を削除）。
  該当TODOコメントを削除。`Battle.command_to_move` のdocstringに用途を一言追記
- `Battle.calc_lethal` に、戻り値 `list[LethalResult]` の構造
  （1要素=1ヒット、`hp_dist`はそのヒット適用後のHP分布、最終致死率は
  `results[-1].lethal_probability`）を明記したdocstringを追加
- `Battle.calc_lethal` / `core.lethal.calc_lethal` の `moves` 引数の型を
  `MoveName | Move | tuple[MoveName | Move, int] | list[...]` に拡張し、文字列は内部で
  `Move(name)` に正規化するようにした（既存の `Move` インスタンス渡しは非破壊）。
  `examples/04_damage_calculation.py` の `moves=Move(move_name)` を `moves=move_name` に変更し、
  未使用になった `Move` importと該当TODOコメントを削除
  - 実装中に発見: `core/lethal.py` のトップレベルで `from jpoke.model import Move` すると、
    `jpoke.data.ability` が `jpoke.core.lethal.LethalHandler` を import する経路と衝突して
    循環importになった（`fix/circular-import-fragility` と同種の問題）。`Move` の import を
    実際に文字列を変換する箇所（`_generate_move_list` 内の `to_move`）まで遅延させて解消した
- `CHANGELOG.md` の `[Unreleased]` に Added（`play_out()`）・Changed（`calc_lethal`の技名文字列対応、
  `print_logs`/`get_log_lines`の`turn="all"`対応）・Fixed（`Battle.finished`の不整合修正）を追記
- フルテストスイート（`python -m pytest tests/ -q`）4829 passed, 1 skipped を確認。
  `tests/test_examples_smoke.py` も個別に実行し6件全てPASSEDを確認。examples 01〜05を
  実際に実行し、`print_logs("all")` の全ターン出力・`command_to_move()`・技名文字列指定の
  `calc_lethal` がいずれも意図通り動作することを目視でも確認した

### 2026-07-12 3度目のレビュー対応（残り4項目）

前回の対応で対象外としていた `Battle.__init__` 可変長引数化・05のmax_pliesコメント・
02のRandomPlayer化・01 L26のstart()説明コメントの4項目に対応した。

- `Battle.__init__(self, players: tuple[Player, ...], ...)` を `Battle.__init__(self, *players:
  Player, ...)` に変更（`self.players: tuple[Player, ...] = players` は可変長引数がタプルとして
  受け取れるため変更不要）。呼び出し箇所を全リポジトリ検索した結果、当初想定していた
  `Battle((p1, p2), ...)` という直接的な二重括弧パターン（examples 01〜05・README・
  scripts/lethal_calc.py・scripts/tree_search/tree_search_1〜4.py・
  docs/poke-env/compat_plan.md・docs/plan/poke-env/poke_env_battle_converter.md・
  tests/test_poke_env_compat.py・tests/test_tree_search_framework.py・
  src/jpoke/core/player.py の16ファイル）に加えて、事前に組み立てたタプル/リスト変数を
  そのまま渡す非明示的なパターン（`Battle(players, ...)` / `Battle([p0, p1], ...)` /
  `Battle(tuple(players), ...)`）が `tests/test_utils.py`・`tests/test_fuzz_regressions.py`・
  `tests/test_replay_fuzz.py`・`src/jpoke/core/replay.py`・`scripts/random_1on1.py`・
  `scripts/fuzz_battle.py`・`scripts/replay_fuzz_battle.py`・`scripts/janken_nash.py` の
  8ファイルにも見つかったため、すべて `Battle(*players, ...)` / `Battle(p1, p2, ...)` の
  個別・展開引数渡しに書き換えた（合計24ファイル）。破壊的変更として `CHANGELOG.md` の
  `### Changed` に明記した
- `examples/05_tree_search_ai.py`: `KOFocusedPlayer(...)` の直前に `max_plies` の意味と
  増やした場合の分岐増加について行コメントを追加し、「試してみよう」に `max_plies` を
  変えて `nodes_expanded` を比較する誘導を追記。解消済みだった同趣旨のTODOコメントを削除
- `examples/02_team_battle.py`: Team A / Team B を `Player` から `jpoke.players.RandomPlayer`
  に変更し、docstringの記述も実態に合わせて更新。01は見送り方針どおり変更していない
- `examples/01_quickstart.py`: `battle.start()` 呼び出しの直前に `Battle.start()` の
  docstringを踏まえた説明コメントを追加し、該当TODOコメントを削除
- フルテストスイート（`.venv/Scripts/python.exe -m pytest tests/ -q`）4829 passed, 1 skipped
  を確認。`tests/test_examples_smoke.py` も個別に実行し6件全てPASSEDを確認。
  examples 01〜05および変更した scripts（lethal_calc.py・tree_search_1〜4.py・
  janken_nash.py・random_1on1.py・fuzz_battle.py・replay_fuzz_battle.py）を実際に実行し、
  `Battle` の可変長引数呼び出しがいずれもエラーなく動作することを確認した

