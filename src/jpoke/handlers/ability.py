"""特性ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext
    from jpoke.model import Pokemon, Move

from jpoke.types import RoleSpec, Type, Stat, WeatherName, TerrainName, \
    AilmentName, VolatileName, ItemDisabledReason, MoveFlag, AbilityName, ItemName
from jpoke.data.signature_items import PLATE_TO_TYPE, MEMORY_TO_TYPE
from jpoke.data import TYPE_MODIFIER
from jpoke.utils.math import apply_fixed_modifier
from jpoke.enums import LogCode, Interrupt
from jpoke.core import HandlerReturn, Handler
from jpoke.core.event_logger import (
    AbilityPayload, AilmentPayload, VolatilePayload, FailureLogPayload,
    FieldPayload, TextPayload,
)

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
ZYGARDE_50 = "ジガルデ(50%)"
ZYGARDE_10 = "ジガルデ(10%)"
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
CALYREX_ICE = "バドレックス(はくば)"
CALYREX_SHADOW = "バドレックス(こくば)"

WEATHER_TO_CASTFORM: dict[str, str] = {
    "はれ": CASTFORM_SUNNY,
    "おおひでり": CASTFORM_SUNNY,
    "あめ": CASTFORM_RAINY,
    "おおあめ": CASTFORM_RAINY,
    "ゆき": CASTFORM_SNOWY,
    "あられ": CASTFORM_SNOWY,
}

_OGERPON_STAT: dict[str, Stat] = {
    "オーガポン(みどり)": "spe",
    "オーガポン(いど)": "spd",
    "オーガポン(かまど)": "atk",
    "オーガポン(いしずえ)": "def",
}

_PROTECT_VOLATILES: frozenset[str] = frozenset({
    "まもる", "トーチカ", "キングシールド", "スレッドトラップ", "かえんのまもり",
})

_EFFECT_SPORE_AILMENTS: list[tuple[float, AilmentName]] = [
    (0.09, "どく"),
    (0.19, "まひ"),
    (0.30, "ねむり"),
]

# メガソーラー: ON_BEGIN_MOVE で保存した天候状態（current_name, はれのcount）を ON_END_MOVE で復元するための辞書
_メガソーラー_saved: dict[int, tuple[str, int]] = {}

class AbilityHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 once: bool = False,
                 ignored_disable_reasons: frozenset[str] = frozenset()) -> None:
        super().__init__(
            func=func,
            source="ability",
            subject_spec=subject_spec,
            priority=priority,
            once=once,
            ignored_disable_reasons=ignored_disable_reasons,
        )

def announce_ability_triggered(battle: Battle,
                               ctx: EventContext | AttackContext,
                               value: Any) -> HandlerReturn:
    """汎用: 特性発動ログを記録する

    ctx.source または ctx.attacker を発動ポケモンとみなす。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_SWITCH_IN)
            - source: 登場したポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 変更なし
    """
    mon = getattr(ctx, "source", None) or getattr(ctx, "attacker", None)
    _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)

def _announce_ability_triggered(battle: Battle, mon: Pokemon) -> None:
    """特性発動ログを記録する。"""
    mon.ability.revealed = True
    battle.add_event_log(
        mon,
        LogCode.ABILITY_TRIGGERED,
        payload=AbilityPayload(ability=mon.ability.name)
    )

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
                                   ctx: AttackContext,
                                   value: Any,
                                   *,
                                   ailment: AilmentName,
                                   chance: float) -> HandlerReturn:
    """接触被弾時カウンターの状態異常付与を試行する。"""
    assert ctx.defender is not None
    if (
        battle.query.is_contact_reaction(ctx)
        and battle.random.random() < chance
    ):
        battle.ailment_manager.apply(
            ctx.attacker, ailment, source=ctx.defender, ctx=ctx,
        )
        _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=value)

def _apply_contact_counter_chip(battle: Battle,
                                ctx: AttackContext,
                                value: Any,
                                *,
                                ratio: float) -> HandlerReturn:
    """接触被弾時カウンターの固定割合ダメージを適用する。"""
    assert ctx.defender is not None
    if battle.query.is_contact_reaction(ctx):
        v = battle.modify_hp(ctx.attacker, r=-ratio, reason="")
        if v:
            # ダメおし判定用: さめはだ/てつのトゲによるダメージも「そのターンに
            # 攻撃を受けた」扱いにする（一次情報: docs/wiki/moves/ダメおし.html 技の仕様節）。
            ctx.attacker.hits_taken += 1
            _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=value)

def _trigger_emergency_switch(battle: Battle, mon: Pokemon):
    """緊急交代を発動する。"""
    player = battle.get_player(mon)
    if battle.query.can_switch(player):
        battle.player_states[player].interrupt = Interrupt.EMERGENCY
        _announce_ability_triggered(battle, mon=mon)

def _apply_type_absorb(battle: Battle,
                       ctx: AttackContext,
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

    _announce_ability_triggered(battle, defender)
    battle.add_event_log(
        ctx.attacker,
        LogCode.MOVE_IMMUNED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason=defender.ability.base_name)
    )

    if heal_ratio > 0:
        battle.modify_hp(defender, r=heal_ratio)
    if stats is not None:
        battle.modify_stats(defender, stats, source=ctx.attacker)

    return HandlerReturn(value=False, stop_event=True)

def _modify_by_move_condition(move: Move,
                              value: int,
                              *,
                              modifier: int,
                              move_type: Type | None = None,
                              move_flag: MoveFlag | None = None) -> HandlerReturn:
    """技のタイプ/フラグ条件を満たすときのみ固定倍率補正を適用する。"""
    if (
        (move_type is not None and move.type == move_type)
        or (move_flag is not None and move.has_flag(move_flag))
    ):
        value = apply_fixed_modifier(value, modifier)
    return HandlerReturn(value=value)

def _activate_weather(battle: Battle,
                      mon: Pokemon | None,
                      value: Any,
                      *,
                      weather: WeatherName,
                      count: int) -> HandlerReturn:
    """天候を変更する"""
    if mon and battle.weather_manager.apply(weather, count, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)

def _deactivate_strong_weather(battle: Battle,
                               ctx: EventContext,
                               value: Any,
                               *,
                               weather: WeatherName) -> HandlerReturn:
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

def _activate_terrain(battle: Battle,
                      mon: Pokemon | None,
                      value: Any,
                      *,
                      terrain: TerrainName,
                      count: int) -> HandlerReturn:
    """地形を変更する"""
    if mon and battle.terrain_manager.apply(terrain, count, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)

def _block_stat_drop_by_foe(value: dict, ctx: EventContext, stat: Stat | None = None) -> dict:
    """相手由来のランク低下を除去する。stat=Noneなら全能力が対象。"""
    if ctx.source is not None and ctx.source != ctx.target:
        if stat is None:
            value = {s: v for s, v in value.items() if v >= 0}
        else:
            value = {s: v for s, v in value.items() if s != stat or v >= 0}
    return value

def _ignore_sandstorm_damage(_battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すなあらしのダメージを無効化する。"""
    if ctx.hp_change_reason == "sandstorm":
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)

def _prevent_ailment(battle: Battle,
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
        _announce_ability_triggered(battle, ctx.target)
        battle.add_event_log(
            ctx.target,
            LogCode.AILMENT_PREVENTED,
            payload=AilmentPayload(ailment=value, display_reason=ctx.target.ability.name)
        )
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)

def _prevent_volatile(battle: Battle,
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
        _announce_ability_triggered(battle, ctx.target)
        battle.add_event_log(
            ctx.target,
            LogCode.VOLATILE_PREVENTED,
            payload=VolatilePayload(volatile=value, display_reason=ctx.target.ability.name)
        )
        return HandlerReturn(value=None, stop_event=True)
    return HandlerReturn(value=value)

def _cure_ailment_on_enable(battle: Battle,
                            ctx: EventContext,
                            *,
                            blocked_ailments: list[AilmentName]) -> HandlerReturn:
    """特性が有効化された時点ですでに無効化対象の状態異常なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合や、
    なやみのタネ等で特性が書き換わった場合などに発動する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_ABILITY_ENABLED)
            - source: 特性が有効化されたポケモン
        blocked_ailments: この特性が防ぐ状態異常のリスト
    """
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=None)
    if mon.ailment.name in blocked_ailments and battle.ailment_manager.remove(mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=None)

def _cure_volatile_on_enable(battle: Battle,
                             ctx: EventContext,
                             *,
                             blocked_volatiles: list[VolatileName]) -> HandlerReturn:
    """特性が有効化された時点ですでに無効化対象の揮発性状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_ABILITY_ENABLED)
            - source: 特性が有効化されたポケモン
        blocked_volatiles: この特性が防ぐ揮発性状態のリスト
    """
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=None)
    for volatile_name in blocked_volatiles:
        if mon.has_volatile(volatile_name) and battle.volatile_manager.remove(mon, volatile_name):
            _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=None)

def ARシステム_apply_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ARシステム特性: 登場時にメモリに合わせてタイプを変更する。"""
    _apply_multitype(ctx.source, MEMORY_TO_TYPE)
    return HandlerReturn(value=value)

def ARシステム_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ARシステム特性: メモリの奪取・交換を防ぐ。

    自分の持つメモリの奪取・交換を防ぐだけでなく、トリック/すりかえ等の
    道具交換では相手がメモリを持っている場合も交換自体が失敗する。
    """
    mon = getattr(ctx, "target", None) or getattr(ctx, "defender", None)
    if getattr(ctx, "is_exchange", False) and battle.foe(mon).item.name in MEMORY_TO_TYPE:
        return HandlerReturn(value=False, stop_event=True)
    return _block_item_change(mon, list(MEMORY_TO_TYPE.keys()))


def アイスフェイス_block_physical(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """アイスフェイス特性: 物理技のダメージを0にしてナイスフェイスにフォルムチェンジする。

    実際のダメージは0になるが、ダメージを肩代わりしているため「攻撃を無効化した」
    扱いにはならない（ばけのかわと同様、ダメおし威力2倍の対象）。
    """
    if ctx.move.category != "physical" or ctx.defender.name != EISCUE_ICE:
        return HandlerReturn(value=value)
    ctx.defender.set_form(EISCUE_NICE)
    ctx.defender.hits_taken += 1
    _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=0)


