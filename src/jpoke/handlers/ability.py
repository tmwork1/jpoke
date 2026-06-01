"""特性ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext
    from jpoke.model import Pokemon

from jpoke.utils.type_defs import Side, RoleSpec, Type, Stat, Weather, Terrain, \
    AilmentName, VolatileName, AbilityDisabledReason, ItemDisabledReason
from jpoke.data.signature_items import PLATE_TO_TYPE, MEMORY_TO_TYPE
from jpoke.utils.math import apply_fixed_modifier
from jpoke.enums import Event, LogCode, Interrupt
from jpoke.core import HandlerReturn, Handler
from . import common


AEGISLASH_SHIELD = "ギルガルド(シールド)"
AEGISLASH_BLADE = "ギルガルド(ブレード)"
PALAFIN_ZERO = "イルカマン(ナイーブ)"
PALAFIN_HERO = "イルカマン(マイティ)"


class AbilityHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            source="ability",
            subject_spec=subject_spec,
            priority=priority,
            once=once,
        )


def announce_ability_triggered(battle: Battle,
                               ctx: EventContext | None,
                               value: Any,
                               *,
                               mon: Pokemon | None = None) -> HandlerReturn:
    """汎用: 特性発動ログを記録する

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_SWITCH_IN)
            - source: 登場したポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 変更なし
    """
    if mon is None and ctx is not None:
        mon = ctx.source
    mon.ability.revealed = True
    battle.add_event_log(mon, LogCode.ABILITY_TRIGGERED,
                         payload={"ability": mon.ability.name})
    return HandlerReturn(value=value)


def _crossed_half_hp(hp_before: int, hp_after: int, max_hp: int) -> bool:
    """HPが最大HPの50%を跨いだかどうかを判定する。

    HPが 50% 超から 50% 以下へ移行したかを判定する。
    特性やアイテムの効果発動判定に使用。

    Args:
        hp_before: ダメージ前のHP
        hp_after: ダメージ後のHP
        max_hp: 最大HP

    Returns:
        bool: 50%を跨いだら True
    """
    return hp_before * 2 > max_hp and hp_after * 2 <= max_hp


def _apply_contact_counter_ailment(battle: Battle,
                                   ctx: EventContext,
                                   *,
                                   ailment: AilmentName,
                                   chance: float) -> bool:
    """接触被弾時カウンターの状態異常付与を試行する。"""
    if (
        battle.query.is_contact(ctx)
        and battle.random.random() < chance
    ):
        battle.ailment_manager.apply(
            ctx.attacker, ailment, source=ctx.defender, ctx=ctx,
        )
        return True
    return False


def _apply_contact_counter_chip(battle: Battle,
                                ctx: EventContext,
                                *,
                                ratio: float) -> bool:
    """接触被弾時カウンターの固定割合ダメージを適用する。

    Returns:
        bool: ダメージが適用された場合True
    """
    if battle.query.is_contact(ctx):
        v = battle.modify_hp(ctx.attacker, r=-ratio, reason="ability")
        return bool(v)
    return False


def _trigger_emergency_switch(battle: Battle, mon: Pokemon):
    """緊急交代を発動する。"""
    player = battle.get_player(mon)
    if battle.get_available_switch_commands(player):
        battle.player_states[player].interrupt = Interrupt.EMERGENCY
        announce_ability_triggered(battle, None, None, mon=mon)


def _apply_type_absorb(battle: Battle,
                       ctx: EventContext,
                       value: bool,
                       *,
                       move_type: Type,
                       heal_ratio: float = 0,
                       stats: dict[Stat, int] | None = None) -> HandlerReturn:
    """特定のタイプの技を無効化し、副次効果（回復/能力上昇）を適用する。"""
    if (
        not ctx.move.target == "foe"
        or ctx.move.type != move_type
    ):
        return HandlerReturn(value=value)

    defender = ctx.defender

    announce_ability_triggered(battle, ctx, value, mon=defender)
    battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                         payload={"reason": defender.ability.base_name})

    if heal_ratio > 0:
        battle.modify_hp(defender, r=heal_ratio)
    if stats is not None:
        battle.modify_stats(defender, stats, source=ctx.attacker)

    return HandlerReturn(value=False, stop_event=True)


def _modify_by_move_condition(battle: Battle,
                              ctx: EventContext,
                              value: int,
                              *,
                              modifier: int,
                              move_type: Type | None = None,
                              move_label: MoveLabel | None = None) -> HandlerReturn:
    """技のタイプ/ラベル条件を満たすときのみ固定倍率補正を適用する。"""
    if (
        (move_type is not None and ctx.move.type == move_type)
        or (move_label is not None and ctx.move.has_label(move_label))
    ):
        value = apply_fixed_modifier(value, modifier)
    return HandlerReturn(value=value)


def activate_weather(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     *,
                     weather: Weather,
                     count: int,
                     source_spec: RoleSpec = "source:self") -> HandlerReturn:
    """天候を変更する"""

    source = ctx.resolve_role(battle, source_spec)
    if battle.weather_manager.apply(weather, count, source=source):
        announce_ability_triggered(battle, ctx, value, mon=source)
    return HandlerReturn(value=value)


def deactivate_strong_weather(battle: Battle,
                              ctx: EventContext,
                              value: Any,
                              *,
                              weather: Weather) -> HandlerReturn:
    """強天候を解除する
    相手の特性が同じ天候を発生させるものなら解除しない。
    """
    source = ctx.source
    foe = battle.foe(source)
    if (
        battle.weather.name == weather
        and foe.ability.name != source.ability.name
    ):
        battle.weather_manager.remove()
    return HandlerReturn(value=value)


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     *,
                     terrain: Terrain,
                     count: int,
                     source_spec: RoleSpec = "source:self") -> HandlerReturn:
    """地形を変更する"""
    source = ctx.resolve_role(battle, source_spec)
    if battle.terrain_manager.apply(terrain, count, source=source):
        announce_ability_triggered(battle, ctx, value, mon=source)
    return HandlerReturn(value=value)


def prevent_ailment(battle: Battle,
                    ctx: EventContext,
                    value: AilmentName,
                    *,
                    blocked_ailments: list[AilmentName] | None = None) -> HandlerReturn:
    """状態異常の付与を防ぐ
    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
            - target: 状態異常を付与されそうなポケモン
        value: 付与されそうな状態異常の名前
        blocked_ailments: 防げる状態異常のリスト（Noneならすべて防ぐ）
    """
    if blocked_ailments is None or value in blocked_ailments:
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
        battle.add_event_log(ctx.target, LogCode.AILMENT_PREVENTED,
                             payload={"ailment": value, "reason": ctx.target.ability.name})
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def prevent_volatile(battle: Battle,
                     ctx: EventContext,
                     value: VolatileName,
                     *,
                     blocked_volatiles: list[VolatileName] | None = None) -> HandlerReturn:
    """揮発状態の付与を防ぐ
    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_VOLATILE)
            - target: 揮発状態を付与されそうなポケモン
        value: 付与されそうな揮発状態の名前
        blocked_volatiles: 防げる揮発状態のリスト（Noneならすべて防ぐ）
    """
    if blocked_volatiles is None or value in blocked_volatiles:
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
        battle.add_event_log(ctx.target, LogCode.VOLATILE_PREVENTED,
                             payload={"volatile": value, "reason": ctx.target.ability.name})
        return HandlerReturn(value=None, stop_event=True)
    return HandlerReturn(value=value)


def ARシステム_apply_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ARシステム特性: 登場時にメモリに合わせてタイプを変更する。"""
    _apply_multitype(ctx.source, MEMORY_TO_TYPE)
    return HandlerReturn(value=value)


