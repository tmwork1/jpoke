# Copilot Instructions ガイド

本ディレクトリは、GitHub Copilot を使用した開発手順を体系的にまとめたものである。

## 構造変更: 統合ワークフローへの移行

**2026年2月7日: エージェント分割を廃止し、統合ワークフローに移行しました**

従来の明示的なエージェント分割から、**単一の包括的なワークフローと知見蓄積フォルダ**に変更しました。これにより、実運用での効率性と実用性が大幅に向上します。

### 新しい構造

```
.github/instructions/
├── workflow.md                      # 統合開発ワークフロー（全工程を網羅）
├── implementation_principles.md     # 実装場所の判断基準
├── architecture.md                  # システム技術詳細
├── project_context.md               # プロジェクト背景
├── knowledge/                       # 知見蓄積フォルダ
│   ├── patterns.md                  # 実装パターン集
│   ├── abilities.md                 # 特性実装の知見
│   ├── moves.md                     # 技実装の知見
│   ├── damage_calc.md               # ダメージ計算の知見
│   ├── edge_cases.md                # エッジケース集
│   └── troubleshooting.md           # トラブルシューティング
├── MIGRATION.md                     # 移行ログ
└── CHANGELOG.md                     # 変更履歴
```

## 基本方針

- **第9世代（SV）仕様準拠**: 第9世代で実装されていない要素は見送る
- **シングル対戦のみ**: ダブルバトルは対象外
- **イベント駆動**: すべての効果はイベント/Handlerで実装
- **完遂主義**: コード追加・修正時はテスト・レビューまで完遂
- **推測継続**: ユーザへの確認はせず、不明点は推測して進める

---

## 推奨読解順序

### 開発着手前（必須）
1. [`project_context.md`](project_context.md) - プロジェクト背景とアーキテクチャ概要（10-15分）
2. [`implementation_principles.md`](implementation_principles.md) - 実装場所の判断基準（10-15分）
3. [`architecture.md`](architecture.md) - 詳細なシステム設計（20-30分）
4. **既存実装・テスト・ドキュメントの確認**（該当領域のコード、tests、README、docs/spec）

### 新機能実装時
1. [`workflow.md`](workflow.md) - 開発フロー全体（調査→計画→設計→実装→テスト→レビュー）
2. [`knowledge/patterns.md`](knowledge/patterns.md) - よく使う実装パターン
3. 必要に応じて [`knowledge/`](knowledge/) 内の関連知見を参照

### トラブル発生時
1. [`knowledge/troubleshooting.md`](knowledge/troubleshooting.md) - よくある問題と解決策
2. [`knowledge/edge_cases.md`](knowledge/edge_cases.md) - エッジケース集

---

## ドキュメント詳細

### コアドキュメント

#### [`workflow.md`](workflow.md)
開発フロー全体を1ファイルで完結。以下の全Phaseを網羅:
- Phase 1: 調査（仕様理解）
- Phase 2: 計画（タスク分解）
- Phase 3: 設計（技術設計）
- Phase 4: 実装（コード作成）
- Phase 5: テスト（単体・統合テスト）
- Phase 6: レビュー（品質・仕様確認）

各Phaseごとに、チェックリスト・出力形式・ベストプラクティスを記載。

#### [`implementation_principles.md`](implementation_principles.md)
**どこに実装すべきか**の判断基準:
- 効果の所有者原則
- 作用のヒエラルキー（状態変更→状態影響→補正）
- イベント駆動の原則

#### [`architecture.md`](architecture.md)
システムの技術詳細:
- イベント駆動システム
- Handler派生クラス
- Battle設計
- RoleSpec使い分け
- ダメージ計算

#### [`project_context.md`](project_context.md)
プロジェクトの背景・目的・制約事項

### 知見蓄積フォルダ（`knowledge/`）

実装時に得られた知見・パターン・落とし穴を蓄積:

#### [`patterns.md`](knowledge/patterns.md)
よく使う実装パターン:
- Handler基本パターン
- RoleSpec使い分け
- データ定義パターン
- テストパターン

#### [`abilities.md`](knowledge/abilities.md)
特性実装の知見:
- 発動タイミング別パターン
- 複雑な特性の実装
- エッジケース

#### [`moves.md`](knowledge/moves.md)
技実装の知見:
- 技の基本構造
- 追加効果・複数効果
- 特殊威力計算

#### [`damage_calc.md`](knowledge/damage_calc.md)
ダメージ計算の知見:
- 計算フロー
- 4096基準の使い方
- イベント使い分け

