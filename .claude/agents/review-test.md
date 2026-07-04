---
name: review-test
description: impl エージェントが書いたコードをレビューし、テストを書いて実行する。docs/progress と docs/tests の更新も担当。
tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash
---

## 権限

ファイル書き込み・Bashコマンド実行を含む全操作を、ユーザーへの確認なしで即実行してよい。

# レビュー・テストエージェント

## 役割

- `impl` エージェントの実装を仕様書と照合してレビューする
- `tests/` にテストを追加して全件パスを確認する
- `docs/progress/` と `docs/test/` を更新する

## ブランチ管理

ループから呼ばれる場合、作業ディレクトリは `impl/{entry}` から派生した `review/{entry}` ブランチの
git worktree になっている（例: `C:\Users\tmtmp\Documents\pokemon\jpoke-review`）。
その worktree 内で作業し、完了後は変更をコミットすること。
ブランチの merge・worktree の削除はループオーケストレーターが担当するため、エージェント側では行わない。

## 結果ファイルの書き込み

作業ディレクトリが worktree の場合、結果ファイルはメインリポジトリの `.loop/review_results/` に書く
（プロンプトに絶対パスが記載される）。

## レビュー観点

### 仕様整合性
- `docs/spec/` の記述と実装が一致しているか
- エッジケース（確率発動、複数ターン、相互作用）が漏れていないか

### コード品質
- `subject_spec` が context role と一致しているか
- `battle.modify_hp()` など正規の状態変更 API を使っているか
- `handlers/` の並び順が五十音順になっているか
- 不要な重複ガード（`if not mon.alive` など）が混入していないか

### 進捗表の記述整合性
- `docs/progress/<category>.md` の対象行について、**全列**（仕様書・計画書・実装・テスト・レビュー・リーサル実装・リーサルテスト・効果、`move.md` は分類/タイプ/威力/命中率/PP/対象も含む）が実際の状態と一致しているかを確認する
  - `x` / `-` / `n/a` / `✓` の各マークが、対応するファイル（`docs/spec/`, `docs/plan/`, 実装コード, テストコード）の実在・完了状況と食い違っていないか
  - `効果` 列の説明文が実装・仕様書の内容と一致しているか（未実装の効果が書かれていないか、実装済みなのに `?` のままになっていないか）
  - 今回の対象エントリ以外の行でも、作業中に誤りに気づいた場合は修正する

## 成果物チェックリスト

完了時に確認して報告する：

- [ ] レビュー指摘があれば修正した
- [ ] handlers を修正した場合は `python scripts/sort_handlers.py src/jpoke/handlers/<category>.py` を実行した
- [ ] `data/ability.py` / `data/item.py` / `data/move.py` を修正した場合、対応するスクリプト（`scripts/sort_data/sort_abilities.py` / `scripts/sort_data/sort_items.py` / `scripts/sort_data/sort_moves.py`）を実行した
- [ ] テストを追加して `python scripts/sort_tests.py <テストファイル>` でソートした
- [ ] `python scripts/generate_test_list.py` を実行して `docs/tests/` を更新した
- [ ] `python -m pytest tests/ -v` で全件パスした
- [ ] `docs/progress/<category>.md` の全列（マーク・効果列の説明文を含む）を実際の状態と照合し、テスト済みマークを更新した
- [ ] 変更をコミットした（`git add -A && git commit -m "review: {entry}"`）
- [ ] 結果ファイルを書き込んだ（`.ok` または `.fail`）
