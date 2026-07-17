# グループ計画: ターン終了・その他効果系

作成日: 2026-06-05

対象: うるおいボディ / ナイトメア / すてみ / とうそうしん / でんきにかえる / じょうききかん / サーフテール / ふくつのこころ

---

## うるおいボディ

### 効果
天気が雨のとき、ターン終了時に状態異常を治す。

**priority**: `turn.md` ON_TURN_END_2 priority 60「うるおいボディ / だっぴ」。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_TURN_END` | 60 | `source:self` | `うるおいボディ_on_turn_end` |

### 実装

```python
def うるおいボディ_on_turn_end(battle, ctx, value):
    """うるおいボディ: あめ中ターン終了時に状態異常を回復する。"""
    if not battle.weather.rainy:
        return HandlerReturn(value=value)
    mon = ctx.source
    if not mon.ailment.is_active:
        return HandlerReturn(value=value)
    battle.ailment_manager.cure(mon)
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**: `battle.weather.rainy` は `name in ("あめ", "おおあめ")` を返すプロパティ（だっぴ参考）。

### data/ability.py 登録

```python
"うるおいボディ": AbilityData(
    handlers={
        Event.ON_TURN_END: h.AbilityHandler(
            h.うるおいボディ_on_turn_end,
            subject_spec="source:self",
            priority=60,
        ),
    }
),
```

### テストケース
- あめ中で状態異常あり → ターン終了時に回復
- 晴れ中では発動しない
- 状態異常なしでは発動しない

---

## ナイトメア

### 効果
ねむり状態の相手のHPを毎ターン最大HPの1/8削る。

**priority**: `turn.md` ON_TURN_END_4 priority 150「ナイトメア」。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_TURN_END` | 150 | `source:self` | `ナイトメア_on_turn_end` |

### 実装

```python
def ナイトメア_on_turn_end(battle, ctx, value):
    """ナイトメア: ねむり状態の相手に毎ターン1/8ダメージ。"""
    mon = ctx.source
    foe = battle.foe(mon)
    if foe is None or not foe.alive:
        return HandlerReturn(value=value)
    if foe.ailment.name != "ねむり":
        return HandlerReturn(value=value)
    if battle.modify_hp(foe, r=-1/8, reason="ability"):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"ナイトメア": AbilityData(
    handlers={
        Event.ON_TURN_END: h.AbilityHandler(
            h.ナイトメア_on_turn_end,
            subject_spec="source:self",
            priority=150,
        ),
    }
),
```

### テストケース
- 相手がねむり中 → ターン終了時に1/8ダメージ
- 相手が覚醒 → 発動しない
- 相手がひんし → 発動しない

---

## すてみ

### 効果
反動を受けるわざの威力が1.2倍になる。

**仕様**: `ability_list.md` には「1.2倍」と記載。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_CALC_POWER_MODIFIER` | 100 | `attacker:self` | `すてみ_modify_power` |

### 実装

```python
def すてみ_modify_power(battle, ctx, value):
    """すてみ: 反動技の威力を1.2倍にする（4915/4096）。"""
    if ctx.move.has_label("recoil"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)
```

**注意**: 反動技の識別は `move.has_label("recoil")` を使う。`move_label.md` で "recoil" ラベルの対象技を確認。

### data/ability.py 登録

```python
"すてみ": AbilityData(
    handlers={
        Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
            h.すてみ_modify_power,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- とびひざげり等の反動技 → 威力1.2倍
- 反動なし技 → 変化なし

---

## とうそうしん

### 効果
相手と同じ性別のときこうげき・とくこうが1.25倍、異性のときは0.75倍。性別不明同士は効果なし。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_CALC_ATK_MODIFIER` | 100 | `attacker:self` | `とうそうしん_modify_atk` |

### 実装

