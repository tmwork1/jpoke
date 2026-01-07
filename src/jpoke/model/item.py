from jpoke.utils import fast_copy
from jpoke.data import ITEMS

from .effect import BaseEffect


class Item(BaseEffect):
    def __init__(self, name: str = "") -> None:
        super().__init__(ITEMS[name])

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def consume(self):
        self.active = False
        self.revealed = True
