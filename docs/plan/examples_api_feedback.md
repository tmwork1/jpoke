# examples/ 作成から見えたAPIフィードバック

作成日: 2026-07-11

## 運用ルール

- 本ドキュメントの項目は `[ ]` / `[x]` のチェックリスト形式で管理する。`[x]` は
  「実装対応済み」または「検討のうえ対応しないと決定した（見送り確定）」の両方を含み、
  `[ ]` は「まだ判断・対応していない」項目を指す。チェックを付けたら、その項目の末尾に
  `→ 対応内容 (日付)` を追記する
- **妥当と判断したフィードバックは、判断した時点で即座にsonnet sub agentへ実装を委任する**。
  本体（Fable）は仕様の精査・妥当性判断・差分レビュー・PR操作を担当し、実装・テスト・
  検証はsonnetサブエージェント（`Agent` ツール、`model: sonnet`、`isolation: "worktree"`）に
  詳細な指示書付きで委任する。1件ずつ都度サブエージェントに投げてよく、まとめて
  バッチ実行する必要はない（関連メモ: `feedback_sonnet_subagent_for_work`）

## 教材としての質

- [x] 難易度勾配（01→06）は概ね適切。01/02で進行、03で方策、04で計算、05で探索、06で統計と段階的に積み上がっており、各docstring冒頭の「jpoke で学べること:」統一フォーマットも良い。（対応不要・肯定的所感）
- [x] 04（ダメージ計算）は03（カスタム方策）と05（木探索）のAI系列に割り込む配置。ユースケース別に独立した題材なので現状でも許容だが、AI開発の連続性を優先するなら 03→05 を隣接させ、04を後ろに回す選択肢もある。（見送り確定: フィードバック自身が「現状でも許容」としており、連番・README対応表への影響に見合わないため据え置き。2026-07-12判断）
- [x] 02 のループ内コメント（瀕死→自動交代の説明3行）はループ本体より長く、docstringへ移した方が読みやすい。05 のdocstringは `src/jpoke/players/...` を参照させているが、「clone不要で動く」前提の読者はソースを持っていないため、参照先はGitHub URLかAPIドキュメントにすべき。（→ 2026-07-11 f41f4df5で対応済み）
- [x] 「次に何を試すか」の誘導が弱い。各サンプル末尾に1行の「試してみよう」（例: 01→技を変える、03→評価関数にHP割合を加える、06→n_battlesや構成を変える）があると学習動線が明確になる。（→ 2026-07-11 examples 01〜06全てに追加）
- [x] examples/README.md の対応表（ファイル/学べる内容/ユースケース）は簡潔で分かりやすい。ルートREADMEのユースケース記述と用語（戦術研究・AI開発・ダメージ計算ツール開発）が揃っている点も良い。（対応不要・肯定的所感）
- [x] 06 の `build_player(item_name, item_name)` は username にアイテム名を渡しており、初見では引数の取り違えに見える。`build_player(username=..., item_name=...)` とキーワード渡しにするだけで誤読が消える。（→ 2026-07-11 f41f4df5で対応済み）

## 公開APIの使い勝手

