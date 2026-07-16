"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.enums import Command, Interrupt, LogCode
from jpoke.types import AilmentName

from .. import test_utils as t

ALL_AILMENTS = ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"]


def test_かがくへんかガス_いえきでとくせいなしになると相手の特性が再有効化される():
    """かがくへんかガス: いえき等でガス保持者自身がとくせいなし状態になり
    特性が無効化された直後に、ガスの効果自体が切れて相手の特性が再有効化される。"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", ability_name="かがくへんかガス")],
        team1=[Pokemon("ライチュウ", ability_name="せいでんき")],
        volatile0={"とくせいなし": 3},
    )
    gas_mon = battle.actives[0]
    foe = battle.actives[1]
    assert not gas_mon.ability.enabled
    assert foe.ability.enabled


def test_かがくへんかガス_瀕死交代でも解除後は特性が再び有効化される():
    """瀕死になったかがくへんかガス持ちが交代する際も、通常の交代と同様に相手の
    特性無効化を解除する（Handler.allow_fainted_subjectの回帰テスト。
    fuzz_log seed=1183参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ふとうのけん")],
    )
    gas_mon = battle.actives[0]
    mon = battle.actives[1]
    assert mon.boosts["atk"] == 0

    battle.modify_hp(gas_mon, -gas_mon.hp)
    assert gas_mon.fainted
    t.run_switch(battle, 0, 1)
    assert mon.boosts["atk"] == 1


def test_かがくへんかガス_登場時に相手の特性を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ピカチュウ", ability_name="ふとうのけん")],
    )
    mon = battle.actives[1]
    assert not mon.ability.enabled
    assert not mon.ability.revealed
    assert mon.boosts["atk"] == 0


def test_かがくへんかガス_解除後は特性が再び有効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ふとうのけん")],
    )
    mon = battle.actives[1]
    assert mon.boosts["atk"] == 0

    t.run_switch(battle, 0, 1)
    assert mon.boosts["atk"] == 1


def test_かぜのり_おいかぜ状態でなければ登場時上昇なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    assert battle.actives[1].boosts["atk"] == 0


def test_かぜのり_おいかぜ状態で登場時こうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        side1={"おいかぜ": 3},
    )
    assert battle.actives[1].boosts["atk"] == 1


def test_かぜのり_おいかぜ発生時にこうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    mon = battle.actives[1]
    battle.get_side(mon).activate("おいかぜ", 3)
    assert mon.boosts["atk"] == 1


def test_かぜのり_かたやぶりで風技吸収無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.boosts["atk"] == 0


def test_かぜのり_みがわり状態でも風の技を吸収して発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        accuracy=100,
    )
    _, defender = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    assert defender.volatiles["みがわり"].hp == 999
    assert defender.boosts["atk"] == 1


def test_かぜのり_対象外の技は通常被弾():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.boosts["atk"] == 0


def test_かぜのり_風の技を吸収してこうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp
    assert defender.boosts["atk"] == 1


def test_かそく_すばやさランクが最大なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かそく", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.boosts["spe"] = 6

    t.reserve_command(battle, command0=Command.MOVE_0)
    battle.step()
    assert mon.boosts["spe"] == 6


def test_かそく_まひで最初の行動がPP消費なしで失敗しても発動する():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="かそく", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動不能になる設定（フルパラ）
    battle.test_option.trigger_ailment = True

    t.reserve_command(battle, command0=Command.MOVE_0)
    battle.step()

    assert not battle.move_executor.action_success
    assert mon.boosts["spe"] == 1


def test_かそく_まもる連続使用失敗後もターン終了時にすばやさが上がる():
    """かそく: まもるを連続使用して2回目が失敗しても、行動自体はしているため
    ターン終了時にすばやさが上がる。かそくの判定は acted_since_switch_in を見ており、
    まもる系連続使用失敗チェック（last_move/failed_or_immobile_last_turn を参照）
    とは独立しているため、連続使用失敗がかそくの判定に巻き添えにならないことを確認する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かそく", move_names=["まもる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: まもる成功
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    t.end_turn(battle)
    assert attacker.boosts["spe"] == 1

    # 2ターン目: まもる失敗（連続使用）だが行動自体はしているのでかそくは発動する
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    t.end_turn(battle)
    assert attacker.boosts["spe"] == 2


def test_かそく_交代直後のターンは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="かそく", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # 交代したターンはかそくが発動しない
    t.reserve_command(battle, command0=Command.SWITCH_1)
    battle.step()

    mon = battle.actives[0]
    assert mon.boosts["spe"] == 0

    # 次のターンはかそくが発動する
    t.reserve_command(battle, command0=Command.MOVE_0)
    battle.step()
    assert mon.boosts["spe"] == 1


def test_かたいツメ_パンチグローブ所持時はパンチ技に発動しない():
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ",
            ability_name="かたいツメ",
            item_name="パンチグローブ",
            move_names=["ほのおのパンチ"],
        )],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    # パンチグローブによる1.1倍（4506）のみが適用され、かたいツメの補正はかからない
    assert battle.damage_calculator.power_modifier == 4506


@pytest.mark.parametrize(
    "move_name, expected_boost",
    [
        ("たいあたり", 5325),
        ("でんきショック", 4096),
    ]
)
def test_かたいツメ_接触技のみ威力補正1_3倍(move_name, expected_boost):
    battle_contact = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたいツメ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle_contact, 0)
    assert expected_boost == battle_contact.damage_calculator.power_modifier


def test_かたやぶり_場に出たときに特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed


def test_かちき_特攻が最大のときはそれ以上上がらない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かちき")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.boosts["spa"] = 6
    battle.modify_stats(mon, {"atk": -1}, source=battle.actives[1])
    assert mon.boosts["spa"] == 6


def test_かちき_複数能力低下技で下がった数だけ発動する():
    # くすぐるはこうげき・ぼうぎょを1段階ずつ下げる技のため、かちきが2回発動して特攻が4段階上がる
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かちき")],
        team1=[Pokemon("ピカチュウ", move_names=["くすぐる"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    mon = battle.actives[0]
    assert mon.boosts["atk"] == -1
    assert mon.boosts["def"] == -1
    assert mon.boosts["spa"] == 4


def test_カブトアーマー_かたやぶりで無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カブトアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is True


def test_カブトアーマー_急所に当たらない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カブトアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is False


def test_かるわざ_アイテムを再取得すると発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    t.change_item(battle, mon, "オボンのみ")
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_かるわざ_アイテムを失うと素早さが2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] * 2


def test_かるわざ_アイテムを失ってから再入場しても発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_かるわざ_入場時にアイテムなしなら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_かるわざ_未発動時にかがくへんかガス中にアイテムを失うと解除後も発動しない():
    """かるわざ: 未発動のときにかがくへんかガスが発動し、その間にアイテムを失った場合、
    ガスが解除されてもかるわざは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    battle.item_manager.consume_item(mon)
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_かるわざ_発動中にかがくへんかガスが発動しても解除後は発動状態を維持する():
    """かるわざ: かがくへんかガスが発動している間は効果が止まるが、解除されれば再度発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] * 2

    battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]

    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] * 2


def test_かんそうはだ_HP満タンならみず技無効化のみで回復しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ")],
        team1=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp
    assert mon.ability.revealed


def test_かんそうはだ_あめが止むターンでは回復しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 1),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert battle.weather.name == ""
    assert mon.hp == 1


def test_かんそうはだ_あめ中はターン終了時に最大HPの1_8回復():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 8


def test_かんそうはだ_はれ中はターン終了時に最大HPの1_8ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    hp_before = mon.hp
    t.end_turn(battle)
    assert mon.hp == hp_before - mon.max_hp // 8


def test_かんそうはだ_ばんのうがさ所持時は天候効果が発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ", item_name="ばんのうがさ")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_かんそうはだ_ほのお技のダメージが5_4倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    t.run_move(battle, 1)
    assert battle.damage_calculator.damage_modifier == 5120


def test_かんそうはだ_みず技はかたやぶりで無効化されず通常ダメージを受ける():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["みずでっぽう"])],
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp < mon.max_hp
    assert not mon.ability.revealed


def test_かんそうはだ_みず技を無効化してHPが減っていれば1_4回復():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ")],
        team1=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1 + mon.max_hp // 4
    assert mon.ability.revealed


def test_かんそうはだ_同ターンに瀕死になったポケモンは回復しない():
    """かんそうはだ: 同ターン中の攻撃で先にHPが0になったポケモンは、
    あめ中でもターン終了時のかんそうはだ回復を受けずに瀕死のままとなる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんそうはだ"), Pokemon("コラッタ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        weather=("あめ", 5),
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 0
    assert mon.fainted
    t.end_turn(battle)
    assert mon.hp == 0
    assert mon.fainted


