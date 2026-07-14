# リプレイ再現 継続バグ出し（replay_fuzz）ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `replay_fuzz`、方式は単一ブランチ）。
**探索・実装作業ディレクトリ**: `{worktree}`（永続 worktree、ブランチ `loop/replay_fuzz`）。

---

## フロー概要

`scripts/fuzz/replay_fuzz_battle.py` で完全ランダムな対戦をシード付きで大量に実行し、
`Battle.build_replay_data()` → `replay_battle()` によるリプレイ再現が元の対戦と
完全に一致するか（`tests/test_replay_fuzz.py` と同じ判定基準）を検証する。
既存の `fuzz` ループ（`.claude/loop/fuzz.md`）が「未捕捉例外」を検出するのに対し、
こちらは「対戦は正常終了するがリプレイが元と食い違う」というリプレイ機能固有のバグを狙う
（`--player` によるモード切替はなく、`fuzz` の random モードと同じチーム生成・行動選択のみを使う）。
バッチ内の全シードを worker プロセスに分散して並列実行し（打ち切りなし）、食い違いが複数件見つかる
こともある。バグを見つけたら `impl`（修正）→ `review-test`（回帰テスト追加・全体テスト・コミット）の
2段階で `loop/replay_fuzz` 上で自動修正する（`fuzz` ループと同じ2段階パターン）。

食い違いは6種類に分類される（`replay_fuzz_battle.py` の判定順）:

| `mismatch_kind` | 意味 |
|---|---|
| `original_exception` | 元の対戦自体が未捕捉例外で終了した（リプレイ以前の問題。`fuzz` ループと同種のバグ） |
| `replay_exception` | `build_replay_data()` / `replay_battle()` が未捕捉例外を投げた |
| `turn` | 最終ターン数が元と異なる |
| `winner` | 勝者が元と異なる |
| `hp` | いずれかのポケモンのHPが元と異なる |
| `logs` | `event_logger.logs` が元と完全一致しない |

同一原因（signature）のバグに **2回連続で自動修正が失敗**した場合はループを中断し、ユーザーに
手動確認を求める（`fuzz` ループと同じ理由: ランダムシードは無限に新しい組み合わせを生むため
「同じバグをスキップして次へ」ができない）。

---

## 状態ファイルのスキーマ

```json
{
  "worktree": "C:\\Users\\tmtmh\\Documents\\pokemon\\jpoke-loop\\replay_fuzz",
  "next_seed": 0,
  "total_battles": 0,
  "batch_size": 200,
  "workers": 4,
  "max_turns": 30,
  "n_pokemon": 3,
  "failure_dir": "replay_fuzz_failures",
  "pending_failures": [
    {"seed": 123, "signature": "...", "mismatch_kind": "...", "report_path": "..."}
  ],
  "current_failure": null,
  "completed_bugs": [{"seed": 123, "signature": "...", "summary": "..."}],
  "failed_bugs": [{"signature": "...", "attempts": 1, "last_seed": 123}]
}
```

- `next_seed` / `total_battles`: 探索済みシード範囲の管理（`fuzz` の `modes.random` と同じ意味）。
- `max_turns` / `n_pokemon`: `tests/test_replay_fuzz.py` の既定値（`MAX_TURNS=30`, `N_POKEMON=3`）を
  踏襲した既定値。値を大きくするほど1戦が高コストになる。
- `pending_failures`: 直近のバッチ実行で見つかった未処理の食い違いのキュー（`fuzz_log.md` の
  `pending_anomalies` と同じ形）。`scripts/fuzz/replay_fuzz_battle.py --search` は打ち切りをせず
  `batch_size` 件を必ず全て並列実行するため、1バッチで複数件の食い違いが同時に見つかることがある。
  1件ずつ手順4で処理し、処理し終えたらそのエントリを取り除く。
- バグ台帳（`completed_bugs` / `failed_bugs`）は `fuzz` と同じ形式（`player` フィールドは無し）。

