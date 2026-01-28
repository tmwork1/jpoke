from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext
    from jpoke.model import Pokemon

from jpoke.utils.types import ContextRole, RoleSpec, Factor, LogPolicy, Weather, Terrain
from . import base


def reveal_ability(battle: Battle,
                   ctx: EventContext,
                   value: Any,
                   source_spec: RoleSpec = "source:self") -> bool:
    return base.reveal(battle, ctx, value, source_spec, "ability")


def modify_stat(battle: Battle,
                ctx: EventContext,
                value: Any,
                stat: str,
                v: int,
                target_spec: RoleSpec = "target:self",
                source_spec: RoleSpec | None = None,
                prob: float = 1.0,
                factor: Factor | None = "ability",
                log: LogPolicy = "always") -> bool:
    return base.modify_stat(battle, ctx, value, stat, v, target_spec, source_spec, prob, factor, log)


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  value: Any,
                  ailment: str,
                  target_spec: RoleSpec = "target:self",
                  source_spec: RoleSpec | None = None,
                  prob: float = 1.0,
                  factor: Factor | None = "ability",
                  log: LogPolicy = "always") -> bool:
    return base.apply_ailment(battle, ctx, value, ailment, target_spec, source_spec, prob, factor, log)


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     terrain: Terrain,
                     count: int = 5,
                     source_spec: RoleSpec = "source:self",
                     log: LogPolicy = "always") -> bool:
    return base.activate_terrain(battle, ctx, value, terrain, count, source_spec, "ability", log)


def ありじごく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    return not ctx.source.is_floating(battle.events)


def かげふみ(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    return ctx.source.ability != "かげふみ"


def じりょく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    return ctx.source.has_type("はがね")


def かちき(battle: Battle, ctx: EventContext, value: Any):
    # ON_MODIFY_STAT
    if value < 0 and ctx.source != ctx.target:
        modify_stat(battle, ctx, value, "C", +2, target_spec="target:self", source_spec="target:self")


def すなかき(battle: Battle, ctx: EventContext, value: Any):
    # ON_CALC_SPEED
    return value * 2 if battle.weather == "すなあらし" else value
