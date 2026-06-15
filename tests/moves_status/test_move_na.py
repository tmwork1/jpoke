"""変化技ハンドラの単体テスト（な行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_なまける_HPが2分の1回復する():
    """なまける: 使用すると最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なまける"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_なまける_まんたんなら失敗():
    """なまける: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なまける"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp


def test_にほんばれ_おおあめ中は失敗する():
    """にほんばれ: おおあめ中は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にほんばれ"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおあめ", 99),
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "おおあめ"


def test_にほんばれ_天気がはれになる():
    """にほんばれ: 使用後に天気がはれになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にほんばれ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "はれ"
    assert battle.weather.count == 5


def test_ねばねばネット_すでに設置済みなら失敗():
    """ねばねばネット: すでにねばねばネットが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねばねばネット"])],
        team1=[Pokemon("カビゴン")],
        side1={"ねばねばネット": 1},
    )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)

    # 状態は継続（重複設置されない）
    assert side.fields["ねばねばネット"].is_active


def test_ねばねばネット_相手陣営に設置される():
    """ねばねばネット: 使用すると相手陣営にねばねばネットが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねばねばネット"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[1])
    assert side.fields["ねばねばネット"].is_active


def test_ねをはる_すでにねをはる状態なら失敗():
    """ねをはる: すでにねをはる状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねをはる"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"ねをはる": 1},
    )
    attacker = battle.actives[0]
    old_count = attacker.volatiles["ねをはる"].count
    t.run_move(battle, 0)

    # カウントは変わらない（重複付与されない）
    assert attacker.has_volatile("ねをはる")
    assert attacker.volatiles["ねをはる"].count == old_count


def test_ねをはる_ねをはる状態を付与する():
    """ねをはる: 使用すると自分をねをはる状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねをはる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("ねをはる")
