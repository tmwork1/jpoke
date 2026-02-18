"""急所判定システムの単体テスト"""
from jpoke import Pokemon, Move
from jpoke.enums import Event
import test_utils as t


def test_critical_damage_multiplier():
    """急所ダメージが1.5倍になることを確認"""
    battle = t.start_battle()
    attacker, defender = battle.actives
    normal_damages = battle.determine_damage_range(attacker, defender, "たいあたり", critical=False)
    critical_damages = battle.determine_damage_range(attacker, defender, "たいあたり", critical=True)
    assert critical_damages[0]/normal_damages[0] > 1.4


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
