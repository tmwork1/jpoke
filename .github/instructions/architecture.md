# アーキテクチャ詳細

前提: `project_context.md` を読了済み。作用実装は `effect_hierarchy.md` 参照。

## イベント駆動システム

### イベントManager
`core/イベント.py` が全イベント処理を管理。

**主要メソッド**: `fire_イベント()`, `register_handler()`, `unregister_handler()`

### HandlerReturn
```python
@dataclass
class HandlerReturn:
    success: bool               # 処理成功
    value: Any = None           # 補正値
    control: HandlerResult = None  # BLOCK/INTERRUPT
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

`Battle` (`core/battle.py`) はマネージャーを統括:
- **MoveExecutor**: 技実行
- **TurnController**: ターン進行
- **SwitchManager**: 交代処理
- **FieldManager**: 天候/地形/場の状態
- **イベントManager**: イベント駆動
- **Logger**: ログ管理

## RoleSpec の使い分け

| イベント種類 | 使用属性 | 例 |
|------------|---------|---|
| ダメージ計算 | `attacker`, `defender` | ON_CALC_*_MODIFIER |
| その他 | `source`, `target` | ON_SWITCH_IN, ON_TURN_END |

**重要**: `subject_spec` は イベントContext 属性名と一致させる。

```python
# ダメージ計算
Handler(func, subject_spec="attacker:self")  # ctx.attacker 使用

# その他
Handler(func, subject_spec="source:self")    # ctx.source 使用
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
- `count`: 継続ターン、`value`: 関連値
- 例: みがわり、アンコール

```python
# 揮発性状態実装例
def みがわり(battle: Battle, ctx: イベントContext, value: Any):
    substitute = ctx.defender.volatiles.get("みがわり")
    if not substitute or not substitute.is_active():
        return HandlerReturn(False)
    substitute.value -= value
    if substitute.value <= 0:
        ctx.defender.remove_volatile("みがわり")
        return HandlerReturn(True, 0, HandlerResult.BLOCK)
    return HandlerReturn(True, 0, HandlerResult.BLOCK)
```

## ダメージ計算

`core/damage.py`:
1. 基本ダメージ = (攻撃力 * 威力 / 防御力 + 2) * 乱数
2. タイプ相性
3. 特性アイテム天候ランク補正

## フィールド管理

`core/field_manager.py`:
- **WeatherManager**: 天候 (はれ、あめ等)
- **TerrainManager**: 地形 (エレキフィールド等)
- **SideFieldManager**: 場の状態 (リフレクター、まきびし等)

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
8. `core/イベント.py` - イベント
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

- 作用実装: `effect_hierarchy.md`
- ワークフロー: `agents/workflow.md`
