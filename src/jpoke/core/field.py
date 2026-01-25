from __future__ import annotations
from typing import TYPE_CHECKING, get_args, Generic, TypeVar
if TYPE_CHECKING:
    from jpoke.core import Player, EventManager

from jpoke.utils import fast_copy
from jpoke.utils.types import GlobalField, SideField, Weather, Terrain
from jpoke.model import Field


T = TypeVar("T")


class SelectiveFieldManager(Generic[T]):
    events: EventManager
    owners: list[Player]
    fields: dict[T, Field]
    current: Field

    def __init__(self, events: EventManager, players: list[Player], kind: type[T]):
        self.events = events
        self.owners = players
        names = get_args(kind)
        self.fields = {name: Field(players, name) for name in names}
        self._default_field = self.fields[names[0]]
        self.current = self._default_field

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=["fields"])
        return new

    def update_reference(self, events: EventManager, players: list[Player]):
        self.events = events
        for field in self.fields.values():
            field.update_reference(players)

    def activate(self, name: T, count: int) -> bool:
        field = self.fields[name]
        if self.current is field:
            return False

        if self.current.is_active:
            self.current.deactivate(self.events)

        self.current = field
        field.activate(self.events, count)
        return True

    def tick(self):
        self.current.tick(self.events)
        if not self.current.is_active:
            self.current = self._default_field


class WeatherManager(SelectiveFieldManager[Weather]):
    def __init__(self, events: EventManager, players: list[Player]):
        super().__init__(events, players, Weather)


class TerrainManager(SelectiveFieldManager[Terrain]):
    def __init__(self, events: EventManager, players: list[Player]):
        super().__init__(events, players, Terrain)


class BaseFieldManager:
    def __init__(self, events: EventManager, players: list[Player]) -> None:
        self.events: EventManager = events
        self.fields: dict[GlobalField | SideField, Field]

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=["fields"])
        return new

    def update_reference(self, events: EventManager, players: list[Player]):
        self.events = events
        for field in self.fields.values():
            field.update_reference(players)

    def activate(self, name: GlobalField | SideField, count: int) -> bool:
        if not self.fields[name].count:
            self.fields[name].activate(self.events, count)
            return True
        return False

    def deactivate(self, name: GlobalField | SideField) -> bool:
        field = self.fields[name]
        if field.count:
            field.deactivate(self.events)
            return True
        return False

    def reduce_count(self, name: GlobalField | SideField, by: int = 1) -> bool:
        field = self.fields[name]
        new_count = max(0, field.count - by)
        if new_count != field.count:
            field.tick(self.events)
            return True
        return False

# TODO


class GlobalFieldManager(BaseFieldManager):
    def __init__(self, events: EventManager, players: list[Player]) -> None:
        super().__init__(events, players)
        self.fields: dict[GlobalField, Field] = {
            "gravity": Field(players, "じゅうりょく"),
            "trickroom": Field(players, "トリックルーム"),
        }


class SideFieldManager(BaseFieldManager):
    def __init__(self, events: EventManager, player: Player) -> None:
        super().__init__(events, [player])
        self.fields: dict[SideField, Field] = {
            "reflector": Field([player], "リフレクター"),
            "lightwall": Field([player], "ひかりのかべ"),
            "shinpi": Field([player], "しんぴのまもり"),
            "whitemist": Field([player], "しろいきり"),
            "oikaze": Field([player], "おいかぜ"),
            "wish": Field([player], "ねがいごと"),
            "makibishi": Field([player], "まきびし"),
            "dokubishi": Field([player], "どくびし"),
            "stealthrock": Field([player], "ステルスロック"),
            "nebanet": Field([player], "ねばねばネット"),
        }

    def update_reference(self, events: EventManager, player: Player):
        self.events = events
        for field in self.fields.values():
            field.update_reference([player])
