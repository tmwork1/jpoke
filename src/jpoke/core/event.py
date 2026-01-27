from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Move, Pokemon, Field

from typing import Callable
from dataclasses import dataclass

from jpoke.utils.types import ContextRole, Side
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
    func: Callable
    role: ContextRole
    side: Side = "self"
    priority: int = 0
    once: bool = False

    def __lt__(self, other):
        return self.priority > other.priority


@dataclass
class RegisteredHandler:
    handler: Handler
    target: Pokemon | Player | None

    def resolve_source(self) -> Pokemon | None:
        return self.target.active if isinstance(self.target, Player) else self.target


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
            for handler, sources in data.items():
                new_sources = []
                for old_source in sources:
                    # プレイヤーまたはポケモンのインデックスから複製後のオブジェクトを見つける
                    if isinstance(old_source, Player):
                        player_idx = old.players.index(old_source)
                        new_source = new.players[player_idx]
                    else:
                        old_player = old.find_player(old_source)
                        player_idx = old.players.index(old_player)
                        team_idx = old_player.team.index(old_source)
                        new_source = new.players[player_idx].team[team_idx]
                    new_sources.append(new_source)

                self.handlers[event][handler] = new_sources

        # Battle への参照を更新する
        self.battle = new

    def on(self,
           event: Event,
           handler: Handler,
           target: Pokemon | Player | None = None):
        """ハンドラを登録"""
        self.handlers.setdefault(event, []).append(
            RegisteredHandler(handler, target))

    def off(self,
            event: Event,
            handler: Handler,
            target: Pokemon | Player | None = None):
        """ハンドラを解除"""
        if event not in self.handlers:
            return
        self.handlers[event] = [
            rh for rh in self.handlers[event]
            if not (rh.handler == handler and rh.target == target)
        ]

    def emit(self,
             event: Event,
             ctx: EventContext | None = None,
             value: Any = None) -> Any:
        """イベントを発火"""
        for rh in self._sort_handlers(self.handlers.get(event, [])):
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
                self.off(event, rh.handler, rh.target)

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
            src = rh.resolve_source()
            s_idx = speed_idx.get(src, float("inf"))
            return (rh.handler.priority, s_idx)

        return sorted(rhs, key=key)

    def _build_context(self, rh: RegisteredHandler) -> EventContext:
        """ハンドラに対応するコンテキストを構築"""
        mon = rh.resolve_source() if rh.handler.side == "self" else self.battle.foe(rh.resolve_source())
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
                return ctx_mon == rh.resolve_source()
            case "foe":
                return ctx_mon == self.battle.foe(rh.resolve_source())
