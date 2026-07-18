# グループ計画: フラグ・タイプ変換・防御系

作成日: 2026-06-05

対象: テイルアーマー / ビビッドボディ / じょおうのいげん / ちどりあし / はっこう / ミラクルスキン / フラワーベール / フラワーギフト / ばんけん / うるおいボイス

---

## じょおうのいげん / テイルアーマー / ビビッドボディ

### 効果
自分と味方は、相手からの先制技（優先度+1以上）を受けなくなる。
3特性は同一効果。テイルアーマーとビビッドボディはじょおうのいげんと同じハンドラ関数を共有する。

**priority**: `turn.md` ON_TRY_MOVE_1 priority 40「じょおうのいげん: 優先度高い技失敗」。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_TRY_MOVE_1` | 40 | `defender:self` | `じょおうのいげん_block_priority` |

### 実装

```python
def じょおうのいげん_block_priority(battle, ctx, value):
    """じょおうのいげん/テイルアーマー/ビビッドボディ: 優先度+1以上の技を無効化。"""
    effective_priority = battle.speed_calculator.calc_move_priority(
        ctx.attacker, ctx.move
    )
    if effective_priority <= 0:
        return HandlerReturn(value=value)
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    battle.add_event_log(
        ctx.attacker, LogCode.MOVE_FAILED,
        payload={"reason": "じょおうのいげん"}
    )
    return HandlerReturn(value=False, stop_event=True)
```

### data/ability.py 登録

```python
"じょおうのいげん": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_TRY_MOVE_1: h.AbilityHandler(
            h.じょおうのいげん_block_priority,
            subject_spec="defender:self",
            priority=40,
        ),
    }
),
"テイルアーマー": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_TRY_MOVE_1: h.AbilityHandler(
            h.じょおうのいげん_block_priority,  # 共有
            subject_spec="defender:self",
            priority=40,
        ),
    }
),
"ビビッドボディ": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_TRY_MOVE_1: h.AbilityHandler(
            h.じょおうのいげん_block_priority,  # 共有
            subject_spec="defender:self",
            priority=40,
        ),
    }
),
```

### テストケース
- 優先度+1技（でんこうせっか等）→ 失敗
- いたずらごころで優先度+1になった変化技 → 失敗
- 優先度0技 → 通常通り
- かたやぶり系 → 特性を無視して技が通る

---

## ちどりあし

### 効果
こんらん状態のとき、受ける攻撃の命中率が2倍下がる（相手の命中率が0.5倍）。

**仕様**: こんらん中に防御側の回避率が実質2倍になる（攻撃者の命中判定を半減）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MODIFY_ACCURACY` | 100 | `defender:self` | `ちどりあし_reduce_accuracy` |

### 実装

```python
def ちどりあし_reduce_accuracy(battle, ctx, value):
    """ちどりあし: こんらん中に受ける技の命中率を半減する。"""
    if ctx.defender.check_volatile("こんらん"):
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"ちどりあし": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
            h.ちどりあし_reduce_accuracy,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- こんらん中に受ける技の命中率が半減
- こんらん状態でないときは変化なし
- かたやぶり系技では無効

---

## はっこう

### 効果
命中率を下げられない。

**仕様**: するどいめの「命中率下降無効」部分のみ（回避無視はなし）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_BEFORE_MODIFY_STAT` | 100 | `target:self` | `はっこう_block_acc_drop` |

### 実装

```python
def はっこう_block_acc_drop(battle, ctx, value):
    """はっこう: 命中率（ACC）の低下を無効化する。"""
    filtered = {stat: v for stat, v in value.items() if not (stat == "ACC" and v < 0)}
    return HandlerReturn(value=filtered)
```

### data/ability.py 登録

```python
"はっこう": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
            h.はっこう_block_acc_drop,
            subject_spec="target:self",
        ),
    }
),
```

### テストケース
- にらみつける等でACC↓を試みる → 無効
- ACC↑は通常通り
- A↓等ACC以外の低下は通常通り

