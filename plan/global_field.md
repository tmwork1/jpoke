# global_field 実装プラン

更新日: 2026-04-30

## 背景

- 既存実装で じゅうりょく・トリックルーム は効果本体が存在する。
- 仕様書には マジックルーム・ワンダールーム もあり、コード上の未接続箇所があった。
- 既存テストは global_field の一部効果のみをカバーしていた。

## 実装方針

1. 型/マネージャ整備
- GlobalField の型定義に 4 効果を明示する。
- GlobalFieldManager の管理対象を 4 効果へ拡張する。

2. ハンドラ実装
- マジックルーム: ON_CHECK_ITEM_ENABLED で持ち物効果を無効化。
- ワンダールーム: 防御計算イベント（ON_CALC_DEF_RANK_MODIFIER / ON_CALC_DEF_MODIFIER）で参照先を入れ替える。
- 解除時に再計算が必要な効果（マジックルーム）は終了タイミングで item enabled を再評価する。

3. 技データ接続
- じゅうりょく/トリックルーム/マジックルーム/ワンダールームの ON_STATUS_HIT に global_field 起動を接続する。
- ルーム系 3 技は再使用で解除（toggle）にする。

4. テスト拡張
- tick 系: global_field 4 効果のカウントダウンを確認。
- global_field 系: マジックルームの無効化・終了復帰・再使用解除、ワンダールームの防御参照入替を追加。

## 完了条件

- global_field 4 効果の仕様書と実装が一致している。
- 追加テストを含む global_field 関連テストが全件通過する。
- progress/global_field.md で進捗を追跡できる。

## このプランでの実施結果

- 実施済み。
- 未実装項目: なし（global_field 範囲）。
