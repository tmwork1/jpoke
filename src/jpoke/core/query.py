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
from jpoke.core import EventContext, AttackContext
from jpoke.utils import fast_copy
from jpoke.utils.type_defs import MoveCategory


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
        return self._events.emit(
            Event.ON_CHECK_TRAPPED,
            EventContext(source=pokemon),
            False
        )

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

    def is_contact(self, ctx: AttackContext) -> bool:
        """技が接触技かどうかを判定する。
        Args:
            ctx: AttackContextインスタンス

         Returns:
            技が接触技の場合True
        """
        return self._events.emit(
            Event.ON_CHECK_CONTACT,
            ctx,
            ctx.move.has_label("contact")
        )

    def resolve_move_category(self, attacker: Pokemon, move: Move) -> MoveCategory:
        """実際の技カテゴリを判定する（MoveExecutorへの委譲）。

        Args:
            attacker: 技を使用するポケモン
            move: 技オブジェクト

        Returns:
            有効な技のカテゴリ（"物理"、"特殊"、"変化"のいずれか）
        """
        return self.battle.move_executor.resolve_move_category(attacker, move)

    def deals_physical_damage(self, attacker: Pokemon, move: Move) -> bool:
        """技が物理ダメージを与えるかどうかを判定する。一部の特殊技も該当する。

        Returns:
            技が物理ダメージを与える場合True
        """
        move_category = self.resolve_move_category(attacker, move)
        return (
            move_category == "物理"
            or move.has_label("physical_damage")
        )

    def is_first_actor(self, player: Player) -> bool | None:
        """このターンで player が先攻かどうかを返す（1vs1想定）。"""
        order = self.battle.turn_controller.action_order
        if not order:
            return None
        index = self.battle.players.index(player)
        return order[0] == index

    def is_second_actor(self, player: Player) -> bool | None:
        """このターンで player が後攻かどうかを返す（1vs1想定）。"""
        order = self.battle.turn_controller.action_order
        if not order:
            return None
        index = self.battle.players.index(player)
        return order[0] != index

    def is_hazard_immune(self, pokemon: Pokemon) -> bool:
        """エントリーハザードへの免疫があるか判定する。"""
        return self._events.emit(
            Event.ON_CHECK_HAZARD_IMMUNE,
            EventContext(source=pokemon),
            False
        )

    def is_super_effective(self, ctx: AttackContext) -> bool:
        """技が効果抜群かどうかを判定する。"""
        type_modifier = self.battle.damage_calculator.calc_def_type_modifier(ctx)
        return type_modifier / 4096 > 1

    def is_not_very_effective(self, ctx: AttackContext) -> bool:
        """技がいまひとつかどうかを判定する。"""
        type_modifier = self.battle.damage_calculator.calc_def_type_modifier(ctx)
        return 0 < type_modifier / 4096 < 1

    def can_switch(self, player: Player) -> bool:
        """プレイヤーが交代可能かどうかを判定する。

        Args:
            player: 交代可能かを判定するプレイヤー

        Returns:
            bool: 交代可能な場合True、そうでない場合False
        """
        state = self.battle.player_states[player]
        # 控えのポケモンがすべて瀕死の場合は交代不可
        if all(mon.fainted for mon in state.bench):
            return False
        # 場のポケモンがとらわれ状態にある場合は交代不可
        if self.is_trapped(state.active):
            return False
        return True

    def get_volatile_duration(self, ctx: AttackContext, name: str, count: int) -> int:
        """ON_MODIFY_DURATION を発火して揮発性状態の持続ターン数を返す。

        Args:
            ctx: AttackContext
            name: 揮発性状態名
            count: 基本ターン数

        Returns:
            int: アイテム等の効果を反映した最終ターン数
        """
        _, modified_count = self._events.emit(
            Event.ON_MODIFY_DURATION,
            ctx,
            [name, count]
        )
        return modified_count
