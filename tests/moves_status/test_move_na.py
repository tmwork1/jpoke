"""変化技ハンドラの単体テスト（な行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_ないしょばなし_とくこうが1段階下がる():
    """ないしょばなし: 命中すると相手のとくこうが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ないしょばなし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spa"] == -1


def test_ないしょばなし_まもる状態の相手にも効果が発動する():
    """ないしょばなし: unprotectableフラグを持つため、まもる状態の相手にも効果が発動する（第六世代以降）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ないしょばなし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spa"] == -1


def test_ないしょばなし_みがわりを貫通してとくこうが下がる():
    """ないしょばなし: soundラベルを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ないしょばなし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.rank["spa"] == -1
    assert defender.volatiles["みがわり"].hp == 999


def test_なかまづくり_uncopyableフラグ持ちを使用者が持つと失敗():
    """なかまづくり: 使用者がイリュージョン（uncopyableフラグ持ち）なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="イリュージョン", move_names=["なかまづくり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は変化しない
    assert defender.ability.name == "めんえき"


def test_なかまづくり_マジックコートで跳ね返され使用者の特性が変わる():
    """なかまづくり: マジックコート状態の相手に使うと反射され、使用者の特性が相手の特性に変わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なかまづくり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    # 反射され、使用者の特性が相手の特性に書き換えられる。相手の特性は変化しない
    assert attacker.ability.name == "めんえき"
    assert defender.ability.name == "めんえき"


def test_なかまづくり_まもるで防がれる():
    """なかまづくり: 対象がまもる状態のときは防がれ、特性は変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なかまづくり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.ability.name == "めんえき"


def test_なかまづくり_みがわり状態の相手には防がれる():
    """なかまづくり: 対象がみがわり状態のときは防がれ、特性は変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なかまづくり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.ability.name == "めんえき"


