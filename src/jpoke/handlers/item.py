from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
from functools import partial
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.enums import Interrupt
from jpoke.core.event import EventContext, HandlerReturn, Handler
from jpoke.utils.type_defs import LogPolicy, RoleSpec
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
    # ON_BEFORE_ACTION: HP50%以下時にHP50%回復
    target = ctx.resolve_role(battle, "source:self")
    if target.hp <= target.max_hp // 2:
        return common.heal_hp(battle, ctx, value, "source:self", r=0.5)
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
    # ON_BEFORE_ACTION: やけど状態時にやけどを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "やけど":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def チーゴのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: どく状態時にどくを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "どく":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def ナナシのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: こんらん状態時にこんらんを治す
    target = ctx.resolve_role(battle, "source:self")
    if "こんらん" in target.volatiles:
        target.volatiles.pop("こんらん", None)
        return HandlerReturn(True)
    return HandlerReturn(False)


def キーのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: こおり状態時にこおりを治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "こおり":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def ヒメリのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: メロメロ状態時にメロメロを治す
    target = ctx.resolve_role(battle, "source:self")
    if "メロメロ" in target.volatiles:
        target.volatiles.pop("メロメロ", None)
        return HandlerReturn(True)
    return HandlerReturn(False)


def オレンのみ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: まひ状態時にまひを治す（クラボのみと同じ）
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment == "まひ":
        return common.cure_ailment(battle, ctx, value, "source:self")
    return HandlerReturn(False)


def ひかりごけ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: HP50%以下時にHP25%回復
    target = ctx.resolve_role(battle, "source:self")
    if target.hp <= target.max_hp // 2:
        return common.heal_hp(battle, ctx, value, "source:self", r=0.25)
    return HandlerReturn(False)


def きゅうこん(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: 毒/火傷/まひ状態時に治す
    target = ctx.resolve_role(battle, "source:self")
    if target.ailment in ("どく", "やけど", "まひ"):
        return common.cure_ailment(battle, ctx, value, "source:self")
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


def シルクのスカーフ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER: ノーマル技1.2倍
    if ctx.move.type == "ノーマル":
        return HandlerReturn(True, value * 6 // 5)
    return HandlerReturn(False, value)


def こくばバット(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER: 悪技1.2倍
    if ctx.move.type == "悪":
        return HandlerReturn(True, value * 6 // 5)
    return HandlerReturn(False, value)


def つめたいいわ(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER: 氷技1.2倍
    if ctx.move.type == "氷":
        return HandlerReturn(True, value * 6 // 5)
    return HandlerReturn(False, value)


def もくたん(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER: 炎技1.2倍
    if ctx.move.type == "炎":
        return HandlerReturn(True, value * 6 // 5)
    return HandlerReturn(False, value)


# ===== 難易度1: フィールド延長系 =====

# さらさらいわ は既に実装済み（ON_CHECK_DURATIONですなあらし+3ターン）
