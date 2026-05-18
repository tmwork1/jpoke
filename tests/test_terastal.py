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

    assert battle.damage_calculator._calc_atk_type_modifier(ctx) == expected


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
    assert battle.damage_calculator._calc_final_power(ctx) == expected

# ──────────────────────────────────────────────────────────────────
# ステラ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("tera_type", "move", "expected"),
    [
        ("ステラ", "でんきショック", 8192, 6144),
        ("ステラ", "ひのこ", 4915, 4096),
    ]
)
def test_ステラタイプ補正(tera_type: Type, move: str, expected_initial: int, expected_after: int):
    """ステラ テラスタル中、元タイプ一致技は初回2.0倍、2回目以降1.5倍。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type=tera_type, moves=[move])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()

    # 初回
    battle.run_move(attacker, attacker.moves[0])
    assert battle.damage_calculator.atk_type_modifier == expected_initial

    # 消費済みに設定してから再計算
    attacker.stellar_boosted_types.add(attacker.moves[0].type)
    battle.run_move(attacker, attacker.moves[0])
    assert battle.damage_calculator.atk_type_modifier == expected_after


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
