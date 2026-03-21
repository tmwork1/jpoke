from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec
from jpoke.enums import LogCode
from jpoke.core import Handler, HandlerReturn


class AilmentHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100):
        super().__init__(func, subject_spec, "ailment", priority)


def もうどく(battle: Battle, ctx: BattleContext, value: Any):
    battle.ailment_manager.tick(ctx.source)
    r = -ctx.source.ailment.elapsed_turns/16
    battle.modify_hp(ctx.source, r=r, reason="もうどく")
    return HandlerReturn()


def まひ_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """まひ状態による素早さ半減"""
    return HandlerReturn(value=value // 2)


def まひ_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（25%確率）"""
    # テスト用に確率を固定できる
    if battle.test_option.trigger_ailment is not None:
        trigger = battle.test_option.trigger_ailment
    else:
        trigger = battle.random.random() < 0.25

    if trigger:
        idx = battle.get_player_index(ctx.attacker)
        battle.event_logger.add(battle.turn, idx, LogCode.ACTION_BLOCKED, payload={"reason": "まひ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def やけど_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """やけど状態によるターン終了時ダメージ（1/16）"""
    battle.modify_hp(ctx.source, r=-1/16, reason="やけど")
    return HandlerReturn()


def やけど_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """やけど状態による物理技ダメージ半減"""
    if ctx.move and ctx.move.category == "物理":
        return HandlerReturn(value=value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(value=value)


def ねむり_check_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねむり状態による行動不能チェック"""
    mon = ctx.attacker
    battle.ailment_manager.tick(mon)
    if not mon.has_ailment("ねむり"):
        # 眠りから覚めた：ハンドラを解除して空の状態に
        battle.ailment_manager.remove(mon)
        return HandlerReturn(value=True)
    # まだ眠っている
    idx = battle.get_player_index(mon)
    battle.event_logger.add(battle.turn, idx, LogCode.ACTION_BLOCKED, payload={"reason": "ねむり"})
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
        battle.ailment_manager.remove(mon)
        return HandlerReturn(value=True)
    # まだ凍っている
    battle.add_event_log(mon, LogCode.ACTION_BLOCKED,
                         payload={"reason": "こおり"})
    return HandlerReturn(value=False, stop_event=True)
