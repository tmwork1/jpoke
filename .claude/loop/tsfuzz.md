# 継続的バグ出し（tsfuzz）ループ 指示書

**作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`

---

## フロー概要

`scripts/tsfuzz_battle.py` で完全ランダムなパーティ同士を、行動選択に
`TreeSearchPlayer`（1手先の総当たりミニマックス、`scripts/tree_search/framework.py`）
を使わせてシード付きで大量に対戦させ、未捕捉例外（エンジンのバグ）を検出する。
`fuzz`（`RandomPlayer` 版、`.claude/loop/fuzz.md`）の派生形で、進行フローは同一。
バグを見つけたら `impl`（修正）→ `review-test`（回帰テスト追加・全体テスト・コミット）
の2段階で自動修正する。todo.md と同じくブランチ／worktree は使わず、main 上で
直接コミットする。

同一原因（signature）のバグに2回連続で自動修正が失敗した場合はループを中断し、
ユーザーに手動確認を求める（ランダムシードは無限に新しい組み合わせを生むため、
「同じバグをスキップして次へ」ができない＝直せないバグは止まって報告する）。

木探索は1ターンあたり `len(自分の合法手) * len(相手の合法手)` 回だけ盤面を複製して
評価するため、`fuzz` より1バトルあたりのコストが大きい。そのため
`config.n_pokemon` / `config.max_turns` / `config.batch_size` は `fuzz` より
小さい値にしてある。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "max_turns": 20,
    "n_pokemon": 3,
    "max_plies": 1,
    "batch_size": 20
  },
  "stats": {"total_battles": 0, "next_seed": 0},
  "current_failure": null,
  "completed_bugs": [{"seed": 123, "signature": "...", "summary": "..."}],
  "failed_bugs": [{"signature": "...", "attempts": 1, "last_seed": 123}]
}
```

ポケモン1匹ごとの性別・性格・レベル・テラスタイプ・個体値・努力値・技数（1〜10個）、
および選出数（n_selected、1〜n_pokemon）は `scripts/fuzz_common.py` 内で seed から
自動的にランダム決定される（CLI 引数では渡さない＝seed だけで完全に再現できる）。

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/tsfuzz_state.json` を Read で読み込む。

### 1.5. 未処理の current_failure が残っていないか確認

`current_failure` が null でない場合、前回のウェイクアップが中断された状態。
手順4（バグ対応）からやり直す。

### 2. バッチ探索を実行

```
PYTHONPATH=src python scripts/tsfuzz_battle.py --search \
  --start-seed {stats.next_seed} --count {config.batch_size} \
  --max-turns {config.max_turns} --n-pokemon {config.n_pokemon} \
  --max-plies {config.max_plies}
```

exit code 0 = 全件成功、exit code 1 = 失敗あり（stdout にレポートパスが出力される）。

### 3. 統計を更新

`stats.next_seed += config.batch_size`
`stats.total_battles += config.batch_size`（探索は失敗地点で打ち切られるため、実際に
実行したバトル数は batch_size 以下だが、シード範囲は消費済みとして扱い前進させる）

失敗なしの場合はここで状態ファイルを保存し、手順6（次回ウェイクアップ予約）へ進む。

### 4. バグ対応（失敗ありの場合）

#### 4.1 レポートを読んで signature を取得

手順2の stdout に出力された `report:` のパス（`.loop/tsfuzz_failures/seed_{seed}.log`）を Read する。
1行目付近に `signature: ...` がある。

#### 4.2 重複チェック

`failed_bugs` に同じ `signature` が `attempts >= 2` で存在する場合:
→ **ループを中断する**（ScheduleWakeup を呼ばない）。
「同一バグ（signature: {signature}）の自動修正が2回失敗したため、tsfuzzループを停止しました。
再現コマンドは {report内の再現コマンド} です。手動確認が必要です。」と報告して終了。

同じ signature が `fuzz` ループ側の `failed_bugs` / `completed_bugs`（`.loop/fuzz_state.json`）に
既にある場合は、原因箇所が `RandomPlayer`/`TreeSearchPlayer` どちらでも共通のエンジンバグである
可能性が高い旨を impl エージェントへの指示に書き添える（重複調査の手間を減らすため）。

#### 4.3 current_failure を記録

`current_failure = {"seed": {seed}, "signature": {signature}, "report_path": {path}}`
を状態ファイルに保存する。

#### 4.4 impl エージェント（foreground）を起動

```
jpoke tsfuzz バグ修正タスク: seed={seed} (signature: {signature})

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

木探索プレイヤー（TreeSearchPlayer）による自動対戦テスト（tsfuzz）が未捕捉例外を検出した。

再現コマンド: PYTHONPATH=src python scripts/tsfuzz_battle.py --seed {seed} --max-turns {max_turns} --n-pokemon {n_pokemon} --max-plies {max_plies}

失敗レポート（両陣営のチーム構成・例外・traceback・全ターンのバトルログ）:
{report_path の内容、またはパスを渡して Read させる}

手順:
1. 上記コマンドで再現することを確認する
2. traceback とバトルログから原因箇所を特定する
   （CLAUDE.md の実装時参照順を参照。handlers/ の個別ハンドラのバグか、core/ のエンジン共通ロジックのバグか、
   scripts/tree_search/framework.py 側（探索フレームワーク固有）のバグかを見極める）
3. 原因を修正する（テストは書かない。review-test エージェントが担当）
4. handlers/ を変更した場合、python scripts/sort_handlers.py src/jpoke/handlers/<category>.py を実行する
5. data/ability.py・data/item.py・data/move.py を変更した場合、対応する sort スクリプトを実行する
6. 再度 PYTHONPATH=src python scripts/tsfuzz_battle.py --seed {seed} ... を実行し、
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
jpoke tsfuzz バグ修正タスク: seed={seed} (signature: {signature}) のレビュー・回帰テスト

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

impl エージェントが tsfuzz（木探索プレイヤーによる自動対戦テスト）発見バグ（再現コマンド:
PYTHONPATH=src python scripts/tsfuzz_battle.py --seed {seed} --max-turns {max_turns} --n-pokemon {n_pokemon} --max-plies {max_plies}
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
   git add src/ tests/ docs/ scripts/
   git commit -m "fix: tsfuzz/seed{seed}_<バグの短い説明>"
```

review-test 成功 →
`completed_bugs` に `{"seed": seed, "signature": signature, "summary": "<一言説明>"}` を追加。
`failed_bugs` に同じ signature があれば削除する。
`current_failure` をクリアして保存し、手順6へ。

review-test 失敗 → 手順4.4の失敗時と同様に `failed_bugs` を更新し、`current_failure` をクリアして
保存し、手順6へ。

### 5. （手順4完了後）状態ファイルを保存

Write ツールで `.loop/tsfuzz_state.json` を上書き。

### 6. 次のウェイクアップを予約

手順4.2で中断していなければ:

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="tsfuzzループ: 次バッチへ（次シード {stats.next_seed}）")
```

---

## エラーハンドリング

- impl / review-test 失敗 → `failed_bugs` に記録してループ継続
- 同一 signature が `failed_bugs` で attempts >= 2 → ループ中断（手動確認）
