"""持ち物操作ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle

from jpoke.enums import Event
from jpoke.model import Pokemon, Move, Item

from .context import BattleContext


class ItemManager:
    """持ち物の変更処理と関連ハンドラ同期を管理する。"""

    def __init__(self, battle: "Battle"):
        """ItemManagerを初期化する。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def update_reference(self, battle: "Battle"):
        """Battleインスタンスの参照を更新する。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    def set_item(self, target: Pokemon, item: str | Item) -> None:
        """ポケモンの持ち物を更新し、ハンドラ登録も同期する。

        Args:
            target: 持ち物を変更するポケモン
            item: 新しい持ち物
        """
        old_item = target.item
        old_item.unregister_handlers(self.battle.events, target)

        target.item = item

        if target in self.battle.actives:
            target.item.register_handlers(self.battle.events, target)

    def can_change_item(self,
                        source: Pokemon,
                        target: Pokemon,
                        move: Move | None = None,
                        reason: str = "") -> bool:
        """持ち物変更が許可されるかを共通イベントで判定する。

        Args:
            source: 変更の発生源となるポケモン
            target: 持ち物変更の対象ポケモン
            move: 関連する技
            reason: 変更理由

        Returns:
            変更可能な場合はTrue
        """
        return self.battle.events.emit(
            Event.ON_CHECK_ITEM_CHANGE,
            BattleContext(source=source, target=target, move=move),
            True
        )

    def swap_items(self, source: Pokemon, target: Pokemon, move: Move | None = None) -> bool:
        """2体の持ち物を入れ替える。

        Args:
            source: 入れ替え元のポケモン
            target: 入れ替え先のポケモン
            move: 関連する技

        Returns:
            入れ替えに成功した場合はTrue
        """
        if not source.has_item() and not target.has_item():
            return False
        if not self.can_change_item(source, source, move=move, reason="swap"):
            return False
        if not self.can_change_item(source, target, move=move, reason="swap"):
            return False

        source_item = source.item.name
        target_item = target.item.name
        self.set_item(source, target_item)
        self.set_item(target, source_item)
        return True

    def take_item(self,
                  source: Pokemon,
                  target: Pokemon,
                  move: Move | None = None,
                  reason: str = "steal") -> bool:
        """対象の持ち物を source に移す。

        Args:
            source: 持ち物を受け取るポケモン
            target: 持ち物を失うポケモン
            move: 関連する技
            reason: 変更理由

        Returns:
            奪取に成功した場合はTrue
        """
        if not target.has_item():
            return False
        if not self.can_change_item(source, target, move=move, reason=reason):
            return False

        item_name = target.item.name
        self.set_item(source, item_name)
        self.set_item(target, "")
        return True

    def remove_item(self,
                    source: Pokemon,
                    target: Pokemon,
                    move: Move | None = None,
                    reason: str = "remove",
                    check_on_empty: bool = False) -> bool:
        """対象の持ち物を失わせる。

        Args:
            source: 変更の発生源となるポケモン
            target: 持ち物を失うポケモン
            move: 関連する技
            reason: 変更理由
            check_on_empty: 空持ち物に対してもイベント判定を行うか

        Returns:
            取り外しに成功した場合はTrue
        """
        if not check_on_empty and not target.has_item():
            return False
        if not self.can_change_item(source, target, move=move, reason=reason):
            return False
        if not target.has_item():
            return False

        self.set_item(target, "")
        return True
