````instructions
# Copilot 指示

## 基本方針

- ポケモンの仕様は第9世代（スカーレット・バイオレット）を参照する
- 第9世代で実装されていない技・アイテム・特性・ポケモンなどは、実装を見送る

## 実装指示

### 基本フロー
1. Manager (MGR) がユーザーリクエストを受け付け
2. `.github/instructions/agents/workflow.md` に従って各エージェントに業務を割り当て
3. 各エージェントは発言の先頭に役職識別子を付ける（下記参照）
4. 不明点は合理的な選択肢を推測して継続し、作業を完遂（全テストパス）することを優先
5. ユーザーの承認を待たずにファイルの作成・編集・削除を直接実行

### 中間ファイルの管理
- **中間スクリプトやテストファイルはルート直下に生成しない**
  - 一時的な分析スクリプト → `docs/research/` または作業後に削除
  - テストファイル → `tests/` ディレクトリ内
- **作業完了時の必須クリーンアップ**:
  - 以後使用しない中間ファイル（分析スクリプト等）は削除
  - 必要なファイルのみを適切なディレクトリに配置
  - ルート直下は `README.md`, `pyproject.toml`, `setup.cfg`, `LICENSE` など設定ファイルのみ

### タスク完了後の必須作業
以下を必ず実行してプロジェクトの知識を蓄積：

1. `python -m jpoke.utils.dashboard` を実行してダッシュボード更新
2. `README.md` の実装状況を更新
3. 得られた知識を該当する指示書（`.github/instructions/agents/*.md`）に追記

### エージェント発言規則

各エージェントは発言の先頭に役職識別子を付けること：

| 識別子 | 役職名 |
|--------|--------|
| MGR | Project Manager |
| RSC | Research Specialist |
| PLN | Planning Specialist |
| ARC | Architecture Specialist |
| COD | Coding Specialist |
| TST | Testing Specialist |
| RVW | Code Review Specialist |
| DOM | Domain Expert |

例：
```
MGR: ユーザーリクエストを受け付けました。リサーチ専門家に調査を依頼します。
RSC: 特性「かたやぶり」の仕様を調査します...
PLN: タスクを3つのサブタスクに分解します...
ARC: データモデルの設計を行います...
COD: handlers/ability.py に新しいハンドラを追加します...
TST: 状態異常のテストケースを作成します...
RVW: コード品質をレビューします...
DOM: ポケモン仕様との整合性を確認します...
```

## クイックリファレンス

### プロジェクト概要
- jpoke: ポケモンシングルバトル対戦シミュレータ
- 目的: 戦闘ロジックの開発検証
- 状態: AI ボット開発は保留中

### 核心概念
1. イベント駆動: `EventManager` が中核（`src/jpoke/core/event.py`）
2. Handler: 効果は全て Handler で実装（`src/jpoke/handlers/`）
3. RoleSpec: `"role:side"` 形式で対象指定（例: `"source:self"`, `"target:foe"`）
   - ダメージ計算系イベントでは `"attacker:self"`, `"defender:self"` を使用
   - その他のイベントでは `"source:self"`, `"target:self"` を使用
4. HandlerReturn: 必ず `HandlerReturn(success, value, control)` を返す

### プロジェクト構造
```
src/jpoke/
├── core/       # バトルシステム中核
├── model/      # Pokemon状態管理
├── data/       # データ定義（特性・技・アイテム）
├── handlers/   # ハンドラ実装
└── utils/      # ユーティリティ
```

### 重要ファイル
- `src/jpoke/core/event.py` - イベント駆動システム
- `src/jpoke/core/battle.py` - Battle ファサード
- `src/jpoke/core/damage.py` - ダメージ計算（4096基準）
- `src/jpoke/model/pokemon.py` - Pokemon クラス
- `src/jpoke/data/ability.py` - 特性データ定義
- `tests/test_utils.py` - テストユーティリティ
- `tests/field.py` - フィールド効果テスト

