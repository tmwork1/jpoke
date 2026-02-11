"""ドメイン処理を管理するモジュール。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import BattleContext, Battle

from jpoke.enums import Event
from .handler_manager import BaseHandlerManager
from .handler import HandlerReturn


class DomainManager(BaseHandlerManager):
    """ドメインとハンドラを管理するクラス。

    ドメイン処理の発火、ハンドラの登録・解除、優先度制御などを行います。

    Attributes:
        battle: バトルインスタンス
        handlers: ドメイン処理タイプごとの登録済みハンドラリスト
    """

    def __init__(self, battle: Battle) -> None:
        """
        Args:
            battle: バトルインスタンス
        """
        super().__init__(battle)

    def emit(self,
             event: Event,
             ctx: BattleContext | None = None,
             value: Any = None) -> Any:
        """ドメイン処理を発火し、登録されたハンドラを実行する。

        ハンドラを登録された順に実行します。
        ハンドラは値を連鎖的に変更でき、最終的な値が返されます。

        Args:
            event: 発火するイベントタイプ
            ctx: コンテキスト（Noneの場合は自動構築）
            value: ハンドラ間で受け渡す初期値

        Returns:
            Any: 全ハンドラ実行後の最終値
        """
        for rh in self.handlers.get(event, []):
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
