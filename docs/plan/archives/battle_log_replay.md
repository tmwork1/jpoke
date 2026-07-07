# 計画書: 対戦ログ出力・リプレイ再生機能

## 目的

対戦の一部始終を記録し、後から**完全に同じ対戦を再生**できるようにする。

- 「チーム構成（両者のパーティ）＋初期シード＋入力されたコマンド列」があれば対戦を再現できる、
  という想定を現状の実装に照らして検証する。
- 検証の結果を踏まえ、記録用データ構造・記録フック・リプレイ再生エンジンを設計する。

## 前提の検証: 本当に「チーム＋シード＋コマンド列」で再現できるか

結論: **できる。ただし「コマンド列」には行動コマンドだけでなく選出・瀕死交代などの
決定も含める必要がある**。根拠は以下の通り。

### 乱数は `battle.random` 一箇所に集約されている

`src/jpoke/core/battle.py:147` `self.random = Random(self.seed)` が対戦中の唯一の乱数源。
ダメージ乱数・命中判定・急所判定・追加効果確率・状態異常のカウント・素早さ同速タイブレークなど、
`handlers/*.py` や `core/*_manager.py` の乱数利用は例外なく `battle.random.xxx()` 経由
（`grep '\.random\.' src/jpoke` で50箇所以上、すべて `self.random` / `battle.random`）。
`scripts/random_1on1.py` の `RandomPlayer` のようにモジュール本来の `random.choice` を使う
プレイヤー方策も存在するが、後述の通りリプレイは方策関数を呼び直さず記録済みコマンドを
そのまま流し込むため、方策側がどの乱数源を使っていたかは再現性に影響しない。

### `Battle.copy()` は乱数・ログを独立に複製する

`Battle._EXTRA_DEEPCOPY_KEYS`（`battle.py:195`）に `random` と `event_logger` が含まれており、
`deepcopy(self)` の度に独立したコピーが作られる。`copy(reseed=True)` を使う木探索
（`TreeSearchPlayer`, `players/tree_search_player.py`）や `resolve_command()` 内の
`build_observation()` によるプレイヤー方策への読み取り専用スナップショットは、
実際の対戦本線 (`battle.random` の消費・`event_logger` への追記) を一切汚さない。
→ 「本線の乱数消費は `battle.step()` による実進行でのみ起こる」という前提が成立する。

### プレイヤーの決定点は3種類、呼び出し口は2箇所しかない

`grep 'choose_command(\|resolve_command(\|choose_selection('` の結果、決定点は次の3つで全て。

| 決定 | 呼び出し元 | 頻度 |
|---|---|---|
| 選出 (`choose_selection`) | `turn_controller.py:100` `_run_selection()` | 対戦開始時に1回のみ |
| 行動コマンド (`choose_command`, phase="action") | `battle.py:532` `step()` 内、`commands is None` の場合のみ | 新しいターンごとに1回 |
| 交代コマンド (`choose_command`, phase="switch") | `switch_manager.py:169` （瀕死交代・だっしゅつパック等の割り込み中） | 瀕死・割り込み交代の度 |

いずれも `CommandManager.resolve_command()`（`command_manager.py:152`）を経由するが、
**行動コマンドは `battle.step(commands={...})` で外部から直接渡されるケースがあり、
その場合は `resolve_command()` を経由しない**（`battle.py:530-535`）。
そのためリプレイ用の記録フックは「`resolve_command()` 単体」ではなく
「`Battle.step()` が確定させた行動コマンド」＋「`resolve_command(\"switch\", ...)` が
確定させた交代コマンド」の2箇所で行う必要がある（設計の节で詳述）。

### 選出は「記録」しなくても取得できる

`PlayerState.selected_indexes`（`player_state.py:19`）は対戦開始時に設定されたら
対戦終了まで変更されない。行動コマンドのように pop されて消費されることもないため、
専用の記録フックは不要で、リプレイデータを組み立てる時点で
`battle.player_states[player].selected_indexes` を直接読めばよい。

### チームは既に `Pokemon.to_dict()` でシリアライズ可能

