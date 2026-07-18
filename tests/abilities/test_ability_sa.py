"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.enums import Command, Interrupt, LogCode
from jpoke.types import AilmentName, WeatherName, SideFieldName

from .. import test_utils as t


def test_サイコメイカー_特性再有効化時にも発動する():
    """サイコメイカー: かがくへんかガス解除後に特性が再有効化されると再発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サイコメイカー")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    # かがくへんかガスにより特性が無効化されているのでフィールドは展開されていない
    assert battle.terrain.name == ""
    # かがくへんかガスの無効化を解除すると特性が再発動してサイコフィールドが展開される
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert battle.terrain.name == "サイコフィールド"
    assert battle.terrain.count == 5


def test_さいせいりょく_かいふくふうじ中でも回復する():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="さいせいりょく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": 99}
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_switch(battle, 0, 1)
    assert mon.hp == 1 + mon.max_hp // 3


def test_さいせいりょく_とんぼがえりで交代しても回復する():
    """さいせいりょく: 使うと交代する技（とんぼがえり）で引っ込んだときも回復する。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ヤドン", ability_name="さいせいりょく", move_names=["とんぼがえり"]),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)
    assert mon.hp == 1 + mon.max_hp // 3


def test_さいせいりょく_ひんし時は発動せず正しく退場する():
    """さいせいりょく: 技のダメージでHPが0になって瀕死交代（run_faint_switch経由の
    ON_SWITCH_OUT）で退場するときは発動せず回復しない。

    修正前は退場処理が瀕死かどうかを問わず無条件にON_SWITCH_OUTを発火するため、
    さいせいりょくが誤って最大HPの1/3を回復してしまい、Pokemon.faintedがFalseに
    戻って正式な瀕死処理が成立しなくなっていた（fuzz_log seed=86で検出）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="さいせいりょく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 0
    assert mon.fainted
    # 瀕死交代処理（本来のターン進行が行うON_SWITCH_OUT発火経路）を明示的に実行する
    battle.switch_manager.run_faint_switch()
    # 回復せず瀕死のまま退場している（さいせいりょくが誤発動していない）
    assert mon.hp == 0
    assert mon.fainted
    # 瀕死交代により控えのピカチュウへ正しく入れ替わっている
    assert battle.actives[0].name == "ピカチュウ"


def test_さいせいりょく_交代で控えに戻ると回復する():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="さいせいりょく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_switch(battle, 0, 1)
    assert mon.hp == 1 + mon.max_hp // 3


def test_さいせいりょく_強制交代させられても回復する():
    """さいせいりょく: ドラゴンテール等で強制交代させられたときも回復する。

    与ダメージを固定（fix_damage）した上で、ダメージ後のHPに最大HPの1/3が
    加算されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[
            Pokemon("ヤドン", ability_name="さいせいりょく"),
            Pokemon("ピカチュウ"),
        ],
        accuracy=100,
    )
    mon = battle.actives[1]
    damage = mon.max_hp // 2
    t.fix_damage(battle, damage)
    t.run_move(battle, 0)
    assert mon.hp == mon.max_hp - damage + mon.max_hp // 3


def test_さまようたましい_うのミサイルは例外的に入れ替わる():
    """さまようたましい: うのミサイルはprotectedフラグを持つが、SV Ver.3.0.0以降は
    さまようたましいでの交換が可能になったため例外的に入れ替わる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うのミサイル", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.name == "さまようたましい"
    assert defender.ability.name == "うのミサイル"


def test_さまようたましい_かがくへんかガスは入れ替わらない():
    """さまようたましい: 攻撃者の元の特性がかがくへんかガスの場合、
    とくせいなし状態でガスの抑制が効いておらず相手の特性が有効でも、
    protectedフラグを持たない代わりにbase_nameで交換を防ぐ。"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", ability_name="かがくへんかガス", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
        volatile0={"とくせいなし": 3},
    )
    attacker, defender = battle.actives
    # ガス自体はとくせいなしで無効化されているので相手の特性は抑制されていない
    assert defender.ability.enabled
    t.run_move(battle, 0)
    assert attacker.ability.base_name == "かがくへんかガス"
    assert defender.ability.name == "さまようたましい"


