# jpoke

ポケモンチャンピオンズ準拠のシングル対戦シミュレーション環境とダメージ計算ロジックを提供する
Python ライブラリ。イベント駆動でポケモンの技・特性・アイテム・状態異常・場の効果などを再現している。戦術研究・AI 開発・ダメージ計算ツール開発などの用途を想定している。

**ドキュメントサイト**: <https://tmwork1.github.io/jpoke/>（このREADME・APIリファレンス・サンプル・変更履歴をまとめて閲覧できる）

> 本プロジェクトは株式会社ポケモン・任天堂・株式会社ゲームフリークとは無関係の非公式（fan-made）
> プロジェクトです。
>
> This is an unofficial, fan-made project and is not affiliated with, endorsed by, or sponsored by
> Nintendo, Game Freak, or The Pokémon Company.

## 対象範囲

- **対象はポケモンチャンピオンズのシングルバトルのみ**（ダブルバトル等は対象外）
- 技・特性・アイテム・ポケモンなどの仕様ソースは **第9世代（スカーレット・バイオレット）** を基本とし、
  ポケモンチャンピオンズ側でルールが異なる場合はそちらを優先する
- 第9世代で実装されていない技・アイテム・特性・ポケモンなどは実装しない
- ローカルでのシミュレーション・分析を目的としたライブラリであり、公式対戦での自動化（bot 運用）は
  目的としていない。乱数調整もサポート対象外

