# examples

`.ipynb` は下表のファイル名リンクから Google Colab でそのまま開いて実行できる
（各ノートブック冒頭のリンクからも開ける）。ローカルで実行する場合は
`pip install jpoke` 後に Jupyter で開く。

## 01_getting_started/

導入（jpokeを初めて使う）

| ファイル | 内容 |
|---|---|
| [`01_quick_start.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_getting_started/01_quick_start.ipynb) | `Player.battle_against()` / `Battle.play_out()` を使った最小構成のバトル実行 |
| [`02_step.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_getting_started/02_step.ipynb) | `battle.step()` によるターン進行、3vs3バトル |
| [`03_custom_player.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_getting_started/03_custom_player.ipynb) | `Player` を継承した最小のカスタム方策（`choose_command()` / `choose_selection()` のオーバーライド） |
| [`04_lethal.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_getting_started/04_lethal.ipynb) | `battle.calc_lethal()` による致死率計算（攻撃回数・致死確率）の基本 |
| [`05_cli_vs_custom_ai.py`](https://github.com/tmwork1/jpoke/blob/main/examples/01_getting_started/05_cli_vs_custom_ai.py) | `jpoke.players.CLIPlayer` を使い、標準入力でコマンドを入力しながら自作AI（`03_custom_player.ipynb`と同じ方策）と対戦する。対話入力のためColab非対応（`.py`） |

## 02_tree_search/

AI開発（`MinimaxPlayer` を継承した木探索AIのカスタマイズ）

| ファイル | 内容 |
|---|---|
| [`01_evaluate.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_tree_search/01_evaluate.ipynb) | `evaluate()` のオーバーライドによる葉ノード（盤面）の評価方法のカスタマイズ |
| [`02_fallback.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_tree_search/02_fallback.ipynb) | `fallback()` のオーバーライドによる、探索できない局面での代替方策のカスタマイズ |
| [`03_estimate_opponent.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_tree_search/03_estimate_opponent.ipynb) | `estimate_opponent()` のオーバーライドによる、相手の未公開の技構成の推定と、それを踏まえた木探索 |
| [`04_configure_sim.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_tree_search/04_configure_sim.ipynb) | `configure_sim()` のオーバーライドによる、探索中だけ命中率・ダメージ乱数を固定する決定論化 |

## 03_lethal/

致死率・ダメージ計算

| ファイル | 内容 |
|---|---|
| [`01_multi_hit.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_lethal/01_multi_hit.ipynb) | 連続技（ヒット数指定）の致死率計算 |
| [`02_multi_move.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_lethal/02_multi_move.ipynb) | 複数の技を組み合わせた（`moves=[...]`）加算ダメージの致死率計算 |
| [`03_merge_results.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_lethal/03_merge_results.ipynb) | `LethalHitResult` どうしを足し合わせて複数の致死率計算結果を合成する方法 |
| [`04_direct_manipulation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_lethal/04_direct_manipulation.ipynb) | HP・能力ランク・状態異常・揮発性状態・場の状態を直接操作してから致死率計算するシナリオ検証 |
| [`05_testing_helpers.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_lethal/05_testing_helpers.ipynb) | `jpoke.testing` の `start_battle()` 等を使い、定型的なセットアップを短く書くショートカット |

## 04_others/

その他のトピック

| ファイル | 内容 |
|---|---|
| [`logcode.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/04_others/logcode.ipynb) | `LogCode` の種類の確認方法（`battle.get_event_logs(turn)` によるログ種別の抽出） |
| [`poke_env_style_player.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/04_others/poke_env_style_player.ipynb) | poke-env互換プロパティ（`battle.available_moves` 等）を使った `choose_command()` の実装 |
| [`pokedex.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/04_others/pokedex.ipynb) | `Pokemon.data` を通した図鑑データ（持てる特性・覚えられる技など）の取得 |

## 05_advanced/

戦術研究（発展）

`03,04` のみColab非対応（重い並列処理・ロールアウト処理のため）。
Windowsで日本語ログが文字化けする場合は `PYTHONUTF8=1` を指定する。

| ファイル | 内容 |
|---|---|
| [`01_bulk_simulation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/05_advanced/01_bulk_simulation.ipynb) | `Player.battle_against()` による多数回対戦・構成比較 |
| [`02_replay.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/05_advanced/02_replay.ipynb) | `Battle.build_replay_data()` / `ReplayPlayer` / `replay_battle()` によるリプレイの記録・再生 |
| [`03_janken_nash_fictitious_play.py`](https://github.com/tmwork1/jpoke/blob/main/examples/05_advanced/03_janken_nash_fictitious_play.py) | 実バトルのモンテカルロ推定 + 反復最適反応（fictitious play）によるNash均衡（固定の混合戦略）の近似、`ProcessPoolExecutor` による並列化 |
| [`04_janken_nash_cfr.py`](https://github.com/tmwork1/jpoke/blob/main/examples/05_advanced/04_janken_nash_cfr.py) | `Battle.copy()` を使ったロールアウトベースのregret matching（CFR風）による、HP状況に応じた適応的な戦略の自己対戦学習 |

`03,04` は対戦セットアップ等の共通処理を [`_janken_common.py`](https://github.com/tmwork1/jpoke/blob/main/examples/05_advanced/_janken_common.py)（単独では実行しない内部ヘルパー）に切り出して共有している。

## 99_dev/

開発用（計算速度の計測）

| ファイル | 内容 |
|---|---|
| [`01_step_time_benchmark.py`](https://github.com/tmwork1/jpoke/blob/main/examples/99_dev/01_step_time_benchmark.py) | 完全ランダムな3vs3全選出バトルを繰り返し実行し、`Battle.step()` 1回あたりの所要時間（mean ± σ）を計測。既定値は数分かかるため`--n-battles`等のコマンドライン引数で調整できる |
