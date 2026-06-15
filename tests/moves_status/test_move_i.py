"""変化技ハンドラの単体テスト（い行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_いとをはく_すでに最低ランクなら変化なし():
    """いとをはく: 相手のすばやさがすでに-6ならランク変化なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いとをはく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"S": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["S"] == -6


def test_いとをはく_すばやさ2段階下がる():
    """いとをはく: 相手のすばやさランクが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いとをはく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["S"] == -2


def test_いばる_こうげき2段階上がりこんらん付与():
    """いばる: 相手のこうげきが2段階上がり、こんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["A"] == 2
    assert defender.has_volatile("こんらん")


def test_いばる_こうげき最大でもこんらん未付与なら成功():
    """いばる: こうげきが+6でもこんらん状態でなければ技は成功しこんらんを付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"A": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["A"] == 6
    assert defender.has_volatile("こんらん")


def test_いばる_すでにこんらんかつこうげき最大なら失敗():
    """いばる: こうげきが+6かつこんらん済みなら技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    # こうげきを+6にする
    battle.modify_stats(defender, {"A": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    # こうげきは変化せず、こんらんも新たに付与されない
    assert defender.rank["A"] == 6
    assert defender.volatiles["こんらん"].count == 3  # カウント変わらず
