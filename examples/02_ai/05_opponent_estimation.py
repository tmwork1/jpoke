"""TreeSearchPlayer.opponent_estimator() をオーバーライドして、
相手の見えていない情報（未公開の技構成）を推定する方法を示す。

対戦開始直後（実対戦の初手など）は相手の技が1つも公開されておらず、既定の
TreeSearchPlayerは相手の合法手を求められないため探索を行わず fallback() に
即座に委譲する（03_tree_search_ai.py参照）。opponent_estimator() をオーバー
ライドすると、相手ポケモンのモデル（moves/item等）に推定値を書き込め、そこから
実際に選べるコマンドの列挙はCommandManagerに任せられる。利用者はMove/Itemなど
見慣れたドメインオブジェクトを推定するだけでよく、Command自体を組み立てる必要はない。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.players.tree_search_player import TreeSearchPlayer


class OpponentGuessingPlayer(TreeSearchPlayer):
    """相手の未公開の技を「みずでっぽう」1本と仮定して探索するAI（opponent_estimator()の拡張例）。"""

    def opponent_estimator(self, battle: Battle, opponent: Player) -> None:
        # 実戦では対戦データベースや使用率統計等から推定するが、ここでは固定の
        # 推測技で最小例を示す。opponent.active.moves が空（未公開）のときだけ
        # 書き込む
        opponent_active = battle.get_active(opponent)
        if not opponent_active.moves:
            opponent_active.set_moves(["みずでっぽう"])


def main() -> None:
    ai_player = OpponentGuessingPlayer("GuessingAI", max_plies=1, max_nodes=50)
    ai_player.add_pokemon("リザードン", move_names=["かえんほうしゃ", "じしん"])

    opponent_player = Player("Opponent")
    opponent_player.add_pokemon("カメックス", move_names=["みずでっぽう"])

    battle = Battle(ai_player, opponent_player, seed=1)
    battle.start()

    # 1ターン目: 相手の技は未公開。opponent_estimator が推定を書き込むため
    # fallback() には委譲されず、推定した相手の技も踏まえた探索が行われる
    # （nodes_expanded > 0 になる。何も推定しない既定実装のままだと0のまま）
    battle.step()
    print(f"1ターン目に展開したノード数: {ai_player.nodes_expanded}")
    battle.print_logs()

    # 試してみよう: opponent_estimator() の中身を消して既定実装（何もしない）に
    # 戻すと、1ターン目は探索されず nodes_expanded が0のままになることを確認できる


if __name__ == "__main__":
    main()
