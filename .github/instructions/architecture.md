# アーキテクチャ詳細

> **前提条件**: [`project_context.md`](project_context.md) を読了していること。

本ドキュメントは、プロジェクトの詳細なアーキテクチャ設計を説明する。

> **重要**: 作用の実装場所については [`effect_hierarchy.md`](effect_hierarchy.md) を参照してください。

---

## イベント駆動システム

### 中核: EventManager

[`core/event.py`](../../src/jpoke/core/event.py) が全イベント処理を管理します。

**主要メソッド**:
- `fire_event()`: イベント発火
- `register_handler()`: ハンドラ登録
- `unregister_handler()`: ハンドラ解除

### HandlerReturn

ハンドラ関数は必ず `HandlerReturn` を返します：

```python
@dataclass
class HandlerReturn:
    success: bool               # 処理が成功したか
    value: Any = None           # ダメージ補正などの値
    control: HandlerResult = None  # イベント制御フラグ

# control の種類
HandlerResult.BLOCK      # 以降のハンドラをブロック
HandlerResult.INTERRUPT  # イベント全体を中断
```

---

## Handler 派生クラス

[`handlers/`](../../src/jpoke/handlers/) 配下には、用途別の Handler 派生クラスがあります：

### AbilityHandler

```python
# 特性専用
AbilityHandler(
    func,
    subject_spec="target:foe",
    source_type="ability"           # 自動設定
    log="on_success"                # デフォルト
)
```

### ItemHandler

```python
# アイテム専用
ItemHandler(
    func,
    subject_spec="source:self",
    source_type="item"              # 自動設定
    log="on_success"                # デフォルト
)
```

### AilmentHandler

```python
# 状態異常専用
AilmentHandler(
    func,
    subject_spec="source:self",
    source_type="ailment"           # 自動設定
    log="always"                    # デフォルト（常にログ）
)
```

### VolatileHandler

```python
# 揮発性状態専用
VolatileHandler(
    func,
    subject_spec="source:self",
    source_type="volatile"          # 自動設定
    log="on_success"                # デフォルト
)
```

---

## Battle クラスの設計

### 責務分離（ファサードパターン）

[`Battle`](../../src/jpoke/core/battle.py) クラスは以下のマネージャーを統括：

- **MoveExecutor**: 技実行処理
- **SwitchManager**: 交代処理
- **TurnController**: ターン進行
- **EventManager**: イベント管理
- **FieldManager**: フィールド状態管理
- **Logger**: ログ出力

### MoveExecutor - 技実行

```python
class MoveExecutor:
    def run_move(self, move: Move, user: Pokemon, target: Pokemon):
        """
        1. 技の発動前処理
        2. 命中判定
        3. ダメージ計算
        4. 状態異常・揮発性状態の付与
        5. イベント発火
        """
```

### SwitchManager - 交代処理

```python
class SwitchManager:
    def run_switch(self, pokemon: Pokemon):
        """通常の交代処理"""
    
    def run_initial_switch(self):
        """バトル開始時の初期選出"""
    
    def run_interrupt_switch(self):
        """割り込み交代（だっしゅつボタンなど）"""
    
    def run_faint_switch(self, fainted_pokemon: Pokemon):
        """瀕死ポケモンの自動交代"""
```

### TurnController - ターン進行

```python
class TurnController:
    def advance_turn(self):
        """
        1. 両プレイヤーからコマンド取得
        2. スピード計算
        3. 実行順序を決定
        4. 技実行 → 交代処理
        5. ターン終了イベント
        """
```

### EventContext - イベントコンテキスト

EventContext は内部的には `source`/`target` のみを保持しますが、`attacker`/`defender` での指定・アクセスも可能です：

```python
class EventContext:
    source: Pokemon | None     # イベントの発生源
    target: Pokemon | None     # イベントの対象
    
    # source/target のエイリアス（プロパティ）
    @property
    def attacker(self) -> Pokemon | None:
        return self.source
    
    @property
    def defender(self) -> Pokemon | None:
        return self.target
```

**重要な使い分けルール**:

