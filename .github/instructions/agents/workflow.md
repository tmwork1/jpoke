# ワークフロー

6人体制による段階的開発（Manager中心）

## チーム構成

```
Manager (00_manager.md)
  ├─ Research (10) - 仕様調査
  ├─ Planner (20) - タスク分解
  ├─ Architect (30) - 詳細設計
  ├─ Coder (40) - 実装
  ├─ Tester (50) - テスト
  └─ Reviewer (60) - 品質+仕様確認
```

## 基本方針

- 第9世代（SV）準拠
- シングル対戦のみ
- Manager が各工程でレビュー・承認

## 全体フロー

```
ユーザーリクエスト
    ↓
Manager（概要把握）
    ↓
[Research必要な場合]
    ↓
Planner → Manager確認
    ↓
Architect → Manager確認
    ↓
Coder → Tester → Reviewer
    ↓
Manager最終承認 → ユーザー報告
```

## パターン

### A: 小〜中規模機能
仕様明白で既存パターン拡張：
```
Manager → Planner → Architect → Coder → Tester → Reviewer → Manager完了
```

### B: 複雑な仕様（大規模）
新規ドメイン知識必要：
```
Manager → Research → Planner → Architect → Coder → Tester → Reviewer → Manager完了
```

### C: バグ修正
```
Manager → Reviewer → Coder → Tester → Manager完了
```

### D: エッジケース対応
```
Manager → Reviewer → Architect → Coder → Tester → Reviewer → Manager完了
```

## Manager責務

1. プロジェクト全体把握
2. 専門家に業務引継ぎ
3. 成果物レビュー・承認
4. 問題発見時は差し戻し
5. 完了時はユーザーに報告

## 実装完了後

1. `python -m jpoke.utils.dashboard` 実行
2. README.md更新
3. リサーチ文書に実装リンク追加
4. 新規知見を指示書に反映

## 参考資料

- 00_manager.md
- 10_research.md
- 20_planner.md
- 30_architect.md
- 40_coder.md
- 50_tester.md
- 60_reviewer.md
