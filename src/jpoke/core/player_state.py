from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Player
    from jpoke.model import Pokemon

from copy import deepcopy

from jpoke.types import CommandType
from jpoke.utils import fast_copy
from jpoke.enums import Command, Interrupt


class PlayerState:
    """対戦中のプレイヤー状態。"""

    def __init__(self, player: Player):
        self.team: list[Pokemon] = deepcopy(player.team)
        self._hide_initial_effects()
        self.selected_indexes: list[int] = []
        self.active_index: int | None = None
        self.reserved_commands: list[Command] = []
        self.last_available_commands: list[Command] = []  # 最後に利用可能だったコマンドのリスト
        self.required_command_type: CommandType | None = None  # 木探索を行う際に補完すべきコマンドタイプ（Noneの場合は補完不要）
        self.interrupt: Interrupt = Interrupt.NONE
        self.has_switched: bool = False
        self.switched_in_by_faint: bool = False  # 今ターン瀕死交代（死に出し）で場に出たか（はりこみ用）
        self.baton_pass_data: dict = {}  # バトンタッチの引き継ぎデータ
        self.last_move_succeeded: bool | None = None  # このターンの技が成功したか（未実行ならNone）
        self.ally_fainted_turn: int | None = None  # 味方が直近にひんしになったターン（かたきうち用）
        self.total_fainted_count: int = 0  # その戦闘で自分側のポケモンがひんしになった延べ回数（そうだいしょう用。復活しても減らず、再度ひんしになれば加算される）

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=["team"])
        return new

    def _hide_initial_effects(self):
        """バトル開始時点で特性・アイテム・技を未公開状態にする。

        `GameEffect.revealed` は「作られた時点では真の情報として既知」を
        既定とするため（テスト用に直接 `Ability(name)` 等を組み立てる場合も
        既知の値として扱える）、相手に対して未公開にする処理はバトル専用の
        状態としてここで明示的に行う。
        """
        for mon in self.team:
            mon.ability.revealed = False
            mon.item.revealed = False
            for move in mon.moves:
                move.revealed = False

    def reset_turn_state(self):
        """ターン状態を初期化する。"""
        self.has_switched = False
        self.switched_in_by_faint = False
        self.last_move_succeeded = None
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
        return [self.team[i] for i in self.selected_indexes]

    @property
    def bench(self) -> list[Pokemon]:
        """控えの選出ポケモンのリストを取得する。"""
        active = self.active
        selection = self.selection
        return [mon for mon in selection if mon is not active]

    def reserve_command(self, command: Command):
        """コマンドを予約する。"""
        self.reserved_commands.append(command)

    def command_reserved(self) -> bool:
        """予約コマンドが存在するかどうかを判定する。"""
        return bool(self.reserved_commands)

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