def test_かんろなミツ_みがわり状態の相手には無効():
    battle = t.start_battle(
        team0=[Pokemon("コラッタ"), Pokemon("ピカチュウ", ability_name="かんろなミツ")],
        team1=[Pokemon("カビゴン", move_names=["みがわり"])],
    )
    t.run_move(battle, 1)
    t.run_switch(battle, 0, 1)
    mon, foe = battle.actives
    assert foe.boosts["evasion"] == 0
    assert mon.ability.revealed
    assert not mon.ability.enabled


def test_かんろなミツ_入場時一度だけ発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんろなミツ"), Pokemon("イーブイ")],
        team1=[Pokemon("カビゴン")],
    )
    mon, foe = battle.actives
    assert foe.boosts["evasion"] == -1
    assert mon.ability.revealed
    assert not mon.ability.enabled

    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert foe.boosts["evasion"] == -1


def test_かんろなミツ_発動ログに特性名が記録される():
    """かんろなミツは発動と同時に自己無効化（"consumed"）されるため、ログ記録時点で
    ability.name が空文字にならず、常に元の特性名（base_name）を使って記録されることを確認する
    （fuzz_log seed=19 で発見されたログ空欄バグの回帰）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんろなミツ")],
        team1=[Pokemon("カビゴン")],
    )
    logs = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED
        and log.payload is not None
        and getattr(log.payload, "ability", None) == "かんろなミツ"
    ]
    assert len(logs) == 1


def test_カーリーヘアー_直接攻撃で攻撃者のSが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カーリーヘアー")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.ability.revealed
    assert attacker.boosts["spe"] == -1


def test_カーリーヘアー_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カーリーヘアー")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert not defender.ability.revealed
    assert attacker.boosts["spe"] == 0


def test_がんじょう_HP満タン時の致死ダメージでHP1残る():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ガブリアス", move_names=["じしん"])],
    )
    defender, _ = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == 1
    assert defender.ability.revealed


def test_がんじょう_かたやぶりで一撃技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じわれ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.move_executor.move_applied is True


def test_がんじょう_かたやぶりで耐えない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ガブリアス", ability_name="かたやぶり", move_names=["じしん"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].hp == 0


def test_がんじょう_きあいのタスキと併せ持つときはがんじょうが優先():
    """がんじょうときあいのタスキを両方持つ場合、がんじょうが先に発動してHP1で耐え、
    きあいのタスキは消費されない（実戦闘のイベント経路での確認。lethal計算側は
    tests/test_lethal.py の同名テストで確認済み）。"""
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう", item_name="きあいのタスキ")],
        team1=[Pokemon("ガブリアス", move_names=["じしん"])],
    )
    defender, _ = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == 1
    assert defender.ability.revealed
    assert defender.has_item()


def test_がんじょう_こんらんの自傷ダメージでもHP1残る():
    """こんらんの自傷ダメージ（ON_MODIFY_NON_MOVE_DAMAGE 経由）も、
    HP満タン時はがんじょうでHP1残る（docs/spec/abilities/がんじょう.md 参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    defender = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 0)
    assert defender.hp == 1
    assert defender.ability.revealed


def test_がんじょう_一撃必殺技は命中判定前に無効化される():
    """一撃必殺技を受けたときは、命中判定が行われる前にがんじょうで無効化される
    （命中率30%のじわれが本来なら外れる乱数でも、がんじょうが先に発動してMISSにならない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["じわれ"])],
    )
    t.fix_random(battle, 0.99)
    defender, _ = battle.actives
    t.run_move(battle, 1)
    assert battle.move_executor.move_success is False
    assert battle.move_executor.move_missed is False
    assert defender.hp == defender.max_hp
    assert defender.ability.revealed


def test_がんじょう_一撃必殺技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["じわれ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.move_executor.move_success is False


def test_がんじょう_連続技の1発目で発動すると2発目は不発():
    """連続攻撃技を受けた場合、がんじょうが発動できるかは各攻撃ごとに判定される。
    1発目を受けてHPが減少しているとき、2発目を受けるとがんじょうは発動しない
    （docs/spec/abilities/がんじょう.md 参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["ダブルアタック"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)
    assert not defender.alive


