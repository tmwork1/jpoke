# ループ共通規約（全フロー共通）

各フローの指示書（`impl.md` / `review.md` / `todo.md` / `impl_lethal.md` / `fuzz.md` / `replay_fuzz.md` /
`fuzz_log.md` / `flaky.md` / `api.md`）は、このファイルを読んだ前提で書かれており、
「§共通N を適用」の形でここを参照する。
**必ず先にこのファイルを読むこと**。`{flow}` は各フローの識別子（`impl` / `review` / …）。

---

## §共通1: ディスパッチャーの役割

- **ディスパッチャー作業ディレクトリ**: プロジェクトルート（Claude セッションの CWD）。以降
  このディレクトリを `$ROOT` と表記する。ユーザー名・ドライブレターは実行環境（端末）ごとに
  異なるため、本ドキュメント群では絶対パスをハードコードせず、必要な箇所で都度
  `ROOT="$(git rev-parse --show-toplevel)"` として求める。worktree 側（CWD が異なる）から
  `$ROOT` を求める場合は、全 worktree が共有する `.git` の場所から逆算する:
  `ROOT="$(dirname "$(git -C "<worktree>" rev-parse --path-format=absolute --git-common-dir)")"`。
  状態ファイル例・result file パス例に登場する `$ROOT` 由来のパスは、実際にはこの方法で求めた
  絶対パスに読み替えること（他端末の具体例をそのままコピーしない）。
- ここでは **git コミット・マージを一切行わない**。状態ファイル `.loop/` の読み書きと、
  worktree に対する `git -C "<worktree>" ...` 操作の起点としてのみ使う。
- **`jpoke/`（ローカル main の作業ツリー）には一切触れない**。main への反映は §共通6 の通り
  GitHub 上の PR 経由（`gh pr create` / `gh pr merge`）で行うため、ローカルの `jpoke/` を
  書き換える必要がない。
  - 理由: 同一リポジトリの worktree はすべて同じ `.git` を共有しており、ローカル `main` ブランチへ
    直接コミット・マージすると、他セッション・他 worktree から見える `main` の先端が即座に変化して
    しまう。これを避けるため、ローカル `main` は自動では一切書き換えない（§共通2・§共通6 も
    この理由を前提とする）。

## §共通2: ブランチ蓄積と main 反映の原則

- ループの成果はフロー専用のブランチ（単一ブランチ方式は `loop/{flow}`、統合ブランチ方式は
  `loop/{flow}/integration`）にまず蓄積する。
- ローカルテスト（各フローの review-test 等）を通過した単位で、ディスパッチャーが **都度自動的に
  GitHub PR 経由で main へ反映する**（§共通6）。反映の粒度はフローごとに異なる:
  - `fuzz` / `replay_fuzz` / `fuzz_log` / `flaky` / `api`（単一ブランチ方式）: 1件の修正コミットごと
  - `todo`: 5件ごと / `impl_lethal`: 10件ごと（単一ブランチ方式、いずれも専用カウンタで管理）
  - `impl` / `review`（統合ブランチ方式）: §共通5 のバッチ整形コミットごと
- **承認条件はローカルテストの通過そのもの**であり、人間のレビュー待ち・PR コメント対応は行わない。
- 反映は GitHub 上の操作（`gh pr create` / `gh pr merge`）のみで完結し、ローカル `main` は
  一切書き換えない（理由は §共通1）。ユーザーが `git pull` した時点で初めてローカルに反映される。
- 複数フローが並行稼働していても、それぞれ独立したブランチ・PR で完結するため、ロック等の
  排他制御は不要。

## §共通3: `.loop/` スクラッチ規約

- `.loop/` は **git 管理外のローカルスクラッチ**（`.gitignore` 済み）。状態ファイル・完了マーカー
  （`.ok`/`.fail`）・テストログはすべてコミット不要・コンフリクトなし。
