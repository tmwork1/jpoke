from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon, Move

from jpoke.utils.enums import Interrupt
from jpoke.core.event import Event, EventContext
from . import common


def pivot(battle: Battle, ctx: EventContext, value: Any):
    player = battle.find_player(ctx.attacker)
    if battle.get_available_switch_commands(player):
        player.interrupt = Interrupt.PIVOT


def blow(battle: Battle, ctx: EventContext, value: Any):
    player = battle.find_player(ctx.defender)
    commands = battle.get_available_switch_commands(player)
    if commands:
        command = battle.random.choice(commands)
        battle.run_switch(player, player.team[command.idx])

# 共通ハンドラ


def reveal_move(battle: Battle, ctx: EventContext, value: Any):
    ctx.move.revealed = True
    battle.add_turn_log(ctx.attacker, ctx.move.name)
    return True


def consume_pp(battle: Battle, ctx: EventContext, value: Any):
    v = battle.events.emit(Event.ON_CHECK_PP_CONSUMED, ctx, 1)
    ctx.move.pp = max(0, ctx.move.pp - v)
    battle.add_turn_log(ctx.attacker, f"PP -{v}")
    ctx.attacker.pp_consumed_moves.append(ctx.move)
    return True