---

## 実行手順

### 1. 状態ファイルを読む

`.loop/replay_fuzz_state.json` を Read で読み込む（存在しなければ初回起動）。

### 1.5. 未処理の current_failure / pending_failures が残っていないか確認

§共通10 の再開ルールを適用する。`current_failure` が null でない場合、手順4.3（impl）からやり直す。
`current_failure` が null で `pending_failures` が空でない場合、新規バッチは実行せず手順4.1から
キューの先頭を処理する。

### 1.6. worktree を準備する

§共通4 パターンA を適用する（`{worktree}`・ブランチ `loop/replay_fuzz`）。

### 2. バッチ探索を実行

`pending_failures` が空の場合のみ実施する。`{worktree}` に cd してから実行する（`replay_fuzz_battle.py`
はスクリプト自身のパスから `.loop/{failure_dir}/` を解決するため、worktree 内で実行するとレポートも
worktree 配下に書き込まれる）:

```bash
cd "{worktree}" && PYTHONPATH=src python scripts/fuzz/replay_fuzz_battle.py --search \
  --start-seed {next_seed} --count {batch_size} --workers {workers} \
  --max-turns {max_turns} --n-pokemon {n_pokemon}
```

`count` 件は打ち切らず必ず全件並列実行される。`--workers {workers}`（既定4）は、他の並行
セッション・ループ（review/impl 等）も同じマシンの CPU を使うため、`replay_fuzz` が全コアを
専有しないよう明示的に絞っている値（省略時のスクリプト既定は CPU数と count の小さい方）。
exit code 0 = 全件一致、exit code 1 = 食い違いあり（stdout に `FAIL: seed=... signature=...` と
`report: {絶対パス}` の組が食い違った件数分、seed 昇順で出力される）。

### 3. 統計を更新

`next_seed += batch_size`、`total_battles += batch_size`（全件並列実行するため、これで seed 範囲を
漏れなく消費したことになる）。
食い違いなしなら状態を保存して手順6へ。

食い違いありの場合、stdout の `FAIL:`/`report:` の組をすべて読み取り、`pending_failures` に
`{"seed": seed, "signature": signature, "mismatch_kind": mismatch_kind, "report_path": path}` として
seed 昇順で積む（`mismatch_kind` はレポート内の該当行から取得する）。状態を保存し、手順4.1へ進む。

### 4. バグ対応

#### 4.1 キューの先頭を取り出す

`pending_failures` の先頭を取り出す（キューからは取り除く）。以下 `{seed}` `{signature}`
`{mismatch_kind}` `{report_path}` はこのエントリの値。

レポート（`{worktree}\.loop\{failure_dir}\seed_{seed}.log`）を Read する（冒頭に `signature:`
`mismatch_kind:` `detail:` がある。stdout から取得済みなら再取得不要）。

#### 4.2 重複チェック

§共通10 の signature 重複チェックを適用する。

#### 4.3 current_failure を記録

`current_failure = {"seed": {seed}, "signature": {signature}, "mismatch_kind": {mismatch_kind}, "report_path": {report_path}}`
を保存する。

#### 4.4 impl エージェント（foreground）を起動

