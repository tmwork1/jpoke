"""木探索プレイヤーの共通フレームワーク。

tree_search_1〜4.py に重複していた「合法手の総当たり列挙」「盤面複製」
「割り込み交代での再帰呼び出しの処理」を1箇所にまとめる。
利用者は evaluate（葉ノード評価関数）を差し替えるだけで木探索プレイヤーを作れる。

設計の詳細・根拠は docs/plan/tree_search_framework.md を参照。
"""
from __future__ import annotations
from typing import Callable
import random

from jpoke import Battle, Player
from jpoke.enums import Command


EvaluateFn = Callable[[Battle, Player], float]
FallbackFn = Callable[[Battle, Player], Command]


def default_fallback(battle: Battle, player: Player) -> Command:
    """探索の再入時（割り込み交代など）に使う既定のフォールバック方策。

    評価値付きの探索は行わず、合法手からランダムに1つ選ぶだけの軽量な方策。
    """
    return random.choice(battle.get_available_commands(player))


def hp_ratio_evaluate(battle: Battle, player: Player) -> float:
    """自分と相手の残りHP割合の差を返す簡易評価関数。

    決着がついている場合は勝敗を最優先する（±inf）。
    """
    opponent = battle.opponent(player)
    winner = battle.judge_winner()
    if winner is player:
        return float("inf")
    if winner is opponent:
        return float("-inf")

    def hp_ratio(target: Player) -> float:
        team = battle.player_states[target].team
        return sum(mon.hp / mon.max_hp for mon in team if not mon.fainted)

    return hp_ratio(player) - hp_ratio(opponent)


class TreeSearchPlayer(Player):
    """合法手を総当たりで評価する木探索プレイヤーの基底クラス。

    自分の各合法手について、相手が最善（自分にとって最悪）の手を選ぶと
    仮定したミニマックスで評価する。max_plies を2以上にすると、相手の
    応手も含めた複数ターン先までを直接の関数再帰で評価する。

    Attributes:
        evaluate: 葉ノードの盤面を評価する関数。値が大きいほど自分に有利。
        max_plies: 探索する手数（1以上）。1手ごとに
            len(my_commands) * len(opponent_commands) 倍に分岐が増えるため、
            2以上を指定する場合は評価関数の呼び出し回数に注意する。
        fallback: 探索の再帰呼び出し（割り込み交代など）で使う方策。
    """

    def __init__(self,
                 name: str,
                 evaluate: EvaluateFn = hp_ratio_evaluate,
                 max_plies: int = 1,
                 fallback: FallbackFn | None = None):
        super().__init__(name=name)
        self.evaluate = evaluate
        self.max_plies = max_plies
        self.fallback = fallback or default_fallback
        self._searching = False

    def choose_command(self, battle: Battle) -> Command:
        if self._searching:
            # sim.step() の内部で発生した割り込み交代（瀕死・だっしゅつボタン・
            # だっしゅつパック・とんぼがえり等）による再帰呼び出し。この局面は
            # 探索木の分岐には含めず、フォールバック方策で即決する。
            # 「copy_depth > 1 なら raise」という決め打ちの代わりに、探索の
            # 最上位呼び出しかどうかを明示的なフラグで判定している
            # （docs/plan/tree_search_framework.md ISSUE-1 参照）。
            return self.fallback(battle, self)

        self._searching = True
        try:
            command, _ = self._best_command(battle, self.max_plies)
            return command
        finally:
            self._searching = False

    def _best_command(self, battle: Battle, plies: int) -> tuple[Command, float]:
        """自分の各合法手について、相手が最善に対抗した場合の評価値を求め、
        その中で最大の評価値を持つ手を返す（ミニマックス）。
        """
        opponent = battle.opponent(self)

        if plies == self.max_plies:
            # 探索の最上位（実際のゲームエンジンから choose_command() が
            # 呼ばれた最初の1回）。battle はエンジンが用意した観測用コピーで、
            # 相手の合法手は情報隠蔽済みのスナップショット
            # （last_available_commands）を尊重する。
            my_commands = battle.get_available_commands(self)
            opponent_commands = battle.get_available_commands(opponent)
        else:
            # 2手目以降の内部シミュレーション。sim.step(commands) は
            # resolve_command() を経由せず直接呼ぶため、required_command_type /
            # last_available_commands は前のシミュレーション内のターンの値
            # （割り込み交代フェーズ等）のまま残っており、新しいターンの
            # 行動コマンド選択としては使えない。ここでは内部探索用の
            # 全知シミュレーションとして CommandManager から現在の合法手を
            # 直接再計算し、required_command_type も行動フェーズ用に
            # 明示的にリセットする（is_observation() が真の盤面では
            # build_observation() がマスク処理をスキップするため、
            # 情報隠蔽つきスナップショットを新しいターン用に作り直す手段が
            # 元々存在しない。docs/plan/tree_search_framework.md 参照）。
            my_commands = battle.command_manager.get_available_action_commands(self)
            opponent_commands = battle.command_manager.get_available_action_commands(opponent)
            battle.player_states[self].required_command_type = "any"
            battle.player_states[opponent].required_command_type = "any"

        best_command, best_score = my_commands[0], float("-inf")
        for my_cmd in my_commands:
            score = self._worst_case_over_opponent(
                battle, my_cmd, opponent, opponent_commands, plies
            )
            if score > best_score:
                best_command, best_score = my_cmd, score
        return best_command, best_score

    def _worst_case_over_opponent(self,
                                   battle: Battle,
                                   my_cmd: Command,
                                   opponent: Player,
                                   opponent_commands: list[Command],
                                   plies: int) -> float:
        """相手が自分にとって最も不利な手を選ぶと仮定し、その評価値を返す。"""
        worst = float("inf")
        for opp_cmd in opponent_commands:
            sim = battle.copy()
            sim.step({self: my_cmd, opponent: opp_cmd})
            score = self._evaluate_node(sim, plies)
            worst = min(worst, score)
        return worst

    def _evaluate_node(self, sim: Battle, plies: int) -> float:
        if sim.judge_winner() is not None or plies <= 1:
            return self.evaluate(sim, self)
        # 残りプライ数分だけ自分の視点で再帰する。sim.step() ではなく直接
        # _best_command() を呼ぶことで、意図した多段探索の再帰と、
        # 割り込み交代によるエンジン起因の再帰（choose_command() 経由）を
        # 明確に分離している（後者だけが _searching フラグの対象になる）。
        _, score = self._best_command(sim, plies - 1)
        return score
