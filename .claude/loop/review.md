# 再レビュー 自律ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `review`、方式は統合ブランチ）。
- **統合 worktree**: `{config.worktree_base}\integration`（ブランチ `loop/review/integration`。
  マージ・整形・状態集約をここで行う）。
- **レビュー worktree**: `{config.worktree_base}\slot{N}`（entry ごとの使い捨て、ブランチ
  `loop/review/{entry}`。`loop/review/integration` から分岐）。

並列モデル: 統合 worktree にディスパッチャーが集約し、slot1..slot{parallel_max} で background
review エージェントが並列にレビュー・修正する。`loop/review/{entry}` は成功したら
`loop/review/integration` にマージ。ソート・テスト一覧生成は slot では行わず §共通5 で一括実行する。
**ローリング・ディスパッチ**: `in_progress` が全件完了するのを待たず、1 件完了するたびにその場で
収穫・マージし、空いたスロットに `review_queue` の次の entry を即座に補充する（§4）。常に
`parallel_max` 件が稼働している状態を維持する。

---

## 状態ファイルのスキーマ

`.loop/` は git 管理外（§共通3）。

```json
{
  "config": {
    "flow":        "review",
    "category":    "変化技",
    "wiki_hint":   "docs/wiki/ の一次情報を参照（moves/, volatiles/, fields/ 等）",
    "spec_dir":    "docs/spec/",
    "plan_dir":    "docs/plan/moves",
    "progress_file": "docs/progress/move.md",
    "review_dir":  "docs/review/moves/",
    "test_files":  ["tests/moves_status/"],
    "parallel_max": 3,
    "worktree_base": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\review"
  },
  "review_queue": ["..."],
  "in_progress":  [],
  "completed":    ["..."],
  "failed":       [],
  "unformatted_merges": 0,
  "last_format_commit": "..."
}
```

`in_progress` の要素は `{"name": "...", "slot": N, "branch": "loop/review/{name}"}` 形式のオブジェクト。

`unformatted_merges` / `last_format_commit` は §共通5（10 件ごとの一括整形）で使う。統合 worktree を
初回作成した直後は `last_format_commit` をそのときの HEAD で初期化する。

---

## 実行手順

### 0. 統合 worktree を用意する

§共通4 パターンB を適用する（`INTG="{config.worktree_base}\integration"`、`BR="loop/review/integration"`）。
以降の git 操作はすべて `git -C "$INTG" ...`。

### 1. 状態ファイルを読む

`.loop/review_state.json` を Read で読み込む（存在しなければ初回起動）。

### 2. 終了チェック

`review_queue` と `in_progress` が両方空なら、`unformatted_merges > 0` の場合は §3.3 の整形を
先に実行してから、「{config.category} 全件レビュー完了: {completed}」と報告してループ終了。

### 3. 収穫（Harvest）

`.loop/review_results/` のファイルを確認して `in_progress` の各 entry の結果を回収する。

各 entry（`{name, slot, branch}`）について:

- `{name}.ok` が存在 →
  1. マージ: `git -C "$INTG" merge --no-ff {branch} -m "Merge {branch}"`
     （統合 worktree はループ専用で常にクリーン。dirty チェック不要）
  2. worktree 削除: `git -C "$INTG" worktree remove "{config.worktree_base}\slot{slot}" --force`
  3. ブランチ削除: `git -C "$INTG" branch -d {branch}`
  4. `.ok` ファイルを削除（§共通9 のガード付き rm を使う）
  5. `in_progress` から除き `completed` に `name`（文字列）を追加
  6. `unformatted_merges += 1`
- `{name}.fail` が存在 →
  1. worktree 削除（存在すれば、上と同じ）
  2. `git -C "$INTG" branch -D {branch}`
  3. `.fail` ファイルを削除（§共通9 のガード付き rm を使う）
  4. `in_progress` から除き `failed` に `name` を追加
- どちらも存在しない → 実行中のまま維持

non-fast-forward 衝突時は §共通8 に従う。

#### 3.3 一括整形（未整形マージが 10 件たまったら）

`unformatted_merges >= 10` の場合のみ実行する。

§共通5 を適用する。`{フロー固有のテストファイル群}` = `{config.test_files をスペース区切り} tests/test_lethal.py`。

### 4. 不足分の補充（ローリング・ディスパッチ）

`review_queue` にエントリがあり、かつ `len(in_progress) < config.parallel_max` の場合に実行する。
`in_progress` が空になるのを待たない — 1 件完了するたびに、その場で空いた分だけ補充する。

不足数（`config.parallel_max - len(in_progress)`）だけ `review_queue` の先頭から取り出す。スロット
番号 N は「1〜`parallel_max` のうち `in_progress` が現在使っていない最小の番号」を割り当てる
（直前の収穫で空いたスロットをそのまま再利用する。1 から詰め直さない）。各エントリで worktree を
作成（`loop/review/integration` の最新から分岐）:

