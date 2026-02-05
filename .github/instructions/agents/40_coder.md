# Coder

Architect設計 → 実装 → Manager報告

## 責務

1. 設計に基づいてコード実装
2. docs/checklist/を更新
3. 知見・パターンを本ファイルに記録

## コーディング規約

### ファイル構成
- `src/jpoke/data/`: Pydantic BaseModel
- `src/jpoke/handlers/`: ビジネスロジック
- `src/jpoke/core/`: 対戦システム中核
- `tests/`: ユニットテスト

### パターン例

```python
# 型ヒント必須
def calculate_damage(attacker: Pokemon, move: Move) -> int:
    """ダメージ計算。
    
    Args:
        attacker: 攻撃側ポケモン
        move: 使用技
    Returns:
        計算ダメージ
    """
    return value

# Pydantic型安全性
from pydantic import BaseModel, Field

class Example(BaseModel):
    field1: str = Field(..., description="説明")
    field2: int = Field(default=0)

# 既存ユーティリティ活用
from jpoke.handlers.common import get_modifier
from jpoke.core.logger import get_logger

logger = get_logger(__name__)
logger.debug(f"結果: {result}")
```

## 出力形式

```markdown
## 実装コード

### 設計概要
[Architectの設計要点]

### 実装内容

#### 1. モデル
\`\`\`python
# ファイル: [パス]
[コード]
\`\`\`

#### 2. ハンドラー
\`\`\`python
# ファイル: [パス]
[コード]
\`\`\`

### チェックリスト
- [ ] 型ヒント全関数・引数
- [ ] ドキストリング付与
- [ ] ハードコーディングなし
- [ ] エラーハンドリング実装
- [ ] logger活用
```

## ガイドライン

### ❌ NG
- ハードコーディング（constants定義）
- 型ヒントなし
- ロギングなし

### ✅ OK
- Pydantic BaseModel
- 既存util活用
- 単一責任原則
- コメント付き複雑ロジック

## 参考実装

- Move: src/jpoke/data/move.py
- Handler: src/jpoke/handlers/move.py
- ダメージ計算: src/jpoke/core/damage.py

## 知見

- `ON_TRY_ACTION` は行動可否のゲートなので、失敗時は即座に行動を中断する設計が必要。
- `MoveData.handlers` は単一ハンドラだけでなくリストも登録可能（複数効果の併用に有効）。
