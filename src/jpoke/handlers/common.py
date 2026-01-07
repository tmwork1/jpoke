from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.utils.types import Side, Stat, AilmentName, Weather, Terrain, SideField
from jpoke.utils.enums import Event


def reveal(battle: Battle, ctx: EventContext,
           what: Literal["ability", "item", "move"], whose: Side) -> bool:
    mon = ctx.source if whose == "self" else battle.foe(ctx.source)
    match what:
        case "ability":
            target = mon.ability
        case "item":
            target = mon.item
        case "move":
            target = ctx.move
    target.revealed = True
    battle.add_turn_log(ctx.source, target.name)
    return True


def modify_hp(
    battle: Battle, ctx: EventContext,
    target: Side,
    v: int = 0,
    r: float = 0,
    prob: float = 1,
) -> bool:
    """HPが変化したらTrueを返す"""
    if prob < 1 and battle.random.random() >= prob:
        return False
    mon = ctx.source if target == "self" else battle.foe(ctx.source)
    return battle.modify_hp(mon, v, r)


def modify_stat(
    battle: Battle, ctx: EventContext,
    target: Side,
    stat: Stat,
    v: int,
    prob: float = 1
) -> bool:
    """能力ランクが変化したらTrueを返す"""
    if prob < 1 and battle.random.random() >= prob:
        return False
    mon = ctx.source if target == "self" else battle.foe(ctx.source)
    by = "self" if ctx.source == target else "foe"
    return battle.modify_stat(mon, stat, v, by=by)


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  target: Side,
                  ailment: AilmentName,
                  prob: float = 1) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    mon = ctx.source if target == "self" else battle.foe(ctx.source)
    if ailment:
        return mon.ailment.overwrite(battle, ailment)
    else:
        return mon.ailment.cure(battle)


def apply_weather(battle: Battle, ctx: EventContext, name: Weather, count: int = 5):
    ctx.field = name
    count = battle.events.emit(Event.ON_CHECK_DURATION, ctx, count)
    return battle.field.activate_weather(name, count)


def apply_terrain(battle: Battle, ctx: EventContext, name: Terrain, count: int = 5):
    ctx.field = name
    count = battle.events.emit(Event.ON_CHECK_DURATION, ctx, count)
    return battle.field.activate_terrain(name, count)


def apply_side(battle: Battle,
               ctx: EventContext,
               target: Side,
               name: SideField,
               count: int) -> bool:
    mon = ctx.source if target == "self" else battle.foe(ctx.source)
    player = battle.find_player(mon)
    side = battle.side(player)
    ctx.field = name
    count = battle.events.emit(Event.ON_CHECK_DURATION, ctx, count)
    return side.activate(name, count)
