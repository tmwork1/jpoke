# jpoke

ポケモンチャンピオンズのシングルバトルを高速に再現する Python ライブラリ。

特性・アイテム・技・状態異常・場の効果などの相互作用をイベント駆動アーキテクチャで再現し、発動タイミングや優先度まで含めてシミュレートする。
ダメージ計算・致死率計算機能も内蔵しており、対戦シミュレータとダメージ計算ツールの両方の基盤として使用可能。

- **スタンドアロン** - `pip install jpoke` するだけでネットワーク接続なしに動作する。
- **高いカバレッジ** - ほとんどの特性・アイテム・技を実装済み。[実装状況](#実装状況)を参照。
- **高速** - 1秒間に100ターン以上計算可能。[計算速度](#計算速度)を参照。
- **木探索** - ゲーム木の部分探索をサポート。すぐに使える `MinimaxPlayer` なども同梱。
- **致死率計算** - 相手を倒すのに必要な攻撃回数と致死率を計算できる。アイテムや技の効果なども考慮可能。
- **多用途** - 対戦研究・AI開発・ダメージ計算ツール開発などの用途を想定。

**ドキュメントサイト**: <https://tmwork1.github.io/jpoke/>

> 本プロジェクトは株式会社ポケモン・任天堂・株式会社ゲームフリークとは無関係の非公式プロジェクトです。
>
> This is an unofficial, fan-made project and is not affiliated with, endorsed by, or sponsored by Nintendo, Game Freak, or The Pokémon Company.

## 対象範囲

- シングルバトルのみ
- 特性・アイテム・技などの仕様はポケモンチャンピオンズに準拠

このプロジェクトの規約・アーキテクチャの詳細は [CLAUDE.md](https://github.com/tmwork1/jpoke/blob/main/CLAUDE.md) を参照。

## インストール

```bash
pip install jpoke
```

`requires-python = ">=3.11"`

変更履歴は [CHANGELOG.md](https://github.com/tmwork1/jpoke/blob/main/CHANGELOG.md) を参照。

## クイックスタート

```python
from jpoke import Battle, Player

player1 = Player("Player 1")
player1.add_pokemon("ピカチュウ", moves=["でんこうせっか"])

player2 = Player("Player 2")
player2.add_pokemon("フシギダネ", moves=["たいあたり"])

battle = Battle(player1, player2)

battle.start()
while battle.can_continue(max_turns=100):
    battle.step()

battle.print_logs("all")
```

ステップごとに学びたい場合は、ターン進行を手動で覗く・自分の `Player` を実装するところまで
順を追う [チュートリアル](https://tmwork1.github.io/jpoke/getting_started/) を参照。
戦術研究・AI開発・ダメージ計算ツール開発それぞれのユースケース別に動かして学べるサンプルは
[examples/](https://github.com/tmwork1/jpoke/blob/main/examples/README.md) に用意している
（各 `.ipynb` は Google Colab でそのまま開いて実行できる）。

## ドキュメント

利用者向けドキュメントは <https://tmwork1.github.io/jpoke/> にまとめている
（この README・チュートリアル・早見表・APIリファレンス（自動生成）・
サンプル・変更履歴・貢献ガイド）。

| ディレクトリ | 役割 |
|---|---|
| `docs/getting_started.md` | 導入チュートリアル（インストール〜最初の対戦〜自作Player） |
| `docs/quick_reference.md` | `Battle` / `Player` / `Pokemon` 等クラス別の公開API早見表 |
| `.internal/spec/` | 技・アイテム・特性・場の効果の挙動仕様 |
| `.internal/plan/` | 実行計画と優先順位 |
| `.internal/progress/` | カテゴリ別の実装追跡（`ability.md`, `item.md`, `move.md` 等） |
| `.internal/tests/logs/` | `.loop` 系フローが保存するテスト実行ログ |

開発への貢献方法は [CONTRIBUTING.md](https://github.com/tmwork1/jpoke/blob/main/CONTRIBUTING.md)、
脆弱性の報告方法は [SECURITY.md](https://github.com/tmwork1/jpoke/blob/main/SECURITY.md) を参照。

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
| `players/` | `Player` の派生方策実装（`RandomPlayer`, `MaxDamagePlayer`, `CLIPlayer`, 木探索の基底 `TreeSearchPlayer` とその実装 `MinimaxPlayer` など） |
| `enums/` | `Event`, `Command`, `Interrupt`, `LogCode` |
| `types/` | `Stat`, `Type`, `AilmentName`, `VolatileName` など Literal 型の定義 |

技データ（`data/move.py`）は五十音の行ごとに `data/moves/move_<行>.py` へ分割されている
（`data/move.py` はそれらを統合する薄いファイル）。

## 実装状況

`.internal/progress/*.md` に基づく件数（実装済み件数 / 全エントリ数、「ダブル専用」「効果なし」を除く）:

| カテゴリ | 件数 |
|---|---|
| 特性（ability） | 290 / 291 |
| アイテム（item） | 154 / 154 |
| 技（move） | 705 / 710 |
| 揮発性状態（volatile） | 50 / 54 |
| 状態異常（ailment） | 7 / 7 |
| 場の効果（field: 天候・地形・グローバル・サイド） | 28 / 28 |

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
- **ゲームデータ**（`src/jpoke/data/`, `.internal/wiki/`, `.internal/spec/` 配下の技・特性・アイテム等の数値・効果テキスト）: CC BY-NC-SA 4.0（[LICENSE-DATA](https://github.com/tmwork1/jpoke/blob/main/LICENSE-DATA)）。出典は [ポケモンWiki](https://wiki.pokemonwiki.com/)（CC BY-NC-SA 3.0）
