"""変化技ハンドラの単体テスト（は行・ビ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_はらだいこ_こうげきすでに最大なら失敗():
    """はらだいこ: こうげきランクがすでに+6なら失敗し、HPは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["A"] = 6
    hp_before = attacker.hp
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6
    assert attacker.hp == hp_before


def test_はらだいこ_こうげき最大化しHP半分消費():
    """はらだいこ: こうげきランクが+6になり最大HPの半分が消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6
    assert attacker.hp == max_hp - (max_hp // 2)


def test_ひかりのかべ_すでにアクティブなら失敗():
    """ひかりのかべ: すでにひかりのかべが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひかりのかべ"])],
        team1=[Pokemon("カビゴン")],
        side0={"ひかりのかべ": 4},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["ひかりのかべ"].is_active
    assert side.fields["ひかりのかべ"].count == 4


def test_ひかりのかべ_自陣営に5ターン設置される():
    """ひかりのかべ: 使用すると自陣営に5ターンのひかりのかべが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひかりのかべ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["ひかりのかべ"].is_active
    assert side.fields["ひかりのかべ"].count == 5


def test_ビルドアップ_こうげきとぼうぎょ1段階ずつ上がる():
    """ビルドアップ: 使用すると自分のこうげきとぼうぎょランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ビルドアップ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["A"] == 0
    assert attacker.rank["B"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["B"] == 1


def test_ビルドアップ_こうげき最大でもぼうぎょは上昇する():
    """ビルドアップ: こうげきがすでに+6でも、ぼうぎょは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ビルドアップ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["A"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6
    assert attacker.rank["B"] == 1


def test_フラフラダンス_こんらん状態を付与する():
    """フラフラダンス: 相手をこんらん状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フラフラダンス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")


def test_フラフラダンス_すでにこんらん状態なら失敗():
    """フラフラダンス: 相手がすでにこんらん状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フラフラダンス"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["こんらん"].count
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")
    assert defender.volatiles["こんらん"].count == old_count
