"""変化技ハンドラの単体テスト（あ行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_アクアリング_すでに付与済みなら失敗する():
    """アクアリング: すでにアクアリング状態なら効果を上書きしない（失敗扱い）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アクアリング"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"アクアリング": 1},
    )
    attacker = battle.actives[0]
    result = t.run_move(battle, 0)

    # 状態は維持されたまま（重複付与されない）
    assert attacker.has_volatile("アクアリング")


def test_アクアリング_揮発性状態が付与される():
    """アクアリング: 使用するとアクアリング揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アクアリング"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("アクアリング")


def test_あくび_すでにねむけ状態なら失敗():
    """あくび: 対象がすでにねむけ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"ねむけ": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    # ねむけは継続したまま（2つ目のねむけは付かない）
    assert defender.has_volatile("ねむけ")


def test_あくび_すでに状態異常なら失敗():
    """あくび: 対象がすでに状態異常を持っているなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert not defender.has_volatile("ねむけ")
    assert defender.has_ailment("まひ")


def test_あくび_ターン終了でねむりになる():
    """あくび: 付与ターン終了時にねむり状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    # 付与ターン終了時にねむりになる
    t.end_turn(battle)
    assert not defender.has_volatile("ねむけ")
    assert defender.has_ailment("ねむり")


def test_あくび_ねむけ付与():
    """あくび: 相手をねむけ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_volatile("ねむけ")
    assert not defender.has_ailment("ねむり")


def test_あくまのキッス_すでに状態異常なら失敗():
    """あくまのキッス: 対象がすでに状態異常を持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくまのキッス"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_ailment("まひ")
    assert not defender.has_ailment("ねむり")


def test_あくまのキッス_ねむり付与():
    """あくまのキッス: 相手をねむり状態に直接する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくまのキッス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")


def test_あさのひざし_あめで4分の1回復():
    """あさのひざし: あめ中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_あさのひざし_おおあめで4分の1回復():
    """あさのひざし: おおあめ中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおあめ", 99),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_あさのひざし_おおひでりで3分の2回復():
    """あさのひざし: おおひでり中は最大HPの2/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 2 / 3)


def test_あさのひざし_すなあらしで4分の1回復():
    """あさのひざし: すなあらし中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("すなあらし", 99),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_あさのひざし_はれで3分の2回復():
    """あさのひざし: はれ中は最大HPの2/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 2 / 3)


def test_あさのひざし_まんたんなら失敗():
    """あさのひざし: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_あさのひざし_ゆきで4分の1回復():
    """あさのひざし: ゆき中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("ゆき", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_あさのひざし_通常天候で2分の1回復():
    """あさのひざし: 通常天候では最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_あまごい_おおひでり中は失敗する():
    """あまごい: おおひでり中は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "おおひでり"


def test_あまごい_天気があめになる():
    """あまごい: 使用後に天気があめになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "あめ"
    assert battle.weather.count == 5


def test_あやしいひかり_こんらん付与():
    """あやしいひかり: 相手をこんらん状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あやしいひかり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.random.randint = lambda a, b: 3
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")
    assert defender.volatiles["こんらん"].count == 3


def test_あやしいひかり_すでにこんらん中は失敗():
    """あやしいひかり: 対象がすでにこんらん状態なら失敗する（重複付与しない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あやしいひかり"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 4},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # カウントは変わらない（重複付与されない）
    assert defender.has_volatile("こんらん")
    assert defender.volatiles["こんらん"].count == 4


def test_アロマミスト_とくぼう上昇():
    """アロマミスト: 使用者のとくぼうが1段階上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アロマミスト"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["D"] == 0
    t.run_move(battle, 0)
    assert attacker.rank["D"] == 1


def test_アロマミスト_とくぼう最大なら失敗():
    """アロマミスト: とくぼうがすでに+6なら効果がない（失敗）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アロマミスト"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["D"] = 6
    t.run_move(battle, 0)
    assert attacker.rank["D"] == 6


def test_おにび_すでに状態異常なら失敗():
    """おにび: 対象がすでに状態異常を持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # まひのまま変わっていないことを確認
    assert battle.actives[1].ailment.name == "まひ"


def test_おにび_ほのおタイプには無効():
    """おにび: ほのおタイプの相手には無効（単タイプ）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("ヒトカゲ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_おにび_やけど付与():
    """おにび: 相手をやけど状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_おにび_複合ほのおタイプにも無効():
    """おにび: ほのお複合タイプの相手にも無効（ファイアロー: ほのお+ひこう）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("ファイアロー")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active