- 状態ファイル等のドロップ先は常に**固定のディレクトリ** `$ROOT\.loop\`（§共通1 参照）
  を使う（worktree 側の `.loop/` ではなくディスパッチャー側を共有ドロップ先とする）。
- **状態ファイルの保存 = Write で上書きするだけ**。コミットしない。

## §共通4: worktree 準備（冪等・各起動冒頭で実行）

ディスパッチャー作業ディレクトリ `jpoke/` で実行する。フローはどちらか一方のパターンを使う。

**必ず `origin/main`（GitHub 上の最新）を起点にする。ローカルの `main` ブランチは参照しない。**
main への反映は GitHub PR 経由で行われ（§共通6）、ユーザーが `git pull` するまでローカル `main`
は更新されない。そのためローカル `main` を起点にすると、他フローや他 PR が既に main に反映した
内容を見落とし、古い状態から作業を始めてしまう。「loop 側のブランチが main から大きく取り残され、
後で巨大なコンフリクトになる」という、このプロジェクトで実際に起きた事故の再発防止である。
各パターンの先頭で必ず次を実行する:

```bash
git fetch origin main --quiet
```

### パターンA（単一ブランチ方式: todo / impl_lethal / fuzz / replay_fuzz / fuzz_log / flaky / api）

作業は永続 worktree `{config.worktree}`・ブランチ `loop/{flow}` 上で直接行う（サブブランチ無し）。

```bash
if ! git worktree list --porcelain | grep -q "branch refs/heads/loop/{flow}$"; then
  git worktree add -b loop/{flow} "{config.worktree}" origin/main   # 初回。origin/main から分岐
  # 新規作成時のみ §共通4.5（<worktree> = {config.worktree}）
else
  git -C "{config.worktree}" checkout loop/{flow}            # 既存: origin/main の最新を取り込む
  git -C "{config.worktree}" merge origin/main
fi
```

`loop/{flow}` を origin/main に追従させておくことで、§共通6 の PR 作成・マージが素直な差分になる
（main が独自に進んでいても non-fast-forward マージで吸収できるが、追従頻度が高いほどコンフリクト
リスクは下がる）。non-fast-forward で衝突する場合は §共通14 の手順で自律解消を試みる（ユーザーの
確認は待たない）。

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
    git worktree add "$INTG" "$BR"                 # ブランチはあるが worktree が無い
  else
    git worktree add "$INTG" -b "$BR" origin/main  # 初回。origin/main から分岐
  fi
  # 新規作成時のみ §共通4.5（<worktree> = $INTG）
fi
git -C "$INTG" merge origin/main   # 既存の場合も含め、毎回 origin/main の最新を取り込む
```

以降のディスパッチャーの git 操作はすべて `git -C "$INTG" ...`（統合 worktree）で行う。
entry worktree は `loop/{flow}/integration` の最新から分岐する。この origin/main 取り込みで
non-fast-forward 衝突する場合は §共通14 の手順で自律解消を試みる（ユーザーの確認は待たない）。
entry ブランチを統合ブランチへマージする際の衝突も同様に §共通14 の対象である。

## §共通4.5: worktree 作成時の設定ファイル複製（確認プロンプト回避）

`git worktree add` は git 管理下のファイルしか複製しないため、`.claude/settings.local.json`
（`.gitignore` 対象・個人の permission 設定）は新規 worktree に複製されない。複製されないと
その worktree 上のエージェント（background 含む）は各所のコミット済み `.claude/settings.json`
（狭い allow リストしかない）にフォールバックし、`git worktree`/`merge`/`branch`/`commit` や
`sort_data/*.py` などで毎回確認プロンプトが発生しループが止まる。

**`git worktree add` で worktree を新規作成した直後は必ず以下を実行する**（統合・単一ブランチ・
entry/slot 問わず全て対象。既存 worktree の再利用時は元から `.claude/` を保持しているので不要）:

```bash
ROOT="$(git rev-parse --show-toplevel)"
SRC="$ROOT\.claude\settings.local.json"
if [ -f "$SRC" ]; then
  mkdir -p "<worktree>\.claude"
  cp "$SRC" "<worktree>\.claude\settings.local.json"
fi
```

`<worktree>` は今回作成した worktree のパス。各フロー指示書で「新規作成」に該当する箇所は
「§共通4.5 を適用」と参照する。

## §共通5: マージ後の一括整形（統合ブランチ方式のフローのみ）

slot / 実装エージェントは五十音ソートを **行わない**（共有ファイルの
コンフリクト回避）。整形は全体テストを毎回走らせるコストの高い処理のため、**マージのたびに毎回
実行するのではなく、未整形のマージが 10 件たまるごとに** ディスパッチャーが統合ブランチ上でまとめて
1 回だけ実行する。

状態ファイルに以下の 2 フィールドを持つ（フロー側のスキーマに追加する）:
- `unformatted_merges`: 前回整形以降にマージが成功した件数（マージ成功のたびに +1）
- `last_format_commit`: 前回整形を実行した時点の統合ブランチ HEAD（無ければ統合ブランチ作成時の
  コミット。差分基点として使う）

