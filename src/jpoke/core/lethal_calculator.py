"""致死率計算ロジックを提供するモジュール
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, SideFieldManager
    from jpoke.model import Pokemon, Move

from copy import deepcopy
from dataclasses import dataclass, field

from jpoke.utils.type_defs import LethalEvent, LethalSubject
from jpoke.utils import fast_copy, math as m


@dataclass(frozen=True)
class LethalHandler:
    func: Callable[..., dict[int, int]]
    event: LethalEvent
    subject: LethalSubject
    priority: int = 100


@dataclass
class LethalContext:
    attacker: Pokemon
    defender: Pokemon
    move: Move
    critical: bool = False


@dataclass
class LethalResult:
    attack_count: int
    move: Move
    hit: int
    hp_dist: dict[int, int]
    damage_dist: dict[int, int]

    @property
    def min_damage(self):
        return min(self.damage_dist.keys())

    @property
    def max_damage(self):
        return max(self.damage_dist.keys())

    @property
    def lethal_probability(self) -> float:
        zero_freq = self.hp_dist.get(0, 0)
        total_freq = sum(self.hp_dist.values())
        return zero_freq / total_freq


def calc_lethal(battle: Battle,
                attacker: Pokemon,
                moves: Move | tuple[Move, int] | list[Move | tuple[Move, int]],
                critical: bool,
                max_attack: int) -> list[LethalResult]:

    # 攻撃側のインデックスを取得
    attacker_index = battle._get_player_index(attacker)

    # 初期化
    battle = deepcopy(battle)
    attacker = battle.actives[attacker_index]
    defender = battle.foe(attacker)
    hp_dist = m.to_dist(defender.hp)
    move_list = _generate_move_list(moves)

    # 致死率計算
    results = []
    for atk in range(1, max_attack + 1):
        for move, count in move_list:
            ctx = LethalContext(attacker, defender, move, critical=critical)

            hp_dist = _emit("pre_hit", battle, ctx, hp_dist)
            if 0 in hp_dist:
                break

            for hit in range(count):
                hp_dist, damage_dist = _apply_damage(battle, ctx, hp_dist)
                results.append(
                    LethalResult(attack_count=atk, move=move, hit=hit,
                                 hp_dist=hp_dist, damage_dist=damage_dist)
                )
            if 0 in hp_dist:
                break

            hp_dist = _emit("post_hit", battle, ctx, hp_dist)
            if 0 in hp_dist:
                break

        if 0 in hp_dist:
            break

    return results


def _generate_move_list(moves: Move | tuple[Move, int] | list[Move | tuple[Move, int]]) -> list[tuple[Move, int]]:
    if isinstance(moves, list):
        result = []
        for x in moves:
            if isinstance(x, tuple):
                result.append(x)
            else:
                result.append((x, 1))
        return result
    elif isinstance(moves, tuple):
        return [moves]
    else:
        return [(moves, 1)]


def _get_pokemon_handlers(event: LethalEvent,
                          mon: Pokemon,
                          subject: LethalSubject) -> list[LethalHandler]:
    candidates = [
        mon.ability.data.lethal_handler,
        mon.item.data.lethal_handler,
        mon.ailment.data.lethal_handler,
    ]
    # 揮発状態のハンドラを追加
    candidates += [v.data.lethal_handler for v in mon.volatiles.values()]
    # 条件に一致するハンドラを返す
    return [h for h in candidates if (
        h is not None and h.event == event and h.subject in {subject, "both"}
    )]


def _get_global_field_handlers(event: LethalEvent, battle: Battle) -> list[LethalHandler]:
    fields = [battle.weather, battle.terrain] + \
        list(battle.global_manager.fields.values())
    candidates = [field.data.lethal_handler for field in fields if field.is_active]
    # 条件に一致するハンドラを返す
    return [h for h in candidates if h is not None and h.event == event]


def _get_side_field_handlers(event: LethalEvent,
                             side: SideFieldManager,
                             subject: LethalSubject) -> list[LethalHandler]:
    fields = side.fields.values()
    candidates = [field.data.lethal_handler for field in fields if field.is_active]
    return [h for h in candidates if (
        h is not None and h.event == event and h.subject in {subject, "both"}
    )]


def _get_handlers(event: LethalEvent,
                  battle: Battle,
                  ctx: LethalContext) -> list[LethalHandler]:
    handlers = []

    # 攻撃側のハンドラを追加
    handlers += _get_pokemon_handlers(event, ctx.attacker, "attacker")
    # 防御側のハンドラを追加
    handlers += _get_pokemon_handlers(event, ctx.defender, "defender")
    # 共通場のハンドラを追加
    handlers += _get_global_field_handlers(event, battle)
    # 片場のハンドラを追加
    handlers += _get_side_field_handlers(event, battle.get_side(ctx.attacker), "attacker")
    handlers += _get_side_field_handlers(event, battle.get_side(ctx.defender), "defender")

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


def _update_hp(mon: Pokemon, hp_dist: dict[int, int]):
    mon.hp = min(hp_dist.keys())


def _emit(event: LethalEvent,
          battle: Battle,
          ctx: LethalContext,
          hp_dist: dict[int, int]) -> dict[int, int]:
    handlers = _get_handlers(event, battle, ctx)
    hp_dist = _apply_handlers(battle, handlers, ctx, hp_dist)
    _update_hp(ctx.defender, hp_dist)
    return hp_dist


def _apply_damage(battle: Battle,
                  ctx: LethalContext,
                  hp_dist: dict[int, int]) -> tuple[dict[int, int], ...]:
    damages = battle.calc_damages(
        ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical
    )
    damage_dist = m.to_dist(damages)
    hp_dist = m.subtract_dist(hp_dist, damage_dist, minimum=0)
    _update_hp(ctx.defender, hp_dist)
    return hp_dist, damage_dist
