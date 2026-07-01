# リファクタ計画: EventContext / AttackContext 分離

更新日: 2026-06-05

## スコープ

- 対象: `src/jpoke/core/context.py` およびその利用箇所
- 実装状態: 未着手
- 方針: 共通基底クラス `BaseContext` を新設し、汎用イベント用 `EventContext` と
  攻撃フロー専用 `AttackContext` に分離する。
  `derive` を `BaseContext` のクラスメソッドとして実装し、呼び出し型を保存する。

## 動機

現在の `EventContext` は次の2つの役割を混在させている。

- **汎用イベント文脈**: `source`/`target`、`hp_change_reason`、`stat_change_reason`
- **攻撃フロー専用**: `critical`、`hit_index`/`hit_count`、`fainted`、`substitute_damage`、
  `attacker`/`defender` エイリアス

攻撃と無関係なイベント（ON_SWITCH_IN、ON_TURN_END 等）でも `ctx.critical` が常に
参照でき、意味的に嘘をつくコードが書ける。また現行の `derive` は常に `EventContext`
を返すため、`AttackContext` から派生しても型情報が失われる。

## 実装ゴール（完了定義）

- `BaseContext` が `source`/`target` と共通メソッド・`derive` を持つ
- `EventContext(BaseContext)` は汎用フィールドのみ（攻撃専用フィールドなし）
- `AttackContext(BaseContext)` が攻撃専用フィールドと `attacker`/`defender` プロパティを持つ
- 攻撃フロー（`MoveExecutor`、`DamageCalculator`）で `AttackContext` を生成する
- `AttackContext.derive(ctx)` が `AttackContext` を返す（型保存）
- 全テストが通る

## クラス設計

```
BaseContext
├── source: Pokemon | None
├── target: Pokemon | None
├── hp_change_reason: HPChangeReason
├── stat_change_reason: StatChangeReason
├── resolve_role(battle, spec) → Pokemon | None
├── is_foe_target() → bool
├── can_bypass_screen(battle) → bool
└── derive(cls, ctx, **kwargs) → Self   ← クラスメソッド

EventContext(BaseContext)
└── （追加フィールドなし。汎用イベントはここ）

AttackContext(BaseContext)
├── move: Move | None
├── hit_index: int = 1
├── hit_count: int = 1
├── critical: bool = False
├── fainted: bool = False
├── substitute_damage: int = 0
├── attacker → self.source  （property）
└── defender → self.target  （property）
```

### `move` フィールドの扱い

`move` は `EventContext` でも使われる（ON_MODIFY_PP_CONSUMED、ON_TRY_MOVE_1 等）。
これらのイベントは攻撃フロー前段だが `MoveExecutor.run_move` 内で発火するため、
`AttackContext` を渡して問題ない。攻撃フロー外で `move` が必要なケースは
`EventContext` に `move` フィールドを残す（または `BaseContext` に置く）。

**判断**: `move` は `BaseContext` に置く。これにより `status_manager` の
`EventContext(source, target, move=move, hp_change_reason=...)` の構成を維持できる。

### `derive` のクラスメソッド実装

```python
from typing import Self
import dataclasses

@classmethod
def derive(cls, ctx: "BaseContext", **kwargs) -> Self:
    cls_fields = {f.name for f in dataclasses.fields(cls)}
    base = {
        f.name: getattr(ctx, f.name)
        for f in dataclasses.fields(ctx)
        if f.name in cls_fields
    }
    base.update(kwargs)
    return cls(**base)
```

`@dataclass` 化が前提。`dataclasses.fields(cls)` でそのクラスのフィールド一覧を取り、
`ctx` が持つフィールドとの積集合だけコピーする。これにより：
- `AttackContext.derive(event_ctx)` → 不足フィールドはデフォルト値になる
- `EventContext.derive(attack_ctx)` → 攻撃専用フィールドは自然に落ちる

## 変更対象

### フェーズ1: コアクラスの再設計（最優先）

| ファイル | 変更内容 |
|---|---|
| `src/jpoke/core/context.py` | `BaseContext` 新設、`EventContext` slim 化、`AttackContext` 新設、`@dataclass` 化 |

### フェーズ2: 生成箇所の切り替え（明確な攻撃フロー）

| ファイル | 変更箇所 | 変更後 |
|---|---|---|
| `src/jpoke/core/move_executor.py:231` | `EventContext(attacker=..., defender=...)` | `AttackContext(attacker=..., defender=...)` |
| `src/jpoke/core/damage_calculator.py:93` | `EventContext(attacker=..., critical=...)` | `AttackContext(attacker=..., critical=...)` |

