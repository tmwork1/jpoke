"""jpoke で学べること: Battle / Player / Pokemon だけを使った最小構成のバトル実行。

ピカチュウ vs フシギダネの1体ずつのバトルを最後まで進め、勝者とログを表示する。
README のクイックスタートと同内容。
"""
from __future__ import annotations

from jpoke import Battle, Player, Pokemon


def main() -> None:
    player1 = Player("Player 1")
    player1.team.append(Pokemon("ピカチュウ", move_names=["でんこうせっか"]))

    player2 = Player("Player 2")
    player2.team.append(Pokemon("フシギダネ", move_names=["たいあたり"]))

    # n_selected: 選出数（チームが1匹だけの場合は1にする。デフォルトは3）
    # seed: 乱数シードを固定し、命中判定・急所判定などを再現可能にする
    battle = Battle((player1, player2), n_selected=1, seed=1)
    battle.start()

    while battle.judge_winner() is None and battle.turn < 100:
        # commands=None の場合は各 Player.choose_command() が使われる
        # （デフォルト実装は利用可能な最初のコマンドを選ぶだけの単純なプレイヤー）
        battle.step()

    winner = battle.judge_winner()
    print(f"勝者: {winner.username if winner else '引き分け（ターン上限）'}")
    battle.print_logs()  # 最終ターンのログを表示


if __name__ == "__main__":
    main()
