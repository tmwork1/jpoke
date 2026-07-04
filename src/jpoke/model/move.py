from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.types import Type, MoveCategory, MoveFlag, MoveTarget, MoveName

from jpoke.utils import fast_copy
from jpoke.data import MOVES
from jpoke.data.models import MoveData
from .effect import GameEffect


class Move(GameEffect):
    """ポケモンの技を表すクラス。

    技は戦闘中に使用される攻撃や補助効果を持ち、
    PP（パワーポイント）によって使用回数が制限される。

    Attributes:
        pp: 技の残りPP（使用可能回数）
        _type: 技のタイプ（一部の効果で変更される可能性がある）
    """

    def __init__(self, name: MoveName):
        """技を初期化する。

        Args:
            name: 技名
        """
        super().__init__(MOVES[name])
        self.pp: int = self.data.pp

        self.type: Type = self.data.type
        self.power: int | None = self.data.power
        self.category: MoveCategory = self.data.category

        self.data: MoveData  # type hint

    def reset(self, reset_pp: bool = False):
        """技の状態をリセットする。"""
        self.type = self.data.type
        self.power = self.data.power
        self.category = self.data.category
        if reset_pp:
            self.pp = self.data.pp

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def to_dict(self):
        """技の情報を辞書形式で返す。

        Returns:
            技名とPPを含む辞書
        """
        return {"name": self.name, "pp": self.pp}

    def has_flag(self, flag: MoveFlag | list[MoveFlag]) -> bool:
        """技が特定のフラグを持っているかを判定する。

        Args:
            label: 判定するフラグ（単一のフラグまたは複数のフラグのリスト）
            複数のフラグが指定された場合、いずれかのフラグを持っていればTrueを返す

        Returns:
            技が指定されたフラグを持っている場合True
        """
        if isinstance(flag, list):
            return any(s in self.data.flags for s in flag)
        return flag in self.data.flags

    def modify_pp(self, v: int):
        """技のPPを増減させる。PPは0から最大PPの範囲に制限される。

        Args:
            v: 増減量（正の値で増加、負の値で減少）
        """
        self.pp = max(0, min(self.data.pp, self.pp + v))

    @property
    def priority(self) -> int:
        """技の優先度を取得する。"""
        return self.data.priority

    @property
    def accuracy(self) -> int | None:
        """技の命中率を取得する。Noneの場合は必中。"""
        return self.data.accuracy

    @property
    def critical_rank(self) -> int:
        """急所ランク補正値を取得する。"""
        return self.data.critical_rank

    @property
    def target(self) -> MoveTarget:
        """技の対象を取得する。"""
        return self.data.target

    @property
    def min_hits(self) -> int:
        """技の最小ヒット数を取得する。"""
        if self.data.multi_hit is None:
            return 1
        return self.data.multi_hit["min"]

    @property
    def max_hits(self) -> int:
        """技の最大ヒット数を取得する。"""
        if self.data.multi_hit is None:
            return 1
        return self.data.multi_hit["max"]

    @property
    def is_attack(self) -> bool:
        """技が攻撃技かどうかを判定する。

        Returns:
            技が物理または特殊技の場合True
        """
        return self.category in ["physical", "special"]

    @property
    def is_blocked_by_protect(self) -> bool:
        """技がまもるで防がれるかどうかを判定する。

        Returns:
            技がまもるで防がれる場合True
        """
        return (
            self.target == "foe"
            and not self.has_flag("unprotectable")
        )