- [x] `Player.team` への追加方法が `.append()`（01,03,05,06）と `= [...]` 代入（02,04）で混在。どちらも動くが教材として一貫性がなく、また `team` が素のlistのため6匹超過などの検証が入らない。`add_pokemon()` 等の正規ルートを1つ定めるか、examples内だけでも書式を統一したい。（→ 2026-07-11/12 `Player.add_pokemon()` を新設し、examples全体で統一）
- [x] `player.team` はコンストラクタ時点のスナップショットで対戦中は更新されず、対戦中の状態は `battle.get_active(player)` で取る必要がある（03のコメントで補足している通り）。「自分のチームなのに戦況が反映されない」のは学習者が最初に踏む罠で、docstringだけでなくAPIリファレンスでの明示が必要。（未対応: examples/03のコード内コメントのみで、`Player.team`属性のdocstring自体には未反映）（→ 2026-07-12 `Player` の `Attributes:` の `team` 説明にスナップショットである旨と `battle.get_active(player)` / `battle.get_team(player)` への誘導を追記）
- [x] 場のポケモンの取得方法が `battle.get_active(player)`（03）と `battle.actives[0]`（04）の2通り登場する。相手チーム参照に至っては `battle.player_states[battle.opponent(self)].team`（05）と内部構造に踏み込んでおり、「外部APIはBattleの公開メソッドを入口にする」方針と齟齬がある。`battle.get_team(player)` のような公開アクセサが欲しい。（→ 2026-07-11 `Battle.get_team()` を新設し、examples全体で`get_active`/`get_team`に統一）
- [x] `Pokemon.__init__` の暗黙デフォルトが多い: `nature="まじめ"`, `level=50`, `move_names` 省略時は `["はねる"]`, `ability_name=""`, IV31/EV0。特に「技を渡さないとはねるになる」「特性が空文字で何になるか」はコードから読み取れず、docstringでの明記かクラスメソッド（例: `Pokemon.simple(...)`）での整理を検討したい。（→ 2026-07-11 docstringに明記して対応。代替コンストラクタは`add_pokemon()`が実質的に代替するため追加実装は見送り）
- [x] `n_selected` のデフォルト3とチーム1匹構成の組み合わせは、01のように毎回 `n_selected=1` を明示する必要がある。省略時に「min(3, len(team))に自動調整」する方が導入体験は滑らか。（→ 2026-07-11 自動調整を実装）
- [x] `Command` から技実体への到達が `mon.moves[command.index]` という2段の間接参照（03）。`command` 自体が技を知らないため学習者が `index` の意味を推測する必要があり、`battle.get_move(command)` のようなヘルパーがあると方策実装が書きやすい。（見送り確定: 優先度メモに含まれず「検討したい」止まりのため、今回は対応しない。2026-07-12判断）
  → **訂正（2026-07-12）**: この見送り判断は誤りだった。`battle.command_to_move(player, command)`（`src/jpoke/core/battle.py:635`、実体は `command_manager.resolve_move_from_command`）が新ヘルパーとして既に公開API化されていたが、見送り判断時に見落としていた。ユーザーが再度同じ指摘をTODOコメントとして書いたことで発覚（下記「3度目のレビュー指摘」参照）。対応不要な新規実装はなく、examples/03を既存APIへ書き換えるだけで解消する

## 既知のバグ・要修正候補

- [x] `Battle(seed=None)` が `int(time.time())`（秒精度）にフォールバックする（`src/jpoke/core/battle.py:155`）。`battle_against(n_battles=30)` をseed省略で呼ぶと30戦全てが同一seedになり勝率が0%/100%に張り付く。対応案: (1) フォールバックを `time.time_ns()` または `Random(None)`（OSエントロピー）に変更、(2) `battle_against` 側で `seed` 指定時は対局ごとに `seed+i` の派生seedを振る。両方入れれば `examples/06` のワークアラウンド（n_battles=1×ループ）を素直な `battle_against(..., n_battles=30)` に書き戻せる。（→ 2026-07-11 `secrets.randbits(32)` に変更 + `battle_against`の対局別seed派生を実装）
- [x] デフォルト `Player.choose_command()` が「利用可能なコマンドの先頭を選ぶ」決定的挙動である点は、seedを変えても同一展開になりやすく、06のような統計比較の分散を殺す方向に働く。ベースラインとしてランダム選択（05の `RandomPlayer` 相当）を標準提供するか、既定挙動をdocstringで強調すべき。（未対応）（→ 2026-07-12 `jpoke.players.RandomPlayer` を新設（`battle.random` ベースで `Battle(seed=...)` の再現性を保つ）。examples/05のローカル定義を置き換え、`Player.choose_command()` のdocstringにも既定実装が決定的である旨と `RandomPlayer` への誘導を追記）

## 優先度メモ