`model/pokemon.py:872` に `to_dict()` が既にあり、`name / gender / level / nature /
ability / item / moves / indiv / effort / tera_type` を辞書化できる（現状どこからも
呼ばれていない）。ただし対応する `from_dict()`（辞書から `Pokemon` を再構築する）は存在しない。
また `to_dict()` は「今の状態」を返すため、対戦中に特性が変化（トレース等）したり
アイテムを消費した後に呼ぶと初期状態と食い違う。**対戦開始前（`Battle.__init__` 時点）に
1回だけスナップショットを取る**必要がある。

## 設計

### 1. `Pokemon.from_dict()` の追加（`src/jpoke/model/pokemon.py`）

`to_dict()` の直後に追加する。

```python
@classmethod
def from_dict(cls, data: dict) -> "Pokemon":
    """to_dict() が返す辞書からポケモンを再構築する。"""
    mon = cls(
        data["name"],
        gender=data["gender"],
        nature=data["nature"],
        level=data["level"],
        ability_name=data["ability"],
        item_name=data["item"],
        move_names=data["moves"],
        tera_type=data["tera_type"],
    )
    mon.indiv = list(data["indiv"])
    mon.effort = list(data["effort"])
    return mon
```

`indiv` / `effort` の setter（`pokemon.py:499`, `pokemon.py:521`）は代入時に
`update_stats()` を呼ぶため、実数値も正しく再計算される。

### 2. チームスナップショットの取得タイミング（`src/jpoke/core/battle.py`）

`Battle.__init__` で `_player_states` を構築した直後（`battle.py:158-159` の直後）に、
対戦開始前の素のチームをスナップショットする。

```python
self._team_snapshot: list[list[dict]] = [
    [mon.to_dict() for mon in state.team] for state in self._player_states
]
```

`PlayerState.__init__` は `self.team = deepcopy(player.team)` なので、この時点では
まだ対戦の影響を一切受けていない。`_team_snapshot` は不変なので
`_EXTRA_DEEPCOPY_KEYS` に追加する必要はない（`fast_copy` によるシャローコピーで
参照共有して問題ない。`option` / `test_option` と同じ扱い）。

### 3. コマンド記録用のデータ構造（新規 `src/jpoke/core/replay.py`）

```python
from dataclasses import dataclass, field
from jpoke.types import BattlePhase
from jpoke.enums import Command


@dataclass(frozen=True)
class RecordedCommand:
    turn: int
    player_idx: int
    phase: BattlePhase  # "action" | "switch"
    command: Command

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "player_idx": self.player_idx,
            "phase": self.phase,
            "command": self.command.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecordedCommand":
        return cls(
            turn=data["turn"],
            player_idx=data["player_idx"],
            phase=data["phase"],
            command=Command[data["command"]],
        )


@dataclass
class BattleReplayData:
    """対戦を完全に再現するために必要な情報一式。"""
    seed: int
    n_selected: int
    battle_option: dict          # BattleOption の各フィールド
    teams: tuple[list[dict], list[dict]]       # Pokemon.to_dict() の対戦開始前スナップショット
    selections: tuple[list[int], list[int]]
    commands: list[RecordedCommand] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "n_selected": self.n_selected,
            "battle_option": self.battle_option,
            "teams": list(self.teams),
            "selections": list(self.selections),
            "commands": [c.to_dict() for c in self.commands],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BattleReplayData":
        return cls(
            seed=data["seed"],
            n_selected=data["n_selected"],
            battle_option=data["battle_option"],
            teams=tuple(data["teams"]),
            selections=tuple(data["selections"]),
            commands=[RecordedCommand.from_dict(c) for c in data["commands"]],
        )
```

`BattlePhase` に `"selection"` も含まれるが、選出は上記の通り記録対象外
（`resolve_command()` を経由しないため、この型に含まれていても実際に記録されるのは
`"action"` / `"switch"` のみ）。

### 4. 記録フック

常時ON（`event_logger` と同じ扱い）。`Battle.__init__` に追加:

```python
self.command_log: list[RecordedCommand] = []
```

`_EXTRA_DEEPCOPY_KEYS`（`battle.py:195`）に `"command_log"` を追加し、
観測・木探索用コピーが独立したログを持つようにする（本線を汚さない）。

**(a) 行動コマンド** — `Battle.step()`（`battle.py:524-544`）、
`turn_controller.step(commands)` を呼ぶ直前に追加:

