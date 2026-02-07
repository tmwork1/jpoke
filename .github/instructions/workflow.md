# 開発ワークフロー

統合的な開発手順書。調査→計画→設計→実装→テスト→レビューの全工程をカバー。

## 基本方針

- **第9世代（SV）準拠**: 第9世代で実装されていない要素は見送る
- **シングル対戦のみ**: ダブルバトルは対象外
- **イベント駆動**: すべての効果はイベント/Handlerで実装
- **完遂主義**: コード追加・修正時はテスト・レビューまで完遂
- **推測継続**: ユーザへの確認はせず、不明点は推測して進める

## 全体フロー

```
ユーザーリクエスト
    ↓
Phase 1: 調査（新規ドメイン・複雑仕様時のみ）
    ↓
Phase 2: 計画（タスク分解・依存関係整理）
    ↓
Phase 3: 設計（技術設計・アーキテクチャ整合性）
    ↓
Phase 4: 実装（コード作成・チェックリスト更新）
    ↓
Phase 5: テスト（単体・統合テスト作成・実行）
    ↓
Phase 6: レビュー（品質・仕様確認・ドキュメント）
    ↓
完了（dashboard更新・README更新・知見記録）
```

---

## Phase 1: 調査

### 目的
新規ドメイン・複雑仕様の理解、実装容易な形式での整理

### 実施タイミング
- 新規特性・技・アイテム・状態異常の実装
- 既存実装がない新規ドメイン
- 複雑な相互作用が予想される場合

### チェックリスト
- [ ] 名前（日本語・英語）確認
- [ ] 分類（特性/技/アイテム/状態異常等）確認
- [ ] 発動条件・効果の詳細記録
- [ ] 第9世代での変更点調査
- [ ] 相互作用・エッジケースの洗い出し
- [ ] 複数情報源で確認（Bulbapedia, ポケモンWiki, 公式）

### 出力先
`docs/spec/[カテゴリ]/[機能名].md`

### 出力形式

```markdown
| 項目 | 内容 | 出典 |
|-----|------|------|
| 名前 | [日本語/英語] | Wiki |
| 分類 | [分類] | - |
| 効果 | [説明] | Wiki |
| 発動条件 | [条件] | Wiki |
| 第9世代変更 | [変更内容] | Bulbapedia |
| 相互作用 | [他機能との組み合わせ] | Wiki |
| エッジケース | [特殊状況] | 検証 |
```

