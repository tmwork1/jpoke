from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core.battle import Battle
    from jpoke.core.event import EventContext


def どく(battle: Battle, ctx: EventContext, value: Any):
    if battle.modify_hp(ctx.source, r=-1/8):
        battle.add_turn_log(ctx.source, "どくダメージ")


def もうどく(battle: Battle, ctx: EventContext, value: Any):
    ctx.source.ailment.count += 1
    r = max(-1, -ctx.source.ailment.count/16)
    if battle.modify_hp(ctx.source, r=r):
        battle.add_turn_log(ctx.source, "もうどくダメージ")
