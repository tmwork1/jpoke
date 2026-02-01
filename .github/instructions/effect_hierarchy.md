# 作用のヒエラルキーと実装原則

## 概要

ポケモン対戦では、複数の作用が相互に影響しあいます。例えば：
- 特性「ひでり」が天候を「はれ」にする
- アイテム「あついいわ」により、はれ「ターンが伸びる」
- 「はれ」状態では「ほのお技の威力が1.5倍になる」
- 「はれ」状態ではソーラービームの「溜めがなくなる」
- 「はれ」状態では特性ようりょくそにより「すばやさが2倍になる」

このような場合、**どの作用をどこに実装すべきか**を明確にする必要があります。

---

## 基本原則

### 1. **効果の所有者原則（Ownership Principle）**

**効果は、それを「所有する」エンティティに実装する**

```
誰が/何が その効果を持っているのか？
    ↓
そのエンティティのデータに実装する
```

#### 例

| 効果 | 所有者 | 実装場所 |
|-----|-------|---------|
| 天候を「はれ」にする | 特性「ひでり」 | `data/ability.py` の「ひでり」 |
| はれターンを延長する | アイテム「あついいわ」 | `data/item.py` の「あついいわ」 |
| ほのお技の威力1.5倍 | 天候「はれ」 | `data/field.py` の「はれ」 |
| ソーラービームの溜めなし | 技「ソーラービーム」 | `data/move.py` の「ソーラービーム」 |
| 晴れ時に素早さ2倍 | 特性「ようりょくそ」 | `data/ability.py` の「ようりょくそ」 |

---

### 2. **単一責任の原則（Single Responsibility Principle）**

**各エンティティは、自分の責任範囲のみを実装する**

#### ✅ 良い例

```python
# data/field.py - 天候「はれ」
"はれ": FieldData(
    handlers={
        # 「はれ」の責任: 技威力に影響を与える
        Event.ON_CALC_POWER_MODIFIER: Handler(
            h.はれ_power_modifier,
            ...
        ),
    }
)

# data/ability.py - 特性「ひでり」
"ひでり": AbilityData(
    handlers={
        # 「ひでり」の責任: 天候を変更する
        Event.ON_SWITCH_IN: AbilityHandler(
            partial(common.activate_weather, weather="はれ", ...),
            ...
        )
    }
)
```

#### ❌ 悪い例

```python
# data/ability.py - 特性「ひでり」
"ひでり": AbilityData(
    handlers={
        # ✗ 天候変更までは良いが...
        Event.ON_SWITCH_IN: AbilityHandler(...),
        
        # ✗ ほのお技の威力補正は「はれ」の責任
        # 特性に実装すべきではない
        Event.ON_CALC_POWER_MODIFIER: AbilityHandler(
            lambda ...: value * 1.5,  # ← ダメ
        )
    }
)
```

---

### 3. **イベント駆動の原則（Event-Driven Principle）**

**相互作用はイベントを通じて実現する**

```
特性「ひでり」発動
    ↓ activate_weather() を呼ぶ
天候が「はれ」になる
    ↓ FieldManager が天候ハンドラを登録
技「ソーラービーム」が使われる
    ↓ ON_BEFORE_MOVE イベント発火
技「ソーラービーム」のハンドラが実行される
    ↓ 天候を確認して溜めターンをスキップ
```

エンティティ間は**直接的に依存しない**。イベントを介して間接的に作用します。

---

## 作用のヒエラルキー

### レイヤー1: **状態変更**（State Modification）

天候・地形・場の状態・揮発性状態などを**変更する**作用

| 作用の種類 | 実装場所 | 例 |
|-----------|---------|---|
| 天候変更 | 技データ | にほんばれ、あまごい、すなあらし |
| 天候変更 | 特性データ | ひでり、あめふらし、すなおこし、ゆきふらし |
| 天候変更 | アイテムデータ | （第9世代では該当なし） |
| 地形変更 | 技データ | エレキフィールド、グラスフィールド |
| 地形変更 | 特性データ | エレキメイカー、グラスメイカー |
| 揮発性状態付与 | 技データ | みがわり、アンコール、ちょうはつ |
| 揮発性状態付与 | 特性データ | （例: へんしょく で状態変化） |

**実装方法**: `common.activate_weather()`, `common.activate_terrain()` などのヘルパー関数を使用

