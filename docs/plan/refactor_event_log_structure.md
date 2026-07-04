# リファクタ計画: EventLog Payload の構造化

更新日: 2026-07-04

## スコープ

- 対象: `src/jpoke/core/event_logger.py`（`Payload` / `EventLog` / `EventLogger`）と
  `battle.add_event_log()` の全呼び出し箇所（`src/jpoke` 内 144 箇所）
- 実装状態: 未着手
- 方針: 単一の緩い `Payload`（`TypedDict(total=False)`）を廃止し、
  **LogCode のカテゴリごとに専用の `dataclass`** に置き換える。
  あわせて「内部判定用の理由コード」と「表示用テキスト」の兼用を解消し、
  攻撃者（`source`）を主要な変化系ログに一貫して記録できるようにする。

## 動機（現状の課題）

### 1. Payload のキーが LogCode をまたいで意味を使い回されている

`Payload`（`event_logger.py:14-35`）は全 LogCode 共通の16キーを持つ辞書で、
「この LogCode にどのキーが必須か」は `EventLog._get_base_text()` の
巨大な `match` 文（同ファイル 83-232行目）を読まないと分からない。
`value` は `HP_CHANGED` では HP 増減量、`PP_CONSUMED` では消費 PP 数、というように
LogCode ごとに異なる意味で再利用されている。

### 2. `reason` が「内部判定コード」と「表示テキスト」を兼任し、実際に事故っている

`reason` の使われ方は LogCode によって二極化している。

- **表示専用**（正しい用法）: `MOVE_FAILED`（コードベース中 74 箇所、最多）は
  ほぼ全て `payload={"reason": "しめりけ"}` のように特性名・アイテム名を
  そのまま人間向けテキストとして渡している（例: `handlers/ability.py:1339-1341`）。
- **内部判定専用のはずが表示に漏れる**（バグ）: `HPChangeReason`
  （`types/literals.py:62-75`）は `"move_damage"` `"poison"` のような
  英語スネークケースの内部分岐用コードだが、`EventLog.render()`
  （`event_logger.py:78-81`）が無条件に `f" [{reason}]"` を付加するため、
  そのまま画面に出てしまう。特に通常攻撃のダメージは必ず
  `move_executor.py:453-455`
  ```python
  actual_damage = -self.battle.modify_hp(
      ctx.defender, -damage, source=ctx.attacker, reason="move_damage"
  )
  ```
  を通り、`status_manager.py:80-89` がこの `reason` をそのまま payload に転記するため、
  **毎回のダメージログに `[move_damage]` という英語が混入する。**

同じキー名 `reason` が LogCode によって「常に表示してよい人間向けテキスト」と
「表示してはいけない内部コード」という非互換な意味を持っており、
型では区別できない。

### 3. 攻撃者（`source`）の情報が握りつぶされている

`modify_hp()` / `modify_stats()`（`status_manager.py:48-97`, `99-148`）は
`source: Pokemon | None` を引数に取り、`move_executor.py:453` では
実際に `source=ctx.attacker` を渡しているが、ログ記録側
（`status_manager.py:80-89` の `HP_CHANGED`、`140-143` の `STAT_CHANGED`）は
`source` を一切 payload に含めていない。
**現状のログからは「誰が誰に何をしたか」を再構築できない**
（対象ポケモンと数値変化しか残らない）。

### 4. `stats` だけネスト構造で他フィールドと形が異なる

`STAT_CHANGED` の `stats: dict[Stat, int]`（例: `{"def": -1, "spd": -1}`）は
フラットな他フィールドと構造が異なり、辞書のネストが1段増える。

### 5. 構造化APIが定義されているが未使用

`EventLog.to_dict()`（`event_logger.py:56-62`）は `vars(self).copy()` を返すだけで
`LogCode` enum を含んだままのため JSON 化できない。
`Battle.get_event_logs()`（`battle.py:620-632`）を含め、両者ともソース全体で
呼び出し元がゼロ。唯一の消費経路は `Battle.print_logs()` → `render()` → `print()`
というテキスト化のみで、構造化データとして解析・検証されたことがない。

## 呼び出し箇所の分布（現状把握）

`add_event_log(` 呼び出し: 144箇所（`grep -rn "add_event_log(" src/jpoke` で確認）

