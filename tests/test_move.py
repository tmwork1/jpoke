"""技ハンドラの単体テスト。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import LogCode
import test_utils as t


def test_はやてがえし_先制攻撃技に成功():
    """はやてがえし: 相手が先制攻撃技を選んだ時のみ成功し、ひるませる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp
    t.reserve_command(battle)

    battle.advance_turn()
    assert battle.actives[1].hp < before_foe_hp
    assert battle.actives[0].hp == before_ally_hp
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_はやてがえし_通常攻撃技には失敗():
    """はやてがえし: 優先度0の攻撃技を選んだ相手には失敗する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp
    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp
    assert not t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_はやてがえし_先制変化技には失敗():
    """はやてがえし: 先制変化技（まもる）には失敗する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["まもる"])],
    )
    before_foe_hp = battle.actives[1].hp
    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert not t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_きあいパンチ_行動前にダメージを受けず成功():
    """きあいパンチ: 行動前に被弾していなければ成功する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp < before_foe_hp


def test_きあいパンチ_攻撃ダメージを受けると失敗():
    """きあいパンチ: 行動前に攻撃ダメージを受けた場合は不発。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=0)


def test_きあいパンチ_みがわりへの被弾では中断しない():
    """きあいパンチ: みがわりが被弾しても使用者は中断されない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    battle.volatile_manager.apply(battle.actives[0], "みがわり", hp=999)
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp < before_foe_hp
    assert battle.actives[0].hp == before_ally_hp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
