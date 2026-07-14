# 4度目のレビュー指摘（2026-07-12、jpoke内部実装を知らない設定のsonnetサブエージェント + Fable本体の検証）

[← 目次に戻る](../README.md)

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

- [x] **【設計見直し・PR #45への追加修正】上記の `new.random = battle.random` という修正には、
  ユーザー指摘により重大な副作用があると判明した：観測用コピー（`sim`）のゲーム進行用 `random` を
  本体と同一オブジェクトにしたことで、`Player.choose_command(sim)` の中で方策が `sim.random` を
  直接触ると、本来はその後の技実行（ダメージロール・命中判定・急所判定等）で消費されるはずだった
  乱数列を、行動選択の時点で先取り・消費できてしまう。例えば方策が `sim.random.random()` を覗いて
  から行動を決めるような実装をすれば、「これから打つ技が急所に当たるかどうか」を実行前に知った
  上で行動を選べてしまう（観測者が未来の乱数を予知できる、チート的先読みが可能になる）。これは
  無限交代ループより深刻な設計上の欠陥であり、「行動選択に使う乱数」と「ゲーム進行に使う乱数」を
  そもそも同じ `battle.random` に押し込めたことが根本原因
  - 修正方針: `Battle` に行動選択専用の乱数生成器 `decision_random`（`battle.seed` から派生した
    別シードで初期化。`Battle.copy(reseed=True)` が `hash((self.seed, self._reseed_count))` で
    派生シードを作っている方式を参考にする）を新設する。`RandomPlayer.choose_command()` と
    `TreeSearchPlayer.fallback()` は `battle.random.choice(...)` ではなく
    `battle.decision_random.choice(...)` を使うように変更する。`observation_builder.build()` では
    `decision_random` だけを本体と同一参照で共有し（無限ループの再発を防ぐ）、ゲーム進行用の
    `random` は今回のPR #45の変更を巻き戻して元通り独立コピー（deepcopy）に戻す（＝先読み不可能に
    戻す）。`Battle.copy(reseed=True)`（木探索の意図的な系列分離用）でも `decision_random` を
    同様に派生シードで再初期化し、既存の `random` と同じ扱いにする
  - 影響範囲: `RandomPlayer`（`src/jpoke/players/random_player.py`）・`TreeSearchPlayer.fallback`
    （`src/jpoke/players/tree_search_player.py:90`）のdocstring更新（`battle.random` への言及を
    `battle.decision_random` に修正）、`PR #45で追加した回帰テスト2件`
    （`test_observation_randomは本体のbattle_randomと同じ参照を共有する` は
    `decision_random`が共有され`random`は共有されない、という検証に書き換える。
    `test_無限交代ループの再現条件下でもコマンドが技を含んで決着する` は変更なく通るはず）、
    `Battle.__init__` のdocstring・`docs/spec/` 配下に乱数系列の説明があれば更新
  - 検証すべき影響範囲: (1) `examples/02_team_battle.py` をseed=1〜10で再実行し無限交代ループが
    再発しないこと、(2) `sim.random is not battle.random`（先読み不可能）かつ
    `sim.decision_random is battle.decision_random`（無限ループ対策）の両方が成り立つこと、
    (3) `TreeSearchPlayer` の探索結果・決定論性が変わらないこと、(4) フルテストスイート全件成功
  → 対応内容 (2026-07-12): `Battle.__init__`（`src/jpoke/core/battle.py`）に
    `self.decision_random = Random(hash((self.seed, "decision")) & 0xFFFFFFFF)` を新設し、
    `_EXTRA_DEEPCOPY_KEYS` に追加、`Battle.copy(reseed=True)` でも派生シードで再初期化するように
    した。`src/jpoke/players/random_player.py` の `RandomPlayer.choose_command()` と
    `src/jpoke/players/tree_search_player.py` の `TreeSearchPlayer.fallback()` を
    `battle.decision_random.choice(...)` に変更（docstringも修正）。
    `src/jpoke/core/observation_builder.py` の `build()` から `new.random = battle.random` を削除し
    （ゲーム進行用randomは元通り独立deepcopyに戻した）、代わりに
    `new.decision_random = battle.decision_random` を追加した。`tests/test_poke_env_compat.py` の
    回帰テストを `test_observationのdecision_randomは共有されrandomは独立している`
    （`sim.random is not battle.random` かつ `sim.decision_random is battle.decision_random` を検証）
    に書き換え、`test_無限交代ループの再現条件下でもコマンドが技を含んで決着する` は変更なく
    通ることを確認した。`examples/02_team_battle.py` をseed=1〜10で実行し全て30ターン以内に
    技コマンドを使って決着すること・`tests/test_tree_search_framework.py` 11件全件成功・
    フルテストスイート（4831 passed, 1 skipped、既存ベースラインと同数）を確認した

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


### 実施記録

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

### 2026-07-12 設計見直し（decision_random新設による行動選択用/ゲーム進行用乱数の分離）

上記「observation randomの共有バグ修正」（`new.random = battle.random`）に、ユーザー指摘により
発覚した重大な副作用（方策が `sim.random` を先取り消費し未来の乱数を予知できてしまう設計欠陥）を
解消した。sonnetサブエージェント（`isolation: "worktree"`）に委任して実装・検証した。

- `src/jpoke/core/battle.py`: `Battle.__init__` に行動選択専用の乱数生成器
  `self.decision_random = Random(hash((self.seed, "decision")) & 0xFFFFFFFF)` を新設
  （`self.random` の直後）。`_EXTRA_DEEPCOPY_KEYS` に `decision_random` を追加してdeepcopy対象にし、
  `Battle.copy(reseed=True)` でも `new.decision_random` を派生シードで再初期化するようにした
