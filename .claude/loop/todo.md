# TODO 直列処理 自律ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `todo`、方式は単一ブランチ）。
**実装作業ディレクトリ**: `{config.worktree}`（永続 worktree、ブランチ `loop/todo`）。

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
ファイルパスや行番号は含めない（実装時に Grep で現在位置を探す）。

---

## 実行手順

### 1. 状態ファイルを読む

`.loop/todo_state.json` を Read で読み込む（存在しなければ初回起動）。

### 1.5. キューが空なら TODO を収集する

`todo_queue` が空の場合、プロジェクト全体から TODO を収集してキューに投入する。

```
Grep pattern="# TODO" glob="**/*.py" path="." output_mode="content"
（.claude/ 配下は除外する）
```

各行の `# TODO: ` 以降のテキストを `todo_queue` に追加し、状態ファイルを保存してから次へ。
収集しても空のまま（TODO が無い）なら完了と判断してループ終了。

### 1.6. worktree を準備する

§共通4 パターンA を適用する（`{config.worktree}`・ブランチ `loop/todo`）。

### 2. 終了チェック

`todo_queue` が空なら「{config.category} 全件完了: {completed}」と報告してループ終了。

### 3. エントリ取り出し

`todo_queue` の先頭を取り出す（→ `entry`）。
`failed` に同じ `entry` が **2 回以上**あればスキップして次のエントリへ（§共通8）。

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
   全テストが通ることを確認する。今回の修正と無関係な既存テストが flaky と判明した場合は
   `.claude/loop/_common.md` §共通13 に従いその場で修正する
6. 変更をすべてコミットする（作業は `loop/todo` ブランチ上で行う）:
   git add -A
   git commit -m "todo: {entry}"
{config.review_extra}
```

成功: `completed` に追加。失敗: `failed` に追加。

> main へのマージは行わない（§共通2）。コミットは `loop/todo` に積むだけでよい。

### 6. 状態保存・終了

§共通7 に従う（続きはユーザーの `/loop todo` 再実行で再開する）。

---

## main への反映

§共通6 を適用する（`{branch}` = `loop/todo`）。

## エラーハンドリング

§共通8 に従う（impl / review-test 失敗 → `failed` に追加してループ継続）。
エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。

## 状態例

```json
{
  "config": {
    "category":     "TODO修正",
    "test_files":   ["tests/test_move.py"],
    "review_extra": "",
    "worktree":     "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\todo"
  },
  "todo_queue": ["ひるみ確率の適用を実装する", "追加効果フラグを追加する"],
  "completed": [],
  "failed":    []
}
```
