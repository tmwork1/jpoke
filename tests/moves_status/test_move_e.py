"""変化技ハンドラの単体テスト（え行・エ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_エレキフィールド_すでに同じフィールドなら失敗():
    """エレキフィールド: すでにエレキフィールド中は発動しない（失敗）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキフィールド"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
    )
    t.run_move(battle, 0)

    # カウントは変わらない（再発動されない）
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5


def test_エレキフィールド_フィールドが5ターン展開される():
    """エレキフィールド: 使用すると5ターンのエレキフィールドが展開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキフィールド"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
