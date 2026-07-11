# 継続的バグ出し（fuzz）ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `fuzz`、方式は単一ブランチ）。
**探索・実装作業ディレクトリ**: `{worktree}`（永続 worktree、ブランチ `loop/fuzz`）。

---

## フロー概要

`scripts/fuzz_battle.py` で完全ランダムな6匹パーティ同士のバトルをシード付きで大量に実行し、
未捕捉例外（エンジンのバグ）を検出する。バグを見つけたら `impl`（修正）→ `review-test`
（回帰テスト追加・全体テスト・コミット）の2段階で `loop/fuzz` 上で自動修正する。

### 2つのプレイヤーモデル（モード）

行動選択の方策が異なる2モードを、同じスクリプト・ブランチ・worktree・バグ台帳の上で切り替えて回す
（`--player` 引数だけが振る舞いの差）。両モードは**同時には走らせない**（エンジン修正を並列にやると
共有コードで衝突するため）。`active_mode` を毎回の起動で交互に切り替えて双方の探索を進める。

| モード | Player | 特徴 | 既定 n_pokemon / max_turns / batch |
|---|---|---|---|
| `random` | RandomPlayer | 安価。広い状態空間を広く浅く掘る | 6 / 100 / 100 |
| `tree_search` | TreeSearchFuzzPlayer（1手先ミニマックス） | 高コスト。実戦的な行動でのみ出るバグを狙う | 3 / 20 / 20 |

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
  "worktree": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\fuzz",
  "modes": {
    "random": {
      "player": "random",
      "max_turns": 100, "n_pokemon": 6, "batch_size": 100,
      "failure_dir": "fuzz_failures",
      "next_seed": 0, "total_battles": 0
    },
    "tree_search": {
      "player": "tree_search",
      "max_turns": 20, "n_pokemon": 3, "batch_size": 20, "max_plies": 1,
      "failure_dir": "tsfuzz_failures",
      "next_seed": 0, "total_battles": 0
    }
  },
  "current_failure": null,
  "completed_bugs": [{"player": "random", "seed": 123, "signature": "...", "summary": "..."}],
  "failed_bugs": [{"player": "tree_search", "signature": "...", "attempts": 1, "last_seed": 123}]
}
```

- `active_mode`: 今回の起動で探索するモード（`modes` のキー）。以下 `M = modes[active_mode]` と書く。
- ポケモン1匹ごとの性別・性格・レベル・テラスタイプ・個体値・努力値・技数（1〜10個）、および
  選出数（n_selected）は seed から自動決定される（CLI 引数では渡さない＝seed だけで完全に再現できる）。
- バグ台帳（`completed_bugs` / `failed_bugs`）は両モード共通の1リスト。各エントリに `player` を付けて
  どちらのモードで見つけたかを記録する（同一 signature の突き合わせ＝旧 tsfuzz の cross-check に使う）。

---

## 実行手順

### 1. 状態ファイルを読む

`.loop/fuzz_state.json` を Read で読み込む（存在しなければ初回起動）。
`active_mode` と `M = modes[active_mode]` を確定する。

### 1.5. 未処理の current_failure が残っていないか確認

§共通10 の再開ルールを適用する。`current_failure` が null でない場合、`current_failure.mode` を
`active_mode` に採用してから（そのモードで見つけた失敗なので）手順4からやり直す。

### 1.6. worktree を準備する

§共通4 パターンA を適用する（`{worktree}`・ブランチ `loop/fuzz`）。

### 2. バッチ探索を実行

`{worktree}` に cd してから実行する（fuzz_battle.py はスクリプト自身のパスから
`.loop/{M.failure_dir}/` を解決するため、worktree 内で実行するとレポートも worktree 配下に書き込まれる）。
`--player {active_mode}` を必ず渡す。`active_mode == tree_search` のときは `--max-plies {M.max_plies}` も付ける:

```bash
cd "{worktree}" && PYTHONPATH=src python scripts/fuzz_battle.py --search \
  --player {active_mode} \
  --start-seed {M.next_seed} --count {M.batch_size} \
  --max-turns {M.max_turns} --n-pokemon {M.n_pokemon}
  # tree_search の場合はさらに: --max-plies {M.max_plies}
