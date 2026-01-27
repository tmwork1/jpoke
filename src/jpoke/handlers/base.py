from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.types import ContextRole, Factor, LogPolicy, Stat, AilmentName, Weather, Terrain
from jpoke.core.event import EventContext


def reveal(battle: Battle,
           ctx: EventContext,
           value: Any,
           source_role: ContextRole,
           factor: Factor | None) -> bool:
    source = ctx.get(source_role)
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
              target_role: ContextRole,
              v: int,
              r: float,
              prob: float,
              source_role: ContextRole | None,
              factor: Factor | None,
              log: LogPolicy) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    target = ctx.get(target_role)
    res = battle.modify_hp(target, v, r)
    if should_log(log, res):
        reveal(battle, ctx, value, source_role, factor)
    if res:
        battle.add_turn_log(target, f"HP {'+' if v > 0 else ''}{v} ({r*100:.1f}%)")
    return res


def modify_stat(battle: Battle,
                ctx: EventContext,
                value: Any,
                stat: Stat,
                v: int,
                target_role: ContextRole,
                source_role: ContextRole | None,
                prob: float,
                factor: Factor | None,
                log: LogPolicy) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    target = ctx.get(target_role)
    source = ctx.get(source_role) if source_role else None
    res = battle.modify_stat(target, stat, v, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source_role, factor)
    if res:
        battle.add_turn_log(target, f"{stat} {'+' if v > 0 else ''}{v}")
    return res


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  value: Any,
                  ailment: AilmentName,
                  target_role: ContextRole,
                  source_role: ContextRole | None,
                  prob: float,
                  factor: Factor | None,
                  log: LogPolicy) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    target = ctx.get(target_role)
    source = ctx.get(source_role) if source_role else None
    res = target.apply_ailment(battle.events, ailment, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source_role, factor)
    if res:
        battle.add_turn_log(target, f"{ailment} 付与")


def cure_ailment(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 target_role: ContextRole,
                 source_role: ContextRole | None,
                 prob: float,
                 factor: Factor | None,
                 log: LogPolicy) -> bool:
    if prob < 1 and battle.random.random() >= prob:
        return False
    target = ctx.get(target_role)
    source = ctx.get(source_role) if source_role else None
    ailment = target.ailment.name
    res = target.cure_ailment(battle.events, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source_role, factor)
    if res:
        battle.add_turn_log(target, f"{ailment} 解除")
    return res


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     terrain: Terrain,
                     count: int,
                     source_role: ContextRole,
                     factor: Factor | None,
                     log: LogPolicy) -> bool:
    source = ctx.get(source_role)
    res = battle.terrain_mgr.activate(terrain, count, source=source)
    if should_log(log, res):
        reveal(battle, ctx, value, source, factor)
    if res:
        battle.add_turn_log(source, f"{terrain} 発動")
    return res
