# examples/ 作成から見えたAPIフィードバック

作成日: 2026-07-11

`docs/plan/examples_api_feedback.md`（1ファイルに全ラウンドを追記する構成）が肥大化したため、
2026-07-14 にラウンドごとのファイルへ分割した。新しい内容は追加せず、この README の
「運用ルール」だけを更新し、あとは全て `pre_loop/` / `loop_rounds/` を参照すること。

## 運用ルール

- 各ラウンドの記録は `[ ]` / `[x]` のチェックリスト形式で管理する。`[x]` は
  「実装対応済み」または「検討のうえ対応しないと決定した（見送り確定）」の両方を含み、
  `[ ]` は「まだ判断・対応していない」項目を指す。チェックを付けたら、その項目の末尾に
  `→ 対応内容 (日付)` を追記する
- **妥当と判断したフィードバックは、判断した時点で即座にsonnet sub agentへ実装を委任する**。
  本体（Fable）は仕様の精査・妥当性判断・差分レビュー・PR操作を担当し、実装・テスト・
  検証はsonnetサブエージェント（`Agent` ツール、`model: sonnet`、`isolation: "worktree"`）に
  詳細な指示書付きで委任する。1件ずつ都度サブエージェントに投げてよく、まとめて
  バッチ実行する必要はない（関連メモ: `feedback_sonnet_subagent_for_work`）
- **`api` ループが新規に追記する記録は `loop_rounds/round{N}.md` を1ラウンド1ファイルとして
  新規作成する**（既存ファイルへの追記ではない）。ファイル内の形式は既存ラウンド
  （`loop_rounds/round5.md` 等）に合わせ、`- [x] <指摘要約> → 対応内容 (日付): <実施内容>`
  の1行1項目とする。`api` ループ以外の手動反映作業も同様に `loop_rounds/` へ
  日付ベースのファイル名（例: `manual_2026-07-14.md`）で追加する
- 次に処理すべきラウンド番号は `loop_rounds/round*.md` のファイル名から最大の番号を
  拾って `+1` する（`.claude/loop/api.md` 参照）

## 目次

### `pre_loop/` — apiループ導入前の一次レビュー（凍結済み・以後編集しない）

1. [初回カバレッジレビュー（2026-07-11/12）](pre_loop/01_initial_coverage.md)
2. [再レビュー指摘（PR #38差分）](pre_loop/02_rereview.md)
3. [3度目のレビュー指摘（examples内TODOコメント）](pre_loop/03_todo_comments.md)
4. [4度目のレビュー指摘（sonnetサブエージェントの内部調査）](pre_loop/04_sonnet_investigation.md)
5. [5度目のラウンド（フレッシュな視点での再調査）](pre_loop/05_fresh_coverage.md)

### `loop_rounds/` — `api` ループおよびその派生作業の記録（ラウンドごとに追加）

- [第5ラウンド（apiループ）](loop_rounds/round5.md)
- [第6ラウンド（apiループ）](loop_rounds/round6.md)
- [examples/ TODOコメントの反映（2026-07-14、手動）](loop_rounds/manual_2026-07-14.md)
- [第7ラウンド（apiループ）](loop_rounds/round7.md)
