"""変化技ハンドラの単体テスト（お行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_おいかぜ_すでにおいかぜなら失敗():
    """おいかぜ: すでにおいかぜが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいかぜ"])],
        team1=[Pokemon("カビゴン")],
        side0={"おいかぜ": 3},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["おいかぜ"].is_active
    assert side.fields["おいかぜ"].count == 3


def test_おいかぜ_自陣営に4ターン設置される():
    """おいかぜ: 使用すると自陣営に4ターンのおいかぜが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいかぜ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["おいかぜ"].is_active
    assert side.fields["おいかぜ"].count == 4


def test_おたけび_こうげきとくこう1段階ずつ下がる():
    """おたけび: 相手のこうげきととくこうランクが1段階ずつ下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おたけび"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["A"] == -1
    assert defender.rank["C"] == -1


def test_おたけび_すでに最低ランクなら変化なし():
    """おたけび: こうげき・とくこうがともにすでに-6ならランク変化なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おたけび"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"A": -6, "C": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["A"] == -6
    assert defender.rank["C"] == -6


def test_おだてる_すでにこんらんかつとくこう最大なら失敗():
    """おだてる: とくこうが+6かつこんらん済みなら技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"C": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    # とくこうは変化せず、こんらんも新たに付与されない
    assert defender.rank["C"] == 6
    assert defender.volatiles["こんらん"].count == 3


def test_おだてる_とくこう1段階上がりこんらん付与():
    """おだてる: 相手のとくこうが1段階上がり、こんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["C"] == 1
    assert defender.has_volatile("こんらん")
