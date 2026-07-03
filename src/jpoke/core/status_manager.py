# TODO : クラスとして実装する意義があるか検討する。関数モジュールとして実装するほうがシンプルで良いかもしれない。
"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.model import Pokemon
from jpoke.types import Stat, HPChangeReason, StatChangeReason
from jpoke.enums import Event, LogCode
from jpoke.core import EventContext
from jpoke.utils import fast_copy

# TODO : クラスではなく関数モジュールで十分ではないか。


class StatusManager:
    """HPと能力ランクの更新を管理するクラス。

    HPやランクを変更する際に必要なイベント発火・ログ記録・勝敗判定トリガーを一括して担当する。

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

    def modify_hp(self,
                  target: Pokemon,
                  v: int,
                  source: Pokemon | None = None,
                  reason: HPChangeReason = "") -> int:
        """ポケモンのHPを変更する。

        Args:
            target: 対象のポケモン
            v: 変更する固定HP量
            reason: 変更の理由
            source: ダメージ源のポケモン

        Returns:
            実際に変化したHP量（正=回復、負=ダメージ）
        """
        if v == 0:
            return 0

        ctx = EventContext(source=source, target=target, hp_change_reason=reason)

        if reason == "poison":
            # NOTE: ON_MODIFY_POISON_DAMAGE はポイズンヒール特性で毒ダメージを回復に変換するため必須。
            v = self._events.emit(Event.ON_MODIFY_POISON_DAMAGE, ctx, v)
        if v > 0:
            v = self._events.emit(Event.ON_MODIFY_HEAL, ctx, v)
        if v < 0:
            v = self._events.emit(Event.ON_MODIFY_NON_MOVE_DAMAGE, ctx, v)

        v = target.modify_hp(v)

        if v != 0:
            self.battle.add_event_log(
                target, LogCode.HP_CHANGED,
                payload={
                    "pokemon": target.name,
                    "value": v,
                    "hp": target.hp,
                    "max_hp": target.max_hp,
                    "reason": reason,
                },
            )

        if v < 0:
            if target.fainted:
                self.battle.judge_winner()

            self._events.emit(Event.ON_HP_CHANGED, ctx, -v)

        return v

    def modify_stats(self,
                     target: Pokemon,
                     stats: dict[Stat, int],
                     source: Pokemon | None = None,
                     reason: StatChangeReason = "") -> dict[Stat, int]:
        """ポケモンの複数の能力ランクを同時に変更する。

        しろいハーブなどのアイテムが正しく動作するよう、
        複数の能力変化を一度に処理してから ON_MODIFY_RANK を1回発火する。

        Args:
            target: 対象のポケモン
            stats: 能力とランク変化量の辞書（例: {"def": -1, "spd": -1}）
            source: 変更の原因となったポケモン
            reason: 変更の理由（ログ記録用）

        Returns:
            実際に変化した能力とランク量の辞書
        """
        ctx = EventContext(target=target, source=source, stat_change_reason=reason)
        stats = self._events.emit(Event.ON_BEFORE_MODIFY_STAT, ctx, stats)

        actual_changes = {}

        for stat, value in stats.items():
            if value == 0:
                continue

            actual_value = target.modify_stat(stat, value)
            if actual_value == 0:
                continue

            actual_changes[stat] = actual_value

        if actual_changes:
            # うっぷんばらし用: ランクが実際に下がった場合にフラグを立てる
            if any(v < 0 for v in actual_changes.values()):
                target.stat_lowered_this_turn = True
            # みわくのボイス・しっとのほのお用: ランクが実際に上がった場合にフラグを立てる
            if any(v > 0 for v in actual_changes.values()):
                target.stat_raised_this_turn = True
            self.battle.add_event_log(
                target, LogCode.STAT_CHANGED,
                payload={"stats": actual_changes, "reason": reason},
            )
            self._events.emit(Event.ON_MODIFY_STAT, ctx, actual_changes)
        else:
            self.battle.add_event_log(target, LogCode.STAT_CHANGE_BLOCKED)

        return actual_changes
