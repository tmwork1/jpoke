`````instructions
````instructions
# Copilot 指示

## 基本方針
- **第9世代（SV）仕様準拠**: 第9世代で実装されていない要素は見送る
- **シングル対戦のみ**: ダブルバトルは対象外
- **イベント駆動アーキテクチャ**: すべての効果はイベント/Handlerで実装
- **完遂主義**: コード追加・修正時はテスト・レビューまで完遂
- **推測継続**: ユーザへの確認はせず、不明点は推測して進める
- **一貫性重視**: 既存コード・テストパターンを踏襲

## 核心概念

### イベント駆動
- **EventManager**: `src/jpoke/core/event.py` が全イベント処理を管理
- **Handler**: 全効果をHandlerで実装（`src/jpoke/handlers/`）
- **派生クラス**: AbilityHandler, ItemHandler, MoveHandler, AilmentHandler, VolatileHandler

### RoleSpec（対象指定）
```python
# ダメージ計算イベント
"attacker:self"   # 攻撃側自身
"defender:self"   # 防御側自身

# その他イベント
"source:self"     # 発動源自身
"target:self"     # 対象自身
"source:foe"      # 発動源の相手
"target:foe"      # 対象の相手
```

### HandlerReturn
```python
HandlerReturn(
    success=bool,              # 処理成功したか
    value=Any,                 # 補正値等（イベントによる）
    control=HandlerResult,     # BLOCK/INTERRUPT（処理制御）
)
```

### ダメージ計算（4096基準）
```python
# 浮動小数点を避けて整数演算
1.5倍 = (value * 6144) // 4096
0.5倍 = (value * 2048) // 4096
2倍   = (value * 8192) // 4096
```

## ファイル構成
```
src/jpoke/
  core/          # event.py, battle.py, damage.py（システム中核）
  model/         # pokemon.py, stats.py, ailment.py, volatile.py
  data/          # ability.py, move.py, item.py（Pydantic BaseModel）
  handlers/      # 効果実装（ビジネスロジック）
    common.py    # 共通処理（activate_weather等）
  utils/         # 型定義、定数、補助機能
tests/
  test_utils.py  # テストヘルパー
  test_*.py      # 各種テスト
docs/
  spec/          # 仕様調査結果
  plan/          # 実装計画
  architecture/  # 設計文書
  checklist/     # 実装状況
  review/        # レビュー結果
.github/instructions/
  workflow.md               # 開発フロー
  implementation_principles.md  # 実装原則
  architecture.md           # システム設計
  project_context.md        # プロジェクト背景
  knowledge/                # 知見集
    patterns.md             # 実装パターン
    abilities.md            # 特性知見
    moves.md                # 技知見
    damage_calc.md          # ダメージ計算知見
    edge_cases.md           # エッジケース
    troubleshooting.md      # トラブルシューティング