def ARシステム_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ARシステム特性: メモリの奪取・交換を防ぐ。"""
    return _block_item_change(ctx.target, list(MEMORY_TO_TYPE.keys()))


def アイスボディ_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アイスボディ特性: ゆき中にターン終了時に最大HPの1/16を回復する。"""
    mon = ctx.source
    if (
        battle.weather.name == "ゆき"
        and battle.modify_hp(mon, r=1/16)
    ):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def あついしぼう_reduce_fire_ice(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """あついしぼう特性: 炎/氷技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type in ["ほのお", "こおり"]:
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def あとだし_on_calc_back_tier(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """あとだし特性: 同一優先度の行動の中で最後に行動する（後攻ティア -1）。"""
    return HandlerReturn(value=-1)


def アナライズ_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """アナライズ特性: 行動が後になったターンの技威力を1.3倍にする。"""
    defender_player = battle.get_player(ctx.defender)
    # TODO : 行動順が確定したときにどこかに保存しておき、それを参照するようにする。現状は「相手がすでに技を出したか、交代しているか」で代用している。
    acted_before = ctx.defender.executed_move is not None or defender_player.has_switched
    if acted_before:
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def あまのじゃく_reverse_stat(battle: Battle, ctx: EventContext, value: dict[str, int]) -> HandlerReturn:
    """あまのじゃく特性: 能力変化量の符号を反転する。"""
    return HandlerReturn(value={stat: -delta for stat, delta in value.items()})


def あめうけざら_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あめうけざら特性: あめ/おおあめ中にターン終了時に最大HPの1/16を回復する。"""
    mon = ctx.source
    if not battle.weather.rainy:
        return HandlerReturn(value=value)

    result = battle.modify_hp(mon, r=1/16)
    if result:
        announce_ability_triggered(battle, ctx, value, mon=mon)

    return HandlerReturn(value=value)


def ありじごく_check_trapped(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
    result = not battle.query.is_floating(ctx.source)
    return HandlerReturn(value=result)


def いかく_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いかく特性: 登場時に相手のこうげきを1段階下げる。"""
    source = ctx.source
    target = battle.foe(source)
    announce_ability_triggered(battle, ctx, value, mon=source)
    battle.modify_stat(target, "A", -1, source=source, reason="いかく")
    return HandlerReturn(value=value)


def いしあたま_ignore_recoil(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """いしあたま特性: 反動ダメージを受けない。"""
    if ctx.hp_change_reason == "recoil":
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def いたずらごころ_modify_move_priority(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """いたずらごころ特性: 変化技の優先度を+1する。"""
    if ctx.move is not None and ctx.move.category == "変化":
        value += 1
    return HandlerReturn(value=value)


def いたずらごころ_blocked_by_dark(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """いたずらごころ特性: 優先度が上がった変化技はあくタイプ相手に無効化される。"""
    if (
        ctx.move.category == "変化"
        and ctx.move.target == "foe"
        and ctx.defender.has_type("あく")
    ):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload={"reason": "いたずらごころ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def いろめがね_boost_ineffective(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """いろめがね特性: いまひとつの技の最終ダメージ補正を2倍にする。"""
    if common.is_not_very_effective(battle, ctx):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def いわはこび_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """いわはこび特性: いわ技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_type="いわ",
    )


def エアロック_check_weather_enabled(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """エアロック特性: 天候効果を無効化する。"""
    return HandlerReturn(value=False, stop_event=True)


def おうごんのからだ_block_status_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おうごんのからだ特性: 他のポケモンからの変化技を無効化する。"""
    if (
        ctx.move.category == "変化"
        and ctx.move.target == "foe"
    ):
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload={"reason": "おうごんのからだ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おやこあい_modify_hit_count(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """おやこあい特性: 単発攻撃技を2ヒット化する。"""
    if ctx.move.is_attack and ctx.move.max_hits == 1:
        value = 2
    return HandlerReturn(value=value)


def おやこあい_reduce_second_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """おやこあい特性: 2ヒット目のダメージを減衰させる。"""
    print(vars(ctx))
    if ctx.hit_index == 2:
        value //= 4
    return HandlerReturn(value=value)


def かいりきバサミ_block_A_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """かいりきバサミ特性: 相手によるこうげきランク低下を無効化する。"""
    value = common.block_stat_drop_by_foe(value, ctx, "A")
    return HandlerReturn(value=value)


def かがくへんかガス_gas_activate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    foe = battle.foe(mon)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    if not foe.ability.has_flag("gas_proof"):
        battle.add_ability_disabled_reason(foe, "かがくへんかガス")
    return HandlerReturn(value=value)


def かがくへんかガス_foe_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かがくへんかガス特性: 特性を無効化する。"""
    mon = ctx.source
    if not mon.ability.has_flag("gas_proof"):
        battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    return HandlerReturn(value=value)


def かがくへんかガス_gas_deactivate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かがくへんかガス特性: 特性無効化を解除する。"""
    mon = battle.foe(ctx.source)
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    return HandlerReturn(value=value)


def かげふみ_check_trapped(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def かそく_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かそく特性: 行動済みならターン終了時に素早さを1段階上げる。"""
    mon = ctx.source
    print(f"{battle.turn=}, {mon.executed_move=}")
    if (
        mon.executed_move is not None
        and battle.modify_stat(mon, "S", +1, source=mon)
    ):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def かたいツメ_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """かたいツメ特性: 直接攻撃の威力を1.3倍にする。"""
    if ctx.move is not None and battle.query.is_contact(ctx):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def かたやぶり_disable_foe_ability(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    mon = ctx.defender
    if mon.ability.has_flag("mold_breaker_ignorable"):
        battle.add_ability_disabled_reason(mon, "かたやぶり")
    return HandlerReturn(value=value)


def かたやぶり_restore_foe_ability(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    battle.remove_ability_disabled_reason(ctx.defender, "かたやぶり")
    return HandlerReturn(value=value)


def かちき_on_stat_down(battle: Battle, ctx: EventContext, value: dict[Stat, int]) -> HandlerReturn:
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
    if (
        has_negative
        and ctx.source != ctx.target
        and battle.modify_stat(ctx.target, "C", +2, source=ctx.source)
    ):
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
    return HandlerReturn(value=value)


def カブトアーマー_block_crit(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """カブトアーマー特性: 防御側の急所ランクを無効化する。"""
    return HandlerReturn(value=0, stop_event=True)


def かるわざ_update_state(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かるわざ特性: 入場時に発動可否の初期状態を記録する。"""
    mon = ctx.source
    # "idle": 入場時にアイテムあり（消失で発動可能）
    # "inactive": 入場時にアイテムなし（この在場中は発動しない）
    mon.ability.state = "idle" if mon.has_item() else "inactive"
    return HandlerReturn(value=value)


def かるわざ_deactivate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かるわざ特性: 交代で状態を初期化する。"""
    ctx.source.ability.state = ""
    return HandlerReturn(value=value)


def かるわざ_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """かるわざ特性: アイテム消失中は素早さを2倍にする。"""
    mon = ctx.source

    # 入場時にアイテムがなかった個体は、この在場中は発動しない。
    if mon.ability.state == "inactive":
        return HandlerReturn(value=value)

    # 発動中にアイテムを再取得したら解除（再消費で再発動できる状態へ戻す）。
    if mon.ability.state == "active" and mon.has_item():
        mon.ability.state = "idle"
        return HandlerReturn(value=value)

    # アイテムを失ったら発動状態へ遷移。
    if mon.ability.state == "idle" and not mon.has_item():
        mon.ability.state = "active"

    if mon.ability.state == "active" and not mon.has_item():
        value *= 2
    return HandlerReturn(value=value)


def がんじょう_block_ohko(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """がんじょう特性: 一撃必殺技を無効化する。"""
    if ctx.move.has_label("ohko"):
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload={"reason": "がんじょう"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def がんじょう_survive_lethal(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """がんじょう特性: HP満タン時の致死ダメージをHP1残しに補正する。(ON_BEFORE_DAMAGE_APPLY / subject_spec="target:self")"""
    defender = ctx.defender
    if (
        defender.hp == defender.max_hp
        and value >= defender.hp
    ):
        announce_ability_triggered(battle, ctx, value, mon=defender)
        value = defender.hp - 1
    return HandlerReturn(value=value)


# ===== ちからずく =====

def がんじょうあご_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """がんじょうあご特性: かみつき技の威力を1.5倍にする。"""
    if ctx.move is not None and ctx.move.has_label("bite"):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def かんそうはだ_absorb_water(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """かんそうはだ特性: みず技を無効化し、HPが減っていれば最大HPの1/4を回復する。"""
    return _apply_type_absorb(battle, ctx, value, move_type="みず", heal_ratio=1/4)


def かんそうはだ_modify_fire_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """かんそうはだ特性: ほのお技を受けたときの威力が5/4倍になる。"""
    if ctx.move.type == "ほのお":
        value = apply_fixed_modifier(value, 5120)  # 5/4倍 = 5120/4096
    return HandlerReturn(value=value)


def かんそうはだ_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かんそうはだ特性: 天候に応じてターン終了時にHP変化を受ける。"""
    mon = ctx.source

    # あめ中は最大HPの1/8回復
    if (
        battle.weather.rainy
        and battle.modify_hp(mon, r=1/8)
    ):
        announce_ability_triggered(battle, ctx, value, mon=mon)

    # にほんばれ中は最大HPの1/8ダメージ
    if (
        battle.weather.sunny
        and battle.modify_hp(mon, r=-1/8)
    ):
        announce_ability_triggered(battle, ctx, value, mon=mon)

    return HandlerReturn(value=value)


def ききかいひ_on_hp_change(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ききかいひ特性: HPが半分以下になったとき交代する。"""
    mon = ctx.target

    # 交代できない条件
    if (
        mon.fainted
        or ctx.hp_change_reason in {"self_attack", "pain_split"}
    ):
        return HandlerReturn(value=value)

    hp_after = mon.hp
    hp_before = hp_after + value
    if _crossed_half_hp(hp_before, hp_after, mon.max_hp):
        _trigger_emergency_switch(battle, mon)

    return HandlerReturn(value=value)


def ぎゃくじょう_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぎゃくじょう特性: HP が半分以下になった時、特攻が1段階上昇する。"""
    mon = ctx.defender
    hp_after = mon.hp
    hp_before = hp_after + value

    if (
        _crossed_half_hp(hp_before, hp_after, mon.max_hp)
        and battle.modify_stat(mon, "C", +1, source=ctx.attacker, reason="ぎゃくじょう")
    ):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def きゅうばん_block_blow(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """きゅうばん特性: 強制交代技の効果を防ぐ。"""
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=False, stop_event=True)


def きょううん_modify_critical_rank(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """きょううん特性: 攻撃側の急所ランクを+1する。"""
    if ctx.move is not None:
        value += 1
    return HandlerReturn(value=value)


def きよめのしお_reduce_ghost(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """きよめのしお特性: ゴースト技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type == "ゴースト":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def きれあじ_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """きれあじ特性: きる技の威力を1.5倍にする。"""
    if ctx.move.has_label("slash"):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def きんちょうかん_check_nervous(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """きんちょうかん特性: 相手のきのみ使用を禁止する。"""
    return HandlerReturn(value=True)


def くさのけがわ_boost_B(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """くさのけがわ特性: グラスフィールド中の物理技への防御補正を1.5倍にする。"""
    if (
        battle.terrain.name == "グラスフィールド"
        and common.deals_physical_damage(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def クリアボディ_block_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """クリアボディ特性: 相手による能力ランク低下を無効化する。

    自分の技や反動による能力低下は防げない。
    """
    value = common.block_stat_drop_by_foe(value, ctx)
    return HandlerReturn(value=value)


def こおりのりんぷん_reduce_special_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """こおりのりんぷん特性: 特殊技で受けるダメージを0.5倍にする。"""
    if battle.resolve_move_category(ctx.attacker, ctx.move) == "特殊":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def ごりむちゅう_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ごりむちゅう特性: 物理技の攻撃補正を1.5倍にする。"""
    if battle.resolve_move_category(ctx.attacker, ctx.move) == "物理":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def こんがりボディ_absorb_fire(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    return _apply_type_absorb(battle, ctx, value, move_type="ほのお", stats={"B": 2})


def こんじょう_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """こんじょう特性: 状態異常時に物理技の攻撃補正を1.5倍にする。"""
    if (
        ctx.attacker.ailment.is_active
        and battle.resolve_move_category(ctx.attacker, ctx.move) == "物理"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def こんじょう_ignore_burn_penalty(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """こんじょう特性: 状態異常時はやけどの物理半減を無効化する。"""
    if (
        ctx.attacker.ailment.is_active
        and battle.resolve_move_category(ctx.attacker, ctx.move) == "物理"
    ):
        value = 4096
    return HandlerReturn(value=value)


def さいせいりょく_on_switch_out(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さいせいりょく特性: 交代で引っ込んだとき最大HPの1/3を回復する（かいふくふうじ無効）。"""
    mon = ctx.source
    if battle.modify_hp(mon, r=1/3, reason="bench_heal"):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def さめはだ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さめはだ特性: 接触技を受けた相手に最大HPの1/8ダメージを与える。"""
    _apply_contact_counter_chip(battle, ctx, ratio=1/8)
    return HandlerReturn(value=value)


def サンパワー_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """サンパワー特性: にほんばれ/おおひでり中に特殊技の特攻補正を1.5倍にする。"""
    if (
        battle.weather.sunny
        and battle.resolve_move_category(ctx.attacker, ctx.move) == "特殊"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def サンパワー_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """サンパワー特性: にほんばれ/おおひでり中にターン終了時に最大HPの1/8ダメージを受ける。"""
    mon = ctx.source
    if not battle.weather.sunny:
        return HandlerReturn(value=value)
    result = battle.modify_hp(mon, r=-1/8)
    if result:
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def じしんかじょう_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じしんかじょう特性: 攻撃技で相手を倒すと攻撃が1段階上がる。"""
    if not ctx.defender.fainted:
        return HandlerReturn(value=value)

    changed = battle.modify_stat(ctx.attacker, "A", +1, source=ctx.attacker)
    if not changed:
        return HandlerReturn(value=value)

    announce_ability_triggered(battle, ctx, value, mon=ctx.attacker)
    return HandlerReturn(value=value)


def しぜんかいふく_on_switch_out(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しぜんかいふく特性: 交代で引っ込んだとき状態異常を回復する。"""
    mon = ctx.source
    result = common.cure_self_ailment(battle, ctx, value)
    if result.value:
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def しめりけ_block_explosion_self(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しめりけ特性（攻撃側）: 自分が爆発技を使おうとしたとき失敗させる。"""
    if ctx.move.has_label("explosion"):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "しめりけ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def しめりけ_block_explosion_foe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しめりけ特性（防御側）: 相手が爆発技を使おうとしたとき失敗させる。"""
    if ctx.move.has_label("explosion"):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "しめりけ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def しゅうかく_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しゅうかく特性: ターン終了時に消費したきのみを復活させる。"""
    mon = ctx.source
    item_name = mon.last_lost_item_name

    # きのみでない、またはすでに別のアイテムを持っている場合は発動しない
    if (
        not common.is_berry_item(item_name)
        or mon.has_item()
    ):
        return HandlerReturn(value=value)

    # 発動確率の計算
    chance = 1.0 if battle.weather.sunny else 0.5

    if battle.random.random() >= chance:
        return HandlerReturn(value=value)

    battle.gain_item(mon, item_name)

    announce_ability_triggered(battle, ctx, value, mon=mon)

    # 復活直後に使用条件を満たすきのみは、その場で使用される。
    return HandlerReturn(value=value)


def じりょく_check_trapped(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じりょく特性: はがねタイプのポケモンの交代を防ぐ。"""
    return HandlerReturn(value=ctx.source.has_type("はがね"))


def すいすい_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すいすい特性: あめ中に素早さが2倍になる。"""
    if battle.weather.rainy:
        value *= 2
    return HandlerReturn(value=value)


def すいほう_modify_boost_water(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すいほう特性: みず技の威力を2倍にする。"""
    if ctx.move.type == "みず":
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def すいほう_reduce_fire(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すいほう特性: ほのお技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type == "ほのお":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def スキルリンク_modify_hit_count(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """スキルリンク特性: 連続技のヒット数を最大にする。"""
    if ctx.move.max_hits > 1:
        value = ctx.move.max_hits
    return HandlerReturn(value=value)


def スナイパー_boost_critical(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """スナイパー特性: 急所時の最終ダメージ補正を1.5倍にする。"""
    if getattr(ctx, "critical", False):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def すなかき_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すなかき特性: すなあらし中に素早さが2倍になる。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 元の素早さ値

    Returns:
        HandlerReturn: (True, 補正後の素早さ)
            - すなあらし中は2倍、それ以外は元の値
    """
    if battle.weather.name == "すなあらし":
        value *= 2
    return HandlerReturn(value=value)


def すなかき_ignore_sandstorm_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すなかき特性: すなあらしのダメージを受けない。"""
    return common.ignore_damage_by_reason(battle, ctx, value, reason="sandstorm")


def すながくれ_ignore_sandstorm_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すながくれ特性: すなあらしのダメージを受けない。"""
    return common.ignore_damage_by_reason(battle, ctx, value, reason="sandstorm")


def すなのちから_ignore_sandstorm_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すなのちから特性: すなあらしのダメージを受けない。"""
    return common.ignore_damage_by_reason(battle, ctx, value, reason="sandstorm")


def すなのちから_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すなのちから特性: すなあらし中の岩/地面/鋼技の威力を1.3倍にする。"""
    if (
        battle.weather.name == "すなあらし"
        and ctx.move.type in ["いわ", "じめん", "はがね"]
    ):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def すりぬけ_bypass_substitute(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """すりぬけ特性: みがわりを無視して攻撃する。"""
    return HandlerReturn(value=False, stop_event=True)


def すりぬけ_bypass_screen(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """すりぬけ特性: 相手の壁を貫通して攻撃する。"""
    return HandlerReturn(value=True)


def するどいめ_block_ACC_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """するどいめ特性: 相手による命中率ランク低下を無効化する。"""
    value = common.block_stat_drop_by_foe(value, ctx, "ACC")
    return HandlerReturn(value=value)


def スロースタート_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スロースタート特性: 登場ターンを記録する。"""
    ctx.source.ability.count = battle.turn
    return HandlerReturn(value=value)


def スロースタート_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """スロースタート特性: 登場から5ターンの物理攻撃補正を0.5倍にする。"""
    if (
        battle.turn - ctx.attacker.ability.count < 5
        and battle.resolve_move_category(ctx.attacker, ctx.move) == "物理"
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def せいしんりょく_block_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """せいしんりょく特性: いかくによる攻撃ランク低下を無効化する。"""
    if ctx.stat_change_reason == "いかく":
        value = {}
    return HandlerReturn(value=value)


def せいでんき_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """せいでんき特性: 直接攻撃を受けた相手を30%でまひにする。"""
    _apply_contact_counter_ailment(battle, ctx, ailment="まひ", chance=0.3)
    return HandlerReturn(value=value)


def そうしょく_absorb_grass(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """そうしょく特性: くさ技を無効化し攻撃を1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="くさ", stats={"A": 1})


def たいねつ_reduce_fire(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """たいねつ特性: 炎技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type == "ほのお":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def ダウンロード_raise_stat(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ダウンロード特性: 入場時に相手の防御と特防を比較し、低い方に対応する攻撃能力を上げる。"""
    mon = ctx.source
    foe = battle.foe(mon)

    foe_def = foe.ranked_stats["B"]
    foe_spd = foe.ranked_stats["D"]
    boost_stat = "A" if foe_def < foe_spd else "C"

    changed = battle.modify_stat(mon, boost_stat, +1, source=mon)
    if changed:
        announce_ability_triggered(battle, ctx, value, mon=mon)

    return HandlerReturn(value=value)


def だっぴ_cure_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だっぴ特性: ターン終了時に30%で状態異常を回復する。"""
    mon = ctx.source
    if not mon.ailment.is_active:
        return HandlerReturn(value=value)

    result = common.cure_self_ailment(battle, ctx, value, chance=0.3)
    if result.value:
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def たんじゅん_double_stat(battle: Battle, ctx: EventContext, value: dict[str, int]) -> HandlerReturn:
    """たんじゅん特性: 能力変化量を2倍にする。"""
    return HandlerReturn(value={stat: delta * 2 for stat, delta in value.items()})


def ちからずく_boost(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ちからずく特性: 追加効果ありの技の威力を 1.3 倍にする。(ON_CALC_POWER_MODIFIER / subject_spec="attacker:self")"""
    if ctx.move.has_label("secondary_effect"):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ちからずく_disable_secondary_effect(battle: Battle, ctx: EventContext, value: float) -> HandlerReturn:
    """ちからずく特性: 追加効果対象技の追加効果確率を 0 にする。"""
    if ctx.move.has_label("secondary_effect"):
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def ちからもち_boost_physical(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ちからもち・ヨガパワー特性: 物理技時の攻撃補正を2.0倍にする。"""
    if (
        battle.resolve_move_category(ctx.attacker, ctx.move) == "物理"
    ):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ちくでん_absorb_electric(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ちくでん特性: でんき技を無効化し最大HPの1/4回復する。"""
    return _apply_type_absorb(battle, ctx, value, move_type="でんき", heal_ratio=1/4)


def ちょすい_absorb_water(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ちょすい特性: みず技を無効化し最大HPの1/4回復する。"""
    return _apply_type_absorb(battle, ctx, value, move_type="みず", heal_ratio=1/4)


def てきおうりょく_modify_stab(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """てきおうりょく特性: タイプ一致補正を強化する。"""
    attacker = ctx.attacker

    # ステラテラスタル時はてきおうりょくがSTAB補正に影響しない。
    if attacker.terastallized and attacker.tera_type == "ステラ":
        return HandlerReturn(value=value)

    if value == 6144:
        return HandlerReturn(value=8192)  # 1.5倍 -> 2倍
    if value == 8192:
        return HandlerReturn(value=9216)  # 2倍 -> 2.25倍
    return HandlerReturn(value=value)


def テクニシャン_boost_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """テクニシャン特性: 元威力60以下の技威力補正を1.5倍にする。"""
    if ctx.move.data.power is not None and ctx.move.data.power <= 60:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def てつのこぶし_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """てつのこぶし特性: パンチ技の威力を1.2倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=4915,
        move_label="punch",
    )


def テラスシェル_overwrite_type_modifier(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """テラスシェル特性: HP満タン時、等倍以上のタイプ相性を半減する。"""
    if ctx.defender.hp == ctx.defender.max_hp:
        value = min(value, 2048)
    return HandlerReturn(value=value)


def でんきエンジン_absorb_electric(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """でんきエンジン特性: でんき技を無効化し素早さを1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="でんき", stats={"S": 1})


def てんねん_ignore_rank(battle: Battle, ctx: EventContext, value: float) -> HandlerReturn:
    """てんねん特性: ランク補正を無視する。"""
    return HandlerReturn(value=1)


def てんのめぐみ_boost_secondary_chance(battle: Battle, ctx: EventContext, value: float) -> HandlerReturn:
    """てんのめぐみ特性: 追加効果対象技の追加効果確率を2倍にする。"""
    return HandlerReturn(value=min(1.0, value * 2))


def どくしゅ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくしゅ特性: 直接攻撃でダメージを与えた相手を30%でどくにする。"""
    if (
        not battle.query.is_contact(ctx)
        or battle.random.random() >= battle.resolve_secondary_chance(ctx, 0.3)
    ):
        return HandlerReturn(value=value)

    battle.ailment_manager.apply(
        ctx.defender,
        "どく",
        source=ctx.attacker,
        ctx=ctx,
    )
    return HandlerReturn(value=value)


def どくのトゲ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくのトゲ特性: 直接攻撃を受けた相手を30%でどくにする。"""
    _apply_contact_counter_ailment(battle, ctx, ailment="どく", chance=0.3)
    return HandlerReturn(value=value)


def しんりょくもうかげきりゅうむしのしらせ_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
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


def どくぼうそう_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """どくぼうそう特性: どく状態時に特殊技の威力を1.5倍にする。"""
    if (
        (ctx.attacker.has_ailment("どく", "もうどく"))
        and battle.resolve_move_category(ctx.attacker, ctx.move) == "特殊"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def どしょく_absorb_ground(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """どしょく特性: じめん技を無効化し最大HPの1/4回復する。"""
    return _apply_type_absorb(battle, ctx, value, move_type="じめん", heal_ratio=1/4)


def トランジスタ_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """トランジスタ特性: でんき技の攻撃補正を1.3倍にする。"""
    if ctx.move is not None and ctx.move.type == "でんき":
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def トレース_copy_ability(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """トレース特性: 入場時に相手のコピー可能な特性へ変更する。"""
    mon = ctx.source
    foe = battle.foe(mon)

    copied_ability = foe.ability.base_name
    if (
        not copied_ability
        or foe.ability.has_flag("uncopyable")
    ):
        return HandlerReturn(value=value)

    battle.change_ability(mon, copied_ability)
    return HandlerReturn(value=value)


def ねつこうかん_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねつこうかん特性: ほのおタイプの攻撃技でダメージを受けたとき、こうげきが1段階上がる。"""
    if ctx.move.type != "ほのお":
        return HandlerReturn(value=value)

    changed = battle.modify_stat(ctx.defender, "A", +1, source=ctx.attacker)
    if not changed:
        return HandlerReturn(value=value)

    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=value)


def ねつぼうそう_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ねつぼうそう特性: やけど状態時の物理技の威力を1.5倍にする。"""
    if (
        ctx.attacker.has_ailment("やけど")
        and battle.resolve_move_category(ctx.attacker, ctx.move) == "物理"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ねんちゃく_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ねんちゃく特性: 相手から受けるアイテム交換・奪取・除去を防ぐ。"""
    if ctx.source != ctx.target:
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ノーガード_guarantee_hit(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def ノーマルスキン_modify_move_type(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    """ノーマルスキン特性: 全ての技をノーマルタイプに変換する（ステラタイプ除く）。"""
    if ctx.move is not None and value not in ("ノーマル", "ステラ"):
        value = "ノーマル"
    return HandlerReturn(value=value)


def ノーマルスキン_boost_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ノーマルスキン特性: 変換した技の威力を4915/4096倍にする。"""
    if ctx.move is not None and ctx.move.data.type not in ("ノーマル", "ステラ"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def ハードロック_reduce_effective(battle: Battle,
                            ctx: EventContext,
                            value: int) -> HandlerReturn:
    """防御側特性: 効果抜群の技ダメージを0.75倍にする。"""
    if common.is_super_effective(battle, ctx):
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def はがねつかい_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はがねつかい特性: はがね技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_type="はがね",
    )


def はがねのせいしん_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はがねのせいしん特性: はがね技の威力を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_type="はがね",
    )


def ばけのかわ_block_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ばけのかわを消費して、このヒットの攻撃ダメージを0にする。"""
    battle.add_ability_disabled_reason(ctx.defender, "consumed")
    battle.modify_hp(ctx.defender, r=-1/8)
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=0)


# ===== がんじょう =====

def はとむね_block_B_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """はとむね特性: 相手によるぼうぎょランク低下を無効化する。"""
    value = common.block_stat_drop_by_foe(value, ctx, "B")
    return HandlerReturn(value=value)


def バトルスイッチ_change_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 行動前に必要なフォルムへ切り替える。"""
    mon = ctx.source
    next_name = ""
    if mon.name == AEGISLASH_SHIELD and ctx.move.is_attack:
        next_name = AEGISLASH_BLADE
    elif mon.name == AEGISLASH_BLADE and ctx.move.name == "キングシールド":
        next_name = AEGISLASH_SHIELD

    if next_name:
        mon.set_form(next_name)
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def バトルスイッチ_revert_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 交代時にシールドフォルムへ戻す。"""
    mon = ctx.source
    if mon.name == AEGISLASH_BLADE:
        mon.set_form(AEGISLASH_SHIELD)
    return HandlerReturn(value=value)


def ハドロンエンジン_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ハドロンエンジン特性: エレキフィールド中の攻撃補正を1.33倍にする。"""
    if battle.terrain.name == "エレキフィールド":
        value = apply_fixed_modifier(value, 5461)
    return HandlerReturn(value=value)


def はやあし_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はやあし特性: 状態異常時に素早さが1.5倍になる。まひの素早さ低下も無効化する。"""
    mon = ctx.source
    if not mon.ailment.is_active:
        return HandlerReturn(value=value)

    if mon.has_ailment("まひ"):
        # まひ_speed による 1/2 ペナルティを打ち消して 1.5 倍（合計 *3）
        value = value * 3
    else:
        value = value * 1.5
    return HandlerReturn(value=value)


def はらぺこスイッチ_on_switch_out(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """はらぺこスイッチ特性: 交代時のフォルム状態を更新する。"""
    # テラスタル状態でなければ
    mon = ctx.source
    if not mon.terastallized:
        mon.ability.is_hangry = False
    return HandlerReturn(value=value)


def はらぺこスイッチ_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """はらぺこスイッチ特性: ターン終了時にフォルムを切り替える。"""
    mon = ctx.source
    if mon.terastallized:
        return HandlerReturn(value=value)

    mon.ability.is_hangry = not mon.ability.is_hangry
    return HandlerReturn(value=value)


def はらぺこスイッチ_modify_move_type(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    """はらぺこスイッチ特性: オーラぐるまのタイプをフォルムで変える。"""
    if ctx.move is not None and ctx.move.name == "オーラぐるま":
        value = "あく" if ctx.source.ability.is_hangry else "でんき"
    return HandlerReturn(value=value)


def はりきり_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はりきり特性: 物理技の攻撃補正を1.5倍にする。"""
    if battle.resolve_move_category(ctx.attacker, ctx.move) == "物理":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def はりきり_modify_accuracy(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はりきり特性: 物理技（一撃必殺・必中技除外）の命中率を0.8倍にする。"""
    if (
        battle.resolve_move_category(ctx.attacker, ctx.move) == "物理"
        and not ctx.move.has_label("ohko")  # 一撃必殺技は命中率ペナルティなし
        and ctx.move.accuracy is not None  # 必中技は命中率ペナルティなし
    ):
        value = apply_fixed_modifier(value, 3277)
    return HandlerReturn(value=value)


def はりこみ_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はりこみ特性: 交代直後の相手に対する攻撃補正を2倍にする。"""
    if ctx.defender is not None and battle.get_player(ctx.defender).has_switched:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def パンクロック_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """パンクロック特性: 音技の威力を1.3倍にする。"""
    if ctx.move is not None and ctx.move.has_label("sound"):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def パンクロック_reduce_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """パンクロック特性: 音技で受けるダメージを0.5倍にする。"""
    if ctx.move.has_label("sound"):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def ひとでなし_modify_critical_rank(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ひとでなし特性: どく/もうどく状態の相手への攻撃を必ず急所にする。"""
    if ctx.defender.has_ailment("どく", "もうどく"):
        value = 10
    return HandlerReturn(value=value)


def ひひいろのこどう_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ひひいろのこどう特性: はれ中の攻撃補正を1.33倍にする。"""
    if battle.weather.sunny:
        value = apply_fixed_modifier(value, 5461)
    return HandlerReturn(value=value)


def ひらいしん_absorb_electric(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ひらいしん特性: でんき技を無効化し特攻を1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="でんき", stats={"C": 1})


def ファーコート_boost_B(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ファーコート特性: 物理技に対する防御補正を2倍にする。"""
    if common.deals_physical_damage(battle, ctx):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ぶきよう_disable_item(battle: Battle, ctx: EventContext, value: set[ItemDisabledReason]) -> HandlerReturn:
    battle.add_item_disabled_reason(ctx.source, "ぶきよう")
    return HandlerReturn(value=value)


def ぶきよう_enable_item(battle: Battle, ctx: EventContext, value: set[ItemDisabledReason]) -> HandlerReturn:
    battle.remove_item_disabled_reason(ctx.source, "ぶきよう")
    return HandlerReturn(value=value)


def ふくがん_boost_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふくがん特性: 使用技の命中率を1.3倍にする（一撃必殺技を除く）。"""
    if not ctx.move.has_label("ohko"):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ふしぎなうろこ_boost_B(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ふしぎなうろこ特性: 状態異常時に物理技への防御補正を1.5倍にする。"""
    if (
        ctx.defender.ailment.is_active
        and common.deals_physical_damage(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ふゆう_float(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ふゆう特性: 常に浮遊状態として扱う。"""
    return HandlerReturn(value=True)


def ブレインフォース_boost_effective(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ブレインフォース特性: 効果抜群のときダメージを1.25倍"""
    if common.is_super_effective(battle, ctx):
        value = apply_fixed_modifier(value, 5120)
    return HandlerReturn(value=value)


def へんげんじざい_change_type(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """へんげんじざい・リベロ: 技実行前に技タイプへ自身のタイプを変更する。"""
    move_type = ctx.move.type

    if (
        not ctx.attacker.ability.activated_since_switch_in
        and not ctx.attacker.terastallized
        and [move_type] != ctx.attacker.types
    ):
        ctx.attacker.ability_override_type = move_type
        ctx.attacker.ability.activated_since_switch_in = True
        announce_ability_triggered(battle, ctx, value, mon=ctx.attacker)
    return HandlerReturn(value=value)


def ポイズンヒール_modify_poison_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ポイズンヒール特性: どく/もうどく由来のHP変化を最大HPの1/8回復に置き換える。"""
    if value < 0:
        value = ctx.target.max_hp // 8
    return HandlerReturn(value=value)


def ぼうおん_block_sound(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ぼうおん特性: 音技を無効化する。"""
    if ctx.move.has_label("sound"):
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload={"reason": "ぼうおん"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ぼうじん_block_powder(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ぼうじん特性: 粉・胞子系の技を無効化する。"""
    if ctx.move.has_label("powder"):
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload={"reason": "ぼうじん"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ぼうじん_block_sandstorm_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ぼうじん特性: すなあらしのダメージを受けない。"""
    return common.ignore_damage_by_reason(battle, ctx, value, reason="sandstorm")


def ぼうだん_block_bullet(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ぼうだん特性: 弾の技を無効化する。"""
    if ctx.move.has_label("bullet"):
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload={"reason": "ぼうだん"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ほのおのからだ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ほのおのからだ特性: 直接攻撃を受けた相手を30%でやけどにする。"""
    _apply_contact_counter_ailment(battle, ctx, ailment="やけど", chance=0.3)
    return HandlerReturn(value=value)


def マイティチェンジ_change_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マイティチェンジ特性: ナイーブフォルムで引っ込むとマイティフォルムへ変化する。"""
    mon = ctx.source
    if mon.name == PALAFIN_ZERO and mon.alive:
        mon.set_form(PALAFIN_HERO)
    return HandlerReturn(value=value)


def マジシャン_steal_item(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マジシャン特性: 攻撃成功後に相手のアイテムを奪う。"""
    battle.take_item(ctx.defender, move=ctx.move)
    return HandlerReturn(value=value)


def マジックガード_ignore_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """マジックガード特性: 間接ダメージを無効化する。"""
    # 直接ダメージ・自己由来の特定HP変動は無効化しない。
    if ctx.hp_change_reason not in {"move_damage", "pain_split", "self_attack", "self_cost"}:
        value = 0
    return HandlerReturn(value=value)


def マジックミラー_reflect(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """マジックミラー特性: 反射対象の変化技を跳ね返す。"""
    value = (
        ctx.move.category == "変化"
        and ctx.move.target == "foe"
    )
    if value:
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=value)


def マルチスケイル_reduce_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """防御側特性: HP満タン時の被ダメージを0.5倍にする。"""
    if ctx.defender.hp == ctx.defender.max_hp:
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def マルチタイプ_apply_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マルチタイプ特性: 登場時にプレートに合わせてタイプを変更する。"""
    _apply_multitype(ctx.source, PLATE_TO_TYPE)
    return HandlerReturn(value=value)


def マルチタイプ_block_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """マルチタイプ特性: プレートの奪取・交換を防ぐ。"""
    return _block_item_change(ctx.target, list(PLATE_TO_TYPE.keys()))


def ミラーアーマー_reflect_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """ミラーアーマー特性: 相手由来の能力ランク低下を反射する。"""
    can_reflect = (
        ctx.is_foe_target()
        and ctx.stat_change_reason != "ミラーアーマー"
    )
    if can_reflect:
        drops = {stat: v for stat, v in value.items() if v < 0}
        if drops:
            # 低下を source（相手）側へ反射（source を ctx.target にすることで「相手から下げられた」扱いになりまけんき等が正常発動）
            battle.modify_stats(ctx.source, drops, source=ctx.target, reason="ミラーアーマー")
            # 自分側の低下分を除去（上昇分は残す）
            value = {stat: v for stat, v in value.items() if v > 0}
    return HandlerReturn(value=value)


def ムラっけ_boost_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ムラっけ特性: ターン終了時に1能力+2、別の1能力-1する。"""
    mon = ctx.source
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
        announce_ability_triggered(battle, ctx, value, mon=mon)

    return HandlerReturn(value=value)


def メガランチャー_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """メガランチャー特性: はどう技の威力を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_label="pulse",
    )


def もふもふ_modify_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """もふもふ特性: 接触技被ダメ0.5倍・炎技被ダメ2倍を適用する。"""
    if battle.query.is_contact(ctx):
        value = apply_fixed_modifier(value, 2048)
    if ctx.move.type == "ほのお":
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def もらいび_block_fire(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技を無効化し、炎技強化状態を有効化する。"""
    if (
        not ctx.move.target == "foe"
        or ctx.move.type != "ほのお"
    ):
        return HandlerReturn(value=value)

    ctx.defender.ability.state = "charged"
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                         payload={"reason": "もらいび"})
    return HandlerReturn(value=False, stop_event=True)


def もらいび_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """もらいび特性: 登場時に炎技強化状態を初期化する。"""
    ctx.source.ability.state = "idle"
    return HandlerReturn(value=value)


def もらいび_charge_fire(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技使用時に強化適用予約。"""
    if (
        ctx.move.type == "ほのお"
        and ctx.source.ability.state == "charged"
    ):
        ctx.source.ability.state = "active"
    return HandlerReturn(value=value)


def もらいび_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """もらいび特性: 吸収後の最初のほのお技のみ威力を1.5倍にする。"""
    if (
        ctx.move.type == "ほのお"
        and ctx.attacker.ability.state == "active"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def もらいび_on_move_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """もらいび特性: 行動終了時に強化を消費済みにする。"""
    state = ctx.source.ability.state
    if state == "active":
        ctx.source.ability.state = "idle"
    return HandlerReturn(value=value)


def ゆきかき_boost_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ゆきかき特性: ゆき中に素早さが2倍になる。"""
    if battle.weather.name == "ゆき":
        value *= 2
    return HandlerReturn(value=value)


def ゆきがくれ_reduce_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ゆきがくれ特性: ゆき中に受ける技の命中率を3277/4096倍にする（必中技は除く）。"""
    if battle.weather.name == "ゆき":
        value = apply_fixed_modifier(value, 3277)
    return HandlerReturn(value=value)


def ようりょくそ_boost_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ようりょくそ特性: はれ中に素早さが2倍になる。"""
    if battle.weather.sunny:
        value *= 2
    return HandlerReturn(value=value)


def よびみず_absorb_water(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """よびみず特性: みず技を無効化し特攻を1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="みず", stats={"C": 1})


def よわき_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """よわき特性: HP半分以下で攻撃補正を0.5倍にする。"""
    if ctx.attacker.hp * 2 <= ctx.attacker.max_hp:
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def リーフガード_prevent_ailment(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    """リーフガード特性: にほんばれ/おおひでり中に状態異常付与を防ぐ。"""
    if battle.weather.sunny:
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def りゅうのあぎと_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """りゅうのあぎと特性: ドラゴン技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(
        battle,
        ctx,
        value,
        modifier=6144,
        move_type="ドラゴン",
    )


def りんぷん_block_secondary_chance(battle: Battle, ctx: EventContext, value: float) -> HandlerReturn:
    """りんぷん特性: 相手の攻撃技の追加効果を無効化する。"""
    return HandlerReturn(value=0, stop_event=True)


# ===== マルチタイプ / ARシステム 共通 =====


def わざわいのうつわ_reduce_C(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """わざわいのうつわ特性: 自分以外の特攻補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def _apply_multitype(mon: Pokemon, item_table: dict[str, Type]) -> None:
    """道具に応じてポケモンのタイプを変更する共通ロジック。"""
    item_name = mon.item.name if mon.has_item() else ""
    mon.ability_override_type = item_table.get(item_name)


def _block_item_change(mon: Pokemon, unchangable_items: list[str]) -> HandlerReturn:
    """道具の奪取・交換を防ぐ共通ロジック。"""
    item_name = mon.item.name if mon.has_item() else ""
    if item_name in unchangable_items:
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def わざわいのおふだ_reduce_A(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """わざわいのおふだ特性: 自分以外の攻撃補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def わざわいのたま_reduce_D(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """わざわいのたま特性: 自分以外の特防補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def わざわいのつるぎ_reduce_B(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """わざわいのつるぎ特性: 自分以外の防御補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def わるいてぐせ_steal_item(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """わるいてぐせ特性: 直接攻撃を受けた後に相手のアイテムを奪う。"""
    if (
        battle.query.is_contact(ctx)
        and not ctx.defender.fainted
    ):
        battle.take_item(ctx.attacker, move=ctx.move)
    return HandlerReturn(value=value)

# 天候展開系


def ひでり_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_weather(battle, ctx, value, weather="はれ", count=5)


def あめふらし_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_weather(battle, ctx, value, weather="あめ", count=5)


def すなおこし_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_weather(battle, ctx, value, weather="すなあらし", count=5)


def ゆきふらし_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_weather(battle, ctx, value, weather="ゆき", count=5)


def おわりのだいち_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_weather(battle, ctx, value, weather="おおひでり", count=1)


def おわりのだいち_deactivate_strong_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return deactivate_strong_weather(battle, ctx, value, weather="おおひでり")


def はじまりのうみ_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_weather(battle, ctx, value, weather="おおあめ", count=1)


def はじまりのうみ_deactivate_strong_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return deactivate_strong_weather(battle, ctx, value, weather="おおあめ")


def デルタストリーム_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_weather(battle, ctx, value, weather="らんきりゅう", count=1)


def デルタストリーム_deactivate_strong_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return deactivate_strong_weather(battle, ctx, value, weather="らんきりゅう")


# フィールド展開系


def エレキメイカー_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_terrain(battle, ctx, value, terrain="エレキフィールド", count=5)


def グラスメイカー_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_terrain(battle, ctx, value, terrain="グラスフィールド", count=5)


def サイコメイカー_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_terrain(battle, ctx, value, terrain="サイコフィールド", count=5)


def ミストメイカー_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_terrain(battle, ctx, value, terrain="ミストフィールド", count=5)


# 状態異常耐性系

def prevent_poison_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_ailment(battle, ctx, value, blocked_ailments=["どく", "もうどく"])


def prevent_paralysis_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_ailment(battle, ctx, value, blocked_ailments=["まひ"])


def prevent_burn_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_ailment(battle, ctx, value, blocked_ailments=["やけど"])


def prevent_sleep_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_ailment(battle, ctx, value, blocked_ailments=["ねむり"])


def prevent_freeze_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_ailment(battle, ctx, value, blocked_ailments=["こおり"])


def きよめのしお_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_ailment(battle, ctx, value)


# 揮発状態耐性系

def アロマベール_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_volatile(battle, ctx, value, blocked_volatiles=[
        "アンコール", "いちゃもん", "かいふくふうじ", "かなしばり", "ちょうはつ", "メロメロ"
    ])


def スイートベール_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_volatile(battle, ctx, value, blocked_volatiles=["ねむけ"])


def せいしんりょく_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_volatile(battle, ctx, value, blocked_volatiles=["ひるみ"])


def どんかん_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_volatile(battle, ctx, value, blocked_volatiles=["ちょうはつ", "メロメロ"])


def ふみん_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_volatile(battle, ctx, value, blocked_volatiles=["ねむけ"])


def マイペース_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_volatile(battle, ctx, value, blocked_volatiles=["こんらん"])


def やるき_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return prevent_volatile(battle, ctx, value, blocked_volatiles=["ねむけ"])


# スキン系


def _skin_modify_move_type(battle: Battle, ctx: EventContext, value: str, *, from_type: str, to_type: str) -> HandlerReturn:
    """スキン系特性共通: from_type の技を to_type に変換する。"""
    if ctx.move is not None and value == from_type:
        value = to_type
    return HandlerReturn(value=value)


def _skin_boost_power(battle: Battle, ctx: EventContext, value: int, *, trigger_type: str) -> HandlerReturn:
    """スキン系特性共通: trigger_type だった技の威力を 4915/4096 倍にする。"""
    if ctx.move is not None and ctx.move.data.type == trigger_type:
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def スカイスキン_modify_move_type(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="ひこう")


def フェアリースキン_modify_move_type(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="フェアリー")


def フリーズスキン_modify_move_type(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="こおり")


def スカイスキン_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")


def フェアリースキン_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")


def フリーズスキン_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")
