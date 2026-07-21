from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Player

from jpoke.utils import fast_copy
from jpoke.data.field import FIELDS
from jpoke.data.models import FieldData
from .effect import GameEffect


class Field(GameEffect):
    """フィールド効果を表すクラス。

    フィールド（エレキフィールド、グラスフィールド等）は
    バトル全体に影響を与える効果で、一定ターン継続する。

    Attributes:
        data: フィールド効果のデータ
        owners: フィールドの所有者（プレイヤー）リスト
        count: フィールド効果の残りターン数
    """

    def __init__(self,
                 name: str,
                 owners: tuple[Player, ...],
                 count: int = 0) -> None:
        """フィールド効果を初期化する。

        Args:
            name: フィールド名
            owners: フィールドの所有者となるプレイヤーのタプル
            count: 初期ターン数（0の場合は非アクティブ）
        """
        super().__init__(FIELDS[name])
        self.owners: tuple[Player, ...] = owners
        self.count: int = count
        self.heal: int = 0  # ねがいごと用
        self.damage: int = 0  # みらいよち・はめつのねがい用

        self.data: FieldData  # IDE hint

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new, keys_to_deepcopy=[])

    @property
    def name(self) -> str:
        """フィールド名を取得する。

        Returns:
            フィールドが有効な場合は名前、無効な場合は空文字
        """
        return super().name if self.count else ""

    @property
    def is_active(self) -> bool:
        """フィールド効果が有効かどうかを判定する。

        Returns:
            残りターン数が1以上の場合True
        """
        return self.count > 0

    @property
    def sunny(self) -> bool:
        """はれ・おおひでり相当かどうかを判定する。"""
        return self.name in {"はれ", "おおひでり"}

    @property
    def rainy(self) -> bool:
        """あめ・おおあめ相当かどうかを判定する。"""
        return self.name in {"あめ", "おおあめ"}
