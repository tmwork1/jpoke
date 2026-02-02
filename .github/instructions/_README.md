# Copilot Instructions ガイド

本ディレクトリは、VS Code Copilot を使用した開発手順を体系的にまとめたものである。

## 重要な変更：新しいチーム構成

**2026年2月1日より、エージェント構成を変更しました**

従来の一直線のリレー方式から、**1人のプロジェクトマネージャーと複数の専門家部下からなるチーム構成**に変更しました。これにより、作業の抜け漏れを大幅に削減します。

### 新しい構造

```
ユーザー → Project Manager (00_manager.md)
              ├─→ Research Specialist (仕様調査)
              ├─→ Planning Specialist (タスク分解)
              ├─→ Architecture Specialist (設計)
              ├─→ Coding Specialist (実装)
              ├─→ Testing Specialist (テスト)
              ├─→ Code Review Specialist (レビュー)
              └─→ Domain Expert (仕様確認)
```

**重要**: すべてのプロジェクトは **Manager (00_manager.md)** から開始してください。Manager が適切な専門家を選定し、業務を割り振ります。

## 基本方針

- **ポケモンの仕様は第9世代（スカーレット・バイオレット）を参照する**
- **第9世代で実装されていない技・アイテム・特性・ポケモンなどは、実装を見送る**
- **すべてのプロジェクトは Manager から開始する**
- **作業開始前に既存リソースを必ず確認する**（既存コード、テスト、README、docs/research、.github/instructions）

---

## 推奨読解順序

### 開発着手前（必須）
1. [`project_context.md`](project_context.md) - プロジェクト背景とアーキテクチャ概要（15分）
2. [`architecture.md`](architecture.md) - 詳細なシステム設計（30分）
3. [`effect_hierarchy.md`](effect_hierarchy.md) - 作用のヒエラルキーと実装原則（15分）
4. **既存実装・テスト・ドキュメントの確認**（該当領域のコード、tests、README、docs/research）

### 新機能実装時
1. [`agents/workflow.md`](agents/workflow.md) - エージェントワークフロー全体（**新しいチーム構成を理解**）
2. **Manager (`agents/00_manager.md`) に相談** - プロジェクト開始
3. Manager の指示に従って各専門家と協業

---

## ドキュメント構成

```
.github/instructions/
├── _README.md              # 本ファイル
├── project_context.md      # プロジェクト背景・要件
├── architecture.md         # 技術アーキテクチャ詳細
├── effect_hierarchy.md     # 作用のヒエラルキーと実装原則
├── CHANGELOG.md            # 変更履歴（重要な修正の記録）
├── references/             # 参考資料（アーカイブ）
│   ├── README.md           # → docs/research/ に移行済み
│   └── *.csv               # 元データ（保持）
└── agents/                 # エージェント実行プロンプト
    ├── workflow.md         # ワークフロー全体ガイド（新構成対応）
    ├── 00_manager.md       # ★ プロジェクトマネージャー（すべてここから開始）
    ├── 05_research.md      # Research Specialist（仕様調査）
    ├── 10_planner.md       # Planning Specialist（タスク分解）
    ├── 20_architect.md     # Architecture Specialist（設計）
    ├── 30_coder.md         # Coding Specialist（実装）
    ├── 40_tester.md        # Testing Specialist（テスト）
    ├── 50_reviewer.md      # Code Review Specialist（レビュー）
    └── 60_domain_expert.md # Domain Expert（Pokemon仕様確認）
```

**注意**: リサーチ結果は `docs/research/` に保存されます（詳細は [agents/05_research.md](agents/05_research.md) 参照）。

---

## ワークフロー例

### 新規特性1件の追加（新しい方法）

```
1. project_context.md を読解（10分）
2. agents/workflow.md で新しいチーム構成を確認（10分）
3. Manager (00_manager.md) に相談
   「新しい特性『いかく』を追加したい」
4. Manager が以下を自動的に進行管理:
   - 仕様調査（必要に応じて）
   - タスク分解
   - 設計
   - 実装
   - テスト
   - レビュー
   - 仕様確認
5. Manager から完了報告を受け取る
```

**特徴**:
- Manager が各工程で成果物をレビュー
- 問題があれば該当専門家に差し戻し
- コンテキストが継続的に保たれる
- 抜け漏れが大幅に削減

### 複雑な仕様の複数機能（新しい方法）

```
1. architecture.md で詳細学習（30分）
2. Manager (00_manager.md) に相談
   「特性『テレパシー』『ダウンロード』『トレーシング』を追加したい」
3. Manager が以下を実施:
   - Research Specialist に一括リサーチを依頼
   - 調査結果をレビュー
   - Planning Specialist にバッチタスク分解を依頼
   - 計画をレビュー・承認
   - 以降の実装フローを進行管理
4. Manager から完了報告を受け取る
```

---

## 利用上の注意点

### 推奨される使用方法（重要な変更）

1. VS Code Copilot Chat を開く（Ctrl + Shift + I）
2. **`00_manager` を選択**
3. ユーザーの要求を入力
4. Manager の指示に従う

### ❌ やってはいけないこと

- 各専門家に直接依頼する
  → Manager が適切な専門家を選定します
- 前の工程の成果物を次に伝えずに進める
  → Manager が自動的に引き継ぎます
- 成果物のレビューをスキップする
  → Manager が各工程で必ずレビューします

### ✅ 新しい方法の利点

- **抜け漏れ防止**: Manager が全体を把握し、各工程をレビュー
- **コンテキスト継続**: Manager が一貫してプロジェクト管理
- **品質向上**: 各工程で成果物の承認が必要
- **効率化**: ユーザーは Manager とだけやり取り

---

## よくある質問

### プロジェクトを開始するには？

**Manager (`00_manager.md`) に相談してください**。Manager が要件を理解し、適切な専門家チームを編成します。

### 複数の特性を一度に実装したい場合は？

Manager に「特性A、B、Cを実装したい」と伝えてください。Manager が Research Specialist に一括調査を依頼し、以降のフローを管理します。

### 従来のエージェントを直接使いたい場合は？

可能ですが、**推奨しません**。Manager を経由することで、引継ぎとレビューが自動化され、品質が向上します。

### Manager はどのように専門家を管理するのか？

1. **業務開始前**: プロジェクト概要、業務目的、前工程の成果物を説明
2. **業務完了後**: 成果物を仕様・目的と照合してレビュー
3. **問題発見時**: 該当専門家に差し戻して修正
4. **承認後**: 次の専門家に引継ぎ

---

## 開発者向けチェックリスト

新規開発者は以下を確認すること。

- [ ] [`project_context.md`](project_context.md) を読了
- [ ] [`effect_hierarchy.md`](effect_hierarchy.md) を読了
- [ ] [`architecture.md`](architecture.md) を読了
- [ ] [`agents/workflow.md`](agents/workflow.md) を読了（**新しいチーム構成を理解**）
- [ ] **Manager (`00_manager.md`) の役割を理解**
- [ ] Copilot Chat の使い方を理解

---

## 移行ガイド

### 従来の方法から新しい方法への移行

| 従来 | 新しい方法 |
|------|----------|
| Orchestrator に相談 | Manager に相談 |
| 各エージェントに順次依頼 | Manager が自動的に進行管理 |
| 手動でコンテキスト引継ぎ | Manager が自動的に引継ぎ |
| 成果物を自分でレビュー | Manager が各工程でレビュー |

**重要**: 従来の `00_orchestrator.md` は使用しないでください。`00_manager.md` を使用してください。

---

**注意**: 本ドキュメントは継続的に改善される。改善案や質問があればプロジェクトに反映すること。