```python
def step(self, commands: dict[Player, Command] | None = None):
    if self.is_new_turn() and commands is None:
        commands = self.resolve_command("action")
    else:
        ...
    if not commands:
        raise InvalidCommandError("No commands provided for step().")

    for player, command in commands.items():
        self.command_log.append(RecordedCommand(
            turn=self.turn + (1 if self.is_new_turn() else 0),
            player_idx=self.players.index(player),
            phase="action",
            command=command,
        ))

    self.turn_controller.step(commands)
```

外部から `battle.step(commands={...})` を直接呼ぶ経路と、
`commands=None` で方策関数に解決させる経路の**両方**をここで一元的に捕捉する
（`resolve_command()` 側だけをフックすると外部供給コマンドを取りこぼすため）。
`turn` は `_begin_turn()` でインクリメントされる前なので `+1` 補正が必要
（`turn_controller.py:137-139` 参照）。

**(b) 交代コマンド（瀕死交代等）** — `CommandManager.resolve_command()`
（`command_manager.py:152-179`）、`phase == "switch"` の場合のみ記録
（`"action"` は (a) で既に記録済みのため二重記録を避ける）:

```python
commands: dict[Player, Command] = {}
for ply in players:
    sim = battle.build_observation(ply)
    commands[ply] = ply.choose_command(sim)
    if phase == "switch":
        battle.command_log.append(RecordedCommand(
            turn=battle.turn,
            player_idx=battle.players.index(ply),
            phase="switch",
            command=commands[ply],
        ))
```

### 5. リプレイデータの組み立て（`Battle` に委譲メソッドを追加）

```python
def build_replay_data(self) -> BattleReplayData:
    from dataclasses import asdict
    return BattleReplayData(
        seed=self.seed,
        n_selected=self.n_selected,
        battle_option=asdict(self.option),
        teams=(self._team_snapshot[0], self._team_snapshot[1]),
        selections=(
            self.player_states[self.players[0]].selected_indexes,
            self.player_states[self.players[1]].selected_indexes,
        ),
        commands=list(self.command_log),
    )
```

対戦の途中でも呼べる（選出とコマンド列はその時点までのもの）が、
典型的には `judge_winner()` が確定した後に呼ぶ。

### 6. `ReplayPlayer` とリプレイ実行ドライバ（新規 `src/jpoke/players/replay_player.py`）

```python
from collections import deque
from jpoke.core import Battle, Player
from jpoke.core.replay import BattleReplayData
from jpoke.enums import Command
from jpoke.model import Pokemon


class ReplayPlayer(Player):
    """記録済みの選出・コマンド列をそのまま再生するプレイヤー。

    方策判断を一切行わず、記録された決定を発生順に払い出すだけなので、
    盤面が記録時と完全に一致する限り常に正しい決定を返す。
    """

    def __init__(self, name: str, team_spec: list[dict],
                 selection: list[int], commands: list[Command]):
        super().__init__(name=name)
        self.team = [Pokemon.from_dict(spec) for spec in team_spec]
        self._selection = selection
        self._queue: deque[Command] = deque(commands)

    def choose_selection(self, battle: Battle) -> list[int]:
        return self._selection

    def choose_command(self, battle: Battle) -> Command:
        if not self._queue:
            raise RuntimeError("リプレイデータのコマンドが不足しています。記録漏れの可能性があります。")
        return self._queue.popleft()


def replay_battle(data: BattleReplayData, max_turns: int = 300) -> Battle:
    """記録済みデータから対戦を再現する。

    Returns:
        再生し終えた Battle インスタンス（event_logger 等で経過を確認できる）。
    """
    commands_by_player = ([], [])
    for rec in data.commands:
        commands_by_player[rec.player_idx].append(rec.command)

    players = (
        ReplayPlayer("Player 1", data.teams[0], data.selections[0], commands_by_player[0]),
        ReplayPlayer("Player 2", data.teams[1], data.selections[1], commands_by_player[1]),
    )
    battle = Battle(players, n_selected=data.n_selected, seed=data.seed, **data.battle_option)
    battle.start()

    while battle.judge_winner() is None and battle.turn < max_turns:
        battle.step()

    return battle
```

