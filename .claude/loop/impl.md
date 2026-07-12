# 大量実装 自律ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `impl`、方式は統合ブランチ）。

3 つの worktree を使う:
- **統合 worktree** `{config.worktree_base}\integration`（ブランチ `loop/impl/integration`。マージ・整形・集約）
- **実装 worktree** `{config.worktree_base}\work`（planner と impl を実行。`loop/impl/integration` に
  detach した状態を基点に、各 entry で `loop/impl/{entry}` を切って実装）
- **レビュー worktree** `{config.worktree_base}\review`（使い捨て。`loop/impl/{entry}` を checkout して review-test）

`review-test` は impl 完了済みの `loop/impl/{entry}` を別 worktree で checkout し回帰テストを追加、
同じ entry ブランチにコミットする。ディスパッチャーがその entry ブランチを
`loop/impl/integration` にマージする（impl と review の両変更がまとめて入る）。

**ローリング・ディスパッチ**: `review_in_progress` / `plan_queue` の全件完了を待たず、1 件完了する
たびにその場で収穫し、空いた分だけ即座に補充する（§3・§4・§7）。常に `review_parallel_max` /
`planning_slots_max` 件が稼働している状態を維持する。

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
  "failed":              ["..."],
  "unformatted_merges":  0,
  "last_format_commit":  "..."
}
```

- `review_queue`: impl 完了・review-test 待ちの件 / `review_in_progress`: review-test が background 実行中の件。
- `unformatted_merges` / `last_format_commit`: §共通5（10 件ごとの一括整形）で使う。統合 worktree を
  初回作成した直後は `last_format_commit` をそのときの HEAD で初期化する。

---

## 実行手順

### 0. worktree を用意する

まず §共通4 パターンB で統合 worktree を用意する（`INTG="{config.worktree_base}\integration"`、
`BR="loop/impl/integration"`）。続けて実装 worktree（統合ブランチ先端に detach した使い回しの作業場）:

```bash
WORK="{config.worktree_base}\work"
if ! git worktree list --porcelain | grep -q "$WORK"; then
  git worktree add --detach "$WORK" "$BR"
  # 新規作成時のみ §共通4.5（<worktree> = $WORK）
fi
```

以降のディスパッチャーの git 操作はすべて `git -C "<対象 worktree>" ...`。

### 1. 状態ファイルを読む

`.loop/impl_state.json` を Read で読み込む（存在しなければ初回起動）。

### 2. 終了チェック

`plan_queue` / `impl_queue` / `review_queue` / `review_in_progress` がすべて空なら、
`unformatted_merges > 0` の場合は §3.5 の整形を先に実行してから、
「{config.category} 全件完了: {completed}」と報告してループ終了。

### 3. レビュー結果の回収（Review Harvest）

`review_in_progress` の各 entry の結果ファイル（`{プロジェクトルート}/.loop/review_results/{entry}.ok`
または `.fail`）を確認する。

- `.ok` が存在 →
  1. マージ: `git -C "$INTG" merge --no-ff "loop/impl/{entry}" -m "Merge loop/impl/{entry}"`
     （統合 worktree はループ専用で常にクリーン。dirty チェック不要）
  2. `git -C "$INTG" worktree remove "{config.worktree_base}\review" --force`
  3. `git -C "$INTG" branch -d "loop/impl/{entry}"`
  4. `.ok` ファイルを削除（§共通9 のガード付き rm を使う）
  5. `review_in_progress` から除き `completed` に追加
  6. `unformatted_merges += 1`
- `.fail` が存在 →
  1. レビュー worktree を削除（存在すれば、上と同じ）
  2. `git -C "$INTG" branch -D "loop/impl/{entry}"`
  3. `.fail` ファイルを削除（§共通9 のガード付き rm を使う）
  4. `review_in_progress` から除き `failed` に追加
- どちらも存在しない → 実行中のまま維持

non-fast-forward 衝突時は §共通8 に従う。

#### 3.5 一括整形（未整形マージが 10 件たまったら）

`unformatted_merges >= 10` の場合のみ実行する。§共通5 を適用する。
`{フロー固有のテストファイル群}` = `{config.test_files をスペース区切り} tests/test_lethal.py`
（リーサルハンドラを実装した entry があるため test_lethal.py も併せてソートする）。

### 4. review-test の起動（background）

`review_queue` にエントリがあり、かつ `len(review_in_progress) < config.review_parallel_max` の場合、
`review_queue` 先頭の entry を取り出し:

1. レビュー worktree を作成（既存の entry ブランチを checkout）:
   ```bash
   git -C "$INTG" worktree add "{config.worktree_base}\review" "loop/impl/{entry}"
   ```
   作成後、§共通4.5 を適用する（`<worktree>` = `{config.worktree_base}\review`）。
2. `review_in_progress` に追加
3. **review-test エージェント（background）** を起動:

```
jpoke {config.category} レビュー・テストタスク: {entry}

作業ディレクトリ: {config.worktree_base}\review

{entry} の実装が完了している（このディレクトリは loop/impl/{entry} ブランチ）。
以下を順に実施すること:

1. handlers/ と data/ の実装をレビュー、問題があれば修正（リーサルハンドラを実装していれば併せてレビュー）
   ※ 五十音ソート（sort_handlers.py / sort_data/*.py）は実行しない（マージ後に一括整形）
2. {config.test_files} にテストを追加
   impl が {entry} のリーサルハンドラを実装した場合（progress の「リーサル実装」列が `x`）は
   tests/test_lethal.py に `t.calc_lethal` を使ったテストも追加する
3. python -m pytest tests/ -v を実行し全テストが通ることを確認する
   （今回の実装と無関係な既存テストが flaky と判明した場合は `.claude/loop/_common.md` §共通13 に
   従いその場で修正する）
   ※ sort_tests.py / generate_test_list.py は実行しない（マージ後にディスパッチャーが一括実行）
4. {config.progress_file} の {entry} 行のテスト済み列を更新する（自分の行だけ）
   手順2でリーサルテストを追加した場合は「リーサルテスト」列も `x` にする
5. 変更をすべてコミットする（loop/impl/{entry} ブランチ上で）:
   git add -A
   git commit -m "review: {entry}"

完了後、結果ファイルを書き込む（パスは作業ディレクトリ外の固定絶対パス）:
  成功: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.ok を Write で作成（内容は空でよい）
  失敗: C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\review_results\{entry}.fail を Write で作成（失敗理由を記述）
{config.review_extra}
```

### 5. 収穫（Harvest）

`{config.worktree_base}\work` 配下の `{config.plan_dir}/{entry}.md` を基準に `plan_queue` を先頭から
走査し、存在するエントリを `impl_queue` 末尾に移して `plan_queue` から除く。

### 6. 実装（impl エージェント、foreground）

`impl_queue` が空でなければ先頭エントリを取り出す（→ `entry`）。

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
3. リーサル計算ハンドラの要否を判断し、必要なら実装する
   {entry} の効果が **リーサル計算の HP 分布に影響するか** を判断する
   （回復・残留ダメージ・ピンチ回復・ダメージ補正・確定急所・きあいのタスキ/がんじょう等の耐え・
     みがわり貫通など）。
   - 影響しない（大半の攻撃技・変化技） → progress の「リーサル実装」「リーサルテスト」列を `n/a` にする
   - ダブル専用効果 → 両列を `ダブル専用` にする / 実装が複雑で今回見送る → 両列を `保留` にする
   - 影響する → `.claude/loop/_common.md` §共通11「リーサル計算ハンドラの実装パターン」に従って
     {config.category} の種別に応じたハンドラ関数を実装する
     - progress の「リーサル実装」列を `x` にする（「リーサルテスト」列は review-test が更新する）
   ※ ここでも sort_handlers.py / sort_data/*.py は実行しない（マージ後に一括整形）
4. テストは書かない（review-test エージェントが担当）
5. {config.progress_file} の {entry} 行の実装列を `x` に更新する（手順3のリーサル列も含め、自分の行だけ）
6. 変更をすべてコミットする:
   git add -A
   git commit -m "impl: {entry}"
7. entry ブランチを解放する（review-test が別 worktree で checkout できるよう detach する）:
   git checkout --detach loop/impl/integration
```

成功: `review_queue` に追加。
失敗: `failed` に追加（ブランチが残っていれば `git -C "{config.worktree_base}\work" branch -D "loop/impl/{entry}"`）。

### 7. 種まき（Sow）

`plan_queue` の先頭から最大 `planning_slots_max` 件を **background** で planner エージェントに渡す
（収穫後に plan_queue に残っているものはすべてファイル未生成）:

```
jpoke {config.category} 計画書作成タスク: {entry}

作業ディレクトリ: {config.worktree_base}\work

{config.spec_hint}
ハンドラ構成・subject_spec・priority（docs/spec/turn.md 参照）・実装コードを含む計画書を
{config.plan_dir}/{entry}.md に作成すること。CLAUDE.md のハンドラ約束事を厳守。
{entry} の効果がリーサル計算の HP 分布に影響する場合（回復・残留ダメージ・ピンチ回復・
ダメージ補正・耐え・みがわり貫通など）は、リーサル計算ハンドラ（handlers/lethal.py）の
設計も計画書に含める。影響しない場合は「リーサル: n/a（理由）」と明記する。
（計画書ファイルは作業ツリーに置くだけでよい。手順5の収穫で impl_queue に移り、impl コミットに含まれる）
```

### 8. 状態保存・終了

§共通7 に従う（続きは background エージェントの完了通知、またはユーザーの `/loop impl` 再実行で
再開する）。

---

## main への反映

エントリ単位では反映しない。§3.5 のバッチ整形コミットが成立するたびに、その手順内（§共通5 →
§共通6）で直ちに main へ反映される（`{branch}` = `loop/impl/integration`）。

## エラーハンドリング

§共通8 に加えて:
- impl 失敗 → `failed` に追加してループ継続（work worktree 内でブランチを削除してから次へ）。
- review-test 失敗 → `failed` に追加してループ継続（review worktree・ブランチを削除してから次へ）。
- エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。

## 状態例

```json
{
  "config": {
    "flow": "impl", "category": "変化技", "plan_dir": "docs/plan/moves",
    "spec_hint": "docs/spec/ の対応仕様書を参照（volatiles/, moves/, side_fields/, global_fields/ 以下も確認）",
    "progress_file": "docs/progress/move.md", "test_files": ["tests/test_move.py"],
    "impl_extra": "- data/move.py の MoveData に技が未登録なら追加する", "review_extra": "",
    "planning_slots_max": 2, "review_parallel_max": 1,
    "worktree_base": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\impl"
  },
  "plan_queue": ["からをやぶる", "ガードシェア"], "impl_queue": ["いばる"],
  "review_queue": ["あくまのキッス"], "review_in_progress": ["あくび"],
  "completed": [], "failed": [],
  "unformatted_merges": 4, "last_format_commit": "1df4c9e7..."
}
```

この例では: `あくび`=review-test background 実行中 / `あくまのキッス`=impl 完了・review 待ち /
`いばる`=今回 impl foreground / `からをやぶる`・`ガードシェア`=planner background 中。
