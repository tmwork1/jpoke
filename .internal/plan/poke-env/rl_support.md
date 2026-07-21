# 実装計画: RL支援ヘルパー（外部ライブラリ非依存）

更新日: 2026-07-21

## 背景

`.internal/poke-env/rl_features_analysis.md` の調査により、poke-env の主目的が
「強化学習(RL)ボット訓練用インターフェースの提供」であり、Gymnasium/PettingZoo準拠の
`PokeEnv`（行動空間・観測空間・報酬シェーピングヘルパー・行動マスク）を持つことを確認した。
jpoke にはこれに相当する機能がなく、`build_observation()`（部分観測）・`Command` Enum
（固定順の行動表現）・`Player.battle_against()`（一括対戦）など断片的な下地はあるものの、
RLを始めるための一貫したAPIは未整備。

**ユーザー方針（2026-07-21確認）: `gymnasium`/`pettingzoo` 等の外部ライブラリは
`dependencies` に追加しない。** その代わり、RLを始めるのに便利な機能（行動の列挙・
合法手マスク・観測ベクトル化の参考実装・報酬シェーピングヘルパー・簡易な学習ループ）を
素の Python だけで提供する。gymnasium 実利用者は本モジュールの戻り値をそのまま
`gymnasium.Env` の各メソッドの戻り値に流用できる設計とする（アダプタは利用者側の数行で済む）。

## スコープ

- 新規 `src/jpoke/rl.py`（単一ファイル。`types/poke_env.py` 程度の規模を想定）
- `pyproject.toml` の変更は不要（依存追加なし）
- 既存の `core/battle.py` / `core/player.py` / `enums/command.py` には手を入れない
  （RL支援機能は既存APIの上に乗る薄いレイヤーとして実装する）

## 前提として確認済みの既存API

- `Command`（`enums/command.py`）: `SWITCH_0..9` / `MOVE_0..9` / `TERASTAL_0..9` /
  `MEGAEVOL_0..9` / `GIGAMAX_0..9` / `ZMOVE_0..9` + 特殊コマンド `STRUGGLE`/`FORCED` の
  固定順 Enum。`Command.names()` で全件、`index`プロパティで枝番、`get_*_command(index)`で逆引き可能。
- `Battle.available_commands(player) -> list[Command]`（現在選択可能なコマンド列挙。
  観測者が相手の場合は `player_states[player].last_available_commands` にフォールバックする
  実装済みの分岐がある）
- `Battle.build_observation(observer) -> Battle`（部分観測コピー）
- `Battle.won(player) -> bool` / `lost(player) -> bool` / `finished`（poke-env互換、実装済み）
- `Battle.step(commands: dict[Player, Command] | None = None)`（`None`なら
  `resolve_command("action")` が各プレイヤーの `choose_command(build_observation(player))` を
  呼んで解決する）
- `Battle.play_out(max_turns)` / `Player.battle_against(*opponents, n_battles, on_battle_end, **battle_kwargs)`
  （実装済み。一括対戦・戦績集計）
- `Pokemon.hp_fraction` / `fainted` / `ailment.name`（状態異常の有無判定に使用）

## 設計上の論点（要ユーザー判断 or 実装時に確定させる）

### 論点1: ターン内の複数意思決定点（強制交代）の扱い

`command_manager.resolve_command()` は `phase="action"` の後、瀕死交代・だっしゅつパック等の
割り込みで `phase="switch"` の解決も必要になった場合、**呼び出し元に制御を戻さず
`player.choose_command(observation)` を内部で自動的に呼ぶ**（`battle.step()` 一回の中に
複数の意思決定が埋め込まれうる）。つまり「RL環境の1 `step(action)` 呼び出し = 1回の意思決定」
という前提が、瀕死交代が絡むターンでは素直に成立しない。

poke-env はこれを「別スレッド + asyncioキュー」で解決している（`_EnvPlayer` が
`choose_move()` 呼び出しのたびにキューで待機し、外側の同期 `env.step()` がキューに
行動を積んで解放する）。jpoke でも同じ発想を asyncio なしで（`threading.Thread` +
`queue.Queue`、いずれも標準ライブラリ）再現することは可能。

**この計画では、まず以下のA案で最小実装し、B案は将来の拡張候補として明記するに留める:**

- **A案（v1・採用）**: 強制交代（瀕死交代等）の意思決定は、学習対象の `Player` の
  既定 `choose_command()`（先頭のコマンドを選ぶ）にフォールバックさせる。RL行動として
  外部に公開するのは「通常のaction フェーズの意思決定」のみに限定する。制約として
  ドキュメントに明記する（瀕死交代の戦略性を学習させたい場合はB案が必要、という注記付き）。
