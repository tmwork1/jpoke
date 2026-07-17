"""TreeSearchPlayer.configure_sim() をオーバーライドして、
探索中だけ確率的要素を固定する木探索AIの拡張例を示す。

木探索は各分岐で battle.copy() した sim 上で技を実際に発動させて評価する
（tree_search_player.py の _worst_case_over_opponent() 参照）ため、命中判定・
ダメージ乱数などの確率的要素がそのまま評価値に混ざり込む。命中率80%の技を
含む盤面で evaluate_commands() を2回呼んでも、シミュレーションのたびに
命中/外れが変わり得るため評価値が一致するとは限らない。configure_sim() を
オーバーライドし、探索専用のsimにだけBattleOption（命中率固定・ダメージ
平均値化）を設定すると、この評価値のブレをなくせる。実際のbattle本体には
影響しない。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command
from jpoke.players.tree_search_player import TreeSearchPlayer


class DeterministicSearchPlayer(TreeSearchPlayer):
    """探索中だけ命中率100%・ダメージを平均値に固定するAI（configure_sim()の拡張例）。

    choose_command() の直前に evaluate_commands() を2回呼び、評価値が
    毎回一致することを表示する（04_command_evaluation_debug.pyの
    DebugPlayerと同様、evaluate_commands()は副作用なしのメソッドなので
    表示を挟んでも探索本体の判断には影響しない）。
    """

    def configure_sim(self, sim: Battle) -> None:
        # accuracy_fix_threshold=0: 命中率0%以上の技（=すべての技）を100%命中扱いにする
        sim.option.accuracy_fix_threshold = 0
        # damage_roll="average": ダメージ乱数を毎回同じ平均値に固定する
        sim.option.damage_roll = "average"

    def choose_command(self, battle: Battle) -> Command:
        table1 = self.evaluate_commands(battle)
        table2 = self.evaluate_commands(battle)
        if table1:
            print("1回目の評価値:", {str(c): round(v, 2) for c, v in table1.items()})
            print("2回目の評価値:", {str(c): round(v, 2) for c, v in table2.items()})
            print(f"2回の評価値が完全に一致: {table1 == table2}")
        return super().choose_command(battle)


def main() -> None:
    # ハイドロポンプは命中率80%。命中判定が絡む技を含む盤面で比較する
    ai_player = DeterministicSearchPlayer("DeterministicAI", max_plies=1, max_nodes=50)
    ai_player.add_pokemon("カメックス", move_names=["ハイドロポンプ", "たいあたり"])

    opponent_player = Player("Opponent")
    opponent_player.add_pokemon("カビゴン", move_names=["のしかかり"])

    battle = Battle(ai_player, opponent_player, seed=1)
    battle.start()
    # 1ターン目は相手の技が未公開のため評価値は空辞書になる（04参照）
    battle.step()
    # 2ターン目以降、相手の技が公開されるとハイドロポンプを含む評価値が表示される
    battle.step()

    # configure_sim() で命中率・ダメージ乱数を固定しているため、reseed=True で
    # シミュレーションごとに乱数系列が変わっても（Battle.copy()のdocstring参照）
    # 評価値は常に一致する

    # 試してみよう: configure_sim() の中身をpassに変えて実行し直すと、命中判定が
    # シミュレーションのたびに変わるため、2回の評価値が一致しなくなることがある


if __name__ == "__main__":
    main()
