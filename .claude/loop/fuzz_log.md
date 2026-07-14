# イベントログ整合性チェック（fuzz_log）ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `fuzz_log`、方式は単一ブランチ）。
**探索・実装作業ディレクトリ**: `{worktree}`（永続 worktree、ブランチ `loop/fuzz_log`）。

---

## フロー概要

`scripts/fuzz_log_battle.py` で完全ランダムな対戦を1バッチ10件実行し、成否を問わず
全ターン分のイベントログをレポートファイルに書き出す。既存の `fuzz` ループ（未捕捉例外を検出）・
`replay_fuzz` ループ（リプレイ再現の食い違いを検出）がいずれもスクリプトで機械的に判定できる
バグを狙うのに対し、こちらは「例外は起きないがログの記述内容がおかしい」という、
機械的な正解が定義しづらい種類のバグを LLM sub agent にログを読ませて検出する。

1バッチ10件のログそれぞれを **Explore エージェント（読み取り専用・並列10体）** に読ませ、
**整合性の観点のみ**（推奨判定基準。可読性・情報の親切さといった主観的な観点は対象外）で
異常の有無を報告させる。整合性とは、たとえば:

- HP・ランク変化等の数値変化が、実際にログに表れている前後の状態と食い違う
  （例: `HP -45 (0/45)` の直後に別のダメージログが続くのに HP が変わっていない等の矛盾）
- ログに登場するポケモン名・プレイヤー名が誤っている（別個体・別プレイヤーの名前になっている）
- ターン番号や行動順が明らかに矛盾している（同ターン内で退場したはずの個体が行動している等）

10件分の Explore エージェントの報告を **ディスパッチャー自身（このループの実行主体）** が確認し、
真のバグと判断したものだけを `impl`（原因特定・修正）→ `review-test`（回帰テスト追加・全体テスト・
コミット）の2段階で `loop/fuzz_log` 上で自動修正する（`fuzz`/`replay_fuzz` と同じ2段階パターン）。
Explore エージェントの指摘は誤検知（既存仕様通りの挙動・ログ表現の揺れ等）を含みうるため、
ディスパッチャーは指摘をそのまま鵜呑みにせず、関連する `docs/spec/` や実装コードを見て
裏取りしてから impl に回すかどうかを判断する。

同一原因（signature）のバグに **2回連続で自動修正が失敗**した場合はループを中断し、ユーザーに
手動確認を求める（`fuzz`/`replay_fuzz` と同じ理由）。ただし本フローは signature が
「バトルレポート作成時点」ではなく「impl による原因特定後」にしか判明しない点が他フローと異なる
（詳細は手順4.3参照）。

---

## 状態ファイルのスキーマ

```json
{
  "worktree": "C:\\Users\\tmtmh\\Documents\\pokemon\\jpoke-loop\\fuzz_log",
  "next_seed": 0,
  "total_battles": 0,
  "batch_size": 10,
  "workers": 1,
  "max_turns": 20,
  "n_pokemon": 3,
  "report_dir": "fuzz_log_reports",
  "pending_anomalies": [
    {"seed": 123, "report_path": "...", "anomaly_summary": "Explore報告の要約"}
  ],
  "current_failure": null,
  "completed_bugs": [{"seed": 123, "signature": "...", "summary": "..."}],
  "failed_bugs": [{"signature": "...", "attempts": 1, "last_seed": 123}]
}
```

- `next_seed` / `total_battles` / `batch_size`: 探索済みシード範囲の管理（`fuzz`/`replay_fuzz` と同じ意味）。
- `max_turns` / `n_pokemon`: ログを sub agent が読みやすいサイズに保つため、既定値は
  `replay_fuzz` と同じ小さめの値（20ターン・3匹）にしている。
- `pending_anomalies`: 直近のバッチでディスパッチャーが「真のバグらしい」と判断したが
  まだ impl に回していない指摘のキュー。1件ずつ手順4で処理し、処理し終えたらそのエントリを
  取り除く。
- バグ台帳（`completed_bugs` / `failed_bugs`）は `replay_fuzz` と同じ形式。

---

## 実行手順

### 1. 状態ファイルを読む

`.loop/fuzz_log_state.json` を Read で読み込む（存在しなければ初回起動。上記スキーマの
初期値で新規作成する: `next_seed=0`, `total_battles=0`, `batch_size=10`, `max_turns=20`,
`n_pokemon=3`, `report_dir="fuzz_log_reports"`, `pending_anomalies=[]`, `current_failure=null`,
`completed_bugs=[]`, `failed_bugs=[]`）。

### 1.5. 未処理の current_failure / pending_anomalies が残っていないか確認

§共通10 の再開ルールを適用する。`current_failure` が null でない場合、手順4からやり直す。
`current_failure` が null で `pending_anomalies` が空でない場合、新規バッチは実行せず
手順4からキューの先頭を処理する。