| ファイル | 件数 |
|---|---|
| `handlers/move_status.py` | 51 |
| `handlers/ability.py` | 20 |
| `handlers/move_attack.py` | 19 |
| `handlers/volatile.py` | 18 |
| `core/move_executor.py` | 7 |
| `core/turn_controller.py` | 5 |
| `handlers/field.py` | 3 |
| `handlers/ailment.py` | 3 |
| `core/volatile_manager.py` | 3 |
| `core/status_manager.py` | 3 |
| `handlers/item.py` | 2 |
| `core/switch_manager.py` | 2 |
| `core/item_manager.py` | 2 |
| `core/field_manager.py` | 2 |
| `core/ailment_manager.py` | 2 |
| `handlers/move.py` | 1 |
| `core/battle.py` | 1 |

LogCode 別の使用頻度（上位）: `MOVE_FAILED` 74、`MOVE_IMMUNED` 15、
`ACTION_BLOCKED` 13、`STAT_CHANGED` 5、他は概ね1〜4件ずつ。
**`MOVE_FAILED`/`ACTION_BLOCKED`/`TEXT_LOG` の3種で全体の6割超**を占め、
これらは `reason`/`text` のみを使う単純な構造なので移行コストが低い。
一方 `HP_CHANGED`/`STAT_CHANGED` は件数こそ少ないが、
上記の課題（`source` 欠落・`reason` 漏れ）の実害が集中している。

## クラス設計

### 粒度の検証（144箇所の実データとの照合）

初版の設計をカテゴリ別に並べただけで確定させず、実際の呼び出し箇所と
突き合わせた結果、以下のズレが見つかった。

1. **`AilmentPayload`/`VolatilePayload` に理由フィールドが欠けていた**
   `AILMENT_PREVENTED`（`handlers/ability.py:284-285`、
   `payload={"ailment": value, "reason": ctx.target.ability.name}`）、
   `VOLATILE_PREVENTED`（`handlers/ability.py:307-308`）、
   `VOLATILE_REMOVED`（`handlers/volatile.py:75-78`）は
   いずれも「対象名」と「理由（特性名）」の**2フィールド**を渡しており、
   `ailment`/`volatile` 単体の設計では表現できない。
2. **`reason` サフィックスは元々1つの共通機構だった**
   `render()`（`event_logger.py:78-80`）の
   `if reason := payload.get("reason"): text += f" [{reason}]"` は
   `FailureLogPayload` 系専用ではなく、`STAT_CHANGED`・`AILMENT_PREVENTED`・
   `VOLATILE_PREVENTED`・`VOLATILE_REMOVED` を含む**全 LogCode 共通**の
   仕組みだった。したがって `display_reason` をサブクラスごとに重複定義するのではなく
   **基底クラス `LogPayload` に1つだけ持たせ、`HPChangePayload` だけが
   これを使わず別名 `internal_reason` を持つ**、という設計にした方が
   現行の実装意図（「reasonがあれば一律で付与」）に忠実で、フィールド数も減る。
3. **`MEGA_EVOLVED` を `TerastalPayload` と同グループにする根拠がなかった**
   `TERASALLIZED` は `{"type": mon.tera_type}` を使うが、
   `MEGA_EVOLVED`（`turn_controller.py:227-229`）は `{"pokemon": mon.name}` を渡す。
   ところが `render()` はどの LogCode でも `payload.get("pokemon")` を
   参照しておらず（唯一の消費者は `SWITCHED_IN`/`SWITCHED_OUT`、
   `event_logger.py:103,107`）、この `pokemon` は表示に使われない死んだ値。
   シングルバトル前提では `idx` だけで行動主体が一意に決まるため、
   `MEGA_EVOLVED` は **専用フィールドを持たない**（`payload=None`）に変更する。
   `TerastalPayload` とは分離する。
4. **`SUBSTITUTE_HIT` がフェーズ2の分類から漏れていた**
   `handlers/volatile.py:1102`（`payload={"move": ctx.move.name}`）は
   `PP_CONSUMED` と同じ「技名＋任意の数値」構造のため `MoveActionPayload`
   （`value` は未使用のため `None` のまま）に統合する。
