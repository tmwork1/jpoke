# 再レビュー 自律ループ 指示書

**ディスパッチャー作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`
（Claude セッションの CWD。ここでは **git コミット・マージを一切行わない**。状態ファイル `.loop/` の
読み書きと、統合 worktree に対する `git -C` 操作の起点としてのみ使う）
**統合 worktree**: `{config.worktree_base}\integration`（ブランチ `loop/{config.flow}`。
ループの成果を集約する常設 worktree。マージ・整形・状態コミットはすべてここで行う）
**レビュー作業ディレクトリ**: `{config.worktree_base}\slot{N}`（entry ごとの使い捨て worktree、
ブランチ `loop/{config.flow}/{entry}`。統合ブランチ `loop/{config.flow}` から分岐する）

> **命名規約（フロー別・案B）**: worktree による作業分離は review 専用ではなく全ループ共通の仕組み。
> ブランチ名前空間は `loop/{flow}` を基点にフローで分離する（`{flow}` は `config.flow`。例 `review`）。
> - 統合ブランチ: `loop/{flow}`（例 `loop/review`）
> - entry ブランチ: `loop/{flow}/{entry}`（例 `loop/review/みだれひっかき`）
> - worktree ベース: `config.worktree_base`（フロー別に分離。例 `...\jpoke-loop\review`）
>
> これにより impl など別フローと並走してもブランチ・worktree が衝突しない。

---

## 並列実行モデル（統合ブランチ方式）

```
ユーザー jpoke/                          : main。ループは読み書きしない（完全に独立）
統合 worktree {worktree_base}\integration : loop/{flow}。マージ・整形・状態集約 [ディスパッチャー所有]
レビュー worktree {worktree_base}\slot1  : loop/{flow}/{entry} でレビュー・修正 [background]
レビュー worktree {worktree_base}\slot2  : loop/{flow}/{entry} でレビュー・修正 [background]
...（parallel_max 個まで）
```

- `loop/{flow}/{entry}` は **`loop/{flow}` から分岐**し、成功したら **`loop/{flow}` にマージ**する。
- ループは `main` にも `jpoke/` の作業ツリーにも一切触れない。したがって **ユーザーの未コミット変更が
  マージをブロックすることはなく、他セッションと index/ref を奪い合う待ちも発生しない**。
- 完了分を `main` に取り込むのは **ユーザーが任意のタイミングで行う**（後述「main への反映」）。
- 五十音ソート・テスト一覧生成などの **共有ファイルを丸ごと書き換える処理は slot では行わず、
  マージ後にディスパッチャーが `loop/{flow}` 上で一括実行する**（コンフリクト回避）。

---

## 状態ファイルのスキーマ

`.loop/` は **git 管理外のローカルスクラッチ**（`.gitignore` 済み）。コミット不要・コンフリクトなし。
状態ファイル・完了マーカー・テストログはすべて固定の絶対パス
`C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\` を共有ドロップ先として使う。

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
  "failed":       []
}
```

`in_progress` の要素は `{"name": "...", "slot": N, "branch": "loop/{flow}/{name}"}` 形式のオブジェクト。
新規にバッチ投入するエントリは常にこの形式で `in_progress` に追加する。

---

## ウェイクアップ手順

### 0. 統合 worktree を用意する（冪等）

各ウェイクアップの冒頭で `loop/{config.flow}` の worktree が存在するか確認し、なければ作成する。

```bash
INTG="{config.worktree_base}\integration"
BR="loop/{config.flow}"
if ! git worktree list --porcelain | grep -q "branch refs/heads/$BR$"; then
  if git show-ref --verify --quiet "refs/heads/$BR"; then
    git worktree add "$INTG" "$BR"          # ブランチはあるが worktree が無い
  else
    git worktree add "$INTG" -b "$BR" main  # 初回。main から分岐
  fi
fi
```

以降のディスパッチャーの git 操作はすべて `git -C "$INTG" ...` で統合 worktree に対して行う。

### 1. 状態ファイルを読む

`.loop/review_state.json` を Read で読み込む。

### 2. 終了チェック

