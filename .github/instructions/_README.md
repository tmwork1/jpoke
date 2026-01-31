# Copilot Instructions ガイド

本ディレクトリは、VS Code Copilot を使用した開発手順を体系的にまとめたものである。

## 推奨読解順序

### 開発着手前（必須）
1. `project_context.md` - プロジェクト背景とアーキテクチャ概要（15分）
2. `architecture.md` - 詳細なシステム設計（20分）

### 新機能実装時
3. `agents/workflow.md` - エージェントワークフロー全体
4. `agents/05_research.md` - 仕様調査（複数特性がある場合）
5. 各エージェントプロンプトを順次使用

---

## ドキュメント構成

```
.github/instructions/
├── _README.md                    # 本ファイル
├── project_context.md             # プロジェクト背景・要件
├── architecture.md                # 技術アーキテクチャ詳細
└── agents/                        # エージェント実行プロンプト
    ├── workflow.md                # ワークフロー全体ガイド
    ├── 05_research.md             # リサーチ（仕様調査）
    ├── 00_orchestrator.md         # 司令塔（全体計画）
    ├── 10_planner.md              # 計画（タスク分解）
    ├── 20_architect.md            # 設計
    ├── 30_coder.md                # 実装
    ├── 40_tester.md               # テスト
    ├── 50_reviewer.md             # レビュー
    └── 60_domain_expert.md        # 専門家（Pokemon仕様）
```

---

## ワークフロー例

### 新規特性1件の追加

```
1. project_context.md を読解（10分）
2. agents/workflow.md で全体フロー確認（10分）
3. agents/05_research.md で仕様調査（10-20分）
4. agents/00_orchestrator.md で計画策定（5分）
5. agents/10_planner.md でタスク分解（5分）
6. 以降の実装フロー（agents/20_architect.md 〜 agents/60_domain_expert.md）
```

**合計時間**: 初回100-120分、2回目以降30-40分

### 複雑な仕様の複数機能

```
1. architecture.md で詳細学習（30分）
2. agents/05_research.md で複数機能を一括リサーチ（30分）
3. agents/00_orchestrator.md で全体計画（10分）
4. agents/10_planner.md でバッチタスク分解（20分）
5. 各エージェントで並列実装
```

---

## 利用上の注意点

### 推奨される使用方法

1. VS Code Copilot Chat を開く（Ctrl + Shift + I）
2. エージェントプロンプトを選択
   - 対象のMarkdownファイル（例: `05_research.md`）をプロンプトコンテキストに追加
3. 要件を入力
   - 例: 「この特性について詳しく調べてください」
4. 出力をコピーして次のエージェントに渡す

### コンテキストの活用

- 前ステップの出力を全てコピーし、次のエージェントに渡すこと
- Copilot Chat にコンテキストが保持される

### よくある失敗パターン

- architecture.md を読まずにいきなり実装
  - アーキテクチャを理解してから実装すること
- リサーチをスキップして実装
  - 複雑な仕様の場合、必ずリサーチしてから設計すること
- エージェント間でコンテキスト引き継ぎなし
  - 前のステップの出力を全てコピーして次へ渡すこと

---

## 関連ファイル

本ガイドに加えて、ルートにある以下のファイルも参考になる。

- `.copilot-instructions.md` - Copilot の自動読込（プロジェクト背景の要約）
- `prompts/` - 補助的な資料（CSVなど）

---

## よくある質問

### プロジェクト構成の学習方法は？

1. `.github/instructions/project_context.md` で背景を理解
2. `.github/instructions/architecture.md` で詳細を学ぶ
3. 実装フロー例に沿ってエージェントを使用

### 複数の特性を一度に実装したい場合は？

1. `agents/05_research.md` で全特性を一括リサーチ
2. `agents/00_orchestrator.md` で全体計画
3. `agents/10_planner.md` でバッチタスク分解
4. 各エージェントで処理

### エージェント間で情報を引き継ぐには？

前のステップの出力を全てコピーして、次のエージェントに渡すこと。Copilot Chat にコンテキストが保持される。

---

## 開発者向けチェックリスト

新規開発者は以下を確認すること。

- [ ] `.github/instructions/project_context.md` を読了
- [ ] `.github/instructions/architecture.md` を読了
- [ ] `.github/instructions/agents/workflow.md` を流し読み
- [ ] Copilot Chat の使い方を理解

---

**注意**: 本ドキュメントは継続的に改善される。改善案や質問があればプロジェクトに反映すること。