`unformatted_merges >= 10` になったら整形を実行する。ループ終了時（キューが尽きて完了報告する場合）
は、`unformatted_merges` が 10 未満でも 1 件以上残っていれば整形してから終える。

```bash
INTG="{config.worktree_base}\integration"
cd "$INTG"
PRE="{last_format_commit}"
# 前回整形以降に変更されたハンドラ・data だけソート
for f in $(git diff --name-only $PRE..HEAD -- 'src/jpoke/handlers/*.py'); do
  python scripts/sort_handlers.py "$f"
done
CHANGED=$(git diff --name-only $PRE..HEAD -- 'src/jpoke/data/*.py')
echo "$CHANGED" | grep -q 'ability' && python scripts/sort_data/sort_abilities.py
echo "$CHANGED" | grep -q 'item'    && python scripts/sort_data/sort_items.py
echo "$CHANGED" | grep -q 'move'    && python scripts/sort_data/sort_moves.py
python scripts/sort_tests.py {フロー固有のテストファイル群}
python -m pytest tests/ -q          # 統合ブランチ全体でテストが通ることを最終確認
git add -A
git commit -m "chore: バッチ整形"
```

整形実行後、`unformatted_merges = 0`、`last_format_commit = $(git -C "{config.worktree_base}\integration" rev-parse HEAD)` に更新する。
続けて §共通6 の手順に従い、この整形コミットまでを直ちに main へ反映する
（`{branch}` = `loop/{flow}/integration`）。

テストが失敗した場合、まず flaky かどうかを確認する（失敗が flaky と判明した場合は §共通13 に従い
その場で修正する）。flaky でない場合は §共通15 の手順で1回だけ自律修正を試みる。修正できた場合は
そのままコミットに含め、続けて main へ反映する。修正できなかった場合は **commit せず**、失敗内容を
ユーザーに報告する（統合ブランチは調査用に残す）。この場合 `unformatted_merges` はリセットしない
（次回また整形を試みる）。main への反映も行わない。

## §共通6: main への反映（ディスパッチャーが都度自動実行・PR経由）

`{branch}` はフローの蓄積先ブランチ（`loop/{flow}` または `loop/{flow}/integration`）。
実行タイミングは各フロー指示書の「main への反映」節で規定する（フローごとの粒度は §共通2 参照）。
反映条件はローカルテスト（各フローの review-test 等で既に実行済み）を通過していることであり、
ユーザーの都度承認や人間レビューは待たない（§共通2）。

**`jpoke/`（ローカル main の作業ツリー）には一切触れない**（§共通1）。GitHub 上の PR を経由して
反映することで、他セッション・他 worktree が参照するローカル `main` の ref を不用意に動かさない。

### 手順

`{branch}` の worktree（無ければ任意の worktree から `git -C "<worktree>" push` で足りる）から:

**0. origin/main への再同期**（push の直前に毎回実行する。ループが長期化するほど main との差分が
開きコンフリクトが肥大化するため、main へ反映するたびに追従させておく）:

```bash
git fetch origin main --quiet
git -C "<worktree>" merge origin/main
```

non-fast-forward で衝突する場合は §共通14 の手順で自律解消を試みる。解消できた（または元々
衝突がなかった）場合のみ以下に進む。

```bash
git -C "<worktree>" push origin {branch}
gh pr create --base main --head {branch} --fill
# 複数コミットをまとめて反映する場合（統合ブランチ方式のバッチ整形・todo/impl_lethal のバッチ等）で
# --fill が不適切なら --title/--body を明示し、含まれるコミット一覧を本文に列挙する
gh pr merge {branch} --merge --delete-branch=false
```

- `--delete-branch=false` を必ず指定する: `{branch}` はフローが継続して使う永続ブランチのため、
  リモート側も削除しない（`delete_branch_on_merge` の自動削除対象から明示的に外す）。ただし
  バックログを使い切りループが完全終了する場合は §共通7「完全終了」の手順でブランチごと削除する。
