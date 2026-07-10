"""変化技ハンドラの単体テスト（た行）。"""

import pytest
from jpoke import Pokemon
from jpoke.data.move import MOVES
from jpoke.enums import Interrupt, LogCode
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


def test_タマゴうみ_マジックコートで跳ね返されない():
    """タマゴうみ: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タマゴうみ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    defender_hp = defender.hp
    t.run_move(battle, 0)
    assert attacker.hp > 1
    assert defender.hp == defender_hp


def test_タマゴうみ_まもるで防がれない():
    """タマゴうみ: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タマゴうみ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp > 1


def test_タマゴうみ_まんたんなら失敗():
    """タマゴうみ: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タマゴうみ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_タマゴうみ_最大HPの半分回復する():
    """タマゴうみ: 自分のHPを最大HPの1/2分回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タマゴうみ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + attacker.max_hp // 2


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


def test_タールショット_マジックコートで跳ね返される():
    """タールショット: マジックコートで跳ね返されると、使用者自身のすばやさが下がりタールショット状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タールショット"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.rank["spe"] == -1
    assert attacker.has_volatile("タールショット")
    assert defender.rank["spe"] == 0
    assert not defender.has_volatile("タールショット")


def test_タールショット_まもるで防がれる():
    """タールショット: 対象がまもる状態のときは防がれ、すばやさもタールショット状態も変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タールショット"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spe"] == 0
    assert not defender.has_volatile("タールショット")


def test_ダークホール_ダークライ以外が使用すると失敗する():
    """ダークホール: 第七世代以降、ダークライ以外が使用すると必ず失敗する（種族制限）。
    本プロジェクトのPOKEDEXにダークライが未収録のため、成功ケースはテストできない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ダークホール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_ailment("ねむり")


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


def test_ちょうはつ_みがわり状態の相手にも効果が発動する():
    """ちょうはつ: bypass_substituteフラグを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうはつ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("ちょうはつ")


def test_つきのひかり_マジックコートで跳ね返されない():
    """つきのひかり: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つきのひかり"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    defender_hp = defender.hp
    t.run_move(battle, 0)

    assert attacker.hp > 1
    assert defender.hp == defender_hp


def test_つきのひかり_まもるで防がれない():
    """つきのひかり: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つきのひかり"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp > 1


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
    (None,               1, 2),  # 通常天候: 1/2 回復
    (("あめ",      5),  1, 4),  # あめ: 1/4 回復
    (("おおあめ", 99),  1, 4),  # おおあめ: 1/4 回復
    (("おおひでり", 99), 2, 3),  # おおひでり: 2/3 回復
    (("すなあらし", 99), 1, 4),  # すなあらし: 1/4 回復
    (("はれ",      5),  2, 3),  # はれ: 2/3 回復
    (("ゆき",      5),  1, 4),  # ゆき: 1/4 回復
])
def test_つきのひかり_天候別回復量(weather_arg, numerator, denominator):
    """つきのひかり: 天候ごとに回復量が変わる（通常1/2, はれ/おおひでり2/3, それ以外1/4）"""
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


def test_つぼをつく_PPは20():
    """つぼをつく: チャンピオンズでのPPは20（docs/champions/move_list.txt準拠）。"""
    assert MOVES["つぼをつく"].pp == 20


def test_つぼをつく_マジックコートで跳ね返されない():
    """つぼをつく: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    battle.random.choice = lambda seq: "def"
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2
    assert defender.rank["def"] == 0


def test_つぼをつく_まもるで防がれない():
    """つぼをつく: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    battle.random.choice = lambda seq: "def"
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2


def test_つぼをつく_全ての能力が最大なら失敗する():
    """つぼをつく: 対象の全ての能力が最大まで上がっている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    for stat in ["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]:
        attacker.rank[stat] = 6

    t.run_move(battle, 0)

    for stat in ["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]:
        assert attacker.rank[stat] == 6


def test_つぼをつく_最大の能力は候補から除外される():
    """つぼをつく: すでに+6の能力はランダム選択の候補から除外される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 6

    def choice(seq):
        assert "atk" not in seq
        return seq[0]

    battle.random.choice = choice
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 6


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


