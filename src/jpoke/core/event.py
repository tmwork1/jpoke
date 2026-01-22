from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon, Move

from typing import Callable
from dataclasses import dataclass

from jpoke.utils.types import Side, GlobalField, SideField, Weather, Terrain
from jpoke.utils.enums import Event, HandlerResult
from jpoke.utils import fast_copy
from .player import Player


@dataclass
class EventContext:
    source: Pokemon
    target: Pokemon | None = None
    move: Move | None = None
    field: GlobalField | SideField | Weather | Terrain = ""


@dataclass(frozen=True)
class Handler:
    func: Callable
    priority: int = 0
    triggered_by: Side = "self"
    once: bool = False

    def __lt__(self, other):
        return self.priority > other.priority


class EventManager:
    def __init__(self, battle: Battle) -> None:
        self.battle = battle
        self.handlers: dict[Event, dict[Handler, list[Pokemon | Player]]] = {}

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

    def on(self, event: Event, handler: Handler, source: Pokemon | Player):
        """イベントを指定してハンドラを登録"""
        self.handlers.setdefault(event, {})
        sources = self.handlers[event].setdefault(handler, [])
        if source not in sources:
            sources.append(source)

    def off(self, event: Event, handler: Handler, source: Pokemon | Player):
        if event in self.handlers and handler in self.handlers[event]:
            # source を削除
            self.handlers[event][handler] = \
                [p for p in self.handlers[event][handler] if p != source]
            # 空のハンドラを解除
            if not self.handlers[event][handler]:
                del self.handlers[event][handler]

    def emit(self, event: Event, ctx: EventContext | None = None, value: Any = None) -> Any:
        """イベントを発火"""
        for handler, sources in sorted(self.handlers.get(event, {}).items()):
            if ctx:
                # 引数のコンテキストに合致するハンドラがあるか検証する
                if (handler.triggered_by == "self" and ctx.source in sources) or \
                        (handler.triggered_by == "foe" and any(ctx.source is not mon for mon in sources)):
                    ctxs = [ctx]
                else:
                    continue
            else:
                # 引数のコンテキストに指定がなければ、登録されている source からコンテキストを生成する
                new_sources = []
                for source in sources:
                    if isinstance(source, Player):
                        source = source.active
                    if source not in new_sources:
                        new_sources.append(source)

                # 素早さ順に並び変える
                if len(new_sources) > 1:
                    order = self.battle.calc_speed_order()
                    new_sources = [p for p in order if p in new_sources]

                ctxs = [EventContext(source) for source in new_sources]

            # すべての source に対してハンドラを実行する
            for c in ctxs:
                res = handler.func(self.battle, c, value)

                # 単発ハンドラの削除
                if handler.once:
                    self.off(event, handler, c.source)

                if isinstance(res, HandlerResult):
                    flag = res
                elif isinstance(res, tuple):
                    value, flag = res
                else:
                    value, flag = res, None

                match flag:
                    case HandlerResult.STOP_HANDLER:
                        break
                    case HandlerResult.STOP_EVENT:
                        return value

        return value
