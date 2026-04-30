# side_field 実装プラン

更新日: 2026-04-30

## 背景

- side_field 本体（11効果）の定義と主要挙動はすでに実装済み。
- `tests/test_side_field.py` に基本ケースは揃っているが、仕様差分が残っていた。
- side_field 仕様は個別ファイルが揃っているが、索引がなかったため参照性を改善する。

## 仕様突合で確認した追加実装対象

1. 壁系の急所時挙動
- 対象: リフレクター / ひかりのかべ / オーロラベール
- 方針: ダメージ補正時に急所フラグを参照し、急所時は軽減を適用しない。

2. ねがいごとの回復量フォールバック
- 対象: `ねがいごと_heal`
- 方針: `field.heal` が未設定のとき、回復量を `target.max_hp // 2` として処理する。

3. テスト補強
- 壁系3種の「急所時に軽減しない」回帰テストを追加。
- ねがいごとの「回復量未設定時フォールバック」テストを追加。

## 実施ステップ

1. `spec/side_field/README.md` を追加して仕様参照を整理
2. `progress/side_field.md` と本プラン作成
3. `src/jpoke/core/damage.py` で急所情報を `BattleContext` に連携
4. `src/jpoke/handlers/field.py` で壁系/ねがいごと処理を更新
5. `tests/test_side_field.py` に回帰テスト追加
6. side_field 関連テスト実行

## 完了条件

- side_field 仕様・進捗・プランが揃っている。
- 追加した回帰テストを含めて `tests/test_side_field.py` が成功する。
