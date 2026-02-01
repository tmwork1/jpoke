# ワークフロー ガイド

本ドキュメントは、複数のエージェント(Copilot Chat の異なる役割)を活用して、ポケモン対戦システムを効率的に開発するためのガイドである。

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

## 全体フロー

```
ユーザー: 新機能のリクエスト
    ↓
Research Agent: 仕様調査
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

### Step 0: Research Agent で仕様調査

**複数の特性を実装する場合は必須**

1. VS Code の Copilot Chat を開く（Ctrl + Shift + I）
2. `05_research` を選択
3. リサーチ対象を入力

```
【リサーチ対象リスト】
以下の特性について詳しく調べてください。

1. テレパシー
2. ダウンロード
3. トレーシング

各特性について:
- 基本効果と発動条件
- 複数効果との相互作用
- エッジケース・バグ情報
```

4. Research Agent の出力を確認
5. 次のステップへ

---

### Step 1: Orchestrator に相談する

1. `00_orchestrator` を選択
2. 要件を入力

```
新しい特性「スキルスワップ」を追加したい。
効果: ターン開始時に相手の特性を一時的に奪う
```

3. Orchestrator の出力を確認

---

### Step 2: Planner にタスク分解を依頼

1. Orchestrator の出力をコピー
2. `10_planner` を選択
3. 以下を入力

```
[Orchestrator の出力]

このタスクを具体的なサブタスクに分解してください。
```

4. Planner の出力を確認

---

### Step 3: Architect に設計を依頼

1. Planner の出力をコピー
2. `20_architect` を選択
3. 以下を入力

```
[Planner の出力]

このタスク計画に基づいて技術設計を作成してください。
```

4. Architect の出力を確認

---

### Step 4: Coder にコーディングを依頼

1. Architect の出力をコピー
2. `30_coder` を選択
3. 以下を入力

```
[Architect の出力]

上記の設計に基づいてコードを実装してください。
```

4. 生成されたコードをエディタに貼り付け
5. 動作確認（インポートエラーなし、型ヒント OK など）

---

### Step 5: Tester にテスト実装を依頼

1. Coder の出力をコピー
2. `40_tester` を選択
3. 以下を入力

```
[Coder の出力]

上記の実装に対して、包括的なテストコードを作成してください。
```

4. テストコードをエディタに貼り付け
5. テスト実行

```bash
pytest tests/ability.py -v
```

---

### Step 6: Reviewer にコードレビューを依頼

1. 実装 + テストコードをコピー
2. `50_reviewer` を選択
3. 以下を入力

```
[実装コード + テストコード]

上記の実装とテストに対してコードレビューしてください。
```

4. Reviewer の出力を確認
   - **CRITICAL** 指摘がある場合 → Coder に修正依頼
   - 問題ない場合 → 次へ

---

### Step 7: Domain Expert に仕様確認を依頼

1. `60_domain_expert` を選択
2. 以下を入力

```
[実装コード + テストコード]

ポケモン対戦の仕様観点から、この実装をレビューしてください。
```

3. Domain Expert の出力を確認
   - ✅ 問題ない → **実装完了**
   - ⚠️ 要修正 → Coder/Architect に対応依頼
   - ❌ 不適切 → 設計段階へ巻き戻し

---

## 修正フロー

```
修正指摘あり
    ↓
Coder に修正内容を渡す
    ↓
修正実装を受け取る
    ↓
Tester に再度テスト
    ↓
Reviewer に再レビュー
    ↓
OK なら Domain Expert へ
```

---

## 効率的な使い方のコツ

### 1. コンテキストの活用

```
❌ やってはいけない:
「Coderエージェントでコード書いて」

✅ 推奨:
[Architectの出力全体をコピペ]
「上記の設計に基づいて実装してください」
```

### 2. 確認ポイント

| ステップ | 確認項目 |
|---------|---------|
| Research | 複数出典、信頼度評価あり |
| Planner | タスクの粒度適切、漏れなし |
| Architect | 既存コードとの矛盾なし |
| Coder | エラーなく動作 |
| Tester | テスト成功 |
| Reviewer | CRITICAL 指摘なし |
| Domain Expert | ゲームバランス OK |

### 3. 手戻りを避けるコツ

- Planner の段階でしっかり確認
- Architect で既存コードを必ず参考にする
- Coder の出力は動作確認してから Tester へ
- Reviewer で修正が出たら、修正内容を正確に Coder に伝える

---

## クイックスタート（小規模な機能の場合）

```
1. Planner で簡単にタスク分解
    ↓
2. Coder に「以下のタスクを実装してください」
    ↓
3. Tester で簡単なテスト
    ↓
4. Reviewer で最終チェック
```

---

## 参考資料

- Research Agent: [`05_research.md`](05_research.md)
- Orchestrator: [`00_orchestrator.md`](00_orchestrator.md)
- Planner: [`10_planner.md`](10_planner.md)
- Architect: [`20_architect.md`](20_architect.md)
- Coder: [`30_coder.md`](30_coder.md)
- Tester: [`40_tester.md`](40_tester.md)
- Reviewer: [`50_reviewer.md`](50_reviewer.md)
- Domain Expert: [`60_domain_expert.md`](60_domain_expert.md)
