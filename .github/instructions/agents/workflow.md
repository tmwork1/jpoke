# ワークフロー ガイド

プロジェクトマネージャーと専門家チームによる効率的開発ガイド。

## チーム構成（6人体制）

```
Manager (00_manager.md)
  ├─ Research Specialist (10_research.md)
  │   └─ ポケモン仕様調査
  ├─ Planner (20_planner.md)
  │   └─ タスク分解
  ├─ Architect (30_architect.md)
  │   └─ 詳細設計
  ├─ Coder (40_coder.md)
  │   └─ 実装
  ├─ Tester (50_tester.md)
  │   └─ テスト
  └─ Reviewer (60_reviewer.md)
      └─ コード品質 + ポケモン仕様確認
```

**廃止:**
- Domain Expert（70_domain_expert.md）- Reviewer に統合

## 基本方針

- 第9世代（SV）準拠
- シングル対戦のみ
- 未実装機能は見送り

## 重要な実装ルール

### イベントContext の属性使い分け

| イベント種類 | 使用属性 | 例 |
|------------|---------|---|
| ダメージ計算 | `attacker`, `defender` | ON_CALC_*_MODIFIER |
| その他 | `source`, `target` | ON_SWITCH_IN, ON_TURN_END |

```python
# ダメージ計算
Handler(func, subject_spec="attacker:self")

# その他
Handler(func, subject_spec="source:self")
```

## 全体フロー

```
ユーザーリクエスト
    ↓
Manager（概要把握・計画）
    ↓
[Research調査が必要な場合]
    ↓
Planner（タスク分解）
    ↓
Manager確認
    ↓
Architect（詳細設計）
    ↓
Manager確認
    ↓
Coder（実装）
    ↓
Tester（テスト）
    ↓
Reviewer（品質 + 仕様確認）
    ↓
Manager最終承認
    ↓
ユーザーに報告
```

**特徴:** Manager が各工程で必ずレビュー・承認を行い、コンテキストを維持

## パターンA: 小〜中規模機能追加

仕様が明白で、既存パターンの拡張の場合：

```
Manager → Planner → Architect → Coder → Tester → Reviewer → Manager完了
```

## パターンB: 複雑な仕様（大規模）

新しいドメイン知識が必要な場合：

```
Manager → Research(調査) → Planner → Architect → Coder → Tester → Reviewer → Manager完了
```

研究成果は `docs/research/` に必ず保存。

## パターンC: バグ修正

```
Manager → Reviewer(仕様確認) → Coder(修正) → Tester(回帰テスト) → Manager完了
```

## パターンD: エッジケース対応

```
Manager → Reviewer(仕様確認) → Architect(詳細設計) → Coder → Tester → Reviewer → Manager完了
```

## Manager の役割

1. プロジェクト全体を把握
2. 専門家に業務引継ぎ
3. 成果物レビュー承認
4. 問題発見時は差し戻し
5. 完了時はユーザーに報告

## 実装完了後の作業

Manager が確認指示:

1. `python -m jpoke.utils.dashboard` 実行
2. README.md 更新
3. リサーチ文書に実装リンク追加
4. 新規知見を指示書に反映

## ベストプラクティス

### 作業前チェック
- 既存コードテスト確認
- READMEdocs/research 確認
- .github/instructions 確認

### 状態異常揮発性状態の付与

```python
# 推奨
mon.apply_ailment(battle.イベントs, "まひ")
mon.add_volatile(battle.イベントs, "みがわり", count=5, value=100)

# 非推奨（ハンドラ登録漏れのリスク）
mon.ailment = Ailment("まひ")
```

## 従来との違い

### 従来: 一直線リレー
問題点: コンテキスト喪失、手戻り大

### 新方式: Manager + 専門家チーム
改善: Manager が常時監督、即座にレビュー、コンテキスト維持

## 参考資料

各エージェント詳細:
- `00_manager.md` - Project Manager
- `10_research.md` - Research Specialist
- `20_planner.md` - Planning Specialist（タスク分解）
- `30_architect.md` - Architecture Specialist（詳細設計）
- `40_coder.md` - Coding Specialist
- `50_tester.md` - Testing Specialist
- `60_reviewer.md` - Code Review Specialist（品質 + 仕様確認）

**廃止（統合済み）:**
- `70_domain_expert.md` → Reviewer に統合