`speed_calculator.py:116,171` の `EventContext(attacker=attacker, move=move)` は
`ON_MODIFY_MOVE_PRIORITY`（行動順決定）用で攻撃ヒット前段。`critical`/`hit_index` が
不要なため `EventContext` のまま `source` に統一する。

### フェーズ3: ハンドラ型アノテーション（段階的・後回し可）

`ctx: EventContext` のアノテーションが `handlers/` に約 650 箇所。
攻撃フローのみで呼ばれるハンドラを `ctx: AttackContext` に変えると型安全になるが、
ランタイム動作には影響しない。フェーズ1・2 完了後に機械的に進める。

`handlers/ability.py`、`handlers/move.py`、`handlers/volatile.py`、
`handlers/item.py`、`handlers/ailment.py`、`handlers/field.py` 等

## 実装ステップ

1. `context.py` を `@dataclass` で再設計し、`BaseContext`・`EventContext`・
   `AttackContext` を定義する。`attacker`/`defender` は `EventContext.__init__` の
   引数から除去し、`AttackContext` の property のみとする。
2. `move_executor.py` の `ctx = EventContext(attacker=..., defender=...)` を
   `AttackContext` に切り替える。
3. `damage_calculator.py` の同様の箇所を切り替える。
4. `speed_calculator.py` の `attacker=` キーワードを `source=` に統一する（`EventContext` のまま）。
5. 全テスト実行で既存動作が壊れていないことを確認する。
6. （任意）フェーズ3: `handlers/` の型アノテーションを段階的に `AttackContext` へ変更する。

## 疑似コード

```python
# context.py（変更後イメージ）
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.model import Move
from jpoke.types import HPChangeReason, StatChangeReason, RoleSpec
import dataclasses


@dataclass
class BaseContext:
    source: Pokemon | None = None
    target: Pokemon | None = None
    move: Move | None = None
    hp_change_reason: HPChangeReason = ""
    stat_change_reason: StatChangeReason = ""

    @classmethod
    def derive(cls, ctx: "BaseContext", **kwargs) -> Self:
        cls_fields = {f.name for f in dataclasses.fields(cls)}
        base = {
            f.name: getattr(ctx, f.name)
            for f in dataclasses.fields(ctx)
            if f.name in cls_fields
        }
        base.update(kwargs)
        return cls(**base)

    def is_foe_target(self) -> bool:
        return self.source != self.target

    def resolve_role(self, battle: Battle, spec: RoleSpec) -> Pokemon | None:
        ...

    def can_bypass_screen(self, battle: Battle) -> bool:
        ...


@dataclass
class EventContext(BaseContext):
    pass  # 汎用イベントはそのまま BaseContext のフィールドで十分


@dataclass
class AttackContext(BaseContext):
    hit_index: int = 1
    hit_count: int = 1
    critical: bool = False
    fainted: bool = False
    substitute_damage: int = 0

    @property
    def attacker(self) -> Pokemon | None:
        return self.source

    @attacker.setter
    def attacker(self, value: Pokemon | None):
        self.source = value

    @property
    def defender(self) -> Pokemon | None:
        return self.target

    @defender.setter
    def defender(self, value: Pokemon | None):
        self.target = value
```

## リスクと対策

- **リスク**: `@dataclass` 化により `__init__` の引数順序が変わる。
  既存の位置引数渡しが壊れる可能性がある。
  - **対策**: 全 `EventContext(...)` 呼び出しがキーワード引数を使っているか確認してから着手する。
    `grep -n "EventContext(" src/` で確認済み（全箇所キーワード引数）。

- **リスク**: `EventContext.__init__` から `attacker=`/`defender=` キーワードがなくなるため、
  既存の `EventContext(attacker=..., defender=...)` 呼び出しがエラーになる。
  - **対策**: フェーズ1 と フェーズ2 を同一コミットで行い、テストを通してから commit する。

- **リスク**: `event_manager.py:163` の `EventContext(**{rh.handler.role: mon})` は
  `role` が `"attacker"` になるケースがある場合に壊れる。
  - **対策**: `rh.handler.role` が取りうる値（`"source"`/`"target"` のみ）を確認してから着手する。

## 検証コマンド

```powershell
python -m pytest tests/ -v
```
