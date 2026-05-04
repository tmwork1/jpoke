# handlers/ability.py レビュー（2026-05-04）

## 目的
`src/jpoke/handlers/ability.py` を対象に、挙動バグ・回帰リスク・保守性の改善点を整理し、実施順を決める。

## Findings（重大度順）

### 1. Critical: 存在しないメソッド呼び出しで実行時エラー
- 対象: `かんそうはだ_on_turn_end`
- 位置: `src/jpoke/handlers/ability.py:1096`
- 現状:
  - `ctx.check_ability_enabled(battle, mon)` を呼んでいる
  - `BattleContext` にそのメソッドは存在しない（`check_def_ability_enabled` のみ）
- 影響:
  - 当該分岐が実行されると `AttributeError` で停止
  - かんそうはだ持ちのターン終了処理でクラッシュしうる
- 改善案:
  - `if weather is None or not mon.ability.enabled:` へ置換
  - 必要なら `check_def_ability_enabled` ではなく「source 自身の特性有効判定」専用 helper を `common` 側に追加

### 2. High: かげふみ判定が常に真になりうる
- 対象: `かげふみ_check_trapped`
- 位置: `src/jpoke/handlers/ability.py:311`
- 現状:
  - `ctx.source.ability != "かげふみ"` と比較
  - `ability` は `Ability` オブジェクトであり文字列比較は常に不一致（`True`）になる可能性が高い
- 影響:
  - 本来は「相手もかげふみなら拘束しない」ケースで拘束してしまうリスク
- 改善案:
  - `ctx.source.ability.orig_name != "かげふみ"` に修正
  - かげふみミラー対面の回帰テストを追加

### 3. High: 晴れ名称の不一致で仕様逸脱
- 対象: `かんそうはだ_on_turn_end`
- 位置: `src/jpoke/handlers/ability.py:1114`
- 現状:
  - `weather.name in ("にほんばれ", "おおひでり")`
  - 同ファイルの他実装（サンパワー、リーフガード等）は通常晴れを `"はれ"` で判定
- 影響:
  - 通常晴れ (`"はれ"`) で かんそうはだ の定期ダメージが発生しない可能性
- 改善案:
  - `("はれ", "おおひでり")` に統一
  - 晴れ/強い晴れ/無天候の3ケースでテスト追加

## 追加の保守改善（低優先）

### 4. Medium: 天候参照APIが混在
- 現状:
  - `battle.weather` と `battle.weather_manager.active` が混在
- リスク:
  - ノーてんき/エアロック下の挙動差を意図せず生む
- 改善案:
  - 「特性ハンドラ内は `battle.weather` を使う」等の統一ルールを決める
  - 既存実装を段階的に統一

## 実施計画

1. `かんそうはだ_on_turn_end` のクラッシュ修正（Finding 1）
2. `かげふみ_check_trapped` の比較修正（Finding 2）
3. `かんそうはだ_on_turn_end` の晴れ名称統一（Finding 3）
4. 回帰テスト追加

## テスト計画（追加案）

- `test_かんそうはだ_ターン終了_晴れでダメージ`
- `test_かんそうはだ_ターン終了_おおひでりでダメージ`
- `test_かんそうはだ_ターン終了_あめで回復`
- `test_かんそうはだ_ターン終了_ノーてんき下で無効`
- `test_かげふみ_互いにかげふみなら拘束しない`

## 備考
- 今回はレビューと計画書化のみ。コード修正は未実施。
