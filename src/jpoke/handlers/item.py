from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.utils.types import Side
from jpoke.utils.enums import Interrupt
from jpoke.core.event import EventContext, HandlerResult
from . import common


def reveal_item(battle: Battle, target: Pokemon) -> bool:
    target.item.revealed = True
    battle.add_turn_log(target, target.item.name)
    return True


def いのちのたま(battle: Battle, ctx: EventContext, value: Any):
    # ON_HITのハンドラ
    if ctx.move.category != "変化" and \
            common.modify_hp(battle, r=-1/8, target=ctx.source, source=ctx.source):
        reveal_item(battle, ctx.source)


def だっしゅつボタン(battle: Battle, ctx: EventContext, value: Any):
    target = battle.foe(ctx.target)
    if target.item == "だっしゅつボタン":
        player = battle.find_player(target)
        player.interrupt = Interrupt.EJECTBUTTON


def だっしゅつパック(battle: Battle, ctx: EventContext, value: Any):
    player = battle.find_player(ctx.target)
    if value < 0 and battle.get_available_switch_commands(player):
        player.interrupt = Interrupt.REQUESTED
        reveal_item(battle, ctx, value)
