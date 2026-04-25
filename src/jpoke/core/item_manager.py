"""持ち物操作ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle

from jpoke.enums import Event
from jpoke.model import Pokemon, Move, Item

from .context import BattleContext


class ItemManager:
    """持ち物の変更・入れ替え・奪取・消失の共通処理を管理する。"""

    def __init__(self, battle: "Battle"):
        self.battle = battle

    def update_reference(self, battle: "Battle"):
        self.battle = battle

    def set_item(self, target: Pokemon, item: str | Item) -> None:
        """ポケモンの持ち物を更新し、必要なハンドラ登録も同期する。"""
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
        """持ち物変更が許可されるかを共通イベントで判定する。"""
        return self.battle.events.emit(
            Event.ON_CHECK_ITEM_CHANGE,
            BattleContext(source=source, target=target, move=move),
            True
        )

    def swap_items(self, source: Pokemon, target: Pokemon, move: Move | None = None) -> bool:
        """2体の持ち物を入れ替える。"""
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
        """対象の持ち物を source に移す。"""
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
        """対象の持ち物を失わせる。"""
        if not check_on_empty and not target.has_item():
            return False
        if not self.can_change_item(source, target, move=move, reason=reason):
            return False
        if not target.has_item():
            return False

        self.set_item(target, "")
        return True
