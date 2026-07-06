from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from jpoke.data.volatile import VolatileData

from jpoke.types import VolatileName, MoveName
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
        交代時に再生成されるため reset_on_switch_out() は実装不要
    """

    def __init__(self,
                 name: VolatileName,
                 count: int | None = None,
                 move_name: MoveName | Literal[""] = "",
                 hp: int = 0,
                 bind_damage_ratio: float = 1/8):
        """揮発性状態を初期化する。

        Args:
            name: 揮発性状態名。空文字列の場合は状態なしとして扱う
        """
        super().__init__(VOLATILES[name])
        self.count: int | None = count
        self.move_name: MoveName | Literal[""] = move_name
        self.hp: int = hp
        self.bind_damage_ratio: float = bind_damage_ratio  # バインドのダメージ比率

        self.data: VolatileData  # type hint

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def tick(self):
        """揮発性状態のターン経過処理を行う"""
        if self.count is not None:
            self.count = max(0, self.count - 1)
