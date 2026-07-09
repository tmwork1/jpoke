"""変化技ハンドラの単体テスト（た行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


@pytest.mark.parametrize("count", [1, 2, 3])
def test_たくわえる_N回使用でカウントがNになる(count):
    """たくわえる: N回使用するとたくわえカウントがNになり、ぼうぎょとくぼうがN段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たくわえる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    for _ in range(count):
        t.run_move(battle, 0)

    assert attacker.has_volatile("たくわえる")
    assert attacker.volatiles["たくわえる"].count == count
    assert attacker.rank["def"] == count
    assert attacker.rank["spd"] == count


def test_たくわえる_カウント3で失敗する():
    """たくわえる: たくわえカウントがすでに3なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たくわえる"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 3},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    # カウントは3のまま変わらない
    assert attacker.volatiles["たくわえる"].count == 3


def test_たくわえる_マジックコートで跳ね返されない():
    """たくわえる: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たくわえる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.has_volatile("たくわえる")
    assert attacker.volatiles["たくわえる"].count == 1
    assert not defender.has_volatile("たくわえる")


def test_たくわえる_まもるで防がれない():
    """たくわえる: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たくわえる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("たくわえる")
    assert attacker.volatiles["たくわえる"].count == 1
    assert attacker.rank["def"] == 1
    assert attacker.rank["spd"] == 1


def test_たてこもる_ぼうぎょ2段階上がる():
    """たてこもる: 使用すると自分のぼうぎょランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たてこもる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["def"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2


def test_たてこもる_自分対象のためまもるで防がれない():
    """たてこもる: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たてこもる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2


def test_タールショット_すでにタールショット状態でもSは下がる():
    """タールショット: 相手がすでにタールショット状態でもすばやさは1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タールショット"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"タールショット": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # タールショット状態は重複付与されない
    assert defender.has_volatile("タールショット")
    # すばやさは下がる（どくのいとのすでにどく状態と同様）
    assert defender.rank["spe"] == -1


def test_タールショット_すばやさ1段階下がりタールショット状態付与():
    """タールショット: 相手のすばやさが1段階下がり、タールショット状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タールショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spe"] == -1
    assert defender.has_volatile("タールショット")


def test_ちいさくなる_マジックコートで跳ね返されない():
    """ちいさくなる: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちいさくなる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.rank["evasion"] == 2
    assert attacker.has_volatile("ちいさくなる")
    assert defender.rank["evasion"] == 0
    assert not defender.has_volatile("ちいさくなる")


def test_ちいさくなる_まもるで防がれない():
    """ちいさくなる: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちいさくなる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["evasion"] == 2
    assert attacker.has_volatile("ちいさくなる")


def test_ちいさくなる_回避率2段階上がりちいさくなる状態を付与する():
    """ちいさくなる: 自分の回避率が2段階上がり、ちいさくなる状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちいさくなる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["evasion"] == 2
    assert attacker.has_volatile("ちいさくなる")


def test_ちからをすいとる_クリアボディでランク低下阻止でもHP回復は発動():
    """ちからをすいとる: クリアボディでランク低下が阻まれても回復効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ちからをすいとる"])],
        team1=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    hp_before = 1
    attacker.hp = hp_before
    expected_recovery = defender.stats["atk"]
    t.run_move(battle, 0)

    # クリアボディでランク低下は阻まれる
    assert defender.rank["atk"] == 0
    # それでも回復は発動する
    assert attacker.hp == hp_before + expected_recovery


def test_ちからをすいとる_こうげきランク最低で失敗():
    """ちからをすいとる: 相手のこうげきランクがすでに-6なら失敗する（HP回復も発動しない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちからをすいとる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.modify_stats(defender, {"atk": -6}, source=attacker)
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)

    assert attacker.hp == hp_before
    assert defender.rank["atk"] == -6


