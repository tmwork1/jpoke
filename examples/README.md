# examples

`pip install jpoke` だけで実行できる、導入・学習用のサンプルスクリプト集。
`jpoke.*` の公開APIのみに依存しており、リポジトリを clone しなくても動く。

```bash
pip install jpoke
python examples/01_basics/01_quickstart.py
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

## ファイル一覧

| ファイル | 学べる内容 | 対応ユースケース |
|---|---|---|
| `01_basics/01_quickstart.py` | `Battle` / `Player` を使った最小構成の1vs1バトル | 導入 |
| `01_basics/02_team_battle.py` | 3体チーム・複数選出・複数ターンのバトルループ・ログ確認 | 導入 |
| `02_ai/01_custom_player.py` | `Player` を継承した最小のカスタム方策 | AI開発 |
| `02_ai/02_tree_search_ai.py` | `TreeSearchPlayer` を継承した木探索AIとランダム方策の対戦 | AI開発（発展） |
| `03_damage_calc/01_damage_calculation.py` | `battle.calc_lethal()` による確定数・乱数ダメージ計算 | ダメージ計算ツール開発 |
| `04_research/01_bulk_simulation.py` | `Player.battle_against()` による多数回対戦・構成比較 | 戦術研究（構成比較） |
| `04_research/02_replay.py` | `Battle.build_replay_data()` / `ReplayPlayer` / `replay_battle()` によるリプレイの記録・再生 | 戦術研究（対戦の記録・解析） |
| `04_research/03_janken_nash_fictitious_play.py` | 実バトルのモンテカルロ推定 + 反復最適反応（fictitious play）によるNash均衡（混合戦略）の近似、`ProcessPoolExecutor` による並列化 | 戦術研究（読み合いの定量分析、発展） |
| `04_research/04_janken_nash_cfr.py` | `Battle.copy()` を使ったロールアウトベースのregret matching（CFR風）による、HP状況に応じた適応的な戦略の自己対戦学習 | 戦術研究（読み合いの定量分析、発展） |

`04_research/03_janken_nash_fictitious_play.py` / `04_research/04_janken_nash_cfr.py` は
多数回のバトルシミュレーションを行うため、他のサンプルより実行に時間がかかる
（手元ではそれぞれ十数秒・数十秒程度）。