5. **payload を一切持たない LogCode 7種のうち、4種は構造化の観点で情報が欠落している**
   `CRITICAL_HIT`・`MOVE_REFLECTED`・`PROTECT_SUCCEEDED`・`PROTECT_FAILED`は
   いずれも `payload=None` で呼ばれているが、呼び出し元
   （`move_executor.py:383`（`MOVE_REFLECTED`）, `move_executor.py:445`（`CRITICAL_HIT`）,
   `handlers/volatile.py:985,988`（`PROTECT_FAILED`/`PROTECT_SUCCEEDED`、
   `_run_protect` 内で `ctx.attacker`/`ctx.defender` を直接使っており
   実体は `AttackContext`）はすべて `ctx.move` を保持している。
   「どの技で急所に当たったか」「どの技が反射/防がれたか」は
   ログ単体から追えず、前後のログ（`PP_CONSUMED`/`MOVE_FAILED`等）の並び順で
   推測するしかない。外部JSON消費（フェーズ3）では並び順への依存は避けたいため、
   この4種は `MoveActionPayload(move=ctx.move.name)` を持たせる（各1箇所、計4箇所）。
   一方 `GAME_STARTED`・`GAME_WON`・`GAME_LOST`・`MEGA_EVOLVED`
   （4種）は本当に付随情報を持たないため `payload=None` のまま変更しない。
6. **`pokemon` 自動補完ロジックは実質デッドコードだった**
   `battle.add_event_log()` の `isinstance(source, Pokemon)` による
   `pokemon` 自動注入（`battle.py:614-617`）は、読まれるのが
   `SWITCHED_IN`/`SWITCHED_OUT` のみであり、かつその2箇所
   （`switch_manager.py:231,255`）は既に明示的に `pokemon=mon.name` を
   渡しているため、**注入が実際に意味を持つ呼び出しは存在しない**。
   フェーズ1でこのロジックごと削除し、`pokemon` フィールドは
   `SwitchPayload` にのみ残す。

### 設計（確定版）

```python
# event_logger.py

@dataclass(frozen=True)
class LogPayload:
    """全ログ共通の基底ペイロード。

    display_reason は現行 render() の「末尾に [reason] を追加する」処理
    （event_logger.py:78-80）が全 LogCode 共通で読む差し込み文言のため、
    サブクラスごとに重複定義せずここに1つだけ持たせる。
    使わないカテゴリ（HPChangePayload 等）は単に設定しない（常に空文字）。
    """
    display_reason: str = ""  # 表示してよい理由テキスト（特性名・アイテム名など）


@dataclass(frozen=True)
class FailureLogPayload(LogPayload):
    """MOVE_FAILED / MOVE_IMMUNED / ACTION_BLOCKED / HEAL_BLOCKED /
    STAT_CHANGE_BLOCKED / MOVE_MISSED など「技が不発に終わった」ログ全般。
    MOVE_MISSED は当初 MoveMissPayload として分離する設計だったが、
    フィールドが `move` のみで完全に一致するため統合した。
    MOVE_MISSED では display_reason を設定しない運用とする
    （命中判定による不発であり、特性等の「原因」を持たないため）。"""
    move: str = ""  # 失敗/不発の原因となった技名（選択した技があれば）


@dataclass(frozen=True)
class HPChangePayload(LogPayload):
    """display_reason は使わない（HP変化に「表示してよい理由」は無いため常に空）。
    internal_reason は render() から一切参照しないことで
    [move_damage] のような漏れを構造的に防ぐ。"""
    pokemon: str = ""
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
    AILMENT_PREVENTED（handlers/ability.py:284-285）は特性名を
    display_reason に入れる。"""
    ailment: str = ""
    source: str | None = None


@dataclass(frozen=True)
class VolatilePayload(LogPayload):
    """VOLATILE_APPLIED/IMMUNE/DISPLAY は display_reason 未使用。
    VOLATILE_REMOVED（handlers/volatile.py:75-78）・
    VOLATILE_PREVENTED（handlers/ability.py:307-308）は
    display_reason に理由（特性名等）を入れる。"""
    volatile: str = ""
    source: str | None = None


@dataclass(frozen=True)
class AbilityPayload(LogPayload):
    ability: str = ""


@dataclass(frozen=True)
class ItemPayload(LogPayload):
    item: str = ""


@dataclass(frozen=True)
class SwitchPayload(LogPayload):
    """render() が pokemon を実際に読む唯一のカテゴリ
    （event_logger.py:103,107）。pokemon 自動補完はここだけに残す。"""
    pokemon: str = ""


@dataclass(frozen=True)
class FieldPayload(LogPayload):
    field: str = ""
    count: int | None = None


@dataclass(frozen=True)
class MoveActionPayload(LogPayload):
    """PP_CONSUMED（move + value）、SUBSTITUTE_HIT・CRITICAL_HIT・
    MOVE_REFLECTED・PROTECT_SUCCEEDED・PROTECT_FAILED（move のみ、
    value は常に None）が対象。"""
    move: str = ""
    value: int | None = None


@dataclass(frozen=True)
class TerastalPayload(LogPayload):
    """TERASALLIZED 専用。MEGA_EVOLVED はフィールドが異なる（pokemonのみ、
    かつ render() 未使用）ため統合しない。MEGA_EVOLVED は payload=None のまま。"""
    type: Type | None = None


@dataclass(frozen=True)
class TextPayload(LogPayload):
    text: str = ""


Payload = (
    LogPayload | FailureLogPayload | HPChangePayload | StatChangePayload
    | AilmentPayload | VolatilePayload | AbilityPayload | ItemPayload
    | SwitchPayload | FieldPayload | MoveActionPayload | TerastalPayload
    | TextPayload
)
```

