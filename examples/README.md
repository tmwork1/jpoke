# examples

`pip install jpoke` だけで実行できる、導入・学習用のサンプル集。
`jpoke.*` の公開APIのみに依存しており、リポジトリを clone しなくても動く。

大半のサンプルは Jupyter Notebook（`.ipynb`）として提供している。下記
「ファイル一覧」の Colab バッジをクリックすると、Google Colab でそのまま
開いて実行できる（Googleアカウントでサインインし、上から順にセルを実行する
だけでよい。ランタイムは既定のCPUのままでよい）。各ノートブック冒頭の
`%pip install -q jpoke` セルが自動で `jpoke` をインストールする。

ローカルの Jupyter で開く場合は以下のように起動する。

```bash
pip install jpoke jupyter
jupyter notebook examples/01_basics/01_battle_against_intro.ipynb
```

`04_research/03,04`（Nash均衡の近似。後述）のみ重い並列処理を伴うため
notebook化しておらず、通常の `.py` スクリプトとして提供している。

```bash
pip install jpoke
python examples/04_research/03_janken_nash_fictitious_play.py
```

Windows環境では、標準出力の既定エンコーディングの都合で `.py` を直接実行すると
日本語のログが文字化けすることがある。その場合は `PYTHONUTF8=1` を指定して
実行する（`.ipynb` 側はJupyter経由の実行のため通常この問題は起きない）。

```powershell
$env:PYTHONUTF8 = "1"
python examples/04_research/03_janken_nash_fictitious_play.py
```

```bash
PYTHONUTF8=1 python examples/04_research/03_janken_nash_fictitious_play.py
```

各ファイル冒頭にある `from __future__ import annotations` は、型アノテーションの
前方参照を有効にするためのおまじない。動作に必要なので、消さずにそのまま残してよい。

サンプルはユースケース別のディレクトリに分かれており、各ディレクトリ内で独立して
連番（`01_`, `02_`, ...）を振っている。新しいサンプルを追加する際は、対応する
ディレクトリ内の連番を延長するだけでよく、他ディレクトリの番号と衝突しない。

## ディレクトリ一覧

| ディレクトリ | ユースケース |
|---|---|
| `01_basics/` | 導入（jpokeを初めて使う） |
| `02_ai/` | AI開発（`Player` を継承した方策の実装） |
| `03_damage_calc/` | ダメージ計算ツール開発 |
| `04_research/` | 戦術研究（多数回対戦・リプレイ・読み合いの定量分析） |
| `05_benchmark/` | 計算速度の計測 |

## ファイル一覧

`.ipynb` のファイル名リンクはColabバッジになっており、クリックするとGoogle Colabで
そのまま開く。`04_research/03,04` の2本のみColab非対応（`.py`）で、GitHub上の
ファイルへのリンクになっている。

