from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext
    from jpoke.model import Pokemon

from jpoke.utils.types import ContextRole, Factor, LogPolicy, Weather, Terrain
from . import base


def reveal_ability(battle: Battle,
                   ctx: EventContext,
                   value: Any,
                   source_role: ContextRole = "source") -> bool:
    return base.reveal(battle, ctx, value, source_role, "ability")


def modify_stat(battle: Battle,
                ctx: EventContext,
                value: Any,
                stat: str,
                v: int,
                target_role: ContextRole = "target",
                source_role: ContextRole | None = None,
                prob: float = 1.0,
                factor: Factor | None = "ability",
                log: LogPolicy = "on_success") -> bool:
    return base.modify_stat(battle, ctx, value, stat, v, target_role, source_role, prob, factor, log)


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  value: Any,
                  ailment: str,
                  target_role: ContextRole = "target",
                  source_role: ContextRole | None = None,
                  prob: float = 1.0,
                  factor: Factor | None = "ability",
                  log: LogPolicy = "on_success") -> bool:
    return base.apply_ailment(battle, ctx, value, ailment, target_role, source_role, prob, factor, log)


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     terrain: Terrain,
                     count: int = 5,
                     source_role: ContextRole = "source",
                     log: LogPolicy = "on_success") -> bool:
    return base.activate_terrain(battle, ctx, value, terrain, count, source_role, "ability", log)


def ありじごく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    return not ctx.source.floating(battle.events)


def かげふみ(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    return ctx.source.ability != "かげふみ"


def じりょく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    return ctx.source.has_type("はがね")


def かちき(battle: Battle, ctx: EventContext, value: Any):
    # ON_MODIFY_STAT
    if value < 0 and ctx.source != ctx.target:
        modify_stat(battle, ctx, value, "C", +2, target_role="target", source_role="target")


def すなかき(battle: Battle, ctx: EventContext, value: Any):
    # ON_CALC_SPEED
    return value * 2 if battle.weather == "すなあらし" else value
