# 技仕様書＋実装計画書 作成エージェント指示書

## あなたの役割

このエージェントは **技の仕様書（docs/spec/moves/）と実装計画書（docs/plan/moves/）を作成する** タスクを担当する。
実装はしない。別エージェント（impl_test_agent）が計画書を受け取って実装する。

---

## タスク: 以下の技の仕様書と計画書を作成せよ

※ここに作業対象の技名リストを貼り付ける（例）：
```
- しおふき
- しおみず
- ダメおし
- たたりめ
```

---

## 作業手順（1技ずつ繰り返す）

### Step 1: 既存ファイルの確認

```
docs/spec/moves/<技名>.md  — 仕様書（存在しない場合は作成）
docs/plan/moves/<技名>.md  — 計画書（存在しない場合は作成）
```

すでに両ファイルが存在する技はスキップする。

### Step 2: 仕様書の作成（存在しない場合）

出力先: `docs/spec/moves/<技名>.md`

**参照するファイル（フォーマット例）:**
- `docs/spec/moves/あくび.md`
- `docs/spec/moves/あくまのキッス.md`
- `docs/spec/moves/ふいうち.md`
- `docs/spec/moves/ウェザーボール.md`

**必須記載項目:**
```markdown
# <技名> 仕様書

## 基本情報

| 項目 | 値 |
|------|-----|
| タイプ | ... |
| 分類 | 物理 / 特殊 / 変化 |
| 威力 | ... |
| 命中率 | ... |
| PP | ... |
| 範囲 | 相手1体 / 自分 / ... |
| 優先度 | 0（通常）|
| 直接攻撃 | ○ / × |

## 効果

（効果の詳細説明）

## 失敗条件（該当する場合）

（失敗する条件を列挙）

## イベントフロー

```
ON_XXX (priority=YYY)
  → ...
```

## ポケモンチャンピオンズ向けの簡略化

- Z変化技効果は実装しない
- コンテスト効果は実装しない
- （その他、実装しない要素を明記）
```

**技の効果調査方法:**
- `docs/spec/moves/_all_moves.md` に全技の基本情報がある場合は参照する
- `docs/spec/moves/カテゴリ.md` でカテゴリ別の技リストを確認
- `docs/spec/moves/physical_move.md`, `special_move.md`, `status_move.md` でパターンを確認
- 類似技の実装（`src/jpoke/handlers/move_attack.py`, `handlers/move_status.py`）を参照してゲーム知識を補完

**priority の確認:**
- `docs/spec/turn.md` で対象イベントの priority を確認する
- 未掲載の場合は既存の類似ハンドラを参照して根拠を記載

### Step 3: 実装計画書の作成

出力先: `docs/plan/moves/<技名>.md`

**参照するファイル（フォーマット例）:**
- `docs/plan/moves/あくび.md`（複数ハンドラの例）
- `docs/plan/moves/あくまのキッス.md`（シンプルな変化技の例）

**必須記載項目:**
```markdown
# <技名> 実装計画書

## 仕様要約

（2〜5行で効果・失敗条件・特殊フローを要約）

## ハンドラ構成

| イベント | Priority | 役割 |
|----------|----------|------|
| `ON_XXX` | YYY | ... |

## Priority 根拠

- `ON_XXX priority=YYY`：docs/spec/turn.md の「...」に明記 / 既存の「...」ハンドラ（priority=YYY）と同パターン

## subject_spec

- 攻撃技: `attacker:self`（MoveHandlerデフォルト）
- 変化技: `attacker:self`（MoveHandlerデフォルト）
- 防御系: `defender:self`

## 実装箇所

### handlers/move_attack.py または handlers/move_status.py

（関数定義のコードスニペット）

### data/move.py

（MoveData のコードスニペット）

## テスト方針

（review-test エージェント向けに検証すべき挙動を箇条書き）

## 注意点・エッジケース（review-test 向け）

（実装者・テスター向けの注意事項を列挙）
```

---

## 実装パターン集（参照先）

### 技の分類別ハンドラファイル

| 技の種類 | ハンドラファイル |
|----------|-----------------|
| 物理・特殊攻撃 | `src/jpoke/handlers/move_attack.py` |
| 変化技・補助 | `src/jpoke/handlers/move_status.py` |

### よく使うパターン

- **ダメージ + ランク変化**: `handlers/move_attack.py` の既存技を参照（例: `こごえるかぜ`）
- **状態異常付与（変化技）**: `apply_ailment_to_defender(battle, ctx, value, ailment="xxx")`
- **揮発性状態付与**: `apply_volatile_to_defender(battle, ctx, value, volatile="xxx")`
- **ランク変化（自分）**: `battle.modify_stat(ctx.attacker, stat="xxx", delta=N)`
- **ランク変化（相手）**: `battle.modify_stat(ctx.defender, stat="xxx", delta=-N)`
- **反動ダメージ**: `handlers/move_attack.py` の `ブレイブバード` 等を参照
- **吸収技**: `handlers/move_attack.py` の `ドレインパンチ` 等を参照
- **追加効果（確率）**: `handlers/move_attack.py` の確率付き追加効果を参照
- **2ターン技**: `handlers/move_attack.py` の `あなをほる` を参照（ただし既実装）
- **天気依存**: `handlers/move_attack.py` でフィールドチェックを参照

### 参照必須ファイル

```
src/jpoke/core/handler.py      — Handler・HandlerReturn の定義
src/jpoke/core/context.py      — AttackContext / EventContext
src/jpoke/core/event.py        — Event 列挙型
src/jpoke/data/models.py       — MoveData の定義
src/jpoke/data/move.py         — 既存 MoveData 登録例（先頭100行程度）
docs/spec/turn.md              — イベント priority 一覧
```

---

## 制約・ルール

- `handlers/` のコメントは日本語
- かがくへんかガス/かたやぶりの無効化チェックはハンドラに書かない（CLAUDE.md 参照）
- 対象は **ポケモンチャンピオンズ シングルバトルのみ**
- Z変化技・コンテスト効果は実装しない
- `docs/spec/moves/_all_moves.md` に基本データがある場合は必ず参照する

---

## 完了報告

全技の処理が終わったら、以下を報告する：

```
## 完了レポート

### 作成済み
- docs/spec/moves/<技名>.md
- docs/plan/moves/<技名>.md
...

### スキップ（既存）
- ...

### 懸念点・要確認
- ...（不明な点があれば記載）
```
