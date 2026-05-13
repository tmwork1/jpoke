"""バトル中のイベント文脈を扱うモジュール。

ハンドラ実行で参照する source/target、技、ダメージ値などを保持する
`BattleContext` を提供する。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon, Field

from jpoke.enums import Event
from jpoke.model import Move
from jpoke.utils.type_defs import ContextRole, RoleSpec, HPChangeReason, StatChangeReason


class BattleContext:
    """ドメイン/イベント発火時のコンテキスト情報。

    ドメイン/イベントに関連するポケモン、技、場の状態などを保持します。
    ハンドラ実行時に必要な情報を提供します。

    内部的には source/target のみを保持しますが、
    attacker/defender での指定・アクセスも可能です（source/target のエイリアス）。

    Attributes:
        source: イベントの発生源となるポケモン（attacker のエイリアス）
        target: イベントの対象となるポケモン（defender のエイリアス）
        move: 使用された技
        field: 場の状態
        hp_change: HP変動量（負=減少、正=回復）
        hp_change_reason: HP変動の原因（"move_damage", "burn", "poison" など）
        move_damage: 技によるダメージ値（hp_change_reason が "move_damage" かつ hp_change < 0 のときのみ -hp_change、それ以外は 0）
        stat_change_reason: 能力ランク変化の理由（"" は通常、"ミラーアーマー" は反射）
    """

    def __init__(self,
                 source: Pokemon | None = None,
                 target: Pokemon | None = None,
                 attacker: Pokemon | None = None,
                 defender: Pokemon | None = None,
                 move: Move | None = None,
                 hp_change: int = 0,
                 hp_change_reason: HPChangeReason = "",
                 stat_change_reason: StatChangeReason = "",
                 hit_index: int = 1,
                 hit_count: int = 1,
                 critical: bool = False,
                 fainted: bool = False) -> None:
        """BattleContext を初期化する。

        Args:
            source: イベントの発生源となるポケモン
            target: イベントの対象となるポケモン
            attacker: 攻撃側のポケモン（source のエイリアス）
            defender: 防御側のポケモン（target のエイリアス）
            move: 使用された技
            hp_change: HP変動量（負=減少、正=回復）
            hp_change_reason: HP変動の原因
            stat_change_reason: 能力ランク変化の理由
            hit_index: マルチヒット時の現在ヒット番号（1始まり）
            hit_count: マルチヒット時の総ヒット回数

        Note:
            attacker が指定された場合は source に、
            defender が指定された場合は target にマッピングされます。
        """
        # attacker/defender が指定された場合は source/target にマッピング
        self.source = attacker if attacker is not None else source
        self.target = defender if defender is not None else target
        self.move = move
        self.hp_change = hp_change
        self.hp_change_reason: HPChangeReason = hp_change_reason
        self.stat_change_reason: StatChangeReason = stat_change_reason
        self.hit_index = hit_index
        self.hit_count = hit_count

        self.critical: bool = critical  # 急所に当たったかどうかのフラグ
        self.fainted: bool = fainted  # 攻撃によりひんしになったかどうかのフラグ
        self.substitute_damage: int = 0  # みがわりに与えたダメージ（みがわり貫通技用）

    @property
    def move_damage(self) -> int:
        """技によるダメージを返す。

        hp_change_reason が "move_damage" かつ hp_change が負の場合のみダメージを返す。
        それ以外（状態異常ダメージなど）は 0 を返す。
        """
        if self.hp_change_reason == "move_damage" and self.hp_change < 0:
            return -self.hp_change
        else:
            return 0

    @move_damage.setter
    def move_damage(self, value: int):
        # TODO : setterを使わずに def set_move_damage(self, value: int) のように明確にする
        """技によるダメージを設定。

        内部的に hp_change と hp_change_reason を設定する。
        """
        if value > 0:
            self.hp_change = -value
            self.hp_change_reason = "move_damage"
        else:
            self.hp_change = 0

    @property
    def attacker(self) -> Pokemon | None:
        """攻撃側のポケモン（source のエイリアス）。"""
        return self.source

    @attacker.setter
    def attacker(self, value: Pokemon | None):
        self.source = value

    @property
    def defender(self) -> Pokemon | None:
        """防御側のポケモン（target のエイリアス）。"""
        return self.target

    @defender.setter
    def defender(self, value: Pokemon | None):
        self.target = value

    @property
    def is_move_context(self) -> bool:
        """move と attacker/defender が揃った文脈かどうか。"""
        return (
            self.move is not None
            and self.attacker is not None
            and self.defender is not None
        )

    @property
    def is_foe_target(self) -> bool:
        """技が相手を対象にするかどうかを判定する。

        Returns:
            技が相手を対象にする場合True
        """
        return self.source != self.target

    def get_by_role(self, role: ContextRole) -> Pokemon | None:
        """指定されたロールのポケモンを取得する。

        Args:
            role: 取得するロール（"source", "target", "attacker", "defender"）

        Returns:
            Pokemon | None: 該当するポケモン。存在しない場合はNone
        """
        # attacker/defender を source/target にマッピング
        if role == "attacker":
            return self.source
        elif role == "defender":
            return self.target
        return getattr(self, role, None)

    def resolve_role(self,
                     battle: Battle,
                     spec: RoleSpec | None) -> Pokemon | None:
        """ロール指定からポケモンを解決する。
        Args:
            battle: バトルインスタンス
            spec: "role:side"形式のロール指定（例: "source:foe"）

        Returns:
            Pokemon | None: 解決されたポケモン。存在しない場合はNone
        """
        if spec is None:
            return None

        role, side = spec.split(":")
        mon = self.get_by_role(role)
        if mon and side == "foe":
            mon = battle.foe(mon)
        return mon

    def derive(self, **kwargs) -> "BattleContext":
        """このコンテキストを基に新しい BattleContext を派生する。

        source/target/move/field/hit_index/hit_count を引き継ぎ、
        kwargs で指定したフィールドを上書きする。

        Args:
            **kwargs: 上書きするフィールド（source, target, move, field, hp_change,
                      hp_change_reason, stat_change_reason, hit_index, hit_count）

        Returns:
            派生した BattleContext
        """
        return BattleContext(
            source=kwargs.get("source", self.source),
            target=kwargs.get("target", self.target),
            move=kwargs.get("move", self.move),
            hp_change=kwargs.get("hp_change", self.hp_change),
            hp_change_reason=kwargs.get("hp_change_reason", self.hp_change_reason),
            stat_change_reason=kwargs.get("stat_change_reason", self.stat_change_reason),
            hit_index=kwargs.get("hit_index", self.hit_index),
            hit_count=kwargs.get("hit_count", self.hit_count),
            critical=kwargs.get("critical", self.critical),
            fainted=kwargs.get("fainted", self.fainted),
        )

    def can_bypass_screen(self, battle: Battle) -> bool:
        """攻撃側が壁を貫通するかを返す。"""
        return battle.events.emit(Event.ON_QUERY_BYPASS_SCREEN, self, False)
