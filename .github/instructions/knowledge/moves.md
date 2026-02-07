# 技実装の知見

技実装時の注意点・パターン・エッジケース。

## 基本方針

- **MoveData**: 技の基本データ（威力・命中・PP等）
- **MoveHandler**: 技の効果実装
- **ON_HIT**: 技が命中したときの効果
- **複数効果**: handlersにリスト登録可能

## 技の基本構造

```python
"技名": MoveData(
    name="技名",
    type="タイプ",
    category="physical" | "special" | "status",
    power=威力,  # 0 = 変化技
    accuracy=命中率,  # 0 = 必中
    pp=PP,
    priority=優先度,  # 通常0、先制+1、後攻-1
    target="normal" | "self" | "ally" | "all-opponents",
    contact=True | False,  # 接触技か
    description="説明",
    handlers={
        Event.ON_HIT: MoveHandler(効果関数, subject_spec="attacker:self"),
    }
)
```

## 実装パターン別

### 1. 単純ダメージ技

```python
"たいあたり": MoveData(
    name="たいあたり",
    type="ノーマル",
    category="physical",
    power=40,
    accuracy=100,
    pp=35,
    contact=True,
    description="相手に体当たりして攻撃する。",
)
# handlers不要（ダメージ計算は自動）
```

### 2. 追加効果付き技

```python
def かえんほうしゃ_burn(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """10%の確率でやけど付与"""
    defender = ctx.defender
    
    # 既存状態異常
    if defender.ailment:
        return HandlerReturn(False)
    
    # 10%判定
    if random.random() > 0.1:
        return HandlerReturn(False)
    
    # やけど付与
    defender.set_ailment("やけど")
    battle.logger.log_message(f"{defender.name}はやけどした！")
    
    return HandlerReturn(True)

"かえんほうしゃ": MoveData(
    name="かえんほうしゃ",
    type="ほのお",
    category="special",
    power=90,
    accuracy=100,
    pp=15,
    handlers={
        Event.ON_HIT: MoveHandler(
            かえんほうしゃ_burn,
            subject_spec="attacker:self",
        ),
    }
)
```

### 3. 複数効果技

```python
"技名": MoveData(
    handlers={
        Event.ON_HIT: [
            MoveHandler(効果1, subject_spec="attacker:self"),
            MoveHandler(効果2, subject_spec="attacker:self"),
        ]
    }
)
```

### 4. ランク補正技

```python
def つるぎのまい_attack_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """攻撃ランク+2"""
    attacker = ctx.attacker
    
    # ランク上昇
    attacker.boost_stat("attack", 2)
    battle.logger.log_message(f"{attacker.name}のこうげきがぐーんと上がった！")
    
    return HandlerReturn(True)

"つるぎのまい": MoveData(
    name="つるぎのまい",
    type="ノーマル",
    category="status",
    power=0,
    pp=20,
    target="self",
    handlers={
        Event.ON_HIT: MoveHandler(
            つるぎのまい_attack_boost,
            subject_spec="attacker:self",
        ),
    }
)
```

### 5. フィールド変更技

```python
from functools import partial
from jpoke.handlers.common import activate_weather, activate_terrain

"にほんばれ": MoveData(
    name="にほんばれ",
    type="ほのお",
    category="status",
    power=0,
    pp=5,
    target="field",
    handlers={
        Event.ON_HIT: MoveHandler(
            partial(activate_weather, weather="はれ", duration=5),
            subject_spec="attacker:self",
        ),
    }
)
```

### 6. 特殊威力計算技

```python
def ジャイロボール_power(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """相手の素早さ÷自分の素早さ × 25（最大150）"""
    attacker = ctx.attacker
    defender = ctx.defender
    
    attacker_speed = attacker.effective_speed
    defender_speed = defender.effective_speed
    
    # 0除算回避
    if attacker_speed == 0:
        return HandlerReturn(False)
    
    # 威力計算
    power = min(150, (defender_speed * 25) // attacker_speed)
    
    return HandlerReturn(True, power)

"ジャイロボール": MoveData(
    name="ジャイロボール",
    type="はがね",
    category="physical",
    power=1,  # ダミー（実際の威力はハンドラで計算）
    accuracy=100,
    pp=5,
    contact=True,
    handlers={
        Event.ON_CALC_POWER: MoveHandler(
            ジャイロボール_power,
            subject_spec="attacker:self",
        ),
    }
)
```