### 1.6. worktree を準備する

§共通4 パターンA を適用する（`{worktree}`・ブランチ `loop/fuzz_log`）。

### 2. バッチ実行（ログ生成）

`pending_anomalies` が空の場合のみ実施する。`{worktree}` に cd してから実行する
（`fuzz_log_battle.py` はスクリプト自身のパスから `.loop/{report_dir}/` を解決するため、
worktree 内で実行するとレポートも worktree 配下に書き込まれる）:

```bash
cd "{worktree}" && PYTHONPATH=src python scripts/fuzz_log_battle.py \
  --start-seed {next_seed} --count {batch_size} --workers {workers} \
  --max-turns {max_turns} --n-pokemon {n_pokemon}
```

`count` 件は worker プロセスに分散して並列実行される。`--workers {workers}`（既定1）は、他の
並行セッション・ループ（review/impl 等）も同じマシンの CPU を使うため、`fuzz_log` が全コアを
専有しないよう明示的に絞っている値（省略時のスクリプト既定は CPU数と count の小さい方）。
`fuzz`/`replay_fuzz` の既定4より小さいのは設定漏れではなく意図的な既定値
（`fuzz_log` は既定 `batch_size` も小さく、direct並列より頻繁な起動間隔で回す設計のため）。
常に exit code 0 で終了し、stdout に1行ずつ seed 昇順で `report: {path} crashed={True|False}` が出力される
（`{path}` は worktree 配下の絶対パス）。`next_seed += batch_size`、
`total_battles += batch_size` を更新する。

`crashed=True` の行は本フローの対象外（`fuzz` ループが検出すべき未捕捉例外なので）としてスキップし、
sub agent には読ませない。

### 3. 10件（`crashed=False` の分）を Explore エージェント1体に読ませる

`crashed=False` の全レポート（`crashed=True` を除いた件数分。通常10件、クラッシュがあれば10件未満）を
**1体の Explore エージェントに、対象ファイル一覧を並べて一括で**読ませる（1レポート1エージェントの
並列起動はしない。並列起動によるコスト・レビュー負荷を抑えるため）:

```
jpoke fuzz_log 整合性チェック: seed={seed_list}（{n}件）

以下のバトルログ（対戦のイベントログ全文）を1件ずつ読み、内容の「整合性」だけを確認してほしい。
可読性や情報の親切さ（もっと詳しく書くべき等）は対象外。以下のような、事実として矛盾している
箇所だけを指摘する:

- HP・ランク変化等の数値変化が、ログ中の前後の記述と食い違っている
  （例: ダメージ後のHP表示が直前の残りHPと計算が合わない）
- ログに登場するポケモン名・プレイヤー名が明らかに誤っている
- ターン番号・行動順が矛盾している（退場済みのはずの個体が行動している等）

読むファイル（{n}件、それぞれ独立したバトル。seed ごとに個別に判定すること）:
- seed={seed1}: {report_path1}
- seed={seed2}: {report_path2}
...

出力形式: seed ごとに結果を分けて出力する。
- 矛盾が見つかった場合: `seed={seed}: ` に続けて該当のターン番号・ログ行を引用し、何がどう
  矛盾しているかを一言で説明する（複数あれば箇条書き）
- 矛盾が見つからなかった場合: `seed={seed}: 異常なし` とだけ答える
```

10件の結果がすべて「異常なし」なら状態を保存して手順6へ（`pending_anomalies` は空のまま）。

### 4. 指摘の裏取りとバグ対応

#### 4.1 ディスパッチャーによる裏取り

手順3で「異常なし」以外の報告があった場合、それぞれについてディスパッチャー自身が
関連する `docs/spec/` や実装コード（CLAUDE.md の実装時参照順を参照）を確認し、
Explore の指摘が実際の不整合か、仕様通りの挙動・誤検知かを判断する。

- 誤検知と判断したものは何もせず読み捨てる（`pending_anomalies` に追加しない）。
- 真のバグらしいと判断したものを `pending_anomalies` に
  `{"seed": seed, "report_path": path, "anomaly_summary": "指摘要約"}` として積む。

`pending_anomalies` が空になった（全て誤検知だった）場合は状態を保存して手順6へ。

#### 4.2 current_failure を記録

`pending_anomalies` の先頭を取り出し、
`current_failure = {"seed": seed, "report_path": path, "anomaly_summary": "..."}`
として保存する（キューからは取り除く）。

#### 4.3 impl エージェント（foreground）を起動

