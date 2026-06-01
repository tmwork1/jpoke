"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import EventContext

import test_utils as t


# ──────────────────────────────────────────────────────────────────
# 攻撃側タイプ補正
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("attacker", "expected"),
    [
        (Pokemon("ピカチュウ", move_names=["でんきショック"]), 4096*1.5),
        (Pokemon("ピカチュウ", move_names=["ひのこ"]), 4096*1.0),
    ]
)
def test_攻撃側タイプ補正計算(attacker: Pokemon, expected: int):
    battle = t.start_battle(
        team0=[attacker],
        team1=[Pokemon("ピカチュウ")],
    )
    t.build_context(battle, atk_idx=0)
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == expected


# ──────────────────────────────────────────────────────────────────
# 防御側タイプ相性補正
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("defender_name", "move", "expected"),
    [
        ("フシギダネ", "ひのこ", 4096*2),
        ("コイル", "じしん", 4096*4),
        ("ゼニガメ", "ひのこ", 4096*0.5),
        ("ピカチュウ", "でんきショック", 4096*0.5),
        ("ゴース", "たいあたり", None),
    ]
)
def test_防御側タイプ相性補正計算(defender_name: str, move: str, expected: float | None):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move])],
        team1=[Pokemon(defender_name)],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected


# ──────────────────────────────────────────────────────────────────
# 急所
# ──────────────────────────────────────────────────────────────────

def test_急所_ダメージ倍率():
    """急所ダメージが1.5倍になることを確認"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    normal_damages = battle.calc_damage_range(attacker, defender, "たいあたり", critical=False)
    critical_damages = battle.calc_damage_range(attacker, defender, "たいあたり", critical=True)
    ratio = critical_damages[0] / normal_damages[0]
    assert 1.4 < ratio < 1.6


def test_急所_攻撃側の能力ランク低下を無視する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    attacker.rank["A"] = -6
    normal_with_drop = battle.calc_damage_range(attacker, defender, "たいあたり", critical=False)
    critical_with_drop = battle.calc_damage_range(attacker, defender, "たいあたり", critical=True)

    attacker.rank["A"] = 0
    critical_without_drop = battle.calc_damage_range(attacker, defender, "たいあたり", critical=True)

    assert normal_with_drop[0] < critical_with_drop[0]
    assert critical_with_drop == critical_without_drop


def test_急所_防御側の能力ランク上昇を無視する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    defender.rank["B"] = 6
    normal_with_boost = battle.calc_damage_range(attacker, defender, "たいあたり", critical=False)
    critical_with_boost = battle.calc_damage_range(attacker, defender, "たいあたり", critical=True)

    defender.rank["B"] = 0
    critical_without_boost = battle.calc_damage_range(attacker, defender, "たいあたり", critical=True)

    assert normal_with_boost[0] < critical_with_boost[0]
    assert critical_with_boost == critical_without_boost


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
