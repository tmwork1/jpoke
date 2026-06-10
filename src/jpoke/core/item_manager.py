"""アイテム操作ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .event_manager import EventManager

from jpoke.utils import fast_copy
from jpoke.utils.type_defs import ItemDisabledReason
from jpoke.enums import Event, LogCode
from jpoke.model import Pokemon, Move, Item

from .context import EventContext


class ItemManager:
    """アイテムの変更処理と関連ハンドラ同期を管理する。"""

    def __init__(self, battle: Battle):
        self.battle = battle

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[])
        return new

    def update_reference(self, battle: Battle):
        """Battleインスタンスの参照を更新する。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    @property
    def _events(self) -> EventManager:
        """Battleのイベントシステムへのショートカットプロパティ。"""
        return self.battle.events

    def add_disabled_reason(self, mon: Pokemon, reason: ItemDisabledReason) -> bool:
        """アイテムを無効にする理由を追加し、有効状態に変化があればイベントを発火する。
        Args:
            mon: 対象のポケモン
            reason: 無効化の理由を示すキー
        Returns:
            アイテムの有効状態に変化があった場合はTrue、そうでない場合はFalse
        """
        was_enabled = mon.item.enabled
        mon.item.add_disable_reason(reason)
        is_enabled = mon.item.enabled

        if was_enabled and not is_enabled:
            self._events.emit(
                Event.ON_ITEM_DISABLED,
                EventContext(source=mon)
            )
            return True
        return False

    def remove_disabled_reason(self, mon: Pokemon, reason: ItemDisabledReason) -> bool:
        """アイテムを無効にする理由を削除し、有効状態に変化があればイベントを発火する。
        Args:
            mon: 対象のポケモン
            reason: 無効化の理由を示すキー
        Returns:
            アイテムの有効状態に変化があった場合はTrue、そうでない場合はFalse
        """
        was_enabled = mon.item.enabled
        mon.item.remove_disable_reason(reason)
        is_enabled = mon.item.enabled

        if not was_enabled and is_enabled:
            self._events.emit(
                Event.ON_ITEM_ENABLED,
                EventContext(source=mon)
            )
            return True
        return False

    def can_change_item(self,
                        target: Pokemon,
                        source: Pokemon | None = None,
                        move: Move | None = None) -> bool:
        """アイテム変更が許可されるかを共通イベントで判定する。

        Args:
            target: アイテムを変更するポケモン
            source: 変更の発生源となるポケモン
            move: 関連する技

        Returns:
            変更可能な場合はTrue
        """
        return self._events.emit(
            Event.ON_CHECK_ITEM_CHANGE,
            EventContext(target=target, source=source),
            True
        )

    def _change_item(self, mon: Pokemon, name: str) -> None:
        """ポケモンのアイテムを更新し、ハンドラ登録も同期する。

        Args:
            mon: アイテムを変更するポケモン
            name: 新しいアイテムの名前
        """
        is_active = self.battle.is_active(mon)
        ctx = EventContext(source=mon)

        # アイテムを変更する前に、現在のアイテムのハンドラを解除してイベントを発火する
        if mon.has_item():
            if not name:
                mon.last_lost_item_name = mon.item.base_name
            self._events.emit(Event.ON_ITEM_LOST, ctx)
            mon.item.unregister_handlers(self._events, mon)

        # アイテムを変更してハンドラを登録し、イベントを発火する
        mon.item = Item(name)
        mon.item.revealed = True

        if mon.item.name:
            self.battle.add_event_log(
                mon,
                LogCode.ITEM_GAINED,
                payload={"item": mon.item.name}
            )
        else:
            self.battle.add_event_log(
                mon,
                LogCode.ITEM_LOST,
                payload={"item": mon.last_lost_item_name}
            )

        if is_active and name:
            mon.item.register_handlers(self._events, mon)
            self._events.emit(Event.ON_ITEM_GAINED, ctx)

    def gain_item(self, target: Pokemon, name: str) -> bool:
        """対象のポケモンがアイテムを得る。

        Args:
            target: アイテムを得るポケモン
            name: 得るアイテムの名前

        Returns:
            アイテムを得ることに成功した場合はTrue
        """
        # 対象がすでにアイテムを持っている場合は失敗
        if target.has_item():
            return False
        self._change_item(target, name)
        return True

    def remove_item(self,
                    target: Pokemon,
                    source: Pokemon | None = None,
                    move: Move | None = None) -> bool:
        """対象のアイテムを失わせる。

        Args:
            target: アイテムを失うポケモン
            source: 変更の発生源となるポケモン
            move: 関連する技

        Returns:
            取り外しに成功した場合はTrue
        """
        # 対象がアイテムを持っていない場合は失敗
        if not target.has_item():
            return False

        # アイテムの変更が禁止されている場合は失敗
        if not self.can_change_item(target, source=source, move=move):
            return False

        self._change_item(target, "")
        return True

    def swap_items(self, move: Move | None = None) -> bool:
        """2体のアイテムを入れ替える。

        Args:
            target: 入れ替え元のポケモン
            source: 入れ替え先のポケモン
            move: 関連する技

        Returns:
            入れ替えに成功した場合はTrue
        """
        mons = self.battle.actives
        names = [mon.item.name for mon in mons]

        # 両方ともアイテムを持っていない場合は失敗
        if not any(names):
            return False

        # アイテムの変更が禁止されている場合は失敗
        if not all(
            self.can_change_item(target=mon, move=move) for mon in mons
        ):
            return False

        for i, mon in enumerate(mons):
            new_name = names[1 - i]  # 入れ替え先のアイテム名
            self._change_item(mon, new_name)
        return True

    def take_item(self,
                  target: Pokemon,
                  move: Move | None = None) -> bool:
        """対象のアイテムを奪う。

        Args:
            target: アイテムを奪われるポケモン
            move: 関連する技

        Returns:
            奪取に成功した場合はTrue
        """
        source = self.battle.foe(target)

        # 対象がアイテムを持っていないか、奪う側がアイテムを持っている場合は失敗
        if (
            not target.has_item()
            or source.has_item()
        ):
            return False
        return self.swap_items(move=move)
