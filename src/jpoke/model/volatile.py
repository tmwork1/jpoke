from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict
if TYPE_CHECKING:
    from jpoke.core import EventManager
    from jpoke.model.pokemon import Pokemon

from jpoke.utils.type_defs import VolatileName
from jpoke.utils import fast_copy
from jpoke.data.volatile import VOLATILES

from .effect import GameEffect


class Volatile(GameEffect):
    """ポケモンの揮発性状態を表すクラス。

    揮発性状態（みがわり、アンコール等）は場に出ているポケモンにのみ作用し、
    引っ込むとリセットされる一時的な状態効果。
    状態異常(Ailment)とは異なり、ベンチに戻ると消える。

    Attributes:
        count: 揮発性状態の継続ターン数などを記録するカウンター
        value: 揮発性状態に紐づく数値（みがわりのHP等）
        disabled_move_name: かなしばりで使用禁止になっている技名
        locked_move_name: アンコールで固定されている技名
        source_pokemon: バインド等で使用者を記録（使用者が交代すると解除される）

    Notes:
        Pokemonクラスのbench_reset()で新しくインスタンスが作られるため、
        bench_reset()の実装は不要。
    """

    def __init__(self,
                 name: VolatileName,
                 count: int = 1,
                 move_name: str = "",
                 hp: int = 0):
        """揮発性状態を初期化する。

        Args:
            name: 揮発性状態名。空文字列の場合は状態なしとして扱う
        """
        super().__init__(VOLATILES[name])
        self.count: int = count
        self.move_name: str = move_name  # あばれる用
        self.hp: int = hp

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    @property
    def is_active(self) -> bool:
        """揮発性状態が実在するかどうか"""
        return self.count > 0

    def tick_up(self, ) -> bool:
        """揮発性状態のカウンターを1増加させる"""
        if self.count < self.max_count:
            self.count += 1
            return True
        return False

    def tick_down(self) -> bool:
        """揮発性状態のカウンターを1減少させる"""
        if self.count > 0:
            self.count -= 1
            return True
        return False