このプロジェクトの規約・アーキテクチャの詳細は
[CLAUDE.md](https://github.com/tmwork1/jpoke/blob/main/CLAUDE.md) を参照（この README の対象範囲の
定義を正とし、CLAUDE.md 側はこの記述を参照する）。

## インストール

```bash
pip install jpoke
```

`requires-python = ">=3.11"`。型アノテーションは Python 3.10+ の構文（`X | Y`, `list[X]`）を使用する
（関数の引数・戻り値の型を書く目印であり、jpoke を利用するだけなら読み飛ばしてよい）。

バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠するが、0.x 系の間は
minor バージョンの更新（例: 0.1.0 → 0.2.0）でも破壊的変更が入る場合がある。変更履歴は
[CHANGELOG.md](https://github.com/tmwork1/jpoke/blob/main/CHANGELOG.md) を参照。

## クイックスタート

もっとも低レベルな API（`Battle` / `Player`）だけを使った最小例:

```python
from jpoke import Battle, Player

player1 = Player("Player 1")
player1.add_pokemon("ピカチュウ", moves=["でんこうせっか"])
player2 = Player("Player 2")
player2.add_pokemon("フシギダネ", moves=["たいあたり"])

# n_selected: 省略時は min(3, チームの手持ち数) が自動設定される（ここでは1）
battle = Battle(player1, player2)
battle.start()

while battle.can_continue(max_turns=100):
    # commands=None の場合は各 Player.choose_command() が使われる
    # （デフォルト実装は利用可能な最初のコマンドを選ぶだけの単純なプレイヤー）
    battle.step()

winner = battle.winner
print(winner.username if winner else "引き分け")   # 勝者の名前（決着しなかった場合はNone）
battle.print_logs()                 # このターンのログを表示
```

戦術研究・AI開発・ダメージ計算ツール開発それぞれのユースケース別に動かして学べるサンプルを
[examples/](https://github.com/tmwork1/jpoke/blob/main/examples/README.md) に用意している。
各 `.ipynb` は Google Colab でそのまま開いて実行できる（ローカルでは `pip install jpoke` 後に
Jupyter で開く）。

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

利用者向けドキュメントは <https://tmwork1.github.io/jpoke/> にまとめている
（この README・APIリファレンス・自動生成のクラスリファレンス・サンプル・変更履歴・貢献ガイド）。

| ディレクトリ | 役割 |
|---|---|
| `docs/api/` | 利用者向け公開APIリファレンス（`Battle` / `Player` / `Pokemon`） |
| `.internal/spec/` | 技・アイテム・特性・場の効果の挙動仕様 |
| `.internal/plan/` | 実行計画と優先順位 |
| `.internal/progress/` | カテゴリ別の実装追跡（`ability.md`, `item.md`, `move.md` 等） |
| `.internal/tests/logs/` | `.loop` 系フローが保存するテスト実行ログ |

開発への貢献方法は [CONTRIBUTING.md](https://github.com/tmwork1/jpoke/blob/main/CONTRIBUTING.md)、
脆弱性の報告方法は [SECURITY.md](https://github.com/tmwork1/jpoke/blob/main/SECURITY.md) を参照。

`jpoke.testing` — `pip install jpoke` だけで使える、任意ターンでのピンポイントな状態検証・技の
実行などを行うテストヘルパー集（`start_battle` / `run_move` / `run_switch` 等）。詳細は後述の
「テストヘルパーを使った検証」を参照。

## 実装状況

`.internal/progress/*.md` に基づく件数（データ定義済みの実数、内部用の空エントリ等を除く）:

| カテゴリ | 件数 |
|---|---|
| 特性（ability） | 310 |
| アイテム（item） | 247 |
| 技（move） | 733 |
| 揮発性状態（volatile） | 66 |
| 状態異常（ailment） | 7 |
| 場の効果（field: 天候・地形・グローバル・サイド） | 31 |

最新の詳細は `.internal/progress/` 配下の各ファイルを参照。

## 計算速度

種族・特性・アイテム・技などが完全ランダムな3vs3全選出バトルを300戦繰り返し、`Battle.step()`
（1ターン進行）1回あたりの所要時間を計測（[examples/99_dev/01_step_time_benchmark.py](https://github.com/tmwork1/jpoke/blob/main/examples/99_dev/01_step_time_benchmark.py)）:

| 指標 | 値 |
|---|---|
| 1step所要時間 | 3.8 ms ± 2.4 ms（mean ± σ） |
| turns/sec | 約260 |
| battles/sec | 約15 |

Windows 11 / Python 3.14 / Intel64（手元環境）での計測値。計算コストは選出中のポケモンの状態
（場の効果・技構成など）に大きく左右されるため、σが大きい（分布の幅が広い）点に注意。

```bash
python examples/99_dev/01_step_time_benchmark.py
```

## テストヘルパーを使った検証

任意ターンでのピンポイントな状態検証や技の実行など、クイックスタートより細かい制御をしたい場合は
`jpoke.testing` のヘルパー（`start_battle` / `run_move` / `run_switch` 等）が便利。
`pip install jpoke` だけで（リポジトリを clone せずに）使える:

```python
from jpoke import Pokemon
from jpoke import testing as t

battle = t.start_battle(
    team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["でんこうせっか"])],
    team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    accuracy=100,  # 命中率を固定して再現性を上げる
)
t.run_move(battle, player_idx=0, move_idx=0)
```

`fix_damage` / `fix_random` は対戦オブジェクトの内部属性を直接差し替えるモンキーパッチのため、
テスト・デバッグ専用であり本番の対戦進行では使わないこと（本来の実装を無視して値を強制的に
上書きするため、通常のゲームルールでは起こらない状態になり得る）。

リポジトリ内部のテストコード（`tests/`）は同じ実体を `tests/test_utils.py` 経由（後方互換の
薄い再エクスポート層）で使っている。詳細な使い方は
[tests/CLAUDE.md](https://github.com/tmwork1/jpoke/blob/main/tests/CLAUDE.md) も参照。

## 開発への貢献

ソースを直接編集する場合の環境セットアップ・コード規約は
[CONTRIBUTING.md](https://github.com/tmwork1/jpoke/blob/main/CONTRIBUTING.md) を参照。
テストの実行方法もそちらにまとめている。

CIがpush/PRごとに自動でテスト・lint・型チェックを実行している（マトリクス構成の詳細は
CONTRIBUTING.md参照）。`.github/workflows/nightly-fuzz.yml` が毎日
`scripts/fuzz/fuzz_battle.py` を random / tree_search の両プレイヤーモデルで実行し、
回帰シードを検出している。

## ライセンス

本プロジェクトはコードとゲームデータで異なるライセンスを適用する二層構成になっている。

- **コード**（`src/jpoke/` 配下の実装ロジックなど）: MIT License（[LICENSE](https://github.com/tmwork1/jpoke/blob/main/LICENSE)）
- **ゲームデータ**（`src/jpoke/data/`, `.internal/wiki/`, `.internal/spec/` 配下の技・特性・アイテム等の数値・効果テキスト）:
  CC BY-NC-SA 4.0（[LICENSE-DATA](https://github.com/tmwork1/jpoke/blob/main/LICENSE-DATA)）。出典は
  [ポケモンWiki](https://wiki.pokemonwiki.com/)（CC BY-NC-SA 3.0）
