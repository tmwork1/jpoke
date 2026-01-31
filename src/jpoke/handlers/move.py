"""技関連のイベントハンドラ関数を提供するモジュール。

技の実行に関連するハンドラ関数を提供します。
PP消費、交代技、吹き飛ばし技などの処理を行います。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.type_defs import RoleSpec, LogPolicy
from jpoke.utils.enums import Event, Interrupt
from jpoke.core.event import Handler, EventContext, HandlerReturn


class MoveHandler(Handler):
    """技ハンドラの派生クラス。

    source_type="move" と log="never" をデフォルトとして設定します。
    技の効果を実装する際に使用します。
    """

    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "attacker:self",
                 log: LogPolicy = "never",
                 log_text: str | None = None,
                 priority: int = 100):
        """MoveHandlerを初期化する。

        Args:
            func: イベント発生時に呼ばれる処理関数
            subject_spec: ログ出力対象のロール指定
            log: ログ出力ポリシー ("always", "on_success", "never")
            log_text: カスタムログテキスト（Noneの場合は技名を使用）
            priority: ハンドラの優先度
        """
        super().__init__(func, subject_spec, "move", log, log_text, priority)


def consume_pp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """技のPPを消費する。

    技を使用した際にPPを減らします。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue（成功）を返す
    """
    v = battle.events.emit(Event.ON_CHECK_PP_CONSUMED, ctx, 1)
    ctx.move.pp = max(0, ctx.move.pp - v)
    battle.add_event_log(ctx.attacker, f"PP -{v}")
    ctx.attacker.pp_consumed_moves.append(ctx.move)
    return HandlerReturn(True)


def pivot(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """交代技の効果を発動する。

    とんぼがえり、ボルトチェンジなどの交代技で、攻撃後に交代を行います。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 交代が可能な場合はTrue、不可能な場合はFalse
    """
    player = battle.find_player(ctx.attacker)
    success = bool(battle.get_available_switch_commands(player))
    if success:
        player.interrupt = Interrupt.PIVOT
    return HandlerReturn(success)


def blow(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の効果を発動する。

    ほえる、ふきとばしなどで、相手を強制的に交代させます。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 吹き飛ばしが成功した場合はTrue、失敗した場合はFalse
    """
    player = battle.find_player(ctx.defender)
    commands = battle.get_available_switch_commands(player)
    success = bool(commands)
    if success:
        command = battle.random.choice(commands)
        battle.run_switch(player, player.team[command.idx])
    return HandlerReturn(success)
