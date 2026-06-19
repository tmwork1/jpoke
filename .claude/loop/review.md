# 再レビュー 自律ループ 指示書

**作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`

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
    "test_files":  ["tests/moves_status/"],
    "parallel_max": 3
  },
  "review_queue": ["..."],
  "in_progress":  [],
  "completed":    ["..."],
  "failed":       ["..."]
}
```

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/review_state.json` を Read で読み込む。

### 2. 終了チェック

`review_queue` と `in_progress` が両方空なら
→「{config.category} 全件レビュー完了: {completed}」と報告してループ終了（ScheduleWakeup を呼ばない）。

### 3. 収穫（Harvest）

`.loop/review_results/` 内のファイルを確認し、`in_progress` の各 entry の結果を回収する。

- `{entry}.ok` が存在 → `in_progress` から除き `completed` に追加、ファイルを削除
- `{entry}.fail` が存在 → `in_progress` から除き `failed` に追加、ファイルを削除

### 4. バッチ取り出し

`in_progress` が空で `review_queue` にエントリがある場合のみ実行：

`review_queue` の先頭から最大 `parallel_max` 件を取り出し、`in_progress` に追加する。

### 5. 並列レビュー

`in_progress` の各 entry を **background** で review エージェントに同時に渡す（1 つのレスポンスで複数の Agent 呼び出し）。

```
jpoke {config.category} 再レビュータスク: {entry}

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

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

5. テストのレビュー・修正
   {config.test_files} のテストを実装と照合する。
   誤り・過不足があれば修正する。
   python scripts/sort_tests.py {config.test_files をスペース区切り} でソート後、
   python -m pytest tests/ -v でテストを実行し、結果を .loop/test_logs/{entry}.log に保存する。
   全テストが通ることを確認する。

6. 修正内容を書き出す
   `docs/review/{entry}.md` を Write で作成し、以下の形式で記録する:

   ```markdown
   # {entry} レビュー結果

   ## 仕様書
   - （変更なし / 新規作成 / 修正した内容を箇条書き）

   ## 実装計画書
   - （変更なし / 新規作成 / 修正した内容を箇条書き）

   ## 実装（handlers/ / data/）
   - （変更なし / 修正した内容を箇条書き）

   ## テスト
   - （変更なし / 追加・修正した内容を箇条書き）
   ```

   修正がなかった項目は「変更なし」と記載する。

7. 進捗ファイルを更新する
   `{config.progress_file}` の {entry} 該当行を実装済みに更新する。

8. 結果を記録する
   成功: `.loop/review_results/{entry}.ok` を Write で作成（内容は空でよい）
   失敗: `.loop/review_results/{entry}.fail` を Write で作成（失敗理由を記述）
```

### 6. 状態ファイルを保存

Write ツールで `.loop/review_state.json` を上書き。

### 7. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=600, prompt="<<autonomous-loop-dynamic>>",
               reason="{config.category} 再レビューループ: 結果回収 → 次バッチへ")
```

---

## エラーハンドリング

- 同じ entry が `failed` に 2 回以上 → スキップして次へ
- `in_progress` のエントリが前回のウェイクアップから残っている場合、結果ファイルがなければ再度エージェントを起動する（再試行扱い）

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
    "test_files":  ["tests/moves_status/"],
    "parallel_max": 3
  },
  "review_queue": ["いえき", "いばる", "うたう"],
  "in_progress":  [],
  "completed":    ["あくび"],
  "failed":       []
}
```
