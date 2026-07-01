"""パラドックス特性（こだいかっせい / クォークチャージ）専用ハンドラー。"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext
    from jpoke.model import Pokemon

from jpoke.core import HandlerReturn
from jpoke.enums import LogCode
from jpoke.utils.math import apply_fixed_modifier
from jpoke.utils.type_defs import BoostSource, Stat

from .ability import _announce_ability_triggered


def _select_paradox_boost_stat(mon: Pokemon) -> Stat:
    """パラドックス補正の対象能力を選ぶ。
    実数値(ランク補正込み)が最も高い能力を選ぶ。同値時は A>B>C>D>S の順で先勝ち。
    """
    stat_order: tuple[Stat, ...] = ("A", "B", "C", "D", "S")
    best_stat: Stat = stat_order[0]
    best_value = mon.ranked_stats[best_stat]
    for stat in stat_order[1:]:
        value = mon.ranked_stats[stat]
        if value > best_value:
            best_stat = stat
            best_value = value
    return best_stat


def _deactivate_paradox_boost(mon: Pokemon) -> None:
    """パラドックス補正状態を解除する。"""
    mon.paradox_boost_stat = None
    mon.paradox_boost_source = ""


def _activate_paradox_boost(battle: Battle,
                            mon: Pokemon,
                            source: BoostSource) -> None:
    """パラドックス補正を有効化し、必要なら消費ログを記録する。"""
    mon.paradox_boost_stat = _select_paradox_boost_stat(mon)
    mon.paradox_boost_source = source
    _announce_ability_triggered(battle, mon)

    # ブーストエナジーを消費する
    if source == "item" and mon.has_item("ブーストエナジー", consider_enabled=True):
        battle.item_manager.consume_item(mon)


def refresh_paradox_charge_state(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こだいかっせい/クォークチャージの補正状態を更新する。"""
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)

    # 能力ごとに参照する場の状態が異なる。
    if mon.ability.name == "こだいかっせい":
        field_active = battle.weather.sunny
    else:
        field_active = battle.terrain.name == "エレキフィールド"

    can_consume_item = mon.item.name == "ブーストエナジー"

    # すでにブーストが有効な場合は、場の状態とアイテム消費の両方を考慮して解除の要否を判定する。
    if mon.paradox_boost_stat is not None:
        # アイテム由来のブーストは場の変化で解除されない。
        if mon.paradox_boost_source == "item":
            return HandlerReturn(value=value)

        # 場由来のブーストで場が継続しているなら解除されない。
        if mon.paradox_boost_source == "field" and field_active:
            return HandlerReturn(value=value)

        _deactivate_paradox_boost(mon)
        if can_consume_item:
            _activate_paradox_boost(battle, mon, "item")
        return HandlerReturn(value=value)

    # ブーストが有効でない場合は、場の状態とアイテム消費の両方を考慮して発動の要否を判定する。
    # 場条件が成立している場合は、アイテムより場由来を優先する。
    if field_active:
        _activate_paradox_boost(battle, mon, "field")
    elif can_consume_item:
        _activate_paradox_boost(battle, mon, "item")

    return HandlerReturn(value=value)


def modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """素早さ補正時: S が強化対象なら 1.5 倍補正を適用する。"""
    mon = ctx.source
    if mon.paradox_boost_stat == "S":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def apply_atk_modifier(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """攻撃側補正時: 強化対象能力と参照能力が一致すれば 1.3 倍補正を適用する。"""
    attacker = ctx.attacker
    defender = ctx.defender

    if ctx.move.name == "イカサマ":
        boost_mon = defender
        stat = "A"
    elif ctx.move.name == "ボディプレス":
        boost_mon = attacker
        stat = "B"
    else:
        boost_mon = attacker
        stat = "A" if ctx.move.category == "物理" else "C"

    if boost_mon.paradox_boost_stat == stat:
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def apply_def_modifier(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """防御側補正時: 強化対象能力と参照能力が一致すれば 1.3 倍補正を適用する。"""
    if ctx.attacker is None or ctx.move is None or ctx.defender is None:
        return HandlerReturn(value=value)

    stat = "B" if battle.query.deals_physical_damage(ctx.attacker, ctx.move) else "D"
    if ctx.defender.paradox_boost_stat == stat:
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)
