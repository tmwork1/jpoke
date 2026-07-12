# API/examples改善（api）ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `api`、方式は単一ブランチ）。
**実装作業ディレクトリ**: `{worktree}`（永続 worktree、ブランチ `loop/api`）。

---

## フロー概要

`docs/plan/examples_api_feedback.md` には、手動（Fable本体 + sonnet sub agent）で行った
4ラウンド分の `examples/`・公開API 改善レビューの記録がある。本フローはこのレビュー→実装
サイクルを自律ループ化したもの。

1ラウンドにつき、次の2種類のレビューエージェント（**Explore・読み取り専用・並列2体**）を起動する:

- **開発者エージェント**: `src/jpoke/` の実装を自由に読める設定。内部実装を読んだからこそ
  気づく未紹介の公開API、公開APIの設計上の問題、実装を読んで気づいたバグを指摘する。
- **初心者エージェント**: **`src/jpoke/` は一切読まない**設定。poke-env 等の類似ライブラリ
  経験者・jpoke初見という立場で、`README.md`・`examples/`・`docs/api/` のみを読み、
  ドキュメント／教材としての分かりやすさ、公開APIの使い勝手を指摘する。

2エージェントの報告を **ディスパッチャー自身**が確認し、`docs/plan/examples_api_feedback.md`
の既存項目と重複しないか、実際に妥当な指摘かを裏取りする（`fuzz_log` ループの Explore 指摘の
裏取りと同じ立ち位置）。妥当と判断したものだけをキューに積み、1件ずつ `impl`（実装）→
`review-test`（レビュー・回帰テスト・ドキュメント追記・コミット）の2段階で `loop/api` 上で
処理する（`todo`/`fuzz_log` と同じ2段階パターン）。

1件処理されるごとに直ちに main へ反映する（1件ごと即時、`fuzz_log` と同じ粒度）。

**1回の起動では1ラウンド分（新規レビュー起動 → 裏取り → キューに積んだ finding の全消化）を
処理したら、そこで必ずターンを終える**（§共通7。次ラウンドをこのターン内で連続開始しない）。

両エージェントとも「指摘なし」（または全指摘が誤検知・重複）だったラウンドが**2回連続**した
場合、「カバレッジは十分に高い状態」と判断してループを一時休止する（ワークツリー・ブランチは
残す。ユーザーが `/loop api` を再実行すると再度レビューラウンドを開始する）。

---

## 状態ファイルのスキーマ

```json
{
  "worktree": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\api",
  "round": 5,
  "pending_findings": [
    {"id": "r5-1", "source": "developer", "summary": "一言要約", "detail": "該当ファイル:行、根拠、対応案"}
  ],
  "current_finding": null,
  "dismissed": [
    {"summary": "一言要約", "reason": "対応不要と判断した理由"}
  ],
  "consecutive_empty_rounds": 0,
  "completed": [{"id": "r5-1", "summary": "...", "round": 5}],
  "failed": [{"summary": "一言要約（正規化）", "attempts": 1, "last_id": "r5-1"}]
}
```

- `round`: 現在処理中（未処理なら次に開始する）のラウンド番号。初回起動時は
  `docs/plan/examples_api_feedback.md` の既存見出し（「N度目のレビュー指摘」「第Nラウンド」等、
  表記ゆれを許容し見出し中の数字を拾う）から最終ラウンド番号を特定し、その番号をそのまま
  初期値にする。このループが新規に追記する見出しは `## 第{round}ラウンド（apiループ）` の形式に
  統一する。**インクリメントのタイミング**: そのラウンドの finding をすべて消化し終えた時点
  （手順4/5の分岐先）、または指摘0件で一時休止に至らなかった場合（手順3）にのみ `round += 1`
  する。一時休止に至った場合は `round` を進めない（次回同じラウンド番号で再挑戦する）。
