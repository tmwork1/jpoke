"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.model import Pokemon, Move, Ailment, Volatile
from jpoke.utils.type_defs import AilmentName, VolatileName, Stat, HPChangeReason
from jpoke.enums import Event, LogCode
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

    @staticmethod
    def _is_blocked_by_poison_type_immunity(mon: Pokemon,
                                            source: Pokemon | None,
                                            name: AilmentName) -> bool:
        if name not in ("どく", "もうどく"):
            return False
        if not (mon.has_type("どく") or mon.has_type("はがね")):
            return False
        return not (
            source is not None
            and source.ability.name == "ふしょく"
            and source.ability.enabled
        )

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

        # 毒/猛毒は、原則として毒・鋼タイプには無効。
        if self._is_blocked_by_poison_type_immunity(mon, source, name):
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

    def apply(self,
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

        # 付与後フック
        self.battle.events.emit(
            Event.ON_APPLY_VOLATILE,
            BattleContext(source=mon),
            name,
        )
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
        # count=0 の失効直後も辞書には残っているため、存在判定は辞書キーで行う。
        if not mon.has_volatile(name):
            return False

        # 揮発状態の終了時イベントを発火する。
        self.battle.events.emit(
            Event.ON_VOLATILE_END,
            BattleContext(source=mon),
            name,
        )

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


class PokemonQuery:
    """ポケモン個体に関する読み取り専用クエリをまとめたクラス。

    状態を変更せず、イベントを通じて現在の判定結果を返す。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        """PokemonQueryを初期化。

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
        """きんちょうかん状態か判定する。

        Args:
            pokemon: 対象のポケモン

        Returns:
            きんちょうかん状態の場合True
        """
        return self.battle.events.emit(
            Event.ON_CHECK_NERVOUS,
            BattleContext(source=pokemon),
            False
        )

    def get_forced_move_name(self, pokemon: Pokemon) -> str | None:
        """強制行動中のポケモンが実行すべき技名を返す。"""
        for volatile in pokemon.volatiles.values():
            if volatile.data.forced:
                return volatile.move_name
        return None


class StatusManager:
    """HPと能力ランクの更新を管理するクラス。

    HPやランクを変更する際に必要なイベント発火・ログ記録・勝敗判定トリガーを一括して担当する。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: "Battle"):
        """StatusManagerを初期化。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def update_reference(self, battle: "Battle"):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    def modify_hp(self, target: Pokemon, v: int = 0, r: float = 0, reason: HPChangeReason = "other") -> int:
        """ポケモンのHPを変更する。

        Args:
            target: 対象のポケモン
            v: 変更する固定HP量
            r: 最大HPに対する割合（0.0～1.0）。v と同時指定時は r が優先される
            reason: 変更の理由

        Returns:
            実際に変化したHP量（正=回復、負=ダメージ）
        """
        if v == 0 and r == 0:
            return 0

        hp_before = target.hp

        if r:
            v = int(target.max_hp * r)

        if v > 0:
            v = self.battle.events.emit(
                Event.ON_BEFORE_HEAL,
                BattleContext(target=target),
                v
            )

        v = target.modify_hp(v)
        hp_after = target.hp

        if v > 0:
            self.battle.add_event_log(target, LogCode.HEAL,
                                      payload={"value": v, "reason": reason})
        elif v < 0:
            self.battle.add_event_log(target, LogCode.DAMAGE,
                                      payload={"value": -v, "reason": reason})
            self.battle.events.emit(
                Event.ON_HP_CHANGED,
                BattleContext(
                    target=target,
                    hp_change=hp_before - hp_after,
                    hp_change_reason=reason,
                ),
            )
            if target.fainted:
                self.battle.judge_winner()

        return v

    def modify_stat(self,
                    target: Pokemon,
                    stat: Stat,
                    v: int,
                    source: Pokemon | None = None,
                    reason: str = "") -> dict[Stat, int]:
        """ポケモンの能力ランクを1つ変更する。

        内部的には modify_stats() を呼び出して処理する。

        Args:
            target: 対象のポケモン
            stat: 変更する能力値（"A", "B", "C", "D", "S" 等）
            v: 変更するランク数（正=上昇、負=下降）
            source: 変更の原因となったポケモン
            reason: 変更の理由（ログ記録用）

        Returns:
            実際に変化した能力とランク量の辞書
        """
        return self.modify_stats(target, {stat: v}, source, reason)

    def modify_stats(self,
                     target: Pokemon,
                     stats: dict[Stat, int],
                     source: Pokemon | None = None,
                     reason: str = "") -> dict[Stat, int]:
        """ポケモンの複数の能力ランクを同時に変更する。

        しろいハーブなどのアイテムが正しく動作するよう、
        複数の能力変化を一度に処理してから ON_MODIFY_STAT を1回発火する。

        Args:
            target: 対象のポケモン
            stats: 能力とランク変化量の辞書（例: {"B": -1, "D": -1}）
            source: 変更の原因となったポケモン
            reason: 変更の理由（ログ記録用）

        Returns:
            実際に変化した能力とランク量の辞書
        """
        stats = self.battle.events.emit(
            Event.ON_BEFORE_MODIFY_STAT,
            BattleContext(target=target, source=source),
            stats
        )

        any_success = False
        actual_changes = {}

        for stat_key, stat_value in stats.items():
            if stat_value == 0:
                continue
            actual_value = target.modify_stat(stat_key, stat_value)
            if actual_value != 0:
                self.battle.add_event_log(
                    target,
                    LogCode.MODIFY_STAT,
                    payload={"stat": stat_key, "value": actual_value, "reason": reason},
                )
                actual_changes[stat_key] = actual_value
                any_success = True

        if any_success:
            self.battle.events.emit(
                Event.ON_MODIFY_STAT,
                BattleContext(target=target, source=source),
                actual_changes
            )

        return actual_changes