def test_さまようたましい_はらぺこスイッチは入れ替わらない():
    """さまようたましい: 攻撃者の元の特性がはらぺこスイッチの場合、
    protectedフラグを持たない代わりにbase_nameで交換を防ぐ（一次情報:
    「この特性をスキルスワップ/さまようたましいで交換することはできない」）。"""
    battle = t.start_battle(
        team0=[Pokemon("モルペコ(まんぷく)", ability_name="はらぺこスイッチ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.base_name == "はらぺこスイッチ"
    assert defender.ability.name == "さまようたましい"


def test_さまようたましい_ひんしになっても発動する():
    """さまようたましい: 直接攻撃を受けてひんしになったときも特性を入れ替える。"""
    battle = t.start_battle(
        team0=[Pokemon("ウインディ", ability_name="いかく", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.ability.name == "さまようたましい"


def test_さまようたましい_みがわり状態では発動しない():
    """さまようたましい: みがわりが身代わりになった場合はダメージを受けていないので発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ウインディ", ability_name="いかく", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
        volatile1={"みがわり": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.name == "いかく"
    assert defender.ability.name == "さまようたましい"


def test_さまようたましい_同士は互いに交換する():
    """さまようたましい: 攻撃相手もさまようたましいである場合、さまようたましい同士を交換する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="さまようたましい", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.name == "さまようたましい"
    assert defender.ability.name == "さまようたましい"


def test_さまようたましい_特定の特性は書き換えられない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おもかげやどし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    # おもかげやどし は protected フラグを持つので入れ替わらない
    assert attacker.ability.name == "おもかげやどし"
    assert defender.ability.name == "さまようたましい"


def test_さまようたましい_直接攻撃で特性が入れ替わる():
    """さまようたましい: 直接攻撃を受けたとき攻撃者と特性が入れ替わる。"""
    battle = t.start_battle(
        team0=[Pokemon("ウインディ", ability_name="いかく", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.name == "さまようたましい"
    assert defender.ability.name == "いかく"


def test_さまようたましい_非直接攻撃では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ウインディ", ability_name="いかく", move_names=["かえんほうしゃ"])],
        team1=[Pokemon("ヤドン", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.name == "いかく"
    assert defender.ability.name == "さまようたましい"


def test_さめはだ_ひんしになっても発動する():
    """さめはだ: 自身が直接攻撃でひんしになったときも反撃ダメージが発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="さめはだ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    battle.modify_hp(defender, v=-(defender.max_hp - 1))
    t.run_move(battle, 1)
    assert defender.fainted
    assert attacker.hp == attacker.max_hp - int(attacker.max_hp * (1 / 8))


def test_さめはだ_マジックガードの相手にはダメージを与えない():
    """さめはだ: 攻撃者がマジックガード持ちの場合、反撃ダメージを受けない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="さめはだ")],
        team1=[Pokemon("イーブイ", ability_name="マジックガード", move_names=["たいあたり"])],
    )
    _, attacker = battle.actives
    t.run_move(battle, 1)
    assert attacker.hp == attacker.max_hp


def test_さめはだ_みがわりで防いだときは発動しない():
    """さめはだ: 相手のみがわりが技を防いだとき（実HPダメージ0）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="さめはだ")],
        team1=[Pokemon("イーブイ", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 1)
    assert attacker.hp == attacker.max_hp


@pytest.mark.parametrize(
    "ability_name,move_name,damage_ratio",
    [
        ("さめはだ", "たいあたり", 1/8),
        ("さめはだ", "みずでっぽう", 0),
        ("さめはだ", "おはかまいり", 0),
        ("さめはだ", "バーンアクセル", 0),
        ("てつのトゲ", "たいあたり", 1/8),
        ("てつのトゲ", "みずでっぽう", 0),
    ],
)
def test_さめはだ_接触ダメージ(ability_name: str, move_name: str, damage_ratio: float):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=[move_name])],
    )
    _, attacker = battle.actives
    t.run_move(battle, 1)
    assert attacker.hp == attacker.max_hp - int(attacker.max_hp * damage_ratio)


def test_サンパワー_ノーてんき下では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー")],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_サンパワー_はれが止むターンではダメージなし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 1),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert battle.weather.name == ""
    assert mon.hp == mon.max_hp


def test_サンパワー_はれ中にターン終了時1_8ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    t.end_turn(battle)
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp - mon.max_hp // 8


@pytest.mark.parametrize(
    "weather_name,weather_count",
    [
        ("はれ", 5),
        ("おおひでり", 5)
    ]
)
def test_サンパワー_はれ中に特殊技の特攻1_5倍(weather_name: WeatherName, weather_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_サンパワー_はれ以外ではターン終了時ダメージなし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.end_turn(battle)
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp


def test_サンパワー_ばんのうがさ所持時は効果が発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー", item_name="ばんのうがさ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_サンパワー_物理技は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_サーフテール_エレキフィールド中にS2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サーフテール")],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
    )
    mon = battle.actives[0]
    speed_with = battle.speed_calculator.calc_effective_speed(mon)
    assert speed_with == mon.stats["spe"] * 2


def test_サーフテール_他フィールドでは変化なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サーフテール")],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
    )
    mon = battle.actives[0]
    speed = battle.speed_calculator.calc_effective_speed(mon)
    assert speed == mon.stats["spe"]


def test_シェルアーマー_かたやぶりで無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="シェルアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is True


def test_シェルアーマー_急所に当たらない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="シェルアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is False


def test_しぜんかいふく_とんぼがえりで交代しても状態異常回復():
    """しぜんかいふく: 使うと交代する技（とんぼがえり）で引っ込んだときも回復する。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="しぜんかいふく", move_names=["とんぼがえり"]),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
        ailment0=("どく", None),
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.ailment.is_active
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)
    assert not mon.ailment.is_active


def test_しぜんかいふく_交代時に状態異常回復():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しぜんかいふく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
    )
    mon = battle.actives[0]
    assert mon.ailment.is_active
    t.run_switch(battle, 0, 1)
    assert not mon.ailment.is_active


def test_しぜんかいふく_強制交代させられても状態異常回復():
    """しぜんかいふく: ドラゴンテール等で強制交代させられたときも回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[
            Pokemon("ピカチュウ", ability_name="しぜんかいふく"),
            Pokemon("ピカチュウ"),
        ],
        ailment1=("どく", None),
        accuracy=100,
    )
    mon = battle.actives[1]
    assert mon.ailment.is_active
    t.run_move(battle, 0)
    assert not mon.ailment.is_active


def test_しめりけ_かたやぶりで爆発技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じばく"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


def test_しめりけ_じばくを失敗させる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じばく"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_しめりけ_爆発ラベルなし技は通す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


def test_しめりけ_自分の爆発技も失敗させる():
    battle = t.start_battle(
        team0=[Pokemon("ニョロモ", ability_name="しめりけ", move_names=["じばく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_しゅうかく_50パーセントの確率で発動する():
    """しゅうかく: 通常時はターン終了時に50%の確率で消費したきのみを復活させる。"""
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)
    assert mon.last_lost_item_name == "オボンのみ"

    t.fix_random(battle, 0.0)
    t.end_turn(battle)
    assert mon.has_item("オボンのみ")


def test_しゅうかく_アイテムを持っている場合は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)
    assert mon.last_lost_item_name == "オボンのみ"
    battle.item_manager.gain_item(mon, "たべのこし")

    t.fix_random(battle, 0.0)
    t.end_turn(battle)
    assert mon.has_item("たべのこし")


def test_しゅうかく_エアロック下では晴れでも50パーセントになる():
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン", ability_name="エアロック")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)

    t.fix_random(battle, 0.99)
    t.end_turn(battle)
    assert not mon.has_item()


def test_しゅうかく_おおひでり中は必ず発動する():
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 5),
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)

    t.fix_random(battle, 0.99)
    t.end_turn(battle)
    assert mon.has_item("オボンのみ")


def test_しゅうかく_きのみを消費していない場合は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    assert mon.last_lost_item_name == ""

    t.fix_random(battle, 0.0)
    t.end_turn(battle)
    assert not mon.has_item()


def test_しゅうかく_きのみ以外の持ち物は復活しない():
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="たべのこし")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)
    assert mon.last_lost_item_name == "たべのこし"

    t.fix_random(battle, 0.0)
    t.end_turn(battle)
    assert not mon.has_item()


def test_しゅうかく_トリックで渡した持ち物は復活しない():
    """しゅうかく: すりかえ・トリック等で相手に渡った持ち物（場に存在したまま持ち主が
    変わるだけ）は消費とみなされないため復活しない。"""
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
    )
    mon = battle.actives[0]
    battle.item_manager.swap_items()
    assert mon.item.name == "たべのこし"
    assert mon.last_lost_item_name == ""

    battle.item_manager.remove_item(mon)  # たべのこしを消費扱いで手放す
    t.fix_random(battle, 0.0)
    t.end_turn(battle)
    # オボンのみは復活せず、最後に失ったたべのこしのみが復活候補になる（かつきのみでないため復活しない）
    assert not mon.has_item()


def test_しゅうかく_どろぼうで奪われた持ち物は復活しない():
    """しゅうかく: 相手に奪われた（場に存在したまま持ち主が変わる）持ち物は復活対象にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.take_item(mon)
    assert not mon.has_item()
    assert mon.last_lost_item_name == ""

    t.fix_random(battle, 0.0)
    t.end_turn(battle)
    assert not mon.has_item()


def test_しゅうかく_ノーてんき下では晴れでも50パーセントになる():
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン", ability_name="ノーてんき")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)

    t.fix_random(battle, 0.99)
    t.end_turn(battle)
    assert not mon.has_item()


def test_しゅうかく_控えにいる間は発動せず再度場に出ると発動する():
    """しゅうかく: きのみ消費後に交代しても記憶は保持され、再度場に出れば発動する。
    控えにいる間は発動しない。"""
    battle = t.start_battle(
        team0=[
            Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)
    assert mon.last_lost_item_name == "オボンのみ"

    t.run_switch(battle, 0, 1)
    t.fix_random(battle, 0.0)
    t.end_turn(battle)
    # 控えにいる間は発動しない
    assert not mon.has_item()

    t.run_switch(battle, 0, 0)
    assert battle.actives[0] is mon
    t.end_turn(battle)
    # 再度場に出ると記憶が保持されているため発動する
    assert mon.has_item("オボンのみ")


def test_しゅうかく_晴れが切れるターンは50パーセントになる():
    """しゅうかく: 天気カウントが0になり晴れが終了するターンは、しゅうかくの発動判定より
    先に天気が戻ってしまうため発動率は50%になる。"""
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 1),
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)

    t.fix_random(battle, 0.99)
    t.end_turn(battle)
    assert battle.weather.name == ""
    assert not mon.has_item()


def test_しゅうかく_晴れ中は確率判定に外れても必ず発動する():
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)

    t.fix_random(battle, 0.99)
    t.end_turn(battle)
    assert mon.has_item("オボンのみ")


def test_しゅうかく_消費後に別の持ち物を消費すると新しい方が復活する():
    """しゅうかく: きのみ消費後に別の持ち物を入手してそれも消費すると、
    しゅうかくの対象は新しく消費した持ち物に更新される。"""
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)
    assert mon.last_lost_item_name == "オボンのみ"

    battle.item_manager.gain_item(mon, "ラムのみ")
    battle.item_manager.remove_item(mon)
    assert mon.last_lost_item_name == "ラムのみ"

    t.fix_random(battle, 0.0)
    t.end_turn(battle)
    assert mon.has_item("ラムのみ")


def test_しゅうかく_確率判定に外れると発動しない():
    battle = t.start_battle(
        team0=[Pokemon("タマタマ", ability_name="しゅうかく", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.remove_item(mon)

    t.fix_random(battle, 0.99)
    t.end_turn(battle)
    assert not mon.has_item()


def test_しょうりのほし_一撃必殺技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しょうりのほし", move_names=["つのドリル"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 30


def test_しょうりのほし_命中率が1_1倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しょうりのほし", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン")],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 4506 // 4096


def test_しろいけむり_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しろいけむり")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == -1


def test_しろいけむり_能力低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しろいけむり")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = {k: v for k, v in stats.items() if v > 0}

    assert expected == battle.modify_stats(mon0, stats, source=mon1)


def test_しろいけむり_自己低下は防げない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しろいけむり")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, _ = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = stats

    assert expected == battle.modify_stats(mon0, stats, source=mon0)


def test_しんがん_いかくは無効化されない():
    """しんがん: きもったまと異なりいかくによる攻撃ランク低下は防がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しんがん")],
        team1=[Pokemon("ウインディ", ability_name="いかく")],
    )
    assert battle.actives[0].boosts["atk"] == -1


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("かわらわり", 8192),  # かくとう技 → はがねに2倍
        ("たいあたり", 2048),  # ノーマル技 → ゴーストに等倍
    ]
)
def test_しんがん_かくとう技がゴースト複合に抜群(move_name, expected_modifier):
    # かわらわり(かくとう) vs サーフゴー(はがね/ゴースト) → はがね×2倍
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しんがん", move_names=[move_name])],
        team1=[Pokemon("サーフゴー", ability_name="")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected_modifier


def test_しんがん_ゴーストタイプへのノーマル技が当たる():
    """しんがん: ノーマル技がゴーストタイプに等倍で当たる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しんがん", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    _, defender = battle.actives
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before, "ゴーストタイプにノーマル技が当たるはず"


def test_しんがん_相手の命中ランク低下を防ぐ():
    """しんがん: 相手による命中ランク低下を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しんがん")],
        team1=[Pokemon("カビゴン")],
    )
    attacker, foe = battle.actives
    # 相手からACCランクを下げようとする
    battle.modify_stats(attacker, {"accuracy": -2}, source=foe)
    # しんがん所持者のACCランクは変化しないはず
    assert attacker.boosts["accuracy"] == 0


def test_しんがん_相手の回避ランクを無視する():
    """しんがん: 相手の回避ランク上昇を命中計算で無視する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しんがん", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    _, defender = battle.actives
    defender.boosts["evasion"] = 6
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100


def test_シンクロ_こんらんは伝染しない():
    """シンクロ: 揮発性状態(こんらん等)は伝染しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="シンクロ")],
        team1=[Pokemon("カビゴン")],
    )
    sync_mon, foe = battle.actives
    # こんらん(揮発性)を付与
    battle.volatile_manager.apply(sync_mon, "こんらん", source=foe)
    assert "こんらん" in sync_mon.volatiles
    # 相手にはこんらんが伝染しないはず
    assert "こんらん" not in foe.volatiles


def test_シンクロ_技によるまひが相手に伝染する():
    """シンクロ: でんじはでまひにされた場合も相手にまひが伝染する（統合テスト）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="シンクロ")],
        team1=[Pokemon("コラッタ", move_names=["でんじは"])],
        accuracy=100,
    )
    sync_mon, attacker = battle.actives
    t.run_move(battle, 1)
    assert sync_mon.has_ailment("まひ")
    assert attacker.has_ailment("まひ")


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど"]
)
def test_シンクロ_状態異常が相手に伝染する(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="シンクロ")],
        team1=[Pokemon("カビゴン")],
    )
    sync_mon, foe = battle.actives
    # 相手からシンクロ所持者に状態異常を付与する
    battle.ailment_manager.apply(sync_mon, ailment_name, source=foe)
    assert sync_mon.has_ailment(ailment_name)
    assert foe.has_ailment(ailment_name)


