from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from jpoke.core import EventManager
    from jpoke.model.pokemon import Pokemon

from jpoke.utils.type_defs import AilmentName
from jpoke.utils import fast_copy
from jpoke.data.ailment import AILMENTS

from .effect import GameEffect


class Ailment(GameEffect):
    """ポケモンの状態異常を表すクラス。

    状態異常（まひ、やけど、どく等）はバトル中にポケモンに
    継続的な影響を与える効果を持つ。

    Attributes:
        count: 状態異常の継続ターン数などを記録するカウンター

    Notes:
        init_game()実装不要; Pokemonクラスで新しくインスタンスが作られるため。
        状態異常は相手に常に公開されるため、初期化時に reveal() を呼ぶ。
    """

    def __init__(self, name: AilmentName = "") -> None:
        """状態異常を初期化する。

        Args:
            name: 状態異常名。空文字列の場合は状態異常なしとして扱う
        """
        super().__init__(AILMENTS[name])
        self.count: int = 0
        self.reveal()

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