```

exit code 0 = 全件成功、exit code 1 = 失敗あり（stdout に worktree 配下の絶対パスでレポートパスが
出力される。以降その絶対パスをそのまま使う）。

### 3. 統計を更新

`M.next_seed += M.batch_size`、`M.total_battles += M.batch_size`
（探索は失敗地点で打ち切られるが、シード範囲は消費済みとして前進させる）。
失敗なしなら状態を保存して手順6へ。

### 4. バグ対応（失敗ありの場合）

#### 4.1 レポートを読んで signature を取得

手順2 stdout の `report:` パス（`{worktree}\.loop\{M.failure_dir}\seed_{seed}.log` 形式の絶対パス）
を Read する。1行目付近に `signature: ...` がある。

#### 4.2 重複チェック

§共通10 の signature 重複チェックを適用する。加えて fuzz 固有のルール:
`completed_bugs` / `failed_bugs` に同じ `signature` が **別の `player`** で存在する場合 → 両モードで踏む
**プレイヤー非依存のエンジン共通バグ**の可能性が高い。この旨を手順4.4の impl エージェントへの指示に
書き添える（重複調査の手間を減らす）。

#### 4.3 current_failure を記録

`current_failure = {"mode": {active_mode}, "seed": {seed}, "signature": {signature}, "report_path": {path}}`
を保存する。

#### 4.4 impl エージェント（foreground）を起動

```
jpoke fuzz バグ修正タスク: seed={seed} player={active_mode} (signature: {signature})

作業ディレクトリ: {worktree}

自動対戦テスト（fuzzer、行動選択={active_mode}）が未捕捉例外を検出した。

再現コマンド: {report内の再現コマンド}
（例: PYTHONPATH=src python scripts/fuzz_battle.py --seed {seed} --player {active_mode} --max-turns {M.max_turns} --n-pokemon {M.n_pokemon}[ --max-plies {M.max_plies}]）

失敗レポート（両陣営のチーム構成・例外・traceback・全ターンのバトルログ）:
{report_path の内容、またはパスを渡して Read させる}

手順:
1. 上記コマンドで再現することを確認する
2. traceback とバトルログから原因箇所を特定する
   （CLAUDE.md の実装時参照順を参照。handlers/ の個別ハンドラのバグか、core/ のエンジン共通ロジックのバグかを見極める）
   ※ player=tree_search の場合、scripts/tree_search/framework.py 側（探索フレームワーク固有）の
     バグの可能性も観点に加える。
   ※ 別 player で同一 signature が既出の場合（手順4.2）は、エンジン共通ロジックのバグである可能性が高い。
3. 以降は `.claude/loop/_common.md` §共通10「impl エージェントの共通ステップ」の 3〜7 に従う
   （修正 → 必要な sort スクリプト実行 → 再現コマンドで解消確認 → コミットしない）
```

impl 失敗（原因不明・修正できず） → §共通10 の失敗時ルールに従う。`failed_bugs` のエントリ形式は
`{"player": active_mode, "signature": signature, "attempts": N, "last_seed": seed}`。
`current_failure` をクリアして保存し、手順6へ（review-test はスキップ）。

#### 4.5 review-test エージェント（foreground）を起動

impl 成功後のみ実施:

```
jpoke fuzz バグ修正タスク: seed={seed} player={active_mode} (signature: {signature}) のレビュー・回帰テスト

作業ディレクトリ: {worktree}

impl エージェントが fuzzer（行動選択={active_mode}）発見バグ（再現コマンド:
{report内の再現コマンド}）を修正した。`.claude/loop/_common.md` §共通10「review-test エージェントの
共通ステップ」に従うこと。手順2（回帰テスト追加）の補足:

- tests/test_utils.py のヘルパー（start_battle・run_move・run_switch など）を使って書く
- 特定の特性・技・アイテムに原因がある場合は該当カテゴリの既存テストファイルに追加する
- 複数コンポーネントにまたがる場合・エンジン共通ロジックの汎用的なバグの場合は
  tests/test_fuzz_regressions.py に追加する（存在しなければ新規作成してよい）

手順6（コミット）はこのブランチ `loop/fuzz` 上で行う:
   git add src/ tests/ docs/
   git commit -m "fix: fuzz/{active_mode}/seed{seed}_<バグの短い説明>"
```

review-test 成功 → §共通10 の成功時ルールに従う。`completed_bugs` のエントリ形式は
`{"player": active_mode, "seed": seed, "signature": signature, "summary": "<一言説明>"}`。

review-test 失敗 → 手順4.4の失敗時と同様に `failed_bugs` を更新し、`current_failure` をクリアして
保存し、手順6へ。

### 5. （手順4完了後）状態ファイルを保存

§共通7・§共通3 に従い Write で上書き（コミット不要）。

### 6. モードを切り替えて終了

手順4.2で中断していない場合のみ:

1. **モード切り替え**: `active_mode` をもう一方のモードに反転する（`random` ↔ `tree_search`）。
   両モードの探索を交互に進めるため。特定モードに集中したいときはこの反転を止めて固定する。
2. §共通7 に従う（続きはユーザーの `/loop fuzz` 再実行で再開する）。

---

## main への反映

§共通6 を適用する（`{branch}` = `loop/fuzz`）。両モードの修正がここに積まれる。

## エラーハンドリング

- impl / review-test 失敗 → `failed_bugs` に記録してループ継続。
- 同一 signature が `failed_bugs` で attempts >= 2 → ループ中断（手動確認）。
- エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。
