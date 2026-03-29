"""特性ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec
from jpoke.enums import Event, LogCode
from jpoke.core import HandlerReturn, Handler
from . import common


class AbilityHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            subject_spec=subject_spec,
            source_type="ability",
            priority=priority,
            once=once,
        )


PARADOX_ABILITIES = {"こだいかっせい", "クォークチャージ"}
PARADOX_STAT_ORDER = ("A", "B", "C", "D", "S")
PARADOX_FIELD_BY_ABILITY = {
    "こだいかっせい": "はれ",
    "クォークチャージ": "エレキフィールド",
}
PARADOX_FIELD_SOURCE_BY_ABILITY = {
    "こだいかっせい": "weather",
    "クォークチャージ": "terrain",
}


def _rank_modifier(v: int) -> float:
    return (2 + v) / 2 if v >= 0 else 2 / (2 - v)


def _effective_stat_with_rank(mon, stat: str) -> float:
    return mon.stats[stat] * _rank_modifier(mon.rank[stat])


def _select_paradox_boost_stat(mon) -> str:
    best_stat = ""
    best_value = -1.0
    for stat in PARADOX_STAT_ORDER:
        value = _effective_stat_with_rank(mon, stat)
        if value > best_value:
            best_stat = stat
            best_value = value
    return best_stat


def _is_paradox_field_active(battle: Battle, ability_name: str) -> bool:
    if ability_name == "こだいかっせい":
        return battle.weather.name == PARADOX_FIELD_BY_ABILITY[ability_name]
    return battle.terrain.name == PARADOX_FIELD_BY_ABILITY[ability_name]


def _can_consume_boost_energy(mon) -> bool:
    return mon.item.name == "ブーストエナジー" and mon.item.enabled


def _deactivate_paradox_boost(mon) -> None:
    mon.paradox_boost_active = False
    mon.paradox_boost_stat = ""
    mon.paradox_boost_source = ""


def _activate_paradox_boost(battle: Battle, mon, source: str) -> None:
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

    if source == "item" and mon.item.name == "ブーストエナジー" and mon.item.enabled:
        battle.add_event_log(mon, LogCode.CONSUME_ITEM, payload={"item": "ブーストエナジー"})
        mon.item.consume()
        mon.paradox_item_activated_once = True


def _refresh_paradox_boost(battle: Battle, mon) -> None:
    ability_name = mon.ability.orig_name
    if ability_name not in PARADOX_ABILITIES:
        return

    field_source = PARADOX_FIELD_SOURCE_BY_ABILITY[ability_name]
    field_active = _is_paradox_field_active(battle, ability_name)
    can_consume_item = _can_consume_boost_energy(mon) and not mon.paradox_item_activated_once

    if mon.paradox_boost_active:
        if mon.paradox_boost_source == "item":
            return
        if mon.paradox_boost_source == field_source and field_active:
            return

        _deactivate_paradox_boost(mon)
        if can_consume_item:
            _activate_paradox_boost(battle, mon, "item")
        return

    if field_active:
        _activate_paradox_boost(battle, mon, field_source)
        return

    if can_consume_item:
        _activate_paradox_boost(battle, mon, "item")


def パラドックスチャージ_refresh(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    _refresh_paradox_boost(battle, ctx.source)
    return HandlerReturn(value=value)


def パラドックスチャージ_on_calc_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    mon = ctx.source
    if mon.paradox_boost_active and mon.paradox_boost_stat == "S":
        value = value * 6144 // 4096
    return HandlerReturn(value=value)


def パラドックスチャージ_on_calc_atk_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
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
    move_category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    stat = "B" if move_category == "物理" or ctx.move.has_label("physical") else "D"

    if ctx.defender.paradox_boost_active and ctx.defender.paradox_boost_stat == stat:
        value = value * 5325 // 4096
    return HandlerReturn(value=value)


def ありじごく(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
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


def かげふみ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
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
    result = ctx.source.ability != "かげふみ"
    return HandlerReturn(value=result)


def かがくへんかガス_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かがくへんかガス特性: 場の特性有効状態を再計算する。"""
    battle.refresh_ability_enabled_states()

    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "かがくへんかガス", "success": True}
    )
    return HandlerReturn(value=value)


