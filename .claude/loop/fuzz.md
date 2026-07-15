# 継続的バグ出し（fuzz）ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `fuzz`、方式は単一ブランチ）。
**探索・実装作業ディレクトリ**: `{worktree}`（永続 worktree、ブランチ `loop/fuzz`）。

---

## フロー概要

`scripts/fuzz/fuzz_battle.py` で完全ランダムな6匹パーティ同士のバトルをシード付きで大量に実行し、
未捕捉例外（エンジンのバグ）を検出する。バッチ内の全シードを worker プロセスに分散して並列実行し
（打ち切りなし）、失敗が複数件見つかることもある。バグを見つけたら `impl`（修正）→ `review-test`
（回帰テスト追加・全体テスト・コミット）の2段階で `loop/fuzz` 上で自動修正する。

### 2つのプレイヤーモデル（モード）

行動選択の方策が異なる2モードを、同じスクリプト・ブランチ・worktree・バグ台帳の上で切り替えて回す
（`--player` 引数だけが振る舞いの差）。両モードは**同時には走らせない**（エンジン修正を並列にやると
共有コードで衝突するため）。`active_mode` を毎回の起動で交互に切り替えて双方の探索を進める。

| モード | Player | 特徴 | 既定 n_pokemon / max_turns / batch |
|---|---|---|---|
| `random` | RandomPlayer | 安価。広い状態空間を広く浅く掘る | 6 / 100 / 500 |
| `tree_search` | TreeSearchFuzzPlayer（1手先ミニマックス） | 高コスト。実戦的な行動でのみ出るバグを狙う | 3 / 20 / 100 |

`batch_size` は `--search` で worker プロセスに分散して並列実行される件数（打ち切りなし）。
`workers`（既定4）は他の並行セッション・ループへの配慮のため CPU コア数を使い切らないよう
明示的に抑えている値であり、`scripts/fuzz/fuzz_battle.py --search` の既定（CPU数と`batch_size`の
小さい方を自動選択）より小さい。

同一 seed でも `n_pokemon` が違えばチーム構成も軌道も別物になるため、**seed カーソル（`next_seed`）と
コストプロファイルはモードごとに保持する**（`modes` ブロック）。修正（エンジンのバグ）は Player 非依存
なので、どちらのモードで見つけた修正も同じ `loop/fuzz` に積み、バグ台帳（signature）も共通で持つ。

同一原因（signature）のバグに **2回連続で自動修正が失敗**した場合はループを中断し、ユーザーに
手動確認を求める（ランダムシードは無限に新しい組み合わせを生むため「同じバグをスキップして次へ」が
できない＝直せないバグは止まって報告する）。

---

## 状態ファイルのスキーマ

```json
{
  "active_mode": "random",
  "worktree": "C:\\Users\\tmtmh\\Documents\\pokemon\\jpoke-loop\\fuzz",
  "modes": {
    "random": {
      "player": "random",
      "max_turns": 100, "n_pokemon": 6, "batch_size": 500, "workers": 4,
      "failure_dir": "fuzz_failures",
      "next_seed": 0, "total_battles": 0
    },
    "tree_search": {
      "player": "tree_search",
      "max_turns": 20, "n_pokemon": 3, "batch_size": 100, "max_plies": 1, "workers": 4,
      "failure_dir": "tsfuzz_failures",
      "next_seed": 0, "total_battles": 0
    }
  },
  "pending_failures": [
    {"mode": "random", "seed": 123, "signature": "...", "report_path": "..."}
  ],
  "current_failure": null,
  "completed_bugs": [{"player": "random", "seed": 123, "signature": "...", "summary": "..."}],
  "failed_bugs": [{"player": "tree_search", "signature": "...", "attempts": 1, "last_seed": 123}]
}
```

- `active_mode`: 今回の起動で探索するモード（`modes` のキー）。以下 `M = modes[active_mode]` と書く。
- ポケモン1匹ごとの性別・性格・レベル・テラスタイプ・個体値・努力値・技数（1〜10個）、および
  選出数（n_selected）は seed から自動決定される（CLI 引数では渡さない＝seed だけで完全に再現できる）。
- `pending_failures`: 直近のバッチ実行で見つかった未処理の失敗のキュー（`fuzz_log.md` の
  `pending_anomalies` と同じ形）。`scripts/fuzz/fuzz_battle.py --search` は打ち切りをせず `batch_size` 件を
  必ず全て並列実行するため、1バッチで複数件の失敗が同時に見つかることがある。1件ずつ手順4で処理し、
  処理し終えたらそのエントリを取り除く。
