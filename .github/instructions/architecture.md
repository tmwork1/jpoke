# アーキテクチャ詳細

前提: [`project_context.md`](project_context.md) を読了済み。
**実装場所の判断は [`implementation_principles.md`](implementation_principles.md) 参照。**

## イベント駆動システム

### イベントManager
`core/event.py` が全イベント処理を管理。

**主要メソッド**: `fire_イベント()`, `register_handler()`, `unregister_handler()`

### HandlerReturn
```python
class HandlerReturn(NamedTuple):
    success: bool | None = None  # 自動ログ判定用（未指定可）
    value: Any = None            # 補正値等（イベントによる）
    stop_event: bool = False     # イベント処理を停止するか
```

**使用例**:
```python
# 成功（補正なし）
return HandlerReturn(True)

# 成功（補正あり）
return HandlerReturn(True, modified_value)

# 失敗
return HandlerReturn(False)

# 成功＆イベント停止
return HandlerReturn(True, stop_event=True)
```

## Handler 派生クラス

`handlers/` 配下の用途別クラス:

```python
# AbilityHandler - 特性専用 (source_type="ability" 自動設定)
# ItemHandler - アイテム専用 (source_type="item" 自動設定)
# AilmentHandler - 状態異常専用 (source_type="ailment", log="always")
# VolatileHandler - 揮発性状態専用 (source_type="volatile")
```

## Battle クラス設計（ファサード）

`Battle` (`core/battle.py`) はマネージャーを統括するファサードクラス:

**主要マネージャー**:
- **EventManager**: イベント駆動システム（`core/event.py`）
- **MoveExecutor**: 技実行処理（`core/move_executor.py`）
- **TurnController**: ターン進行制御（`core/turn.py`）
- **SwitchManager**: 交代処理（`core/switch.py`）
- **SpeedCalculator**: 行動順計算（`core/speed.py`）
- **DamageCalculator**: ダメージ計算（`core/damage.py`）

**フィールドマネージャー**（`core/field_manager.py`）:
- **WeatherManager**: 天候管理
- **TerrainManager**: 地形管理
- **GlobalFieldManager**: 全体場の状態管理
- **SideFieldManager**: サイド場の状態管理（2つ: 味方/相手）

**ログ管理**:
- **EventLogger**: イベントログ（`core/event_logger.py`）
- **CommandLogger**: コマンドログ（`core/command_logger.py`）

**プレイヤー管理**:
- **Player**: プレイヤー情報（`core/player.py`）

## RoleSpec の使い分け

`BattleContext` は内部的に `source`/`target` として保持し、`attacker`/`defender` はそのエイリアスです。

| イベント種類 | 使用属性 | 慣例 | 備考 |
|------------|---------|------|------|
| ダメージ計算 | `attacker`, `defender` | attacker/defender | ON_CALC_*_MODIFIER |
| その他 | `source`, `target` | source/target | ON_SWITCH_IN, ON_TURN_END |

**内部的な関係**: `source == attacker`, `target == defender`

**重要**: `subject_spec` は イベントContext 属性名と一致させる。

```python
# ダメージ計算（慣例的に attacker/defender を使用）
Handler(func, subject_spec="attacker:self")  # ctx.attacker 使用

# その他イベント（慣例的に source/target を使用）
Handler(func, subject_spec="source:self")    # ctx.source 使用

# どちらでも動作（内部的には同じ）
Handler(func, subject_spec="source:self")    # ctx.source または ctx.attacker
Handler(func, subject_spec="attacker:self")  # ctx.attacker または ctx.source
```

## Pokemon 状態管理

`Pokemon` (`model/pokemon.py`) の管理対象:
- 基本ステータス (HP, 攻撃等)
- ランク補正 (-6 ~ +6)
- 状態異常 (1つのみ)
- 揮発性状態 (複数可)
- 特性アイテム

### ライフサイクル
```python
init_game()      # ゲーム開始: HP初期化、ハンドラ登録
bench_reset()    # ベンチ: ランク/揮発性リセット
switch_in()      # 場に出る: ハンドラ登録、イベント発火
switch_out()     # 引っ込む: ハンドラ解除
```

## 状態異常と揮発性状態

### Ailment (状態異常)
- 1つのみ保持
- `count`: 継続ターン数
- 例: どく、まひ、やけど

### Volatile (揮発性状態)
- 複数同時保持可
- `count`: 継続ターン数
- `value`: 状態に紐づく値（みがわりのHPなど）
- 例: みがわり、アンコール、ちょうはつ

**揮発性状態の管理**:
```python
# 揮発性状態の付与
pokemon.set_volatile("みがわり", count=None, value=substitute_hp)

# 揮発性状態の取得
substitute = pokemon.volatiles.get("みがわり")
if substitute and substitute.is_active():
    hp = substitute.value  # みがわりのHP

# 揮発性状態の削除
pokemon.remove_volatile("みがわり")
```

