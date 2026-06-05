"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager, Player
    from jpoke.model import Move

from jpoke.model import Pokemon
from jpoke.enums import Event
from jpoke.core import EventContext, BaseContext
from jpoke.utils import fast_copy


class PokemonQuery:
    """ポケモン個体に関する読み取り専用クエリをまとめたクラス。

    状態を変更せず、イベントを通じて現在の判定結果を返す。

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
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    @property
    def _events(self) -> EventManager:
        return self.battle.events

    def get_forced_move_name(self, pokemon: Pokemon) -> str | None:
        """強制行動中のポケモンが実行すべき技名を返す。"""
        for volatile in pokemon.volatiles.values():
            if volatile.data.forced:
                return volatile.move_name
        return None

    def is_floating(self, pokemon: Pokemon) -> bool:
        """浮いている状態か判定する。

        Args:
            pokemon: 対象のポケモン

        Returns:
            浮いていればTrue

        Note:
            タイプや特性、技の効果を考慮して判定する。
        """
        return self._events.emit(
            Event.ON_CHECK_FLOATING,
            EventContext(source=pokemon),
            pokemon.has_type("ひこう")
        )

    def is_trapped(self, pokemon: Pokemon) -> bool:
        """逃げられない状態か判定する。

        Args:
            pokemon: 対象のポケモン

        Returns:
            逃げられない場合True

        Note:
            ゴーストタイプは逃げられる。
        """
        trapped = self._events.emit(
            Event.ON_CHECK_TRAPPED,
            EventContext(source=pokemon),
            False
        )
        return trapped and not pokemon.has_type("ゴースト")

    def is_nervous(self, pokemon: Pokemon) -> bool:
        """きんちょうかん状態か判定する。

        Args:
            pokemon: 対象のポケモン

        Returns:
            きんちょうかん状態の場合True
        """
        return self._events.emit(
            Event.ON_CHECK_NERVOUS,
            EventContext(source=pokemon),
            False
        )

    def is_contact(self, ctx: BaseContext) -> bool:
        """技が接触技かどうかを判定する。
        Args:
            ctx: EventContextインスタンス

         Returns:
            技が接触技の場合True
        """
        return self._events.emit(
            Event.ON_CHECK_CONTACT,
            ctx,
            ctx.move.has_label("contact")
        )

    def deals_physical_damage(self, attacker: Pokemon, move: Move) -> bool:
        """技が物理ダメージを与えるかどうかを判定する。一部の特殊技も該当する。

        Returns:
            技が物理ダメージを与える場合True
        """
        move_category = self.battle.resolve_move_category(attacker, move)
        return (
            move_category == "物理"
            or move.has_label("physical_damage")
        )

    def is_first_actor(self, player: Player) -> bool | None:
        """このターンで player が先攻かどうかを返す（1vs1想定）。"""
        state = self.battle.player_states[player]
        if state.action_order_index is None:
            return None
        return state.action_order_index == 0

    def is_second_actor(self, player: Player) -> bool | None:
        """このターンで player が後攻かどうかを返す（1vs1想定）。"""
        state = self.battle.player_states[player]
        if state.action_order_index is None:
            return None
        return state.action_order_index == 1
