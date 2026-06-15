"""変化技ハンドラの単体テスト（た行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_たてこもる_ぼうぎょ2段階上がる():
    """たてこもる: 使用すると自分のぼうぎょランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たてこもる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["B"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 2


def test_たてこもる_ぼうぎょ最大なら変化なし():
    """たてこもる: ぼうぎょがすでに+6なら効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たてこもる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["B"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 6


def test_ちょうのまい_1つでも上昇できれば成功():
    """ちょうのまい: とくこうが最大でも、とくぼうとすばやさは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["C"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["C"] == 6
    assert attacker.rank["D"] == 1
    assert attacker.rank["S"] == 1


def test_ちょうのまい_とくこうととくぼうとすばやさ1段階ずつ上がる():
    """ちょうのまい: 使用すると自分のとくこう・とくぼう・すばやさランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["C"] == 1
    assert attacker.rank["D"] == 1
    assert attacker.rank["S"] == 1


def test_ちょうはつ_すでにちょうはつ状態なら失敗():
    """ちょうはつ: 相手がすでにちょうはつ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうはつ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"ちょうはつ": 2},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # カウントは変わらない（重複付与されない）
    assert defender.has_volatile("ちょうはつ")
    assert defender.volatiles["ちょうはつ"].count == 2


def test_ちょうはつ_ちょうはつ状態を付与する():
    """ちょうはつ: 相手にちょうはつ揮発性状態を付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうはつ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("ちょうはつ")


def test_つきのひかり_あめで4分の1回復():
    """つきのひかり: あめ中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つきのひかり"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_つきのひかり_はれで3分の2回復():
    """つきのひかり: はれ中は最大HPの2/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つきのひかり"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 2 / 3)


def test_つきのひかり_まんたんなら失敗():
    """つきのひかり: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つきのひかり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp


def test_つきのひかり_通常天候で2分の1回復():
    """つきのひかり: 通常天候では最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つきのひかり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_つぶらなひとみ_こうげき最低なら変化なし():
    """つぶらなひとみ: 相手のこうげきがすでに-6ならランク変化なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぶらなひとみ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"A": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["A"] == -6


def test_つぶらなひとみ_相手のこうげき1段階下がる():
    """つぶらなひとみ: 相手のこうげきランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぶらなひとみ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["A"] == -1


def test_つるぎのまい_こうげき2段階上がる():
    """つるぎのまい: 使用すると自分のこうげきランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["A"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 2


def test_つるぎのまい_こうげき最大なら変化なし():
    """つるぎのまい: こうげきがすでに+6なら効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["A"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6


def test_てんしのキッス_こんらん状態を付与する():
    """てんしのキッス: 相手をこんらん状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["てんしのキッス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")


def test_てんしのキッス_すでにこんらん状態なら失敗():
    """てんしのキッス: 相手がすでにこんらん状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["てんしのキッス"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["こんらん"].count
    t.run_move(battle, 0)

    # カウントは変わらない（重複付与されない）
    assert defender.has_volatile("こんらん")
    assert defender.volatiles["こんらん"].count == old_count


def test_でんじふゆう_すでにでんじふゆう状態なら失敗():
    """でんじふゆう: すでにでんじふゆう状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじふゆう"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"でんじふゆう": 5},
    )
    attacker = battle.actives[0]
    old_count = attacker.volatiles["でんじふゆう"].count
    t.run_move(battle, 0)

    assert attacker.has_volatile("でんじふゆう")
    assert attacker.volatiles["でんじふゆう"].count == old_count


def test_でんじふゆう_でんじふゆう状態を付与する():
    """でんじふゆう: 使用すると自分をでんじふゆう状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじふゆう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("でんじふゆう")


def test_とおせんぼう_すでににげられない状態なら失敗():
    """とおせんぼう: 相手がすでににげられない状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とおせんぼう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"にげられない": 1},
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["にげられない"].count
    t.run_move(battle, 0)

    assert defender.has_volatile("にげられない")
    assert defender.volatiles["にげられない"].count == old_count


def test_とおせんぼう_にげられない状態を付与する():
    """とおせんぼう: 相手をにげられない状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とおせんぼう"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("にげられない")


def test_とおぼえ_こうげき1段階上がる():
    """とおぼえ: 使用すると自分のこうげきランクが1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とおぼえ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1


def test_とおぼえ_こうげき最大なら変化なし():
    """とおぼえ: こうげきがすでに+6なら効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とおぼえ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["A"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6


def test_とぐろをまく_1つでも上昇できれば成功():
    """とぐろをまく: こうげきが最大でも、ぼうぎょと命中率は上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とぐろをまく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["A"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6
    assert attacker.rank["B"] == 1
    assert attacker.rank["ACC"] == 1


def test_とぐろをまく_こうげきとぼうぎょと命中率1段階ずつ上がる():
    """とぐろをまく: 使用すると自分のこうげき・ぼうぎょ・命中率ランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とぐろをまく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["B"] == 1
    assert attacker.rank["ACC"] == 1


def test_とける_ぼうぎょ2段階上がる():
    """とける: 使用すると自分のぼうぎょランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とける"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["B"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 2


def test_とける_ぼうぎょ最大なら変化なし():
    """とける: ぼうぎょがすでに+6なら効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とける"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["B"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 6


def test_どくのいと_すでにどく状態ならS下げのみ():
    """どくのいと: 相手がすでにどく状態でもすばやさは下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくのいと"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("どく", None),
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["S"] == -1
    assert defender.has_ailment("どく")


def test_どくのいと_すばやさ1段階下がりどく付与():
    """どくのいと: 相手のすばやさが1段階下がり、どく状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくのいと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["S"] == -1
    assert defender.has_ailment("どく")


def test_どくびし_すでに設置済みなら失敗():
    """どくびし: すでにどくびしが設置済みなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくびし"])],
        team1=[Pokemon("カビゴン")],
        side1={"どくびし": 1},
    )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)

    assert side.fields["どくびし"].is_active
    assert side.fields["どくびし"].count == 1


def test_どくびし_相手陣営に設置される():
    """どくびし: 使用すると相手陣営にどくびしが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくびし"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[1])
    assert side.fields["どくびし"].is_active
