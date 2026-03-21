"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import BattleContext

import test_utils as t


@pytest.mark.parametrize(
    ("attacker", "terastallize", "expected"),
    [
        (Pokemon("ピカチュウ", moves=["でんきショック"]), False, 1.5),
        (Pokemon("ピカチュウ", moves=["ひのこ"]), False, 1.0),
        (Pokemon("ピカチュウ", terastal="ほのお", moves=["ひのこ"]), True, 1.5),
        (Pokemon("リザードン", terastal="ほのお", moves=["ひのこ"]), True, 2.0),
        (Pokemon("ピカチュウ", terastal="ほのお", moves=["でんきショック"]), True, 1.5),
    ]
)
def test_攻撃側タイプ補正計算(attacker: Pokemon, terastallize: bool, expected: int):
    battle = t.start_battle(
        ally=[attacker],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    if terastallize:
        attacker.terastallize()

    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == expected


@pytest.mark.parametrize(
    ("move_name", "defender_name", "expected"),
    [
        ("ひのこ", "フシギダネ", 2.0),
        ("ひのこ", "ゼニガメ", 0.5),
        ("でんきショック", "ピカチュウ", 0.5),
        ("たいあたり", "ゴース", 0.0),
    ]
)
def test_防御側タイプ相性補正計算(move_name: str, defender_name: str, expected: float):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon(defender_name)],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert battle.damage_calculator.calc_def_type_modifier(ctx) == pytest.approx(expected)


def test_防御側タイプ相性補正計算_直接引数():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("フシギバナ")],
    )

    assert battle.damage_calculator.calc_def_type_modifier(
        defender=battle.actives[1],
        move="ひのこ",
    ) == pytest.approx(2.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
