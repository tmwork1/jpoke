from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.utils.types import Side
from jpoke.utils.enums import Interrupt
from jpoke.core.event import EventContext, HandlerResult
from . import common


def reveal_item(battle: Battle, ctx: EventContext, value: Any, whose: Side = "self"):
    return common.reveal(battle, ctx, what="item", whose=whose)


def check_item(battle: Battle, ctx: EventContext, item: str, whose: Side = "self"):
    mon = ctx.source if whose == "self" else battle.foe(ctx.source)
    return mon.item == item


def いのちのたま(battle: Battle, ctx: EventContext, value: Any):
    if ctx.move.category != "変化" and common.modify_hp(battle, ctx, "self", r=-1/8):
        reveal_item(battle, ctx, value)


def だっしゅつボタン(battle: Battle, ctx: EventContext, value: Any):
    target = battle.foe(ctx.source)
    if target.item == "だっしゅつボタン":
        player = battle.find_player(target)
        player.interrupt = Interrupt.EJECTBUTTON


def だっしゅつパック(battle: Battle, ctx: EventContext, value: Any):
    player = battle.find_player(ctx.source)
    if value < 0 and battle.get_available_switch_commands(player):
        player.interrupt = Interrupt.REQUESTED
        reveal_item(battle, ctx, value)
