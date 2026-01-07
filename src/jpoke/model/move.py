
from jpoke.utils.types import MoveCategory
from jpoke.utils import fast_copy
from jpoke.data import MOVES

from .effect import BaseEffect


class Move(BaseEffect):
    def __init__(self, name: str, pp: int | None = None):
        super().__init__(MOVES[name])
        self.pp: int = pp if pp else self.data.pp

        self.bench_reset()

    def bench_reset(self):
        self._type: str = self.data.type

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def dump(self):
        return {"name": self.name, "pp": self.pp}

    def modify_pp(self, v: int):
        self.pp = max(0, min(self.data.pp, self.pp + v))

    @property
    def type(self) -> str:
        return self._type

    @property
    def category(self) -> MoveCategory:
        return self.data.category
