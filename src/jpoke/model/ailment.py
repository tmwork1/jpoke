from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.data.models import AilmentData

from jpoke.types import AilmentName
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
        状態異常は相手に常に公開されるため、`GameEffect` の既定（revealed=True）を
        そのまま使う（Ability/Item と異なり PlayerState._hide_initial_effects() の
        対象外）。
    """

    def __init__(self, name: AilmentName = "", count: int | None = None) -> None:
        """状態異常を初期化する。

        Args:
            name: 状態異常名。空文字列の場合は状態異常なしとして扱う
        """
        super().__init__(AILMENTS[name])
        self.count: int | None = count
        self.elapsed_turns: int = 0

        self.data: AilmentData  # type hint

    def reset_on_switch_out(self):
        """ベンチに戻ったときのリセット処理
        経過ターンはリセットされるが、カウントはリセットされない。
        """
        self.elapsed_turns = 0

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    @property
    def is_active(self) -> bool:
        """状態異常が実在するかどうか（空でない状態異常が存在する）"""
        return self.name != ""

    @property
    def is_sleep(self) -> bool:
        """ねむり状態扱いかどうか"""
        return self.data.is_sleep

    @property
    def uncurable(self) -> bool:
        """回復不能な状態異常かどうか"""
        return self.data.uncurable

    def tick(self):
        """状態異常のターン経過処理を行う"""
        self.elapsed_turns += 1
        if self.count is not None:
            self.count = max(0, self.count - 1)
