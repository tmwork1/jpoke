# Changelog

このプロジェクトの変更点はすべてこのファイルに記録する。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に、
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

## [Unreleased]

### Added

- `Battle.get_team(player)` — 対戦中のプレイヤーのチーム実体を取得する公開アクセサ
  （`player_states[player].team` への直接アクセスを置き換える）
- `Player.add_pokemon(name, **kwargs)` — `Pokemon` を直接importせずにチームへ
  ポケモンを追加できる正規ルート
- `jpoke.players.RandomPlayer` — 合法手からランダムに選ぶ `Player` 実装。既定の
  `Player.choose_command()`（常に先頭のコマンドを選ぶ決定的挙動）では
  `battle_against()` による統計比較の分散が潰れてしまう問題への対応
- `Battle.play_out(max_turns=100)` — 決着がつくかターン上限に達するまで
  自動的に対戦を進める便宜メソッド。`start()` → `while not battle.finished
  and battle.turn < N: battle.step()` という定型ループの重複を解消する。
  `Player.battle_against()` の内部ループもこれに置き換えた
- `Battle.set_ailment(target, name, count=None)` / `Battle.set_weather(name, count=5)` /
  `Battle.set_terrain(name, count=5)` — 状態異常・天候・地形を技を介さず直接
  セットする薄い公開ラッパー（既存の `ailment_manager` / `weather_manager` /
  `terrain_manager` への委譲）。シナリオ構築や `calc_lethal()` によるダメージ計算
  検証で、対戦を進行させずに状態異常・天候込みの複合致死率を確認できる
- `examples/07_replay.py` — `Battle.build_replay_data()` / `ReplayPlayer` /
  `replay_battle()`（リプレイの記録・再生一式）を紹介するサンプルを新設
- `jpoke.testing` モジュール — `tests/test_utils.py` にあった内部テストヘルパー
  （`start_battle` / `run_move` / `run_switch` / `apply_ailment` /
  `get_action_order` / `calc_lethal` / `fix_damage` / `fix_random` 等14関数と
  `CustomPlayer`）を本体パッケージへ昇格。`pip install jpoke` だけで（リポジトリを
  clone せずに）任意ターンでのピンポイントな状態検証・技の実行ができるようになった。
  `tests/test_utils.py` は後方互換のための薄い再エクスポート層として残している。
  移植にあたり `Battle` に不足していた公開ラッパーを追加した:
  `Battle.set_ailment()` に `source` / `overwrite` 引数を追加、
  `Battle.set_volatile()` / `Battle.set_item()` /
  `Battle.activate_global_field()` / `Battle.activate_side_field()` /
  `Battle.resolve_action_order()` / `Battle.calc_move_priority()` /
  `Battle.can_switch()` / `Battle.end_turn()` を新設
  （いずれも `ailment_manager` 等の内部マネージャーへの薄い委譲で、外部コードが
  `battle.<manager>.<method>()` を直接呼ばずに済むようにするための追加）
- `Command` をトップレベルパッケージから再エクスポート（`from jpoke import Command`。
  従来は `from jpoke.enums import Command` のみ）。`Battle` / `Player` は既にトップ
  レベルから使えたが `Command` だけ欠けていたための追加
- `Battle.has_available_bench(player)` / `Battle.is_floating(pokemon)` /
  `Battle.is_trapped(pokemon)` / `Battle.is_nervous(pokemon)` /
  `Battle.is_hazard_immune(pokemon)` / `Battle.can_use_last_resort(pokemon)` /
  `Battle.get_forced_move_name(pokemon)` / `Battle.is_first_actor(player)` /
  `Battle.is_second_actor(player)` — `battle.query`（`PokemonQuery`）のうち
  `Pokemon`/`Player` 単体の引数で完結する判定メソッドを `Battle` 直下に薄い
  委譲として追加。`can_switch()` 以外は `battle.query.<method>()` の直接呼び出しが
  必要で `docs/api/README.md` にも未掲載だったための対応（`AttackContext`/
  `EventContext` を要求する内部専用メソッドは対象外のまま）

### Changed

- **破壊的変更**: `Battle.__init__` が `players: tuple[Player, ...]` ではなく
  `*players: Player` の可変長引数を受け取るようになった。
  `Battle((player1, player2), ...)` ではなく `Battle(player1, player2, ...)`
  と書く