def test_なかまづくり_交代後に元の特性に戻る():
    """なかまづくり: 特性を書き換えられたポケモンが交代すると元の特性に戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なかまづくり"])],
        team1=[
            Pokemon("カビゴン", ability_name="めんえき"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert defender_before.ability.name == "せいでんき"

    # 交代後は元の特性に戻る
    t.run_switch(battle, 1, 1)
    assert defender_before.ability.name == "めんえき"


def test_なかまづくり_同じ特性なら失敗():
    """なかまづくり: 使用者と対象が同じ特性の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なかまづくり"])],
        team1=[Pokemon("カビゴン", ability_name="せいでんき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    original_ability = defender.ability.name
    t.run_move(battle, 0)

    assert defender.ability.name == original_ability


@pytest.mark.parametrize("d_ability", ["アイスフェイス", "なまけ"])
def test_なかまづくり_失敗条件(d_ability):
    """なかまづくり: protectedフラグ持ちまたはなまけ特性の相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なかまづくり"])],
        team1=[Pokemon("カビゴン", ability_name=d_ability)],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は変化しない
    assert defender.ability.name == d_ability


def test_なかまづくり_相手の特性が使用者の特性に変わる():
    """なかまづくり: 使用すると相手の特性が使用者と同じ特性に変わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なかまづくり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.ability.name == "せいでんき"


def test_なかよくする_こうげきが1段階下がる():
    """なかよくする: 使用すると相手のこうげきが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なかよくする"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1


def test_なかよくする_こうげきが最低値のとき変化なし():
    """なかよくする: こうげきランクがすでに-6のときはランクが変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なかよくする"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"atk": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -6


def test_なかよくする_まもる状態を無視してこうげきを下げる():
    """なかよくする: unprotectableフラグを持つため、まもる状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なかよくする"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1


def test_なかよくする_みがわりを貫通してこうげきを下げる():
    """なかよくする: bypass_substituteフラグを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なかよくする"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1


def test_なきごえ_こうげきが1段階下がる():
    """なきごえ: 使用すると相手のこうげきが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1


def test_なきごえ_まもるで防がれる():
    """なきごえ: unprotectableフラグを持たないため、まもる状態の相手には効果が発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 0


def test_なきごえ_みがわりを貫通してこうげきが下がる():
    """なきごえ: soundラベルを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1
    assert defender.volatiles["みがわり"].hp == 999


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


def test_なまける_マジックコートで跳ね返されない():
    """なまける: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なまける"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    defender_hp = defender.hp
    t.run_move(battle, 0)
    assert attacker.hp > 1
    assert defender.hp == defender_hp


def test_なまける_まもるで防がれない():
    """なまける: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なまける"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp > 1


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


def test_なみだめ_こうげきととくこうが1段階ずつ下がる():
    """なみだめ: 使用すると相手のこうげき・とくこうがそれぞれ1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみだめ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1
    assert defender.rank["spa"] == -1


def test_なみだめ_まもる状態を無視してランクを下げる():
    """なみだめ: unprotectableフラグを持つため、まもる状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみだめ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1
    assert defender.rank["spa"] == -1


def test_なみだめ_みがわり状態の相手には防がれる():
    """なみだめ: bypass_substituteフラグを持たないため、みがわり状態の相手には防がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみだめ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 0
    assert defender.rank["spa"] == 0


@pytest.mark.parametrize("d_ability", ["なまけ", "ふみん"])
def test_なやみのタネ_かたやぶりでもなまけ・ふみんの相手には失敗する(d_ability):
    """なやみのタネ: なまけ・ふみんは上書きできない特性のため、使用者がかたやぶりでも失敗する

    ふみんはmold_breaker_ignorableフラグを持ち技中は特性の効果自体が無効化されるが、
    「相手の特性がすでにふみん/なまけか」の判定は特性の有効/無効状態に関わらない
    元の特性名（base_name）で行われるべきであり、かたやぶりでは無視できない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なやみのタネ"])],
        team1=[Pokemon("カビゴン", ability_name=d_ability)],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は変化しない
    assert defender.ability.base_name == d_ability


def test_なやみのタネ_すでにねむり状態の相手に使うと即座に回復する():
    """なやみのタネ: すでにねむり状態の相手の特性をふみんに変えると、ねむり状態は回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なやみのタネ"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
        ailment1=("ねむり", 3),
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.ability.name == "ふみん"
    assert not defender.ailment.is_active


def test_なやみのタネ_ふみん付与後はねむり系技が効かない():
    """なやみのタネ: ふみんに書き換えられた相手にはその後ねむり系技が効かない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なやみのタネ", "ねむりごな"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # なやみのタネでふみんに書き換える
    t.run_move(battle, 0, move_idx=0)
    assert defender.ability.name == "ふみん"

    # ふみんになったのでねむりごなは失敗する
    t.run_move(battle, 0, move_idx=1)
    assert not defender.ailment.is_active


def test_なやみのタネ_やるき特性の相手には成功する():
    """なやみのタネ: やるきはふみんと同様の効果だが、なやみのタネに対しては成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なやみのタネ"])],
        team1=[Pokemon("カビゴン", ability_name="やるき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # ふみんに書き換えられる
    assert defender.ability.name == "ふみん"


def test_なやみのタネ_交代後に元の特性に戻る():
    """なやみのタネ: 特性をふみんに書き換えられたポケモンが交代すると元の特性に戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なやみのタネ"])],
        team1=[
            Pokemon("カビゴン", ability_name="めんえき"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert defender_before.ability.name == "ふみん"

    # 交代後は元の特性に戻る
    t.run_switch(battle, 1, 1)
    assert defender_before.ability.name == "めんえき"


@pytest.mark.parametrize("d_ability", ["アイスフェイス", "なまけ", "ふみん"])
def test_なやみのタネ_失敗条件(d_ability):
    """なやみのタネ: protectedフラグ持ち・なまけ・すでにふみんの相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なやみのタネ"])],
        team1=[Pokemon("カビゴン", ability_name=d_ability)],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は変化しない
    assert defender.ability.name == d_ability


def test_なやみのタネ_相手の特性がふみんに変わる():
    """なやみのタネ: 使用すると相手の特性がふみんに変わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なやみのタネ"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.ability.name == "ふみん"


def test_なりきり_いえきで無効化された相手の特性はコピーすると空特性になる():
    """なりきり: いえき状態で特性無効の相手の特性をコピーすると「とくせいなし」（空）になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
        volatile1={"とくせいなし": 3},
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    # 相手の特性がいえきで無効化されている（ability.name == ""）
    assert defender.ability.name == ""
    t.run_move(battle, 0)

    # コピー元が""なのでattackerのbase_nameが""でなければ change_abilityが実行される
    # 結果として attacker の特性は "" になる
    assert attacker.ability.name == ""


def test_なりきり_うのミサイルはコピーできる():
    """なりきり: うのミサイルはSV Ver.3.0.0以降コピー可能になったため成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name="うのミサイル")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.ability.name == "うのミサイル"


def test_なりきり_コピー後にいかくが発動して相手のこうげきが下がる():
    """なりきり: なりきりでいかくをコピーするとON_ABILITY_ENABLEDが発火して相手のこうげきが下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # バトル開始時にいかくが発動してattackerのこうげきが-1されている
    # この時点でdefenderのこうげきは0
    assert attacker.rank["atk"] == -1
    assert defender.rank["atk"] == 0
    # なりきりでいかくをコピーする
    t.run_move(battle, 0)
    assert attacker.ability.name == "いかく"
    # ON_ABILITY_ENABLEDによっていかくが再発動し、defenderのこうげきが-1になる
    assert defender.rank["atk"] == -1


def test_なりきり_ふしぎなまもりはコピーできない():
    """なりきり: ふしぎなまもりはuncopyableフラグを持たないがなりきりでは個別に失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("ヌケニン", ability_name="ふしぎなまもり")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    # 使用者の特性は変化しない
    assert attacker.ability.name == "せいでんき"


def test_なりきり_まもる状態の相手にも成功する():
    """なりきり: unprotectableフラグを持つためまもる状態の相手にも成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.ability.name == "めんえき"


def test_なりきり_みがわり状態の相手にも成功する():
    """なりきり: bypass_substituteフラグを持つためみがわり状態の相手にも成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert attacker.ability.name == "めんえき"


def test_なりきり_交代後に元の特性に戻る():
    """なりきり: 特性をコピーした使用者が交代すると元の特性に戻る"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"]),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker_before = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker_before.ability.name == "めんえき"

    # 交代後は元の特性に戻る
    t.run_switch(battle, 0, 1)
    assert attacker_before.ability.name == "せいでんき"


def test_なりきり_使用者と対象の特性が同じ場合は失敗する():
    """なりきり: 使用者と対象の特性がすでに同じ場合は失敗する（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name="せいでんき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.ability.name == "せいでんき"


def test_なりきり_使用者の特性が上書きできない場合は失敗する():
    """なりきり: 使用者自身の特性がprotectedフラグを持つ場合（マルチタイプ等）は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    # 使用者の特性は変化しない
    assert attacker.ability.name == "マルチタイプ"


@pytest.mark.parametrize("d_ability", ["アイスフェイス", "イリュージョン"])
def test_なりきり_失敗条件(d_ability):
    """なりきり: uncopyableフラグ持ちの相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name=d_ability)],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    # 使用者の特性は変化しない
    assert attacker.ability.name == "せいでんき"


def test_にほんばれ_天気がはれになる():
    """にほんばれ: 使用後に天気がはれになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にほんばれ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "はれ"
    assert battle.weather.count == 5


def test_にらみつける_ぼうぎょが1段階下がる():
    """にらみつける: 使用すると相手のぼうぎょが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にらみつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["def"] == -1


def test_にらみつける_まもるで防がれる():
    """にらみつける: unprotectableフラグを持たないため、まもる状態の相手には効果が発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にらみつける"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["def"] == 0


def test_にらみつける_みがわりには効果がない():
    """にらみつける: 音技ではないため、みがわり状態の相手には効果が発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にらみつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.rank["def"] == 0


def test_ニードルガード_ターン終了で解除される():
    """ニードルガード: ターン終了時に揮発状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "ニードルガード", count=1)
    t.end_turn(battle)

    assert not mon.has_volatile("ニードルガード")


def test_ニードルガード_変化技も無効化する():
    """ニードルガード: 相手対象の変化技も無効化する（まもると同様）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "ニードルガード", count=1)
    t.run_move(battle, 0)

    assert not battle.move_executor.move_success


def test_ニードルガード_接触技で攻撃した相手に8分の1ダメージ():
    """ニードルガード: 直接攻撃してきた相手に最大HPの1/8ダメージを与える"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(battle.actives[1], "ニードルガード", count=1)
    t.run_move(battle, 0)

    expected_damage = int(attacker.max_hp * 1 / 8)
    assert attacker.max_hp - attacker.hp == expected_damage


def test_ニードルガード_揮発状態が付与される():
    """ニードルガード: 使用すると自分にニードルガード状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ニードルガード"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("ニードルガード")


def test_ニードルガード_攻撃技を無効化する():
    """ニードルガード: 相手の攻撃技を無効化する"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "ニードルガード", count=1)
    t.run_move(battle, 0)

    assert not battle.move_executor.move_success


def test_ニードルガード_非接触技ではダメージなし():
    """ニードルガード: 非接触技では攻撃者にダメージを与えない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(battle.actives[1], "ニードルガード", count=1)
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp


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


def test_ねむりごな_くさタイプには無効():
    """ねむりごな: 粉技のためくさタイプの相手には効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねむりごな"])],
        team1=[Pokemon("キマワリ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_ailment("ねむり")


def test_ねむりごな_命中率75で外れることがある():
    """ねむりごな: 命中率75のため外れる場合がある"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねむりごな"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.fix_random(battle, 0.95)
    t.run_move(battle, 0)

    assert not defender.has_ailment("ねむり")


def test_ねむりごな_相手をねむり状態にする():
    """ねむりごな: 命中すると相手を『ねむり』状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねむりごな"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")


def test_ねをはる_かいふくふうじ状態でも使用できる():
    """ねをはる: HP回復技には分類されないため、かいふくふうじ状態でも使用できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねをはる"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"かいふくふうじ": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("ねをはる")


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


def test_ねをはる_まもるで防がれない():
    """ねをはる: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねをはる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("ねをはる")


@pytest.mark.parametrize("count,numerator,denominator", [
    (1, 1, 4),
    (2, 1, 2),
    (3, 1, 1),
])
def test_のみこむ_たくわえカウントに応じて回復する(count, numerator, denominator):
    """のみこむ: たくわえカウント1→1/4、2→1/2、3→全回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": count},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    expected_heal = int(attacker.max_hp * numerator / denominator)
    expected_hp = min(1 + expected_heal, attacker.max_hp)
    t.run_move(battle, 0)

    assert attacker.hp == expected_hp
    assert not attacker.has_volatile("たくわえる")


def test_のみこむ_たくわえなしで失敗():
    """のみこむ: たくわえていない状態では失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    # HP が変わらず失敗している
    assert attacker.hp == 1


def test_のみこむ_ランク逆補正がクリアボディに阻まれない():
    """のみこむ: ランク戻し（自分源）はクリアボディに阻まれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 1},
    )
    attacker = battle.actives[0]
    attacker.rank["def"] = 1
    attacker.rank["spd"] = 1
    t.run_move(battle, 0)

    # クリアボディでも自分源のランク低下は防げない
    assert attacker.rank["def"] == 0
    assert attacker.rank["spd"] == 0


def test_のみこむ_使用後にランクが元に戻る():
    """のみこむ: たくわえた回数分だけぼうぎょとくぼうが下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のみこむ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
    )
    attacker = battle.actives[0]
    # たくわえカウント2相当のランクを事前に設定
    attacker.rank["def"] = 2
    attacker.rank["spd"] = 2
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 0
    assert attacker.rank["spd"] == 0


def test_のろい_HPが半分以下でも成功しひんしになることがある():
    """のろい: 使用者のHPが半分以下でも成功し、使用者はひんしになることがある"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.fainted
    assert defender.has_volatile("のろい")


def test_のろい_ゴーストタイプは自分のHPを半分消費して相手をのろい状態にする():
    """のろい: ゴーストタイプが使うと自分の最大HPの半分（切り捨て）を消費し、相手をのろい状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == max_hp - max_hp // 2
    assert defender.has_volatile("のろい")


def test_のろい_ゴーストタイプ以外はこうげきとぼうぎょが上がりすばやさが下がる():
    """のろい: ゴーストタイプ以外が使うと自分のこうげき・ぼうぎょが1段階上がり、すばやさが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1
    assert attacker.rank["spe"] == -1
    # HPは消費されず、相手にも状態変化は起きない
    assert attacker.hp == max_hp
    assert not defender.has_volatile("のろい")


def test_のろい_すでにのろい状態の相手には失敗しHPも消費されない():
    """のろい: 対象がすでにのろい状態の場合は失敗し、使用者のHPも消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"のろい": 1},
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == max_hp


