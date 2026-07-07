# TODO 直列処理 自律ループ 指示書

**ディスパッチャー作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`
（Claude セッションの CWD。状態ファイル `.loop/` の読み書きと worktree 起動のみ。
**`jpoke/` の作業ツリーには一切コミット・マージしない**）
**実装作業ディレクトリ**: `{config.worktree}`（永続 worktree、ブランチ `loop/todo`）

> **統合ブランチ方式**: ループの成果は永続ブランチ `loop/todo` に蓄積し、**main へは自動マージしない**。
> ユーザーの `jpoke/`(main) には一切触れないため、ループ稼働中でも待ち・競合が発生しない。
> 完了分を main に取り込むのはユーザーが任意のタイミングで行う（末尾「main への反映」）。
> `.loop/` は git 管理外のローカルスクラッチ（`.gitignore` 済み・コミット不要）。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "category":      "TODO修正",
    "scan_glob":     "**/*.py",  // .claude/ 除外、プロジェクト全体
    "test_files":    ["tests/"],
    "review_extra":  "",
    "worktree":      "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\todo"
  },
  "todo_queue": ["TODO コメントの文言をそのまま"],
  "completed":  ["..."],
  "failed":     ["..."]
}
```

`todo_queue` の各エントリは **TODO コメントの文言**（`# TODO: ` 以降のテキスト）。
ファイルパスや行番号は含めない。実装時に Grep で現在位置を探す。

---

## キューの事前準備（ループ開始前に手動で実施）

ループを開始する前に、Grep で TODO を収集して `todo_queue` に列挙する。

```
Grep pattern="# TODO" glob="**/*.py" path="." output_mode="content"
（.claude/ 配下は除外する）
```

各行の `# TODO: ` 以降のテキストをそのまま `todo_queue` に書き込む。

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/todo_state.json` を Read で読み込む。

### 1.5. キューが空なら TODO を収集する

`todo_queue` が空の場合、ループ開始前にプロジェクト全体から TODO を収集してキューに投入する。

```
Grep pattern="# TODO" glob="**/*.py" path="." output_mode="content"
（.claude/ 配下は除外する）
```

各行の `# TODO: ` 以降のテキストを `todo_queue` に追加し、状態ファイルを保存してから次のステップへ進む。

収集しても `todo_queue` が空のまま（プロジェクトに TODO がない）なら、完了と判断してループ終了。

### 1.6. worktree を準備する（冪等）

（ディスパッチャー作業ディレクトリ jpoke/ で実行）

`{config.worktree}` が存在しなければ作成する:
```bash
git worktree add -b loop/todo "{config.worktree}" main
```
既に存在する場合は main の最新変更を取り込む（`loop/todo` を main に追従させておくと、
後でユーザーが main へ FF 反映しやすい）:
```bash
git -C "{config.worktree}" checkout loop/todo
git -C "{config.worktree}" merge main
```

### 2. 終了チェック

`todo_queue` が空なら
→「{config.category} 全件完了: {completed}」と報告してループ終了（ScheduleWakeup を呼ばない）。

### 3. エントリ取り出し

`todo_queue` の先頭を取り出す（→ `entry`）。
失敗履歴に同じ `entry` が **2 回以上** あればスキップして次のエントリへ。

### 4. 実装（impl エージェント、foreground）

```
jpoke {config.category} 修正タスク: {entry}

作業ディレクトリ: {config.worktree}

対象 TODO: "{entry}"

手順:
1. Grep で "{entry}" をプロジェクト全体（glob="**/*.py"、.claude/ 除外）から検索し、現在のファイル・行を特定する
   （見つからない場合は既に解決済みとみなして completed に追加し終了する）
2. 該当箇所を Read で確認し、TODO の内容を把握する
3. CLAUDE.md の実装時参照順・ハンドラ約束事に従って修正を実装する
4. TODO コメント自体は修正完了後に削除する
5. テストは書かない（review-test エージェントが担当）
```

失敗した場合: `failed` に追加して手順 6 へ（review-test はスキップ）。

### 5. レビュー・テスト（review-test エージェント、foreground）

impl 成功後のみ実行：

```
jpoke {config.category} レビュー・テストタスク: {entry}

作業ディレクトリ: {config.worktree}

{entry} の TODO 修正が完了した。以下を順に実施すること:
1. 修正内容を対象ファイルで確認し、問題があれば修正する
2. {config.test_files} に必要なテストを追加・修正する
3. python scripts/sort_tests.py <変更したテストファイル> でソートする
4. python scripts/generate_test_list.py でテスト一覧を更新する
5. python -m pytest tests/ -v でテストを実行し、結果を docs/test/logs/<entry_slug>.log に保存する
   （entry_slug は entry の先頭20文字をファイル名として使用する）
   全テストが通ることを確認する
6. 変更をすべてコミットする（作業は `loop/todo` ブランチ上で行う）:
   git add -A
   git commit -m "todo: {entry}"
{config.review_extra}
```

成功: `completed` に追加。失敗: `failed` に追加。

> **main へのマージは行わない**。修正コミットは `loop/todo` に積むだけでよい。
> non-fast-forward の心配も無い（main に触れないため）。

### 6. 状態ファイルを保存

Write ツールで `.loop/todo_state.json` を上書きする。**`.loop/` は git 管理外なのでコミット不要**。

### 7. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="{config.category} TODO処理ループ: 次の件へ")
```

---

## main への反映（ユーザーが任意のタイミングで実行）

`loop/todo` に溜まった完了分を main に取り込む。ループとは非同期でよい。

```bash
# jpoke/ で:
git switch main
git merge --ff-only loop/todo    # loop/todo は main を取り込んで追従しているので通常 FF
# main が独自に進んで FF 不可のときのみ:
git merge --no-ff loop/todo -m "Merge loop/todo"
```

---

## エラーハンドリング

- impl / review-test 失敗 → `failed` に追加してループ継続
- 同じ entry が `failed` に 2 回以上 → スキップして次へ

---

## 状態例

```json
{
  "config": {
    "category":     "TODO修正",
    "test_files":   ["tests/test_move.py"],
    "review_extra": "",
    "worktree":     "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\todo"
  },
  "todo_queue": [
    "ひるみ確率の適用を実装する",
    "追加効果フラグを追加する"
  ],
  "completed": [],
  "failed":    []
}
```
