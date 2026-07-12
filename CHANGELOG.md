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

## [0.1.0] - 2026-07-11

### Added

- 初回 PyPI 公開。`pip install jpoke` でイベント駆動のポケモンチャンピオンズ
  シングルバトルシミュレーションを利用できる
- 特性 310 件・アイテム 247 件・技 733 件・揮発性状態 66 件・状態異常 7 件・
  場の効果（天候・地形・グローバル・サイド）31 件を実装
  （詳細は `docs/progress/` 配下を参照）
