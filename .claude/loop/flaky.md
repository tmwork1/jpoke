# flaky test 検出・修正 自律ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `flaky`、方式は単一ブランチ）。
**作業ディレクトリ**: `{worktree}`（永続 worktree、ブランチ `loop/flaky`）。

---

## フロー概要

全テスト（`tests/`）を繰り返し実行し、間欠的に失敗する flaky test を検出する。本プロジェクトの
テストは `battle.random.random` 等を差し替えて乱数を確定させる設計のため、原則としてテスト結果は
毎回同一のはず（`tests/test_utils.py` 参照）。それでも間欠的に失敗するテストがあれば、
モック漏れ・テスト間の状態汚染・実行順依存など何らかのバグのサインである。

検出したら単体再実行で再現性を確認したうえで `impl`（原因調査・修正）→ `review-test`
（再現確認・回帰確認・コミット）の2段階で `loop/flaky` 上で自動修正する。

## 「flaky」と「常に失敗」の区別

隔離再実行（後述 手順4.1）で:

- **一部だけ失敗**（0 < 失敗回数 < 実行回数）→ flaky 確定。手順4.3 以降で修正する。
- **毎回失敗**（失敗回数 = 実行回数）→ flaky ではなく、現時点のコードに存在する通常の
  デグレ／既存バグ。このフローの対象外なのでループを中断し、ユーザーに報告する
  （黙って「修正」すると本来レビューが必要な仕様変更を握りつぶしかねないため）。
- **一度も再現しない**（フルスイート実行では失敗したが、隔離再実行・追加のフルスイート再実行でも
  再現しない）→ 環境要因等の可能性があるノイズとして `unreproduced` に記録し、次へ進む。

---

## 状態ファイルのスキーマ

```json
{
  "worktree": "{ROOTの親}\\jpoke-loop\\flaky",
  "batch_size": 100,
  "isolate_reruns": 100,
  "extra_fullsuite_reruns": 5,
  "verify_reruns": 100,
  "total_runs": 0,
  "current_investigation": null,
  "pending_investigation": [],
  "completed": [{"test_id": "tests/.../test_x.py::test_y", "summary": "..."}],
  "failed": [{"test_id": "...", "attempts": 1, "note": "..."}],
  "unreproduced": [{"test_id": "...", "seen_at_run": 12, "log_path": "..."}]
}
```

`{ROOTの親}` は `$ROOT`（プロジェクトルート、§共通1 参照）の親ディレクトリ。初回状態ファイル
作成時に実際の絶対パスへ置き換える（他端末の具体例をそのままコピーしない）。

- `total_runs`: これまでに完走したフルスイート実行の累計回数（バッチをまたいで単調増加）。
- `current_investigation`: `{"test_id", "stage", "log_path"}`。`stage` は
  `"isolating"`（隔離再現チェック中）/ `"fixing"`（impl 待ち）/ `"verifying"`（review-test 待ち）。
- `pending_investigation`: 同一バッチ内で複数テストが失敗した場合、先頭以外をここに積む
  （`test_id` の配列）。

---

## 実行手順

### 1. 状態ファイルを読む

`.loop/flaky_state.json` を Read で読み込む（存在しなければ上記スキーマの初期値
`batch_size=100, isolate_reruns=100, extra_fullsuite_reruns=5, verify_reruns=100, total_runs=0` で
新規作成）。

### 1.5. 中断していた調査が残っていないか確認

`current_investigation` が null でない場合、`stage` に応じて手順4.1（`isolating`）/ 4.3（`fixing`）/
4.4（`verifying`）からやり直す。

### 1.6. worktree を準備する

§共通4 パターンA を適用する（`{worktree}`・ブランチ `loop/flaky`）。

### 1.7. 他フローからのハンドオフを取り込む

`$ROOT\.loop\flaky_found.md`（§共通13 の手順5で他フローが書き込む、無ければスキップ）を確認する。
存在すれば各エントリ（`{test_id, 発見日時, 発見元フロー, 症状}`）について:

- `completed` / `failed`（attempts >= 2）に同じ test_id が既にあればスキップ（対応済み・調査済み）。
- それ以外は test_id を `pending_investigation` に追加する（`current_investigation` が null かつ
  重複しない場合のみ追加。症状メモは手順4.2 の impl エージェントへの依頼文に含める）。

取り込んだら `flaky_found.md` を空にする（§共通9 のガード付き rm、またはWrite で空文字列に上書き）。

