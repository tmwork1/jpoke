# 大量実装 自律ループ 指示書

**ディスパッチャー作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`（状態ファイル読み書き・git merge・worktree 起動はここで行う）

---

## 並列実行モデル

```
ディスパッチャー jpoke/         : 状態管理・git merge・worktree の起動/削除のみ（main 固定・編集しない）
impl worktree    jpoke-impl/    : impl/{N} ブランチで計画書作成・impl 実装 [planner: background / impl: foreground]
レビュー worktree jpoke-review/ : review/{N} ブランチで review-test  [background]
```

impl が終わり次第すぐ次の件を開始する。review-test は別ディレクトリで並行して動く。
`review/{N}` は `impl/{N}` から派生するため、merge 時は `review/{N}` だけを main にマージすれば
impl と review の両変更が取り込まれる（`impl/{N}` ブランチは不要になる）。
ユーザーのメイン作業ディレクトリ（jpoke/）は常に main のままで、ループが直接編集することはない
（状態ファイル読み書きと git merge/worktree コマンドのみ）。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "category":           "変化技",
    "plan_dir":           "docs/plan/moves",
    "spec_hint":          "docs/spec/ を参照",
    "progress_file":      "docs/progress/move.md",
    "test_files":         ["tests/test_move.py"],
    "impl_extra":         "",
    "review_extra":       "",
    "planning_slots_max": 1,
    "review_parallel_max": 1,
    "impl_worktree":      "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-impl",
    "review_worktree":    "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-review"
  },
  "plan_queue":          ["..."],
  "impl_queue":          ["..."],
  "review_queue":        [],
  "review_in_progress":  [],
  "completed":           ["..."],
  "failed":              ["..."]
}
```

- `review_queue`: impl 完了・review-test 待ちの件
- `review_in_progress`: review-test が background で実行中の件

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/impl_state.json` を Read で読み込む。

### 2. 終了チェック

`plan_queue` / `impl_queue` / `review_queue` / `review_in_progress` がすべて空なら
→「{config.category} 全件完了: {completed}」と報告してループ終了（ScheduleWakeup を呼ばない）。

### 3. レビュー結果の回収（Review Harvest）

`review_in_progress` の各 entry を確認する。

結果ファイルの存在チェック:

```
{プロジェクトルート}/.loop/review_results/{entry}.ok
{プロジェクトルート}/.loop/review_results/{entry}.fail
```

- `.ok` が存在 →
  1. ディスパッチャー作業ディレクトリ（jpoke/）で `git status --porcelain` を確認する。
     出力がある（ユーザーの未コミット変更が残っている）場合は merge を見送り、`.ok` ファイルは
     削除せずに残したまま次のウェイクアップで再試行する（worktree・ブランチもまだ削除しない）。
  2. クリーンなら `review/{entry}` を main にマージ（fast-forward 不可なら `--no-ff`）:
     ```bash
     git merge --no-ff review/{entry} -m "Merge review/{entry}"
     ```
  3. worktree を削除（存在する場合）:
     ```bash
     git worktree remove "{config.review_worktree}" --force
     ```
  4. ブランチを削除:
     ```bash
     git branch -d review/{entry}
     git branch -d impl/{entry}
     ```
  5. `.ok` ファイルを削除
  6. `review_in_progress` から除き `completed` に追加

- `.fail` が存在 →
  1. worktree を削除（存在する場合）:
     ```bash
     git worktree remove "{config.review_worktree}" --force
     ```
  2. ブランチを削除:
     ```bash
     git branch -d review/{entry} 2>$null
     git branch -d impl/{entry} 2>$null
     ```
  3. `.fail` ファイルを削除
  4. `review_in_progress` から除き `failed` に追加

- どちらも存在しない → 実行中のまま維持（次のウェイクアップで再確認）

### 4. バックグラウンド review-test の起動

`review_queue` にエントリがあり、かつ `len(review_in_progress) < config.review_parallel_max` の場合:

`review_queue` から先頭の entry を取り出し、以下を実施:

1. worktree を作成:
   ```bash
   git worktree add -b "review/{entry}" "{config.review_worktree}" "impl/{entry}"
   ```

2. `review_in_progress` に追加

3. **review-test エージェント（background）** を起動:

```
jpoke {config.category} レビュー・テストタスク: {entry}

作業ディレクトリ: {config.review_worktree}

{entry} の実装が完了している（このディレクトリは impl/{entry} ブランチから派生した review/{entry} ブランチ）。
以下を順に実施すること:

1. handlers/ と data/ の実装をレビュー、問題があれば修正
   - handlers を修正した場合は python scripts/sort_handlers.py src/jpoke/handlers/<category>.py を実行する
   - data/ability.py・data/item.py・data/move.py を修正した場合、対応するスクリプト
     （scripts/sort_data/sort_abilities.py / scripts/sort_data/sort_items.py / scripts/sort_data/sort_moves.py）を実行する
2. {config.test_files} にテストを追加
3. python scripts/sort_tests.py {config.test_files をスペース区切り} でソート
4. python scripts/generate_test_list.py でテスト一覧更新
5. python -m pytest tests/ -v を実行し全テストが通ることを確認する
6. {config.progress_file} の {entry} 行のテスト済み列を更新する
7. 変更をすべてコミットする:
   git add -A
   git commit -m "review: {entry}"