```python
# 技「にほんばれ」
"にほんばれ": MoveData(
    handlers={
        Event.ON_HIT: MoveHandler(
            partial(common.activate_weather, weather="はれ", source_spec="attacker:self"),
            subject_spec="attacker:self",
        )
    }
)

# 特性「ひでり」
"ひでり": AbilityData(
    handlers={
        Event.ON_SWITCH_IN: AbilityHandler(
            partial(common.activate_weather, weather="はれ", source_spec="source:self", count=999),
            subject_spec="source:self",
        )
    }
)
```

---

### レイヤー2: **状態の効果**（State Effects）

天候・地形・場の状態が**他の要素に与える影響**

| 効果の種類 | 実装場所 | 例 |
|-----------|---------|---|
| 技威力補正 | 天候データ（`data/field.py`） | はれ→ほのお技1.5倍 |
| 命中率補正 | 天候データ | はれ→かみなり50% |
| ダメージ付与 | 天候データ | すなあらし→非いわ/じめん/はがねに1/16ダメージ |
| ステータス補正 | 天候データ | すなあらし→いわタイプ特防1.5倍 |
| 状態異常無効 | 地形データ | エレキフィールド→ねむり無効 |
| 技無効化 | 地形データ | サイコフィールド→先制技無効 |

**実装方法**: 天候・地形データの `handlers` に実装

```python
# data/field.py
"はれ": FieldData(
    handlers={
        # 天候「はれ」の効果
        Event.ON_CALC_POWER_MODIFIER: Handler(
            h.はれ_power_modifier,  # ほのお技1.5倍、みず技0.5倍
            subject_spec="source:self",
            log="never",
        ),
        Event.ON_CALC_ACCURACY: Handler(
            h.はれ_accuracy,  # かみなり・ぼうふう50%
            subject_spec="source:self",
            log="never",
        ),
    }
)
```

---

### レイヤー3: **状態への反応**（Reaction to State）

特性・アイテムなどが**天候・地形の存在に反応する**作用

| 反応の種類 | 実装場所 | 例 |
|-----------|---------|---|
| 天候依存の能力強化 | 特性データ | ようりょくそ（晴れ時素早さ2倍）、すなかき（砂嵐時素早さ2倍） |
| 天候依存のダメージ無効 | 特性データ | すながくれ、すなのちから（砂嵐ダメージ無効） |
| 天候依存の回復 | 特性データ、アイテムデータ | あめうけざら（雨時回復） |
| 地形依存の能力強化 | 特性データ | サーフテール（エレキフィールド時素早さ2倍） |
| 天候依存の技変化 | 技データ | ソーラービーム（晴れ時溜めなし） |

**実装方法**: 特性・アイテムデータの `handlers` に実装

```python
# data/ability.py
"ようりょくそ": AbilityData(
    handlers={
        Event.ON_CALC_SPEED: AbilityHandler(
            h.ようりょくそ,  # 晴れ時に素早さ2倍
            subject_spec="source:self",
            log="never",
        )
    }
)

# handlers/ability.py
def ようりょくそ(battle: Battle, ctx: EventContext, value: Any):
    # 天候が「はれ」かどうかを確認
    if battle.weather == "はれ":
        return HandlerReturn(True, value * 2)
    return HandlerReturn(False, value)
```

---

## 実装時の判断フロー

```
┌─────────────────────────────────────┐
│ この効果は何をするのか？              │
└─────────────────────────────────────┘
              ↓
    ┌─────────┴─────────┐
    │                   │
 状態を変更         状態の効果
    │                   │
    ↓                   ↓
┌─────────┐      ┌─────────┐
│ 誰が発動？│      │ 何の状態？│
└─────────┘      └─────────┘
    │                   │
    ↓                   ↓
技データ            天候データ
特性データ          地形データ
アイテムデータ      グローバルフィールドデータ
                    サイドフィールドデータ
```

### 例: 「ほのお技の威力が1.5倍になる」

1. **何をするのか？** → 技威力を変更（状態の効果）
2. **何の状態？** → 天候「はれ」
3. **実装場所** → `data/field.py` の「はれ」

### 例: "晴れ時に素早さが2倍になる"

1. **何をするのか？** → 素早さを変更（状態への反応）
2. **誰が持っている能力？** → 特性「ようりょくそ」
3. **実装場所** → `data/ability.py` の「ようりょくそ"

---

## 複雑なケース

### ケース1: 特性が複数の効果を持つ

**特性「あついしぼう」**: ほのお・こおり技のダメージを半減

```python
# data/ability.py
"あついしぼう": AbilityData(
    handlers={
        Event.ON_CALC_POWER_MODIFIER: AbilityHandler(
            h.あついしぼう,
            subject_spec="target:self",
            log="never",
        )
    }
)

# handlers/ability.py
def あついしぼう(battle: Battle, ctx: EventContext, value: Any):
    if ctx.move.type in ["ほのお", "こおり"]:
        return HandlerReturn(True, value * 0.5)
    return HandlerReturn(False, value)
```