- `pending_findings`: ディスパッチャーが妥当と判断した指摘のキュー。`id` は `r{round}-{連番}`。
- `current_finding`: 処理中の finding（中断復帰用）。**手順4で `pending_findings` から
  ポップした時点でセットする。中断復帰時は再ポップしない**（手順1.5参照）。
- `dismissed`: impl エージェントが「対応不要」と判定した finding の記録（`summary` と理由）。
  手順3の重複判定で `docs/plan/examples_api_feedback.md` と合わせて参照し、同じ指摘が
  次ラウンド以降で再提出されるのを防ぐ（このリストが無いと、対応不要判定は diff を生まず
  記録にも残らないため、同じ指摘が延々と再提出されて `consecutive_empty_rounds` が
  0 にリセットされ続け、ループが一時休止に到達できなくなる）。
- `consecutive_empty_rounds`: 有効な指摘が0件だったラウンドの連続回数。
- `completed`/`failed`: `todo`/`fuzz_log` と同じ役割。**`failed` の照合キーは `id` ではなく
  正規化した `summary`**（`id` はラウンドごとに採番し直されるため、同一指摘が別ラウンドで
  再提出されたときに `id` では一致しない。`last_id` は直近の finding id を記録するだけの
  参考情報）。同一 summary で `attempts >= 2` になったものは§共通8と同様スキップ対象とする。

---

## 実行手順

### 1. 状態ファイルを読む

`.loop/api_state.json` を Read で読み込む。存在しなければ初回起動:
`docs/plan/examples_api_feedback.md` を Read し、既存見出し（表記ゆれ「N度目のレビュー指摘」
「第Nラウンド」等を問わず見出し中の数字を拾う）から最終ラウンド番号を特定して
`round = 最終ラウンド番号`（見つからない場合は `round = 1`）とし、`pending_findings=[]`,
`current_finding=null`, `dismissed=[]`, `consecutive_empty_rounds=0`, `completed=[]`,
`failed=[]` で新規作成する。

### 1.5. 再開ルール

- `current_finding` が null でない場合、前回の起動が中断された状態。**再ポップせず**
  `current_finding` の内容をそのまま `finding` として使い、手順4の「impl エージェント起動」
  からやり直す（ポップ・failed チェックは行わない）。
- `current_finding` が null で `pending_findings` が空でない場合、手順4の
  「先頭をポップする」からやり直す。
- 両方とも空の場合、通常どおり手順2（新規ラウンド起動）へ進む。

### 1.6. worktree を準備する

§共通4 パターンA を適用する（`{worktree}`・ブランチ `loop/api`）。

### 2. 新規ラウンド起動

`pending_findings` が空 かつ `current_finding` が null の場合のみ実施する。
開発者エージェントと初心者エージェントを **同一メッセージ内で並列起動**する
（`Agent` ツール、`subagent_type: "Explore"`、`run_in_background: false`、breadth は
"very thorough"）。

開発者エージェントへのプロンプト:

```
jpoke API改善レビュー（第{round}ラウンド、開発者視点）

あなたは jpoke（ポケモンバトルシミュレーションPythonライブラリ）の開発者です。
src/jpoke/ 配下の実装を自由に読んでよい。examples/ ディレクトリ（examples/README.md含む）・
docs/api/・公開API（jpoke トップレベルおよび jpoke.model / jpoke.players 等からimportできる
クラス・関数）を対象に、以下の観点でレビューしてほしい:

- src/jpoke/ 内部を読んだからこそ気づく、examples で一度も実演されていない有用な公開API
- 公開APIの設計上の問題（内部実装への直接アクセスを利用者に強いている、一貫性のない引数名・
  戻り値、docstring不足、不必要に複雑な呼び出し方法）
- 実装を読んで気づいたバグ・potential issue（examples や公開APIの使い方に起因して
  利用者が踏みやすい罠）

参考: 過去のレビュー結果は docs/plan/examples_api_feedback.md に記録されている
（このファイル自体は先に読むこと）。既に「対応済み」「見送り確定」となっている項目と
同じ指摘は避けること。

出力形式: 指摘ごとに「summary: 一言要約」「detail: 該当ファイル:行、根拠、対応案」を
箇条書きで。指摘が無ければ「指摘なし」とだけ答える。300語程度で簡潔に。
```