- `src/jpoke/players/random_player.py`: `RandomPlayer.choose_command()` を
  `battle.decision_random.choice(...)` に変更（docstringの `battle.random` への言及も修正）
- `src/jpoke/players/tree_search_player.py`: `TreeSearchPlayer.fallback()` を
  `battle.decision_random.choice(...)` に変更（docstringも同様に修正）
- `src/jpoke/core/observation_builder.py`: `build()` から `new.random = battle.random` を削除し
  （ゲーム進行用 `random` を元通り独立deepcopyに戻し先読みを不可能にした）、
  代わりに `new.decision_random = battle.decision_random` を追加（無限交代ループ対策は維持）
- `tests/test_poke_env_compat.py`: `test_observation_randomは本体のbattle_randomと同じ参照を共有する`
  を `test_observationのdecision_randomは共有されrandomは独立している` に改名し、
  `sim.random is not battle.random` かつ `sim.decision_random is battle.decision_random` の
  両方を検証するように書き換え。`test_無限交代ループの再現条件下でもコマンドが技を含んで決着する`
  は変更なしでそのまま成功することを確認。あわせて `test_randomplayerは同じseedで対戦すると
  同じコマンド列を再現する` の docstring中の `battle.random` 言及も `battle.decision_random` に
  修正した。`scripts/sort_tests.py` / `scripts/generate_test_list.py` を実行
- 検証: `examples/02_team_battle.py` をseed=1〜10で実行し全seedが30ターン以内に技コマンドを
  使って決着すること（無限交代ループが再発しないこと）を確認。`sim.random is not battle.random`
  かつ `sim.decision_random is battle.decision_random` の両方をテストで担保。
  `tests/test_tree_search_framework.py` 11件全件成功（木探索の決定論性に影響なし）。
  フルテストスイート（`python -m pytest tests/ -q`）4831 passed, 1 skipped
  （バグ修正時点のベースラインと同数、リグレッションなし）を確認
- `CHANGELOG.md` の `[Unreleased]` / `### Fixed` に本追加修正を追記し、PR #45の記述が
  「先読み可能」な問題を残したままの表現になっていた部分を修正後の正しい状態に更新した

### 2026-07-12 4度目のレビュー指摘・残り項目対応（リプレイ・poke-env互換プロパティ・modify_hp系・get_event_logs・優先度低4項目）

「内部実装に精通したsonnetサブエージェントによる追加調査」節の残り5項目（うち1件は4サブ項目の
まとめ）に対応した。damage_roll系・EV/IVは前段の別タスクで対応済みのため対象外。

- 新規 `examples/07_replay.py` を追加。1vs1バトルを最後まで進めて `Battle.build_replay_data()` で
  記録し、`to_dict()`/`from_dict()` でシリアライズ・復元してから `jpoke.core.replay.replay_battle()`
  に渡し、勝者・ターン数が元の対戦と一致することを確認する最小例。`examples/README.md` の対応表に
  1行追加し、`CHANGELOG.md` の `[Unreleased]` / `### Added` にも記載した
- `examples/03_custom_player.py` の `StrongestMovePlayer` に、`battle.available_moves` 等の
  poke-env互換プロパティ（`choose_command` に渡される観測コピーの `battle.observer` が呼び出し元
  プレイヤーに設定されるため、そのまま自分視点の情報として使える）で同じ判断を書いた
  `choose_command_poke_env_style()` を未使用の別メソッドとして併記した。既存の `choose_command()` を
  一時的に差し替えて同一seedで最終ターン数・勝者が一致することを手動検証済み
- `examples/04_damage_calculation.py` に、`modify_hp(r=-0.6)` で防御側のHPを残り40%まで直接
  減らしてから `calc_lethal(max_attack=1)` を呼ぶ例（致死率0.00%→100.00%）と、続けて
  `modify_stats(target, {"def": 1})` でぼうぎょランクを上げると同条件でも致死率が下がる
  （100.00%→56.25%）ことを示す例、`faint()` で対象を即座にひんし化する例を追加した
- `examples/02_team_battle.py` の勝敗表示の直後に、`get_event_logs(turn)` を全ターン分走査して
  `LogCode.CRITICAL_HIT` のログだけを抽出・表示する例を追加した
- 優先度低4項目のうち低コストな2件のみ対応: `Player.n_lost_battles` を
  `examples/06_bulk_simulation.py` の勝率表示に追記し、`Player.add_pokemon()` の戻り値を
  `build_player()` で変数に受けて `mon.set_evs(...)` の追加設定に使う形に書き換えた。
  `Battle.copy(reseed=True)` と `TreeSearchPlayer.configure_sim()`/`opponent_estimator()` は
  意味のある実演に既存サンプルの作り替えが必要になるため見送った（詳細は各チェック項目参照）
- `python -m pytest tests/ -q` 4837 passed, 1 skipped（新規回帰なし、既存テストは無変更）。
  `python -m ruff check src/ tests/ scripts/ examples/` 全件成功。
  変更・追加した `examples/02_team_battle.py`・`03_custom_player.py`・`04_damage_calculation.py`・
  `06_bulk_simulation.py`・`07_replay.py`（新規）を実際に実行し、出力が意図通りであることを
  目視確認した（`tests/test_examples_smoke.py` の7件全PASSEDも確認）

