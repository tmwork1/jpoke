"""特性ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from functools import partial
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec, HPChangeReason, Type, Stat
from jpoke.utils.constants import PLATE_TO_TYPE, MEMORY_TO_TYPE
from jpoke.utils.battle_math import rank_modifier, apply_fixed_modifier
from jpoke.enums import Event, LogCode
from jpoke.core import HandlerReturn, Handler
from . import common


AEGISLASH_NAME = "ギルガルド"
AEGISLASH_SHIELD_ALIAS = "ギルガルド(シールド)"
AEGISLASH_BLADE_ALIAS = "ギルガルド(ブレード)"
PALAFIN_NAME = "イルカマン"
PALAFIN_ZERO_ALIAS = "イルカマン(ナイーブ)"
PALAFIN_HERO_ALIAS = "イルカマン(マイティ)"


class AbilityHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            subject_spec=subject_spec,
            priority=priority,
            once=once,
        )


def _apply_contact_counter_ailment(
    battle: Battle,
    ctx: BattleContext,
    *,
    ailment: str,
    chance: float,
) -> bool:
    """接触被弾時カウンターの状態異常付与を試行する。"""
    if not battle.move_executor.is_contact(ctx) or battle.random.random() >= chance:
        return False

    battle.ailment_manager.apply(
        ctx.attacker,
        ailment,
        source=ctx.defender,
        origin_ctx=ctx,
    )
    return True


def _apply_contact_counter_chip(
    battle: Battle,
    ctx: BattleContext,
    *,
    ratio: float,
) -> bool:
    """接触被弾時カウンターの固定割合ダメージを適用する。"""
    if not battle.move_executor.is_contact(ctx) or ctx.attacker.fainted:
        return False

    battle.modify_hp(ctx.attacker, r=-ratio, reason="ability")
    return True


def _trigger_emergency_switch(battle: Battle, mon, ability_name: str) -> bool:
    """緊急交代を発動する。"""
    from jpoke.enums import Interrupt

    player = battle.find_player(mon)
    if player.interrupt != Interrupt.NONE:
        return False
    if not battle.get_available_switch_commands(player):
        return False

    player.interrupt = Interrupt.EMERGENCY
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": ability_name, "success": True},
    )
    return True


def _handle_type_absorb(battle: Battle,
                        ctx: BattleContext,
                        value: bool,
                        *,
                        ability_name: str,
                        move_type: Type,
                        heal_ratio: float = 0,
                        raise_stat: Stat | None = None) -> HandlerReturn:
    """タイプ一致技を無効化し、副次効果（回復/能力上昇）を適用する。"""
    if (
        value
        or ctx.move is None
        or not ctx.is_foe_target
        or ctx.move.type != move_type
        or not ctx.check_def_ability_enabled(battle)
    ):
        return HandlerReturn(value=value)

    target = ctx.defender

    if heal_ratio > 0:
        battle.modify_hp(target, r=heal_ratio, reason="ability")

    if raise_stat is not None:
        battle.modify_stat(
            target,
            raise_stat,
            1,
            source=ctx.attacker,
            reason=ability_name,
        )

    idx = battle.get_player_index(target)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": ability_name, "success": True},
    )
    return HandlerReturn(value=True, stop_event=True)


def _modify_by_move_condition(battle: Battle,
                              ctx: BattleContext,
                              value: int,
                              *,
                              modifier: int,
                              move_type: Type | None = None,
                              move_label: str | None = None) -> HandlerReturn:
    """技のタイプ/ラベル条件を満たすときのみ固定倍率補正を適用する。"""
    if ctx.move is None:
        return HandlerReturn(value=value)
    if move_type is not None and ctx.move.type != move_type:
        return HandlerReturn(value=value)
    if move_label is not None and not ctx.move.has_label(move_label):
        return HandlerReturn(value=value)

    value = apply_fixed_modifier(value, modifier)
    return HandlerReturn(value=value)


def _activate_weather_with_log(battle: Battle,
                               ctx: BattleContext,
                               value: Any,
                               *,
                               weather: str,
                               ability_name: str) -> HandlerReturn:
    """天候を変更し、LogCode.ABILITY_TRIGGERED を記録する。"""
    battle.weather_manager.activate(weather, 5, source=ctx.source)
    mon = ctx.source
    mon.ability.revealed = True
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": ability_name, "success": True}
    )
    return HandlerReturn(value=value)


def _activate_terrain_with_log(battle: Battle,
                               ctx: BattleContext,
                               value: Any,
                               *,
                               terrain: str,
                               ability_name: str) -> HandlerReturn:
    """地形を変更し、LogCode.ABILITY_TRIGGERED を記録する。"""
    battle.terrain_manager.activate(terrain, 5, source=ctx.source)
    mon = ctx.source
    mon.ability.revealed = True
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": ability_name, "success": True}
    )
    return HandlerReturn(value=value)


def _apply_ailment_with_log(battle: Battle,
                            ctx: BattleContext,
                            value: Any,
                            *,
                            ailment: str,
                            ability_name: str) -> HandlerReturn:
    """自身に状態異常を付与し、LogCode.ABILITY_TRIGGERED を記録する。"""
    mon = ctx.source
    battle.ailment_manager.apply(mon, ailment, source=mon)
    mon.ability.revealed = True
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": ability_name, "success": True}
    )
    return HandlerReturn(value=value)


def _modify_speed_by_weather_names(battle: Battle,
                                   value: int,
                                   *,
                                   weather_names: set[str],
                                   multiplier: int) -> HandlerReturn:
    """指定天候のとき素早さを2倍にする。"""
    active = battle.weather
    if active is not None and active.name in weather_names:
        value *= multiplier
    return HandlerReturn(value=value)


def あまのじゃく_modify_stat(battle: Battle, ctx: BattleContext, value: dict[str, int]) -> HandlerReturn:
    """あまのじゃく特性: 能力変化量の符号を反転する。"""
    return HandlerReturn(value={stat: -delta for stat, delta in value.items()})


def たんじゅん_modify_stat(battle: Battle, ctx: BattleContext, value: dict[str, int]) -> HandlerReturn:
    """たんじゅん特性: 能力変化量を2倍にする。"""
    if ctx.check_def_ability_enabled(battle):
        value = {stat: delta * 2 for stat, delta in value.items()}
    return HandlerReturn(value=value)


def だっぴ_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """だっぴ特性: ターン終了時に30%で状態異常を回復する。"""
    mon = ctx.source
    if mon is None or not mon.ability.enabled or not mon.ailment.is_active:
        return HandlerReturn(value=value)

    result = common.cure_ailment(
        battle,
        ctx,
        value,
        target_spec="source:self",
        source_spec="source:self",
        chance=0.3,
    )
    if result.value:
        idx = battle.get_player_index(mon)
        battle.event_logger.add(
            battle.turn,
            idx,
            LogCode.ABILITY_TRIGGERED,
            payload={"ability": "だっぴ", "success": True},
        )
    return HandlerReturn(value=value)


def ダウンロード_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ダウンロード特性: 入場時に相手の防御と特防を比較し、低い方に対応する攻撃能力を上げる。"""
    mon = ctx.source
    if not mon.ability.enabled:
        return HandlerReturn(value=value)

    foe = battle.foe(mon)

    def _rank_eff(pokemon, stat: str) -> float:
        return pokemon.stats[stat] * rank_modifier(pokemon.rank[stat])

    foe_def = _rank_eff(foe, "B")
    foe_spd = _rank_eff(foe, "D")

    # 防御 < 特防 なら攻撃+1、防御 >= 特防 なら特攻+1
    boost_stat = "A" if foe_def < foe_spd else "C"

    changed = battle.modify_stat(
        mon,
        boost_stat,
        +1,
        source=mon,
        reason="ダウンロード",
    )
    if not changed:
        return HandlerReturn(value=value)

    mon.ability.revealed = True
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ダウンロード", "success": True},
    )
    return HandlerReturn(value=value)


def あとだし_on_calc_back_tier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """あとだし特性: 同一優先度の行動の中で最後に行動する（後攻ティア -1）。"""
    return HandlerReturn(value=-1)


