# 再レビュー 自律ループ 指示書

**ディスパッチャー作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`（状態ファイル読み書き・git merge・worktree の起動/削除はここで行う）
**レビュー作業ディレクトリ**: `{config.worktree_base}\slot{N}`（entry ごとの使い捨て worktree、ブランチ `reloop/{entry}`）

---

## 並列実行モデル

```
ディスパッチャー jpoke/                 : 状態管理・git merge・worktree の起動/削除のみ（main 固定・編集しない）
レビュー worktree {worktree_base}\slot1  : reloop/{entry} ブランチでレビュー・修正 [background]
レビュー worktree {worktree_base}\slot2  : reloop/{entry} ブランチでレビュー・修正 [background]
...（parallel_max 個まで）
```

`review_queue` から取り出したバッチ（最大 `parallel_max` 件）は、entry ごとに使い捨ての
worktree + ブランチを割り当てて並列に background レビューする。成功したエントリは
ディスパッチャーが main にマージして worktree・ブランチを削除する。
ユーザーのメイン作業ディレクトリ（jpoke/）は常に main のままで、ループが直接編集することはない。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "category":    "変化技",
    "wiki_hint":   "docs/wiki/ の一次情報を参照（moves/, volatiles/, fields/ 等）",
    "spec_dir":    "docs/spec/",
    "plan_dir":    "docs/plan/moves",
    "progress_file": "docs/progress/move.md",
    "review_dir":  "docs/review/moves/",
    "test_files":  ["tests/moves_status/"],
    "parallel_max": 3,
    "worktree_base": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-reloop"
  },
  "review_queue": ["..."],
  "in_progress":  [],
  "completed":    ["..."],
  "failed":       []
}
```

`in_progress` の要素は2種類ある:
- **文字列**（旧形式。worktree 対応前に開始されたエントリ。そのまま収穫し worktree 操作はしない）
- **オブジェクト** `{"name": "...", "slot": N, "branch": "reloop/{name}"}`（新形式。worktree で実行中）

新規にバッチ投入するエントリは常に新形式で `in_progress` に追加する。

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/review_state.json` を Read で読み込む。

### 2. 終了チェック

`review_queue` と `in_progress` が両方空なら
→「{config.category} 全件レビュー完了: {completed}」と報告してループ終了（ScheduleWakeup を呼ばない）。

### 3. 収穫（Harvest）

`.loop/review_results/` 内のファイルを確認し、`in_progress` の各 entry の結果を回収する。
entry が文字列か `{name, slot, branch}` オブジェクトかで扱いを分ける。

#### 3.1 旧形式（文字列 entry）

- `{entry}.ok` が存在 → `in_progress` から除き `completed` に追加、結果ファイルを削除
- `{entry}.fail` が存在 → `in_progress` から除き `failed` に追加、結果ファイルを削除
- どちらも存在しない → 実行中のまま維持

#### 3.2 新形式（オブジェクト entry、`name`/`slot`/`branch` を持つ）

- `{name}.ok` が存在 →
  1. ディスパッチャー作業ディレクトリ（jpoke/）で `git status --porcelain` を確認する。
     出力がある（ユーザーの未コミット変更が残っている）場合は merge を見送り、`.ok` ファイル・
     worktree・ブランチはそのまま残して次のウェイクアップで再試行する。
  2. クリーンなら `{branch}` を main にマージ（fast-forward 不可なら `--no-ff`）:
     ```bash
     git merge --no-ff {branch} -m "Merge {branch}"
     ```
  3. worktree を削除:
     ```bash
     git worktree remove "{config.worktree_base}\slot{slot}" --force
     ```
  4. ブランチを削除:
     ```bash
     git branch -d {branch}
     ```
  5. `.ok` ファイルを削除
  6. `in_progress` から除き `completed` に `name` を追加（文字列として追加し、既存の `completed` 配列と形式を揃える）
- `{name}.fail` が存在 →
  1. worktree を削除（存在する場合）:
     ```bash
     git worktree remove "{config.worktree_base}\slot{slot}" --force
     ```
  2. ブランチを削除:
     ```bash
     git branch -D {branch}
     ```
  3. `.fail` ファイルを削除
  4. `in_progress` から除き `failed` に `name` を追加
- どちらも存在しない → 実行中のまま維持

non-fast-forward で衝突が起きた場合は自動解決せず、`failed` に記録してユーザーに報告する
（worktree・ブランチは調査用に残す）。

### 4. バッチ取り出し

`in_progress` が空で `review_queue` にエントリがある場合のみ実行：

`review_queue` の先頭から最大 `parallel_max` 件を取り出し、1 から順にスロット番号（N）を割り当てる。
各エントリについて worktree を作成する（main の最新コミットから分岐）:

```bash
git worktree add -b "reloop/{entry}" "{config.worktree_base}\slot{N}" main
```

`in_progress` に `{"name": entry, "slot": N, "branch": "reloop/{entry}"}` を追加する。

### 5. 並列レビュー

`in_progress` のうち今回新規に作成した entry を **background** で review エージェントに同時に渡す
（1 つのレスポンスで複数の Agent 呼び出し）。

```
jpoke {config.category} 再レビュータスク: {entry}

