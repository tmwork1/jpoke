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
from jpoke.data import TYPE_MODIFIER
from jpoke.utils.math import apply_fixed_modifier
from jpoke.enums import Event, LogCode, Interrupt
from jpoke.core import HandlerReturn, Handler
from . import common


AEGISLASH_SHIELD = "ギルガルド(シールド)"
AEGISLASH_BLADE = "ギルガルド(ブレード)"
PALAFIN_ZERO = "イルカマン(ナイーブ)"
PALAFIN_HERO = "イルカマン(マイティ)"
EISCUE_ICE = "コオリッポ(アイス)"
EISCUE_NICE = "コオリッポ(ナイス)"
CRAMORANT_NORMAL = "ウッウ"
CRAMORANT_GULPING = "ウッウ(うのみ)"
CRAMORANT_GORGING = "ウッウ(まるのみ)"
WISHIWASHI_SOLO = "ヨワシ(たんどく)"
WISHIWASHI_SCHOOL = "ヨワシ(むれ)"
ZYGARDE_PERFECT = "ジガルデ(パーフェクト)"
METEONO_METEOR = "メテノ(りゅうせい)"
METEONO_CORE = "メテノ(コア)"
CASTFORM_NORMAL = "ポワルン"
CASTFORM_SUNNY = "ポワルン(たいよう)"
CASTFORM_RAINY = "ポワルン(あまみず)"
CASTFORM_SNOWY = "ポワルン(ゆきぐも)"
DARMANITAN_NORMAL = "ヒヒダルマ(ノーマル)"
DARMANITAN_ZEN = "ヒヒダルマ(ダルマ)"
TERAPAGOS_NORMAL = "テラパゴス(ノーマル)"
TERAPAGOS_TERASTAL = "テラパゴス(テラスタル)"

WEATHER_TO_CASTFORM: dict[str, str] = {
    "はれ": CASTFORM_SUNNY,
    "おおひでり": CASTFORM_SUNNY,
    "あめ": CASTFORM_RAINY,
    "おおあめ": CASTFORM_RAINY,
    "ゆき": CASTFORM_SNOWY,
    "あられ": CASTFORM_SNOWY,
}

# メガソーラー: ON_BEGIN_MOVE で保存した天候状態（current_name, はれのcount）を ON_END_MOVE で復元するための辞書
_メガソーラー_saved: dict[int, tuple[str, int]] = {}


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
        mon = getattr(ctx, "source", None) or getattr(ctx, "attacker", None)
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
    mon = getattr(ctx, "target", None) or getattr(ctx, "defender", None)
    return _block_item_change(mon, list(MEMORY_TO_TYPE.keys()))


def アイスフェイス_block_physical(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """アイスフェイス特性: 物理技のダメージを0にしてナイスフェイスにフォルムチェンジする。"""
    if battle.resolve_move_category(ctx.attacker, ctx.move) != "物理":
        return HandlerReturn(value=value)
    if ctx.defender.name != EISCUE_ICE:
        return HandlerReturn(value=value)
    ctx.defender.set_form(EISCUE_NICE)
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=0)


