"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke.utils.type_defs import Type
from jpoke import Pokemon
from jpoke.core import BattleContext

import test_utils as t


# ──────────────────────────────────────────────────────────────────
# テラスタル基礎性能
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("tera_type", "move", "expected"),
    [
        ("でんき", "でんきショック", 2.0),
        ("ほのお", "ひのこ", 1.5),
        ("ほのお", "でんきショック", 1.5),
    ]
)
def test_攻撃側タイプ補正計算(tera_type: Type, move: str, expected: int):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type=tera_type, moves=[move])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == expected


@pytest.mark.parametrize(
    ("move_name", "tera_type", "expected"),
    [
        ("でんきショック", "でんき", 60),
        ("でんきショック", "ほのお", 40),
        ("でんこうせっか", "ノーマル", 40),
        ("にどげり", "かくとう", 30),
    ],
)
def test_威力底上げ(move_name: str,
               tera_type: Type,
               expected: int):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type=tera_type, moves=[move_name])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()
    move = attacker.moves[0]
    ctx = BattleContext(attacker=attacker, defender=defender, move=move)
    assert battle.damage_calculator.calc_final_power(ctx) == expected

# ──────────────────────────────────────────────────────────────────
# ステラ
# ──────────────────────────────────────────────────────────────────


def test_ステラSTAB_元タイプ一致_初回2倍_以降1倍5():
    """ステラ テラスタル中、元タイプ一致技は初回2.0倍、2回目以降1.5倍。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type="ステラ", moves=["でんきショック"])],
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
        ally=[Pokemon("ピカチュウ", tera_type="ステラ", moves=["ひのこ"])],
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
