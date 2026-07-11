"""合法手からランダムに選ぶだけのプレイヤー。

`Player.choose_command()` の既定実装（常に先頭のコマンドを選ぶ決定的挙動）の
代わりに使う、統計比較・ベースライン対戦向けの標準実装。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


class RandomPlayer(Player):
    """比較対象・ベースラインとして使う、合法手からランダムに選ぶだけのプレイヤー。

    `battle.random`（各対戦固有の乱数系列）を使って選ぶため、`Battle(seed=...)`
    による再現性を壊さない。`Player.battle_against()` で複数回対戦して統計比較
    する場合、既定の `Player.choose_command()`（常に先頭のコマンドを選ぶ決定的
    挙動）では展開の分散が潰れてしまうため、対戦相手やベースラインとして
    このクラスを使うとよい。
    """

    def choose_command(self, battle: Battle) -> Command:
        """利用可能なコマンドから `battle.random` でランダムに1つ選ぶ。"""
        return battle.random.choice(battle.get_available_commands(self))
