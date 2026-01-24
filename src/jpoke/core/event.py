from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Move, Pokemon

from typing import Callable
from dataclasses import dataclass

from jpoke.utils.types import ContextRole, Side, GlobalField, SideField, Weather, Terrain
from jpoke.utils.enums import Event, HandlerResult
from jpoke.utils import fast_copy

from .player import Player


@dataclass
class EventContext:
    target: Pokemon | None = None,
    source: Pokemon | None = None,
    attacker: Pokemon | None = None,
    defender: Pokemon | None = None,
    move: Move | None = None,
    field: GlobalField | SideField | Weather | Terrain = ""


@dataclass(frozen=True)
class Handler:
    func: Callable
    role: ContextRole = "source"
    side: Side = "self"
    priority: int = 0
    once: bool = False

    def __lt__(self, other):
        return self.priority > other.priority


@dataclass(frozen=True)
class RegisteredHandler:
    handler: Handler
    source: Pokemon | Player | None

    def resolve_source(self) -> Pokemon | None:
        if isinstance(self.source, Player):
            return self.source.active
        else:
            return self.source


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
           source: Pokemon | Player | None = None):
        """ハンドラを登録"""
        self.handlers.setdefault(event, []).append(
            RegisteredHandler(handler, source))

    def off(self,
            event: Event,
            handler: Handler,
            source: Pokemon | Player | None = None):
        """ハンドラを解除"""
        if event not in self.handlers:
            return
        self.handlers[event] = [
            rh for rh in self.handlers[event]
            if not (rh.handler == handler and rh.source == source)
        ]

    def emit(self,
             event: Event,
             ctx: EventContext | None = None,
             value: Any = None) -> Any:
        """イベントを発火"""
        print(f"Event emitted: {event}, handlers={self.handlers.get(event, [])}")
        for rh in sorted(self.handlers.get(event, []), key=lambda x: x.handler):
            handler = rh.handler

            if ctx:
                if not self._match(ctx, rh):
                    continue
                ctxs = [ctx]
            else:
                ctxs = self._build_contexts(rh)

            for c in ctxs:
                res = handler.func(self.battle, c, value)

                if handler.once:
                    self.off(event, handler, rh.source)

                if isinstance(res, HandlerResult):
                    flag = res
                elif isinstance(res, tuple):
                    value, flag = res
                else:
                    value, flag = res, None

                # 制御フラグの処理
                match flag:
                    case HandlerResult.STOP_HANDLER:
                        break
                    case HandlerResult.STOP_EVENT:
                        return value

        return value

    def _match(self, ctx: EventContext, rh: RegisteredHandler) -> bool:
        match rh.handler.side:
            case "self":
                return ctx.target == rh.resolve_source()
            case "foe":
                return ctx.target == self.battle.foe(rh.resolve_source())
            case "all":
                return False

    def _build_contexts(self, rh: RegisteredHandler) -> list[EventContext]:
        """
        RegisteredHandler から EventContext のリストを構築する
        """
        sources = self._expand(rh.source)
        target_sides = self._expand(rh.handler.side)

        if not sources:
            return []

        # 素早さ順に source を並べる
        if len(sources) > 1:
            order = self.battle.calc_speed_order()
            sources = [p for p in order if p in sources]

        # ターゲットを決定する
        ctxs = [
            EventContext(
                source=s,
                target=s if ts == "self" else self.battle.foe(s)
            )
            for s in sources
            for ts in target_sides
        ]

        return ctxs

    def _expand(self, obj) -> list[Pokemon]:
        if obj is None:
            return []
        if isinstance(obj, Player):
            return [obj.active]
        return [obj]
