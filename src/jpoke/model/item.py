from jpoke.utils import fast_copy
from jpoke.data import ITEMS

from .effect import GameEffect


class Item(GameEffect):
    """ポケモンの持ち物を表すクラス。

    持ち物は戦闘中に自動的に効果を発揮したり、
    特定の条件下で消費されたりする。
    """

    def __init__(self, name: str = "") -> None:
        """持ち物を初期化する。

        Args:
            name: 持ち物名。空文字列の場合は持ち物なしとして扱う
        """
        super().__init__(ITEMS[name])

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def init_game(self):
        """ゲーム初期化処理。

        持ち物の状態をリセットし、ゲーム開始時の状態にする。
        """
        self.reset_effect()

    def consume(self):
        """アイテムを消費する。

        アイテムを公開状態にし、無効化する。
        消費されたアイテムは効果を失い、二度と使用できなくなる。
        """
        self.reveal()
        self.disable()
