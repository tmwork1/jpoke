"""イベント駆動システムの中核を担うモジュール。

バトル中に発生する様々なイベントを管理し、登録されたハンドラを適切なタイミングで実行します。
特性、技、持ち物などの効果発動を統一的に処理するイベントシステムを提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, Player
    from jpoke.model import Pokemon

from jpoke.enums import Event
from jpoke.utils import fast_copy

from .handler import Handler, RegisteredHandler
from .context import BattleContext


class BaseHandlerManager:
    """イベントとハンドラを管理するクラス。

    イベントの発火、ハンドラの登録・解除、優先度制御などを行います。

    Attributes:
        battle: バトルインスタンス
        handlers: イベントタイプごとの登録済みハンドラリスト
    """

    def __init__(self, battle: Battle) -> None:
        """BaseHandlerManagerを初期化する。

        Args:
            battle: バトルインスタンス
        """
        self.battle = battle
        self.handlers: dict[Event, list[RegisteredHandler]] = {}

    def __deepcopy__(self, memo):
        """BaseHandlerManagerインスタンスのディープコピーを作成する。

        Args:
            memo: コピー済みオブジェクトのメモ辞書

        Returns:
            BaseHandlerManager: コピーされたBaseHandlerManagerインスタンス
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def update_reference(self, new: Battle):
        """ディープコピー後のBattleインスタンスへの参照を更新する。

        ハンドラが参照するポケモンやプレイヤーを新しいBattleインスタンスのものに置き換えます。

        Args:
            new: 新しいBattleインスタンス
        """
        old = self.battle

        # ハンドラの対象に指定されているポケモンまたはプレイヤーへの参照を更新する
        for event, data in self.handlers.items():
            for i, _ in enumerate(data):
                self.handlers[event][i].update_reference(old, new)

        # Battle への参照を更新する
        self.battle = new

    def on(self,
           event: Event,
           handler: Handler,
           subject: Pokemon | Player):
        """イベントにハンドラを登録する。

        Args:
            event: 登録するイベントタイプ
            handler: ハンドラ定義
            subject: ハンドラの対象（ポケモンまたはプレイヤー）
        """
        # print(f"Register handler: {event} {handler} {subject}")
        self.handlers.setdefault(event, []).append(
            RegisteredHandler(handler, subject)
        )

    def off(self,
            event: Event,
            handler: Handler,
            subject: Pokemon | Player):
        """イベントからハンドラを解除する。

        Args:
            event: 解除するイベントタイプ
            handler: ハンドラ定義
            subject: ハンドラの対象（ポケモンまたはプレイヤー）
        """
        if event not in self.handlers:
            return
        self.handlers[event] = [
            rh for rh in self.handlers[event]
            if not (rh.handler == handler and rh._subject == subject)
        ]

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
        raise NotImplementedError()

    def _build_context(self, rh: RegisteredHandler) -> BattleContext:
        """ハンドラに対応するコンテキストを構築"""
        if rh.handler.side == "self":
            mon = rh.subject
        else:
            mon = self.battle.foe(rh.subject)
        return BattleContext(**{rh.handler.role: mon})

    def _match(self, ctx: BattleContext, rh: RegisteredHandler) -> bool:
        """コンテキストがハンドラにマッチするか判定"""
        # コンテキストの対象の判定
        ctx_mon = ctx.get(rh.handler.role)
        if ctx_mon is None:
            return False

        # ハンドラの対象の判定
        if rh.handler.side == "self":
            return ctx_mon == rh.subject
        else:
            return ctx_mon == self.battle.foe(rh.subject)