## テスト実装のベストプラクティス

### テストで使用するポケモン
- 初歩的で周知されたポケモンを使う: ピカチュウ、フシギダネ、ヒトカゲ、ゼニガメなど第1世代の有名なポケモンを優先
- 目的: 誰でも分かりやすく、テストの意図が明確になる
- 例:
  - 攻撃技テスト → ピカチュウ、リザードン
  - 防御技テスト → カメックス、フシギバナ
  - 素早さ → ピカチュウ、ペルシアン
  - 特殊技 → フーディン、ゲンガー

### フィールド効果のテスト
- 補正値の検証: イベントシステムを使って補正値を直接検証する
  - `ON_CALC_POWER_MODIFIER`: 技威力補正（4096基準）
  - `ON_CALC_DAMAGE_MODIFIER`: ダメージ補正（4096基準）
- 補正計算の基準値: すべて4096基準で計算される
  - 例: 1.5倍補正 → `4096 * 1.5 = 6144`
  - 例: 0.5倍補正 → `4096 * 0.5 = 2048`
- 浮動小数点数の比較: `abs(actual - expected) < 0.01` で誤差を許容

### テストヘルパー関数
- `start_battle()`: バトル初期化（天候・地形・フィールドを指定可能）
- `tick_fields()`: フィールド効果のカウントダウン
- `assert_field_active()`: フィールドの有効性を検証
- `get_field_count()`: フィールドの残りカウントを取得

### フィールドパラメータの一貫性
- `weather`: タプル `(天候名, カウント)`
- `terrain`: タプル `(地形名, カウント)`
- `ally_side_field`: 辞書 `{名前: レイヤー数}`
- `foe_side_field`: 辞書 `{名前: レイヤー数}`
- `global_field`: 辞書 `{名前: カウント}`
- `ally_volatile`: 辞書 `{名前: カウント}`
- `foe_volatile`: 辞書 `{名前: カウント}`

## ドキュメント構成

必ず最初に `.github/instructions/_README.md` を読んでください。

```
.github/instructions/
├── _README.md              # 読む順序・全体ガイド
├── project_context.md      # プロジェクト背景（15分）
├── architecture.md         # 詳細アーキテクチャ（30分）
└── agents/                 # エージェントプロンプト
    ├── workflow.md         # ワークフロー全体
    ├── 00_manager.md       # 全体調整
    ├── 10_research.md      # 仕様調査
    ├── 20_planner.md       # タスク分解
    ├── 30_architect.md     # 設計
    ├── 40_coder.md         # 実装
    ├── 50_tester.md        # テスト
    ├── 60_reviewer.md      # レビュー
    └── 70_domain_expert.md # Pokemon仕様確認
```

## 新機能実装フロー

1. `.github/instructions/agents/workflow.md` で全体確認
2. `.github/instructions/agents/10_research.md` で仕様調査
3. 各エージェント（Manager → Research → Planner → Architect → Coder → Tester → Reviewer → Domain Expert）で実装

## 詳細情報

すべての詳細は `.github/instructions/` を参照：

- プロジェクト背景: `.github/instructions/project_context.md`
- アーキテクチャ詳細: `.github/instructions/architecture.md`
- ワークフロー: `.github/instructions/agents/workflow.md`

## 最適化方針

本ドキュメントは以下の原則に基づいて最適化されています：

1. 簡潔性: 絵文字、太字、装飾的な区切り線を排除し、情報を直接的に記述
2. 一貫性: エージェント採番を10の倍数に統一（00, 10, 20...）
3. 正確性: ファイルパスは実際のプロジェクト構成と一致させ、相対パスまたはバッククォート形式で記述
4. 機械可読性: Copilot が解析しやすい構造化されたフォーマットを使用
5. 実用性: 冗長な説明を避け、実装に直結する情報のみを記載
````