| コンテキスト | 使用する属性 | 理由 |
|------------|------------|------|
| **ダメージ計算系イベント** | `attacker`, `defender` | 攻撃/防御の役割が明確 |
| **その他のイベント** | `source`, `target` | 一般的な発生源/対象の関係 |

**ダメージ計算系イベント**:
- `ON_CALC_POWER_MODIFIER` - 技威力補正
- `ON_CALC_ATK_MODIFIER` - 攻撃力補正
- `ON_CALC_DEF_MODIFIER` - 防御力補正
- `ON_CALC_ATK_TYPE_MODIFIER` - 攻撃タイプ補正
- `ON_CALC_DEF_TYPE_MODIFIER` - 防御タイプ補正
- `ON_CALC_DAMAGE_MODIFIER` - ダメージ補正

**Handler の subject_spec は使用する属性名と一致させる**:

```python
# ✅ 正しい例（ダメージ計算）
Event.ON_CALC_POWER_MODIFIER: Handler(
    はれ_power_modifier,
    subject_spec="attacker:self",  # attacker を使用
    log="never",
)

# ✅ 正しい例（その他）
Event.ON_SWITCH_IN: Handler(
    いかく,
    subject_spec="source:self",  # source を使用
    log="on_success",
)

# ❌ 間違った例
Event.ON_CALC_POWER_MODIFIER: Handler(
    はれ_power_modifier,
    subject_spec="source:self",  # ダメージ計算では attacker を使うべき
    log="never",
)
```

---

## Pokemon の状態管理

### 基本構造

[`Pokemon`](../../src/jpoke/model/pokemon.py) クラスは以下を管理：

- **基本ステータス**: HP、攻撃、防御、特攻、特防、素早さ
- **ランク補正**: -6 〜 +6
- **状態異常**: 毒、まひ、やけど、ねむり、こおり
- **揮発性状態**: みがわり、アンコール、こんらんなど
- **特性・アイテム**: 現在保持している特性とアイテム

### ライフサイクル

#### init_game() - ゲーム開始

```python
def init_game(self):
    """
    HP初期化、状態異常クリア、
    ランクリセット、ハンドラ登録
    """
```

#### bench_reset() - ベンチに戻った

```python
def bench_reset(self):
    """
    ランクをリセット、
    揮発性状態をクリア、
    一時状態をリセット
    """
```

#### switch_in() - 場に出た

```python
def switch_in(self, battle: Battle):
    """
    ハンドラ登録、
    特性・アイテム・状態異常のイベント発火
    """
```

#### switch_out() - 場から引っ込んだ

```python
def switch_out(self):
    """ハンドラ解除"""
```

### PokemonStats - ステータス計算

ステータスの計算は [`PokemonStats`](../../src/jpoke/model/stats.py) に委譲されます：

```python
class PokemonStats:
    def get_attack(self) -> int:
        """攻撃力を計算（ランク補正含む）"""
    
    def get_defense(self) -> int:
        """防御力を計算（ランク補正含む）"""
    
    def apply_rank_change(self, stat: Stat, change: int):
        """ランクを変更（-6 〜 +6 に制限）"""
```

---

## 状態異常と揮発性状態

### Ailment - 状態異常

```python
class Ailment(GameEffect):
    # 状態異常は1つのみ
    count: int  # 継続ターン数
    
    def bench_reset(self):
        """count をリセット（状態自体は維持）"""
```

**例**: 毒（どく）、まひ、ねむり、やけど、こおり

### Volatile - 揮発性状態

```python
class Volatile(GameEffect):
    # 複数の揮発性状態を同時保持可能
    count: int  # 継続ターン数
    value: Any  # 状態に紐づく数値（みがわりのHP等）
    
    def is_active(self) -> bool:
        return self.count > 0
```

**例**: みがわり、アンコール、ちょうはつ、やどりぎのタネ、こんらん

### 揮発性状態の実装例