要点:

- `reason` というキー名は **廃止**し、用途別に分割する。
  - 「常に表示してよい理由テキスト」→ **基底クラス `LogPayload.display_reason`**
    に1本化する（`FailureLogPayload`・`StatChangePayload`・`AilmentPayload`・
    `VolatilePayload` はこれを継承してそのまま使う。サブクラスごとの重複定義はしない）。
  - 「表示してはいけない内部判定コード」→ `HPChangePayload.internal_reason`
    のように `internal_` 接頭辞をつけ、`render()` からは参照しない。
  - この分割により `[move_damage]` のような漏れは **構造的に発生しなくなる**
    （internal_reason を render() が読まないため）。
- `FailureLogPayload` には `move`（失敗の原因となった技名）を追加する。
  現状の呼び出し元は `reason` のみを渡しており技名を渡していないため、
  各呼び出し箇所で `ctx.move.name`（`AttackContext`）等から技名を補う必要がある
  （フェーズ2は純粋な機械的置換ではなく、この分だけ手動確認が要る）。
- `MOVE_MISSED`（技が外れた）は当初 `FailureLogPayload` から独立した
  `MoveMissPayload` を設ける設計だったが、フィールドが `move` のみで
  `FailureLogPayload` と完全に一致していたため、判定 dispatch が
  `self.log`（LogCode）で行われクラス自体は分岐に使われないことも踏まえ、
  `FailureLogPayload` に統合した。意図の違い（「原因」を持たない）は
  「`display_reason` を設定しない」という運用ルールで表現する。
- `SUBSTITUTE_HIT`・`CRITICAL_HIT`・`MOVE_REFLECTED`・`PROTECT_SUCCEEDED`・
  `PROTECT_FAILED` は `MoveActionPayload` に統合する（`value` は使わない）。
  後者4種は現状 `payload=None` だが、呼び出し元は `ctx.move` を保持しており
  技名を記録しないと前後のログ順から推測するしかなくなるため、
  `move=ctx.move.name` を新規に追加する。
- `MEGA_EVOLVED`・`GAME_STARTED`・`GAME_WON`・`GAME_LOST` の4種は
  本当に付随情報を持たないため、専用 dataclass を持たず `payload=None` のまま据え置く。
- `source`（攻撃者名）を `HPChangePayload` / `StatChangePayload` /
  `AilmentPayload` / `VolatilePayload` に追加する。
  呼び出し元（`move_executor.py` 等）は既に `source=` を持っているため、
  ログ記録箇所（`status_manager.py` 等）で転記するだけでよい。
- 各 dataclass は **そのログが実際に使うフィールドしか持たない**ため、
  キーのタイポやコピペミスをコンストラクタ呼び出し時に型チェックで検出できる
  （現状の `payload={"pokemon": ...}` のような辞書リテラルは
  キー名が文字列なので mypy が検出できない）。
- `EventLog.render()` の `match` 文は `payload.get("x")` ではなく
  `cast(HPChangePayload, payload).value` のような属性アクセスに変える
  （どの LogCode がどの Payload 型を使うかは `_get_base_text()` 内の
  対応関係がそのまま契約になる）。`display_reason` のサフィックス付与は
  基底クラスの属性を見るだけの共通処理として残せる。
- `EventLog.to_dict()` を `LogCode` を `.name`（文字列）に変換し、
  `payload` を `dataclasses.asdict()` するよう修正し、真に
  JSON-serializable にする。

## 変更対象（フェーズ別）

### フェーズ1: 基盤クラスの再設計（最優先・低リスク）