def アイスフェイス_restore_on_snow(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アイスフェイス特性: ゆきが発生したときナイスフェイスからアイスフェイスに戻る。"""
    mon = ctx.source
    if mon.name != EISCUE_NICE or battle.weather.name != "ゆき":
        return HandlerReturn(value=value)
    mon.set_form(EISCUE_ICE)
    _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def アイスフェイス_restore_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アイスフェイス特性: ゆき状態の場に登場したときアイスフェイスに戻る。"""
    mon = ctx.source
    if mon.name != EISCUE_NICE or battle.weather.name != "ゆき":
        return HandlerReturn(value=value)
    mon.set_form(EISCUE_ICE)
    _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def アイスボディ_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アイスボディ特性: ゆき中にターン終了時に最大HPの1/16を回復する。"""
    mon = ctx.source
    if (
        battle.weather.name == "ゆき"
        and battle.modify_hp(mon, r=1/16)
    ):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


# 元々ひるみの追加効果を持つ技（アイアンヘッド等）。あくしゅうの効果は重複しない。
# handlers/item.py の _INNATE_FLINCH_MOVES（おうじゃのしるし・するどいキバ）と同一。
_INNATE_FLINCH_MOVES: frozenset[str] = frozenset({
    "3ぼんのや", "アイアンヘッド", "あくのはどう", "いびき", "いわなだれ", "エアスラッシュ",
    "おどろかす", "かみつく", "かみなりのキバ", "こおりのキバ", "ゴッドバード", "しねんのずつき",
    "じんつうりき", "ずつき", "たきのぼり", "たつまき", "つららおとし",
    "ドラゴンダイブ", "ねこだまし", "はやてがえし",
    "ひょうざんおろし", "びりびりちくちく", "ふみつけ",
    "ほのおのキバ", "もえあがるいかり",
})


def あくしゅう_maybe_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あくしゅう特性: 攻撃技を命中させたとき10%の確率でひるみを付与する。

    元々ひるみの追加効果を持つ技（アイアンヘッド等）や一撃必殺技には効果が無い。
    特性りんぷん・アイテムおんみつマントで防がれるため、確率は
    resolve_secondary_chance を経由して解決する。
    """
    defender = ctx.defender
    if (
        defender is None
        or ctx.move.has_flag("ohko")
        or ctx.move.name in _INNATE_FLINCH_MOVES
    ):
        return HandlerReturn(value=value)
    chance = battle.resolve_secondary_chance(ctx, 0.1)
    if battle.random.random() < chance:
        battle.volatile_manager.apply(defender, "ひるみ", source=ctx.attacker)
    return HandlerReturn(value=value)


def あついしぼう_reduce_fire_ice(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """あついしぼう特性: 炎/氷技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type in {"ほのお", "こおり"}:
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def あとだし_delay_move_order(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """あとだし特性: 同一優先度の行動の中で最後に行動する（後攻ティア -1）。"""
    return HandlerReturn(value=value - 1)


def アナライズ_boost_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """アナライズ特性: 行動が後になったターンの技威力を1.3倍にする。

    こんらんによる自傷行動（内部技"_こんらん"）の威力は上がらない。
    """
    if ctx.move.name == "_こんらん":
        return HandlerReturn(value=value)

    # 条件分岐が複雑なのでコメントを追加する
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
    """あめうけざら特性: あめ/おおあめ中にターン終了時に最大HPの1/16を回復する。
    ばんのうがさを持つ場合は雨の恩恵を受けない。
    """
    mon = ctx.source
    if not battle.weather_for(mon).rainy:
        return HandlerReturn(value=value)

    if battle.modify_hp(mon, r=1/16):
        _announce_ability_triggered(battle, mon)

    return HandlerReturn(value=value)


def あめふらし_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_weather(battle, ctx.source, value, weather="あめ", count=5)


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
    source = ctx.source
    result = (
        source is not None
        and not source.has_type("ゴースト")
        and not battle.query.is_floating(source)
    )
    return HandlerReturn(value=result)


def アロマベール_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_volatile(battle, ctx, value, blocked_volatiles=[
        "アンコール", "いちゃもん", "かいふくふうじ", "かなしばり", "ちょうはつ", "メロメロ"
    ])


def いかく_lower_foe_atk(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いかく特性: 登場時に相手のこうげきを1段階下げる。みがわり状態の相手には無効。"""
    source = ctx.source
    target = battle.foe(source)
    _announce_ability_triggered(battle, source)
    if target.has_volatile("みがわり"):
        return HandlerReturn(value=value)
    battle.modify_stats(target, {"atk": -1}, source=source, reason="いかく")
    return HandlerReturn(value=value)


def いかりのこうら_boost_on_half_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いかりのこうら特性: HPが半分以下になったときA・C・S↑1、B・D↓1。

    ひんしになった場合は発動しない（ON_DAMAGE_HIT はKO後にも発火するため明示的に除外する）。
    連続攻撃技はすべてのヒットが終わった後（攻撃側がひんしになって中断した場合はその時点）に、
    1発目を受ける前のHPを基準にまとめて判定する（かいがらのすずの合計ダメージ集計と同じ idiom）。
    """
    mon = ctx.defender
    if not mon.alive:
        return HandlerReturn(value=value)

    if ctx.hit_index == 1:
        ctx._angershell_hp_before = mon.hp + value

    is_last_hit = ctx.hit_index == ctx.hit_count or ctx.attacker.fainted
    if not is_last_hit:
        return HandlerReturn(value=value)

    hp_before = ctx._angershell_hp_before
    hp_after = mon.hp
    if not _crossed_half_hp(hp_before, hp_after, mon.max_hp):
        return HandlerReturn(value=value)
    battle.modify_stats(mon, {"def": -1, "spd": -1}, source=ctx.attacker)
    if battle.modify_stats(mon, {"atk": +1, "spa": +1, "spe": +1}, source=ctx.attacker):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def いかりのつぼ_max_atk_on_crit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いかりのつぼ特性: 急所に被弾したときこうげきを最大まで上げる。"""
    if not battle.move_executor.critical:
        return HandlerReturn(value=value)
    mon = ctx.defender
    diff = 6 - mon.rank["atk"]
    if diff > 0 and battle.modify_stats(mon, {"atk": diff}, source=ctx.attacker):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def いしあたま_ignore_recoil(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """いしあたま特性: 反動ダメージを受けない。"""
    if ctx.hp_change_reason == "recoil":
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def いたずらごころ_blocked_by_dark(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """いたずらごころ特性: 優先度が上がった変化技はあくタイプ相手に無効化される。"""
    if (
        ctx.move.category == "status"
        and ctx.move.target == "foe"
        and ctx.defender.has_type("あく")
    ):
        battle.add_event_log(
            ctx.attacker,
            LogCode.MOVE_IMMUNED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="いたずらごころ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def いたずらごころ_modify_move_priority(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """いたずらごころ特性: 変化技の優先度を+1する。"""
    if ctx.move.category == "status":
        value += 1
    return HandlerReturn(value=value)


def いろめがね_boost_ineffective(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """いろめがね特性: いまひとつの技の最終ダメージ補正を2倍にする。"""
    if battle.query.is_not_very_effective(ctx):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def いわはこび_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """いわはこび特性: いわ技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(ctx.move, value, modifier=6144, move_type="いわ")


def _set_cramorant_form_by_hp(battle: Battle, mon: Pokemon) -> None:
    """うのミサイル特性: HP に応じたフォルムへ変化させる（うのみ/まるのみ）。"""
    next_form = CRAMORANT_GULPING if mon.hp * 2 > mon.max_hp else CRAMORANT_GORGING
    mon.set_form(next_form)
    _announce_ability_triggered(battle, mon)


def うのミサイル_load_prey(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うのミサイル特性: なみのり成功後に HP に応じてフォルムチェンジする。

    ダイビングは溜めターン（1ターン目）に成功した時点でフォルムチェンジが
    確定し、2ターン目の攻撃がまもる等で無効化されても維持されるため、
    `うのミサイル_load_prey_on_charge`（Event.ON_MOVE_CHARGE）で別途処理する。
    """
    mon = ctx.attacker
    if (
        mon.name != CRAMORANT_NORMAL
        or ctx.move.name != "なみのり"
        or not battle.move_executor.move_applied
    ):
        return HandlerReturn(value=value)

    _set_cramorant_form_by_hp(battle, mon)
    return HandlerReturn(value=value)


def うのミサイル_load_prey_on_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うのミサイル特性: ダイビングの溜めターン（1ターン目）に成功すると HP に応じてフォルムチェンジする。

    技自身の揮発状態「ダイビング」付与ハンドラ（Event.ON_MOVE_CHARGE, priority=100）
    より先に判定する必要があるため priority=90 とし、揮発状態がまだ付与されて
    いない（＝1ターン目）ことを条件にする。パワフルハーブで1ターンで繰り出した
    場合も、揮発状態が付与される前にこのハンドラが実行されるためフォルム
    チェンジは成立する。
    """
    mon = ctx.attacker
    if (
        mon.name != CRAMORANT_NORMAL
        or ctx.move.name != "ダイビング"
        or mon.has_volatile("ダイビング")
    ):
        return HandlerReturn(value=value)

    _set_cramorant_form_by_hp(battle, mon)
    return HandlerReturn(value=value)


def うのミサイル_revert_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """うのミサイル特性: 交代時に通常のすがたに戻す。"""
    mon = ctx.source
    if mon.name in (CRAMORANT_GULPING, CRAMORANT_GORGING):
        mon.set_form(CRAMORANT_NORMAL)
    return HandlerReturn(value=value)


def うのミサイル_spit_out_prey(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うのミサイル特性: 咥えたすがたのときダメージを受けると獲物を吐き出して反撃する。"""
    mon = ctx.defender
    form = mon.name
    if (
        form not in (CRAMORANT_GULPING, CRAMORANT_GORGING)
        or mon.has_volatile("そらをとぶ")
        or mon.has_volatile("あなをほる")
        or mon.has_volatile("ダイビング")
        or mon.has_volatile("シャドーダイブ")
        or ctx.attacker.fainted
    ):
        return HandlerReturn(value=value)

    mon.set_form(CRAMORANT_NORMAL)
    _announce_ability_triggered(battle, mon)

    damage = max(1, ctx.attacker.max_hp // 4)
    battle.modify_hp(ctx.attacker, -damage, source=mon, reason="ability")

    if form == CRAMORANT_GULPING:
        battle.modify_stats(ctx.attacker, {"def": -1}, source=mon)
    else:
        battle.ailment_manager.apply(ctx.attacker, "まひ", source=mon, ctx=ctx)

    return HandlerReturn(value=value)


def うるおいボイス_modify_move_type(battle: Battle, ctx: AttackContext, value: Type) -> HandlerReturn:
    """うるおいボイス特性: 音技を（元のタイプに関わらず）みずタイプに変換する。"""
    if ctx.move.has_flag("sound"):
        return HandlerReturn(value="みず")
    return HandlerReturn(value=value)


def うるおいボディ_cure_ailment_in_rain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """うるおいボディ特性: あめ/おおあめ中にターン終了時に状態異常を回復する。
    ばんのうがさを持つ場合は雨の恩恵を受けない。
    """
    mon = ctx.source
    if not battle.weather_for(mon).rainy:
        return HandlerReturn(value=value)
    if not mon.ailment.is_active:
        return HandlerReturn(value=value)
    result = HandlerReturn(value=battle.ailment_manager.remove(mon))
    if result.value:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def エアロック_check_weather_enabled(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """エアロック特性: 天候効果を無効化する。"""
    return HandlerReturn(value=False, stop_event=True)


def エレキメイカー_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_terrain(battle, ctx.source, value, terrain="エレキフィールド", count=5)


def えんかく_nullify_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """えんかく特性: 自分が使う技の接触判定を無効化する。"""
    return HandlerReturn(value=False, stop_event=True)


# 自分含む全員が対象の技（使用者自身にも効果が及ぶ技）は、技全体を無効化すると
# 使用者自身への効果まで防いでしまうため、通常の全体無効化の対象から除外する。
# 対象ポケモンごとの免疫判定は各技のハンドラ側（handlers/move_status.py の
# _blocked_by_ougon_no_karada）で行う（docs/spec/abilities/おうごんのからだ.md
# 「自分含む全員が対象の技」）。
_OUGON_NO_KARADA_EXCLUDED_MOVES: frozenset[str] = frozenset({"ほろびのうた"})


def おうごんのからだ_block_status_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おうごんのからだ特性: 他のポケモンからの変化技を無効化する。"""
    if (
        ctx.move.category == "status"
        and ctx.move.target == "foe"
        and ctx.move.name not in _OUGON_NO_KARADA_EXCLUDED_MOVES
    ):
        _announce_ability_triggered(battle, ctx.defender)
        battle.add_event_log(
            ctx.attacker,
            LogCode.MOVE_IMMUNED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="おうごんのからだ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おみとおし_reveal_foe_item(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おみとおし特性: 場に出たとき相手のアイテムを公開する。"""
    mon = ctx.source
    foe = battle.foe(mon)
    if not foe.has_item():
        return HandlerReturn(value=value)
    foe.item.revealed = True
    _announce_ability_triggered(battle, mon)
    battle.add_event_log(
        mon,
        LogCode.TEXT_LOG,
        payload=TextPayload(text=f"{mon.name}は{foe.name}の{foe.item.base_name}をお見通しだ！")
    )
    return HandlerReturn(value=value)


def おもかげやどし_boost_stat(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おもかげやどし特性: 場に出たとき（かこの特性に変化したとき）フォルムに対応する能力が1段階上がる。

    場に出るたびに1回しか発動しない（かがくへんかガスの発動・解除が起きても再発動しない）。
    """
    mon = ctx.source
    stat = _OGERPON_STAT.get(mon.name)
    if stat is None:
        return HandlerReturn(value=value)
    if mon.ability.activated_since_switch_in:
        return HandlerReturn(value=value)
    mon.ability.activated_since_switch_in = True
    _announce_ability_triggered(battle, mon)
    battle.modify_stats(mon, {stat: +1}, source=mon)
    return HandlerReturn(value=value)


def おやこあい_modify_hit_count(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """おやこあい特性: 単発攻撃技を2ヒット化する。

    がむしゃらはHPの変動有無に関わらずいかなる状況でも連続攻撃にならないため対象外とする。
    ころがる/アイスボールも連続攻撃にならない（数ターン継続する強制行動技のため）。
    """
    if ctx.move.name in ("がむしゃら", "ころがる", "アイスボール"):
        return HandlerReturn(value=value)
    if ctx.move.is_attack and ctx.move.max_hits == 1:
        value = 2
    return HandlerReturn(value=value)


def おやこあい_reduce_second_damage(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """おやこあい特性: 2ヒット目のダメージを1/4に減衰させる（最低1ダメージ保証）。"""
    if ctx.hit_index == 2:
        value = max(1, value // 4)
    return HandlerReturn(value=value)


def おわりのだいち_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_weather(battle, ctx.source, value, weather="おおひでり", count=1)


def おわりのだいち_deactivate_strong_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _deactivate_strong_weather(battle, ctx, value, weather="おおひでり")


def かいりきバサミ_block_A_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """かいりきバサミ特性: 相手によるこうげきランク低下を無効化する。"""
    value = _block_stat_drop_by_foe(value, ctx, "atk")
    return HandlerReturn(value=value)


def かがくへんかガス_disable_foe_ability(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    foe = battle.foe(mon)
    _announce_ability_triggered(battle, mon)
    if not foe.ability.has_flag("gas_proof"):
        battle.add_ability_disabled_reason(foe, "かがくへんかガス")
    return HandlerReturn(value=value)


def かがくへんかガス_disable_new_foe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
    source = ctx.source
    result = (
        source is not None
        and not source.has_type("ゴースト")
        and source.ability.name != "かげふみ"
    )
    return HandlerReturn(value=result)


def かぜのり_absorb_wind(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """かぜのり特性: 風の技を無効化しこうげきを1段階上げる。"""
    if (
        ctx.move.target != "foe"
        or not ctx.move.has_flag("wind")
    ):
        return HandlerReturn(value=value)

    defender = ctx.defender
    _announce_ability_triggered(battle, defender)
    battle.add_event_log(
        ctx.attacker,
        LogCode.MOVE_IMMUNED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason=defender.ability.base_name)
    )
    battle.modify_stats(defender, {"atk": 1}, source=ctx.attacker)
    return HandlerReturn(value=False, stop_event=True)


def かぜのり_boost_atk_in_tailwind(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かぜのり特性: おいかぜ状態の場に出たときこうげきを1段階上げる。"""
    mon = ctx.source
    side = battle.get_side(mon)
    if not side.get("おいかぜ").is_active:
        return HandlerReturn(value=value)

    changed = battle.modify_stats(mon, {"atk": 1}, source=mon)
    if changed:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def かぜのり_boost_atk_on_tailwind_start(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かぜのり特性: 味方の場においかぜが発生したときこうげきを1段階上げる。"""
    mon = ctx.source
    if (
        mon is None
        or not battle.is_active(mon)
        or value.name != "おいかぜ"
        or not battle.get_side(mon).get("おいかぜ").is_active
    ):
        return HandlerReturn(value=value)
    changed = battle.modify_stats(mon, {"atk": 1}, source=mon)
    if changed:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def かそく_boost_speed(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かそく特性: 場に出てから一度でも行動を選択していればターン終了時に素早さを1段階上げる。

    状態異常等でPPを消費せず技が失敗した場合も「行動を選択した」ことになるため、
    技の成否を問わない acted_since_switch_in を判定に用いる（executed_move は
    技が実際に実行された場合のみ True になるため使用しない）。
    """
    mon = ctx.source
    if (
        mon.acted_since_switch_in
        and battle.modify_stats(mon, {"spe": +1}, source=mon)
    ):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def かたいツメ_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """かたいツメ特性: 直接攻撃の威力を1.3倍にする。"""
    if battle.query.is_contact(ctx):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def かたやぶり_disable_foe_ability(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    mon = ctx.defender
    if mon.ability.has_flag("mold_breaker_ignorable"):
        battle.add_ability_disabled_reason(mon, "かたやぶり")
    return HandlerReturn(value=value)


def かたやぶり_restore_foe_ability(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    battle.remove_ability_disabled_reason(ctx.defender, "かたやぶり")
    return HandlerReturn(value=value)


def かちき_boost_spa_on_stat_drop(battle: Battle, ctx: EventContext, value: dict[Stat, int]) -> HandlerReturn:
    """かちき特性: 能力が下がると特攻が2段階上昇する。下がった能力の数だけ発動する。

    くすぐる・おきみやげのように一度に複数の能力を下げる技を受けた場合、
    下がった能力の数だけかちきが発動する（一次情報: docs/wiki/abilities/かちき.html
    特性の仕様節）。

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
    # 下がった能力の数を数える
    negative_count = sum(1 for v in value.values() if v < 0)
    # 自分以外が原因で能力が下がった場合、下がった数だけ特攻を2段階上昇
    if negative_count and ctx.source != ctx.target:
        for _ in range(negative_count):
            if battle.modify_stats(ctx.target, {"spa": +2}, source=ctx.source):
                _announce_ability_triggered(battle, ctx.target)
    return HandlerReturn(value=value)


def カブトアーマー_block_crit(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """カブトアーマー特性: 防御側の急所ランクを無効化する。"""
    return HandlerReturn(value=0, stop_event=True)


def かるわざ_activate_on_item_lost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かるわざ特性: アイテムを失った瞬間に発動状態へ遷移する。

    かがくへんかガス等で無効化されている間はこのハンドラ自体が発火しないため、
    無効化中にアイテムを失っても発動状態へは移行しない
    （無効化中に失ったアイテムはガス解除後もかるわざを発動させない仕様に対応）。
    """
    mon = ctx.source
    if mon.ability.state == "idle":
        mon.ability.state = "active"
    return HandlerReturn(value=value)


def かるわざ_init_state(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かるわざ特性: 入場時、または特性が有効化されたときに発動可否の初期状態を記録する。

    交代での再入場時は必ず状態がリセット済み（state == ""）なので初期化される。
    かがくへんかガスの解除等、同一の特性インスタンスが無効化から復帰しただけの
    場合は既に発動可否が確定しているため、状態を保持し再判定しない
    （発動中だった場合はガス解除後も発動状態が継続する仕様に対応）。
    """
    mon = ctx.source
    if mon.ability.state == "":
        # "idle": 入場時（有効化時）にアイテムあり（消失で発動可能）
        # "inactive": 入場時（有効化時）にアイテムなし（この在場中は発動しない）
        mon.ability.state = "idle" if mon.has_item() else "inactive"
    return HandlerReturn(value=value)


def かるわざ_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """かるわざ特性: 発動状態のとき素早さを2倍にする。アイテムを再取得したら解除する。"""
    mon = ctx.source
    if mon.ability.state != "active":
        return HandlerReturn(value=value)

    # 発動中にアイテムを再取得したら解除（再消費で再発動できる状態へ戻す）。
    if mon.has_item():
        mon.ability.state = "idle"
        return HandlerReturn(value=value)

    value *= 2
    return HandlerReturn(value=value)


def かんそうはだ_absorb_water(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """かんそうはだ特性: みず技を無効化し、HPが減っていれば最大HPの1/4を回復する。"""
    return _apply_type_absorb(battle, ctx, value, move_type="みず", heal_ratio=1/4)


def かんそうはだ_change_hp_by_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かんそうはだ特性: 天候に応じてターン終了時にHP変化を受ける。
    ばんのうがさを持つ場合は晴れダメージ・雨回復を受けない。
    """
    mon = ctx.source
    weather = battle.weather_for(mon)

    # あめ中は最大HPの1/8回復
    if (
        weather.rainy
        and battle.modify_hp(mon, r=1/8)
    ):
        _announce_ability_triggered(battle, mon)

    # にほんばれ中は最大HPの1/8ダメージ
    if (
        weather.sunny
        and battle.modify_hp(mon, r=-1/8)
    ):
        _announce_ability_triggered(battle, mon)

    return HandlerReturn(value=value)


def かんそうはだ_modify_fire_damage(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """かんそうはだ特性: ほのお技を受けたときの威力が5/4倍になる。"""
    if ctx.move.type == "ほのお":
        value = apply_fixed_modifier(value, 5120)  # 5/4倍 = 5120/4096
    return HandlerReturn(value=value)


def かんろなミツ_lower_foe_evasion(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かんろなミツ特性: 初登場時に相手の回避率を1段階下げる（バトル中1回）。みがわり状態の相手には無効。"""
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    foe = battle.foe(mon)
    if foe is None:
        return HandlerReturn(value=value)
    battle.add_ability_disabled_reason(mon, "consumed")
    _announce_ability_triggered(battle, mon)
    if foe.has_volatile("みがわり"):
        return HandlerReturn(value=value)
    battle.modify_stats(foe, {"evasion": -1}, source=mon)
    return HandlerReturn(value=value)


def カーリーヘアー_lower_spd_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """カーリーヘアー特性: 直接攻撃を受けると攻撃者のすばやさを1段階下げる。"""
    if battle.query.is_contact_reaction(ctx):
        _announce_ability_triggered(battle, ctx.defender)
        battle.modify_stats(ctx.attacker, {"spe": -1}, source=ctx.defender)
    return HandlerReturn(value=value)


def がんじょう_block_ohko(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """がんじょう特性: 一撃必殺技を無効化する。(ON_TRY_MOVE_2 / subject_spec="defender:self")

    命中判定(Interrupt)より前に無効化する（docs/spec/abilities/がんじょう.md 参照）。
    """
    if ctx.move.has_flag("ohko"):
        _announce_ability_triggered(battle, ctx.defender)
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload=FailureLogPayload(move=ctx.move.name, display_reason="がんじょう"))
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def がんじょう_survive_confusion_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """がんじょう特性: こんらんの自傷ダメージも、HP満タン時はHP1残しで耐える。
    (ON_MODIFY_NON_MOVE_DAMAGE / subject_spec="target:self")

    だいばくはつ等の自滅効果(reason="self_cost")、反動ダメージ(reason="recoil")、
    みちづれ/ほろびのうたによるひんし(reason="perish")には発動しない
    （docs/spec/abilities/がんじょう.md 参照）。
    """
    if ctx.hp_change_reason != "self_attack":
        return HandlerReturn(value=value)
    mon = ctx.target
    if mon.hp == mon.max_hp and -value >= mon.hp:
        _announce_ability_triggered(battle, mon)
        value = -(mon.hp - 1)
    return HandlerReturn(value=value)


def がんじょう_survive_lethal(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """がんじょう特性: HP満タン時の致死ダメージをHP1残しに補正する。(ON_MODIFY_MOVE_DAMAGE / subject_spec="defender:self")"""
    defender = ctx.defender
    if (
        defender.hp == defender.max_hp
        and value >= defender.hp
    ):
        _announce_ability_triggered(battle, defender)
        value = defender.hp - 1
    return HandlerReturn(value=value)


def がんじょうあご_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """がんじょうあご特性: かみつき技の威力を1.5倍にする。"""
    if ctx.move.has_flag("bite"):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ききかいひ_switch_on_half_hp(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ききかいひ特性: HPが半分以下になったとき交代する。

    こんらん自傷(self_attack)・いたみわけ(pain_split)・みがわり/はらだいこ/のろい/
    ソウルビートなどの自己HP消費(self_cost)によるHP減少では発動しない。
    """
    mon = ctx.target

    # 交代できない条件
    if (
        mon.fainted
        or ctx.hp_change_reason in {"self_attack", "pain_split", "self_cost"}
    ):
        return HandlerReturn(value=value)

    hp_after = mon.hp
    hp_before = hp_after + value
    if _crossed_half_hp(hp_before, hp_after, mon.max_hp):
        _trigger_emergency_switch(battle, mon)

    return HandlerReturn(value=value)


def きけんよち_warn_threat(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """きけんよち特性: 登場時に相手がバツグン攻撃技か一撃必殺技を持つ場合にメッセージを出す。"""
    source = ctx.source
    foe = battle.foe(source)
    for move in foe.moves:
        if not move.is_attack:
            continue
        if move.has_flag("ohko"):
            _announce_ability_triggered(battle, source)
            return HandlerReturn(value=value)
        type_chart = TYPE_MODIFIER.get(move.type, {})
        modifier = 1.0
        for def_type in source.types:
            modifier *= type_chart.get(def_type, 1.0)
        if modifier > 1.0:
            _announce_ability_triggered(battle, source)
            return HandlerReturn(value=value)
    return HandlerReturn(value=value)


def きもったま_block_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """きもったま特性: いかくによるこうげきランク低下を無効化する。"""
    if ctx.stat_change_reason == "いかく":
        value = {}
    return HandlerReturn(value=value)


def きもったま_ghost_immune_bypass(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """きもったま特性: ノーマル/かくとう技がゴーストタイプに当たるよう相性補正を書き換える。"""
    if ctx.move.type not in ("ノーマル", "かくとう") or not ctx.defender.has_type("ゴースト"):
        return HandlerReturn(value=value)
    type_chart = TYPE_MODIFIER.get(ctx.move.type, {})
    base = 4096
    for def_type in ctx.defender.types:
        if def_type == "ゴースト":
            continue
        rate = type_chart.get(def_type, 1.0)
        base = int(base * rate)
    return HandlerReturn(value=base)


def きゅうばん_block_blow(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きゅうばん特性: 強制交代技の効果を防ぐ。"""
    _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=False, stop_event=True)


def きょううん_modify_critical_rank(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """きょううん特性: 攻撃側の急所ランクを+1する。"""
    return HandlerReturn(value=value + 1)


def prevent_poison_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_ailment(battle, ctx, value, blocked_ailments=["どく", "もうどく"])

def prevent_paralysis_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_ailment(battle, ctx, value, blocked_ailments=["まひ"])

def prevent_burn_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_ailment(battle, ctx, value, blocked_ailments=["やけど"])

def prevent_sleep_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_ailment(battle, ctx, value, blocked_ailments=["ねむり"])

def prevent_freeze_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_ailment(battle, ctx, value, blocked_ailments=["こおり"])


def きよめのしお_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_ailment(battle, ctx, value)


def きよめのしお_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_volatile(battle, ctx, value, blocked_volatiles=["ねむけ"])


def きよめのしお_reduce_ghost(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """きよめのしお特性: ゴースト技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type == "ゴースト":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def きれあじ_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """きれあじ特性: きる技の威力を1.5倍にする。"""
    if ctx.move.has_flag("slash"):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def きんしのちから_delay_status_move(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """きんしのちから特性: 変化技選択時に行動を後攻化する（後攻ティア -1）。"""
    if ctx.move.is_attack:
        return HandlerReturn(value=value)
    return HandlerReturn(value=value - 1)


def きんしのちから_disable_foe_ability(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """きんしのちから特性: 変化技使用直前に相手の特性を無効化する。"""
    if ctx.move.is_attack:
        return HandlerReturn(value=value)
    mon = ctx.defender
    if mon.ability.has_flag("mold_breaker_ignorable"):
        battle.add_ability_disabled_reason(mon, "かたやぶり")
    return HandlerReturn(value=value)


def きんしのちから_restore_foe_ability(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """きんしのちから特性: 変化技使用後に相手の特性の無効化を解除する。"""
    if ctx.move.is_attack:
        return HandlerReturn(value=value)
    battle.remove_ability_disabled_reason(ctx.defender, "かたやぶり")
    return HandlerReturn(value=value)


def きんちょうかん_check_nervous(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """きんちょうかん特性: 相手のきのみ使用を禁止する。

    自身がひんしになった瞬間に効果が失われるため、場に留まっている（生存している）
    ことを確認する。
    """
    assert ctx.source is not None
    if battle.foe(ctx.source).fainted:
        return HandlerReturn(value=value)
    return HandlerReturn(value=True)


ぎたい_フィールドタイプ対応表: dict[TerrainName, Type] = {
    "エレキフィールド": "でんき",
    "グラスフィールド": "くさ",
    "ミストフィールド": "フェアリー",
    "サイコフィールド": "エスパー",
}


def ぎたい_change_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぎたい特性: フィールドに応じて自身のタイプを単タイプに変化させる。

    フィールドが無いときは本来のタイプ（種族本来のタイプ）に戻す。
    現在のタイプと変化先のタイプが同じ場合は発動しない。
    """
    mon = ctx.source
    terrain_type = ぎたい_フィールドタイプ対応表.get(battle.terrain.name)
    target_types = [terrain_type] if terrain_type else mon.base_types
    if mon.types == target_types:
        return HandlerReturn(value=value)
    mon.ability_override_type = terrain_type
    _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ぎゃくじょう_boost_spa_on_half_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ぎゃくじょう特性: HPが最大HPの1/2超から1/2以下になったとき、とくこうが1段階上がる。

    連続攻撃技はすべてのヒットが終わった後（攻撃側がひんしになって中断した場合はその時点）に、
    1発目を受ける前のHPを基準にまとめて判定する（いかりのこうらと同じ idiom）。
    """
    mon = ctx.defender
    if not mon.alive:
        return HandlerReturn(value=value)

    if ctx.hit_index == 1:
        ctx._berserk_hp_before = mon.hp + value

    is_last_hit = ctx.hit_index == ctx.hit_count or ctx.attacker.fainted
    if not is_last_hit:
        return HandlerReturn(value=value)

    hp_before = ctx._berserk_hp_before
    hp_after = mon.hp
    if (
        _crossed_half_hp(hp_before, hp_after, mon.max_hp)
        and battle.modify_stats(mon, {"spa": +1}, source=ctx.attacker, reason="ぎゃくじょう")
    ):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ぎょぐん_enter_school_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぎょぐん特性: 登場時にレベル20以上かつHP1/4超ならむれたすがたへフォルムチェンジする。"""
    mon = ctx.source
    if mon.name not in (WISHIWASHI_SOLO, WISHIWASHI_SCHOOL):
        return HandlerReturn(value=value)
    if mon.level < 20:
        return HandlerReturn(value=value)
    if mon.hp * 4 > mon.max_hp:
        mon.set_form(WISHIWASHI_SCHOOL)
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ぎょぐん_update_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぎょぐん特性: ターン終了時にHPに応じてフォルムを切り替える。"""
    mon = ctx.source
    if mon.name not in (WISHIWASHI_SOLO, WISHIWASHI_SCHOOL):
        return HandlerReturn(value=value)
    if mon.level < 20:
        return HandlerReturn(value=value)

    if mon.hp * 4 > mon.max_hp:
        if mon.set_form(WISHIWASHI_SCHOOL):
            _announce_ability_triggered(battle, mon)
    else:
        if mon.set_form(WISHIWASHI_SOLO):
            _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def クイックドロウ_maybe_fast_attack(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """クイックドロウ特性: 攻撃技選択時に 30% の確率で先攻化する（後攻ティア +1）。

    こうこうのしっぽ所持時は発動すると道具の効果（後攻ティア-1）が無視されるため、
    道具側の補正分を打ち消すように+2する（順序に依存せず正味+1になる）。
    """
    if (
        not ctx.move.is_attack
        or not battle.random.random() < 0.3
    ):
        return HandlerReturn(value=value)
    _announce_ability_triggered(battle, ctx.attacker)
    if ctx.attacker.item.name == "こうこうのしっぽ":
        return HandlerReturn(value=value + 2)
    return HandlerReturn(value=value + 1)


def くさのけがわ_boost_B(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """くさのけがわ特性: グラスフィールド中の物理技への防御補正を1.5倍にする。

    こんらんの自傷ダメージ（"_こんらん"）には効果が無い。
    """
    if (
        battle.terrain.name == "グラスフィールド"
        and ctx.move.name != "_こんらん"
        and battle.query.deals_physical_damage(ctx.attacker, ctx.move)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def くだけるよろい_drop_B_boost_S(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くだけるよろい特性: 物理技を受けるとぼうぎょが1段階下がりすばやさが2段階上がる。

    自分自身の特性による自発的な変化のため、しろいきり/フラワーベールでは防げない。
    source は攻撃者ではなく自分自身を指定する（クリアボディ等の「相手由来の低下」判定にも
    引っかからないようにするため）。
    """
    if ctx.move.category != "physical":
        return HandlerReturn(value=value)
    mon = ctx.defender
    battle.modify_stats(mon, {"def": -1}, source=mon)
    if battle.modify_stats(mon, {"spe": +2}, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def クリアボディ_block_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """クリアボディ特性: 相手による能力ランク低下を無効化する。

    自分の技や反動による能力低下は防げない。
    """
    value = _block_stat_drop_by_foe(value, ctx)
    return HandlerReturn(value=value)


def _boost_on_move_ko(battle: Battle, ctx: AttackContext, value: Any, stats: dict[Stat, int]) -> HandlerReturn:
    if battle.modify_stats(ctx.attacker, stats, source=ctx.attacker):
        _announce_ability_triggered(battle, ctx.attacker)
    return HandlerReturn(value=value)


def くろのいななき_boost(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くろのいななき特性: 攻撃技で相手を倒すと特攻が1段階上がる。"""
    return _boost_on_move_ko(battle, ctx, value, stats={"spa": +1})


def グラスメイカー_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_terrain(battle, ctx.source, value, terrain="グラスフィールド", count=5)


def こおりのりんぷん_reduce_special_damage(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """こおりのりんぷん特性: 特殊技で受けるダメージを0.5倍にする。"""
    if ctx.move.category == "special":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def こぼれダネ_set_grassy_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こぼれダネ特性: 攻撃技でダメージを受けたときグラスフィールドを展開する。

    こらえるでHP1のまま耐えたときやみねうちを受けたとき（実HPダメージ0）も発動するが、
    みがわりに攻撃を防がれたとき（実HPダメージ0）は発動しない。
    """
    if ctx.substitute_damage:
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.terrain_manager.apply("グラスフィールド", 5, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def こんがりボディ_absorb_fire(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    return _apply_type_absorb(battle, ctx, value, move_type="ほのお", stats={"def": 2})


def こんじょう_ignore_burn_penalty(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """こんじょう特性: 状態異常時はやけどの物理半減を無効化する。"""
    return HandlerReturn(value=4096)


def こんじょう_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """こんじょう特性: 状態異常時に物理技の攻撃補正を1.5倍にする。

    こんらんの自傷ダメージ（"_こんらん"）には効果が無い
    （Champions仕様＝第五世代以降の仕様に準拠）。
    """
    if (
        ctx.attacker.ailment.is_active
        and ctx.move.category == "physical"
        and ctx.move.name != "_こんらん"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ごりむちゅう_lock_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ごりむちゅう特性: 最初に使用した技でロックする。

    ねごとのサブ実行中（sleep_talk_active）はロック対象としない
    （こだわり系アイテムと同様、ねごとで選ばれた技ではなく「ねごと」自体でロックする）。
    かがくへんかガス等で特性が無効化されている間は本ハンドラ自体が発火しないため、
    無効化中に使用した技ではロックされず、無効化解除後は無効化前のロックが再度有効になる。
    """
    mon = ctx.attacker
    if mon.sleep_talk_active:
        return HandlerReturn(value=value)
    if not mon.has_volatile("ごりむちゅう"):
        battle.volatile_manager.apply(
            mon, "ごりむちゅう", source=mon, move_name=ctx.move.name
        )
    return HandlerReturn(value=value)


def ごりむちゅう_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ごりむちゅう特性: 物理技の攻撃補正を1.5倍にする。"""
    if ctx.move.category == "physical":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ごりむちゅう_restrict_commands(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ごりむちゅう特性: ロック中の技と交代コマンドのみ選択可能にする。

    かがくへんかガス等で特性が無効化されている間は本ハンドラ自体が発火しないため、
    ロック中の技があっても無効化中は自由に技を選べる。
    """
    mon = ctx.source
    if not mon.has_volatile("ごりむちゅう"):
        return HandlerReturn(value=value)
    fixed_move_name = mon.volatiles["ごりむちゅう"].move_name
    new_options = [
        cmd for cmd in value
        if (
            cmd.is_type("switch")
            or (cmd.is_type("move") and mon.moves[cmd.index].name == fixed_move_name)
        )
    ]
    return HandlerReturn(value=new_options)


def サイコメイカー_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_terrain(battle, ctx.source, value, terrain="サイコフィールド", count=5)


def さいせいりょく_heal_on_withdraw(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さいせいりょく特性: 交代で引っ込んだとき最大HPの1/3を回復する（かいふくふうじ無効）。"""
    mon = ctx.source
    if battle.modify_hp(mon, r=1/3, reason="bench_heal"):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def さまようたましい_swap_ability_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さまようたましい特性: 直接攻撃を受けたとき攻撃者と特性を入れ替える。

    例外: うのミサイルは protected フラグを持つが、SV Ver.3.0.0 以降は
    さまようたましいでの交換が可能になったため base_name で個別に除外する。

    かがくへんかガスは protected フラグを持たないが、とくせいなし状態に
    なっていてもさまようたましいでの交換は発動しないため base_name で
    個別に判定する。
    """
    attacker = ctx.attacker
    defender = ctx.defender
    if (
        not battle.query.is_contact_reaction(ctx)
        or attacker is None
        or attacker.fainted
        or (attacker.ability.has_flag("protected") and attacker.ability.base_name != "うのミサイル")
        or attacker.ability.base_name == "かがくへんかガス"
        or defender is None
    ):
        return HandlerReturn(value=value)
    battle.ability_manager.swap_ability(defender, attacker)
    return HandlerReturn(value=value)


def さめはだ_chip_contact_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さめはだ特性: 接触技を受けた相手に最大HPの1/8ダメージを与える。"""
    return _apply_contact_counter_chip(battle, ctx, value, ratio=1/8)


def サンパワー_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """サンパワー特性: にほんばれ/おおひでり中に特殊技の特攻補正を1.5倍にする。
    ばんのうがさを持つ場合は晴れの恩恵を受けない。
    """
    if (
        battle.weather_for(ctx.attacker).sunny
        and ctx.move.category == "special"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def サンパワー_take_sun_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """サンパワー特性: にほんばれ/おおひでり中にターン終了時に最大HPの1/8ダメージを受ける。
    ばんのうがさを持つ場合は晴れのダメージを受けない。
    """
    mon = ctx.source
    if not battle.weather_for(mon).sunny:
        return HandlerReturn(value=value)
    result = battle.modify_hp(mon, r=-1/8)
    if result:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def サーフテール_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """サーフテール特性: エレキフィールド中に素早さが2倍になる。"""
    if battle.terrain.name == "エレキフィールド":
        value *= 2
    return HandlerReturn(value=value)


def しぜんかいふく_cure_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しぜんかいふく特性: 交代で引っ込んだとき状態異常を回復する。"""
    mon = ctx.source
    result = HandlerReturn(value=battle.ailment_manager.remove(mon))
    if result.value:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def しめりけ_block_explosion_foe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しめりけ特性（防御側）: 相手が爆発技を使おうとしたとき失敗させる。"""
    if ctx.move.has_flag("explosion"):
        _announce_ability_triggered(battle, ctx.defender)
        battle.add_event_log(
            ctx.attacker,
            LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="しめりけ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def しめりけ_block_explosion_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しめりけ特性（攻撃側）: 自分が爆発技を使おうとしたとき失敗させる。"""
    if ctx.move.has_flag("explosion"):
        _announce_ability_triggered(battle, ctx.attacker)
        battle.add_event_log(
            ctx.attacker,
            LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="しめりけ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def しゅうかく_restore_berry(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しゅうかく特性: ターン終了時に消費したきのみを復活させる。"""
    mon = ctx.source
    item_name = mon.last_lost_item_name

    # きのみでない、またはすでに別のアイテムを持っている場合は発動しない
    if (
        not item_name.endswith("のみ")
        or mon.has_item()
    ):
        return HandlerReturn(value=value)

    # 発動確率の計算（weather_for はノーてんき/エアロックの影響で「なし」天候を返す）
    chance = 1.0 if battle.weather_for(mon).sunny else 0.5

    if battle.random.random() >= chance:
        return HandlerReturn(value=value)

    battle.item_manager.gain_item(mon, item_name)

    _announce_ability_triggered(battle, mon)

    # TODO: 使用条件（HPしきい値等）を満たすきのみは仕様上その場で即時使用されるが、
    # gain_item は ON_ITEM_GAINED のみ発火し、オボンのみ等のHPしきい値判定は
    # ON_HP_CHANGED 側にしか登録されていないため即時発動しない。ON_HP_CHANGED を
    # 直接emitすると ききかいひ 等の無関係なハンドラまで誤発火するため、当面は
    # 次にHPが変化するタイミングまで発動が持ち越される（リサイクルも同様の制約）。
    return HandlerReturn(value=value)


def しょうりのほし_modify_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しょうりのほし特性: 技の命中率を1.1倍にする（一撃必殺技を除く）。"""
    if not ctx.move.has_flag("ohko"):
        value = apply_fixed_modifier(value, 4506)
    return HandlerReturn(value=value)


def しろのいななき_boost(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じしんかじょう特性: 攻撃技で相手を倒すと攻撃が1段階上がる。"""
    return _boost_on_move_ko(battle, ctx, value, stats={"atk": +1})


def しんがん_ghost_immune_bypass(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """しんがん特性: ノーマル/かくとう技がゴーストタイプに等倍で当たるよう相性補正を書き換える。"""
    if ctx.move.type not in ("ノーマル", "かくとう") or not ctx.defender.has_type("ゴースト"):
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
    _announce_ability_triggered(battle, ctx.target)
    battle.ailment_manager.apply(foe, ailment_name, source=ctx.target, ctx=ctx)
    return HandlerReturn(value=value)


def シンプル_modify_stat_delta(battle: Battle, ctx: EventContext, value: dict[str, int]) -> HandlerReturn:
    """シンプル特性: 自分のランク変化量を 2 倍にする。

    ON_BEFORE_MODIFY_STAT イベントで value（能力とランク変化量の辞書）の各変化量を
    2 倍にして返す。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_MODIFY_STAT)
            - target: ランク変化を受けるポケモン（シンプル所持者）
        value: 能力とランク変化量の辞書（例: {"atk": 1, "spe": -1}）
    """
    return HandlerReturn(value={stat: delta * 2 for stat, delta in value.items()})


PINCH_TYPE_BOOST_ABILITIES: dict[str, str] = {
    "しんりょく": "くさ",
    "もうか": "ほのお",
    "げきりゅう": "みず",
    "むしのしらせ": "むし",
}


def しんりょくもうかげきりゅうむしのしらせ_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ピンチ系特性: HP1/3以下かつ対応タイプ技で攻撃補正を1.5倍にする。"""
    required_type = PINCH_TYPE_BOOST_ABILITIES.get(ctx.attacker.ability.name)

    if (
        ctx.attacker.hp * 3 <= ctx.attacker.max_hp
        and ctx.move.type == required_type
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def じきゅうりょく_boost_B_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じきゅうりょく特性: 攻撃技でダメージを受けるたびにぼうぎょが1段階上がる。

    こらえるでHP1のまま耐えたときなど（実HPダメージ0）も発動するが、
    みがわりに攻撃を防がれたとき（実HPダメージ0）は発動しない。
    """
    if ctx.substitute_damage:
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"def": +1}, source=ctx.attacker):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def じゅうなん_cure_paralysis_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じゅうなん特性: 特性が有効化された時点ですでにまひ状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_ailment_on_enable(battle, ctx, blocked_ailments=["まひ"])


def じょうききかん_max_boost_speed(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じょうききかん特性: みずまたはほのお技でダメージを受けるとすばやさが6段階上がる。

    バブルこうせん等、技自身の追加効果によるすばやさ変化との発動順は
    priority（data/ability.py 側で指定）で制御する。
    """
    if ctx.move.type not in ("みず", "ほのお"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"spe": +6}, source=ctx.attacker):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def じょおうのいげん_block_priority(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じょおうのいげん/テイルアーマー/ビビッドボディ: 優先度+1以上の技を無効化する。

    自分や味方が味方側に対して使用した技（まもる等の自己対象技）や、
    場の全体・相手の場が対象の技は対象外（相手の単体を対象とする技のみ無効化する）。
    """
    if ctx.move.target != "foe":
        return HandlerReturn(value=value)
    effective_priority = battle.speed_calculator.calc_move_priority(ctx.attacker, ctx.move)
    if effective_priority <= 0:
        return HandlerReturn(value=value)
    _announce_ability_triggered(battle, ctx.defender)
    battle.add_event_log(
        ctx.attacker,
        LogCode.MOVE_FAILED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="じょおうのいげん")
    )
    return HandlerReturn(value=False, stop_event=True)


def じりょく_check_trapped(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じりょく特性: はがねタイプのポケモンの交代を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_TRAPPED)
            - source: 交代を試みるポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: (True, 交代が制限されるかどうか)
            - はがねタイプの場合はTrue（交代制限）
            - ゴーストタイプを併せ持つ場合はゴーストタイプの性質が優先され、交代を制限しない
    """
    source = ctx.source
    result = (
        source is not None
        and source.has_type("はがね")
        and not source.has_type("ゴースト")
    )
    return HandlerReturn(value=result)


def じんばいったい_boost(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じんばいったい特性: 攻撃技で相手を倒すと、はくばじょうのすがたはこうげき、
    こくばじょうのすがたはとくこうが1段階上がる（しろのいななき/くろのいななき相当）。
    """
    stat: Stat = "atk" if ctx.attacker.name == CALYREX_ICE else "spa"
    return _boost_on_move_ko(battle, ctx, value, stats={stat: +1})


def すいすい_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すいすい特性: あめ・おおあめ中に素早さが2倍になる。
    ばんのうがさを持つ場合や、ノーてんき/エアロックで天候効果が無効化されている場合は発動しない。
    """
    if battle.weather_for(ctx.source).rainy:
        value *= 2
    return HandlerReturn(value=value)


def すいほう_boost_water(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """すいほう特性: みず技の威力を2倍にする。"""
    if ctx.move.type == "みず":
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def すいほう_cure_burn_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """すいほう特性: 特性が有効化された時点ですでにやけど状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_ailment_on_enable(battle, ctx, blocked_ailments=["やけど"])


def すいほう_reduce_fire(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """すいほう特性: ほのお技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type == "ほのお":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def スイートベール_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_volatile(battle, ctx, value, blocked_volatiles=["ねむけ"])


def _skin_modify_move_type(battle: Battle, ctx: AttackContext, value: Type, *, from_type: str, to_type: str) -> HandlerReturn:
    """スキン系特性共通: from_type の技を to_type に変換する。"""
    if value == from_type:
        value = to_type
    return HandlerReturn(value=value)

def _skin_boost_power(battle: Battle, ctx: AttackContext, value: int, *, trigger_type: str) -> HandlerReturn:
    """スキン系特性共通: trigger_type だった技の威力を 4915/4096 倍にする。"""
    if ctx.move.data.type == trigger_type:
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def スカイスキン_modify_move_type(battle: Battle, ctx: AttackContext, value: Type) -> HandlerReturn:
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="ひこう")


def スカイスキン_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")


def スキルリンク_modify_hit_check_each_time(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """スキルリンク特性: トリプルキック等、毎ヒット命中判定する技を初回ヒットのみの判定にする。"""
    return HandlerReturn(value=False)


def スキルリンク_modify_hit_count(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """スキルリンク特性: 連続技のヒット数を最大にする。"""
    if ctx.move.max_hits > 1:
        value = ctx.move.max_hits
    return HandlerReturn(value=value)


def すてみ_boost_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """すてみ特性: 反動を受ける技の威力を1.2倍にする。"""
    if ctx.move.has_flag("recoil"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def スナイパー_boost_critical(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """スナイパー特性: 急所時の最終ダメージ補正を1.5倍にする。"""
    if ctx.critical:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def すなおこし_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_weather(battle, ctx.source, value, weather="すなあらし", count=5)


def すなかき_ignore_sandstorm_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すなかき特性: すなあらしのダメージを受けない。"""
    return _ignore_sandstorm_damage(battle, ctx, value)


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


def すながくれ_ignore_sandstorm_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すながくれ特性: すなあらしのダメージを受けない。"""
    return _ignore_sandstorm_damage(battle, ctx, value)


def すながくれ_reduce_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すながくれ特性: すなあらし中に受ける技の命中率を3277/4096倍にする（必中技・一撃必殺技は除く）。"""
    if (
        battle.weather.name == "すなあらし"
        and not ctx.move.has_flag("ohko")
    ):
        value = apply_fixed_modifier(value, 3277)
    return HandlerReturn(value=value)


def すなのちから_ignore_sandstorm_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """すなのちから特性: すなあらしのダメージを受けない。"""
    return _ignore_sandstorm_damage(battle, ctx, value)


def すなのちから_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """すなのちから特性: すなあらし中の岩/地面/鋼技の威力を1.3倍にする。"""
    if (
        battle.weather.name == "すなあらし"
        and ctx.move.type in ["いわ", "じめん", "はがね"]
    ):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def すなはき_set_sandstorm(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すなはき特性: 攻撃技でダメージを受けたときすなあらし（5ターン）を展開する。

    こらえるでHP1のまま耐えたときやみねうちを受けたとき（実HPダメージ0）も発動するが、
    みがわりに攻撃を防がれたとき（実HPダメージ0）は発動しない。
    """
    if ctx.substitute_damage:
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.weather_manager.apply("すなあらし", 5, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def すりぬけ_bypass_screen(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """すりぬけ特性: リフレクター・ひかりのかべ等の壁を貫通する"""
    return HandlerReturn(value=True)


def すりぬけ_bypass_status_guard(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """すりぬけ特性: しんぴのまもり・しろいきり等の耐性を貫通する"""
    return HandlerReturn(value=True)


def すりぬけ_bypass_substitute(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """すりぬけ特性: みがわりを無視して攻撃する。"""
    return HandlerReturn(value=False, stop_event=True)


def するどいめ_block_ACC_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """するどいめ特性: 相手による命中率ランク低下を無効化する。"""
    value = _block_stat_drop_by_foe(value, ctx, "accuracy")
    return HandlerReturn(value=value)


def するどいめ_ignore_evasion(battle: Battle, ctx: AttackContext, value: dict[Stat, int]) -> HandlerReturn:
    """するどいめ特性: 相手の回避率ランク上昇を無効化する。"""
    value["evasion"] = 0
    return HandlerReturn(value=value)


def スロースタート_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """スロースタート特性: 登場から5ターンの物理攻撃補正を0.5倍にする。"""
    if (
        ctx.attacker.ability.count < 5
        and ctx.move.category == "physical"
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def スロースタート_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """スロースタート特性: 登場から5ターンのすばやさ補正を0.5倍にする。"""
    if ctx.source.ability.count < 5:
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def スロースタート_start(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スロースタート特性: 登場ターンを記録する。"""
    ctx.source.ability.count = 0
    _announce_ability_triggered(battle, ctx.source)
    return HandlerReturn(value=value)


def スロースタート_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スロースタート特性: 登場からのターン数をカウントする。"""
    mon = ctx.source
    mon.ability.count += 1
    if mon.ability.count == 5:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def スワームチェンジ_form_change_on_low_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スワームチェンジ特性: ターン終了時にHP1/2以下ならパーフェクトフォルムへフォルムチェンジする。"""
    mon = ctx.source
    if mon.name not in (ZYGARDE_50, ZYGARDE_10):
        return HandlerReturn(value=value)
    if mon.hp * 2 <= mon.max_hp:
        # ひんし後にさいきのいのり等で復活した際、元のフォルムへ戻すために記憶しておく
        mon.memory["battle"]["スワームチェンジ_origin_form"] = mon.name
        mon.set_form(ZYGARDE_PERFECT)
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def スワームチェンジ_revert_form_on_faint(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スワームチェンジ特性: パーフェクトフォルムでひんしになったとき、フォルムと最大HPを元に戻す。

    一次情報: 「ひんし状態になった場合、フォルムと最大HPは元に戻る。このときも
    げんきのかけらなどで復活できれば、条件を満たすことで再度スワームチェンジが発動する。」
    """
    mon = ctx.target
    if mon.name != ZYGARDE_PERFECT or not mon.fainted:
        return HandlerReturn(value=value)
    origin_form = mon.memory["battle"].get("スワームチェンジ_origin_form")
    if origin_form:
        mon.set_form(origin_form, keep_damage=False)
    return HandlerReturn(value=value)


def せいぎのこころ_boost_atk_on_dark(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """せいぎのこころ特性: あくタイプの技でダメージを受けるとこうげきが1段階上がる。"""
    if ctx.move.type != "あく":
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"atk": +1}, source=ctx.attacker):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def せいしんりょく_block_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """せいしんりょく特性: いかくによる攻撃ランク低下を無効化する。"""
    if ctx.stat_change_reason == "いかく":
        value = {}
        _announce_ability_triggered(battle, ctx.target)
    return HandlerReturn(value=value)


def せいしんりょく_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_volatile(battle, ctx, value, blocked_volatiles=["ひるみ"])


def せいでんき_maybe_paralyze_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """せいでんき特性: 直接攻撃を受けた相手を30%でまひにする。"""
    return _apply_contact_counter_ailment(battle, ctx, value, ailment="まひ", chance=0.3)


def ぜったいねむり_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぜったいねむり特性: 登場時にゆめうつつ状態を付与する。"""
    mon = ctx.source
    assert mon is not None
    if not battle.ailment_manager.apply(mon, "ゆめうつつ"):
        # 既にゆめうつつ（2回目以降の登場）→ メッセージのみ出す
        battle.add_event_log(mon, LogCode.AILMENT_APPLIED, payload=AilmentPayload(ailment="ゆめうつつ"))
    return HandlerReturn(value=value)


def ゼロフォーミング_clear_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ゼロフォーミング特性: テラスタル時に場の天候とフィールドを消去する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_TERASTALLIZE)
            - source: テラスタルしたポケモン
        value: イベント値（未使用）
    """
    mon = ctx.source
    _announce_ability_triggered(battle, mon)
    battle.weather_manager.remove()
    battle.terrain_manager.remove()
    return HandlerReturn(value=value)


def そうしょく_absorb_grass(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """そうしょく特性: くさ技を無効化し攻撃を1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="くさ", stats={"atk": 1})


def そうだいしょう_announce_on_entry(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """そうだいしょう特性: 特性発動時点（場に出たとき、または他の特性からそうだいしょうに
    書き変わったとき）で、その戦闘で自分側がひんしになった延べ回数×10%の威力補正率を
    確定させる（最大+50%）。復活しても延べ回数は減らず、再度ひんしになれば加算される
    （一次情報: docs/wiki/abilities/そうだいしょう.html 特性の仕様節）。
    確定した補正率は `ability.count` に保持し、以後その戦闘中に味方がひんしになっても
    再計算しない（威力の補正率は発動時点で決まる）。
    """
    mon = ctx.source
    player = battle.get_player(mon)
    state = battle.player_states[player]
    fainted_count = min(state.total_fainted_count, 5)
    mon.ability.count = fainted_count
    if fainted_count:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def そうだいしょう_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """そうだいしょう特性: 特性発動時に確定した威力補正率（ability.count）を適用する。"""
    fainted_count = ctx.attacker.ability.count
    if not fainted_count:
        return HandlerReturn(value=value)
    modifier = 4096 * (10 + fainted_count) // 10
    return HandlerReturn(value=apply_fixed_modifier(value, modifier))


def ソウルハート_boost_spa_on_faint(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ソウルハート特性: 相手が攻撃技以外の要因（状態異常・天候・自滅技など）で
    ひんしになったときもとくこうが1段階上がる。

    攻撃技によるKO（reason="move_damage"）は ON_MOVE_KO 側の
    ソウルハート_boost_spa_on_ko で処理するため、ここでは除外する
    （二重発動の防止、およびミイラ等による特性書き換え順序を正しく保つため）。
    """
    if not ctx.target.fainted or ctx.hp_change_reason == "move_damage":
        return HandlerReturn(value=value)
    mon = battle.foe(ctx.target)
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    if battle.modify_stats(mon, {"spa": +1}, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ソウルハート_boost_spa_on_ko(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソウルハート特性: 自分の攻撃技で相手を倒すととくこうが1段階上がる。

    攻撃技によるKOはミイラ/さまようたましい/とれないにおいの特性書き換え
    （ON_DAMAGE_HIT）より後に発火する ON_MOVE_KO で処理する必要がある
    （一次情報: 直接攻撃で倒した相手がミイラ等を持つ場合、特性が書き換えられて
    ソウルハートは発動しない）。ON_MOVE_KO は ON_DAMAGE_HIT の後に発火するため、
    この順序が自然に守られる。
    """
    mon = ctx.attacker
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    if battle.modify_stats(mon, {"spa": +1}, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def たいねつ_reduce_burn_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """たいねつ特性: やけどのターン終了時ダメージを半分にする（最低1）。"""
    if ctx.hp_change_reason == "burn":
        value = -max(1, apply_fixed_modifier(-value, 2048))
    return HandlerReturn(value=value)


def たいねつ_reduce_fire(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """たいねつ特性: 炎技を受けるとき攻撃補正を0.5倍にする。"""
    if ctx.move.type == "ほのお":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def たんじゅん_double_stat(battle: Battle, ctx: EventContext, value: dict[str, int]) -> HandlerReturn:
    """たんじゅん特性: 能力変化量を2倍にする。"""
    return HandlerReturn(value={stat: delta * 2 for stat, delta in value.items()})


def ダウンロード_raise_stat(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ダウンロード特性: 入場時に相手の防御と特防を比較し、低い方に対応する攻撃能力を上げる。

    比較にはランク補正（パワートリック・ガードシェアで書き換わった実数値を含む）を
    考慮し、持ち物・特性・天候による補正は除外する。ワンダールーム下では実数値は
    据え置いたまま防御・特防のランク補正のみを入れ替えて比較する（本家の既知の仕様）。
    """
    mon = ctx.source
    foe = battle.foe(mon)

    if battle.get_global_field("ワンダールーム").is_active:
        foe_def = foe.stats["def"] * foe.rank_modifier("spd")
        foe_spd = foe.stats["spd"] * foe.rank_modifier("def")
    else:
        foe_def = foe.ranked_stats["def"]
        foe_spd = foe.ranked_stats["spd"]
    boost_stat = "atk" if foe_def < foe_spd else "spa"

    changed = battle.modify_stats(mon, {boost_stat: +1}, source=mon)
    if changed:
        _announce_ability_triggered(battle, mon)

    return HandlerReturn(value=value)


def だっぴ_cure_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だっぴ特性: ターン終了時に30%で状態異常を回復する。"""
    mon = ctx.source
    if not mon.ailment.is_active:
        return HandlerReturn(value=value)

    chance = battle.resolve_secondary_chance(ctx, 0.3)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    result = HandlerReturn(value=battle.ailment_manager.remove(mon))
    if result.value:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ダルマモード_revert_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ダルマモード特性: 交代時にダルマのすがたから元のすがたへ戻す。

    Note:
        ガラルのすがた未対応の理由は `ダルマモード_update_form` を参照。
    """
    mon = ctx.source
    if mon.name == DARMANITAN_ZEN:
        mon.set_form(DARMANITAN_NORMAL)
    return HandlerReturn(value=value)


def ダルマモード_update_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ダルマモード特性: ターン終了時にHPが1/2以下ならダルマのすがたへ、1/2超なら元のすがたへフォルムチェンジする。

    Note:
        ヒヒダルマ(ガラルのすがた)もダルマモードを隠れ特性として持つが、
        ダルマモード発動後のガラル専用フォルムのデータが pokedex.json に
        存在しないため、この判定は通常のヒヒダルマ(ノーマル/ダルマ)のみを
        対象とする。ガラルのすがたのヒヒダルマがダルマモードを持っていても
        名前が一致せずフォルムチェンジは発動しない。
    """
    mon = ctx.source
    if mon.hp * 2 <= mon.max_hp:
        if mon.name == DARMANITAN_NORMAL:
            mon.set_form(DARMANITAN_ZEN)
            _announce_ability_triggered(battle, mon)
    else:
        if mon.name == DARMANITAN_ZEN:
            mon.set_form(DARMANITAN_NORMAL)
            _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ダークオーラ_boost_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ダークオーラ特性: あく技の威力を1.33倍にする。オーラブレイクがいる場合は0.75倍にする。"""
    if ctx.move.type != "あく":
        return HandlerReturn(value=value)
    aura_break = (
        ctx.attacker.ability.name == "オーラブレイク"
        or ctx.defender.ability.name == "オーラブレイク"
    )
    modifier = 3072 if aura_break else 5448
    return HandlerReturn(value=apply_fixed_modifier(value, modifier))


def ちからずく_boost(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ちからずく特性: 追加効果ありの技の威力を 1.3 倍にする。(ON_CALC_POWER_MODIFIER / subject_spec="attacker:self")"""
    if ctx.move.has_flag("secondary_effect"):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ちからずく_disable_secondary_effect(battle: Battle, ctx: AttackContext, value: float) -> HandlerReturn:
    """ちからずく特性: 追加効果対象技の追加効果確率を 0 にする。"""
    if ctx.move.has_flag("secondary_effect"):
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def ちからもち_boost_physical(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ちからもち・ヨガパワー特性: 物理技時の攻撃補正を2.0倍にする。

    こんらんの自傷ダメージ（"_こんらん"）には影響しない
    （Champions仕様＝第五世代以降の仕様に準拠）。
    """
    if (
        ctx.move.category == "physical"
        and ctx.move.name != "_こんらん"
    ):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ちくでん_absorb_electric(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """ちくでん特性: でんき技を無効化し最大HPの1/4回復する。"""
    return _apply_type_absorb(battle, ctx, value, move_type="でんき", heal_ratio=1/4)


def ちどりあし_reduce_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちどりあし特性: こんらん中の自分に対する技の命中率を半分にする。"""
    if ctx.defender.has_volatile("こんらん"):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def ちょすい_absorb_water(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """ちょすい特性: みず技を無効化し最大HPの1/4回復する。"""
    return _apply_type_absorb(battle, ctx, value, move_type="みず", heal_ratio=1/4)


def てきおうりょく_modify_stab(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """てきおうりょく特性: タイプ一致補正を強化する。

    テラスタル中は、テラスタイプに一致した技のみ効果が発動する。
    テラスタルにより失った元タイプの技（元タイプには一致するがテラスタイプには
    一致しない技）には発動しない（STAB補正は1.5倍のまま据え置かれる）。
    """
    attacker = ctx.attacker
    tera_type = attacker.active_tera_type

    # ステラテラスタル時はてきおうりょくがSTAB補正に影響しない。
    if tera_type == "ステラ":
        return HandlerReturn(value=value)

    # テラスタル中、技のタイプがテラスタイプと不一致なら効果は発動しない
    # （元タイプ一致による1.5倍のSTABはそのまま）。
    if tera_type and ctx.move.type != tera_type:
        return HandlerReturn(value=value)

    if value == 6144:
        return HandlerReturn(value=8192)  # 1.5倍 -> 2倍
    if value == 8192:
        return HandlerReturn(value=9216)  # 2倍 -> 2.25倍
    return HandlerReturn(value=value)


def テクニシャン_boost_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """テクニシャン特性: 元威力60以下の技威力補正を1.5倍にする。"""
    if ctx.move.data.power is not None and ctx.move.data.power <= 60:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def てつのこぶし_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """てつのこぶし特性: パンチ技の威力を1.2倍にする。"""
    return _modify_by_move_condition(ctx.move, value, modifier=4915, move_flag="punch")


def テラスシェル_overwrite_type_modifier(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """テラスシェル特性: HP満タン時、等倍以上のタイプ相性を半減する。"""
    if ctx.defender.hp == ctx.defender.max_hp:
        value = min(value, 2048)
    return HandlerReturn(value=value)


def テラスチェンジ_form_change_on_entry(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """テラスチェンジ特性: 登場時に他の特性より先にテラスタルフォルムへフォルムチェンジする。"""
    mon = ctx.source
    if mon.name != TERAPAGOS_NORMAL:
        return HandlerReturn(value=value)
    mon.set_form(TERAPAGOS_TERASTAL)
    _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def てんきや_sync_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """てんきや特性: 現在の天気に合わせたフォルムへフォルムチェンジする。ノーてんき/エアロック中は通常フォルムに戻す。"""
    mon = ctx.source
    if mon.name not in (CASTFORM_NORMAL, CASTFORM_SUNNY, CASTFORM_RAINY, CASTFORM_SNOWY):
        return HandlerReturn(value=value)
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    weather_name = battle.weather.name
    form = WEATHER_TO_CASTFORM.get(weather_name, CASTFORM_NORMAL)
    if mon.set_form(form):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def てんねん_ignore_rank(battle: Battle, ctx: AttackContext, value: float) -> HandlerReturn:
    """てんねん特性: ランク補正を無視する。"""
    return HandlerReturn(value=1)


def てんのめぐみ_boost_secondary_chance(battle: Battle, ctx: AttackContext, value: float) -> HandlerReturn:
    """てんのめぐみ特性: 追加効果対象技の追加効果確率を2倍にする。"""
    return HandlerReturn(value=min(1.0, value * 2))


def デルタストリーム_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_weather(battle, ctx.source, value, weather="らんきりゅう", count=1)


def デルタストリーム_deactivate_strong_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _deactivate_strong_weather(battle, ctx, value, weather="らんきりゅう")


def でんきエンジン_absorb_electric(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """でんきエンジン特性: でんき技を無効化し素早さを1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="でんき", stats={"spe": 1})


def でんきにかえる_charge_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんきにかえる特性: 攻撃技でダメージを受けるとじゅうでん状態になる。"""
    mon = ctx.defender
    if battle.volatile_manager.apply(mon, "じゅうでん", source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def とうそうしん_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
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


def とびだすなかみ_retaliate_on_ko(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とびだすなかみ特性: 攻撃技でひんしになったとき攻撃者に反撃ダメージを与える。"""
    attacker = ctx.attacker
    defender = ctx.defender
    if attacker is None or attacker.fainted:
        return HandlerReturn(value=value)
    hp_before = _とびだすなかみ_hp_before.pop(id(defender), abs(value))
    if hp_before <= 0:
        return HandlerReturn(value=value)
    battle.modify_hp(attacker, -hp_before)
    _announce_ability_triggered(battle, defender)
    return HandlerReturn(value=value)


_とびだすなかみ_hp_before: dict[int, int] = {}  # id(defender) → HP before move


def とびだすなかみ_save_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とびだすなかみ補助: 技開始時に防御側の初期HPを保存する。"""
    _とびだすなかみ_hp_before[id(ctx.defender)] = ctx.defender.hp
    return HandlerReturn(value=value)


def とびだすハバネロ_burn_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とびだすハバネロ特性: 攻撃技を受けたとき攻撃者をやけど状態にする。"""
    attacker = ctx.attacker
    if attacker is None:
        return HandlerReturn(value=value)
    battle.ailment_manager.apply(attacker, "やけど", source=ctx.defender, ctx=ctx)
    return HandlerReturn(value=value)


def トランジスタ_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """トランジスタ特性: でんき技の攻撃補正を1.3倍にする。"""
    if ctx.move.type == "でんき":
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def とれないにおい_overwrite_attacker_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とれないにおい特性: 直接攻撃でダメージを受けたとき攻撃者の特性をとれないにおいにする。"""
    if _overwrite_ability_on_contact(battle, ctx, new_ability="とれないにおい"):
        _announce_ability_triggered(battle, ctx.defender)
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


def どくくぐつ_confuse_on_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくくぐつ特性: どく/もうどく付与時に対象をこんらんにする。"""
    if value not in ("どく", "もうどく"):
        return HandlerReturn(value=value)
    target = ctx.target
    if target is None:
        return HandlerReturn(value=value)
    battle.volatile_manager.apply(target, "こんらん", source=ctx.source)
    _announce_ability_triggered(battle, ctx.source)
    return HandlerReturn(value=value)


def どくげしょう_set_toxic_spikes(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくげしょう特性: 物理技被弾時に攻撃者の場にどくびしを1層設置する。"""
    if ctx.move.category != "physical":
        return HandlerReturn(value=value)
    foe_side = battle.get_side(ctx.attacker)
    field = foe_side.get("どくびし")
    if field.count >= 2:
        return HandlerReturn(value=value)
    if field.is_active:
        field.count += 1
        battle.add_event_log(0, LogCode.FIELD_STARTED, payload=FieldPayload(field="どくびし", count=field.count))
    else:
        foe_side.activate("どくびし", 1)
    _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=value)


def どくしゅ_maybe_poison_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def どくのくさり_maybe_badly_poison(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくのくさり特性: 攻撃を命中させたとき30%の確率で相手をもうどくにする。"""
    if battle.random.random() < battle.resolve_secondary_chance(ctx, 0.3):
        battle.ailment_manager.apply(
            ctx.defender, "もうどく", source=ctx.attacker, ctx=ctx,
        )
    return HandlerReturn(value=value)


def どくのトゲ_maybe_poison_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくのトゲ特性: 直接攻撃を受けた相手を30%でどくにする。"""
    return _apply_contact_counter_ailment(battle, ctx, value, ailment="どく", chance=0.3)


def どくぼうそう_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """どくぼうそう特性: どく状態時に特殊技の威力を1.5倍にする。"""
    if (
        (ctx.attacker.has_ailment("どく", "もうどく"))
        and ctx.move.category == "special"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def どしょく_absorb_ground(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """どしょく特性: じめん技を無効化し最大HPの1/4回復する。"""
    return _apply_type_absorb(battle, ctx, value, move_type="じめん", heal_ratio=1/4)


def ドラゴンスキン_modify_move_type(battle: Battle, ctx: AttackContext, value: Type) -> HandlerReturn:
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="ドラゴン")


def ドラゴンスキン_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")


def どんかん_block_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """どんかん特性: いかくによるこうげきランク低下を無効化する (第八世代以降)。"""
    if ctx.stat_change_reason == "いかく":
        value = {}
    return HandlerReturn(value=value)


def どんかん_cure_volatile_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どんかん特性: 特性が有効化された時点ですでにちょうはつ/メロメロ状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_volatile_on_enable(battle, ctx, blocked_volatiles=["ちょうはつ", "メロメロ"])


def どんかん_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_volatile(battle, ctx, value, blocked_volatiles=["ちょうはつ", "メロメロ"])


def ナイトメア_damage_sleeping_foe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ナイトメア特性: 相手がねむり状態のとき毎ターン最大HPの1/8を削る。"""
    mon = ctx.source
    foe = battle.foe(mon)
    if (
        foe.ailment.is_sleep
        and battle.modify_hp(foe, r=-1/8)
    ):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def なまけ_init(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """なまけ特性: 登場/有効化時になまけカウンタを「行動可」で初期化する。"""
    ctx.source.ability.state = "can_act"
    return HandlerReturn(value=value)


def なまけ_try_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なまけ特性: X=1のターンは行動をスキップし、Xを反転する。"""
    mon = ctx.attacker
    state = mon.ability.state
    if state == "skip_next":
        # このターンはなまける
        mon.ability.state = "can_act"
        battle.add_event_log(mon, LogCode.ACTION_BLOCKED, payload=FailureLogPayload(move=ctx.move.name, display_reason="なまけ"))
        return HandlerReturn(value=False, stop_event=True)
    # state == "can_act"
    mon.ability.state = "skip_next"
    return HandlerReturn(value=value)


def ぬめぬめ_lower_spd_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ぬめぬめ特性: 直接攻撃を受けると攻撃者のすばやさを1段階下げる。"""
    if battle.query.is_contact_reaction(ctx):
        _announce_ability_triggered(battle, ctx.defender)
        battle.modify_stats(ctx.attacker, {"spe": -1}, source=ctx.defender)
    return HandlerReturn(value=value)


def ねつこうかん_boost_atk_on_fire(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねつこうかん特性: ほのおタイプの攻撃技でダメージを受けたとき、こうげきが1段階上がる。"""
    if ctx.move.type != "ほのお":
        return HandlerReturn(value=value)

    changed = battle.modify_stats(ctx.defender, {"atk": +1}, source=ctx.attacker)
    if not changed:
        return HandlerReturn(value=value)

    _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=value)


def ねつこうかん_cure_burn_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねつこうかん特性: 特性が有効化された時点ですでにやけど状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_ailment_on_enable(battle, ctx, blocked_ailments=["やけど"])


def ねつぼうそう_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ねつぼうそう特性: やけど状態時の物理技の威力を1.5倍にする。"""
    if (
        ctx.attacker.has_ailment("やけど")
        and ctx.move.category == "physical"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ねんちゃく_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ねんちゃく特性: 相手から受けるアイテム交換・奪取・除去を防ぐ。

    はたきおとすの威力補正判定（dry_run=True）では、除去自体は行われないため
    特性を発動・表示させず、威力補正の対象として扱う（除去は別途阻止される）。
    ignore_sticky_hold（むしくい・ついばむが対象をひんしにさせた場合等、
    第五世代以降の仕様）が指定されている場合も阻止しない。
    """
    if ctx.dry_run or ctx.ignore_sticky_hold:
        return HandlerReturn(value=value)
    if ctx.source != ctx.target:
        _announce_ability_triggered(battle, ctx.target)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def のろわれボディ_maybe_disable_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """のろわれボディ特性: 直接攻撃を受けたとき30%の確率で攻撃技をかなしばりにする。"""
    if not battle.query.is_contact_reaction(ctx) or ctx.attacker is None:
        return HandlerReturn(value=value)
    if battle.random.random() < 0.3:
        battle.volatile_manager.apply(
            ctx.attacker, "かなしばり",
            source=ctx.defender, move_name=ctx.move.name,
        )
        _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=value)


def ノーガード_guarantee_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ノーガード特性: 命中判定を必中化する。"""
    if value is not None:
        attacker_no_guard = ctx.attacker.ability.name == "ノーガード"
        defender_no_guard = ctx.defender.ability.name == "ノーガード"
        if attacker_no_guard or defender_no_guard:
            value = None
    return HandlerReturn(value=value)


def ノーマルスキン_boost_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ノーマルスキン特性: 変換した技の威力を4915/4096倍にする。"""
    if ctx.move.data.type not in ("ノーマル", "ステラ"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def ノーマルスキン_modify_move_type(battle: Battle, ctx: AttackContext, value: Type) -> HandlerReturn:
    """ノーマルスキン特性: 全ての技をノーマルタイプに変換する（ステラタイプ除く）。"""
    if value not in ("ノーマル", "ステラ"):
        value = "ノーマル"
    return HandlerReturn(value=value)


def はがねつかい_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """はがねつかい特性: はがね技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(ctx.move, value, modifier=6144, move_type="はがね")


def はがねのせいしん_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """はがねのせいしん特性: はがね技の威力を1.5倍にする。"""
    return _modify_by_move_condition(ctx.move, value, modifier=6144, move_type="はがね")


def はじまりのうみ_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_weather(battle, ctx.source, value, weather="おおあめ", count=1)


def はじまりのうみ_deactivate_strong_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _deactivate_strong_weather(battle, ctx, value, weather="おおあめ")


def はっこう_block_acc_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """はっこう特性: 相手による命中率ランク低下を無効化する。"""
    filtered = {stat: v for stat, v in value.items() if not (stat == "accuracy" and v < 0)}
    return HandlerReturn(value=filtered)


def はとむね_block_B_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """はとむね特性: 相手によるぼうぎょランク低下を無効化する。"""
    value = _block_stat_drop_by_foe(value, ctx, "def")
    return HandlerReturn(value=value)


def ハドロンエンジン_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_terrain(battle, ctx.source, value, terrain="エレキフィールド", count=5)


def ハドロンエンジン_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ハドロンエンジン特性: エレキフィールド中の攻撃補正を1.33倍にする。"""
    if (
        battle.terrain.name == "エレキフィールド"
        and ctx.move.category == "special"
    ):
        value = apply_fixed_modifier(value, 5461)
    return HandlerReturn(value=value)


def はやあし_modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はやあし特性: 状態異常時に素早さが1.5倍になる。まひの素早さ低下も無効化する。"""
    mon = ctx.source
    if not mon.ailment.is_active:
        return HandlerReturn(value=value)

    if mon.has_ailment("まひ"):
        # まひ_speed による 1/2 ペナルティを打ち消して 1.5 倍（合計 *3）
        value *= 3
    else:
        value *= 1.5
    return HandlerReturn(value=value)


def はやおき_extra_decrement(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def はやてのつばさ_modify_priority(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """はやてのつばさ特性: HP満タン時にひこうタイプの技を使うと優先度を+1する。"""
    mon = ctx.attacker
    if (
        ctx.move.type == "ひこう"
        and mon.hp == mon.max_hp
    ):
        value += 1
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


def はりきり_modify_accuracy(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """はりきり特性: 物理技（一撃必殺・必中技除外）の命中率を0.8倍にする。"""
    if (
        ctx.move.category == "physical"
        and not ctx.move.has_flag("ohko")  # 一撃必殺技は命中率ペナルティなし
        and ctx.move.accuracy is not None  # 必中技は命中率ペナルティなし
    ):
        value = apply_fixed_modifier(value, 3277)
    return HandlerReturn(value=value)


def はりきり_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """はりきり特性: 物理技の攻撃補正を1.5倍にする。"""
    if ctx.move.category == "physical":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def はりこみ_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """はりこみ特性: 交代直後の相手に対する攻撃補正を2倍にする。"""
    if (
        ctx.defender is not None
        and battle.player_states[battle.get_player(ctx.defender)].has_switched
    ):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ハードロック_reduce_effective(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """防御側特性: 効果抜群の技ダメージを0.75倍にする。"""
    if battle.query.is_super_effective(ctx):
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def ばけのかわ_block_damage(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ばけのかわを消費して、このヒットの攻撃ダメージを0にする。

    実際のダメージは0になるが、ばけのかわの効果でHPが減少するため
    「攻撃を無効化した」扱いにはならない（きあいパンチ不発の対象）。
    """
    battle.add_ability_disabled_reason(ctx.defender, "consumed")
    battle.modify_hp(ctx.defender, r=-1/8)
    ctx.defender.hits_taken += 1
    _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=0)


def バトルスイッチ_change_form(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 行動前に必要なフォルムへ切り替える。"""
    mon = ctx.attacker
    next_name = ""
    if mon.name == AEGISLASH_SHIELD and ctx.move.is_attack:
        next_name = AEGISLASH_BLADE
    elif mon.name == AEGISLASH_BLADE and ctx.move.name == "キングシールド":
        next_name = AEGISLASH_SHIELD

    if next_name:
        mon.set_form(next_name)
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def バトルスイッチ_revert_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 交代時にシールドフォルムへ戻す。"""
    mon = ctx.source
    if mon.name == AEGISLASH_BLADE:
        mon.set_form(AEGISLASH_SHIELD)
    return HandlerReturn(value=value)


_BARRIER_SCREENS: tuple[str, ...] = ("リフレクター", "ひかりのかべ", "オーロラベール")


def バリアフリー_remove_screens(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バリアフリー特性: 場に出たとき敵味方全体の壁を解除する。"""
    mon = ctx.source
    triggered = False
    for side in battle.side_managers:
        for screen in _BARRIER_SCREENS:
            if side.deactivate(screen):
                triggered = True
    if triggered:
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ばんけん_boost_atk_on_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """ばんけん特性: いかくによるこうげき低下を、こうげきの上昇に変える。"""
    if ctx.stat_change_reason != "いかく" or "atk" not in value:
        return HandlerReturn(value=value)
    return HandlerReturn(value={**value, "atk": 1})


def パステルベール_cure_poison_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """パステルベール特性: 特性が有効化された時点ですでにどく/もうどく状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_ailment_on_enable(battle, ctx, blocked_ailments=["どく", "もうどく"])


def パンクロック_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """パンクロック特性: 音技の威力を1.3倍にする。"""
    if ctx.move.has_flag("sound"):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def パンクロック_reduce_damage(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """パンクロック特性: 音技で受けるダメージを0.5倍にする。"""
    if ctx.move.has_flag("sound"):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


# 天候展開系


def ひでり_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_weather(battle, ctx.source, value, weather="はれ", count=5)


def ひとでなし_modify_critical_rank(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ひとでなし特性: どく/もうどく状態の相手への攻撃を必ず急所にする。"""
    if ctx.defender.has_ailment("どく", "もうどく"):
        value = 10
    return HandlerReturn(value=value)


def ひひいろのこどう_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_weather(battle, ctx.source, value, weather="はれ", count=5)


def ひひいろのこどう_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ひひいろのこどう特性: はれ中の攻撃補正を1.33倍にする。ばんのうがさを持つ場合は無効。"""
    if (
        battle.weather_for(ctx.attacker).sunny
        and ctx.move.category == "physical"
    ):
        value = apply_fixed_modifier(value, 5461)
    return HandlerReturn(value=value)


def ひらいしん_absorb_electric(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """ひらいしん特性: でんき技を無効化し特攻を1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="でんき", stats={"spa": 1})


def ヒーリングシフト_modify_priority(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ヒーリングシフト特性: 回復技・吸収技の優先度を+3する。"""
    if ctx.move.has_flag("heal"):
        value += 3
    return HandlerReturn(value=value)


def びびり_boost_spd_on_fear_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """びびり特性: あく/ゴースト/むしタイプの技でダメージを受けるとすばやさが1段階上がる。"""
    if ctx.move.type not in ("あく", "ゴースト", "むし"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"spe": +1}, source=ctx.attacker):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def びんじょう_copy_stat_rise(battle: Battle, ctx: EventContext, value: dict[Stat, int]) -> HandlerReturn:
    """びんじょう特性: 相手のランク上昇をコピーする。

    相手のびんじょう・ものまねハーブによるコピーで上がった分は、再度のコピー対象にしない。
    """
    if ctx.stat_change_reason in ("びんじょう", "ものまねハーブ"):
        return HandlerReturn(value=value)
    rises = {stat: v for stat, v in value.items() if v > 0}
    if not rises:
        return HandlerReturn(value=value)
    # びんじょう所持者は相手（ctx.target）の敵側
    self_mon = battle.foe(ctx.target)
    if self_mon is None:
        return HandlerReturn(value=value)
    changed = battle.modify_stats(self_mon, rises, source=ctx.target, reason="びんじょう")
    if changed:
        _announce_ability_triggered(battle, self_mon)
    return HandlerReturn(value=value)


_BEAST_BOOST_ORDER: tuple[str, ...] = ("atk", "def", "spa", "spd", "spe")


def ビーストブースト_boost_best_stat_on_ko(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ビーストブースト特性: 攻撃技で倒すと最も実数値が高い能力が1段階上がる。"""
    mon = ctx.attacker
    best_stat = max(_BEAST_BOOST_ORDER, key=lambda s: mon.stats[s])
    if battle.modify_stats(mon, {best_stat: +1}, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ファーコート_boost_B(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ファーコート特性: 物理技に対する防御補正を2倍にする。"""
    if battle.query.deals_physical_damage(ctx.attacker, ctx.move):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ふうりょくでんき_on_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふうりょくでんき特性: 風技のダメージを受けたときじゅうでん状態になる。"""
    if not ctx.move.has_flag("wind"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    battle.volatile_manager.apply(mon, "じゅうでん")
    _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ふうりょくでんき_on_field_activate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふうりょくでんき特性: 味方のおいかぜ発生時にじゅうでん状態になる。"""
    mon = ctx.source
    if (
        mon is None
        or not battle.is_active(mon)
        or value.name != "おいかぜ"
        or not battle.get_side(mon).get("おいかぜ").is_active
    ):
        return HandlerReturn(value=value)
    battle.volatile_manager.apply(mon, "じゅうでん")
    _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def フェアリーオーラ_boost_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """フェアリーオーラ特性: フェアリー技の威力を1.33倍にする。オーラブレイクがいる場合は0.75倍にする。"""
    if ctx.move.type != "フェアリー":
        return HandlerReturn(value=value)
    aura_break = (
        ctx.attacker.ability.name == "オーラブレイク"
        or ctx.defender.ability.name == "オーラブレイク"
    )
    modifier = 3072 if aura_break else 5448
    return HandlerReturn(value=apply_fixed_modifier(value, modifier))


def フェアリースキン_modify_move_type(battle: Battle, ctx: AttackContext, value: Type) -> HandlerReturn:
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="フェアリー")


def フェアリースキン_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")


def ふかしのこぶし_bypass_protect(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """接触技使用時にまもる系の防護を貫通する"""
    if battle.query.is_contact(ctx):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ふかしのこぶし_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まもる系揮発性状態を持つ相手への接触技ダメージを1/4にする"""
    if (
        not battle.query.is_contact(ctx)
        or not ctx.move.is_blocked_by_protect
        or not any(ctx.defender.has_volatile(v) for v in _PROTECT_VOLATILES)
    ):
        return HandlerReturn(value=value)
    return HandlerReturn(value=1024)


def ふくがん_boost_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふくがん特性: 使用技の命中率を1.3倍にする（一撃必殺技を除く）。"""
    if not ctx.move.has_flag("ohko"):
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def ふくつのこころ_boost_spd_on_flinch(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふくつのこころ特性: ひるみ状態になったときすばやさが1段階上がる。"""
    volatile_name = value.name if hasattr(value, "name") else value
    mon = ctx.source
    if (
        volatile_name != "ひるみ"
        or mon is None
    ):
        return HandlerReturn(value=value)
    if battle.modify_stats(mon, {"spe": +1}, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ふくつのたて_boost_B(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふくつのたて特性: 初登場時にぼうぎょが1段階上がる（バトル中1回）。"""
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    battle.add_ability_disabled_reason(mon, "consumed")
    if battle.modify_stats(mon, {"def": +1}, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ふしぎなうろこ_boost_B(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ふしぎなうろこ特性: 状態異常時に物理技への防御補正を1.5倍にする。"""
    if (
        ctx.defender.ailment.is_active
        and battle.query.deals_physical_damage(ctx.attacker, ctx.move)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ふしぎなまもり_block_non_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふしぎなまもり特性: 効果抜群でない攻撃技を無効化する。"""
    if (
        not ctx.move.is_attack
        or battle.query.is_super_effective(ctx)
    ):
        return HandlerReturn(value=value)
    return HandlerReturn(value=False, stop_event=True)


def ふとうのけん_boost_A(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふとうのけん特性: 初登場時にこうげきが1段階上がる（バトル中1回）。"""
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    if battle.modify_stats(mon, {"atk": +1}, source=mon):
        _announce_ability_triggered(battle, mon)
        battle.add_ability_disabled_reason(mon, "consumed")
    return HandlerReturn(value=value)


def ふみん_cure_sleep_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふみん特性: 特性が有効化された時点ですでにねむり状態なら即座に回復する。

    なやみのタネ・なかまづくり等で特性がふみんに書き換わった場合や、
    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合、
    メガシンカで特性がふみんに変わった場合などに発動する。
    """
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    if mon.ailment.is_sleep and battle.ailment_manager.remove(mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ふみん_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_volatile(battle, ctx, value, blocked_volatiles=["ねむけ"])


def ふゆう_float(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ふゆう特性: 常に浮遊状態として扱う。"""
    return HandlerReturn(value=True)


def フラワーギフト_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """フラワーギフト特性（攻撃側）: はれ中にこうげきが1.5倍になる。
    フラワーギフト持ちポケモン（attacker）自身がばんのうがさを持つ場合は無効。
    """
    if battle.weather_for(ctx.attacker).sunny:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def フラワーギフト_modify_def(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """フラワーギフト特性（防御側）: はれ中にとくぼうが1.5倍になる。
    フラワーギフト持ちポケモン（defender）自身がばんのうがさを持つ場合は無効。
    """
    if battle.weather_for(ctx.defender).sunny:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def フラワーベール_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """フラワーベール特性: くさタイプの状態異常を防ぐ。"""
    target = ctx.target
    if target is None or "くさ" not in target.types:
        return HandlerReturn(value=value)
    _announce_ability_triggered(battle, target)
    return HandlerReturn(value=False, stop_event=True)


def フラワーベール_prevent_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """フラワーベール特性: くさタイプへの能力低下を防ぐ。"""
    target = ctx.target
    if target is None or "くさ" not in target.types:
        return HandlerReturn(value=value)
    filtered = {s: v for s, v in value.items() if v >= 0}
    if filtered != value:
        _announce_ability_triggered(battle, target)
    return HandlerReturn(value=filtered)


def フリーズスキン_modify_move_type(battle: Battle, ctx: AttackContext, value: Type) -> HandlerReturn:
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="こおり")


def フリーズスキン_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")


def ぶきよう_disable_item(battle: Battle, ctx: EventContext, value: set[ItemDisabledReason]) -> HandlerReturn:
    battle.item_manager.add_disabled_reason(ctx.source, "ぶきよう")
    return HandlerReturn(value=value)


def ぶきよう_enable_item(battle: Battle, ctx: EventContext, value: set[ItemDisabledReason]) -> HandlerReturn:
    battle.item_manager.remove_disabled_reason(ctx.source, "ぶきよう")
    return HandlerReturn(value=value)


def ブレインフォース_boost_effective(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ブレインフォース特性: 効果抜群のときダメージを1.25倍"""
    if battle.query.is_super_effective(ctx):
        value = apply_fixed_modifier(value, 5120)
    return HandlerReturn(value=value)


def プレッシャー_announce(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """プレッシャー特性: 登場時にアナウンスを出す。"""
    _announce_ability_triggered(battle, ctx.source)
    return HandlerReturn(value=value)


def プレッシャー_extra_pp(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """プレッシャー特性: こちらを対象にした技のPPを1多く消費させる。"""
    return HandlerReturn(value=value + 1)


def ヘドロえき_reverse_drain(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ヘドロえき特性: 吸収技による回復を攻撃者へのダメージに変換する。"""
    if ctx.hp_change_reason != "drain":
        return HandlerReturn(value=value)
    hedoro = battle.foe(ctx.target)
    _announce_ability_triggered(battle, hedoro)
    return HandlerReturn(value=-value)


def へんげんじざい_change_type(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """へんげんじざい・リベロ: 技実行前に技タイプへ自身のタイプを変更する。"""
    move_type = ctx.move.type

    if (
        not ctx.attacker.ability.activated_since_switch_in
        and not ctx.attacker.terastallized
        and [move_type] != ctx.attacker.types
    ):
        ctx.attacker.ability_override_type = move_type
        ctx.attacker.ability.activated_since_switch_in = True
        _announce_ability_triggered(battle, ctx.attacker)
    return HandlerReturn(value=value)


def へんしょく_copy_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """へんしょく特性: 攻撃技を受けた後、その技のタイプになる。"""
    mon = ctx.defender
    move_type = ctx.move.type
    if (
        mon.fainted
        or ctx.hit_index != ctx.hit_count
        or not move_type
        or move_type in mon.types
    ):
        return HandlerReturn(value=value)
    mon.ability_override_type = move_type
    _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def ほうし_maybe_inflict_ailment_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほうし特性: 接触技を受けたとき30%でどく/まひ/ねむりのいずれかを付与。

    Note:
        攻撃側がぼうじんゴーグルを持っている場合は無効（ぼうじんゴーグルの仕様）。
    """
    if (
        not battle.query.is_contact_reaction(ctx)
        or ctx.attacker.has_item("ぼうじんゴーグル")
    ):
        return HandlerReturn(value=value)
    r = battle.random.random()
    ailment: AilmentName | None = next((a for threshold, a in _EFFECT_SPORE_AILMENTS if r < threshold), None)
    if ailment is None:
        return HandlerReturn(value=value)
    battle.ailment_manager.apply(ctx.attacker, ailment, source=ctx.defender, ctx=ctx)
    return HandlerReturn(value=value)


def ほのおのからだ_maybe_burn_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほのおのからだ特性: 直接攻撃を受けた相手を30%でやけどにする。"""
    return _apply_contact_counter_ailment(battle, ctx, value, ailment="やけど", chance=0.3)


def ほろびのボディ_apply_perish_song_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほろびのボディ特性: 直接攻撃を受けると自分と攻撃者の双方にほろびのうたを付与する。"""
    attacker = ctx.attacker
    if (
        not battle.query.is_contact_reaction(ctx)
        or attacker is None
        or attacker.fainted
    ):
        return HandlerReturn(value=value)
    defender = ctx.defender
    triggered = False
    for mon in (defender, attacker):
        if battle.volatile_manager.apply(mon, "ほろびのうた", source=defender):
            triggered = True
    if triggered:
        _announce_ability_triggered(battle, defender)
    return HandlerReturn(value=value)


def ぼうおん_block_sound(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """ぼうおん特性: 音技を無効化する。

    自分や味方（自分自身も含む）を対象とする音技（例: いやしのすず）は、
    相手のぼうおんとは無関係のため、相手を対象とする技（target="foe"）のみを無効化する。
    """
    if (
        not ctx.move.has_flag("sound")
        or ctx.move.target != "foe"
    ):
        return HandlerReturn(value=value)

    _announce_ability_triggered(battle, ctx.defender)
    battle.add_event_log(
        ctx.attacker,
        LogCode.MOVE_IMMUNED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="ぼうおん")
    )
    return HandlerReturn(value=False, stop_event=True)


def ぼうじん_block_powder(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """ぼうじん特性: 粉・胞子系の技を無効化する。"""
    if not ctx.move.has_flag("powder"):
        return HandlerReturn(value=value)

    _announce_ability_triggered(battle, ctx.defender)
    battle.add_event_log(
        ctx.attacker,
        LogCode.MOVE_IMMUNED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="ぼうじん")
    )
    return HandlerReturn(value=False, stop_event=True)


def ぼうじん_block_sandstorm_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ぼうじん特性: すなあらしのダメージを受けない。"""
    return _ignore_sandstorm_damage(battle, ctx, value)


def ぼうだん_block_bullet(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """ぼうだん特性: 弾の技を無効化する。"""
    if not ctx.move.has_flag("bullet"):
        return HandlerReturn(value=value)

    _announce_ability_triggered(battle, ctx.defender)
    battle.add_event_log(
        ctx.attacker,
        LogCode.MOVE_IMMUNED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="ぼうだん")
    )
    return HandlerReturn(value=False, stop_event=True)


def ポイズンヒール_modify_poison_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ポイズンヒール特性: どく/もうどく由来のHP変化を最大HPの1/8回復に置き換える。"""
    if value < 0:
        value = ctx.target.max_hp // 8
    return HandlerReturn(value=value)


def マイティチェンジ_change_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マイティチェンジ特性: ナイーブフォルムで引っ込むとマイティフォルムへ変化する。"""
    mon = ctx.source
    if mon.name == PALAFIN_ZERO and mon.alive:
        mon.set_form(PALAFIN_HERO)
    return HandlerReturn(value=value)


def マイペース_block_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """マイペース特性: いかくによるこうげきランク低下を無効化する (第八世代以降)。"""
    if ctx.stat_change_reason == "いかく":
        value = {}
    return HandlerReturn(value=value)


def マイペース_cure_confusion_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マイペース特性: 特性が有効化された時点ですでにこんらん状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_volatile_on_enable(battle, ctx, blocked_volatiles=["こんらん"])


def マイペース_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_volatile(battle, ctx, value, blocked_volatiles=["こんらん"])


def マグマのよろい_cure_freeze_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マグマのよろい特性: 特性が有効化された時点ですでにこおり状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_ailment_on_enable(battle, ctx, blocked_ailments=["こおり"])


def まけんき_boost_atk_on_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """まけんき特性: 敵から能力を下げられたときこうげきが2段階上昇する。"""
    if (
        any(v < 0 for v in value.values())
        and ctx.source != ctx.target
    ):
        battle.modify_stats(ctx.target, {"atk": +2}, source=ctx.source)
        _announce_ability_triggered(battle, ctx.target)
    return HandlerReturn(value=value)


def マジシャン_steal_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """マジシャン特性: 攻撃成功後に相手のアイテムを奪う。"""
    battle.item_manager.take_item(ctx.defender)
    return HandlerReturn(value=value)


def マジックガード_ignore_damage(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """マジックガード特性: 間接ダメージを無効化する。"""
    # 直接ダメージ・自己由来の特定HP変動・ほろびのうた/みちづれのひんしは無効化しない。
    if ctx.hp_change_reason not in {"move_damage", "pain_split", "self_attack", "self_cost", "perish"}:
        value = 0
    return HandlerReturn(value=value)


def マジックミラー_reflect(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """マジックミラー特性: 反射対象の変化技を跳ね返す。"""
    value = ctx.move.is_reflectable
    if value:
        _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=value)


def マルチスケイル_reduce_damage(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
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


def _overwrite_ability_on_contact(battle: Battle,
                                  ctx: AttackContext,
                                  *,
                                  new_ability: AbilityName) -> bool:
    """直接攻撃でダメージを受けたとき攻撃者の特性を書き換える共通処理。

    Returns:
        書き換えに成功した場合True
    """
    attacker = ctx.attacker
    if not battle.query.is_contact_reaction(ctx):
        return False
    if attacker.ability.has_flag("uncopyable"):
        return False
    if attacker.ability.name == new_ability:
        return False
    battle.change_ability(attacker, new_ability)
    return True


def ミイラ_overwrite_attacker_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミイラ特性: 直接攻撃でダメージを受けたとき攻撃者の特性をミイラにする。"""
    if _overwrite_ability_on_contact(battle, ctx, new_ability="ミイラ"):
        _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=value)


def ミストメイカー_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_terrain(battle, ctx.source, value, terrain="ミストフィールド", count=5)


def みずがため_boost_B_on_water(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みずがため特性: みずタイプの技でダメージを受けるとぼうぎょが2段階上がる。"""
    if ctx.move.type != "みず":
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"def": +2}, source=ctx.attacker):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def みずのベール_cure_burn_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みずのベール特性: 特性が有効化された時点ですでにやけど状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_ailment_on_enable(battle, ctx, blocked_ailments=["やけど"])


def ミラクルスキン_reduce_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミラクルスキン特性: 相手の変化技の命中率を50%に固定する。"""
    if ctx.move.is_attack or value is None:
        return HandlerReturn(value=value)
    return HandlerReturn(value=min(value, 50))


def ミラーアーマー_reflect_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """ミラーアーマー特性: 相手由来の能力ランク低下を反射する。"""
    if (
        not ctx.is_foe_target()
        or ctx.stat_change_reason == "ミラーアーマー"
    ):
        return HandlerReturn(value=value)

    drops = {stat: v for stat, v in value.items() if v < 0}
    if drops:
        # 低下を source（相手）側へ反射（source を ctx.target にすることで「相手から下げられた」扱いになりまけんき等が正常発動）
        battle.modify_stats(ctx.source, drops, source=ctx.target, reason="ミラーアーマー")
        # 自分側の低下分を除去（上昇分は残す）
        value = {stat: v for stat, v in value.items() if v > 0}

        # だっしゅつパック: 自身のランクは実際には変化しないが、跳ね返した時点で発動する
        mon = ctx.target
        if mon.item.name == "だっしゅつパック":
            player = battle.get_player(mon)
            if battle.query.has_available_bench(player):
                battle.player_states[player].interrupt = Interrupt.EJECTPACK_REQUESTED
    return HandlerReturn(value=value)


def ムラっけ_boost_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ムラっけ特性: ターン終了時に1能力+2、別の1能力-1する。"""
    mon = ctx.source
    stats: tuple[Stat, ...] = ("atk", "def", "spa", "spd", "spe")
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
        _announce_ability_triggered(battle, mon)

    return HandlerReturn(value=value)


def メガソーラー_activate(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def メガソーラー_deactivate(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def メガランチャー_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """メガランチャー特性: はどう技の威力を1.5倍にする。"""
    return _modify_by_move_condition(ctx.move, value, modifier=6144, move_flag="pulse")


def メロメロボディ_maybe_infatuate_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メロメロボディ特性: 直接攻撃を受けたとき30%の確率で攻撃者をメロメロにする。"""
    if battle.query.is_contact_reaction(ctx) and battle.random.random() < 0.3:
        battle.volatile_manager.apply(
            ctx.attacker, "メロメロ", source=ctx.defender,
        )
    return HandlerReturn(value=value)


def めんえき_cure_poison_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """めんえき特性: 特性が有効化された時点ですでにどく/もうどく状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_ailment_on_enable(battle, ctx, blocked_ailments=["どく", "もうどく"])


def ものひろい_pickup_foe_item(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ものひろい特性: ターン終了時に自分がアイテムを持っていなければ相手が消費したアイテムを拾う。"""
    mon = ctx.source
    if mon is None or mon.has_item():
        return HandlerReturn(value=value)
    foe = battle.foe(mon)
    item_name = foe.last_lost_item_name
    if not item_name:
        return HandlerReturn(value=value)
    if battle.item_manager.gain_item(mon, item_name):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def もふもふ_modify_damage(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """もふもふ特性: 接触技被ダメ0.5倍・炎技被ダメ2倍を適用する。"""
    if battle.query.is_contact(ctx):
        value = apply_fixed_modifier(value, 2048)
    if ctx.move.type == "ほのお":
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def もらいび_block_fire(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技を無効化し、炎技強化状態を有効化する。"""
    if (
        not ctx.move.target == "foe"
        or ctx.move.type != "ほのお"
    ):
        return HandlerReturn(value=value)

    ctx.defender.ability.state = "charged"
    _announce_ability_triggered(battle, ctx.defender)
    battle.add_event_log(
        ctx.attacker,
        LogCode.MOVE_IMMUNED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="もらいび")
    )
    return HandlerReturn(value=False, stop_event=True)


def もらいび_consume_fire_boost(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もらいび特性: 行動終了時に強化を消費済みにする。"""
    mon = ctx.attacker
    state = mon.ability.state
    if state == "active":
        mon.ability.state = "idle"
    return HandlerReturn(value=value)


def もらいび_init_state(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """もらいび特性: 登場時に炎技強化状態を初期化する。"""
    ctx.source.ability.state = "idle"
    return HandlerReturn(value=value)


def もらいび_modify_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """もらいび特性: 吸収後の最初のほのお技のみ威力を1.5倍にする。"""
    if (
        ctx.move.type == "ほのお"
        and ctx.attacker.ability.state == "active"
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def もらいび_reserve_fire_boost(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技使用時に強化適用予約。"""
    mon = getattr(ctx, "source", None) or getattr(ctx, "attacker", None)
    if (
        ctx.move.type == "ほのお"
        and mon is not None
        and mon.ability.state == "charged"
    ):
        mon.ability.state = "active"
    return HandlerReturn(value=value)


def やるき_cure_sleep_on_enable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """やるき特性: 特性が有効化された時点ですでにねむり状態なら即座に回復する。

    かがくへんかガス・かたやぶりの効果が終わって特性が再び有効になった場合などに発動する。
    """
    return _cure_ailment_on_enable(battle, ctx, blocked_ailments=["ねむり"])


def やるき_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_volatile(battle, ctx, value, blocked_volatiles=["ねむけ"])


def ゆうばく_damage_attacker_on_ko(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆうばく特性: 直接攻撃でひんしになったとき攻撃者に最大HPの1/4ダメージを与える。

    しめりけ特性のポケモンが場にいる場合は発動しない
    （かたやぶり等でしめりけが無効化されている場合は通常通り発動する）。
    この無効化が発生したとき、しめりけ・ゆうばくいずれのメッセージも表示されない
    （docs/spec/abilities/しめりけ.md）。
    """
    attacker = ctx.attacker
    if (
        not battle.query.is_contact_reaction(ctx)
        or attacker.fainted
    ):
        return HandlerReturn(value=value)
    if attacker.ability.enabled and attacker.ability.name == "しめりけ":
        return HandlerReturn(value=value)
    damage = max(1, attacker.max_hp // 4)
    battle.modify_hp(attacker, -damage, reason="ability")
    _announce_ability_triggered(battle, ctx.defender)
    return HandlerReturn(value=value)


def ゆきかき_boost_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ゆきかき特性: ゆき中に素早さが2倍になる。"""
    if battle.weather.name == "ゆき":
        value *= 2
    return HandlerReturn(value=value)


def ゆきがくれ_reduce_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆきがくれ特性: ゆき中に受ける技の命中率を3277/4096倍にする（必中技は除く）。"""
    if battle.weather.name == "ゆき":
        value = apply_fixed_modifier(value, 3277)
    return HandlerReturn(value=value)


def ゆきふらし_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _activate_weather(battle, ctx.source, value, weather="ゆき", count=5)


def ようりょくそ_boost_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ようりょくそ特性: はれ中に素早さが2倍になる。ばんのうがさを持つ場合は無効。"""
    if battle.weather_for(ctx.source).sunny:
        value *= 2
    return HandlerReturn(value=value)


# よちむ仕様: 変化技=0、その他は data.power を使用
def _move_power(move) -> int:
    if move.data.power is None:
        return 0
    return move.data.power


def よちむ_reveal_strongest_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """よちむ特性: 登場時に相手が覚えている技のうち最高威力の技を1つ公開する。
    変化技など威力がない技は威力0として扱う。
    """
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)
    foe = battle.foe(mon)
    if not foe.moves:
        return HandlerReturn(value=value)

    max_power = max(_move_power(m) for m in foe.moves)
    candidates = [m for m in foe.moves if _move_power(m) == max_power]
    chosen = battle.random.choice(candidates)
    chosen.revealed = True
    _announce_ability_triggered(battle, mon)
    battle.add_event_log(
        mon,
        LogCode.TEXT_LOG,
        payload=TextPayload(text=f"{foe.name}の{chosen.name}を読み取った！")
    )
    return HandlerReturn(value=value)


def よびみず_absorb_water(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    """よびみず特性: みず技を無効化し特攻を1段階上げる。"""
    return _apply_type_absorb(battle, ctx, value, move_type="みず", stats={"spa": 1})


def よわき_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """よわき特性: HP半分以下で攻撃補正を0.5倍にする。"""
    if ctx.attacker.hp * 2 <= ctx.attacker.max_hp:
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def リミットシールド_enter_meteor_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リミットシールド特性: 登場時にHP1/2超ならりゅうせいのすがたへフォルムチェンジする。"""
    mon = ctx.source
    if mon.name != METEONO_CORE:
        return HandlerReturn(value=value)
    if mon.hp * 2 > mon.max_hp:
        mon.set_form(METEONO_METEOR)
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def リミットシールド_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リミットシールド特性: りゅうせいのすがた時に全状態異常を無効化する。"""
    if ctx.target.name != METEONO_METEOR:
        return HandlerReturn(value=value)
    return _prevent_ailment(battle, ctx, value)


def リミットシールド_revert_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リミットシールド特性: 交代時にりゅうせいのすがたからコアの姿へ戻す。"""
    mon = ctx.source
    if mon.name == METEONO_METEOR:
        mon.set_form(METEONO_CORE)
    return HandlerReturn(value=value)


def リミットシールド_update_form(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リミットシールド特性: ターン終了時にHPに応じてフォルムを切り替える。"""
    mon = ctx.source
    if mon.name not in (METEONO_CORE, METEONO_METEOR):
        return HandlerReturn(value=value)
    if mon.hp * 2 > mon.max_hp:
        if mon.set_form(METEONO_METEOR):
            _announce_ability_triggered(battle, mon)
    else:
        if mon.set_form(METEONO_CORE):
            _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def りゅうのあぎと_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """りゅうのあぎと特性: ドラゴン技の攻撃補正を1.5倍にする。"""
    return _modify_by_move_condition(ctx.move, value, modifier=6144, move_type="ドラゴン")


def りんぷん_block_secondary_chance(battle: Battle, ctx: AttackContext, value: float) -> HandlerReturn:
    """りんぷん特性: 相手の攻撃技の追加効果を無効化する。"""
    return HandlerReturn(value=0, stop_event=True)


def リーフガード_prevent_ailment(battle: Battle, ctx: EventContext, value: str) -> HandlerReturn:
    """リーフガード特性: にほんばれ/おおひでり中に状態異常付与を防ぐ。ばんのうがさを持つ場合は無効。"""
    if battle.weather_for(ctx.target).sunny:
        _announce_ability_triggered(battle, ctx.target)
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def わざわいのうつわ_reduce_C(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """わざわいのうつわ特性: 自分以外の特攻補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def _apply_multitype(mon: Pokemon, item_table: dict[ItemName, Type]) -> None:
    """道具に応じてポケモンのタイプを変更する共通ロジック。"""
    item_name = mon.item.name if mon.has_item() else ""
    mon.ability_override_type = item_table.get(item_name)

def _block_item_change(mon: Pokemon, unchangable_items: list[ItemName]) -> HandlerReturn:
    """道具の奪取・交換を防ぐ共通ロジック。"""
    item_name = mon.item.name if mon.has_item() else ""
    if item_name in unchangable_items:
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def わざわいのおふだ_reduce_A(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """わざわいのおふだ特性: 自分以外の攻撃補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def わざわいのたま_reduce_D(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """わざわいのたま特性: 自分以外の特防補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def わざわいのつるぎ_reduce_B(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """わざわいのつるぎ特性: 自分以外の防御補正を0.75倍にする。"""
    if ctx.attacker is not ctx.defender:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)


def わたげ_lower_spd_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """わたげ特性: 攻撃を受けたとき攻撃者のすばやさを1段階下げる。"""
    mon = ctx.defender
    attacker = ctx.attacker
    if attacker is None:
        return HandlerReturn(value=value)
    if battle.modify_stats(attacker, {"spe": -1}, source=mon):
        _announce_ability_triggered(battle, mon)
    return HandlerReturn(value=value)


def わるいてぐせ_steal_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """わるいてぐせ特性: 直接攻撃を受けた後に相手のアイテムを奪う。"""
    if (
        battle.query.is_contact(ctx)
        and not ctx.defender.fainted
    ):
        battle.item_manager.take_item(ctx.attacker)
    return HandlerReturn(value=value)
