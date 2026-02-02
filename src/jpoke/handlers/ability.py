from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.core.event import HandlerReturn, Handler
from jpoke.utils.type_defs import LogPolicy, RoleSpec
from . import common


class AbilityHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 log: LogPolicy = "on_success",
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            subject_spec=subject_spec,
            source_type="ability",
            log=log,
            priority=priority,
            once=once,
        )


def ありじごく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    result = not ctx.source.is_floating(battle.events)
    return HandlerReturn(True, result)


def かげふみ(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    result = ctx.source.ability != "かげふみ"
    return HandlerReturn(True, result)


def じりょく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    result = ctx.source.has_type("はがね")
    return HandlerReturn(True, result)


def かちき(battle: Battle, ctx: EventContext, value: Any):
    # ON_MODIFY_STAT
    # valueは{stat: change}の辞書
    has_negative = any(v < 0 for v in value.values())
    result = has_negative and \
        ctx.source != ctx.target and \
        common.modify_stat(battle, ctx, value, "C", +2, target_spec="target:self", source_spec="target:self")
    return HandlerReturn(result)


def すなかき(battle: Battle, ctx: EventContext, value: Any):
    # ON_CALC_SPEED
    value = value * 2 if battle.weather == "すなあらし" else value
    return HandlerReturn(True, value)


def めんえき(battle: Battle, ctx: EventContext, value: Any):
    # ON_BEFORE_APPLY_AILMENT
    # どく・もうどく状態を防ぐ
    if value in ["どく", "もうどく"]:
        return HandlerReturn(True, "", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(False, value)  # 防がない


def ふみん(battle: Battle, ctx: EventContext, value: Any):
    # ON_BEFORE_APPLY_AILMENT
    # ねむり状態を防ぐ
    if value == "ねむり":
        return HandlerReturn(True, "", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(False, value)  # 防がない


def やるき(battle: Battle, ctx: EventContext, value: Any):
    # ON_BEFORE_APPLY_AILMENT
    # ねむり状態を防ぐ（ふみんと同じ効果）
    if value == "ねむり":
        return HandlerReturn(True, "", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(False, value)  # 防がない


def マイペース(battle: Battle, ctx: EventContext, value: Any):
    # ON_BEFORE_APPLY_AILMENT（こんらんは揮発状態なので後で別途実装）
    # ここでは状態異常の防御のみ（こんらんは揮発状態で別処理）
    return HandlerReturn(False, value)  # 状態異常は防がない


def じゅうなん(battle: Battle, ctx: EventContext, value: Any):
    # ON_BEFORE_APPLY_AILMENT
    # まひ状態を防ぐ
    if value == "まひ":
        return HandlerReturn(True, "", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(False, value)  # 防がない


def みずのベール(battle: Battle, ctx: EventContext, value: Any):
    # ON_BEFORE_APPLY_AILMENT
    # やけど状態を防ぐ
    if value == "やけど":
        return HandlerReturn(True, "", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(False, value)  # 防がない


def マグマのよろい(battle: Battle, ctx: EventContext, value: Any):
    # ON_BEFORE_APPLY_AILMENT
    # こおり状態を防ぐ
    if value == "こおり":
        return HandlerReturn(True, "", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(False, value)  # 防がない


def どんかん(battle: Battle, ctx: EventContext, value: Any):
    # ON_BEFORE_APPLY_AILMENT（メロメロ・ちょうはつは揮発状態なので後で別途実装）
    # ここでは状態異常の防御のみ
    return HandlerReturn(False, value)  # 状態異常は防がない
