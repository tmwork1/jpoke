from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.utils.type_defs import RoleSpec, Stat, AilmentName, Weather, Terrain, Side
from jpoke.utils.enums import Event
from jpoke.core.event import EventContext, HandlerReturn


def modify_hp(battle: Battle,
              ctx: EventContext,
              value: Any,
              target_spec: RoleSpec,
              v: int = 0,
              r: float = 0,
              prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    success = battle.modify_hp(target, v, r)
    return HandlerReturn(success)


def drain_hp(battle: Battle,
             ctx: EventContext,
             value: Any,
             from_: RoleSpec,
             to_: RoleSpec | None = None,
             v: int = 0,
             r: float = 0,
             prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)

    from_mon = ctx.resolve_role(battle, from_)
    if to_ is not None:
        to_mon = ctx.resolve_role(battle, to_)
    else:
        to_mon = from_mon

    success, _ = battle.drain_hp(from_mon, to_mon, v, r)
    return HandlerReturn(success)


def modify_stat(battle: Battle,
                ctx: EventContext,
                value: Any,
                stat: Stat,
                v: int,
                target_spec: RoleSpec,
                source_spec: RoleSpec | None = None,
                prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = battle.modify_stat(target, stat, v, source=source)
    return HandlerReturn(success)


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  value: Any,
                  ailment: AilmentName,
                  target_spec: RoleSpec,
                  source_spec: RoleSpec | None = None,
                  prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = target.apply_ailment(battle.events, ailment, source=source)
    return HandlerReturn(success)


def cure_ailment(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 target_spec: RoleSpec,
                 source_spec: RoleSpec | None = None,
                 prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = target.cure_ailment(battle.events, source=source)
    return HandlerReturn(success)


def activate_weather(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     source_spec: RoleSpec,
                     weather: Weather,
                     count: int = 5) -> HandlerReturn:
    source = ctx.resolve_role(battle, source_spec)
    success = battle.weather_mgr.activate(weather, count, source=source)
    return HandlerReturn(success)


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     source_spec: RoleSpec,
                     terrain: Terrain,
                     count: int = 5) -> HandlerReturn:
    source = ctx.resolve_role(battle, source_spec)
    success = battle.terrain_mgr.activate(terrain, count, source=source)
    return HandlerReturn(success)


def resolve_field_count(battle: Battle,
                        ctx: EventContext,
                        value: Any,
                        field: Weather | Terrain,
                        additonal_count: int) -> HandlerReturn:
    if ctx.field.orig_name == field:
        return HandlerReturn(True, value + additonal_count)
    else:
        return HandlerReturn(False, value)