def test_シンクロ_相手が既に状態異常のときは発動しない():
    """シンクロ: 相手が既に状態異常のときは状態異常を付与できず伝染しない。
    このとき「シンクロが発動した」という発動ログ（ABILITY_TRIGGERED）自体も
    出ないことを確認する（fuzzログ回帰）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="シンクロ")],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
    )
    sync_mon, foe = battle.actives
    battle.ailment_manager.apply(sync_mon, "どく", source=foe)
    assert sync_mon.has_ailment("どく")
    # 相手は既にまひ状態のため、どくは伝染しない
    assert foe.has_ailment("まひ")
    assert not foe.has_ailment("どく")
    triggered = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED
        and log.payload is not None
        and getattr(log.payload, "ability", None) == "シンクロ"
    ]
    assert triggered == []


def test_シンクロ_自発的な状態異常は伝染しない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="シンクロ")],
        team1=[Pokemon("カビゴン")],
    )
    sync_mon, foe = battle.actives
    # source=None（自傷）でどくを付与
    battle.ailment_manager.apply(sync_mon, "どく", source=None)
    assert sync_mon.has_ailment("どく")
    # 相手にはどくが伝染しないはず
    assert not foe.has_ailment("どく")


def test_じきゅうりょく_クリアスモッグでランクリセット後に発動する():
    """じきゅうりょく: クリアスモッグを受けた場合、ランクが+6→0にリセットされた後に
    じきゅうりょくが発動し、最終的に+1になる（.internal/spec/abilities/じきゅうりょく.md）。
    ぼうぎょが上限(+6)のままだとリセット前にじきゅうりょくが不発判定されてしまう
    順序バグの回帰テスト（fuzz_log seed=2717）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
        team1=[Pokemon("ベトベトン", move_names=["クリアスモッグ"])],
    )
    defender = battle.actives[0]
    defender.boosts["def"] = 6

    t.run_move(battle, 1)

    assert defender.boosts["def"] == 1


def test_じきゅうりょく_こらえるでHP1のまま耐えたときも発動する():
    """じきゅうりょく: こらえるでHP1のまま耐えた（実ダメージ0）ときも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert defender.hp == 1
    assert defender.boosts["def"] == 1


def test_じきゅうりょく_タイプ相性でダメージを無効化したときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", ability_name="じきゅうりょく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]

    t.run_move(battle, 1)

    assert defender.boosts["def"] == 0


def test_じきゅうりょく_ぼうぎょが最大ランクのときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.boosts["def"] = 6
    t.run_move(battle, 1)
    assert defender.boosts["def"] == 6


def test_じきゅうりょく_みがわりに阻まれたときは発動しない():
    """じきゅうりょく: みがわりに攻撃を防がれたとき（実ダメージ0）は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)

    t.run_move(battle, 1)

    assert defender.boosts["def"] == 0


