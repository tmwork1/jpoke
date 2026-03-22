---
applyTo: "src/jpoke/**/*.py,tests/**/*.py,script/**/*.py"
description: "jpoke の Python バトルロジック、データ定義、ハンドラ、テスト、保守スクリプトを編集する時に使う。"
---

# Python 実装指示

## 基本方針
- `Battle`、`EventManager`、`BattleContext`、`Handler` を中心としたイベント駆動設計を維持する。
- 効果宣言は `src/jpoke/data/*.py`、効果本体は `src/jpoke/handlers/*.py` または `src/jpoke/handlers/common.py` に置く。
- データ表の既存の並び順を崩さず、`common_setup()` の振る舞いを維持する。

## Handler の約束事
- `HandlerReturn` は `value` と `stop_event` だけを持つ。
- `subject_spec` は必須であり、使う context role と一致させる。
- 通常イベントでは `source:self`、`source:foe`、`target:self`、`target:foe` を使う。
- ダメージ計算や命中計算では主に `attacker:*` と `defender:*` を使う。
- 独自 helper を増やす前に、`partial(common.modify_stat, ...)`、`partial(common.apply_ailment, ...)`、`partial(common.apply_volatile, ...)`、`partial(common.activate_weather, ...)`、`partial(common.activate_terrain, ...)` を優先する。

## 状態変更ルール
- `Pokemon.hp` へ直接代入してはいけない。必ず `battle.modify_hp(...)` を使う。
- ランク変化には `battle.modify_stat(...)` または `battle.modify_stats(...)` を使う。
- 既存コードが明確に別の流儀を取っていない限り、状態異常、揮発性状態、天候、地形、場の状態は各 manager を通して更新する。
- 新しい横断状態が必要なら、`Battle` または `Pokemon` がすでに持っている近接責務の場所に置く。

## テスト
- `tests/test_utils.py` の `start_battle`、`calc_damage_modifier`、`check_event_result`、`reserve_command`、`log_contains` などを再利用する。
- 可能な限り最寄りの既存テストモジュールに focused な回帰テストを追加する。
- 効果実装を足すときは、発動ケースと非発動ケースを最低 1 つずつ確認する。

## 進捗更新
- 実装数が変わるときは `script/dashboard.py` を使って `dashboard.json` と README の集計を更新する。