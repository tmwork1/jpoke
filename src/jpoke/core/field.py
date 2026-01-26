from __future__ import annotations
from typing import TYPE_CHECKING, get_args, Generic, TypeVar
if TYPE_CHECKING:
    from jpoke.core import Player, EventManager
    from jpoke.model import Pokemon

from jpoke.utils import fast_copy
from jpoke.utils.types import GlobalField, SideField, Weather, Terrain
from jpoke.utils.enums import Event
from jpoke.model import Field
from jpoke.core.event import EventContext

T = TypeVar("T")


class BaseFieldManager(Generic[T]):
    def __init__(self, events: EventManager, owners: list[Player], fields: dict[T, Field]):
        self.events = events
        self.owners = owners
        self.fields = fields

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=["fields"])
        return new

    def update_reference(self, events: EventManager, owners: list[Player]):
        self.events = events
        self.owners = owners
        for field in self.fields.values():
            field.update_reference(owners)

    def tick(self, name: T) -> bool:
        field = self.fields[name]
        if not field.is_active:
            return False
        field.count -= 1
        if not field.count:
            field.deactivate(self.events)
        return True


class ExclusiveFieldManager(BaseFieldManager[T]):
    def __init__(self, events: EventManager, owners: list[Player], kind: type[T]):
        names = get_args(kind)
        fields = {name: Field(name, owners) for name in names}
        super().__init__(events, owners, fields)
        self._default = fields[names[0]]
        self.current = self._default

    def activate(self, name: T, count: int, source: Pokemon | None = None) -> bool:
        field = self.fields[name]
        if self.current is field:
            return False
        if self.current.is_active:
            self.current.deactivate(self.events)

        count = self.events.emit(
            Event.ON_CHECK_DURATION,
            EventContext(source=source, field=field),
            count
        )
        self.current = field
        field.activate(self.events, count)
        return True

    def deactivate(self) -> bool:
        if not self.current.is_active:
            return False
        self.current.deactivate(self.events)
        self.current = self._default
        return True

    def tick(self) -> bool:
        return super().tick(self.current.name)


class StackableFieldManager(BaseFieldManager[T]):
    def activate(self, name: T, count: int) -> bool:
        field = self.fields[name]
        if field.is_active:
            return False
        field.activate(self.events, count)
        return True

    def deactivate(self, name: T) -> bool:
        field = self.fields[name]
        if not field.is_active:
            return False
        field.deactivate(self.events)
        return True


class WeatherManager(ExclusiveFieldManager[Weather]):
    def __init__(self, events: EventManager, players: list[Player]):
        super().__init__(events, players, Weather)


class TerrainManager(ExclusiveFieldManager[Terrain]):
    def __init__(self, events: EventManager, players: list[Player]):
        super().__init__(events, players, Terrain)


class GlobalFieldManager(StackableFieldManager[GlobalField]):
    def __init__(self, events: EventManager, players: list[Player]):
        super().__init__(
            events,
            players,
            {
                "gravity": Field("じゅうりょく", players),
                "trickroom": Field("トリックルーム", players),
            }
        )


class SideFieldManager(StackableFieldManager[SideField]):
    def __init__(self, events: EventManager, player: Player):
        super().__init__(
            events,
            [player],
            {
                "reflector": Field("リフレクター", [player]),
                "lightwall": Field("ひかりのかべ", [player]),
                "shinpi": Field("しんぴのまもり", [player]),
                "whitemist": Field("しろいきり", [player]),
                "oikaze": Field("おいかぜ", [player]),
                "wish": Field("ねがいごと", [player]),
                "makibishi": Field("まきびし", [player]),
                "dokubishi": Field("どくびし", [player]),
                "stealthrock": Field("ステルスロック", [player]),
                "nebanet": Field("ねばねばネット", [player]),
            }
        )