| ファイル | 変更内容 |
|---|---|
| `src/jpoke/core/event_logger.py` | 上記の `LogPayload` 系 dataclass 群を新設。`EventLog.payload` の型を `Payload | None` に変更。`render()`/`_get_base_text()` を属性アクセスに書き換え。`to_dict()` をJSON化可能にする |
| `src/jpoke/core/battle.py:599-618` | `add_event_log()` の型注釈を新しい `Payload` に更新。`isinstance(source, Pokemon)` で `pokemon` を補完する処理（614-617行目）は**削除**する（読まれるのは `SWITCHED_IN`/`OUT` のみで、その2箇所は既に明示的に `pokemon` を渡しており実質デッドコードと判明したため） |

この段階では呼び出し元はまだ辞書リテラルのままで動かなくなるため、
フェーズ2と同一コミットで進める（`refactor_context_split.md` の教訓を踏襲）。

### フェーズ2: 呼び出し箇所の書き換え（機械的だが件数が多い）

呼び出しパターンは「`payload={"key": value, ...}`」を
「`XxxPayload(key=value, ...)`」に変えるだけの機械的な置換が大半。
影響件数が多い順に対応する。

| グループ | 対象ファイル | 対応する Payload | 件数目安 |
|---|---|---|---|
| 技失敗・行動不能系 | `handlers/move_status.py`, `handlers/ability.py`, `handlers/move_attack.py`, `handlers/volatile.py` 他（`MOVE_FAILED`/`MOVE_IMMUNED`/`ACTION_BLOCKED`/`HEAL_BLOCKED`/`STAT_CHANGE_BLOCKED`） | `FailureLogPayload` | 約108（74+15+13+他）。`move` は呼び出し箇所ごとに `ctx.move.name` 等から補う |
| 技外れ | `core/move_executor.py:414`, `handlers/volatile.py:111` | `FailureLogPayload`（`display_reason`は設定しない） | 2（現状 payload なし。技名を新規に追加） |
| HP変化 | `core/status_manager.py`, `core/move_executor.py`, `handlers/ailment.py`, `handlers/field.py` 等 `modify_hp` 呼び出し元経由 | `HPChangePayload` | ログ記録自体は `status_manager.py` 1箇所（呼び出し元の `modify_hp()` 引数は変更不要） |
| 能力ランク変化 | `core/status_manager.py` | `StatChangePayload` | 1箇所（`modify_stats()` 内） |
| 状態異常 | `core/ailment_manager.py`, `handlers/ability.py:284-285` | `AilmentPayload` | 数箇所。`AILMENT_PREVENTED` は `display_reason` に特性名を入れる |
| 揮発性状態 | `core/volatile_manager.py`, `handlers/volatile.py:75-78`, `handlers/ability.py:307-308` | `VolatilePayload` | 数箇所。`VOLATILE_REMOVED`/`VOLATILE_PREVENTED` は `display_reason` に理由を入れる |
| 特性・アイテム発動/得喪 | `handlers/ability.py`, `handlers/item.py`, `core/item_manager.py` | `AbilityPayload` / `ItemPayload` | 数箇所 |
| 交代 | `core/switch_manager.py` | `SwitchPayload` | 2箇所 |
| 場の状態 | `core/field_manager.py`, `handlers/field.py` | `FieldPayload` | 数箇所 |
| 技名タグ付けログ | `core/move_executor.py:552`（PP_CONSUMED）, `handlers/volatile.py:1102`（SUBSTITUTE_HIT）, `move_executor.py:383`（MOVE_REFLECTED）, `move_executor.py:445`（CRITICAL_HIT）, `handlers/volatile.py:985,988`（PROTECT_FAILED/SUCCEEDED） | `MoveActionPayload` | 6箇所。うち4箇所（反射/急所/まもる成功・失敗）は現状 payload なしで、`ctx.move.name` を新規に追加する |
| テラスタル | `core/turn_controller.py:201-203` | `TerastalPayload` | 1箇所 |
| 汎用テキスト | 各所 `TEXT_LOG` | `TextPayload` | 4箇所 |
| ペイロードなし | `turn_controller.py`（`MEGA_EVOLVED:227-229`は`pokemon`指定を削除, `GAME_STARTED/WON/LOST`） | なし（`payload=None`） | 4種。変更不要（`MEGA_EVOLVED`のみ不要な`pokemon`指定を削除） |

