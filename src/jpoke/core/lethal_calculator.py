"""致死率計算ロジックを提供するモジュール
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon, Move

from copy import deepcopy
from dataclasses import dataclass, field

from jpoke.utils.type_defs import LethalEvent, LethalSubject
from jpoke.utils import fast_copy
from jpoke.utils import math as m


@dataclass
class LethalContext:
    attacker: Pokemon
    defender: Pokemon
    move: Move
    critical: bool = False


@dataclass(frozen=True)
class LethalHandler:
    func: Callable[..., dict[int, int]]
    event: LethalEvent
    subject: LethalSubject
    priority: int = 100


def _get_pokemon_handlers(mon: Pokemon,
                          event: LethalEvent,
                          subject: LethalSubject) -> list[LethalHandler]:
    candidates = [
        mon.ability.data.lethal_handler,
        mon.item.data.lethal_handler,
        mon.ailment.data.lethal_handler,
    ]
    # 揮発状態のハンドラを追加
    candidates += [v.data.lethal_handler for v in mon.volatiles.values()]

    # Noneを除去したリストを返す
    return [h for h in candidates if (
        h is not None and h.event == event and h.subject in {subject, "both"}
    )]


def _get_handlers(event: LethalEvent,
                  ctx: LethalContext) -> list[LethalHandler]:
    handlers = []

    # 攻撃側のハンドラを追加
    handlers += _get_pokemon_handlers(ctx.attacker, event, "attacker")
    # 防御側のハンドラを追加
    handlers += _get_pokemon_handlers(ctx.defender, event, "defender")
    # 共通場のハンドラを追加
    # 片場のハンドラを追加

    return sorted(handlers, key=lambda h: h.priority)


def _apply_handlers(battle: Battle,
                    handlers: list[LethalHandler],
                    ctx: LethalContext,
                    hp_dist: dict[int, int]) -> dict[int, int]:
    for h in handlers:
        hp_dist = h.func(battle, ctx, hp_dist)
        if 0 in hp_dist:
            break
    return hp_dist


def _update_defender_hp(ctx: LethalContext, hp_dist: dict[int, int]):
    ctx.defender.hp = min(hp_dist.keys())


def _emit(event: LethalEvent,
          battle: Battle,
          ctx: LethalContext,
          hp_dist: dict[int, int]) -> dict[int, int]:
    handlers = _get_handlers(event, ctx)
    hp_dist = _apply_handlers(battle, handlers, ctx, hp_dist)
    _update_defender_hp(ctx, hp_dist)
    return hp_dist


def _apply_damage(battle: Battle,
                  ctx: LethalContext,
                  hp_dist: dict[int, int]) -> dict[int, int]:
    damages = battle.calc_damages(
        ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical
    )
    damage_dist = m.to_dist(damages)
    hp_dist = m.subtract_dist(hp_dist, damage_dist, minimum=0)
    _update_defender_hp(ctx, hp_dist)
    return hp_dist


def calc_lethal(battle: Battle,
                attacker: Pokemon,
                move: Move,
                critical: bool,
                max_hit: int):
    attacker_index = battle._get_player_index(attacker)

    # 初期化
    battle = deepcopy(battle)
    attacker = battle.actives[attacker_index]
    defender = battle.foe(attacker)

    ctx = LethalContext(
        attacker=attacker, defender=defender, move=move, critical=critical,
    )

    hp_dist = m.to_dist(defender.hp)

    # 致死率計算
    for hit in range(1, max_hit + 1):
        hp_dist = _emit("pre_hit", battle, ctx, hp_dist)
        if 0 in hp_dist:
            break

        hp_dist = _apply_damage(battle, ctx, hp_dist)
        if 0 in hp_dist:
            break

        hp_dist = _emit("post_hit", battle, ctx, hp_dist)
        if 0 in hp_dist:
            break

    zero_freq = hp_dist.get(0, 0)
    total_freq = sum(hp_dist.values())
    lethal_prob = zero_freq / total_freq

    print(f"Attacker: {attacker.name}")
    print(f"Defender: {defender.name} hp={defender.max_hp}")
    print(f"Move: {move.name}")
    # print(f"Damages: {damages[0]}~{damages[-1]}")
    print(f"Lethal count: {hit}")
    print(f"Lethal probability: {lethal_prob: .2%}")