def test_がんじょうあご_いかりのまえばはかみつき技でないため威力補正がかからない():
    """いかりのまえばは固定ダメージ技で通常の威力計算を経由しないため、
    がんじょうあごを持っていても威力補正（power_modifier）自体が計算されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょうあご", move_names=["いかりのまえば"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier is None


def test_がんじょうあご_かみつき技で威力補正1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょうあご", move_names=["かみつく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_ききかいひ_HPが半分以下になると交代():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.step()

    assert battle.actives[0] is not defender


def test_ききかいひ_こんらん自傷では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.modify_hp(defender, v=-1, reason="self_attack")

    assert battle.actives[0] is defender


def test_ききかいひ_ちからずくの技のダメージでも発動する():
    """相手がちからずくで追加効果技（secondary_effect フラグ持ち）を使用した場合の
    ダメージ(move_damage)でも、Championsではききかいひが通常どおり発動する
    （第七世代からSVまでは不発だったが、Championsではこの制限が撤廃されている。
    docs/spec/abilities/ききかいひ.md参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", ability_name="ちからずく", move_names=["かえんほうしゃ"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    attacker.last_move = attacker.moves[0]
    defender.hp = defender.max_hp
    battle.modify_hp(defender, v=-(defender.max_hp // 2 + 1), source=attacker, reason="move_damage")

    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.EMERGENCY


def test_ききかいひ_はらだいこの自己HP消費では発動しない():
    """はらだいこのHP消費(self_cost)ではききかいひが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ", move_names=["はらだいこ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp * 9 // 10
    t.run_move(battle, 0)

    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_ききかいひ_みがわりの自己HP消費では発動しない():
    """みがわりのHP消費(self_cost)ではききかいひが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ", move_names=["みがわり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp * 6 // 10
    t.run_move(battle, 0)

    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_ききかいひ_やけどダメージでも発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("やけど", None),
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.step()

    assert battle.actives[0] is not defender


def test_ききかいひ_控えがいない場合は発動しない():
    """交代先の控えがいない場合はききかいひが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.step()

    assert battle.actives[0] is defender


def test_ききかいひ_相手のいたみわけを受けても発動しない():
    """相手のいたみわけによるHP均等化(pain_split)ではききかいひが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", move_names=["いたみわけ"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp
    attacker = battle.actives[1]
    attacker.hp = 1
    t.run_move(battle, 1)

    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_ききかいひ_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2
    battle.step()

    assert battle.actives[0] is defender


@pytest.mark.parametrize(
    "move_name, revealed",
    [
        ("じしん", True),
        ("つのドリル", True),
        ("なきごえ", False),
        ("たいあたり", False)
    ]
)
def test_きけんよち_特性が開示される(move_name, revealed):
    # ピカチュウ(でんき)に対してじしん(じめん、2倍) → みぶるいした
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きけんよち")],
        team1=[Pokemon("ピカチュウ", move_names=[move_name])],
    )
    assert battle.actives[0].ability.revealed is revealed


def test_きもったま_いかくを無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きもったま")],
        team1=[Pokemon("ウインディ", ability_name="いかく")],
    )
    assert battle.actives[0].boosts["atk"] == 0


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("かわらわり", 8192),  # かくとう技 → はがねに2倍
        ("たいあたり", 2048),  # ノーマル技 → ゴーストに等倍
    ]
)
def test_きもったま_かくとう技がゴースト複合に抜群(move_name, expected_modifier):
    # かわらわり(かくとう) vs サーフゴー(はがね/ゴースト) → はがね×2倍
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きもったま", move_names=[move_name])],
        team1=[Pokemon("サーフゴー", ability_name="")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected_modifier


def test_きゅうばん_かたやぶりで無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("フシギダネ")],
    )
    mon = battle.actives[1]
    t.run_move(battle, 0)
    # かたやぶりによってきゅうばんの無効化が貫通され、交代が発生する
    assert mon is not battle.actives[1]


def test_きゅうばん_吹き飛ばしを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("フシギダネ")],
    )
    mon = battle.actives[1]
    t.run_move(battle, 0)
    # きゅうばんにより交代が阻止され、アクティブは変わらない
    assert mon is battle.actives[1]


def test_きょううん_急所ランクが1上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きょううん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 1


def test_きよめのしお_あくびのねむけ無効():
    """きよめのしお: あくびによるねむけ状態も無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きよめのしお")],
        team1=[Pokemon("カビゴン", move_names=["あくび"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert not battle.actives[0].has_volatile("ねむけ")


def test_きよめのしお_かたやぶりのあくびはねむけになるが次のターンねむりにならない():
    """きよめのしお: かたやぶりであくびを受けたときはねむけ状態になるが、
    ねむけ→ねむりへの移行は特性により防がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きよめのしお")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["あくび"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.has_volatile("ねむけ")
    assert not mon.has_ailment("ねむり")

    t.end_turn(battle)
    t.end_turn(battle)
    assert not mon.has_volatile("ねむけ")
    assert not mon.has_ailment("ねむり")


