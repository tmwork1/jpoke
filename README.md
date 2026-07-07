# jpoke

ポケモンバトルシミュレーション開発用の Python ライブラリ。イベント駆動でポケモンの技・特性・アイテム・
状態異常・場の効果などを再現し、bot 開発や乱数調整・ダメージ計算・木探索などの用途に使う。

## 対象範囲

- **対象はポケモンチャンピオンズのシングルバトルのみ**（ダブルバトル等は対象外）
- 技・特性・アイテム・ポケモンなどの仕様ソースは **第9世代（スカーレット・バイオレット）** を基本とし、
  ポケモンチャンピオンズ側でルールが異なる場合はそちらを優先する
- 第9世代で実装されていない技・アイテム・特性・ポケモンなどは実装しない

このプロジェクトの規約・アーキテクチャの詳細は [CLAUDE.md](CLAUDE.md) を参照（この README の対象範囲の
定義を正とし、CLAUDE.md 側はこの記述を参照する）。

## インストール

```bash
git clone https://github.com/tmwork1/jpoke.git
cd jpoke
pip install -e .

# 開発（テスト・lint・型チェック）に必要な依存を含める場合
pip install -e . pytest pytest-cov ruff mypy
# または uv を使う場合
uv sync
```

`requires-python = ">=3.10"`。型アノテーションは Python 3.10+ の構文（`X | Y`, `list[X]`）を使用する。

## クイックスタート

もっとも低レベルな API（`Battle` / `Player` / `Pokemon`）だけを使った最小例:

```python
from jpoke import Battle, Player, Pokemon

player1 = Player("Player 1")
player1.team.append(Pokemon("ピカチュウ", move_names=["でんこうせっか"]))
player2 = Player("Player 2")
player2.team.append(Pokemon("フシギダネ", move_names=["たいあたり"]))

# n_selected: 選出数（チームが1匹だけの場合は1にする。デフォルトは3）
battle = Battle((player1, player2), n_selected=1)
battle.start()

while battle.judge_winner() is None and battle.turn < 100:
    # commands=None の場合は各 Player.choose_command() が使われる
    # （デフォルト実装は利用可能な最初のコマンドを選ぶだけの単純なプレイヤー）
    battle.step()

print(battle.judge_winner().name)   # 勝者の名前
battle.print_logs()                 # このターンのログを表示
```

任意ターンでのピンポイントな状態検証や技の実行など、より細かい制御をしたい場合は
`tests/test_utils.py` のヘルパー（`start_battle` / `run_move` / `run_switch` 等）が便利。
これはテスト用のヘルパーだが、プロジェクトルートを `sys.path` に含めれば通常のスクリプトからも使える。
詳細な使い方は [tests/CLAUDE.md](tests/CLAUDE.md) を参照:

```python
# プロジェクトルートから実行する想定（tests/ が import できる状態）
from jpoke import Pokemon
from tests import test_utils as t

battle = t.start_battle(
    team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["でんこうせっか"])],
    team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    accuracy=100,  # 命中率を固定して再現性を上げる
)
t.run_move(battle, atk_idx=0, move_idx=0)
```

## アーキテクチャ

イベント駆動モデルを採用している:

1. バトルロジックが `Event` を発火する
2. `EventManager` が登録済み `Handler` を優先度順に呼び出す
3. 各 `Handler` は `HandlerReturn(value, stop_event)` を返す
4. ハンドラの登録は `data/ability.py`, `data/item.py`, `data/move.py` などで行う

