"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.model.pokemon import Pokemon
from jpoke.model.volatile import Volatile
from jpoke.types import VolatileName
from jpoke.enums import Event, LogCode
from .context import EventContext
from .log_payload import VolatilePayload
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
              name: VolatileName,
              count: int | None = None,
              source: Pokemon | None = None,
              **kwargs) -> bool:
        """揮発性状態を付与する。

        Args:
            target: 対象のポケモン
            name: 揮発性状態名
            count: 継続ターン数
            source: 揮発性状態の原因となったポケモン
            **kwargs: Volatile クラスの追加引数（例: move_name, hp)
        Returns:
            付与に成功したTrue

        Note:
            - 既に同じ揮発性状態があれば失敗
            - targetが瀕死（HP0）の場合は付与しない。技の追加効果等でダメージにより
              瀕死になった相手には揮発性状態が付与されないため（実機仕様）
        """
        # 瀕死のポケモンには揮発性状態を付与しない
        if target.fainted:
            return False

        # 既に同じ揮発性状態がある場合は失敗
        if target.has_volatile(name):
            return False

        # ON_BEFORE_APPLY_VOLATILE イベントを発火して特性やフィールドによる無効化をチェック
        apply_ctx = EventContext(source=source, target=target)

        # ハンドラーが空値を返した場合は無効化させる
        logs = self.battle.event_logger.logs
        log_count_before = len(logs)
        resolved_name = self._events.emit(Event.ON_BEFORE_APPLY_VOLATILE, apply_ctx, name)
        if not resolved_name:
            # どんかん等、登録ハンドラ自身が理由付きのVOLATILE_PREVENTEDログを
            # 記録して無効化するケースがある。その場合は汎用フォールバックログ
            # （VOLATILE_IMMUNE）を重ねて出さないよう、このemit呼び出し中に
            # 新たにVOLATILE_PREVENTEDログが追加されたかどうかで判定する。
            already_logged = (
                len(logs) > log_count_before
                and logs[-1].log == LogCode.VOLATILE_PREVENTED
            )
            if not already_logged:
                self.battle.add_event_log(
                    target,
                    LogCode.VOLATILE_IMMUNE,
                    payload=VolatilePayload(volatile=name)
                )
            return False

        self.battle.add_event_log(
            target,
            LogCode.VOLATILE_APPLIED,
            payload=VolatilePayload(volatile=resolved_name, source=source.name if source else None)
        )
        target.volatiles[resolved_name] = Volatile(resolved_name, count=count, **kwargs)
        target.volatiles[resolved_name].register_handlers(self._events, target)

        # 付与後フック
        self._events.emit(
            Event.ON_VOLATILE_START,
            EventContext(source=target),
            resolved_name
        )
        return True

    def remove(self, target: Pokemon, name: VolatileName, reason: str = "") -> bool:
        """揮発性状態を解除する。

        Args:
            target: 対象のポケモン
            name: 揮発性状態名
            reason: 解除理由（ログの display_reason に表示する。既定は理由なし）

        Returns:
            解除に成功したTrue

        Note:
            指定された揮発性状態がない場合は失敗する。
        """
        if not target.has_volatile(name):
            return False

        volatile = target.volatiles.pop(name)

        # 終了時ハンドラ（例: ほろびのうた_faint）が modify_hp で致死ダメージを
        # 与えて即座に勝敗を決めてしまうと、VOLATILE_REMOVED ログより先に
        # GAME_WON/GAME_LOST が記録されてしまう。この一連の処理が完了するまで
        # 勝敗ログの記録を遅延させ、順序（HP変化→解除ログ→勝敗ログ）を保つ。
        self.battle.begin_deferred_winner_log()
        try:
            # 終了時ハンドラ内では、現在の保持状態に基づく再計算が行えるよう先に辞書から外す。
            self._events.emit(
                Event.ON_VOLATILE_END,
                EventContext(source=target),
                name
            )

            volatile.unregister_handlers(self._events, target)
            self.battle.add_event_log(
                target,
                LogCode.VOLATILE_REMOVED,
                payload=VolatilePayload(volatile=name, display_reason=reason)
            )
        finally:
            self.battle.end_deferred_winner_log()

        return True

    def remove_all(self, target: Pokemon):
        """対象のポケモンからすべての揮発性状態を解除する。

        Args:
            target: 対象のポケモン
        """
        for volatile_name in list(target.volatiles.keys()):
            self.remove(target, volatile_name)

    def apply_confusion(self,
                        target: Pokemon | None,
                        source: Pokemon | None = None) -> bool:
        """こんらん状態を2〜5ターンのランダム期間で付与する。"""
        if target is None:
            return False
        count = self.battle.random.randint(2, 5)
        return self.apply(target, "こんらん", count=count, source=source)

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
