"""イベント駆動システムの中核を担うモジュール。

バトル中に発生する様々なイベントを管理し、登録されたハンドラを適切なタイミングで実行します。
特性、技、アイテムなどの効果発動を統一的に処理するイベントシステムを提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, Handler, Player
    from jpoke.model import Pokemon

from jpoke.enums import DomainEvent, Event
from jpoke.utils import fast_copy

from .context import BaseContext, EventContext
from .handler import HandlerReturn, RegisteredHandler


class EventManager:
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
        self.battle = battle
        self.handlers: dict[Event | DomainEvent, list[RegisteredHandler]] = {}

    def __deepcopy__(self, memo):
        """EventManagerインスタンスのディープコピーを作成する。

        Args:
            memo: コピー済みオブジェクトのメモ辞書

        Returns:
            EventManager: コピーされたEventManagerインスタンス
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new, keys_to_deepcopy=["handlers"])

    def update_reference(self, new: Battle):
        """ディープコピー後のBattleインスタンスへの参照を更新する。

        ハンドラが参照するポケモンやプレイヤーを新しいBattleインスタンスのものに置き換える。

        Args:
            new: 新しいBattleインスタンス
        """
        # ハンドラの対象に指定されているポケモンまたはプレイヤーへの参照を更新する
        old = self.battle
        for handlers in self.handlers.values():
            for rh in handlers:
                rh.update_reference(old, new)

        # Battle への参照を更新する
        self.battle = new

    def _resolve_subject(self, rh: RegisteredHandler) -> Pokemon | None:
        return rh.get_subject(self.battle)

    def on(self,
           event: Event | DomainEvent,
           handler: Handler,
           subject: Pokemon | Player):
        """イベントにハンドラを登録する。

        Args:
            event: 登録するイベントタイプ
            handler: ハンドラ定義
            subject: ハンドラの主体（ポケモンまたはプレイヤー）
        """
        self.handlers.setdefault(event, []).append(
            RegisteredHandler(handler, subject)
        )

    def off(self,
            event: Event | DomainEvent,
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
            if not (rh.handler == handler and rh.registered_subject == subject)
        ]
        if not self.handlers[event]:
            del self.handlers[event]

    def emit(self,
             event: Event | DomainEvent,
             ctx: BaseContext | None = None,
             value: Any = None,
             stop_if_winner_determined: bool = False) -> Any:
        """イベントを発火し、登録されたハンドラを実行する。

        優先度とポケモンの素早さに基づいてハンドラを順次実行します。
        ハンドラは値を連鎖的に変更でき、最終的な値が返されます。

        Args:
            event: 発火するイベントタイプ
            ctx: コンテキスト（Noneの場合は自動構築）
            value: ハンドラ間で受け渡す初期値
            stop_if_winner_determined: Trueの場合、ハンドラ実行後に
                `self.battle.winner` が確定した時点で残りのハンドラの
                実行を打ち切る。Event.ON_TURN_END のように、異なる
                ポケモンを対象とする複数のハンドラ（どく・やけど等の
                継続ダメージ）を素早さ順にまとめて処理するイベントで、
                先に処理された個体の瀕死により決着した後、決着に無関係な
                他個体のハンドラが実行され続けるのを防ぐために使う

        Returns:
            Any: 全ハンドラ実行後の最終値
        """
        # ソート時にドメインイベントを発火して素早さ計算を行うため、
        # ドメインイベントはソートせずに発火して再帰を防ぐ
        # （ハンドラ内での on/off に耐えるようコピーをイテレートする）
        if isinstance(event, DomainEvent):
            handlers = list(self.handlers.get(event, []))
        else:
            handlers = self._sort_handlers(self.handlers.get(event, []))

        for rh in handlers:
            context = ctx if ctx else self._build_context(rh)

            # ハンドラが現在のコンテキストで有効かどうかをチェックする
            # （subject_spec が指すポケモンが既に瀕死の場合のスキップ判定を含む）
            if not self._check_handler_validity(rh, context):
                continue

            result = rh.handler.func(self.battle, context, value)

            if not isinstance(result, HandlerReturn):
                raise ValueError("Handler function must return HandlerReturn")

            # 一度きりのハンドラを解除
            if rh.handler.once:
                self.off(event, rh.handler, rh.registered_subject)

            value = result.value

            # イベント停止フラグの処理
            if result.stop_event:
                return value

            # このハンドラの実行中に勝敗が確定した場合、以降の
            # （決着に無関係な別個体向けの）ハンドラは実行しない
            if stop_if_winner_determined and self.battle.winner is not None:
                break

        return value

    def _build_context(self, rh: RegisteredHandler) -> BaseContext:
        """ハンドラに対応するコンテキストを構築"""
        mon = self._resolve_subject(rh)
        if rh.handler.side == "foe":
            assert mon is not None
            mon = self.battle.foe(mon)
        role = rh.handler.role
        if role == "target":
            return EventContext(target=mon)
        return EventContext(source=mon)

    def _sort_handlers(self, rhs: list[RegisteredHandler]) -> list[RegisteredHandler]:
        """ハンドラを優先度と素早さに基づいてソートする。

        Args:
            rhs: ソート対象のRegisteredHandlerリスト

        Returns:
            list[RegisteredHandler]: ソート後のリスト
        """
        if len(rhs) <= 1:
            return list(rhs)

        def key(rh: RegisteredHandler):
            subject = self._resolve_subject(rh)
            assert subject is not None
            speed = self.battle.speed_calculator.calc_effective_speed(subject)
            return (rh.handler.priority, -speed)

        return sorted(rhs, key=key)

    def _check_handler_validity(self, rh: RegisteredHandler, ctx: BaseContext) -> bool:
        """ハンドラが現在のコンテキストで有効かどうかをチェックする。"""
        subject = self._resolve_subject(rh)
        if (
            not rh.handler.skip_subject_check
            and subject != ctx.resolve_role(self.battle, rh.handler.subject_spec)
        ):
            # print(f"Context mismatch: Handler {rh.handler.func} skipped")
            return False

        # subject_spec が指すポケモンが既に瀕死ならスキップする。
        # Event.ON_MOVE_KO のように、瀕死になった当のポケモン自身の効果が
        # 発動すべきハンドラは Handler.allow_fainted_subject=True で明示的に除外する。
        if not rh.handler.allow_fainted_subject:
            role_mon = ctx.resolve_role(self.battle, rh.handler.subject_spec)
            if role_mon is not None and role_mon.fainted:
                return False

        # ハンドラの発生源が無効化されている場合はスキップ
        match rh.handler.source:
            case "ability":
                assert subject is not None
                if not subject.ability.enabled_ignoring(rh.handler.ignored_disable_reasons):
                    return False
            case "item":
                assert subject is not None
                if not subject.item.enabled_ignoring(rh.handler.ignored_disable_reasons):
                    return False
            case "ailment":
                assert subject is not None
                if not subject.ailment.is_active:
                    return False

        return True
