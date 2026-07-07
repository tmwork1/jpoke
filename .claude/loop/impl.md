# 大量実装 自律ループ 指示書

**ディスパッチャー作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`
（Claude セッションの CWD。ここでは **git コミット・マージを一切行わない**。状態ファイル `.loop/` の
読み書きと、各 worktree に対する `git -C` 操作の起点としてのみ使う）

> **統合ブランチ方式（案B命名）**: ループの成果は統合ブランチ `loop/impl/integration` に集約し、
> **main へは自動マージしない**。ユーザーの `jpoke/`(main) には一切触れないため、稼働中でも待ち・
> 競合が発生しない。完了分を main に取り込むのはユーザーが任意のタイミングで行う（末尾「main への反映」）。
> - 統合ブランチ: `loop/impl/integration`
> - entry ブランチ: `loop/impl/{entry}`（統合ブランチと ref D/F 衝突しないよう `loop/impl/` 配下の兄弟）
> - `.loop/` は git 管理外のローカルスクラッチ（`.gitignore` 済み・コミット不要）
> - 五十音ソート・テスト一覧生成は各エージェントで行わず、**マージ後にディスパッチャーが統合ブランチ上で
>   一括実行**する（共有ファイルのコンフリクト回避）

---

## 並列実行モデル

```
ディスパッチャー jpoke/                      : 状態管理と git -C 操作のみ（main・jpoke/ は触らない）
統合 worktree {worktree_base}\integration    : loop/impl/integration。マージ・整形・集約 [所有]
実装 worktree  {worktree_base}\work           : planner（計画書作成）と impl（実装）を実行。
                                              : loop/impl/integration に detach した状態を基点に
                                              : 各 entry で loop/impl/{entry} を切って実装 [foreground/background]
レビュー worktree {worktree_base}\review      : loop/impl/{entry} を checkout して review-test [background]
```

`review-test` は impl 完了済みの `loop/impl/{entry}` を別 worktree で checkout して回帰テストを追加し、
同じ entry ブランチ上にコミットする。ディスパッチャーがその entry ブランチを
`loop/impl/integration` にマージする（impl と review の両変更がまとめて入る）。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "flow":               "impl",
    "category":           "変化技",
    "plan_dir":           "docs/plan/moves",
    "spec_hint":          "docs/spec/ を参照",
    "progress_file":      "docs/progress/move.md",
    "test_files":         ["tests/test_move.py"],
    "impl_extra":         "",
    "review_extra":       "",
    "planning_slots_max": 1,
    "review_parallel_max": 1,
    "worktree_base":      "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\impl"
  },
  "plan_queue":          ["..."],
  "impl_queue":          ["..."],
  "review_queue":        [],
  "review_in_progress":  [],
  "completed":           ["..."],
  "failed":              ["..."]
}
```

- 統合 worktree = `{config.worktree_base}\integration`（ブランチ `loop/impl/integration`）
- 実装 worktree = `{config.worktree_base}\work`
- レビュー worktree = `{config.worktree_base}\review`（使い捨て）
- `review_queue`: impl 完了・review-test 待ちの件
- `review_in_progress`: review-test が background で実行中の件

---

## ウェイクアップ手順

### 0. worktree を用意する（冪等）

```bash
BASE="{config.worktree_base}"
INTG="$BASE\integration"
WORK="$BASE\work"
BR="loop/impl/integration"
# 統合 worktree
if ! git worktree list --porcelain | grep -q "branch refs/heads/$BR$"; then
  if git show-ref --verify --quiet "refs/heads/$BR"; then
    git worktree add "$INTG" "$BR"
  else
    git worktree add "$INTG" -b "$BR" main
  fi
fi
# 実装 worktree（統合ブランチ先端に detach した使い回しの作業場）
git worktree list --porcelain | grep -q "$WORK" || git worktree add --detach "$WORK" "$BR"
```

以降のディスパッチャーの git 操作はすべて `git -C "<対象 worktree>" ...` で行う。

### 1. 状態ファイルを読む

`.loop/impl_state.json` を Read で読み込む。

### 2. 終了チェック

`plan_queue` / `impl_queue` / `review_queue` / `review_in_progress` がすべて空なら
→「{config.category} 全件完了: {completed}」と報告してループ終了（ScheduleWakeup を呼ばない）。

### 3. レビュー結果の回収（Review Harvest）

`review_in_progress` の各 entry を確認する。結果ファイルの存在チェック:

```
{プロジェクトルート}/.loop/review_results/{entry}.ok
{プロジェクトルート}/.loop/review_results/{entry}.fail
```

