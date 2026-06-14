# 技実装＋テスト エージェント指示書

## あなたの役割

このエージェントは **すでに実装計画書（docs/plan/moves/）が存在する技を実装し、テストを書いて通す** タスクを担当する。
仕様書・計画書の作成は別エージェント（spec_plan_agent）が担当する。

---

## タスク: 以下の技を実装してテストを通せ

※ここに作業対象の技名リストを貼り付ける（事前に計画書が存在するもののみ）：
```
- あくび
- あくまのキッス
```

---

## 前提確認

作業開始前に各技の計画書が存在することを確認する：
```
docs/plan/moves/<技名>.md  — 存在しない場合は作業できない（spec_plan_agent に依頼）
```

---

## 作業手順（1技ずつ繰り返す）

### Step 1: 計画書の読み込み

`docs/plan/moves/<技名>.md` を読む。
以下を把握する：
- ハンドラ構成（イベント名・priority）
- 実装箇所（handlers/xxx.py, data/move.py）
- コードスニペット（そのまま使用可）
- テスト方針・エッジケース

### Step 2: 既存コードの確認

```
src/jpoke/handlers/move_attack.py   — 物理・特殊攻撃ハンドラ
src/jpoke/handlers/move_status.py   — 変化技ハンドラ
src/jpoke/data/move.py              — MoveData 登録
```

五十音順の挿入位置を確認する（handlers と data で順番を揃える）。

### Step 3: ハンドラ実装

対象ファイル: `src/jpoke/handlers/move_attack.py` または `src/jpoke/handlers/move_status.py`

**ルール:**
- 関数名は `<技名>_<役割>` の形式（例: `あくび_can_apply`, `あくび_apply_volatile_to_defender`）
- 配置は五十音順
- 計画書のコードスニペットをベースに実装
- コメントは日本語
- かがくへんかガス/かたやぶりの無効化チェックは書かない

### Step 4: data/move.py への登録

`src/jpoke/data/move.py` の MoveData に handlers を追加する。
五十音順の位置に挿入する。

### Step 5: テストの作成

対象ファイル: `tests/test_move.py`（既存の技テストに追記）

**参照すべきファイル:**
```
tests/test_utils.py         — start_battle / run_move / run_switch などのユーティリティ
tests/test_move.py          — 既存テスト（フォーマット・パターン参照）
```

**テスト関数名の規則:**
```python
def test_<技名>_<確認内容>():
```

**テスト作成ガイド:**
1. 計画書の「テスト方針」と「注意点・エッジケース」を必ず全てカバーする
2. 必要に応じて `start_battle(accuracy=100)` で命中を固定する
3. 各テスト関数は1つの挙動を検証する（小さく作る）
4. `assert` の条件は具体的に書く

**典型的なテストパターン:**
```python
# 基本効果の確認
def test_あくまのキッス_ねむり付与():
    battle = t.start_battle(...)
    t.run_move(battle, "あくまのキッス")
    assert battle.team1[0].ailment == "ねむり"

# 失敗条件の確認
def test_あくまのキッス_状態異常持ちには失敗():
    battle = t.start_battle(...)
    battle.team1[0].ailment = "まひ"
    t.run_move(battle, "あくまのキッス")
    assert battle.team1[0].ailment == "まひ"  # 変化していない
```

### Step 6: テストの並び替えと実行

```powershell
# 1. 五十音順にソート
python scripts/sort_tests.py tests/test_move.py

# 2. 全テスト実行
python -m pytest tests/ -v

# 3. 実装した技のテストだけ実行（確認用）
python -m pytest tests/test_move.py -k "<技名>" -v
```

テストが通ったら次の技へ進む。失敗した場合はエラーを読んで修正する。

### Step 7: 進捗の更新

`docs/progress/move.md` の該当行を更新する：

変更前:
```
| ☐ | あくまのキッス | - | - | - |
```

変更後:
```
| ✓ | あくまのキッス | - | - | 実装済み | ✓ |
```

（仕様書がある場合は仕様書欄も `○` に更新する）

---

## 1技完了後の確認チェックリスト

- [ ] handlers/move_attack.py または move_status.py に関数追加済み（五十音順）
- [ ] data/move.py に MoveData ハンドラ登録済み（五十音順）
- [ ] tests/test_move.py にテスト追加済み
- [ ] `python scripts/sort_tests.py tests/test_move.py` 実行済み
- [ ] `python -m pytest tests/ -v` で全テスト PASSED
- [ ] docs/progress/move.md 更新済み

---

## 実装時の参照ファイル（必ず最初に読む）

```
src/jpoke/core/handler.py      — Handler・HandlerReturn の定義
src/jpoke/core/context.py      — AttackContext / EventContext のフィールド
src/jpoke/core/event.py        — Event 列挙型
src/jpoke/data/models.py       — MoveData の定義
docs/spec/turn.md              — イベント priority 一覧
```

---

## 制約・ルール

- `Pokemon.hp` に直接代入禁止 → 必ず `battle.modify_hp(...)` を使う
- ランク変化は `battle.modify_stat(...)` または `battle.modify_stats(...)`
- コメント・テスト関数名は日本語
- 型アノテーションは Python 3.10+ 構文（`X | Y`, `list[X]`）
- かがくへんかガス/かたやぶりの無効化チェックはハンドラに書かない

---

## 完了報告

全技の処理が終わったら、以下を報告する：

```
## 完了レポート

### 実装完了
- <技名>: テスト N 件追加、全テスト PASSED
...

### 失敗・スキップ
- <技名>: 計画書未存在 / テスト失敗の詳細
...

### 懸念点・要確認
- ...
```