- `Battle(n_selected=...)` を省略した場合、`min(3, 各プレイヤーの手持ち数)` を
  自動設定するようになった（従来は常に3固定で、手持ちが3未満だと `n_selected` の
  明示指定が必須だった）
- `Battle.calc_lethal` / `core.lethal.calc_lethal` の `moves` 引数が技名の文字列
  （`MoveName`）を受け付けるようになった。`Move(name)` へのラップなしに
  `moves="ドラゴンテール"` のように渡せる（`Move` インスタンスでの指定は従来通り
  可能）
- `Battle.print_logs(turn)` / `Battle.get_log_lines(turn)` が `turn="all"` を
  受け付けるようになった。1ターン目から現在ターンまでの全ログを一括で
  取得・出力できる（`turn=None` で現在ターンのみ、という既存の挙動は変更なし）
- **破壊的変更**: `examples/` をユースケース別ディレクトリ構造に再編した。
  従来のフラットな連番（`examples/01_quickstart.py` 〜
  `examples/09_janken_nash_cfr.py`）を廃止し、`examples/01_basics/`,
  `examples/02_ai/`, `examples/03_damage_calc/`, `examples/04_research/` の
  ディレクトリに分割、各ディレクトリ内で独立して連番を振り直した
  （例: `examples/01_quickstart.py` → `examples/01_basics/01_quickstart.py`）。
  独立した作業が同じ番号を取り合う衝突事故を防ぐための変更
- **破壊的変更**: `Battle.consume_item()` / `ItemManager.consume_item()` の第1引数名を
  `mon` から `target` にリネームした（`gain_item` / `remove_item` / `take_item` 等、
  他のアイテム系メソッドとの引数名を統一するための変更）。キーワード引数で
  `mon=...` と呼び出している箇所は `target=...` に変更する必要がある
  （リポジトリ内の既存呼び出しはすべて位置引数のため影響なし）
- **破壊的変更**: `Pokemon.modify_hp()` を `Pokemon._modify_hp_raw()` にリネームした。
  従来のdocstringで「内部用。外部からは`battle.modify_hp()`を使用」と警告して
  いたにもかかわらず、アンダースコアなしのメソッド名のままトップレベル
  `from jpoke import Pokemon` から到達可能で誤って直接呼び出しやすい状態
  だった。直接呼ぶとHPのクランプのみが行われ、`ON_HP_CHANGE`系ハンドラの
  発火・瀕死判定・ログ記録がスキップされる罠になっていたため、命名で
  内部専用であることを明示した。外部コードは常に `Battle.modify_hp()` を使うこと

- **破壊的変更**: `Battle.decision_random`（行動選択専用の乱数生成器）の種の派生式を
  `hash((seed, "decision")) & 0xFFFFFFFF` から `(seed + 0x9E3779B9) & 0xFFFFFFFF` に
  変更した。`str` を含む `tuple` の `hash()` は `PYTHONHASHSEED` によりプロセスごとに
  ランダム化されるため、同じ `seed` を指定しても `decision_random` が生成する乱数列が
  プロセスを跨ぐと再現しなかった（`RandomPlayer.choose_command()` /
  `TreeSearchPlayer.fallback()` はこの乱数列を消費するため、これらを経由するコマンド
  選択の再現実験・CI比較が壊れうる問題があった）。新しい派生式は整数の算術演算のみで
  `PYTHONHASHSEED` に依存しないため、プロセスを跨いでも同じ `seed` なら同じ乱数列が
  再現される。加算する定数（ハッシュ撹拌でよく使われる黄金比由来の値）が0でないため
  mod 2**32 上で不動点を持たず、あらゆる `seed` で `Battle.random`（種は `seed` その
  もの）と衝突しないことが保証される。`Battle.copy(reseed=True)` 側も同様に修正した。
  **同じ `seed` でも `decision_random` が生成する具体的な乱数列は旧バージョンから
  変わる**（ゲーム進行用の `Battle.random` の乱数列には影響しない）

- `examples/` 配下のファイル構成を「1ファイル=1事例」の原則で再点検し、詰め込み
  過ぎていたファイルを分割・renumberした（`01_basics/` 3→5ファイル、`02_ai/`
  3→4ファイル、`03_damage_calc/` 3→9ファイル、`04_research/` は
  `03_janken_nash_cfr.py` / `04_janken_nash_fictitious_play.py` の番号を入れ替え）。
  `04_research/03_janken_nash_cfr.py` の `hp_bucket()` はHP満タン
  （fraction=1.0）を専用の最上位バケットとして切り出す仕様に変更し、バケット
  総数が `HP_BUCKETS` から `HP_BUCKETS + 1` になった

