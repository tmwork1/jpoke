"""致死率計算ロジックを提供するモジュール
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager
    from jpoke.model import Pokemon, Move

from jpoke.utils import fast_copy
from jpoke.utils import math as m


def calc_lethal(battle: Battle,
                attacker: Pokemon,
                move: Move):

    defender = battle.foe(attacker)

    damages = battle.calc_damages(
        attacker, defender, move
    )

    hp_dist = m.to_dist(defender.hp)
    damage_dist = m.to_dist(damages)

    for hit in range(1, 10):
        hp_dist = m.subtract_dist(hp_dist, damage_dist)
        hp_dist = m.clip_dist(hp_dist, minimum=0)
        if 0 in hp_dist:
            break

    zero_freq = hp_dist[0]
    total_freq = sum(hp_dist.values())
    lethal_prob = zero_freq / total_freq

    print(f"Attacker: {attacker.name}")
    print(f"Defender: {defender.name}")
    print(f"Move: {move.name}")
    print(f"Damages: {damages[0]}~{damages[-1]}")
    print(f"Lethal count: {hit}")
    print(f"Lethal probability: {lethal_prob: .2%}")