```python
# data/volatile.py
"みがわり": VolatileData(
    handlers={
        Event.ON_BEFORE_DAMAGE: VolatileHandler(
            func=みがわり,
            subject_spec="source:self",
            priority=50,
            log="on_success"
        )
    }
),

# handlers/volatile.py
def みがわり(battle: Battle, ctx: EventContext, value: Any):
    """みがわりがダメージを肩代わりする"""
    substitute = ctx.defender.volatiles.get("みがわり")
    if not substitute or not substitute.is_active():
        return HandlerReturn(False)
    
    # みがわりのHPを減らす
    substitute.value -= value
    if substitute.value <= 0:
        ctx.defender.remove_volatile("みがわり")
        battle.logger.log(f"{ctx.defender.name}のみがわりが壊れた！")
        return HandlerReturn(True, 0, HandlerResult.BLOCK)
    
    return HandlerReturn(True, 0, HandlerResult.BLOCK)
```

---

## ダメージ計算（damage.py）

ダメージ計算は複数の要因を考慮します：

```python
def calculate_damage(
    attacker: Pokemon,
    defender: Pokemon,
    move: Move,
    battle: Battle
) -> int:
    """
    1. 基本ダメージ = (攻撃力 * 技の威力 / 防御力 + 2) * 0.85 ~ 1.0
    2. タイプ相性 * 乱数
    3. 特性による補正（いかくなど）
    4. アイテムによる補正
    5. 天気/フィールドによる補正
    6. ランク補正
    """
```

---

## ログシステム（logger.py）

[`Logger`](../../src/jpoke/core/logger.py) はバトルログを管理します：

```python
class Logger:
    def log(self, message: str):
        """通常ログ"""
    
    def log_critical(self, message: str):
        """重要ログ（赤色）"""
    
    def log_debug(self, message: str):
        """デバッグログ（グレー）"""
```

---

## フィールド管理（field_manager.py）

### WeatherManager - 天気

```python
# 天気の種類
"sunny"      # 晴れ
"rainy"      # 雨
"sandstorm"  # 砂嵐
"hail"       # あられ
```

### TerrainManager - 地形

```python
# 地形の種類
"electric"   # エレキフィールド
"grassy"     # グラスフィールド
"misty"      # ミストフィールド
"psychic"    # サイコフィールド
```

### SideFieldManager - 場の状態

```python
# 場の状態
"reflect"         # リフレクター
"light_screen"    # ライトスクリーン
"spikes"          # まきびし
"stealth_rock"    # ステルスロック
```

---

## 複数効果の相互作用

### 優先度制御

複数のハンドラが同じイベントで発動する場合：

```python
# EventManager._sort_handlers() で以下の順序でソート
1. priority が小さい順
2. 同じなら素早さが大きい順
```

### RoleSpec による対象指定

```python
"source:self"   # 自分（効果の発動源）
"source:foe"    # 相手（効果の発動源の相手）
"target:self"   # 自分（効果の対象）
"target:foe"    # 相手（効果の対象）
"attacker:*"    # 攻撃側（どちらか）
"defender:*"    # 防御側（どちらか）
```

---

## コピー戦略

### fast_copy() - 高速コピー

```python
# 特定のキーのみ deepcopy
battle_copy = fast_copy(
    battle,
    keys_to_deepcopy=[
        "players",
        "move_executor",
        "turn_controller"
    ]
)
```

### update_reference() - 参照更新

deepcopy 後は、内部参照を新オブジェクトに付け替える：

```python
battle_copy.update_reference()
# Battle が持つ各マネージャーの battle 参照を更新
```

---

## 型定義（utils/type_defs.py）

```python
# ロール指定
RoleSpec = Literal["source:self", "source:foe", "target:self", ...]

# 効果の出典
EffectSource = Literal["ability", "item", "move", "ailment", "volatile"]

# ログポリシー
LogPolicy = Literal["always", "on_success", "on_failure", "never"]

# ゲーム定数
Stat = Literal["hp", "attack", "defense", "sp_atk", "sp_def", "speed"]
Type = Literal["ノーマル", "ほのお", "みず", ...]
Weather = Literal["sunny", "rainy", "sandstorm", "hail"]
```

---

## 関連ファイル解読順序（詳細）

実装を始める前に、以下の順序でファイルを理解してください：

