# チュートリアル

jpoke を初めて使う人向けに、インストールから最初の対戦・自作AIの作成までを順に進める。より深く知りたくなったら、末尾の「次の一歩」から目的別のサンプル・ドキュメントへ進める。

## 1. インストール

```bash
pip install jpoke
```

対応Pythonバージョンは3.11以降（`requires-python = ">=3.11"`）。ランタイム依存ライブラリが
ないため、インストール後はネットワーク接続なしに動作する。

## 2. 最初の一戦

`Player` を2体用意してポケモンを1匹ずつ持たせ、`Battle` に渡して `play_out()` で
決着まで自動的に進める。

```python
from jpoke import Player, Battle

player1 = Player("Player 1")
player1.add_pokemon("ヒトカゲ", moves=["ひっかく"])

player2 = Player("Player 2")
player2.add_pokemon("フシギダネ", moves=["たいあたり"])

battle = Battle(player1, player2, seed=1)
battle.play_out(max_turns=100)

battle.print_logs("all")
winner = battle.winner
print(f"勝者: {winner.username if winner else '引き分け'}")
```

技・特性・持ち物・種族値などを何も指定しなければ、そのポケモンの標準的な値が自動で
設定される。多数回対戦させて勝率を比較したいだけなら `Player.battle_against()`
（`examples/01_getting_started/01_quick_start.ipynb` 参照）の方が手軽である。

## 3. ターンを覗く

`play_out()` は決着まで一気に進めるが、`start()` + `step()` で1ターンずつ手動で
進めながら、`print_logs()` で何が起きたかをその都度確認できる。

```python
from jpoke import Battle
from jpoke.players import RandomPlayer

player1 = RandomPlayer("Team A")
player1.add_pokemon("ピカチュウ", ability="せいでんき", item="いのちのたま", moves=["かみなり"])

player2 = RandomPlayer("Team B")
player2.add_pokemon("ゼニガメ", ability="げきりゅう", item="オボンのみ", moves=["なみのり"])

battle = Battle(player1, player2, seed=1)
battle.start()  # 選出・初期繰り出しが行われる

while battle.can_continue(max_turns=30):
    battle.step()
    battle.print_logs()
    print("-" * 50)
```

`RandomPlayer` は合法手からランダムに行動を選ぶ `Player` の既定実装である。自作の方策を
まだ持っていない段階での動作確認に使える。

## 4. 自分のPlayerを作る

`Player` を継承して `choose_command()` をオーバーライドすると、独自の対戦AIになる。
現在の盤面（`battle`）から選べる行動の一覧は `battle.available_commands(self)` で
取得できる。

```python
from jpoke import Battle, Player
from jpoke.enums import Command

class MyPlayer(Player):
    def choose_command(self, battle: Battle) -> Command:
        commands = battle.available_commands(self)
        return battle.decision_random.choice(commands)  # まずはランダムに1つ選ぶ
```

ダメージが最大になる技を選ぶ、木探索で数手先まで読む、といった発展形は
`examples/01_getting_started/03_custom_player.ipynb`（`Battle.calc_damages()` を
使った最大火力方策）や `examples/02_tree_search/`（`MinimaxPlayer` を継承した
木探索AIのカスタマイズ）を参照。

## 5. 次の一歩

目的に応じて、以下から進むとよい。

| 知りたいこと | 参照先 |
|---|---|
| 基礎をもう少し広く知りたい | [`examples/01_getting_started/`](https://github.com/tmwork1/jpoke/blob/main/examples/README.md) — 本チュートリアルの元になった導入サンプル一式 |
| 対戦AIを開発したい | [`examples/02_tree_search/`](https://github.com/tmwork1/jpoke/blob/main/examples/README.md) — `MinimaxPlayer` を継承した木探索AIのカスタマイズ |
| 致死率・ダメージ計算がしたい | [`examples/03_lethal/`](https://github.com/tmwork1/jpoke/blob/main/examples/README.md) — `battle.calc_lethal()` による確定数・致死率計算 |
| 戦術研究（多数回対戦・ゲーム理論）がしたい | [`examples/05_advanced/`](https://github.com/tmwork1/jpoke/blob/main/examples/README.md) — 多数回対戦の統計比較、Nash均衡の近似など |
| メソッド名やコード例からクラスの使い方を早引きしたい | [早見表](quick_reference.md) |
| 全メソッド・全属性のシグネチャを網羅的に確認したい | [APIリファレンス](reference/index.md)（自動生成） |