def test_じきゅうりょく_被弾して瀕死になった場合はぼうぎょが上がらない():
    """じきゅうりょく: 被弾して瀕死になった場合、自分自身のランク変化は発動しない
    （へんしょく・ぎゃくじょう等の既存特性と同じ規約）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)
    assert defender.fainted is True
    assert defender.boosts["def"] == 0


@pytest.mark.parametrize(
    "move_name",
    ["たいあたり", "でんきショック"]
)
def test_じきゅうりょく_被弾でBが1段階上がる(move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["def"] == 1


def test_じきゅうりょく_連続攻撃技は1発ごとに発動する():
    """物理技の連続攻撃技を受けた場合、1発ごとにぼうぎょが1段階上がる。

    防御側をHP・防御ともに高いカビゴンにすることで、2発ヒットしてもひんしに
    ならないようにする（ひんしになる一撃ではじきゅうりょくが発動しない仕様のため、
    ちょうどひんしになるレアケースを踏むと発動回数がずれてflakyになる）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="じきゅうりょく")],
        team1=[Pokemon("ピカチュウ", move_names=["ダブルアタック"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["def"] == 2


def test_じゅくせい_おちゃかいで強制消費したきのみの回復量も2倍になる():
    """じゅくせい: おちゃかいで強制消費した相手のきのみの回復量も、相手自身がじゅくせいなら2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"])],
        team1=[Pokemon("カビゴン", ability_name="じゅくせい", item_name="オボンのみ")],
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp // 2 + defender.max_hp // 4 * 2
    assert not defender.item.is_berry()


def test_じゅくせい_オッカのみの被ダメージが4分の1になる():
    """じゅくせい: 17種の半減系きのみ(オッカのみ)は被ダメージが1/2ではなく1/4になる
    （1/2の補正を2回掛けるのではなく1回の乗算で1/4を算出する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["だいもんじ"])],
        team1=[Pokemon("フシギダネ", ability_name="じゅくせい", item_name="オッカのみ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 1024
    assert not battle.actives[1].has_item()


def test_じゅくせい_オボンのみの回復量が2倍になる():
    """じゅくせい: HP回復系きのみ(オボンのみ)の回復量が端数切り捨て後に2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じゅくせい", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + mon.max_hp // 4 * 2
    assert not mon.has_item()


def test_じゅくせい_オレンのみの回復量が2倍になる():
    """じゅくせい: 固定値回復系きのみ(オレンのみ)の回復量も2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じゅくせい", item_name="オレンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + 20
    assert not mon.has_item()


def test_じゅくせい_サンのみのきゅうしょランク上昇量は変化しない():
    """じゅくせい: サンのみによる急所ランク上昇は+2のままで確定急所にならない（対象外）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じゅくせい", item_name="サンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.get_volatile("きゅうしょアップ").count == 2
    assert not mon.has_item()


def test_じゅくせい_ジャポのみの反動ダメージが4分の1になる():
    """じゅくせい: ジャポのみ/レンブのみの反動ダメージは最大HPの1/8の2倍ではなく1/4になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="じゅくせい", item_name="ジャポのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 4
    assert not battle.actives[1].has_item()


def test_じゅくせい_タラプのみのランク上昇量が2倍になる():
    """じゅくせい: 被弾カテゴリ系ランク上昇きのみ(タラプのみ)の上昇量も2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", ability_name="じゅくせい", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == 2
    assert not foe.has_item()


def test_じゅくせい_なげつけるで受けたオボンのみの回復量も2倍になる():
    """じゅくせい: なげつけるで受けたオボンのみの回復量も、受け取った側がじゅくせいなら2倍になる。

    なげつける自体のダメージを0に固定し、きのみの効果による回復量のみを検証する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="オボンのみ", move_names=["なげつける"])],
        team1=[Pokemon("ピカチュウ", ability_name="じゅくせい")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.fix_damage(battle, 0)
    t.run_move(battle, 0)
    assert defender.hp == hp_before + defender.max_hp // 4 * 2


def test_じゅくせい_なげつけるで受けたリュガのみのランク上昇量も2倍になる():
    """じゅくせい: なげつけるで受けたリュガのみのランク上昇量も、受け取った側がじゅくせいなら2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="リュガのみ", move_names=["なげつける"])],
        team1=[Pokemon("ピカチュウ", ability_name="じゅくせい")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.boosts["def"] == 2


def test_じゅくせい_ナゾのみの回復量が2倍になる():
    """じゅくせい: ナゾのみの回復量も2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", ability_name="じゅくせい", item_name="ナゾのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    # 回復量が最大HPを超えて頭打ちにならないよう、ダメージ量を回復量より大きくする
    damage = foe.max_hp // 4 * 2 + 10
    t.fix_damage(battle, damage)
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp - damage + foe.max_hp // 4 * 2
    assert not foe.has_item()


def test_じゅくせい_ヒメリのみのPP回復量が20になる():
    """じゅくせい: ヒメリのみのPP回復量が2倍の20になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じゅくせい", item_name="ヒメリのみ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.moves[0].pp = 1
    t.run_move(battle, 0)
    assert mon.moves[0].pp == 20
    assert not mon.has_item()


def test_じゅくせい_ほおばるで消費したきのみの回復量も2倍になる():
    """じゅくせい: ほおばるで強制消費したきのみの回復量も2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じゅくせい", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp // 2 + attacker.max_hp // 4 * 2


def test_じゅくせい_ミクルのみの命中率補正は変化しない():
    """じゅくせい: ミクルのみによる命中補正は1.2倍のまま変わらない（対象外）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じゅくせい", item_name="ミクルのみ", move_names=["ハイドロポンプ"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 4915 // 4096
    assert not mon.has_item()


def test_じゅくせい_むしくいで奪ったきのみの回復量も2倍になる():
    """じゅくせい: むしくいで相手のきのみを奪って食べた場合、奪った側がじゅくせいなら回復量が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイロス", ability_name="じゅくせい", move_names=["むしくい"])],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + attacker.max_hp // 4 * 2
    assert not defender.has_item()


def test_じゅくせい_リュガのみのランク上昇量が2倍になる():
    """じゅくせい: HP1/4以下で発動するランク上昇系きのみ(リュガのみ)の上昇量が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じゅくせい", item_name="リュガのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["def"] == 2
    assert not mon.has_item()


def test_じょうききかん_Sランクがすでに最大なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうききかん")],
        team1=[Pokemon("カビゴン", move_names=["みずでっぽう"])],
    )
    defender = battle.actives[0]
    defender.boosts["spe"] = 6
    t.run_move(battle, 1)
    assert defender.boosts["spe"] == 6
    assert not defender.ability.revealed


def test_じょうききかん_バブルこうせんの追加効果の後に発動する():
    """じょうききかん: バブルこうせんの追加効果（S-1）の後にじょうききかん（S+6）が発動する。

    発動順が逆（じょうききかんが先）だと S は 5 で止まってしまうため、
    正しい順序（S-1 → S+6）なら 6 になることで発動順を検証する。
    """
    battle = t.start_battle(
        team0=[Pokemon("セキタンザン", ability_name="じょうききかん")],
        team1=[Pokemon("カビゴン", move_names=["バブルこうせん"])],
        accuracy=100,
        secondary_chance=1.0,
    )
    defender = battle.actives[0]
    battle.modify_stats(defender, {"spe": 1})
    t.run_move(battle, 1)
    assert defender.boosts["spe"] == 6


@pytest.mark.parametrize(
    "move_name, rank",
    [
        ("ひのこ", 6),
        ("みずでっぽう", 6),
        ("たいあたり", 0),
    ]
)
def test_じょうききかん_ほのおまたはみず技でSが6段階上がる(move_name: str, rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうききかん")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["spe"] == rank


def test_じょうききかん_まもるで防がれたときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうききかん")],
        team1=[Pokemon("カビゴン", move_names=["みずでっぽう"])],
        volatile0={"まもる": 1},
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["spe"] == 0
    assert not defender.ability.revealed


def test_じょうききかん_みがわり状態では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうききかん")],
        team1=[Pokemon("カビゴン", move_names=["みずでっぽう"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 1)
    assert defender.boosts["spe"] == 0
    assert not defender.ability.revealed


def test_じょうききかん_変化技では発動しない():
    """じょうききかん: みずびたし等、変化技を受けたときは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうききかん")],
        team1=[Pokemon("カビゴン", move_names=["みずびたし"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["spe"] == 0
    assert not defender.ability.revealed


def test_じょうききかん_被弾して瀕死になった場合はすばやさが上がらない():
    """じょうききかん: みず/ほのお技を受けて瀕死になった場合、自分自身のランク変化は
    発動しない（へんしょく・ぎゃくじょう等の既存特性と同じ規約）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうききかん")],
        team1=[Pokemon("カビゴン", move_names=["みずでっぽう"])],
    )
    defender = battle.actives[0]
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)
    assert defender.fainted is True
    assert defender.boosts["spe"] == 0


def test_じんばいったい_こくばじょうのすがたが相手を倒すととくこうが上がる():
    """じんばいったい: こくばじょうのすがた（くろのいななき相当）は攻撃技で相手を倒すと
    とくこうが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("バドレックス(こくば)", ability_name="じんばいったい", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.boosts["spa"] == 1
    assert attacker.boosts["atk"] == 0


def test_じんばいったい_はくばじょうのすがたが相手を倒すとこうげきが上がる():
    """じんばいったい: はくばじょうのすがた（しろのいななき相当）は攻撃技で相手を倒すと
    こうげきが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("バドレックス(はくば)", ability_name="じんばいったい", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.boosts["atk"] == 1
    assert attacker.boosts["spa"] == 0


def test_じんばいったい_相手をきんちょうかん状態にする():
    """じんばいったい: きんちょうかんと同様に相手のきのみ使用を禁止する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="じんばいったい")],
    )
    assert battle.actives[1].ability.revealed
    assert battle.query.is_nervous(battle.actives[0])


def test_じんばいったい_相手を倒せないと能力上昇しない():
    """じんばいったい: 攻撃技で相手を倒せなければ能力は上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("バドレックス(はくば)", ability_name="じんばいったい", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.fainted
    assert attacker.boosts["atk"] == 0


def test_すいすい_おおあめ中も素早さ2倍():
    """すいすい: おおあめ状態でもあめと同様に素早さが2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すいすい")],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおあめ", 99),
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] * 2


def test_すいほう_相手のほのお技を弱化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すいほう")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    t.run_move(battle, 1)
    assert 2048 == battle.damage_calculator.atk_modifier


def test_すいほう_自分のみず技を強化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すいほう", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_スキルリンク_2から5連続技が最大ヒット数になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スキルリンク", move_names=["タネマシンガン"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].hits_taken == 5


@pytest.mark.parametrize("move_name", ["トリプルキック", "トリプルアクセル", "ネズミざん"])
def test_スキルリンク_毎ヒット命中判定技は初回のみ判定(move_name):
    """スキルリンク: トリプルキック等の毎ヒット命中判定技を初回ヒットのみの判定にする。
    2発目以降は本来なら外れる状況を疑似的に発生させても、判定自体が行われず全ヒットする。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability_name="スキルリンク", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
    )
    t.fix_damage(battle, 1)
    # 2発目以降で呼ばれたら外れる想定の命中判定（呼ばれなければヒットし続ける）
    battle.move_executor._check_hit = lambda ctx: ctx.hit_index == 1
    foe = battle.actives[1]
    initial_hp = foe.max_hp
    move = t.run_move(battle, 0)
    assert foe.hp == initial_hp - move.max_hits


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("すてみタックル", 4915),  # 1.2倍
        ("かかとおとし", 4915),  # 1.2倍（失敗反動技もrecoilフラグの対象）
        ("とびげり", 4915),  # 1.2倍（失敗反動技もrecoilフラグの対象）
        ("とびひざげり", 4915),  # 1.2倍（失敗反動技もrecoilフラグの対象）
        ("サンダーダイブ", 4915),  # 1.2倍（失敗反動技もrecoilフラグの対象）
        ("たいあたり", 4096),  # 補正なし
    ]
)
def test_すてみ_反動技の威力が1_2倍になる(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すてみ", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


def test_スナイパー_急所時の最終ダメージを1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スナイパー", move_names=["トリックフラワー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True
    assert 6144 == battle.damage_calculator.damage_modifier


def test_すながくれ_一撃必殺技には命中率変化なし():
    """一撃必殺技の命中率は独自計算のため、すながくれの命中率補正は適用されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じわれ"])],
        team1=[Pokemon("ピカチュウ", ability_name="すながくれ")],
        weather=("すなあらし", 5),
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


@pytest.mark.parametrize(
    "move_name, expected",
    [
        ("いわなだれ", 5325),
        ("じならし", 5325),
        ("アイアンヘッド", 5325),
        ("でんきショック", 4096),],
)
def test_すなのちから_すなあらし中に岩地面鋼技の威力が1_3倍になる(move_name: str, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなのちから", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected


def test_すなのちから_すなあらし以外では威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなのちから", move_names=["いわなだれ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_すなはき_こらえるでHP1のまま耐えたときも発動する():
    """すなはき: こらえるでHP1のまま耐えた（実ダメージ0）ときも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert defender.hp == 1
    assert battle.weather.name == "すなあらし"
    assert battle.weather.count == 5


def test_すなはき_さらさらいわ所持で継続ターンが8になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき", item_name="さらさらいわ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.weather.name == "すなあらし"
    assert battle.weather.count == 8


def test_すなはき_すでにすなあらし中は変化なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        weather=("すなあらし", 3),
    )
    t.run_move(battle, 1)
    assert battle.weather.count == 3


def test_すなはき_タイプ相性でダメージを無効化したときは発動しない():
    """すなはき: 攻撃技のダメージを無効化（タイプ相性0倍）したときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.weather.name == ""


def test_すなはき_みがわりに阻まれたときは発動しない():
    """すなはき: みがわりに攻撃を防がれたとき（実ダメージ0）は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)

    t.run_move(battle, 1)

    assert battle.weather.name == ""


def test_すなはき_変化技を受けても発動しない():
    """すなはき: みずびたし等、変化技を受けたときは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["みずびたし"])],
    )
    t.run_move(battle, 1)
    assert battle.weather.name == ""