def アイスフェイス_restore_on_snow(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アイスフェイス特性: ゆきが発生したときナイスフェイスからアイスフェイスに戻る。"""
    mon = ctx.source
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    if mon.name != EISCUE_NICE:
        return HandlerReturn(value=value)
    if battle.weather.name != "ゆき":
        return HandlerReturn(value=value)
    mon.set_form(EISCUE_ICE)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def アイスフェイス_restore_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アイスフェイス特性: ゆき状態の場に登場したときアイスフェイスに戻る。"""
    mon = ctx.source
    if mon.name != EISCUE_NICE:
        return HandlerReturn(value=value)
    if battle.weather.name != "ゆき":
        return HandlerReturn(value=value)
    mon.set_form(EISCUE_ICE)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def アイスボディ_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アイスボディ特性: ゆき中にターン終了時に最大HPの1/16を回復する。"""
    mon = ctx.source
    if (
        battle.weather.name == "ゆき"
        and battle.modify_hp(mon, r=1/16)
    ):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def あくしゅう_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あくしゅう特性: 攻撃技を命中させたとき10%の確率でひるみを付与する。"""
    defender = ctx.defender
    if defender is None:
        return HandlerReturn(value=value)
    if battle.random.random() < 0.1:
        battle.volatile_manager.apply(defender, "ひるみ", source=ctx.attacker, ctx=ctx)
    return HandlerReturn(value=value)


def あついしぼう_reduce_fire_ice(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """あついしぼう特性: 炎/氷技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type in ["ほのお", "こおり"]:
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def あとだし_on_calc_back_tier(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """あとだし特性: 同一優先度の行動の中で最後に行動する（後攻ティア -1）。"""
    return HandlerReturn(value=value - 1)


def アナライズ_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """アナライズ特性: 行動が後になったターンの技威力を1.3倍にする。"""
    attacker_player = battle.get_player(ctx.attacker)
    is_second_actor = battle.query.is_second_actor(attacker_player)
    if is_second_actor is None:
        defender_player = battle.get_player(ctx.defender)
        defender_state = battle.player_states[defender_player]
        is_second_actor = (
            ctx.defender.executed_move is not None
            or defender_state.has_switched
        )

    if is_second_actor:
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


def いかく_lower_foe_atk(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いかく特性: 登場時に相手のこうげきを1段階下げる。"""
    source = ctx.source
    target = battle.foe(source)
    announce_ability_triggered(battle, ctx, value, mon=source)
    battle.modify_stats(target, {"A": -1}, source=source, reason="いかく")
    return HandlerReturn(value=value)


def いかりのこうら_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いかりのこうら特性: HPが半分以下になったときA・C・S↑1、B・D↓1。"""
    mon = ctx.defender
    hp_after = mon.hp
    hp_before = hp_after + value
    if not _crossed_half_hp(hp_before, hp_after, mon.max_hp):
        return HandlerReturn(value=value)
    battle.modify_stats(mon, {"B": -1, "D": -1}, source=ctx.attacker)
    if battle.modify_stats(mon, {"A": +1, "C": +1, "S": +1}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def いかりのつぼ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いかりのつぼ特性: 急所に被弾したときこうげきを最大まで上げる。"""
    if not battle.move_executor.critical:
        return HandlerReturn(value=value)
    mon = ctx.defender
    diff = 6 - mon.rank["A"]
    if diff > 0 and battle.modify_stats(mon, {"A": diff}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
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


def うのミサイル_on_move_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """うのミサイル特性: なみのり/ダイビング成功後に HP に応じてフォルムチェンジする。"""
    mon = ctx.attacker
    if mon.name != CRAMORANT_NORMAL:
        return HandlerReturn(value=value)
    if ctx.move is None or ctx.move.name not in ("なみのり", "ダイビング"):
        return HandlerReturn(value=value)
    if not battle.move_executor.move_applied:
        return HandlerReturn(value=value)

    next_form = CRAMORANT_GULPING if mon.hp * 2 > mon.max_hp else CRAMORANT_GORGING
    mon.set_form(next_form)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def うのミサイル_on_damage_hit(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """うのミサイル特性: 咥えたすがたのときダメージを受けると獲物を吐き出して反撃する。"""
    mon = ctx.defender
    form = mon.name
    if form not in (CRAMORANT_GULPING, CRAMORANT_GORGING):
        return HandlerReturn(value=value)
    if mon.has_volatile("かくれる"):
        return HandlerReturn(value=value)
    if ctx.attacker.fainted:
        return HandlerReturn(value=value)

    mon.set_form(CRAMORANT_NORMAL)
    announce_ability_triggered(battle, ctx, value, mon=mon)

    damage = max(1, ctx.attacker.max_hp // 4)
    battle.modify_hp(ctx.attacker, -damage, source=mon, reason="ability")

    if form == CRAMORANT_GULPING:
        battle.modify_stats(ctx.attacker, {"B": -1}, source=mon)
    else:
        battle.ailment_manager.apply(ctx.attacker, "まひ", source=mon, ctx=ctx)

    return HandlerReturn(value=value)


def うのミサイル_on_switch_out(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """うのミサイル特性: 交代時に通常のすがたに戻す。"""
    mon = ctx.source
    if mon.name in (CRAMORANT_GULPING, CRAMORANT_GORGING):
        mon.set_form(CRAMORANT_NORMAL)
    return HandlerReturn(value=value)


def うるおいボイス_modify_move_type(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    """うるおいボイス特性: ノーマルタイプの音技をみずタイプに変換する。"""
    if ctx.move is not None and ctx.move.has_label("sound") and value == "ノーマル":
        return HandlerReturn(value="みず")
    return HandlerReturn(value=value)


def うるおいボイス_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """うるおいボイス特性: みず変換した音技の威力を1.2倍にする。"""
    if ctx.move is not None and ctx.move.has_label("sound") and ctx.move.data.type == "ノーマル":
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def うるおいボディ_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """うるおいボディ特性: あめ/おおあめ中にターン終了時に状態異常を回復する。"""
    if not battle.weather.rainy:
        return HandlerReturn(value=value)
    mon = ctx.source
    if not mon.ailment.is_active:
        return HandlerReturn(value=value)
    result = common.cure_self_ailment(battle, ctx, value)
    if result.value:
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def エアロック_check_weather_enabled(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """エアロック特性: 天候効果を無効化する。"""
    return HandlerReturn(value=False, stop_event=True)


def えんかく_nullify_contact(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """えんかく特性: 自分が使う技の接触判定を無効化する。"""
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


_OGERPON_STAT: dict[str, Stat] = {
    "オーガポン(みどり)": "S",
    "オーガポン(いど)": "D",
    "オーガポン(かまど)": "A",
    "オーガポン(いしずえ)": "B",
}


def おみとおし_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おみとおし特性: 場に出たとき相手のアイテムを公開する。"""
    mon = ctx.source
    foe = battle.foe(mon)
    if not foe.has_item():
        return HandlerReturn(value=value)
    foe.item.revealed = True
    announce_ability_triggered(battle, ctx, value, mon=mon)
    battle.add_event_log(
        mon, LogCode.TEXT_LOG,
        payload={"text": f"{mon.name}は{foe.name}の{foe.item.base_name}をお見通しだ！"}
    )
    return HandlerReturn(value=value)


def カーリーヘアー_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """カーリーヘアー特性: 直接攻撃を受けると攻撃者のすばやさを1段階下げる。"""
    attacker = ctx.attacker
    if attacker is not None and battle.query.is_contact(ctx):
        battle.modify_stats(attacker, {"S": -1}, source=ctx.defender)
    return HandlerReturn(value=value)


def おもかげやどし_boost_stat(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おもかげやどし特性: 場に出たときフォルムに対応する能力が1段階上がる。"""
    mon = ctx.source
    stat = _OGERPON_STAT.get(mon.name)
    if stat is None:
        return HandlerReturn(value=value)
    mon.ability.activated_since_switch_in = True
    announce_ability_triggered(battle, ctx, value, mon=mon)
    battle.modify_stats(mon, {stat: +1}, source=mon)
    return HandlerReturn(value=value)


def かいりきバサミ_block_A_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """かいりきバサミ特性: 相手によるこうげきランク低下を無効化する。"""
    value = common.block_stat_drop_by_foe(value, ctx, "A")
    return HandlerReturn(value=value)


def かがくへんかガス_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def かぜのり_absorb_wind(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """かぜのり特性: 風の技を無効化しこうげきを1段階上げる。"""
    if (
        not ctx.move.target == "foe"
        or not ctx.move.has_label("wind")
    ):
        return HandlerReturn(value=value)
    defender = ctx.defender
    announce_ability_triggered(battle, ctx, value, mon=defender)
    battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                         payload={"reason": defender.ability.base_name})
    battle.modify_stats(defender, {"A": 1}, source=ctx.attacker)
    return HandlerReturn(value=False, stop_event=True)


def かぜのり_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かぜのり特性: おいかぜ状態の場に出たときこうげきを1段階上げる。"""
    mon = ctx.source
    if not battle.get_side(mon).get("おいかぜ").is_active:
        return HandlerReturn(value=value)
    changed = battle.modify_stats(mon, {"A": 1}, source=mon)
    if changed:
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def かぜのり_on_field_activate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かぜのり特性: 味方の場においかぜが発生したときこうげきを1段階上げる。"""
    mon = ctx.source
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    if value.name != "おいかぜ":
        return HandlerReturn(value=value)
    if not battle.get_side(mon).get("おいかぜ").is_active:
        return HandlerReturn(value=value)
    changed = battle.modify_stats(mon, {"A": 1}, source=mon)
    if changed:
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def かそく_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かそく特性: 行動済みならターン終了時に素早さを1段階上げる。"""
    mon = ctx.source
    print(f"{battle.turn=}, {mon.executed_move=}")
    if (
        mon.executed_move is not None
        and battle.modify_stats(mon, {"S": +1}, source=mon)
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
        and battle.modify_stats(ctx.target, {"C": +2}, source=ctx.source)
    ):
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
    return HandlerReturn(value=value)


def カブトアーマー_block_crit(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """カブトアーマー特性: 防御側の急所ランクを無効化する。"""
    return HandlerReturn(value=0, stop_event=True)


def かるわざ_init_state(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かるわざ特性: 入場時に発動可否の初期状態を記録する。"""
    mon = ctx.source
    # "idle": 入場時にアイテムあり（消失で発動可能）
    # "inactive": 入場時にアイテムなし（この在場中は発動しない）
    mon.ability.state = "idle" if mon.has_item() else "inactive"
    return HandlerReturn(value=value)


def かるわざ_reset_state(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
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


def かんろなミツ_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かんろなミツ特性: 初登場時に相手の回避率を1段階下げる（バトル中1回）。"""
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    foe = battle.foe(mon)
    if foe is None:
        return HandlerReturn(value=value)
    battle.add_ability_disabled_reason(mon, "consumed")
    if battle.modify_stats(foe, {"EVA": -1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
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


def きけんよち_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """きけんよち特性: 登場時に相手がバツグン攻撃技か一撃必殺技を持つ場合にメッセージを出す。"""
    source = ctx.source
    foe = battle.foe(source)
    for move in foe.moves:
        if not move.is_attack:
            continue
        if move.has_label("ohko"):
            announce_ability_triggered(battle, ctx, value, mon=source)
            return HandlerReturn(value=value)
        type_chart = TYPE_MODIFIER.get(move.type, {})
        modifier = 1.0
        for def_type in source.types:
            modifier *= type_chart.get(def_type, 1.0)
        if modifier > 1.0:
            announce_ability_triggered(battle, ctx, value, mon=source)
            return HandlerReturn(value=value)
    return HandlerReturn(value=value)


def きもったま_ghost_immune_bypass(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """きもったま特性: ノーマル/かくとう技がゴーストタイプに当たるよう相性補正を書き換える。"""
    if ctx.move.type not in ("ノーマル", "かくとう"):
        return HandlerReturn(value=value)
    if not ctx.defender.has_type("ゴースト"):
        return HandlerReturn(value=value)
    type_chart = TYPE_MODIFIER.get(ctx.move.type, {})
    base = 4096
    for def_type in ctx.defender.types:
        if def_type == "ゴースト":
            continue
        rate = type_chart.get(def_type, 1.0)
        base = int(base * rate)
    return HandlerReturn(value=base)


def きもったま_block_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """きもったま特性: いかくによるこうげきランク低下を無効化する。"""
    if ctx.stat_change_reason == "いかく":
        value = {}
    return HandlerReturn(value=value)


def ぎゃくじょう_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぎゃくじょう特性: HP が半分以下になった時、特攻が1段階上昇する。"""
    mon = ctx.defender
    hp_after = mon.hp
    hp_before = hp_after + value

    if (
        _crossed_half_hp(hp_before, hp_after, mon.max_hp)
        and battle.modify_stats(mon, {"C": +1}, source=ctx.attacker, reason="ぎゃくじょう")
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


def ぎょぐん_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぎょぐん特性: 登場時にレベル20以上かつHP1/4超ならむれたすがたへフォルムチェンジする。"""
    mon = ctx.source
    if mon.level < 20:
        return HandlerReturn(value=value)
    if mon.hp * 4 > mon.max_hp:
        mon.set_form(WISHIWASHI_SCHOOL)
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ぎょぐん_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぎょぐん特性: ターン終了時にHPに応じてフォルムを切り替える。"""
    mon = ctx.source
    if mon.level < 20:
        return HandlerReturn(value=value)
    if mon.hp * 4 > mon.max_hp:
        if mon.set_form(WISHIWASHI_SCHOOL):
            announce_ability_triggered(battle, ctx, value, mon=mon)
    else:
        if mon.set_form(WISHIWASHI_SOLO):
            announce_ability_triggered(battle, ctx, value, mon=mon)
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


def きんしのちから_on_calc_back_tier(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """きんしのちから特性: 変化技選択時に行動を後攻化する（後攻ティア -1）。"""
    if ctx.move is None or ctx.move.is_attack:
        return HandlerReturn(value=value)
    return HandlerReturn(value=value - 1)


def きんしのちから_disable_foe_ability(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """きんしのちから特性: 変化技使用直前に相手の特性を無効化する。"""
    if ctx.move is None or ctx.move.is_attack:
        return HandlerReturn(value=value)
    mon = ctx.defender
    if mon.ability.has_flag("mold_breaker_ignorable"):
        battle.add_ability_disabled_reason(mon, "かたやぶり")
    return HandlerReturn(value=value)


def きんしのちから_restore_foe_ability(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """きんしのちから特性: 変化技使用後に相手の特性の無効化を解除する。"""
    if ctx.move is None or ctx.move.is_attack:
        return HandlerReturn(value=value)
    battle.remove_ability_disabled_reason(ctx.defender, "かたやぶり")
    return HandlerReturn(value=value)


def きんちょうかん_check_nervous(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """きんちょうかん特性: 相手のきのみ使用を禁止する。"""
    return HandlerReturn(value=True)


def クイックドロウ_on_calc_back_tier(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """クイックドロウ特性: 攻撃技選択時に 30% の確率で先攻化する（後攻ティア +1）。"""
    if ctx.move is None or not ctx.move.is_attack:
        return HandlerReturn(value=value)
    if not battle.random.random() < 0.3:
        return HandlerReturn(value=value)
    announce_ability_triggered(battle, ctx, value, mon=ctx.source)
    return HandlerReturn(value=value + 1)


def くさのけがわ_boost_B(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """くさのけがわ特性: グラスフィールド中の物理技への防御補正を1.5倍にする。"""
    if (
        battle.terrain.name == "グラスフィールド"
        and common.deals_physical_damage(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def くだけるよろい_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くだけるよろい特性: 物理技を受けるとぼうぎょが1段階下がりすばやさが2段階上がる。"""
    if battle.resolve_move_category(ctx.attacker, ctx.move) != "物理":
        return HandlerReturn(value=value)
    mon = ctx.defender
    battle.modify_stats(mon, {"B": -1}, source=ctx.attacker)
    if battle.modify_stats(mon, {"S": +2}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
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


def こぼれダネ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こぼれダネ特性: 攻撃技でダメージを受けたときグラスフィールドを展開する。"""
    mon = ctx.defender
    if battle.terrain_manager.apply("グラスフィールド", 5, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
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


def サーフテール_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """サーフテール特性: エレキフィールド中に素早さが2倍になる。"""
    if battle.terrain.name == "エレキフィールド":
        value *= 2
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


def さまようたましい_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さまようたましい特性: 直接攻撃を受けたとき攻撃者と特性を入れ替える。"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    attacker = ctx.attacker
    if attacker is None or attacker.fainted:
        return HandlerReturn(value=value)
    if not attacker.ability.base_name:
        return HandlerReturn(value=value)
    if attacker.ability.has_flag("protected"):
        return HandlerReturn(value=value)
    defender = ctx.defender
    if defender is None:
        return HandlerReturn(value=value)
    battle.ability_manager.swap_ability(defender, attacker)
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


def _boost_on_move_ko(battle: Battle, ctx: EventContext, value: Any, stats: dict[Stat, int]) -> HandlerReturn:
    if battle.modify_stats(ctx.attacker, stats, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=ctx.attacker)
    return HandlerReturn(value=value)


def くろのいななき_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くろのいななき特性: 攻撃技で相手を倒すと特攻が1段階上がる。"""
    return _boost_on_move_ko(battle, ctx, value, stats={"C": +1})


def じきゅうりょく_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じきゅうりょく特性: 攻撃技でダメージを受けるたびにぼうぎょが1段階上がる。"""
    mon = ctx.defender
    if battle.modify_stats(mon, {"B": +1}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def しろのいななき_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じしんかじょう特性: 攻撃技で相手を倒すと攻撃が1段階上がる。"""
    return _boost_on_move_ko(battle, ctx, value, stats={"A": +1})


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


def じょうきっかん_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じょうきっかん特性: みずまたはほのお技でダメージを受けるとすばやさが6段階上がる。"""
    if ctx.move.type not in ("みず", "ほのお"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"S": +6}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def しょうりのほし_modify_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しょうりのほし特性: 技の命中率を1.1倍にする（一撃必殺技を除く）。"""
    if ctx.move is not None and not ctx.move.has_label("ohko"):
        value = apply_fixed_modifier(value, 4506)
    return HandlerReturn(value=value)


def しゅうかく_restore_berry(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def じょおうのいげん_block_priority(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じょおうのいげん/テイルアーマー/ビビッドボディ: 優先度+1以上の技を無効化する。"""
    effective_priority = battle.speed_calculator.calc_move_priority(ctx.attacker, ctx.move)
    if effective_priority <= 0:
        return HandlerReturn(value=value)
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED, payload={"reason": "じょおうのいげん"})
    return HandlerReturn(value=False, stop_event=True)


def じりょく_check_trapped(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じりょく特性: はがねタイプのポケモンの交代を防ぐ。"""
    return HandlerReturn(value=ctx.source.has_type("はがね"))


def しんがん_ghost_immune_bypass(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """しんがん特性: ノーマル/かくとう技がゴーストタイプに等倍で当たるよう相性補正を書き換える。"""
    if ctx.move.type not in ("ノーマル", "かくとう"):
        return HandlerReturn(value=value)
    if not ctx.defender.has_type("ゴースト"):
        return HandlerReturn(value=value)
    type_chart = TYPE_MODIFIER.get(ctx.move.type, {})
    base = 4096
    for def_type in ctx.defender.types:
        if def_type == "ゴースト":
            continue
        rate = type_chart.get(def_type, 1.0)
        base = int(base * rate)
    return HandlerReturn(value=base)


_SYNC_AILMENTS: frozenset[AilmentName] = frozenset(["どく", "もうどく", "まひ", "やけど"])


def シンクロ_return_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """シンクロ特性: 相手から受けたどく・もうどく・まひ・やけど状態を相手に返す。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_APPLY_AILMENT)
            - target: 状態異常を付与されたポケモン（シンクロ所持者）
            - source: 状態異常を付与した相手
        value: 付与された状態異常名
    """
    ailment_name = value
    if ailment_name not in _SYNC_AILMENTS:
        return HandlerReturn(value=value)
    # 自傷（かえんだま等）や自分自身による付与には反応しない
    if not ctx.is_foe_target():
        return HandlerReturn(value=value)
    foe = ctx.source
    if foe is None:
        return HandlerReturn(value=value)
    announce_ability_triggered(battle, ctx, value, mon=ctx.target)
    battle.ailment_manager.apply(foe, ailment_name, source=ctx.target, ctx=ctx)
    return HandlerReturn(value=value)


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


def すてみ_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すてみ特性: 反動を受ける技の威力を1.2倍にする。"""
    if ctx.move is not None and ctx.move.has_label("recoil"):
        value = apply_fixed_modifier(value, 4915)
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


def すながくれ_reduce_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """すながくれ特性: すなあらし中に受ける技の命中率を3277/4096倍にする（必中技は除く）。"""
    if battle.weather.name == "すなあらし":
        value = apply_fixed_modifier(value, 3277)
    return HandlerReturn(value=value)


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


def すなはき_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """すなはき特性: 攻撃を受けたときすなあらし（5ターン）を展開する。"""
    mon = ctx.defender
    if battle.weather_manager.apply("すなあらし", 5, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
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


def するどいめ_ignore_evasion(battle: Battle, ctx: EventContext, value: dict[Stat, int]) -> HandlerReturn:
    """するどいめ特性: 相手の回避率ランク上昇を無効化する。"""
    value["EVA"] = 0
    return HandlerReturn(value=value)


def スロースタート_start(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def スワームチェンジ_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スワームチェンジ特性: ターン終了時にHP1/2以下ならパーフェクトフォルムへフォルムチェンジする。"""
    mon = ctx.source
    if mon.name == ZYGARDE_PERFECT:
        return HandlerReturn(value=value)
    if mon.hp * 2 <= mon.max_hp:
        mon.set_form(ZYGARDE_PERFECT)
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def せいぎのこころ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """せいぎのこころ特性: あくタイプの技でダメージを受けるとこうげきが1段階上がる。"""
    if ctx.move.type != "あく":
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"A": +1}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
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


def ぜったいねむり_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぜったいねむり特性: 登場時にゆめうつつ状態を付与する。"""
    mon = ctx.source
    assert mon is not None
    if not battle.ailment_manager.apply(mon, "ゆめうつつ"):
        # 既にゆめうつつ（2回目以降の登場）→ メッセージのみ出す
        battle.add_event_log(mon, LogCode.AILMENT_APPLIED, payload={"ailment": "ゆめうつつ"})
    return HandlerReturn(value=value)


def ぜったいねむり_boost_sleep_moves(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ぜったいねむり特性: めざましビンタ・たたりめ・ひゃっきやこうの威力を2倍にする。"""
    if ctx.move.name in ["めざましビンタ", "たたりめ", "ひゃっきやこう"]:
        return HandlerReturn(value=value * 2)
    return HandlerReturn(value=value)


def ゼロフォーミング_on_terastallize(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ゼロフォーミング特性: テラスタル時に場の天候とフィールドを消去する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_TERASTALLIZE)
            - source: テラスタルしたポケモン
        value: イベント値（未使用）
    """
    mon = ctx.source
    announce_ability_triggered(battle, ctx, value, mon=mon)
    battle.weather_manager.remove()
    battle.terrain_manager.remove()
    return HandlerReturn(value=value)


def そうしょく_absorb_grass(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """そうしょく特性: くさ技を無効化し攻撃を1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="くさ", stats={"A": 1})


def そうだいしょう_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """そうだいしょう特性: 入場時、ひんし味方の数×10%の威力補正を得る（最大50%）。"""
    mon = ctx.source
    player = battle.get_player(mon)
    state = battle.player_states[player]
    fainted_count = sum(1 for p in state.selection if p.fainted and p is not mon)
    if fainted_count == 0:
        return HandlerReturn(value=value)
    mon.ability.state = min(fainted_count * 0.1, 0.5)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def そうだいしょう_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """そうだいしょう特性: 入場時に記録した威力補正を適用する。"""
    multiplier = ctx.attacker.ability.state
    if not multiplier:
        return HandlerReturn(value=value)
    return HandlerReturn(value=apply_fixed_modifier(value, int(4096 * (1 + multiplier))))


def ソウルハート_on_ko(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ソウルハート特性: 攻撃技で相手を倒すととくこうが1段階上がる。"""
    mon = ctx.attacker
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    if battle.modify_stats(mon, {"C": +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


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

    changed = battle.modify_stats(mon, {boost_stat: +1}, source=mon)
    if changed:
        announce_ability_triggered(battle, ctx, value, mon=mon)

    return HandlerReturn(value=value)


def ダークオーラ_boost_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ダークオーラ特性: あく技の威力を1.33倍にする。オーラブレイクがいる場合は0.75倍にする。"""
    if ctx.move.type != "あく":
        return HandlerReturn(value=value)
    aura_break = (
        ctx.attacker.ability.name == "オーラブレイク"
        or ctx.defender.ability.name == "オーラブレイク"
    )
    modifier = 3072 if aura_break else 5448
    return HandlerReturn(value=apply_fixed_modifier(value, modifier))


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


def ダルマモード_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ダルマモード特性: ターン終了時にHPが1/2以下ならダルマのすがたへ、1/2超なら元のすがたへフォルムチェンジする。"""
    mon = ctx.source
    if mon.hp * 2 <= mon.max_hp:
        if mon.name == DARMANITAN_NORMAL:
            mon.set_form(DARMANITAN_ZEN)
            announce_ability_triggered(battle, ctx, value, mon=mon)
    else:
        if mon.name == DARMANITAN_ZEN:
            mon.set_form(DARMANITAN_NORMAL)
            announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ダルマモード_on_switch_out(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ダルマモード特性: 交代時にダルマのすがたから元のすがたへ戻す。"""
    mon = ctx.source
    if mon.name == DARMANITAN_ZEN:
        mon.set_form(DARMANITAN_NORMAL)
    return HandlerReturn(value=value)


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


def ちどりあし_reduce_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちどりあし特性: こんらん中の自分に対する技の命中率を半分にする。"""
    if ctx.defender is not None and ctx.defender.has_volatile("こんらん"):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


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


def テラスチェンジ_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """テラスチェンジ特性: 登場時に他の特性より先にテラスタルフォルムへフォルムチェンジする。"""
    mon = ctx.source
    if mon.name != TERAPAGOS_NORMAL:
        return HandlerReturn(value=value)
    mon.set_form(TERAPAGOS_TERASTAL)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def でんきエンジン_absorb_electric(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """でんきエンジン特性: でんき技を無効化し素早さを1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="でんき", stats={"S": 1})


def でんきにかえる_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """でんきにかえる特性: 攻撃技でダメージを受けるとじゅうでん状態になる。"""
    mon = ctx.defender
    if battle.volatile_manager.apply(mon, "じゅうでん", source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def てんきや_sync_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """てんきや特性: 現在の天気に合わせたフォルムへフォルムチェンジする。ノーてんき/エアロック中は通常フォルムに戻す。"""
    mon = ctx.source
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    weather_name = battle.weather.name
    form = WEATHER_TO_CASTFORM.get(weather_name, CASTFORM_NORMAL)
    if mon.set_form(form):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def てんねん_ignore_rank(battle: Battle, ctx: EventContext, value: float) -> HandlerReturn:
    """てんねん特性: ランク補正を無視する。"""
    return HandlerReturn(value=1)


def てんのめぐみ_boost_secondary_chance(battle: Battle, ctx: EventContext, value: float) -> HandlerReturn:
    """てんのめぐみ特性: 追加効果対象技の追加効果確率を2倍にする。"""
    return HandlerReturn(value=min(1.0, value * 2))


def とうそうしん_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """とうそうしん特性: 同性の相手にこうげく/とくこうが1.25倍、異性には0.75倍になる。"""
    a_gender = ctx.attacker.gender
    d_gender = ctx.defender.gender if ctx.defender is not None else ""
    if not a_gender or not d_gender:
        return HandlerReturn(value=value)
    if a_gender == d_gender:
        value = apply_fixed_modifier(value, 5120)
    else:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def どくくぐつ_on_apply_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくくぐつ特性: どく/もうどく付与時に対象をこんらんにする。"""
    if value not in ("どく", "もうどく"):
        return HandlerReturn(value=value)
    target = ctx.target
    if target is None:
        return HandlerReturn(value=value)
    battle.volatile_manager.apply(target, "こんらん", source=ctx.source)
    announce_ability_triggered(battle, ctx, value, mon=ctx.source)
    return HandlerReturn(value=value)


def どくげしょう_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくげしょう特性: 物理技被弾時に攻撃者の場にどくびしを1層設置する。"""
    if battle.resolve_move_category(ctx.attacker, ctx.move) != "物理":
        return HandlerReturn(value=value)
    foe_side = battle.get_side(ctx.attacker)
    field = foe_side.get("どくびし")
    if field.count >= 2:
        return HandlerReturn(value=value)
    if field.is_active:
        field.count += 1
        battle.add_event_log(0, LogCode.FIELD_STARTED, payload={"field": "どくびし", "count": field.count})
    else:
        foe_side.activate("どくびし", 1)
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=value)


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


def どくのくさり_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくのくさり特性: 攻撃を命中させたとき30%の確率で相手をもうどくにする。"""
    if battle.random.random() < battle.resolve_secondary_chance(ctx, 0.3):
        battle.ailment_manager.apply(
            ctx.defender, "もうどく", source=ctx.attacker, ctx=ctx,
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


_とびだすなかみ_hp_before: dict[int, int] = {}  # id(defender) → HP before move


def とびだすなかみ_save_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """とびだすなかみ補助: 技開始時に防御側の初期HPを保存する。"""
    _とびだすなかみ_hp_before[id(ctx.defender)] = ctx.defender.hp
    return HandlerReturn(value=value)


def とびだすなかみ_on_ko(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """とびだすなかみ特性: 攻撃技でひんしになったとき攻撃者に反撃ダメージを与える。"""
    attacker = ctx.attacker
    defender = ctx.defender
    if attacker is None or attacker.fainted:
        return HandlerReturn(value=value)
    hp_before = _とびだすなかみ_hp_before.pop(id(defender), abs(value))
    if hp_before <= 0:
        return HandlerReturn(value=value)
    battle.modify_hp(attacker, -hp_before)
    announce_ability_triggered(battle, ctx, value, mon=defender)
    return HandlerReturn(value=value)


def とびだすハバネロ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """とびだすハバネロ特性: 攻撃技を受けたとき攻撃者をやけど状態にする。"""
    attacker = ctx.attacker
    if attacker is None:
        return HandlerReturn(value=value)
    battle.ailment_manager.apply(attacker, "やけど", source=ctx.defender, ctx=ctx)
    return HandlerReturn(value=value)


def ドラゴンスキン_modify_move_type(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="ドラゴン")


def ドラゴンスキン_modify_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")


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


def とれないにおい_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """とれないにおい特性: 直接攻撃でダメージを受けたとき攻撃者の特性をとれないにおいにする。"""
    if _overwrite_ability_on_contact(battle, ctx, new_ability="とれないにおい"):
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=value)


def ナイトメア_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ナイトメア特性: 相手がねむり状態のとき毎ターン最大HPの1/8を削る。"""
    mon = ctx.source
    foe = battle.foe(mon)
    if foe is None or not foe.alive:
        return HandlerReturn(value=value)
    if foe.ailment.name != "ねむり":
        return HandlerReturn(value=value)
    if battle.modify_hp(foe, r=-1/8, reason="ability"):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def なまけ_init(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """なまけ特性: 登場/有効化時になまけカウンタを「行動可」で初期化する。"""
    ctx.source.ability.state = "can_act"  # TODO: AbilityState に追加
    return HandlerReturn(value=value)


def ぬめぬめ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぬめぬめ特性: 直接攻撃を受けると攻撃者のすばやさを1段階下げる。"""
    attacker = ctx.attacker
    if attacker is not None and battle.query.is_contact(ctx):
        battle.modify_stats(attacker, {"S": -1}, source=ctx.defender)
    return HandlerReturn(value=value)


def なまけ_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """なまけ特性: X=1のターンは行動をスキップし、Xを反転する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_TRY_ACTION)
            - attacker: 行動しようとするポケモン
        value: 行動可否フラグ（True=行動可）
    """
    mon = ctx.attacker
    state = mon.ability.state
    if state == "skip_next":  # TODO : AbilityState に追加
        # このターンはなまける
        mon.ability.state = "can_act"
        battle.add_event_log(mon, LogCode.ACTION_BLOCKED, payload={"reason": "なまけ"})
        return HandlerReturn(value=False, stop_event=True)
    # state == "can_act"
    mon.ability.state = "skip_next"
    return HandlerReturn(value=value)


def ねつこうかん_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねつこうかん特性: ほのおタイプの攻撃技でダメージを受けたとき、こうげきが1段階上がる。"""
    if ctx.move.type != "ほのお":
        return HandlerReturn(value=value)

    changed = battle.modify_stats(ctx.defender, {"A": +1}, source=ctx.attacker)
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


def のろわれボディ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """のろわれボディ特性: 直接攻撃を受けたとき30%の確率で攻撃技をかなしばりにする。"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    if ctx.move is None or ctx.attacker is None:
        return HandlerReturn(value=value)
    if battle.random.random() < 0.3:
        battle.volatile_manager.apply(
            ctx.attacker, "かなしばり",
            source=ctx.defender, ctx=ctx, move_name=ctx.move.name,
        )
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
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


def はっこう_block_acc_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """はっこう特性: 相手による命中率ランク低下を無効化する。"""
    filtered = {stat: v for stat, v in value.items() if not (stat == "ACC" and v < 0)}
    return HandlerReturn(value=filtered)


# ===== がんじょう =====

def はとむね_block_B_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """はとむね特性: 相手によるぼうぎょランク低下を無効化する。"""
    value = common.block_stat_drop_by_foe(value, ctx, "B")
    return HandlerReturn(value=value)


def バトルスイッチ_change_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 行動前に必要なフォルムへ切り替える。"""
    mon = ctx.attacker
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


def ハドロンエンジン_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_terrain(battle, ctx, value, terrain="エレキフィールド", count=5)


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


def はやおき_extra_decrement(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """はやおき特性: ねむり状態のとき、ねむりカウンタを追加で1消費する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_TRY_ACTION)
            - attacker: 行動しようとするポケモン
        value: 行動可否フラグ
    """
    mon = ctx.attacker
    if not mon.has_ailment("ねむり"):
        return HandlerReturn(value=value)
    # ねむり_check_action より先 (priority=9) に追加tickを実行
    battle.ailment_manager.tick(mon)
    return HandlerReturn(value=value)


def はやてのつばさ_modify_priority(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はやてのつばさ特性: HP満タン時にひこうタイプの技を使うと優先度を+1する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_MOVE_PRIORITY)
            - source: 技を使用するポケモン
        value: 現在の優先度
    """
    mon = ctx.source
    if ctx.move is None:
        return HandlerReturn(value=value)
    if ctx.move.type != "ひこう":
        return HandlerReturn(value=value)
    if mon.hp < mon.max_hp:
        return HandlerReturn(value=value)
    return HandlerReturn(value=value + 1)


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


_BARRIER_SCREENS: tuple[str, ...] = ("リフレクター", "ひかりのかべ", "オーロラベール")


def バリアフリー_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バリアフリー特性: 場に出たとき敵味方全体の壁を解除する。"""
    mon = ctx.source
    triggered = False
    for side in battle.side_managers:
        for screen in _BARRIER_SCREENS:
            if side.deactivate(screen):
                triggered = True
    if triggered:
        announce_ability_triggered(battle, ctx, value, mon=mon)
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
    if (
        ctx.defender is not None
        and battle.player_states[battle.get_player(ctx.defender)].has_switched
    ):
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


def ばんけん_on_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """ばんけん特性: いかくを受けたときこうげきを1段階上げる。"""
    if ctx.stat_change_reason != "いかく":
        return HandlerReturn(value=value)
    mon = ctx.target
    battle.modify_stats(mon, {"A": +1}, source=mon)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


_BEAST_BOOST_ORDER: tuple[str, ...] = ("A", "B", "C", "D", "S")


def ビーストブースト_on_ko(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ビーストブースト特性: 攻撃技で倒すと最も実数値が高い能力が1段階上がる。"""
    mon = ctx.attacker
    best_stat = max(_BEAST_BOOST_ORDER, key=lambda s: mon.stats[s])
    if battle.modify_stats(mon, {best_stat: +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ひとでなし_modify_critical_rank(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ひとでなし特性: どく/もうどく状態の相手への攻撃を必ず急所にする。"""
    if ctx.defender.has_ailment("どく", "もうどく"):
        value = 10
    return HandlerReturn(value=value)


def ヒーリングシフト_modify_priority(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ヒーリングシフト特性: 回復技・吸収技の優先度を+3する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_MOVE_PRIORITY)
            - attacker: 技を使用するポケモン
        value: 現在の優先度
    """
    if ctx.move is not None and ctx.move.has_label("heal"):
        value += 3
    return HandlerReturn(value=value)


def ひひいろのこどう_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return activate_weather(battle, ctx, value, weather="はれ", count=5)


def ひひいろのこどう_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ひひいろのこどう特性: はれ中の攻撃補正を1.33倍にする。"""
    if battle.weather.sunny:
        value = apply_fixed_modifier(value, 5461)
    return HandlerReturn(value=value)


def びびり_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """びびり特性: あく/ゴースト/むしタイプの技でダメージを受けるとすばやさが1段階上がる。"""
    if ctx.move.type not in ("あく", "ゴースト", "むし"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"S": +1}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ひらいしん_absorb_electric(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ひらいしん特性: でんき技を無効化し特攻を1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="でんき", stats={"C": 1})


def びんじょう_copy_stat_rise(battle: Battle, ctx: EventContext, value: dict[Stat, int]) -> HandlerReturn:
    """びんじょう特性: 相手のランク上昇をコピーする。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_STAT)
            - target: ランクが変化したポケモン（相手）
            - source: 変化の原因
        value: 実際に変化した能力ランクの辞書

    subject_spec="target:foe" で登録するため、ctx.target が相手（ランクが上がった側）。
    びんじょう所持者は battle.foe(ctx.target) で取得する。
    """
    rises = {stat: v for stat, v in value.items() if v > 0}
    if not rises:
        return HandlerReturn(value=value)
    # びんじょう所持者は相手（ctx.target）の敵側
    self_mon = battle.foe(ctx.target)
    if self_mon is None:
        return HandlerReturn(value=value)
    changed = battle.modify_stats(self_mon, rises, source=ctx.target)
    if changed:
        announce_ability_triggered(battle, ctx, value, mon=self_mon)
    return HandlerReturn(value=value)


def ファーコート_boost_B(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ファーコート特性: 物理技に対する防御補正を2倍にする。"""
    if common.deals_physical_damage(battle, ctx):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def フェアリーオーラ_boost_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """フェアリーオーラ特性: フェアリー技の威力を1.33倍にする。オーラブレイクがいる場合は0.75倍にする。"""
    if ctx.move.type != "フェアリー":
        return HandlerReturn(value=value)
    aura_break = (
        ctx.attacker.ability.name == "オーラブレイク"
        or ctx.defender.ability.name == "オーラブレイク"
    )
    modifier = 3072 if aura_break else 5448
    return HandlerReturn(value=apply_fixed_modifier(value, modifier))


def ぶきよう_disable_item(battle: Battle, ctx: EventContext, value: set[ItemDisabledReason]) -> HandlerReturn:
    battle.add_item_disabled_reason(ctx.source, "ぶきよう")
    return HandlerReturn(value=value)


def ぶきよう_enable_item(battle: Battle, ctx: EventContext, value: set[ItemDisabledReason]) -> HandlerReturn:
    battle.remove_item_disabled_reason(ctx.source, "ぶきよう")
    return HandlerReturn(value=value)


_PROTECT_VOLATILES: frozenset[str] = frozenset([
    "まもる", "トーチカ", "キングシールド", "スレッドトラップ", "かえんのまもり",
])


def ふかしのこぶし_bypass_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """接触技使用時にまもる系の防護を貫通する"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    return HandlerReturn(value=False)


def ふかしのこぶし_reduce_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まもる系揮発性状態を持つ相手への接触技ダメージを1/4にする"""
    if (
        not battle.query.is_contact(ctx)
        or not ctx.move.is_blocked_by_protect
        or not any(ctx.defender.has_volatile(v) for v in _PROTECT_VOLATILES)
    ):
        return HandlerReturn(value=value)
    return HandlerReturn(value=1024)


def ふうりょくでんき_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふうりょくでんき特性: 風技のダメージを受けたときじゅうでん状態になる。"""
    if not ctx.move.has_label("wind"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    battle.volatile_manager.apply(mon, "じゅうでん")
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ふうりょくでんき_on_field_activate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふうりょくでんき特性: 味方のおいかぜ発生時にじゅうでん状態になる。"""
    mon = ctx.source
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    if value.name != "おいかぜ":
        return HandlerReturn(value=value)
    if not battle.get_side(mon).get("おいかぜ").is_active:
        return HandlerReturn(value=value)
    battle.volatile_manager.apply(mon, "じゅうでん")
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ふくがん_boost_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふくがん特性: 使用技の命中率を1.3倍にする（一撃必殺技を除く）。"""
    if not ctx.move.has_label("ohko"):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ふくつのこころ_on_flinch(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふくつのこころ特性: ひるみ状態になったときすばやさが1段階上がる。"""
    volatile_name = value.name if hasattr(value, "name") else value
    if volatile_name != "ひるみ":
        return HandlerReturn(value=value)
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    if battle.modify_stats(mon, {"S": +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ふくつのたて_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふくつのたて特性: 初登場時にぼうぎょが1段階上がる（バトル中1回）。"""
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    battle.add_ability_disabled_reason(mon, "consumed")
    if battle.modify_stats(mon, {"B": +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ふしぎなうろこ_boost_B(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ふしぎなうろこ特性: 状態異常時に物理技への防御補正を1.5倍にする。"""
    if (
        ctx.defender.ailment.is_active
        and common.deals_physical_damage(battle, ctx)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ふしぎなまもり_block_non_effective(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふしぎなまもり特性: 効果抜群でない攻撃技を無効化する。"""
    if not ctx.move.is_attack:
        return HandlerReturn(value=value)
    if common.is_super_effective(battle, ctx):
        return HandlerReturn(value=value)
    return HandlerReturn(value=False, stop_event=True)


def ふとうのけん_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふとうのけん特性: 初登場時にこうげきが1段階上がる（バトル中1回）。"""
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    battle.add_ability_disabled_reason(mon, "consumed")
    if battle.modify_stats(mon, {"A": +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ふゆう_float(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ふゆう特性: 常に浮遊状態として扱う。"""
    return HandlerReturn(value=True)


def フラワーギフト_modify_atk(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """フラワーギフト特性: はれ中にこうげき/とくぼうが1.5倍になる。"""
    if battle.weather.sunny:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def フラワーベール_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """フラワーベール特性: くさタイプの状態異常を防ぐ。"""
    target = ctx.target
    if target is None or "くさ" not in target.types:
        return HandlerReturn(value=value)
    announce_ability_triggered(battle, ctx, value, mon=target)
    return HandlerReturn(value=False, stop_event=True)


def フラワーベール_prevent_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """フラワーベール特性: くさタイプへの能力低下を防ぐ。"""
    target = ctx.target
    if target is None or "くさ" not in target.types:
        return HandlerReturn(value=value)
    filtered = {s: v for s, v in value.items() if v >= 0}
    if filtered != value:
        announce_ability_triggered(battle, ctx, value, mon=target)
    return HandlerReturn(value=filtered)


def ブレインフォース_boost_effective(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ブレインフォース特性: 効果抜群のときダメージを1.25倍"""
    if common.is_super_effective(battle, ctx):
        value = apply_fixed_modifier(value, 5120)
    return HandlerReturn(value=value)


def プレッシャー_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """プレッシャー特性: 登場時にアナウンスを出す。"""
    announce_ability_triggered(battle, ctx, value, mon=ctx.source)
    return HandlerReturn(value=value)


def プレッシャー_extra_pp(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """プレッシャー特性: こちらを対象にした技のPPを1多く消費させる。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_PP_CONSUMED)
            - attacker: 技を使用するポケモン
            - target: 技の対象（プレッシャー所持者）
        value: PP消費量
    """
    return HandlerReturn(value=value + 1)


def ヘドロえき_reverse_drain(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ヘドロえき特性: 吸収技による回復を攻撃者へのダメージに変換する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_HEAL)
            - source: ダメージ源（吸収技の使用者）
            - target: ヘドロえき所持者
        value: 回復量（正の値）
    """
    if ctx.hp_change_reason != "drain":
        return HandlerReturn(value=value)
    hedoro = battle.foe(ctx.target)
    announce_ability_triggered(battle, ctx, value, mon=hedoro)
    return HandlerReturn(value=-value)


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


def へんしょく_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """へんしょく特性: 攻撃技を受けた後、その技のタイプになる。"""
    mon = ctx.defender
    if mon.fainted:
        return HandlerReturn(value=value)
    if ctx.hit_index != ctx.hit_count:
        return HandlerReturn(value=value)
    move_type = ctx.move.type
    if not move_type:
        return HandlerReturn(value=value)
    if move_type in mon.types:
        return HandlerReturn(value=value)
    mon.ability_override_type = move_type
    announce_ability_triggered(battle, ctx, value, mon=mon)
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


def ほうし_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ほうし特性: 接触技を受けたとき30%でどく/まひ/ねむりのいずれかを付与。"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    r = battle.random.random()
    if r < 0.09:
        ailment: AilmentName = "どく"
    elif r < 0.19:
        ailment = "まひ"
    elif r < 0.30:
        ailment = "ねむり"
    else:
        return HandlerReturn(value=value)
    battle.ailment_manager.apply(ctx.attacker, ailment, source=ctx.defender, ctx=ctx)
    return HandlerReturn(value=value)


def ほのおのからだ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ほのおのからだ特性: 直接攻撃を受けた相手を30%でやけどにする。"""
    _apply_contact_counter_ailment(battle, ctx, ailment="やけど", chance=0.3)
    return HandlerReturn(value=value)


def ほろびのボディ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ほろびのボディ特性: 直接攻撃を受けると自分と攻撃者の双方にほろびのうたを付与する。"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    attacker = ctx.attacker
    if attacker is None or attacker.fainted:
        return HandlerReturn(value=value)
    defender = ctx.defender
    triggered = False
    for mon in (defender, attacker):
        if battle.volatile_manager.apply(mon, "ほろびのうた", source=defender):
            triggered = True
    if triggered:
        announce_ability_triggered(battle, ctx, value, mon=defender)
    return HandlerReturn(value=value)


def マイティチェンジ_change_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マイティチェンジ特性: ナイーブフォルムで引っ込むとマイティフォルムへ変化する。"""
    mon = ctx.source
    if mon.name == PALAFIN_ZERO and mon.alive:
        mon.set_form(PALAFIN_HERO)
    return HandlerReturn(value=value)


def まけんき_on_stat_down(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """まけんき特性: 敵から能力を下げられたときこうげきが2段階上昇する。"""
    has_negative = any(v < 0 for v in value.values())
    if (
        has_negative
        and ctx.source != ctx.target
        and battle.modify_stats(ctx.target, {"A": +2}, source=ctx.source)
    ):
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
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
    mon = getattr(ctx, "target", None) or getattr(ctx, "defender", None)
    return _block_item_change(mon, list(PLATE_TO_TYPE.keys()))


def みずがため_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みずがため特性: みずタイプの技でダメージを受けるとぼうぎょが2段階上がる。"""
    if ctx.move.type != "みず":
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"B": +2}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


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


def ミラクルスキン_reduce_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ミラクルスキン特性: 相手の変化技の命中率を50%に固定する。"""
    if ctx.move is None or ctx.move.category != "変化":
        return HandlerReturn(value=value)
    if value is None:
        return HandlerReturn(value=value)
    return HandlerReturn(value=min(value, 50))


def _overwrite_ability_on_contact(battle: Battle,
                                  ctx: EventContext,
                                  *,
                                  new_ability: str) -> bool:
    """直接攻撃でダメージを受けたとき攻撃者の特性を書き換える共通処理。

    Returns:
        書き換えに成功した場合True
    """
    attacker = ctx.attacker
    if attacker is None:
        return False
    if not battle.query.is_contact(ctx):
        return False
    if attacker.ability.has_flag("uncopyable"):
        return False
    if attacker.ability.name == new_ability:
        return False
    battle.change_ability(attacker, new_ability)
    return True


def ミイラ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ミイラ特性: 直接攻撃でダメージを受けたとき攻撃者の特性をミイラにする。"""
    if _overwrite_ability_on_contact(battle, ctx, new_ability="ミイラ"):
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
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
        changed = battle.modify_stats(mon, {raised_stat: +2}, source=mon, reason="ムラっけ") or changed

    down_candidates = [stat for stat in stats if mon.rank[stat] > -6 and stat != raised_stat]
    if down_candidates:
        lowered_stat = battle.random.choice(down_candidates)
        changed = battle.modify_stats(mon, {lowered_stat: -1}, source=mon, reason="ムラっけ") or changed

    if changed:
        announce_ability_triggered(battle, ctx, value, mon=mon)

    return HandlerReturn(value=value)


def メガソーラー_activate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メガソーラー特性: 技使用前に天候を「はれ」に直接変更する（副作用なし）。"""
    mon = ctx.attacker
    wm = battle.weather_manager
    original_name = wm.current_name
    original_hare_count = wm.fields["はれ"].count
    _メガソーラー_saved[id(mon)] = (original_name, original_hare_count)
    if original_name != "はれ":
        # 元天候のハンドラを解除してから「はれ」のハンドラを登録する
        if wm.fields[original_name].is_active:
            for player in wm.fields[original_name].owners:
                wm.fields[original_name].unregister_handlers(battle.events, player)
        wm.fields["はれ"].count = 1
        for player in wm.fields["はれ"].owners:
            wm.fields["はれ"].register_handlers(battle.events, player)
    wm.current_name = "はれ"
    mon.ability.state = "active"
    return HandlerReturn(value=value)


def メガソーラー_deactivate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メガソーラー特性: 技使用後に天候を元に戻す。"""
    mon = ctx.attacker
    if mon.ability.state != "active":
        return HandlerReturn(value=value)
    wm = battle.weather_manager
    saved = _メガソーラー_saved.pop(id(mon), None)
    if saved is not None:
        original_name, original_hare_count = saved
        if original_name != "はれ":
            # 「はれ」のハンドラを解除して元天候のハンドラを復元する
            for player in wm.fields["はれ"].owners:
                wm.fields["はれ"].unregister_handlers(battle.events, player)
            wm.fields["はれ"].count = original_hare_count
            if wm.fields[original_name].is_active:
                for player in wm.fields[original_name].owners:
                    wm.fields[original_name].register_handlers(battle.events, player)
        wm.current_name = original_name
    mon.ability.state = ""
    return HandlerReturn(value=value)


def メガソーラー_force_weather_enabled(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """メガソーラー特性: 攻撃中はノーてんき等による天候無効化を無視して「はれ」を有効にする。"""
    if ctx.source.ability.state == "active":
        return HandlerReturn(value=True, stop_event=True)
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


def メロメロボディ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メロメロボディ特性: 直接攻撃を受けたとき30%の確率で攻撃者をメロメロにする。"""
    if battle.query.is_contact(ctx) and battle.random.random() < 0.3:
        battle.volatile_manager.apply(
            ctx.attacker, "メロメロ", source=ctx.defender, ctx=ctx,
        )
    return HandlerReturn(value=value)


def ものひろい_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ものひろい特性: ターン終了時に自分がアイテムを持っていなければ相手が消費したアイテムを拾う。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_TURN_END)
            - source: ものひろい所持者
        value: イベント値（未使用）
    """
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    if mon.has_item():
        return HandlerReturn(value=value)
    foe = battle.foe(mon)
    item_name = foe.last_lost_item_name
    if not item_name:
        return HandlerReturn(value=value)
    if battle.gain_item(mon, item_name):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


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


def もらいび_arm_fire_boost(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技使用時に強化適用予約。"""
    mon = getattr(ctx, "source", None) or getattr(ctx, "attacker", None)
    if (
        ctx.move.type == "ほのお"
        and mon is not None
        and mon.ability.state == "charged"
    ):
        mon.ability.state = "active"
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
    mon = ctx.attacker
    state = mon.ability.state
    if state == "active":
        mon.ability.state = "idle"
    return HandlerReturn(value=value)


def ゆうばく_on_ko(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ゆうばく特性: 直接攻撃でひんしになったとき攻撃者に最大HPの1/4ダメージを与える。"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    attacker = ctx.attacker
    if attacker is None or attacker.fainted:
        return HandlerReturn(value=value)
    damage = max(1, attacker.max_hp // 4)
    battle.modify_hp(attacker, -damage, reason="ability")
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
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


def よちむ_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """よちむ特性: 登場時に相手が覚えている技のうち最高威力の技を1つ公開する。

    変化技など威力がない技は威力0として扱う。
    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_SWITCH_IN)
            - source: よちむ所持者
        value: イベント値（未使用）
    """
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    foe = battle.foe(mon)
    if not foe.moves:
        return HandlerReturn(value=value)

    # よちむ仕様: 変化技=0、その他は data.power を使用
    def _move_power(move) -> int:
        if move.data.power is None:
            return 0
        return move.data.power

    max_power = max(_move_power(m) for m in foe.moves)
    candidates = [m for m in foe.moves if _move_power(m) == max_power]
    chosen = battle.random.choice(candidates)
    chosen.revealed = True
    announce_ability_triggered(battle, ctx, value, mon=mon)
    battle.add_event_log(
        mon, LogCode.TEXT_LOG,
        payload={"text": f"{foe.name}の{chosen.name}を読み取った！"}
    )
    return HandlerReturn(value=value)


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


def リミットシールド_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リミットシールド特性: 登場時にHP1/2超ならりゅうせいのすがたへフォルムチェンジする。"""
    mon = ctx.source
    if mon.name != METEONO_CORE:
        return HandlerReturn(value=value)
    if mon.hp * 2 > mon.max_hp:
        mon.set_form(METEONO_METEOR)
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def リミットシールド_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リミットシールド特性: ターン終了時にHPに応じてフォルムを切り替える。"""
    mon = ctx.source
    if mon.hp * 2 > mon.max_hp:
        if mon.set_form(METEONO_METEOR):
            announce_ability_triggered(battle, ctx, value, mon=mon)
    else:
        if mon.set_form(METEONO_CORE):
            announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def リミットシールド_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リミットシールド特性: りゅうせいのすがた時に全状態異常を無効化する。"""
    if ctx.target.name != METEONO_METEOR:
        return HandlerReturn(value=value)
    return prevent_ailment(battle, ctx, value)


def リミットシールド_on_switch_out(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リミットシールド特性: 交代時にりゅうせいのすがたからコアの姿へ戻す。"""
    mon = ctx.source
    if mon.name == METEONO_METEOR:
        mon.set_form(METEONO_CORE)
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


def わたげ_on_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """わたげ特性: 攻撃を受けたとき攻撃者のすばやさを1段階下げる。"""
    mon = ctx.defender
    attacker = ctx.attacker
    if attacker is None:
        return HandlerReturn(value=value)
    if battle.modify_stats(attacker, {"S": -1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
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