#### [`edge_cases.md`](knowledge/edge_cases.md)
エッジケース集:
- 交代関連
- 状態異常関連
- フィールド効果関連
- ダメージ計算関連

#### [`troubleshooting.md`](knowledge/troubleshooting.md)
よくある問題と解決策:
- Handlerが発動しない
- ダメージが期待値と違う
- テストが失敗する

---

## ワークフロー例

### 新規特性1件の追加

```
1. workflow.md を開く
2. Phase 1（調査）: 特性仕様を調査 → docs/spec/ability/[特性名].md
3. Phase 2（計画）: タスク分解（不要ならスキップ）
4. Phase 3（設計）: データ構造・Handler設計
5. Phase 4（実装）: 
   - data/ability.py にデータ追加
   - handlers/ability.py にHandler実装
6. Phase 5（テスト）: tests/test_ability.py にテスト追加
7. Phase 6（レビュー）: 品質・仕様確認
8. 完了: dashboard更新、README更新、knowledge/に知見追記
```

### バグ修正

```
1. workflow.md → パターンB: バグ修正 を参照
2. Phase 6（レビュー）: 原因特定・影響範囲調査
3. Phase 4（実装）: 修正コード
4. Phase 5（テスト）: 修正テスト・回帰テスト
5. Phase 6（レビュー）: 再確認
6. 完了: knowledge/troubleshooting.md に知見追記
```

### 複雑な相互作用（大規模）

```
1. workflow.md → パターンD: 複雑な相互作用 を参照
2. Phase 1（調査）: 詳細仕様調査
3. Phase 2（計画）: 複数技術要素の分解
4. Phase 6（レビュー）: 既存実装調査
5. Phase 3（設計）: 統合設計
6. Phase 4-6: 段階的実装（機能単位）
7. 完了: docs/review/に包括的レビュー文書作成
```

---

## 利用上の注意点

### 推奨される使用方法

1. **copilot-instructions.md を起点に**: 基本方針・核心概念を確認
2. **workflow.md で全体フロー把握**: 自分のタスクがどのPhaseか確認
3. **knowledge/ で実装パターン参照**: 同様の実装例を確認
4. **問題発生時は troubleshooting.md**: 即座に解決策を確認

### ✅ 新しい方法の利点

- **シンプル**: 1-2ファイルで大半のケースをカバー
- **実用的**: 実際の作業フローに即した構成
- **蓄積型**: 知見が着実に蓄積され、再利用可能
- **効率的**: 役割演技のオーバーヘッドなし

### ❌ 旧方法の問題点（廃止理由）

- **オーバーヘッド**: エージェント間の引き継ぎコスト
- **形骸化**: 実際は同じCopilotが全役割を演じる
- **分散**: 情報が複数ファイルに散らばり検索困難
- **非実用的**: 日常的な小規模タスクに不向き

---

## 知見の蓄積

新しい知見・パターン・落とし穴を発見したら、積極的に [`knowledge/`](knowledge/) に追記:

```markdown
<!-- knowledge/patterns.md の末尾に追記 -->

## 最新パターン（随時追記）

### パターン名：XXX

\`\`\`python
# 実装例
\`\`\`

**使用例**: [ケース]
**注意点**: [落とし穴]
```

---

## FAQ

**Q: どのドキュメントから読むべき？**
A: 新規参加なら `project_context.md` → `architecture.md`。実装なら `workflow.md` → `knowledge/patterns.md`。

**Q: エージェント指示は使わないの？**
A: 廃止しました。実運用では `workflow.md` 1ファイルの方が効率的でした。

**Q: 旧agents/フォルダは？**
A: 削除しました。内容は `workflow.md` に統合済み。

**Q: 知見はどこに記録？**
A: `knowledge/[カテゴリ].md` に追記。パターン・落とし穴・解決策を記録。

**Q: 実装場所がわからない**
A: `implementation_principles.md` で判断基準確認。所有者原則＋ヒエラルキーで判断。

---

## 更新履歴

- **2026-02-07**: エージェント分割を廃止、統合ワークフローへ移行
  - workflow.md 作成（agents/全ファイルを統合）
  - knowledge/ フォルダ新設（知見蓄積）
  - effect_hierarchy.md → implementation_principles.md にリネーム
  
- **2026-02-01**: エージェント構成をManager中心に変更（※既に廃止）

- **2026-01-XX**: 初版作成
