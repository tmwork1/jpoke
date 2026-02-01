from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import EventManager, Player

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

    Notes:
        init_game()実装不要; ゲームの初期化は管理クラス側で行うため。
    """

    def __init__(self,
                 name: str,
                 owners: list[Player],
                 count: int = 0) -> None:
        """フィールド効果を初期化する。

        Args:
            name: フィールド名
            owners: フィールドの所有者となるプレイヤーのリスト
            count: 初期ターン数（0の場合は非アクティブ）
        """
        super().__init__(FIELDS[name])
        self.data: FieldData  # IDE hint
        self.owners: list[Player] = owners
        self.count = count
        self.layers = 0  # まきびし、どくびしなどの層数管理
        self.reveal()

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new, keys_to_deepcopy=[])

    def update_reference(self, owners: list[Player]):
        """フィールドの所有者参照を更新する。

        Args:
            owners: 新しい所有者（プレイヤー）のリスト
        """
        self.owners = owners

    def activate(self, events: EventManager, count: int):
        """フィールド効果を有効化する。

        Args:
            events: イベントマネージャー
            count: フィールド効果の継続ターン数
        """
        self.count = count
        for player in self.owners:
            self.register_handlers(events, player)

    def deactivate(self, events: EventManager):
        """フィールド効果を無効化する。

        Args:
            events: イベントマネージャー
        """
        self.count = 0
        for player in self.owners:
            self.unregister_handlers(events, player)

    @property
    def name(self) -> str:
        """フィールド名を取得する。

        Returns:
            フィールドが有効な場合は名前、無効な場合は空文字
        """
        return super().name if self.count else ""

    @property
    def turn_extention_item(self) -> str | None:
        """フィールド効果の継続ターンを延長するアイテムを取得する。

        Returns:
            ターン延長アイテムの名前。存在しない場合はNone
        """
        return self.data.turn_extension_item

    @property
    def is_active(self) -> bool:
        """フィールド効果が有効かどうかを判定する。

        Returns:
            残りターン数が1以上の場合True
        """
        return self.count > 0
