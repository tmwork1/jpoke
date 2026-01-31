# アーキテクチャ詳細

> **前提条件**: `project_context.md` を読了していること。

本ドキュメントは、プロジェクトの詳細なアーキテクチャ設計を説明する。

---

## イベント駆動システム

### 中核: EventManager

**`core/event.py`** の `EventManager` がシステムの中心です。

```python
class EventManager:
    def fire(self, event: Event, ctx: EventContext) -> EventResult:
        """
        1. 登録されたハンドラを優先度でソート
        2. 各ハンドラを実行
        3. 結果を集約して返す
        """
```

### Handler の構造

```python
@dataclass
class Handler:
    func: Callable              # 実行する関数
    subject_spec: RoleSpec      # "role:side" 形式
    source_type: EffectSource   # "ability" | "item" | "move" | "ailment"
    log: LogPolicy              # ログ出力方法
    priority: int = 100         # 優先度
```

### HandlerReturn

ハンドラ関数は必ず `HandlerReturn` を返します：

```python
@dataclass
class HandlerReturn:
    success: bool               # 処理が成功したか
    value: Any = None           # ダメージ補正などの値
    control: HandlerResult = None  # イベント制御フラグ
```

### EventContext

ハンドラ内で利用可能な情報：

```python
@dataclass
class EventContext:
    battle: Battle
    event: Event
    source: Pokemon             # 効果の発動源
    target: Pokemon             # 効果の対象
    attacker: Pokemon           # 攻撃側
    defender: Pokemon           # 防御側
    value: Any                  # イベント固有データ
```

---

## Handler 派生クラス

`handlers/` 配下には、用途別の Handler 派生クラスがあります：

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

```
Battle（ファサード）
  ├── move_executor: MoveExecutor   # 技実行
  ├── switch_manager: SwitchManager # 交代処理
  ├── turn_controller: TurnController # ターン進行
  ├── field_manager: FieldManager   # フィールド管理
  └── logger: Logger                # ログ管理
```

Battle クラス自体は各マネージャーへの**ファサードメソッド**を提供：

```python
# Battle 経由の呼び出し（推奨）
battle.run_move(move, user, target)
battle.run_switch(pokemon)
battle.advance_turn()

# 内部では委譲
def run_move(self, move, user, target):
    return self.move_executor.run_move(move, user, target)
```

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

---

## Pokemon の状態管理

### 基本構造

```python
class Pokemon:
    # 基本データ
    name: str
    level: int
    ability: Ability
    item: Item
    moves: list[Move]
    nature: Nature
    
    # バトル状態
    hp: int
    ailment: Ailment              # 状態異常（1つのみ）
    volatiles: dict[str, Volatile] # 揮発性状態（複数可能）
    rank: dict[Stat, int]         # ランク変化（+-7段階）
    
    # 場限定の状態
    is_terastallized: bool
    
    # ステータス計算
    _stats_manager: PokemonStats
```

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

```python
class PokemonStats:
    _stats: list[int]      # [HP, 攻撃, 防御, 特攻, 特防, 素早さ]
    _indiv: list[int]      # 個体値
    _effort: list[int]     # 努力値
    
    def update_stats(self, level, base, nature):
        """
        種族値、個体値、努力値、性格補正から
        ステータス実数値を再計算
        """
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

### 3種類のログ

```python
@dataclass
class EventLog:
    text: str  # イベント説明

@dataclass
class CommandLog:
    command: Command  # プレイヤーコマンド

@dataclass
class DamageLog:
    damage: int  # ダメージ量
```

### ログアクセスの推奨方法

```python
# Battle 経由（推奨）
battle.add_event_log(source_pokemon, "メッセージ")
logs = battle.get_event_logs(turn)  # dict[Player, list[str]]

# Logger 直接（低レベルAPI）
battle.logger.add_event_log(turn, idx, "メッセージ")
logs = battle.logger.get_event_logs(turn, idx)  # list[str]
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
"spikes"          # ステルスロック
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
"source:foe"    # 相手（効果の発動源）
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
EffectSource = Literal["ability", "item", "move", "ailment"]

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

1. **`utils/type_defs.py`** - 型定義
2. **`utils/enums/`** - Event, Command などの enum
3. **`utils/constants.py`** - ゲーム定数
4. **`model/stats.py`** - ステータス計算
5. **`model/effect.py`** - GameEffect 基底クラス
6. **`model/ailment.py`** - 状態異常管理
7. **`model/volatile.py`** - 揮発性状態管理
8. **`model/pokemon.py`** - Pokemon クラス
9. **`core/event.py`** - イベントシステム
10. **`core/move_executor.py`** - 技実行
11. **`core/switch_manager.py`** - 交代処理
12. **`core/turn_controller.py`** - ターン進行
13. **`core/battle.py`** - Battle ファサード
14. **`data/models.py`** - データ構造定義
15. **`handlers/*.py`** - ハンドラ実装

---

## 開発時のベストプラクティス

### ✅ 推奨

- **HandlerReturn を必ず返す** - ハンドラ関数は必ず HandlerReturn 型を返す
- **名前付き関数** - Lambda ではなく名前付き関数で実装（デバッグが容易）
- **RoleSpec を正確に** - `"role:side"` 形式を守る
- **派生クラスを活用** - AbilityHandler, ItemHandler など
- **ステータス計算は PokemonStats に委譲** - Pokemon.update_stats() で対応

### ❌ 避けるべき

- **Any 型の多用** - 型ヒントを正確に
- **グローバル変数** - 参照追跡が困難
- **直接的なミュータブル修正** - イベントハンドラ経由で統一
- **複雑な Lambda** - `<lambda>` としかスタックトレースに表示されない

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

- 実装フローは `.github/instructions/agents/workflow.md` を参照
- 複数機能の並列実装は `.github/instructions/agents/05_research.md` を参照
