from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle, LethalDist, LethalContext
    from jpoke.model import Pokemon

from collections import defaultdict
from jpoke.core.lethal_calculator import LethalState, LethalContext, add_dist


def _heal(hp_dist: LethalDist,
          target: Pokemon,
          v: int = 0,
          r: float = 0.) -> LethalDist:
    max_hp = target.max_hp
    if r:
        heal = max(1, int(max_hp * r))
    else:
        heal = v
    return add_dist(hp_dist, heal, maximum=max_hp)


def _heal_at_pinch(hp_dist: LethalDist,
                   target: Pokemon,
                   v: int = 0,
                   r: float = 0.,
                   threshold_rate: float = 0,
                   heal_with: Literal["ability", "item"] | None = None,
                   consume: bool = True) -> LethalDist:
    max_hp = target.max_hp
    if r:
        heal = max(1, int(max_hp * r))
    else:
        heal = v
    threshold = max(1, int(max_hp * threshold_rate))
    new_dist = defaultdict(int)

    for state, freq in hp_dist.items():
        # 回復手段が無効化されている場合は回復しない
        if heal_with == "ability" and not state.ability_enabled:
            continue
        if heal_with == "item" and not state.item_enabled:
            continue

        # HPが閾値を超えている場合は回復しない
        if state.hp > threshold:
            new_dist[state] = freq
            continue

        # HPが閾値以下の場合は回復する
        keep_ability_enabled = not (heal_with == "ability" and consume)
        keep_item_enabled = not (heal_with == "item" and consume)
        new_state = LethalState(
            min(state.hp + heal, max_hp),
            ability_enabled=state.ability_enabled and keep_ability_enabled,
            item_enabled=state.item_enabled and keep_item_enabled
        )
        new_dist[new_state] = freq

    return new_dist


def たべのこし_heal(battle: Battle, ctx: LethalContext, hp_dist: LethalDist) -> LethalDist:
    return _heal(hp_dist, ctx.defender, r=1/16)


def オボンのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: LethalDist) -> LethalDist:
    return _heal_at_pinch(hp_dist, ctx.defender, r=1/4, threshold_rate=1/2, heal_with="item", consume=True)
