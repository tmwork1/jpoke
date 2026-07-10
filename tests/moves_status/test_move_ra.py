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

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spe"] == 1


def test_りゅうのまい_こうげき最大でもすばやさは上昇する():
    """りゅうのまい: こうげきがすでに+6でも、すばやさは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 6
    assert attacker.rank["spe"] == 1


def test_りゅうのまい_マジックコートで跳ね返されない():
    """りゅうのまい: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spe"] == 1
    assert defender.rank["atk"] == 0
    assert defender.rank["spe"] == 0


def test_りゅうのまい_自分対象のためまもるで防がれない():
    """りゅうのまい: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spe"] == 1


def test_ロックオン_自分にロックオン状態が付与される():
    """ロックオン: 使用すると相手ではなく自分にロックオン状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ロックオン"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.has_volatile("ロックオン")
    assert not defender.has_volatile("ロックオン")


def test_ロックオン_すでにロックオン状態なら失敗する():
    """ロックオン: すでに自分がロックオン状態の場合、再使用しても失敗する（カウントは変わらない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ロックオン"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"ロックオン": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.volatiles["ロックオン"].count == 1


def test_ロックオン_まもるで防がれる():
    """ロックオン: まもる状態の相手に使うと防がれ、ロックオン状態が付与されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ロックオン"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.has_volatile("ロックオン")


def test_ロックオン_マジックコートで跳ね返されない():
    """ロックオン: unreflectableフラグを持つため、マジックコート状態の相手に使っても跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ロックオン"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.has_volatile("ロックオン")
    assert not defender.has_volatile("ロックオン")
