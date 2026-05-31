"""バトル中のイベント文脈を扱うモジュール。

ハンドラ実行で参照する source/target、技、ダメージ値などを保持する
`EventContext` を提供する。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon, Field

from jpoke.enums import Event
from jpoke.model import Move
from jpoke.utils.type_defs import ContextRole, RoleSpec, HPChangeReason, StatChangeReason


class EventContext:
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
        hp_change_reason: HP変動の原因（"move_damage", "burn", "poison" など）
        stat_change_reason: 能力ランク変化の理由（"" は通常、"ミラーアーマー" は反射）
    """

    def __init__(self,
                 source: Pokemon | None = None,
                 target: Pokemon | None = None,
                 attacker: Pokemon | None = None,
                 defender: Pokemon | None = None,
                 move: Move | None = None,
                 hp_change_reason: HPChangeReason = "",
                 stat_change_reason: StatChangeReason = "",
                 hit_index: int = 1,
                 hit_count: int = 1,
                 critical: bool = False,
                 fainted: bool = False) -> None:
        """EventContext を初期化する。

        Args:
            source: イベントの発生源となるポケモン
            target: イベントの対象となるポケモン
            attacker: 攻撃側のポケモン（source のエイリアス）
            defender: 防御側のポケモン（target のエイリアス）
            move: 使用された技
            hp_change_reason: HP変動の原因
            stat_change_reason: 能力ランク変化の理由
            hit_index: マルチヒット時の現在ヒット番号（1始まり）
            hit_count: マルチヒット時の総ヒット回数
            critical: 急所に当たったかどうかのフラグ
            fainted: 攻撃によりひんしになったかどうかのフラグ
        Note:
            attacker が指定された場合は source に、
            defender が指定された場合は target にマッピングされます。
        """
        # attacker/defender が指定された場合は source/target にマッピング
        self.source = attacker if attacker is not None else source
        self.target = defender if defender is not None else target
        self.move = move
        self.hp_change_reason: HPChangeReason = hp_change_reason
        self.stat_change_reason: StatChangeReason = stat_change_reason
        self.hit_index = hit_index
        self.hit_count = hit_count

        self.critical: bool = critical  # 急所に当たったかどうかのフラグ
        self.fainted: bool = fainted  # 攻撃によりひんしになったかどうかのフラグ
        self.substitute_damage: int = 0  # みがわりに与えたダメージ（みがわり貫通技用）

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

    def is_foe_target(self) -> bool:
        """相手を対象にした処理かどうかを判定する。
        ctx.source と ctx.target が異なるポケモンであれば、相手を対象にする処理とみなす。

        Returns:
            相手を対象にする場合True
        """
        return self.source != self.target

    def resolve_role(self, battle: Battle, spec: RoleSpec) -> Pokemon | None:
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
        mon = getattr(self, role, None)
        if mon is not None and side == "foe":
            mon = battle.foe(mon)
        return mon

    def derive(self, **kwargs) -> "EventContext":
        """このコンテキストを基に新しい EventContext を派生する。

        source/target/move/field/hit_index/hit_count を引き継ぎ、
        kwargs で指定したフィールドを上書きする。

        Args:
            **kwargs: 上書きするフィールド（source, target, move, field,
                      hp_change_reason, stat_change_reason, hit_index, hit_count,
                      critical, move_reflected, fainted）

        Returns:
            派生した EventContext
        """
        return EventContext(
            source=kwargs.get("source", self.source),
            target=kwargs.get("target", self.target),
            move=kwargs.get("move", self.move),
            hp_change_reason=kwargs.get("hp_change_reason", self.hp_change_reason),
            stat_change_reason=kwargs.get("stat_change_reason", self.stat_change_reason),
            hit_index=kwargs.get("hit_index", self.hit_index),
            hit_count=kwargs.get("hit_count", self.hit_count),
            critical=kwargs.get("critical", self.critical),
            fainted=kwargs.get("fainted", self.fainted),
        )

    def can_bypass_screen(self, battle: Battle) -> bool:
        """攻撃側が壁を貫通するかを返す。"""
        return battle.events.emit(Event.ON_CHECK_BYPASS_SCREEN, self, False)