作業ディレクトリ: {config.worktree_base}\slot{N}

このディレクトリは main から分岐した使い捨て worktree（ブランチ reloop/{entry}）。
以下を順に実施すること:

1. 一次情報の確認
   {config.wiki_hint} から {entry} に関する情報を読む。

2. 仕様書のレビュー・補充
   {config.spec_dir} に {entry} の仕様書が存在するか確認する。
   - 存在しない → 一次情報をもとに新規作成する
   - 存在する → 一次情報と照合し、誤り・欠落があれば修正する

3. 実装計画書のレビュー・補充
   {config.plan_dir}/{entry}.md が存在するか確認する。
   - 存在しない → 仕様書をもとに新規作成する（CLAUDE.md のハンドラ約束事を厳守）
   - 存在する → 仕様書と照合し、誤り・欠落があれば修正する

4. 実装のレビュー・修正
   handlers/ と data/ の実装を仕様書・計画書と照合する。
   誤り・欠落があれば修正する。
   handlers を修正した場合は python scripts/sort_handlers.py src/jpoke/handlers/<category>.py を実行する。
   data/ability.py・data/item.py・data/move.py を修正した場合、対応するスクリプト
   （scripts/sort_data/sort_abilities.py / scripts/sort_data/sort_items.py / scripts/sort_data/sort_moves.py）を実行する。

