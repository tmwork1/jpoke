# グループ計画: 接触被弾反応系（簡単）

作成日: 2026-06-05

対象: あくしゅう / カーリーヘアー / ぬめぬめ / のろわれボディ / どくのくさり / メロメロボディ / すなはき / わたげ

---

## 共通パターン

全て `ON_DAMAGE_HIT`、`subject_spec="defender:self"` で発火。
既存の `_apply_contact_counter_ailment` / `_apply_contact_counter_chip` ヘルパーを活用するか、同パターンで直書きする。

---

## あくしゅう

### 効果
技を使用したとき10%の確率で相手をひるませる。

**注意**: 仕様書では「技使用時」とあるが、実際には攻撃技の命中時のみ発動。`ON_DAMAGE_HIT` の `attacker:self` で実装する。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `attacker:self` | `あくしゅう_on_damage` |

### 実装

```python
def あくしゅう_on_damage(battle, ctx, value):
    if battle.random.random() < 0.1:
        battle.volatile_manager.apply(ctx.defender, "ひるみ", source=ctx.attacker, ctx=ctx)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"あくしゅう": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.あくしゅう_on_damage,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- 攻撃技命中時 10% でひるみ付与
- 非命中・変化技では発動しない（ON_DAMAGE_HIT は damage > 0 時のみ発火）

---

## カーリーヘアー

### 効果
直接攻撃を受けたとき、攻撃者のすばやさを1段階下げる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `カーリーヘアー_on_damage` |

### 実装

```python
def カーリーヘアー_on_damage(battle, ctx, value):
    if battle.query.is_contact(ctx):
        battle.modify_stats(ctx.attacker, {"S": -1}, source=ctx.defender, ctx=ctx)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"カーリーヘアー": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.カーリーヘアー_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 直接攻撃受けると攻撃者S↓1
- 直接攻撃でない（念力等）→発動しない

---

## ぬめぬめ

### 効果
直接攻撃を受けたとき、攻撃者のすばやさを1段階下げる。（カーリーヘアーと同効果）

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `ぬめぬめ_on_damage` |

### 実装

```python
def ぬめぬめ_on_damage(battle, ctx, value):
    if battle.query.is_contact(ctx):
        battle.modify_stats(ctx.attacker, {"S": -1}, source=ctx.defender, ctx=ctx)
    return HandlerReturn(value=value)
```

**注意**: カーリーヘアーと同実装。data/ability.py でも同一関数を登録してよい（`h.カーリーヘアー_on_damage` を共有するか専用関数を用意する）。

### data/ability.py 登録

```python
"ぬめぬめ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.ぬめぬめ_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 直接攻撃受けると攻撃者S↓1
- 非接触技では発動しない

---

## のろわれボディ

### 効果
直接攻撃を受けたとき、30%の確率で攻撃技を「かなしばり」状態にする。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 20 | `defender:self` | `のろわれボディ_on_damage` |

**priority**: `turn.md` ON_DAMAGE priority 20「のろわれボディ等: 攻撃技を受けた」に対応。

### 実装

```python
def のろわれボディ_on_damage(battle, ctx, value):
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    if battle.random.random() < 0.3:
        battle.volatile_manager.apply(
            ctx.attacker, "かなしばり",
            source=ctx.defender, ctx=ctx,
            move=ctx.move,
        )
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=value)
```

**注意**: `battle.volatile_manager.apply` で "かなしばり" を付与する際、対象の技（`ctx.move`）を封じる。かなしばりの実装が技指定に対応しているか確認が必要。

### data/ability.py 登録

```python
"のろわれボディ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.のろわれボディ_on_damage,
            subject_spec="defender:self",
            priority=20,
        ),
    }
),
```

### テストケース
- 直接攻撃受けて 30% でかなしばり
- 非接触技では発動しない
- 攻撃者の技がロックされる

---

## どくのくさり

### 効果
攻撃を当てると30%の確率で相手をもうどく状態にする。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `attacker:self` | `どくのくさり_on_damage` |

### 実装

```python
def どくのくさり_on_damage(battle, ctx, value):
    if battle.random.random() < battle.resolve_secondary_chance(ctx, 0.3):
        battle.ailment_manager.apply(
            ctx.defender, "もうどく",
            source=ctx.attacker, ctx=ctx,
        )
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"どくのくさり": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.どくのくさり_on_damage,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- 攻撃命中で 30% もうどく付与
- ちからずく使用者は追加効果なし（`resolve_secondary_chance` → 0）
- 相手がどく無効特性なら発動しない

---

## メロメロボディ

### 効果
直接攻撃を受けたとき、30%の確率で相手をメロメロ状態にする。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `メロメロボディ_on_damage` |

### 実装

```python
def メロメロボディ_on_damage(battle, ctx, value):
    if battle.query.is_contact(ctx) and battle.random.random() < 0.3:
        battle.volatile_manager.apply(
            ctx.attacker, "メロメロ",
            source=ctx.defender, ctx=ctx,
        )
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"メロメロボディ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.メロメロボディ_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 直接攻撃受けて 30% でメロメロ（異性の場合のみ成立する→volatile.apply 側でチェック）
- 非接触技では発動しない

---

## すなはき

### 効果
攻撃を受けたとき、天候をすなあらしにする。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `すなはき_on_damage` |

### 実装

```python
def すなはき_on_damage(battle, ctx, value):
    mon = ctx.defender
    if battle.weather.apply("すなあらし", 5, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"すなはき": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.すなはき_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 攻撃を受けるとすなあらしが発動（5ターン）
- すでにすなあらしなら変化なし（weather.apply が False を返す）
- おおひでり等の強天候中は上書きされない

---

## わたげ

### 効果
攻撃を受けたとき、すべてのポケモンのすばやさを1段階下げる。シングルバトルでは攻撃者のSを1段階下げる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `わたげ_on_damage` |

### 実装

```python
def わたげ_on_damage(battle, ctx, value):
    mon = ctx.defender
    attacker = ctx.attacker
    if attacker is None:
        return HandlerReturn(value=value)
    if battle.modify_stats(attacker, {"S": -1}, source=mon, ctx=ctx):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**: ダブルの場合は全ポケモン対象だが、シングル専用実装では攻撃者のみ。

### data/ability.py 登録

```python
"わたげ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.わたげ_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 攻撃受けると攻撃者S↓1
- クリアボディ等でS↓無効なら発動しない
