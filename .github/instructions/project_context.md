# プロジェクトコンテキスト

## プロジェクト概要

**jpoke** はポケモンシングルバトル対戦シミュレータである。

### 基本方針

- **ポケモンの仕様は第9世代（スカーレット・バイオレット）を参照する**
- **第9世代で実装されていない技・アイテム・特性・ポケモンなどは、実装を見送る**

### 目的
- 戦闘ロジックの開発・検証
- Pokemon AI ボット開発の基盤（準備中）

### 現在の状況
- **ポケモン利用規約**: AI ボットの開発は保留中
- **対象**: シングルバトル（1v1）

---

## クイックスタート

### プロジェクト構造

```
src/jpoke/
├── core/              # バトルシステムの中核
│   ├── battle.py      # Battle クラス（ファサード）
│   ├── event.py       # イベント駆動システム
│   ├── turn_controller.py  # ターン進行管理
│   ├── move_executor.py    # 技実行処理
│   └── switch_manager.py   # 交代処理
├── model/             # ポケモンの状態管理
│   ├── pokemon.py     # Pokemon クラス
│   ├── stats.py       # ステータス計算
│   ├── ailment.py     # 状態異常
│   └── volatile.py    # 揮発性状態
├── data/              # データ定義
│   ├── ability.py     # 特性データ
│   ├── move.py        # 技データ
│   ├── item.py        # アイテムデータ
│   └── pokedex.py     # ポケモン図鑑
├── handlers/          # イベントハンドラ実装
│   ├── ability.py     # 特性ハンドラ
│   ├── move.py        # 技ハンドラ
│   ├── item.py        # アイテムハンドラ
│   └── common.py      # 汎用関数
└── utils/             # ユーティリティ
    ├── constants.py   # ゲーム定数
    ├── type_defs.py   # 型定義
    └── enums/         # Enum定義
```

---

## 核心アーキテクチャ

### 1. イベント駆動パターン

このシステムの中核は **`EventManager`** （[`core/event.py`](../../src/jpoke/core/event.py)）です。

```
バトルの各フェーズ
    ↓
イベント発火
    ↓
登録されたハンドラを実行
    ↓
各効果を適用
```

**例**: ターン開始時に「天気が変わる → 特性が発動 → ダメージが変わる」

### 2. Handler（ハンドラ）

特性・技・アイテムの効果は全て **Handler** で実装されます。

```python
# 特性「いかく」の例
def いかく(battle: Battle, ctx: EventContext, value: Any):
    # 相手の攻撃を1段階下げる
    return HandlerReturn(True, ...)

# ハンドラ登録
Event.ON_SWITCH_IN: Handler(
    func=いかく,
    subject_spec="source:foe",  # 相手が対象
    log="on_success"            # 成功時にログ
)
```

**Handler の構造**:
- `func`: 実行する関数
- `subject_spec`: 対象指定（`"role:side"` 形式）
- `source_type`: 効果の出典（`"ability"` | `"item"` | `"move"` | `"ailment"` | `"volatile"`）
- `log`: ログ出力方法（`"always"` | `"on_success"` | `"on_failure"` | `"never"`）
- `priority`: 優先度（小さいほど先に実行）

### 3. EventContext

ハンドラ内で利用可能な情報：

```python
# EventContext の主要属性
ctx.source      # 効果の発動源（Pokemon）
ctx.target      # 効果の対象（Pokemon）
ctx.attacker    # 攻撃側のPokemon（source のエイリアス）
ctx.defender    # 防御側のPokemon（target のエイリアス）
ctx.move        # 使用された技
ctx.field       # 場の状態
```

**重要**: `attacker`/`defender` は `source`/`target` のエイリアスですが、**イベントの種類によって使い分ける必要があります**：

- **ダメージ計算系イベント**: `attacker`/`defender` を使用し、`subject_spec` も `"attacker:self"` などと指定
- **その他のイベント**: `source`/`target` を使用し、`subject_spec` も `"source:self"` などと指定

詳細は [`architecture.md`](architecture.md) の「EventContext - イベントコンテキスト」セクションを参照してください。

---

## 基本的な使い方

### 新しい特性を追加する場合

