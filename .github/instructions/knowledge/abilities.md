# 特性実装の知見

特性実装時の注意点・パターン・エッジケース。

## 基本方針

- **所有者原則**: 特性の効果は特性データに実装
- **イベント駆動**: 効果はイベント経由で発動
- **AbilityHandler使用**: `source_type="ability"` が自動設定される

## 実装済み特性の知見

### 発動タイミング別

#### ON_SWITCH_IN（場に出たとき）

```python
# 天候変更系（ひでり、あまふらし等）
"ひでり": AbilityData(
    handlers={
        Event.ON_SWITCH_IN: AbilityHandler(
            partial(common.activate_weather, weather="はれ", duration=8),
            subject_spec="source:self",
            log="on_success",
        )
    }
)
```

#### ON_CALC_POWER_MODIFIER（威力補正）

```python
# タイプ一致補正強化（てきおうりょく）
def てきおうりょく_power(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """タイプ一致技の威力を2倍に（通常1.5倍の代わり）"""
    move = ctx.move
    attacker = ctx.attacker
    
    # タイプ一致チェック
    if move.type not in [attacker.type1, attacker.type2]:
        return HandlerReturn(False)
    
    # 通常1.5倍(6144)を2倍(8192)に変更
    # 既に1.5倍された値を受け取るので、1.5倍から2倍への補正は (2.0/1.5) = 1.333...
    modifier = (value * 8192) // 6144
    
    return HandlerReturn(True, modifier)
```

#### ON_DAMAGE_RECEIVED（ダメージ受けた時）

接触技でまひ付与等

```python
def せいでんき_on_contact(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """接触技を受けたとき、30%の確率で相手をまひ状態にする"""
    move = ctx.move
    attacker = ctx.attacker
    defender = ctx.defender
    
    # 接触技チェック
    if not move.contact:
        return HandlerReturn(False)
    
    # 既にまひ（または他の状態異常）
    if attacker.ailment:
        return HandlerReturn(False)
    
    # 30%判定
    if random.random() > 0.3:
        return HandlerReturn(False)
    
    # まひ付与
    attacker.set_ailment("まひ")
    battle.logger.log_message(f"{attacker.name}はまひした！")
    
    return HandlerReturn(True)
```

## 複雑な特性の実装パターン

### カウンター系（なまけ等）

```python
class PokemonState:
    ability_counters: dict[str, int] = Field(default_factory=dict)

def なまけ_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """1ターンおきに行動できなくなる"""
    pokemon = ctx.source
    
    # カウンター初期化
    if "なまけ" not in pokemon.ability_counters:
        pokemon.ability_counters["なまけ"] = 0
    
    # カウンター増加
    pokemon.ability_counters["なまけ"] += 1
    
    return HandlerReturn(True)

def なまけ_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """偶数ターンは行動不可"""
    pokemon = ctx.source
    counter = pokemon.ability_counters.get("なまけ", 0)
    
    if counter % 2 == 1:
        battle.logger.log_message(f"{pokemon.name}はなまけている！")
        return HandlerReturn(True, None, HandlerResult.BLOCK)
    
    return HandlerReturn(False)
```

### フォルムチェンジ系（バトルスイッチ等）

```python
def バトルスイッチ_before_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """攻撃技使用前にブレードフォルムに変更"""
    pokemon = ctx.source
    move = ctx.move
    
    # 現在シールドフォルム かつ 攻撃技
    if pokemon.form != "シールド" or move.category == "status":
        return HandlerReturn(False)
    
    # フォルムチェンジ
    pokemon.change_form("ブレード")
    battle.logger.log_message(f"{pokemon.name}はブレードフォルムに変化した！")
    
    return HandlerReturn(True)
```

### 複数条件判定（ようりょくそ等）

```python
def ようりょくそ_speed(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """晴れ状態の時、素早さが2倍"""
    pokemon = ctx.source
    
    # 天候確認
    if not battle.field.weather or battle.field.weather.name != "はれ":
        return HandlerReturn(False)
    
    # 素早さ2倍
    modified_speed = value * 2
    
    return HandlerReturn(True, modified_speed)
```

## よくあるエッジケース

### 1. 特性無効化（かたやぶり等）

```python
def check_ability_ignored(battle: Battle, attacker: Pokemon, defender: Pokemon) -> bool:
    """特性が無効化されるかチェック"""
    # かたやぶり系特性
    if attacker.ability.name in ["かたやぶり", "ターボブレイズ", "テラボルテージ"]:
        return True
    
    # かがくへんかガス
    # TODO: 実装
    
    return False
```

### 2. 特性変更・上書き

- 特性変更時は古いハンドラを解除
- 新しい特性のハンドラを登録

```python
def change_ability(pokemon: Pokemon, new_ability: str):
    """特性変更"""
    # 古いハンドラ解除
    pokemon.unregister_handlers()
    
    # 特性変更
    pokemon.ability = get_ability_data(new_ability)
    
    # 新ハンドラ登録（場に出ている場合のみ）
    if pokemon.is_active:
        pokemon.register_handlers()
```

### 3. 特性発動の優先順位

同一イベントで複数特性が発動する場合、`priority`で制御

```python
# 先制発動
Event.ON_SWITCH_IN: AbilityHandler(func, priority=0)

# 後発発動
Event.ON_SWITCH_IN: AbilityHandler(func, priority=10)
```

## トラブルシューティング

### 特性が発動しない

**チェック項目**:
1. イベントが正しいか（ON_SWITCH_INなど）
2. RoleSpecが正しいか（source:selfなど）
3. ハンドラ登録されているか（`pokemon.register_handlers()`）
4. 条件チェックが厳しすぎないか

### 特性が重複発動

**原因**: ハンドラの二重登録

**対策**:
- `switch_out()` 時に必ず `unregister_handlers()`
- `switch_in()` 前に未登録を確認

### 補正計算がおかしい

**原因**: 浮動小数点演算

**対策**: 4096基準の整数演算を使用

```python
# ❌ NG
value * 1.5

# ✅ OK
(value * 6144) // 4096
```

## 最新知見（随時追記）

<!-- 新しい知見はここに追記 -->