完了後、結果ファイルを書き込む（パスは作業ディレクトリ外の絶対パス）:
  成功: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.ok を Write で作成（内容は空でよい）
  失敗: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.fail を Write で作成（失敗理由を記述）
{config.review_extra}
```

### 5. 収穫（Harvest）

`{config.impl_worktree}` 配下の `{config.plan_dir}/{entry}.md` を基準に、`plan_queue` を先頭から
走査し、存在するエントリを `impl_queue` 末尾に移して `plan_queue` から除く。

### 5.5. impl worktree を準備する

（ディスパッチャー作業ディレクトリ jpoke/ で実行）

`{config.impl_worktree}` が存在しなければ作成する（main を checkout した状態で作成）:
```bash
git worktree add "{config.impl_worktree}" main
```
既に存在する場合は特に準備不要（手順6のエージェントが main を checkout してから分岐する）。

### 6. 実装

`impl_queue` が空でなければ先頭エントリを取り出す（→ `entry`）。

**impl エージェント（foreground）**

```
jpoke {config.category} 実装タスク: {entry}

作業ディレクトリ: {config.impl_worktree}

計画書: {config.plan_dir}/{entry}.md

手順:
0. main を最新化してから ブランチ impl/{entry} を作成して切り替える:
   git checkout main
   git checkout -b "impl/{entry}" main
1. 計画書を読み込む（CLAUDE.md の実装時参照順に従い関連ファイルも確認）
2. CLAUDE.md のハンドラ約束事に従い、handlers/ と data/ に実装する
3. python scripts/sort_handlers.py src/jpoke/handlers/<category>.py でハンドラを五十音順に並び替える
   （<category> は変更した handlers/ のファイル名に合わせる）
4. data/ability.py・data/item.py・data/move.py にエントリを追加・変更した場合、対応するスクリプトを実行する:
   python scripts/sort_data/sort_abilities.py（data/ability.py を変更した場合）
   python scripts/sort_data/sort_items.py（data/item.py を変更した場合）
   python scripts/sort_data/sort_moves.py（data/move.py を変更した場合）
{config.impl_extra}
5. テストは書かない（review-test エージェントが担当）
6. {config.progress_file} の {entry} 行の実装列を `x` に更新する
7. 変更をすべてコミットする:
   git add -A
   git commit -m "impl: {entry}"
8. main に戻る（次の entry のためにワーキングツリーを空けておく）:
   git checkout main
```

成功した場合: `review_queue` に追加。
失敗した場合: `failed` に追加（ブランチが残っている場合は削除する: `git -C "{config.impl_worktree}" branch -D impl/{entry}`）。

### 7. 種まき（Sow）

`plan_queue` の先頭から最大 `planning_slots_max` 件を **background** で planner エージェントに渡す
（収穫後に plan_queue に残っているものはすべてファイル未生成）。

```
jpoke {config.category} 計画書作成タスク: {entry}

作業ディレクトリ: {config.impl_worktree}

{config.spec_hint}
ハンドラ構成・subject_spec・priority（docs/spec/turn.md 参照）・実装コードを含む計画書を
{config.plan_dir}/{entry}.md に作成すること。
CLAUDE.md のハンドラ約束事を厳守。
```

### 8. 状態ファイルを保存

Write ツールで `.loop/impl_state.json` を上書きし、ディスパッチャー作業ディレクトリ（jpoke/）で
コミットする（`.loop/*.json` は git 管理下にあるため、コミットせず放置すると jpoke/ が常に
dirty 判定になり手順 3 の review merge が永久にブロックされる）:
```bash
git add .loop/impl_state.json
git commit -m "chore: 実装ループ状態更新"
```

### 9. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="{config.category} 実装ループ: 次の件へ")
```

---

## エラーハンドリング

- impl 失敗 → `failed` に追加してループ継続（`{config.impl_worktree}` 内でブランチを削除してから次へ）
- review-test 失敗 → `failed` に追加してループ継続（worktree・ブランチを削除してから次へ）
- review マージ時に jpoke/ がクリーンでない → merge を見送り次回再試行（`.ok` ファイル・worktree・
  ブランチはそのまま残す）
- 同じ件が `failed` に 2 回以上 → スキップして次へ
- `review_in_progress` のエントリに結果ファイルが来ない場合 → 次のウェイクアップで再確認（再試行しない）

---

## 状態例

```json
{
  "config": {
    "category":           "変化技",
    "plan_dir":           "docs/plan/moves",
    "spec_hint":          "docs/spec/ の対応仕様書を参照（volatiles/, moves/, side_fields/, global_fields/ 以下も確認）",
    "progress_file":      "docs/progress/move.md",
    "test_files":         ["tests/test_move.py"],
    "impl_extra":         "- data/move.py の MoveData に技が未登録なら追加する",
    "review_extra":       "",
    "planning_slots_max": 2,
    "review_parallel_max": 1,
    "impl_worktree":      "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-impl",
    "review_worktree":    "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-review"
  },
  "plan_queue":         ["からをやぶる", "ガードシェア"],
  "impl_queue":         ["いばる"],
  "review_queue":       ["あくまのキッス"],
  "review_in_progress": ["あくび"],
  "completed":          [],
  "failed":             []
}
```

この例では:
- `あくび`: review-test が jpoke-review/ で background 実行中
- `あくまのキッス`: impl 完了済み・review-test 待ち（次のウェイクアップで worktree 作成 → background 起動）
- `いばる`: 今回のウェイクアップで impl foreground 実行
- `からをやぶる`, `ガードシェア`: planner background で計画書作成中