1. [x] **seed フォールバックの修正 + battle_against の対局別seed派生**（上記バグ）。統計的に誤った結果を静かに返す罠であり、examples/06 の注意書きと歪んだ書き方を解消できるため最優先。（→ 2026-07-11 対応済み）
2. [x] **対戦中状態へのアクセスAPI整理**（`get_active` / `actives` / `player_states` の一本化と `get_team` 追加）。教材3本にまたがって説明コメントが必要になっている＝学習コストが最も高い箇所。（→ 2026-07-11 対応済み）
3. [x] **`n_selected` の自動調整（min(3, len(team))）**。全サンプルで `n_selected=1` の明示とコメントが必要になっており、導入の最初の1行目の摩擦を減らせる。（→ 2026-07-11 対応済み）

## 再レビュー指摘（2026-07-12 Fableサブエージェント、PR #38差分）

- [x] `tests/moves_attack/test_move_ha.py` の `test_はたきおとす_相手のアイテムがないとき威力補正なし` が同種のflakiness（急所のブレでダメージ比較が逆転しうる）を持つとMonte Carlo実測（300回中8回失敗）で指摘 → `fix_random()` を追加して解消
- [x] `Battle.roll_damage()` の `int(random() * len(damages))` が `random()==1.0` の境界（一部テストが `battle.random.random = lambda: 1.0` を使用）でIndexErrorになり得ると指摘 → `min(index, len(damages)-1)` のクランプを追加
- [x] `examples/README.md` の01の説明が `Pokemon` importなし化に追従していなかったと指摘 → 修正
- [x] `n_selected` 自動調整のdocstringに「チーム間で手持ち数が異なっても両者に同じ値が適用される」旨の追記が必要と指摘 → 追記
- [x] `battle_against` のdocstringに「複数opponent指定時は対戦通番がopponentごとにリセットされ、同じseed系列を使い回す」旨の追記が必要と指摘 → 追記
- [x] （付随発見・スコープ外）`tests/abilities/test_ability_a.py:667`（いかりのつぼ）で `random()==1.0` 固定時に技自体がミスして意図せず空虚に合格する既存の問題を発見 → 今回の変更が原因ではなく、examples APIフィードバック対応のスコープ外のため見送り確定

## 3度目のレビュー指摘（2026-07-12、ユーザー記入のexamples内TODOコメント + Fableサブエージェント）

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

## 4度目のレビュー指摘（2026-07-12、jpoke内部実装を知らない設定のsonnetサブエージェント + Fable本体の検証）

`src/jpoke/` 配下を一切読ませず、poke-env経験者・jpoke初見という設定のsonnetサブエージェントに
`README.md`・`examples/` のみを見せてレビューさせた。指摘の中に「`examples/02_team_battle.py` を
実行すると両陣営が終盤ずっと交代コマンドだけを選び続け、二度と技を出さないまま30ターン打ち切りになる」
という重大な指摘があり、Fable本体が `src/jpoke` 側を調査して原因を特定した。