---

## ミラクルスキン

### 効果
相手から受ける変化技の命中率が50%になる（必中技は除く）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MODIFY_ACCURACY` | 100 | `defender:self` | `ミラクルスキン_reduce_accuracy` |

### 実装

```python
def ミラクルスキン_reduce_accuracy(battle, ctx, value):
    """ミラクルスキン: 変化技の命中率を最大50%（2048/4096）にする。"""
    if ctx.move is None or ctx.move.category != "変化":
        return HandlerReturn(value=value)
    if ctx.move.accuracy is None:  # 必中技
        return HandlerReturn(value=value)
    value = min(value, 2048)  # value は 4096 スケール
    return HandlerReturn(value=value)
```

**注意**: 命中率の内部スケールが 4096 基準かどうか確認。50% = 2048/4096。

### data/ability.py 登録

```python
"ミラクルスキン": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
            h.ミラクルスキン_reduce_accuracy,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 変化技（どくどく等）の命中率が50%になる
- 攻撃技には適用されない
- 必中の変化技には適用されない

---

## ばんけん

### 効果
いかくを受けるとこうげきが1段階上がる（いかく無効ではなく上乗せ）。また、交代させる技や道具の効果を受けない。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_BEFORE_MODIFY_STAT` | 100 | `target:self` | `ばんけん_on_intimidate` |
| `ON_TRY_BLOW` | 100 | `defender:self` | `ばんけん_block_blow` |

### 実装

```python
def ばんけん_on_intimidate(battle, ctx, value):
    """ばんけん: いかくでA↓を受けたとき逆にA↑1する。"""
    if ctx.stat_change_reason != "いかく":
        return HandlerReturn(value=value)
    mon = ctx.target
    # いかくによるA↓は通常通り適用し、その上でA↑1を追加
    battle.modify_stats(mon, {"A": +1}, source=mon)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ばんけん_block_blow(battle, ctx, value):
    """ばんけん: ふきとばし・ほえる等の強制交代を無効化する。"""
    announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=False, stop_event=True)
```

**注意**:
- いかくのA↓は通常通り発生し、その後でA↑1が追加される（差し引きA↑1）。
- `ON_TRY_BLOW` は `きゅうばん_block_blow` と同様。

### data/ability.py 登録

```python
"ばんけん": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
            h.ばんけん_on_intimidate,
            subject_spec="target:self",
        ),
        Event.ON_TRY_BLOW: h.AbilityHandler(
            h.ばんけん_block_blow,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- いかく発動時 → A↓1した後にA↑1（差し引き変化なし？実際は-1+1=0変化）
- ほえる等の強制交代 → 無効
- A↓以外の原因（あまえる等）には A↑ 発動しない

---

## フラワーベール

### 効果
自分と味方の草タイプが状態異常にならず、能力を下げられない。シングルでは自分のみ対象（くさタイプのとき有効）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_BEFORE_APPLY_AILMENT` | 100 | `target:self` | `フラワーベール_prevent_ailment` |
| `ON_BEFORE_MODIFY_STAT` | 100 | `target:self` | `フラワーベール_prevent_stat_drop` |

### 実装

```python
def フラワーベール_prevent_ailment(battle, ctx, value):
    """フラワーベール: くさタイプへの状態異常を無効化する。"""
    mon = ctx.target
    if "くさ" not in mon.types:
        return HandlerReturn(value=value)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=False, stop_event=True)