初心者エージェントへのプロンプト:

```
jpoke API改善レビュー（第{round}ラウンド、初心者視点）

あなたは poke-env 等の類似ライブラリの経験はあるが jpoke は初めて使う開発者です。
**src/jpoke/ 配下のソースコードは絶対に読まないこと**。README.md・examples/ 配下・
docs/api/ のみを読んでレビューしてほしい。

観点:
- ドキュメント・examples だけでは分からない、または誤解しやすい挙動
- 教材としての質（難易度勾配、コメントの分かりやすさ、次に何を試すかの誘導）
- 公開APIの使い勝手（引数の分かりにくさ、命名の一貫性、冗長な書き方）

参考: 過去のレビュー結果は docs/plan/examples_api_feedback.md に記録されている
（このファイル自体はドキュメントなので読んでよい。src/jpoke/ を読む代わりにこれを参照してよい）。
既に「対応済み」「見送り確定」となっている項目と同じ指摘は避けること。

出力形式: 指摘ごとに「summary: 一言要約」「detail: 該当箇所、根拠、対応案」を箇条書きで。
指摘が無ければ「指摘なし」とだけ答える。300語程度で簡潔に。
万一 src/jpoke/ を読んでしまった場合はその旨を明記してよい（その指摘は開発者視点相当として
扱われる）。
```

### 3. 指摘の裏取りとキュー投入（ディスパッチャー自身）

2エージェントの報告を確認し、それぞれの指摘について:

- `docs/plan/examples_api_feedback.md` の既存項目（対応済み・見送り確定を含む）と重複していないか
- 状態ファイルの `dismissed`（impl が対応不要と判定した過去の指摘）と重複していないか
- 状態ファイルの `failed` に同内容（正規化した `summary` が一致）で `attempts >= 2` の
  エントリが無いか（あれば§共通8と同様スキップし、キューに積まない）
- 関連する実装コード・`docs/spec/`・`docs/api/` を見て、実際に妥当な指摘か（誤検知でないか）

を判断する。誤検知・重複・見送り確定済み・`dismissed`済み・`failed` 2回以上のものは読み捨てる。
妥当と判断したものだけ、`id = "r{round}-{連番}"` を付けて `pending_findings` に
`{"id", "source": "developer"|"beginner", "summary", "detail"}` として積む。

**`pending_findings` に1件も積まれなかった場合**（両エージェントとも「指摘なし」、または
全指摘が誤検知・重複・見送り確定・dismissed済みだった場合）:

- `consecutive_empty_rounds += 1`
- `consecutive_empty_rounds >= 2` の場合: 状態を保存し（**`round` は変更しない**）、
  「examples/API改善: 直近2ラウンド連続で有効な指摘なし。カバレッジは十分に高い状態と
  判断し、ループを一時休止します。`/loop api` を再実行すると再度レビューラウンドを
  開始します」と報告してターンを終える（§共通7のターン終了。worktree・ブランチは残す。
  完全終了処理は行わない）。
- `consecutive_empty_rounds < 2` の場合: `round += 1` として状態を保存し、
  「examples/API改善: 第{旧round}ラウンドは有効な指摘なし。次回 `/loop api` 実行時に
  第{round}ラウンドを開始します」と報告してターンを終える（§共通7。1回の起動につき
  1ラウンド分の処理に留める）。

**1件以上妥当な指摘があった場合**: `consecutive_empty_rounds = 0` に戻し、手順4へ進む。

### 4. 実装（impl エージェント、foreground）

