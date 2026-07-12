"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke.types import Type
from jpoke import Pokemon

from . import test_utils as t


def test_terastallize_戻り値はNone():
    """Pokemon.terastallize()は`is_terastallized`を立てるだけの内部メソッドであり、
    戻り値は常にNone（成功/失敗を示すbool値ではない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="でんき")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    result = attacker.terastallize()
    assert result is None
    assert attacker.is_terastallized is True


def test_グラススライダー_テラスタルで威力60に底上げされる():
    """グラススライダー: くさタイプにテラスタルすると威力60底上げ補正が適用される。
    技自体の基本優先度は0（グラスフィールド下でのみ動的に+1される）であり、
    でんこうせっかのような固定優先度+1の技とは異なり底上げ補正の除外対象にならない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ゴリランダー", tera_type="くさ", move_names=["グラススライダー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 60


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
