# Gのちから レビュー結果

## 仕様書

- `.internal/spec/moves/` に個別の仕様書は存在しない。100%発動の追加効果（相手の
  『ぼうぎょ』-1）は他の同種の追加効果技（アイアンテール、かみくだく など）
  と同様に `.internal/spec/moves/_move_secondary_1.md` の一覧表で管理する方針であり、
  一次情報（Wiki）と照合した結果、効果自体は正しく記載されていた（18行目）。
- **不備を発見し修正した**: `_move_secondary_1.md` 18行目の技名が全角の
  `Ｇのちから`（U+FF27）になっており、実装・進捗表で使われている半角の
  `Gのちから`（一次情報のページタイトルも半角）と一致していなかった。半角
  表記に修正した。
- じゅうりょく状態時の威力1.5倍効果は `.internal/spec/fields/じゅうりょく.md` に
  既に正しく記載されている（「Gのちからの威力が1.5倍になる」）ため変更なし。
- 個別ファイルは作成しないという既存の方針（3ぼんのや等のレビュー実績と同様）
  を踏襲し、新規作成は行っていない。

## 実装計画書

- `.internal/plan/moves/Gのちから.md` は存在しない。同種の単純な追加効果技にも
  個別の計画書は存在せず、慣例に倣い新規作成はしていない。
- じゅうりょく威力補正のハンドラ優先度（ON_CALC_POWER_MODIFIER, priority=100）
  は `.internal/spec/fields/じゅうりょく.md` に既に根拠が明記されており、実装も
  それに準拠している。

## 実装（handlers/ / data/）

- **不備を発見し修正した**: `src/jpoke/data/move.py` の `"Gのちから"` の
  `power` が `80` になっていたが、一次情報（Wiki）によると本プロジェクトが
  対象とする Pokémon Champions では威力90に変更されている（SVまでは80）。
  `power=90` に修正した。`.internal/progress/move.md` の該当行は元々90と正しく
  記載されていたため、実装側のみが誤っていた。
- `Event.ON_CALC_POWER_MODIFIER`（`Gのちから_gravity_boost`）でじゅうりょく中に
  威力1.5倍（6144/4096）にする実装、`Event.ON_DAMAGE_HIT`（
  `Gのちから_lower_defender_def`）で `modify_defender_stats` を用いて防御側の
  ぼうぎょを1段階下げる実装、いずれも仕様通りで変更なし。
- `lethal_handlers` の `Gのちから_lower_def`（`LethalEvent.ON_HIT`）も
  `ctx.move_secondary` を条件に防御ダウンを適用しており妥当。変更なし。
- `subject_spec` は `MoveHandler` のデフォルト（`attacker:self`）を用いており、
  他の同種ハンドラと一貫している。
- `flags={"secondary_effect"}` は追加効果技として正しい。直接攻撃ではない
  （`contact` フラグなし）ことも一次情報と一致。
- `python scripts/sort_data/sort_moves.py` を実行済み（並び替え自体は変更なし）。

## テスト

- 既存テストで一次情報の全項目がカバーされていることを確認した。変更なし。
  - `tests/moves_attack/test_move_sa.py`:
    `test_Gのちから_じゅうりょくなしでは通常威力`,
    `test_Gのちから_ぼうぎょ1段階低下が発動する`
  - `tests/test_field.py`: `test_じゅうりょく_Gのちから強化`
    （威力補正6144/4096の確認）
  - `tests/test_lethal.py`: `test_Gのちから_ぼうぎょダウン_secondary有り`,
    `test_Gのちから_ぼうぎょダウン_secondary無し`
  - `power` 修正（80→90）はダメージ量に依存する既存テストを壊さないことを
    確認した（威力の具体値をハードコードしたテストは存在しない）。
- `python scripts/sort_tests.py tests/moves_attack/test_move_sa.py`、
  `python scripts/generate_test_list.py` を実行したが差分なし。
- `python -m pytest tests/ -v` を実行し、Gのちから関連のテストはすべて成功。
  なお `test_megaevol.py` の2件（`うなぎのぼり`・`ほのおのたてがみ` の
  `ABILITIES` 未登録によるKeyError）と `test_ability_ta.py` の
  `test_てんねん_攻撃側は防御ランク補正を無視する` の2件は、本タスクの変更
  （`git stash` で確認済み）とは無関係の既存不具合／並列作業中の影響であり、
  Gのちからの実装には起因しない。結果は `.loop/test_logs/Gのちから.log` に
  保存した。

## 進捗表

- `.internal/progress/move.md` のGのちから行を更新:
  - `PP` 列を誤記の `12` から一次情報どおりの `10` に修正
  - `レビュー` 列を `-` から `✓` に更新
