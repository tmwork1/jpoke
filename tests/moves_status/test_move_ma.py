"""変化技ハンドラの単体テスト（ま行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_まきびし_すでに設置済みなら失敗():
    """まきびし: すでにまきびしが設置済みなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
        team1=[Pokemon("カビゴン")],
        side1={"まきびし": 1},
    )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["まきびし"].is_active
    assert side.fields["まきびし"].count == 1


def test_まきびし_相手陣営に設置される():
    """まきびし: 使用すると相手陣営にまきびしが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[1])
    assert side.fields["まきびし"].is_active


def test_めいそう_とくこうととくぼう1段階ずつ上がる():
    """めいそう: 使用すると自分のとくこうとぼうぎょランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["めいそう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["C"] == 0
    assert attacker.rank["D"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["C"] == 1
    assert attacker.rank["D"] == 1


def test_めいそう_とくこう最大でもとくぼうは上昇する():
    """めいそう: とくこうがすでに+6でも、とくぼうは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["めいそう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["C"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["C"] == 6
    assert attacker.rank["D"] == 1


def test_メロメロ_すでにメロメロ状態なら失敗():
    """メロメロ: 相手がすでにメロメロ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="オス")],
        team1=[Pokemon("カビゴン", gender="メス")],
        volatile1={"メロメロ": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["メロメロ"].count
    t.run_move(battle, 0)

    assert defender.has_volatile("メロメロ")
    assert defender.volatiles["メロメロ"].count == old_count


def test_メロメロ_異なる性別なら付与される():
    """メロメロ: 自分と異なる性別の相手をメロメロ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="オス")],
        team1=[Pokemon("カビゴン", gender="メス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("メロメロ")


def test_もりののろい_すでにくさタイプなら失敗():
    """もりののろい: 相手がすでにくさタイプなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("フシギバナ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # くさタイプには付与されない
    assert not defender.has_volatile("もりののろい")


def test_もりののろい_もりののろい状態を付与する():
    """もりののろい: 相手にもりののろい状態を付与する（くさタイプが追加される）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("もりののろい")
