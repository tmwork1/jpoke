"""持ち物ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
from functools import partial
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec, Type, Weather, Terrain
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


def announce_item_triggered(battle: Battle,
                            ctx: BattleContext,
                            value: Any,
                            *,
                            mon: Pokemon | None = None) -> HandlerReturn:
    if mon is None:
        mon = ctx.source

    mon.item.revealed = True
    battle.add_event_log(
        mon,
        LogCode.ITEM_TRIGGERED,
        payload={"item": mon.item.name}
    )
    return HandlerReturn(value=value)


def _consume_self_item(battle: Battle, target) -> bool:
    if not target.has_item():
        return False
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


def resolve_field_count(battle: Battle,
                        ctx: BattleContext,
                        value: list[Weather | Terrain | int],
                        *,
                        field: Weather | Terrain,
                        additonal_count: int) -> HandlerReturn:
    """指定場状態と一致するとき継続ターン数に加算する。"""
    name, count = value
    if field == name:
        count += additonal_count
    return HandlerReturn(value=[name, count])


def いのちのたま_recoil(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    if (
        ctx.move.category != "変化"
        and common.modify_hp(battle, ctx, value, target_spec="attacker:self", r=-1/8)
    ):
        announce_item_triggered(battle, ctx, value, mon=ctx.attacker)
    return HandlerReturn(value=value)


def いかさまダイス_modify_hit_count(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いかさまダイス: 2-5回連続技のヒット数を4回または5回へ補正する。"""
    min_hits, max_hits = ctx.move.min_hits, ctx.move.max_hits
    if (min_hits, max_hits) == (2, 5):
        value = 4 if battle.random.random() < 0.5 else 5
    return HandlerReturn(value=value)


def だっしゅつパック_trigger_switch(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # valueは{stat: change}の辞書
    mon = ctx.target
    player = battle.get_player(mon)
    if (
        any(v < 0 for v in value.values())
        and bool(battle.get_available_switch_commands(player))
    ):
        player.interrupt = Interrupt.REQUESTED
    return HandlerReturn(value=value)


def だっしゅつボタン_trigger_switch(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    player = battle.get_player(ctx.defender)
    player.interrupt = Interrupt.REQUESTED
    return HandlerReturn(value=value)


def たべのこし_heal_hp(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """たべのこし: ターン終了時HP回復"""
    mon = ctx.source
    if battle.modify_hp(mon, r=1/16):
        announce_item_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ちからのハチマキ_boost_physical(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """物理技1.1倍"""
    if ctx.move.category == "物理":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def とくせいガード_block_ability_disable(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """とくせいガード: 特性無効化をブロックする。"""
    ability = ctx.source.ability
    was_self_disabled = ability.consumed
    ability.reset_enable_state()
    # 自己無効化している特性はリセット後も無効状態を維持する
    if was_self_disabled:
        ability.set_disabled_reasons("consumed")
    return HandlerReturn(value=value)


def ものしりメガネ_boost_special(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """特殊技1.1倍"""
    if ctx.move.category == "特殊":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)
