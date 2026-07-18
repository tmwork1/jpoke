"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.model.pokemon import Pokemon
from jpoke.types import Stat, HPChangeReason, StatChangeReason
from jpoke.enums import Event, LogCode
from .context import EventContext
from jpoke.core.log_payload import HPChangePayload, StatChangePayload, FailureLogPayload
from jpoke.utils import fast_copy


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

        Note:
            瀕死によりGAME_WON/GAME_LOSTログが確定する場合、勝者判定自体
            （`battle.judge_winner()`）はここで即座に行うが、ログの記録
            （`battle.flush_winner_log()`）は `battle.begin_deferred_winner_log()`
            〜 `battle.end_deferred_winner_log()` の抑制区間の内側であれば
            遅延する。技のダメージ処理（move_executor._execute_hit）のように、
            この HP 変化と同一の「1ヒット」に属する後続イベント（ON_HIT・
            ON_DAMAGE_HIT・ON_MOVE_KO 等）が呼び出し元でこの後に控えている
            場合、それらの効果（撃破時特性・自己ランク変化・さめはだ等の
            反撃ダメージなどのログ）が勝敗確定ログより後に記録されてしまう
            不整合を避けるため、呼び出し元がその一連の処理全体を
            `begin_deferred_winner_log()` / `end_deferred_winner_log()` で
            囲む必要がある。
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

        v = target._modify_hp_raw(v)

        if v != 0:
            self.battle.add_event_log(
                target, LogCode.HP_CHANGED,
                payload=HPChangePayload(
                    value=v,
                    hp=target.hp,
                    max_hp=target.max_hp,
                    source=source.name if source else None,
                    internal_reason=reason,
                ),
            )

        if v < 0:
            if target.fainted:
                # 勝者判定自体はここで即座に行う（=どちらが先にひんしになったかで
                # 決まる）。ただしログ記録（GAME_WON/GAME_LOST）は、この HP 変化に
                # 伴う効果（オボンのみ・状態異常付与などの ON_HP_CHANGED ハンドラ）
                # よりも後に行いたいため、下記 flush_winner_log() 側に委ねる。
                # ハンドラ側は battle.winner の値を参照しないため、ログ記録タイミング
                # の変更が既存ハンドラの挙動に影響することはない。
                self.battle.judge_winner()

                # かたきうち用: 味方がひんしになったターンを記録する
                player = self.battle.get_player(target)
                self.battle.player_states[player].ally_fainted_turn = self.battle.turn
                # そうだいしょう用: 自分側がひんしになった延べ回数を加算する
                # （さいきのいのり等で復活しても減らず、再度ひんしになれば加算され続ける）
                self.battle.player_states[player].total_fainted_count += 1

            # ダメおし・きあいパンチ判定用: 反動ダメージ（すてみタックル系・わるあがき系の
            # 確定反動）も「そのターンに攻撃を受けた」扱いにする（一次情報:
            # .internal/wiki/moves/ダメおし.html 技の仕様節）。move_damage は
            # core/move_executor.py 側で別途インクリメントするため、ここでは対象外。
            if reason in ("recoil", "fixed_recoil"):
                target.hits_taken += 1

            self._events.emit(Event.ON_HP_CHANGED, ctx, -v)

            self.battle.flush_winner_log()

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
                payload=StatChangePayload(
                    stats=actual_changes,
                    source=source.name if source else None,
                    display_reason=reason,
                ),
            )
            self._events.emit(Event.ON_MODIFY_STAT, ctx, actual_changes)
        else:
            self.battle.add_event_log(
                target, LogCode.STAT_CHANGE_BLOCKED,
                payload=FailureLogPayload(display_reason=reason),
            )

        return actual_changes