- ローカルテスト済みのため人間レビューは待たず、作成した PR を即座に `gh pr merge` する。
- `gh pr merge` が失敗した場合、失敗理由で扱いを分ける:
  - **衝突由来**（手順0の再同期後に main がさらに進み non-fast-forward になった等、取り込み漏れが
    原因と判断できる場合）→ `git fetch origin main --quiet` して手順0からやり直し（§共通14 の自律
    解消を経由してよい）、push・PR作成・マージを **1回だけ** 再試行する。ユーザーの確認は待たない。
  - **非衝突要因**（ブランチ保護・必須ステータスチェック未達・権限エラー等、ファイル編集では解消
    できない原因）、または上記の再試行後も失敗する場合 → 自動解決せず、PR を open のままユーザーに
    報告して中断する（§共通8 相当）。フロー側のブランチ・コミットは無傷のまま残るので、次回ターン
    で再試行するか、ユーザーが手動で解決すればよい。

反映（PR マージ）が GitHub 上で成立しても、`jpoke/` のローカル `main` ブランチは動かない。
ユーザーが `git pull`（または `git fetch` + `checkout`）した時点で初めてローカルに反映される
（CLAUDE.md「Git運用ルール」参照）。

この PR は CLAUDE.md「Git運用ルール」の手動作業向けステップ（`確認のうえ gh pr merge`）の対象外
である（§共通2 の設計上、承認条件はローカルテストの通過であり、ユーザーの都度承認を待たず
ディスパッチャーが自動的に `gh pr merge` する）。

## §共通7: 状態保存と終了

- **状態保存**: Write で `.loop/{flow}_state.json` を上書きする（§共通3・コミット不要）。
- **継続の仕組み**: 1回の起動で処理できる範囲を実行したら、そこでターンを終える。以降の継続は
  次の2通りのいずれかで起こる:
  1. **background エージェントの完了通知**: dispatch した review-test / impl 等のエージェントが
     完了すると `<task-notification>` が届く。それに応答する形で収穫・補充・次の処理を行う
     （実質的に「次のステップ」として機能する）。
  2. **ユーザーによる再実行**: ユーザーが任意のタイミングで `/loop {flow}` を再度実行すると、
     状態ファイルを読み込んで続きから再開する。
- **ターン終了**（1回の起動で処理できる範囲をやり切ったが、キューや調査対象がまだ残っている・
  今後増える見込みがあるなど、次回 `/loop {flow}` での再開を前提とする一時停止）は、worktree・
  ブランチを残したまま完了を報告して終える（次回起動時に §共通4 がそのまま再利用する）。
- **完全終了**（各フロー指示書の「終了チェック」等でバックログ・キューを使い切り「全件完了」と
  報告してループそのものを終えるケース）は、報告の前に必ず以下を行う:
  1. §共通6 の手順で未反映分（`unformatted_merges` / `pending_main_merges` 等）をすべて main へ
     反映済みであることを確認する（残っていれば先に反映する）。
  2. entry/slot worktree が残っていれば削除する（通常はマージのたびに都度削除済みのはず）。
  3. フロー本体の worktree を削除する:
     ```bash
     git worktree remove "<worktree または $INTG>" --force
     ```
  4. ブランチを削除する（ローカル・リモート双方）:
     ```bash
     git branch -D loop/{flow}                    # 統合ブランチ方式なら loop/{flow}/integration
     git push origin --delete loop/{flow}         # 同上（統合ブランチ方式なら loop/{flow}/integration）
     ```
     §共通6 の `--delete-branch=false` はループ継続中にリモートブランチを存続させるための指定で
     あり、完全終了時はこの限りではない。
  5. 状態ファイルのキュー・カウンタをリセットして保存する。次回 `/loop {flow}` 実行時は §共通4 が
     origin/main を起点に worktree・ブランチを新規作成するため、ブランチ名の重複は起きない。
  - 理由: 反映済みの内容は main の履歴にすべて残るため、バックログを使い切った後まで worktree・
    ブランチを保持し続ける意味がない。残したままだと「まだ未反映の作業が残っている」ように見えて
    紛らわしい（CLAUDE.md「一時保存・worktree」の原則に合わせる）。

## §共通8: 共通エラーハンドリング

- 同じ entry が `failed` に **2 回以上** → スキップして次へ。
- non-fast-forward で衝突 → まず §共通14 の自律解消を試みる（origin/main 取り込み時・entry ブランチの
  統合ブランチへのマージ時のいずれも対象、ユーザーの確認は待たない）。それでも解消できなかった場合
  のみ、自動解決を諦めて対象 worktree（パターンAなら `<worktree>`、パターンBなら統合 worktree
  `{config.worktree_base}\integration`）で `merge --abort` して中断し、`failed` に記録してユーザーに
  報告する（worktree・ブランチは調査用に残す）。