### 2. バッチ実行

`{worktree}` に cd してから、フルスイートを `batch_size` 回連続実行する。1回でも失敗したら
その時点で打ち切る:

```bash
cd "{worktree}"
mkdir -p .loop/flaky_runs
n=0
for i in $(seq 1 {batch_size}); do
  n=$((total_runs + i))
  PYTHONPATH=src python -m pytest tests/ -q > ".loop/flaky_runs/run_$n.log" 2>&1
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "FAILED at run $n"
    break
  fi
done
echo "ran_count=$i rc=$rc"
```

`total_runs += {ran_count}`（打ち切りも含め実際に完走した回数分。失敗した回も1回として数える）。

### 3. 全件成功の場合

状態を保存して §共通7 に従い終了する（「{ran_count}回連続でflaky test無し（累計{total_runs}回）」
と報告）。

### 4. 失敗検出時

`.loop/flaky_runs/run_{n}.log` の `FAILED tests/...` 行（`short test summary info` セクション）から
失敗した test node id を全て抽出する。先頭1件を今回の調査対象にし、残りがあれば
`pending_investigation` に積む。

`failed` に同じ test_id が **attempts >= 2** で既に存在する場合 → 今回は調査せず
`pending_investigation` の次（無ければ手順6）に進む（§共通8 相当。無限ループ防止）。

`current_investigation = {"test_id": ..., "stage": "isolating", "log_path": ".loop/flaky_runs/run_{n}.log"}`
を保存する。

#### 4.1 隔離再現チェック

対象 test_id を単体で `isolate_reruns` 回連続実行し、成功/失敗の内訳を記録する:

```bash
cd "{worktree}"
pass=0; fail=0
for i in $(seq 1 {isolate_reruns}); do
  PYTHONPATH=src python -m pytest "{test_id}" -q > ".loop/flaky_runs/isolate_${i}.log" 2>&1
  if [ $? -eq 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); fi
done
echo "pass=$pass fail=$fail"
```

- `fail == 0`（毎回成功）→ 単体では再現しない。フルスイートを追加で `extra_fullsuite_reruns` 回
  連続実行し（手順2と同じ形式でログを `.loop/flaky_runs/` に追記）、いずれかで同じ test_id が
  再び FAILED に含まれるか確認する。
  - 含まれない → `unreproduced` に `{"test_id", "seen_at_run": n, "log_path"}` を追加。
    `current_investigation` をクリアして保存し、手順5へ。
  - 含まれる → flaky 確定として手順4.2へ。
- `fail == isolate_reruns`（毎回失敗）→ 「flaky ではなく常に失敗する」ケース。このフローの対象外
  なので、`failed` の該当 test_id エントリを探し、あれば `attempts += 1`、なければ
  `{"test_id": ..., "attempts": 1, "note": "隔離再実行{isolate_reruns}/{isolate_reruns}回失敗、
  flakyではなく既存のデグレ／バグの可能性あり。手動確認が必要"}` を新規追加する。
  `current_investigation` をクリアして保存し、**ループは中断せず**手順5（次の調査対象へ）に進む。
  「{test_id} は毎回失敗するため flaky 調査対象外として `failed` に記録し、次へ進みました。
  手動確認をお願いします。」とその場でユーザーに報告する（黙って握りつぶさない）。同じ test_id が
  後日の全体テストで再検出された場合も、手順4冒頭の重複チェック（`attempts >= 2` でスキップ）が
  同様に効く。
- `0 < fail < isolate_reruns` → flaky 確定。手順4.2へ。

#### 4.2 impl エージェント（foreground）を起動

