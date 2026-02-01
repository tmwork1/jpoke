# ワークフロー ガイド

本ドキュメントは、**プロジェクトマネージャーと専門家チーム**を活用して、ポケモン対戦システムを効率的に開発するためのガイドである。

## 新しいチーム構成

従来の一直線のリレー方式から、**1人のプロジェクトマネージャーと複数の専門家部下からなるチーム構成**に変更しました。

### チーム構造

```
ユーザー
   ↓
プロジェクトマネージャー (00_manager.md)
   ├─→ Research Specialist (05_research.md) - 仕様調査
   ├─→ Planning Specialist (10_planner.md) - タスク分解
   ├─→ Architecture Specialist (20_architect.md) - 設計
   ├─→ Coding Specialist (30_coder.md) - 実装
   ├─→ Testing Specialist (40_tester.md) - テスト
   ├─→ Code Review Specialist (50_reviewer.md) - レビュー
   └─→ Domain Expert (60_domain_expert.md) - 仕様確認
```

### 重要な改善点

1. **業務開始前の引継ぎ**: マネージャーが各専門家に、プロジェクト概要・業務目的・前工程の成果物を必ず説明
2. **成果物のレビュー**: マネージャーが各専門家の成果物を仕様・目的と照合してレビュー
3. **フィードバックループ**: 問題があれば該当専門家に差し戻して修正
4. **コンテキストの継続性**: プロジェクト全体の一貫性を保ちつつ進行

## 全体フロー

```
ユーザー: 新機能のリクエスト
    ↓
Manager: 要件理解・プロジェクト計画
    ↓
[必要に応じて]
Research Specialist: 仕様調査
    ↓
Manager: 調査結果レビュー
    ↓
Planning Specialist: タスク分解
    ↓
Manager: 計画レビュー・承認
    ↓
Architecture Specialist: 設計
    ↓
Manager: 設計レビュー・承認
    ↓
Coding Specialist: 実装
    ↓
Manager: 実装レビュー
    ↓
Testing Specialist: テスト
    ↓
Manager: テスト結果確認
    ↓
Code Review Specialist: 品質レビュー
    ↓
Manager: 最終確認
    ↓
Domain Expert: 仕様妥当性確認
    ↓
Manager: 完了確認・ユーザーへ報告
```

---

## 基本方針

- **ポケモンの仕様は第9世代（スカーレット・バイオレット）を参照する**
- **第9世代で実装されていない技・アイテム・特性・ポケモンなどは、実装を見送る**

---

## 重要な実装ルール

### EventContext の属性の使い分け

イベントの種類によって、使用すべき EventContext の属性が異なる：

| イベント種類 | 使用する属性 | 例 |
|------------|------------|---|
| **ダメージ計算関連** | `attacker`, `defender` | ON_CALC_POWER_MODIFIER, ON_CALC_DAMAGE_MODIFIER, ON_CALC_ATK_MODIFIER, ON_CALC_DEF_MODIFIER |
| **その他のイベント** | `source`, `target` | ON_SWITCH_IN, ON_TURN_END, ON_BEFORE_APPLY_AILMENT |

**重要**: Handler の `subject_spec` は、EventContext で使用される属性名と一致させる必要がある。

```python
# ✅ 正しい例（ダメージ計算）
Handler(
    はれ_power_modifier,
    subject_spec="attacker:self",  # EventContext(attacker=...) を使うため
    log="never",
)

# ❌ 間違った例
Handler(
    はれ_power_modifier,
    subject_spec="source:self",  # ダメージ計算では attacker を使うべき
    log="never",
)
```

### ダメージ補正値の基準

**すべてのダメージ関連補正は 4096 基準** で扱う：

