"""ミニマックス評価による木探索プレイヤー。"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command

from .tree_search_player import TreeSearchPlayer


class MinimaxPlayer(TreeSearchPlayer):
    """自分の各合法手について、相手が最善（自分にとって最悪）の手を選ぶと
    仮定したミニマックスで評価する木探索プレイヤー。

    `TreeSearchPlayer` が提供する `evaluate`/`fallback`/`estimate_opponent`/
    `configure_sim` の4フックはそのまま利用できる。詳細は `TreeSearchPlayer`
    のクラスdocstringを参照。
    """

    def _score_command(self,
                        battle: Battle,
                        my_cmd: Command,
                        opponent: Player,
                        opp_commands: list[Command],
                        plies: int) -> float:
        """相手が自分にとって最も不利な手を選ぶと仮定し、その評価値を返す。"""
        worst = float("inf")

        # 相手の各合法手について、相手が最善に対抗した場合の評価値を求める
        for opp_cmd in opp_commands:
            # ノード上限に達したら即座に探索を打ち切る
            if self._node_limit_reached():
                break

            sim = battle.copy(reseed=True, copy_logs=False, omniscient=True)

            # 探索専用の決定論化オプション（例: 命中固定・平均ダメージ）を
            # sim にだけ設定する。実盤面（battle）には影響しない。
            # 分岐（sim）ごとに新規オブジェクトのため、choose_command()側で
            # 1度だけ呼んでも各simには伝播しない。分岐ごとの呼び出しが必須
            # （test_configure_simが各分岐でsim_step実行前に呼ばれる で担保）。
            self.configure_sim(sim)

            # コマンドを指定して盤面を進める。
            sim.step({self: my_cmd, opponent: opp_cmd})
            self.nodes_expanded += 1
            score = self._evaluate_node(sim, plies)
            worst = min(worst, score)
        return worst
