from jpoke.utils import fast_copy
from jpoke.data import ITEMS
from jpoke.data.models import ItemData
from jpoke.utils.type_defs import ItemLostCause

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
        self.lost_cause: ItemLostCause = ""

        self.data: ItemData  # type hint

    def __deepcopy__(self, memo):
        """持ち物オブジェクトのディープコピーを作成する。"""
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def init_game(self):
        """ゲーム初期化処理。

        持ち物の状態をリセットし、ゲーム開始時の状態にする。
        """
        self.bench_reset()

    def bench_reset(self):
        """ベンチに戻ったときのリセット処理。

        持ち物の状態をリセットする。
        """
        self.reset_enable_state()
        self.lost_cause = ""

    def reset_enable_state(self):
        """持ち物の有効状態をリセットする。"""
        reasons = set()
        if self.consumed:
            reasons.add("consumed")
        self.set_disabled_reasons(reasons)

    @property
    def lost(self) -> bool:
        """持ち物が失われているかどうかを示すプロパティ。"""
        return self.lost_cause != ""

    @property
    def mega_evol_before(self) -> str | None:
        """メガシンカ前のポケモンの名前を返すプロパティ。"""
        if self.data.mega_evol is not None:
            return self.data.mega_evol[0]
        return None

    @property
    def mega_evol_after(self) -> str | None:
        """メガシンカ後のポケモンの名前を返すプロパティ。"""
        if self.data.mega_evol is not None:
            return self.data.mega_evol[1]
        return None