def test_のろい_呪いはマジックガード所持でもHPが減る():
    """のろい: 特性マジックガードを持つ使用者が呪いを使ってもHPは消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", ability_name="マジックガード", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == max_hp - max_hp // 2
    assert defender.has_volatile("のろい")


def test_のろい_呪いはマジックコートで跳ね返されない():
    """のろい: 呪い版はunreflectableフラグを持つため、マジックコート状態の相手に使っても跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    # 跳ね返されず、相手がのろい状態になる（使用者はのろい状態にならない）
    assert attacker.hp == max_hp - max_hp // 2
    assert defender.has_volatile("のろい")
    assert not attacker.has_volatile("のろい")


def test_のろい_呪いはまもるを無視して発動する():
    """のろい: 呪い版はunprotectableフラグを持つため、まもる状態の相手にも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker, defender = battle.actives
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == max_hp - max_hp // 2
    assert defender.has_volatile("のろい")


def test_のろい_呪いはみがわりを貫通してのろい状態にする():
    """のろい: 呪い版はbypass_substituteフラグを持つため、みがわり状態の相手にものろい状態を付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    max_hp = attacker.max_hp
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert attacker.hp == max_hp - max_hp // 2
    assert defender.has_volatile("のろい")
    assert defender.volatiles["みがわり"].hp == 999
