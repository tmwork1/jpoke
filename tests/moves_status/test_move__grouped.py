"""フィールド展開技のまとめテスト。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


@pytest.mark.parametrize("terrain_name,move_name", [
    ("エレキフィールド", "エレキフィールド"),
    ("グラスフィールド", "グラスフィールド"),
    ("サイコフィールド", "サイコフィールド"),
    ("ミストフィールド", "ミストフィールド"),
])
def test_フィールド展開技_5ターン展開される(terrain_name, move_name):
    """フィールド展開技: 使用すると5ターンのフィールドが展開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 5


@pytest.mark.parametrize("terrain_name,move_name", [
    ("エレキフィールド", "エレキフィールド"),
    ("グラスフィールド", "グラスフィールド"),
    ("サイコフィールド", "サイコフィールド"),
    ("ミストフィールド", "ミストフィールド"),
])
def test_フィールド展開技_すでに同じフィールドなら失敗(terrain_name, move_name):
    """フィールド展開技: すでに同じフィールド中は発動しない（失敗）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
        terrain=(terrain_name, 5),
    )
    t.run_move(battle, 0)

    # カウントは変わらない（再発動されない）
    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 5
