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
- `subject_spec` は必須。使う context role と一致させる（`source:self` / `target:self` など）。
- `data/*.py` では `partial(...)` の用途を「定数束縛」（タイプ名、倍率、固定ターン数など）に留める。複雑な制御ロジックは `handlers/*` に名前付き関数で実装。
- `handlers/*` では lambda を増やさず、名前付き関数か共通 helper を優先。
- イベント発火側で前提が保証されている場合、ハンドラ側の重ね書きガード（`if not mon.alive` など）は不要。
- 値修正ハンドラは値更新を 1 箇所に集約し、不要なアーリーリターンを避ける。

## 状態変更ルール
- `Pokemon.hp` へ直接代入してはいけない。必ず `battle.modify_hp(...)` を使う。
- ランク変化には `battle.modify_stat(...)` または `battle.modify_stats(...)` を使う。
- 既存コードが明確に別の流儀を取っていない限り、状態異常、揮発性状態、天候、地形、場の状態は各 manager を通して更新する。
- 新しい横断状態が必要なら、`Battle` または `Pokemon` がすでに持っている近接責務の場所に置く。

## 効果の責務設計（イベント駆動設計）
- **効果を所持している側がハンドラを実装する**。技が効果を提供する場合は `handlers/move.py`、特性が効果を提供する場合は `handlers/ability.py`、道具が効果を提供する場合は `handlers/item.py` で実装する。
- 相手方が別のハンドラを持っている場合（例：相手の技が自分の特性で無効化される）、**効果を発動する側（所有者）** ではなく、**その効果に対抗する側** がハンドラを登録する。
- 例：
  - 特性 きゅうばん（強制交代防止）：防御側（きゅうばん所有）が ON_HIT ハンドラで交代効果をキャンセル
  - 特性 すいほう（火炎技のダメージ削減）：防御側（すいほう所有）が ON_CALC_DAMAGE_MODIFIER ハンドラでダメージを修正
  - 技による干渉：発動する側が定義し、相手の特性・道具が干渉する場合は相手側がハンドラを登録

## テスト
- `tests/test_utils.py` の `start_battle`、`calc_damage_modifier`、`check_event_result`、`reserve_command`、`log_contains` などを再利用する。
- 可能な限り最寄りの既存テストモジュールに focused な回帰テストを追加する。
- 効果実装を足すときは、発動ケースと非発動ケースを最低 1 つずつ確認する。

## ひんし時の特殊イベント（ON_FAINTED）
- HP が 0 になったとき、`ON_HP_CHANGED` の直後に `ON_FAINTED` を emit する。
- `ON_FAINTED` は `target`（ひんしポケモン）、`attacker`（ダメージ源）、`move`（使用技）をコンテキストに持つ。
- ひんし時効果（おんねん PP 削減・みちづれ 道連れなど）を ON_FAINTED で実装。
- `ON_FAINTED` emit 直後にハンドラを即座に解除するため、ひんし退場時に `not mon.alive` ガードは不要。
- 詳細：[/memories/repo/jpoke_on_fainted_refactoring.md](../../memories/repo/jpoke_on_fainted_refactoring.md)

## コード整形ルール
- 長い `if` 文（80文字以上）は括弧で囲んで複数行に展開する。`and` で条件ごとに改行。
- 1 行に収まる単純な条件（`and` が 1〜2 個）はそのまま保持。

## 進捗更新
- 実装数が変わるときは `progress/*.md` の該当カテゴリ行を更新し、`README.md` の集計と整合させる。