- **B案（将来拡張）**: `threading.Thread` + `queue.Queue` で `Battle.play_out()` を
  バックグラウンドスレッドに移し、学習対象 `Player` の `choose_command()` を
  「キューから行動を受け取るまでブロックする」実装に差し替える。`RLBattleEnv.step(action)`
  はメインスレッドからキューに行動を積んで結果を待つ。poke-env の `_EnvPlayer`/`_AsyncQueue`
  と同型だが asyncio 不要（標準ライブラリの`threading`/`queue`のみで完結、外部依存は増えない）。

### 論点2: 観測の型

poke-env の `embed_battle()` は「利用者が実装する」設計（参考実装なし）。jpokeは
`build_observation()` で部分観測の `Battle` オブジェクトそのものは得られるが、数値配列への
変換は用途依存性が高い（種族・技をどうエンコードするか等）。本計画では**最小の参考実装
（HP割合・状態異常有無・ランク変化・場の状態の一部を並べただけの`list[float]`）を1つ添える**に
留め、「本格的な特徴量設計は利用者に委ねる」というスタンスは poke-env と揃える。

### 論点3: 対戦相手（opponent）の扱い

RLでは「学習対象1体 vs 固定/ランダムな対戦相手」という単一エージェント構成がまず必要
（poke-env の `SingleAgentWrapper` に相当）。対戦相手は既存の `Player` サブクラス
（`RandomPlayer` / `MaxDamagePlayer` / `TreeSearchPlayer` 等）をそのまま使う
（新規クラスを作らない）。自己対戦（マルチエージェント、PettingZoo相当）は本計画のスコープ外。

## モジュール設計: `src/jpoke/rl.py`

```python
"""強化学習を始めるための補助機能。

外部ライブラリ（gymnasium 等）には一切依存しない。reset()/step() など
gymnasium と同じ形のメソッド名を持つが、返り値は list/dict/float/bool のみで
構成する。gymnasium.Env を実際に使いたい場合は、本モジュールの戻り値を
そのまま各メソッドの戻り値に使えばよい。
"""
from __future__ import annotations
from dataclasses import dataclass

from jpoke.core.battle import Battle
from jpoke.core.player import Player
from jpoke.enums.command import Command

# 実際の行動として選ばれることのない特殊コマンドは行動空間から除外する
_EXCLUDED = (Command.STRUGGLE, Command.FORCED)
ACTION_COMMANDS: tuple[Command, ...] = tuple(c for c in Command if c not in _EXCLUDED)
ACTION_SPACE_SIZE: int = len(ACTION_COMMANDS)


def command_to_action(command: Command) -> int:
    """Command を RL 用の整数行動（0 〜 ACTION_SPACE_SIZE-1）に変換する。"""
    return ACTION_COMMANDS.index(command)


def action_to_command(action: int) -> Command:
    """RL 用の整数行動を Command に変換する（逆変換）。"""
    return ACTION_COMMANDS[action]


def get_action_mask(battle: Battle, player: Player) -> list[int]:
    """現在選択可能なコマンドを1、それ以外を0とする長さ ACTION_SPACE_SIZE のマスクを返す。"""
    available = set(battle.available_commands(player))
    return [1 if c in available else 0 for c in ACTION_COMMANDS]


@dataclass
class RewardWeights:
    """reward_computing_helper 相当の重み設定。既定は poke-env と同じ0（勝敗のみ1.0）。"""
    fainted: float = 0.0
    hp: float = 0.0
    status: float = 0.0
    victory: float = 1.0


def calc_state_value(battle: Battle, player: Player, weights: RewardWeights) -> float:
    """現在の対戦状態の評価値を計算する（差分報酬の元になる値。poke-envのreward_computing_helperと同じ考え方）。"""
    opponent = battle.opponent(player)
    value = 0.0
    for mon in battle.get_team(player):
        value += mon.hp_fraction * weights.hp
        if mon.fainted:
            value -= weights.fainted
        elif mon.ailment.name:
            value -= weights.status
    for mon in battle.get_team(opponent):
        value -= mon.hp_fraction * weights.hp
        if mon.fainted:
            value += weights.fainted
        elif mon.ailment.name:
            value += weights.status
    if battle.won(player):
        value += weights.victory
    elif battle.lost(player):
        value -= weights.victory
    return value


def embed_battle_basic(battle: Battle, player: Player) -> list[float]:
    """観測ベクトル化の最小参考実装（HP割合・瀕死・状態異常有無を並べただけ）。

    本格的な特徴量設計（技・タイプ相性・場の状態等）は利用者に委ねる。
    """
    ...


class RLBattleEnv:
    """gymnasiumのreset()/step()と同じ形の薄いラッパー。

    学習対象は `learner`（行動をRL側が決める）、対戦相手は `opponent`（既存の
    Playerサブクラスがそのまま行動を決める）。強制交代（瀕死交代等）は
    `opponent`/`learner`双方とも既定のchoose_command（先頭コマンド）に
    フォールバックする（論点1のA案。将来的にB案でRL行動として公開可能にする余地あり）。
    """

    def __init__(
        self,
        learner: Player,
        opponent: Player,
        *,
        reward_weights: RewardWeights | None = None,
        max_turns: int = 100,
        **battle_kwargs,
    ):
        self.learner = learner
        self.opponent = opponent
        self.reward_weights = reward_weights or RewardWeights()
        self.max_turns = max_turns
        self._battle_kwargs = battle_kwargs
        self.battle: Battle | None = None

    def reset(self) -> tuple[list[int], dict]:
        """新しい対戦を開始し、(action_mask, info) を返す。"""
        self.battle = Battle(self.learner, self.opponent, **self._battle_kwargs)
        self.battle.start()
        return get_action_mask(self.battle, self.learner), {}

    def step(self, action: int) -> tuple[list[int], float, bool, bool, dict]:
        """1手を実行し、(action_mask, reward, terminated, truncated, info) を返す。"""
        assert self.battle is not None
        command = action_to_command(action)
        # 論点1: switchフェーズの解決は resolve_command 内部で相手/学習対象双方の
        # 既定choose_commandに委ねられる（学習対象のフェーズがaction以外の場合の扱いは
        # 実装時に command_manager.validate_command / phase を見て確定させる）
        opponent_command = self.battle.resolve_command("action", self.opponent)[self.opponent]
        self.battle.step({self.learner: command, self.opponent: opponent_command})
        reward = calc_state_value(self.battle, self.learner, self.reward_weights)
        terminated = self.battle.finished
        truncated = (not terminated) and self.battle.turn >= self.max_turns
        return get_action_mask(self.battle, self.learner), reward, terminated, truncated, {}
```