- [x] **【重大・バグ】`Player.choose_command()` に渡される観測用コピー（`Battle.build_observation()`
  が返す `sim`）の `random` が本体の `battle.random` から独立した deepcopy のスナップショットに
  なっており、`RandomPlayer`（`battle.random.choice(...)` を使う）が `sim.random` を消費しても
  本体側の `battle.random` の状態が一切進まない。デバッグ実行で `battle.random.getstate()` を
  ターンごとに出力したところ、ターン2以降まったく同じ状態のまま固定されることを確認した
  （`src/jpoke/core/battle.py:330` `build_observation()` → `observation_builder.build()`
  → `new = deepcopy(battle)` で `random` も複製される）。技を使わず交代だけが選ばれ続けるターンでは
  `battle.random` がどこからも消費されないため、`build_observation()` は毎ターン全く同じ乱数状態
  から `sim` を作り直すことになり、`sim.random.choice(candidates)` は毎回同じ選択肢を返し続ける。
  結果として「交代を選ぶ→技を使わないので本体のrandomが進まない→次のターンも同じ状態からsimが
  作られ同じ選択が繰り返される」という無限ループに陥る。`examples/02_team_battle.py`
  （`seed=1,2,3,5`）で再現し、`seed=4` のみ他の理由で早期決着していた。
  - `src/jpoke/players/tree_search_player.py` の `TreeSearchPlayer` は探索用に
    `battle.copy()`（`reseed`省略でFalse、独立した`random`のdeepcopy）を明示的に使っており、
    これは意図した設計（探索中の乱数消費が本体を汚染しないようにするため）。しかし
    `TreeSearchPlayer.fallback()`（`_toplevel_commands` で相手コマンドが未公開の場合に呼ばれる）は
    探索の最上位で `build_observation()` が返す最初の `battle`（＝観測用コピー）に対して
    `battle.random.choice(...)` を呼ぶため、こちらも同様に本体の `battle.random` を進められない
    経路になっている
  - 影響箇所は `src/jpoke/core/command_manager.py:178`（`resolve_command` の行動コマンド選択）と
    `src/jpoke/core/turn_controller.py:99`（`_run_selection` の選出）の両方で、
    `battle.build_observation(player)` を経由する全ての `choose_command` / `choose_selection` 呼び出し
  - 修正方針案: `src/jpoke/core/observation_builder.py` の `build()` 内、`new = deepcopy(battle)` の
    直後に `new.random = battle.random`（deepcopyされた複製を捨て、本体と同一のオブジェクト参照に
    差し替える）とすることで、`choose_command`/`choose_selection` 内での乱数消費が本体の
    `battle.random` にも反映されるようにする。`Battle.build_observation()` のもう一方の分岐
    （`self.is_observation()` が真の場合の `return self.copy()`）は探索中の内部シミュレーション
    （`self` が既に本体から切り離された `sim`）向けであり、ここは変更不要（`self.random` を
    そのまま複製すればよい。木探索の各分岐が独立した乱数系列を持つという既存の意図を壊さない）
  - 検証すべき影響範囲: (1) `TreeSearchPlayer` の探索結果が変わらないこと（`sim = battle.copy()` は
    `build_observation()` を経由しないため無関係のはず）、(2) `Battle.replay` 機能（`command_log` に
    記録済みのコマンドを再生する経路）が `random` の消費状況に依存していないか、(3) 修正後に
    `examples/02_team_battle.py` を `seed=1〜10` 程度で実行し、無限交代ループが再現しないこと、
    (4) 既存の乱数依存テスト（`fix_random()` 使用箇所含む）がフルスイートで全件成功すること
  - 再現用の最小デバッグコード（サブエージェントへの指示に転記）:
    ```python
    from jpoke import Battle
    from jpoke.players import RandomPlayer
    player1 = RandomPlayer("Team A")
    player1.add_pokemon("ピカチュウ", move_names=["かみなり"])
    player1.add_pokemon("ヒトカゲ", move_names=["かえんほうしゃ"])
    player1.add_pokemon("フシギダネ", move_names=["ギガドレイン"])
    player2 = RandomPlayer("Team B")
    player2.add_pokemon("ゼニガメ", move_names=["なみのり"])
    player2.add_pokemon("コラッタ", move_names=["すてみタックル"])
    player2.add_pokemon("ピッピ", move_names=["ムーンフォース"])
    battle = Battle(player1, player2, seed=1)
    battle.start()
    for t in range(10):
        print(t + 1, battle.random.getstate()[1][:3])
        battle.step()
    # 修正前: ターン2以降 getstate() が完全に固定されたまま変化しない
    ```
  → 対応内容 (2026-07-12): `src/jpoke/core/observation_builder.py` の `build()` 内、
  `new = deepcopy(battle)` の直後に `new.random = battle.random` を追加し、
  deepcopyされた複製を捨てて本体と同一のオブジェクト参照に差し替えた。
  `self.is_observation()` が真の場合に `self.copy()` を返すもう一方の分岐
  （`TreeSearchPlayer` の探索用 `sim = battle.copy()`）は変更していない。
  `tests/test_poke_env_compat.py` に回帰テストを2件追加した
  （観測用コピーの `random` が本体と同一オブジェクトであることの検証、および
  バグ報告の再現条件（3体チーム・両陣営RandomPlayer、seed=1,2,3,5）で技コマンドが
  実際に選ばれた上で30ターン以内に決着することの検証）。フルテストスイート
  （4831 passed, 1 skipped）で回帰がないことを確認し、`examples/02_team_battle.py` を
  seed=1〜10で実行して無限交代ループが再現しないこと・技コマンドが使われることを
  目視確認した

