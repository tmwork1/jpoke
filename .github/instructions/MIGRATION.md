# MIGRATION - アーカイブ

本ドキュメントは、ドキュメント構成の変遷記録です。

## 2026-02-07: 統合ワークフローへの移行

### 変更内容

エージェント分割を廃止し、統合ワークフローに移行。

**廃止**:
- `agents/` フォルダ（全8ファイル）
	- 00_manager.md
	- 10_research.md
	- 20_planner.md
	- 30_architect.md
	- 40_coder.md
	- 50_tester.md
	- 60_reviewer.md
	- workflow.md

**新設**:
- `workflow.md` - 統合開発ワークフロー（agents/の内容を統合）
- `knowledge/` - 知見蓄積フォルダ
	- patterns.md - 実装パターン集
	- abilities.md - 特性実装の知見
	- moves.md - 技実装の知見
	- damage_calc.md - ダメージ計算の知見
	- edge_cases.md - エッジケース集
	- troubleshooting.md - トラブルシューティング

**リネーム**:
- `effect_hierarchy.md` → `implementation_principles.md`

### 理由

**エージェント分割の問題点**:
- オーバーヘッド: エージェント間の引き継ぎコスト
- 形骸化: 実際は同じCopilotが全役割を演じる
- 分散: 情報が複数ファイルに散らばり検索困難
- 非実用的: 日常的な小規模タスクに不向き

**統合ワークフローの利点**:
- シンプル: 1-2ファイルで大半のケースをカバー
- 実用的: 実際の作業フローに即した構成
- 蓄積型: 知見が着実に蓄積され、再利用可能
- 効率的: 役割演技のオーバーヘッドなし

---

## 2026-02-01: エージェント構成変更（廃止済み）

Manager中心のチーム構成に変更（2026-02-07に統合ワークフローへ移行）

## 新構成

### 最終構成（2026-02-07時点）

```
.github/
├── copilot-instructions.md         ← Entry point
└── instructions/
	├── _README.md                  ← ナビゲーション
	├── workflow.md                 ← 統合ワークフロー
	├── implementation_principles.md ← 実装原則
	├── architecture.md             ← システム設計
	├── project_context.md          ← 背景知識
	├── knowledge/                  ← 知見蓄積
	│   ├── patterns.md
	│   ├── abilities.md
	│   ├── moves.md
	│   ├── damage_calc.md
	│   ├── edge_cases.md
	│   └── troubleshooting.md
	├── MIGRATION.md                ← 本ファイル
	└── CHANGELOG.md
```

### 旧構成（2026-02-01 ~ 2026-02-06）

.github/
└── instructions/
	├── _README.md
	├── project_context.md
	├── architecture.md
	├── effect_hierarchy.md
	└── agents/
		├── 00_manager.md
		├── 10_research.md
		├── 20_planner.md
		├── 30_architect.md
		├── 40_coder.md
		├── 50_tester.md
		├── 60_reviewer.md
		└── workflow.md
``` 

## 改善効果

| 項目 | Before | After |
|-----|--------|-------|
| サイズ | 142.52 KB | 69.34 KB (51% 削減) |
| 読む順序 | 不明確 | _README.md で明確 |
| 役割の明確性 | 曖昧 | 各ファイルで定義 |
| ファイル数 | 分散 | 一元化 |

## 参照先

詳細は `.github/instructions/_README.md` を参照してください。
