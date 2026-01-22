from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core.battle import Battle

from jpoke.utils.types import Side
from jpoke.core.event import EventContext
from . import common


def reveal_ability(battle: Battle, ctx: EventContext, value: Any, whose: Side = "self"):
    return common.reveal(battle, ctx, what="ability", whose=whose)


def check_ability(battle: Battle, ctx: EventContext, ability: str, whose: Side = "self"):
    mon = ctx.source if whose == "self" else battle.foe(ctx.source)
    return mon.ability == ability


def ありじごく(battle: Battle, ctx: EventContext, value: Any) -> bool:
    return not ctx.source.floating(battle.events)


def いかく(battle: Battle, ctx: EventContext, value: Any) -> bool:
    ctx.target = battle.foe(ctx.source)
    return reveal_ability(battle, ctx, value) and common.modify_stat(battle, ctx, "A", -1)


def かげふみ(battle: Battle, ctx: EventContext, value: Any) -> bool:
    return ctx.source.ability != "かげふみ"


def じりょく(battle: Battle, ctx: EventContext, value: Any) -> bool:
    return "はがね" in ctx.source.types


def かちき(battle: Battle, ctx: EventContext, value: Any):
    if value < 0 and ctx.by == "foe":
        battle.modify_stat(ctx.source, "C", +2)
        reveal_ability(battle, ctx, value)