- バグ台帳（`completed_bugs` / `failed_bugs`）は両モード共通の1リスト。各エントリに `player` を付けて
  どちらのモードで見つけたかを記録する（同一 signature の突き合わせ＝旧 tsfuzz の cross-check に使う）。

---

## 実行手順

### 1. 状態ファイルを読む

`.loop/fuzz_state.json` を Read で読み込む（存在しなければ初回起動）。
`active_mode` と `M = modes[active_mode]` を確定する。

### 1.5. 未処理の current_failure / pending_failures が残っていないか確認

§共通10 の再開ルールを適用する。`current_failure` が null でない場合、`current_failure.mode` を
`active_mode` に採用してから（そのモードで見つけた失敗なので）手順4.3（impl）からやり直す。
`current_failure` が null で `pending_failures` が空でない場合、新規バッチは実行せず手順4.1から
キューの先頭を処理する。

### 1.6. worktree を準備する

§共通4 パターンA を適用する（`{worktree}`・ブランチ `loop/fuzz`）。

### 2. バッチ探索を実行

`pending_failures` が空の場合のみ実施する。`{worktree}` に cd してから実行する（fuzz_battle.py は
スクリプト自身のパスから `.loop/{M.failure_dir}/` を解決するため、worktree 内で実行するとレポートも
worktree 配下に書き込まれる）。`--player {active_mode}` を必ず渡す。`active_mode == tree_search`
のときは `--max-plies {M.max_plies}` も付ける:

```bash
cd "{worktree}" && PYTHONPATH=src python scripts/fuzz/fuzz_battle.py --search \
  --player {active_mode} \
  --start-seed {M.next_seed} --count {M.batch_size} --workers {M.workers} \
  --max-turns {M.max_turns} --n-pokemon {M.n_pokemon}
  # tree_search の場合はさらに: --max-plies {M.max_plies}
```

`count` 件は打ち切らず必ず全件並列実行される。`--workers {M.workers}`（既定4）は、他の並行
セッション・ループ（review/impl 等）も同じマシンの CPU を使うため、`fuzz` が全コアを専有しない
よう明示的に絞っている値（省略時のスクリプト既定は CPU数と count の小さい方）。exit code 0 =
全件成功、exit code 1 = 失敗あり（stdout に `FAIL: seed=... signature=...` と
`report: {絶対パス}` の組が失敗した件数分、seed 昇順で出力される）。

### 3. 統計を更新

`M.next_seed += M.batch_size`、`M.total_battles += M.batch_size`（全件並列実行するため、
これで seed 範囲を漏れなく消費したことになる）。
失敗なしなら状態を保存して手順6へ。

失敗ありの場合、stdout の `FAIL:`/`report:` の組をすべて読み取り、`pending_failures` に
`{"mode": active_mode, "seed": seed, "signature": signature, "report_path": path}` として
seed 昇順で積む。状態を保存し、手順4.1へ進む。

### 4. バグ対応

#### 4.1 キューの先頭を取り出す

`pending_failures` の先頭を取り出す（キューからは取り除く）。以下 `{seed}` `{signature}` `{report_path}`
はこのエントリの値、`{mode}` はこのエントリの `mode`（`active_mode` と異なる場合は `{mode}` を
`active_mode` として扱い直す＝1.5 の再開時と同じ考え方）。

レポート（`{worktree}\.loop\{modes[mode].failure_dir}\seed_{seed}.log`）を Read する。1行目付近に
`signature: ...` がある（stdout から取得済みなら再取得不要）。

#### 4.2 重複チェック

§共通10 の signature 重複チェックを適用する。加えて fuzz 固有のルール:
`completed_bugs` / `failed_bugs` に同じ `signature` が **別の `player`** で存在する場合 → 両モードで踏む
**プレイヤー非依存のエンジン共通バグ**の可能性が高い。この旨を手順4.4の impl エージェントへの指示に
書き添える（重複調査の手間を減らす）。

#### 4.3 current_failure を記録

`current_failure = {"mode": {mode}, "seed": {seed}, "signature": {signature}, "report_path": {report_path}}`
を保存する。

#### 4.4 impl エージェント（foreground）を起動

