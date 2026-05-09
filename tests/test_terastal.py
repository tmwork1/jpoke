"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import BattleContext

import test_utils as t


# ──────────────────────────────────────────────────────────────────
# テラスタル基礎性能
# ──────────────────────────────────────────────────────────────────
# TODO : terastallizeフラグは削除
@pytest.mark.parametrize(
    ("attacker", "terastallize", "expected"),
    [
        (Pokemon("ピカチュウ", terastal="でんき", moves=["でんきショック"]), True, 2.0),
        (Pokemon("ピカチュウ", terastal="ほのお", moves=["ひのこ"]), True, 1.5),
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


# TODO : terastallizeフラグは削除
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

# ──────────────────────────────────────────────────────────────────
# ステラ
# ──────────────────────────────────────────────────────────────────


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
