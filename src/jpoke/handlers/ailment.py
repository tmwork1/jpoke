from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.utils.type_defs import RoleSpec, LogPolicy
from jpoke.core.event import Handler, HandlerReturn


class AilmentHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 log: LogPolicy = "on_success",
                 log_text: str | None = None,
                 priority: int = 100):
        super().__init__(func, subject_spec, "ailment", log, log_text, priority)


def もうどく(battle: Battle, ctx: EventContext, value: Any):
    ctx.target.ailment.count += 1
    r = max(-1, -ctx.target.ailment.count/16)
    success = battle.modify_hp(ctx.target, r=r)
    return HandlerReturn(success)


def まひ_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """まひ状態による素早さ半減"""
    return HandlerReturn(True, value // 2)


def まひ_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（25%確率）"""
    # テスト用に確率を固定できる
    if battle.test_option.ailment_trigger_rate is not None:
        trigger = battle.test_option.ailment_trigger_rate >= 0.25
    else:
        trigger = battle.random.random() < 0.25

    if trigger:
        # ログはハンドラ側では出力しない（log_policyで制御）
        return HandlerReturn(False)
    return HandlerReturn(True)


def やけど_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """やけど状態によるターン終了時ダメージ（1/16）"""
    success = battle.modify_hp(ctx.target, r=-1/16)
    return HandlerReturn(success)


def やけど_burn(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """やけど状態による物理技ダメージ半減"""
    if ctx.move and ctx.move.category == "物理":
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def ねむり_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねむり状態による行動不能チェック"""
    if ctx.target.ailment.count > 0:
        ctx.target.ailment.count -= 1
        if ctx.target.ailment.count == 0:
            # 回復時はハンドラを解除して空の状態に
            ctx.target.ailment.unregister_handlers(battle.events, ctx.target)
            from jpoke.model.ailment import Ailment
            ctx.target.ailment = Ailment()
            return HandlerReturn(True)
        # まだねむっている
        return HandlerReturn(False)
    return HandlerReturn(True)


def こおり_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こおり状態による行動不能チェック（20%確率で解凍）"""
    # テスト用に確率を固定できる
    if battle.test_option.ailment_trigger_rate is not None:
        thaw = battle.test_option.ailment_trigger_rate >= 0.2
    else:
        thaw = battle.random.random() < 0.2

    if thaw:
        # 解凍した：ハンドラを解除して空の状態に
        ctx.target.ailment.unregister_handlers(battle.events, ctx.target)
        from jpoke.model.ailment import Ailment
        ctx.target.ailment = Ailment()
        return HandlerReturn(True)
    # まだ凍っている
    return HandlerReturn(False)
