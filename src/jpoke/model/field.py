from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import EventManager, Player

from jpoke.utils import fast_copy
from jpoke.data.field import FIELDS
from jpoke.data.models import FieldData
from .effect import BaseEffect


class Field(BaseEffect):
    def __init__(self,
                 owners: list[Player],
                 name: str = "",
                 count: int = 0) -> None:
        super().__init__(FIELDS[name])
        self.data: FieldData  # IDE hint
        self.owners: list[Player] = owners
        self.count = count
        self.revealed = True

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new, keys_to_deepcopy=[])

    def update_reference(self, owners: list[Player]):
        self.owners = owners

    @property
    def name(self) -> str:
        return self.data.name if self.active and self.count else ""

    @property
    def turn_extention_item(self) -> str | None:
        return self.data.turn_extension_item

    @property
    def is_active(self) -> bool:
        return self.count > 0

    def can_activate(self) -> bool:
        return not self.is_active

    def activate(self, events: EventManager, count: int) -> bool:
        if not self.can_activate():
            return False
        self.count = count
        for player in self.owners:
            self.register_handlers(events, player)
        return True

    def deactivate(self, events: EventManager) -> bool:
        self.count = 0
        for player in self.owners:
            self.unregister_handlers(events, player)
        return True

    def tick(self, events: EventManager, by: int = 1) -> bool:
        if not self.is_active:
            return False
        self.count = max(0, self.count - by)
        if not self.count:
            self.deactivate(events)
        return True
