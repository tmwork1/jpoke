# TODO : クラスとして実装する意義があるか検討する。関数モジュールとして実装するほうがシンプルで良いかもしれない。

"""アイテム操作ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .event_manager import EventManager

from jpoke.utils import fast_copy
from jpoke.types import ItemDisabledReason
from jpoke.enums import Event, LogCode
from jpoke.model import Pokemon, Item

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
                        source: Pokemon | None = None) -> bool:
        """アイテム変更が許可されるかを共通イベントで判定する。

        Args:
            target: アイテムを変更するポケモン
            source: 変更の発生源となるポケモン

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
                    source: Pokemon | None = None) -> bool:
        """対象のアイテムを失わせる。

        Args:
            target: アイテムを失うポケモン
            source: 変更の発生源となるポケモン

        Returns:
            取り外しに成功した場合はTrue
        """
        # 対象がアイテムを持っていない場合は失敗
        if not target.has_item():
            return False

        # アイテムの変更が禁止されている場合は失敗
        if not self.can_change_item(target, source=source):
            return False

        self._change_item(target, "")
        return True

    def swap_items(self) -> bool:
        """2体のアイテムを入れ替える。

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
            self.can_change_item(target=mon) for mon in mons
        ):
            return False

        for i, mon in enumerate(mons):
            new_name = names[1 - i]  # 入れ替え先のアイテム名
            self._change_item(mon, new_name)
        return True

    def take_item(self,
                  target: Pokemon) -> bool:
        """対象のアイテムを奪う。

        Args:
            target: アイテムを奪われるポケモン

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
        return self.swap_items()

    def consume_item(self, mon: Pokemon) -> bool:
        """ポケモンの道具を消費する。

        きのみを消費する場合は食べたフラグを立ててから remove_item を呼ぶ。

        Args:
            mon: アイテムを消費するポケモン

        Returns:
            消費に成功した場合はTrue
        """
        if mon.item.is_berry():
            mon.ate_berry = True
        return self.remove_item(mon, source=mon)

    def force_trigger_berry(self, mon: Pokemon) -> None:
        """きのみを強制発動してから消費する。

        ほおばる・おちゃかい等で「HP閾値やターン終了を待たずに即座に」
        きのみ効果を発動させるときに使う。

        発火順:
        1. ON_HP_CHANGED (value=max_hp): HP 閾値ベースのきのみ（オボンのみ等）を対象にする
        2. ON_FORCE_BERRY_TRIGGER: ON_HP_CHANGED に登録されていないきのみ（
           状態異常治療きのみ等）を発動する
        3. まだ消費されていなければ consume_item で明示的に消費する

        Args:
            mon: きのみを強制発動するポケモン
        """
        # HP 閾値ベースのきのみを発動（オボンのみ・フィラのみ等）
        hp_ctx = EventContext(target=mon, source=mon)
        self._events.emit(Event.ON_HP_CHANGED, hp_ctx, mon.max_hp)
        # HP 閾値チェックなしで発動するきのみ（状態異常治療きのみ等）
        if mon.item.is_berry():
            force_ctx = EventContext(source=mon)
            self._events.emit(Event.ON_FORCE_BERRY_TRIGGER, force_ctx)
        # いずれの発火でも消費されなかった場合は明示的に消費する
        if mon.item.is_berry():
            self.consume_item(mon)