```python
def とうそうしん_modify_atk(battle, ctx, value):
    """とうそうしん: 性別による攻撃補正。"""
    attacker = ctx.attacker
    defender = ctx.defender
    if attacker is None or defender is None:
        return HandlerReturn(value=value)
    a_gender = attacker.gender
    d_gender = defender.gender
    if a_gender == "" or d_gender == "":  # 性別不明なら無効
        return HandlerReturn(value=value)
    if a_gender == d_gender:
        value = apply_fixed_modifier(value, 5120)  # 1.25倍
    else:
        value = apply_fixed_modifier(value, 3072)  # 0.75倍
    return HandlerReturn(value=value)
```

**注意**: `mon.gender` の実際のAPIを確認（`"♂"`, `"♀"`, `""` 等）。

### data/ability.py 登録

```python
"とうそうしん": AbilityData(
    handlers={
        Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
            h.とうそうしん_modify_atk,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- 同性対決 → こうげき/とくこう 1.25倍
- 異性対決 → 0.75倍
- 性別不明 → 補正なし

---

## でんきにかえる

### 効果
攻撃技でダメージを受けたとき、じゅうでん状態になる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `でんきにかえる_on_damage` |

### 実装

```python
def でんきにかえる_on_damage(battle, ctx, value):
    """でんきにかえる: 被弾時にじゅうでん状態になる。"""
    mon = ctx.defender
    if battle.volatile_manager.apply(mon, "じゅうでん", source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"でんきにかえる": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.でんきにかえる_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 攻撃技受けてじゅうでん状態になる
- すでにじゅうでん状態なら重複しない（apply が False）

---

## じょうききかん

### 効果
みずタイプかほのおタイプの攻撃技でダメージを受けたとき、すばやさが6段階上がる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `じょうききかん_on_damage` |

### 実装

```python
def じょうききかん_on_damage(battle, ctx, value):
    """じょうききかん: みず/ほのお技受けてS↑6。"""
    if ctx.move.type not in ("みず", "ほのお"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"S": +6}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"じょうききかん": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.じょうききかん_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- みず技受けてS↑6
- ほのお技受けてS↑6
- でんき等他タイプでは発動しない
- S最大なら発動しない

---

## サーフテール

### 効果
エレキフィールドのとき、すばやさが2倍になる。

**仕様**: すいすい・ゆきかきのエレキフィールド版。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `DomainEvent.ON_CALC_SPEED` | 100 | `source:self` | `サーフテール_modify_speed` |

### 実装

```python
def サーフテール_modify_speed(battle, ctx, value):
    """サーフテール: エレキフィールド中すばやさ2倍。"""
    if battle.terrain.name == "エレキフィールド":
        value *= 2
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"サーフテール": AbilityData(
    handlers={
        DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
            h.サーフテール_modify_speed,
            subject_spec="source:self",
        ),
    }
),
```

### テストケース
- エレキフィールド中 → S実数値2倍
- グラスフィールド等他フィールドでは変化なし

---

## ふくつのこころ

### 効果
ひるんだとき、すばやさが1段階上がる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_VOLATILE_START` | 100 | `target:self` | `ふくつのこころ_on_flinch` |

**注意**: ひるみ状態が付与された直後（`ON_VOLATILE_START`）に発火。volatile の名前をチェックして "ひるみ" のときのみ発動。

### 実装

```python
def ふくつのこころ_on_flinch(battle, ctx, value):
    """ふくつのこころ: ひるんだときS↑1。"""
    if not hasattr(value, "name") or value.name != "ひるみ":
        return HandlerReturn(value=value)
    mon = ctx.target
    if battle.modify_stats(mon, {"S": +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**: `ON_VOLATILE_START` の `value` が volatile オブジェクトか名前文字列かを実装時に確認。`value.name` か `value == "ひるみ"` か判断が必要。

### data/ability.py 登録

```python
"ふくつのこころ": AbilityData(
    handlers={
        Event.ON_VOLATILE_START: h.AbilityHandler(
            h.ふくつのこころ_on_flinch,
            subject_spec="target:self",
        ),
    }
),
```

### テストケース
- ひるみ付与時にS↑1
- こんらん等他のvolatile付与では発動しない
- S最大なら発動しない