- [x] **教材カバレッジ不足**: 同サブエージェントに、「README『実装状況』の規模（特性310・アイテム247・
  技733・揮発性状態66・場の効果31）に対して、examplesのどのサンプルにも一度も登場しない主要概念」を
  追加調査させたところ、以下が判明した（`src/jpoke` は見せずexamples/READMEのみから調査させたが、
  Fable本体が該当APIの実在をコード側で裏付け済み）：
  - **EV/IVを設定する手段がexamplesに一度も登場しない**。`Pokemon.__init__`/`Player.add_pokemon()`は
    `gender/nature/level/ability_name/item_name/move_names/tera_type`のみで、EV/IVはコンストラクタ引数
    にない。ただし`Pokemon.set_evs(evs, hp_policy=...)`/`Pokemon.set_ivs(ivs, hp_policy=...)`という
    正規のインスタンスメソッドが既に存在する（`src/jpoke/model/pokemon.py:624,650`）。ダメージ計算
    ツール開発ユースケースを掲げる04がまさにEV/IVを振った実数値でこそ効果を発揮する場面なのに、
    一度も使われていない
  - 特性（`ability_name`）がexamples全体で一度も指定されず、ダメージ計算・行動選択への影響が
    一度も見せられていない
  - 天候・地形・状態異常（どく・やけど等の意図的な発生）・交代誘発技（とんぼがえり等）・
    設置技・先制/素早さ操作技・わるあがき（PP切れ）がexamples全体で一度も登場しない
  - テラスタルを能動的に選ぶ方法（`Command.get_terastal_command()`相当）や、交代コマンドを
    明示的に組み立てる方法がexamplesのどこにも示されていない
  - （対応不要・見送り）EV/IV以外の項目は「新規サンプルの追加」が必要な範囲が広く、
    今回のバグ修正（上記random共有）を優先。教材拡充は別タスクとして後日改めて着手する
  → 対応内容 (2026-07-12): EV/IVの実演のみ最小コストで価値が高いため、
    `examples/04_damage_calculation.py` の攻撃側ガブリアスに `mon.set_evs([0, 32, 0, 0, 0, 0])`
    （こうげき努力値をChampions形式で最大まで振る）を追加し、こうげき実数値の表示と
    「無振りより確定数・致死率が高くなる」旨のコメントを添えた（他の未カバー項目は見送り、上記の通り）

### 追加の気づき（Fableサブエージェントの指摘、対応不要）

- `RandomPlayer` は `jpoke.players` 経由でのみ提供され、トップレベル `jpoke` からは未エクスポート。
  ただし `TreeSearchPlayer` 等の既存のPlayer派生クラスも同様の扱いのため、既存の設計方針との整合が
  取れており対応不要と判断

## 実施記録（詳細ログ）

### 2026-07-11 実装（優先度メモ1〜3 + 教材としての質）

