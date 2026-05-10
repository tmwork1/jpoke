"""パラドックス特性（こだいかっせい / クォークチャージ）専用ハンドラー。"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext
    from jpoke.model import Pokemon

from jpoke.core import HandlerReturn
from jpoke.enums import LogCode
from jpoke.utils.battle_math import rank_modifier
from jpoke.utils.type_defs import Stat


# TODO : Pokemonクラスのメソッドとして実装すべき
def _effective_stat_with_rank(mon: Pokemon, stat: str) -> float:
    """指定能力の実効値（ランク補正込み）を返す。"""
    return mon.stats[stat] * rank_modifier(mon.rank[stat])


def _select_paradox_boost_stat(mon: Pokemon) -> Stat:
    """パラドックス補正の対象能力を選ぶ。
    実数値(ランク補正込み)が最も高い能力を選ぶ。同値時は A>B>C>D>S の順で先勝ち。
    """
    stat_order: tuple[Stat, ...] = ("A", "B", "C", "D", "S")
    best_stat: Stat = stat_order[0]
    best_value = _effective_stat_with_rank(mon, best_stat)
    for stat in stat_order[1:]:
        value = _effective_stat_with_rank(mon, stat)
        if value > best_value:
            best_stat = stat
            best_value = value
    return best_stat


def _can_consume_boost_energy(mon: Pokemon) -> bool:
    """ブーストエナジーを今消費できる状態かを判定する。"""
    return mon.has_item("ブーストエナジー") and mon.item.enabled


def _deactivate_paradox_boost(mon: Pokemon) -> None:
    """パラドックス補正状態を解除する。"""
    mon.paradox_boost_active = False
    mon.paradox_boost_stat = None
    mon.paradox_boost_source = ""


def _activate_paradox_boost(battle: Battle, mon: Pokemon, source: str) -> None:
    """パラドックス補正を有効化し、必要なら消費ログを記録する。"""
    mon.paradox_boost_active = True
    mon.paradox_boost_stat = _select_paradox_boost_stat(mon)
    mon.paradox_boost_source = source

    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": mon.ability.orig_name, "success": True}
    )

    if source == "item" and _can_consume_boost_energy(mon):
        # ブーストエナジー起動時は消費する。
        battle.add_event_log(mon, LogCode.CONSUME_ITEM, payload={"item": "ブーストエナジー"})
        battle.consume_item(mon)


def _refresh_paradox_boost(battle: Battle, mon: Pokemon) -> None:
    """場状態と所持アイテムからパラドックス補正の状態を再計算する。"""
    ability_name = mon.ability.orig_name

    # 能力ごとに参照する場の状態が異なる。
    if ability_name == "こだいかっせい":
        field_source = "weather"
        field_active = battle.weather.sunny
    else:
        field_source = "terrain"
        field_active = battle.terrain.name == "エレキフィールド"

    can_consume_item = _can_consume_boost_energy(mon)

    # すでにブーストが有効な場合は、場の状態とアイテム消費の両方を考慮して解除の要否を判定する。
    if mon.paradox_boost_active:
        # アイテム由来のブーストは場の変化で解除されない。
        if mon.paradox_boost_source == "item":
            return

        # 場由来のブーストで場が継続しているなら解除されない。
        if mon.paradox_boost_source == field_source and field_active:
            return

        _deactivate_paradox_boost(mon)
        if can_consume_item:
            _activate_paradox_boost(battle, mon, "item")
        return

    # ブーストが有効でない場合は、場の状態とアイテム消費の両方を考慮して発動の要否を判定する。
    # 場条件が成立している場合は、アイテムより場由来を優先する。
    if field_active:
        _activate_paradox_boost(battle, mon, field_source)
    elif can_consume_item:
        _activate_paradox_boost(battle, mon, "item")


def パラドックスチャージ_refresh(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """こだいかっせい/クォークチャージの補正状態を更新する。"""
    _refresh_paradox_boost(battle, ctx.source)
    return HandlerReturn(value=value)


def パラドックスチャージ_on_calc_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """素早さ補正時: S が強化対象なら 1.5 倍補正を適用する。"""
    mon = ctx.source
    if mon.paradox_boost_active and mon.paradox_boost_stat == "S":
        value = value * 6144 // 4096
    return HandlerReturn(value=value)


def パラドックスチャージ_on_calc_atk_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
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
        move_category = battle.move_executor.get_effective_move_category(attacker, ctx.move)
        boost_mon = attacker
        stat = "A" if move_category == "物理" else "C"

    if boost_mon.paradox_boost_active and boost_mon.paradox_boost_stat == stat:
        value = value * 5325 // 4096
    return HandlerReturn(value=value)


def パラドックスチャージ_on_calc_def_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """防御側補正時: 強化対象能力と参照能力が一致すれば 1.3 倍補正を適用する。"""
    move_category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    stat = "B" if move_category == "物理" or ctx.move.has_label("physical") else "D"

    if ctx.defender.paradox_boost_active and ctx.defender.paradox_boost_stat == stat:
        value = value * 5325 // 4096
    return HandlerReturn(value=value)
