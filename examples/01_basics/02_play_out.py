"""Battle と Player を直接使い、最小構成でバトルを実行する。

ピカチュウ vs フシギダネの1体ずつのバトルを最後まで進め、勝者とログを表示する。

01の battle_against() は「多数回対戦させて勝率を見る」用途に向くが、Battle/Player
を直接扱いたい場合は battle.play_out() で決着まで自動的に進められる。ターンごとに
手動でstep()を呼びながら中身を観察する方法は03_team_battle.py以降で示す。
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

    # play_out()は未開始ならstart()を行い、決着がつくかターン上限に達するまで
    # 自動的にstep()を繰り返す（戻り値はNone。結果はbattle.winner等から取得する）
    battle.play_out(max_turns=100)

    battle.print_logs("all")

    winner = battle.winner
    print(f"勝者: {winner.username if winner else '引き分け'}")

    # 試してみよう: player1 の技を "ひのこ" に変えると、決着までのターン数がどう変わるか観察できる


if __name__ == "__main__":
    main()
