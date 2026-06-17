# jpoke — Claude Code ガイド

## プロジェクト概要

ポケモンバトルシミュレーション開発用 Python ライブラリ。
ポケモンチャンピオンズのシングルバトルをターゲットにしている。
テスト・仕様書・コード内コメントは **日本語** で書く。

## テストの実行

```powershell
# 全テスト
python -m pytest tests/ -v

# 特定ファイル
python -m pytest tests/test_ability.py -v

# 特定テスト関数（日本語関数名も可）
python -m pytest tests/test_ability.py -k "ARシステム" -v
```

テストは `tests/` 直下にあり、`tests/test_utils.py` はテストヘルパー（テスト対象外）。

## アーキテクチャ

### 主要コンポーネント

| クラス／モジュール | 役割 |
|---|---|
| `core/battle.py` `Battle` | バトル全体の状態管理・ターン進行 |
| `core/turn_controller.py` | ターン順・行動順の制御 |
| `core/event_manager.py` | イベント発火・ハンドラ呼び出し |
| `core/handler.py` `Handler` | ハンドラ定義（subject, subject_spec, 関数） |
| `core/context.py` `BaseContext` / `EventContext` / `AttackContext` | ハンドラに渡すイベントコンテキスト（攻撃フローは `AttackContext`、それ以外は `EventContext`） |
| `model/` | `Pokemon`, `Move`, `Field` などのモデル |
| `data/` | `ability.py`, `move.py`, `item.py` — 各エンティティのデータ定義とハンドラ登録 |
| `handlers/` | `ability.py`, `move.py`, `item.py` など — ハンドラ実装 |
| `enums/` | `Event`, `Command`, `Interrupt`, `LogCode` |
| `utils/type_defs.py` | `Stat`, `Type`, `AilmentName`, `VolatileName` など Literal 型の定義 |

### イベント駆動モデル

1. バトルロジックが `Event` を発火
2. `EventManager` が登録済み `Handler` を順に呼び出す
3. 各 `Handler` は `HandlerReturn(value, stop_event)` を返す
4. ハンドラ登録は `data/ability.py`, `data/item.py` などで行う

### ハンドラ追加の流れ

```
data/ability.py  →  handlers/ability.py に実装  →  data/ability.py に登録
```

### テストユーティリティ

`tests/test_utils.py` の `start_battle()` でバトルを即座にセットアップできる。

```python
battle = t.start_battle(
    team0=[Pokemon("ピカチュウ", ability_name="せいでんき")],
    team1=[Pokemon("カビゴン")],
    weather=("はれ", 5),
    accuracy=100,   # 命中率を固定
)
```

## 実装時の参照順

新しい特性・技・アイテムを実装する前に以下の順で読む：

1. `src/jpoke/core/handler.py`
2. `src/jpoke/core/context.py`
3. `src/jpoke/core/event.py`
4. `src/jpoke/core/battle.py`
5. `src/jpoke/data/models.py`
6. 対象の `src/jpoke/data/<category>.py` と `src/jpoke/handlers/<category>.py`
7. `tests/test_utils.py` と最寄りの既存テスト
8. **`docs/spec/turn.md`** — 実装するイベントの priority を確認し、計画書に明記する

## Handler の約束事

- `HandlerReturn` は `value` と `stop_event` のみを持つ
- `subject_spec` は必須。イベントが渡すコンテキスト型のロールと一致させる
  - 攻撃フェーズ（`AttackContext`）: `attacker:self` / `defender:self`
  - 非攻撃フェーズ（`EventContext`）: `source:self` / `target:self`
- 固有効果のロジックは `handlers/*` に名前付き関数で実装し、`data/*.py` からその関数を登録する
- `handlers/*` の並びは `data/*.py` の定義順（五十音順）に合わせる
- イベント発火側で前提が保証されている場合、ハンドラ側の重複ガード（`if not mon.alive` など）は不要
- **priority は `docs/spec/turn.md` で対象イベントの行を必ず確認する。未掲載のイベント（ダメージ計算内部等）は既存の同種ハンドラを参照して決定し、計画書に根拠を明記する**

## 状態変更ルール

- `Pokemon.hp` へ直接代入禁止 → 必ず `battle.modify_hp(...)` を使う
- ランク変化は `battle.modify_stat(...)` または `battle.modify_stats(...)`
- 状態異常・揮発性状態・天候・地形・場の状態は各 manager を通して更新する


## 仕様書・ドキュメント

| ディレクトリ | 役割 |
|---|---|
| `docs/spec/` | 技・アイテム・特性・場の効果の挙動仕様（実装前に読む） |
| `docs/plan/` | 現在の実行計画と優先順位 |
| `docs/progress/` | カテゴリ別の実装追跡（`ability.md`, `item.md`, `move.md`） |
| `docs/test/` | テスト一覧（`scripts/generate_test_list.py` で生成） |

実装が完了したら、以下の順で進捗を更新する：

1. `docs/progress/<category>.md` の該当行を更新する（実装済みフラグ・件数）

## 開発ルール

- **ファイルの書き出し先はプロジェクトディレクトリ（`c:\Users\tmtmh\Documents\pokemon\jpoke\`）配下に限定する。プロジェクト外へのファイル作成・書き込みは禁止**
- **対象はポケモンチャンピオンズシングルバトルのみ**
- コメント・docstring・テスト関数名は **日本語** で書く
- テスト関数名は `test_<特性名/技名>_<確認内容>` の形式
- ハンドラの実装は `handlers/`、登録は `data/` で行う
- 新しい `Literal` 型は `utils/type_defs.py` に追加する
- 型アノテーションは Python 3.10+ の構文（`X | Y`, `list[X]`）を使う
- 長い `if` 文（80文字以上）は括弧で囲んで複数行に展開し、`and` で条件ごとに改行する

## テストの追加ルール

- `test_utils.py` の `start_battle`、`run_move`、`run_switch` などを再利用する
- テスト項目を追加・修正したら、以下の順で実行する：
  1. `python scripts/sort_tests.py <対象ファイル>` — テスト関数を五十音順に並び替える（複数指定可、例: `tests/test_ability.py tests/test_move.py`）
  2. `python scripts/generate_test_list.py` — `docs/test/` のテスト一覧を更新する
  3. `python -m pytest tests/ -v` — 全テストが通ることを確認する
