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
- `data/*.py` では `partial(...)` を使ってよいが、用途は「定数束縛」までに留める。天候名、地形名、タイプ名、倍率、固定ターン数のような宣言的パラメータに限る。
- `target_spec` と `source_spec` を含む多引数の `partial(common.modify_stat, ...)` や、`count`・`toggle` つきの `partial(common.apply_volatile, ...)` / `partial(common.activate_global_field, ...)` が増えてきたら、`data` 側ではなく `handlers/*` に名前付き関数や薄いラッパーを作ることを優先する。
- 特性・技・道具の意味が強い処理は、汎用 `partial(...)` で直接表さず、`handlers/ability.py`、`handlers/move.py`、`handlers/item.py` に名前付き関数を置く。
- `handlers/*` では lambda を基本的に増やさない。定数の `HandlerReturn` を返すだけの極小用途を除き、名前付き関数または共通 helper を使う。
- 重複削減は、lambda 化よりも「共通関数 + 名前付き薄ラッパー」または「共通関数 + data 側 partial」を優先する。
- イベント発火側で前提が保証されている場合は、同じ条件の防御ガードをハンドラ側に重ね書きしない（冗長な `if` を避ける）。
- 値を修正して返すタイプのハンドラは、原則として値を更新して `return HandlerReturn(value=value)` を1か所に集約する（不要なアーリーリターンを増やさない）。

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

## 進捗更新
- 実装数が変わるときは `progress/*.md` の該当カテゴリ行を更新し、`README.md` の集計と整合させる。