- 統合／永続 worktree が壊れた・消えた → §共通4 が冪等に再作成する。
- background エージェントの結果ファイルが来ない → 次回の起動（完了通知またはユーザーの再実行）で
  再確認する（勝手に再試行しない）。

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

`fuzz.md` / `replay_fuzz.md` / `fuzz_log.md` が参照する。いずれも「シード付きでランダムに大量実行 → 未捕捉例外や
不整合を検出 → impl で修正 → review-test で回帰テスト」という同じ形の単一ブランチループのため、
共通部分をここにまとめる。フロー固有の差分（調査観点・レポートパスパターン・モード管理等）は
各指示書側に残す。

### 再開ルール

`current_failure` が null でない場合、前回の起動が中断された状態。手順4（バグ対応）から
やり直す。

### signature 重複チェック

`failed_bugs` に同じ `signature` が **attempts >= 2** で存在する場合 → **ループを中断**。
「同一バグ（signature: {signature}）の自動修正が2回失敗したため、
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
4. `python -m pytest tests/ -v` を実行し、全件パスすることを確認する（今回の修正と無関係な既存テストが
   flaky と判明した場合は §共通13 に従いその場で修正する）
5. 変更をコミットする（`{branch}` ブランチ上で行う）

成功した場合: `completed_bugs` に追加し、`failed_bugs` に同じ signature があれば削除する。
失敗した場合: impl 失敗時と同様に `failed_bugs` を更新する。いずれも `current_failure` をクリアして保存する。

成功時は続けて各フロー指示書の「main への反映」の手順に従い、この1件をただちに main へマージする
（単発修正自体を先に確定させる）。**その main 反映が完了した後**、§共通16 の判断基準を適用し、
単発修正で足りるか体系的対応が必要かを判断する（詳細な適用箇所は各フロー指示書の「main への反映」
節に明記する）。

> このフローは単一ブランチ・単一エージェントのため、ソートはエージェント側で実行する
> （§共通5「マージ後一括整形」は適用しない）。main への反映は各フロー指示書の
> 「main への反映」節（§共通6、1件ごとに即時）に従う。§共通16 による横断リファクタを行う場合の
> main への反映は §共通16 側の特例（1件ごとではなく1セット単位）に従う。

## §共通11: リーサル計算ハンドラの実装パターン

`impl.md` / `review.md` / `impl_lethal.md` が参照する。リーサル計算ハンドラ（`handlers/lethal.py`）を
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

## §共通12: APIセッション制限への対応

全フロー共通。§共通7 の方針と一貫させ、セッション制限からの自動待機・自動再開・リセット時刻の
予測の仕組みは持たない。制限を検知したら**その場で止まり、ユーザーに報告してターンを終える**。
再開はユーザーが次に `/loop {flow}` を実行したときに行う。

1. **セッション制限エラーを検知する**: foreground/background 問わず、エージェント（ディスパッチャー
   自身を含む）の呼び出しが「セッション制限」エラー（例:
   `You've hit your session limit · resets HH:MMam (Etc/GMT-9)`）で失敗した場合、それ以上の
   新規ディスパッチを止める（同時に複数エージェントが同一メッセージで失敗している場合も
   再試行しない）。
2. **完了済みの分は失わない**: 制限失敗は一部のエージェントのみに起きることがある（例: 4並列中1件
   だけ成功）。ターンを終える前に、既に成功・コミット済みの分は通常どおりマージ・ハーベストする。
3. **状態を保存してターンを終える**: 未処理の entry（失敗したエージェントに対応する分）は
   `in_progress` やキューから無理に取り除かず、実態に合わせて state を保存する。「◯件がセッション
   制限で失敗しました。ユーザーが `/loop {flow}` を再実行すると再開します」と報告してターンを終える。
4. **次回起動時の再開**: ユーザーが `/loop {flow}` を再度実行したときに再開する。前回失敗していた
   entry は §共通8 のエラーハンドリング（ワークツリーの状態を確認し、未コミットの作業は破棄して
   作り直す）に従って再ディスパッチする。まだ制限中であれば同じ流れで再度検知・報告する。

## §共通13: テスト実行中に flaky test を発見した場合