| ファイル | 学べる内容 | 対応ユースケース |
|---|---|---|
| [`01_basics/01_battle_against_intro.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/01_battle_against_intro.ipynb) | `Player.battle_against()` を使った最小構成のバトル実行 | 導入 |
| [`01_basics/02_play_out.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/02_play_out.ipynb) | `Battle.play_out()` によるBattle/Playerを直接使った最小構成の1vs1バトル自動進行 | 導入 |
| [`01_basics/03_team_battle.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/03_team_battle.ipynb) | `battle.step()` によるターンごとの手動進行、3体チーム・複数選出のバトルループ | 導入 |
| [`01_basics/04_pokedex_ability_lookup.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/04_pokedex_ability_lookup.ipynb) | `POKEDEX[name].abilities` / `POKEDEX[name].learnset` によるポケモンが持てる特性・覚えられる技の確認 | 導入 |
| [`01_basics/05_command_type_identification.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/05_command_type_identification.ipynb) | `battle.get_available_commands()` が返す `Command` の種類の識別（`is_regular_move`/`is_terastal`/`is_switch`） | 導入 |
| [`01_basics/06_logcode_variety.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/01_basics/06_logcode_variety.ipynb) | `LogCode` の種類の確認、`battle.get_event_logs()` が返す構造化ログ（LogCode付きのEventLog） | 導入 |
| [`02_ai/01_custom_player.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/01_custom_player.ipynb) | `Player` を継承した最小のカスタム方策（`choose_command()` のオーバーライド） | AI開発 |
| [`02_ai/02_selection_customization.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/02_selection_customization.ipynb) | `choose_selection()` のオーバーライドによる選出順のカスタマイズ | AI開発 |
| [`02_ai/03_tree_search_ai.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/03_tree_search_ai.ipynb) | `TreeSearchPlayer` を継承した木探索AIとランダム方策の対戦 | AI開発（発展） |
| [`02_ai/04_command_evaluation_debug.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/04_command_evaluation_debug.ipynb) | `TreeSearchPlayer.evaluate_commands()` によるコマンド候補・評価値のデバッグ確認 | AI開発（発展） |
| [`02_ai/05_opponent_estimation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/05_opponent_estimation.ipynb) | `TreeSearchPlayer.estimate_opponent()` のオーバーライドによる、相手の未公開の技構成の推定と、それを踏まえた木探索 | AI開発（発展） |
| [`02_ai/06_deterministic_search.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/06_deterministic_search.ipynb) | `TreeSearchPlayer.configure_sim()` のオーバーライドによる、探索中だけ命中率・ダメージ乱数を固定する決定論化 | AI開発（発展） |
| [`02_ai/07_fallback_policy.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/07_fallback_policy.ipynb) | `TreeSearchPlayer.fallback()` のオーバーライドによる、探索できない局面での代替方策のカスタマイズ | AI開発（発展） |
| [`02_ai/08_poke_env_style_player.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/02_ai/08_poke_env_style_player.ipynb) | poke-env互換プロパティ（`battle.available_moves` 等）を使った `choose_command()` の実装 | AI開発 |
| [`03_damage_calc/01_raw_damage_rolls.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/01_raw_damage_rolls.ipynb) | `calc_damages()` / `roll_damage()` による生ダメージロールの確認、`damage_roll` / `critical_mode` による固定ロール | ダメージ計算ツール開発 |
| [`03_damage_calc/02_direct_state_manipulation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/02_direct_state_manipulation.ipynb) | `set_ailment()` / `modify_hp()` / `modify_stats()` / `faint()` を単体で直接操作するAPIの確認 | ダメージ計算ツール開発 |
| [`03_damage_calc/03_basic_lethal_calculation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/03_basic_lethal_calculation.ipynb) | `battle.calc_lethal()` による確定数・乱数ダメージの基本計算、努力値、`Pokemon.show()` | ダメージ計算ツール開発 |
| [`03_damage_calc/04_ailment_and_scenario_comparison.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/04_ailment_and_scenario_comparison.ipynb) | 02の各操作を組み合わせ、シナリオ間でcalc_lethal()の致死率を比較 | ダメージ計算ツール開発 |
| [`03_damage_calc/05_multi_hit_and_combo_moves.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/05_multi_hit_and_combo_moves.ipynb) | `Move.expected_hits`（連続技の期待ヒット数）、複数技を組み合わせる（`moves=[...]`） | ダメージ計算ツール開発 |
| [`03_damage_calc/06_secondary_effects.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/06_secondary_effects.ipynb) | `secondary=True` による追加効果込みの確定数短縮、自傷効果（りゅうせいぐん等）が`secondary`の対象外である理由 | ダメージ計算ツール開発 |
| [`03_damage_calc/07_field_effects.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/07_field_effects.ipynb) | 天候（すなあらし）・地形（エレキフィールド）の効果 | ダメージ計算ツール開発 |
| [`03_damage_calc/08_ailment_and_volatile.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/08_ailment_and_volatile.ipynb) | 技を実際に当てて状態異常を発生させる方法、`battle.set_volatile()` による揮発性状態（やどりぎのタネ）の直接付与、`effect_chance_threshold` による追加効果発動確率の固定 | ダメージ計算ツール開発 |
| [`03_damage_calc/09_ability_and_item_logs.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/09_ability_and_item_logs.ipynb) | `battle.step()` を伴う進行での特性・アイテムの発動ログ確認 | ダメージ計算ツール開発 |
| [`03_damage_calc/10_testing_helpers.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/10_testing_helpers.ipynb) | `jpoke.testing` の `start_battle()` / `apply_ailment()` / `run_move()` / `calc_lethal()` による、定型的なセットアップを短く書くショートカット | ダメージ計算ツール開発 |
| [`03_damage_calc/11_form_change_comparison.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/11_form_change_comparison.ipynb) | `Pokemon.set_form()` によるフォルム変化（ロトムの姿）がタイプ・種族値の違いを通じてダメージ・致死率に与える影響の比較 | ダメージ計算ツール開発 |
| [`03_damage_calc/12_item_manipulation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/03_damage_calc/12_item_manipulation.ipynb) | `gain_item()` / `remove_item()` / `set_item()` / `take_item()` / `consume_item()` / `swap_items()` による持ち物の直接操作、成功/失敗条件の違い | ダメージ計算ツール開発 |
| [`04_research/01_bulk_simulation.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/04_research/01_bulk_simulation.ipynb) | `Player.battle_against()` による多数回対戦・構成比較 | 戦術研究（構成比較） |
| [`04_research/02_replay.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/04_research/02_replay.ipynb) | `Battle.build_replay_data()` / `ReplayPlayer` / `replay_battle()` によるリプレイの記録・再生 | 戦術研究（対戦の記録・解析） |
| [`04_research/03_janken_nash_fictitious_play.py`](https://github.com/tmwork1/jpoke/blob/main/examples/04_research/03_janken_nash_fictitious_play.py)（Colab非対応） | 実バトルのモンテカルロ推定 + 反復最適反応（fictitious play）によるNash均衡（固定の混合戦略）の近似、`ProcessPoolExecutor` による並列化 | 戦術研究（読み合いの定量分析、発展） |
| [`04_research/04_janken_nash_cfr.py`](https://github.com/tmwork1/jpoke/blob/main/examples/04_research/04_janken_nash_cfr.py)（Colab非対応） | `Battle.copy()` を使ったロールアウトベースのregret matching（CFR風）による、HP状況に応じた適応的な戦略の自己対戦学習 | 戦術研究（読み合いの定量分析、発展） |
| [`05_benchmark/01_step_time_benchmark.ipynb`](https://colab.research.google.com/github/tmwork1/jpoke/blob/main/examples/05_benchmark/01_step_time_benchmark.ipynb) | 完全ランダムな3vs3全選出バトルを繰り返し実行し、`Battle.step()` 1回あたりの所要時間（mean ± σ）を計測。既定値は数分かかるためノートブック内のパラメータセルで`n_battles`等を調整できる | 計算速度の計測 |

`04_research/03_janken_nash_fictitious_play.py` / `04_research/04_janken_nash_cfr.py` は
重い並列処理・ロールアウト処理を伴うため、Jupyter Notebook化・Colab対応をしておらず
`.py` スクリプトのまま提供している。多数回のバトルシミュレーションを行うため、他の
サンプルより実行に時間がかかる（手元ではそれぞれ十数秒・数十秒程度）。どちらも構文・
ゲーム理論用語の両面でそれまでのexamplesより難易度が上がるため、まず03（固定の混合
戦略のNash均衡）を読んでから04（HP状況に応じた適応的な戦略）に進むと理解しやすい
構成にしてある。