5. リーサル計算のレビュー・実装
   `{config.progress_file}` の {entry} 行の「リーサル実装」列を確認する。
   - `n/a` または `保留` → 対象外なのでスキップする
   - `x` → handlers/lethal.py の既存ハンドラを仕様書・実装（handlers/ / data/）と照合し、
     誤り・欠落があれば修正する
   - `-` → 仕様書をもとに新規にリーサル計算ハンドラを実装する
     - handlers/lethal.py の既存パターン（`_heal`, `_heal_at_pinch` など）を参照する
     - シグネチャ: `(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist`
     - {entry} の種別に対応する data ファイルの `lethal_handlers` にエントリを追加する
       （move → data/move.py, item → data/item.py, ability → data/ability.py,
       ailment → data/ailment.py, volatile → data/volatile.py, global_field → data/field.py）
     - イベントは `LethalEvent.ON_BEFORE_HIT` / `ON_HIT` / `ON_TURN_END` / `ON_EVERY_EVENT` から選ぶ
     - subject は `"attacker"` / `"defender"` / `None` から選ぶ
   handlers/lethal.py を修正した場合は python scripts/sort_handlers.py src/jpoke/handlers/lethal.py を実行する。
   data/*.py を修正した場合は対応する sort スクリプトを実行する。

6. テストのレビュー・修正
   {config.test_files} のテストを実装と照合する。
   誤り・過不足があれば修正する。
   手順5でリーサル計算ハンドラを新規実装・修正した場合は tests/test_lethal.py にも
   `t.calc_lethal` を使ったテストを追加・修正する。
   python scripts/sort_tests.py {config.test_files をスペース区切り}（リーサルを触った場合は tests/test_lethal.py も追加）でソート後、
   python scripts/generate_test_list.py でテスト一覧を更新し、
   python -m pytest tests/ -v でテストを実行し、結果を .loop/test_logs/{entry}.log に保存する。
   全テストが通ることを確認する。

7. 修正内容を書き出す
   `{config.review_dir}{entry}.md` を Write で作成し、以下の形式で記録する:

   ```markdown
   # {entry} レビュー結果

   ## 仕様書
   - （変更なし / 新規作成 / 修正した内容を箇条書き）

   ## 実装計画書
   - （変更なし / 新規作成 / 修正した内容を箇条書き）

   ## 実装（handlers/ / data/）
   - （変更なし / 修正した内容を箇条書き）

   ## リーサル計算
   - （対象外 / 変更なし / 新規実装 / 修正した内容を箇条書き）

   ## テスト
   - （変更なし / 追加・修正した内容を箇条書き）
   ```

   修正がなかった項目は「変更なし」、対象外の場合は「対象外」と記載する。

8. 進捗ファイルを更新する
   `{config.progress_file}` の {entry} 該当行のテスト済みマークを更新する。
   手順5でリーサル計算を新規実装・修正した場合は「リーサル実装」「リーサルテスト」列も
   `x` に更新する（対象外だった場合は変更しない）。

9. 変更をすべてコミットする:
   git add -A
   git commit -m "review: {entry}"

10. 結果を記録する
   成功: {プロジェクトルート}\.loop\review_results\{entry}.ok を Write で作成（内容は空でよい、
        パスは作業ディレクトリ外の絶対パス: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.ok）
   失敗: 同様に {entry}.fail を Write で作成（失敗理由を記述）
```

### 6. 状態ファイルを保存

Write ツールで `.loop/review_state.json` を上書きし、ディスパッチャー作業ディレクトリ（jpoke/）で
コミットする（`.loop/*.json` は git 管理下にあるため、コミットせず放置すると jpoke/ が常に
dirty 判定になり手順 3.2 の merge が永久にブロックされる）:
```bash
git add .loop/review_state.json
git commit -m "chore: レビューループ状態更新（...）"
```

### 7. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=600, prompt="<<autonomous-loop-dynamic>>",
               reason="{config.category} 再レビューループ: 結果回収 → 次バッチへ")
```

---

## エラーハンドリング

- 同じ entry が `failed` に 2 回以上 → スキップして次へ
- `in_progress` のエントリが前回のウェイクアップから残っている場合、結果ファイルがなければ再度エージェントを起動する（再試行扱い）
- merge 時に jpoke/ がクリーンでない → merge を見送り次回再試行（`.ok` ファイル・worktree・ブランチはそのまま残す）
- non-fast-forward で衝突 → 自動解決せず `failed` に記録して報告（worktree・ブランチは調査用に残す）

---

## 状態例

```json
{
  "config": {
    "category":    "変化技",
    "wiki_hint":   "docs/wiki/ の一次情報を参照（moves/, volatiles/ 等）",
    "spec_dir":    "docs/spec/moves/",
    "plan_dir":    "docs/plan/moves",
    "progress_file": "docs/progress/move.md",
    "review_dir":    "docs/review/moves/",
    "test_files":  ["tests/moves_status/"],
    "parallel_max": 3,
    "worktree_base": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-reloop"
  },
  "review_queue": ["いえき", "いばる", "うたう"],
  "in_progress":  [],
  "completed":    ["あくび"],
  "failed":       []
}
```