`current_finding` が null なら、`pending_findings` の先頭をポップして `finding` とする
（既にセットされていた場合＝再開時は、ポップし直さずそのまま使う。1.5節参照）。

ポップした直後に `failed` を確認し、同内容（正規化した `summary` が一致）で
`attempts >= 2` のエントリがあれば（手順3の事前チェックをすり抜けて手順3実行後に
`failed` へ追加されたケース等）このラウンドではスキップする。`current_finding` は
セットせず、`pending_findings` が残っていれば本手順の先頭に戻って次の finding を取り出す。
残っていなければ `round += 1` して手順6へ進む。

スキップ対象でなければ `current_finding = finding` として保存してからエージェントを起動する。

```
jpoke API改善タスク: {finding.summary}（id: {finding.id}）

作業ディレクトリ: {worktree}

{finding.source == "developer" ? "開発者視点" : "初心者視点"}のレビューで挙がった指摘:
{finding.detail}

手順:
1. 指摘対象に応じて関連コードを確認する（src/jpoke/ の実装に関わる場合は CLAUDE.md の
   実装時参照順に従う。examples/ やドキュメントのみに関わる指摘の場合は README.md・
   examples/・docs/api/ を中心に確認すればよい）
2. 妥当性を再確認する。既に対応済み、または指摘が事実誤認と判明した場合は実装を行わず
   「対応不要: <理由>」とだけ報告して終了する
3. 必要な実装・修正を行う（src/jpoke/ の公開API変更、examples/ への追加・修正、
   docs/api/README.md 等の関連ドキュメント更新を含みうる）。src/jpoke/ の公開APIの
   シグネチャ変更（引数の削除・型変更等）を伴う破壊的変更は、他の並行 loop の進行中
   ブランチと衝突しうるため、examples/ 側の書き換えだけで済む代替手段が無いか優先的に
   検討する。実装する場合は CHANGELOG.md への明記を忘れない
4. handlers/ を変更した場合、python scripts/sort_handlers.py src/jpoke/handlers/<category>.py を実行する
5. data/ability.py・data/item.py・data/move.py を変更した場合、対応する
   scripts/sort_data/sort_*.py を実行する
6. テストは書かない（review-test エージェントが担当）
```

- **「対応不要」と報告された場合**: 何も変更されていないので diff は無い。`dismissed` に
  `{"summary": finding.summary, "reason": <impl の理由>}` を追加する。`current_finding` を
  クリアして保存し、review-test はスキップする（`completed`/`failed` どちらにも追加しない）。
  `pending_findings` が残っていれば本手順の先頭に戻り、空なら `round += 1` して手順6へ進む。
- **失敗（実装を試みたが完了できなかった）場合**: `failed` の同内容（正規化した `summary` が
  一致）エントリを探し、あれば `attempts += 1` かつ `last_id = finding.id` を更新、なければ
  新規に `{"summary": finding.summary, "attempts": 1, "last_id": finding.id}` を追加する。
  `current_finding` をクリアして保存し、review-test はスキップする。`pending_findings` が
  残っていれば本手順の先頭に戻り、空なら `round += 1` して手順6へ進む。

### 5. レビュー・テスト（review-test エージェント、foreground）

impl が実装を完了した場合のみ実施（「対応不要」判定・失敗時はスキップ）:

