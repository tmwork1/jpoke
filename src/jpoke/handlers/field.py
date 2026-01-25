from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core.battle import Battle

from jpoke.utils.types import GlobalField, SideField
from jpoke.core.event import EventContext, HandlerResult


def reduce_global_field_count(battle: Battle, ctx: EventContext, value: Any,
                              name: GlobalField):
    if battle.field.reduce_count(name):
        field = battle.field.fields[name]
        battle.add_turn_log(None, f"{field.name} 残り{field.count}ターン")
    return HandlerResult.STOP_HANDLER


def reduce_side_field_count(battle: Battle, ctx: EventContext, value: Any,
                            name: SideField):
    player = battle.find_player(ctx.target)
    side = battle.side[player]
    if side.reduce_count(name):
        field = side.fields[name]
        battle.add_turn_log(None, f"{field.name} 残り{field.count}ターン")


def リフレクター(battle: Battle, ctx: EventContext, value: Any):
    # ON_CALC_DAMAGE_MODIFIER ハンドラ
    if ctx.move.category == "物理":
        battle.add_turn_log(ctx.target, f"リフレクター x0.5")
        return value // 2
