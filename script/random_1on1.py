"""
ランダムに生成したポケモンを1体ずつ出して戦うスクリプト
ポケモン、特性、アイテム、技をランダムに選ぶ
"""

from __future__ import annotations

import random
from typing import Optional

from jpoke import Battle, Player, Pokemon
from jpoke.data.pokedex import pokedex
from jpoke.data.ability import ABILITIES
from jpoke.data.item import ITEMS
from jpoke.data.move import MOVES
from jpoke.enums import Command


class RandomPlayer(Player):
    """毎ターン、利用可能なコマンドからランダムに選ぶプレイヤー。"""

    def choose_action_command(self, battle: Battle) -> Command:
        """行動コマンドを選択する（利用可能なコマンドからランダムに選択）。"""
        available_commands = battle.get_available_action_commands(self)
        return random.choice(available_commands)


def build_random_pokemon(n_moves: int) -> Optional[Pokemon]:
    """ランダムなポケモンを構築する。

    Args:
        n_moves: 技の数

    Returns:
        構築されたPokemonインスタンス、またはランダム選択に失敗した場合はNone
    """
    # ランダムなポケモンを選択
    pokemon_names = list(pokedex.keys())
    name = random.choice(pokemon_names)

    # ランダムな特性を選択
    ability_names = list(ABILITIES.keys())
    ability = random.choice(ability_names)

    # ランダムなアイテムを選択
    item_names = list(ITEMS.keys())
    item = random.choice(item_names)

    # ランダムな技を選択
    move_names = list(MOVES.keys())
    selected_moves = random.sample(move_names, n_moves)

    # ポケモンを構築
    mon = Pokemon(name, ability=ability, item=item, moves=selected_moves)
    return mon


def play_game(seed: int = None, max_turns: int = 10) -> tuple[Player | None, int]:
    """1ゲーム実行して、勝者とターン数を返す。

    Args:
        seed: 乱数シード（Noneの場合はランダム）
        max_turns: 最大ターン数

    Returns:
        (勝者のPlayerインスタンス または None（引き分け）, ターン数)
    """
    # プレイヤーを作成
    p0 = RandomPlayer(name="Player1")
    p1 = RandomPlayer(name="Player2")

    # ランダムなポケモンをチームに追加
    p0.team.append(build_random_pokemon(n_moves=1))
    p1.team.append(build_random_pokemon(n_moves=1))

    p0.team[0].show()
    p1.team[0].show()

    # バトルを作成・実行
    battle = Battle([p0, p1], seed=seed)
    battle.start()

    while (winner := battle.judge_winner()) is None:
        battle.advance_turn()
        battle.print_logs()
        if battle.turn == max_turns:
            break

    return winner, battle.turn


def main():
    """メイン実行関数。"""
    print("ランダムポケモン1on1バトル実行")
    print("=" * 50)

    winner, turn = play_game(max_turns=2)

    print("=" * 50)
    if winner is None:
        print(f"結果: 引き分け（{turn}ターン）")
    else:
        print(f"結果: {winner.name} 勝利（{turn}ターン）")
    print("=" * 50)


if __name__ == "__main__":
    main()
