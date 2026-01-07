from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Player, EventManager

from jpoke.utils import fast_copy
from jpoke.utils.types import GlobalField, SideField, Weather, Terrain
from jpoke.model import Field


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
            field.reduce_count(self.events)
            return True
        return False


class GlobalFieldManager(BaseFieldManager):
    def __init__(self, events: EventManager, players: list[Player]) -> None:
        super().__init__(events, players)
        self.fields: dict[GlobalField, Field] = {
            "weather": Field(players),
            "terrain": Field(players),
            "gravity": Field(players, "じゅうりょく"),
            "trickroom": Field(players, "トリックルーム"),
        }

    def activate_weather(self, name: Weather, count: int) -> bool:
        field = self.fields["weather"]
        # 重ねがけ不可
        if name == field.name:
            return False

        if not name or count == 0:
            field.deactivate(self.events)
        else:
            field.overwrite(self.events, name, count)
        return True

    def activate_terrain(self, name: Terrain, count: int) -> bool:
        field = self.fields["terrain"]
        # 重ねがけ不可
        if name == field.name:
            return False

        if not name or count == 0:
            field.deactivate(self.events)
        else:
            field.overwrite(self.events, name, count)
        return True


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
