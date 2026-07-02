# 継続的バグ出し（fuzz）ループ 指示書

**作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`

---

## フロー概要

`scripts/fuzz_battle.py` で完全ランダムな6匹パーティ同士のバトルをシード付きで大量に実行し、
未捕捉例外（エンジンのバグ）を検出する。バグを見つけたら `impl`（修正）→ `review-test`
（回帰テスト追加・全体テスト・コミット）の2段階で自動修正する。todo.md と同じく
ブランチ／worktree は使わず、main 上で直接コミットする。

同一原因（signature）のバグに2回連続で自動修正が失敗した場合はループを中断し、
ユーザーに手動確認を求める（ランダムシードは無限に新しい組み合わせを生むため、
「同じバグをスキップして次へ」ができない＝直せないバグは止まって報告する）。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "n_selected": 3,
    "max_turns": 100,
    "n_pokemon": 6,
    "n_moves": 4,
    "batch_size": 100
  },
  "stats": {"total_battles": 0, "next_seed": 0},
  "current_failure": null,
  "completed_bugs": [{"seed": 123, "signature": "...", "summary": "..."}],
  "failed_bugs": [{"signature": "...", "attempts": 1, "last_seed": 123}]
}
```

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/fuzz_state.json` を Read で読み込む。

### 1.5. 未処理の current_failure が残っていないか確認

`current_failure` が null でない場合、前回のウェイクアップが中断された状態。
手順4（バグ対応）からやり直す。

### 2. バッチ探索を実行

```
PYTHONPATH=src python scripts/fuzz_battle.py --search \
  --start-seed {stats.next_seed} --count {config.batch_size} \
  --n-selected {config.n_selected} --max-turns {config.max_turns} \
  --n-pokemon {config.n_pokemon} --n-moves {config.n_moves}
```

exit code 0 = 全件成功、exit code 1 = 失敗あり（stdout にレポートパスが出力される）。

### 3. 統計を更新

`stats.next_seed += config.batch_size`
`stats.total_battles += config.batch_size`（探索は失敗地点で打ち切られるため、実際に
実行したバトル数は batch_size 以下だが、シード範囲は消費済みとして扱い前進させる）

失敗なしの場合はここで状態ファイルを保存し、手順6（次回ウェイクアップ予約）へ進む。

### 4. バグ対応（失敗ありの場合）

#### 4.1 レポートを読んで signature を取得

手順2の stdout に出力された `report:` のパス（`.loop/fuzz_failures/seed_{seed}.log`）を Read する。
1行目付近に `signature: ...` がある。

#### 4.2 重複チェック

`failed_bugs` に同じ `signature` が `attempts >= 2` で存在する場合:
→ **ループを中断する**（ScheduleWakeup を呼ばない）。
「同一バグ（signature: {signature}）の自動修正が2回失敗したため、fuzzループを停止しました。
再現コマンドは {report内の再現コマンド} です。手動確認が必要です。」と報告して終了。

#### 4.3 current_failure を記録

`current_failure = {"seed": {seed}, "signature": {signature}, "report_path": {path}}`
を状態ファイルに保存する。

#### 4.4 impl エージェント（foreground）を起動

```
jpoke fuzz バグ修正タスク: seed={seed} (signature: {signature})

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

ランダムバトルの自動テスト（fuzzer）が未捕捉例外を検出した。

再現コマンド: PYTHONPATH=src python scripts/fuzz_battle.py --seed {seed} --n-selected {n_selected} --max-turns {max_turns} --n-pokemon {n_pokemon} --n-moves {n_moves}

失敗レポート（両陣営のチーム構成・例外・traceback・全ターンのバトルログ）:
{report_path の内容、またはパスを渡して Read させる}

手順:
1. 上記コマンドで再現することを確認する
2. traceback とバトルログから原因箇所を特定する
   （CLAUDE.md の実装時参照順を参照。handlers/ の個別ハンドラのバグか、core/ のエンジン共通ロジックのバグかを見極める）
3. 原因を修正する（テストは書かない。review-test エージェントが担当）
4. handlers/ を変更した場合、python scripts/sort_handlers.py src/jpoke/handlers/<category>.py を実行する
5. data/ability.py・data/item.py・data/move.py を変更した場合、対応する sort スクリプトを実行する
6. 再度 PYTHONPATH=src python scripts/fuzz_battle.py --seed {seed} ... を実行し、
   例外が発生しなくなったこと（`OK:` が出力されること）を確認する
7. コミットはしない（review-test エージェントが担当）
```

impl 失敗（原因不明・修正できず） →
`failed_bugs` の該当 signature を探し、あれば `attempts += 1`、なければ
`{"signature": signature, "attempts": 1, "last_seed": seed}` を追加。
`current_failure` をクリアして保存し、手順6へ（review-test はスキップ）。

#### 4.5 review-test エージェント（foreground）を起動

impl 成功後のみ実施:

```
jpoke fuzz バグ修正タスク: seed={seed} (signature: {signature}) のレビュー・回帰テスト

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

impl エージェントが fuzzer 発見バグ（再現コマンド:
PYTHONPATH=src python scripts/fuzz_battle.py --seed {seed} --n-selected {n_selected} --max-turns {max_turns} --n-pokemon {n_pokemon} --n-moves {n_moves}
）を修正した。以下を順に実施すること:

1. 修正内容をレビューする（{report_path} に元の例外・原因箇所の情報がある）
2. 原因箇所に応じた最小の決定的な回帰テストを tests/test_utils.py のヘルパー
   （start_battle・run_move・run_switch など）を使って書く。
   ランダムなfuzzシードをそのままテストにしない（乱数依存でエンジン変更のたびに壊れるため）。
   特定の特性・技・アイテムに原因がある場合は該当カテゴリの既存テストファイルに追加する。
   複数コンポーネントにまたがる場合・エンジン共通ロジックの汎用的なバグの場合は
   tests/test_fuzz_regressions.py に追加する（存在しなければ新規作成してよい）。
3. python scripts/sort_tests.py <対象ファイル> を実行する
4. python scripts/generate_test_list.py を実行する
5. python -m pytest tests/ -v を実行し、全件パスすることを確認する
6. 変更をコミットする:
   git add src/ tests/ docs/
   git commit -m "fix: fuzz/seed{seed}_<バグの短い説明>"
```

review-test 成功 →
`completed_bugs` に `{"seed": seed, "signature": signature, "summary": "<一言説明>"}` を追加。
`failed_bugs` に同じ signature があれば削除する。
`current_failure` をクリアして保存し、手順6へ。

review-test 失敗 → 手順4.4の失敗時と同様に `failed_bugs` を更新し、`current_failure` をクリアして
保存し、手順6へ。

### 5. （手順4完了後）状態ファイルを保存

Write ツールで `.loop/fuzz_state.json` を上書き。

### 6. 次のウェイクアップを予約

手順4.2で中断していなければ:

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="fuzzループ: 次バッチへ（次シード {stats.next_seed}）")
```

---

## エラーハンドリング

- impl / review-test 失敗 → `failed_bugs` に記録してループ継続
- 同一 signature が `failed_bugs` で attempts >= 2 → ループ中断（手動確認）
