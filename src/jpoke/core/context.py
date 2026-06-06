"""バトル中のイベント文脈を扱うモジュール。

ハンドラ実行で参照するポケモン、技、ダメージ値などを保持する
BaseContext / EventContext / AttackContext を提供する。
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
import dataclasses

if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.enums import Event
from jpoke.model import Move
from jpoke.utils.type_defs import RoleSpec, HPChangeReason, StatChangeReason


@dataclass(eq=False)
class BaseContext:
    """全イベントコンテキストの基底クラス。技・HP変化理由・ランク変化理由を保持する。"""
    move: Move | None = None
    hp_change_reason: HPChangeReason = ""
    stat_change_reason: StatChangeReason = ""

    def derive(self, **kwargs) -> BaseContext:
        """同型の新しいコンテキストを派生する。kwargs で指定したフィールドを上書きする。"""
        cls = type(self)
        cls_fields = {f.name for f in dataclasses.fields(cls)}
        base = {
            f.name: getattr(self, f.name)
            for f in dataclasses.fields(self)
            if f.name in cls_fields
        }
        base.update(kwargs)
        return cls(**base)

    def is_foe_target(self) -> bool:
        """発動対象が相手側かを返す。サブクラスでオーバーライドする。"""
        return False

    def resolve_role(self, battle: Battle, spec: RoleSpec) -> Pokemon | None:
        """ロール指定からポケモンを解決する。

        Args:
            battle: バトルインスタンス
            spec: "role:side" 形式のロール指定（例: "source:foe"）

        Returns:
            解決されたポケモン。存在しない場合は None
        """
        if spec is None:
            return None
        role, side = spec.split(":")
        mon = getattr(self, role, None)
        if mon is not None and side == "foe":
            mon = battle.foe(mon)
        return mon

    def can_bypass_screen(self, battle: Battle) -> bool:
        """攻撃側が壁を貫通するかを返す。

        コンテキスト種別に依らず source=attacker の EventContext に正規化して発火する。
        """
        attacker = getattr(self, "attacker", None) or getattr(self, "source", None)
        check_ctx = EventContext(source=attacker, move=self.move)
        return battle.events.emit(Event.ON_CHECK_BYPASS_SCREEN, check_ctx, False)


@dataclass(eq=False)
class EventContext(BaseContext):
    """汎用イベントコンテキスト。攻撃フロー以外のイベントで使用する。"""
    source: Pokemon | None = None
    target: Pokemon | None = None

    def is_foe_target(self) -> bool:
        """source と target が異なるポケモンかを返す。"""
        return self.source != self.target


@dataclass(eq=False)
class AttackContext(BaseContext):
    """攻撃フロー専用コンテキスト。ダメージ計算・命中処理で使用する。"""
    attacker: Pokemon | None = None
    defender: Pokemon | None = None
    hit_index: int = 1
    hit_count: int = 1
    critical: bool = False
    fainted: bool = False
    substitute_damage: int = 0

    def is_foe_target(self) -> bool:
        """attacker と defender が異なるポケモンかを返す。"""
        return self.attacker != self.defender