```
jpoke replay_fuzz バグ修正タスク: seed={seed} (signature: {signature}, mismatch_kind: {mismatch_kind})

作業ディレクトリ: {worktree}

リプレイ再現の自動検証（replay_fuzz_battle.py）が、対戦とリプレイ再現の食い違いを検出した。

再現コマンド: {report内の再現コマンド}

食い違いの詳細（両陣営のチーム構成・食い違いの種類・元の対戦ログ・リプレイ対戦ログ）:
{report_path の内容、またはパスを渡して Read させる}

手順:
1. 上記コマンドで食い違いが再現することを確認する（FAIL: が出力されること）
2. mismatch_kind に応じて調査の当たりをつける:
   - original_exception: 元の対戦自体が例外で落ちている。fuzz ループと同種のエンジンバグ
     （CLAUDE.md の実装時参照順を参照。handlers/ か core/ かを見極める）
   - replay_exception: build_replay_data()（src/jpoke/core/battle.py）または
     replay_battle()/ReplayPlayer（src/jpoke/core/replay.py）側の記録・再生ロジックのバグ
   - turn / winner / hp / logs: 記録漏れ（command_log・selection・teams のスナップショットに
     含まれない状態依存の乱数消費や外部状態）、または Pokemon.from_dict() 等の再構築時に
     元の状態を完全に復元できていないバグの可能性が高い。特に hp は
     Pokemon の hp_policy 系セッター（set_level/set_nature/set_base/set_indiv/set_effort/set_stats）の
     扱いを疑う
3. 以降は `.claude/loop/_common.md` §共通10「impl エージェントの共通ステップ」の 3〜7 に従う
   （修正 → 必要な sort スクリプト実行 → 再現コマンドで解消確認 → コミットしない）
```

impl 失敗（原因不明・修正できず） → §共通10 の失敗時ルールに従う。`failed_bugs` のエントリ形式は
`{"signature": signature, "attempts": N, "last_seed": seed}`。
`current_failure` をクリアして保存し、手順5へ（review-test はスキップ）。

#### 4.5 review-test エージェント（foreground）を起動

impl 成功後のみ実施:

```
jpoke replay_fuzz バグ修正タスク: seed={seed} (signature: {signature}) のレビュー・回帰テスト

作業ディレクトリ: {worktree}

impl エージェントが replay_fuzz（リプレイ再現検証）発見バグ（再現コマンド:
{report内の再現コマンド}）を修正した。`.claude/loop/_common.md` §共通10「review-test エージェントの
共通ステップ」に従うこと。手順2（回帰テスト追加）の補足:

- リプレイ・状態復元に関する一般的なバグは tests/test_replay.py に、
  特定の特性・技・アイテムに原因がある場合は該当カテゴリの既存テストファイルに追加する

手順6（コミット）はこのブランチ `loop/replay_fuzz` 上で行う:
   git add src/ tests/ docs/
   git commit -m "fix: replay_fuzz/seed{seed}_<バグの短い説明>"
```

review-test 成功 → §共通10 の成功時ルールに従う。`completed_bugs` のエントリ形式は
`{"seed": seed, "signature": signature, "summary": "<一言説明>"}`。
続けて「main への反映」の手順に従い、この1件をただちに main へマージする。

review-test 失敗 → 手順4.4の失敗時と同様に `failed_bugs` を更新し、`current_failure` をクリアして
保存し、手順5へ。

### 5. 次のバグへ

`pending_failures` が空でなければ手順4.1に戻って続行する。1件処理し終えた時点でターンを終えても
よい（§共通7）。`pending_failures` が空なら手順6へ。

### 6. 終了

手順4.2で中断していない場合のみ、§共通7 に従う（続きはユーザーの `/loop replay_fuzz` 再実行で
再開する）。

---

## main への反映

1件の修正が review-test で成功・コミットされるたびに、ディスパッチャーがその場で §共通6 の
手順に従い直ちに main へ反映する（`{branch}` = `loop/replay_fuzz`）。

## ループの実行間隔

`/loop replay_fuzz` の動的セルフペーシング（`ScheduleWakeup`）では、`/loop` スキルの汎用ガイド
（1200〜1800秒）ではなく **固定1分間隔（`delaySeconds=60`）** を使う（`fuzz`/`fuzz_log` と共通）。
impl / review-test エージェントは常に foreground 起動でそのターン内に完結するため、次回起動も
同様に60秒後とする。

## エラーハンドリング

- impl / review-test 失敗 → `failed_bugs` に記録してループ継続（`pending_failures` の残りがあれば続行）。
- 同一 signature が `failed_bugs` で attempts >= 2 → ループ中断（手動確認）。
- エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。
