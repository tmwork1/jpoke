from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.utils.type_defs import EffectSource, LogPolicy
from jpoke.core.event import Handler, HandlerReturn


class AilmentHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: str,
                 log: LogPolicy = "always",
                 log_text: str | None = None,
                 priority: int = 100):
        super().__init__(func, subject_spec, "ailment", log, log_text, priority)


def もうどく(battle: Battle, ctx: EventContext, value: Any):
    ctx.target.ailment.count += 1
    r = max(-1, -ctx.target.ailment.count/16)
    success = battle.modify_hp(ctx.target, r=r)
    return HandlerReturn(success)