| イベント | 初期値 | 補正の意味 |
|---------|-------|----------|
| ON_CALC_POWER_MODIFIER | 4096 | 技威力補正（例: 1.5倍 = 6144） |
| ON_CALC_ATK_MODIFIER | 4096 | 攻撃力補正 |
| ON_CALC_DEF_MODIFIER | 4096 | 防御力補正 |
| ON_CALC_ATK_TYPE_MODIFIER | 4096 | 攻撃タイプ補正 |
| ON_CALC_DEF_TYPE_MODIFIER | 4096 | 防御タイプ補正 |
| ON_CALC_DAMAGE_MODIFIER | 4096 | 最終ダメージ補正 |

**Handler での補正値の計算例**:

```python
# 0.5倍にする場合
return HandlerReturn(True, value // 2)  # 4096 → 2048

# 1.5倍にする場合
return HandlerReturn(True, value * 3 // 2)  # 4096 → 6144

# 1.3倍にする場合
return HandlerReturn(True, value * 5325 // 4096)  # 4096 → 5325
```

参考: [ポケモンWiki - ダメージ計算式](https://latest.pokewiki.net/%E3%83%80%E3%83%A1%E3%83%BC%E3%82%B8%E8%A8%88%E7%AE%97%E5%BC%8F#damageformula_detail)

---

### 乱数の使用ルール

**バトルに関する乱数は必ず `battle.random` を使用する**

これにより、シード値を指定することでバトルの再現性が保証されます。

**✅ 正しい例**:
```python
def まひ_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（25%確率）"""
    if battle.random.random() < 0.25:  # ✅ battle.random を使用
        return HandlerReturn(False)
    return HandlerReturn(True)
```

**❌ 間違った例**:
```python
def まひ_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（25%確率）"""
    import random
    if random.random() < 0.25:  # ❌ 標準ライブラリのrandomを使用
        return HandlerReturn(False)
    return HandlerReturn(True)
```

### テスト用の確率制御

確率的な動作をテストする場合は、`battle.test_option.ailment_trigger_rate` を使用します。

**テストコード例**:
```python
# 必ず発動する設定でテスト
battle.test_option.ailment_trigger_rate = 1.0
result = battle.events.emit(Event.ON_BEFORE_ACTION, EventContext(target=mon), None)

# 必ず発動しない設定でテスト
battle.test_option.ailment_trigger_rate = 0.0
result = battle.events.emit(Event.ON_BEFORE_ACTION, EventContext(target=mon), None)
```

**ハンドラ実装例**:
```python
def まひ_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（25%確率）"""
    # テスト用に確率を固定できる
    if battle.test_option.ailment_trigger_rate is not None:
        trigger = battle.test_option.ailment_trigger_rate >= 0.25
    else:
        trigger = battle.random.random() < 0.25
    
    if trigger:
        return HandlerReturn(False)
    return HandlerReturn(True)
```

### 状態異常の付与

状態異常を付与する際は、`Pokemon.apply_ailment()` メソッドを使用します。

**✅ 正しい例**:
```python
# 状態異常を付与
mon.apply_ailment(battle.events, "まひ")
```

**❌ 間違った例**:
```python
# 直接 Ailment インスタンスを作成して代入
from jpoke.model.ailment import Ailment
mon.ailment = Ailment("まひ")
mon.ailment.register_handlers(battle.events, mon)  # 手動でハンドラ登録が必要
```

**理由**:
- `apply_ailment()` は既存の状態異常のハンドラを自動的に解除
- 新しい状態異常のハンドラを自動的に登録
- 状態異常の上書き可否を制御（force パラメータ）

---

## 全体フロー

```
ユーザー: 新機能のリクエスト
    ↓
Research Agent: 仕様調査
    ↓
Documentation: リサーチ結果を文書化
    ↓
Orchestrator: 全体計画
    ↓
Planner: タスク分解
    ↓
Architect: 設計
    ↓
Coder: コード実装
    ↓
Tester: テスト実装
    ↓
Reviewer: コードレビュー
    ↓
Domain Expert: 仕様確認
    ↓
実装完了
```

---

## 具体的な使い方

### プロジェクト開始: Manager に相談する

**すべてのプロジェクトはManagerから開始します**

1. VS Code の Copilot Chat を開く（Ctrl + Shift + I）
2. `00_manager` を選択
3. ユーザーの要求を入力

```
新しい特性「いかく」を追加したい。
効果: 場に出た時、相手の攻撃ランクを1段階下げる
```

4. Manager が以下を実行:
   - 要件の理解・明確化
   - プロジェクト計画の策定
   - 必要な専門家の選定
   - 最初の専門家への業務依頼

5. Manager の指示に従って進める

---

### パターンA: 小〜中規模の新機能追加

**Manager が自動的に以下のフローを進行管理します**

#### Step 1: Planning（計画）

Manager が Planning Specialist に業務を依頼します。

```
Manager → Planning Specialist
- プロジェクト概要の引継ぎ
- タスク分解の依頼
```

Planning Specialist の成果物を Manager がレビューし、承認します。

#### Step 2: Architecture（設計）

Manager が Architecture Specialist に業務を依頼します。

```
Manager → Architecture Specialist
- プロジェクト概要の引継ぎ
- Planning の成果物を提供
- 設計の依頼
```

Architecture Specialist の成果物を Manager がレビューし、承認します。

#### Step 3: Coding（実装）

Manager が Coding Specialist に業務を依頼します。

```
Manager → Coding Specialist
- プロジェクト概要の引継ぎ
- Architecture の設計を提供
- 実装の依頼
```

Coding Specialist の成果物を Manager がレビューします。

#### Step 4: Testing（テスト）

Manager が Testing Specialist に業務を依頼します。

```
Manager → Testing Specialist
- プロジェクト概要の引継ぎ
- 実装コードを提供
- テスト作成・実行の依頼
```

Testing Specialist の成果物を Manager が確認します。

#### Step 5: Code Review（品質レビュー）

Manager が Code Review Specialist に業務を依頼します。

```
Manager → Code Review Specialist
- プロジェクト概要の引継ぎ
- 実装とテスト結果を提供
- 品質レビューの依頼
```

Code Review Specialist の成果物を Manager が確認します。

問題があれば、該当の専門家に差し戻して修正します。

#### Step 6: Domain Expert（仕様確認）

Manager が Domain Expert に業務を依頼します。

```
Manager → Domain Expert
- プロジェクト概要の引継ぎ
- 実装とテスト結果を提供
- Pokemon仕様との整合性確認を依頼
```

Domain Expert の成果物を Manager が確認します。

#### Step 7: 完了報告

Manager がすべての成果物が揃い、品質基準を満たしていることを確認し、ユーザーに報告します。

---

### パターンB: 複雑な仕様の実装（大規模）

**仕様が複雑な場合は、Research Specialist から開始します**

#### Step 0: Research（調査）

Manager が Research Specialist に業務を依頼します。

```
Manager → Research Specialist
- プロジェクト概要の引継ぎ
- 調査対象の特性・技・ルールを指定
- 仕様調査の依頼
```

Research Specialist の成果物（調査結果）を Manager がレビューし、方針を決定します。

#### Step 0.5: リサーチ結果の文書化

**調査結果は `docs/research/` に必ず保存します**

Manager が文書化を指示し、完了を確認します。

#### 以降はパターンAと同様

Planning → Architecture → Coding → Testing → Code Review → Domain Expert → 完了

---

### パターンC: バグ修正・改善

#### Step 1: 問題の把握

Manager がユーザーから問題を受け取り、内容を把握します。

#### Step 2: 仕様確認

Manager が Domain Expert に仕様確認を依頼します。

```
Manager → Domain Expert
- 問題の内容を提供
- 仕様の確認を依頼
```

#### Step 3: 修正方針決定

Manager が Domain Expert の確認結果をもとに修正方針を決定します。

#### Step 4: 修正実装

Manager が Coding Specialist に修正を依頼します。

```
Manager → Coding Specialist
- 問題の内容と修正方針を提供
- 修正実装を依頼
```

#### Step 5: テスト

Manager が Testing Specialist に回帰テストを依頼します。

```
Manager → Testing Specialist
- 修正内容を提供
- 回帰テストを依頼
```

#### Step 6: 完了確認

Manager がテスト結果を確認し、ユーザーに報告します。

---

## Manager の役割（重要）

### ユーザーとして Manager を使う際のポイント

1. **最初は Manager に相談する**
   - すべてのプロジェクトは Manager から開始
   - Manager が適切な専門家を選定し、業務を割り振る

2. **Manager が各専門家に引継ぎを行う**
   - プロジェクト概要
   - 業務目的
   - 前工程の成果物
   - 注意事項

3. **Manager が成果物をレビューする**
   - 仕様適合性
   - 完全性
   - 一貫性
   - 品質

4. **問題があれば差し戻す**
   - Manager が問題を指摘
   - 該当の専門家に修正を依頼
   - 修正後に再レビュー

5. **最終的にユーザーに報告**
   - すべての成果物が揃ったことを確認
   - プロジェクトサマリーを提供

---

## 従来との違い

### 従来の方式（一直線のリレー）

```
Orchestrator → Planner → Architect → Coder → Tester → Reviewer → Domain Expert
```

**問題点**:
- 前の工程の成果物が次に正しく引き継がれない
- 途中で問題が発生しても気づかずに進む
- 最後に大きな手戻りが発生する
- コンテキストが失われやすい

### 新しい方式（Manager + 専門家チーム）

```
Manager
  ├─ 業務引継ぎ → Specialist
  ├─ 成果物レビュー → Specialist
  ├─ 修正指示 → Specialist（必要時）
  └─ 次の Specialist へ
```

**改善点**:
- Manager が常にプロジェクト全体を把握
- 各工程で成果物を必ずレビュー
- 問題があれば即座に差し戻し
- コンテキストが継続的に保たれる
- 抜け漏れが大幅に削減

---

## 実装完了後の作業

**Manager がプロジェクト完了時に以下を確認・指示します**

### 1. ダッシュボード更新

```bash
python -m jpoke.utils.dashboard
```

### 2. README.md 更新

- 実装完了項目をリストに追加
- 進捗率の表を更新
- 実装日付を更新

### 3. リサーチ文書の最終更新

- `docs/research/` 内の該当ファイルに実装コードへのリンクを追加
- 実装中に発見した追加情報があれば記載
- 変更履歴に実装完了日を記録

### 4. 知識の反映

- 新しい設計パターン → `architecture.md` に追記
- よくあるエラーパターン → `workflow.md` のトラブルシューティングに追記
- ベストプラクティス → 該当エージェントの指示書に追記

---

## 効率的な使い方のコツ

### 1. Manager を信頼する

```
❌ やってはいけない:
各専門家に直接依頼する

✅ 推奨:
Manager に相談し、Manager が適切な専門家を選定
```

### 2. Manager が確認すること

| 確認項目 | 内容 |
|---------|------|
| 仕様適合性 | 元の要件を満たしているか |
| 完全性 | 抜け漏れがないか |
| 一貫性 | プロジェクト全体と矛盾していないか |
| 品質 | コード品質、テスト、ドキュメントが適切か |

### 3. 手戻りを避けるコツ

- Manager が各工程で必ずレビューする
- 問題があれば即座に差し戻す
- 次の工程に進む前に承認を得る

---

## 参考資料

- Project Manager: [`00_manager.md`](00_manager.md)
- Research Specialist: [`05_research.md`](05_research.md)
- Planning Specialist: [`10_planner.md`](10_planner.md)
- Architecture Specialist: [`20_architect.md`](20_architect.md)
- Coding Specialist: [`30_coder.md`](30_coder.md)
- Testing Specialist: [`40_tester.md`](40_tester.md)
- Code Review Specialist: [`50_reviewer.md`](50_reviewer.md)
- Domain Expert: [`60_domain_expert.md`](60_domain_expert.md)