1. **[`utils/type_defs.py`](../../src/jpoke/utils/type_defs.py)** - 型定義
2. **[`utils/enums/`](../../src/jpoke/utils/enums/)** - Event, Command などの enum
3. **[`utils/constants.py`](../../src/jpoke/utils/constants.py)** - ゲーム定数
4. **[`model/stats.py`](../../src/jpoke/model/stats.py)** - ステータス計算
5. **[`model/effect.py`](../../src/jpoke/model/effect.py)** - GameEffect 基底クラス
6. **[`model/ailment.py`](../../src/jpoke/model/ailment.py)** - 状態異常管理
7. **[`model/volatile.py`](../../src/jpoke/model/volatile.py)** - 揮発性状態管理
8. **[`model/pokemon.py`](../../src/jpoke/model/pokemon.py)** - Pokemon クラス
9. **[`core/event.py`](../../src/jpoke/core/event.py)** - イベントシステム
10. **[`core/move_executor.py`](../../src/jpoke/core/move_executor.py)** - 技実行
11. **[`core/switch_manager.py`](../../src/jpoke/core/switch_manager.py)** - 交代処理
12. **[`core/turn_controller.py`](../../src/jpoke/core/turn_controller.py)** - ターン進行
13. **[`core/battle.py`](../../src/jpoke/core/battle.py)** - Battle ファサード
14. **[`data/models.py`](../../src/jpoke/data/models.py)** - データ構造定義
15. **[`handlers/*.py`](../../src/jpoke/handlers/)** - ハンドラ実装

---

## 開発時のベストプラクティス

### ✅ 推奨

- **HandlerReturn を必ず返す** - ハンドラ関数は必ず HandlerReturn 型を返す
- **名前付き関数** - Lambda ではなく名前付き関数で実装（デバッグが容易）
- **RoleSpec を正確に** - `"role:side"` 形式を守る
- **派生クラスを活用** - AbilityHandler, ItemHandler など
- **ステータス計算は PokemonStats に委譲** - [`Pokemon.update_stats()`](../../src/jpoke/model/pokemon.py) で対応
- **GameEffect を継承した処理は Event と Handler で実装** - 対戦に影響を与える処理（特性、アイテム、状態異常、揮発性状態など）は、可能な限り Event と Handler の組み合わせとして実装する

### ❌ 避けるべき

- **Any 型の多用** - 型ヒントを正確に
- **グローバル変数** - 参照追跡が困難
- **直接的なミュータブル修正** - イベントハンドラ経由で統一
- **複雑な Lambda** - `<lambda>` としかスタックトレースに表示されない

---

## エラーハンドリング

### 例外処理の基本方針

```python
# ❌ 避けるべき: 例外を握りつぶす
try:
    handler_func(battle, ctx, value)
except Exception:
    pass

# ✅ 推奨: ログに記録して適切に処理
try:
    handler_func(battle, ctx, value)
except ValueError as e:
    battle.logger.log_critical(f"Invalid value: {e}")
    return HandlerReturn(False)
except Exception as e:
    battle.logger.log_critical(f"Unexpected error in handler: {e}")
    raise
```

### バリデーション

```python
# ハンドラ関数内でのバリデーション例
def 特性ハンドラ(battle: Battle, ctx: EventContext, value: Any):
    if ctx.source is None:
        battle.logger.log_debug("source is None, skipping")
        return HandlerReturn(False)
    
    if not isinstance(value, int):
        battle.logger.log_critical(f"Expected int, got {type(value)}")
        return HandlerReturn(False)
    
    # 正常処理
    return HandlerReturn(True)
```

---

## デバッグ情報の活用

### ログレベル

Handler の `log` パラメータで制御：

```python
"always"       # 常にログ出力
"on_success"   # 成功時のみ
"on_failure"   # 失敗時のみ
"never"        # ログなし
```

### スタックトレース

デバッグ時にスタックトレースが有効になるよう、**名前付き関数を使用**：

```python
# ✅ スタックトレースに関数名が表示される
def 特性A(battle, ctx, value):
    ...

# ❌ スタックトレースに <lambda> としか表示されない
lambda battle, ctx, value: ...
```

---

## 次のステップ

- **作用のヒエラルキー**: [`effect_hierarchy.md`](effect_hierarchy.md) を参照
- **実装フロー**: [`agents/workflow.md`](agents/workflow.md) を参照
- **複数機能の並列実装**: [`agents/05_research.md`](agents/05_research.md) を参照