def test_きよめのしお_ゴースト半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シャドーボール"])],
        team1=[Pokemon("ピカチュウ", ability_name="きよめのしお")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 2048


@pytest.mark.parametrize(
    "ailment_name",
    ALL_AILMENTS
)
def test_きよめのしお_状態異常無効(ailment_name):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きよめのしお")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert not t.apply_ailment(battle, 0, ailment_name)


def test_きれあじ_きる技は威力補正1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きれあじ", move_names=["きりさく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_きれあじ_きる技以外は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きれあじ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_きれあじ_連続技でとれないにおいにより2発目以降は補正なし():
    """きれあじ: ネズミざんのような接触連続技をとれないにおい特性の相手に使用した場合、
    1発目で特性が上書きされるため、2発目以降はきれあじの威力補正が適用されなくなる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability_name="きれあじ", move_names=["ネズミざん"])],
        team1=[Pokemon("カビゴン", ability_name="とれないにおい")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    power_modifiers: list[int | None] = []
    original_roll_damage = battle.roll_damage

    def _tracking_roll_damage(*args, **kwargs):
        damage = original_roll_damage(*args, **kwargs)
        power_modifiers.append(battle.damage_calculator.power_modifier)
        return damage

    battle.roll_damage = _tracking_roll_damage
    t.run_move(battle, 0)
    assert attacker.ability.name == "とれないにおい"
    assert power_modifiers[0] == 6144
    assert all(m == 4096 for m in power_modifiers[1:])
    assert len(power_modifiers) > 1


def test_きんしのちから_変化技でクリアボディを無視できる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きんしのちから", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["atk"] == -1


def test_きんしのちから_変化技選択時に同優先度で最後に行動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きんしのちから", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]


def test_きんしのちから_攻撃技選択時は後攻化しない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="きんしのちから", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    # コイルより素早いピカチュウが先攻のまま
    assert order[0] == battle.actives[1]


def test_きんちょうかん_相手をきんちょうかん状態にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="きんちょうかん")],
    )
    assert battle.actives[1].ability.revealed
    assert battle.query.is_nervous(battle.actives[0])


def test_きんちょうかん_自身がひんしになった瞬間に効果が解除される():
    """きんちょうかん: 場から去るか特性が効かなくなった瞬間にきのみ使用禁止の効果が失われる。
    ひんしになった場合、交代（後続の繰り出し）を待たずその時点で解除される。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="きんちょうかん")],
    )
    assert battle.query.is_nervous(battle.actives[0])
    battle.faint(battle.actives[1])
    assert battle.actives[1].fainted
    assert not battle.query.is_nervous(battle.actives[0])