def test_ちからをすいとる_相手のランク補正込みA実数値だけ回復してAを下げる():
    """ちからをすいとる: 相手のこうげきランクが+1のとき、回復量はranked_stats["atk"]（補正済み）になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ちからをすいとる"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    # ランクを+1に設定（補正倍率 3/2）
    battle.modify_stats(defender, {"atk": 1}, source=defender)
    assert defender.rank["atk"] == 1
    hp_before = 1
    attacker.hp = hp_before
    # ランク補正済みの期待値
    expected_recovery = defender.ranked_stats["atk"]
    t.run_move(battle, 0)

    assert attacker.hp == hp_before + expected_recovery
    assert defender.rank["atk"] == 0


def test_ちからをすいとる_ヘドロえきで回復がダメージに変換される():
    """ちからをすいとる: 相手がヘドロえき持ちの場合、回復の代わりに使用者がダメージを受ける
    （reason="drain" を経由することでヘドロえきのドレイン反転処理が発動する）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ちからをすいとる"])],
        team1=[Pokemon("ピカチュウ", ability_name="ヘドロえき")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    hp_before = attacker.hp
    t.run_move(battle, 0)

    # 回復ではなくダメージを受ける
    assert attacker.hp < hp_before
    # こうげきランクは通常通り下がる
    assert defender.rank["atk"] == -1


def test_ちょうおんぱ_こんらん状態を付与する():
    """ちょうおんぱ: 相手をこんらん状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうおんぱ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")


def test_ちょうおんぱ_すでにこんらん状態なら失敗():
    """ちょうおんぱ: 相手がすでにこんらん状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうおんぱ"])],
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


def test_ちょうおんぱ_みがわりを貫通する():
    """ちょうおんぱ: 音技のため、みがわりを貫通してこんらん状態を付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうおんぱ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("みがわり")
    assert defender.has_volatile("こんらん")


def test_ちょうのまい_1つでも上昇できれば成功():
    """ちょうのまい: とくこうが最大でも、とくぼうとすばやさは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["spa"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["spa"] == 6
    assert attacker.rank["spd"] == 1
    assert attacker.rank["spe"] == 1


def test_ちょうのまい_とくこうととくぼうとすばやさ1段階ずつ上がる():
    """ちょうのまい: 使用すると自分のとくこう・とくぼう・すばやさランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["spa"] == 1
    assert attacker.rank["spd"] == 1
    assert attacker.rank["spe"] == 1


def test_ちょうのまい_マジックコートで跳ね返されない():
    """ちょうのまい: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうのまい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.rank["spa"] == 1
    assert attacker.rank["spd"] == 1
    assert attacker.rank["spe"] == 1
    assert defender.rank["spa"] == 0
    assert defender.rank["spd"] == 0
    assert defender.rank["spe"] == 0


def test_ちょうのまい_自分対象のためまもるで防がれない():
    """ちょうのまい: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうのまい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["spa"] == 1
    assert attacker.rank["spd"] == 1
    assert attacker.rank["spe"] == 1


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


@pytest.mark.parametrize("weather_arg,numerator,denominator", [
    (None,          1, 2),  # 通常天候: 1/2 回復
    (("あめ",  5), 1, 4),  # あめ: 1/4 回復
    (("はれ",  5), 2, 3),  # はれ: 2/3 回復
])
def test_つきのひかり_天候別回復量(weather_arg, numerator, denominator):
    """つきのひかり: 天候ごとに回復量が変わる（通常1/2, はれ2/3, あめ1/4）"""
    kwargs = {}
    if weather_arg is not None:
        kwargs["weather"] = weather_arg
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つきのひかり"])],
        team1=[Pokemon("カビゴン")],
        **kwargs,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * numerator / denominator)


def test_つぶらなひとみ_相手のこうげき1段階下がる():
    """つぶらなひとみ: 相手のこうげきランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぶらなひとみ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1


def test_つぼをつく_選ばれない能力のランクは変化しない():
    """つぼをつく: ランダムで選ばれた1種類以外の能力ランクは変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.random.choice = lambda seq: "def"
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2
    assert attacker.rank["atk"] == 0
    assert attacker.rank["spa"] == 0
    assert attacker.rank["spd"] == 0
    assert attacker.rank["spe"] == 0
    assert attacker.rank["accuracy"] == 0
    assert attacker.rank["evasion"] == 0


def test_つららおとし_ひるみが発動する():
    """つららおとし: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("マンムー", move_names=["つららおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_つるぎのまい_こうげき2段階上がる():
    """つるぎのまい: 使用すると自分のこうげきランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["atk"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 2


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

    assert attacker.rank["atk"] == 1


def test_とぐろをまく_1つでも上昇できれば成功():
    """とぐろをまく: こうげきが最大でも、ぼうぎょと命中率は上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とぐろをまく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 6
    assert attacker.rank["def"] == 1
    assert attacker.rank["accuracy"] == 1


def test_とぐろをまく_こうげきとぼうぎょと命中率1段階ずつ上がる():
    """とぐろをまく: 使用すると自分のこうげき・ぼうぎょ・命中率ランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とぐろをまく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1
    assert attacker.rank["accuracy"] == 1


def test_とける_ぼうぎょ2段階上がる():
    """とける: 使用すると自分のぼうぎょランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とける"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["def"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2


def test_どくガス_どくタイプには無効():
    """どくガス: どくタイプの相手には効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくガス"])],
        team1=[Pokemon("ベトベトン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_ailment("どく")


def test_どくガス_どく状態にする():
    """どくガス: 命中すると相手を『どく』状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくガス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("どく")


def test_どくガス_命中率90で外れることがある():
    """どくガス: 命中率90のため外れる場合がある"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくガス"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.fix_random(battle, 0.95)
    t.run_move(battle, 0)

    assert not defender.has_ailment("どく")


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

    assert defender.rank["spe"] == -1
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

    assert defender.rank["spe"] == -1
    assert defender.has_ailment("どく")


@pytest.mark.parametrize("initial_count,expected_count", [
    (0, 1),  # 未設置 → 1層目
    (1, 2),  # 1層 → 2層（最大）
    (2, 2),  # 最大層では変化なし（失敗）
])
def test_どくびし_カウント累積(initial_count: int, expected_count: int):
    """どくびし: count=0~2の各状態から使用したときのカウント変化を検証する"""
    if initial_count == 0:
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["どくびし"])],
            team1=[Pokemon("カビゴン")],
        )
    else:
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["どくびし"])],
            team1=[Pokemon("カビゴン")],
            side1={"どくびし": initial_count},
        )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)
    assert side.fields["どくびし"].count == expected_count


def test_どくびし_相手陣営に設置される():
    """どくびし: 使用すると相手陣営にどくびしが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくびし"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[1])
    assert side.fields["どくびし"].is_active


def test_ドラゴンダイブ_ひるみが発動する():
    """ドラゴンダイブ: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー", move_names=["ドラゴンダイブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")
