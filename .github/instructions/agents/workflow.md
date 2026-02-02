# ワークフロー ガイド

プロジェクトマネージャーと専門家チームによる効率的開発ガイド。

## チーム構成

```
Manager (00_manager.md)
  Research Specialist (10_research.md) - 仕様調査
  Planner (20_planner.md) - タスク分解
  Architect (30_architect.md) - 設計
  Coder (40_coder.md) - 実装
  Tester (50_tester.md) - テスト
  Reviewer (60_reviewer.md) - レビュー
  Domain Expert (70_domain_expert.md) - 仕様確認
```

## 基本方針

- 第9世代（SV）準拠
- シングル対戦のみ
- 未実装機能は見送り

## 重要な実装ルール

### EventContext の属性使い分け

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
ユーザー  Manager  [Research ] Planner  Architect  Coder  Tester  Reviewer  Domain Expert  完了報告
```

Manager が各工程で:
1. 業務引継ぎ（概要目的成果物）
2. 成果物レビュー
3. 問題あれば差し戻し

## パターンA: 小〜中規模機能追加

```
Manager  Planner  Architect  Coder  Tester  Reviewer  Domain Expert
```

各工程で Manager がレビュー承認。

## パターンB: 複雑な仕様（大規模）

```
Manager  Research  [文書化]  Planner  ...
```

調査結果は `docs/research/` に保存必須。

## パターンC: バグ修正

```
Manager  Domain Expert(仕様確認)  Coder(修正)  Tester(回帰テスト)  完了
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
mon.apply_ailment(battle.events, "まひ")
mon.add_volatile(battle.events, "みがわり", count=5, value=100)

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
- `10_research.md` - Research
- `20_planner.md` - Planning
- `30_architect.md` - Architecture
- `40_coder.md` - Coding
- `50_tester.md` - Testing
- `60_reviewer.md` - Review
- `70_domain_expert.md` - Domain Expert
