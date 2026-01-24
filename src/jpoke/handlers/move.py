from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core.battle import Battle

from jpoke.utils.enums import Interrupt
from jpoke.core.event import Event, EventContext
from . import common


def reveal_move(battle: Battle, ctx: EventContext, value: Any):
    ctx.move.revealed = True
    battle.add_turn_log(ctx.target, ctx.move.name)
    return True


def consume_pp(battle: Battle, ctx: EventContext, value: Any):
    v = battle.events.emit(Event.ON_CHECK_PP_CONSUMED, ctx, 1)
    ctx.move.pp = max(0, ctx.move.pp - v)
    battle.add_turn_log(ctx.target, f"PP -{v} >> {ctx.move.pp}")
    ctx.target.expended_moves.append(ctx.move)
    return True


def pivot(battle: Battle, ctx: EventContext, value: Any):
    player = battle.find_player(ctx.target)
    if battle.get_available_switch_commands(player):
        player.interrupt = Interrupt.PIVOT


def blow(battle: Battle, ctx: EventContext, value: Any):
    player = battle.find_player(ctx.target)
    rival = battle.rival(player)
    commands = battle.get_available_switch_commands(rival)
    if commands:
        command = battle.random.choice(commands)
        battle.run_switch(rival, rival.team[command.idx])
