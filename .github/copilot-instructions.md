# Copilot 指示

## 対象範囲
- ポケモン SV のシングルバトルのみを対象とする。
- 既存コードが対応していない限り、ダブルバトル前提の設計はしない。
- 大きく残っている実装領域は特性、アイテム、技である。状態異常、場、揮発性状態の大半はすでに揃っている。

## 先に読むコード
1. `src/jpoke/core/handler.py`
2. `src/jpoke/core/context.py`
3. `src/jpoke/core/event.py`
4. `src/jpoke/core/battle.py`
5. `src/jpoke/data/models.py`
6. 対象となる `src/jpoke/data/` 配下のファイル
7. 対象となる `src/jpoke/handlers/` 配下のファイル
8. `tests/test_utils.py` と最も近い既存テスト

## 現在のアーキテクチャ
- `Battle` は event、turn、speed、switch、damage、ailment、volatile、query、weather、terrain、global field、side field の各 manager を束ねる facade である。
- 効果宣言は `src/jpoke/data/*.py`、効果本体は `src/jpoke/handlers/*.py` または `src/jpoke/handlers/common.py` に置く。
- `BattleContext` は `source` と `target` を保持し、`attacker` と `defender` はその別名である。
- `HandlerReturn` は現状 `value` と `stop_event` だけを持つ。`success` や log policy がある前提で案内や実装をしないこと。
- `Handler` は現状 `func`、`subject_spec`、`source_type`、`priority`、`once` を使う。

## 実装ルール
- 通常イベントでは `source` と `target` を優先し、ダメージ系イベントで主に `attacker` と `defender` を使う。
- 状態変更は直接書き換えず、manager や共通 helper を優先して使う。
- `Pokemon.hp` へ直接代入してはいけない。`battle.modify_hp(...)` を使うこと。
- ランク変化、状態異常、揮発性状態、天候、地形には `src/jpoke/handlers/common.py` の既存 helper を優先する。
- 追加実装は既存の日本語命名とデータ並び順に合わせる。
- 同じパターンを複数箇所で使わない限り、新しい抽象化は増やさない。

## テストと文書
- `tests/` に焦点の絞れたテストを追加または更新し、可能な範囲で `tests/test_utils.py` の helper を再利用する。
- 実装数が変わる場合は `script/dashboard.py` を使って `dashboard.json` と `README.md` を更新する。
- 調査は `docs/spec/`、実行計画は `docs/plan/`、実装追跡は `docs/checklist/` を使う。
- `.github/` の指示書は短く保ち、現実に存在するファイルと現在のコードにだけ結び付ける。