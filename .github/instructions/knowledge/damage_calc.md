# ダメージ計算の知見

ダメージ計算の仕様・実装パターン・注意点。

## ダメージ計算式

```
ダメージ = ((レベル × 2 / 5 + 2) × 威力 × 攻撃力 / 防御力 / 50 + 2) × 乱数(0.85-1.0) × 各種補正
```

### 実装場所
`core/damage.py` の `calculate_damage()`

## 計算フロー

```
1. 基本ダメージ計算
   ├─ レベル補正
   ├─ 威力取得 (ON_CALC_POWER イベント)
   ├─ 威力補正 (ON_CALC_POWER_MODIFIER イベント)
   ├─ 攻撃力取得 (ランク補正含む)
   ├─ 攻撃力補正 (ON_CALC_ATTACK_MODIFIER イベント)
   ├─ 防御力取得 (ランク補正含む)
   └─ 防御力補正 (ON_CALC_DEFENSE_MODIFIER イベント)

2. タイプ相性
   └─ type_effectiveness(攻撃タイプ, 防御タイプ1, 防御タイプ2)

3. 最終補正
   ├─ タイプ一致補正 (1.5倍 = 6144/4096)
   ├─ 急所補正 (1.5倍 = 6144/4096)
   ├─ 乱数 (0.85-1.0)
   └─ ダメージ補正 (ON_CALC_DAMAGE_MODIFIER イベント)
```

## 4096基準

**理由**: 浮動小数点演算を避けて正確な計算を行うため

```python
# 補正値の基準
BASE = 4096

# 1.5倍
modifier = 6144
value = (value * 6144) // 4096

# 0.5倍
modifier = 2048
value = (value * 2048) // 4096

# 2倍
modifier = 8192
value = (value * 8192) // 4096
```

### よく使う補正値

| 倍率 | 4096基準 | 計算式 |
|------|---------|--------|
| 0.5倍 | 2048 | 4096 * 0.5 |
| 0.75倍 | 3072 | 4096 * 0.75 |
| 1.2倍 | 4915 | 4096 * 1.2 |
| 1.3倍 | 5325 | 4096 * 1.3 |
| 1.5倍 | 6144 | 4096 * 1.5 |
| 2倍 | 8192 | 4096 * 2 |

## イベント使い分け

### ON_CALC_POWER
**用途**: 威力そのものを計算（技固有の威力計算）

```python
# 例: ジャイロボール
def ジャイロボール_power(battle, ctx, value):
    power = min(150, (defender_speed * 25) // attacker_speed)
    return HandlerReturn(True, power)
```

### ON_CALC_POWER_MODIFIER
**用途**: 威力に補正をかける（特性・天候・アイテム等）

```python
# 例: 天候「はれ」でほのお技1.5倍
def はれ_power_modifier(battle, ctx, value):
    if ctx.move.type == "ほのお":
        return HandlerReturn(True, (value * 6144) // 4096)
    return HandlerReturn(False)
```

### ON_CALC_ATTACK_MODIFIER / ON_CALC_DEFENSE_MODIFIER
**用途**: 攻撃力・防御力に補正をかける

```python
# 例: やけど状態で物理攻撃力0.5倍
def やけど_attack_modifier(battle, ctx, value):
    if ctx.move.category == "physical":
        return HandlerReturn(True, (value * 2048) // 4096)
    return HandlerReturn(False)
```

### ON_CALC_DAMAGE_MODIFIER
**用途**: 最終ダメージに補正をかける

```python
# 例: リフレクター（物理ダメージ0.5倍）
def リフレクター_damage_modifier(battle, ctx, value):
    if ctx.move.category == "physical":
        return HandlerReturn(True, (value * 2048) // 4096)
    return HandlerReturn(False)
```

## タイプ相性

### 実装場所
`utils/type_effectiveness.py`

### 相性テーブル
```python
TYPE_CHART = {
    "ほのお": {
        "くさ": 2.0,    # 効果抜群
        "みず": 0.5,    # 効果いまひとつ
        "ほのお": 0.5,
    },
    # ...
}
```

### 計算
```python
effectiveness = get_type_effectiveness(move_type, [defender_type1, defender_type2])
# 2タイプの相性を掛け合わせ
# 例: くさ/どく に ほのお技 → 2.0 * 1.0 = 2.0
```

## ランク補正

### ランク範囲
-6 ~ +6

### 補正倍率テーブル
```python
RANK_MULTIPLIERS = {
    -6: 2/8,   # 0.25倍
    -5: 2/7,
    -4: 2/6,
    -3: 2/5,
    -2: 2/4,   # 0.5倍
    -1: 2/3,
    0:  1.0,
    1:  3/2,   # 1.5倍
    2:  4/2,   # 2.0倍
    3:  5/2,
    4:  6/2,
    5:  7/2,
    6:  8/2,   # 4.0倍
}
```

### 適用タイミング
攻撃力・防御力取得時に自動適用

```python
effective_attack = base_attack * rank_multiplier(attack_rank)
```

## 急所

### 急所率ランク
```python
CRITICAL_RATIOS = {
    0: 1/24,   # 通常
    1: 1/8,
    2: 1/2,
    3: 1/1,    # 必ず急所
}
```

### 急所補正
- ダメージ1.5倍
- 攻撃側の攻撃ランク下降無視
- 防御側の防御ランク上昇無視

## 乱数

### 範囲
0.85 ~ 1.0（16段階）

### 実装
```python
import random

def random_multiplier():
    return random.randint(85, 100) / 100.0
```

## タイプ一致補正

```python
# 技タイプがポケモンのタイプ1またはタイプ2と一致
if move.type in [attacker.type1, attacker.type2]:
    damage = (damage * 6144) // 4096  # 1.5倍
```

### 特性による変更
**てきおうりょく**: タイプ一致補正が2倍に

```python
# てきおうりょく持ちの場合
if move.type in [attacker.type1, attacker.type2]:
    damage = (damage * 8192) // 4096  # 2倍
```

## よくあるエッジケース

### 1. 0ダメージ防止

```python
# 最低1ダメージ保証
damage = max(1, damage)
```

### 2. HP上限チェック

```python
# ダメージがHP超過しないように
actual_damage = min(damage, defender.current_hp)
```

### 3. 補正の重複

複数の補正が重複する場合、**掛け算で累積**

```python
# 例: はれ(1.5倍) + てきおうりょく(タイプ一致2倍)
power = base_power
power = (power * 6144) // 4096  # はれ
power = (power * 8192) // 4096  # タイプ一致2倍
```

### 4. 整数演算の丸め誤差

```python
# ❌ NG: 複数回の除算で誤差蓄積
value = value * 3 / 2 / 4096

# ✅ OK: 一度に計算
value = (value * 3 * 4096) // (2 * 4096)
```

## トラブルシューティング

### ダメージが期待値と違う

**チェック項目**:
1. 乱数要素を考慮しているか
2. タイプ相性は正しいか
3. ランク補正が適用されているか
4. 補正の重複は正しいか

### 補正が効かない

**チェック項目**:
1. 正しいイベントを使用しているか
2. RoleSpec（attacker/defender）は正しいか
3. 条件チェックが正しいか
4. HandlerReturnの返り値は正しいか

### オーバーフロー/アンダーフロー

**対策**: 計算途中で適切に丸める

```python
# 大きな値の掛け算前に除算
value = (value // 4096) * modifier
```

## 最新知見（随時追記）

<!-- 新しい知見はここに追記 -->
