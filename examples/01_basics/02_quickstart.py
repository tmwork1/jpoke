"""Battle と Player だけを使い、最小構成でバトルを実行する。

ピカチュウ vs フシギダネの1体ずつのバトルを最後まで進め、勝者とログを表示する。
README のクイックスタートと同内容。

01の battle_against() は「多数回対戦させて勝率を見る」用途に向くが、1回の対戦を
ターンごとに手動で進めながら中身を観察したい場合はこちらのように Battle / Player を
直接使う。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    player1 = Player("Player 1")
    player1.add_pokemon("ヒトカゲ", move_names=["ひっかく"])

    player2 = Player("Player 2")
    player2.add_pokemon("フシギダネ", move_names=["たいあたり"])

    # n_selected: 省略時は min(3, チームの手持ち数) が自動設定される（ここでは1）
    # seed: 乱数シードを固定し、命中判定・急所判定などを再現可能にする
    battle = Battle(player1, player2, seed=1)

    # start() は選出と初期繰り出し（先頭のポケモンを場に出す処理）を完了させ、
    # 以降 step() でターンを進められる状態にする
    battle.start()

    # 決着がつくかターン上限に達するまで手動でstep()する
    # （バトルを最後まで自動的に進めたいだけなら battle.play_out() も使える）
    while not battle.finished and battle.turn < 100:
        battle.step()

    battle.print_logs("all")

    winner = battle.winner
    print(f"勝者: {winner.username if winner else '引き分け（ターン上限）'}")

    # 試してみよう: player1 の技を "ひのこ" に変えると、決着までのターン数がどう変わるか観察できる


if __name__ == "__main__":
    main()
