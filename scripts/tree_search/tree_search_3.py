"""
同時に死に出しする場合の木探索の例（framework.TreeSearchPlayer の利用例）

両者の先頭が同時に瀕死になるシナリオ。この場合 required_command_type は
どちらの側も None（自分は switch、相手は「後攻」ではないため絞り込みが働かない）
になる。
"""

from jpoke import Battle, Player, Pokemon
from jpoke.players import TreeSearchPlayer


def play_game(seed: int | None = None,
              max_turns: int = 100) -> tuple[Player | None, int]:
    """1ゲーム実行して、勝者とターン数を返す。

    Args:
        seed: 乱数シード（Noneの場合はランダム）
        max_turns: 最大ターン数

    Returns:
        (勝者のPlayerインスタンス または None（引き分け）, ターン数)
    """
    # Player 1（1手先の総当たり探索）
    player1 = TreeSearchPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="いのちのたま", move_names=["たいあたり"]),
        Pokemon("リザード", item_name="", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメール", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]

    # 相手のポケモンを公開する
    player2.team[2].revealed = True

    # 先頭のポケモンのHPを1にする
    player1.team[0].hp = 1
    player2.team[0].hp = 1

    # バトルを作成・実行
    battle = Battle((player1, player2), n_selected=len(player1.team), seed=seed)

    battle.start()

    while True:
        print(f"--- ターン {battle.turn} ---")
        battle.step()
        battle.print_logs()
        winner = battle.judge_winner()
        if winner is not None or battle.turn >= max_turns:
            break

    return winner, battle.turn


def main():
    winner, turn = play_game(max_turns=1)

    if winner is None:
        print(f"結果: 引き分け（{turn}ターン）")
    else:
        print(f"結果: {winner.username} 勝利（{turn}ターン）")


if __name__ == "__main__":
    main()
