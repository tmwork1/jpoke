# エッジケース集

実装時に注意すべきエッジケース・特殊状況の一覧。

## 交代関連

### 1. 交代時の特性発動順序

```
交代元 (switch_out)
  ├─ ON_SWITCH_OUT イベント
  ├─ ハンドラ解除 (unregister_handlers)
  └─ 揮発性状態クリア

交代先 (switch_in)
  ├─ ハンドラ登録 (register_handlers)
  ├─ ON_SWITCH_IN イベント
  └─ 特性発動（天候変更等）
```

**注意**: 交代先の特性が先に発動し、その後相手の特性が反応する

### 2. 瀕死と同時に交代

```python
# 相手を倒した場合
if defender.is_fainted():
    # 相手の ON_FAINT イベント
    # 特性「ゆうばく」等が発動
    # 交代処理
```

**注意**: 瀕死時の効果→交代の順序

### 3. 強制交代技（ほえる等）

- 交代阻止特性（きゅうばん、ねんちゃく）の判定
- 交代先がいない場合の失敗
- ダイマックス中は無効

## 状態異常関連

### 1. 状態異常の上書き

```python
# 既に状態異常がある場合
if pokemon.ailment:
    return HandlerReturn(False)  # 新規付与失敗
```

**第9世代の変更**: でんじは（まひ）がでんきタイプに無効等

### 2. 状態異常治癒

```python
# 特性「しぜんかいふく」
def しぜんかいふく_on_switch_out(battle, ctx, value):
    """交代で状態異常治癒"""
    pokemon = ctx.source
    
    if pokemon.ailment:
        pokemon.clear_ailment()
        battle.logger.log_message(f"{pokemon.name}の状態異常が治った！")
    
    return HandlerReturn(True)
```

**注意**: 交代時=ON_SWITCH_OUT（引っ込むとき）

### 3. 状態異常の重複効果

やけど + 特性「こんじょう」等

```python
# こんじょう: やけど・まひ・どく時に攻撃1.5倍
if pokemon.ailment and pokemon.ability.name == "こんじょう":
    attack = (attack * 6144) // 4096
```

## フィールド効果関連

### 1. 天候の上書き

```python
# 新しい天候が発動
def activate_weather(battle, ctx, weather, duration):
    # 既存天候を終了
    if battle.field.weather:
        battle.field.end_weather()
    
    # 新天候開始
    battle.field.start_weather(weather, duration)
```

**注意**: 天候は1つだけ（重複なし）

### 2. 天候延長アイテム

```python
# あついいわ: はれ延長（5→8ターン）
def あついいわ_weather_extend(battle, ctx, duration):
    if ctx.weather == "はれ":
        return HandlerReturn(True, 8)
    return HandlerReturn(False, duration)
```

**タイミング**: 天候発動時に延長判定

### 3. フィールド重複

- 天候: 1つのみ
- 地形: 1つのみ
- 場の状態（リフレクター等）: 両サイド別々に複数可

### 4. フィールドカウントダウン

```python
# ターン終了時
def tick_fields(battle, ticks=1):
    """フィールド効果のカウントダウン"""
    # 天候
    if battle.field.weather:
        battle.field.weather.count -= ticks
        if battle.field.weather.count <= 0:
            battle.field.end_weather()
    
    # 地形
    if battle.field.terrain:
        battle.field.terrain.count -= ticks
        if battle.field.terrain.count <= 0:
            battle.field.end_terrain()
```

## ダメージ計算関連

### 1. 0ダメージ

```python
# 最低1ダメージ保証（通常）
damage = max(1, damage)

# ただし、特性「ふしぎなまもり」は例外
if defender.ability.name == "ふしぎなまもり" and effectiveness <= 1.0:
    damage = 0
```

### 2. HP1残し

```python
# 特性「がんじょう」「きあいのタスキ」
if pokemon.current_hp == pokemon.max_hp and damage >= pokemon.current_hp:
    damage = pokemon.current_hp - 1
    # HP1で耐える
```

