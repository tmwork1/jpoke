"""技関連のハンドラ基盤モジュール。

MoveHandler クラスと攻撃技・変化技ハンドラ共通のユーティリティ関数を提供します。
攻撃技ハンドラは move_attack.py、変化技ハンドラは move_status.py を参照してください。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, AttackContext
    from jpoke.types import RoleSpec, Stat, AilmentName, VolatileName

from jpoke.core import Handler, HandlerReturn
from jpoke.enums import LogCode


class MoveHandler(Handler):
    """技ハンドラの派生クラス。

    技の効果を実装する際に使用します。
    """

    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "attacker:self",
                 priority: int = 100):
        """MoveHandlerを初期化する。

        Args:
            func: イベント発生時に呼ばれる処理関数
            subject_spec: ハンドラの対象を指定するロール
            priority: ハンドラの優先度
        """
        super().__init__(
            func=func,
            source="move",
            subject_spec=subject_spec,
            priority=priority,
            skip_subject_check=True,  # 技ハンドラはコンテキストの攻守を直接参照するため、主体の照合をスキップする
        )


def modify_attacker_stats(battle: Battle,
                          ctx: AttackContext,
                          value: Any,
                          stats: dict[Stat, int],
                          chance: float = 1) -> HandlerReturn:
    """攻撃側の能力ランクを変化させる。"""
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.modify_stats(ctx.attacker, stats, source=ctx.attacker))


def modify_defender_stats(battle: Battle,
                          ctx: AttackContext,
                          value: Any,
                          stats: dict[Stat, int],
                          chance: float = 1) -> HandlerReturn:
    """防御側の能力ランクを変化させる。"""
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.modify_stats(ctx.defender, stats, source=ctx.attacker))


def apply_ailment_to_defender(battle: Battle,
                              ctx: AttackContext,
                              value: Any,
                              ailment: AilmentName,
                              count: int | None = None,
                              chance: float = 1) -> HandlerReturn:
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.ailment_manager.apply(
        ctx.defender, ailment, count=count, source=ctx.attacker, ctx=ctx
    ))


def apply_volatile_to_attacker(battle: Battle,
                               ctx: AttackContext,
                               value: Any,
                               volatile: VolatileName,
                               count: int | None = None,
                               chance: float = 1,
                               **kwargs) -> HandlerReturn:
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.attacker, volatile, count=count, source=ctx.attacker, **kwargs
    ))


def apply_volatile_to_defender(battle: Battle,
                               ctx: AttackContext,
                               value: Any,
                               volatile: VolatileName,
                               count: int | None = None,
                               chance: float = 1,
                               **kwargs) -> HandlerReturn:
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, volatile, count=count, source=ctx.attacker, **kwargs
    ))


def apply_confusion_to_defender(battle: Battle,
                               ctx: AttackContext,
                               value: Any,
                               chance: float = 1) -> HandlerReturn:
    """こんらん状態をランダムターン数（2〜5）で防御者に付与するヘルパー。"""
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def gravity_restricted_fail(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうりょく中にこの技を失敗させる。

    gravity_restricted フラグを持つ技に登録し、
    じゅうりょくが有効な場合に技を失敗させる。
    """
    if battle.get_global_field("じゅうりょく").is_active:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "じゅうりょく"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def charge_into_volatile(battle: Battle,
                         ctx: AttackContext,
                         value: Any,
                         volatile: VolatileName) -> HandlerReturn:
    """半透明技の1ターン目：揮発状態を付与して技を停止する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在のイベント値
        volatile: 付与する揮発状態名（技名と同一）

    Returns:
        HandlerReturn: ためターンなら False/stop_event=True、2ターン目なら value をそのまま返す
    """
    attacker = ctx.attacker
    if not attacker.has_volatile(volatile):
        battle.volatile_manager.apply(attacker, volatile, count=1, source=attacker)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)
