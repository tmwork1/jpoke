"""
同時に死に出しする場合の木探索の例
"""

from itertools import product

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command


class SearchPlayer(Player):
    def choose_command(self, battle: Battle) -> Command:
        print(f"[depth={battle.copy_depth}] Choosing switch command for {self.name}")

        if battle.copy_depth > 1:
            raise ValueError("木探索の深さが2を超えています。")

        my_commands = battle.get_available_commands(self)
        if battle.phase == "action":
            return my_commands[0]

        self_state = battle.player_states[self]
        opponent = battle.opponent(self)
        opponent_state = battle.player_states[opponent]

        assert self_state.required_command_type == "switch"
        assert opponent_state.required_command_type is None
        assert not opponent_state.reserved_commands

        opponent_commands = battle.get_available_commands(opponent)

        print(f"- Self available commands: {[cmd.name for cmd in my_commands]}")
        print(f"- Rival available commands: {[cmd.name for cmd in opponent_commands]}")

        # コマンドの組み合わせを総当たりで評価する
        print("-"*20)
        for my_cmd, opponent_cmd in product(my_commands, opponent_commands):
            print(f"\n<< Simulation {my_cmd} vs {opponent_cmd} >>")
            sim = battle.copy()
            commands = {self: my_cmd, opponent: opponent_cmd}
            sim.step(commands)
            sim.print_logs()
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
        Pokemon("ヒトカゲ", item_name="いのちのたま", move_names=["たいあたり"]),
        Pokemon("リザード", item_name="", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(name="RandomPlayer")
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
        print(f"結果: {winner.name} 勝利（{turn}ターン）")


if __name__ == "__main__":
    main()
