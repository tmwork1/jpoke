"""イベント駆動システムの中核を担うモジュール。

バトル中に発生する様々なイベントを管理し、登録されたハンドラを適切なタイミングで実行します。
特性、技、持ち物などの効果発動を統一的に処理するイベントシステムを提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, NamedTuple
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Move, Pokemon, Field

from typing import Callable
from dataclasses import dataclass

from jpoke.utils.type_defs import ContextRole, RoleSpec, LogPolicy, EffectSource, Side
from jpoke.utils.enums import Event
from jpoke.utils import fast_copy

from .player import Player


class EventContext:
    """イベント発火時のコンテキスト情報。

    イベントに関連するポケモン、技、場の状態などを保持します。
    ハンドラ実行時に必要な情報を提供します。

    内部的には source/target のみを保持しますが、
    attacker/defender での指定・アクセスも可能です（source/target のエイリアス）。

    Attributes:
        source: イベントの発生源となるポケモン（attacker のエイリアス）
        target: イベントの対象となるポケモン（defender のエイリアス）
        move: 使用された技
        field: 場の状態
    """

    def __init__(self,
                 source: Pokemon | None = None,
                 target: Pokemon | None = None,
                 attacker: Pokemon | None = None,
                 defender: Pokemon | None = None,
                 move: Move | None = None,
                 field: Field | None = None):
        """EventContext を初期化する。

        Args:
            source: イベントの発生源となるポケモン
            target: イベントの対象となるポケモン
            attacker: 攻撃側のポケモン（source のエイリアス）
            defender: 防御側のポケモン（target のエイリアス）
            move: 使用された技
            field: 場の状態

        Note:
            attacker が指定された場合は source に、
            defender が指定された場合は target にマッピングされます。
        """
        # attacker/defender が指定された場合は source/target にマッピング
        self.source = attacker if attacker is not None else source
        self.target = defender if defender is not None else target
        self.move = move
        self.field = field

    @property
    def attacker(self) -> Pokemon | None:
        """攻撃側のポケモン（source のエイリアス）。"""
        return self.source

    @property
    def defender(self) -> Pokemon | None:
        """防御側のポケモン（target のエイリアス）。"""
        return self.target

    def get(self, role: ContextRole) -> Pokemon | None:
        """指定されたロールのポケモンを取得する。

        Args:
            role: 取得するロール（"source", "target", "attacker", "defender"）

        Returns:
            Pokemon | None: 該当するポケモン。存在しない場合はNone
        """
        # attacker/defender を source/target にマッピング
        if role == "attacker":
            return self.source
        elif role == "defender":
            return self.target
        return getattr(self, role, None)

    def resolve_role(self,
                     battle: Battle,
                     spec: RoleSpec | None) -> Pokemon | None:
        """ロール指定からポケモンを解決する。

        Args:
            battle: バトルインスタンス
            spec: "role:side"形式のロール指定（例: "source:foe"）

        Returns:
            Pokemon | None: 解決されたポケモン。存在しない場合はNone
        """
        if spec is None:
            return None

        role, side = spec.split(":")
        mon = self.get(role)
        if mon and side == "foe":
            mon = battle.foe(mon)
        return mon


@dataclass
class Handler:
    """イベントハンドラの定義。

    Handler は特定のポケモンまたはプレイヤー（subject）に紐づいて登録され、条件に合うイベントが発火したときに実行される。

    - **subject**: ハンドラを所有・発動させるトリガーとなるポケモン（またはプレイヤー）
    - **subject_spec**: どの役割（role）のどちら側（side）に対して発動するかを "role:side" 形式で指定

    例: 「いかく」特性
    - subject: いかくを持つポケモン自身
    - subject_spec="source:self": イベントの source（登場したポケモン）が自分自身の時に発動
    - target_spec="source:foe": 効果の対象は source から見て相手側のポケモン
    """
    func: Callable
    subject_spec: RoleSpec
    source_type: EffectSource | None = None
    log: LogPolicy = "always"
    log_text: str | None = None
    priority: int = 100
    once: bool = False

    def __lt__(self, other):
        """priorityが小さいほど先に実行される"""
        return self.priority < other.priority

    @property
    def role(self) -> ContextRole:
        """subject_spec から role を抽出"""
        return self.subject_spec.split(":")[0]

    @property
    def side(self) -> Side:
        """subject_spec から side を抽出"""
        return self.subject_spec.split(":")[1]

    def resolve_subject(self, battle: Battle, ctx: EventContext) -> Pokemon | None:
        """subject_spec に基づいてハンドラの対象ポケモンを解決"""
        return ctx.resolve_role(battle, self.subject_spec)

    def should_log(self, success: bool) -> bool:
        return self.log == "always" or \
            (self.log == "on_success" and success) or \
            (self.log == "on_failure" and not success)

    def write_log(self, battle: Battle, ctx: EventContext, success: bool) -> None:
        if not self.should_log(success):
            return

        subject = self.resolve_subject(battle, ctx)
        if not subject:
            return

        text = ""
        if self.log_text is not None:
            text = self.log_text
        else:
            match self.source_type:
                case "ability":
                    subject.ability.reveal()
                    text = subject.ability.orig_name
                case "item":
                    subject.item.reveal()
                    text = subject.item.orig_name
                case "move":
                    ctx.move.reveal()
                    text = ctx.move.orig_name
                case "ailment":
                    text = subject.ailment.name
                case "volatile":
                    text = self.log_text if self.log_text else ""

        if not success:
            text += " 失敗"

        if text:
            battle.add_event_log(subject, text)


class HandlerReturn(NamedTuple):
    """ハンドラ関数の戻り値。

    - success: 処理が成功したかどうか
    - value: 補正値などの連鎖計算に使う値（省略可）
    - stop_event: イベント処理を停止するかどうか（省略可）
    """
    success: bool
    value: Any = None
    stop_event: bool = False


@dataclass
class RegisteredHandler:
    """登録済みのイベントハンドラ情報。

    ハンドラとその対象（ポケモンまたはプレイヤー）の組み合わせを保持します。

    Attributes:
        handler: ハンドラ定義
        _subject: ハンドラの対象（ポケモンまたはプレイヤー）
    """
    handler: Handler
    _subject: Pokemon | Player

    @property
    def subject(self) -> Pokemon:
        """ハンドラの対象ポケモンを取得する。

        Playerの場合は現在場に出ているポケモンを返します。

        Returns:
            Pokemon: 対象のポケモン
        """
        if isinstance(self._subject, Player):
            return self._subject.active
        else:
            return self._subject


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
        self.handlers: dict[Event, list[RegisteredHandler]] = {}

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
            for i, rh in enumerate(data):
                # プレイヤーまたはポケモンのインデックスから複製後のオブジェクトを見つける
                if isinstance(rh._subject, Player):
                    player_idx = old.players.index(rh._subject)
                    new_source = new.players[player_idx]
                else:
                    old_player = old.find_player(rh._subject)
                    player_idx = old.players.index(old_player)
                    team_idx = old_player.team.index(rh._subject)
                    new_source = new.players[player_idx].team[team_idx]

                self.handlers[event][i]._subject = new_source

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
             ctx: EventContext | None = None,
             value: Any = None) -> Any:
        """イベントを発火し、登録されたハンドラを実行する。

        優先度とポケモンの素早さに基づいてハンドラを順次実行します。
        ハンドラは値を連鎖的に変更でき、最終的な値が返されます。

        Args:
            event: 発火するイベントタイプ
            ctx: イベントコンテキスト（Noneの場合は自動構築）
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

            result: HandlerReturn = rh.handler.func(self.battle, context, value)

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
            speed = self.battle.calc_effective_speed(subject)
            return (rh.handler.priority, -speed)

        return sorted(rhs, key=key)

    def _build_context(self, rh: RegisteredHandler) -> EventContext:
        """ハンドラに対応するコンテキストを構築"""
        if rh.handler.side == "self":
            mon = rh.subject
        else:
            mon = self.battle.foe(rh.subject)
        return EventContext(**{rh.handler.role: mon})

    def _match(self, ctx: EventContext, rh: RegisteredHandler) -> bool:
        """コンテキストがハンドラにマッチするか判定"""
        from jpoke.core import Player

        # コンテキストの対象の判定
        ctx_mon = ctx.get(rh.handler.role)
        if ctx_mon is None:
            return False

        # ハンドラの対象を解決（Playerの場合はactiveポケモンに変換）
        subject = rh.subject
        if isinstance(subject, Player):
            subject = subject.active
            if subject is None:
                return False

        # ハンドラの対象の判定
        match rh.handler.side:
            case "self":
                return ctx_mon == subject
            case "foe":
                return ctx_mon == self.battle.foe(subject)
