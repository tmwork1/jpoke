"""TreeSearchPlayer を継承した簡易AIとランダム方策を対戦させる。

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


class KOFocusedPlayer(TreeSearchPlayer):
    """相手を瀕死にできる手を優先する簡易AI（evaluate() の拡張例）。"""

    def evaluate(self, battle: Battle) -> float:
        # super().evaluate(battle) は継承元 TreeSearchPlayer の既定実装（未変更の
        # 評価関数）をそのまま呼び出す記法。オーバーライドしつつ親クラスの処理も
        # 活かしたいときに使う
        # 既定の評価（残りHP割合の差）に、相手の瀕死数をボーナスとして加える
        base = super().evaluate(battle)
        opponent_team = battle.get_team(battle.opponent(self))
        n_fainted = sum(1 for mon in opponent_team if mon.fainted)
        return base + n_fainted


def main() -> None:
    # max_plies は木探索の深さ（何手先まで読むか）。2にすると相手の応手まで読むが、
    # 分岐が自分の合法手数×相手の合法手数倍に増えるため max_nodes も合わせて調整が必要
    ai_player = KOFocusedPlayer("TreeSearchAI", max_plies=1, max_nodes=50)
    # じしん（じめんタイプ、威力100）は相手のピカチュウ（でんきタイプ、弱点）に
    # 抜群が入り確実に瀕死にできるが、みずでっぽう（みずタイプ、威力40、等倍かつ
    # カビゴンはみずタイプではないためSTABも乗らない）は威力が低く、急所に当たっても
    # 1発で瀕死にできない。威力・タイプ相性の異なる技を混在させることで、
    # 「相手を瀕死にできる技」を優先するKOFocusedPlayerの判断を観察しやすくする
    ai_player.add_pokemon("カビゴン", move_names=["じしん", "みずでっぽう"])

    random_player = RandomPlayer("RandomPlayer")
    # カビゴン（じしんで弱点を突かれない）ではなく、じめんが弱点のピカチュウにする
    random_player.add_pokemon("ピカチュウ", move_names=["でんきショック", "でんこうせっか"])

    battle = Battle(ai_player, random_player, seed=1)

    max_turns = 20
    battle.play_out(max_turns=max_turns)
    winner = battle.winner
    if winner is None:
        print(f"結果: 決着つかず（{max_turns}ターン経過）")
    else:
        print(f"結果: {winner.username} 勝利（{battle.turn}ターン）")
    print(f"直近ターンで TreeSearchAI が展開したノード数: {ai_player.nodes_expanded}")
    battle.print_logs()

    # 試してみよう: evaluate() に「残り技のPP」や「急所を受けた回数」など
    # 別の要素を加点・減点として加えると、AIの手の選び方がどう変わるか観察できる。
    # max_plies を2以上に増やして探索の深さを変えると、手の選び方や
    # nodes_expanded（展開ノード数）がどう変わるかも比較できる


if __name__ == "__main__":
    main()