def フラワーベール_prevent_stat_drop(battle, ctx, value):
    """フラワーベール: くさタイプへの能力低下を無効化する。"""
    mon = ctx.target
    if "くさ" not in mon.types:
        return HandlerReturn(value=value)
    has_negative = any(v < 0 for v in value.values())
    if not has_negative:
        return HandlerReturn(value=value)
    # 能力低下を含む変化をすべて除外
    filtered = {stat: v for stat, v in value.items() if v >= 0}
    if filtered != value:
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=filtered)
```

### data/ability.py 登録

```python
"フラワーベール": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
            h.フラワーベール_prevent_ailment,
            subject_spec="target:self",
        ),
        Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
            h.フラワーベール_prevent_stat_drop,
            subject_spec="target:self",
        ),
    }
),
```

### テストケース
- くさタイプのポケモンへの状態異常 → 無効
- くさタイプへの能力低下 → 無効
- くさタイプでないポケモンには保護なし
- かたやぶり系では無効

---

## フラワーギフト

### 効果
天気が晴れのとき、自分と味方のこうげき・とくぼうが1.5倍になる。シングルでは自分のみに適用。

**仕様**: チェリムの専用特性。フォルムチェンジ（晴れ→はなやかなすがた）もあるが、本計画ではシングルバトルでのランク/倍率効果のみ実装。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_CALC_ATK_MODIFIER` | 100 | `attacker:self` | `フラワーギフト_modify_atk` |

**補足**: ON_SWITCH_IN でフォルムチェンジ（はなやかなすがた）するハンドラは `turn.md` ON_SWITCH_IN priority 140 に記載あり。フォルムチェンジ実装は別途対応。

### 実装

```python
def フラワーギフト_modify_atk(battle, ctx, value):
    """フラワーギフト: 晴れ中こうげき・とくぼうが1.5倍。"""
    if not battle.weather.sunny:
        return HandlerReturn(value=value)
    # こうげきとくぼう両方に適用（ON_CALC_ATK_MODIFIER は A/C 両方を扱う）
    value = apply_fixed_modifier(value, 6144)  # 1.5倍
    return HandlerReturn(value=value)
```

**注意**: `ON_CALC_ATK_MODIFIER` がこうげき(A)とくぼう(D)をどのように区別するか確認が必要。

### data/ability.py 登録

```python
"フラワーギフト": AbilityData(
    flags=["uncopyable", "mold_breaker_ignorable"],
    handlers={
        Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
            h.フラワーギフト_modify_atk,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- 晴れ中 → こうげき1.5倍
- 雨等他天候では変化なし
- かたやぶり系では無効

---

## うるおいボイス

### 効果
音の技がみずタイプになる（威力1.2倍も適用）。

**仕様**: ノーマルスキンのみず版（音技のみ対象）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MODIFY_MOVE_TYPE` | 100 | `source:self` | `うるおいボイス_modify_move_type` |
| `ON_CALC_POWER_MODIFIER` | 100 | `attacker:self` | `うるおいボイス_modify_power` |

### 実装

```python
def うるおいボイス_modify_move_type(battle, ctx, value):
    """うるおいボイス: 音技をみずタイプに変換する。"""
    if ctx.move.has_label("sound") and value == "ノーマル":
        return HandlerReturn(value="みず")
    return HandlerReturn(value=value)


def うるおいボイス_modify_power(battle, ctx, value):
    """うるおいボイス: 音技（みず変換後）の威力を1.2倍にする。"""
    # ON_MODIFY_MOVE_TYPE で変換済みかどうかを確認する方法が必要。
    # ノーマルスキン系のパターン（move が元々sound で変換された）を参照。
    if ctx.move.has_label("sound") and ctx.move.type == "みず":
        value = apply_fixed_modifier(value, 4915)  # 1.2倍
    return HandlerReturn(value=value)
```

**注意**:
- `ON_MODIFY_MOVE_TYPE` での型変換後、`ctx.move.type` が書き換えられているかどうかはイベントフローによる。フェアリースキン等の実装を参照。
- 音技かどうかは `move.has_label("sound")` で判定。

### data/ability.py 登録

```python
"うるおいボイス": AbilityData(
    handlers={
        Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
            h.うるおいボイス_modify_move_type,
            subject_spec="source:self",
        ),
        Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
            h.うるおいボイス_modify_power,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- 音技（ラスターカノン等）がみずタイプになる
- 非音技には適用されない
- みず変換後に威力1.2倍適用
