"""アイテム操作ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from .battle import Battle
    from .event_manager import EventManager

from jpoke.utils import fast_copy
from jpoke.types import ItemDisabledReason, ItemName
from jpoke.enums import Event, LogCode
from jpoke.model.pokemon import Pokemon
from jpoke.model.item import Item

from .context import EventContext
from .log_payload import ItemPayload


class ItemManager:
    """アイテムの変更処理と関連ハンドラ同期を管理する。"""

    def __init__(self, battle: Battle):
        self.battle = battle
        self.suppress_berry_consumed_event: bool = False
        """True の間は consume_item が Event.ON_BERRY_CONSUMED を発火しない。
        はんすうが自分の再発動できのみを消費する際、その消費自体が新たな
        はんすうカウントの起点にならないようにするための一時停止フラグ。
        """

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
                        *,
                        dry_run: bool = False,
                        ignore_sticky_hold: bool = False,
                        is_exchange: bool = False) -> bool:
        """アイテム変更が許可されるかを共通イベントで判定する。

        Args:
            target: アイテムを変更するポケモン
            source: 変更の発生源となるポケモン
            dry_run: True の場合、実際に変更を試みるわけではない判定のみの呼び出しとして扱う
                （例: はたきおとすの威力補正判定）。ねんちゃく等、実除去は防ぐが判定のみの
                呼び出しでは特性発動を表に出さない特性の分岐に使う。
            ignore_sticky_hold: True の場合、ねんちゃくによる奪取阻止のみを無視する
                （例: むしくい・ついばむが対象をひんしにさせた場合の第五世代以降の仕様）。
                ねんちゃく以外のアイテム変更禁止効果（マルチタイプ等）は通常通り機能する。
            is_exchange: True の場合、トリック・すりかえ等、相手の道具と入れ替わる形の
                道具変更判定として扱う（ARシステム等、相手の道具次第で交換自体が
                失敗する特性の判定に使う）。

        Returns:
            変更可能な場合はTrue
        """
        return self._events.emit(
            Event.ON_CHECK_ITEM_CHANGE,
            EventContext(
                target=target, source=source, dry_run=dry_run,
                ignore_sticky_hold=ignore_sticky_hold, is_exchange=is_exchange,
            ),
            True
        )

    def _change_item(self,
                     mon: Pokemon,
                     name: ItemName,
                     *,
                     track_loss: bool = True) -> None:
        """ポケモンのアイテムを更新し、ハンドラ登録も同期する。

        Args:
            mon: アイテムを変更するポケモン
            name: 新しいアイテムの名前
            track_loss: True の場合、アイテムを失ったときに last_lost_item_name を
                更新する（リサイクル・しゅうかく・ものひろい等の復元/拾得対象になる）。
                どろぼう・ほしがる・すりかえ等、道具が場に存在したまま相手に渡る場合は
                False を指定し、復元/拾得の対象にしない。
        """
        is_active = self.battle.is_active(mon)
        ctx = EventContext(source=mon)
        lost_item_name = mon.item.base_name if mon.has_item() else ""

        # アイテムを変更する前に、現在のアイテムのハンドラを解除してイベントを発火する
        if mon.has_item():
            if not name and track_loss:
                mon.last_lost_item_name = cast(ItemName, lost_item_name)
                mon.last_lost_item_turn = self.battle.turn
            self._events.emit(Event.ON_ITEM_LOST, ctx)
            mon.item.unregister_handlers(self._events, mon)

        # アイテムを変更してハンドラを登録し、イベントを発火する
        mon.item = Item(name)
        mon.item.revealed = True

        if mon.item.name:
            self.battle.add_event_log(
                mon,
                LogCode.ITEM_GAINED,
                payload=ItemPayload(item=mon.item.name)
            )
        else:
            self.battle.add_event_log(
                mon,
                LogCode.ITEM_LOST,
                payload=ItemPayload(item=lost_item_name)
            )

        if is_active and name:
            mon.item.register_handlers(self._events, mon)
            self._events.emit(Event.ON_ITEM_GAINED, ctx)

    def gain_item(self, target: Pokemon, name: ItemName) -> bool:
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
                    *,
                    track_loss: bool = True) -> bool:
        """対象のアイテムを失わせる。

        Args:
            target: アイテムを失うポケモン
            source: 変更の発生源となるポケモン
            track_loss: True の場合、last_lost_item_name を更新し
                リサイクル・しゅうかく・ものひろい等の復元/拾得対象にする。
                はたきおとす・やきつくす・ふしょくガス等、場に存在したまま
                消滅する扱いの効果では False を指定する。

        Returns:
            取り外しに成功した場合はTrue
        """
        # 対象がアイテムを持っていない場合は失敗
        if not target.has_item():
            return False

        # アイテムの変更が禁止されている場合は失敗
        if not self.can_change_item(target, source=source):
            return False

        self._change_item(target, "", track_loss=track_loss)
        return True

    def set_item(self,
                target: Pokemon,
                name: ItemName,
                source: Pokemon | None = None) -> bool:
        """ポケモンの持ち物を任意の状態に設定する（シナリオ構築・ダメージ計算検証用）。

        現在の持ち物と一致する場合は何もせず成功扱いにする。持ち物を持たない場合は
        そのまま獲得させ、name が空文字列の場合は除去する。既に別の持ち物を持っている
        場合は can_change_item による判定を経て入れ替える（gain_item / remove_item /
        _change_item の組み合わせでは表現できない「既存の持ち物を別の持ち物へ
        直接差し替える」経路をまとめたもの）。

        Args:
            target: 持ち物を設定するポケモン
            name: 設定後の持ち物名（空文字列の場合は持ち物を外す）
            source: 変更の原因となったポケモン（例: 交換元のポケモン、技の使用者など）

        Returns:
            bool: 設定に成功した場合True
        """
        if target.has_item(name):
            return True
        if not target.has_item():
            return self.gain_item(target, name)
        if not name:
            return self.remove_item(target, source=source)
        if not self.can_change_item(target, source=source):
            return False
        self._change_item(target, name)
        return True

    def swap_items(self,
                  *,
                  source: Pokemon | None = None,
                  ignore_sticky_hold: bool = False) -> bool:
        """2体のアイテムを入れ替える。

        Args:
            source: 交換の発生源となるポケモン（トリック・すりかえ・どろぼう等の
                使用者）。ねんちゃくを持つポケモン自身がこの交換を起こした場合
                （= source が対象自身と同一の場合）は、ねんちゃくの効果は
                発動しない（自分から道具を交換するときは防がれない）。
            ignore_sticky_hold: True の場合、ねんちゃくによる奪取阻止のみを無視する
                （むしくい・ついばむが対象をひんしにさせた場合の第五世代以降の仕様）。

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
            self.can_change_item(
                target=mon, source=source,
                ignore_sticky_hold=ignore_sticky_hold, is_exchange=True,
            )
            for mon in mons
        ):
            return False

        for i, mon in enumerate(mons):
            new_name = names[1 - i]  # 入れ替え先のアイテム名
            # 相手に渡った道具は場に存在し続けるため、リサイクル等の
            # 復元対象にしない（track_loss=False）
            self._change_item(mon, cast(ItemName, new_name), track_loss=False)
        return True

    def take_item(self,
                  target: Pokemon,
                  *,
                  ignore_sticky_hold: bool = False) -> bool:
        """対象のアイテムを奪う。

        Args:
            target: アイテムを奪われるポケモン
            ignore_sticky_hold: True の場合、ねんちゃくによる奪取阻止のみを無視する
                （むしくい・ついばむが対象をひんしにさせた場合の第五世代以降の仕様）。

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
        return self.swap_items(source=source, ignore_sticky_hold=ignore_sticky_hold)

    def consume_item(self, target: Pokemon, *, track_loss: bool = True) -> bool:
        """ポケモンの道具を消費する。

        きのみを消費する場合は食べたフラグを立ててから remove_item を呼ぶ。

        Args:
            target: アイテムを消費するポケモン
            track_loss: True の場合、last_lost_item_name を更新し
                リサイクル・しゅうかく・ものひろい等の復元/拾得対象にする。
                割れたふうせん等、対象外にすべき場合は False を指定する。

        Returns:
            消費に成功した場合はTrue
        """
        if target.item.is_berry():
            target.ate_berry = True
            if not self.suppress_berry_consumed_event:
                self._events.emit(
                    Event.ON_BERRY_CONSUMED,
                    EventContext(source=target, item_name=cast(ItemName, target.item.base_name))
                )
        return self.remove_item(target, source=target, track_loss=track_loss)

    def force_trigger_berry(self, mon: Pokemon, *, track_loss: bool = True) -> None:
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
            track_loss: True の場合、消費したきのみは last_lost_item_name に記録され
                リサイクル等の復元対象になる。むしくい・ついばむで奪って自分が消費した
                きのみは復元対象にならないため False を指定する。各きのみハンドラは
                個別に track_loss を意識しないため、False の場合は発動後に
                last_lost_item_name を発動前の値へ戻して記録を打ち消す。
        """
        previous_last_lost = mon.last_lost_item_name
        previous_last_lost_turn = mon.last_lost_item_turn
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
        if not track_loss:
            mon.last_lost_item_name = previous_last_lost
            mon.last_lost_item_turn = previous_last_lost_turn
