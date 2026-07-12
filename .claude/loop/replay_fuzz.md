# リプレイ再現 継続バグ出し（replay_fuzz）ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `replay_fuzz`、方式は単一ブランチ）。
**探索・実装作業ディレクトリ**: `{worktree}`（永続 worktree、ブランチ `loop/replay_fuzz`）。

---

## フロー概要

`scripts/replay_fuzz_battle.py` で完全ランダムな対戦をシード付きで大量に実行し、
`Battle.build_replay_data()` → `replay_battle()` によるリプレイ再現が元の対戦と
完全に一致するか（`tests/test_replay_fuzz.py` と同じ判定基準）を検証する。
既存の `fuzz` ループ（`.claude/loop/fuzz.md`）が「未捕捉例外」を検出するのに対し、
こちらは「対戦は正常終了するがリプレイが元と食い違う」というリプレイ機能固有のバグを狙う
（`--player` によるモード切替はなく、`fuzz` の random モードと同じチーム生成・行動選択のみを使う）。
バグを見つけたら `impl`（修正）→ `review-test`（回帰テスト追加・全体テスト・コミット）の
2段階で `loop/replay_fuzz` 上で自動修正する（`fuzz` ループと同じ2段階パターン）。

食い違いは4種類に分類される（`replay_fuzz_battle.py` の判定順）:

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
  "worktree": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\replay_fuzz",
  "next_seed": 0,
  "total_battles": 0,
  "batch_size": 100,
  "max_turns": 30,
  "n_pokemon": 3,
  "failure_dir": "replay_fuzz_failures",
  "current_failure": null,
  "completed_bugs": [{"seed": 123, "signature": "...", "summary": "..."}],
  "failed_bugs": [{"signature": "...", "attempts": 1, "last_seed": 123}]
}
```

- `next_seed` / `total_battles`: 探索済みシード範囲の管理（`fuzz` の `modes.random` と同じ意味）。
- `max_turns` / `n_pokemon`: `tests/test_replay_fuzz.py` の既定値（`MAX_TURNS=30`, `N_POKEMON=3`）を
  踏襲した既定値。値を大きくするほど1戦が高コストになる。
- バグ台帳（`completed_bugs` / `failed_bugs`）は `fuzz` と同じ形式（`player` フィールドは無し）。

---

## 実行手順

### 1. 状態ファイルを読む

`.loop/replay_fuzz_state.json` を Read で読み込む（存在しなければ初回起動）。

### 1.5. 未処理の current_failure が残っていないか確認

§共通10 の再開ルールを適用する。`current_failure` が null でない場合、手順4からやり直す。

### 1.6. worktree を準備する

§共通4 パターンA を適用する（`{worktree}`・ブランチ `loop/replay_fuzz`）。

### 2. バッチ探索を実行

`{worktree}` に cd してから実行する（`replay_fuzz_battle.py` はスクリプト自身のパスから
`.loop/{failure_dir}/` を解決するため、worktree 内で実行するとレポートも worktree 配下に書き込まれる）:

```bash
cd "{worktree}" && PYTHONPATH=src python scripts/replay_fuzz_battle.py --search \
  --start-seed {next_seed} --count {batch_size} \
  --max-turns {max_turns} --n-pokemon {n_pokemon}
```

exit code 0 = 全件一致、exit code 1 = 食い違いあり（stdout に worktree 配下の絶対パスでレポートパスが
出力される。以降その絶対パスをそのまま使う）。

### 3. 統計を更新

`next_seed += batch_size`、`total_battles += batch_size`
（探索は失敗地点で打ち切られるが、シード範囲は消費済みとして前進させる）。
食い違いなしなら状態を保存して手順6へ。

### 4. バグ対応（食い違いありの場合）

#### 4.1 レポートを読んで signature を取得

手順2 stdout の `report:` パス（`{worktree}\.loop\{failure_dir}\seed_{seed}.log` 形式の絶対パス）
を Read する。冒頭に `signature:` `mismatch_kind:` `detail:` がある。

#### 4.2 重複チェック

§共通10 の signature 重複チェックを適用する。

#### 4.3 current_failure を記録

`current_failure = {"seed": {seed}, "signature": {signature}, "mismatch_kind": {mismatch_kind}, "report_path": {path}}`
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
`current_failure` をクリアして保存し、手順6へ（review-test はスキップ）。

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
保存し、手順6へ。

### 5. （手順4完了後）状態ファイルを保存

§共通7・§共通3 に従い Write で上書き（コミット不要）。

### 6. 終了

手順4.2で中断していない場合のみ、§共通7 に従う（続きはユーザーの `/loop replay_fuzz` 再実行で
再開する）。

---

## main への反映

1件の修正が review-test で成功・コミットされるたびに、ディスパッチャーがその場で §共通6 の
手順に従い直ちに main へ反映する（`{branch}` = `loop/replay_fuzz`）。

## エラーハンドリング

- impl / review-test 失敗 → `failed_bugs` に記録してループ継続。
- 同一 signature が `failed_bugs` で attempts >= 2 → ループ中断（手動確認）。
- エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。
