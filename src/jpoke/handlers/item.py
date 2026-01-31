from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.enums import Interrupt
from jpoke.core.event import EventContext, EventControl, HandlerReturn, Handler
from jpoke.utils.type_defs import LogPolicy, RoleSpec
from . import common


class ItemHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 log: LogPolicy = "on_success",
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            subject_spec=subject_spec,
            source_type="item",
            log=log,
            priority=priority,
            once=once,
        )


def いのちのたま(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_HITのハンドラ
    success = ctx.move.category != "変化" and \
        common.modify_hp(battle, ctx, value, target_spec="attacker:self", r=-1/8)
    return HandlerReturn(success)


def だっしゅつボタン(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_DAMAGEのハンドラ
    player = battle.find_player(ctx.defender)
    player.interrupt = Interrupt.EJECTBUTTON
    return HandlerReturn(True)


def だっしゅつパック(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_MODIFY_STATのハンドラ
    player = battle.find_player(ctx.target)
    success = value < 0 and bool(battle.get_available_switch_commands(player))
    if success:
        player.interrupt = Interrupt.REQUESTED
    return HandlerReturn(success)
