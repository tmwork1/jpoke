# TODO 直列処理 自律ループ 指示書

**ディスパッチャー作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`（状態ファイル読み書き・git 操作はここで行う）
**実装作業ディレクトリ**: `{config.worktree}`（永続 worktree、ブランチ `loop/todo`）

これによりユーザーのメイン作業ディレクトリ（jpoke/）はループ稼働中も自由に使える状態を保つ。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "category":      "TODO修正",
    "scan_glob":     "**/*.py",  // .claude/ 除外、プロジェクト全体
    "test_files":    ["tests/"],
    "review_extra":  "",
    "worktree":      "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-todo"
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

### 1.6. worktree を準備する

（ディスパッチャー作業ディレクトリ jpoke/ で実行）

`{config.worktree}` が存在しなければ作成する:
```bash
git worktree add -b loop/todo "{config.worktree}" main
```
既に存在する場合は main の最新変更を取り込む:
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
6. 変更をすべてコミットする:
   git add -A
   git commit -m "todo: {entry}"
{config.review_extra}
```

成功: `completed` に追加。失敗: `failed` に追加。

### 5.5 main へ反映する

impl・review-test が両方成功した場合のみ実施する。

ディスパッチャー作業ディレクトリ（jpoke/）で `git status --porcelain` を確認する。
- 出力が空（クリーン） → `git merge loop/todo` を実行して main に取り込む
- 出力がある（ユーザーの未コミット変更が残っている） → merge を見送り、次回ウェイクアップで再試行する
  （状態ファイル保存・次エントリへの進行は通常どおり進めてよい。次回ウェイクアップの手順 1.6 で
  `loop/todo` に main を取り込んだ後、改めてこの手順で merge を試みる）

non-fast-forward で衝突が起きた場合は自動解決せず、`failed` に記録してユーザーに報告する。

### 6. 状態ファイルを保存

Write ツールで `.loop/todo_state.json` を上書きし、ディスパッチャー作業ディレクトリ（jpoke/）で
コミットする（`.loop/*.json` は git 管理下にあるため、コミットせず放置すると jpoke/ が常に
dirty 判定になり手順 5.5 の merge が永久にブロックされる）:
```bash
git add .loop/todo_state.json
git commit -m "chore: TODOループ状態更新（{entry} 完了/失敗）"
```

### 7. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="{config.category} TODO処理ループ: 次の件へ")
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
    "review_extra": ""
  },
  "todo_queue": [
    "ひるみ確率の適用を実装する",
    "追加効果フラグを追加する"
  ],
  "completed": [],
  "failed":    []
}
```