`review_queue` と `in_progress` が両方空なら
→「{config.category} 全件レビュー完了: {completed}」と報告してループ終了（ScheduleWakeup を呼ばない）。

### 3. 収穫（Harvest）

`.loop/review_results/` 内のファイルを確認し、`in_progress` の各 entry の結果を回収する。

**マージ前に統合 worktree の HEAD を記録しておく**（手順 3.3 の一括整形の差分基点にする）:

```bash
INTG="{config.worktree_base}\integration"
PRE=$(git -C "$INTG" rev-parse HEAD)
```

各 entry（`{name, slot, branch}` オブジェクト）について:

- `{name}.ok` が存在 →
  1. `{branch}` を `loop/{config.flow}` にマージする（fast-forward 不可なら `--no-ff`）:
     ```bash
     git -C "$INTG" merge --no-ff {branch} -m "Merge {branch}"
     ```
     ユーザーの `jpoke/`（main）は無関係なので **dirty チェックは不要**。統合 worktree は
     ループ専用で常にクリーンなはず。
  2. worktree を削除:
     ```bash
     git -C "$INTG" worktree remove "{config.worktree_base}\slot{slot}" --force
     ```
  3. ブランチを削除:
     ```bash
     git -C "$INTG" branch -d {branch}
     ```
  4. `.ok` ファイルを削除
  5. `in_progress` から除き `completed` に `name` を追加（文字列として追加）
- `{name}.fail` が存在 →
  1. worktree を削除（存在する場合）:
     ```bash
     git -C "$INTG" worktree remove "{config.worktree_base}\slot{slot}" --force
     ```
  2. ブランチを削除:
     ```bash
     git -C "$INTG" branch -D {branch}
     ```
  3. `.fail` ファイルを削除
  4. `in_progress` から除き `failed` に `name` を追加
- どちらも存在しない → 実行中のまま維持

non-fast-forward で衝突が起きた場合は自動解決せず、`git -C "$INTG" merge --abort` で中断し、
`failed` に記録してユーザーに報告する（worktree・ブランチは調査用に残す）。

#### 3.3 バッチ後の一括整形・テスト一覧再生成（マージが 1 件でもあった場合）

slot は五十音ソート・`generate_test_list.py`・テスト一覧更新を **行わない**（共有ファイルの
コンフリクト回避）。代わりにディスパッチャーが `loop/{config.flow}` 上でまとめて 1 回実行する。

```bash
cd "$INTG"
# 今回のバッチで変更されたハンドラファイルだけ五十音ソート
for f in $(git diff --name-only $PRE..HEAD -- 'src/jpoke/handlers/*.py'); do
  python scripts/sort_handlers.py "$f"
done
# data を触っていれば対応する sort を実行
CHANGED=$(git diff --name-only $PRE..HEAD -- 'src/jpoke/data/*.py')
echo "$CHANGED" | grep -q 'ability' && python scripts/sort_data/sort_abilities.py
echo "$CHANGED" | grep -q 'item'    && python scripts/sort_data/sort_items.py
echo "$CHANGED" | grep -q 'move'    && python scripts/sort_data/sort_moves.py
# テストを五十音ソートしてテスト一覧を再生成
python scripts/sort_tests.py {config.test_files をスペース区切り} tests/test_lethal.py
python scripts/generate_test_list.py
# 最終サニティ（統合ブランチ全体でテストが通ることを確認）
python -m pytest tests/ -q
git add -A
git commit -m "chore: バッチ整形・テスト一覧再生成"
```

テストが失敗した場合は commit せず、失敗内容をユーザーに報告する（統合ブランチは調査用に残す）。

### 4. バッチ取り出し

`in_progress` が空で `review_queue` にエントリがある場合のみ実行：

`review_queue` の先頭から最大 `parallel_max` 件を取り出し、1 から順にスロット番号（N）を割り当てる。
各エントリについて worktree を作成する（**`loop/{config.flow}` の最新から分岐**）:

```bash
git -C "$INTG" worktree add -b "loop/{config.flow}/{entry}" "{config.worktree_base}\slot{N}" loop/{config.flow}
```

