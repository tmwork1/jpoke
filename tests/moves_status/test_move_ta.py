"""変化技ハンドラの単体テスト（た行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_たくわえる_3回目にカウント3になる():
    """たくわえる: 3回使用するとたくわえカウントが3になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たくわえる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    t.run_move(battle, 0)
    t.run_move(battle, 0)

    assert attacker.has_volatile("たくわえる")
    assert attacker.volatiles["たくわえる"].count == 3


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


def test_たくわえる_ぼうぎょとくぼうが上がる():
    """たくわえる: 使用するとぼうぎょとくぼうがそれぞれ1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たくわえる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 1
    assert attacker.rank["D"] == 1


def test_たくわえる_初回でvolatile付与される():
    """たくわえる: 初めて使用するとたくわえる揮発状態がcount=1で付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たくわえる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("たくわえる")
    assert attacker.volatiles["たくわえる"].count == 1


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
    assert defender.rank["S"] == -1


def test_タールショット_すばやさ1段階下がりタールショット状態付与():
    """タールショット: 相手のすばやさが1段階下がり、タールショット状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タールショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["S"] == -1
    assert defender.has_volatile("タールショット")


def test_ちからをすいとる_HPが満タンのとき上限でとまる():
    """ちからをすいとる: 回復量で最大HPを超えることはない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちからをすいとる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # HPをあえて満タンにしておく
    attacker.hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp


def test_ちからをすいとる_HPを回復する():
    """ちからをすいとる: 相手のこうげき実数値分だけ自分のHPを回復する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ちからをすいとる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # カビゴンの最大HPは大きいため、ピカチュウの攻撃実数値分の回復でもオーバーしない
    hp_before = 1
    attacker.hp = hp_before
    expected_recovery = defender.stats["A"]
    t.run_move(battle, 0)

    assert attacker.hp == hp_before + expected_recovery


def test_ちからをすいとる_クリアボディでランク低下阻止でもHP回復は発動():
    """ちからをすいとる: クリアボディでランク低下が阻まれても回復効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ちからをすいとる"])],
        team1=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = 1
    attacker.hp = hp_before
    expected_recovery = defender.stats["A"]
    t.run_move(battle, 0)

    # クリアボディでランク低下は阻まれる
    assert defender.rank["A"] == 0
    # それでも回復は発動する
    assert attacker.hp == hp_before + expected_recovery


def test_ちからをすいとる_こうげきランク上昇時は補正込みの値を回復する():
    """ちからをすいとる: 相手のこうげきランクが+1のとき、回復量はranked_stats["A"]（補正済み）になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ちからをすいとる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # ランクを+1に設定（補正倍率 3/2）
    battle.modify_stats(defender, {"A": 1}, source=defender)
    assert defender.rank["A"] == 1
    hp_before = 1
    attacker.hp = hp_before
    # ランク補正済みの期待値
    expected_recovery = defender.ranked_stats["A"]
    t.run_move(battle, 0)

    assert attacker.hp == hp_before + expected_recovery


def test_ちからをすいとる_こうげきランク低下時は補正込みの値を回復する():
    """ちからをすいとる: 相手のこうげきランクが-1のとき、回復量はranked_stats["A"]（補正済み）になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ちからをすいとる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # ランクを-1に設定（補正倍率 2/3）
    # ちからをすいとる実行前にランクを直接設定（modify_stats はランク変化を発火する）
    defender.rank["A"] = -1
    hp_before = 1
    attacker.hp = hp_before
    # ランク補正済みの期待値（ランク変更前に取得）
    expected_recovery = defender.ranked_stats["A"]
    t.run_move(battle, 0)

    assert attacker.hp == hp_before + expected_recovery


def test_ちからをすいとる_こうげきランク最低で失敗():
    """ちからをすいとる: 相手のこうげきランクがすでに-6なら失敗する（HP回復も発動しない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちからをすいとる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.modify_stats(defender, {"A": -6}, source=attacker)
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)

    assert attacker.hp == hp_before
    assert defender.rank["A"] == -6


def test_ちからをすいとる_こうげきを1段階下げる():
    """ちからをすいとる: 相手のこうげきランクを1段階下げる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちからをすいとる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["A"] == -1


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

    assert defender.rank["A"] == -1


def test_つぼをつく_かいひりつが選ばれた場合ランクが2段階上がる():
    """つぼをつく: 回避率が選ばれた場合、自分の回避率ランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.random.choice = lambda seq: "EVA"
    t.run_move(battle, 0)

    assert attacker.rank["EVA"] == 2


def test_つぼをつく_こうげきが選ばれた場合ランクが2段階上がる():
    """つぼをつく: こうげきが選ばれた場合、自分のこうげきランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.random.choice = lambda seq: "A"
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 2


def test_つぼをつく_すばやさが選ばれた場合ランクが2段階上がる():
    """つぼをつく: すばやさが選ばれた場合、自分のすばやさランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.random.choice = lambda seq: "S"
    t.run_move(battle, 0)

    assert attacker.rank["S"] == 2


def test_つぼをつく_めいちゅうりつが選ばれた場合ランクが2段階上がる():
    """つぼをつく: 命中率が選ばれた場合、自分の命中率ランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.random.choice = lambda seq: "ACC"
    t.run_move(battle, 0)

    assert attacker.rank["ACC"] == 2


def test_つぼをつく_選ばれない能力のランクは変化しない():
    """つぼをつく: ランダムで選ばれた1種類以外の能力ランクは変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つぼをつく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.random.choice = lambda seq: "B"
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 2
    assert attacker.rank["A"] == 0
    assert attacker.rank["C"] == 0
    assert attacker.rank["D"] == 0
    assert attacker.rank["S"] == 0
    assert attacker.rank["ACC"] == 0
    assert attacker.rank["EVA"] == 0


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


def test_のみこむ_カウント0で失敗する():
    """のみこむ: たくわえていない（カウント0）なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)

    assert attacker.hp == hp_before


def test_のみこむ_カウント1で4分の1回復():
    """のみこむ: たくわえカウント1で最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    expected = 1 + int(attacker.max_hp * 1 / 4)
    assert attacker.hp == expected


def test_のみこむ_カウント2で2分の1回復():
    """のみこむ: たくわえカウント2で最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    expected = 1 + int(attacker.max_hp * 1 / 2)
    assert attacker.hp == expected


def test_のみこむ_カウント3で全回復():
    """のみこむ: たくわえカウント3で最大HPまで全回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 3},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp


def test_のみこむ_ランク逆補正がクリアボディに阻まれない():
    """のみこむ: ランク戻し（自分源）はクリアボディに阻まれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 1},
    )
    attacker = battle.actives[0]
    attacker.rank["B"] = 1
    attacker.rank["D"] = 1
    t.run_move(battle, 0)

    # クリアボディでも自分源のランク低下は防げない
    assert attacker.rank["B"] == 0
    assert attacker.rank["D"] == 0


def test_のみこむ_使用後にたくわえる状態が消える():
    """のみこむ: 使用後にたくわえる揮発状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.has_volatile("たくわえる")


def test_のみこむ_使用後にランクが元に戻る():
    """のみこむ: たくわえた回数分だけぼうぎょとくぼうが下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
    )
    attacker = battle.actives[0]
    # たくわえカウント2相当のランクを事前に設定
    attacker.rank["B"] = 2
    attacker.rank["D"] = 2
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 0
    assert attacker.rank["D"] == 0
