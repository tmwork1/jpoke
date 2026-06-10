"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke.utils.type_defs import Type
from jpoke import Pokemon
from jpoke.core import EventContext

from . import test_utils as t


# ──────────────────────────────────────────────────────────────────
# テラスタル基礎性能
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("tera_type", "move", "expected"),
    [
        ("でんき", "でんきショック", 8192),
        ("ほのお", "ひのこ", 6144),
        ("ほのお", "でんきショック", 6144),
    ]
)
def test_攻撃側タイプ補正計算(tera_type: Type, move: str, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type=tera_type, move_names=[move])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == expected


@pytest.mark.parametrize(
    ("move_name", "tera_type", "expected"),
    [
        ("でんきショック", "でんき", 60),
        ("でんきショック", "ほのお", 40),
        ("でんこうせっか", "ノーマル", 40),
        ("にどげり", "かくとう", 30),
    ],
)
def test_威力底上げ(move_name: str, tera_type: Type, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type=tera_type, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == expected

# ──────────────────────────────────────────────────────────────────
# ステラ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("tera_type", "move", "expected_initial", "expected_after"),
    [
        ("ステラ", "でんきショック", 8192, 6144),
        ("ステラ", "ひのこ", 4915, 4096),
    ]
)
def test_ステラタイプ補正(tera_type: Type, move: str, expected_initial: int, expected_after: int):
    """ステラ テラスタル中、元タイプ一致技は初回2.0倍、2回目以降1.5倍。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type=tera_type, move_names=[move])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()

    # 初回
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == expected_initial

    # 消費済みに設定してから再計算
    attacker.stellar_boosted_types.add(attacker.moves[0].type)
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == expected_after


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