全フロー共通（専用の `flaky` ループ自体は除く。あちらは体系的な検出が本編）。今回の entry/修正とは
無関係な既存テストが `python -m pytest tests/ -v` 等の実行中に原因不明・間欠的に失敗した場合、
「既知のflakyとして再実行して収束を確認」だけで済ませて次に進んではいけない。**発見したその場で
原因調査・修正まで完了させる**（放置すると以降の全フローの回帰確認に影響するため）。

1. 対象テストを単体で数回再実行し、間欠的な失敗（毎回失敗ではない）であることを確認する。
   毎回失敗する場合は flaky ではなく通常のデグレ／バグなので対象外（通常のエラーハンドリングに従う）。
2. 現在作業中の impl / review-test エージェントがその場で原因調査・修正を行う。よくある原因は
   `battle.random.random` 等の乱数モック漏れ、テスト間の状態汚染（モジュール/クラスレベルの可変
   状態）、実行順序依存。
3. 修正後、対象テストを単体で複数回連続実行し、収束（毎回成功）することを確認してからコミットする。
4. 今回のフロー本来の変更と同じコミットに含めてよい。**後回しにせず、今回のブランチのコミットに
   含めて main へ反映する**。
5. その場で原因が特定できない・修正しきれない場合のみ、`.loop/flaky_found.md`（無ければ新規作成、
   git 管理外）に `{test_id, 発見日時, 発見元フロー, 症状}` を追記してユーザーに報告し、詳しい調査は
   専用の `flaky` ループ（`.claude/loop/flaky.md`）に委ねる。

## §共通14: loop フロー内マージ衝突の自律解消

**適用範囲**: loop フロー実行中に発生する git マージ衝突全般。ユーザーの確認は待たず、以下の
手順で自律解消を試みる。
- §共通4（ターン開始時に `loop/{flow}` または統合 worktree へ origin/main を取り込む処理）
- §共通6 手順0（PR 作成直前の origin/main 再同期）
- entry/slot ブランチを統合ブランチへマージする際の衝突（`impl.md` / `review.md` の Harvest 処理等）

対象外（ファイル編集では解消できないため §共通8 に従い中断・報告する）:
- `gh pr merge` 自体の失敗のうち非衝突要因のもの（ブランチ保護・必須ステータスチェック未達・権限
  エラー等。衝突由来の失敗は §共通6 の再試行手順に従う）
- 同じコンフリクトに対して本手順を1回試みて失敗した場合の再試行（リトライしない）

### 手順

1. コンフリクトファイル一覧を取得する: `git -C "<worktree>" diff --name-only --diff-filter=U`
2. `review-test` エージェント（foreground・1回のみ）にコンフリクト解消一式を委任する。ディスパッチャー
   自身は解消作業を行わない。エージェントへの依頼内容:
   - コンフリクトマーカー（`<<<<<<<` / `=======` / `>>>>>>>`）を、**両側の変更意図を保ったまま**解消する
     （どちらか一方を機械的に破棄しない。`-X ours`/`-X theirs` のような戦略的マージは使わない）
   - `data/ability.py` / `data/item.py` / `data/move.py` を解消した場合、対応する
     `scripts/sort_data/sort_*.py` を再実行する
   - `python -m pytest tests/ -v` を実行し、全件パスすることを確認する
   - パスしたら `git add -A && git commit`（マージコミットを完成させる。メッセージ例:
     `merge: origin/main 取り込み（コンフリクト解消）` / `merge: loop/impl/{entry}（コンフリクト解消）`）
3. エージェントの結果をディスパッチャーが判定する:
   - **成功**（コンフリクト全解消・全テストパス・コミット済み）→ そのまま後続処理を続ける
     （§共通4 なら通常のフロー処理へ、§共通6 なら手順0以降の push/PR作成・マージへ進む）
   - **失敗**（テストが落ちた、またはコンフリクトの意味を確定できないとエージェントが判断した場合）
     → **リトライしない**。`git -C "<worktree>" merge --abort` で中断し、§共通8 の通り `failed` に
       記録してユーザーに報告する（フロー側の元のコミットは無傷のまま残る。worktree・ブランチは
       調査用に残す）。

## §共通15: バッチ整形（§共通5）テスト失敗時の自律修正

**適用範囲**: §共通5 でバッチ整形後の `python -m pytest tests/ -q` が失敗した場合（flaky と判明した
場合は §共通13 が優先し、こちらは対象外）。個別エントリは合流前に review-test 等で単体テスト済みの
ため、この失敗は複数エントリの変更を組み合わせて初めて顕在化した相互作用バグである可能性が高い。

### 手順

