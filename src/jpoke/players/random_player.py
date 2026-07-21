"""合法手からランダムに選ぶだけのプレイヤー。

`Player.choose_command()` の既定実装（常に先頭のコマンドを選ぶ決定的挙動）の
代わりに使う、統計比較・ベースライン対戦向けの標準実装。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


class RandomPlayer(Player):
    """比較対象・ベースラインとして使う、合法手からランダムに選ぶだけのプレイヤー。

    `battle.decision_random`（行動選択専用の乱数系列）を使って選ぶため、
    `Battle(seed=...)` による再現性を壊さない。`Player.battle_against()` で
    複数回対戦して統計比較する場合、既定の `Player.choose_command()`（常に
    先頭のコマンドを選ぶ決定的挙動）では展開の分散が潰れてしまうため、
    対戦相手やベースラインとしてこのクラスを使うとよい。選出も
    `Player.choose_selection()`（先頭から順に選出）の代わりにランダムに選ぶ。
    """

    def choose_selection(self, battle: Battle) -> list[int]:
        """選出可能な `battle.n_selected` 匹を `battle.decision_random` でランダムに選ぶ。"""
        return battle.decision_random.sample(range(len(self.team)), battle.n_selected)

    def choose_command(self, battle: Battle) -> Command:
        """利用可能なコマンドから `battle.decision_random` でランダムに1つ選ぶ。"""
        return battle.decision_random.choice(battle.available_commands(self))