### Fixed

- `Battle(seed=None)` のフォールバックが `int(time.time())`（秒精度）だったため、
  短時間に複数の `Battle` を生成すると同一シードになり、`Player.battle_against()`
  などの多数回対戦がすべて同じ展開になってしまう問題を修正。OSの乱数源から
  高エントロピーな値を生成するように変更した
- `Player.battle_against(..., seed=...)` を指定した場合、対戦ごとに
  `seed + 対戦通番` の派生シードを自動的に使うようにし、`n_battles` を1回の
  呼び出しで指定しても展開が固定化しないようにした
- `Battle.roll_damage()` の通常ロール抽選が `random.choice()`（PRNG内部状態に
  依存し `random()` のみを固定するテストヘルパーでは制御できない）だったため
  `random.random()` ベースの抽選に変更。上記のseed高エントロピー化に伴い、
  乱数固定が不十分だった一部テストがダメージ比較で偶発的に失敗する状態を解消した
- `Battle.finished` が `self.winner is not None` だけを見ていたため、
  `judge_winner()` を一度も呼ばずに `finished` だけを参照すると、TODスコアで
  実際には決着している対戦でも `False` を返し続ける不整合を修正。
  `judge_winner()` 経由で判定するように変更した
- `Battle.build_observation()`（`choose_command()`/`choose_selection()` に渡される
  観測用コピーを構築する）が乱数生成器 `random` をdeepcopyで独立複製していたため、
  `RandomPlayer` 等が観測用コピー側の `random` を消費しても本体の `battle.random` が
  一切進まなかった。技を使わず交代コマンドのみが選ばれ続けるターンでは本体の乱数状態が
  毎ターン同一のまま固定され、`build_observation()` が同じ乱数状態から同じコピーを
  作り直すことで同じ選択が繰り返される無限交代ループに陥っていた
  （`examples/02_team_battle.py` の `seed=1,2,3,5` で再現）。当初は観測用コピーの
  `random` を本体と同一のオブジェクト参照に差し替えて解消したが、これには
  「行動選択に使う乱数」と「ゲーム進行に使う乱数」を分離していなかったことに起因する
  重大な設計上の欠陥があった（後述の追加修正を参照）
- 上記修正で `random` を観測用コピーと本体で共有した結果、`Player.choose_command(sim)`
  内で方策が `sim.random` を直接触ると、本来は技実行後（ダメージロール・命中判定・
  急所判定等）に消費されるはずの乱数列を行動選択の時点で先取り消費できてしまい、
  「これから打つ技が急所に当たるか」を打つ前に知った上で行動を選べるチート的先読みが
  可能になる欠陥があった。`Battle` に行動選択専用の乱数生成器 `decision_random`
  （`seed` から決定的に派生させ、`Battle.copy(reseed=True)` でも派生シードで
  再初期化される）を新設し、`RandomPlayer.choose_command()` /
  `TreeSearchPlayer.fallback()` はこちらを使うように変更した。
  `build_observation()` は `decision_random` だけを本体と共有し（無限交代ループ対策を
  維持）、ゲーム進行用の `random` は元通りdeepcopyによる独立コピーに戻すことで
  先読みを不可能にした
- `Pokemon.set_stats(stats)` が辞書のキー（`Stat`）を無視し、`enumerate()` による
  挿入順を暗黙の固定順（0=HP, 1=攻撃, 2=防御, ...）とみなして書き込んでいたため、
  `{"atk": 150, "def": 100}` のようにキー順が典型順と異なる辞書や6項目に満たない
  辞書を渡すと、例外を出さずに意図と異なるステータスへ書き込まれる不具合を修正。
  `stats.items()` からキーで対象インデックスを引くように変更した

## [0.1.0] - 2026-07-11

### Added

- 初回 PyPI 公開。`pip install jpoke` でイベント駆動のポケモンチャンピオンズ
  シングルバトルシミュレーションを利用できる
- 特性 310 件・アイテム 247 件・技 733 件・揮発性状態 66 件・状態異常 7 件・
  場の効果（天候・地形・グローバル・サイド）31 件を実装
  （詳細は `docs/progress/` 配下を参照）