1. `review-test` エージェント（foreground・1回のみ）に、失敗したテストのログと
   `git -C "{config.worktree_base}\integration" diff {last_format_commit}..HEAD` の差分
   （今回合流した各エントリの変更内容）を渡し、
   原因調査・修正一式を委任する。**ビセクト（entry ごとの逐次テスト実行）は行わず**、差分とテスト
   失敗のログから直接原因を特定させる:
   - 原因箇所を修正する
   - `python -m pytest tests/ -v` を実行し、全件パスすることを確認する
   - パスしたら、修正を整形コミットに含める（`git add -A && git commit`。メッセージ例:
     `fix: バッチ整形時に発覚した相互作用バグの修正`）
2. エージェントの結果をディスパッチャーが判定する:
   - **成功**（全テストパス・コミット済み）→ §共通5 の残り手順（`unformatted_merges` リセット等）へ
     進み、続けて §共通6 で main へ反映する
   - **失敗**（原因を特定できない、または修正してもテストが通らない）→ **リトライしない**。§共通5 の
     従来通り commit せず、失敗内容をユーザーに報告する（統合ブランチは調査用に残し、
     `unformatted_merges` はリセットしない）

## §共通16: 単発修正か体系的対応かの判断・sub agentへの委譲

**適用範囲**: `fuzz` / `fuzz_log` / `replay_fuzz` / `flaky`（バグ発見型の単一ブランチループ）。
`impl_lethal` はバックログの新規実装（未知のバグ発見ではない）であり「同じ原因パターンの繰り返し」
という前提が当てはまらないため対象外。`impl` / `review` も新規実装・レビューが主目的であり対象外。

### 背景

`impl` は原因箇所1件を最小修正するエージェントであり、それ自体は正しい設計だが、複数のバグの
根本原因が実は同一だった場合、この2段階パターン（impl → review-test）を都度繰り返すだけでは
「同種の見落としが他の箇所にも潜在的に多数存在する」という俯瞰的な気づきが起こりにくい
（実例: 「瀕死になったポケモンに対してハンドラが誤発動する」という同一原因のバグが、対象を変えて
20件以上、1つずつ別々の signature として発見・個別修正されていた）。このセクションは、単発修正を
繰り返すべきか、根本原因を横断的に解消すべきかをその都度判断し、後者の場合の対応手順を定める。

### 判断のタイミング

- 主に review-test 成功時（`completed_bugs` に今回のエントリを追加した直後）にディスパッチャーが
  判断する（§共通10 の review-test 成功時ルール、および `flaky.md` の該当箇所から参照される）。
- impl が原因調査中に「同種の書き忘れが他にも多数ありそうだ」と明示的に報告した場合も、判断材料に
  加える。ただし **単発修正・review-test は必ず先に完了させる**（体系的対応が必要そうだからと
  いって、その場の単発修正を止めて切り替えることはしない。単発修正を完了・反映した上で、必要なら
  追加で体系的対応を行う）。

### 判断基準

以下のうち **2つ以上** に該当する場合、「体系的リファクタが必要」と判断する。1つだけの該当では
単発修正で十分と判断し、通常どおり次に進む。

- 同一の防御的チェック（ガード）がコードベース中に類似パターンで何度も手書きされている
  （コピー&ペーストされている）ことが原因である
- `completed_bugs` / `failed_bugs` 台帳や `git log --oneline {branch}` に、signature は異なるが
  本質的に同じ原因パターンの修正が **目安3回以上** 記録されている（`completed_bugs` の `summary` を
  Grep し、似た表現が繰り返し登場していないか確認する）
- 原因が「個別のハンドラ実装の書き忘れ」ではなく、「そのクラスの実装を安全にする一元的な仕組み
  （宣言的フィールド・共通ヘルパー関数・基底クラスの既定動作等）がそもそも存在しないこと」に
  起因する
- 修正が1〜2ファイルの局所的な変更では閉じず、同種のパターンが **5箇所以上** の複数ファイルに
  散らばっている（`grep`/`Grep` で類似ガード文字列を検索し、ヒット数で判断する）

該当する場合でも明らかに緊急度が低い・影響範囲が不確かな場合は、無理に体系的対応へ進めず、
判断根拠とともにユーザーに報告して次のバグ対応に進んでもよい（体系的対応は義務ではなく、
まとめて解消したほうが安全・効率的と判断できる場合の選択肢）。

### 体系的と判断した場合: 横断リファクタ sub agent への委譲