```
jpoke API改善タスク: {finding.summary}（id: {finding.id}）のレビュー・回帰テスト

作業ディレクトリ: {worktree}

impl エージェントが jpoke API改善指摘（第{round}ラウンド、{finding.source}視点）を実装した。

{finding.detail}

手順:
1. 修正内容を対象ファイルで確認し、問題があれば修正する
2. 必要なテストを追加・修正する（tests/test_utils.py のヘルパーを再利用する）
3. python scripts/sort_tests.py <対象ファイル> でソートする（テストファイルを変更した場合）
4. python scripts/generate_test_list.py でテスト一覧を更新する
5. examples/ 配下のファイルを変更・追加した場合、そのファイルを個別実行して出力を確認する。
   tests/test_examples_smoke.py が存在すれば併せて実行する
6. python -m pytest tests/ -v を実行し、全テストが通ることを確認する。今回の修正と無関係な
   既存テストが flaky と判明した場合は .claude/loop/_common.md §共通13 に従いその場で修正する
7. docs/plan/examples_api_feedback.md に対応内容を追記する。第{round}ラウンドの見出し
   （`## 第{round}ラウンド（apiループ）`）がまだ無ければ新規作成し、既存ラウンドと同じ形式
   （`- [x] <指摘要約> → 対応内容 (日付): <実施内容>`）で1項目を追記する
8. 変更をすべてコミットする（このブランチ loop/api 上で行う）:
   git add -A
   git commit -m "api: {finding.summary}"
```

成功 → `completed` に `{"id": finding.id, "summary": finding.summary, "round": round}` を追加し、
`current_finding` をクリアして保存する。続けて「main への反映」の手順に従い、この1件を
ただちに main へマージする。`pending_findings` が残っていれば手順4の先頭に戻り、空なら
`round += 1` して手順6へ進む。

失敗 → 手順4の失敗時と同様に `failed` を更新し、`current_finding` をクリアして保存する。
`pending_findings` が残っていれば手順4の先頭に戻り、空なら `round += 1` して手順6へ進む。

### 6. 状態保存・ターン終了

§共通7・§共通3 に従い Write で状態ファイルを上書き保存する（コミット不要）。手順4/5から
ここに来た時点で、そのラウンドの finding は全て消化済み（成功・失敗・対応不要いずれか）。
**次ラウンドをこのターン内で連続開始せず、必ずここでターンを終える**。続きはユーザーの
`/loop api` 再実行、または直前に投げた background エージェントの完了通知で再開する。

### 7. 終了

手順3・手順6のいずれから来た場合も、一時休止と判定していない限り §共通7 に従い簡潔な
完了報告でターンを終える。

---

## main への反映

1件の指摘が review-test で成功・コミットされるたびに、ディスパッチャーがその場で §共通6 の
手順に従い直ちに main へ反映する（`{branch}` = `loop/api`）。

## エラーハンドリング

- impl / review-test 失敗 → `failed` に記録してループ継続（`pending_findings` の残りが
  あれば続行）。同内容の再提出は次ラウンド以降の手順3の裏取りで弾かれる。
- 同一内容（正規化した summary）が `failed` で attempts >= 2 → 手順3または手順4で
  スキップして次の finding へ（`fuzz_log` の signature 重複中断とは異なり、本フローの
  finding は指摘ごとに独立しているためループ全体は中断しない）。
- impl が「対応不要」と判定した finding は `dismissed` に記録し、以後の重複提出を手順3で
  弾く（記録し忘れると同じ指摘が再提出され続け、一時休止条件に到達できなくなる）。
- 公開APIのシグネチャ変更を伴う破壊的変更が、他の並行 loop（`impl`/`review`/`todo`/`lethal`
  等）の進行中ブランチと衝突しうる場合は、実装より examples/ドキュメント側の対応を優先する
  （impl プロンプトの手順3に明記済み）。
- エージェント呼び出しがAPIセッション制限で失敗した場合 → §共通12 に従う。

## 状態例

```json
{
  "worktree": "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\api",
  "round": 5,
  "pending_findings": [
    {"id": "r5-2", "source": "beginner", "summary": "◯◯の引数名が分かりにくい", "detail": "..."}
  ],
  "current_finding": null,
  "dismissed": [
    {"summary": "△△を新設すべき", "reason": "既に□□として実装済みだった"}
  ],
  "consecutive_empty_rounds": 0,
  "completed": [
    {"id": "r5-1", "summary": "battle.foo() にdocstringを追加", "round": 5}
  ],
  "failed": []
}
```