def あめうけざら_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あめうけざら特性: あめ/おおあめ中にターン終了時に最大HPの1/16を回復する。"""
    mon = ctx.source
    active = battle.weather
    if active is None or active.name not in ("あめ", "おおあめ"):
        return HandlerReturn(value=value)
    if mon.item.orig_name == "ばんのうがさ":
        return HandlerReturn(value=value)
    result = battle.modify_hp(mon, r=1/16)
    if result:
        idx = battle.get_player_index(mon)
        battle.event_logger.add(
            battle.turn, idx, LogCode.ABILITY_TRIGGERED,
            payload={"ability": "あめうけざら", "success": True},
        )
    return HandlerReturn(value=value)


def いしあたま_ignore_recoil(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いしあたま特性: 反動ダメージを受けない。"""
    if ctx.hp_change_reason == "recoil" and ctx.target.ability.enabled:
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def いかく_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """いかく特性: 登場時に相手のこうげきを1段階下げる。"""
    return common.modify_stat(
        battle,
        ctx,
        value,
        stat="A",
        v=-1,
        target_spec="source:foe",
        source_spec="source:self",
    )


def いたずらごころ_modify_move_priority(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いたずらごころ特性: 変化技の優先度を+1する。"""
    if ctx.move is not None and ctx.move.category == "変化":
        value += 1
    return HandlerReturn(value=value)


def いたずらごころ_block_dark_target(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """いたずらごころ特性: 優先度が上がった変化技はあくタイプ相手に無効化される。"""
    if (
        value
        or ctx.move is None
        or ctx.move.category != "変化"
        or ctx.move.priority < 0
        or not ctx.is_foe_target
        or not ctx.defender.has_type("あく")
    ):
        return HandlerReturn(value=value)

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "いたずらごころ", "success": True},
    )
    return HandlerReturn(value=True, stop_event=True)


def エアロック_check_weather_enabled(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """エアロック特性: 天候効果を無効化する。"""
    return HandlerReturn(value=False, stop_event=True)


def ありじごく_check_trapped(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ありじごく特性: 浮いていないポケモンの交代を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_TRAPPED)
            - source: 交代を試みるポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: (True, 交代が制限されるかどうか)
            - 浮いていない場合はTrue（交代制限）
    """
    # ポケモンが浮いているかどうかを判定
    # 浮いている = ふゆう、でんじふゆう、テレキネシス等
    result = not battle.query_manager.is_floating(ctx.source)
    return HandlerReturn(value=result)


def かげふみ_check_trapped(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かげふみ特性: かげふみ持ち以外のポケモンの交代を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_TRAPPED)
            - source: 交代を試みるポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: (True, 交代が制限されるかどうか)
            - かげふみ持ち以外はTrue（交代制限）
    """
    result = ctx.source.ability.name != "かげふみ"
    return HandlerReturn(value=result)


def かがくへんかガス_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かがくへんかガス特性: 場の特性有効状態を再計算する。"""
    battle.refresh_effect_enabled_states()

    mon = ctx.source
    mon.ability.revealed = True
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "かがくへんかガス", "success": True}
    )
    return HandlerReturn(value=value)


def ぎゃくじょう_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ぎゃくじょう特性: HP が半分以下になった時、特攻が1段階上昇する。"""
    if ctx.defender.fainted:
        return HandlerReturn(value=value)

    # マルチヒット時は全ヒットのダメージを累算し、最終ヒット後に判定する
    if not hasattr(ctx, "total_damage"):
        ctx.total_damage = 0
    ctx.total_damage += ctx.move_damage

    if ctx.hit_index != ctx.hit_count:
        return HandlerReturn(value=value)

    hp_after = ctx.defender.hp
    hp_before = hp_after + ctx.total_damage
    del ctx.total_damage

    if not common.crossed_half_hp(hp_before, hp_after, ctx.defender.max_hp):
        return HandlerReturn(value=value)

    changed = battle.modify_stat(
        ctx.defender,
        "C",
        +1,
        source=ctx.attacker,
        reason="ぎゃくじょう",
    )
    if not changed:
        return HandlerReturn(value=value)

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ぎゃくじょう", "success": True},
    )
    return HandlerReturn(value=value)


def ききかいひ_on_hp_change(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ききかいひ特性: HPが半分以下になったとき交代する。"""
    mon = ctx.target
    if mon is None or mon.fainted:
        return HandlerReturn(value=value)
    # こんらん自傷、いたみわけでは交代できない
    if ctx.hp_change_reason in {"self_attack", "pain_split"}:
        return HandlerReturn(value=value)

    hp_after = mon.hp
    hp_before = hp_after + value
    if not common.crossed_half_hp(hp_before, hp_after, mon.max_hp):
        return HandlerReturn(value=value)

    _trigger_emergency_switch(battle, mon, mon.ability.orig_name)
    return HandlerReturn(value=value)


def きゅうばん_check_blow(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """きゅうばん特性: 強制交代技の効果を防ぐ。

    ふきとばし、ほえる、ドラゴンテール、ともえなげなどで相手に強制交代させられない。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_HIT)
            - defender: この特性を持つポケモン
        value: イベント値（技がヒットしたかどうか）

    Returns:
        HandlerReturn: 強制交代技がヒットしても技の交代効果を無効化
    """
    if value and ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def きれあじ_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """きれあじ特性: きる技の威力を1.5倍にする。"""
    if ctx.move is not None and ctx.move.has_label("slash"):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def きんちょうかん_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """きんちょうかん特性: 登場時の処理（ログ用途のフック）。"""
    return HandlerReturn(value=value)


def きんちょうかん_check_nervous(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """きんちょうかん特性: 相手のきのみ使用を禁止する。"""
    return HandlerReturn(value=True)


def じりょく_check_trapped(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """じりょく特性: はがねタイプのポケモンの交代を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_TRAPPED)
            - source: 交代を試みるポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: (True, 交代が制限されるかどうか)
            - はがねタイプの場合はTrue（交代制限）
    """
    result = ctx.source.has_type("はがね")
    return HandlerReturn(value=result)


def じしんかじょう_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """じしんかじょう特性: 攻撃技で相手を倒すと攻撃が1段階上がる。"""
    if not ctx.defender.fainted:
        return HandlerReturn(value=value)

    changed = battle.modify_stat(
        ctx.attacker,
        "A",
        +1,
        source=ctx.attacker,
        reason="じしんかじょう",
    )
    if not changed:
        return HandlerReturn(value=value)

    idx = battle.get_player_index(ctx.attacker)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "じしんかじょう", "success": True},
    )
    return HandlerReturn(value=value)


def ポイズンヒール_modify_poison_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ポイズンヒール特性: どく/もうどく由来のHP変化を最大HPの1/8回復に置き換える。"""
    mon = ctx.target
    if value < 0 and mon.ability.enabled:
        value = mon.max_hp // 8
    return HandlerReturn(value=value)


def さいせいりょく_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さいせいりょく特性: 交代で引っ込んだとき最大HPの1/3を回復する（かいふくふうじ無効）。"""
    mon = ctx.source
    if not mon.ability.enabled:
        return HandlerReturn(value=value)
    result = battle.modify_hp(mon, r=1/3, reason="bench_heal")
    if result:
        idx = battle.get_player_index(mon)
        battle.event_logger.add(
            battle.turn, idx, LogCode.ABILITY_TRIGGERED,
            payload={"ability": "さいせいりょく", "success": True},
        )
    return HandlerReturn(value=value)


def さめはだ_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さめはだ特性: 接触技を受けた相手に最大HPの1/8ダメージを与える。"""
    _apply_contact_counter_chip(battle, ctx, ratio=1/8)
    return HandlerReturn(value=value)


def サンパワー_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """サンパワー特性: にほんばれ/おおひでり中に特殊技の特攻補正を1.5倍にする。"""
    active = battle.weather
    if (
        active is not None
        and active.name in ("はれ", "おおひでり")
        and ctx.move is not None
        and common.is_special_move(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def サンパワー_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """サンパワー特性: にほんばれ/おおひでり中にターン終了時に最大HPの1/8ダメージを受ける。"""
    mon = ctx.source
    active = battle.weather
    if active is None or active.name not in ("はれ", "おおひでり"):
        return HandlerReturn(value=value)
    if not mon.ability.enabled:
        return HandlerReturn(value=value)
    result = battle.modify_hp(mon, r=-1/8)
    if result:
        idx = battle.get_player_index(mon)
        battle.event_logger.add(
            battle.turn, idx, LogCode.ABILITY_TRIGGERED,
            payload={"ability": "サンパワー", "success": True},
        )
    return HandlerReturn(value=value)


def しぜんかいふく_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しぜんかいふく特性: 交代で引っ込んだとき状態異常を回復する。"""
    mon = ctx.source
    if not mon.ability.enabled:
        return HandlerReturn(value=value)
    result = common.cure_ailment(battle, ctx, value, "source:self")
    if result.value:
        idx = battle.get_player_index(mon)
        battle.event_logger.add(
            battle.turn, idx, LogCode.ABILITY_TRIGGERED,
            payload={"ability": "しぜんかいふく", "success": True},
        )
    return HandlerReturn(value=value)


def しめりけ_block_explosion_self(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しめりけ特性（攻撃側）: 自分が爆発技を使おうとしたとき失敗させる。"""
    if (
        ctx.move is not None
        and ctx.move.has_label("explosion")
        and ctx.attacker is not None
        and ctx.attacker.ability.enabled
    ):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def しめりけ_block_explosion_foe(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しめりけ特性（防御側）: 相手が爆発技を使おうとしたとき失敗させる。"""
    if (
        ctx.move is not None
        and ctx.move.has_label("explosion")
        and ctx.check_def_ability_enabled(battle)
    ):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def しゅうかく_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しゅうかく特性: ターン終了時に消費したきのみを復活させる。"""
    mon = ctx.source

    berry_name = mon.item.orig_name
    if (
        mon.has_item()
        or not mon.item.lost
        or mon.item.lost_cause != "consume"
        or not common.is_berry_item(berry_name)
    ):
        return HandlerReturn(value=value)

    # 発動確率の計算
    if battle.weather is not None and battle.weather.is_sunny:
        chance = 1.0
    else:
        chance = 0.5

    if battle.random.random() >= chance:
        return HandlerReturn(value=value)

    battle.set_item(mon, berry_name)

    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "しゅうかく", "success": True},
    )

    # 復活直後に使用条件を満たすきのみは、その場で使用される。
    battle.events.emit(Event.ON_ITEM_RESTORED, ctx.__class__(source=mon))
    return HandlerReturn(value=value)


def ちょすい_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ちょすい特性: みず技を無効化し最大HPの1/4回復する。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="ちょすい",
        move_type="みず",
        heal_ratio=1 / 4,
    )


def どしょく_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """どしょく特性: じめん技を無効化し最大HPの1/4回復する。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="どしょく",
        move_type="じめん",
        heal_ratio=1 / 4,
    )


def ちくでん_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ちくでん特性: でんき技を無効化し最大HPの1/4回復する。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="ちくでん",
        move_type="でんき",
        heal_ratio=1 / 4,
    )


