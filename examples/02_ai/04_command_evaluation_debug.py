"""TreeSearchPlayer.evaluate_commands() によるコマンド候補・評価値のデバッグ確認方法を扱う。

03のKOFocusedPlayerは「どのコマンドが選ばれたか」だけを見ていたが、
evaluate_commands()を使うと「選ばれなかったコマンドがどう評価されていたか」まで
確認できる。木探索AIの読み筋を検証する発展的な使い方。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.players.tree_search_player import TreeSearchPlayer


class DebugPlayer(TreeSearchPlayer):
    """choose_command()の直前にevaluate_commands()の結果を表示するデバッグ用サブクラス。

    evaluate_commands()は探索本体の状態を変更しない副作用なしのメソッドなので、
    表示を挟んでもchoose_command()自体の判断には影響しない
    （ただし毎ターン呼ぶ構成をそのまま流用する場合はmax_nodesの上限を無視して
    評価する点に注意。詳細はメソッドのdocstring参照）。
    """

    def choose_command(self, battle: Battle):
        table = self.evaluate_commands(battle)
        if table:
            print("評価値:", {str(cmd): round(v, 2) for cmd, v in table.items()})
        return super().choose_command(battle)


def main() -> None:
    ai_player = DebugPlayer("TreeSearchAI", max_plies=1, max_nodes=50)
    ai_player.add_pokemon("カビゴン", move_names=["はねる", "のしかかり"])
    opponent_player = Player("Opponent")
    opponent_player.add_pokemon("カビゴン", move_names=["はねる"])

    battle = Battle(ai_player, opponent_player, seed=1)
    battle.start()
    # 1ターン目は相手の技が未公開のため評価値は空辞書になる
    battle.step()
    # 2ターン目以降、相手の技が公開されると各コマンドの評価値が表示される
    # （はねる=無効技より、のしかかり=攻撃技の方が高く評価されるはず）
    battle.step()

    # 試してみよう: max_plies=2にして相手の応手まで読ませると、評価値がどう変わるか比較できる


if __name__ == "__main__":
    main()
