from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core.battle import Battle

from jpoke.utils.types import GlobalField, SideField
from jpoke.core.event import EventContext, EventControl, HandlerReturn


def reduce_global_field_count(battle: Battle,
                              ctx: EventContext,
                              value: Any,
                              name: GlobalField):
    if battle.field.reduce_count(name):
        field = battle.field.fields[name]
        battle.add_turn_log(None, f"{field.name} 残り{field.count}ターン")
    return HandlerReturn(True, control=EventControl.STOP_HANDLER)


def reduce_side_field_count(battle: Battle,
                            ctx: EventContext,
                            value: Any,
                            name: SideField):
    player = battle.find_player(ctx.target)
    side = battle.side[player]
    if side.reduce_count(name):
        field = side.fields[name]
        battle.add_turn_log(None, f"{field.name} 残り{field.count}ターン")
    return HandlerReturn(True)


def apply_sandstorm_damage(battle: Battle, ctx: EventContext, value: Any):
    # ON_TURN_END ハンドラ
    if not ctx.target or \
            any(ctx.target.has_type(t) for t in ["いわ", "じめん", "はがね"]) or \
            ctx.target.ability.name in ["すなかき", "すながくれ", "すなのちから", "ぼうじん"]:
        return HandlerReturn(True)
    if battle.modify_hp(ctx.target, r=-1/16):
        battle.add_turn_log(ctx.target, f"すなあらし")
    return HandlerReturn(True)


def リフレクター(battle: Battle, ctx: EventContext, value: Any):
    # ON_CALC_DAMAGE_MODIFIER ハンドラ
    if ctx.move.category == "物理":
        battle.add_turn_log(ctx.attacker, f"リフレクター x0.5")
        return HandlerReturn(True, value // 2)
    return HandlerReturn(True)