**理由**: ダメージ軽減は「あついしぼう」が所有する効果なので、特性データに実装

---

### ケース2: アイテムが天候を延長

**アイテム「あついいわ」**: 晴れ状態を3ターン延長（5→8ターン）

```python
# data/item.py
"あついいわ": ItemData(
    consumable=False,
    throw_power=60,
    handlers={
        Event.ON_CHECK_DURATION: ItemHandler(
            partial(common.resolve_field_count, field="はれ", additonal_count=3),
            subject_spec="source:self",
            log="never",
        )
    }
)
```

**理由**: 
- 延長効果は「アイテムが所有する効果」なので、アイテムデータに実装
- `ON_CHECK_DURATION` イベントで天候の持続ターン数を判定
- `resolve_field_count` ヘルパー関数が、フィールド名のチェックと延長処理を行う
- `field="はれ"` で対象の天候を指定し、`additonal_count=3` で延長ターン数を指定

---

### ケース3: 技が天候に反応する

**技「ソーラービーム」**: 晴れ時に溜めなしで発動

```python
# data/move.py
"ソーラービーム": MoveData(
    type="くさ",
    category="特殊",
    power=120,
    charge_turn=1,  # 通常は1ターン溜める
    handlers={
        # 技自身が天候を確認して溜めターンをスキップ
        Event.ON_BEFORE_MOVE: MoveHandler(
            h.ソーラービーム_charge,
            subject_spec="attacker:self",
        ),
    }
)

# handlers/move.py
def ソーラービーム_charge(battle: Battle, ctx: EventContext, value: Any):
    # 晴れ時は溜めターンをスキップ
    if battle.weather == "はれ":
        ctx.move.charge_turn = 0
        return HandlerReturn(True)
    # 雨・砂嵐・雪時は威力半減（別イベントで処理）
    return HandlerReturn(False)
```

**理由**: 天候依存の溜めスキップは「技の性質」なので、技データに実装

---

## イベント優先度と実行順序

同じイベントに複数のハンドラが登録されている場合、以下の順序で実行されます：

1. **priority が小さい順**
2. **同じ priority なら素早さが大きい順**

### 例: ON_CALC_POWER_MODIFIER

```
天候「はれ」のハンドラ (priority=100)
特性「てきおうりょく」のハンドラ (priority=100)
アイテム「いのちのたま」のハンドラ (priority=100)
```

→ 素早さ順に実行される

---

## まとめ

### 実装場所の決定ルール

| 作用の種類 | 実装場所 | キーワード |
|-----------|---------|-----------|
| **状態を変更する** | 技/特性/アイテムデータ | 「〜を発動する」「〜にする」 |
| **状態が与える効果** | 天候/地形/場データ | 「〜時に威力が上がる」 |
| **状態に反応する** | 特性/アイテムデータ | 「〜時に素早さが上がる」 |

### チェックリスト

- [ ] この効果は誰/何が所有しているか？
- [ ] 状態を変更するのか、状態の効果なのか？
- [ ] イベント経由で実装されているか？
- [ ] 単一責任の原則に違反していないか？
- [ ] 他のエンティティの責任を侵害していないか？

---

## 参考実装例

### 天候関連

- **天候変更**: [`data/ability.py`](../../src/jpoke/data/ability.py) の「ひでり」、[`data/move.py`](../../src/jpoke/data/move.py) の「にほんばれ」
- **天候延長**: [`data/item.py`](../../src/jpoke/data/item.py) の「あついいわ」（※実装上は `data/field.py` に `turn_extension_item` として記載）
- **天候効果**: [`data/field.py`](../../src/jpoke/data/field.py) の「はれ」「あめ」
- **天候反応（特性）**: [`data/ability.py`](../../src/jpoke/data/ability.py) の「ようりょくそ」「すなかき」
- **天候反応（技）**: [`data/move.py`](../../src/jpoke/data/move.py) の「ソーラービーム」

### 地形関連

- **地形変更**: [`data/move.py`](../../src/jpoke/data/move.py) の「エレキフィールド」
- **地形効果**: [`data/field.py`](../../src/jpoke/data/field.py) の「エレキフィールド」
- **地形反応**: [`data/ability.py`](../../src/jpoke/data/ability.py) の「サーフテール」

---

**次のステップ**: 実装時は常にこの原則に従い、コードレビュー時にも確認すること。