def そうしょく_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """そうしょく特性: くさ技を無効化し攻撃を1段階上げる。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="そうしょく",
        move_type="くさ",
        raise_stat="A",
    )


def ひらいしん_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ひらいしん特性: でんき技を無効化し特攻を1段階上げる。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="ひらいしん",
        move_type="でんき",
        raise_stat="C",
    )


def でんきエンジン_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """でんきエンジン特性: でんき技を無効化し素早さを1段階上げる。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="でんきエンジン",
        move_type="でんき",
        raise_stat="S",
    )


def よびみず_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """よびみず特性: みず技を無効化し特攻を1段階上げる。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="よびみず",
        move_type="みず",
        raise_stat="C",
    )


def もらいび_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技を無効化し、炎技強化状態を有効化する。"""
    if (
        value
        or ctx.move is None
        or not ctx.is_foe_target
        or ctx.move.type != "ほのお"
        or not ctx.check_def_ability_enabled(battle)
    ):
        return HandlerReturn(value=value)

    ctx.defender.ability.state = "charged"

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "もらいび", "success": True},
    )
    return HandlerReturn(value=True, stop_event=True)


def もらいび_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """もらいび特性: 登場時に炎技強化状態を初期化する。"""
    ctx.source.ability.state = "idle"
    return HandlerReturn(value=value)


def もらいび_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """もらいび特性: 吸収後の最初のほのお技のみ威力を1.5倍にする。"""
    if (
        ctx.move is not None
        and ctx.move.type == "ほのお"
        and ctx.attacker.ability.state == "active"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def もらいび_on_move_charge(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技使用時に強化適用予約。"""
    if (
        value
        and ctx.move is not None
        and ctx.move.type == "ほのお"
        and ctx.source.ability.state == "charged"
    ):
        ctx.source.ability.state = "active"
    return HandlerReturn(value=value)


def もらいび_on_move_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """もらいび特性: 行動終了時に強化を消費済みにする。"""
    state = ctx.source.ability.state
    if state == "active":
        ctx.source.ability.state = "idle"
    return HandlerReturn(value=value)


def はらぺこスイッチ_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """はらぺこスイッチ特性: 交代時のフォルム状態を更新する。"""
    # テラスタル中に交代した場合は現在のフォルムを維持する。
    # ただし瀕死退場時はまんぷくへ戻す。
    if ctx.source.is_terastallized and ctx.source.alive:
        return HandlerReturn(value=value)

    ctx.source.ability.is_hangry = False
    return HandlerReturn(value=value)


def はらぺこスイッチ_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """はらぺこスイッチ特性: ターン終了時にフォルムを切り替える。"""
    if ctx.source.is_terastallized:
        return HandlerReturn(value=value)

    ctx.source.ability.is_hangry = not ctx.source.ability.is_hangry
    return HandlerReturn(value=value)


def はらぺこスイッチ_modify_move_type(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """はらぺこスイッチ特性: オーラぐるまのタイプをフォルムで変える。"""
    if ctx.move is not None and ctx.move.name == "オーラぐるま":
        value = "あく" if ctx.source.ability.is_hangry else "でんき"
    return HandlerReturn(value=value)


def バトルスイッチ_check_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 行動前に必要なフォルムへ切り替える。"""
    mon = ctx.source
    if mon is None or mon.name != AEGISLASH_NAME or ctx.move is None:
        return HandlerReturn(value=value)

    next_alias = ""
    if mon.alias == AEGISLASH_SHIELD_ALIAS and ctx.move.is_attack:
        next_alias = AEGISLASH_BLADE_ALIAS
    elif mon.alias == AEGISLASH_BLADE_ALIAS and ctx.move.name == "キングシールド":
        next_alias = AEGISLASH_SHIELD_ALIAS

    if not next_alias:
        return HandlerReturn(value=value)

    mon.set_form(next_alias)

    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "バトルスイッチ", "success": True},
    )
    return HandlerReturn(value=value)


def バトルスイッチ_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 交代時にシールドフォルムへ戻す。"""
    mon = ctx.source
    if mon is not None and mon.name == AEGISLASH_NAME:
        mon.set_form(AEGISLASH_SHIELD_ALIAS)
    return HandlerReturn(value=value)


def かちき_on_stat_down(battle: Battle, ctx: BattleContext, value: dict[str, int]) -> HandlerReturn:
    """かちき特性: 能力が下がると特攻が2段階上昇する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_STAT)
            - target: 能力変化の対象（自分）
            - source: 能力変化の原因
        value: 能力変化の辞書 {stat: change}

    Returns:
        HandlerReturn: (処理実行フラグ)
            - 能力が下がり、自分以外が原因の場合は特攻上昇
    """
    # いずれかの能力が下がったかチェック
    has_negative = any(v < 0 for v in value.values())
    # 自分以外が原因で能力が下がった場合、特攻を2段階上昇
    result = has_negative and \
        ctx.source != ctx.target and \
        common.modify_stat(battle, ctx, value, "C", +2, target_spec="target:self", source_spec="target:self")
    return HandlerReturn(value=result)


def かるわざ_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かるわざ特性: 入場時に発動可否の初期状態を記録する。"""
    mon = ctx.source
    # "idle": 入場時に持ち物あり（消失で発動可能）
    # "inactive": 入場時に持ち物なし（この在場中は発動しない）
    mon.ability.state = "idle" if mon.has_item() else "inactive"
    return HandlerReturn(value=value)


def かるわざ_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """かるわざ特性: 持ち物消失中は素早さを2倍にする。"""
    mon = ctx.source

    # 入場時に持ち物がなかった個体は、この在場中は発動しない。
    if mon.ability.state == "inactive":
        return HandlerReturn(value=value)

    # 発動中に持ち物を再取得したら解除（再消費で再発動できる状態へ戻す）。
    if mon.ability.state == "active" and mon.has_item():
        mon.ability.state = "idle"
        return HandlerReturn(value=value)

    # 持ち物を失ったら発動状態へ遷移。
    if mon.ability.state == "idle" and mon.item.lost:
        mon.ability.state = "active"

    if mon.ability.state == "active" and not mon.has_item():
        value *= 2
    return HandlerReturn(value=value)


