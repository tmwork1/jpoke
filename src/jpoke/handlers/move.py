"""技関連のハンドラ基盤モジュール。

MoveHandler クラスと攻撃技・変化技ハンドラ共通のユーティリティ関数を提供します。
攻撃技ハンドラは move_attack.py、変化技ハンドラは move_status.py を参照してください。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext
    from jpoke.utils.type_defs import RoleSpec, Stat, AilmentName, VolatileName

from jpoke.core import Handler, HandlerReturn
from . import common


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
                          ctx: EventContext,
                          value: Any,
                          stats: dict[Stat, int],
                          chance: float = 1) -> HandlerReturn:
    """攻撃側の能力ランクを変化させる。"""
    return common.modify_stats(
        battle, ctx, value, stats,
        target_spec="attacker:self", source_spec="attacker:self", chance=chance
    )


def modify_defender_stats(battle: Battle,
                          ctx: EventContext,
                          value: Any,
                          stats: dict[Stat, int],
                          chance: float = 1) -> HandlerReturn:
    """防御側の能力ランクを変化させる。"""
    return common.modify_stats(
        battle, ctx, value, stats,
        target_spec="defender:self", source_spec="attacker:self", chance=chance
    )


def apply_ailment_to_defender(battle: Battle,
                              ctx: EventContext,
                              value: Any,
                              ailment: AilmentName,
                              count: int | None = None,
                              chance: float = 1) -> HandlerReturn:
    return common.apply_ailment(
        battle, ctx, value, target_spec="defender:self", ailment=ailment,
        count=count, source_spec="attacker:self", chance=chance
    )


def apply_volatile_to_attacker(battle: Battle,
                               ctx: EventContext,
                               value: Any,
                               volatile: VolatileName,
                               count: int | None = None,
                               chance: float = 1,
                               **kwargs) -> HandlerReturn:
    return common.apply_volatile(
        battle, ctx, value, target_spec="attacker:self", volatile=volatile,
        count=count, source_spec="attacker:self", chance=chance, **kwargs
    )


def apply_volatile_to_defender(battle: Battle,
                               ctx: EventContext,
                               value: Any,
                               volatile: VolatileName,
                               count: int | None = None,
                               chance: float = 1,
                               **kwargs) -> HandlerReturn:
    return common.apply_volatile(
        battle, ctx, value, target_spec="defender:self", volatile=volatile,
        count=count, source_spec="attacker:self", chance=chance, **kwargs
    )