def じりょく(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
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


def かちき(battle: Battle, ctx: BattleContext, value: dict[str, int]) -> HandlerReturn:
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


def すなかき(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すなかき特性: すなあらし中に素早さが2倍になる。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 元の素早さ値

    Returns:
        HandlerReturn: (True, 補正後の素早さ)
            - すなあらし中は2倍、それ以外は元の値
    """
    value = value * 2 if battle.weather.name == "すなあらし" else value
    return HandlerReturn(value=value)


def てつのこぶし(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """てつのこぶし特性: パンチ技の威力を1.2倍にする。"""
    if ctx.move.has_label("punch"):
        value = value * 4915 // 4096
    return HandlerReturn(value=value)


def めんえき(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """めんえき特性: どく・もうどく状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - どく/もうどくの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # どく・もうどく状態を防ぐ
    if value in ["どく", "もうどく"]:
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add(battle.turn, idx, LogCode.ABILITY_TRIGGERED, payload={"ability": "めんえき", "success": True})
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def ふみん(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ふみん特性: ねむり状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - ねむりの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # ねむり状態を防ぐ
    if value == "ねむり":
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add(battle.turn, idx, LogCode.ABILITY_TRIGGERED, payload={"ability": "ふみん", "success": True})
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def やるき(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """やるき特性: ねむり状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - ねむりの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # ねむり状態を防ぐ（ふみんと同じ効果）
    if value == "ねむり":
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add(battle.turn, idx, LogCode.ABILITY_TRIGGERED, payload={"ability": "やるき", "success": True})
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def マイペース(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
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


def じゅうなん(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """じゅうなん特性: まひ状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - まひの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # まひ状態を防ぐ
    if value == "まひ":
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def みずのベール(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """みずのベール特性: やけど状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - やけどの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # やけど状態を防ぐ
    if value == "やけど":
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def マグマのよろい(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """マグマのよろい特性: こおり状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - こおりの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # こおり状態を防ぐ
    if value == "こおり":
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


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
    if value in ["メロメロ", "ちょうはつ", "ゆうわく", "いかく"]:
        return HandlerReturn(value="", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(value=value)


def おうごんのからだ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
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
    # 場対象技は防がない
    if ctx.move.field_targeting:
        return HandlerReturn(value=value)

    # 変化技以外は防がない
    if ctx.move.category != "変化":
        return HandlerReturn(value=value)

    # 自分対象技は防がない
    if ctx.move.self_targeting:
        return HandlerReturn(value=value)

    # 自分が使う変化技は防がない（同じポケモン）
    if ctx.attacker == ctx.target:
        return HandlerReturn(value=value)

    # 防御側特性を確認（かたやぶり・きんしのちから対応）
    def_ability = battle.events.emit(
        Event.ON_CHECK_DEF_ABILITY,
        ctx,
        ctx.target.ability,
    )

    # おうごんのからだじゃなければ防がない（かたやぶり等でNoneになった場合も含む）
    if def_ability is None or def_ability.name != "おうごんのからだ":
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

    かがくへんかガスが場に発動していると、以下を除く特性を無効化する：
    - かがくへんかガス自身
    - undeniable フラグを持つ特性（別ハンドラで復元）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_ABILITY_ENABLED)
            - source: 判定対象のポケモン
        should_enable: 現在の有効化状態

    Returns:
        HandlerReturn: ガス発動中で無効化対象なら False、それ以外は should_enable をそのまま返す
    """
    # 判定対象のポケモンが既に無効化されていたら、その状態を保持
    if not should_enable:
        return HandlerReturn(value=should_enable)

    # かがくへんかガスが発動中か判定
    actives = [mon for mon in battle.actives if mon is not None]
    gas_active = any(
        mon.alive and
        mon.ability.orig_name == "かがくへんかガス" and
        not mon.has_volatile("とくせいなし")
        for mon in actives
    )

    if not gas_active:
        return HandlerReturn(value=should_enable)

    # ガス発動中なので、自身がかがくへんかガスでない限り、無効化を検討
    source_ability = ctx.source.ability
    if source_ability.orig_name == "かがくへんかガス":
        # かがくへんかガス自身は無効化されない
        return HandlerReturn(value=True)

    # それ以外は無効化
    return HandlerReturn(value=False)


def undeniable_check_enabled(battle: Battle, ctx: BattleContext, should_enable: bool) -> HandlerReturn:
    """undeniable フラグ保護判定（priority=20）。

    undeniable フラグを持つ特性は、かがくへんかガスなどによる無効化を
    受けない。このハンドラはガス判定の後に評価され、該当特性を保護する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_ABILITY_ENABLED)
            - source: 判定対象のポケモン
        should_enable: 現在の有効化状態

    Returns:
        HandlerReturn: undeniable フラグ持ちなら True（保護）、それ以外は should_enable をそのまま返す
    """
    source_ability = ctx.source.ability
    # SV仕様では こだいかっせい / クォークチャージ は
    # かがくへんかガスで無効化されるため、undeniable 保護の対象外にする。
    if source_ability.orig_name in PARADOX_ABILITIES:
        return HandlerReturn(value=should_enable)

    if "undeniable" in source_ability.data.flags:
        return HandlerReturn(value=True)
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
    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": ctx.source.ability.name, "success": True}
    )
    return HandlerReturn(value=value)


def かたやぶり_check_def_ability(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かたやぶり系特性: 無視できる防御側特性をNoneに変換する (ON_CHECK_DEF_ABILITY, priority=100)。

    かたやぶり / ターボブレイズ / テラボルテージ で共用。
    防御側が とくせいガード を持つ場合は、とくせいガード側ハンドラ (priority=200) が
    値を元に戻すことで無視が打ち消される。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_DEF_ABILITY)
            - attacker: かたやぶり系特性所持ポケモン
            - defender: 防御側のポケモン
        value: 現在の防御側特性（Ability または None）

    Returns:
        HandlerReturn: 無視できる特性の場合はNone、それ以外はvalueをそのまま返す
    """
    defender_ability = ctx.defender.ability
    if "mold_breaker_ignorable" in defender_ability.data.flags:
        return HandlerReturn(value=None)
    return HandlerReturn(value=value)
