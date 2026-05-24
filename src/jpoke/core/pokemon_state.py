# TODO : Managerクラスごとにモジュールをわける

"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.model import Pokemon, Move, Ailment, Volatile
from jpoke.utils.type_defs import AilmentName, VolatileName, Stat, HPChangeReason, StatChangeReason
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

    @property
    def events(self) -> EventManager:
        """Battleのイベントマネージャーへのショートカットプロパティ。"""
        return self.battle.events

    @staticmethod
    def can_apply_by_type(ailment: AilmentName,
                          target: Pokemon,
                          source: Pokemon | None) -> bool:
        """タイプによって状態異常を付与できるか判定する。"""
        match ailment:
            case "どく" | "もうどく":
                if not (target.has_type("どく") or target.has_type("はがね")):
                    return True
                return (
                    source is not None
                    and source.ability.name == "ふしょく"
                )

            case "やけど":
                return not target.has_type("ほのお")

            case "まひ":
                return not target.has_type("でんき")

            case "こおり":
                return not target.has_type("こおり")

        return True

    def apply(self,
              target: Pokemon,
              name: AilmentName,
              count: int | None = None,
              source: Pokemon | None = None,
              force: bool = False,
              ctx: BattleContext | None = None) -> bool:
        """状態異常を付与する。

        Args:
            target: 対象のポケモン
            name: 状態異常名
            count: 継続ターン数（必要な状態異常のみ）
            source: 状態異常の原因となったポケモン
            force: Trueの場合、既存の状態異常を上書き
            ctx: ON_BEFORE_APPLY_AILMENT イベントの BattleContext
        Returns:
            付与に成功したTrue

        Note:
            - force=Falseの場合、既に状態異常があれば失敗
            - 同じ状態異常の重ね掛けは不可
        """
        # force=True でない限り上書き不可
        if target.ailment.is_active and not force:
            return False

        # 重ねがけ不可
        if name == target.ailment.name:
            return False

        # タイプによる無効化をチェック
        if not self.can_apply_by_type(name, target, source):
            return False

        # ON_BEFORE_APPLY_AILMENT イベントを発火して特性などによる無効化をチェック
        # ハンドラーがvalueを空文字列に変更した場合は状態異常を防ぐ
        if ctx is not None:
            new_ctx = ctx.derive(target=target, source=source)
        else:
            new_ctx = BattleContext(target=target, source=source)

        if not self.events.emit(Event.ON_BEFORE_APPLY_AILMENT, new_ctx, name):
            return False

        # 既存のハンドラを削除
        target.ailment.unregister_handlers(self.events, target)

        # 新しい状態異常を設定してハンドラ登録
        self.battle.add_event_log(target, LogCode.AILMENT_APPLIED,
                                  payload={"ailment": name})
        target.ailment = Ailment(name, count=count)
        target.ailment.register_handlers(self.events, target)
        return True

    def remove(self, target: Pokemon, source: Pokemon | None = None) -> bool:
        """状態異常を解除する。

        Args:
            target: 対象のポケモン
            source: 解除の原因となったポケモン

        Returns:
            解除に成功したらTrue
        """
        if not target.ailment.is_active:
            return False

        self.battle.add_event_log(target, LogCode.AILMENT_REMOVED,
                                  payload={"ailment": target.ailment.name})
        target.ailment.unregister_handlers(self.events, target)
        target.ailment = Ailment()
        return True

    def tick(self, target: Pokemon) -> bool:
        """状態異常のターン経過処理を行う。

        Args:
            target: 対象のポケモン

        Returns:
            ターン経過処理を行った場合True、状態異常がない場合False
        """
        if not target.ailment.is_active:
            return False
        target.ailment.tick()
        if target.ailment.count == 0:
            self.remove(target)
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

    @property
    def events(self) -> EventManager:
        """Battleのイベントマネージャーへのショートカットプロパティ。"""
        return self.battle.events

    def apply(self,
              target: Pokemon,
              name: VolatileName,
              count: int | None = None,
              source: Pokemon | None = None,
              ctx: BattleContext | None = None,
              **kwargs) -> bool:
        """揮発性状態を付与する。

        Args:
            target: 対象のポケモン
            name: 揮発性状態名
            count: 継続ターン数
            source: 揮発性状態の原因となったポケモン
            ctx: ON_BEFORE_APPLY_VOLATILE イベントの BattleContext
            **kwargs: Volatile クラスの追加引数（例: move_name, hp)
        Returns:
            付与に成功したTrue

        Note:
            - 既に同じ揮発性状態があれば失敗
        """
        # 既に同じ揮発性状態がある場合は失敗
        if target.has_volatile(name):
            return False

        # ON_BEFORE_APPLY_VOLATILE イベントを発火して特性やフィールドによる無効化をチェック
        # ハンドラーがvalueを空文字列に変更した場合は揮発状態を防ぐ
        if ctx is not None:
            new_ctx = ctx.derive(target=target, source=source)
        else:
            new_ctx = BattleContext(target=target, source=source)

        orig_volatile = name
        name = self.events.emit(Event.ON_BEFORE_APPLY_VOLATILE, new_ctx, name)
        if not name:
            self.battle.add_event_log(target, LogCode.VOLATILE_IMMUNE,
                                      payload={"volatile": orig_volatile})
            return False

        self.battle.add_event_log(target, LogCode.VOLATILE_APPLIED,
                                  payload={"volatile": name})
        target.volatiles[name] = Volatile(name, count=count, **kwargs)
        target.volatiles[name].register_handlers(self.events, target)

        # 付与後フック
        # TODO : ON_APPLY_VOLATILE では source=mon だが ON_BEFORE_APPLY_VOLATILE では target=mon である点がややこしい。イベント名を変えるなど対策を考える。
        ctx = BattleContext(source=target)
        self.events.emit(Event.ON_APPLY_VOLATILE, ctx, name)
        return True

    def remove(self, target: Pokemon, name: VolatileName) -> bool:
        """揮発性状態を解除する。

        Args:
            target: 対象のポケモン
            name: 揮発性状態名

        Returns:
            解除に成功したTrue

        Note:
            指定された揮発性状態がない場合は失敗する。
        """
        # count=0 の失効直後も辞書には残っているため、存在判定は辞書キーで行う。
        if not target.has_volatile(name):
            return False

        volatile = target.volatiles.pop(name)

        # 終了時ハンドラ内では、現在の保持状態に基づく再計算が行えるよう先に辞書から外す。
        ctx = BattleContext(source=target)
        self.events.emit(Event.ON_VOLATILE_END, ctx, name)

        volatile.unregister_handlers(self.events, target)
        self.battle.add_event_log(target, LogCode.VOLATILE_REMOVED,
                                  payload={"volatile": name})

        return True

    def tick(self, target: Pokemon, name: VolatileName) -> bool:
        """揮発性状態のターン経過処理を行う。

        Args:
            target: 対象のポケモン
            name: 揮発性状態名

        Returns:
            ターン経過処理を行った場合True、指定された揮発性状態がない場合False
        """
        if not target.has_volatile(name):
            return False

        volatile = target.volatiles[name]
        volatile.tick()
        if volatile.count == 0:
            self.remove(target, name)
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

    @property
    def events(self) -> EventManager:
        """Battleのイベントマネージャーへのショートカットプロパティ。"""
        return self.battle.events

    def is_floating(self, pokemon: Pokemon) -> bool:
        """浮いている状態か判定する。

        Args:
            pokemon: 対象のポケモン

        Returns:
            浮いていればTrue

        Note:
            タイプや特性、技の効果を考慮して判定する。
        """
        return self.events.emit(
            Event.ON_CHECK_FLOATING,
            BattleContext(source=pokemon),
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
        trapped = self.events.emit(
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
        return self.events.emit(
            Event.ON_CHECK_NERVOUS,
            BattleContext(source=pokemon),
            False
        )

    def get_forced_move_name(self, pokemon: Pokemon) -> str | None:
        """強制行動中のポケモンが実行すべき技名を返す。"""
        for volatile in pokemon.volatiles.values():
            if volatile.data.forced:
                return volatile.move_name


class StatusManager:
    """HPと能力ランクの更新を管理するクラス。

    HPやランクを変更する際に必要なイベント発火・ログ記録・勝敗判定トリガーを一括して担当する。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        """StatusManagerを初期化。

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

    @property
    def events(self) -> EventManager:
        """Battleのイベントマネージャーへのショートカットプロパティ。"""
        return self.battle.events

    def modify_hp(self,
                  target: Pokemon,
                  v: int = 0,
                  r: float = 0,
                  reason: HPChangeReason = "",
                  source: Pokemon | None = None,
                  move: Move | None = None) -> int:
        """ポケモンのHPを変更する。

        Args:
            target: 対象のポケモン
            v: 変更する固定HP量
            r: 最大HPに対する割合（0.0～1.0）。v と同時指定時は r が優先される
            reason: 変更の理由
            source: ダメージ源のポケモン（技によるひんし時に ON_FAINTED へ渡す）
            move: 使用された技（技によるひんし時に ON_FAINTED へ渡す）

        Returns:
            実際に変化したHP量（正=回復、負=ダメージ）
        """
        if v == 0 and r == 0:
            return 0

        if r:
            v = int(target.max_hp * r)

        ctx = BattleContext(source=source, target=target, move=move, hp_change_reason=reason)

        if reason == "poison":
            # NOTE: ON_MODIFY_POISON_DAMAGE はポイズンヒール特性で毒ダメージを回復に変換するため必須。
            v = self.events.emit(Event.ON_MODIFY_POISON_DAMAGE, ctx, v)
        if v > 0:
            v = self.events.emit(Event.ON_MODIFY_HEAL, ctx, v)
        if v < 0:
            v = self.events.emit(Event.ON_MODIFY_NON_MOVE_DAMAGE, ctx, v)

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
                self.events.emit(Event.ON_FAINTED, ctx, -v)
            else:
                self.events.emit(Event.ON_HP_CHANGED, ctx, -v)

        return v

    def modify_stat(self,
                    target: Pokemon,
                    stat: Stat,
                    v: int,
                    source: Pokemon | None = None,
                    reason: StatChangeReason = "") -> dict[Stat, int]:
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
                     reason: StatChangeReason = "") -> dict[Stat, int]:
        """ポケモンの複数の能力ランクを同時に変更する。

        しろいハーブなどのアイテムが正しく動作するよう、
        複数の能力変化を一度に処理してから ON_MODIFY_RANK を1回発火する。

        Args:
            target: 対象のポケモン
            stats: 能力とランク変化量の辞書（例: {"B": -1, "D": -1}）
            source: 変更の原因となったポケモン
            reason: 変更の理由（ログ記録用）

        Returns:
            実際に変化した能力とランク量の辞書
        """
        ctx = BattleContext(target=target, source=source, stat_change_reason=reason)
        stats = self.events.emit(Event.ON_BEFORE_MODIFY_STAT, ctx, stats)

        actual_changes = {}

        for stat, value in stats.items():
            if value == 0:
                continue

            actual_value = target.modify_stat(stat, value)
            if actual_value == 0:
                continue

            actual_changes[stat] = actual_value

        if actual_changes:
            self.battle.add_event_log(
                target, LogCode.STAT_CHANGED,
                payload={"stats": actual_changes, "reason": reason},
            )
            self.events.emit(Event.ON_MODIFY_STAT, ctx, actual_changes)
        else:
            self.battle.add_event_log(target, LogCode.STAT_CHANGE_BLOCKED)

        return actual_changes
