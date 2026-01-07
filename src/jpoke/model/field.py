from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import EventManager, Player

from jpoke.utils import fast_copy
from jpoke.data.field import FIELDS
from jpoke.data.models import FieldData
from .effect import BaseEffect


class Field(BaseEffect):
    def __init__(self, owners: list[Player], name: str = "", count: int = 0) -> None:
        self.owners: list[Player] = owners
        self.init(name, count)

    def init(self, name: str, count: int):
        super().__init__(FIELDS[name])
        self.count = count
        self.revealed = True
        self.data: FieldData

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

    def activate(self, events: EventManager, count: int):
        """フィールドを起動する"""
        self.count = count
        for player in self.owners:
            self.register_handlers(events, player)

    def deactivate(self, events: EventManager):
        """フィールドを終了する"""
        self.count = 0
        for player in self.owners:
            self.unregister_handlers(events, player)

    def reduce_count(self, events: EventManager, by: int = 1):
        """フィールドのカウントを減らす"""
        self.count = max(0, self.count - by)
        if not self.count:
            self.deactivate(events)

    def overwrite(self, events: EventManager, name: str, count: int):
        """フィールドを強制的に書き変える"""
        # 現在のハンドラを解除
        for player in self.owners:
            self.unregister_handlers(events, player)
        # 初期化
        self.init(name, count)
        # 新しくハンドラを登録
        for player in self.owners:
            self.register_handlers(events, player)
