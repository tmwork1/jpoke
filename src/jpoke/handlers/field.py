from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.core.event import EventContext, EventControl, HandlerReturn


def すなあらし_apply_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_TURN_END ハンドラ
    success = ctx.target and \
        not any(ctx.target.has_type(t) for t in ["いわ", "じめん", "はがね"]) and \
        ctx.target.ability.name not in ["すなかき", "すながくれ", "すなのちから", "ぼうじん"] and \
        battle.modify_hp(ctx.target, r=-1/16)
    return HandlerReturn(success)


def リフレクター(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_CALC_DAMAGE_MODIFIER ハンドラ
    if ctx.move.category == "物理":
        return HandlerReturn(True, value // 2)
    return HandlerReturn(False, value)