def test_つめとぎ_こうげきと命中率が1段階ずつ上がる():
    """つめとぎ: 使用すると自分のこうげき・命中率ランクがそれぞれ1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つめとぎ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["atk"] == 0
    assert attacker.rank["accuracy"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["accuracy"] == 1


def test_つめとぎ_マジックコートで跳ね返されない():
    """つめとぎ: 自分が対象の技のため、相手のマジックコート状態でも跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つめとぎ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["accuracy"] == 1


def test_つめとぎ_相手のまもる状態に影響されず成功する():
    """つめとぎ: 自分が対象の技のため、相手のまもる状態に関係なく成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つめとぎ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["accuracy"] == 1


def test_つめとぎ_相手のランクは変化しない():
    """つめとぎ: 自分が対象のため相手の能力ランクは変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つめとぎ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 0
    assert defender.rank["accuracy"] == 0


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


def test_テクスチャー_PPは30():
    """テクスチャー: PPは30（champions基準）"""
    move_data = MOVES["テクスチャー"]
    assert move_data.pp == 30


def test_テクスチャー_一番上の技と同じタイプになる():
    """テクスチャー: 一番上の技（moves[0]）と同じタイプに自分のタイプを変更する"""
    battle = t.start_battle(
        team0=[Pokemon("イーブイ", move_names=["みずでっぽう", "テクスチャー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.types == ["ノーマル"]
    t.run_move(battle, 0, move_idx=1)

    assert attacker.types == ["みず"]


def test_テクスチャー２_PPは30():
    """テクスチャー２: move_list.txtに記載がないため、原作準拠のPP30を維持する。"""
    assert MOVES["テクスチャー２"].pp == 30


def test_テクスチャー２_フリーズドライに対してみずタイプとして判定される():
    """テクスチャー２: フリーズドライは実際の技タイプ（こおり）ではなく、
    みずタイプとして判定される（原作のバグ仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("ポリゴン２", move_names=["テクスチャー２"])],
        team1=[Pokemon("カビゴン", move_names=["フリーズドライ"])],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 1)
    assert defender.last_move_type == "こおり"

    battle.random.choice = lambda seq: seq[0]
    t.run_move(battle, 0)

    # こおりタイプの抵抗候補（ほのお・みず・こおり・はがね）ではなく、
    # みずタイプの抵抗候補（みず・くさ・ドラゴン）の先頭が選ばれる
    assert attacker.types == ["みず"]


def test_テクスチャー２_まもるを無視して成立する():
    """テクスチャー２: 相手のまもる状態を無視して発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ポリゴン２", move_names=["テクスチャー２"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
        volatile1={"まもる": 1},
    )
    attacker, defender = battle.actives
    # まもる状態のためかえんほうしゃ自体は直接発動できないので、直近使用技を直接設定して検証する
    defender.last_move_type = "ほのお"
    defender.last_move_name = "かえんほうしゃ"
    battle.random.choice = lambda seq: seq[0]
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied is True
    assert attacker.types == ["ほのお"]


def test_テクスチャー２_もりののろいで追加されたタイプがリセットされる():
    """テクスチャー２: もりののろいで追加されたタイプは、タイプ変更成功時にリセットされる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["テクスチャー２"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        volatile0={"もりののろい": 0},
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert "くさ" in attacker.types
    t.run_move(battle, 1)
    battle.random.choice = lambda seq: seq[0]
    t.run_move(battle, 0)

    assert attacker.types == ["ほのお"]


def test_テクスチャー２_交代でタイプが元に戻る():
    """テクスチャー２: 交代すると変更したタイプが元に戻る。"""
    battle = t.start_battle(
        team0=[Pokemon("ポリゴン２", move_names=["テクスチャー２"]), Pokemon("コイキング")],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 1)
    battle.random.choice = lambda seq: seq[0]
    t.run_move(battle, 0)
    assert attacker.types == ["ほのお"]

    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert attacker.types == ["ノーマル"]


def test_テクスチャー２_変更候補タイプが存在しない場合失敗する():
    """テクスチャー２: 相手の技を半減できるタイプをすべて現在持っている場合は失敗する。"""
    # ゴースト技の抵抗タイプはノーマル・あくの2つのみ。ノーマル・あく複合のタチフサグマは
    # 候補が0件になるため失敗する（うらみはゴーストタイプの変化技のためタイプ相性による
    # 無効化を挟まず直近使用技として記録される）。
    battle = t.start_battle(
        team0=[Pokemon("タチフサグマ", move_names=["テクスチャー２"])],
        team1=[Pokemon("ゲンガー", move_names=["うらみ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    before_types = list(attacker.types)
    t.run_move(battle, 1)
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied is False
    assert attacker.types == before_types


def test_テクスチャー２_現在持っているタイプは候補から除外される():
    """テクスチャー２: すでに持っているタイプは変更候補から除外される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["テクスチャー２"])],  # ほのお・ひこう
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 1)

    def choice(seq):
        # ほのお技の抵抗候補は ほのお・みず・いわ・ドラゴン。
        # 現在のタイプ（ほのお・ひこう）のうち「ほのお」は候補から除外される
        assert "ほのお" not in seq
        return seq[0]

    battle.random.choice = choice
    t.run_move(battle, 0)

    assert attacker.types == ["みず"]


