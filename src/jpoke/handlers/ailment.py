from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.utils.type_defs import RoleSpec
from jpoke.utils.math import apply_fixed_modifier
from jpoke.enums import LogCode
from jpoke.core import Handler, HandlerReturn


class AilmentHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100):
        super().__init__(
            func=func,
            source="ailment",
            subject_spec=subject_spec,
            priority=priority,
        )


def どく_damage(battle: Battle, ctx: EventContext, value: Any):
    """どく状態によるターン終了時ダメージ（最大HPの1/8、最小1）。"""
    mon = ctx.source
    damage = max(1, mon.max_hp // 8)
    battle.modify_hp(mon, v=-damage, reason="poison")
    return HandlerReturn(value=value)


def もうどく_damage(battle: Battle, ctx: EventContext, value: Any):
    """もうどく状態によるターン終了時ダメージ（経過ターンに比例して増加）。

    ダメージ量: max(1, 最大HP × min(15, 経過ターン数) // 16)
    経過ターン数の上限は15（最大ダメージは最大HP × 15/16）。
    """
    battle.ailment_manager.tick(ctx.source)
    mon = ctx.source
    turns = min(15, mon.ailment.elapsed_turns)
    damage = max(1, mon.max_hp * turns // 16)
    battle.modify_hp(mon, v=-damage, reason="poison")
    return HandlerReturn(value=value)


def まひ_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """まひ状態による素早さ半減"""
    return HandlerReturn(value=value // 2)


def まひ_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（12.5%確率）。

    Champions仕様: 行動不能率は12.5%（SV以前の25%から変更）。
    """
    # テスト用に確率を固定できる
    if battle.test_option.trigger_ailment is not None:
        trigger = battle.test_option.trigger_ailment
    else:
        trigger = battle.random.random() < 0.125

    if trigger:
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload={"reason": "まひ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def やけど_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """やけど状態によるターン終了時ダメージ（最大HPの1/16、最小1）。"""
    mon = ctx.source
    damage = max(1, mon.max_hp // 16)
    battle.modify_hp(mon, v=-damage, reason="burn")
    return HandlerReturn(value=value)


def やけど_modifier(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """やけど状態による物理技ダメージ半減"""
    if battle.resolve_move_category(ctx.attacker, ctx.move) == "物理":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def ねむり_check_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねむり状態による行動不能チェック"""
    mon = ctx.attacker
    battle.ailment_manager.tick(mon)
    if not mon.has_ailment("ねむり"):
        # 眠りから覚めた：ハンドラを解除して空の状態に
        battle.ailment_manager.remove(mon)
        return HandlerReturn(value=True)

    if ctx.move.name in ["いびき", "ねごと"] or ctx.attacker.sleep_talk_active:
        return HandlerReturn(value=True)

    # まだ眠っている
    battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                         payload={"reason": "ねむり"})

    return HandlerReturn(value=False, stop_event=True)


def こおり_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こおり状態による行動不能チェック。

    Champions仕様:
    - わざを出す直前に25%の確率で解凍（SV以前は20%）
    - 行動不能2回の後（3回目の行動時）は必ず解凍
    """
    mon = ctx.attacker

    # 3回目の行動時は必ず解凍（elapsed_turns >= 2 = 既に2回行動不能）
    if mon.ailment.elapsed_turns >= 2:
        battle.ailment_manager.remove(mon)
        return HandlerReturn(value=True)

    # テスト用に確率を固定できる
    if battle.test_option.trigger_ailment is not None:
        thaw = battle.test_option.trigger_ailment
    else:
        thaw = battle.random.random() < 0.25

    if thaw:
        # 解凍した：ハンドラを解除して空の状態に
        battle.ailment_manager.remove(mon)
        return HandlerReturn(value=True)

    # まだ凍っている：行動不能カウントを増やす
    battle.ailment_manager.tick(mon)
    battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                         payload={"reason": "こおり"})
    return HandlerReturn(value=False, stop_event=True)


def こおり_cure_by_fire_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ほのお技でダメージを受けたら解凍する。"""
    if ctx.move.type == "ほのお":
        battle.ailment_manager.remove(ctx.defender)
    return HandlerReturn(value=value)