def test_すなはき_致命打でも発動する():
    """すなはき: 攻撃技でHPが0になったときも、特性を発動させてからひんしになる
    （seed=2225 fuzz_log 回帰テスト。.internal/spec/abilities/すなはき.md）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = 1
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert defender.fainted
    assert battle.weather.name == "すなあらし"
    assert battle.weather.count == 5


def test_すなはき_被弾ですなあらし発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.weather.name == "すなあらし"


def test_すりぬけ_しんぴのまもりを貫通してこんらんが入る():
    """すりぬけ: しんぴのまもり中でも相手にこんらんを与えられる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ")],
        side1={"しんぴのまもり": 5},
    )
    attacker, defender = battle.actives
    assert battle.volatile_manager.apply(defender, "こんらん", count=3, source=attacker)
    assert defender.has_volatile("こんらん")


def test_すりぬけ_しんぴのまもりを貫通して状態異常が入る():
    """すりぬけ: しんぴのまもり中でも相手に状態異常を与えられる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ")],
        side1={"しんぴのまもり": 5},
    )
    attacker, defender = battle.actives
    assert battle.ailment_manager.apply(defender, "どく", source=attacker)
    assert defender.ailment.name == "どく"


def test_すりぬけ_みがわりを無視する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みがわり": 1},
    )
    t.run_move(battle, 0)
    mon = battle.actives[1]
    assert mon.hp < mon.max_hp


@pytest.mark.parametrize(
    "wall_name, move_name, expected_modifier",
    [
        ("リフレクター", "たいあたり", 4096),
        ("ひかりのかべ", "でんきショック", 4096),
        ("オーロラベール", "たいあたり", 4096),
        ("オーロラベール", "でんきショック", 4096),
    ],
)
def test_すりぬけ_壁を無視する(wall_name: SideFieldName, move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        side1={wall_name: 5},
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.damage_modifier


def test_するどいめ_かたやぶりで命中率を下げられる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["accuracy"] == -1


def test_するどいめ_命中率低下を防ぐ():
    """するどいめ: 相手による命中率ランク低下を防ぐ。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ")],
        team1=[Pokemon("ピカチュウ", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].boosts["accuracy"] == 0


def test_するどいめ_相手の回避率ランクを無視する():
    """するどいめ: 攻撃時に相手の回避率ランク上昇を無視する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].boosts["evasion"] = 6
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_するどいめ_相手の回避率ランク低下も無視する():
    """するどいめ: 相手の回避率ランクが下がっていても命中率を上げない（第六世代以降の仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ", move_names=["ストーンエッジ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].boosts["evasion"] = -1
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_スロースタート_かがくへんかガス解除後はカウントがリセットされる():
    """スロースタート: かがくへんかガスで無効化されている間に消費したカウントは、
    解除後にリセットされる（消費分は引き継がれない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スロースタート", move_names=["たいあたり"])],
        team1=[Pokemon("ハガネール", move_names=["たいあたり"])],
    )
    # ダメージを固定し、かがくへんかガス解除の時点でピカチュウが瀕死にならない
    # ようにする（瀕死個体はON_ABILITY_ENABLEDがスキップされ本来検証したい
    # カウントリセットが発動しなくなるため）
    t.fix_damage(battle, 1)
    mon = battle.actives[0]
    battle.step()
    battle.step()
    assert mon.ability.count == 2

    battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    battle.step()
    battle.step()
    assert mon.ability.count == 2

    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert mon.ability.count == 0
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] // 2


def test_スロースタート_特性を変えるわざで得た場合そのターンからカウントを開始する():
    """スロースタート: なりきり等で新たにスロースタートを得た場合、その瞬間から
    カウントが始まる（発動時のアナウンスが再度行われる）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いかく")],
        team1=[Pokemon("ハガネール")],
    )
    mon = battle.actives[0]
    battle.change_ability(mon, "スロースタート")
    assert mon.ability.count == 0
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] // 2


