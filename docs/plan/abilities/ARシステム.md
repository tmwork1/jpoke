# 特性実装計画: ARシステム

更新日: 2026-07-10

## 仕様参照

- `docs/spec/abilities/ARシステム.md`

## 実装ゴール

- シルヴァディが持っているメモリに応じてタイプ（＝フォルム相当）を変更する。
- メモリの奪取・交換（自分の道具・相手の道具どちらが対象でも）を防ぐ。
- かがくへんかガス・かたやぶりに影響されない。
- コピー・上書き不可（uncopyable / protected）。

## 実装方針

- `docs/spec/turn.md` に ARシステム/マルチタイプ 個別の記載はないため、同種の
  タイプ変更系特性（マルチタイプ）と同じ Priority（デフォルト100）を踏襲する。
- `Pokemon.ability_override_type` に登場時（`Event.ON_SWITCH_IN`）でタイプを設定し、
  `Pokemon.types` プロパティで反映する（マルチタイプと共通の `_apply_multitype()` ヘルパーを使用）。
  フォルム名・見た目の変化は本シミュレーターでは対象外（バトルに影響するのはタイプのみ）。
- 対応表は `src/jpoke/data/signature_items.py` の `MEMORY_TO_TYPE` に集約する
  （マルチタイプの `PLATE_TO_TYPE` と対の構成）。
- 道具保護は `Event.ON_CHECK_ITEM_CHANGE` ハンドラ（`ARシステム_prevent_item_change`）で
  `ItemManager.can_change_item()` を通して判定する。
  - 自分の持つメモリの奪取・交換を防ぐ（`_block_item_change()` 共通ヘルパー）。
  - トリック/すりかえ等の**交換型**の道具変更では、相手がメモリを持っている場合も
    交換自体が失敗する（`EventContext.is_exchange` フラグ経由で判定。はたきおとす等の
    一方的な除去では `is_exchange=False` のため影響しない）。
- `uncopyable` / `protected` / `gas_proof` フラグで、コピー不可・上書き不可・
  かがくへんかガス非対象を表現する（`mold_breaker_ignorable` は付与しないため、
  かたやぶりの効果を受けない）。

## 変更候補

- `src/jpoke/model/pokemon.py`（`ability_override_type` / `types`）
- `src/jpoke/data/ability.py`
- `src/jpoke/handlers/ability.py`
- `src/jpoke/data/signature_items.py`（`MEMORY_TO_TYPE`）
- `src/jpoke/core/item_manager.py`（`can_change_item` の `is_exchange` フラグ）
- `src/jpoke/core/context.py`（`EventContext.is_exchange`）
- `src/jpoke/data/item.py`（17種のメモリアイテム登録）
- `tests/abilities/test_ability_a.py`

## テスト観点

1. 17種のメモリそれぞれでタイプが対応するタイプに変わる。
2. メモリなしではタイプ変更なし。
3. 自分の持つメモリの奪取・交換は防がれる。
4. メモリを持っていなければ通常の道具変更は防がれない。
5. 交換型の道具変更（トリック/すりかえ相当）は、相手がメモリを持つ場合も失敗する。
6. はたきおとす等の一方的な除去は、相手の道具に関係なく通常通り判定される。
7. かがくへんかガスで無効化されない（`tests/abilities/test_gas.py`）。
8. バトンタッチで、とくせいなし状態が引き継がれずに消える（`tests/moves_status/test_move_ha.py`）。

## 保留・論点

- マルチアタックは `docs/champions/move_list.txt` に存在しないため実装対象外
  （本シミュレーターの対象範囲はポケモンチャンピオンズシングルバトルのみ）。
- へんしん（Transform）は `docs/progress/move.md` で実装保留のため、
  「へんしん先がARシステムをコピーする」仕様は未実装（へんしん実装時に対応する）。
- マルチタイプ（プレート）側にも同様の「相手の道具が交換対象なら失敗する」抜けが
  あったが、マルチタイプのレビュー時に `マルチタイプ_block_item_change` へ
  `is_exchange` 判定を追加して修正済み（`docs/review/abilities/マルチタイプ.md` 参照）。
- プレート系アイテム（マルチタイプ用）は本タスクでは未整備のまま（せいれいプレートのみ登録済み）。
