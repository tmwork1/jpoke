"""変化技ハンドラの単体テスト（ら行・リ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_リフレクター_すでにアクティブなら失敗():
    """リフレクター: すでにリフレクターが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リフレクター"])],
        team1=[Pokemon("カビゴン")],
        side0={"リフレクター": 4},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["リフレクター"].is_active
    assert side.fields["リフレクター"].count == 4


def test_リフレクター_自陣営に5ターン設置される():
    """リフレクター: 使用すると自陣営に5ターンのリフレクターが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リフレクター"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["リフレクター"].is_active
    assert side.fields["リフレクター"].count == 5


def test_りゅうのまい_こうげきとすばやさ1段階ずつ上がる():
    """りゅうのまい: 使用すると自分のこうげきとすばやさランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["S"] == 1


def test_りゅうのまい_こうげき最大でもすばやさは上昇する():
    """りゅうのまい: こうげきがすでに+6でも、すばやさは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["A"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6
    assert attacker.rank["S"] == 1