def test_スロースタート_特攻には補正がかからない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スロースタート", move_names=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_スロースタート_登場5ターン未満はすばやさが半分になる():
    """スロースタート: 場に出てから5ターンの間、実効すばやさが半分になる。

    5ターン目終了時点でピカチュウ・ハガネールとも生存し、決着が付かず
    ターン終了時のカウント処理（ON_TURN_END）が正常に行われることを
    確認するため、相手はダメージを与えない技（なきごえ）を使う。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スロースタート", move_names=["たいあたり"])],
        team1=[Pokemon("ハガネール", move_names=["なきごえ"])],
    )
    mon = battle.actives[0]
    base_speed = mon.stats["spe"]

    for _ in range(5):
        assert battle.speed_calculator.calc_effective_speed(mon) == base_speed // 2
        battle.step()

    assert battle.speed_calculator.calc_effective_speed(mon) == base_speed


def test_スロースタート_登場5ターン未満は攻撃補正0_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スロースタート", move_names=["たいあたり"])],
        team1=[Pokemon("ハガネール")],
    )
    assert battle.actives[0].ability.revealed

    for _ in range(5):
        battle.step()
        assert 2048 == battle.damage_calculator.atk_modifier

    battle.step()
    assert 4096 == battle.damage_calculator.atk_modifier


def test_スワームチェンジ_ジガルデ以外はHP1_2以下でもフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スワームチェンジ")],
        team1=[Pokemon("コラッタ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "ピカチュウ"


def test_スワームチェンジ_ターン終了時にHP1_2以下ならフォルムチェンジ():
    battle = t.start_battle(
        team0=[Pokemon("ジガルデ(10%)", ability_name="スワームチェンジ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    damage = mon.max_hp // 2 + 1
    mon.hp = mon.max_hp - damage
    t.end_turn(battle)

    assert mon.name == "ジガルデ(パーフェクト)"
    assert mon.hp == mon.max_hp - damage


def test_スワームチェンジ_ターン終了時にHP1_2超ならフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ジガルデ(10%)", ability_name="スワームチェンジ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.name == "ジガルデ(10%)"


def test_スワームチェンジ_パーフェクトフォルムでひんしになるとフォルムと最大HPが元に戻る():
    battle = t.start_battle(
        team0=[Pokemon("ジガルデ(50%)", ability_name="スワームチェンジ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    damage = mon.max_hp // 2 + 1
    mon.hp = mon.max_hp - damage
    t.end_turn(battle)
    assert mon.name == "ジガルデ(パーフェクト)"

    battle.faint(mon)

    assert mon.name == "ジガルデ(50%)"
    assert mon.hp == 0


def test_スワームチェンジ_ひんしから復活すると再度フォルムチェンジできる():
    battle = t.start_battle(
        team0=[
            Pokemon("ジガルデ(10%)", ability_name="スワームチェンジ"),
            Pokemon("ピカチュウ", move_names=["さいきのいのり"]),
        ],
        team1=[Pokemon("コラッタ")],
    )
    zygarde = battle.player_states[battle.players[0]].team[0]
    damage = zygarde.max_hp // 2 + 1
    zygarde.hp = zygarde.max_hp - damage
    t.end_turn(battle)
    assert zygarde.name == "ジガルデ(パーフェクト)"

    battle.faint(zygarde)
    assert zygarde.name == "ジガルデ(10%)"

    # ひんしになったジガルデをベンチへ、ピカチュウを場に出す
    t.run_switch(battle, 0, 1)
    t.run_move(battle, 0)
    assert zygarde.alive
    assert zygarde.hp == zygarde.max_hp // 2

    # 復活したジガルデを場に戻し、HP1/2以下のままターンを終えると再度発動する
    t.run_switch(battle, 0, 0)
    t.end_turn(battle)
    assert zygarde.name == "ジガルデ(パーフェクト)"


def test_せいぎのこころ_A最大のときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        team1=[Pokemon("カビゴン", move_names=["かみつく"])],
    )
    defender = battle.actives[0]
    defender.boosts["atk"] = 6
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 6


def test_せいぎのこころ_あくタイプの変化技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        team1=[Pokemon("カビゴン", move_names=["ちょうはつ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == 0


@pytest.mark.parametrize(
    "move_name, rank",
    [
        ("かみつく", 1),
        ("たいあたり", 0),
    ]
)
def test_せいぎのこころ_あく技を受けるとA上昇(move_name: str, rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == rank


def test_せいぎのこころ_まもるで防がれたときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        team1=[Pokemon("カビゴン", move_names=["かみつく"])],
        volatile0={"まもる": 1},
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 0
    assert not defender.ability.revealed


def test_せいぎのこころ_みがわり状態では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        team1=[Pokemon("カビゴン", move_names=["かみつく"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 0
    assert not defender.ability.revealed


def test_せいぎのこころ_被弾して瀕死になった場合はこうげきが上がらない():
    """せいぎのこころ: あく技を受けて瀕死になった場合、自分自身のランク変化は発動しない
    （へんしょく・ぎゃくじょう等の既存特性と同じ規約）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        team1=[Pokemon("カビゴン", move_names=["かみつく"])],
    )
    defender = battle.actives[0]
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)
    assert defender.fainted is True
    assert defender.boosts["atk"] == 0


