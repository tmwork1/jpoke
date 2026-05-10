"""特性の有効/無効状態管理モジュール。"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from jpoke.model import Pokemon

from jpoke.utils.type_defs import EnableKey
from jpoke.enums import Event
from .context import BattleContext


class AbilityManager:
    """場の特性の有効/無効状態と発動状態を管理するクラス。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: "Battle"):
        """AbilityManagerを初期化する。

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

    def refresh_ability_enabled_states(self) -> dict[str, dict[EnableKey, bool]]:
        """場の状況に応じて特性の有効/無効状態を再計算する。
        Returns:
            dict[str, dict[EnableKey, bool]]: 特性の有効/無効状態の辞書
        """
        results = {}
        for i, mon in enumerate(self.battle.actives):
            if mon is None:
                continue

            states = self.battle.events.emit(
                Event.ON_CHECK_ABILITY_ENABLED,
                BattleContext(source=mon),
                {"self": mon.ability.get_enabled("self")}
            )
            mon.ability.replace_enabled(states)
            results[f"ability_{i+1}"] = states

        # こだいかっせい・クォークチャージの発動状態を再判定する。
        self.battle.events.emit(Event.ON_REFRESH_PARADOX_BOOST)

        return results

    def set_ability(self,
                    mon: Pokemon,
                    ability_name: str,
                    refresh_enabled_states: bool = True) -> None:
        """ポケモンの特性を更新し、ハンドラ登録状態を同期する。"""
        if mon.ability.orig_name == ability_name:
            return

        was_active = mon in self.battle.actives
        was_enabled = mon.ability.enabled

        if was_active:
            mon.ability.unregister_handlers(self.battle.events, mon)

        mon.ability = ability_name
        mon.ability.enabled = was_enabled

        if was_active and mon.ability.enabled:
            mon.ability.register_handlers(self.battle.events, mon)

        if refresh_enabled_states:
            self.refresh_ability_enabled_states()
