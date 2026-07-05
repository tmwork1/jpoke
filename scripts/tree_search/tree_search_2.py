"""
自分が先攻でとんぼがえりを使う場合の木探索の例（framework.TreeSearchPlayer の利用例）

CRIT-1（相手のベンチが公開済みの状態で switch フェーズに入ると、修正前は
required_command_type でフィルタされない SWITCH コマンドが混入し sim.step() が
ValueError で落ちていた）の回帰確認も兼ねる。相手チームのベンチ（カメックス）を
あえて公開済みにしている。
"""

import random

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command

from framework import TreeSearchPlayer


class RandomPlayer(Player):
    def choose_command(self, battle: Battle) -> Command:
        commands = battle.get_available_commands(self)
        return random.choice(commands)


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
    player1 = TreeSearchPlayer(name="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["とんぼがえり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = RandomPlayer(name="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり", "なきごえ", "しっぽをふる"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]

    # 先頭以外の技を公開する
    for i in range(1, 3):
        player2.team[0].moves[i].revealed = True

    # ベンチ（カメックス）を公開済みにする（CRIT-1の再現条件）
    player2.team[1].revealed = True

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
        print(f"結果: {winner.name} 勝利（{turn}ターン）")


if __name__ == "__main__":
    main()
