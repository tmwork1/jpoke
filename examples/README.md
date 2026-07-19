# examples

`.ipynb` は下表のファイル名リンクから Google Colab でそのまま開いて実行できる。

## 01_basics/

導入（jpokeを初めて使う）

| ファイル | 内容 |
|---|---|
| [`01_battle_against_intro.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/01_battle_against_intro.ipynb) | `Player.battle_against()` を使った最小構成のバトル実行 |
| [`02_play_out.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/02_play_out.ipynb) | `Battle.play_out()` による最小構成のバトル自動進行 |
| [`03_team_battle.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/03_team_battle.ipynb) | `battle.step()` によるターン進行、3vs3バトル |
| [`04_pokedex_intro.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/04_pokedex_intro.ipynb) | `POKEDEX` の紹介 |
| [`05_command_type_identification.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/05_command_type_identification.ipynb) | 行動を決定する `Command` の種類の識別 |
| [`06_logcode_variety.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/06_logcode_variety.ipynb) | ログの構造と種類の確認 |

## 02_ai/

AI開発（`Player` を継承した方策の実装）

| ファイル | 内容 |
|---|---|
| [`01_custom_player.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/01_custom_player.ipynb) | `Player` を継承した最小のカスタム方策（`choose_command()` のオーバーライド） |
| [`02_selection_customization.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/02_selection_customization.ipynb) | `choose_selection()` のオーバーライドによる選出順のカスタマイズ |
| [`03_tree_search_ai.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/03_tree_search_ai.ipynb) | `TreeSearchPlayer` を継承した木探索AIとランダム方策の対戦（発展） |
| [`04_command_evaluation_debug.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/04_command_evaluation_debug.ipynb) | `TreeSearchPlayer.evaluate_commands()` によるコマンド候補・評価値のデバッグ確認（発展） |
| [`05_opponent_estimation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/05_opponent_estimation.ipynb) | `TreeSearchPlayer.estimate_opponent()` のオーバーライドによる、相手の未公開の技構成の推定と、それを踏まえた木探索（発展） |
| [`06_deterministic_search.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/06_deterministic_search.ipynb) | `TreeSearchPlayer.configure_sim()` のオーバーライドによる、探索中だけ命中率・ダメージ乱数を固定する決定論化（発展） |
| [`07_fallback_policy.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/07_fallback_policy.ipynb) | `TreeSearchPlayer.fallback()` のオーバーライドによる、探索できない局面での代替方策のカスタマイズ（発展） |
| [`08_poke_env_style_player.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/08_poke_env_style_player.ipynb) | poke-env互換プロパティ（`battle.available_moves` 等）を使った `choose_command()` の実装 |

## 03_damage_calc/

ダメージ計算

| ファイル | 内容 |
|---|---|
| [`01_raw_damage_rolls.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/01_raw_damage_rolls.ipynb) | `calc_damages()` / `roll_damage()` による生ダメージロールの確認、`damage_roll` / `critical_mode` による固定ロール |
| [`02_direct_state_manipulation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/02_direct_state_manipulation.ipynb) | `set_ailment()` / `modify_hp()` / `modify_stats()` / `faint()` を単体で直接操作するAPIの確認 |
| [`03_basic_lethal_calculation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/03_basic_lethal_calculation.ipynb) | `battle.calc_lethal()` による確定数・乱数ダメージの基本計算、努力値、`Pokemon.show()` |
| [`04_ailment_and_scenario_comparison.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/04_ailment_and_scenario_comparison.ipynb) | 02の各操作を組み合わせ、シナリオ間でcalc_lethal()の致死率を比較 |
| [`05_multi_hit_and_combo_moves.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/05_multi_hit_and_combo_moves.ipynb) | `Move.expected_hits`（連続技の期待ヒット数）、複数技を組み合わせる（`moves=[...]`） |
| [`06_secondary_effects.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/06_secondary_effects.ipynb) | `secondary=True` による追加効果込みの確定数短縮、自傷効果（りゅうせいぐん等）が`secondary`の対象外である理由 |
| [`07_field_effects.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/07_field_effects.ipynb) | 天候（すなあらし）・地形（エレキフィールド）の効果 |
| [`08_ailment_and_volatile.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/08_ailment_and_volatile.ipynb) | 技を実際に当てて状態異常を発生させる方法、`battle.set_volatile()` による揮発性状態（やどりぎのタネ）の直接付与、`effect_chance_threshold` による追加効果発動確率の固定 |
| [`09_ability_and_item_logs.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/09_ability_and_item_logs.ipynb) | `battle.step()` を伴う進行での特性・アイテムの発動ログ確認 |
| [`10_testing_helpers.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/10_testing_helpers.ipynb) | `jpoke.testing` の `start_battle()` / `apply_ailment()` / `run_move()` / `calc_lethal()` による、定型的なセットアップを短く書くショートカット |
| [`11_form_change_comparison.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/11_form_change_comparison.ipynb) | `Pokemon.set_form()` によるフォルム変化（ロトムの姿）がタイプ・種族値の違いを通じてダメージ・致死率に与える影響の比較 |
| [`12_item_manipulation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/12_item_manipulation.ipynb) | `gain_item()` / `remove_item()` / `set_item()` / `take_item()` / `consume_item()` / `swap_items()` による持ち物の直接操作、成功/失敗条件の違い |

## 04_research/

戦術研究

`03,04` のみColab非対応（重い並列処理・ロールアウト処理のため）。
Windowsで日本語ログが文字化けする場合は `PYTHONUTF8=1` を指定する。

| ファイル | 内容 |
|---|---|
| [`01_bulk_simulation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/04_research/01_bulk_simulation.ipynb) | `Player.battle_against()` による多数回対戦・構成比較 |
| [`02_replay.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/04_research/02_replay.ipynb) | `Battle.build_replay_data()` / `ReplayPlayer` / `replay_battle()` によるリプレイの記録・再生 |
| [`03_janken_nash_fictitious_play.py`](https://github.com/tmwork1/jpoke/blob/main/examples/04_research/03_janken_nash_fictitious_play.py) | 実バトルのモンテカルロ推定 + 反復最適反応（fictitious play）によるNash均衡（固定の混合戦略）の近似、`ProcessPoolExecutor` による並列化（発展） |
| [`04_janken_nash_cfr.py`](https://github.com/tmwork1/jpoke/blob/main/examples/04_research/04_janken_nash_cfr.py) | `Battle.copy()` を使ったロールアウトベースのregret matching（CFR風）による、HP状況に応じた適応的な戦略の自己対戦学習（発展） |

`03,04` は対戦セットアップ等の共通処理を `_janken_common.py`（単独では実行しない内部ヘルパー）
に切り出して共有している。

## 05_benchmark/

計算速度の計測

| ファイル | 内容 |
|---|---|
| [`01_step_time_benchmark.py`](https://github.com/tmwork1/jpoke/blob/main/examples/05_benchmark/01_step_time_benchmark.py) | 完全ランダムな3vs3全選出バトルを繰り返し実行し、`Battle.step()` 1回あたりの所要時間（mean ± σ）を計測。既定値は数分かかるため`--n-battles`等のコマンドライン引数で調整できる |
