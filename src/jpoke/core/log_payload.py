"""イベントログのペイロード（詳細情報）を定義するモジュール。

LogCode ごとに必要な詳細情報を dataclass として定義する。

## プログラムでログを解析する場合の入口

`EventLog.render()`（event_logger.py）が返す文字列は LogCode ごとに文体・
省略ルールが異なる **人間向け表示専用のテキスト** であり、機械的なパース対象
ではない。プログラムでログを解析・検証したい場合は代わりに以下を使う。

- `EventLog.log`（LogCode enum）で種別を判定する
- `EventLog.pokemon`（イベントの主体となったポケモン名。add_event_log() の
  呼び出し元が Pokemon インスタンスを渡した場合のみ設定される）
- `EventLog.payload`（下表の Payload dataclass。属性に直接アクセスする）
- `EventLog.to_dict()`（上記を JSON-serializable な dict に変換したもの）

## LogCode → Payload 対応表

`payload=None` の行は詳細情報を持たない（LogCode 自体が情報のすべて）。
`source` は「行為の原因となったポケモン名」（例: いかくを発動した相手）を指し、
`EventLog.pokemon`（イベントの対象/主体）とは役割が異なる。

| LogCode | Payload | 主なフィールドの意味 |
|---|---|---|
| GAME_STARTED / GAME_WON / GAME_LOST | None | — |
| SWITCHED_IN / SWITCHED_OUT | None | 交代したポケモン名は `EventLog.pokemon` |
| ACTION_BLOCKED / MOVE_FAILED / MOVE_MISSED / HEAL_BLOCKED / STAT_CHANGE_BLOCKED | `FailureLogPayload` | `move`=不発の原因となった技名。MOVE_MISSED は `display_reason` 未設定 |
| MOVE_IMMUNED | `FailureLogPayload` | `move`=無効化された技名 |
| PP_CONSUMED | `MoveActionPayload` | `move`=技名, `value`=消費PP量 |
| MOVE_REFLECTED / SUBSTITUTE_HIT / PROTECT_SUCCEEDED / PROTECT_FAILED / CRITICAL_HIT | `MoveActionPayload` | `move`=関係する技名。`value` は常に None |
| MOVE_REVEALED | `MoveRevealPayload` | `target`=技を公開された相手のポケモン名, `move`=公開された技名（よちむ等） |
| HP_CHANGED | `HPChangePayload` | `value`=増減量（符号付き）, `hp`/`max_hp`=変化後, `source`=攻撃者名, `internal_reason`=内部判定コード（表示しない）。対象ポケモン名は `EventLog.pokemon` |
| STAT_CHANGED | `StatChangePayload` | `stats`=`{Stat: 増減段階}`, `source`=原因となったポケモン名。対象ポケモン名は `EventLog.pokemon` |
| ABILITY_TRIGGERED | `AbilityPayload` | `ability`=発動した特性名。発動したポケモン名は `EventLog.pokemon` |
| ABILITY_EFFECT_ENDED | `AbilityPayload` | `ability`=効果が終了した特性名, `message`=終了時の固有台詞（末尾の「！」は含まない）。対象ポケモン名は `EventLog.pokemon` |
| ITEM_TRIGGERED / ITEM_GAINED / ITEM_LOST | `ItemPayload` | `item`=対象アイテム名。対象ポケモン名は `EventLog.pokemon` |
| ITEM_REVEALED | `ItemRevealPayload` | `target`=持ち物を公開された相手のポケモン名, `item`=公開されたアイテム名（おみとおし等） |
| AILMENT_APPLIED / AILMENT_REMOVED / AILMENT_PREVENTED | `AilmentPayload` | `ailment`=状態異常名, `source`=原因ポケモン名（あれば）。PREVENTEDは`display_reason`に理由 |
| VOLATILE_IMMUNE / VOLATILE_APPLIED / VOLATILE_DISPLAY | `VolatilePayload` | `volatile`=揮発状態名, `source`=原因ポケモン名（あれば） |
| VOLATILE_REMOVED / VOLATILE_PREVENTED | `VolatilePayload` | `volatile`=揮発状態名, `source`=原因ポケモン名（あれば）, `display_reason`=理由 |
| FIELD_STARTED / FIELD_ENDED | `FieldPayload` | `field`=場の状態名, `count`=残りターン数（あれば） |
| FIELD_STACKED | `FieldPayload` | `field`=場の状態名, `count`=増加後の層数（まきびし・どくびし等） |
| TERASALLIZED | `TerastalPayload` | `type`=テラスタイプ |
| MEGA_EVOLVED | None | メガシンカしたポケモン名は `EventLog.pokemon` |

対応関係の実体は `EventLog._get_base_text()`（event_logger.py）の `match` 文。
この docstring は解析用リファレンスであり、実装が変わった場合は両方を
同時に更新する。
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
    AILMENT_PREVENTED は無効化理由（特性名または「タイプ無効」）を display_reason に入れる。
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
    """ABILITY_TRIGGERED は message 未使用。
    ABILITY_EFFECT_ENDED は message に終了時の固有台詞（末尾の「！」は含まない）を入れる。
    """
    ability: str = ""
    message: str = ""


@dataclass(frozen=True)
class ItemPayload(LogPayload):
    item: str = ""


@dataclass(frozen=True)
class ItemRevealPayload(LogPayload):
    """ITEM_REVEALED 専用（おみとおし等、相手の持ち物を公開する効果）。
    行動主体（公開した側）は EventLog.pokemon、target は公開された側。
    """
    target: str = ""  # 持ち物を公開された相手のポケモン名
    item: str = ""    # 公開されたアイテム名


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
class MoveRevealPayload(LogPayload):
    """MOVE_REVEALED 専用（よちむ等、相手の技を公開する効果）。
    行動主体（公開した側）は EventLog.pokemon、target は公開された側。
    """
    target: str = ""  # 技を公開された相手のポケモン名
    move: str = ""    # 公開された技名


@dataclass(frozen=True)
class TerastalPayload(LogPayload):
    """TERASALLIZED 専用。MEGA_EVOLVED はフィールドが異なる（pokemonのみ、
    かつ render() 未使用）ため統合しない。MEGA_EVOLVED は payload=None のまま。
    """
    type: Type | None = None


Payload = (
    LogPayload | FailureLogPayload | HPChangePayload | StatChangePayload
    | AilmentPayload | VolatilePayload | AbilityPayload | ItemPayload
    | ItemRevealPayload | FieldPayload | MoveActionPayload | MoveRevealPayload
    | TerastalPayload
)