`commands_by_player` は `RecordedCommand.player_idx` 順に詰め直したFIFOキュー。
`phase`（"action"/"switch"）で区別する必要はない —
`resolve_command()` は常にゲームエンジンの実行順で `choose_command()` を呼ぶため、
記録時と同じ順序で払い出せば呼び出し側のフェーズと自動的に一致する
（記録側で `turn`/`phase` を保持しているのは主に人間可読なログ・デバッグ用途）。

## 実装順序

1. `src/jpoke/model/pokemon.py`: `Pokemon.from_dict()` を追加
2. `src/jpoke/core/replay.py`（新規）: `RecordedCommand` / `BattleReplayData`
3. `src/jpoke/core/battle.py`:
   - `_team_snapshot` の取得（`__init__`）
   - `command_log` の初期化・`_EXTRA_DEEPCOPY_KEYS` への追加
   - `step()` への行動コマンド記録の追加
   - `build_replay_data()` の追加
4. `src/jpoke/core/command_manager.py`: `resolve_command()` の "switch" フェーズ記録の追加
5. `src/jpoke/players/replay_player.py`（新規）: `ReplayPlayer` / `replay_battle()`
6. `python -m pytest tests/ -v` で既存テストが通ることを確認
   （記録は既存フローに追記するだけで分岐を増やさないため、既存動作への影響はないはず）

## テスト観点

- `Pokemon.to_dict()` → `from_dict()` の往復で元と同じステータス・技・特性・アイテム・
  テラスタイプになること
- スクリプト化されたコマンド列（`test_utils.reserve_command` 相当）で対戦を1本走らせ、
  `build_replay_data()` の結果を `replay_battle()` に渡すと、
  **同じ勝者・同じ最終HP・同じ `event_logger.logs`（ターン/プレイヤー/LogCode/payload全て）**
  になること（往復の完全性を保証する中心的なテスト）
- 瀕死による強制交代（`run_faint_switch`）が発生する対戦で、"switch" フェーズの
  コマンドも過不足なく記録・再生されること
- だっしゅつパック等、同ターン中に複数回の割り込み交代が起きるケースでも
  コマンド列の順序がずれないこと
- テラスタル/メガシンカコマンド（`TERASTAL_n` / `MEGAEVOL_n`）を含むターンが
  正しく再生されること
- `ReplayPlayer` にコマンド不足がある壊れたリプレイデータを渡すと
  明示的な例外（`RuntimeError`）で失敗すること（サイレントに `choose_command` の
  既定実装にフォールバックしない）

## 備考

- **`test_option`（`accuracy` / `trigger_ailment` / `trigger_volatile` / `secondary_chance`）
  は非対応**。これらはテストコード専用の「乱数判定を都度上書きする」フックであり、
  `battle.random` の消費をスキップして固定値を返すため、記録・再生の対象に含めていない。
  もし実対戦中にこれらを使うツール（fuzzer等）をリプレイ対象にしたい場合は、
  `BattleReplayData` に `test_option: dict` を追加し `replay_battle()` で
  `battle.test_option = TestOption(**data.test_option)` のように適用する拡張が必要。
  現時点ではスコープ外とする。
- ポケモンデータテーブル（`POKEDEX` / `ABILITIES` / `ITEMS` / `MOVES`）が記録時と
  再生時で異なるバージョンだと再現できない。バージョン情報の埋め込みは本計画では扱わない。
- `max_turns` は無限ループ防止の安全装置（既存スクリプト `scripts/random_1on1.py` の
  `max_turns` と同じ考え方）。決着がつかず上限に到達した場合は `judge_winner() is None`
  のまま `battle` を返すため、呼び出し側で判定する。
- ログの人間可読出力（`Battle.get_log_lines()` / `print_logs()`）は既存のまま変更不要。
  `BattleReplayData` は「再生に必要な最小限の入力」、`event_logger` は「見るためのログ」
  という役割分担になる。両方をまとめて1ファイルに保存したい場合は、
  `build_replay_data().to_dict()` と `{turn: [log.to_dict() for log in ...]}`
  （`EventLog.to_dict()`、`event_logger.py:144`）を並べて保存すればよい
  （リプレイ後に両者を突き合わせれば記録の正しさをセルフチェックできる）。
