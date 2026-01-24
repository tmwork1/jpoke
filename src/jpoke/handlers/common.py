from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext
    from jpoke.model import Pokemon

from jpoke.utils.types import Side, Stat, AilmentName, Weather, Terrain, SideField
from jpoke.utils.enums import Event


def modify_hp(battle: Battle,
              v: int = 0,
              r: float = 0,
              ctx: EventContext | None = None,
              target: Pokemon | None = None,
              source: Pokemon | None = None,
              prob: float = 1) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    if not target:
        target = ctx.target
    if not source:
        source = ctx.source
    return battle.modify_hp(target, v, r)


def modify_stat(battle: Battle,
                stat: Stat,
                v: int,
                ctx: EventContext | None = None,
                target: Pokemon | None = None,
                source: Pokemon | None = None,
                prob: float = 1) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    if not target:
        target = ctx.target
    if not source:
        source = ctx.source
    return battle.modify_stat(target, stat, v, source=source)


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


def apply_weather(battle: Battle, ctx: EventContext, weather: Weather, count: int = 5):
    ctx.field = weather
    count = battle.events.emit(Event.ON_CHECK_DURATION, ctx, count)
    if battle.field.activate_weather(weather, count):
        battle.add_turn_log(None, weather)
        return True
    return False


def apply_terrain(battle: Battle, ctx: EventContext, terrain: Terrain, count: int = 5):
    ctx.field = terrain
    count = battle.events.emit(Event.ON_CHECK_DURATION, ctx, count)
    if battle.field.activate_terrain(terrain, count):
        battle.add_turn_log(None, terrain)
        return True
    return False


def apply_side(battle: Battle,
               ctx: EventContext,
               target: Side,
               name: SideField,
               count: int) -> bool:
    mon = ctx.target if target == "self" else battle.foe(ctx.target)
    player = battle.find_player(mon)
    side = battle.side[player]
    ctx.field = name
    count = battle.events.emit(Event.ON_CHECK_DURATION, ctx, count)
    return side.activate(name, count)
