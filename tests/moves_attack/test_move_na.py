"""攻撃技ハンドラの単体テスト（な行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_ナイトヘッド_与ダメージは使用者レベル固定():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", level=50, move_names=["ナイトヘッド"])],
                            )
    before_hp = battle.actives[1].hp
    battle.advance_turn()
    assert before_hp - battle.actives[1].hp == 50


def test_にどげり_命中判定1回で2回ヒットする():
    """にどげり: 命中判定は1回だけで、2ヒットする。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にどげり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


def test_ねんりき_こんらんが発動する():
    """ねんりき: 10%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ねんりき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_のしかかり_まひが発動する():
    """のしかかり: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["のしかかり"])],
        team1=[Pokemon("リザードン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"
