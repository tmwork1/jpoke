from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
from functools import partial
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.enums import Interrupt, Event
from jpoke.core.event import EventContext, HandlerReturn, Handler
from jpoke.utils.type_defs import LogPolicy, RoleSpec, Type
from . import common


class ItemHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 log: LogPolicy = "on_success",
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            subject_spec=subject_spec,
            source_type="item",
            log=log,
            priority=priority,
            once=once,
        )


def modify_power_by_type(battle: Battle,
                         ctx: EventContext,
                         value: Any,
                         type_: Type,
                         modifier: float) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER
    if ctx.move and ctx.move.type == type_:
        return HandlerReturn(True, value * modifier)
    return HandlerReturn(False, value)


def modify_super_effective_damage(battle: Battle,
                                  ctx: EventContext,
                                  value: Any,
                                  type_: Type,
                                  modifier: float) -> HandlerReturn:
    # ON_CALC_DAMAGE_MODIFIER
    if ctx.move and ctx.move.type == type_ and \
            common.calc_effectiveness(battle, ctx.attacker, ctx.defender, ctx.move) > 1:
        return HandlerReturn(True, value * modifier)
    return HandlerReturn(False, value)


def いのちのたま(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_HITのハンドラ
    success = ctx.move.category != "変化" and \
        common.modify_hp(battle, ctx, value, target_spec="attacker:self", r=-1/8)
    return HandlerReturn(success)


def だっしゅつボタン(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_DAMAGEのハンドラ
    player = battle.find_player(ctx.defender)
    player.interrupt = Interrupt.EJECTBUTTON
    return HandlerReturn(True)


def だっしゅつパック(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_MODIFY_STATのハンドラ
    # valueは{stat: change}の辞書
    player = battle.find_player(ctx.target)
    success = any(v < 0 for v in value.values()) and bool(battle.get_available_switch_commands(player))
    if success:
        player.interrupt = Interrupt.REQUESTED
    return HandlerReturn(success)


# ===== 難易度1: HP回復系アイテム =====

def オボンのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: HP50%以下時にHP25%回復
    return HandlerReturn(False)


def クラボのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: まひ状態時にまひを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "まひ":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def カゴのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: ねむり状態時にねむりを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "ねむり":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def モモンのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: どく状態時にどくを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "どく":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def チーゴのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: やけど状態時にやけどを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "やけど":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def ナナシのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: こおり状態時にこおりを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "こおり":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def キーのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: こんらん状態時にこんらんを治す
    return HandlerReturn(False)


def ヒメリのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(False)


def オレンのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(False)


def ひかりごけ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(False)


def きゅうこん(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(False)


# ===== 難易度1: 火力補正系アイテム =====

def ちからのハチマキ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER: 物理技1.1倍
    if ctx.move.category == "物理":
        return HandlerReturn(True, value * 11 // 10)
    return HandlerReturn(False, value)


def ものしりメガネ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER: 特殊技1.1倍
    if ctx.move.category == "特殊":
        return HandlerReturn(True, value * 11 // 10)
    return HandlerReturn(False, value)


def ラムのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: すべての状態異常を回復する（消費型）
    target = ctx.resolve_role(battle, "source:self")

    # 状態異常をチェック
    if target.ailment:
        return common.cure_ailment(battle, ctx, value, "source:self")

    # volatiles（こんらん等）はここでは処理しない（状態異常のみ対応）
    return HandlerReturn(False)
