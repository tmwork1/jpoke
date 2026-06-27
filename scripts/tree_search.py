"""
ランダムに生成したポケモンを1体ずつ出して戦うスクリプト
ポケモン、特性、アイテム、技をランダムに選ぶ
"""

from __future__ import annotations

from itertools import product

from jpoke import Battle, Player, Pokemon
from jpoke.data.pokedex import POKEDEX
from jpoke.data.ability import ABILITIES
from jpoke.data.item import ITEMS
from jpoke.data.move import MOVES
from jpoke.enums import Command


class SearchPlayer(Player):
    def choose_action_command(self, battle: Battle) -> Command:
        """行動コマンドを選択する（利用可能なコマンドからランダムに選択）。"""
        print(f"[depth={battle.depth}] Choosing action command for {self.name}")
        player_index = battle.players.index(self)
        my_commands = battle.get_available_action_commands(self)
        return my_commands[0]

        rival = battle.rival(self)
        rival_commands = battle.get_available_action_commands(rival)

        # コマンドの組み合わせを総当たりで評価する
        for my_cmd, rival_cmd in product(my_commands, rival_commands):
            print(f"\tSimulation {my_cmd} vs {rival_cmd}")
            # コマンドの組み合わせごとにBattleのコピーを作成してシミュレーション
            sim = battle.build_observation()
            sim_player = sim.players[player_index]
            sim_rival = sim.rival(sim_player)
            commands = {sim_player: my_cmd, sim_rival: rival_cmd}
            sim.step(commands)
            break

        return my_commands[0]

    def choose_switch_command(self, battle: Battle) -> Command:
        """交代コマンドを選択する（利用可能なコマンドからランダムに選択）。"""
        print(f"[depth={battle.depth}] Choosing switch command for {self.name}")
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
        Pokemon("リザード", item_name="", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(name="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメール", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]

    # バトルを作成・実行
    battle = Battle((player1, player2), seed=seed)

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
