"""持ち物操作ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .event_manager import EventManager

from jpoke.utils.type_defs import AbilityDisabledReason, ItemLostCause
from jpoke.enums import Event, LogCode
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

    @property
    def events(self) -> EventManager:
        """Battleのイベントシステムへのショートカットプロパティ。"""
        return self.battle.events

    def refresh_item_enabled_states(self) -> dict[str, set[AbilityDisabledReason]]:
        """場の状況に応じて道具効果の有効/無効状態を再計算する。
        Returns:
            dict[str, set[DisabledReason]]: 道具効果の有効/無効状態の辞書
        """
        results = {}
        for i, mon in enumerate(self.battle.actives):
            if (
                mon is None
                or not mon.has_item()
                or mon.item.self_disabled
            ):
                continue
            reasons = self.events.emit(
                Event.ON_CHECK_ITEM_ENABLED,
                BattleContext(source=mon),
                set(),
            )
            mon.item.set_disabled_reasons(reasons)
            results[f"item_{i+1}"] = reasons

        return results

    def set_item(self, mon: Pokemon, item: str) -> None:
        """ポケモンの持ち物を更新し、ハンドラ登録も同期する。

        Args:
            target: 持ち物を変更するポケモン
            item: 新しい持ち物
        """
        is_active = self.battle.is_active(mon)
        if mon.has_item():
            mon.item.unregister_handlers(self.events, mon)

        mon.item = Item(item)
        if is_active:
            mon.item.register_handlers(self.events, mon)
            self.refresh_item_enabled_states()

    def lose_item(self, target: Pokemon, cause: ItemLostCause = "remove") -> bool:
        """対象の道具を喪失状態にする。"""
        if not target.has_item():
            return False

        item = target.item
        item.unregister_handlers(self.events, target)
        item.lose(cause=cause)
        self.battle.add_event_log(
            target,
            LogCode.LOSE_ITEM,
            payload={"item": item.name, "reason": cause}
        )
        return True

    def consume_item(self, target: Pokemon) -> bool:
        """対象の道具を消費状態にする。"""
        return self.lose_item(target, cause="consume")

    def can_change_item(self,
                        source: Pokemon,
                        target: Pokemon,
                        move: Move | None = None,
                        reason: str = "") -> bool:
        # TODO : 引数を target, source の順に変更し、影響範囲をすべて修正する
        """持ち物変更が許可されるかを共通イベントで判定する。

        Args:
            source: 変更の発生源となるポケモン
            target: 持ち物変更の対象ポケモン
            move: 関連する技
            reason: 変更理由

        Returns:
            変更可能な場合はTrue
        """
        return self.events.emit(
            Event.ON_CHECK_ITEM_CHANGE,
            BattleContext(source=source, target=target, move=move),
            True
        )

    def swap_items(self,
                   mon1: Pokemon,
                   mon2: Pokemon,
                   move: Move | None = None) -> bool:
        """2体の持ち物を入れ替える。

        Args:
            mon1: 入れ替え元のポケモン
            mon2: 入れ替え先のポケモン
            move: 関連する技

        Returns:
            入れ替えに成功した場合はTrue
        """
        if not mon1.has_item() and not mon2.has_item():
            return False
        if not self.can_change_item(mon1, mon1, move=move, reason="swap"):
            return False
        if not self.can_change_item(mon1, mon2, move=move, reason="swap"):
            return False

        source_item = mon1.item.name
        target_item = mon2.item.name
        if mon1.has_item():
            self.lose_item(mon1, cause="swap")
        if mon2.has_item():
            self.lose_item(mon2, cause="swap")
        self.set_item(mon1, target_item)
        self.set_item(mon2, source_item)
        return True

    def take_item(self,
                  to_mon: Pokemon,
                  from_mon: Pokemon,
                  move: Move | None = None,
                  reason: ItemLostCause = "steal") -> bool:
        # TODO : 引数を from_mon, to_mon の順に変更し、影響範囲をすべて修正する
        """対象の持ち物を to_mon に移す。

        Args:
            to_mon: 持ち物を受け取るポケモン
            from_mon: 持ち物を失うポケモン
            move: 関連する技
            reason: 変更理由

        Returns:
            奪取に成功した場合はTrue
        """

        if not from_mon.has_item():
            return False
        if not self.can_change_item(to_mon, from_mon, move=move, reason=reason):
            return False

        item_name = from_mon.item.name
        self.lose_item(from_mon, cause=reason)
        self.set_item(to_mon, item_name)
        self.set_item(from_mon, "")
        return True

    def remove_item(self,
                    source: Pokemon,
                    target: Pokemon,
                    move: Move | None = None,
                    reason: ItemLostCause = "remove",
                    check_on_empty: bool = False) -> bool:
        # TODO : 引数を target, source の順に変更し、影響範囲をすべて修正する
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

        self.lose_item(target, cause=reason)
        self.set_item(target, "")
        return True