#### ステップ1: [`data/ability.py`](../../src/jpoke/data/ability.py) でデータ定義

```python
ABILITIES = {
    "新特性": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: AbilityHandler(
                handler_func,
                subject_spec="source:self",
                log="on_success"
            )
        }
    )
}
```

#### ステップ2: [`handlers/ability.py`](../../src/jpoke/handlers/ability.py) でハンドラ実装

```python
def 新特性(battle: Battle, ctx: EventContext, value: Any):
    # 特性の効果を実装
    result = ...
    return HandlerReturn(result.success, result.value)
```

#### ステップ3: テストを作成

**テストは [`/tests/`](../../tests/) ディレクトリに作成し、再現性を担保する**

```python
# tests/ability.py
def test_新特性():
    battle = start_battle(...)
    # テストコード
```

---

## 重要な概念

### RoleSpec（役割指定）

ハンドラが「誰に対して」効果を与えるかを指定：

```
"role:side" 形式

role: "source", "target", "attacker", "defender"
side: "self"（自分側）, "foe"（相手側）

例:
- "source:self"  → 効果の発動源本人
- "source:foe"   → 効果の発動源の相手
- "target:self"  → 効果の対象（自分側）
- "target:foe"   → 効果の対象（相手側）
```

### Handler優先度

複数のハンドラが同じイベントで発動する場合、優先度で順序を制御：

```python
# priority が小さいほど先に実行
# 同じなら素早さが大きい順に実行
Handler(..., priority=100)
```

### LogPolicy（ログポリシー）

ハンドラのログ出力方法を制御：

```
"always"       → 常にログ出力
"on_success"   → 成功時のみ
"on_failure"   → 失敗時のみ
"never"        → ログなし
```

---

## 複雑な仕様への対応

### 複数効果の相互作用

このプロジェクトでは、複数の効果が組み合わさることを常に考慮します：

```
技「XXX」 + 特性「YYY」 + アイテム「ZZZ」
    ↓
どの順序で発動するか？
（priority で制御）
    ↓
各効果が適用
```

### ターン処理フロー

```
1. ターン開始イベント
2. 場の効果を適用
3. スピード計算
4. 攻撃順序決定
5. ポケモンAが行動
6. ポケモンBが行動
7. ターン終了処理
```

---

## 推奨される学習順序

1. **このファイル** ([`project_context.md`](project_context.md)) を読む ← 今ここ
2. **[`architecture.md`](architecture.md)** で詳細を学ぶ
3. **[`agents/workflow.md`](agents/workflow.md)** でエージェント運用を理解
4. 実装フロー例に沿ってエージェントを使う

---

## 重要なファイル一覧

### 必ず理解すべき

- **[`src/jpoke/core/event.py`](../../src/jpoke/core/event.py)** - イベント駆動の中核
- **[`src/jpoke/core/battle.py`](../../src/jpoke/core/battle.py)** - バトルシステムのファサード
- **[`src/jpoke/model/pokemon.py`](../../src/jpoke/model/pokemon.py)** - ポケモンの状態管理
- **[`src/jpoke/data/ability.py`](../../src/jpoke/data/ability.py)** - 特性定義の例

### 参考になる既存実装

- **[`src/jpoke/handlers/ability.py`](../../src/jpoke/handlers/ability.py)** - 特性ハンドラの実装例
- **[`tests/ability.py`](../../tests/ability.py)** - テストの例

---

## デバッグのコツ

```python
# ハンドラ関数は名前付きにする
# Lambda では <lambda> としかスタックトレースに表示されない

# ❌ 避けるべき
Event.ON_SWITCH_IN: Handler(
    lambda battle, ctx, value: HandlerReturn(True),
)

# ✅ 推奨
def 新特性(battle: Battle, ctx: EventContext, value: Any):
    return HandlerReturn(True)

Event.ON_SWITCH_IN: Handler(新特性, ...)
```

---

## 次のステップ

- 詳細な設計については **[`architecture.md`](architecture.md)** を参照
- 新機能の実装フローは **[`agents/workflow.md`](agents/workflow.md)** を参照
- 複数特性を実装する場合は **[`agents/05_research.md`](agents/05_research.md)** で調査
