# ループ共通規約（全フロー共通）

各フローの指示書（`impl.md` / `review.md` / `todo.md` / `lethal.md` / `fuzz.md` / `replay_fuzz.md`）は、
このファイルを読んだ前提で書かれている。フロー固有の指示書は「§共通N を適用」と参照するので、
**必ず先にこのファイルを読むこと**。`{flow}` は各フローの識別子（`impl` / `review` / …）。

---

## §共通1: ディスパッチャーの役割

- **ディスパッチャー作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`（Claude セッションの CWD）。
- ここでは **git コミット・マージを一切行わない**。状態ファイル `.loop/` の読み書きと、
  worktree に対する `git -C "<worktree>" ...` 操作の起点としてのみ使う。
- **`jpoke/`（main）の作業ツリーには一切触れない**。

## §共通2: 統合ブランチ方式の原則

- ループの成果はフロー専用のブランチ（単一ブランチ方式は `loop/{flow}`、統合ブランチ方式は
  `loop/{flow}/integration`）に蓄積し、**main へは自動マージしない**。
- ユーザーの `jpoke/`(main) に触れないため、**ループ稼働中でも待ち・ref/index の奪い合い・
  未コミット変更によるブロックが発生しない**。
- 完了分を main に取り込むのは **ユーザーが任意のタイミングで行う**（§共通6）。

## §共通3: `.loop/` スクラッチ規約

- `.loop/` は **git 管理外のローカルスクラッチ**（`.gitignore` 済み）。状態ファイル・完了マーカー
  （`.ok`/`.fail`）・テストログはすべてコミット不要・コンフリクトなし。
- 状態ファイル等のドロップ先は常に**固定の絶対パス** `C:\Users\tmtmp\Documents\pokemon\jpoke\.loop\`
  を使う（worktree 側の `.loop/` ではなくディスパッチャー側を共有ドロップ先とする）。
- **状態ファイルの保存 = Write で上書きするだけ**。コミットしない。

## §共通4: worktree 準備（冪等・各ウェイクアップ冒頭で実行）

ディスパッチャー作業ディレクトリ `jpoke/` で実行する。フローはどちらか一方のパターンを使う。

### パターンA（単一ブランチ方式: todo / lethal / fuzz / replay_fuzz）

作業は永続 worktree `{config.worktree}`・ブランチ `loop/{flow}` 上で直接行う（サブブランチ無し）。

```bash
if ! git worktree list --porcelain | grep -q "branch refs/heads/loop/{flow}$"; then
  git worktree add -b loop/{flow} "{config.worktree}" main   # 初回。main から分岐
  # 新規作成時のみ §共通4.5（<worktree> = {config.worktree}）
else
  git -C "{config.worktree}" checkout loop/{flow}            # 既存: main の最新を取り込む
  git -C "{config.worktree}" merge main
fi
```

`loop/{flow}` を main に追従させておくと、後でユーザーが main へ FF 反映しやすい。

### パターンB（統合ブランチ方式: review / impl）

統合 worktree `{config.worktree_base}\integration`・ブランチ `loop/{flow}/integration` に集約する。
entry ブランチは `loop/{flow}/{entry}`（`loop/{flow}/` 配下の兄弟）。

> **D/F 衝突に注意**: 統合を `loop/{flow}` にすると entry ブランチ `loop/{flow}/{entry}` と
> git ref の D/F 衝突（`loop/{flow}` ファイルと `loop/{flow}/{entry}` ディレクトリ）を起こす。
> **必ず `loop/{flow}/integration` を使い**、entry 名に `integration` は使わない。

```bash
INTG="{config.worktree_base}\integration"
BR="loop/{flow}/integration"
if ! git worktree list --porcelain | grep -q "branch refs/heads/$BR$"; then
  if git show-ref --verify --quiet "refs/heads/$BR"; then
    git worktree add "$INTG" "$BR"          # ブランチはあるが worktree が無い
  else
    git worktree add "$INTG" -b "$BR" main  # 初回。main から分岐
  fi
  # 新規作成時のみ §共通4.5（<worktree> = $INTG）