def test_せいぎのこころ_連続技はヒットごとに発動する():
    battle = t.start_battle(
        team0=[
            Pokemon("ガブリアス", move_names=["ふくろだたき"]),
            Pokemon("ピカチュウ"),
            Pokemon("カビゴン"),
        ],
        team1=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 選出3体とも健康なので3ヒットし、そのたびにAが1段階ずつ上がる
    assert battle.actives[1].boosts["atk"] == 3


def test_せいしんりょく_いかくを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        team1=[Pokemon("ウインディ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 0
    assert mon.ability.revealed


def test_せいしんりょく_おうじゃのしるしのひるみを防ぐ():
    """せいしんりょく: おうじゃのしるし由来のひるみも防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="おうじゃのしるし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_せいしんりょく_かたやぶりの技によるひるみは防げない():
    """せいしんりょく: 特性かたやぶりの効果が発動した技によるひるみは防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["アイアンヘッド"])],
        team1=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_せいしんりょく_ひるみを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert not battle.volatile_manager.apply(battle.actives[0], "ひるみ", count=1)


def test_せいでんき_ひんしになっても発動する():
    """せいでんき: 直接攻撃を受けて自身がひんしになったときも攻撃者をまひ状態にする
    （.internal/spec/abilities/せいでんき.md「攻撃技でひんしになったときも発動する」）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = 1
    t.fix_random(battle, 0.0)
    t.run_move(battle, 1)
    assert defender.fainted
    assert battle.actives[1].has_ailment("まひ")


def test_ぜったいねむり_どくどくだまでも状態異常にならない():
    """ぜったいねむり: どくどくだまを持たせてもターン終了時にもうどくが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ネッコアラ", ability_name="ぜったいねむり", item_name="どくどくだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name == "ゆめうつつ"


def test_ぜったいねむり_ねごとが成功する():
    """ぜったいねむり: ゆめうつつ状態でもねごとが成功する（ねむり状態でなくても失敗しない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ネッコアラ", ability_name="ぜったいねむり", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    # ねごとで自動選択された技（たいあたり）が実行されダメージが発生する
    assert defender.hp < hp_before


def test_ぜったいねむり_ミストフィールド下でも登場時にゆめうつつ状態になる():
    """ぜったいねむり: ミストフィールド展開中でもゆめうつつは無効化されずに付与される。

    ミストフィールドは通常の状態異常（どく・やけど・こおり・ねむり・まひ・もうどく）の
    付与を無効化するが、ゆめうつつは無効化不能な特殊な状態異常のため対象外
    （.internal/spec/fields/ミストフィールド.md, .internal/spec/abilities/ぜったいねむり.md）。
    ゆめうつつの付与自体がミストフィールドにブロックされて失敗すると、状態異常スロットが
    空のまま残り、後から別の状態異常が誤って重複付与されてしまう（fuzz_log seed=1504で確認）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ネッコアラ", ability_name="ぜったいねむり")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", 99),
    )
    mon = battle.actives[0]
    assert mon.ailment.name == "ゆめうつつ"
    # ゆめうつつでスロットが埋まっているため、他の状態異常は重複付与されない
    assert not battle.ailment_manager.apply(mon, "やけど")
    assert mon.ailment.name == "ゆめうつつ"


def test_ぜったいねむり_ゆめうつつは解除されない():
    """ぜったいねむり: ゆめうつつは回復不能（uncurable）のため、状態異常回復手段でも解除できない。"""
    battle = t.start_battle(
        team0=[Pokemon("ネッコアラ", ability_name="ぜったいねむり")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.remove(mon)
    assert mon.ailment.name == "ゆめうつつ"


def test_ぜったいねむり_交代して戻ってもゆめうつつを維持する():
    """ぜったいねむり: 一度交代して戻ってきても、再度ゆめうつつになる。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ネッコアラ", ability_name="ぜったいねむり"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    assert mon.ailment.name == "ゆめうつつ"
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    mon = battle.actives[0]
    assert mon.ailment.name == "ゆめうつつ"


def test_ぜったいねむり_他の状態異常を新たに受け付けない():
    """ぜったいねむり: ゆめうつつ状態のため、どくなど他の状態異常を新たに付与できない。"""
    battle = t.start_battle(
        team0=[Pokemon("ネッコアラ", ability_name="ぜったいねむり")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.name == "ゆめうつつ"


def test_ぜったいねむり_登場時にゆめうつつ状態になる():
    """ぜったいねむり: 場に出ると状態異常『ゆめうつつ』になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ネッコアラ", ability_name="ぜったいねむり")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ailment.name == "ゆめうつつ"
    assert mon.ailment.is_sleep


def test_ゼロフォーミング_かがくへんかガス中にテラスタルすると発動しない():
    """ゼロフォーミング: かがくへんかガス発動中にテラスタルすると発動機会を失い、ガス解除後も発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゼロフォーミング")],
        team1=[Pokemon("カビゴン", ability_name="かがくへんかガス")],
        weather=("あめ", 5),
        terrain=("グラスフィールド", 5),
    )
    mon = battle.actives[0]
    t.reserve_command(battle, Command.TERASTAL_0)
    battle.step()
    # かがくへんかガスにより特性が無効化されているため天候・フィールドは消えない
    assert battle.weather.name == "あめ"
    assert battle.terrain.name == "グラスフィールド"

    # ガスを解除しても、テラスタルの発動機会は失われたままで発動しない
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert battle.weather.name == "あめ"
    assert battle.terrain.name == "グラスフィールド"


def test_ゼロフォーミング_テラスタル後は天候とフィールドを新たに発生させられる():
    """ゼロフォーミング: 発動は1回のみで、テラスタル後はこのポケモンが場にいる間でも天候・フィールドを新たに発生させられる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゼロフォーミング", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン"), Pokemon("イワンコ", ability_name="エレキメイカー")],
        weather=("すなあらし", 5),
        terrain=("グラスフィールド", 5),
    )
    t.reserve_command(battle, Command.TERASTAL_0)
    battle.step()
    # テラスタルで既存の天候は消去されるが、同ターン中のあまごいで新たに天候が発生する
    assert battle.weather.name == "あめ"

    # ゼロフォーミングのポケモンが場に残っていても、新たにフィールドを発生させられる
    t.run_switch(battle, 1, 1)
    assert battle.terrain.name == "エレキフィールド"


def test_ゼロフォーミング_テラスタル時に天候とフィールドが消える():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゼロフォーミング")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
        terrain=("グラスフィールド", 5),
    )
    t.reserve_command(battle, Command.TERASTAL_0)
    battle.step()
    assert battle.weather.name == "", "ゼロフォーミングで天候が消去される"
    assert battle.terrain.name == "", "ゼロフォーミングでフィールドが消去される"


