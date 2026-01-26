from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.utils.types import ContextRole, Side, Stat, AilmentName, Weather, Terrain, SideField
from jpoke.utils.enums import Event
from jpoke.core.event import EventContext


def modify_hp(battle: Battle,
              target: Pokemon,
              v: int = 0,
              r: float = 0,
              source: Pokemon | None = None,
              prob: float = 1) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    return battle.modify_hp(target, v, r)


def modify_stat(battle: Battle,
                target: Pokemon,
                stat: Stat,
                v: int,
                source: Pokemon | None = None,
                prob: float = 1) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    return battle.modify_stat(target, stat, v, source=source)


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     terrain: Terrain,
                     count: int) -> bool:
    return battle.terrain_mgr.activate(terrain, count, source=ctx.subject)


def apply_ailment(battle: Battle,
                  target: Pokemon,
                  ailment: AilmentName,
                  prob: float = 1) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    if ailment:
        return target.ailment.overwrite(battle, ailment)
    else:
        return target.ailment.cure(battle)


def apply_side_field(battle: Battle,
                     target: Side,
                     field: SideField,
                     base_count: int) -> bool:
    count = battle.events.emit(
        Event.ON_CHECK_DURATION,
        EventContext(target=target, side_field=field),
        base_count
    )
    player = battle.find_player(target)
    return battle.side[player].activate(field, count)
