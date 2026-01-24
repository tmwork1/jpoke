from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core.battle import Battle
    from jpoke.model.pokemon import Pokemon

from jpoke.utils.enums import Command, Interrupt
from jpoke.utils import fast_copy


class Player:
    def __init__(self, name: str = ""):
        self.name = name

        self.team: list[Pokemon] = []
        self.n_game: int = 0
        self.n_won: int = 0
        self.rating: float = 1500

        self.reset_game()

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new, keys_to_deepcopy=["team"])

    def reset_game(self):
        self.selection_idxes: list[int] = []
        self.active_idx: int = None  # type: ignore
        self.interrupt: Interrupt = Interrupt.NONE
        self.reserved_commands: list[Command] = []

        self.reset_turn()

    def reset_turn(self):
        self.has_switched = False

    def reserve_command(self, command: Command) -> Command:
        self.reserved_commands.append(command)
        return self.reserved_commands[-1]

    def choose_selection_commands(self, battle: Battle) -> list[Command]:
        n = min(3, len(self.team))
        return battle.get_available_selection_commands(self)[:n]

    def choose_action_command(self, battle: Battle) -> Command:
        return battle.get_available_action_commands(self)[0]

    def choose_switch_command(self, battle: Battle) -> Command:
        return battle.get_available_switch_commands(self)[0]

    @property
    def active(self) -> Pokemon | None:
        if self.active_idx is not None:
            return self.team[self.active_idx]
        return None

    @property
    def selection(self) -> list[Pokemon]:
        return [self.team[i] for i in self.selection_idxes]

    def can_use_terastal(self) -> bool:
        return all(mon.can_terastallize() for mon in self.selection)