```
jpoke fuzz バグ修正タスク: seed={seed} player={mode} (signature: {signature})

作業ディレクトリ: {worktree}

自動対戦テスト（fuzzer、行動選択={mode}）が未捕捉例外を検出した。

再現コマンド: {report内の再現コマンド}
（例: PYTHONPATH=src python scripts/fuzz/fuzz_battle.py --seed {seed} --player {mode} --max-turns {modes[mode].max_turns} --n-pokemon {modes[mode].n_pokemon}[ --max-plies {modes[mode].max_plies}]）

失敗レポート（両陣営のチーム構成・例外・traceback・全ターンのバトルログ）:
{report_path の内容、またはパスを渡して Read させる}

手順:
1. 上記コマンドで再現することを確認する
2. traceback とバトルログから原因箇所を特定する
   （CLAUDE.md の実装時参照順を参照。handlers/ の個別ハンドラのバグか、core/ のエンジン共通ロジックのバグかを見極める）
   ※ player=tree_search の場合、`scripts/fuzz/fuzz_battle.py` の `TreeSearchFuzzPlayer` および
     `src/jpoke/players/tree_search_player.py` の `TreeSearchPlayer`（探索フレームワーク固有）の
     バグの可能性も観点に加える。
   ※ 別 player で同一 signature が既出の場合（手順4.2）は、エンジン共通ロジックのバグである可能性が高い。
3. 以降は `.claude/loop/_common.md` §共通10「impl エージェントの共通ステップ」の 3〜7 に従う
   （修正 → 必要な sort スクリプト実行 → 再現コマンドで解消確認 → コミットしない）
```

impl 失敗（原因不明・修正できず） → §共通10 の失敗時ルールに従う。`failed_bugs` のエントリ形式は
`{"player": mode, "signature": signature, "attempts": N, "last_seed": seed}`。
`current_failure` をクリアして保存し、手順5へ（review-test はスキップ）。

#### 4.5 review-test エージェント（foreground）を起動

impl 成功後のみ実施:

```
jpoke fuzz バグ修正タスク: seed={seed} player={mode} (signature: {signature}) のレビュー・回帰テスト

作業ディレクトリ: {worktree}

impl エージェントが fuzzer（行動選択={mode}）発見バグ（再現コマンド:
{report内の再現コマンド}）を修正した。`.claude/loop/_common.md` §共通10「review-test エージェントの
共通ステップ」に従うこと。手順2（回帰テスト追加）の補足:

- tests/test_utils.py のヘルパー（start_battle・run_move・run_switch など）を使って書く
- 特定の特性・技・アイテムに原因がある場合は該当カテゴリの既存テストファイルに追加する
- 複数コンポーネントにまたがる場合・エンジン共通ロジックの汎用的なバグの場合は
  tests/test_fuzz_regressions.py に追加する（存在しなければ新規作成してよい）

手順6（コミット）はこのブランチ `loop/fuzz` 上で行う:
   git add src/ tests/ docs/
   git commit -m "fix: fuzz/{mode}/seed{seed}_<バグの短い説明>"
```

review-test 成功 → §共通10 の成功時ルールに従う。`completed_bugs` のエントリ形式は
`{"player": mode, "seed": seed, "signature": signature, "summary": "<一言説明>"}`。
続けて「main への反映」の手順に従い、この1件をただちに main へマージする。

review-test 失敗 → 手順4.4の失敗時と同様に `failed_bugs` を更新し、`current_failure` をクリアして
保存し、手順5へ。

### 5. 次のバグへ

`pending_failures` が空でなければ手順4.1に戻って続行する。1件処理し終えた時点でターンを終えても
よい（§共通7）。`pending_failures` が空なら手順6へ。

### 6. モードを切り替えて終了

手順4.2で中断していない場合のみ:

1. **モード切り替え**: `active_mode` をもう一方のモードに反転する（`random` ↔ `tree_search`）。
   両モードの探索を交互に進めるため。特定モードに集中したいときはこの反転を止めて固定する。
2. §共通7 に従う（続きはユーザーの `/loop fuzz` 再実行で再開する）。

---

## main への反映

1件の修正が review-test で成功・コミットされるたびに、ディスパッチャーがその場で §共通6 の
手順に従い直ちに main へ反映する（`{branch}` = `loop/fuzz`）。両モードの修正がここに積まれる。

## ループの実行間隔

`/loop fuzz` の動的セルフペーシング（`ScheduleWakeup`）では、`/loop` スキルの汎用ガイド
（1200〜1800秒）ではなく **固定1分間隔（`delaySeconds=60`）** を使う（`replay_fuzz`/`fuzz_log`
と共通）。impl / review-test エージェントは常に foreground 起動でそのターン内に完結するため、
次回起動も同様に60秒後とする。

## エラーハンドリング

- impl / review-test 失敗 → `failed_bugs` に記録してループ継続（`pending_failures` の残りがあれば続行）。
- 同一 signature が `failed_bugs` で attempts >= 2 → ループ中断（手動確認）。
- エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。
