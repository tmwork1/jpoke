from typing import Literal

from jpoke.utils import fast_copy
from jpoke.data.item import ITEMS
from jpoke.data.models import ItemData
from jpoke.types import PokemonName, MoveName, ItemName

from .effect import GameEffect


class Item(GameEffect):
    """ポケモンのアイテムを表すクラス。

    アイテムは戦闘中に自動的に効果を発揮したり、
    特定の条件下で消費されたりする。
    """

    def __init__(self, name: ItemName = "") -> None:
        """アイテムを初期化する。

        Args:
            name: アイテム名。空文字列の場合はアイテムなしとして扱う
        """
        super().__init__(ITEMS[name])

        self.data: ItemData  # type hint
        self.count: int = 0
        self.move_name: MoveName | Literal[""] = ""

    def __deepcopy__(self, memo):
        """アイテムオブジェクトのディープコピーを作成する。"""
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def reset_on_switch_out(self):
        """ベンチに戻ったときのリセット処理。

        アイテムの状態をリセットする。
        """
        self.reset_enable_state()
        self.count = 0
        self.move_name = ""

    def reset_enable_state(self):
        """アイテムの有効状態をリセットする。"""
        reasons = set()
        if self.consumed:
            reasons.add("consumed")
        self.replace_disabled_reasons(reasons)

    def is_berry(self) -> bool:
        """きのみかどうかを判定する。"""
        return self.name.endswith("のみ")

    @property
    def mega_evol_before(self) -> PokemonName | None:
        """メガシンカ前のポケモンの名前を返すプロパティ。"""
        if self.data.mega_evolve is not None:
            return self.data.mega_evolve[0]
        return None

    @property
    def mega_evol_after(self) -> PokemonName | None:
        """メガシンカ後のポケモンの名前を返すプロパティ。"""
        if self.data.mega_evolve is not None:
            return self.data.mega_evolve[1]
        return None
