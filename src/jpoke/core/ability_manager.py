"""特性の有効/無効状態管理モジュール。"""
from __future__ import annotations

from typing import TYPE_CHECKING

from jpoke.enums import Event
from .context import BattleContext

if TYPE_CHECKING:
    from .battle import Battle
    from jpoke.model import Pokemon


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

    def set_ability_enabled(self, mon: "Pokemon", enabled: bool) -> None:
        """特性の有効/無効状態を更新し、ハンドラ登録状態を同期する。"""
        ability = mon.ability
        if ability.enabled == enabled:
            return

        if ability.enabled:
            ability.unregister_handlers(self.battle.events, mon)
            ability.enabled = False
            return

        ability.enabled = True
        if mon in self.battle.actives:
            ability.register_handlers(self.battle.events, mon)

    def set_ability(self,
                    mon: "Pokemon",
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

    def refresh_ability_enabled_states(self):
        """場の状況に応じて特性の有効/無効状態を再計算する。

        Note:
            ON_CHECK_ABILITY_ENABLEDイベントを使用して判定を実施。
            ハンドラは入場時に特性・持ち物から通常登録される。
        """
        actives = [mon for mon in self.battle.actives if mon is not None]

        for mon in actives:
            ability = mon.ability

            # per_battle_once 特性は一度無効化されたら交代後も再有効化しない。
            if "per_battle_once" in ability.data.flags and not ability.enabled:
                continue

            # 基本判定：生存していれば有効
            # とくせいなし等の追加無効化条件は各ハンドラ側で判定する
            should_enable = mon.alive

            # イベント駆動で有効/無効を判定
            # context の source は判定対象ポケモン。
            should_enable = self.battle.events.emit(
                Event.ON_CHECK_ABILITY_ENABLED,
                BattleContext(source=mon),
                should_enable
            )

            self.set_ability_enabled(mon, should_enable)

        self.refresh_paradox_boost_states()

    def refresh_paradox_boost_states(self):
        """こだいかっせい・クォークチャージの発動状態を再判定する。"""
        self.battle.events.emit(Event.ON_REFRESH_PARADOX_BOOST)