**揮発性状態実装例**:
```python
def みがわり_on_before_damage(battle: Battle, ctx: BattleContext, value: Any):
    """みがわりがダメージを肩代わりする"""
    substitute = ctx.defender.volatiles.get("みがわり")
    if not substitute or not substitute.is_active():
        return HandlerReturn(False)
    
    # みがわりのHPを減らす
    substitute.value -= value
    
    if substitute.value <= 0:
        ctx.defender.remove_volatile("みがわり")
        battle.logger.log_message(f"{ctx.defender.name}のみがわりが壊れた！")
        return HandlerReturn(True, stop_event=True)
    
    return HandlerReturn(True, stop_event=True)
```

## ダメージ計算

`core/damage.py`:
1. 基本ダメージ = (攻撃力 * 威力 / 防御力 + 2) * 乱数
2. タイプ相性
3. 特性アイテム天候ランク補正

## フィールド管理

`core/field_manager.py` はフィールド効果を統一的に管理:

### マネージャークラス

1. **WeatherManager**: 天候（排他的）
   - 同時に1つのみ存在
   - 例: はれ、あめ、すなあらし、ゆき、あられ

2. **TerrainManager**: 地形（排他的）
   - 同時に1つのみ存在
   - 例: エレキフィールド、グラスフィールド、サイコフィールド、ミストフィールド

3. **GlobalFieldManager**: 全体場の状態（スタック可能）
   - 複数同時存在可能
   - 例: トリックルーム、ワンダールーム、マジックルーム、じゅうりょく

4. **SideFieldManager**: サイド場の状態（スタック可能、各サイド独立）
   - 味方側・相手側それぞれで複数同時存在可能
   - 例: リフレクター、ひかりのかべ、ステルスロック、まきびし、おいかぜ

### 基本操作

```python
# 天候の設定
battle.weather.set("はれ", duration=5)

# 地形の設定
battle.terrain.set("エレキフィールド", duration=5)

# 全体場の状態の設定
battle.global_field.set("トリックルーム", duration=5)

# サイド場の状態の設定（味方側）
battle.get_side_field(player).set("リフレクター", duration=5)

# 状態の確認
if battle.weather.is_active("はれ"):
    # はれの効果

# カウントの取得
remaining = battle.weather.get_count("はれ")
```

## 優先度制御

同一イベントの複数ハンドラ:
1. `priority` 昇順
2. 素早さ降順 (Player の場合は active Pokemon に変換)

## RoleSpec 一覧

```python
"source:self"    # 自分（発動源）
"source:foe"     # 相手（発動源の相手）
"target:self"    # 自分（対象）
"target:foe"     # 相手（対象）
"attacker:*"     # 攻撃側
"defender:*"     # 防御側
```

## コピー戦略

```python
# 高速コピー（特定キーのみ deepcopy）
battle_copy = fast_copy(battle, keys_to_deepcopy=["players"])
battle_copy.update_reference()  # 内部参照を更新
```

## 型定義

`utils/type_defs.py`:
```python
RoleSpec = Literal["source:self", ...]
EffectSource = Literal["ability", "item", "move", "ailment", "volatile"]
LogPolicy = Literal["always", "on_success", "on_failure", "never"]
Stat = Literal["hp", "attack", "defense", "sp_atk", "sp_def", "speed"]
```

## ファイル読解順序

1. `utils/type_defs.py` - 型定義
2. `utils/enums/` - イベント, Command
3. `utils/constants.py` - 定数
4. `model/stats.py` - ステータス
5. `model/effect.py` - 基底クラス
6. `model/ailment.py`, `volatile.py` - 状態管理
7. `model/pokemon.py` - Pokemon
8. `core/event.py` - イベント
9. `core/move_executor.py`, `switch_manager.py`, `turn_controller.py`
10. `core/battle.py` - ファサード
11. `data/models.py` - データ構造
12. `handlers/*.py` - ハンドラ実装

## ベストプラクティス

### 推奨
- HandlerReturn を必ず返す
- 名前付き関数（デバッグ容易）
- RoleSpec を正確に
- 派生クラス活用
- GameEffect 処理は イベント/Handler で実装

### 回避
- Any 型の多用
- グローバル変数
- 複雑な Lambda
- 例外の握りつぶし

## エラーハンドリング

```python
# 推奨
try:
    handler_func(battle, ctx, value)
except ValueError as e:
    battle.logger.log_critical(f"Invalid value: {e}")
    return HandlerReturn(False)
except Exception as e:
    battle.logger.log_critical(f"Unexpected error: {e}")
    raise
```

## ログレベル

```python
log="always"       # 常時
log="on_success"   # 成功時
log="on_failure"   # 失敗時
log="never"        # なし
```

## 次のステップ

- 実装原則: [`implementation_principles.md`](implementation_principles.md)
- 開発ワークフロー: [`workflow.md`](workflow.md)
- 実装パターン: [`knowledge/patterns.md`](knowledge/patterns.md)
