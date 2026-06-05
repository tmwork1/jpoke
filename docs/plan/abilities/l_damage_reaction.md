# グループ計画: 被弾後能力変化系

作成日: 2026-06-05

対象: じきゅうりょく / くだけるよろい / みずがため / せいぎのこころ / びびり / いかりのこうら / まけんき

---

## 共通パターン

ダメージを受けた後、条件に応じて自分の能力ランクを変化させる。
全て `ON_DAMAGE_HIT`（またはまけんきのみ `ON_MODIFY_STAT`）を使用。

---

## じきゅうりょく

### 効果
攻撃技のダメージを受けたとき、ぼうぎょが1段階上がる（物理・特殊問わず）。

**priority**: `turn.md` ON_DAMAGE に記載なし → デフォルト 100。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `じきゅうりょく_on_damage` |

### 実装

```python
def じきゅうりょく_on_damage(battle, ctx, value):
    mon = ctx.defender
    if battle.modify_stats(mon, {"B": +1}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"じきゅうりょく": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.じきゅうりょく_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 物理技受けてB↑1
- 特殊技受けてもB↑1
- B最大のときは発動しない（modify_stats が False を返す）
- 連続攻撃: 1発ごとにB↑1

---

## くだけるよろい

### 効果
物理技を受けると、ぼうぎょが1段階下がり、すばやさが2段階上がる。

**priority**: `turn.md` ON_DAMAGE priority 20「くだけるよろい等: 物理技を受けた」。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 20 | `defender:self` | `くだけるよろい_on_damage` |

### 実装

```python
def くだけるよろい_on_damage(battle, ctx, value):
    if battle.resolve_move_category(ctx.attacker, ctx.move) != "物理":
        return HandlerReturn(value=value)
    mon = ctx.defender
    battle.modify_stats(mon, {"B": -1}, source=ctx.attacker)
    if battle.modify_stats(mon, {"S": +2}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**: B↓は必ず適用、S↑2が成立したときに特性発動アナウンス。

### data/ability.py 登録

```python
"くだけるよろい": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.くだけるよろい_on_damage,
            subject_spec="defender:self",
            priority=20,
        ),
    }
),
```

### テストケース
- 物理技受けてB↓1,S↑2
- 特殊技では発動しない
- S最大のときもB↓は発生するが特性バー不表示

---

## みずがため

### 効果
みずタイプの技を受けると、ぼうぎょが2段階上がる。

**priority**: `turn.md` ON_DAMAGE priority 20「みずがため等: 特定タイプを受けた」。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 20 | `defender:self` | `みずがため_on_damage` |

### 実装

```python
def みずがため_on_damage(battle, ctx, value):
    if ctx.move.type != "みず":
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"B": +2}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**: ダメージ技のみ（ON_DAMAGE_HIT）が前提なので damage > 0 保証済み。変化技の水タイプは対象外。

### data/ability.py 登録

```python
"みずがため": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.みずがため_on_damage,
            subject_spec="defender:self",
            priority=20,
        ),
    }
),
```

### テストケース
- みず技受けてB↑2
- ほのお等他タイプでは発動しない
- B最大のときは発動しない

---

## せいぎのこころ

### 効果
あくタイプの攻撃を受けるとこうげきが1段階上がる。

**priority**: `turn.md` ON_DAMAGE に記載なし → デフォルト 100。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `せいぎのこころ_on_damage` |

### 実装

```python
def せいぎのこころ_on_damage(battle, ctx, value):
    if ctx.move.type != "あく":
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"A": +1}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"せいぎのこころ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.せいぎのこころ_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- あく技受けてA↑1
- ノーマル等では発動しない

---

## びびり

### 効果
あく・ゴースト・むしタイプの技を受けると、すばやさが1段階上がる。

**priority**: `turn.md` ON_DAMAGE に記載なし → デフォルト 100。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `びびり_on_damage` |

### 実装

```python
def びびり_on_damage(battle, ctx, value):
    if ctx.move.type not in ("あく", "ゴースト", "むし"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"S": +1}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**: いかくによるこうげき↓でも発動する（仕様書参照）が、いかくは ON_MODIFY_STAT で処理されるため ON_DAMAGE_HIT では発動しない。いかく対応は別途検討。

### data/ability.py 登録

```python
"びびり": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.びびり_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- あく/ゴースト/むし技受けてS↑1
- ほのお等では発動しない

---

## いかりのこうら

### 効果
HPが半分以下になったとき、こうげき・とくこう・すばやさが1段階上がり、ぼうぎょ・とくぼうが1段階下がる。

**仕様**: ぎゃくじょうと同じHP50%跨ぎのトリガー。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `いかりのこうら_on_damage` |

### 実装

```python
def いかりのこうら_on_damage(battle, ctx, value):
    mon = ctx.defender
    hp_after = mon.hp
    hp_before = hp_after + value  # value は damage量（正値）

    if not _crossed_half_hp(hp_before, hp_after, mon.max_hp):
        return HandlerReturn(value=value)

    battle.modify_stats(mon, {"B": -1, "D": -1}, source=ctx.attacker)
    if battle.modify_stats(mon, {"A": +1, "C": +1, "S": +1}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**:
- `value` は ON_DAMAGE_HIT 時点で受け取ったダメージ量（正値）。
- `_crossed_half_hp` はハンドラモジュール内の共通ヘルパー関数。
- B↓/D↓は必ず適用し、A,C,S↑のいずれかが成功したときにアナウンス。

### data/ability.py 登録

```python
"いかりのこうら": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.いかりのこうら_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- HP半分跨ぎで発動 → A,C,S↑1、B,D↓1
- HP半分以下にならない攻撃では発動しない
- すでに半分以下のとき、さらに受けても再発動しない
- ひんしになっても発動する（ON_DAMAGE_HIT は KO 後にも発火）

---

## まけんき

### 効果
敵から能力ランクを下げられたとき、こうげきが2段階上昇する。

**仕様**: かちきのA版。`ON_MODIFY_STAT` ハンドラで実装（かちき参照）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MODIFY_STAT` | 100 | `target:self` | `まけんき_on_stat_down` |

### 実装

```python
def まけんき_on_stat_down(battle, ctx, value):
    """まけんき特性: 能力を下げられたとき、こうげきが2段階上昇する。"""
    has_negative = any(v < 0 for v in value.values())
    if (
        has_negative
        and ctx.source != ctx.target
        and battle.modify_stats(ctx.target, {"A": +2}, source=ctx.source)
    ):
        announce_ability_triggered(battle, ctx, value, mon=ctx.target)
    return HandlerReturn(value=value)
```

**注意**: `ctx.source != ctx.target` で自分の技の反動等を除外（かちきと同パターン）。

### data/ability.py 登録

```python
"まけんき": AbilityData(
    handlers={
        Event.ON_MODIFY_STAT: h.AbilityHandler(
            h.まけんき_on_stat_down,
            subject_spec="target:self",
        )
    }
),
```

### テストケース
- いかくでA↓→まけんき発動でA↑2（差し引きA↑1）
- 自分の技の追加効果でA↓→発動しない（ctx.source == ctx.target）
- A最大のときはメッセージ出るが特性バー不表示
- 複数能力同時下降（くすぐる等）→その数だけ発動
