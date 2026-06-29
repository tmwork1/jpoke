from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, LethalContext
    from jpoke.model import Pokemon, Move

from jpoke.utils import math as m


def _heal_hp(hp_dist: dict[int, int],
             target: Pokemon,
             v: int = 0,
             r: float = 0.) -> dict[int, int]:
    max_hp = target.max_hp
    if r:
        v = max(1, max_hp // 16)
    return m.add_dist(hp_dist, v, maximum=max_hp)


def たべのこし_heal_hp(battle: Battle, ctx: LethalContext, hp_dist: dict[int, int]) -> dict[int, int]:
    return _heal_hp(hp_dist, ctx.defender, r=1/16)