## よくあるエッジケース

### 1. 必中技

```python
"技名": MoveData(
    accuracy=0,  # 0 = 必中
)
```

### 2. 先制技

```python
"でんこうせっか": MoveData(
    priority=1,  # +1 = 先制
)
```

### 3. 後攻技

```python
"カウンター": MoveData(
    priority=-5,  # -5 = 後攻
)
```

### 4. 連続攻撃技

```python
def おうふくビンタ_multi_hit(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """2-5回連続攻撃"""
    # ヒット数決定
    hits = random.choices([2, 3, 4, 5], weights=[3/8, 3/8, 1/8, 1/8])[0]
    
    # NOTE: 連続攻撃の実装は複雑
    # TODO: MoveExecutorでの対応が必要
    
    return HandlerReturn(True, hits)
```

### 5. 反動技

```python
def すてみタックル_recoil(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """与えたダメージの1/4を反動で受ける"""
    attacker = ctx.attacker
    damage_dealt = ctx.damage  # 与えたダメージ
    
    recoil = damage_dealt // 4
    attacker.take_damage(recoil)
    battle.logger.log_message(f"{attacker.name}は反動を受けた！")
    
    return HandlerReturn(True)

"すてみタックル": MoveData(
    handlers={
        Event.ON_AFTER_MOVE: MoveHandler(
            すてみタックル_recoil,
            subject_spec="attacker:self",
        ),
    }
)
```

### 6. HP吸収技

```python
def きゅうけつ_drain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """与えたダメージの1/2を回復"""
    attacker = ctx.attacker
    damage_dealt = ctx.damage
    
    heal = damage_dealt // 2
    attacker.heal(heal)
    battle.logger.log_message(f"{attacker.name}はHPを回復した！")
    
    return HandlerReturn(True)
```

## トラブルシューティング

### 技が発動しない

**チェック項目**:
1. イベントが正しいか（ON_HIT、ON_CALC_POWER等）
2. RoleSpecが正しいか（attacker:selfなど）
3. 条件チェックが正しいか

### 威力計算がおかしい

**チェック項目**:
1. `ON_CALC_POWER` vs `ON_CALC_POWER_MODIFIER` の使い分け
   - `ON_CALC_POWER`: 威力そのものを計算（ジャイロボール等）
   - `ON_CALC_POWER_MODIFIER`: 威力に補正をかける（特性・天候等）

2. 4096基準の整数演算

### 追加効果が発動しすぎる/しなさすぎる

**確認**: 確率判定のロジック

```python
# ✅ OK: 10%判定
if random.random() < 0.1:
    # 発動

# ❌ NG: 逆
if random.random() > 0.1:
    # これだと90%発動
```

## ON_TRY_ACTION の重要性

**用途**: 技使用前の行動可否チェック

```python
# 例: アンコール中は同じ技しか使えない
def アンコール_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アンコール中は指定技以外使用不可"""
    pokemon = ctx.source
    move = ctx.move
    
    encore = pokemon.volatiles.get("アンコール")
    if not encore or not encore.is_active():
        return HandlerReturn(False)
    
    # 指定技以外
    if move.name != encore.locked_move:
        battle.logger.log_message(f"{pokemon.name}はアンコールされている！")
        return HandlerResult(True, None, HandlerResult.BLOCK)
    
    return HandlerReturn(False)
```

**注意**: `ON_TRY_ACTION` は行動可否のゲートなので、失敗時は即座に行動を中断する設計が必要。

## 最新知見（随時追記）

<!-- 新しい知見はここに追記 -->
