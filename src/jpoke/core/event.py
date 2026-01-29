from __future__ import annotations
from typing import TYPE_CHECKING, Any, NamedTuple
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Move, Pokemon, Field

from typing import Callable
from dataclasses import dataclass

from jpoke.utils.types import ContextRole, RoleSpec, LogPolicy, EffectSource, Side
from jpoke.utils.enums import Event, EventControl
from jpoke.utils import fast_copy

from .player import Player


class HandlerReturn(NamedTuple):
    """ハンドラ関数の戻り値。

    - success: 処理が成功したかどうか
    - value: 補正値などの連鎖計算に使う値（省略可）
    - control: イベント制御フラグ（省略可）
    """
    success: bool
    value: Any = None
    control: EventControl | None = None


@dataclass
class EventContext:
    source: Pokemon | None = None
    target: Pokemon | None = None
    attacker: Pokemon | None = None
    defender: Pokemon | None = None
    move: Move | None = None
    field: Field | None = None

    def get(self, role: ContextRole) -> Pokemon | None:
        return getattr(self, role)

    def resolve_role(self,
                     battle: Battle,
                     spec: RoleSpec | None) -> Pokemon | None:
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
                    subject.ability.revealed = True
                    text = subject.ability.orig_name
                case "item":
                    subject.item.revealed = True
                    text = subject.item.orig_name
                case "move":
                    ctx.move.revealed = True
                    text = ctx.move.orig_name
                case "ailment":
                    text = subject.ailment.name

        if not success:
            text += " 失敗"

        battle.add_turn_log(subject, text)


@dataclass
class RegisteredHandler:
    handler: Handler
    _subject: Pokemon | Player

    @property
    def subject(self) -> Pokemon:
        if isinstance(self._subject, Player):
            return self._subject.active
        else:
            return self._subject


class EventManager:
    def __init__(self, battle: Battle) -> None:
        self.battle = battle
        self.handlers: dict[Event, list[RegisteredHandler]] = {}

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def update_reference(self, new: Battle):
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
        """ハンドラを登録"""
        self.handlers.setdefault(event, []).append(
            RegisteredHandler(handler, subject)
        )

    def off(self,
            event: Event,
            handler: Handler,
            subject: Pokemon | Player):
        """ハンドラを解除"""
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
        """イベントを発火"""
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

            # 制御フラグの処理
            match result.control:
                case EventControl.STOP_HANDLER:
                    break
                case EventControl.STOP_EVENT:
                    return value

        return value

    def _sort_handlers(self, rhs: list[RegisteredHandler]) -> list[RegisteredHandler]:
        if len(rhs) <= 1:
            return rhs

        def key(rh: RegisteredHandler):
            speed = self.battle.calc_effective_speed(rh.subject)
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
        # コンテキストの対象の判定
        ctx_mon = ctx.get(rh.handler.role)
        if ctx_mon is None:
            return False

        # ハンドラの対象の判定
        match rh.handler.side:
            case "self":
                return ctx_mon == rh.subject
            case "foe":
                return ctx_mon == self.battle.foe(rh.subject)
