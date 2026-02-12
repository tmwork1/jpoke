"""イベント駆動システムの中核を担うモジュール。

バトル中に発生する様々なイベントを管理し、登録されたハンドラを適切なタイミングで実行します。
特性、技、持ち物などの効果発動を統一的に処理するイベントシステムを提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, Handler
    from jpoke.model import Pokemon, Player

from jpoke.enums import DomainEvent, Event
from jpoke.utils import fast_copy

from .context import BattleContext
from .handler import HandlerReturn, RegisteredHandler


class EventManager:
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

        # ドメインイベントはソートしない
        # ソート処理にイベント発火が含まれるため、無限ループになる可能性がある
        if isinstance(event, DomainEvent):
            handlers = self.handlers.get(event, [])
        else:
            handlers = self._sort_handlers(self.handlers.get(event, []))

        for rh in handlers:
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
