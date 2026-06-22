"""攻撃技ハンドラの単体テスト（さ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_しんぴのちから_特攻1段階上昇が発動する():
    """しんぴのちから: 命中時に使用者のCが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["しんぴのちから"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["C"] == 1
