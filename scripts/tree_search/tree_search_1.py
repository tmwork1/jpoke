"""
行動選択の方策関数で木探索を行うテスト
"""

from itertools import product

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command


class SearchPlayer(Player):
    def choose_command(self, battle: Battle) -> Command:
        print(f"[depth={battle.copy_depth}] Choosing action command")

        if battle.copy_depth > 1:
            raise ValueError("木探索の深さが2を超えています。")

        self_state = battle.player_states[self]
        opponent = battle.opponent(self)
        opponent_state = battle.player_states[opponent]

        assert self_state.required_command_type == "any"
        assert opponent_state.required_command_type == "any"
        assert not opponent_state.reserved_commands

        my_commands = battle.get_available_commands(self)
        opponent_commands = battle.get_available_commands(opponent)

        print(f"- Self available commands: {[cmd.name for cmd in my_commands]}")
        print(f"- Rival available commands: {[cmd.name for cmd in opponent_commands]}")
        print(f"- Rival moves: {[m.name for m in opponent_state.active.moves]}")

        # コマンドの組み合わせを総当たりで評価する
        print("-"*20)
        for my_cmd, opponent_cmd in product(my_commands, opponent_commands):
            print(f"<< Simulation {my_cmd} vs {opponent_cmd} >>")
            commands = {self: my_cmd, opponent: opponent_cmd}
            sim = battle.copy()
            sim.step(commands)
            sim.print_logs()
            print()
            # break
        print(f"{'-'*20}")

        return my_commands[0]


def play_game(seed: int | None = None,
              max_turns: int = 100) -> tuple[Player | None, int]:
    """1ゲーム実行して、勝者とターン数を返す。

    Args:
        seed: 乱数シード（Noneの場合はランダム）
        max_turns: 最大ターン数

    Returns:
        (勝者のPlayerインスタンス または None（引き分け）, ターン数)
    """
    # Player 1
    player1 = SearchPlayer(name="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(name="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]
    player2.team[0].moves[0].revealed = True  # 相手の技を公開する

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
