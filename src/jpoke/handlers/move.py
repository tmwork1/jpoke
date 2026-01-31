from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.type_defs import RoleSpec, LogPolicy
from jpoke.utils.enums import Event, Interrupt
from jpoke.core.event import Handler, EventContext, HandlerReturn


class MoveHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "attacker:self",
                 log: LogPolicy = "never",
                 log_text: str | None = None,
                 priority: int = 100):
        super().__init__(func, subject_spec, "move", log, log_text, priority)


def consume_pp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    v = battle.events.emit(Event.ON_CHECK_PP_CONSUMED, ctx, 1)
    ctx.move.pp = max(0, ctx.move.pp - v)
    battle.add_event_log(ctx.attacker, f"PP -{v}")
    ctx.attacker.pp_consumed_moves.append(ctx.move)
    return HandlerReturn(True)


def pivot(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    player = battle.find_player(ctx.attacker)
    success = bool(battle.get_available_switch_commands(player))
    if success:
        player.interrupt = Interrupt.PIVOT
    return HandlerReturn(success)


def blow(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    player = battle.find_player(ctx.defender)
    commands = battle.get_available_switch_commands(player)
    success = bool(commands)
    if success:
        command = battle.random.choice(commands)
        battle.run_switch(player, player.team[command.idx])
    return HandlerReturn(success)
