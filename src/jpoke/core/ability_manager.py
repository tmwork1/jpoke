"""特性の有効/無効状態管理モジュール。"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from jpoke.model import Pokemon

from jpoke.utils import fast_copy
from jpoke.utils.type_defs import AbilityDisabledReason
from jpoke.enums import Event
from jpoke.model import Ability
from .context import EventContext


class AbilityManager:
    """場の特性の有効/無効状態と発動状態を管理するクラス。

    Attributes:
        battle: 親となるBattleインスタンス
    """

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
    def _events(self):
        return self.battle.events

    def _register_ability_handlers(self, mon: Pokemon):
        """ポケモンの特性のハンドラをイベントマネージャに登録する。

        Args:
            mon: 対象のポケモン
        """
        mon.ability.register_handlers(self._events, mon)

    def _unregister_ability_handlers(self, mon: Pokemon):
        """ポケモンの特性のハンドラをイベントマネージャから解除する。

        Args:
            mon: 対象のポケモン
        """
        mon.ability.unregister_handlers(self._events, mon)

    def change_ability(self, mon: Pokemon, ability: str) -> None:
        """ポケモンの特性を更新し、ハンドラの登録/解除やイベントの発火を行う。
        Args:
            mon: 特性を変更するポケモン
            ability: 新しい特性の名前
        """
        if mon.ability.base_name == ability:
            return

        ctx = EventContext(source=mon)
        is_active = self.battle.is_active(mon)

        # 対象のポケモンが場に出ている場合は、古い特性のハンドラを解除し、イベントを発火する
        if is_active:
            self._unregister_ability_handlers(mon)
            self._events.emit(Event.ON_ABILITY_DISABLED, ctx)

        # 新しい特性に更新して公開する
        mon.ability = Ability(ability)
        mon.ability.revealed = True

        # 対象のポケモンが場に出ている場合は、新しい特性のハンドラを登録し、イベントを発火する
        if is_active:
            self._register_ability_handlers(mon)
            self._events.emit(Event.ON_ABILITY_ENABLED, ctx)

    def swap_ability(self, mon1: Pokemon, mon2: Pokemon) -> None:
        """2体のポケモンの特性を入れ替える。

        Args:
            mon1: 1体目のポケモン
            mon2: 2体目のポケモン
        """
        ability1 = mon1.ability.base_name
        ability2 = mon2.ability.base_name

        # 両者の特性の無効化イベントをまとめて発火する
        self._events.emit(Event.ON_ABILITY_DISABLED)

        for mon, ability in ((mon1, ability2), (mon2, ability1)):
            self._unregister_ability_handlers(mon)
            mon.ability = Ability(ability)
            self._register_ability_handlers(mon)

        # 両者の特性の有効化イベントをまとめて発火する
        self._events.emit(Event.ON_ABILITY_ENABLED)

    def add_disabled_reason(self, mon: Pokemon, reason: AbilityDisabledReason) -> bool:
        """特性を無効にする理由を追加し、有効状態に変化があればイベントを発火する。
        Args:
            mon: 対象のポケモン
            reason: 無効化の理由を示すキー
        Returns:
            特性の有効状態に変化があった場合はTrue、そうでない場合はFalse
        """
        was_enabled = mon.ability.enabled
        mon.ability.add_disable_reason(reason)
        is_enabled = mon.ability.enabled

        if was_enabled and not is_enabled:
            self._events.emit(
                Event.ON_ABILITY_DISABLED,
                EventContext(source=mon)
            )
            return True
        return False

    def remove_disabled_reason(self, mon: Pokemon, reason: AbilityDisabledReason) -> bool:
        """特性を無効にする理由を削除し、有効状態に変化があればイベントを発火する。
        Args:
            mon: 対象のポケモン
            reason: 無効化の理由を示すキー
        Returns:
            特性の有効状態に変化があった場合はTrue、そうでない場合はFalse
        """
        was_enabled = mon.ability.enabled
        mon.ability.remove_disable_reason(reason)
        is_enabled = mon.ability.enabled

        if not was_enabled and is_enabled:
            self._events.emit(
                Event.ON_ABILITY_ENABLED,
                EventContext(source=mon)
            )
            return True
        return False
