from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.utils.types import RoleSpec, Factor, LogPolicy, Stat, AilmentName, Weather, Terrain, Side
from jpoke.core.event import EventContext


def _resolve_role(battle: Battle,
                  ctx: EventContext,
                  spec: RoleSpec | None) -> Pokemon | None:
    if spec is None:
        return None

    # spec は常に "role:side" 形式
    role, side = spec.split(":")
    mon = ctx.get(role)
    if not mon:
        return None

    if side == "foe":
        mon = battle.foe(mon)
    return mon


def reveal(battle: Battle,
           ctx: EventContext,
           value: Any,
           source_spec: RoleSpec,
           factor: Factor | None) -> bool:
    source = _resolve_role(battle, ctx, source_spec)
    if not source:
        return False
    match factor:
        case "ability":
            source.ability.revealed = True
            battle.add_turn_log(source, source.ability.name)
        case "item":
            source.item.revealed = True
            battle.add_turn_log(source, source.item.name)
        case "move":
            ctx.move.revealed = True
            battle.add_turn_log(source, ctx.move.name)
    return True


def should_log(log: LogPolicy, res: bool) -> bool:
    return log == "always" or \
        (log == "on_success" and res) or \
        (log == "on_failure" and not res)


def modify_hp(battle: Battle,
              ctx: EventContext,
              value: Any,
              target_spec: RoleSpec,
              v: int,
              r: float,
              prob: float,
              source_spec: RoleSpec | None,
              factor: Factor | None,
              log: LogPolicy) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    target = _resolve_role(battle, ctx, target_spec)
    res = battle.modify_hp(target, v, r)
    if should_log(log, res):
        reveal(battle, ctx, value, source_spec, factor)
    if res:
        battle.add_turn_log(target, f"HP {'+' if v > 0 else ''}{v} ({r*100:.1f}%)")
    return res


def modify_stat(battle: Battle,
                ctx: EventContext,
                value: Any,
                stat: Stat,
                v: int,
                target_spec: RoleSpec,
                source_spec: RoleSpec | None,
                prob: float,
                factor: Factor | None,
                log: LogPolicy) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    target = _resolve_role(battle, ctx, target_spec)
    source = _resolve_role(battle, ctx, source_spec)
    res = battle.modify_stat(target, stat, v, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source_spec, factor)
    if res:
        battle.add_turn_log(target, f"{stat} {'+' if v > 0 else ''}{v}")
    return res


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  value: Any,
                  ailment: AilmentName,
                  target_spec: RoleSpec,
                  source_spec: RoleSpec | None,
                  prob: float,
                  factor: Factor | None,
                  log: LogPolicy) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    target = _resolve_role(battle, ctx, target_spec)
    source = _resolve_role(battle, ctx, source_spec)
    res = target.apply_ailment(battle.events, ailment, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source_spec, factor)
    if res:
        battle.add_turn_log(target, f"{ailment} 付与")
    return res


def cure_ailment(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 target_spec: RoleSpec,
                 source_spec: RoleSpec | None,
                 prob: float,
                 factor: Factor | None,
                 log: LogPolicy) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    target = _resolve_role(battle, ctx, target_spec)
    source = _resolve_role(battle, ctx, source_spec)
    ailment = target.ailment.name
    res = target.cure_ailment(battle.events, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source_spec, factor)
    if res:
        battle.add_turn_log(target, f"{ailment} 解除")
    return res


def activate_weather(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     weather: Weather,
                     count: int,
                     source_spec: RoleSpec,
                     factor: Factor | None,
                     log: LogPolicy) -> bool:
    source = _resolve_role(battle, ctx, source_spec)
    res = battle.weather_mgr.activate(weather, count, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source_spec, factor)
    if res:
        battle.add_turn_log(source, f"{weather} 発動")
    return res


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     terrain: Terrain,
                     count: int,
                     source_spec: RoleSpec,
                     factor: Factor | None,
                     log: LogPolicy) -> bool:
    source = _resolve_role(battle, ctx, source_spec)
    res = battle.terrain_mgr.activate(terrain, count, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source_spec, factor)
    if res:
        battle.add_turn_log(source, f"{terrain} 発動")
    return res


def resolve_field_count(battle: Battle,
                        ctx: EventContext,
                        value: Any,
                        field: Weather | Terrain,
                        additonal_count: int) -> int:
    if ctx.field.orig_name == field:
        return value + additonal_count
    else:
        return value