マージ前に統合 worktree の HEAD を記録する（手順 3.5 の一括整形の差分基点）:
```bash
INTG="{config.worktree_base}\integration"
PRE=$(git -C "$INTG" rev-parse HEAD)
```

- `.ok` が存在 →
  1. `loop/impl/{entry}` を統合ブランチにマージ（fast-forward 不可なら `--no-ff`）:
     ```bash
     git -C "$INTG" merge --no-ff "loop/impl/{entry}" -m "Merge loop/impl/{entry}"
     ```
     ユーザーの jpoke/（main）は無関係なので **dirty チェックは不要**。
  2. レビュー worktree を削除:
     ```bash
     git -C "$INTG" worktree remove "{config.worktree_base}\review" --force
     ```
  3. ブランチを削除:
     ```bash
     git -C "$INTG" branch -d "loop/impl/{entry}"
     ```
  4. `.ok` ファイルを削除
  5. `review_in_progress` から除き `completed` に追加

- `.fail` が存在 →
  1. レビュー worktree を削除（存在する場合）:
     ```bash
     git -C "$INTG" worktree remove "{config.worktree_base}\review" --force
     ```
  2. ブランチを削除:
     ```bash
     git -C "$INTG" branch -D "loop/impl/{entry}"
     ```
  3. `.fail` ファイルを削除
  4. `review_in_progress` から除き `failed` に追加

- どちらも存在しない → 実行中のまま維持（次のウェイクアップで再確認）

non-fast-forward で衝突が起きた場合は自動解決せず、`git -C "$INTG" merge --abort` で中断し、
`failed` に記録してユーザーに報告する（worktree・ブランチは調査用に残す）。

### 3.5 バッチ後の一括整形・テスト一覧再生成（マージが 1 件でもあった場合）

各エージェントは五十音ソート・`generate_test_list.py` を **行わない**。ディスパッチャーが
統合ブランチ上でまとめて 1 回実行する:

```bash
cd "$INTG"
for f in $(git diff --name-only $PRE..HEAD -- 'src/jpoke/handlers/*.py'); do
  python scripts/sort_handlers.py "$f"
done
CHANGED=$(git diff --name-only $PRE..HEAD -- 'src/jpoke/data/*.py')
echo "$CHANGED" | grep -q 'ability' && python scripts/sort_data/sort_abilities.py
echo "$CHANGED" | grep -q 'item'    && python scripts/sort_data/sort_items.py
echo "$CHANGED" | grep -q 'move'    && python scripts/sort_data/sort_moves.py
python scripts/sort_tests.py {config.test_files をスペース区切り}
python scripts/generate_test_list.py
python -m pytest tests/ -q
git add -A
git commit -m "chore: バッチ整形・テスト一覧再生成"
```

テストが失敗した場合は commit せず、失敗内容をユーザーに報告する。

### 4. バックグラウンド review-test の起動

`review_queue` にエントリがあり、かつ `len(review_in_progress) < config.review_parallel_max` の場合:

`review_queue` から先頭の entry を取り出し、以下を実施:

1. レビュー worktree を作成（既存の entry ブランチを checkout）:
   ```bash
   git -C "{config.worktree_base}\integration" worktree add "{config.worktree_base}\review" "loop/impl/{entry}"
   ```

2. `review_in_progress` に追加

3. **review-test エージェント（background）** を起動:

```
jpoke {config.category} レビュー・テストタスク: {entry}

作業ディレクトリ: {config.worktree_base}\review

{entry} の実装が完了している（このディレクトリは loop/impl/{entry} ブランチ）。
以下を順に実施すること:

1. handlers/ と data/ の実装をレビュー、問題があれば修正
   ※ 五十音ソート（sort_handlers.py / sort_data/*.py）は実行しない（マージ後に一括整形）
2. {config.test_files} にテストを追加
3. python -m pytest tests/ -v を実行し全テストが通ることを確認する
   ※ sort_tests.py / generate_test_list.py は実行しない（マージ後にディスパッチャーが一括実行）
4. {config.progress_file} の {entry} 行のテスト済み列を更新する（自分の行だけ）
5. 変更をすべてコミットする（loop/impl/{entry} ブランチ上で）:
   git add -A
   git commit -m "review: {entry}"

完了後、結果ファイルを書き込む（パスは作業ディレクトリ外の絶対パス）:
  成功: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.ok を Write で作成（内容は空でよい）
  失敗: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.fail を Write で作成（失敗理由を記述）
{config.review_extra}
```

