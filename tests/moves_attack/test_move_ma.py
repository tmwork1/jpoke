"""攻撃技ハンドラの単体テスト（ま行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_マジカルアクセル_こんらんが発動する():
    """マジカルアクセル: 30%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジカルアクセル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_みずのはどう_こんらんが発動する():
    """みずのはどう: 20%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["みずのはどう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")
