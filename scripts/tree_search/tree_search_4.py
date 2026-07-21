"""
一般的な木探索の例（framework.MinimaxPlayer で複数手先を探索する例）

max_plies=2 を指定し、自分と相手それぞれ2手先まで総当たりで評価する。
探索中にとんぼがえり等で割り込み交代が発生し choose_command() が再帰的に
呼ばれた場合は、探索木には含めずフォールバック方策（既定ではランダム選択）で
即決する。
"""

from jpoke import Battle, Player, Pokemon
from jpoke.players import MinimaxPlayer


def play_game(seed: int | None = None,
              max_turns: int = 100) -> tuple[Player | None, int]:
    """1ゲーム実行して、勝者とターン数を返す。

    Args:
        seed: 乱数シード（Noneの場合はランダム）
        max_turns: 最大ターン数

    Returns:
        (勝者のPlayerインスタンス または None（引き分け）, ターン数)
    """
    # Player 1（2手先までの総当たり探索）
    player1 = MinimaxPlayer(username="SearchPlayer", max_plies=2)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["とんぼがえり"]),
        Pokemon("リザードン", item_name="", move_names=["とんぼがえり"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]

    # バトルを作成・実行
    battle = Battle(player1, player2, n_selected=len(player1.team), seed=seed)

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
    winner, turn = play_game(max_turns=2)

    if winner is None:
        print(f"結果: 引き分け（{turn}ターン）")
    else:
        print(f"結果: {winner.username} 勝利（{turn}ターン）")


if __name__ == "__main__":
    main()
