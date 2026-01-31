from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.core.event import HandlerReturn, Handler
from jpoke.utils.type_defs import LogPolicy, RoleSpec
from . import common


class AbilityHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 log: LogPolicy = "on_success",
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            subject_spec=subject_spec,
            source_type="ability",
            log=log,
            priority=priority,
            once=once,
        )


def ありじごく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    result = not ctx.source.is_floating(battle.events)
    return HandlerReturn(True, result)


def かげふみ(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    result = ctx.source.ability != "かげふみ"
    return HandlerReturn(True, result)


def じりょく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    result = ctx.source.has_type("はがね")
    return HandlerReturn(True, result)


def かちき(battle: Battle, ctx: EventContext, value: Any):
    # ON_MODIFY_STAT
    result = value < 0 and \
        ctx.source != ctx.target and \
        common.modify_stat(battle, ctx, value, "C", +2, target_spec="target:self", source_spec="target:self")
    return HandlerReturn(result)


def すなかき(battle: Battle, ctx: EventContext, value: Any):
    # ON_CALC_SPEED
    value = value * 2 if battle.weather == "すなあらし" else value
    return HandlerReturn(True, value)
