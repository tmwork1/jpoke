from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model.pokemon import Pokemon

from jpoke.utils.types import AilmentName
from jpoke.utils import fast_copy
from jpoke.data.ailment import AILMENTS

from .effect import BaseEffect


class Ailment(BaseEffect):
    def __init__(self, owner: Pokemon, name: AilmentName = "") -> None:
        self.owner: Pokemon = owner
        self.init(name)

        self.revealed = True

    def init(self, name: str):
        super().__init__(AILMENTS[name])
        self.bench_reset()

    def bench_reset(self):
        self.count: int = 0

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def overwrite(self, battle: Battle, name: AilmentName, force: bool = False) -> bool:
        # force=True でない限り上書き不可
        if not force and self.name:
            return False

        # 重ねがけ不可
        if name == self.name:
            return False

        battle.add_turn_log(self.owner, name)

        # 現在のハンドラを解除
        self.unregister_handlers(battle.events, self.owner)
        # 初期化
        self.init(name)
        # 新しいハンドラを登録
        self.register_handlers(battle.events, self.owner)

        return True

    def cure(self, battle: Battle) -> bool:
        """状態異常を解除する"""
        if not self.name:
            return False
        battle.add_turn_log(self.owner, f"{self.name}解除")
        self.unregister_handlers(battle.events, self.owner)
        self.init("")
        return True
