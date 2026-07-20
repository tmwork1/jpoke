"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager, Player
    from jpoke.model import Move

from jpoke.model.pokemon import Pokemon
from jpoke.enums import Event
from .context import EventContext, AttackContext
from jpoke.utils import fast_copy
from jpoke.types import MoveCategory


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

    def can_use_last_resort(self, pokemon: Pokemon) -> bool:
        """とっておきの発動条件を満たしているか判定する。

        自身がとっておきを覚えており、かつとっておき以外に覚えている技を
        すべて場に出てから1回以上PP消費して使用していれば True を返す。
        Champions では条件を満たしていない場合、とっておき自体を選択できない。
        """
        if not pokemon.has_move("とっておき"):
            return False
        other_move_names = [m.name for m in pokemon.moves if m.name != "とっておき"]
        if not other_move_names:
            return False
        return all(name in pokemon.pp_consumed_moves for name in other_move_names)

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
            ctx.move.has_flag("contact")
        )

    def is_contact_reaction(self, ctx: AttackContext) -> bool:
        """相手の直接攻撃を受けたことに反応する効果（さめはだ・ゴツゴツメット等）が
        発動対象となる接触かどうかを判定する。

        Note:
            かたいツメ/どくしゅ/ふかしのこぶしのように「自分の技が接触技であること」
            に由来する効果や、もふもふ/わるいてぐせのようにぼうごパットの対象外となる
            効果を判定する場合は、こちらではなく is_contact() を使う。

        Args:
            ctx: AttackContextインスタンス

        Returns:
            技が接触技であり、かつぼうごパット等で反応効果が防がれていない場合True
        """
        return self._events.emit(
            Event.ON_CHECK_CONTACT_REACTION,
            ctx,
            self.is_contact(ctx),
        )

    def resolve_move_category(self, attacker: Pokemon, move: Move) -> MoveCategory:
        """実際の技カテゴリを判定する（MoveExecutorへの委譲）。

        Args:
            attacker: 技を使用するポケモン
            move: 技オブジェクト

        Returns:
            有効な技のカテゴリ（"physical"、"special"、"status"のいずれか）
        """
        return self.battle.move_executor.resolve_move_category(attacker, move)

    def deals_physical_damage(self, attacker: Pokemon, move: Move) -> bool:
        """技が物理ダメージを与えるかどうかを判定する。一部の特殊技も該当する。

        Returns:
            技が物理ダメージを与える場合True
        """
        move_category = self.resolve_move_category(attacker, move)
        return (
            move_category == "physical"
            or move.has_flag("physical_damage")
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
        return type_modifier > 4096

    def is_not_very_effective(self, ctx: AttackContext) -> bool:
        """技がいまひとつかどうかを判定する。"""
        type_modifier = self.battle.damage_calculator.calc_def_type_modifier(ctx)
        return 0 < type_modifier < 4096

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

    def has_available_bench(self, player: Player) -> bool:
        """プレイヤーの控えに瀕死でないポケモンが残っているかを判定する。

        だっしゅつパックなど、とらわれ状態（にげられない・バインド・ねをはる・
        フェアリーロックや特性かげふみ・ありじごく・じりょくなど）を無視して
        強制的に交代させる効果の判定に使う。

        Args:
            player: 判定するプレイヤー

        Returns:
            bool: 交代先が残っている場合True
        """
        state = self.battle.player_states[player]
        return any(not mon.fainted for mon in state.bench)

    def get_volatile_duration(self, ctx: AttackContext, name: str, count: int) -> int:
        """ON_MODIFY_BIND_DURATION を発火して揮発性状態の持続ターン数を返す。

        Notes:
            フィールド・場の状態の持続ターン延長で使う Event.ON_MODIFY_DURATION は
            EventContext 専用イベントのため、AttackContext から発火する本メソッドでは
            別イベント（ON_MODIFY_BIND_DURATION）を使う（1イベント=1コンテキスト型の原則）。

        Args:
            ctx: AttackContext
            name: 揮発性状態名
            count: 基本ターン数

        Returns:
            int: アイテム等の効果を反映した最終ターン数
        """
        _, modified_count = self._events.emit(
            Event.ON_MODIFY_BIND_DURATION,
            ctx,
            [name, count]
        )
        return modified_count