- `Battle(seed=None)` のフォールバックを `secrets.randbits(32)`（OSエントロピー）に変更。
  `Player.battle_against(..., seed=...)` は対戦ごとに `seed + 対戦通番` の派生シードを
  自動的に使うよう変更し、examples/06 のワークアラウンド（seedを手動でずらすループ）を
  `battle_against(..., n_battles=N, seed=1)` の素直な呼び出しに戻した
  - 副作用として、`Battle.roll_damage()` の通常ロール抽選が `random.choice()`
    （`getrandbits()` 依存）だったため、テストヘルパー `fix_random()`（`random()` のみ固定）
    では制御できず、seedの高エントロピー化により一部テストが乱数依存で不安定化することが
    判明した。`roll_damage()` の抽選を `random.random()` ベースに変更し、`fix_random()` で
    完全に制御できるようにして解消（`tests/moves_attack/test_move_ma.py` の1件は
    `fix_random()` 追加で対応）
  - さらに `critical_mode="確定のみ"` は「急所を確定させる」設定ではなく「急所レート
    計算を特性等の割り込みなしの基礎値のみにする」設定で、急所に当たるか自体は
    引き続き `random.random()` の実ロールに依存すると判明。`damage_roll="最大"` /
    `critical_mode="確定のみ"` だけに頼り `fix_random()` を使っていなかった
    `test_move_ta.py`（DDラリアット×2）・`test_move_sa.py`（ソーラービーム×2）の
    比較系テストが急所のブレで偶発的に失敗し得たため、`fix_random()` を追加して解消。
    フルテストスイートを10回超連続実行して再発しないことを確認済み
- `Battle(n_selected=None)` を `min(3, 各プレイヤーの手持ち数)` に自動設定するよう変更。
  全examplesから冗長な `n_selected=1`/`n_selected=3` の明示を削除
- `Battle.get_team(player)` を追加し、examples/05 の
  `battle.player_states[battle.opponent(self)].team` を置き換え。examples/04 の
  `battle.actives[0]` も `battle.get_active()` に統一
- 各サンプル末尾に「試してみよう」の1行コメントを追加（01/02/03/04/05/06）
- `Player.team` への追加方法を `.append()` に統一（02, 04 の `= [...]` 代入を書き換え）
- `Pokemon.__init__` のdocstringに暗黙のデフォルト（性格・レベル・特性・技・個体値/努力値）を明記
- ユーザー指摘により、`Player.add_pokemon(name, **kwargs)` を新設。`Pokemon` を直接
  importせずにチームを組めるようにし、examples全体で `from jpoke import ... Pokemon` の
  importと `team.append(Pokemon(...))` を置き換えた（教材としての質・公開APIの使い勝手
  双方の指摘に対応）
- 04の防御側表示も `defender_player.team[0]` から `battle.get_active(defender_player)` に統一

### 2026-07-12 再レビュー対応

PR #38 の差分に対して再度Fableモデルでレビューを受け、上記「再レビュー指摘」の内容を修正した。

### 2026-07-12 残り2項目の実装（`player.team`スナップショット警告 + `RandomPlayer`新設）

- `Player`（`src/jpoke/core/player.py`）の `Attributes:` の `team` 説明に、対戦中は
  更新されないスナップショットであることと、対戦中の実際の状態は
  `battle.get_active(player)` / `battle.get_team(player)` を使うべき旨を追記
- `src/jpoke/players/random_player.py` に `RandomPlayer(Player)` を新設。
  `battle.random.choice(battle.get_available_commands(self))` で選ぶ実装で、
  `examples/05_tree_search_ai.py` に元々ローカル定義されていたものと同等
  （`battle.random` を使うため `Battle(seed=...)` の再現性を壊さない）
- `src/jpoke/players/__init__.py` に `RandomPlayer` を追加してエクスポート
- `Player.choose_command()` のdocstringに、既定実装が決定的（常に先頭のコマンドを
  選ぶ）である旨と、統計比較などで分散が必要な場合は `jpoke.players.RandomPlayer`
  を使うとよい旨を追記
- `examples/05_tree_search_ai.py` のローカル `RandomPlayer` 定義を削除し、
  `from jpoke.players import RandomPlayer` に置き換え（未使用になった `Player` /
  `Command` importも削除）