### 5. 収穫（Harvest）

`{config.worktree_base}\work` 配下の `{config.plan_dir}/{entry}.md` を基準に、`plan_queue` を先頭から
走査し、存在するエントリを `impl_queue` 末尾に移して `plan_queue` から除く。

### 6. 実装

`impl_queue` が空でなければ先頭エントリを取り出す（→ `entry`）。

**impl エージェント（foreground）**

```
jpoke {config.category} 実装タスク: {entry}

作業ディレクトリ: {config.worktree_base}\work

計画書: {config.plan_dir}/{entry}.md

手順:
0. 統合ブランチ先端から entry ブランチを作成して切り替える:
   git checkout -B "loop/impl/{entry}" loop/impl/integration
1. 計画書を読み込む（CLAUDE.md の実装時参照順に従い関連ファイルも確認）
2. CLAUDE.md のハンドラ約束事に従い、handlers/ と data/ に実装する
   ※ 五十音ソート（sort_handlers.py / sort_data/*.py）は実行しない（マージ後に一括整形）
{config.impl_extra}
3. テストは書かない（review-test エージェントが担当）
4. {config.progress_file} の {entry} 行の実装列を `x` に更新する（自分の行だけ）
5. 変更をすべてコミットする:
   git add -A
   git commit -m "impl: {entry}"
6. entry ブランチを解放する（review-test が別 worktree で checkout できるよう detach する）:
   git checkout --detach loop/impl/integration
```

成功した場合: `review_queue` に追加。
失敗した場合: `failed` に追加（ブランチが残っていれば削除する:
`git -C "{config.worktree_base}\work" branch -D "loop/impl/{entry}"`）。

### 7. 種まき（Sow）

`plan_queue` の先頭から最大 `planning_slots_max` 件を **background** で planner エージェントに渡す
（収穫後に plan_queue に残っているものはすべてファイル未生成）。

```
jpoke {config.category} 計画書作成タスク: {entry}

作業ディレクトリ: {config.worktree_base}\work

{config.spec_hint}
ハンドラ構成・subject_spec・priority（docs/spec/turn.md 参照）・実装コードを含む計画書を
{config.plan_dir}/{entry}.md に作成すること。
CLAUDE.md のハンドラ約束事を厳守。
（計画書ファイルは作業ツリーに置くだけでよい。手順5の収穫で impl_queue に移り、impl コミットに含まれる）
```

### 8. 状態ファイルを保存

Write ツールで `.loop/impl_state.json` を上書きする。**`.loop/` は git 管理外なのでコミット不要**。

### 9. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="{config.category} 実装ループ: 次の件へ")
```

---

## main への反映（ユーザーが任意のタイミングで実行）

```bash
# jpoke/ で:
git switch main
git merge --ff-only loop/impl/integration
# FF 不可のときのみ:
git merge --no-ff loop/impl/integration -m "Merge loop/impl/integration"
```

---

## エラーハンドリング

- impl 失敗 → `failed` に追加してループ継続（work worktree 内でブランチを削除してから次へ）
- review-test 失敗 → `failed` に追加してループ継続（review worktree・ブランチを削除してから次へ）
- non-fast-forward で衝突 → `git -C "$INTG" merge --abort` で中断し `failed` に記録して報告
- 同じ件が `failed` に 2 回以上 → スキップして次へ
- `review_in_progress` のエントリに結果ファイルが来ない場合 → 次のウェイクアップで再確認（再試行しない）
- worktree が壊れた/消えた → 手順 0 が冪等に再作成する

---

## 状態例

```json
{
  "config": {
    "flow":               "impl",
    "category":           "変化技",
    "plan_dir":           "docs/plan/moves",
    "spec_hint":          "docs/spec/ の対応仕様書を参照（volatiles/, moves/, side_fields/, global_fields/ 以下も確認）",
    "progress_file":      "docs/progress/move.md",
    "test_files":         ["tests/test_move.py"],
    "impl_extra":         "- data/move.py の MoveData に技が未登録なら追加する",
    "review_extra":       "",
    "planning_slots_max": 2,
    "review_parallel_max": 1,
    "worktree_base":      "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\impl"
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
- `あくび`: review-test が review worktree で background 実行中
- `あくまのキッス`: impl 完了済み・review-test 待ち（次のウェイクアップで review worktree 作成 → background 起動）
- `いばる`: 今回のウェイクアップで impl foreground 実行
- `からをやぶる`, `ガードシェア`: planner background で計画書作成中