```
jpoke fuzz_log バグ修正タスク: seed={seed}

作業ディレクトリ: {worktree}

fuzzで生成した対戦ログ（バトル自体は例外なく正常終了、またはmax_turnsまで進行）を
Explore エージェントがレビューし、以下の不整合が指摘された（ディスパッチャーで簡易裏取り済み）:

{anomaly_summary}

対象ログ全文: {report_path}
再現コマンド（同一シードでバトルを再現できる。ログ全文を再度確認したい場合に使う）:
python scripts/fuzz_log_battle.py --start-seed {seed} --count 1 --max-turns {max_turns} --n-pokemon {n_pokemon}

手順:
1. 上記ログ・再現コマンドで指摘内容を確認する
2. 原因箇所を特定する（CLAUDE.md の実装時参照順を参照。handlers/ の個別ハンドラのバグか、
   core/ のログ記録ロジック（event_manager.py・event_logger等）自体のバグかを見極める）
3. 原因を特定できたら、signature を `LogInconsistency@{ファイル名}:{関数名}:{行番号}`
   の形式（`fuzz`/`replay_fuzz` の signature と同じ形式）で報告に含める
4. 以降は `.claude/loop/_common.md` §共通10「impl エージェントの共通ステップ」の 3〜7 に従う
   （修正 → 必要な sort スクリプト実行 → 再現コマンドで解消確認 → コミットしない）
```

impl が原因を特定できた場合、報告された signature に対して §共通10 の signature 重複チェックを
ここで初めて適用する（`failed_bugs` に同一 signature が attempts >= 2 で存在する場合 →
ループ中断。手動確認を求める）。

impl 失敗（原因不明・修正できず）した場合: `failed_bugs` の該当 signature（判明していれば）を探し
あれば `attempts += 1`、なければ新規エントリを追加する（signature が最後まで判明しなかった場合は
`seed_{seed}` を仮の signature として使う）。`current_failure` をクリアして保存し、review-test は
スキップする。

#### 4.4 review-test エージェント（foreground）を起動

impl 成功後のみ実施:

```
jpoke fuzz_log バグ修正タスク: seed={seed} (signature: {signature}) のレビュー・回帰テスト

作業ディレクトリ: {worktree}

impl エージェントが fuzz_log（イベントログ整合性チェック）発見バグ（再現コマンド:
python scripts/fuzz_log_battle.py --start-seed {seed} --count 1 --max-turns {max_turns} --n-pokemon {n_pokemon}）
を修正した。`.claude/loop/_common.md` §共通10「review-test エージェントの共通ステップ」に従うこと。
手順2（回帰テスト追加）の補足:

- tests/test_utils.py のヘルパー（start_battle・run_move・run_switch など）を使って書く
- 特定の特性・技・アイテムに原因がある場合は該当カテゴリの既存テストファイルに追加する
- ログ記録ロジック自体（event_manager.py・event_logger等）の汎用的なバグの場合は
  tests/test_fuzz_regressions.py に追加する（存在しなければ新規作成してよい）

手順6（コミット）はこのブランチ `loop/fuzz_log` 上で行う:
   git add src/ tests/ docs/
   git commit -m "fix: fuzz_log/seed{seed}_<バグの短い説明>"
```

review-test 成功 → §共通10 の成功時ルールに従う。`completed_bugs` のエントリ形式は
`{"seed": seed, "signature": signature, "summary": "<一言説明>"}`。
続けて「main への反映」の手順に従い、この1件をただちに main へマージする。

review-test 失敗 → 手順4.3の失敗時と同様に `failed_bugs` を更新し、`current_failure` をクリアして
保存し、手順6へ（ただし `pending_anomalies` に未処理分が残っていれば手順4.2に戻って続行する）。

### 5. （手順4完了後）状態ファイルを保存

§共通7・§共通3 に従い Write で上書き（コミット不要）。`pending_anomalies` に未処理分が残っていれば
手順4.2に戻って続行し、空になったら手順6へ。

### 6. 終了

手順4で signature 重複により中断していない場合のみ、§共通7 に従う（続きはユーザーの
`/loop fuzz_log` 再実行で再開する）。

---

## main への反映

1件の修正が review-test で成功・コミットされるたびに、ディスパッチャーがその場で §共通6 の
手順に従い直ちに main へ反映する（`{branch}` = `loop/fuzz_log`）。

## ループの実行間隔

`/loop fuzz_log` の動的セルフペーシング（`ScheduleWakeup`）では、`/loop` スキルの汎用ガイド
（1200〜1800秒）ではなく **固定1分間隔（`delaySeconds=60`）** を使う（`fuzz`/`replay_fuzz` と共通）。
impl / review-test エージェントは常に foreground 起動でそのターン内に完結するため、次回起動も
同様に60秒後とする。

## エラーハンドリング

- impl / review-test 失敗 → `failed_bugs` に記録してループ継続（`pending_anomalies` の残りがあれば続行）。
- 同一 signature が `failed_bugs` で attempts >= 2 と判明 → ループ中断（手動確認）。
- エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。
