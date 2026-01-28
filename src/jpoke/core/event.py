from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Move, Pokemon, Field

from typing import Callable
from dataclasses import dataclass

from jpoke.utils.types import ContextRole, RoleSpec, Side
from jpoke.utils.enums import Event, HandlerResult
from jpoke.utils import fast_copy

from .player import Player


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
    priority: int = 0
    once: bool = False

    @property
    def role(self) -> ContextRole:
        """subject_spec から role を抽出"""
        return self.subject_spec.split(":")[0]  # type: ignore

    @property
    def side(self) -> Side:
        """subject_spec から side を抽出"""
        return self.subject_spec.split(":")[1]  # type: ignore

    def __lt__(self, other):
        return self.priority > other.priority


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
                elif rh._subject:
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
                print(f"  Handler skipped: {rh}")
                continue

            res = rh.handler.func(self.battle, context, value)
            # ハンドラの戻り値の処理
            if isinstance(res, HandlerResult):
                flag = res
            elif isinstance(res, tuple):
                value, flag = res
            else:
                value, flag = res, None

            # 一度きりのハンドラを解除
            if rh.handler.once:
                self.off(event, rh.handler, rh._subject)

            # 制御フラグの処理
            match flag:
                case HandlerResult.STOP_HANDLER:
                    break
                case HandlerResult.STOP_EVENT:
                    return value

        return value

    def _sort_handlers(self, rhs: list[RegisteredHandler]) -> list[RegisteredHandler]:
        if len(rhs) <= 1:
            return rhs

        speed_order = self.battle.calc_speed_order()
        speed_idx = {p: i for i, p in enumerate(speed_order)}

        def key(rh: RegisteredHandler):
            s_idx = speed_idx.get(rh.subject, float("inf"))
            return (rh.handler.priority, s_idx)

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
