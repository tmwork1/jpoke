# examples

`pip install jpoke` だけで実行できる、導入・学習用のサンプルスクリプト集。
`jpoke.*` の公開APIのみに依存しており、リポジトリを clone しなくても動く。

```bash
pip install jpoke
python examples/01_quickstart.py
```

| ファイル | 学べる内容 | 対応ユースケース |
|---|---|---|
| `01_quickstart.py` | `Battle` / `Player` を使った最小構成の1vs1バトル | 導入 |
| `02_team_battle.py` | 3体チーム・複数選出・複数ターンのバトルループ・ログ確認 | 導入 |
| `03_custom_player.py` | `Player` を継承した最小のカスタム方策 | AI開発 |
| `04_damage_calculation.py` | `battle.calc_lethal()` による確定数・乱数ダメージ計算 | ダメージ計算ツール開発 |
| `05_tree_search_ai.py` | `TreeSearchPlayer` を継承した木探索AIとランダム方策の対戦 | AI開発（発展） |
| `06_bulk_simulation.py` | `Player.battle_against()` による多数回対戦・構成比較 | 戦術研究（構成比較） |