`in_progress` に `{"name": entry, "slot": N, "branch": "loop/{config.flow}/{entry}"}` を追加する。

### 5. 並列レビュー

`in_progress` のうち今回新規に作成した entry を **background** で review エージェントに同時に渡す
（1 つのレスポンスで複数の Agent 呼び出し）。

```
jpoke {config.category} 再レビュータスク: {entry}

作業ディレクトリ: {config.worktree_base}\slot{N}

このディレクトリは loop/{config.flow} から分岐した使い捨て worktree（ブランチ loop/{config.flow}/{entry}）。
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
   ※ 五十音ソート（sort_handlers.py / sort_data/*.py）は **実行しない**。
     整形はマージ後にディスパッチャーが一括で行う（共有ファイルのコンフリクト回避）。

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
   ※ ここでも sort_handlers.py / sort_data/*.py は **実行しない**（マージ後に一括整形）。

6. テストのレビュー・修正
   {config.test_files} のテストを実装と照合する。
   誤り・過不足があれば修正する。
   手順5でリーサル計算ハンドラを新規実装・修正した場合は tests/test_lethal.py にも
   `t.calc_lethal` を使ったテストを追加・修正する。
   ※ sort_tests.py / generate_test_list.py は **実行しない**（マージ後にディスパッチャーが一括実行）。
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
   ※ 進捗ファイルは entry ごとに自分の行だけを編集すること（他行を触らない＝コンフリクト回避）。

9. 変更をすべてコミットする:
   git add -A
   git commit -m "review: {entry}"

10. 結果を記録する
   成功: {プロジェクトルート}\.loop\review_results\{entry}.ok を Write で作成（内容は空でよい、
        パスは作業ディレクトリ外の絶対パス: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.ok）
   失敗: 同様に {entry}.fail を Write で作成（失敗理由を記述）
```

### 6. 状態ファイルを保存

Write ツールで `.loop/review_state.json` を上書きする。**`.loop/` は git 管理外なのでコミットは不要**。

### 7. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=600, prompt="<<autonomous-loop-dynamic>>",
               reason="{config.category} 再レビューループ: 結果回収 → 次バッチへ")
```

---

## main への反映（ユーザーが任意のタイミングで実行）

`loop/{config.flow}`（例 `loop/review`）に溜まった完了分を `main` に取り込む。ループとは非同期でよい。

```bash
# jpoke/ で:
git switch main
git merge --ff-only loop/review    # 通常はこれで一発（loop/review は main の子孫）

# main が独自に進んで FF できない場合のみ:
git merge --no-ff loop/review -m "Merge loop/review"
```

FF 同期なら競合は起きない。ユーザーが main に独自コミットを重ねた場合だけ通常のマージになる。

---

## エラーハンドリング

- 同じ entry が `failed` に 2 回以上 → スキップして次へ
- `in_progress` のエントリが前回のウェイクアップから残っている場合、結果ファイルがなければ再度エージェントを起動する（再試行扱い）
- non-fast-forward で衝突 → `git -C "$INTG" merge --abort` で中断し `failed` に記録して報告（worktree・ブランチは調査用に残す）
- 手順 3.3 の最終 pytest が失敗 → commit せずユーザーに報告（統合ブランチは調査用に残す）
- 統合 worktree が壊れた/消えた → 手順 0 が冪等に再作成する

---

## 状態例

```json
{
  "config": {
    "flow":        "review",
    "category":    "変化技",
    "wiki_hint":   "docs/wiki/ の一次情報を参照（moves/, volatiles/ 等）",
    "spec_dir":    "docs/spec/moves/",
    "plan_dir":    "docs/plan/moves",
    "progress_file": "docs/progress/move.md",
    "review_dir":    "docs/review/moves/",
    "test_files":  ["tests/moves_status/"],
    "parallel_max": 3,
    "worktree_base": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\review"
  },
  "review_queue": ["いえき", "いばる", "うたう"],
  "in_progress":  [],
  "completed":    ["あくび"],
  "failed":       []
}
```