def test_ゼロフォーミング_テラスタル済みなら交代して戻っても再発動しない():
    """ゼロフォーミング: テラスタル済みの状態で引っ込めて再度場に出しても発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゼロフォーミング"), Pokemon("カイリキー")],
        team1=[Pokemon("カビゴン", move_names=["あまごい"])],
    )
    t.reserve_command(battle, Command.TERASTAL_0)
    battle.step()
    assert battle.actives[0].is_terastallized

    # 交代後に相手が天候を発生させる
    t.run_switch(battle, 0, 1)
    t.run_move(battle, 1)
    assert battle.weather.name == "あめ"

    # ゼロフォーミングのポケモンが再度場に出ても発動しない
    t.run_switch(battle, 0, 0)
    assert battle.weather.name == "あめ"


def test_そうしょく_くさタイプの変化技も無効化してこうげきが上がる():
    """そうしょく: やどりぎのタネのようなくさタイプの変化技を受けても無効化し、こうげきが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="そうしょく")],
        team1=[Pokemon("フシギダネ", move_names=["やどりぎのタネ"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 1
    assert not defender.has_volatile("やどりぎのタネ")


def test_そうしょく_くさタイプの粉技を受けたときタイプ無効化より優先して発動する():
    """そうしょく: くさタイプを持つポケモンが粉技を受けた場合、
    くさタイプによる無効化よりそうしょくの効果が優先されるため、こうげきが上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="そうしょく")],
        team1=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 1
    assert defender.ailment.name == ""


def test_そうしょく_まもるで防がれたときは発動しない():
    """そうしょく: まもる状態でくさ技を防いだときは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="そうしょく")],
        team1=[Pokemon("コラッタ", move_names=["このは"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "まもる", count=1)
    t.run_move(battle, 1)
    assert mon.boosts["atk"] == 0


def test_そうしょく_みがわり状態の攻撃技でも発動する():
    """そうしょく: みがわり状態でくさ技（攻撃技）を受けても発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="そうしょく")],
        team1=[Pokemon("コラッタ", move_names=["このは"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "みがわり", count=mon.max_hp // 4)
    t.run_move(battle, 1)
    assert mon.boosts["atk"] == 1


def test_そうしょく_場を対象とするくさ技には発動しない():
    """そうしょく: グラスフィールドなど場を対象とするくさ技には発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["グラスフィールド"])],
        team1=[Pokemon("コラッタ", ability_name="そうしょく")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.terrain.name == "グラスフィールド"
    assert defender.boosts["atk"] == 0


def test_そうしょく_自分自身を対象とするくさ技には発動しない():
    """そうしょく: ねをはるなど自分自身を対象とするくさ技には発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="そうしょく", move_names=["ねをはる"])],
        team1=[Pokemon("コラッタ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.boosts["atk"] == 0
    assert mon.has_volatile("ねをはる")


def test_そうしょく_連続技を受けてもこうげき上昇は1回のみ():
    """そうしょく: くさタイプの連続攻撃技を受けても無効化し、こうげき上昇は1回のみ。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="そうしょく")],
        team1=[Pokemon("コラッタ", move_names=["タネマシンガン"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 1


def test_そうだいしょう_ひんしの味方がいないとき補正なし():
    """そうだいしょう: ひんしの味方がいないときは威力補正がかからない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ"), Pokemon("カビゴン", ability_name="そうだいしょう", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
    )
    t.run_switch(battle, 0, 2)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_そうだいしょう_入場後に味方がひんしになっても補正率は変わらない():
    """そうだいしょう: 威力補正率は特性発動時点で確定し、以後味方がひんしになっても変わらない。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ"), Pokemon("ライチュウ"),
            Pokemon("カビゴン", ability_name="そうだいしょう", move_names=["たいあたり"]),
        ],
        team1=[Pokemon("フシギダネ")],
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    battle.modify_hp(bench[0], v=-bench[0].max_hp)  # ライチュウをひんしにする

    mon = t.run_switch(battle, 0, 2)
    assert mon.ability.revealed

    # そうだいしょう発動後にピカチュウがひんしになっても補正率は上昇しない
    battle.modify_hp(battle.player_states[player0].bench[0], v=-battle.player_states[player0].bench[0].max_hp)

    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096 * 11 // 10


def test_そうだいしょう_味方1体ひんしで補正率1_1():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ"), Pokemon("カビゴン", ability_name="そうだいしょう", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    battle.modify_hp(bench[0], v=-bench[0].max_hp)  # ライチュウをひんしにする

    mon = t.run_switch(battle, 0, 2)
    assert mon.ability.revealed

    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096 * 11 // 10


def test_そうだいしょう_味方5体ひんしで補正率上限1_5():
    """そうだいしょう: ひんし味方が5体以上でも威力補正率は上限の1.5倍(+50%)まで。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ"),
            Pokemon("ライチュウ"), Pokemon("コラッタ"), Pokemon("ラッタ"),
            Pokemon("ポッポ"), Pokemon("ピジョン"),
            Pokemon("カビゴン", ability_name="そうだいしょう", move_names=["たいあたり"]),
        ],
        team1=[Pokemon("フシギダネ")],
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    for mon in bench[:5]:
        battle.modify_hp(mon, v=-mon.max_hp)

    mon = t.run_switch(battle, 0, 6)
    assert mon.ability.revealed

    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096 * 15 // 10


def test_そうだいしょう_復活しても延べひんし回数は減らない():
    """そうだいしょう: 一度ひんしになった味方が復活しても、延べひんし回数は減らない。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ"), Pokemon("ライチュウ"),
            Pokemon("カビゴン", ability_name="そうだいしょう", move_names=["たいあたり"]),
        ],
        team1=[Pokemon("フシギダネ")],
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    ally = bench[0]
    battle.modify_hp(ally, v=-ally.max_hp)  # ライチュウをひんしにする
    assert ally.fainted

    battle.modify_hp(ally, v=ally.max_hp // 2)  # ライチュウを復活させる
    assert not ally.fainted

    mon = t.run_switch(battle, 0, 2)
    assert mon.ability.revealed

    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096 * 11 // 10


def test_ソウルハート_KO時にCが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ソウルハート", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.fainted
    assert attacker.boosts["spa"] == 1
    assert attacker.ability.revealed


def test_ソウルハート_攻撃技によるKOでランクがすでに最大のときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ソウルハート", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    attacker.boosts["spa"] = 6
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.fainted
    assert attacker.boosts["spa"] == 6


def test_ソウルハート_相手が状態異常のダメージでひんしになってもCが1段階上がる():
    """攻撃技によるKOではないため、ON_HP_CHANGED(target:foe) 経由で発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ソウルハート")],
        team1=[Pokemon("コイキング")],
    )
    attacker, defender = battle.actives
    t.apply_ailment(battle, player_idx=1, ailment_name="どく")
    defender.hp = 1
    t.end_turn(battle)

    assert defender.fainted
    assert attacker.boosts["spa"] == 1
    assert attacker.ability.revealed


def test_ソウルハート_相手が状態異常のダメージでひんしになってもランクがすでに最大のときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ソウルハート")],
        team1=[Pokemon("コイキング")],
    )
    attacker, defender = battle.actives
    attacker.boosts["spa"] = 6
    t.apply_ailment(battle, player_idx=1, ailment_name="どく")
    defender.hp = 1
    t.end_turn(battle)

    assert defender.fainted
    assert attacker.boosts["spa"] == 6


def test_ソウルハート_相手が自滅技でひんしになってもCが1段階上がる():
    """だいばくはつ等の自己HP消費（reason="self_cost"）による自滅も、攻撃技による
    KOではないため ON_HP_CHANGED(target:foe) 経由で発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ソウルハート")],
        team1=[Pokemon("カビゴン", move_names=["だいばくはつ"])],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 1)

    assert defender.fainted
    assert attacker.boosts["spa"] == 1
    assert attacker.ability.revealed


def test_ソウルハート_自分自身がひんしになってもCは上がらない():
    """一次情報では発動条件が「自分以外が倒れる」に分類されており、自分自身が
    ひんしになったことは対象外。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ソウルハート")],
        team1=[Pokemon("カビゴン", move_names=["じしん"])],
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    t.run_move(battle, 1)

    assert attacker.fainted
    assert attacker.boosts["spa"] == 0


def test_てつのトゲ_ひんしになっても発動する():
    """てつのトゲ: さめはだと同じ効果を持つため、自身が直接攻撃でひんしになった
    ときも反撃ダメージが発動する（fuzz_log横断監査。.internal/spec/abilities/てつのトゲ.md
    「さめはだ#特性の仕様を参照」）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てつのトゲ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    battle.modify_hp(defender, v=-(defender.max_hp - 1))
    t.run_move(battle, 1)
    assert defender.fainted
    assert attacker.hp == attacker.max_hp - int(attacker.max_hp * (1 / 8))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
