from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Player
    from jpoke.model import Pokemon

from copy import deepcopy

from jpoke.utils import fast_copy
from jpoke.enums import Command, Interrupt


class PlayerState:
    """対戦中のプレイヤー状態。"""

    def __init__(self, player: Player):
        self.team: list[Pokemon] = deepcopy(player.team)
        self.selection_indexes: list[int] = []
        self.active_index: int | None = None
        self.reserved_commands: list[Command] = []
        self.interrupt: Interrupt = Interrupt.NONE
        self.has_switched: bool = False
        self.action_order_index: int | None = None
        self.inherit_migawari: bool = False

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=["team"])
        return new

    def reset_turn_state(self):
        """ターン状態を初期化する。"""
        self.has_switched = False
        self.action_order_index = None
        self.active.reset_turn_state()

    @property
    def active(self) -> Pokemon:
        """現在場に出ているポケモンを取得する。"""
        if self.active_index is not None:
            return self.team[self.active_index]
        raise ValueError("No active Pokemon found.")

    @property
    def selection(self) -> list[Pokemon]:
        """選出されているポケモンのリストを取得する。"""
        return [self.team[i] for i in self.selection_indexes]

    @property
    def bench(self) -> list[Pokemon]:
        """控えの選出ポケモンのリストを取得する。"""
        active = self.active
        selection = self.selection
        return [mon for mon in selection if mon is not active]

    def reserve_command(self, command: Command):
        """コマンドを予約する。"""
        self.reserved_commands.append(command)

    @property
    def next_command(self) -> Command:
        """次に実行するコマンドを取得する。"""
        if self.reserved_commands:
            return self.reserved_commands[0]
        raise ValueError("No reserved commands found.")

    def pop_command(self) -> Command:
        """次に実行するコマンドを取得し、予約リストから削除する。"""
        if self.reserved_commands:
            return self.reserved_commands.pop(0)
        raise ValueError("No reserved commands found.")

    def clear_reserved_commands(self):
        """予約済みコマンドをクリアする。"""
        self.reserved_commands.clear()

    def has_interrupt(self) -> bool:
        """割り込み状態かどうかを判定する。"""
        return self.interrupt != Interrupt.NONE

    def tod_score(self, alpha: float = 1) -> float:
        """プレイヤーのTime Over Death（TOD）スコアを計算。

        Args:
            alpha: HP割合の重み係数

        Returns:
            TODスコア（生存ポケモン数 + HP割合）
        """
        selection = self.selection
        n_alive, total_max_hp, total_hp = 0, 0, 0
        for mon in selection:
            total_max_hp += mon.max_hp
            total_hp += mon.hp
            if mon.hp:
                n_alive += 1
        return n_alive + alpha * total_hp / total_max_hp
