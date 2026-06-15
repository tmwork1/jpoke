"""変化技ハンドラの単体テスト（う行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_うたう_すでに状態異常なら失敗():
    """うたう: 対象がすでに状態異常を持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("まひ")
    assert not defender.has_ailment("ねむり")


def test_うたう_ねむり付与():
    """うたう: 相手をねむり状態にする（accuracy=100で固定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")