- `CHANGELOG.md` の `[Unreleased]` / `### Added` に `RandomPlayer` の追加を記載
- `tests/test_poke_env_compat.py` に `RandomPlayer` のテストを2件追加
  （選択コマンドが常に `get_available_commands()` に含まれること、
  `battle.random` 経由で同一seedなら同一コマンド列を再現すること）。
  `scripts/sort_tests.py` / `scripts/generate_test_list.py` を実行し、
  フルテストスイートを3回連続実行して全件成功・非flakyを確認済み
  （worktree分離環境ではeditable installが別チェックアウトの`src`を指すため、
  `tests/test_examples_smoke.py`（サブプロセス起動によるスモークテスト）を
  検証する際は `PYTHONPATH=<worktree>/src` を明示してworktree内の実装を
  優先させる必要があった。mainマージ後は不要な手当て）

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

### 2026-07-12 4度目のレビュー対応（observation randomの共有バグ修正 + EV/IV教材追加）

「4度目のレビュー指摘」の重大バグ（無限交代ループ）と、追加依頼のあった教材カバレッジ
不足（EV/IV）の2項目に対応した。sonnetサブエージェント（`isolation: "worktree"`）に
委任して実装・検証した。

- `src/jpoke/core/observation_builder.py` の `build()` 内、`new = deepcopy(battle)` の
  直後に `new.random = battle.random` を追加。観測用コピー（`sim`）の乱数生成器を
  deepcopyされた独立インスタンスではなく本体と同一のオブジェクト参照に差し替えることで、
  `RandomPlayer` 等が `sim.random` を消費した際に本体の `battle.random` にも反映される
  ようにした。`Battle.build_observation()` のもう一方の分岐（`is_observation()` が真の
  場合の `self.copy()`、`TreeSearchPlayer` の探索用シミュレーション向け）は意図的に
  変更していない
- `tests/test_poke_env_compat.py` に回帰テストを2件追加:
  `test_observation_randomは本体のbattle_randomと同じ参照を共有する`
  （`sim.random is battle.random` を直接検証）、
  `test_無限交代ループの再現条件下でもコマンドが技を含んで決着する`
  （バグ報告の再現条件そのまま、seed=1,2,3,5で技コマンドの使用と30ターン以内の決着を検証）。
  `scripts/sort_tests.py` / `scripts/generate_test_list.py` を実行
- `examples/04_damage_calculation.py`: 攻撃側ガブリアスに
  `attacker.set_evs([0, 32, 0, 0, 0, 0])`（こうげき努力値をChampions形式で最大まで振る）を
  追加し、こうげき実数値の表示（`攻撃側: ガブリアス（ドラゴンテール, こうげき実数値 182）`）と
  「無振りより確定数・致死率が高くなる」旨のコメントを追加。実行結果は無振り時の確定数3から
  2に短縮されることを確認した
- 影響範囲の確認: `tests/test_tree_search_framework.py`（木探索の決定論性）・
  `tests/test_replay_fuzz.py` / `tests/test_fuzz_regressions.py`（リプレイ再生）・
  `tests/test_observation.py`（情報隠蔽）を個別実行し全件成功を確認。
  `ReplayPlayer.choose_command()` は渡された `battle`（sim）を一切参照せず記録済み
  コマンドをそのまま払い出す実装のため、`sim.random` の共有化とは無関係であることを
  コードで確認した
- フルテストスイート（`.venv/Scripts/python.exe -m pytest tests/ -q`）4831 passed, 1 skipped
  を確認（回帰テスト2件分の純増）。`examples/02_team_battle.py` をseed=1〜10で実行し、
  修正前は無限ループしていた条件が全seedで30ターン以内に決着し、技コマンドが実際に使われる
  ことを確認した。`examples/04_damage_calculation.py` を実行し、EV追加後の出力が意図通り
  変化することを確認した
- `CHANGELOG.md` の `[Unreleased]` / `### Fixed` に本バグ修正を追記
