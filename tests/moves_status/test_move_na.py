"""変化技ハンドラの単体テスト（な行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


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
    assert attacker.rank["A"] == -1
    assert defender.rank["A"] == 0
    # なりきりでいかくをコピーする
    t.run_move(battle, 0)
    assert attacker.ability.name == "いかく"
    # ON_ABILITY_ENABLEDによっていかくが再発動し、defenderのこうげきが-1になる
    assert defender.rank["A"] == -1


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


@pytest.mark.parametrize("d_ability", ["アイスフェイス", "イリュージョン"])
def test_なりきり_失敗条件(d_ability):
    """なりきり: uncopyable/protectedフラグ持ちの相手には失敗する"""
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
    attacker.rank["B"] = 1
    attacker.rank["D"] = 1
    t.run_move(battle, 0)

    # クリアボディでも自分源のランク低下は防げない
    assert attacker.rank["B"] == 0
    assert attacker.rank["D"] == 0


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
