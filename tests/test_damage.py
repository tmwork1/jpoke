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


def test_ステラSTAB_元タイプ一致_初回2倍_以降1倍5():
    """ステラ テラスタル中、元タイプ一致技は初回2.0倍、2回目以降1.5倍。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ステラ", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()

    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    # 初回: 元タイプ一致 → 2.0倍
    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == pytest.approx(2.0)

    # 消費済みに設定してから再計算
    attacker.stellar_boosted_types.add("でんき")
    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == pytest.approx(1.5)


def test_ステラSTAB_不一致技_初回1倍2_以降1倍0():
    """ステラ テラスタル中、不一致技は初回1.2倍、2回目以降1.0倍。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ステラ", moves=["ひのこ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()

    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    # 初回: 不一致 → 1.2倍
    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == pytest.approx(4915 / 4096)

    # 消費済みに設定してから再計算
    attacker.stellar_boosted_types.add("ほのお")
    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == pytest.approx(1.0)


def test_ステラ技_テラスタルポケモンへ効果抜群():
    """ステラタイプの技はテラスタル済みポケモンに対して2.0倍の相性補正。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ステラ", moves=["テラバースト"])],
        foe=[Pokemon("コイキング", terastal="みず")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()

    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)
    # テラバーストのタイプをステラに設定
    move_type = battle.move_executor.get_effective_move_type(attacker, move)
    move.set_type(move_type)

    ctx = BattleContext(attacker=attacker, defender=defender, move=move)

    # 非テラスタル相手: 等倍
    assert battle.damage_calculator.calc_def_type_modifier(ctx) == pytest.approx(1.0)

    # テラスタル相手: 効果抜群
    defender.terastallize()
    assert battle.damage_calculator.calc_def_type_modifier(ctx) == pytest.approx(2.0)

    move.unregister_handlers(battle.events, attacker)


def test_テラバースト_ステラ時に威力100():
    """ステラ テラスタル中のテラバーストは威力が100になる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ステラ", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()

    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    ctx = BattleContext(attacker=attacker, defender=defender, move=move)
    assert battle.damage_calculator.calc_final_power(ctx) == 100

    move.unregister_handlers(battle.events, attacker)


def test_テラバースト_非ステラ時は威力80():
    """通常テラスタル中のテラバーストは威力80のまま。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ほのお", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()

    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    ctx = BattleContext(attacker=attacker, defender=defender, move=move)
    assert battle.damage_calculator.calc_final_power(ctx) == 80

    move.unregister_handlers(battle.events, attacker)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