`FailureLogPayload` 系（約110箇所）は基本的に
`payload={"reason": x}` → `payload=FailureLogPayload(display_reason=x)`
という機械的な置換で済む（キーワード名は `reason` → `display_reason` に
一括変換）。ただし `move` は現状渡されていない値のため、
技が関わる失敗（`MOVE_FAILED`/`MOVE_IMMUNED` 等）については
呼び出し箇所ごとに技名を取得できるか個別確認が必要で、この部分のみ
一括置換の対象外とする。

### フェーズ3: 外部消費対応

| ファイル | 変更内容 |
|---|---|
| `src/jpoke/core/battle.py` | `export_logs_json()`（仮称）を新設し、`get_event_logs()` の結果を `EventLog.to_dict()` でシリアライズしてターン単位のJSONを返せるようにする |
| `docs/spec/` | 必要であれば `event_log.md` を追加し、LogCode ごとの Payload 対応表を仕様として残す（実装方針そのものはこのファイルに残さない） |

## 実装ステップ

1. `event_logger.py` に `LogPayload` 系 dataclass 群を定義し、
   `EventLog.render()`/`_get_base_text()` を属性アクセスに書き換える。
   `to_dict()` をJSON-serializableにする。
2. `battle.add_event_log()` の型注釈を更新し、`pokemon` 自動補完ロジック
   （`battle.py:614-617`）を削除する。
3. `status_manager.py` の `modify_hp()`/`modify_stats()` 内のログ記録を
   `HPChangePayload`/`StatChangePayload` に切り替え、`source` を転記する
   （このコミットで課題3「攻撃者情報の欠落」を解消）。
4. `FailureLogPayload` を使う約108箇所（`MOVE_FAILED`/`MOVE_IMMUNED`/
   `ACTION_BLOCKED`/`HEAL_BLOCKED`/`STAT_CHANGE_BLOCKED`）を
   ファイル単位で置換する。`display_reason` への置き換え自体は機械的だが、
   `move` は呼び出し箇所ごとに技名を取得できるか確認しながら追加する。
5. `MOVE_MISSED` の2箇所（`move_executor.py:414`, `handlers/volatile.py:111`）を
   `FailureLogPayload(move=...)` に置換する（現状 payload なしのため技名を新規追加。
   `display_reason` は設定しない）。
6. 残りのカテゴリ（状態異常・揮発性状態・特性・アイテム・交代・場・
   技名タグ付け・テラスタル・汎用テキスト）を順に置換する。
   `AILMENT_PREVENTED`/`VOLATILE_PREVENTED`/`VOLATILE_REMOVED` は
   `display_reason` に理由を入れる。`SUBSTITUTE_HIT`/`CRITICAL_HIT`/
   `MOVE_REFLECTED`/`PROTECT_SUCCEEDED`/`PROTECT_FAILED` は
   `MoveActionPayload` に統合し、後者4種は `ctx.move.name` を新規に追加する。
   `MEGA_EVOLVED`（`turn_controller.py:227-229`）は
   不要な `pokemon` 指定を外して `payload=None` にする。
7. 全テスト実行で既存動作が壊れていないことを確認する。
8. （フェーズ3・任意）`export_logs_json()` を追加し、簡単な利用例を
   1つ用意する。

## リスクと対策

- **リスク**: 144箇所という件数の多さから、書き換え漏れ・キー名の
  スペルミスが発生しやすい。
  - **対策**: `Payload` を `frozen dataclass` にすることで、
    未対応キーワードを渡すと `TypeError` になり実行時にも検出できる。
    フェーズ2はカテゴリ単位でコミットを分け、都度 `pytest` を通す。

- **リスク**: `reason` を `internal_reason`/`display_reason` に
  分割することで、既存コードが `payload.get("reason")` のように
  暗黙的に読んでいる箇所（もしあれば）が壊れる。
  - **対策**: `grep -rn 'payload.get(\"reason\")\|payload\[.reason.\]'` で
    `render()` 以外に `reason` を直接参照している箇所がないか事前に確認する。
    また接頭辞なしの `reason` という名前は用途が判別しづらいため採用せず、
    表示用は必ず `display_reason`、非表示用は必ず `internal_reason` に統一する
    （クラス設計で反映済み）。

- **リスク**: `HP_CHANGED`/`STAT_CHANGED` に `source` を追加する際、
  `source is None` のケース（天候ダメージ・状態異常ダメージなど
  攻撃者が存在しない変化）の扱いを統一する必要がある。
  - **対策**: `source: str | None = None` とし、`render()` は
    `source` があるときだけ追加情報を出す設計にする（必須にしない）。

## 検証コマンド

```powershell
python -m pytest tests/ -v
```
