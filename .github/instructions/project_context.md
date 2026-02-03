# プロジェクトコンテキスト

**jpoke**: ポケモンシングルバトル対戦シミュレータ

## 基本方針

- 第9世代（SV）準拠
- シングル対戦（1v1）のみ
- 未実装機能は見送り

## 目的

- 戦闘ロジック開発検証
- AI ボット開発基盤（準備中）

## プロジェクト構造

```
src/jpoke/
 core/       # イベント.py, battle.py, damage.py
 model/      # pokemon.py, stats.py, ailment.py
 data/       # ability.py, move.py, item.py
 handlers/   # 効果実装
 utils/      # ユーティリティ
```

## 核心アーキテクチャ

### 1. イベント駆動

`イベントManager` (`core/イベント.py`) が中核。

```
バトルフェーズ  イベント発火  登録ハンドラ実行  効果適用
```

### 2. Handler

特性技アイテムの効果は Handler で実装。

```python
def いかく(battle: Battle, ctx: イベントContext, value: Any):
    # 相手の攻撃を1段階下げる
    return HandlerReturn(True, ...)

イベント.ON_SWITCH_IN: Handler(
    func=いかく,
    subject_spec="source:foe",
    log="on_success"
)
```

**Handler 構造**:
- `func`: 実行関数
- `subject_spec`: 対象指定 (`"role:side"` 形式)
- `source_type`: 出典 (`"ability"` | `"item"` | `"move"` | `"ailment"` | `"volatile"`)
- `log`: ログポリシー
- `priority`: 優先度

### 3. イベントContext

```python
class イベントContext:
    source: Pokemon | None
    target: Pokemon | None
    
    # エイリアス（プロパティ）
    @property
    def attacker(self) -> Pokemon | None: return self.source
    
    @property
    def defender(self) -> Pokemon | None: return self.target
```

**使い分け**:
- ダメージ計算系: `attacker`, `defender`
- その他: `source`, `target`

## ファイル読解順序

1. `utils/type_defs.py`, `utils/enums/`, `utils/constants.py`
2. `model/stats.py`, `model/effect.py`, `model/ailment.py`, `model/volatile.py`
3. `model/pokemon.py`
4. `core/イベント.py`, `core/move_executor.py`, `core/turn_controller.py`
5. `core/battle.py`
6. `data/models.py`
7. `handlers/*.py`

## ドキュメント構成

```
.github/instructions/
 _README.md              # 読む順序
 project_context.md      # 本ファイル
 architecture.md         # 詳細設計
 effect_hierarchy.md     # 作用実装原則
 agents/                 # エージェント指示
     workflow.md         # ワークフロー
     00_manager.md
     10_research.md
     20_planner.md
     30_architect.md
     40_coder.md
     50_tester.md
     60_reviewer.md
     70_domain_expert.md
```

## 新機能実装フロー

1. `agents/workflow.md` で全体確認
2. Manager  Research  Planner  Architect  Coder  Tester  Reviewer  Domain Expert

## 次のステップ

- 詳細設計: `architecture.md`
- 作用実装: `effect_hierarchy.md`
- ワークフロー: `agents/workflow.md`
