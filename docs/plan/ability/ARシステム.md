# 特性実装計画: ARシステム

更新日: 2026-05-01

## 仕様参照

- `spec/ability/ARシステム.md`

## 実装ゴール

- シルヴァディがメモリに応じてタイプ・フォルムを変更する。
- メモリの奪取・交換を防ぐ。
- マジックルーム / さしおさえ との相互作用を仕様どおりにする。

## 実装方針

- マルチタイプと同じ基盤で、対応表だけ差し替える。
- 本体タイプと技タイプ（マルチアタック）の評価タイミングを分離する。
- 道具保護は ItemManager の共通条件で管理する。

## 変更候補

- `src/jpoke/model/pokemon.py`
- `src/jpoke/data/ability.py`
- `src/jpoke/handlers/ability.py`
- `src/jpoke/core/item_manager.py`
- `src/jpoke/data/move.py`
- `tests/test_ability.py`
- `tests/test_item.py`
- `tests/test_move.py`

## テスト観点

1. メモリでタイプとフォルムが変わる。
2. メモリの奪取・交換不可。
3. マルチアタック のタイプ連動。
4. マジックルーム / さしおさえ 中の分離挙動。

## 保留・論点

- マルチタイプとARシステムでコード分岐が増えないよう、型解決をデータ駆動に寄せる。