### 参考資料
- [ポケモンWiki](https://wiki.xn--rckteqa2e.com/) (日本語)
- [Bulbapedia](https://bulbapedia.bulbagarden.net/) (英語)
- [ポケモン公式](https://www.pokemon.co.jp/)

---

## Phase 2: 計画

### 目的
要件のサブタスク分解、実装順序・依存関係の整理

### チェックリスト
- [ ] 要件を実装可能な単位に分解
- [ ] 実装順序・依存関係を明確化
- [ ] 既存コード連携点を洗い出し
- [ ] リスク・落とし穴の指摘
- [ ] 未確認ポイントの明示
- [ ] 既存機能との重複確認

### 出力先
`docs/plan/[機能名].md`

### 出力形式

```markdown
## タスク分解

### 要件概要
[ユーザーの要望を簡潔に]

### 全体フロー
[実装フロー図またはテキスト]

### サブタスク一覧

| # | タスク | ファイル | 依存 | 難度 | 備考 |
|----|--------|---------|------|------|------|
| 1 | データモデル定義 | src/jpoke/data/[type].py | - | 低 | 既存XXX参照 |
| 2 | ハンドラ実装 | src/jpoke/handlers/[type].py | 1 | 中 | イベント登録 |
| 3 | テスト作成 | tests/test_[type].py | 1,2 | 低 | 単体+統合 |

### 注意点・リスク
- [既存の制約事項]
- [潜在的な問題]
- [確認が必要な点]

### 完了条件
- [ ] XXX機能が動作
- [ ] テスト全パス
- [ ] ドキュメント更新
```

### プロジェクト構造参照
- `src/jpoke/data/`: Pydantic BaseModelによるデータ定義
- `src/jpoke/handlers/`: ビジネスロジック（効果実装）
- `src/jpoke/core/`: 対戦システム中核（ターン制御・ダメージ計算・イベント管理）
- `tests/`: ユニットテスト

---

## Phase 3: 設計

### 目的
計画の技術的精査、既存アーキテクチャとの整合性確保

### チェックリスト
- [ ] 既存アーキテクチャ適合性評価
- [ ] データ構造・API設計定義
- [ ] パフォーマンスリスク評価
- [ ] テスト容易性評価
- [ ] 既存データモデルとの型互換性確認
- [ ] 複数効果の相互作用考慮
- [ ] ターン制御への影響確認
- [ ] ハードコーディングの回避

### 出力先
`docs/architecture/[機能名].md`

### 出力形式

```markdown
## 実装設計

### 計画概要
[Phase 2の要点]

### 技術レビュー
- 既存アーキテクチャ適合性: [評価]
- パフォーマンスリスク: [評価]
- テスト容易性: [評価]

### 詳細設計

#### 1. データモデル
\`\`\`python
class Example(BaseModel):
    field1: Type1 = Field(..., description="XXX")
    field2: Type2 = Field(default=value, description="YYY")
    
    def method(self, arg: ArgType) -> ReturnType:
        """メソッド説明"""
        pass
\`\`\`

#### 2. ハンドラ実装
\`\`\`python
def handler_function(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ハンドラ説明
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: 入力値
    
    Returns:
        HandlerReturn(success, value, control)
    """
    # 実装ロジック
    return HandlerReturn(True, modified_value)
\`\`\`

#### 3. 既存コード連携
| ファイル | 変更内容 | 理由 |
|---------|--------|------|
| src/jpoke/data/[type].py | XXX追加 | 新規データ定義 |
| src/jpoke/handlers/[type].py | YYY関数追加 | 効果実装 |

#### 4. 特殊ケース処理
\`\`\`python
# ケース: [説明]
# シナリオ: [具体例]
# 実装方針: [方針]
\`\`\`

### 設計上の制約・仮定
- [既存仕様との制約]
- [エッジケース処理方針]
- [想定される制限事項]

### 実装注意点
- 既存テスト影響: [評価]
- ターン制御: [確認事項]
- パフォーマンス: [評価]
```

### システム特性の理解
- **イベント駆動**: `core/event.py` が全イベント処理を管理
- **Handler**: 全効果をHandlerで実装、RoleSpecで対象を指定
- **ターン制御**: `turn_controller.py` で複雑な順序制御
- **ダメージ計算**: `damage.py` で4096基準の詳細ロジック
- **フィールド管理**: 天候・地形・場の状態を個別管理

---

## Phase 4: 実装

### 目的
設計に基づくコード実装、チェックリスト更新

### チェックリスト
- [ ] 型ヒント全関数・全引数に付与
- [ ] ドキストリング（説明・Args・Returns）記載
- [ ] ハードコーディング回避（constants使用）
- [ ] エラーハンドリング実装
- [ ] logger活用（デバッグ・動作確認）
- [ ] 既存パターン踏襲（一貫性重視）
- [ ] HandlerReturn を必ず返す
- [ ] RoleSpec を正確に指定

### ファイル構成
- `src/jpoke/data/`: データモデル定義
- `src/jpoke/handlers/`: ハンドラ実装
- `src/jpoke/core/`: システム中核（必要時のみ変更）
- `docs/checklist/`: 実装済み項目の更新

### コーディングパターン

#### 型ヒント必須
```python
def calculate_damage(attacker: Pokemon, move: Move, defender: Pokemon) -> int:
    """ダメージ計算。
    
    Args:
        attacker: 攻撃側ポケモン
        move: 使用技
        defender: 防御側ポケモン
    
    Returns:
        計算ダメージ
    """
    return value
```

#### Pydantic型安全性
```python
from pydantic import BaseModel, Field

class MoveData(BaseModel):
    name: str = Field(..., description="技名")
    power: int = Field(default=0, description="威力")
    accuracy: int = Field(default=100, description="命中率")
    handlers: dict[Event, Handler | list[Handler]] = Field(default_factory=dict)
```

#### 既存ユーティリティ活用
```python
from jpoke.handlers.common import get_modifier, apply_modifier
from jpoke.core.logger import get_logger

logger = get_logger(__name__)
logger.debug(f"威力補正: {modifier}")
```

#### ハンドラ実装パターン
```python
def 特性_effect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """特性の効果説明
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト（source/targetまたはattacker/defenderを持つ）
        value: 入力値（補正値など）
    
    Returns:
        HandlerReturn(success, modified_value, control)
    """
    # 条件チェック
    if not condition:
        return HandlerReturn(False)
    
    # 効果適用
    modified_value = apply_effect(value)
    
    # ログ出力
    logger.info(f"{ctx.source.name}の特性が発動")
    
    return HandlerReturn(True, modified_value)
```

### ベストプラクティス

#### ✅ 推奨
- 名前付き関数（デバッグ容易）
- Pydantic BaseModel活用
- 既存util・common関数の再利用
- 単一責任原則
- 複雑ロジックにコメント

#### ❌ 回避
- ハードコーディング（定数化すべき）
- 型ヒントなし
- ロギングなし
- 複雑なLambda
- Any型の多用

### 参考実装
- 技データ: [src/jpoke/data/move.py](../../src/jpoke/data/move.py)
- 特性データ: [src/jpoke/data/ability.py](../../src/jpoke/data/ability.py)
- ハンドラ: [src/jpoke/handlers/](../../src/jpoke/handlers/)
- ダメージ計算: [src/jpoke/core/damage.py](../../src/jpoke/core/damage.py)

---

## Phase 5: テスト

### 目的
単体・統合テストの作成・実行、カバレッジ確保

### テストレベル分類

#### レベル1: ハンドラ単体テスト
**対象**: `handlers/*.py` の個別関数（条件判定・副作用）

```python
from jpoke.handlers.ability import apply_static_electricity

def test_静電気_発動():
    """接触技でまひ付与"""
    battle = start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいでんき")],
        foe=[Pokemon("フシギダネ")],
    )
    # ハンドラ直接呼び出しまたは技実行
    execute_move(battle, "つるのムチ")
    assert battle.foe.active.ailment.name == "まひ"
```

#### レベル2: 統合テスト
**対象**: バトル全体でのハンドラ連携（イベント発火・優先度・相互作用）

```python
def test_複合効果_天候と特性():
    """はれ + ようりょくそで素早さ2倍"""
    battle = start_battle(
        ally=[Pokemon("フシギバナ", ability="ようりょくそ")],
        foe=[Pokemon("リザードン")],
        weather=("はれ", 5),
    )
    # 素早さ確認
    assert battle.ally.active.effective_speed == battle.ally.active.stats.speed * 2
```

### チェックリスト
- [ ] 主要ロジックのカバレッジ確保
- [ ] エッジケース（境界値・エラー系）テスト
- [ ] 既存テスト破壊なし（回帰テスト）
- [ ] test_utils共通処理共通化
- [ ] 1テスト = 1仕様確認
- [ ] ハンドラ単体 + 統合の両レベル実施

### test_utils活用

```python
from tests.test_utils import start_battle, tick_fields, assert_field_active, get_field_count

# 初期化
battle = start_battle(
    ally=[Pokemon("ピカチュウ", ability="せいでんき", item="きあいのタスキ")],
    foe=[Pokemon("フシギダネ")],
    weather=("はれ", 5),
    terrain=("エレキフィールド", 5),
    ally_side_field={"リフレクター": 5},
    ally_volatile={"みがわり": (None, hp//4)},
)

# ターン進行
tick_fields(battle, ticks=3)

# フィールド確認
assert_field_active(battle, "はれ")
assert get_field_count(battle, "エレキフィールド") == 2
```

### テスト対象別の優先順位

| 優先度 | 対象 | テストケース例 |
|--------|------|----------------|
| 高 | 新機能（特性・技・アイテム） | 発動条件・効果・相互作用 |
| 高 | ダメージ計算 | 基本・補正・エッジケース |
| 中 | ターン制御・イベント | 順序・優先度・複数効果 |
| 中 | フィールド効果 | 付与・カウント・消滅 |
| 低 | UI・ロギング | 表示順序・ログ整合性 |

### 出力先
`tests/test_[対象].py`

### テスト実行
```bash
python tests/run.py
```

### ベストプラクティス

#### ✅ 推奨
- test_utilsテンプレート活用
- 1テスト = 1仕様確認
- 失敗時は詳細レポート（原因・期待値・実際値）
- 浮動小数点比較は許容誤差設定(`abs(actual - expected) < 0.01`)

#### ❌ 回避
- 直接オブジェクト生成（test_utils使用）
- テストケース間の依存関係
- ハードコーディング数値（定数化）

---

## Phase 6: レビュー

### 目的
コード品質・テストカバレッジ・ポケモン仕様適合性の確認

### レビュー観点

#### 1. コード品質
- [ ] 型ヒント: 全関数・変数に型指定
- [ ] ネーミング: 日本語で一貫、わかりやすい
- [ ] 構造: 単一責任、複雑すぎない
- [ ] エラーハンドリング: 例外処理適切
- [ ] Lambda: 複雑さなし
- [ ] コメント: 複雑部分にコメント
- [ ] ドキストリング: 全関数に説明

#### 2. テスト
- [ ] カバレッジ: 主要ロジック網羅
- [ ] エッジケース: 境界値・エラー系テスト
- [ ] 回帰テスト: 既存テスト破壊なし
- [ ] test_utils: 共通処理共通化

#### 3. アーキテクチャ一貫性
- [ ] プロジェクト全体: 既存コードとの一貫性
- [ ] RoleSpec: "role:side"形式正確使用
- [ ] HandlerReturn: 必ず返却
- [ ] イベント/Handler: 正しいパターン
- [ ] データモデル: Pydantic BaseModel使用

#### 4. ドキュメント
- [ ] README: 新機能記録
- [ ] docs/spec: 背景情報
- [ ] docs/checklist: 実装済み項目更新
- [ ] コードコメント: 必要箇所に記載

#### 5. ポケモン仕様適合性

##### 5.1 基本仕様
- [ ] 発動条件: リサーチ通りに実装
- [ ] 効果: 説明と実装一致
- [ ] 第9世代変更: 過去世代との相違反映

##### 5.2 相互作用
- [ ] 複数特性: 優先順位正確
- [ ] 特性+アイテム: 相互作用実装
- [ ] 技+天候: 威力・効果変化
- [ ] ランク補正: 正しく計算

##### 5.3 エッジケース
- [ ] 瀕死状態: 特性発動判定
- [ ] 交代時: 特性・アイテム効果
- [ ] 場を去る: 効果消滅
- [ ] 上書き: 状態異常判定

##### 5.4 テスト仕様適合性
- [ ] ユニットテスト: 個別機能仕様通り
- [ ] 統合テスト: 複数機能組み合わせ仕様通り
- [ ] エッジケーステスト: 例外ケース正しく処理

### レビュー結果の保存

包括的なレビューや調査結果は以下に保存:

- **保存先**: `docs/review/`
- **命名規則**: `YYYYMMDD_レビュー内容.md`
- **例**: `20260207_実装済みハンドラと最新research資料の整合性.md`

---

## パターン別ガイド

### パターンA: 新規ハンドラ実装（特性・技・アイテム）

```
Phase 1: 調査 → docs/spec/[カテゴリ]/[名前].md
Phase 2: 計画 → タスク分解
Phase 3: 設計 → データモデル・ハンドラ設計
Phase 4: 実装 → data + handlers実装
Phase 5: テスト → 単体・統合テスト
Phase 6: レビュー → 品質・仕様確認
完了: dashboard・README更新
```

### パターンB: バグ修正

```
Phase 6: レビュー → 原因特定・影響範囲調査
Phase 4: 実装 → 修正コード
Phase 5: テスト → 修正テスト・回帰テスト
Phase 6: レビュー → 再確認
完了: 知見記録
```

### パターンC: リファクタリング

```
Phase 6: レビュー → 問題点洗い出し
Phase 3: 設計 → リファクタ設計
Phase 4: 実装 → コード整理
Phase 5: テスト → 回帰テスト全実行
Phase 6: レビュー → 品質向上確認
```

### パターンD: 複雑な相互作用（大規模）

```
Phase 1: 調査 → 詳細仕様調査
Phase 2: 計画 → 複数技術要素の分解
Phase 6: レビュー → 既存実装調査
Phase 3: 設計 → 統合設計
Phase 4-6: 段階的実装（機能単位）
完了: 包括的レビュー文書作成
```

---

## 完了時タスク

### 必須
1. **Dashboard更新**: `python -m jpoke.utils.dashboard` 実行
2. **README更新**: 実装済み機能を記載
3. **Checklist更新**: `docs/checklist/[カテゴリ].md` に実装済みマーク

### 知見の記録
新規知見・パターン・トラブルシューティングを以下に記録:

- `knowledge/patterns.md` - 実装パターン
- `knowledge/abilities.md` - 特性実装の知見
- `knowledge/moves.md` - 技実装の知見
- `knowledge/damage_calc.md` - ダメージ計算の知見
- `knowledge/edge_cases.md` - エッジケース集
- `knowledge/troubleshooting.md` - よくある問題と解決策

---

## ツール使用法

### ファイル操作
- `create_file`: 新規ファイル作成
- `replace_string_in_file`: 既存ファイル編集
- `multi_replace_string_in_file`: 複数箇所同時編集（効率的）
- `read_file`: ファイル内容確認

### 検索
- `semantic_search`: セマンティック検索（コンセプト・機能検索）
- `grep_search`: パターン検索（正確な文字列・正規表現）
- `file_search`: ファイル名検索（glob）

### Python環境
- `configure_python_environment`: Python環境構築
- `install_python_packages`: パッケージインストール
- `mcp_pylance_mcp_s_pylanceRunCodeSnippet`: コードスニペット実行（推奨）

### テスト・実行
- `run_in_terminal`: コマンド実行
- `get_terminal_output`: ターミナル出力確認

---

## 参考ドキュメント

### 必読
1. [project_context.md](project_context.md) - プロジェクト背景
2. [implementation_principles.md](implementation_principles.md) - 実装場所の判断基準
3. [architecture.md](architecture.md) - システム技術詳細

### 補助
- [MIGRATION.md](MIGRATION.md) - 移行ログ
- [CHANGELOG.md](CHANGELOG.md) - 変更履歴
- `docs/spec/` - 仕様調査結果
- `docs/checklist/` - 実装状況
- `tests/test_utils.py` - テストヘルパー

---

## よくある質問

### Q: どのPhaseから始めるべき？
A: 新規実装ならPhase 1（調査）から。バグ修正ならPhase 6（レビュー）で原因特定から。

### Q: 既存コードはどこを参照すべき？
A: 同カテゴリの既存実装を参照。特性なら`data/ability.py` + `handlers/ability.py`。

### Q: テストが失敗したら？
A: Phase 4（実装）に戻って修正。Phase 6（レビュー）で根本原因を分析。

### Q: ドキュメントはどこまで書く？
A: 最低限：ドキストリング必須。複雑ロジック：コメント必須。新規ドメイン：docs/spec/に詳細。

### Q: 知見はどこに記録？
A: `knowledge/[カテゴリ].md`に追記。パターン・落とし穴・解決策を記録。
