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

    # おうごんのからだじゃなければ防がない
    if def_ability.name != "おうごんのからだ":
        return HandlerReturn(value=value)

    # ログ出力
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "おうごんのからだ", "success": True}
    )

    return HandlerReturn(value=True, stop_event=True)
