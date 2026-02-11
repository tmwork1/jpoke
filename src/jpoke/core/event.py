"""イベント駆動システムの中核を担うモジュール。

バトル中に発生する様々なイベントを管理し、登録されたハンドラを適切なタイミングで実行します。
特性、技、持ち物などの効果発動を統一的に処理するイベントシステムを提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import BattleContext, Battle

from jpoke.enums import Event
from .handler_manager import BaseHandlerManager
from .handler import HandlerReturn, RegisteredHandler


class EventManager(BaseHandlerManager):
    """イベントとハンドラを管理するクラス。

    イベントの発火、ハンドラの登録・解除、優先度制御などを行います。

    Attributes:
        battle: バトルインスタンス
        handlers: イベントタイプごとの登録済みハンドラリスト
    """

    def __init__(self, battle: Battle) -> None:
        """EventManagerを初期化する。

        Args:
            battle: バトルインスタンス
        """
        super().__init__(battle)

    def emit(self,
             event: Event,
             ctx: BattleContext | None = None,
             value: Any = None) -> Any:
        """イベントを発火し、登録されたハンドラを実行する。

        優先度とポケモンの素早さに基づいてハンドラを順次実行します。
        ハンドラは値を連鎖的に変更でき、最終的な値が返されます。

        Args:
            event: 発火するイベントタイプ
            ctx: コンテキスト（Noneの場合は自動構築）
            value: ハンドラ間で受け渡す初期値

        Returns:
            Any: 全ハンドラ実行後の最終値
        """
        for rh in self._sort_handlers(self.handlers.get(event, [])):
            # print(event, rh)
            context = ctx if ctx else self._build_context(rh)

            if not self._match(context, rh):
                # print(f"  Handler skipped: {rh}")
                continue

            result = rh.handler.func(self.battle, context, value)

            if not isinstance(result, HandlerReturn):
                raise ValueError("Handler function must return HandlerReturn")

            if result.value is not None:
                value = result.value

            # log_policy に基づいてログを出力
            rh.handler.write_log(self.battle, context, result.success)

            # 一度きりのハンドラを解除
            if rh.handler.once:
                self.off(event, rh.handler, rh._subject)

            # イベント停止フラグの処理
            if result.stop_event:
                return value

        return value

    def _sort_handlers(self, rhs: list[RegisteredHandler]) -> list[RegisteredHandler]:
        if len(rhs) <= 1:
            return rhs

        def key(rh: RegisteredHandler):
            from jpoke.core import Player
            subject = rh.subject
            # Playerの場合はactiveポケモンに変換
            if isinstance(subject, Player):
                subject = subject.active
                if subject is None:
                    return (rh.handler.priority, 0)

            # battle -> speed_calculator 内部でON_CALC_SPEEDイベント発火で無限ループになっている
            speed = self.battle.calc_effective_speed(subject)
            return (rh.handler.priority, -speed)

        return sorted(rhs, key=key)
