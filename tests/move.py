import math
from jpoke import Pokemon
import test_utils as t


def test_arm_hammer_speed_reduction():
    """アームハンマー: 素早さ低下"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["アームハンマー"])],
        turn=1
    )
    assert battle.actives[0].rank["S"] == -1, "アームハンマー: 素早さ低下失敗"


def test_sandstorm_weather():
    """すなあらし: 天気設定"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["すなあらし"])],
        turn=1
    )
    assert battle.weather == "すなあらし", "すなあらし: 天気設定失敗"


def test_thunderbolt_paralysis():
    """でんじほう: まひ適用"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんじほう"])],
        foe=[Pokemon("フシギバナ")],
        turn=1
    )
    assert battle.actives[1].ailment == "まひ", "でんじほう: まひ適用失敗"


def test_volt_switch_switch():
    """とんぼがえり: 交代"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["とんぼがえり"]) for _ in range(2)],
        turn=1
    )
    assert battle.players[0].active_idx != 0, "とんぼがえり: 交代失敗"


def test_struggle_damage():
    """わるあがき: ダメージ計算"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["わるあがき"])],
        turn=1
    )
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 3/4), "わるあがき: ダメージ計算失敗"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
