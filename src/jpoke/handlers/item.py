from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.utils.types import RoleSpec, Factor, LogPolicy, Weather, Terrain
from jpoke.utils.enums import Interrupt
from jpoke.core.event import EventContext, HandlerResult
from . import base


def reveal_item(battle: Battle,
                ctx: EventContext,
                value: Any,
                source_spec: RoleSpec = "source:self") -> bool:
    return base.reveal(battle, ctx, value, source_spec, "item")


def modify_hp(battle: Battle,
              ctx: EventContext,
              value: Any,
              target_spec: RoleSpec = "target:self",
              v: int = 0,
              r: float = 0,
              prob: float = 1.0,
              source_spec: RoleSpec | None = None,
              factor: Factor | None = "item",
              log: LogPolicy = "always") -> bool:
    return base.modify_hp(battle, ctx, value, target_spec, v, r, prob, source_spec, factor, log)


def modify_stat(battle: Battle,
                ctx: EventContext,
                value: Any,
                stat: str,
                v: int,
                target_spec: RoleSpec = "target:self",
                source_spec: RoleSpec | None = None,
                prob: float = 1.0,
                factor: Factor | None = "item",
                log: LogPolicy = "always") -> bool:
    return base.modify_stat(battle, ctx, value, stat, v, target_spec, source_spec, prob, factor, log)


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  value: Any,
                  ailment: str,
                  target_spec: RoleSpec = "target:self",
                  source_spec: RoleSpec | None = None,
                  prob: float = 1.0,
                  factor: Factor | None = "item",
                  log: LogPolicy = "always") -> bool:
    return base.apply_ailment(battle, ctx, value, ailment, target_spec, source_spec, prob, factor, log)


def activate_weather(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     weather: Weather,
                     count: int = 5,
                     source_spec: RoleSpec = "source:self",
                     log: LogPolicy = "always") -> bool:
    return base.activate_weather(battle, ctx, value, weather, count, source_spec, "item", log)


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     terrain: Terrain,
                     count: int = 5,
                     source_spec: RoleSpec = "source:self",
                     log: LogPolicy = "always") -> bool:
    return base.activate_terrain(battle, ctx, value, terrain, count, source_spec, "item", log)


def いのちのたま(battle: Battle, ctx: EventContext, value: Any):
    # ON_HITのハンドラ
    if ctx.move.category != "変化" and modify_hp(battle, ctx, value, target_spec="attacker:self", r=-1/8):
        reveal_item(battle, ctx, value, source_spec="attacker:self")


def だっしゅつボタン(battle: Battle, ctx: EventContext, value: Any):
    # ON_DAMAGEのハンドラ
    player = battle.find_player(ctx.defender)
    player.interrupt = Interrupt.EJECTBUTTON


def だっしゅつパック(battle: Battle, ctx: EventContext, value: Any):
    # ON_MODIFY_STATのハンドラ
    player = battle.find_player(ctx.target)
    if value < 0 and battle.get_available_switch_commands(player):
        player.interrupt = Interrupt.REQUESTED
