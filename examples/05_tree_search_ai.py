"""jpoke で学べること: TreeSearchPlayer を継承した簡易AIとランダム方策の対戦。

TreeSearchPlayer は「自分の全ての合法手x相手の全ての合法手」を1手分シミュレーションし、
相手が自分にとって最も不利な手を選ぶと仮定したミニマックスで評価する木探索の基底クラス
（詳細: https://github.com/tmwork1/jpoke/blob/main/src/jpoke/players/tree_search_player.py）。
既定の評価関数（残りHP割合の差）のままでも
動くが、ここでは evaluate() をオーバーライドして「相手を瀕死にできたか」を加点する例を示す。
AI開発ユースケースの発展形。
"""
from __future__ import annotations

from jpoke import Battle
from jpoke.players import RandomPlayer
from jpoke.players.tree_search_player import TreeSearchPlayer


# TODO: TreeSearchPlayer という名前は適切か。MinimaxPlayer の方がわかりやすいかも。
# TODO: ユーザーからは木探索の深さ設定が見えてこない。
class KOFocusedPlayer(TreeSearchPlayer):
    """相手を瀕死にできる手を優先する簡易AI（evaluate() の拡張例）。"""

    def evaluate(self, battle: Battle) -> float:
        # 既定の評価（残りHP割合の差）に、相手の瀕死数をボーナスとして加える
        base = super().evaluate(battle)
        opponent_team = battle.get_team(battle.opponent(self))
        n_fainted = sum(1 for mon in opponent_team if mon.fainted)
        return base + n_fainted


def main() -> None:
    # 1ターンで決着してしまうと探索の様子が観察しづらいため、HPが高いカビゴン同士を
    # 対戦させ、複数ターンにわたる駆け引きが起きるようにする
    ai_player = KOFocusedPlayer("TreeSearchAI", max_plies=1, max_nodes=50)
    ai_player.add_pokemon("カビゴン", move_names=["のしかかり", "じしん"])

    random_player = RandomPlayer("RandomPlayer")
    random_player.add_pokemon("カビゴン", move_names=["たいあたり", "からげんき"])

    battle = Battle((ai_player, random_player), seed=1)
    battle.start()

    max_turns = 20
    while not battle.finished and battle.turn < max_turns:
        battle.step()

    winner = battle.judge_winner()
    if winner is None:
        print(f"結果: 決着つかず（{max_turns}ターン経過）")
    else:
        print(f"結果: {winner.username} 勝利（{battle.turn}ターン）")
    print(f"直近ターンで TreeSearchAI が展開したノード数: {ai_player.nodes_expanded}")
    battle.print_logs()

    # 試してみよう: evaluate() に「残り技のPP」や「急所を受けた回数」など
    # 別の要素を加点・減点として加えると、AIの手の選び方がどう変わるか観察できる


if __name__ == "__main__":
    main()