```
jpoke flaky test 調査・修正タスク: {test_id}

作業ディレクトリ: {worktree}

{test_id} が全体テスト実行中に間欠的に失敗することを検出した
（隔離再実行 {fail}/{isolate_reruns} 回失敗）。

失敗ログ: {手順2または4.1で採取したログの内容、またはパスを渡してReadさせる}

手順:
1. 上記 test_id を単体で複数回実行し、失敗が再現することを確認する
   （PYTHONPATH=src python -m pytest "{test_id}" -q を数回繰り返す。
   間欠的なので1回で再現しなくてもよい）
2. 原因を調査する。よくある観点:
   - テスト側の乱数モック漏れ（battle.random.random の差し替え忘れ、一部分岐だけ未モック）
   - テスト間の状態共有・汚染（モジュール/クラスレベルの可変状態、キャッシュ、
     使い回されているインスタンス）
   - dict/set の反復順序に依存したロジック
   - 浮動小数点比較の誤差
   - 実行順序依存（他テストの副作用が残っている）
3. 原因箇所を特定し、最小の修正を行う:
   - テスト側の不備（モック漏れ・フィクスチャの状態リセット漏れ）が原因ならテストを直接修正してよい
   - 本体コード（handlers/ 等）側に非決定性があるならソースを修正する
     （CLAUDE.md の実装ルールに従う）
4. handlers/ を変更した場合、python scripts/sort_handlers.py src/jpoke/handlers/<category>.py を実行する
5. data/ability.py・data/item.py・data/move.py を変更した場合、対応する
   scripts/sort_data/sort_*.py を実行する
6. 修正後、{test_id} を単体で {isolate_reruns} 回連続実行し、全て成功することを確認する
7. コミットはしない（review-test エージェントが担当）
```

`current_investigation.stage = "fixing"` に更新して保存する。

impl 失敗（原因不明・再現しない・修正できず）: `failed` の該当 test_id エントリを探し、あれば
`attempts += 1`、なければ `{"test_id": ..., "attempts": 1, "note": "..."}` を新規追加する。
`current_investigation` をクリアして保存し、手順5へ（review-test はスキップ）。

#### 4.3 review-test エージェント（foreground）を起動

impl 成功後のみ実施:

```
jpoke flaky test 修正タスク: {test_id} のレビュー・回帰確認

作業ディレクトリ: {worktree}

impl エージェントが間欠的に失敗していたテスト {test_id} を修正した。

手順:
1. 修正内容をレビューする（原因箇所の特定と修正方法が妥当か）
2. {test_id} を単体で {verify_reruns} 回連続実行し、全て成功することを確認する
   （PYTHONPATH=src python -m pytest "{test_id}" -q を {verify_reruns} 回繰り返す）
3. python -m pytest tests/ -v を実行し、全体テストが通ることを確認する（デグレ確認）
4. テストファイルを変更した場合、python scripts/sort_tests.py <変更したテストファイル> を実行する
5. テスト一覧に変更があれば python scripts/generate_test_list.py を実行する
6. 変更をすべてコミットする（作業は `loop/flaky` ブランチ上で行う）:
   git add -A
   git commit -m "fix: flaky/{test_id を短く表した説明}"
```

`current_investigation.stage = "verifying"` に更新して保存する。

review-test 成功 → `completed` に `{"test_id": ..., "summary": "<一言説明>"}` を追加。`failed` に
同じ test_id があれば削除する。**続けて「main への反映」の手順に従い、この1件をただちに main へ
マージする**（flaky test は他の CI すべてに影響するため特に重要）。
review-test 失敗 → 4.2 の失敗時と同様に `failed` を更新する（この場合は main への反映を行わない）。

いずれも `current_investigation` をクリアして保存し、手順5へ。

### 5. 次の調査対象へ

`pending_investigation` が空でなければ先頭を取り出して `current_investigation` にセットし、
手順4.1 から繰り返す。1件処理し終えた時点でターンを終えてもよい（§共通7）。
`pending_investigation` が空なら手順6へ。

### 6. 状態保存・終了

§共通7 に従う（続きはユーザーの `/loop flaky` 再実行、または background エージェントの完了通知で
再開する）。

---

## main への反映

**flaky test は他の CI すべてに影響するため特に重要。1件の修正が review-test で成功・コミット
されるたびに、ディスパッチャーがその場で §共通6 の手順（PR経由）に従い即座に main へ反映する**
（`{branch}` = `loop/flaky`）。

`gh pr merge` が失敗した場合（コンフリクト・ブランチ保護等）は §共通6 の通り自動解決せず、PR を
open のままユーザーに報告してこの手順を止める。この場合でも `loop/flaky` 側のコミット自体は
失われないので、ループは通常どおり次の調査対象へ進めてよい。

## エラーハンドリング

§共通8 に従う（impl / review-test 失敗 → `failed` に記録してループ継続。同一 test_id が
`failed` で attempts >= 2 → スキップ）。
隔離再現チェックで「毎回失敗」（4.1）が出た場合 → ループを中断してユーザーに報告する
（flaky ではなく既存バグの可能性があるため、自動修正の対象外）。
エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。
