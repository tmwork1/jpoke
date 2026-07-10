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
from jpoke.types import RoleSpec, HPChangeReason, StatChangeReason


@dataclass(eq=False)
class BaseContext:
    """全イベントコンテキストの基底クラス。HP変化理由・ランク変化理由を保持する。"""
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
        if role not in ("source", "target", "attacker", "defender"):
            raise ValueError(f"不正なロール指定: {spec}")
        # コンテキスト型に存在しないロール（例: EventContext に 'attacker'）は
        # None を返し、呼び出し側でハンドラをスキップさせる
        mon = getattr(self, role, None)
        if mon is not None and side == "foe":
            mon = battle.foe(mon)
        return mon


@dataclass(eq=False)
class EventContext(BaseContext):
    """汎用イベントコンテキスト。攻撃フロー以外のイベントで使用する。"""
    source: Pokemon | None = None
    target: Pokemon | None = None
    dry_run: bool = False
    """実際にアイテムを変更せず判定のみ行う呼び出しかどうか（例: はたきおとすの威力判定）。
    ねんちゃく等、実際の除去は防ぐが判定のみの呼び出しでは発動（発表）しない特性の分岐に使う。
    """
    ignore_sticky_hold: bool = False
    """ねんちゃくによる奪取阻止を無視するかどうか（例: むしくい・ついばむが対象をひんしにさせた場合）。
    第五世代以降の仕様で、ねんちゃく以外のアイテム変更禁止効果には影響しない。
    """
    is_exchange: bool = False
    """トリック・すりかえ等、相手の道具と入れ替わる形の道具変更判定かどうか。
    ARシステム/マルチタイプ等、相手が特定の道具を持っている場合も交換自体が
    失敗する特性の判定に使う（はたきおとす等の一方的な除去では立てない）。
    """

    def is_foe_target(self) -> bool:
        """source と target が異なるポケモンかを返す。"""
        return self.source != self.target

    def can_bypass_status_guard(self, battle: Battle) -> bool:
        """発動元がしんぴのまもり・しろいきり等の耐性を貫通するかを返す。"""
        return battle.events.emit(Event.ON_CHECK_BYPASS_STATUS_GUARD, self, False)


@dataclass(eq=False, kw_only=True)
class AttackContext(BaseContext):
    """攻撃フロー専用コンテキスト。ダメージ計算・命中処理で使用する。"""
    attacker: Pokemon
    defender: Pokemon | None = None
    move: Move
    hit_index: int = 1
    hit_count: int = 1
    critical: bool = False
    fainted: bool = False
    substitute_damage: int = 0

    def is_foe_target(self) -> bool:
        """attacker と defender が異なるポケモンかを返す。"""
        return self.attacker != self.defender

    def can_bypass_screen(self, battle: Battle) -> bool:
        """攻撃側がリフレクター・ひかりのかべ等の壁を貫通するかを返す。"""
        return battle.events.emit(Event.ON_CHECK_BYPASS_SCREEN, self, False)
