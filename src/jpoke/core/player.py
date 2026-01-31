from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.utils.enums import Command, Interrupt
from jpoke.utils import fast_copy


class Player:
    MAX_RESERVED = 10

    def __init__(self, name: str = ""):
        self.name = name

        self.team: list[Pokemon] = []
        self.n_game: int = 0
        self.n_won: int = 0
        self.rating: float = 1500

        # ゲーム状態
        self.selection_idxes: list[int] = []
        self.active_idx: int | None = None
        self.interrupt: Interrupt = Interrupt.NONE
        self.reserved_commands: list[Command] = []

        # ターン状態
        self.has_switched: bool = False

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new, keys_to_deepcopy=["team"])

    def init_game(self):
        """ゲーム状態をリセットする。

        選出、場のポケモン、割り込み状態、予約コマンドをクリアし、
        ターン状態もリセットする。
        """
        self.selection_idxes = []
        self.active_idx = None
        self.interrupt = Interrupt.NONE
        self.reserved_commands = []

        self.init_turn()

        for mon in self.team:
            mon.init_game()

    def init_turn(self):
        """ターン状態をリセットする。

        交代フラグをクリアする。
        """
        self.has_switched = False

    def reserve_command(self, command: Command):
        """コマンドを予約する。"""
        if len(self.reserved_commands) >= self.MAX_RESERVED:
            raise RuntimeError(f"予約上限({self.MAX_RESERVED})を超えました")
        self.reserved_commands.append(command)

    def choose_selection_commands(self, battle: Battle) -> list[Command]:
        """選出コマンドを選択する。

        デフォルト実装では利用可能な選出コマンドからチームサイズ分を返す。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された選出コマンドのリスト
        """
        n = len(self.team)
        return battle.get_available_selection_commands(self)[:n]

    def choose_action_command(self, battle: Battle) -> Command:
        """行動コマンドを選択する。

        デフォルト実装では利用可能な行動コマンドの最初の1つを返す。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された行動コマンド
        """
        return battle.get_available_action_commands(self)[0]

    def choose_switch_command(self, battle: Battle) -> Command:
        """交代コマンドを選択する。

        デフォルト実装では利用可能な交代コマンドの最初の1つを返す。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された交代コマンド
        """
        return battle.get_available_switch_commands(self)[0]

    @property
    def active(self) -> Pokemon | None:
        """現在場に出ているポケモンを取得する。

        Returns:
            場に出ているポケモン。いない場合はNone
        """
        if self.active_idx is not None:
            return self.team[self.active_idx]

    @property
    def selection(self) -> list[Pokemon]:
        """選出したポケモンのリストを取得する。

        Returns:
            選出されたポケモンのリスト
        """
        return [self.team[i] for i in self.selection_idxes]

    def can_use_terastal(self) -> bool:
        """テラスタルが使用可能かどうかを判定する。

        選出したポケモン全てがテラスタルしていない場合に使用可能。

        Returns:
            テラスタルが使用可能な場合True
        """
        return all(not mon.is_terastallized for mon in self.selection)
