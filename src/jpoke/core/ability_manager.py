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
        """Battleのイベントマネージャーへのショートカットプロパティ。"""
        return self.battle.events

    def change_ability(self, mon: Pokemon, ability: str) -> None:
        """ポケモンの特性を更新し、ハンドラの登録/解除やイベントの発火を行う。
        Args:
            mon: 特性を変更するポケモン
            ability: 新しい特性の名前
        """
        if mon.ability.base_name == ability:
            return

        is_active = self.battle.is_active(mon)
        ctx = EventContext(source=mon)

        if is_active:
            self._events.emit(Event.ON_ABILITY_DISABLED, ctx)
            mon.ability.unregister_handlers(self._events, mon)

        mon.ability = Ability(ability)

        if is_active:
            mon.ability.register_handlers(self._events, mon)
            self._events.emit(Event.ON_ABILITY_ENABLED, ctx)

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
