# examples

`pip install jpoke` だけで実行できる、導入・学習用のサンプルスクリプト集。
`jpoke.*` の公開APIのみに依存しており、リポジトリを clone しなくても動く。

```bash
pip install jpoke
python examples/01_basics/01_battle_against_intro.py
```

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

| ファイル | 学べる内容 | 対応ユースケース |
|---|---|---|
| `01_basics/01_battle_against_intro.py` | `Player.battle_against()` を使った最小構成のバトル実行 | 導入 |
| `01_basics/02_quickstart.py` | `Battle` / `Player` を手動管理する最小構成の1vs1バトル | 導入 |
| `01_basics/03_team_battle.py` | 3体チーム・複数選出・複数ターンのバトルループ | 導入 |
| `01_basics/04_log_and_pokedex_lookup.py` | `battle.get_event_logs()` による構造化ログからの特定イベント抽出、`POKEDEX[name].abilities` によるポケモンが持てる特性の確認 | 導入 |
| `01_basics/05_hazards_and_explicit_commands.py` | 設置技（ステルスロック）・交代誘発技（とんぼがえり）の効果、`Command.get_switch_command()` / `get_terastal_command()` / `get_megaevol_command()` による交代・テラスタル・メガシンカコマンドの明示的な組み立て、わるあがき（PP切れ）の挙動 | 導入 |
| `02_ai/01_custom_player.py` | `Player` を継承した最小のカスタム方策（`choose_command()` のオーバーライド） | AI開発 |
| `02_ai/02_selection_customization.py` | `choose_selection()` のオーバーライドによる選出順のカスタマイズ | AI開発 |
| `02_ai/03_tree_search_ai.py` | `TreeSearchPlayer` を継承した木探索AIとランダム方策の対戦 | AI開発（発展） |
| `02_ai/04_priority_and_command_debug.py` | 優先度技・素早さ操作技（トリックルーム）が行動順に与える影響、`TreeSearchPlayer.evaluate_commands()` によるコマンド候補・評価値のデバッグ確認 | AI開発（発展） |
| `03_damage_calc/01_basic_lethal_calculation.py` | `battle.calc_lethal()` による確定数・乱数ダメージの基本計算、努力値、`Pokemon.show()` | ダメージ計算ツール開発 |
| `03_damage_calc/02_ailment_and_scenario_comparison.py` | `set_ailment()` / `modify_hp()` / `modify_stats()` / `faint()` でシナリオを組み立てた致死率比較 | ダメージ計算ツール開発 |
| `03_damage_calc/03_raw_damage_rolls.py` | `calc_damages()` / `roll_damage()` による生ダメージロールの確認、`damage_roll` / `critical_mode` による固定ロール | ダメージ計算ツール開発 |
| `03_damage_calc/04_multi_hit_and_combo_moves.py` | `Move.expected_hits`（連続技の期待ヒット数）、複数技を組み合わせる（`moves=[...]`） | ダメージ計算ツール開発 |
| `03_damage_calc/05_secondary_effects.py` | `secondary=True` による追加効果込みの確定数短縮 | ダメージ計算ツール開発 |
| `03_damage_calc/06_field_effects.py` | 天候（すなあらし）・地形（エレキフィールド）の効果 | ダメージ計算ツール開発 |
| `03_damage_calc/07_ailment_and_volatile.py` | 技を実際に当てて状態異常を発生させる方法、`battle.set_volatile()` による揮発性状態（やどりぎのタネ）の直接付与、`effect_chance_threshold` による追加効果発動確率の固定 | ダメージ計算ツール開発 |
| `03_damage_calc/08_ability_and_item_logs.py` | `battle.step()` を伴う進行での特性・アイテムの発動ログ確認 | ダメージ計算ツール開発 |
| `03_damage_calc/09_testing_helpers.py` | `jpoke.testing` の `start_battle()` / `apply_ailment()` / `run_move()` / `calc_lethal()` による、定型的なセットアップを短く書くショートカット | ダメージ計算ツール開発 |
| `03_damage_calc/10_form_change_comparison.py` | `Pokemon.set_form()` によるフォルム変化（ロトムの姿）がタイプ・種族値の違いを通じてダメージ・致死率に与える影響の比較 | ダメージ計算ツール開発 |
| `04_research/01_bulk_simulation.py` | `Player.battle_against()` による多数回対戦・構成比較 | 戦術研究（構成比較） |
| `04_research/02_replay.py` | `Battle.build_replay_data()` / `ReplayPlayer` / `replay_battle()` によるリプレイの記録・再生 | 戦術研究（対戦の記録・解析） |
| `04_research/03_janken_nash_cfr.py` | `Battle.copy()` を使ったロールアウトベースのregret matching（CFR風）による、HP状況に応じた適応的な戦略の自己対戦学習 | 戦術研究（読み合いの定量分析、発展） |
| `04_research/04_janken_nash_fictitious_play.py` | 実バトルのモンテカルロ推定 + 反復最適反応（fictitious play）によるNash均衡（固定の混合戦略）の近似、`ProcessPoolExecutor` による並列化 | 戦術研究（読み合いの定量分析、発展） |
| `05_benchmark/01_step_time_benchmark.py` | 完全ランダムな3vs3全選出バトルを繰り返し実行し、`Battle.step()` 1回あたりの所要時間（mean ± σ）を計測 | 計算速度の計測 |

`04_research/03_janken_nash_cfr.py` / `04_research/04_janken_nash_fictitious_play.py` は
多数回のバトルシミュレーションを行うため、他のサンプルより実行に時間がかかる
（手元ではそれぞれ数十秒・十数秒程度）。