fi
```

以降のディスパッチャーの git 操作はすべて `git -C "$INTG" ...`（統合 worktree）で行う。
entry worktree は `loop/{flow}/integration` の最新から分岐する。

## §共通4.5: worktree 作成時の設定ファイル複製（確認プロンプト回避）

`git worktree add` は git 管理下のファイルしか複製しないため、`.claude/settings.local.json`
（`.gitignore` 対象・個人の permission 設定）は新規 worktree に複製されない。複製されないと
その worktree 上のエージェント（background 含む）は各所のコミット済み `.claude/settings.json`
（狭い allow リストしかない）にフォールバックし、`git worktree`/`merge`/`branch`/`commit` や
`sort_data/*.py` などで毎回確認プロンプトが発生しループが止まる。

**`git worktree add` で worktree を新規作成した直後は必ず以下を実行する**（統合・単一ブランチ・
entry/slot 問わず全て対象。既存 worktree の再利用時は元から `.claude/` を保持しているので不要）:

```bash
SRC="C:\Users\tmtmp\Documents\pokemon\jpoke\.claude\settings.local.json"
if [ -f "$SRC" ]; then
  mkdir -p "<worktree>\.claude"
  cp "$SRC" "<worktree>\.claude\settings.local.json"
fi
```

`<worktree>` は今回作成した worktree のパス。各フロー指示書で「新規作成」に該当する箇所は
「§共通4.5 を適用」と参照する。

## §共通5: マージ後の一括整形・テスト一覧再生成（統合ブランチ方式のフローのみ）

slot / 実装エージェントは五十音ソート・`generate_test_list.py` を **行わない**（共有ファイルの
コンフリクト回避）。マージ後にディスパッチャーが統合ブランチ上でまとめて 1 回だけ実行する。
マージ前に `PRE=$(git -C "$INTG" rev-parse HEAD)` を記録し、これを差分基点にする。

```bash
cd "$INTG"
# 今回のバッチで変更されたハンドラ・data だけソート
for f in $(git diff --name-only $PRE..HEAD -- 'src/jpoke/handlers/*.py'); do
  python scripts/sort_handlers.py "$f"
done
CHANGED=$(git diff --name-only $PRE..HEAD -- 'src/jpoke/data/*.py')
echo "$CHANGED" | grep -q 'ability' && python scripts/sort_data/sort_abilities.py
echo "$CHANGED" | grep -q 'item'    && python scripts/sort_data/sort_items.py
echo "$CHANGED" | grep -q 'move'    && python scripts/sort_data/sort_moves.py
python scripts/sort_tests.py {フロー固有のテストファイル群}
python scripts/generate_test_list.py
python -m pytest tests/ -q          # 統合ブランチ全体でテストが通ることを最終確認
git add -A
git commit -m "chore: バッチ整形・テスト一覧再生成"
```

テストが失敗した場合は **commit せず**、失敗内容をユーザーに報告する（統合ブランチは調査用に残す）。

## §共通6: main への反映（ユーザーが任意のタイミングで実行）

ループとは非同期でよい。`{branch}` はフローの蓄積先ブランチ（`loop/{flow}` または
`loop/{flow}/integration`）。

```bash
# jpoke/ で:
git switch main
git merge --ff-only {branch}                 # 通常はこれで一発（main の子孫）
# main が独自に進んで FF 不可のときのみ:
git merge --no-ff {branch} -m "Merge {branch}"
```

FF 同期なら競合は起きない。ユーザーが main に独自コミットを重ねた場合だけ通常マージになる。

この main への直接マージは CLAUDE.md「ブランチ運用ルール」（手動作業のブランチ+PR義務化）の対象外
である。ループ成果は §共通2 の設計上 main から隔離された専用ブランチに蓄積されるため、その反映は
意図的にこの軽量な FF/マージで行う。

## §共通7: 状態保存と次ウェイクアップ予約

- **状態保存**: Write で `.loop/{flow}_state.json` を上書きする（§共通3・コミット不要）。
- **次ウェイクアップ**: ループを中断・終了しない限り、各フロー指定の `delaySeconds` で予約する。
  ```
  ScheduleWakeup(delaySeconds=<フロー指定>, prompt="<<autonomous-loop-dynamic>>",
                 reason="<フロー名>: 次へ")
  ```
- **終了時**（キューが空など）は ScheduleWakeup を呼ばず、完了を報告して終える。

## §共通8: 共通エラーハンドリング

- 同じ entry が `failed` に **2 回以上** → スキップして次へ。
- non-fast-forward で衝突 → 自動解決せず `git -C "$INTG" merge --abort` で中断し、`failed` に記録して
  ユーザーに報告（worktree・ブランチは調査用に残す）。
- 統合／永続 worktree が壊れた・消えた → §共通4 が冪等に再作成する。
- background エージェントの結果ファイルが来ない → 次のウェイクアップで再確認（勝手に再試行しない）。

## §共通9: `.ok`/`.fail` マーカー削除時のガード（rtk フック対策）

`rm -f "$VAR1/$VAR2..."` のようにシェル変数を無検証のまま rm のパスに使うと、グローバル設定
（`~/.claude/settings.json`）の `rtk hook claude`（PreToolUse）が「危険な rm」として検知し、
`bypassPermissions` を設定していても確認プロンプトを強制する。自律ループ中にこれが起きると
応答者不在でループが停止するため、ハーベスト処理で `.ok`/`.fail` を削除する際は必ず存在チェックを
挟んでから rm する。

```bash
target="$RES/{name}.ok"   # または .fail
if [ -n "$target" ] && [ -f "$target" ]; then
  rm -f "$target"
fi
```

worktree 削除（`git worktree remove`）やブランチ削除（`git branch -d/-D`）は git コマンドであり
このフックの対象外なので、素の呼び出しで問題ない。ガードが必要なのは生の `rm` のみ。

## §共通10: シードベース継続バグ出しループの共通骨格

`fuzz.md` / `replay_fuzz.md` が参照する。両者とも「シード付きでランダムに大量実行 → 未捕捉例外や
不整合を検出 → impl で修正 → review-test で回帰テスト」という同じ形の単一ブランチループのため、
共通部分をここにまとめる。フロー固有の差分（調査観点・レポートパスパターン・モード管理等）は
各指示書側に残す。

### 再開ルール

`current_failure` が null でない場合、前回のウェイクアップが中断された状態。手順4（バグ対応）から
やり直す。

### signature 重複チェック

`failed_bugs` に同じ `signature` が **attempts >= 2** で存在する場合 → **ループを中断**
（ScheduleWakeup を呼ばない）。「同一バグ（signature: {signature}）の自動修正が2回失敗したため、
{flow}ループを停止しました。再現コマンドは {report内の再現コマンド} です。手動確認が必要です。」
と報告して終了する。

### impl エージェント（foreground）の共通ステップ

1. 再現コマンドで再現することを確認する
2. 原因を調査する（フロー固有の調査観点に従う）
3. 原因を修正する（テストは書かない。review-test エージェントが担当）
4. `handlers/` を変更した場合、`python scripts/sort_handlers.py src/jpoke/handlers/<category>.py` を実行する
5. `data/ability.py` / `data/item.py` / `data/move.py` を変更した場合、対応する sort スクリプトを実行する
6. 再度再現コマンドを実行し、解消したこと（`OK:` が出力されること）を確認する
7. コミットはしない（review-test エージェントが担当）

失敗（原因不明・修正できず）した場合: `failed_bugs` の該当 signature を探し、あれば `attempts += 1`、
なければ新規エントリを追加する。`current_failure` をクリアして保存し、review-test はスキップする。

### review-test エージェント（foreground）の共通ステップ

impl 成功後のみ実施:

1. 修正内容をレビューする（レポートに元の例外・原因箇所の情報がある）
2. 原因箇所に応じた最小の決定的な回帰テストを追加する。**ランダムなfuzzシードをそのままテストに
   しない**（乱数依存でエンジン変更のたびに壊れるため）
3. `python scripts/sort_tests.py <対象ファイル>` を実行する
4. `python scripts/generate_test_list.py` を実行する
5. `python -m pytest tests/ -v` を実行し、全件パスすることを確認する
6. 変更をコミットする（`{branch}` ブランチ上で行う）

成功した場合: `completed_bugs` に追加し、`failed_bugs` に同じ signature があれば削除する。
失敗した場合: impl 失敗時と同様に `failed_bugs` を更新する。いずれも `current_failure` をクリアして保存する。

> このフローは単一ブランチ・単一エージェントのため、ソートはエージェント側で実行する
> （§共通5「マージ後一括整形」は適用しない）。main へのマージも行わない（§共通2）。

## §共通11: リーサル計算ハンドラの実装パターン

`impl.md` / `review.md` / `lethal.md` が参照する。リーサル計算ハンドラ（`handlers/lethal.py`）を
新規実装・修正する際は共通で以下に従う。各指示書側には「このパターンに該当するかどうかの判断」
だけを残す。

- シグネチャ: `(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist`
- 既存パターン（`_heal`, `_heal_at_pinch`, `_survive_at_full_hp`, `_type_resist_berry` など）を参照して実装する
- 種別に対応する data ファイルの `lethal_handlers` にエントリを追加する:
  - `move` → `data/move.py`
  - `item` → `data/item.py`
  - `ability` → `data/ability.py`
  - `ailment` → `data/ailment.py`
  - `volatile` → `data/volatile.py`
  - `global_field` → `data/field.py`
- イベントは `LethalEvent.ON_BEFORE_HIT` / `ON_HIT` / `ON_TURN_END` / `ON_EVERY_EVENT` から選ぶ
- subject は `"attacker"` / `"defender"` / `None` から選ぶ
