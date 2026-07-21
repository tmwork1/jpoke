"""バトル中のイベント文脈を扱うモジュール。

ハンドラ実行で参照するポケモン、技、ダメージ値などを保持する
BaseContext / EventContext / AttackContext を提供する。
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypeVar
import dataclasses

if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.enums import Event
from jpoke.model.move import Move
from jpoke.types import RoleSpec, HPChangeReason, StatChangeReason, ItemName

_ContextT = TypeVar("_ContextT", bound="BaseContext")


@dataclass(eq=False)
class BaseContext:
    """全イベントコンテキストの基底クラス。HP変化理由・ランク変化理由を保持する。"""
    hp_change_reason: HPChangeReason = ""
    stat_change_reason: StatChangeReason = ""

    def derive(self: _ContextT, **kwargs) -> _ContextT:
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
            解決されたポケモン。ロールに対応するポケモンが存在しない場合（例:
            AttackContext.defender が None）、または side="foe" でロール側の
            ポケモンが場に出ていない場合（例: さいきのいのりで復活する瀕死の
            控えポケモンに対する ON_MODIFY_HEAL）は None。後者は「相手」という
            関係自体が定義できない（＝どのハンドラの所有者とも一致し得ない）
            ことを表し、該当するハンドラが単に不適用になる。

        Raises:
            ValueError: role がこのコンテキスト型に定義されていない場合（例:
                EventContext に対して "attacker:self" を指定した場合）。
                subject_spec と登録先イベントのコンテキスト型が食い違う
                実装ミスを、サイレントなハンドラ無効化ではなく即座に検出するため。
                各イベントは単一のコンテキスト型からのみ発火する前提（1イベント
                = 1コンテキスト型）。複数のコンテキスト型から発火しうる効果
                （例: ON_CALC_DRAIN、技由来/揮発状態由来のHP吸収）は、emit側で
                EventContext に正規化してから発火することでこの前提を保つ。
        """
        if spec is None:
            return None
        role, side = spec.split(":")
        if role not in ("source", "target", "attacker", "defender"):
            raise ValueError(f"不正なロール指定: {spec}")
        if not hasattr(self, role):
            raise ValueError(
                f"{type(self).__name__} は role '{role}' を持たない"
                f"（subject_spec='{spec}'）。ハンドラの subject_spec と"
                "登録先イベントのコンテキスト型が一致しているか確認してください。"
            )
        mon = getattr(self, role)
        if mon is not None and side == "foe":
            if mon not in battle.actives:
                return None
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
    item_name: ItemName = ""
    """Event.ON_BERRY_CONSUMED で消費されたきのみ名を伝える（はんすう・ほおぶくろ用）。"""
    is_self_fling: bool = False
    """Event.ON_BERRY_CONSUMED専用: なげつけるの使用者が自分の持ち物のきのみを投げて
    手放したことによる消費の場合True。はんすうはこの経路でも消費として扱うが、
    ほおぶくろは「きのみを食べる」ことが発動条件のため、この経路では発動しない
    （一次情報: ほおぶくろの一次情報 特性の仕様節「なげつける/ギフトパスで自分のきのみを
    手放したとき」）。
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
    defender_hp_before_move: int = 0
    """技開始時点（ON_BEGIN_MOVE）の防御側HP。とびだすなかみ等、多段技の最初のヒット前HPを
    基準とする効果で使用する。"""
    secondary_effect_target: Literal["attacker", "defender"] = "defender"
    """Event.ON_MODIFY_SECONDARY_CHANCE で判定する追加効果の対象ロール。
    "defender"（既定）は相手（防御側）に対する追加効果、"attacker" は自分自身に対する
    追加効果（例: コメットパンチの自分のこうげき上昇）を表す。りんぷん・おんみつマント
    （'defender:self' で登録）は "attacker" のときは反応しない（一次情報どおり、使用者
    自身の能力変化はりんぷん・おんみつマントで防げないため）。ちからずく・てんのめぐみ
    （'attacker:self' で登録）はこの値に関わらず常に反応する。
    battle.resolve_secondary_chance() 経由でのみ設定される。"""
    blocked_by_protect: bool = False
    """まもる・ワイドガード等のprotect系揮発状態によって技がブロックされたかどうか。
    `handlers/volatile.py` の `_run_protect` がブロック成立時に True を設定する。
    Event.ON_TRY_MOVE_1 はしめりけ（HPコスト支払い前に失敗すべき）と同じイベントで
    発火するが、だいばくはつ等の自爆技はまもる等でブロックされても使用者は必ず
    ひんしになる必要がある（`.internal/spec/moves/だいばくはつ.md`）。この違いを
    区別するため、move_executor はこのフラグを見て、まもるブロックの場合のみ
    ON_TRY_MOVE_1失敗後もEvent.ON_PAY_HPを発火させる。"""
    missed_hidden_target: bool = False
    """そらをとぶ・あなをほる等で姿を隠している相手に対して、対応していない技で
    命中させられず外れたかどうか。`handlers/volatile.py` の `can_hit_hidden_target`
    が回避成立時に True を設定する。このケースは通常の命中率判定による「外れ」と
    同様に扱う必要があり（.internal/spec/moves/とびひざげり.md「姿を隠している
    相手（そらをとぶ等）に使用して外れた場合も、通常の『外れ』と同様に反動ダメージを
    受ける」）、Event.ON_TRY_MOVE_1 失敗時にこのフラグを見て move_executor が
    通常のミス処理（Event.ON_MISS発火等）を行う。"""

    def is_foe_target(self) -> bool:
        """attacker と defender が異なるポケモンかを返す。"""
        return self.attacker != self.defender

    def can_bypass_screen(self, battle: Battle) -> bool:
        """攻撃側がリフレクター・ひかりのかべ等の壁を貫通するかを返す。"""
        return battle.events.emit(Event.ON_CHECK_BYPASS_SCREEN, self, False)
