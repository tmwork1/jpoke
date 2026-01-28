from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from jpoke.core import EventManager
    from jpoke.model.pokemon import Pokemon

from jpoke.utils.types import AilmentName
from jpoke.utils import fast_copy
from jpoke.data.ailment import AILMENTS

from .effect import BaseEffect


class Ailment(BaseEffect):
    def __init__(self, name: AilmentName = "") -> None:
        super().__init__(AILMENTS[name])
        self.revealed = True
        self.bench_reset()

    def bench_reset(self):
        """ベンチに戻ったときのリセット処理"""
        self.count: int = 0

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    @property
    def is_active(self) -> bool:
        """状態異常が実在するかどうか（空でない状態異常が存在する）"""
        return self.name != ""