- `RLBattleEnv.step()` の具体的な配線（`resolve_command`の呼び分け、フェーズが `"switch"` の
  ときの扱い）は実装時に `core/command_manager.py` / `core/turn_controller.py` を再確認して
  確定させる（上記コードはあくまで設計方針を示す試案であり、実装ステップで検証する）。
- `calc_state_value` は「前回呼び出し時との差分」を返す poke-env の `reward_computing_helper`
  とは違い、**呼び出し時点の絶対評価値**を返す純粋関数にする（状態を持たない）。差分報酬が
  欲しい利用者は前回値を自分で保持して引き算すればよい（`WeakKeyDictionary`のような内部状態は
  jpoke側には持たせない、というシンプルさ優先の判断）。

## 実装ステップ

1. `src/jpoke/rl.py` を新規作成し、`ACTION_COMMANDS` / `command_to_action` /
   `action_to_command` / `get_action_mask` を実装する
2. `RewardWeights` / `calc_state_value` を実装する
3. `embed_battle_basic` の最小参考実装を実装する（対象は要検討: 自分の場のポケモンの
   HP割合・状態異常有無・相手の場のポケモンの同項目、程度に留める）
4. `RLBattleEnv` を実装する（論点1のA案で、まず「学習対象が瀕死交代を要求されない対戦
   （相手の技構成やレベル差である程度回避できるテストシナリオ）」で動作確認する）
5. `examples/` に `04_others/` または新規カテゴリで最小の学習ループ例
   （Q学習等、外部ライブラリ不要な最小のRLアルゴリズムでよい）を1つ追加する
   （poke-envのRL exampleがPyTorch前提なのに対し、jpoke側は「外部ライブラリなしでも
   動く」ことを示す差別化ポイントにする）
6. `tests/test_rl.py`（新規）でユニットテストを書く:
   - `command_to_action`/`action_to_command` の往復変換
   - `get_action_mask` が `available_commands` と一致すること
   - `calc_state_value` の重み付け計算（poke-envのdocstring例と同じ数値で検証: fainted_value=1,
     status_value=0.5, hp_value=1 の場合に -1 になるケース等）
   - `RLBattleEnv.reset()`/`step()` の基本ループが最後まで例外なく完走すること
     （`tests/test_utils.py` の `start_battle` 等は使わず、素の `Player`/`Battle` で構成する）
7. `python -m pytest tests/ -v` で既存テストに regression がないことを確認する
8. `.internal/poke-env/rl_features_analysis.md` に「実装済み」の追記をする

## 対象外（今回のスコープ外）

- `gymnasium`/`pettingzoo` への依存追加、実際の `gymnasium.Env`/`ParallelEnv` サブクラスの提供
- マルチエージェント・自己対戦環境（PettingZoo相当）
- 論点1のB案（スレッド+キューによる強制交代のRL行動化）— 将来拡張候補として明記のみ
- 本格的な特徴量設計（技相性・場の状態全体等を含む `embed_battle` の実用実装）— 最小参考実装に留める
- 具体的なRLアルゴリズム（DQN/PPO等）の実装 — `RLBattleEnv` は環境のみ提供し、
  学習アルゴリズムは利用者（または `examples/` の最小サンプル）に委ねる
