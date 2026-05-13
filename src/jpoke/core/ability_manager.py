"""特性の有効/無効状態管理モジュール。"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from jpoke.model import Pokemon

from jpoke.utils.type_defs import AbilityDisabledReason
from jpoke.enums import Event
from jpoke.model import Ability
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

    def refresh_ability_enabled_states(self) -> dict[str, set[AbilityDisabledReason]]:
        """場の状況に応じて特性の有効/無効状態を再計算する。
        Returns:
            dict[str, set[DisabledReason]]: 特性の有効/無効状態の辞書
        """
        results = {}
        for i, mon in enumerate(self.battle.actives):
            if (
                mon is None
                or mon.ability.self_disabled
            ):
                continue

            reasons = self.battle.events.emit(
                Event.ON_CHECK_ABILITY_ENABLED,
                BattleContext(source=mon),
                set(),
            )
            mon.ability.set_disabled_reasons(reasons)
            results[f"ability_{i+1}"] = reasons

        # こだいかっせい・クォークチャージの発動状態を再判定する。
        self.battle.events.emit(Event.ON_REFRESH_PARADOX_BOOST)

        return results

    def set_ability(self, mon: Pokemon, ability: str) -> None:
        """ポケモンの特性を更新し、ハンドラ登録状態を同期する。"""
        if mon.ability.orig_name == ability:
            return

        is_active = self.battle.is_active(mon)

        if is_active:
            mon.ability.unregister_handlers(self.battle.events, mon)

        mon.ability = Ability(ability)

        if is_active:
            mon.ability.register_handlers(self.battle.events, mon)
            self.refresh_ability_enabled_states()
