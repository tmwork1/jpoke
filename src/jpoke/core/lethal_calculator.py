"""致死率計算ロジックを提供するモジュール
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, SideFieldManager
    from jpoke.model import Pokemon, Move

from copy import deepcopy
from dataclasses import dataclass
from collections import defaultdict, Counter

from jpoke.utils.type_defs import LethalEvent, LethalSubject
from jpoke.utils import math as m


@dataclass(frozen=True)
class LethalState:
    hp: int
    ability_enabled: bool = True
    item_enabled: bool = True


type LethalDist = dict[LethalState, int]


@dataclass(frozen=True)
class LethalHandler:
    func: Callable[..., LethalDist]
    event: LethalEvent
    subject: LethalSubject
    priority: int = 100


@dataclass(frozen=True)
class LethalContext:
    attacker: Pokemon
    defender: Pokemon
    move: Move
    critical: bool = False


@dataclass(frozen=True)
class LethalResult:
    n_attack: int
    move: Move
    hit: int
    hp_dist: LethalDist
    damage_dist: LethalDist

    @property
    def hp_counter(self) -> dict[int, int]:
        return {state.hp: freq for state, freq in self.hp_dist.items()}

    @property
    def damage_counter(self) -> dict[int, int]:
        return {state.hp: freq for state, freq in self.damage_dist.items()}

    @property
    def min_damage(self) -> int:
        return min(self.damage_counter.keys())

    @property
    def max_damage(self) -> int:
        return max(self.damage_counter.keys())

    @property
    def lethal_probability(self) -> float:
        hp_counter = self.hp_counter
        zero_freq = hp_counter.get(0, 0)
        total_freq = sum(hp_counter.values())
        return zero_freq / total_freq


def to_dist(x: int | list[int] | LethalDist,
            ability_enabled: bool = True,
            item_enabled: bool = True) -> LethalDist:
    if isinstance(x, dict):
        return x
    elif isinstance(x, list):
        counter = Counter(x)
        return {LethalState(hp=k, ability_enabled=ability_enabled, item_enabled=item_enabled): v
                for k, v in counter.items()}
    else:
        return {LethalState(hp=x, ability_enabled=ability_enabled, item_enabled=item_enabled): 1}


def flip_dist(dist: LethalDist) -> LethalDist:
    return {LethalState(hp=-k.hp, ability_enabled=k.ability_enabled, item_enabled=k.item_enabled): v
            for k, v in dist.items()}


def _clip_dist(dist: LethalDist,
               minimum: int | None = None,
               maximum: int | None = None) -> LethalDist:
    if minimum is None and maximum is None:
        return dist

    result = defaultdict(int)
    for value, freq in dist.items():
        hp = value.hp
        if minimum is not None:
            hp = max(hp, minimum)
        if maximum is not None:
            hp = min(hp, maximum)
        key = LethalState(hp=hp, ability_enabled=value.ability_enabled, item_enabled=value.item_enabled)
        result[key] += freq
    return dict(result)


def _check_hp(dist: LethalDist, value: int) -> bool:
    return any(state.hp == value for state in dist)


def _convolve(a: LethalDist | list[int] | int,
              b: LethalDist | list[int] | int) -> LethalDist:
    x = to_dist(a)
    y = to_dist(b)

    result = defaultdict(int)
    for vx, fx in x.items():
        for vy, fy in y.items():
            hp = vx.hp + vy.hp
            ability_enabled = vx.ability_enabled and vy.ability_enabled
            item_enabled = vx.item_enabled and vy.item_enabled
            key = LethalState(hp=hp, ability_enabled=ability_enabled, item_enabled=item_enabled)
            result[key] += fx * fy
    return dict(result)


def add_dist(a: LethalDist | list[int] | int,
             b: LethalDist | list[int] | int,
             minimum: int | None = None,
             maximum: int | None = None) -> LethalDist:
    result = _convolve(a, b)
    return _clip_dist(result, minimum=minimum, maximum=maximum)


def subtract_dist(a: LethalDist | list[int] | int,
                  b: LethalDist | list[int] | int,
                  minimum: int | None = None,
                  maximum: int | None = None) -> LethalDist:
    y = to_dist(b)
    result = _convolve(a, flip_dist(y))
    return _clip_dist(result, minimum=minimum, maximum=maximum)


def _lethal_loop(hp_dist: LethalDist,
                 battle: Battle,
                 attacker: Pokemon,
                 defender: Pokemon,
                 move_list: list[tuple[Move, int]],
                 critical: bool,
                 max_attack: int) -> list[LethalResult]:
    results = []
    for atk in range(1, max_attack + 1):
        for move, count in move_list:
            ctx = LethalContext(attacker, defender, move, critical=critical)

            # ヒット前のハンドラを適用
            hp_dist = _emit("pre_hit", battle, ctx, hp_dist)
            if _check_hp(hp_dist, 0):  # HPが0になったら終了
                return results

            for hit in range(count):
                # ダメージを適用
                hp_dist, damage_dist = _apply_damage(battle, ctx, hp_dist)
                results.append(
                    LethalResult(n_attack=atk, move=move, hit=hit,
                                 hp_dist=hp_dist, damage_dist=damage_dist)
                )
                if _check_hp(hp_dist, 0):  # HPが0になったら終了
                    return results

                # ヒット後のハンドラを適用
                hp_dist = _emit("post_hit", battle, ctx, hp_dist)
                if _check_hp(hp_dist, 0):  # HPが0になったら終了
                    return results

    return results


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

    hp_dist = to_dist(
        defender.hp,
        ability_enabled=defender.ability.enabled,
        item_enabled=defender.item.enabled
    )
    move_list = _generate_move_list(moves)

    # 致死率計算
    return _lethal_loop(hp_dist, battle, attacker, defender, move_list, critical, max_attack)


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
                    hp_dist: LethalDist) -> LethalDist:
    for h in handlers:
        if _check_hp(hp_dist, 0):
            break
        hp_dist = h.func(battle, ctx, hp_dist)
    return hp_dist


def _update_hp(mon: Pokemon, hp_dist: LethalDist):
    mon.hp = min(state.hp for state in hp_dist)


def _emit(event: LethalEvent,
          battle: Battle,
          ctx: LethalContext,
          hp_dist: LethalDist) -> LethalDist:
    if _check_hp(hp_dist, 0):
        return hp_dist
    handlers = _get_handlers(event, battle, ctx)
    hp_dist = _apply_handlers(battle, handlers, ctx, hp_dist)
    _update_hp(ctx.defender, hp_dist)
    return hp_dist


def _apply_damage(battle: Battle,
                  ctx: LethalContext,
                  hp_dist: LethalDist) -> tuple[LethalDist, ...]:
    damages = battle.calc_damages(
        ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical
    )
    damage_dist = to_dist(damages)
    hp_dist = subtract_dist(hp_dist, damage_dist, minimum=0)
    _update_hp(ctx.defender, hp_dist)
    return hp_dist, damage_dist