def test_テクスチャー_一番上の技が自分と同じタイプなら失敗する():
    """テクスチャー: 一番上の技が自分の現在のタイプと同じなら失敗する（次の技へのフォールバックはしない）"""
    battle = t.start_battle(
        team0=[Pokemon("イーブイ", move_names=["でんこうせっか", "テクスチャー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.types == ["ノーマル"]
    t.run_move(battle, 0, move_idx=1)

    # でんこうせっかはノーマルタイプで自分と同じため失敗し、タイプは変化しない
    assert attacker.types == ["ノーマル"]


def test_テクスチャー_複数タイプの場合いずれかと同じなら失敗する():
    """テクスチャー: 複数タイプ所持時、一番上の技がそのいずれかと同じタイプなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー", move_names=["ぼうふう", "テクスチャー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.types == ["ドラゴン", "ひこう"]
    t.run_move(battle, 0, move_idx=1)

    # ぼうふうはひこうタイプで自分の所持タイプ(ひこう)と同じため失敗する
    assert attacker.types == ["ドラゴン", "ひこう"]


def test_テクスチャー_自分自身も一番上なら選ばれる():
    """テクスチャー: 第六世代以降はテクスチャー自身も『選ばれない技』から除外されず選ばれる"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["テクスチャー", "したでなめる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.types == ["ゴースト", "どく"]
    t.run_move(battle, 0, move_idx=0)

    # 一番上の技はテクスチャー自身（ノーマル）で、自分の現在タイプと異なるため成功する
    assert attacker.types == ["ノーマル"]


def test_テクスチャー_もりののろい等で追加されたタイプの効果が消える():
    """テクスチャー: タイプ変更後はもりののろい・ハロウィンで追加されたタイプの効果が消える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "テクスチャー"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"ハロウィン": 0},
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert "ゴースト" in attacker.types
    t.run_move(battle, 0, move_idx=1)

    # でんこうせっか（ノーマル）のみになり、追加されていたゴーストタイプは消える
    assert attacker.types == ["ノーマル"]


def test_テクスチャー_テラスタル中は失敗する():
    """テクスチャー: 自分がテラスタルしているときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "テクスチャー"], tera_type="ほのお")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.terastallized = True
    t.run_move(battle, 0, move_idx=1)

    # テラスタル中は失敗するためタイプ変化なし（テラタイプのまま）
    assert attacker.types == ["ほのお"]


def test_テクスチャー_交代でタイプがリセットされる():
    """テクスチャー: 交代後は変更されたタイプが元に戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "テクスチャー"]), Pokemon("カビゴン")],
        team1=[Pokemon("ゲッコウガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0, move_idx=1)
    assert attacker.types == ["ノーマル"]

    t.run_switch(battle, 0, 1)
    # ピカチュウのタイプは元に戻る
    assert attacker.types == ["でんき"]


def test_テクスチャー_対象はself():
    """テクスチャー: 対象は自分（target="self"）。foeのままだとまもる・マジックコートに誤って阻害される"""
    move_data = MOVES["テクスチャー"]
    assert move_data.target == "self"


def test_テクスチャー_まもるで防がれない():
    """テクスチャー: 自分が対象の技のため、相手のまもる状態に関係なく成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "テクスチャー"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0, move_idx=1)

    assert attacker.types == ["ノーマル"]


def test_テクスチャー_マジックコートで跳ね返されない():
    """テクスチャー: 自分が対象の技のため、相手のマジックコート状態でも跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "テクスチャー"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0, move_idx=1)

    assert attacker.types == ["ノーマル"]


def test_テクスチャー２_相手が場に出てから技を使っていない場合失敗する():
    """テクスチャー２: 相手が場に出てからまだ技を使用していない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ポリゴン２", move_names=["テクスチャー２"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied is False
    assert attacker.types == ["ノーマル"]


def test_テクスチャー２_相手の技タイプを半減できるタイプに変わる():
    """テクスチャー２: 相手が直前に使った技のタイプを半減できるタイプに変わる。"""
    battle = t.start_battle(
        team0=[Pokemon("ポリゴン２", move_names=["テクスチャー２"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 1)
    battle.random.choice = lambda seq: seq[0]
    t.run_move(battle, 0)

    # ほのお技を半減できるタイプ（ほのお・みず・いわ・ドラゴン）のいずれかになる
    assert attacker.types == ["ほのお"]


def test_テクスチャー２_自分がテラスタル中の場合失敗する():
    """テクスチャー２: 自分がテラスタル中の場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ポリゴン２", move_names=["テクスチャー２"], tera_type="ほのお")],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 1)
    attacker.terastallized = True
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied is False
    assert attacker.types == ["ほのお"]


def test_てっぺき_すでに最大なら失敗する():
    """てっぺき: ぼうぎょランクがすでに+6の場合はランクが変化せず技は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["てっぺき"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"def": 6}, source=attacker)
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 6


def test_てっぺき_ぼうぎょ2段階上がる():
    """てっぺき: 使用すると自分のぼうぎょランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["てっぺき"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["def"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2


def test_てっぺき_自分対象のためまもるで防がれない():
    """てっぺき: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["てっぺき"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2


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


def test_テレポート_PPは20():
    """テレポート: PPは20"""
    assert MOVES["テレポート"].pp == 20


def test_テレポート_優先度はマイナス6():
    """テレポート: 優先度は-6"""
    assert MOVES["テレポート"].priority == -6


def test_テレポート_対象は自分():
    """テレポート: 対象は自分自身（まもる・マジックコートの誤爆防止のため）"""
    assert MOVES["テレポート"].target == "self"


def test_テレポート_控えのポケモンと交代する():
    """テレポート: 控えのポケモンと交代し、PIVOT が設定される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["テレポート"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    t.run_move(battle, 0)

    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_テレポート_控えがいない場合は失敗する():
    """テレポート: 控えにポケモンがいない場合は技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["テレポート"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    t.run_move(battle, 0)

    # 控えがいないので失敗し、PIVOT は設定されない
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_テレポート_とらわれ状態でも使用できる():
    """テレポート: にげられない状態でも技が失敗せず PIVOT が設定される（トレーナー戦の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["テレポート"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"にげられない": 3},
        accuracy=100,
    )
    player = battle.players[0]
    t.run_move(battle, 0)

    # とらわれ状態でもテレポートは失敗しない
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_テレポート_ランクは引き継がれない():
    """テレポート: バトンタッチと異なり、能力ランクは交代先に引き継がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["テレポート"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 2
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.rank["atk"] == 0


def test_でんじは_じめんタイプには無効():
    """でんじは: 対象がじめんタイプの場合は無効になる（例外的にタイプ相性の影響を受ける）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        team1=[Pokemon("サンドパン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not battle.actives[1].ailment.is_active


def test_でんじは_でんきタイプには無効():
    """でんじは: 対象がでんきタイプの場合は無効になる（まひ無効）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        team1=[Pokemon("ライチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not battle.actives[1].ailment.is_active


def test_でんじは_ねらいのまとでじめんタイプへの無効化が解除される():
    """でんじは: ねらいのまとを持つじめんタイプの相手にはタイプ無効が解除されまひが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        team1=[Pokemon("サンドパン", item_name="ねらいのまと")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert battle.actives[1].ailment.name == "まひ"


def test_でんじは_まひ付与():
    """でんじは: 相手をまひ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert battle.actives[1].ailment.name == "まひ"


def test_でんじふゆう_PPは12():
    """でんじふゆう: チャンピオンズでのPPは12（docs/champions/move_list.txt準拠）。"""
    assert MOVES["でんじふゆう"].pp == 12


def test_でんじふゆう_うちおとす状態なら失敗():
    """でんじふゆう: うちおとす状態のポケモンが使うと失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじふゆう"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"うちおとす": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.has_volatile("でんじふゆう")


def test_でんじふゆう_じゅうりょく状態では失敗():
    """でんじふゆう: 場がじゅうりょく状態のときは使えない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじふゆう"])],
        team1=[Pokemon("カビゴン")],
        field={"じゅうりょく": 3},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.has_volatile("でんじふゆう")


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


def test_でんじふゆう_ねをはる状態なら失敗():
    """でんじふゆう: ねをはる状態のポケモンが使うと失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじふゆう"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"ねをはる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.has_volatile("でんじふゆう")


def test_でんじふゆう_マジックコートで跳ね返されない():
    """でんじふゆう: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじふゆう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.has_volatile("でんじふゆう")
    assert not defender.has_volatile("でんじふゆう")


def test_でんじふゆう_まもるで防がれない():
    """でんじふゆう: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじふゆう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("でんじふゆう")


def test_とおせんぼう_PPは8():
    """とおせんぼう: チャンピオンズでのPPは8（docs/champions/move_list.txt準拠）。"""
    assert MOVES["とおせんぼう"].pp == 8


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


def test_とおせんぼう_まもる状態の相手にも効果が発動する():
    """とおせんぼう: unprotectableフラグを持つため、まもる状態の相手にも効果が発動する（第六世代以降）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とおせんぼう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
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


def test_とおぼえ_マジックコートで跳ね返されない():
    """とおぼえ: 自分が対象の技のため、相手のマジックコート状態でも跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とおぼえ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1


def test_とおぼえ_相手のまもる状態に影響されず成功する():
    """とおぼえ: 自分が対象の技のため、相手のまもる状態に関係なく成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とおぼえ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
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


def test_とぐろをまく_マジックコートで跳ね返されない():
    """とぐろをまく: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とぐろをまく"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1
    assert attacker.rank["accuracy"] == 1


def test_とぐろをまく_自分対象のためまもるで防がれない():
    """とぐろをまく: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とぐろをまく"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1
    assert attacker.rank["accuracy"] == 1


def test_とける_すでに最大なら失敗する():
    """とける: ぼうぎょランクがすでに+6の場合はランクが変化せず技は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とける"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"def": 6}, source=attacker)
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 6


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


def test_とける_自分対象のためまもるで防がれない():
    """とける: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とける"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2


def test_トリック_こだわり系アイテムを入手してもロックされない():
    """トリック: 自身の効果でこだわり系アイテムを新たに入手しても、トリックにロックされない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", item_name="こだわりハチマキ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.item.name == "こだわりハチマキ"
    assert not attacker.has_volatile("こだわり")


def test_トリック_マジックコートで跳ね返されない():
    """トリック: マジックコート・マジックミラーで跳ね返されない（すりかえと同様の例外仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 跳ね返されていれば MOVE_REFLECTED ログが記録される
    assert not any(log.log == LogCode.MOVE_REFLECTED for log in battle.event_logger.logs)
    assert attacker.item.name == "オボンのみ"
    assert defender.item.name == "たべのこし"


def test_トリック_両者がアイテムを持っていないとき失敗():
    """トリック: 両者ともアイテムを持っていない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not attacker.has_item()
    assert not defender.has_item()


def test_トリック_両者のアイテムが入れ替わる():
    """トリック: 使用者と相手のアイテムを入れ替える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.item.name == "オボンのみ"
    assert defender.item.name == "たべのこし"


def test_トリック_既にロックされていた場合も解除される():
    """トリック: 既にこだわりでロックされていた場合も、トリックの使用でロックが解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="こだわりスカーフ")],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "こだわり", source=attacker, move_name="トリック")
    assert attacker.has_volatile("こだわり")

    t.run_move(battle, 0)

    assert attacker.item.name == "たべのこし"
    assert not attacker.has_volatile("こだわり")


@pytest.mark.parametrize("a_item,d_item,expected_a,expected_d", [
    ("たべのこし", None, None, "たべのこし"),  # 使用者のみアイテム持ち
    (None, "オボンのみ", "オボンのみ", None),   # 相手のみアイテム持ち
])
def test_トリック_片方のみアイテムを持つとき入れ替わる(a_item, d_item, expected_a, expected_d):
    """トリック: 使用者または相手のみアイテムを持つ場合も入れ替えが成功する。"""
    a_kwargs = {"item_name": a_item} if a_item else {}
    d_kwargs = {"item_name": d_item} if d_item else {}
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], **a_kwargs)],
        team1=[Pokemon("カビゴン", **d_kwargs)],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    if expected_a is None:
        assert not attacker.has_item()
    else:
        assert attacker.item.name == expected_a
    if expected_d is None:
        assert not defender.has_item()
    else:
        assert defender.item.name == expected_d


def test_どくガス_PPは20():
    """どくガス: チャンピオンズでのPPは20（move_list.txtに単独項目はないが、PP圧縮則
    〈SV基準PPが20以上の技は一律20に圧縮〉から導出。Gen9本家は40）。"""
    assert MOVES["どくガス"].pp == 20


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


def test_どくどく_どくタイプでない場合は命中率90で外れることがある():
    """どくどく: どくタイプでない使用者の場合、通常どおり命中率90で判定する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくどく"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.fix_random(battle, 0.95)
    t.run_move(battle, 0)

    assert not defender.has_ailment("もうどく")


def test_どくどく_どくタイプ使用時は必中になる():
    """どくどく: 使用者がどくタイプの場合、命中率90を無視して必ず命中する。

    random.random()=0.95 のとき 100*0.95=95>90 で本来は外れるが、
    どくタイプが使用するとON_MODIFY_ACCURACYでNoneが返り必中になるため命中する。
    """
    battle = t.start_battle(
        team0=[Pokemon("マタドガス", move_names=["どくどく"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.random.random = lambda: 0.95
    t.run_move(battle, 0)

    assert defender.has_ailment("もうどく")


def test_どくどく_命中すると相手をもうどく状態にする():
    """どくどく: 命中すると相手を『もうどく』状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくどく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("もうどく")


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

    assert defender.rank["spe"] == -2
    assert defender.has_ailment("どく")


def test_どくのいと_すばやさ2段階下がりどく付与():
    """どくのいと: 相手のすばやさが2段階下がり、どく状態になる（Championsで1段階→2段階に変更）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくのいと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spe"] == -2
    assert defender.has_ailment("どく")


def test_どくのいと_すばやさもどくも失敗する場合は技全体が失敗する():
    """どくのいと: すばやさが既に-6段階かつ相手がどくタイプの場合、両方失敗して技全体が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくのいと"])],
        team1=[Pokemon("ベトベトン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"spe": -6})
    t.run_move(battle, 0)

    assert defender.rank["spe"] == -6
    assert not defender.has_ailment("どく")


def test_どくのいと_どくタイプにはどく無効だがS低下は有効():
    """どくのいと: どくタイプの相手にはどく状態付与のみ無効になり、すばやさ低下は通常通り発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくのいと"])],
        team1=[Pokemon("ベトベトン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spe"] == -2
    assert not defender.has_ailment("どく")


def test_どくのこな_くさタイプには無効():
    """どくのこな: 粉技のためくさタイプの相手には効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくのこな"])],
        team1=[Pokemon("キマワリ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_ailment("どく")


def test_どくのこな_どく状態にする():
    """どくのこな: 命中すると相手を『どく』状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくのこな"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("どく")


def test_どくのこな_命中率75で外れることがある():
    """どくのこな: 命中率75のため外れる場合がある"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくのこな"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.fix_random(battle, 0.95)
    t.run_move(battle, 0)

    assert not defender.has_ailment("どく")


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


def test_どくびし_マジックコートで跳ね返り使用者側に設置される():
    """どくびし: マジックコートで跳ね返されると、使用者側の場にどくびしが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくびし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    t.run_move(battle, 0)

    attacker_side = battle.get_side(battle.actives[0])
    defender_side = battle.get_side(battle.actives[1])
    assert attacker_side.fields["どくびし"].is_active
    assert not defender_side.fields["どくびし"].is_active


def test_どくびし_相手陣営に設置される():
    """どくびし: 使用すると相手陣営にどくびしが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくびし"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[1])
    assert side.fields["どくびし"].is_active


def test_ドわすれ_とくぼう2段階上がる():
    """ドわすれ: 使用すると自分のとくぼうランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ドわすれ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["spd"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["spd"] == 2


def test_ドわすれ_自分対象のためまもるで防がれない():
    """ドわすれ: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ドわすれ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["spd"] == 2


def test_ドわすれ_マジックコートで跳ね返されない():
    """ドわすれ: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ドわすれ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.rank["spd"] == 2
    assert defender.rank["spd"] == 0


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
