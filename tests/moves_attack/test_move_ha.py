"""攻撃技ハンドラの単体テスト（は行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_はやてがえし_先制変化技には失敗():
    """はやてがえし: 先制変化技（まもる）には失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["まもる"])],
    )
    before_foe_hp = battle.actives[1].hp

    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp


def test_はやてがえし_先制攻撃技に成功():
    """はやてがえし: 相手が先制攻撃技を選んだ時のみ成功し、ひるませる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    battle.advance_turn()
    assert battle.actives[0].hp == battle.actives[0].max_hp
    assert battle.actives[1].hp < battle.actives[1].max_hp


def test_はやてがえし_通常攻撃技には失敗():
    """はやてがえし: 優先度0の攻撃技を選んだ相手には失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp
