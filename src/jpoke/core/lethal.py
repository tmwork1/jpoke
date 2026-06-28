"""致死率計算ロジックを提供するモジュール
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon, Move

from dataclasses import dataclass

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
    target: Literal["attacker", "defender"]
    priority: int = 100


class LethalCalculator:
    def __init__(self, battle: Battle):
        self.battle = battle

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[])
        return new

    def update_reference(self, battle: Battle):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    def _get_pokemon_handlers(self, mon: Pokemon) -> list[LethalHandler]:
        handlers = [
            mon.ability.data.lethal_handler,
            mon.item.data.lethal_handler,
            mon.ailment.data.lethal_handler,
        ]
        # 揮発状態のハンドラを追加
        handlers += [v.data.lethal_handler for v in mon.volatiles.values()]

        # Noneを除去したリストを返す
        return [h for h in handlers if h is not None]

    def get_handlers(self, ctx: LethalContext) -> list[LethalHandler]:
        handlers = []

        # 攻撃側のハンドラを追加
        attacker_handlers = self._get_pokemon_handlers(ctx.attacker)
        handlers += [h for h in attacker_handlers if h.target == "attacker"]

        # 防御側のハンドラを追加
        defender_handlers = self._get_pokemon_handlers(ctx.defender)
        handlers += [h for h in defender_handlers if h.target == "defender"]

        # 共通場のハンドラを追加
        # 片場のハンドラを追加

        return sorted(handlers, key=lambda h: h.priority)

    def calc_lethal(self,
                    attacker: Pokemon,
                    move: Move,
                    critical: bool = False,
                    max_hit: int = 9):

        defender = self.battle.foe(attacker)

        damages = self.battle.calc_damages(attacker, defender, move, critical=critical)

        ctx = LethalContext(attacker=attacker, defender=defender, move=move, critical=critical)
        handlers = self.get_handlers(ctx)

        hp_dist = m.to_dist(defender.hp)
        damage_dist = m.to_dist(damages)

        for hit in range(1, max_hit + 1):
            hp_dist = m.subtract_dist(hp_dist, damage_dist, minimum=0)
            if 0 in hp_dist:
                break

            for h in handlers:
                hp_dist = h.func(self.battle, ctx, hp_dist)
                if 0 in hp_dist:
                    break

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
