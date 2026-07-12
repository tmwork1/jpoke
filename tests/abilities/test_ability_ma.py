"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import PLATE_TO_TYPE

from .. import test_utils as t

MULTI_TYPE_PLATE_CASES = [
    (plate_item_name, expected_type)
    for plate_item_name, expected_type in PLATE_TO_TYPE.items()
    if plate_item_name in ITEMS
]


def test_マイティチェンジ_ナイーブで交代するとマイティへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "イルカマン(マイティ)"


def test_マイペース_あばれる終了時の自傷こんらんを防ぐ():
    """マイペース: あばれる状態が終了して自身にこんらんが発生する際も防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース", move_names=["あばれる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=1, move_name="あばれる")
    battle.step()
    assert not attacker.has_volatile("あばれる")
    assert not attacker.has_volatile("こんらん")


def test_マイペース_あやしいひかりでこんらんにならない():
    """マイペース: 変化技（あやしいひかり）の効果によるこんらんも防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース")],
        team1=[Pokemon("ピカチュウ", move_names=["あやしいひかり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert not defender.has_volatile("こんらん")


def test_マイペース_いかくを無効化する():
    """マイペース: 第八世代からいかくによるこうげきランク低下を無効化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].boosts["atk"] == 0


def test_マイペース_いばるを受けてもランクは上昇しこんらんにならない():
    """マイペース: いばるの効果でこうげきは上昇するが、こんらんは防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース")],
        team1=[Pokemon("ピカチュウ", move_names=["いばる"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 2
    assert not defender.has_volatile("こんらん")


def test_マジシャン_攻撃後に相手のアイテムを奪う():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert not defender.has_item()


def test_マジシャン_自分がアイテムを持っている場合は奪わない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", item_name="たべのこし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="いのちのたま")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.has_item()


def test_マジックガード_いたみわけを受ける():
    """いたみわけ(pain_split)はマジックガードのブロック対象外なのでHP均等化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いたみわけ"])],
        team1=[Pokemon("ピカチュウ", ability_name="マジックガード")],
    )
    attacker, defender = battle.actives
    # マジックガードを持たないattacker側のHPを減らす
    battle.modify_hp(attacker, -(attacker.max_hp - 10))
    defender_hp = defender.hp  # 満タン
    expected_hp = (10 + defender_hp) // 2
    t.run_move(battle, 0)
    assert defender.hp == expected_hp


def test_マジックガード_すなあらしダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_マジックガード_どくダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_マジックガード_わるあがきの反動ダメージは防げない():
    """マジックガード: わるあがきの反動は通常の反動技と異なる仕様のため無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード", move_names=["わるあがき"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_マジックガード_技ダメージを受ける():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="マジックガード")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_マジックミラー_unreflectableフラグを持つ技は跳ね返さない():
    """マジックミラー: unreflectableフラグを持つうつしえは跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    # 跳ね返されず、通常通り相手の特性がコピーされる
    assert attacker.ability.name == "マジックミラー"


def test_マジックミラー_ステルスロックを跳ね返す():
    """マジックミラー: ステルスロックを跳ね返し、使用者側に設置する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ステルスロック"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.get_side(attacker).get("ステルスロック").is_active
    assert not battle.get_side(defender).get("ステルスロック").is_active


def test_マジックミラー_変化技を跳ね返す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.boosts["atk"] == -1
    assert defender.boosts["atk"] == 0


def test_マルチスケイル_HP満タンのとき半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="マルチスケイル")],
    )
    # 1発目は半減
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier

    # 2発目は半減しない
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_マルチスケイル_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="マルチスケイル")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


@pytest.mark.parametrize("plate_item_name, expected_type", MULTI_TYPE_PLATE_CASES)
def test_マルチタイプ_プレートで対応タイプになる(plate_item_name: str, expected_type: str):
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ", item_name=plate_item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == expected_type
    assert mon.ability.revealed is False  # マルチタイプは開示されない


def test_マルチタイプ_プレートなしでタイプ変更なし():
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None
    assert mon.ability.revealed is False  # プレートなしは不発なので False


def test_マルチタイプ_プレートの奪取を阻止する():
    """マルチタイプ: はたきおとすでプレートを奪取できない。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ", item_name="せいれいプレート")],
        team1=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    # プレートが奪取されずに残っている
    assert mon.item.name == "せいれいプレート"
    assert mon.has_item()


def test_ミイラ_接触技で攻撃した相手の特性がミイラになる():
    """ミイラ: 直接攻撃でダメージを受けたとき攻撃者の特性をミイラにする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ミイラ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.ability.name == "ミイラ"
    assert attacker.ability.name == "ミイラ"
    assert defender.ability.revealed
    assert attacker.ability.revealed


def test_ミイラ_非接触技では特性が変わらない():
    """ミイラ: 非接触技では攻撃者の特性が変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", ability_name="ミイラ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.ability.revealed
    assert attacker.ability.name != "ミイラ"


@pytest.mark.parametrize(
    "move_name, expected_rank",
    [
        ("みずでっぽう", 2),
        ("たいあたり", 0)
    ],
)
def test_みずがため_みず技でBが2段階上がる(move_name: str, expected_rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="みずがため")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["def"] == expected_rank


@pytest.mark.parametrize(
    "move_name, expected_accuracy",
    [
        ("どくどく", 50),
        ("たいあたり", 100)
    ],
)
def test_ミラクルスキン_変化技の命中率を50パーセントに固定する(move_name: str, expected_accuracy: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラクルスキン")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == expected_accuracy


def test_ミラーアーマー_かたやぶりで反射されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == -1
    assert battle.actives[1].boosts["atk"] == 0


def test_ミラーアーマー_反射により相手のかちきが発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かちき")],
    )
    ally, foe = battle.actives
    battle.modify_stats(ally, {"atk": -1}, source=foe)
    assert ally.boosts["atk"] == 0
    assert foe.boosts["atk"] == -1
    assert foe.boosts["spa"] == 2


def test_ミラーアーマー_能力低下のみ反射する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ")],
    )
    ally, foe = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -2}
    battle.modify_stats(ally, stats, source=foe)  # type: ignore
    assert ally.boosts["atk"] == 0
    assert ally.boosts["def"] == 1
    assert ally.boosts["spa"] == 0
    assert foe.boosts["atk"] == -1
    assert foe.boosts["def"] == 0
    assert foe.boosts["spa"] == -2


def test_ミラーアーマー_自己能力低下は反射しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
    )
    target, source = battle.actives
    battle.modify_stats(target, {"atk": -1}, source=target)
    assert battle.actives[0].boosts["atk"] == -1
    assert battle.actives[1].boosts["atk"] == 0


def test_ムラっけ_ターン終了時に別々の能力が上昇と下降する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)

    assert 2 in mon.boosts.values()
    assert -1 in mon.boosts.values()


def test_ムラっけ_全能力が最大なら下降のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd", "spe"):
        mon.boosts[stat] = 6
    t.end_turn(battle)

    assert 5 in mon.boosts.values()


def test_ムラっけ_全能力が最小なら上昇のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd", "spe"):
        mon.boosts[stat] = -6
    t.end_turn(battle)

    assert -4 in mon.boosts.values()


def test_メガソーラー_あめ中でもほのお技が1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["ひのこ"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_メガソーラー_ノーてんき相手でも有効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_メガソーラー_天候なしでほのお技が1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["ひのこ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_メガソーラー_天候なしでみず技が0_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 2048


def test_メガソーラー_攻撃後に天候が元に戻る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["ひのこ"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "あめ"


def test_メガソーラー_相手が攻撃するときは天候補正なし():
    # 天候なし、メガソーラー持ちが防御側のとき相手のほのお技に補正がかからない
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        team1=[Pokemon("カビゴン", ability_name="メガソーラー")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_メタルプロテクト_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メタルプロテクト")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == 0


def test_メロメロボディ_接触攻撃30パーセントでメロメロ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メロメロボディ", gender="female")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"], gender="male")],
    )
    battle.random.random = lambda: 0.29
    t.run_move(battle, 1)
    assert battle.actives[1].has_volatile("メロメロ")


def test_ものひろい_どろぼうで奪われたアイテムは拾わない():
    """ものひろい: take_item（どろぼう相当）で奪われた道具は場に存在し続けるため拾わない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    # どろぼう相当の奪取をtake_itemで再現する（pickup_monがfoeの道具を奪う）
    battle.item_manager.take_item(foe)
    assert pickup_mon.has_item("オボンのみ")
    assert foe.last_lost_item_name == ""

    # 奪った道具をpickup_monが手放す（既にアイテムを保持している間はものひろいが発動しないため）
    battle.item_manager.remove_item(pickup_mon)
    assert not pickup_mon.has_item()
    t.end_turn(battle)
    # foeのlast_lost_item_nameが空のため、ものひろいは発動しない
    assert not pickup_mon.has_item()


def test_ものひろい_相手がアイテムを消費していない場合は拾わない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ")],
    )
    pickup_mon, _ = battle.actives
    t.end_turn(battle)
    assert not pickup_mon.has_item(), "相手がアイテムを消費していないときは何も拾わないはず"


