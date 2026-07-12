"""jpoke で学べること: Battle / Player だけを使った最小構成のバトル実行。

ピカチュウ vs フシギダネの1体ずつのバトルを最後まで進め、勝者とログを表示する。
README のクイックスタートと同内容。
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

    # 選出と初期繰り出しを行い、対戦を開始する
    battle.start()

    # 決着がつくかターン上限に達するまで手動でstep()する
    # （バトルを最後まで自動的に進めたいだけなら battle.play_out() も使える）
    while not battle.finished and battle.turn < 100:
        # commands=None の場合は各 Player.choose_command() が使われる
        # （デフォルト実装は利用可能な最初のコマンドを選ぶだけの単純なプレイヤー）
        battle.step()

    winner = battle.winner
    print(f"勝者: {winner.username if winner else '引き分け（ターン上限）'}")
    battle.print_logs("all")  # 1ターン目から現在ターンまでの全ログを表示

    # 試してみよう: player1 の技を "ひのこ" に変えると、決着までのターン数がどう変わるか観察できる


if __name__ == "__main__":
    main()
