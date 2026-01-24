from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core.battle import Battle
    from jpoke.core.event import EventContext


def どく(battle: Battle, ctx: EventContext, value: Any):
    if battle.modify_hp(ctx.target, r=-1/8):
        battle.add_turn_log(ctx.target, "どくダメージ")


def もうどく(battle: Battle, ctx: EventContext, value: Any):
    ctx.target.ailment.count += 1
    r = max(-1, -ctx.target.ailment.count/16)
    if battle.modify_hp(ctx.target, r=r):
        battle.add_turn_log(ctx.target, "もうどくダメージ")