### 3. ダメージ上限

```python
# HPを超えるダメージは無意味
actual_damage = min(damage, pokemon.current_hp)
```

### 4. 割合ダメージ

```python
# 「ちきゅうなげ」等（レベル=ダメージ）
damage = pokemon.level

# 「じわれ」等（一撃必殺）
damage = pokemon.current_hp  # HP全部
```

## ランク補正関連

### 1. ランク上限・下限

```python
def boost_stat(pokemon, stat, amount):
    """ランク変更（-6 ~ +6）"""
    current_rank = pokemon.stat_ranks[stat]
    new_rank = max(-6, min(6, current_rank + amount))
    pokemon.stat_ranks[stat] = new_rank
```

**注意**: ±6を超えない

### 2. ランク無視

```python
# 急所ヒット時
# - 攻撃側の攻撃ランク下降無視
# - 防御側の防御ランク上昇無視

if is_critical:
    attack_rank = max(0, attack_rank)
    defense_rank = min(0, defense_rank)
```

### 3. 能力リセット

```python
# 交代でリセット
def bench_reset(pokemon):
    """ベンチに戻ったときのリセット"""
    pokemon.stat_ranks = {stat: 0 for stat in STATS}
    pokemon.clear_volatiles()
```

## 揮発性状態関連

### 1. 複数同時保持

```python
# 揮発性状態は複数可
pokemon.volatiles = {
    "みがわり": Volatile(count=None, value=50),
    "アンコール": Volatile(count=3, value="たいあたり"),
}
```

### 2. カウントvsバリュー

```python
class Volatile:
    count: int | None  # 継続ターン（None=無制限）
    value: Any         # 関連値（HP、技名等）
```

### 3. 交代でクリア

```python
def bench_reset(pokemon):
    """揮発性状態は交代でクリア"""
    pokemon.clear_volatiles()
```

**例外**: 一部の揮発性状態は残る可能性（要確認）

## 優先度関連

### 1. 優先度の比較

```
+5: てだすけ
+4: マジックコート
+3: ねこだまし、フェイント
+2: しんそく、アクアジェット（特性加速時）
+1: でんこうせっか、アクアジェット
 0: 通常技
-1: 
-2: 
-3: きあいパンチ
-4: ゆきなだれ、カウンター
-5: トリックルーム
-6: ほえる、ふきとばし
-7: 
```

### 2. 同優先度の行動順

```
1. 優先度降順
2. 素早さ降順
3. 同速ランダム
```

### 3. トリックルーム

```python
# トリックルーム中は素早さ逆転
if battle.field.has_effect("トリックルーム"):
    speed_order.reverse()
```

## 特性無効化

### 1. かたやぶり系

```python
# かたやぶり、ターボブレイズ、テラボルテージ
if attacker.ability.name in ["かたやぶり", "ターボブレイズ", "テラボルテージ"]:
    # 相手の特性無効
    ignore_defender_ability = True
```

### 2. かがくへんかガス

```python
# 場にいる間、全員の特性無効
# TODO: 実装複雑（全体に影響）
```

## テラスタル関連

**TODO**: 第9世代の主要機能だが、実装は別途

- タイプ変更
- テラバースト
- テラスタル補正（タイプ一致1.5倍）

## その他

### 1. みがわり貫通

一部の技（音技等）はみがわりを貫通

```python
# みがわり貫通技リスト
SUBSTITUTE_BYPASS_MOVES = ["ハイパーボイス", "ほえる", ...]

if move.name in SUBSTITUTE_BYPASS_MOVES:
    bypass_substitute = True
```

### 2. 接触技判定

```python
# 接触技かどうか
if move.contact:
    # 特性「せいでんき」等が発動
```

### 3. PP切れ

```python
# 技のPP
if move_pp <= 0:
    # わるあがき
    use_struggle()
```

## 最新エッジケース（随時追記）

<!-- 新しいエッジケースはここに追記 -->
