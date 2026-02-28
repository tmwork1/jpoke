from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec, LogPolicy
from jpoke.enums import LogCode
from jpoke.core import Handler, HandlerReturn


class AilmentHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 log: LogPolicy = "on_success",
                 log_text: str | None = None,
                 priority: int = 100):
        super().__init__(func, subject_spec, "ailment", log, log_text, priority)


def もうどく(battle: Battle, ctx: BattleContext, value: Any):
    ctx.source.ailment.count += 1
    r = max(-1, -ctx.source.ailment.count/16)
    success = battle.modify_hp(ctx.source, r=r)
    return HandlerReturn(success)


def まひ_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """まひ状態による素早さ半減"""
    return HandlerReturn(True, value // 2)


def まひ_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（25%確率）"""
    # テスト用に確率を固定できる
    if battle.test_option.trigger_ailment is not None:
        trigger = battle.test_option.trigger_ailment
    else:
        trigger = battle.random.random() < 0.25

    if trigger:
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload={"reason": "まひ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def やけど_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """やけど状態によるターン終了時ダメージ（1/16）"""
    success = battle.modify_hp(ctx.source, r=-1/16)
    return HandlerReturn(success)


def やけど_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """やけど状態による物理技ダメージ半減"""
    if ctx.move and ctx.move.category == "物理":
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def ねむり_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねむり状態による行動不能チェック"""
    mon = ctx.attacker
    mon.tick_down_ailment(battle)
    if mon.ailment.count == 0:
        # 眠りから覚めた：ハンドラを解除して空の状態に
        mon.cure_ailment(battle)
        return HandlerReturn(value=True)
    # まだ眠っている
    battle.add_event_log(mon, LogCode.ACTION_BLOCKED,
                         payload={"reason": "ねむり"})
    return HandlerReturn(value=False, stop_event=True)


def こおり_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """こおり状態による行動不能チェック（20%確率で解凍）"""
    # テスト用に確率を固定できる
    if battle.test_option.trigger_ailment is not None:
        thaw = battle.test_option.trigger_ailment
    else:
        thaw = battle.random.random() < 0.2

    mon = ctx.attacker
    if thaw:
        # 解凍した：ハンドラを解除して空の状態に
        mon.cure_ailment(battle)
        return HandlerReturn(value=True)
    # まだ凍っている
    battle.add_event_log(mon, LogCode.ACTION_BLOCKED,
                         payload={"reason": "こおり"})
    return HandlerReturn(value=False, stop_event=True)