```

## コーディング規約

### 型ヒント必須
```python
def handler(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ハンドラの説明
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: 入力値
    
    Returns:
        HandlerReturn(success, value, control)
    """
    return HandlerReturn(True, modified_value)
```

### Pydantic活用
```python
from pydantic import BaseModel, Field

class MoveData(BaseModel):
    name: str = Field(..., description="技名")
    power: int = Field(default=0, description="威力")
    handlers: dict[Event, Handler | list[Handler]] = Field(default_factory=dict)
```

### ロギング
```python
from jpoke.core.logger import get_logger

logger = get_logger(__name__)
logger.debug(f"計算結果: {result}")
battle.logger.log_message(f"{pokemon.name}のこうげきが上がった！")
```

## テスト規則

### ポケモン選択
第1世代の有名種（ピカチュウ、フシギダネ、ヒトカゲ等）を優先

### test_utils活用
```python
from tests.test_utils import start_battle, tick_fields, assert_field_active

battle = start_battle(
    ally=[Pokemon("ピカチュウ", ability="せいでんき", item="きあいのタスキ")],
    foe=[Pokemon("フシギダネ")],
    weather=("はれ", 5),
    terrain=("エレキフィールド", 5),
    ally_side_field={"リフレクター": 5},
    ally_volatile={"みがわり": (None, 50)},
)

# ターン進行
tick_fields(battle, ticks=3)

# フィールド確認
assert_field_active(battle, "はれ")
assert get_field_count(battle, "エレキフィールド") == 2
```

### 浮動小数点比較
```python
# ❌ NG: 完全一致
assert value == 1.5

# ✅ OK: 許容誤差
assert abs(value - 1.5) < 0.01
```

## クイックリファレンス

### Handler基本パターン
```python
# 補正値計算
def 特性_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    if not condition:
        return HandlerReturn(False)
    modified = (value * 6144) // 4096  # 1.5倍
    return HandlerReturn(True, modified)

# 状態付与
def 技_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    if ctx.defender.ailment:
        return HandlerReturn(False)
    ctx.defender.set_ailment("まひ")
    return HandlerReturn(True)

# フィールド効果
from functools import partial
from jpoke.handlers.common import activate_weather

Handler(
    partial(activate_weather, weather="はれ", duration=5),
    subject_spec="source:self",
)
```

### データ定義パターン
```python
# 特性
"特性名": AbilityData(
    name="特性名",
    handlers={
        Event.ON_SWITCH_IN: AbilityHandler(func, subject_spec="source:self"),
    }
)

# 技
"技名": MoveData(
    name="技名", type="ほのお", category="physical",
    power=90, accuracy=100, pp=15,
    handlers={
        Event.ON_HIT: MoveHandler(func, subject_spec="attacker:self"),
    }
)
```

## ワークフロー

開発フローの詳細は [`workflow.md`](instructions/workflow.md) を参照。

**基本フロー**:
```
調査 → 計画 → 設計 → 実装 → テスト → レビュー → 完了
```

**パターン別**:
- 新規実装: Phase 1（調査）から開始
- バグ修正: Phase 6（レビュー）で原因特定から開始
- リファクタ: Phase 3（設計）から開始

## タスク完了時

### 必須
1. **Dashboard更新**: `python -m jpoke.utils.dashboard` 実行
2. **README更新**: 実装済み機能を記載
3. **Checklist更新**: `docs/checklist/[カテゴリ].md` にマーク

### 知見記録
新規知見・パターンを [`knowledge/`](instructions/knowledge/) に追記:
- `patterns.md` - 実装パターン
- `abilities.md` - 特性知見
- `moves.md` - 技知見
- `damage_calc.md` - ダメージ計算知見
- `edge_cases.md` - エッジケース
- `troubleshooting.md` - トラブルシューティング

## 参考ドキュメント

### 必読
1. [`workflow.md`](instructions/workflow.md) - 開発フロー全体
2. [`implementation_principles.md`](instructions/implementation_principles.md) - 実装場所の判断基準
3. [`architecture.md`](instructions/architecture.md) - システム技術詳細
4. [`project_context.md`](instructions/project_context.md) - プロジェクト背景

### 補助
- [`knowledge/`](instructions/knowledge/) - 実装パターン・知見集
- `docs/spec/` - 仕様調査結果
- `docs/checklist/` - 実装状況
- `tests/test_utils.py` - テストヘルパー

## よくある質問

**Q: どこから始めるべき？**
A: 新規実装なら調査から。バグ修正なら原因特定から。[`workflow.md`](instructions/workflow.md) 参照。

**Q: 実装場所がわからない**
A: [`implementation_principles.md`](instructions/implementation_principles.md) で判断基準を確認。

**Q: テストが失敗したら？**
A: [`knowledge/troubleshooting.md`](instructions/knowledge/troubleshooting.md) で解決策を確認。

**Q: エッジケースは？**
A: [`knowledge/edge_cases.md`](instructions/knowledge/edge_cases.md) で特殊状況を確認。
````

`````