def test_ものひろい_相手が消費したアイテムをターン終了時に拾う():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    assert not pickup_mon.has_item()
    # 相手のアイテムを消費させる
    battle.item_manager.remove_item(foe)
    assert not foe.has_item()
    assert foe.last_lost_item_name == "オボンのみ"
    # ターン終了でものひろい発動
    t.end_turn(battle)
    assert pickup_mon.has_item("オボンのみ"), "ものひろいで相手のアイテムを拾うはず"


def test_ものひろい_自分がアイテムを持っているときは拾わない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    battle.item_manager.remove_item(foe)
    t.end_turn(battle)
    assert pickup_mon.has_item("たべのこし"), "アイテム持ちのときは拾わないはず"


def test_もふもふ_ほのお技を倍加():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.damage_modifier


def test_もふもふ_ほのお接触技は等倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_もふもふ_接触技を半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_もらいび_かたやぶりには貫通される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もらいび")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp
    assert defender.ability.state == "idle"
    assert defender.ability.revealed is False


def test_もらいび_吸収後は最初の炎技のみ1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もらいび", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender, attacker = battle.actives

    # もらいびでひのこを吸収してチャージ状態へ
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp
    assert defender.ability.state == "charged"
    assert defender.ability.revealed

    # もらいびのチャージ状態でひのこを使うと1.5倍
    t.run_move(battle, 0)
    assert defender.ability.state == "idle"
    assert battle.damage_calculator.power_modifier == 6144

    # 2回目: idle なので等倍
    t.run_move(battle, 0)
    assert defender.ability.state == "idle"
    assert battle.damage_calculator.power_modifier == 4096


def test_もらいび_自分対象技では相手の吸収特性は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かえんのまもり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もらいび")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.has_volatile("かえんのまもり")
    assert defender.ability.state == "idle"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