`impl` / `review-test` は個別箇所の最小修正に特化したエージェントであり、複数ファイルにまたがる
設計変更（宣言的フィールドの追加、共通ヘルパーへの集約、基底クラスの既定動作変更等）を任せる
想定ではないため、この用途には汎用の `general-purpose` サブエージェントを使う（foreground・
`{branch}` の worktree（`{worktree}`）上でそのまま作業させる。新しい worktree は作らない）。

```
jpoke {flow} 横断リファクタタスク: {パターンの短い説明}

作業ディレクトリ: {worktree}

{flow} ループが、本質的に同じ原因パターンのバグを複数回（{件数}回。対象 signature/summary:
{該当エントリの一覧}）個別に発見し、そのたびに1箇所だけの手書き修正（例: {代表的な修正例}）を
繰り返していた。これは場当たり的な対症療法であり、同種の見落としが他の未検出の箇所にも
潜在している可能性が高い。

CLAUDE.md（実装ルール・ハンドラの約束事・状態変更ルール）を読み込んだ上で、この問題クラスを
横断的に解消する設計を立てて実装すること。対応方針の例（そのまま採用しなくてよい。実際のコードを
調査した上で最適な設計を判断すること）:
- 宣言的なフィールドを共通の基底・データクラスに追加し、判定を一元化する
- 個別ハンドラに散らばったチェックを共通ヘルパー関数に集約する
- 基底クラスの既定動作自体を安全側に変更する

手順:
1. CLAUDE.md の実装時参照順に従い、関連する core/ handlers/ data/ を調査し、同種パターンが
   実際に何箇所に存在するかを特定する
2. 横断的な解消方法を設計する（複数ファイルにまたがってよい）
3. 実装する（CLAUDE.md のハンドラ約束事・状態変更ルールを厳守）
4. `handlers/` を変更した場合、対応する `python scripts/sort_handlers.py` を実行する
5. `data/*.py` を変更した場合、対応する `scripts/sort_data/sort_*.py` を実行する
6. 個別に書かれていた対症療法的なガード（今回の横断対応で不要になったもの）があれば、重複を
   避けるため削除してよい（削除前に該当箇所の既存テストが引き続き通ることを確認する）
7. 今回のリファクタで解消したパターンに対応する回帰テストを追加・整理する（個別テストが既にある
   場合は重複を避けつつ、横断的な観点のテストを `tests/test_fuzz_regressions.py` 等に追加してよい）
8. `python scripts/sort_tests.py <変更したテストファイル>` を実行する
9. `python -m pytest tests/ -v` を実行し、全件パスすることを確認する（今回と無関係な既存テストが
    flaky と判明した場合は §共通13 に従いその場で修正する）
10. 該当する `.internal/progress/*.md` に変更があれば更新する
11. 変更を意味のある単位でコミットする（`{branch}` ブランチ上で行う。1コミットにまとめても、
    設計変更・削除・テスト追加等で複数コミットに分けてもよい。コミットメッセージ例:
    `refactor: {flow}/{パターンの短い説明}`）

完了したら、対応したパターン・変更ファイル一覧・追加/削除したテストを簡潔に報告すること。
```

失敗（設計が困難・テストが通らない等）した場合: 自動リトライはしない。ユーザーに状況を報告して
中断する（`{branch}` の内容は無傷のまま残す。個別の単発修正は既に §共通10 の通り完了・反映済みの
ため、失われるものはない）。

### 後処理・main への反映

横断リファクタが成功した場合、通常の「main への反映」節（§共通6、1件ごと）とは粒度が異なる
特例として扱う:

- 複数コミットになりうるため、`{branch}` から `origin/main` への反映は §共通6 の手順に従うが、
  `gh pr create` の `--fill` が不適切な場合は `--title`/`--body` を明示し、含まれるコミット一覧を
  本文に列挙する（§共通6 の注記と同じ扱い）。
- 反映は「この横断リファクタ1セット」を単位として直ちに行う（点修正のような1件=1コミット単位の
  カウンタ運用はしない）。
- 台帳（`completed_bugs` 等）には、通常のエントリに加えて
  `{"systemic_refactor": true, "pattern": "...", "summary": "...", "resolved_signatures": [...]}`
  のようなエントリを追加してよい（以降の判断基準チェックで「既に横断対応済みのパターンか」を
  確認する材料にする）。

反映後は通常のフロー処理に戻る（次のバッチ・次のキュー処理へ進む）。
