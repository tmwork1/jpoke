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
from jpoke.utils.battle_math import apply_fixed_modifier
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
            source="item",
            subject_spec=subject_spec,
            priority=priority,
            once=once,
        )


def _consume_self_item(battle: Battle, target) -> bool:
    if not target.has_item():
        return False

    battle.add_event_log(target, LogCode.CONSUME_ITEM, payload={"item": target.item.name})
    battle.consume_item(target)
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
    return HandlerReturn(value=value)


def いかさまダイス_modify_hit_count(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いかさまダイス: 2-5回連続技のヒット数を4回または5回へ補正する。"""
    min_hits, max_hits = ctx.move.min_hits, ctx.move.max_hits
    if (min_hits, max_hits) == (2, 5):
        value = 4 if battle.random.random() < 0.5 else 5
    return HandlerReturn(value=value)


def だっしゅつボタン_trigger_switch(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    player = battle.get_player(ctx.defender)
    player.interrupt = Interrupt.EJECTBUTTON
    return HandlerReturn(value=value)


def だっしゅつパック_on_stat_down(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # valueは{stat: change}の辞書
    player = battle.get_player(ctx.target)
    if any(v < 0 for v in value.values()) and \
            bool(battle.get_available_switch_commands(player)):
        player.interrupt = Interrupt.REQUESTED
    return HandlerReturn(value=value)


def たべのこし_heal_hp(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # HPを1/16回復
    if battle.modify_hp(ctx.source, r=1/16):
        ctx.source.item.revealed = True
    return HandlerReturn(value=value)


def ちからのハチマキ_boost_physical(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """物理技1.1倍"""
    if ctx.move.category == "物理":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def ものしりメガネ_boost_special(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """特殊技1.1倍"""
    if ctx.move.category == "特殊":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def ラムのみ_cure_ailments(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ON_BEFORE_ACTION: すべての状態異常を回復する（消費型）
    target = ctx.resolve_role(battle, "source:self")

    # 状態異常をチェック
    if target.ailment:
        result = common.cure_ailment(battle, ctx, value, "source:self")
        if result.value:
            _consume_self_item(battle, target)
        return result

    # volatiles（こんらん等）はここでは処理しない（状態異常のみ対応）
    return HandlerReturn(value=value)
