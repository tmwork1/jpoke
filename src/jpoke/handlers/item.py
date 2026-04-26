"""持ち物ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
from functools import partial
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec, Type
from jpoke.enums import Interrupt, LogCode
from jpoke.core import HandlerReturn, Handler
from . import common


class ItemHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            subject_spec=subject_spec,
            source_type="item",
            priority=priority,
            once=once,
        )


def _consume_self_item(battle: Battle, target) -> bool:
    if not target.has_item():
        return False

    battle.add_event_log(target, LogCode.CONSUME_ITEM, payload={"item": target.item.name})
    target.item.consume()
    return True


def modify_power_by_type(battle: Battle,
                         ctx: BattleContext,
                         value: Any,
                         type_: Type,
                         modifier: float) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER
    if ctx.move.type == type_:
        value = int(value * modifier)
    return HandlerReturn(value=value)


def modify_super_effective_damage(battle: Battle,
                                  ctx: BattleContext,
                                  value: Any,
                                  type_: Type,
                                  modifier: float) -> HandlerReturn:
    # ON_CALC_DAMAGE_MODIFIER
    if ctx.move.type == type_ and battle.damage_calculator.calc_def_type_modifier(ctx) > 1:
        value = int(value * modifier)
    return HandlerReturn(value=value)


def いのちのたま_recoil(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    if ctx.move.category != "変化" and \
            common.modify_hp(battle, ctx, value, target_spec="attacker:self", r=-1/8):
        ctx.attacker.item.revealed = True
    return HandlerReturn()


def だっしゅつボタン(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    player = battle.find_player(ctx.defender)
    player.interrupt = Interrupt.EJECTBUTTON
    return HandlerReturn()


def だっしゅつパック(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # valueは{stat: change}の辞書
    player = battle.find_player(ctx.target)
    if any(v < 0 for v in value.values()) and \
            bool(battle.get_available_switch_commands(player)):
        player.interrupt = Interrupt.REQUESTED
    return HandlerReturn()


def たべのこし(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # 毎ターンHPを1/16回復
    if battle.modify_hp(ctx.source, r=1/16):
        ctx.source.item.revealed = True
    return HandlerReturn()

# ===== 難易度1: HP回復系アイテム =====


def オボンのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: HP50%以下時にHP25%回復
    target = ctx.resolve_role(battle, "source:self")
    if target.hp * 2 > target.max_hp:
        return HandlerReturn()

    healed = battle.modify_hp(target, r=1/4, reason="オボンのみ")
    if healed > 0:
        _consume_self_item(battle, target)
    return HandlerReturn()


def クラボのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: まひ状態時にまひを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "まひ":
        result = common.cure_ailment(battle, ctx, value, "source:self")
        if result.value:
            _consume_self_item(battle, target)
        return result
    return HandlerReturn()


def カゴのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: ねむり状態時にねむりを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "ねむり":
        result = common.cure_ailment(battle, ctx, value, "source:self")
        if result.value:
            _consume_self_item(battle, target)
        return result
    return HandlerReturn()


def モモンのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: どく状態時にどくを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "どく":
        result = common.cure_ailment(battle, ctx, value, "source:self")
        if result.value:
            _consume_self_item(battle, target)
        return result
    return HandlerReturn()


def チーゴのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: やけど状態時にやけどを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "やけど":
        result = common.cure_ailment(battle, ctx, value, "source:self")
        if result.value:
            _consume_self_item(battle, target)
        return result
    return HandlerReturn()


def ナナシのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: こおり状態時にこおりを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "こおり":
        result = common.cure_ailment(battle, ctx, value, "source:self")
        if result.value:
            _consume_self_item(battle, target)
        return result
    return HandlerReturn()


def キーのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: こんらん状態時にこんらんを治す
    return HandlerReturn()


def ヒメリのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    return HandlerReturn()


def オレンのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    return HandlerReturn()


def ひかりごけ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    return HandlerReturn()


def きゅうこん(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    return HandlerReturn()


# ===== 難易度1: 火力補正系アイテム =====

def ちからのハチマキ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER: 物理技1.1倍
    if ctx.move.category == "物理":
        return HandlerReturn(value=value * 11 // 10)
    return HandlerReturn(value=value)


def ものしりメガネ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER: 特殊技1.1倍
    if ctx.move.category == "特殊":
        return HandlerReturn(value=value * 11 // 10)
    return HandlerReturn(value=value)


def ラムのみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: すべての状態異常を回復する（消費型）
    target = ctx.resolve_role(battle, "source:self")

    # 状態異常をチェック
    if target.ailment:
        result = common.cure_ailment(battle, ctx, value, "source:self")
        if result.value:
            _consume_self_item(battle, target)
        return result

    # volatiles（こんらん等）はここでは処理しない（状態異常のみ対応）
    return HandlerReturn()
