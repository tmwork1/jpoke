"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.enums import Command, Interrupt
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


def test_さいせいりょく_交代で控えに戻ると回復する():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="さいせいりょく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
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


def test_サンパワー_物理技は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


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


def test_サンパワー_ノーてんき下では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー")],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
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
    assert attacker.rank["accuracy"] == 0


def test_しんがん_相手の回避ランクを無視する():
    """しんがん: 相手の回避ランク上昇を命中計算で無視する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しんがん", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    _, defender = battle.actives
    defender.rank["evasion"] = 6
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100


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
    assert battle.actives[0].rank["def"] == 1


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
    assert battle.actives[0].rank["spe"] == rank


def test_じんばいったい_相手をきんちょうかん状態にする():
    """じんばいったい: きんちょうかんと同様に相手のきのみ使用を禁止する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="じんばいったい")],
    )
    assert battle.actives[1].ability.revealed
    assert battle.query.is_nervous(battle.actives[0])


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


def test_すなはき_すでにすなあらし中は変化なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        weather=("すなあらし", 3),
    )
    t.run_move(battle, 1)
    assert battle.weather.count == 3


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
    assert battle.actives[0].rank["accuracy"] == -1


def test_するどいめ_命中率低下を防ぐ():
    """するどいめ: 相手による命中率ランク低下を防ぐ。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ")],
        team1=[Pokemon("ピカチュウ", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["accuracy"] == 0


def test_するどいめ_相手の回避率ランクを無視する():
    """するどいめ: 攻撃時に相手の回避率ランク上昇を無視する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].rank["evasion"] = 6
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_スロースタート_特攻には補正がかからない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スロースタート", move_names=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


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
    assert battle.actives[0].rank["atk"] == rank


def test_せいしんりょく_いかくを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        team1=[Pokemon("ウインディ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.rank["atk"] == 0
    assert mon.ability.revealed


def test_せいしんりょく_ひるみを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert not battle.volatile_manager.apply(battle.actives[0], "ひるみ", count=1)


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


def test_そうだいしょう_ひんしの味方がいないとき補正なし():
    """そうだいしょう: ひんしの味方がいないときは威力補正がかからない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ"), Pokemon("カビゴン", ability_name="そうだいしょう", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
    )
    t.run_switch(battle, 0, 2)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_そうだいしょう_味方1体ひんしで補正率1_1():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ"), Pokemon("カビゴン", ability_name="そうだいしょう", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    bench[0].hp = 0

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
    assert attacker.rank["spa"] == 1
    assert attacker.ability.revealed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