def かそく_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かそく特性: 行動済みならターン終了時に素早さを1段階上げる。"""
    mon = ctx.source
    if mon is not None and mon.executed_move is not None:
        battle.modify_stat(mon, "S", +1, source=mon)
    return HandlerReturn(value=value)


def カブトアーマー_on_calc_critical_rank(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """カブトアーマー特性: 防御側の急所ランクを無効化する。"""
    if ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def きょううん_modify_critical_rank(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """きょううん特性: 攻撃側の急所ランクを+1する。"""
    if ctx.move is not None:
        value += 1
    return HandlerReturn(value=value)


def すなかき_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すなかき特性: すなあらし中に素早さが2倍になる。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 元の素早さ値

    Returns:
        HandlerReturn: (True, 補正後の素早さ)
            - すなあらし中は2倍、それ以外は元の値
    """
    return _modify_speed_by_weather_names(
        battle,
        value,
        weather_names={"すなあらし"},
        multiplier=2,
    )


def すなかき_ignore_sandstorm_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すなかき特性: すなあらしのダメージを受けない。"""
    return common.ignore_damage_by_reason(battle, ctx, value, reason="sandstorm_damage")


def すながくれ_ignore_sandstorm_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すながくれ特性: すなあらしのダメージを受けない。"""
    return common.ignore_damage_by_reason(battle, ctx, value, reason="sandstorm_damage")


def すなのちから_ignore_sandstorm_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すなのちから特性: すなあらしのダメージを受けない。"""
    return common.ignore_damage_by_reason(battle, ctx, value, reason="sandstorm_damage")


def すりぬけ_check_infiltrate(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """すりぬけ特性: 相手の壁・みがわりを貫通して攻撃する。"""
    if ctx.attacker.ability.enabled:
        return HandlerReturn(value=True, stop_event=True)
    return HandlerReturn(value=value)


def すいすい_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すいすい特性: あめ中に素早さが2倍になる。"""
    return _modify_speed_by_weather_names(
        battle,
        value,
        weather_names={"あめ", "おおあめ"},
        multiplier=2,
    )


