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


def test_テラバースト_テラスタル時にタイプがテラスタイプへ変化():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ほのお", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.get_effective_move_type(attacker, move) == "ノーマル"

    attacker.terastallize()
    assert battle.move_executor.get_effective_move_type(attacker, move) == "ほのお"

    move.unregister_handlers(battle.events, attacker)


@pytest.mark.parametrize(
    ("attacker_name", "expected"),
    [
        ("カイリキー", "物理"),
        ("フーディン", "特殊"),
    ],
)
def test_テラバースト_テラスタル時に高い攻撃値の分類になる(attacker_name: str, expected: str):
    battle = t.start_battle(
        ally=[Pokemon(attacker_name, terastal="でんき", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.get_effective_move_category(attacker, move) == "特殊"

    attacker.terastallize()
    assert battle.move_executor.get_effective_move_category(attacker, move) == expected

    move.unregister_handlers(battle.events, attacker)


@pytest.mark.parametrize(
    ("move_name", "terastal", "terastallize", "expected"),
    [
        ("でんきショック", "でんき", True, 60),
        ("でんきショック", "ほのお", True, 40),
        ("でんこうせっか", "ノーマル", True, 40),
        ("にどげり", "かくとう", True, 30),
        ("でんきショック", "でんき", False, 40),
    ],
)
def test_テラスタル時の威力60底上げ補正(move_name: str,
                          terastal: str,
                          terastallize: bool,
                          expected: int):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal=terastal, moves=[move_name])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    if terastallize:
        attacker.terastallize()

    ctx = BattleContext(attacker=attacker, defender=defender, move=move)
    assert battle.damage_calculator.calc_final_power(ctx) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
