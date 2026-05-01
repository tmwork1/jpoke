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


def build_random_pokemon(name: str | None = None,
                         ability: str | None = None,
                         item: str | None = None,
                         moves: list[str] | None = None,
                         n_moves: int = 1) -> Optional[Pokemon]:
    """ランダムなポケモンを構築する。

    Args:
        n_moves: 技の数

    Returns:
        構築されたPokemonインスタンス、またはランダム選択に失敗した場合はNone
    """
    # ランダムなポケモンを選択
    if name is None:
        pokemon_names = list(pokedex.keys())
        name = random.choice(pokemon_names)

    # ランダムな特性を選択
    if ability is None:
        ability_names = list(ABILITIES.keys())
        ability = random.choice(ability_names)

    # ランダムなアイテムを選択
    if item is None:
        item_names = list(ITEMS.keys())
        item = random.choice(item_names)

    # ランダムな技を選択
    if moves is None:
        move_names = list(MOVES.keys())
        moves = random.sample(move_names, n_moves)

    # ポケモンを構築
    mon = Pokemon(name, ability=ability, item=item, moves=moves)
    return mon


def play_game(seed: int = None, max_turns: int = 10) -> tuple[Player | None, int]:
    """1ゲーム実行して、勝者とターン数を返す。

    Args:
        seed: 乱数シード（Noneの場合はランダム）
        max_turns: 最大ターン数

    Returns:
        (勝者のPlayerインスタンス または None（引き分け）, ターン数)
    """
    names = [None, None]
    abilities = [None, None]
    items = [None, None]
    moves = [None, None]

    players = []
    for i in range(2):
        players.append(RandomPlayer(name=f"Player{i+1}"))
        mon = build_random_pokemon(
            name=None,
            ability=None,
            item=None,
            moves=None,
            n_moves=1,
        )
        if mon is None:
            raise ValueError("ランダムなポケモンの構築に失敗しました。")
        mon.show()
        players[i].team.append(mon)

    # バトルを作成・実行
    battle = Battle(players, seed=seed)
    battle.start()

    while (winner := battle.judge_winner()) is None:
        battle.advance_turn()
        battle.print_logs()
        print("-" * 50)
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