def スキルリンク_modify_hit_count(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """スキルリンク特性: 連続技のヒット数を最大にする。"""
    if ctx.move.data.max_hits > 1:
        value = ctx.move.data.max_hits
    return HandlerReturn(value=value)


def ねんちゃく_prevent_item_change(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ねんちゃく特性: 相手から受ける持ち物交換・奪取・除去を防ぐ。"""
    if (
        value
        and ctx.source != ctx.target
        and (ctx.move is None or ctx.check_def_ability_enabled(battle))
    ):
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add(
            battle.turn,
            idx,
            LogCode.ABILITY_TRIGGERED,
            payload={"ability": "ねんちゃく", "success": True},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def マジシャン_steal_item(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マジシャン特性: 攻撃成功後に相手の持ち物を奪う。"""
    if (
        ctx.move_damage != 0
        and not ctx.attacker.has_item()
        and ctx.defender.has_item()
    ):
        battle.take_item(ctx.attacker, ctx.defender, move=ctx.move)
    return HandlerReturn(value=value)


def マイティチェンジ_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マイティチェンジ特性: ナイーブフォルムで引っ込むとマイティフォルムへ変化する。"""
    mon = ctx.source
    if (
        mon is not None
        and mon.name == PALAFIN_NAME
        and mon.alias == PALAFIN_ZERO_ALIAS
        and mon.alive
    ):
        mon.set_form(PALAFIN_HERO_ALIAS)

        idx = battle.get_player_index(mon)
        battle.event_logger.add(
            battle.turn,
            idx,
            LogCode.ABILITY_TRIGGERED,
            payload={"ability": "マイティチェンジ", "success": True},
        )
    return HandlerReturn(value=value)


def わるいてぐせ_steal_item(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """わるいてぐせ特性: 直接攻撃を受けた後に相手の持ち物を奪う。"""
    if (
        ctx.move_damage != 0
        and not ctx.defender.fainted
        and not ctx.defender.has_item()
        and ctx.attacker.has_item()
        and battle.move_executor.is_contact(ctx)
    ):
        battle.take_item(ctx.defender, ctx.attacker, move=ctx.move)
    return HandlerReturn(value=value)


def せいしんりょく_prevent_flinch(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """せいしんりょく特性: ひるみ状態を防ぐ。"""
    if value == "ひるみ" and ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def せいしんりょく_block_intimidate(battle: Battle, ctx: BattleContext, value: dict) -> HandlerReturn:
    """せいしんりょく特性: いかくによる攻撃ランク低下を無効化する。"""
    if (
        ctx.source is not None
        and ctx.source.ability.name == "いかく"
        and ctx.check_def_ability_enabled(battle)
    ):
        value = common.block_stat_drop(value, ctx, "A")
    return HandlerReturn(value=value)


def せいでんき_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """せいでんき特性: 直接攻撃を受けた相手を30%でまひにする。"""
    _apply_contact_counter_ailment(battle, ctx, ailment="まひ", chance=0.3)
    return HandlerReturn(value=value)


def どくしゅ_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """どくしゅ特性: 直接攻撃でダメージを与えた相手を30%でどくにする。"""
    if (
        not ctx.has_move_context
        or not battle.move_executor.is_contact(ctx)
        or battle.random.random() >= 0.3
    ):
        return HandlerReturn(value=value)

    battle.ailment_manager.apply(
        ctx.defender,
        "どく",
        source=ctx.attacker,
        origin_ctx=ctx,
    )
    return HandlerReturn(value=value)


def どくのトゲ_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """どくのトゲ特性: 直接攻撃を受けた相手を30%でどくにする。"""
    _apply_contact_counter_ailment(battle, ctx, ailment="どく", chance=0.3)
    return HandlerReturn(value=value)


def てつのこぶし_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """てつのこぶし特性: パンチ技の威力を1.2倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=4915,
        move_label="punch",
    )


def がんじょうあご_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """がんじょうあご特性: かみつき技の威力を1.5倍にする。"""
    if ctx.move is not None and ctx.move.has_label("bite"):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def かたいツメ_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """かたいツメ特性: 直接攻撃の威力を1.3倍にする。"""
    if ctx.move is not None and battle.move_executor.is_contact(ctx):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def かんそうはだ_check_water_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """かんそうはだ特性: みず技を無効化し、HPが減っていれば最大HPの1/4を回復する。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="かんそうはだ",
        move_type="みず",
        heal_ratio=1 / 4,
    )


def かんそうはだ_modify_fire_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """かんそうはだ特性: ほのお技を受けたときの威力が5/4倍になる。"""
    if (
        ctx.check_def_ability_enabled(battle)
        and ctx.move is not None
        and ctx.move.type == "ほのお"
        and ctx.move.category != "変化"
    ):
        value = apply_fixed_modifier(value, 5120)  # 5/4倍 = 5120/4096
    return HandlerReturn(value=value)


def かんそうはだ_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かんそうはだ特性: 天候に応じてターン終了時にHP変化を受ける。"""
    mon = ctx.source
    weather = battle.weather_manager.active

    # 天候が有効でない場合はスキップ
    if weather is None or not mon.ability.enabled:
        return HandlerReturn(value=value)

    # ばんのうがさ判定
    if mon.item.orig_name == "ばんのうがさ":
        return HandlerReturn(value=value)

    if weather.name in ("あめ", "おおあめ"):
        # あめ中は最大HPの1/8回復
        result = battle.modify_hp(mon, r=1 / 8)
        if result:
            idx = battle.get_player_index(mon)
            battle.event_logger.add(
                battle.turn,
                idx,
                LogCode.ABILITY_TRIGGERED,
                payload={"ability": "かんそうはだ", "success": True},
            )
    elif weather.is_sunny:
        # にほんばれ中は最大HPの1/8ダメージ
        result = battle.modify_hp(mon, r=-1 / 8)
        if result:
            idx = battle.get_player_index(mon)
            battle.event_logger.add(
                battle.turn,
                idx,
                LogCode.ABILITY_TRIGGERED,
                payload={"ability": "かんそうはだ", "success": True},
            )

    return HandlerReturn(value=value)


def メガランチャー_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """メガランチャー特性: はどう技の威力を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_label="pulse",
    )


def パンクロック_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """パンクロック特性: 音技の威力を1.3倍にする。"""
    if ctx.move is not None and ctx.move.has_label("sound"):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ぼうおん_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ぼうおん特性: 音技を無効化する。"""
    if (
        not value
        and ctx.move is not None
        and ctx.move.has_label("sound")
        and ctx.check_def_ability_enabled(battle)
    ):
        return HandlerReturn(value=True, stop_event=True)
    return HandlerReturn(value=value)


def ぼうじん_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ぼうじん特性: 粉・胞子系の技を無効化する。"""
    if (
        not value
        and ctx.move is not None
        and ctx.move.has_label("powder")
        and ctx.check_def_ability_enabled(battle)
    ):
        return HandlerReturn(value=True, stop_event=True)
    return HandlerReturn(value=value)


def ぼうじん_ignore_sandstorm_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ぼうじん特性: すなあらしのダメージを受けない。"""
    return common.ignore_damage_by_reason(battle, ctx, value, reason="sandstorm_damage")


def ぼうだん_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ぼうだん特性: 弾の技を無効化する。"""
    if (
        not value
        and ctx.move is not None
        and ctx.move.has_label("bullet")
        and ctx.check_def_ability_enabled(battle)
    ):
        return HandlerReturn(value=True, stop_event=True)
    return HandlerReturn(value=value)


def ほのおのからだ_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ほのおのからだ特性: 直接攻撃を受けた相手を30%でやけどにする。"""
    _apply_contact_counter_ailment(battle, ctx, ailment="やけど", chance=0.3)
    return HandlerReturn(value=value)


def すなのちから_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すなのちから特性: すなあらし中の岩/地面/鋼技の威力を1.3倍にする。"""
    active = battle.weather
    if (
        ctx.move is not None
        and active is not None
        and active.name == "すなあらし"
        and ctx.move.type in ["いわ", "じめん", "はがね"]
    ):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def どくぼうそう_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """どくぼうそう特性: どく状態時のどく特殊技威力を1.5倍にする。"""
    if (
        (ctx.attacker.has_ailment("どく") or ctx.attacker.has_ailment("もうどく"))
        and ctx.move is not None
        and ctx.move.type == "どく"
        and common.is_special_move(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ねつぼうそう_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ねつぼうそう特性: やけど状態時のほのお特殊技威力を1.5倍にする。"""
    if (
        ctx.attacker.has_ailment("やけど")
        and ctx.move is not None
        and ctx.move.type == "ほのお"
        and common.is_special_move(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ねつこうかん_prevent_burn(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """ねつこうかん特性: やけど状態を防ぐ。"""
    if value == "やけど" and ctx.check_def_ability_enabled(battle):
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add(battle.turn, idx, LogCode.ABILITY_TRIGGERED, payload={"ability": "ねつこうかん", "success": True})
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def ねつこうかん_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねつこうかん特性: ほのおタイプの攻撃技でダメージを受けたとき、こうげきが1段階上がる。"""
    if (
        not ctx.has_move_context
        or ctx.move.type != "ほのお"
        or ctx.defender.fainted
        or not ctx.check_def_ability_enabled(battle)
    ):
        return HandlerReturn(value=value)

    changed = battle.modify_stat(
        ctx.defender,
        "A",
        +1,
        source=ctx.attacker,
        reason="ねつこうかん",
    )
    if not changed:
        return HandlerReturn(value=value)

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ねつこうかん", "success": True},
    )
    return HandlerReturn(value=value)


def アイスボディ_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """アイスボディ特性: ゆき中にターン終了時に最大HPの1/16を回復する。"""
    mon = ctx.source
    active = battle.weather
    if active is None or active.name != "ゆき":
        return HandlerReturn(value=value)
    result = battle.modify_hp(mon, r=1/16)
    if result:
        idx = battle.get_player_index(mon)
        battle.event_logger.add(
            battle.turn, idx, LogCode.ABILITY_TRIGGERED,
            payload={"ability": "アイスボディ", "success": True},
        )
    return HandlerReturn(value=value)


def アナライズ_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """アナライズ特性: 行動が後になったターンの技威力を1.3倍にする。"""
    if ctx.defender is not None:
        defender_player = battle.find_player(ctx.defender)
        acted_before = ctx.defender.executed_move is not None or defender_player.has_switched
        if acted_before:
            value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def こんじょう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """こんじょう特性: 状態異常時に物理技の攻撃補正を1.5倍にする。"""
    if (
        ctx.attacker.ailment.is_active
        and common.is_physical_move(battle, ctx)
        and ctx.move.name not in ["イカサマ", "ボディプレス"]
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def こんじょう_ignore_burn_penalty(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """こんじょう特性: 状態異常時はやけどの物理半減を無効化する。"""
    if ctx.attacker.ailment.is_active and common.is_physical_move(battle, ctx):
        value = 4096
    return HandlerReturn(value=value)


def はやあし_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はやあし特性: 状態異常時に素早さが1.5倍になる。まひの素早さ低下も無効化する。"""
    mon = ctx.source
    if not mon.ailment.is_active or not mon.ability.enabled:
        return HandlerReturn(value=value)

    if mon.has_ailment("まひ"):
        # まひ_speed による 1/2 ペナルティを打ち消して 1.5 倍（合計 *3）
        value = value * 3
    else:
        value = value * 1.5
    return HandlerReturn(value=value)


def はりきり_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はりきり特性: 物理技の攻撃補正を1.5倍にする。"""
    if common.is_physical_move(battle, ctx):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def はりきり_modify_accuracy(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はりきり特性: 物理技（一撃必殺・必中技除外）の命中率を0.8倍にする。"""
    if (
        common.is_physical_move(battle, ctx)
        and not ctx.move.has_label("ohko")  # 一撃必殺技は命中率ペナルティなし
        and ctx.move.accuracy is not None  # 必中技は命中率ペナルティなし
    ):
        value = apply_fixed_modifier(value, 3277)
    return HandlerReturn(value=value)


def はりこみ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はりこみ特性: 交代直後の相手に対する攻撃補正を2倍にする。"""
    if ctx.defender is not None and battle.find_player(ctx.defender).has_switched:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def しんりょくもうかげきりゅうむしのしらせ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ピンチ系特性: HP1/3以下かつ対応タイプ技で攻撃補正を1.5倍にする。"""
    required_type = {
        "しんりょく": "くさ",
        "もうか": "ほのお",
        "げきりゅう": "みず",
        "むしのしらせ": "むし",
    }.get(ctx.attacker.ability.name)

    if (
        ctx.move is not None
        and ctx.attacker.hp * 3 <= ctx.attacker.max_hp
        and ctx.move.type == required_type
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def いわはこび_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いわはこび特性: いわ技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_type="いわ",
    )


def はがねつかい_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はがねつかい特性: はがね技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_type="はがね",
    )


def はがねのせいしん_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はがねのせいしん特性: はがね技の威力を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_type="はがね",
    )


def りゅうのあぎと_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """りゅうのあぎと特性: ドラゴン技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_type="ドラゴン",
    )


def ごりむちゅう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ごりむちゅう特性: 物理技の攻撃補正を1.5倍にする。"""
    if common.is_physical_move(battle, ctx) and ctx.move.name not in ["イカサマ", "ボディプレス"]:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def トランジスタ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """トランジスタ特性: でんき技の攻撃補正を1.3倍にする。"""
    if ctx.move is not None and ctx.move.type == "でんき":
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ひとでなし_modify_critical_rank(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ひとでなし特性: どく/もうどく状態の相手への攻撃を必ず急所にする。"""
    if ctx.attacker.ability.enabled and (
        ctx.defender.has_ailment("どく") or ctx.defender.has_ailment("もうどく")
    ):
        value = 10
    return HandlerReturn(value=value)


def ひひいろのこどう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ひひいろのこどう特性: はれ中の攻撃補正を1.33倍にする。"""
    active = battle.weather
    if active is not None and active.name == "はれ":
        value = apply_fixed_modifier(value, 5461)
    return HandlerReturn(value=value)


def ハドロンエンジン_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ハドロンエンジン特性: エレキフィールド中の攻撃補正を1.33倍にする。"""
    if battle.terrain.name == "エレキフィールド":
        value = apply_fixed_modifier(value, 5461)
    return HandlerReturn(value=value)


def スロースタート_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """スロースタート特性: 登場ターンを記録する。"""
    ctx.source.ability.count = battle.turn
    return HandlerReturn(value=value)


def スロースタート_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """スロースタート特性: 登場から5ターンの物理攻撃補正を0.5倍にする。"""
    if (
        battle.turn - ctx.attacker.ability.count < 5
        and common.is_physical_move(battle, ctx)
        and ctx.move.name not in ["イカサマ", "ボディプレス"]
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def よわき_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """よわき特性: HP半分以下で攻撃補正を0.5倍にする。"""
    if ctx.attacker.hp * 2 <= ctx.attacker.max_hp:
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def あついしぼう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """あついしぼう特性: 炎/氷技を受けるとき攻撃補正を0.5倍にする。"""
    if (
        ctx.check_def_ability_enabled(battle)
        and ctx.move is not None
        and ctx.move.type in ["ほのお", "こおり"]
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def たいねつ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """たいねつ特性: 炎技を受けるとき攻撃補正を0.5倍にする。"""
    if (
        ctx.check_def_ability_enabled(battle)
        and ctx.move is not None
        and ctx.move.type == "ほのお"
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def すいほう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すいほう特性: 水技の攻撃補正2倍、炎技被ダメ計算時の攻撃補正0.5倍。"""
    if ctx.move is not None:
        if ctx.attacker.ability.name == "すいほう" and ctx.move.type == "みず":
            value = apply_fixed_modifier(value, 8192)

        if (
            ctx.defender.ability.name == "すいほう"
            and ctx.move.type == "ほのお"
            and ctx.check_def_ability_enabled(battle)
        ):
            value = apply_fixed_modifier(value, 2048)

    return HandlerReturn(value=value)


def きよめのしお_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """きよめのしお特性: ゴースト技を受けるとき攻撃補正を0.5倍にする。"""
    if (
        ctx.check_def_ability_enabled(battle)
        and ctx.move is not None
        and ctx.move.type == "ゴースト"
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def わざわいのおふだ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """わざわいのおふだ特性: 自分以外の攻撃補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def わざわいのうつわ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """わざわいのうつわ特性: 自分以外の特攻補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def ファーコート_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ファーコート特性: 物理技に対する防御補正を2倍にする。"""
    if ctx.check_def_ability_enabled(battle) and common.is_physical_move(battle, ctx):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ふしぎなうろこ_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ふしぎなうろこ特性: 状態異常時に物理技への防御補正を1.5倍にする。"""
    if (
        ctx.check_def_ability_enabled(battle)
        and ctx.defender.ailment.is_active
        and common.is_physical_move(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def くさのけがわ_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """くさのけがわ特性: ゆき中の物理技への防御補正を1.5倍にする。"""
    active = battle.weather
    if (
        ctx.check_def_ability_enabled(battle)
        and active is not None
        and active.name == "ゆき"
        and common.is_physical_move(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def わざわいのつるぎ_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """わざわいのつるぎ特性: 自分以外の防御補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def わざわいのたま_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """わざわいのたま特性: 自分以外の特防補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def いろめがね_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いろめがね特性: いまひとつの技の最終ダメージ補正を2倍にする。"""
    if common.is_not_very_effective(battle, ctx):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def スナイパー_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """スナイパー特性: 急所時の最終ダメージ補正を1.5倍にする。"""
    if getattr(ctx, "critical", False):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ブレインフォース_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ブレインフォース特性: 効果抜群時の最終ダメージ補正を1.25倍にする。"""
    if common.is_super_effective(battle, ctx):
        value = apply_fixed_modifier(value, 5120)
    return HandlerReturn(value=value)


def フィルターハードロックプリズムアーマー_modify_damage(
    battle: Battle,
    ctx: BattleContext,
    value: int,
) -> HandlerReturn:
    """防御側特性: 効果抜群の技ダメージを0.75倍にする。"""
    if (
        ctx.check_def_ability_enabled(battle)
        and common.is_super_effective(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def マルチスケイルファントムガード_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """防御側特性: HP満タン時の被ダメージを0.5倍にする。"""
    if (
        ctx.check_def_ability_enabled(battle)
        and ctx.defender.hp == ctx.defender.max_hp
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def こおりのりんぷん_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """こおりのりんぷん特性: 特殊技で受けるダメージを0.5倍にする。"""
    if ctx.check_def_ability_enabled(battle) and common.is_special_move(battle, ctx):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def パンクロック_reduce_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """パンクロック特性: 音技で受けるダメージを0.5倍にする。"""
    if (
        ctx.check_def_ability_enabled(battle)
        and ctx.move is not None
        and ctx.move.has_label("sound")
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def もふもふ_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """もふもふ特性: 接触技被ダメ0.5倍・炎技被ダメ2倍を適用する。"""
    if ctx.check_def_ability_enabled(battle):
        if ctx.move is not None and battle.move_executor.is_contact(ctx):
            value = apply_fixed_modifier(value, 2048)
        if ctx.move is not None and ctx.move.type == "ほのお":
            value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ちからもちヨガパワー_on_calc_atk_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ちからもち・ヨガパワー特性: 物理技時の攻撃補正を2.0倍にする。"""
    move_category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    if move_category == "物理" and ctx.move.name not in ["イカサマ", "ボディプレス"]:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def テクニシャン_on_calc_power_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """テクニシャン特性: 元威力60以下の技威力補正を1.5倍にする。"""
    if ctx.move.data.power is not None and ctx.move.data.power <= 60:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def テラスシェル_modify_def_type_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """テラスシェル特性: HP満タン時、等倍以上のタイプ相性を半減する。"""
    if (
        value >= 4096
        and ctx.defender.hp == ctx.defender.max_hp
        and ctx.check_def_ability_enabled(battle)
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def _skin_modify_move_type(battle: Battle, ctx: BattleContext, value: str, *, from_type: str, to_type: str) -> HandlerReturn:
    """スキン系特性共通: from_type の技を to_type に変換する。"""
    if ctx.move is not None and value == from_type:
        value = to_type
    return HandlerReturn(value=value)


def _skin_modify_power(battle: Battle, ctx: BattleContext, value: int, *, trigger_type: str) -> HandlerReturn:
    """スキン系特性共通: trigger_type だった技の威力を 4915/4096 倍にする。"""
    if ctx.move is not None and ctx.move.data.type == trigger_type:
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


スカイスキン_modify_move_type = partial(_skin_modify_move_type, from_type="ノーマル", to_type="ひこう")
スカイスキン_modify_power = partial(_skin_modify_power, trigger_type="ノーマル")
フェアリースキン_modify_move_type = partial(_skin_modify_move_type, from_type="ノーマル", to_type="フェアリー")
フェアリースキン_modify_power = partial(_skin_modify_power, trigger_type="ノーマル")
フリーズスキン_modify_move_type = partial(_skin_modify_move_type, from_type="ノーマル", to_type="こおり")
フリーズスキン_modify_power = partial(_skin_modify_power, trigger_type="ノーマル")


def ノーマルスキン_modify_move_type(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """ノーマルスキン特性: 全ての技をノーマルタイプに変換する（ステラタイプ除く）。"""
    if ctx.move is not None and value not in ("ノーマル", "ステラ"):
        value = "ノーマル"
    return HandlerReturn(value=value)


def ノーマルスキン_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ノーマルスキン特性: 変換した技の威力を4915/4096倍にする。"""
    if ctx.move is not None and ctx.move.data.type not in ("ノーマル", "ステラ"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def トレース_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トレース特性: 入場時に相手のコピー可能な特性へ変更する。"""
    mon = ctx.source
    foe = battle.foe(mon)

    copied_ability = foe.ability.name
    if not copied_ability or "uncopyable" in foe.ability.data.flags:
        return HandlerReturn(value=value)

    battle.set_ability(mon, copied_ability)

    mon.ability.revealed = True
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "トレース", "success": True},
    )

    # コピー直後に入場時処理を再評価し、いかく等の登場時効果を即時反映する。
    battle.events.emit(Event.ON_SWITCH_IN, ctx.__class__(source=mon))
    return HandlerReturn(value=value)


def トレース_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トレース特性: 交代時に元の特性へ戻す。"""
    mon = ctx.source
    battle.set_ability(mon, mon.base_ability_name, refresh_enabled_states=False)
    return HandlerReturn(value=value)


def おやこあい_modify_hit_count(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """おやこあい特性: 単発攻撃技を2ヒット化する。"""
    if ctx.move.is_attack and ctx.move.data.max_hits <= 1:
        value = 2
    return HandlerReturn(value=value)


def おやこあい_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """おやこあい特性: 2ヒット目のダメージを減衰させる。"""
    if ctx.hit_count >= 2 and ctx.hit_index == 2:
        value //= 4
    return HandlerReturn(value=value)


def てんねん_on_calc_atk_rank_modifier(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """てんねん特性: 防御側のとき相手の攻撃ランク補正を無視する。"""
    if ctx.check_def_ability_enabled(battle) and value != 1:
        value = 1
    return HandlerReturn(value=value)


def てんねん_on_calc_def_rank_modifier(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """てんねん特性: 攻撃側のとき相手の防御ランク補正を無視する。"""
    if value != 1:
        value = 1
    return HandlerReturn(value=value)


def てきおうりょく_modify_stab(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """てきおうりょく特性: タイプ一致補正を強化する。"""
    attacker = ctx.attacker
    if attacker is None or not attacker.ability.enabled:
        return HandlerReturn(value=value)

    # ステラテラスタル時はてきおうりょくがSTAB補正に影響しない。
    if attacker.is_terastallized and attacker._terastal == "ステラ":
        return HandlerReturn(value=value)

    if value == 6144:
        return HandlerReturn(value=8192)
    if value == 8192:
        return HandlerReturn(value=9216)
    return HandlerReturn(value=value)


def めんえき_prevent_poison(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """めんえき特性: どく・もうどく状態を防ぐ。"""
    return common.prevent_ailment(battle, ctx, value, ailment_names=["どく", "もうどく"], ability_name="めんえき")


def クリアボディ_modify_stat(battle: Battle, ctx: BattleContext, value: dict) -> HandlerReturn:
    """クリアボディ特性: 相手による能力ランク低下を無効化する。

    自分の技や反動による能力低下は防げない。
    """
    if ctx.check_def_ability_enabled(battle):
        value = common.block_stat_drop(value, ctx)
    return HandlerReturn(value=value)


def かいりきバサミ_modify_stat(battle: Battle, ctx: BattleContext, value: dict) -> HandlerReturn:
    """かいりきバサミ特性: 相手によるこうげきランク低下を無効化する。"""
    if ctx.check_def_ability_enabled(battle):
        value = common.block_stat_drop(value, ctx, "A")
    return HandlerReturn(value=value)


def はとむね_modify_stat(battle: Battle, ctx: BattleContext, value: dict) -> HandlerReturn:
    """はとむね特性: 相手によるぼうぎょランク低下を無効化する。"""
    if ctx.check_def_ability_enabled(battle):
        value = common.block_stat_drop(value, ctx, "B")
    return HandlerReturn(value=value)


def するどいめ_modify_stat(battle: Battle, ctx: BattleContext, value: dict) -> HandlerReturn:
    """するどいめ特性: 相手による命中率ランク低下を無効化する。"""
    if ctx.check_def_ability_enabled(battle):
        value = common.block_stat_drop(value, ctx, "ACC")
    return HandlerReturn(value=value)


def ノーガード_modify_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ノーガード特性: 命中判定を必中化する。

    攻撃側がノーガード、または防御側がノーガードの場合、
    命中率を None（必中）に設定する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_ACCURACY)
            - attacker: 攻撃側のポケモン
            - defender: 防御側のポケモン
        value: 現在の命中率

    Returns:
        HandlerReturn: None（必中化）またはそのまま
    """
    if value is not None:
        attacker_no_guard = ctx.attacker.ability.name == "ノーガード"
        defender_no_guard = ctx.defender.ability.name == "ノーガード"
        if attacker_no_guard or defender_no_guard:
            value = None
    return HandlerReturn(value=value)


def ふみん_prevent_sleep(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """ふみん特性: ねむり状態を防ぐ。"""
    return common.prevent_ailment(battle, ctx, value, ailment_names=["ねむり"], ability_name="ふみん")


def ふくがん_modify_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ふくがん特性: 使用技の命中率を1.3倍にする（一撃必殺技を除く）。"""
    if (
        value is not None
        and ctx.move is not None
        and not ctx.move.has_label("ohko")
        and ctx.attacker is not None
        and ctx.attacker.ability.enabled
    ):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ふゆう_check_floating(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ふゆう特性: 常に浮遊状態として扱う。"""
    return HandlerReturn(value=True)


def マジックガード_reduce_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """マジックガード特性: 間接ダメージを無効化する。"""
    # 直接ダメージ・自己由来の特定HP変動は無効化しない。
    if ctx.hp_change_reason not in {"move_damage", "pain_split", "self_attack", "self_cost"}:
        value = 0
    return HandlerReturn(value=value)


def マジックミラー_reflect(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """マジックミラー特性: 反射対象の変化技を跳ね返す。"""
    if ctx.check_def_ability_enabled(battle):
        value = ctx.move.has_label("reflectable")
    return HandlerReturn(value=value)


def ミラーアーマー_reflect_stat_drop(battle: Battle, ctx: BattleContext, value: dict) -> HandlerReturn:
    """ミラーアーマー特性: 相手由来の能力ランク低下を反射する。"""
    can_reflect = (
        ctx.stat_change_reason != "ミラーアーマー"
        and ctx.source is not None
        and ctx.source is not ctx.target
        and ctx.check_def_ability_enabled(battle)
    )
    if can_reflect:
        drops = {stat: v for stat, v in value.items() if v < 0}
        if drops:
            # 低下を source（相手）側へ反射（source を ctx.target にすることで「相手から下げられた」扱いになりまけんき等が正常発動）
            battle.modify_stats(ctx.source, drops, source=ctx.target, reason="ミラーアーマー")
            # 自分側の低下分を除去（上昇分は残す）
            value = {stat: v for stat, v in value.items() if v > 0}
    return HandlerReturn(value=value)


def ムラっけ_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ムラっけ特性: ターン終了時に1能力+2、別の1能力-1する。"""
    mon = ctx.source
    if mon is None or not mon.ability.enabled:
        return HandlerReturn(value=value)

    stats: tuple[Stat, ...] = ("A", "B", "C", "D", "S")
    raised_stat: Stat | None = None
    changed = False

    up_candidates = [stat for stat in stats if mon.rank[stat] < 6]
    if up_candidates:
        raised_stat = battle.random.choice(up_candidates)
        changed = battle.modify_stat(mon, raised_stat, +2, source=mon, reason="ムラっけ") or changed

    down_candidates = [stat for stat in stats if mon.rank[stat] > -6 and stat != raised_stat]
    if down_candidates:
        lowered_stat = battle.random.choice(down_candidates)
        changed = battle.modify_stat(mon, lowered_stat, -1, source=mon, reason="ムラっけ") or changed

    if changed:
        idx = battle.get_player_index(mon)
        battle.event_logger.add(
            battle.turn,
            idx,
            LogCode.ABILITY_TRIGGERED,
            payload={"ability": "ムラっけ", "success": True},
        )
    return HandlerReturn(value=value)


def ぶきよう_check_item_enabled(battle: Battle, ctx: BattleContext, should_enable: bool) -> HandlerReturn:
    """ぶきよう特性: 所持道具の効果を無効化する。"""
    if should_enable and ctx.source.ability.name == "ぶきよう" and ctx.source.ability.enabled:
        should_enable = False
    return HandlerReturn(value=should_enable)


def へんげんじざいリベロ_on_move_charge(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """へんげんじざい・リベロ: 技実行前に技タイプへ自身のタイプを変更する。"""
    can_activate = (
        value
        and ctx.source is not None
        and ctx.move is not None
        and not ctx.source.is_terastallized
        and not ctx.source.ability.activated_since_switch_in
    )
    if can_activate:
        move_type = ctx.move.type
        # 現在タイプと同じ技では発動しない。
        if move_type and not ctx.source.has_type(move_type):
            ctx.source.ability_override_type = move_type
            ctx.source.ability.activated_since_switch_in = True

            idx = battle.get_player_index(ctx.source)
            battle.event_logger.add(
                battle.turn,
                idx,
                LogCode.ABILITY_TRIGGERED,
                payload={"ability": ctx.source.ability.orig_name, "success": True},
            )
    return HandlerReturn(value=value)


def やるき_prevent_sleep(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """やるき特性: ねむり状態を防ぐ。"""
    return common.prevent_ailment(battle, ctx, value, ailment_names=["ねむり"], ability_name="やるき")


def ようりょくそ_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ようりょくそ特性: はれ中に素早さが2倍になる。"""
    return _modify_speed_by_weather_names(
        battle,
        value,
        weather_names={"はれ", "おおひでり"},
        multiplier=2,
    )


def ゆきかき_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ゆきかき特性: ゆき中に素早さが2倍になる。"""
    return _modify_speed_by_weather_names(
        battle,
        value,
        weather_names={"ゆき"},
        multiplier=2,
    )


def ゆきがくれ_modify_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ゆきがくれ特性: ゆき中に受ける技の命中率を3277/4096倍にする（必中技は除く）。"""
    if value is None:
        return HandlerReturn(value=value)
    active = battle.weather
    if active is not None and active.name == "ゆき" and ctx.check_def_ability_enabled(battle):
        value = apply_fixed_modifier(value, 3277)
    return HandlerReturn(value=value)


def マイペース_prevent_confusion(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """マイペース特性: こんらん状態を防ぐ（揮発状態の実装が必要）。

    Note:
        こんらんは揮発状態のため、別途ON_BEFORE_APPLY_VOLATILEイベントで実装

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (False, value) - 状態異常は防がない
    """
    # 状態異常は防がない（こんらんは揮発状態で別処理）
    return HandlerReturn(value=value)


def じゅうなん_prevent_paralysis(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """じゅうなん特性: まひ状態を防ぐ。"""
    return common.prevent_ailment(battle, ctx, value, ailment_names=["まひ"], ability_name="じゅうなん")


def みずのベール_prevent_burn(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """みずのベール特性: やけど状態を防ぐ。"""
    return common.prevent_ailment(battle, ctx, value, ailment_names=["やけど"], ability_name="みずのベール")


def マグマのよろい_prevent_freeze(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """マグマのよろい特性: こおり状態を防ぐ。"""
    return common.prevent_ailment(battle, ctx, value, ailment_names=["こおり"], ability_name="マグマのよろい")


def どんかん_prevent_volatile(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """どんかん特性: メロメロ・ちょうはつ・ゆうわく・いかくを防ぐ。

    Note:
        メロメロ・ちょうはつ・ゆうわくは揮発状態のため、
        別途ON_BEFORE_APPLY_VOLATILEイベントで実装が必要

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (False, value) - 状態異常は防がない
    """
    if value in ["メロメロ", "ちょうはつ", "ゆうわく", "いかく"] and ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def おうごんのからだ_block_status_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """おうごんのからだ特性: 他のポケモンからの変化技を無効化する。

    酸化しない丈夫な黄金の体が、相手からの変化技をすべて受けつけない。
    ただし、自分が対象の変化技や場を対象とした技は防がない。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_IMMUNE)
            - target: 防御側（自分）
            - attacker: 攻撃側（相手）
            - move: 使用する技
        value: 現在の無効化状態（初期値：False）

    Returns:
        HandlerReturn: 変化技を無効化した場合True, stop_event=True
    """
    # 変化技以外、自分対象や場対象、かたやぶり系、自身が非所持なら防がない。
    if (
        ctx.move.category != "変化"
        or not ctx.is_foe_target
        or not ctx.check_def_ability_enabled(battle)
        or ctx.target.ability.name != "おうごんのからだ"
    ):
        return HandlerReturn(value=value)

    # ログ出力
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "おうごんのからだ", "success": True}
    )

    return HandlerReturn(value=True, stop_event=True)


def かがくへんかガス_check_enabled(battle: Battle, ctx: BattleContext, should_enable: bool) -> HandlerReturn:
    """かがくへんかガス無効化判定（priority=10）。

    かがくへんかガスが場に発動していると、gas_proof を除く特性を無効化する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_ABILITY_ENABLED)
            - source: 判定対象のポケモン
        should_enable: 現在の有効化状態

    Returns:
        HandlerReturn: ガス発動中で無効化対象なら False、それ以外は should_enable をそのまま返す
    """
    if should_enable:
        # 本ハンドラが呼ばれる時点で、かがくへんかガス有効はイベント登録側で保証される。
        source_ability = ctx.source.ability
        if "gas_proof" not in source_ability.data.flags:
            should_enable = False
    return HandlerReturn(value=should_enable)


def announce_ability_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """汎用: 登場時に特性発動ログを記録する (ON_SWITCH_IN)。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_SWITCH_IN)
            - source: 登場したポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 変更なし
    """
    mon = ctx.source
    mon.ability.revealed = True
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": mon.ability.name, "success": True}
    )
    return HandlerReturn(value=value)


def かたやぶり_check_def_ability_enabled(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """かたやぶり系特性: 無視できる防御側特性の無視フラグを立てる。

    かたやぶり / ターボブレイズ / テラボルテージ で共用。
    防御側が とくせいガード を持つ場合は、とくせいガード側ハンドラ (priority=200) が
    値を元に戻すことで無視が打ち消される。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_DEF_ABILITY_ENABLED)
            - attacker: かたやぶり系特性所持ポケモン
            - defender: 防御側のポケモン
        value: 現在の防御側特性有効フラグ

    Returns:
        HandlerReturn: 無視対象なら False、それ以外は value
    """
    if "mold_breaker_ignorable" in ctx.defender.ability.data.flags:
        value = False
    return HandlerReturn(value=value)


def ばけのかわ_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ばけのかわ特性: 初回の攻撃技ダメージを防ぐ。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    # ばけのかわを消費して、このヒットの攻撃ダメージを0にする。
    battle.set_ability_enabled(ctx.defender, False)
    battle.modify_hp(ctx.defender, r=-1/8)

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ばけのかわ", "success": True},
    )
    return HandlerReturn(value=0)


# ===== がんじょう =====

def がんじょう_block_ohko(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """がんじょう特性: 一撃必殺技を無効化する。(ON_CHECK_IMMUNE / subject_spec="target:self")"""
    if ctx.move is None or not ctx.move.has_label("ohko") or not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "がんじょう", "success": True},
    )
    return HandlerReturn(value=True, stop_event=True)


def がんじょう_survive_lethal(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """がんじょう特性: HP満タン時の致死ダメージをHP1残しに補正する。(ON_BEFORE_DAMAGE_APPLY / subject_spec="target:self")"""
    target = ctx.target
    is_lethal_from_full = (
        ctx.hp_change_reason == "move_damage"
        and target.hp >= target.max_hp
        and target.hp + value <= 0
    )
    if is_lethal_from_full:
        idx = battle.get_player_index(target)
        battle.event_logger.add(
            battle.turn, idx, LogCode.ABILITY_TRIGGERED,
            payload={"ability": "がんじょう", "success": True},
        )
        value = -target.hp + 1
    return HandlerReturn(value=value)


# ===== ちからずく =====

def ちからずく_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ちからずく特性: 追加効果ありの技の威力を 1.3 倍にする。(ON_CALC_POWER_MODIFIER / subject_spec="attacker:self")"""
    if ctx.move is not None and ctx.move.data.move_secondary:
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ちからずく_on_modify_secondary_chance(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """ちからずく特性: 追加効果対象技の追加効果確率を 0 にする。"""
    if ctx.move is not None and ctx.move.data.move_secondary:
        value = 0.0
    return HandlerReturn(value=value)


def てんのめぐみ_on_modify_secondary_chance(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """てんのめぐみ特性: 追加効果対象技の追加効果確率を2倍にする。"""
    if ctx.move is not None and ctx.move.data.move_secondary:
        value = min(1.0, value * 2)
    return HandlerReturn(value=value)


def リーフガード_prevent_ailment(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """リーフガード特性: にほんばれ/おおひでり中に状態異常付与を防ぐ。"""
    active = battle.weather
    if (
        active is not None
        and active.name in ("はれ", "おおひでり")
        and ctx.check_def_ability_enabled(battle)
        and value != ""
    ):
        value = ""
        return HandlerReturn(value=value, stop_event=True)
    return HandlerReturn(value=value)


def りんぷん_modify_secondary_chance(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """りんぷん特性: 相手の攻撃技の追加効果を無効化する。"""
    if value > 0 and ctx.check_def_ability_enabled(battle):
        value = 0.0
    return HandlerReturn(value=value)


# ===== マルチタイプ / ARシステム 共通 =====


def _apply_multitype(mon, item_table: dict[str, str]) -> None:
    """道具に応じてポケモンのタイプを変更する共通ロジック。"""
    item_name = mon.item.orig_name if mon.has_item() else ""
    mon.ability_override_type = item_table.get(item_name)


def マルチタイプ_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マルチタイプ特性: 登場時にプレートに合わせてタイプを変更する。"""
    _apply_multitype(ctx.source, PLATE_TO_TYPE)
    return HandlerReturn(value=value)


def マルチタイプ_prevent_item_change(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """マルチタイプ特性: プレートの奪取・交換を防ぐ。(ON_CHECK_ITEM_CHANGE / subject_spec="target:self")"""
    # 持ち物がプレートの場合のみ保護
    item_name = ctx.target.item.orig_name if ctx.target.has_item() else ""
    if not value or ctx.source == ctx.target or item_name not in PLATE_TO_TYPE:
        return HandlerReturn(value=value)
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "マルチタイプ", "success": True},
    )
    return HandlerReturn(value=False, stop_event=True)


def ARシステム_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ARシステム特性: 登場時にメモリに合わせてタイプを変更する。"""
    _apply_multitype(ctx.source, MEMORY_TO_TYPE)
    return HandlerReturn(value=value)


def ARシステム_prevent_item_change(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ARシステム特性: メモリの奪取・交換を防ぐ。(ON_CHECK_ITEM_CHANGE / subject_spec="target:self")"""
    item_name = ctx.target.item.orig_name if ctx.target.has_item() else ""
    if not value or ctx.source == ctx.target or item_name not in MEMORY_TO_TYPE:
        return HandlerReturn(value=value)
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ARシステム", "success": True},
    )
    return HandlerReturn(value=False, stop_event=True)
