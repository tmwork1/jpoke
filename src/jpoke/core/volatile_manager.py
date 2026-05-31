"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.model import Pokemon, Volatile
from jpoke.utils.type_defs import VolatileName
from jpoke.enums import Event, LogCode
from jpoke.core import EventContext
from jpoke.utils import fast_copy


class VolatileManager:
    """ポケモンの揮発状態を管理するクラス。

    揮発状態の付与、解除、ターン経過処理を担当。
    Pokemonクラスから揮発状態管理を分離し、単一責任原則を実現。

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

    def apply(self,
              target: Pokemon,
              volatile_name: VolatileName,
              count: int | None = None,
              source: Pokemon | None = None,
              ctx: EventContext | None = None,
              **kwargs) -> bool:
        """揮発性状態を付与する。

        Args:
            target: 対象のポケモン
            volatile_name: 揮発性状態名
            count: 継続ターン数
            source: 揮発性状態の原因となったポケモン
            ctx: ON_BEFORE_APPLY_VOLATILE イベントの EventContext
            **kwargs: Volatile クラスの追加引数（例: move_name, hp)
        Returns:
            付与に成功したTrue

        Note:
            - 既に同じ揮発性状態があれば失敗
        """
        # 既に同じ揮発性状態がある場合は失敗
        if target.has_volatile(volatile_name):
            return False

        # ON_BEFORE_APPLY_VOLATILE イベントを発火して特性やフィールドによる無効化をチェック
        if ctx is not None:
            apply_ctx = ctx.derive(target=target, source=source)
        else:
            apply_ctx = EventContext(target=target, source=source)

        # ハンドラーが空値を返した場合は無効化させる
        resolved_name = self._events.emit(Event.ON_BEFORE_APPLY_VOLATILE, apply_ctx, volatile_name)
        if not resolved_name:
            self.battle.add_event_log(
                target,
                LogCode.VOLATILE_IMMUNE,
                payload={"volatile": volatile_name}
            )
            return False

        self.battle.add_event_log(
            target,
            LogCode.VOLATILE_APPLIED,
            payload={"volatile": resolved_name}
        )
        target.volatiles[resolved_name] = Volatile(resolved_name, count=count, **kwargs)
        target.volatiles[resolved_name].register_handlers(self._events, target)

        # 付与後フック
        # TODO : ON_APPLY_VOLATILE では source=mon だが ON_BEFORE_APPLY_VOLATILE では target=mon である点がややこしい。
        hook_ctx = EventContext(source=target)
        self._events.emit(Event.ON_APPLY_VOLATILE, hook_ctx, resolved_name)
        return True

    def remove(self, target: Pokemon, volatile_name: VolatileName) -> bool:
        """揮発性状態を解除する。

        Args:
            target: 対象のポケモン
            volatile_name: 揮発性状態名

        Returns:
            解除に成功したTrue

        Note:
            指定された揮発性状態がない場合は失敗する。
        """
        if not target.has_volatile(volatile_name):
            return False

        volatile = target.volatiles.pop(volatile_name)

        # 終了時ハンドラ内では、現在の保持状態に基づく再計算が行えるよう先に辞書から外す。
        self._events.emit(
            Event.ON_VOLATILE_END,
            EventContext(source=target),
            volatile_name
        )

        volatile.unregister_handlers(self._events, target)
        self.battle.add_event_log(
            target,
            LogCode.VOLATILE_REMOVED,
            payload={"volatile": volatile_name}
        )

        return True

    def remove_all(self, target: Pokemon):
        """対象のポケモンからすべての揮発性状態を解除する。

        Args:
            target: 対象のポケモン
        """
        for volatile_name in list(target.volatiles.keys()):
            self.remove(target, volatile_name)

    def tick(self, target: Pokemon, volatile_name: VolatileName) -> bool:
        """揮発性状態のターン経過処理を行う。

        Args:
            target: 対象のポケモン
            volatile_name: 揮発性状態名

        Returns:
            ターン経過処理を行った場合True、指定された揮発性状態がない場合False
        """
        if not target.has_volatile(volatile_name):
            return False

        volatile = target.volatiles[volatile_name]
        volatile.tick()
        if volatile.count == 0:
            self.remove(target, volatile_name)
        return True
