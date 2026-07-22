"""強化学習を始めるための補助機能。

外部ライブラリ（gymnasium等）には一切依存しない。reset()/step()など
gymnasiumと同じ形のメソッド名を持つが、返り値はlist/dict/float/boolのみで
構成する。gymnasium.Envを実際に使いたい場合は、本モジュールの戻り値を
そのまま各メソッドの戻り値に使えばよい。

強制交代（瀕死交代等）の意思決定はRL行動として公開せず、`learner`/`opponent`
双方とも既定の`Player.choose_command()`（先頭コマンドを選ぶ）にフォールバック
させる。瀕死交代の戦略性を学習させたい場合は本モジュールの対象外
（`.internal/plan/poke-env/rl_support.md` 論点1参照）。
"""
from __future__ import annotations

from dataclasses import dataclass

from jpoke import Battle, Player
from jpoke.enums import Command

# 実際の行動として選ばれることのない特殊コマンドは行動空間から除外する
_EXCLUDED = (Command.STRUGGLE, Command.FORCED)
ACTION_COMMANDS: tuple[Command, ...] = tuple(c for c in Command if c not in _EXCLUDED)
ACTION_SPACE_SIZE: int = len(ACTION_COMMANDS)


def command_to_action(command: Command) -> int:
    """CommandをRL用の整数行動（0〜ACTION_SPACE_SIZE-1）に変換する。"""
    return ACTION_COMMANDS.index(command)


def action_to_command(action: int) -> Command:
    """RL用の整数行動をCommandに変換する（逆変換）。"""
    return ACTION_COMMANDS[action]


def get_action_mask(battle: Battle, player: Player) -> list[int]:
    """現在選択可能なコマンドを1、それ以外を0とする長さACTION_SPACE_SIZEのマスクを返す。

    `Battle.available_commands()` は`resolve_command()`内部からのphase文脈
    （`battle.phase == "action"`）でのみ呼べる実装のため、`phase_context("action")`
    で一時的にaction フェーズへ切り替えて問い合わせる（`jpoke.testing.reserve_command`
    と同じ手法）。`RLBattleEnv`は1回の`step()`内で発生する強制交代を全て解決してから
    呼び出し元に制御を返すため、常に次のaction フェーズの合法手を問い合わせればよい。
    """
    with battle.phase_context("action"):
        available = set(battle.available_commands(player))
    return [1 if c in available else 0 for c in ACTION_COMMANDS]


@dataclass
class RewardWeights:
    """reward_computing_helper相当の重み設定。既定はpoke-envと同じ0（勝敗のみ1.0）。"""
    fainted: float = 0.0
    hp: float = 0.0
    status: float = 0.0
    victory: float = 1.0


def calc_state_value(battle: Battle, player: Player, weights: RewardWeights) -> float:
    """現在の対戦状態の評価値を計算する（差分報酬の元になる値。poke-envのreward_computing_helperと同じ考え方）。

    評価基準は利用者が`RewardWeights`で自由に変える前提の叩き台であり、
    `players/tree_search_player.py`の評価ロジックとは独立させている
    （`.internal/plan/poke-env/rl_support.md` 論点4）。
    """
    opponent = battle.opponent(player)
    player_hp = sum(mon.hp_fraction for mon in battle.get_team(player) if not mon.fainted)
    opponent_hp = sum(mon.hp_fraction for mon in battle.get_team(opponent) if not mon.fainted)
    value = (player_hp - opponent_hp) * weights.hp
    for mon in battle.get_team(player):
        if mon.fainted:
            value -= weights.fainted
        elif mon.ailment.name:
            value -= weights.status
    for mon in battle.get_team(opponent):
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

    自分の場のポケモン→相手の場のポケモンの順に、1体につき
    [HP割合, 瀕死か, 状態異常があるか] の3項目を並べる。本格的な特徴量設計
    （技・タイプ相性・場の状態等）は利用者に委ねる。
    """
    opponent = battle.opponent(player)
    features: list[float] = []
    for team in (battle.get_team(player), battle.get_team(opponent)):
        for mon in team:
            features.append(mon.hp_fraction)
            features.append(1.0 if mon.fainted else 0.0)
            features.append(1.0 if mon.ailment.name else 0.0)
    return features


class RLBattleEnv:
    """gymnasiumのreset()/step()と同じ形の薄いラッパー。

    学習対象は`learner`（行動をRL側が決める）、対戦相手は`opponent`（既存の
    Playerサブクラスがそのまま行動を決める）。強制交代（瀕死交代等）は
    `opponent`/`learner`双方とも既定のchoose_command（先頭コマンド）に
    フォールバックする（`Battle.step()`内部で両者のchoose_command()が
    switchフェーズ用に再入的に呼ばれるため、追加の分岐は不要）。
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
        assert self.battle is not None, "reset()を先に呼ぶこと"
        command = action_to_command(action)
        if not get_action_mask(self.battle, self.learner)[action]:
            raise ValueError(
                f"行動{action}（{command}）は現在選択できません。"
                "get_action_mask()で合法手を確認してください。"
            )
        # resolve_command("action")は両プレイヤーのstate.required_command_typeを
        # "any"へ更新する副作用を持つ（前ターンに学習対象が強制交代を挟んだ場合、
        # 更新せずにstepへ進むと"switch"が残ったままでvalidate_commandに弾かれる）。
        # learner側の戻り値（learner.choose_command()の既定実装）は使わず、
        # 外部から渡されたactionのコマンドで上書きする。
        commands = self.battle.resolve_command("action")
        commands[self.learner] = command
        self.battle.step(commands)
        # finishedはjudge_winner()を経由してBattle.winnerを確定させる副作用を持つため、
        # calc_state_value()内のwon()/lost()判定より先に呼ぶ必要がある
        terminated = self.battle.finished
        reward = calc_state_value(self.battle, self.learner, self.reward_weights)
        truncated = (not terminated) and self.battle.turn >= self.max_turns
        return get_action_mask(self.battle, self.learner), reward, terminated, truncated, {}
