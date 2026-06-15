"""変化技ハンドラの単体テスト（ま行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_めいそう_とくこうととくぼう1段階ずつ上がる():
    """めいそう: 使用すると自分のとくこうとぼうぎょランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["めいそう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["C"] == 0
    assert attacker.rank["D"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["C"] == 1
    assert attacker.rank["D"] == 1


def test_めいそう_とくこう最大でもとくぼうは上昇する():
    """めいそう: とくこうがすでに+6でも、とくぼうは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["めいそう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["C"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["C"] == 6
    assert attacker.rank["D"] == 1
