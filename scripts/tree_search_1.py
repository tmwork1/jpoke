"""
行動選択の方策関数で木探索を行うテスト
"""

from itertools import product

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command


class SearchPlayer(Player):
    def choose_action_command(self, battle: Battle) -> Command:
        """行動コマンドを選択する（利用可能なコマンドからランダムに選択）。"""
        print(f"[depth={battle.copy_depth}] Choosing action command")

        # 木探索のために相手の情報を補完する
        rival = battle.rival(self)
        required_command_type = battle.complete(rival)
        assert required_command_type == "action"

        my_commands = battle.get_available_action_commands(self)
        rival_state = battle.player_states[rival]
        rival_commands = battle.get_available_action_commands(rival)

        # complete直後は予約コマンドが存在しないことを確認する
        assert not rival_state.reserved_commands

        print()
        print(f"My commands: {[cmd.name for cmd in my_commands]}")
        print(f"Rival commands: {[cmd.name for cmd in rival_commands]}")
        print(f"Rival moves: {[m.name for m in rival_state.active.moves]}")

        # コマンドの組み合わせを総当たりで評価する
        print("-"*20)
        for my_cmd, rival_cmd in product(my_commands, rival_commands):
            print(f"<< Simulation {my_cmd} vs {rival_cmd} >>")
            sim = battle.copy()
            commands = {self: my_cmd, rival: rival_cmd}
            sim.step(commands)
            sim.print_logs()
            print()
            # break
        print(f"{'-'*20}")

        return my_commands[0]

    def choose_switch_command(self, battle: Battle) -> Command:
        """交代コマンドを選択する（利用可能なコマンドからランダムに選択）。"""
        print(f"[depth={battle.copy_depth}] Choosing switch command for {self.name}")
        my_commands = battle.get_available_switch_commands(self)
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
        # Pokemon("リザード", item_name="", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(name="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        # Pokemon("カメール", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]

    # バトルを作成・実行
    battle = Battle((player1, player2), n_selected=2, seed=seed)

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
