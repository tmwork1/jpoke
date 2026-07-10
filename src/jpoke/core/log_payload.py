"""イベントログのペイロード（詳細情報）を定義するモジュール。

LogCode ごとに必要な詳細情報を dataclass として定義する。
どの LogCode がどの Payload を使うかは event_logger.py の
EventLog._get_base_text() を参照。
"""
from dataclasses import dataclass, field

from jpoke.types import Stat, Type, HPChangeReason


@dataclass(frozen=True)
class LogPayload:
    """全ログ共通の基底ペイロード。

    display_reason は render() の「末尾に [reason] を追加する」処理が
    全 LogCode 共通で読む差し込み文言のため、サブクラスごとに重複定義せず
    ここに1つだけ持たせる。使わないカテゴリ（HPChangePayload 等）は
    単に設定しない（常に空文字）。
    """
    display_reason: str = ""  # 表示してよい理由テキスト（特性名・アイテム名など）


@dataclass(frozen=True)
class FailureLogPayload(LogPayload):
    """MOVE_FAILED / MOVE_IMMUNED / ACTION_BLOCKED / HEAL_BLOCKED /
    STAT_CHANGE_BLOCKED / MOVE_MISSED など「技が不発に終わった」ログ全般。
    MOVE_MISSED では display_reason を設定しない運用とする
    （命中判定による不発であり、特性等の「原因」を持たないため）。
    """
    move: str = ""  # 失敗/不発の原因となった技名（選択した技があれば）


@dataclass(frozen=True)
class HPChangePayload(LogPayload):
    """display_reason は使わない（HP変化に「表示してよい理由」は無いため常に空）。
    internal_reason は render() から一切参照しないことで
    [move_damage] のような漏れを構造的に防ぐ。
    対象ポケモン名は EventLog.pokemon（add_event_log の呼び出し元から自動記録）
    で取得するため、ここでは持たない。
    """
    value: int = 0
    hp: int = 0
    max_hp: int = 0
    source: str | None = None             # 攻撃者名（あれば）
    internal_reason: HPChangeReason = ""  # 表示しない内部判定コード


@dataclass(frozen=True)
class StatChangePayload(LogPayload):
    """display_reason は基底のものをそのまま使う（いかく等）。"""
    stats: dict[Stat, int] = field(default_factory=dict)
    source: str | None = None


@dataclass(frozen=True)
class AilmentPayload(LogPayload):
    """AILMENT_APPLIED/REMOVED は display_reason 未使用。
    AILMENT_PREVENTED は特性名を display_reason に入れる。
    """
    ailment: str = ""
    source: str | None = None


@dataclass(frozen=True)
class VolatilePayload(LogPayload):
    """VOLATILE_APPLIED/IMMUNE/DISPLAY は display_reason 未使用。
    VOLATILE_REMOVED・VOLATILE_PREVENTED は display_reason に理由（特性名等）を入れる。
    """
    volatile: str = ""
    source: str | None = None


@dataclass(frozen=True)
class AbilityPayload(LogPayload):
    ability: str = ""


@dataclass(frozen=True)
class ItemPayload(LogPayload):
    item: str = ""


@dataclass(frozen=True)
class FieldPayload(LogPayload):
    field: str = ""
    count: int | None = None


@dataclass(frozen=True)
class MoveActionPayload(LogPayload):
    """PP_CONSUMED（move + value）、SUBSTITUTE_HIT・CRITICAL_HIT・
    MOVE_REFLECTED・PROTECT_SUCCEEDED・PROTECT_FAILED（move のみ、
    value は常に None）が対象。
    """
    move: str = ""
    value: int | None = None


@dataclass(frozen=True)
class TerastalPayload(LogPayload):
    """TERASALLIZED 専用。MEGA_EVOLVED はフィールドが異なる（pokemonのみ、
    かつ render() 未使用）ため統合しない。MEGA_EVOLVED は payload=None のまま。
    """
    type: Type | None = None


@dataclass(frozen=True)
class TextPayload(LogPayload):
    text: str = ""


Payload = (
    LogPayload | FailureLogPayload | HPChangePayload | StatChangePayload
    | AilmentPayload | VolatilePayload | AbilityPayload | ItemPayload
    | FieldPayload | MoveActionPayload | TerastalPayload | TextPayload
)
