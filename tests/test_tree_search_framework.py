"""scripts/tree_search/framework.py の TreeSearchPlayer の単体テスト。

木探索フレームワーク（docs/plan/tree_search_framework.md）が解消する
CRIT-1（相手の合法手が required_command_type でフィルタされない）と
ISSUE-1（探索中の割り込み交代による再帰呼び出しが copy_depth の決め打ちで
クラッシュする）の回帰確認を兼ねる。
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "tree_search"))

from jpoke import Battle, Player, Pokemon  # noqa: E402

from framework import TreeSearchPlayer, hp_ratio_evaluate  # noqa: E402


def test_evaluate関数が例外を投げてもsearchingフラグは解除される():
    """探索中に評価関数が例外を投げても _searching が True のまま残らないこと。

    残ってしまうと、以降ずっとフォールバック方策しか使われなくなる。
    """
    def broken_evaluate(battle: Battle, player: Player) -> float:
        raise RuntimeError("評価関数が壊れている")

    player1 = TreeSearchPlayer(name="SearchPlayer", evaluate=broken_evaluate)
    player1.team = [Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"])]

    player2 = Player(name="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]
    player2.team[0].moves[0].revealed = True  # 相手の技を公開し合法手が空にならないようにする

    battle = Battle((player1, player2), n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    with pytest.raises(RuntimeError):
        battle.step()

    assert player1._searching is False


def test_とんぼがえり使用時に相手のベンチが公開済みでもValueErrorにならない():
    """CRIT-1回帰: 相手のベンチが公開済みの状態でとんぼがえりを使い、
    switch フェーズに入っても sim.step() が例外にならず探索が完了すること。
    """
    player1 = TreeSearchPlayer(name="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["とんぼがえり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(name="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]
    player2.team[0].moves[0].revealed = True
    player2.team[1].revealed = True  # ベンチのカメックスを公開済みにする

    battle = Battle((player1, player2), n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()  # ここで ValueError が起きないことを確認する

    assert player1._searching is False


def test_探索中に割り込み交代が発生してもフォールバックで完了する():
    """ISSUE-1回帰: 探索対象の各分岐で瀕死交代が発生しても、フォールバック
    方策により choose_command() が例外にならず正常にコマンドを返すこと。
    """
    player1 = TreeSearchPlayer(name="SearchPlayer", max_plies=2)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="いのちのたま", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(name="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]
    player2.team[0].moves[0].revealed = True  # 相手の技を公開し合法手が空にならないようにする

    # 先頭同士のHPを1にして、同時瀕死交代が起きやすくする
    player1.team[0].hp = 1
    player2.team[0].hp = 1

    battle = Battle((player1, player2), n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()  # 探索中の瀕死交代でも例外にならないことを確認する

    assert player1._searching is False


def test_有利な技を選択する():
    """max_plies=1 で、明確に有利な技（相手を倒せる）を選ぶこと。"""
    player1 = TreeSearchPlayer(name="SearchPlayer", evaluate=hp_ratio_evaluate)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(name="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]
    player2.team[0].moves[0].revealed = True  # 相手の技を公開し合法手が空にならないようにする

    battle = Battle((player1, player2), n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    # ダメージを固定し、たいあたりでは倒せず10まんボルトなら確実に倒せるようにする
    battle.actives[1].hp = 50
    battle.roll_damage = lambda attacker, defender, move, critical=False: (
        200 if move.name == "10まんボルト" else 1
    )

    battle.step()

    assert battle.actives[0].executed_move.name == "10まんボルト"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
