"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.model import Pokemon, Move, Ailment, Volatile
from jpoke.utils.type_defs import AilmentName, VolatileName
from jpoke.enums import Event
from jpoke.core import BattleContext


class AilmentManager:
    """ポケモンの状態異常を管理するクラス。

    状態異常の付与、治療、ターン経過処理を担当。
    Pokemonクラスから状態異常管理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        """AilmentManagerを初期化。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def update_reference(self, battle: Battle):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    def apply(self,
              mon: Pokemon,
              name: AilmentName,
              count: int | None = None,
              source: Pokemon | None = None,
              force: bool = False) -> bool:
        """状態異常を付与する。

        Args:
            mon: 対象のポケモン
            name: 状態異常名
            count: 継続ターン数（必要な状態異常のみ）
            source: 状態異常の原因となったポケモン
            force: Trueの場合、既存の状態異常を上書き

        Returns:
            付与に成功したTrue

        Note:
            - force=Falseの場合、既に状態異常があれば失敗
            - 同じ状態異常の重ね掛けは不可
        """
        # force=True でない限り上書き不可
        if mon.ailment.is_active and not force:
            return False

        # 重ねがけ不可
        if name == mon.ailment.name:
            return False

        # ON_BEFORE_APPLY_AILMENT イベントを発火して特性などによる無効化をチェック
        # ハンドラーがvalueを空文字列に変更した場合は状態異常を防ぐ
        name = self.battle.events.emit(
            Event.ON_BEFORE_APPLY_AILMENT,
            BattleContext(target=mon, source=source),
            name
        )
        if not name:
            return False

        # 既存のハンドラを削除
        mon.ailment.unregister_handlers(self.battle.events, mon)

        # 新しい状態異常を設定してハンドラ登録
        mon.ailment = Ailment(name, count=count)
        mon.ailment.register_handlers(self.battle.events, mon)
        return True

    def remove(self, mon: Pokemon, source: Pokemon | None = None) -> bool:
        """状態異常を解除する。

        Args:
            mon: 対象のポケモン
            source: 解除の原因となったポケモン

        Returns:
            解除に成功したらTrue
        """
        if not mon.ailment.is_active:
            return False
        mon.ailment.unregister_handlers(self.battle.events, mon)
        mon.ailment = Ailment()
        return True

    def tick(self, mon: Pokemon) -> bool:
        """状態異常のターン経過処理を行う。

        Args:
            mon: 対象のポケモン

        Returns:
            ターン経過処理を行った場合True、状態異常がない場合False
        """
        if not mon.ailment.is_active:
            return False
        mon.ailment.tick()
        if mon.ailment.count == 0:
            self.remove(mon)
        return True


class VolatileManager:
    """ポケモンの揮発状態を管理するクラス。

    揮発状態の付与、解除、ターン経過処理を担当。
    Pokemonクラスから揮発状態管理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        """PokemonVolatileManagerを初期化。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def update_reference(self, battle: Battle):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    def apply_(self,
               mon: Pokemon,
               name: VolatileName,
               count: int = 1,
               move: Move | str = "",
               hp: int = 0,
               source: Pokemon | None = None) -> bool:
        """揮発性状態を付与する。

        Args:
            mon: 対象のポケモン
            name: 揮発性状態名
            count: 継続ターン数
            move: 関連する技オブジェクトまたは技名
            hp: 関連するHP値
            source: 揮発性状態の原因となったポケモン

        Returns:
            付与に成功したTrue

        Note:
            - 既に同じ揮発性状態があれば失敗
        """
        # 既に同じ揮発性状態がある場合は失敗
        if mon.has_volatile(name):
            return False

        # ON_BEFORE_APPLY_VOLATILE イベントを発火して特性やフィールドによる無効化をチェック
        # ハンドラーがvalueを空文字列に変更した場合は揮発状態を防ぐ
        name = self.battle.events.emit(
            Event.ON_BEFORE_APPLY_VOLATILE,
            BattleContext(target=mon, source=source),
            name
        )
        if not name:
            return False

        if isinstance(move, Move):
            move = move.name

        volatile = Volatile(name, count=count, move_name=move, hp=hp)
        volatile.register_handlers(self.battle.events, mon)
        mon.volatiles[name] = volatile
        return True

    def remove(self, mon: Pokemon, name: VolatileName) -> bool:
        """揮発性状態を解除する。

        Args:
            mon: 対象のポケモン
            name: 揮発性状態名

        Returns:
            解除に成功したTrue

        Note:
            指定された揮発性状態がない場合は失敗する。
        """
        if not mon.has_volatile(name):
            return False
        mon.volatiles.pop(name).unregister_handlers(self.battle.events, mon)
        return True

    def tick(self, mon: Pokemon, name: VolatileName) -> bool:
        """揮発性状態のターン経過処理を行う。

        Args:
            mon: 対象のポケモン
            name: 揮発性状態名

        Returns:
            ターン経過処理を行った場合True、指定された揮発性状態がない場合False
        """
        if not mon.has_volatile(name):
            return False
        volatile = mon.volatiles[name]
        volatile.tick()
        if volatile.count == 0:
            self.remove(mon, name)
        return True


class PokemonQueryManager:
    """ポケモンの状態判定クエリを管理するクラス。

    浮遊、束縛、びんじょう状態などの判定を担当。
    Pokemonクラスからクエリロジックを分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        """PokemonQueryManagerを初期化。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def update_reference(self, battle: Battle):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    def is_floating(self, pokemon: Pokemon) -> bool:
        """浮いている状態か判定する。

        Args:
            pokemon: 対象のポケモン

        Returns:
            浮いていればTrue

        Note:
            タイプや特性、技の効果を考慮して判定する。
        """
        floating = pokemon.has_type("ひこう")
        floating = self.battle.events.emit(
            Event.ON_CHECK_FLOATING,
            BattleContext(source=pokemon),
            floating
        )
        return floating

    def is_trapped(self, pokemon: Pokemon) -> bool:
        """逃げられない状態か判定する。

        Args:
            pokemon: 対象のポケモン

        Returns:
            逃げられない場合True

        Note:
            ゴーストタイプは逃げられる。
        """
        trapped = self.battle.events.emit(
            Event.ON_CHECK_TRAPPED,
            BattleContext(source=pokemon),
            False
        )
        trapped &= not pokemon.has_type("ゴースト")
        return trapped

    def is_nervous(self, pokemon: Pokemon) -> bool:
        """びんじょう状態か判定する。

        Args:
            pokemon: 対象のポケモン

        Returns:
            びんじょう状態の場合True
        """
        return self.battle.events.emit(
            Event.ON_CHECK_NERVOUS,
            BattleContext(source=pokemon),
            False
        )