```bash
git -C "$INTG" worktree add -b "loop/review/{entry}" "{config.worktree_base}\slot{N}" loop/review/integration
```

作成後、§共通4.5 を適用する（`<worktree>` = `{config.worktree_base}\slot{N}`）。

`in_progress` に `{"name": entry, "slot": N, "branch": "loop/review/{entry}"}` を追加。

### 5. 並列レビュー

今回新規作成した entry を **background** で review エージェントに同時に渡す（1 レスポンスで複数 Agent 呼び出し）:

```
jpoke {config.category} 再レビュータスク: {entry}

作業ディレクトリ: {config.worktree_base}\slot{N}

このディレクトリは loop/review/integration から分岐した使い捨て worktree
（ブランチ loop/review/{entry}）。以下を順に実施すること:

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
   handlers/ と data/ の実装を仕様書・計画書と照合し、誤り・欠落があれば修正する。
   ※ 五十音ソート（sort_handlers.py / sort_data/*.py）は実行しない（マージ後に一括整形）。
   ※ 技のレビューの場合、PP値は必ず `docs/champions/move_list.txt` の値を正とする
     （`docs/champions/changes_from_sv.md` により全技PPは8/12/16/20の4段階に統一されている）。
     `data/moves/*.py` の実装がGen9本家基準の値になっている場合はそちらが移行漏れのバグであり、
     champions側の値に修正すること。`docs/progress/move.md` のPP列とmove_list.txtが食い違う
     場合も、move_list.txt を優先し進捗表の方を修正する（実装値に進捗表を合わせて
     champions値を消してしまわないこと）。

5. リーサル計算のレビュー・実装
   `{config.progress_file}` の {entry} 行の「リーサル実装」列を確認する。
   - `n/a` または `保留` → 対象外なのでスキップする
   - `x` → handlers/lethal.py の既存ハンドラを仕様書・実装と照合し、誤り・欠落があれば修正する
     （`.claude/loop/_common.md` §共通11「リーサル計算ハンドラの実装パターン」を基準にする）
   - `-` → 仕様書をもとに §共通11 に従って新規にリーサル計算ハンドラを実装する
   ※ ここでも sort_handlers.py / sort_data/*.py は実行しない（マージ後に一括整形）。

6. テストのレビュー・修正
   {config.test_files} のテストを実装と照合し、誤り・過不足があれば修正する。
   手順5でリーサル計算ハンドラを新規実装・修正した場合は tests/test_lethal.py にも
   `t.calc_lethal` を使ったテストを追加・修正する。
   ※ sort_tests.py / generate_test_list.py は実行しない（マージ後に一括実行）。
   python -m pytest tests/ -v でテストを実行し、結果を .loop/test_logs/{entry}.log に保存する。
   全テストが通ることを確認する。今回の修正と無関係な既存テストが flaky（間欠的に失敗）と
   判明した場合は `.claude/loop/_common.md` §共通13 に従いその場で修正する。

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
   手順5でリーサル計算を新規実装・修正した場合は「リーサル実装」「リーサルテスト」列も `x` にする。
   ※ entry ごとに自分の行だけを編集すること（他行を触らない＝コンフリクト回避）。

9. 変更をすべてコミットする:
   git add -A
   git commit -m "review: {entry}"

10. 結果を記録する（パスは作業ディレクトリ外の固定絶対パス）
   成功: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.ok を Write で作成（内容は空でよい）
   失敗: 同 .fail を Write で作成（失敗理由を記述）
```

### 6. 状態保存・終了

§共通7 に従う（続きは background エージェントの完了通知、またはユーザーの `/loop review` 再実行で
再開する）。

---

## main への反映

§共通6 を適用する（`{branch}` = `loop/review/integration`）。

## エラーハンドリング

§共通8 に加えて:
- `in_progress` のエントリが前回から残り結果ファイルが無い場合 → 再度エージェントを起動（再試行扱い）。
- §共通5 の最終 pytest が失敗 → commit せずユーザーに報告（統合ブランチは調査用に残す）。
- エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。

## 状態例

```json
{
  "config": {
    "flow": "review", "category": "変化技",
    "wiki_hint": "docs/wiki/ の一次情報を参照（moves/, volatiles/ 等）",
    "spec_dir": "docs/spec/moves/", "plan_dir": "docs/plan/moves",
    "progress_file": "docs/progress/move.md", "review_dir": "docs/review/moves/",
    "test_files": ["tests/moves_status/"], "parallel_max": 3,
    "worktree_base": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\review"
  },
  "review_queue": ["いえき", "いばる", "うたう"],
  "in_progress": [], "completed": ["あくび"], "failed": [],
  "unformatted_merges": 3, "last_format_commit": "1df4c9e7..."
}
```
