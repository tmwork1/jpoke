"""攻撃技ハンドラの単体テスト（や行・ら行・わ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_Ｖジェネレート_防御特防素早さが各1段階低下する():
    """Ｖジェネレート: 命中時に使用者のB/D/Sが各1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ビクティニ", move_names=["Ｖジェネレート"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["B"] == -1
    assert attacker.rank["D"] == -1
    assert attacker.rank["S"] == -1