| クラス／モジュール | 役割 |
|---|---|
| `core/battle.py` `Battle` | バトル全体の状態管理・ターン進行 |
| `core/turn_controller.py` | ターン順・行動順の制御 |
| `core/event_manager.py` | イベント発火・ハンドラ呼び出し |
| `core/handler.py` `Handler` | ハンドラ定義（subject, subject_spec, 関数） |
| `core/context.py` `BaseContext` / `EventContext` / `AttackContext` | ハンドラに渡すイベントコンテキスト（攻撃フローは `AttackContext`、それ以外は `EventContext`） |
| `model/` | `Pokemon`, `Move`, `Field` などのモデル |
| `data/` | `ability.py`, `move.py`, `item.py` など — 各エンティティのデータ定義とハンドラ登録 |
| `handlers/` | `ability.py`, `ability_paradox.py`, `ailment.py`, `field.py`, `item.py`, `lethal.py`, `move.py`, `move_attack.py`, `move_status.py`, `volatile.py` など — ハンドラ実装 |
| `enums/` | `Event`, `Command`, `Interrupt`, `LogCode` |
| `types/` | `Stat`, `Type`, `AilmentName`, `VolatileName` など Literal 型の定義 |

技データ（`data/move.py`）は五十音の行ごとに `data/moves/move_<行>.py` へ分割されている
（`data/move.py` はそれらを統合する薄いファイル）。

## ドキュメント

| ディレクトリ | 役割 |
|---|---|
| `docs/spec/` | 技・アイテム・特性・場の効果の挙動仕様 |
| `docs/plan/` | 実行計画と優先順位 |
| `docs/progress/` | カテゴリ別の実装追跡（`ability.md`, `item.md`, `move.md` 等） |
| `docs/tests/` | テスト一覧（`scripts/generate_test_list.py` で生成） |

## 実装状況

`docs/progress/*.md` に基づく件数（データ定義済みの実数、内部用の空エントリ等を除く）:

| カテゴリ | 件数 |
|---|---|
| 特性（ability） | 310 |
| アイテム（item） | 247 |
| 技（move） | 733 |
| 揮発性状態（volatile） | 66 |
| 状態異常（ailment） | 7 |
| 場の効果（field: 天候・地形・グローバル・サイド） | 31 |

最新の詳細は `docs/progress/` 配下の各ファイルを参照。

## テストの実行

```bash
# 全テスト
python -m pytest tests/ -v

# カテゴリ別
python -m pytest tests/abilities/ -v
python -m pytest tests/items/ -v
python -m pytest tests/moves_attack/ -v
python -m pytest tests/moves_status/ -v
python -m pytest tests/volatiles/ -v

# 特定ファイル
python -m pytest tests/abilities/test_ability_ka.py -v

# 特定テスト関数（日本語関数名も可）
python -m pytest tests/abilities/ -k "ARシステム" -v

# カバレッジ付き
python -m pytest tests/ -q --cov=jpoke --cov-report=term
```

テストは `tests/` 直下（`test_ailment.py`, `test_copy.py`, `test_damage.py`, `test_field.py`,
`test_lethal.py` など）とサブディレクトリ（`abilities/`, `items/`, `moves_attack/`,
`moves_status/`, `volatiles/`）に分かれている。`tests/test_utils.py` はテストヘルパー（テスト対象外）。

## 開発ツール

```bash
# lint
python -m ruff check src/ tests/ scripts/

# 型チェック（src/jpoke/core のみを対象に段階導入中）
python -m mypy

# 五十音順の維持・データ整合性チェック（--check は変更せず確認のみ）
python scripts/sort_handlers.py --check
python scripts/sort_data/sort_abilities.py --check
python scripts/sort_data/sort_items.py --check
python scripts/sort_data/sort_moves.py --check
python scripts/sort_tests.py --check tests/**/test_*.py
```

CI（`.github/workflows/test.yml`）で push/PR ごとに Windows + Linux × Python 3.10/3.12 のマトリクスで
テスト・lint・型チェックを実行する。`.github/workflows/nightly-fuzz.yml` が毎日 `scripts/fuzz_battle.py`
を random / tree_search の両プレイヤーモデル（`--player`）で実行し、回帰シードを検出する。`.pre-commit-config.yaml` を使うと
コミット前にこれらのチェック（の一部）をローカルで実行できる。

## ライセンス

MIT License
