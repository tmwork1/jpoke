"""急所判定システムの単体テスト"""
from jpoke import Pokemon, Move
from jpoke.enums import Event
import test_utils as t


def test_critical_damage_multiplier():
    """急所ダメージが1.5倍になることを確認"""
    battle = t.start_battle()
    normal_damages = battle.determine_damage_range(battle.actives[0], "たいあたり", critical=False)
    critical_damages = battle.determine_damage_range(battle.actives[0], "たいあたり", critical=True)
    assert critical_damages[0]/normal_damages[0] > 1.4, "Incorrect critical damage multiplier"


def test_critical_rank_calculation():
    """急所ランク計算の検証"""
    battle = t.start_battle()
    mon = battle.actives[0]
    rank = battle.move_executor.calc_critical_rank(mon, Move("たいあたり"))
    assert rank == 0, "Invalid initial critical rank"

    rank = battle.move_executor.calc_critical_rank(mon, Move("きりさく"))
    assert rank == 1, "Invalid initial critical rank"

    rank = battle.move_executor.calc_critical_rank(mon, Move("あんこくきょうだ"))
    assert rank == 3, "Invalid initial critical rank"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
