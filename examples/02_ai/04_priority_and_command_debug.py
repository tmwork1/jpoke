"""jpoke で学べること: 優先度技・素早さ操作技（トリックルーム）が行動順に与える影響、
TreeSearchPlayer.evaluate_commands() によるコマンド候補・評価値のデバッグ確認。

03のKOFocusedPlayerは「どのコマンドが選ばれたか」だけを見ていたが、
evaluate_commands()を使うと「選ばれなかったコマンドがどう評価されていたか」まで
確認できる。木探索AIの読み筋を検証する発展的な使い方。
"""
from __future__ import annotations

from jpoke import Battle, Move, Player
from jpoke.players.tree_search_player import TreeSearchPlayer


def show_priority_and_speed_control() -> None:
    """優先度技は素早さに関わらず先に発動する。トリックルームは素早さ順を反転させる。"""
    player1 = Player("Slow")
    player1.add_pokemon("カビゴン", move_names=["でんこうせっか", "のしかかり"])
    player2 = Player("Fast")
    player2.add_pokemon("ピカチュウ", move_names=["たいあたり"])

    battle = Battle(player1, player2, seed=1)
    battle.start()
    slow = battle.get_active(player1)

    # calc_move_priority() で技の優先度（+補正込み）を直接確認できる
    print(
        f"優先度: でんこうせっか={battle.calc_move_priority(slow, Move('でんこうせっか'))}, "
        f"のしかかり={battle.calc_move_priority(slow, Move('のしかかり'))}"
    )
    print(f"素早さ順（通常時）: {[m.name for m in battle.resolve_speed_order()]}")

    # activate_global_field() は技を介さずグローバルフィールド効果を直接発動する検証用API
    battle.activate_global_field("トリックルーム", 5)
    print(f"素早さ順（トリックルーム下）: {[m.name for m in battle.resolve_speed_order()]}")


class DebugPlayer(TreeSearchPlayer):
    """choose_command()の直前にevaluate_commands()の結果を表示するデバッグ用サブクラス。

    evaluate_commands()は探索本体の状態を変更しない副作用なしのメソッドなので、
    表示を挟んでもchoose_command()自体の判断には影響しない。
    ただしevaluate_commands()はmax_nodesによるノード数上限を無視して全合法手を
    評価するため、このサンプルのように毎ターン（choose_command()の呼び出しごと）
    呼び出す構成をそのまま学習ループの可視化等に転用する場合、max_plies次第では
    探索コストが無制限に膨らみうる点に注意する。
    """

    def choose_command(self, battle: Battle):
        table = self.evaluate_commands(battle)
        if table:
            print("評価値:", {str(cmd): round(v, 2) for cmd, v in table.items()})
        return super().choose_command(battle)


def main() -> None:
    show_priority_and_speed_control()
    print("-" * 50)

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
