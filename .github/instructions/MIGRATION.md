# MIGRATION - アーカイブ

本ドキュメントは、2026年2月のドキュメント構成統合の記録です。

## 統合の目的

複数のファイルに分散されていた Copilot 用ドキュメントを一元的に整理：
- 読込順序を明確化
- 各ドキュメントの役割を定義
- エージェントワークフローを体系化

## 新構成

```
.github/
├── instructions/
│   ├── _README.md              ← ナビゲーション
│   ├── project_context.md      ← 背景・概要
│   ├── architecture.md         ← 詳細設計
│   ├── effect_hierarchy.md     ← 実装原則
│   └── agents/                 ← エージェント (8ファイル)
└── copilot-instructions.md     ← Entry point
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