def test_ぎたい_かがくへんかガスの効果中は発動せず解除後に即座に発動する():
    battle = t.start_battle(
        team0=[Pokemon("マッギョ(ガラル)", ability_name="ぎたい")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("グラスフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.types == ["くさ"]

    battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    battle.terrain_manager.remove()
    assert mon.types == ["くさ"]

    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert mon.types == ["じめん", "はがね"]


def test_ぎたい_テラスタルしていない場合はフィールド変化で従来通り発動する():
    """対称ケース: テラスタルしていなければフィールド変化で通常通りタイプが変わり、
    発動アナウンス（ABILITY_TRIGGERED ログ）も記録される。"""
    battle = t.start_battle(
        team0=[Pokemon("マッギョ(ガラル)", ability_name="ぎたい")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.types == ["じめん", "はがね"]

    battle.terrain_manager.apply("グラスフィールド", 5)

    assert mon.types == ["くさ"]
    triggered = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED
        and log.payload is not None
        and getattr(log.payload, "ability", None) == "ぎたい"
    ]
    assert len(triggered) == 1


def test_ぎたい_テラスタル中はフィールド変化が起きてもタイプが変化せず発動しない():
    """ぎたい: テラスタル中は Pokemon.types が active_tera_type を最優先するため、
    フィールド変化イベントが起きても ability_override_type の書き換えは実際のタイプに
    反映されない。その場合は発動アナウンス（ABILITY_TRIGGERED ログ）も出ない
    （fuzzログ回帰: seed=682, メルメタル+テラスタル済み+みずタイプに対する
    「すなあらしが始まった」契機で誤発動していた）。"""
    battle = t.start_battle(
        team0=[Pokemon("マッギョ(ガラル)", ability_name="ぎたい", tera_type="みず")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.is_terastallized = True
    assert mon.types == ["みず"]

    battle.terrain_manager.apply("グラスフィールド", 5)

    assert mon.types == ["みず"]
    triggered = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED
        and log.payload is not None
        and getattr(log.payload, "ability", None) == "ぎたい"
    ]
    assert triggered == []


def test_ぎたい_フィールドが無い状態で登場すると本来のタイプのまま発動しない():
    battle = t.start_battle(
        team0=[Pokemon("マッギョ(ガラル)", ability_name="ぎたい")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.types == ["じめん", "はがね"]
    assert mon.ability.revealed is False


@pytest.mark.parametrize("terrain, expected_type", [
    ("エレキフィールド", "でんき"),
    ("グラスフィールド", "くさ"),
    ("ミストフィールド", "フェアリー"),
    ("サイコフィールド", "エスパー"),
])
def test_ぎたい_フィールドが発生している場に繰り出すと対応タイプに変化する(terrain: str, expected_type: str):
    battle = t.start_battle(
        team0=[Pokemon("マッギョ(ガラル)", ability_name="ぎたい")],
        team1=[Pokemon("ピカチュウ")],
        terrain=(terrain, 5),
    )
    mon = battle.actives[0]
    assert mon.types == [expected_type]
    assert mon.ability.revealed is True


def test_ぎたい_フィールドが解除されると本来のタイプに戻る():
    battle = t.start_battle(
        team0=[Pokemon("マッギョ(ガラル)", ability_name="ぎたい")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.types == ["フェアリー"]

    battle.terrain_manager.remove()
    assert mon.types == ["じめん", "はがね"]


def test_ぎたい_交代すると本来のタイプに戻り再度場に出ると再びタイプが変わる():
    battle = t.start_battle(
        team0=[
            Pokemon("マッギョ(ガラル)", ability_name="ぎたい"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.types == ["でんき"]

    t.run_switch(battle, 0, 1)
    assert mon.types == ["じめん", "はがね"]

    t.run_switch(battle, 0, 0)
    assert battle.actives[0] is mon
    assert mon.types == ["でんき"]


def test_ぎたい_特性がぎたいに変わると即座にフィールドに応じたタイプになる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いかく")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.types == ["でんき"]

    battle.change_ability(mon, "ぎたい")
    assert mon.types == ["エスパー"]


def test_ぎたい_自身が場にいる状態でフィールドが変化すると即座にタイプが変わる():
    battle = t.start_battle(
        team0=[Pokemon("マッギョ(ガラル)", ability_name="ぎたい")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.types == ["じめん", "はがね"]

    battle.terrain_manager.apply("グラスフィールド", 5)
    assert mon.types == ["くさ"]

    battle.terrain_manager.apply("サイコフィールド", 5)
    assert mon.types == ["エスパー"]


def test_ぎゃくじょう_HPが半分以下になると攻撃が1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender, _ = battle.actives
    defender.hp = defender.max_hp // 2 + 1
    t.run_move(battle, 1)

    assert defender.boosts["spa"] == 1
    assert defender.ability.revealed is True


def test_ぎゃくじょう_さまようたましいで多段技のヒット途中に特性を獲得しても正しく判定する():
    """ぎゃくじょう: さまようたましいでコンタクト技のヒット途中に本特性を獲得した場合、
    1発目の時点ではまだ特性を持っておらずハンドラが呼ばれないため、獲得後最初のヒット
    （このケースでは2発目）を受ける前のHPを基準に判定する
    （かつてはこのケースで基準HPが未設定のまま最終ヒットで参照されAttributeErrorになっていた）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="さまようたましい")],
        team1=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう", move_names=["トリプルアクセル"])],
        accuracy=100,
        damage_roll="max",
    )
    t.fix_random(battle, 0.99)  # 急所を回避する
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]
    power_sequence = move.data.multi_hit["power_sequence"]

    expected_damages = []
    for power in power_sequence:
        move.base_power = power
        expected_damages.append(battle.roll_damage(attacker, defender, move, critical=False))

    # 2発目終了時点（＝特性獲得後最初のヒット直前）ではまだ半分を上回るように調整する。
    half = defender.max_hp // 2
    start_hp = half + expected_damages[0] + expected_damages[1] // 2 + 1
    defender.hp = start_hp
    assert (start_hp - expected_damages[0]) * 2 > defender.max_hp  # 2発目直前では下回らない
    assert (start_hp - sum(expected_damages)) * 2 <= defender.max_hp  # 3発目で下回る

    t.run_move(battle, 1)

    assert defender.alive
    assert defender.ability.base_name == "ぎゃくじょう"
    assert attacker.ability.base_name == "さまようたましい"
    assert defender.hp == start_hp - sum(expected_damages)
    assert defender.boosts["spa"] == 1


def test_ぎゃくじょう_さまようたましいで特性獲得時点で既に半分以下なら発動しない():
    """ぎゃくじょう: さまようたましいでコンタクト技のヒット途中に本特性を獲得した時点
    （このケースでは2発目直前）で既にHPが半分以下の場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="さまようたましい")],
        team1=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう", move_names=["トリプルアクセル"])],
        accuracy=100,
        damage_roll="max",
    )
    t.fix_random(battle, 0.99)  # 急所を回避する
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]
    power_sequence = move.data.multi_hit["power_sequence"]

    expected_damages = []
    for power in power_sequence:
        move.base_power = power
        expected_damages.append(battle.roll_damage(attacker, defender, move, critical=False))

    half = defender.max_hp // 2
    start_hp = half + expected_damages[0]
    defender.hp = start_hp
    assert (start_hp - expected_damages[0]) * 2 <= defender.max_hp  # 2発目直前で既に半分以下

    t.run_move(battle, 1)

    assert defender.alive
    assert defender.ability.base_name == "ぎゃくじょう"
    assert defender.boosts["spa"] == 0


def test_ぎゃくじょう_ちからずくの技を受けても発動する():
    """ぎゃくじょう: Championsではちからずくの効果が発動した技を受けたときも
    通常通り発動する（docs/spec/abilities/ちからずく.md参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["かえんほうしゃ"])],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    t.run_move(battle, 1)

    assert defender.boosts["spa"] == 1


def test_ぎゃくじょう_とくこうランクが最大なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    defender.boosts["spa"] = 6
    t.run_move(battle, 1)

    assert defender.boosts["spa"] == 6


def test_ぎゃくじょう_ひんし時は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう"), Pokemon("コラッタ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)

    assert defender.fainted
    assert defender.boosts["spa"] == 0


def test_ぎゃくじょう_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2
    t.run_move(battle, 1)

    assert defender.boosts["spa"] == 0


def test_ぎゃくじょう_連続攻撃技は最終ヒット後にまとめて判定する():
    """ぎゃくじょう: 連続攻撃技の途中でHPが半分を下回っても、全ヒットが終わるまで発動しない。

    1発目を受ける前のHPを基準にまとめて判定されることを、2発目終了後のHPと
    最終的なとくこうランクの両方から確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["トリプルアクセル"])],
        accuracy=100,
        damage_roll="最大",
    )
    t.fix_random(battle, 0.99)  # 急所を回避する
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]
    power_sequence = move.data.multi_hit["power_sequence"]

    expected_damages = []
    for power in power_sequence:
        move.base_power = power
        expected_damages.append(battle.roll_damage(attacker, defender, move, critical=False))

    # 2発目終了時点でHPが半分を下回るように調整する。
    half = defender.max_hp // 2
    start_hp = half + expected_damages[0] + expected_damages[1] // 2 + 1
    defender.hp = start_hp
    assert (start_hp - expected_damages[0]) * 2 > defender.max_hp  # 1発目では下回らない
    assert (start_hp - expected_damages[0] - expected_damages[1]) * 2 <= defender.max_hp  # 2発目で下回る

    t.run_move(battle, 1)

    assert defender.alive
    assert defender.hp == start_hp - sum(expected_damages)
    assert defender.boosts["spa"] == 1


def test_ぎょぐん_HP1_4以下で登場してもたんどくのすがたのまま():
    mon = Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん")
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), mon],
        team1=[Pokemon("コラッタ")],
    )
    mon.hp = mon.max_hp // 4
    t.run_switch(battle, 0, 1)
    assert mon.name == "ヨワシ(たんどく)"


def test_ぎょぐん_HP1_4超で登場するとむれたすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヨワシ(むれ)"


def test_ぎょぐん_ターン終了時にHP1_4以下ならたんどくのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(むれ)", ability_name="ぎょぐん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4
    t.end_turn(battle)
    assert mon.name == "ヨワシ(たんどく)"


def test_ぎょぐん_ターン終了時にHP1_4超ならむれたすがたを維持する():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(むれ)", ability_name="ぎょぐん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.name == "ヨワシ(むれ)"


def test_ぎょぐん_ヨワシ以外はターン終了時にフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎょぐん")],
        team1=[Pokemon("コラッタ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4
    t.end_turn(battle)
    assert mon.name == "ピカチュウ"


def test_ぎょぐん_ヨワシ以外は登場時にフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎょぐん")],
        team1=[Pokemon("コラッタ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ピカチュウ"


def test_ぎょぐん_レベル20未満ではターン終了時にフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(むれ)", ability_name="ぎょぐん", level=19)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4
    t.end_turn(battle)
    assert mon.name == "ヨワシ(むれ)"


def test_ぎょぐん_レベル20未満では登場時にフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん", level=19)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヨワシ(たんどく)"


def test_くいしんぼう_HP1_2以下でイアのみが発動する():
    """くいしんぼう: 本来HP1/4以下でしか発動しないイアのみをHP1/2以下で発動できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くいしんぼう", item_name="イアのみ", nature="いじっぱり")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + mon.max_hp // 3
    assert not mon.has_item()


def test_くいしんぼう_HP1_2以下でイバンのみのフラグが立つ():
    """くいしんぼう: HP1/2以下に下がった瞬間にイバンのみのフラグが立つ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くいしんぼう", item_name="イバンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1
    assert mon.has_item()  # 消費は次の攻撃時


def test_くいしんぼう_HP1_2以下でカムラのみが発動する():
    """くいしんぼう: HP1/2以下に下がった瞬間にカムラのみが発動しすばやさが上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くいしんぼう", item_name="カムラのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["spe"] == 1
    assert not mon.has_item()


def test_くいしんぼう_HP1_2以下でサンのみが発動する():
    """くいしんぼう: HP1/2以下に下がった瞬間にサンのみが発動しきゅうしょアップ状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くいしんぼう", item_name="サンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.has_volatile("きゅうしょアップ")
    assert not mon.has_item()


def test_くいしんぼう_HP1_2以下でスターのみが発動する():
    """くいしんぼう: HP1/2以下に下がった瞬間にスターのみが発動しランダムな能力が上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くいしんぼう", item_name="スターのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.random.choice = lambda seq: seq[0]  # A が選ばれる
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["atk"] == 2
    assert not mon.has_item()


def test_くいしんぼう_HP1_2以下でミクルのみのフラグが立つ():
    """くいしんぼう: HP1/2以下に下がった瞬間にミクルのみのフラグが立つ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くいしんぼう", item_name="ミクルのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1
    assert mon.has_item()  # 消費は次の技使用時


def test_くいしんぼう_HP1_2超では発動しない():
    """くいしんぼう所持でも、HPが1/2より多いときはイアのみが発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くいしんぼう", item_name="イアのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 2
    battle.modify_hp(mon, v=-1)
    assert mon.has_item()


def test_くいしんぼう_オボンのみの発動閾値は変化しない():
    """くいしんぼう: もとから最大HPの1/2以下で発動するオボンのみには効果が無い"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くいしんぼう", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 2
    battle.modify_hp(mon, v=-1)
    assert mon.has_item()  # HPが1/2超のため発動しない（くいしんぼうでも緩和されない）

    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + mon.max_hp // 4
    assert not mon.has_item()


def test_くいしんぼう_非所持ならHP1_4超1_2以下でイアのみは発動しない():
    """くいしんぼうを持たない場合は従来通りHP1/4以下でしか発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="イアのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.has_item()


def test_クイックドロウ_30パーセント発動しないとき通常行動順():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 1.0  # 発動しない
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]


def test_クイックドロウ_トリックルーム状態でも先攻になる():
    """クイックドロウはトリックルーム状態でも行動順が早くなる。"""
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        field={"トリックルーム": 5},
    )
    t.fix_random(battle, 0.0)  # クイックドロウを必ず発動させる
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]  # トリックルームで本来後攻のコイルが先攻になる


def test_クイックドロウ_優先度が異なる技には発動しても後攻になる():
    """クイックドロウは優先度を変化させないため、相手が優先度+1技を使えば後攻になる。"""
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    t.fix_random(battle, 0.0)  # クイックドロウを必ず発動させる
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]  # 優先度帯が異なるため後攻のまま


def test_クイックドロウ_変化技選択時は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 0.0  # 乱数を0に固定しても変化技では発動しない
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]
    assert battle.actives[0].ability.revealed is False


def test_クイックドロウ_攻撃技選択時に発動すると先攻になる():
    # コイル(S低い)がクイックドロウで先攻化
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 0.0  # 必ず発動
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]
    assert battle.actives[0].ability.revealed is True


def test_くさのけがわ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


def test_くさのけがわ_グラスフィールドでないと発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


def test_くさのけがわ_グラスフィールドで防御1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_くさのけがわ_こんらんの自傷ダメージには発動しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        team0=[Pokemon("ピカチュウ")],
        volatile1={"こんらん": 2},
        terrain=("グラスフィールド", 5),
    )
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 1)
    assert 4096 == battle.damage_calculator.def_modifier


def test_くさのけがわ_ぼうぎょ参照の特殊技には発動する():
    """サイコショック等、特殊技だがぼうぎょを参照する技には効果が乗る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["サイコショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_くさのけがわ_ワンダールームでとくぼうが1_5倍になる():
    """ワンダールーム中は物理技でも防御と特防が入れ替わり参照されるため、
    くさのけがわの効果は実質的に特防を1.5倍にする形になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5),
        field={"ワンダールーム": 5},
    )
    defender = battle.actives[1]
    before = defender.stats["spd"]
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_defense == round(before * 1.5)


def test_くさのけがわ_特殊技には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


def test_くだけるよろい_しろいきりでは防げない():
    """くだけるよろいの防御低下は自発的な変化のため、しろいきりでも防げない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        side0={"しろいきり": 1},
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["def"] == -1
    assert battle.actives[0].boosts["spe"] == 2


def test_くだけるよろい_すばやさが最大でもぼうぎょは下がる():
    """すでにすばやさランクが最大まで上がっている場合も、ぼうぎょの低下は発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    battle.actives[0].boosts["spe"] = 6
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["def"] == -1
    assert battle.actives[0].boosts["spe"] == 6


def test_くだけるよろい_ぼうぎょが最低でもすばやさは上がる():
    """すでにぼうぎょランクが最低まで下がっている場合も、すばやさの上昇は発動する。

    ぼうぎょが-6段階の状態でダメージを受けると通常のダメージ計算では瀕死になって
    しまう（瀕死時は自分自身への能力ランク変化が発動しない仕様のため検証できない）ので、
    fix_damageで瀕死にならない値に固定する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    battle.actives[0].boosts["def"] = -6
    t.fix_damage(battle, 10)
    t.run_move(battle, 1)
    assert battle.actives[0].fainted is False
    assert battle.actives[0].boosts["def"] == -6
    assert battle.actives[0].boosts["spe"] == 2


def test_くだけるよろい_物理技でB下がりS上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["def"] == -1
    assert battle.actives[0].boosts["spe"] == 2


def test_くだけるよろい_特殊技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["def"] == 0
    assert battle.actives[0].boosts["spe"] == 0


def test_くだけるよろい_被弾して瀕死になった場合はすばやさが上がらない():
    """被弾して瀕死になった場合、くだけるよろいによる自分自身のランク変化は発動しない
    （へんしょく・ぎゃくじょう等の既存特性と同じ規約）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.fix_damage(battle, battle.actives[0].max_hp)
    t.run_move(battle, 1)
    assert battle.actives[0].fainted is True
    assert battle.actives[0].boosts["def"] == 0
    assert battle.actives[0].boosts["spe"] == 0


def test_くだけるよろい_連続攻撃技は1発ごとに発動する():
    """物理技の連続攻撃技を受けた場合、1発ごとにB↓1・S↑2が発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="くだけるよろい")],
        team1=[Pokemon("ピカチュウ", move_names=["トリプルアクセル"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    defender = battle.actives[0]
    assert defender.boosts["def"] == -3
    assert defender.boosts["spe"] == 6  # 2段階 x 3発だが+6で頭打ち


def test_クリアボディ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == -1


def test_クリアボディ_能力低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = {k: v for k, v in stats.items() if v > 0}

    assert expected == battle.modify_stats(mon0, stats, source=mon1)


def test_クリアボディ_自己低下は防げない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, _ = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = stats

    assert expected == battle.modify_stats(mon0, stats, source=mon0)


def test_グラスメイカー_特性再有効化時にも発動する():
    """グラスメイカー: かがくへんかガス解除後に特性が再有効化されると再発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="グラスメイカー")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    # かがくへんかガスにより特性が無効化されているのでフィールドは展開されていない
    assert battle.terrain.name == ""
    # かがくへんかガスの無効化を解除すると特性が再発動してグラスフィールドが展開される
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert battle.terrain.name == "グラスフィールド"
    assert battle.terrain.count == 5


def test_こおりのりんぷん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_こおりのりんぷん_ぼうぎょ参照の特殊技には効果が乗る():
    """サイコショック等、特殊技だがぼうぎょを参照する技にも半減効果が乗る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["サイコショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("でんきショック", 2048),
        ("たいあたり", 4096),
    ],
)
def test_こおりのりんぷん_特殊技のダメージ半減(move_name, expected_modifier):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.damage_modifier


def test_こぼれダネ_こらえるでHP1のまま耐えたときも発動する():
    """こぼれダネ: こらえるでHP1のまま耐えた（実ダメージ0）ときも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こぼれダネ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert defender.hp == 1
    assert battle.terrain.name == "グラスフィールド"
    assert battle.terrain.count == 5


def test_こぼれダネ_すでにグラスフィールドなら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こぼれダネ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        terrain=("グラスフィールド", 3),
    )
    t.run_move(battle, 1)
    assert battle.terrain.name == "グラスフィールド"
    assert battle.terrain.count == 3


def test_こぼれダネ_タイプ相性でダメージを無効化したときは発動しない():
    """こぼれダネ: 攻撃技のダメージを無効化（タイプ相性0倍）したときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", ability_name="こぼれダネ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    hp_before = defender.hp

    t.run_move(battle, 1)

    assert defender.hp == hp_before
    assert battle.terrain.name == ""


def test_こぼれダネ_みがわりに阻まれたときは発動しない():
    """こぼれダネ: みがわりに攻撃を防がれたとき（実ダメージ0）は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こぼれダネ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)

    t.run_move(battle, 1)

    assert battle.terrain.name == ""


def test_こぼれダネ_被弾時にグラスフィールドが展開される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こぼれダネ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.terrain.name == "グラスフィールド"
    assert battle.terrain.count == 5


def test_こぼれダネ_被弾時にグランドコート所持でグラスフィールドが8ターンになる():
    """こぼれダネ: 所有者がグランドコートを持っている場合、グラスフィールドの持続ターンは8になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こぼれダネ", item_name="グランドコート")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.terrain.name == "グラスフィールド"
    assert battle.terrain.count == 8


def test_こんがりボディ_かたやぶり相手には無効化されずダメージを受ける():
    """こんがりボディ: かたやぶりを持つ相手のほのお技は無効化されず通常通りダメージを受ける"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="こんがりボディ")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.boosts["def"] == 0


def test_こんがりボディ_ほのおタイプの変化技も無効化してぼうぎょが2段階上がる():
    """こんがりボディ: おにび等のほのおタイプの変化技を受けても無効化してぼうぎょが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("ピカチュウ", ability_name="こんがりボディ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert defender.boosts["def"] == 2


def test_こんがりボディ_まもるで防がれたときは発動しない():
    """こんがりボディ: まもるでほのお技を防いだときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="こんがりボディ")],
        volatile1={"まもる": 1},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.boosts["def"] == 0
    assert not defender.ability.revealed


def test_こんがりボディ_みがわり状態でも発動してぼうぎょが上がる():
    """こんがりボディ: みがわり状態でほのお技を受けても発動し、ぼうぎょが上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="こんがりボディ")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=100)
    substitute = defender.volatiles["みがわり"]
    t.run_move(battle, 0)
    assert defender.boosts["def"] == 2
    assert substitute.hp == 100


def test_こんがりボディ_自分対象技では発動しない():
    """こんがりボディ: かえんのまもり等、自分自身を対象とする技には発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かえんのまもり"])],
        team1=[Pokemon("ピカチュウ", ability_name="こんがりボディ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_volatile("かえんのまもり")
    assert defender.boosts["def"] == 0
    assert not defender.ability.revealed


def test_こんじょう_こんらん自傷ダメージには補正なし():
    """こんじょう: こんらんの自傷ダメージには攻撃補正がかからない（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="こんじょう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096
    assert attacker.hp < attacker.max_hp


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "やけど"],
)
def test_こんじょう_行動可能な状態異常で攻撃1_5倍(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="こんじょう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, ailment_name)
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144
    assert battle.damage_calculator.burn_modifier == 4096  # やけどによる攻撃半減を無効


def test_ごりむちゅう_かがくへんかガスで無効化中は攻撃補正がかからず自由に技を選べる():
    # 1ターン目のじしんで相手を瀕死にしないよう、あらかじめHP・ぼうぎょのEVを振っておく
    # （相手が瀕死のまま2発目を撃つと対象不在で技自体が不発になってしまうため）
    defender = Pokemon("ピカチュウ")
    defender.set_evs({"hp": 252, "def": 252})
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ガラル)", ability_name="ごりむちゅう", move_names=["じしん", "ようかいえき"])],
        team1=[defender],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0, move_idx=0)
    assert mon.has_volatile("ごりむちゅう")

    battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    assert not mon.ability.enabled
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_commands = [cmd for cmd in commands if cmd.is_type("move")]
    assert {cmd.index for cmd in move_commands} == {0, 1}  # 無効化中は自由に選べる

    t.run_move(battle, 0, move_idx=1)
    assert battle.damage_calculator.atk_modifier == 4096  # 無効化中は攻撃補正がかからない

    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_commands = [cmd for cmd in commands if cmd.is_type("move")]
    assert all(cmd.index == 0 for cmd in move_commands)  # 解除後は無効化前のロックが再度有効になる


def test_ごりむちゅう_こだわりハチマキと重複して2_25倍():
    battle = t.start_battle(
        team0=[Pokemon(
            "ヒヒダルマ(ガラル)", ability_name="ごりむちゅう",
            item_name="こだわりハチマキ", move_names=["じしん"],
        )],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 9216  # 6144 * 6144 / 4096 = 9216 (1.5*1.5=2.25倍)


def test_ごりむちゅう_スキルスワップで得た場合はその技でロックされない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ", "でんこうせっか"])],
        team1=[Pokemon("ヒヒダルマ(ガラル)", ability_name="ごりむちゅう")],
    )
    t.run_move(battle, 0, move_idx=0)
    mon = battle.actives[0]
    assert mon.ability.base_name == "ごりむちゅう"
    assert not mon.has_volatile("ごりむちゅう")
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_commands = [cmd for cmd in commands if cmd.is_type("move")]
    assert {cmd.index for cmd in move_commands} == {0, 1}


def test_ごりむちゅう_ためわざの1ターン目のコマンド解決でロックされる():
    """ごりむちゅう: ためわざ（ソーラービーム）を選択・PP消費したコマンド解決経由
    （battle.get_available_commands→battle.step）の1ターン目時点で、実際に選んだ技
    （ソーラービーム）でごりむちゅうロックが付与される。

    以前はEvent.ON_MOVE_ENDでのみロックしており、ためターン中はON_MOVE_CHARGEが
    Falseを返してON_MOVE_ENDが発火しないため、ロックが2ターン目（強制続行して
    実際に攻撃が発動した後）まで遅延する不具合があった（fuzz_log seed=1404/1408）。
    Event.ON_PP_CONSUMED（PP消費確定直後、ON_MOVE_CHARGEより前に必ず発火する）
    でもロックするよう修正し、1ターン目の時点で確実にロックされることを確認する。

    揮発状態にmove_nameが未設定でわるあがきにフォールバックし、ロックが誤った技
    （わるあがき）で付与される不具合の回帰も兼ねる（t.run_move() はCommand解決層を
    経由しないため、この不具合は検出できない）。
    """
    battle = t.start_battle(
        team0=[Pokemon(
            "カビゴン", ability_name="ごりむちゅう", move_names=["ソーラービーム", "たいあたり"],
        )],
        team1=[Pokemon("カビゴン", move_names=["つるぎのまい"])],
        accuracy=100,
    )
    player0, player1 = battle.players
    mon = battle.actives[0]

    # 1ターン目: 溜め。PP消費時点でごりむちゅうロックが実際に選んだ技（ソーラービーム）
    # で付与される
    battle.step({
        player0: Command.get_move_command(0),
        player1: Command.get_move_command(0),
    })
    assert mon.has_volatile("ソーラービーム")
    assert mon.has_volatile("ごりむちゅう")
    assert mon.volatiles["ごりむちゅう"].move_name == "ソーラービーム"

    # 2ターン目: 強制続行コマンドのみが選択可能になっているはず
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player0)
    assert commands == [Command.FORCED]

    battle.step({player0: Command.FORCED, player1: Command.get_move_command(0)})
    assert not mon.has_volatile("ソーラービーム")

    # 2ターン目に実際にソーラービームが発動した後も、同じ技でロックされ続けている
    assert mon.has_volatile("ごりむちゅう")
    assert mon.volatiles["ごりむちゅう"].move_name == "ソーラービーム"
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player0)
    move_commands = [cmd for cmd in commands if cmd.is_type("move")]
    assert move_commands and all(cmd.index == 0 for cmd in move_commands)  # index 0 = ソーラービーム


def test_ごりむちゅう_なりきりで得た場合はその技でロックされない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なりきり", "でんこうせっか"])],
        team1=[Pokemon("ヒヒダルマ(ガラル)", ability_name="ごりむちゅう")],
    )
    t.run_move(battle, 0, move_idx=0)
    mon = battle.actives[0]
    assert mon.ability.base_name == "ごりむちゅう"
    assert not mon.has_volatile("ごりむちゅう")
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_commands = [cmd for cmd in commands if cmd.is_type("move")]
    assert {cmd.index for cmd in move_commands} == {0, 1}


def test_ごりむちゅう_交代でロックが解除される():
    battle = t.start_battle(
        team0=[
            Pokemon("ヒヒダルマ(ガラル)", ability_name="ごりむちゅう", move_names=["じしん", "ようかいえき"]),
            Pokemon("ライチュウ"),
        ],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0, move_idx=0)
    assert battle.actives[0].has_volatile("ごりむちゅう")
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert not battle.actives[0].has_volatile("ごりむちゅう")
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_commands = [cmd for cmd in commands if cmd.is_type("move")]
    assert {cmd.index for cmd in move_commands} == {0, 1}


def test_ごりむちゅう_最初に選んだ技のみ選択可能になる():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ガラル)", ability_name="ごりむちゅう", move_names=["じしん", "ようかいえき"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0, move_idx=0)
    player = battle.players[0]
    mon = battle.actives[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_commands = [cmd for cmd in commands if cmd.is_type("move")]
    assert move_commands and all(cmd.index == 0 for cmd in move_commands)


def test_ごりむちゅう_物理技の攻撃1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ガラル)", ability_name="ごりむちゅう", move_names=["じしん"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_ごりむちゅう_特殊技には効果がない():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ガラル)", ability_name="ごりむちゅう", move_names=["だいもんじ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,  # だいもんじの命中率(85%)固定漏れで技が外れるとatk_modifierが計算されずflakyになるため
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
