"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import MEMORY_TO_TYPE
from jpoke.enums import Command
from jpoke.types import Stat, WeatherName, TerrainName

from .. import test_utils as t

AR_SYSTEM_MEMORY_CASES = [
    (memory_item_name, expected_type)
    for memory_item_name, expected_type in MEMORY_TO_TYPE.items()
    if memory_item_name in ITEMS
]

ability_weather_defaultcount = [
    ("あめふらし", "あめ", 5),
    ("ひでり", "はれ", 5),
    ("すなおこし", "すなあらし", 5),
    ("ゆきふらし", "ゆき", 5),
    ("おわりのだいち", "おおひでり", 1),
    ("はじまりのうみ", "おおあめ", 1),
    ("デルタストリーム", "らんきりゅう", 1),
]
abilities = [x[0] for x in ability_weather_defaultcount]
weathers = [x[1] for x in ability_weather_defaultcount]
normal_weathers = weathers[:4]
strong_weathers = weathers[4:]


@pytest.mark.parametrize(
    "memory_item_name, expected_type",
    AR_SYSTEM_MEMORY_CASES,
)
def test_ARシステム_メモリで対応タイプになる(memory_item_name: str, expected_type: str):
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム", item_name=memory_item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == expected_type
    assert mon.ability.revealed is False  # ARシステムは開示されない


def test_ARシステム_メモリなしでタイプ変更なし():
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None
    assert mon.ability.revealed is False  # メモリなしは不発なので False


def test_アイスフェイス_エアロック中はゆき変化でフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
        team1=[Pokemon("ラティアス", ability_name="エアロック")],
    )
    mon = battle.actives[0]
    battle.weather_manager.apply("ゆき", 5)
    assert mon.name == "コオリッポ(ナイス)"


def test_アイスフェイス_かたやぶりで物理技のダメージを防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("コオリッポ(アイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.name == "コオリッポ(アイス)"


def test_アイスフェイス_かたやぶりのゆきげしきでは戻れない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ゆきげしき"])],
        team1=[Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.raw_weather.name == "ゆき"
    assert defender.name == "コオリッポ(ナイス)"


def test_アイスフェイス_ナイスフェイスでは物理技を防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_アイスフェイス_ゆきが発生するとアイスフェイスに戻る():
    battle = t.start_battle(
        team0=[Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.weather_manager.apply("ゆき", 5)
    assert battle.actives[0].name == "コオリッポ(アイス)"


def test_アイスフェイス_ゆき状態の場に登場するとアイスフェイスに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
        team1=[Pokemon("ピカチュウ")],
        weather=("ゆき", 5),
    )
    mon = battle.player_states[battle.players[0]].team[1]
    assert mon.name == "コオリッポ(ナイス)"  # ベンチではまだナイスフェイス
    t.run_switch(battle, 0, 1)
    assert battle.actives[0].name == "コオリッポ(アイス)"


def test_アイスフェイス_物理技を無効にしてフォルムチェンジ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("コオリッポ(アイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp
    assert defender.name == "コオリッポ(ナイス)"


def test_アイスフェイス_特殊技のダメージを防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("コオリッポ(アイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.name == "コオリッポ(アイス)"


def test_あくしゅう_攻撃時10パーセントでひるみを付与する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あくしゅう", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    t.fix_damage(battle, 1)
    battle.random.random = lambda: 0.09
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_あくしゅう_確率外ではひるみを付与しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あくしゅう", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    t.fix_damage(battle, 1)
    battle.random.random = lambda: 0.11
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_あとだし_トリックルームでも後攻():
    """あとだし: トリックルーム状態でも最後に行動する（素早さ逆転の影響を受けない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし")],
        team1=[Pokemon("ピカチュウ")],
        field={"トリックルーム": 5},
    )
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]


def test_あとだし_同優先度で最後に行動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし")],
        team1=[Pokemon("ピカチュウ")],
    )
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]


def test_あとだし_技優先度が優先される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]


def test_アナライズ_先攻なら威力据え置き():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("コイル")],
    )
    battle.step()
    assert 4096 == battle.damage_calculator.power_modifier


def test_アナライズ_後攻なら威力上昇():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.step()
    assert 5325 == battle.damage_calculator.power_modifier


def test_あまのじゃく_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["atk"] == -1


def test_あまのじゃく_能力変化の符号反転():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"atk": 1, "def": -2, "spa": 3, "spd": -4, "spe": 1, "accuracy": -2, "evasion": 3}
    battle.modify_stats(target, stats, source=source)
    for stat, change in stats.items():
        assert target.rank[stat] == max(-6, min(6, -change))


def test_あめうけざら_あめ以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="あめうけざら")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    t.end_turn(battle)
    assert mon.hp == before


def test_いかく_登場時に相手攻撃1段階ダウン():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["atk"] == -1


def test_いかりのこうら_HP半分超から半分以下でACSアップBDダウン():
    """いかりのこうら: HPが半分を下回ったとき A/C/S↑1、B/D↓1。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 2
    t.fix_damage(battle, 3)  # 半分以上削る
    t.run_move(battle, 1)

    assert defender.hp <= defender.max_hp // 2
    assert defender.rank["atk"] == 1
    assert defender.rank["spa"] == 1
    assert defender.rank["spe"] == 1
    assert defender.rank["def"] == -1
    assert defender.rank["spd"] == -1


def test_いかりのこうら_ひんし時は発動しない():
    """いかりのこうら: 瀕死になった場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)

    assert defender.fainted
    assert defender.rank["atk"] == 0


def test_いかりのこうら_被弾前HPが半分以下なら発動しない():
    """いかりのこうら: すでにHP半分以下のときは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2
    t.fix_damage(battle, 1)
    t.run_move(battle, 1)

    assert defender.rank["atk"] == 0


def test_いかりのつぼ_A最大のとき急所被弾でも変化なし():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert battle.move_executor.critical is True
    assert defender.rank["atk"] == 6


def test_いかりのつぼ_急所でない被弾は発動しない():
    """いかりのつぼ: 急所でない被弾ではこうげきランクが変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    battle.random.random = lambda: 1.0  # 急所が発生しない乱数
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.rank["atk"] == 0


def test_いかりのつぼ_急所被弾でこうげき最大():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert battle.move_executor.critical is True
    assert defender.rank["atk"] == 6


def test_いしあたま_わるあがきの反動ダメージは防げない():
    """いしあたま: わるあがきの反動は通常の反動技と異なる仕様のため無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["わるあがき"])],
        team1=[Pokemon("ヤドン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_いしあたま_反動技を使っても反動ダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["すてみタックル"])],
        team1=[Pokemon("ヤドン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_いたずらごころ_あくタイプ相手には変化技が無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["でんじは"])],
        team1=[Pokemon("ヘルガー")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    # あくタイプ相手には変化技が無効化されるため、まひが付与されない
    assert not defender.ailment.is_active
    assert battle.move_executor.move_applied is False


def test_いたずらごころ_変化技の優先度が1上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["でんじは"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    assert attacker.moves[0].priority == 0
    assert battle.speed_calculator.calc_move_priority(attacker, attacker.moves[0]) == 1


def test_いたずらごころ_自己対象の変化技はあくタイプ相手でも成功する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["かえんのまもり"])],
        team1=[Pokemon("ヘルガー")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    # 自己対象の変化技はあくタイプ相手でも成功するため、かえんのまもり状態になる
    assert battle.move_executor.move_applied is True
    assert attacker.has_volatile("かえんのまもり")


def test_いろめがね_いまひとつのダメージが2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いろめがね", move_names=["むしのていこう"])],
        team1=[Pokemon("ピジョン")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.damage_modifier


def test_うのミサイル_ウッウ以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うのミサイル", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ピカチュウ"


def test_うのミサイル_うのみのすがたで攻撃を受けると通常に戻りぼうぎょが下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ウッウ(うのみ)", ability_name="うのミサイル")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.name == "ウッウ"
    assert attacker.rank["def"] == -1
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 4


def test_うのミサイル_なみのりが命中するとHP半分以下でまるのみのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ウッウ", ability_name="うのミサイル", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.run_move(battle, 0)
    assert mon.name == "ウッウ(まるのみ)"


def test_うのミサイル_なみのりが命中するとHP半分超でうのみのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ウッウ", ability_name="うのミサイル", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ウッウ(うのみ)"


def test_うのミサイル_まるのみのすがたで攻撃を受けると通常に戻りまひになる():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ウッウ(まるのみ)", ability_name="うのミサイル")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.name == "ウッウ"
    assert attacker.has_ailment("まひ")


def test_うのミサイル_みがわりで防いだ場合は吐き出しが発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ウッウ(うのみ)", ability_name="うのミサイル")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    before_attacker_hp = attacker.hp
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    assert defender.name == "ウッウ(うのみ)"
    assert attacker.hp == before_attacker_hp


def test_うのミサイル_交代するとフォルムが通常のすがたに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ウッウ(うのみ)", ability_name="うのミサイル"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ウッウ(うのみ)"
    t.run_switch(battle, 0, 1)
    assert mon.name == "ウッウ"


def test_うるおいボイス_ノーマル音技をみずタイプに変換する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボイス", move_names=["ハイパーボイス"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "みず"


def test_うるおいボイス_非音技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボイス", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"


@pytest.mark.parametrize("weather_name, expected_recovered", [
    ("あめ", True),
    ("はれ", False),
])
def test_うるおいボディ_天候別に状態異常を回復する(weather_name: WeatherName, expected_recovered: bool):
    """うるおいボディ: あめ中は状態異常を回復し、はれ中は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボディ")],
        team1=[Pokemon("カビゴン")],
        weather=(weather_name, 5),
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert mon.ailment.is_active == (not expected_recovered)


def test_エアロック_すなあらしのターン終了ダメージが無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="エアロック")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


@pytest.mark.parametrize(
    "weather_name",
    weathers
)
def test_エアロック_天候と強天候を無効化する(weather_name: WeatherName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="エアロック")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 5),
    )
    assert battle.weather.name == ""


@pytest.mark.parametrize(
    "initial_terrain",
    [
        "グラスフィールド",
        "サイコフィールド",
        "ミストフィールド",
    ],
)
def test_エレキメイカー_別フィールドを上書きする(initial_terrain: TerrainName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="エレキメイカー")],
        team1=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 5),
    )
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


def test_えんかく_直接攻撃でさめはだが発動しない():
    """えんかく所持者が直接攻撃を使っても、相手のさめはだが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="えんかく", move_names=["たいあたり"])],
        team1=[Pokemon("ウインディ", ability_name="さめはだ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_えんかく_直接攻撃でわるいてぐせが発動しない():
    """えんかく所持者が直接攻撃を使っても、相手のわるいてぐせが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="えんかく", item_name="たべのこし",
                       move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_item()


def test_おうごんのからだ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_場が対象の技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にほんばれ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_攻撃技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied
    assert not battle.actives[1].ability.revealed


def test_おうごんのからだ_相手の変化技を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.move_applied
    assert battle.actives[1].ability.revealed is True


def test_おうごんのからだ_自分対象の変化技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied


def test_おみとおし_アイテムありの相手のアイテムが公開される():
    """おみとおし: 場に出たとき相手のアイテムが公開される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おみとおし")],
        team1=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    foe = battle.actives[1]
    assert foe.item.revealed
    assert battle.actives[0].ability.revealed


def test_おみとおし_アイテムなしの相手には発動しない():
    """おみとおし: 相手がアイテムを持っていなければ発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おみとおし")],
        team1=[Pokemon("ピカチュウ")],
    )
    foe = battle.actives[1]
    assert not foe.item.revealed


def test_おもかげやどし_オーガポン以外は発動しない():
    """おもかげやどし: オーガポン以外のポケモンには発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # どのランクも変化しない
    for stat in ("atk", "def", "spa", "spd", "spe"):
        assert mon.rank[stat] == 0


def test_おもかげやどし_テラスタル時に能力が上昇する():
    """おもかげやどし: テラスタル時にフォルムに対応する能力が1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # 登場時の上昇をリセット
    mon.rank["spe"] = 0
    # テラスタルコマンドを予約して step でテラスタルフェーズを実行する
    t.reserve_command(battle, Command.TERASTAL_0, Command.MOVE_0)
    battle.step()
    assert mon.terastallized
    assert mon.rank["spe"] == 1


@pytest.mark.parametrize(
    "form_name, expected_stat",
    [
        ("オーガポン(みどり)", "spe"),
        ("オーガポン(いど)", "spd"),
        ("オーガポン(かまど)", "atk"),
        ("オーガポン(いしずえ)", "def"),
    ],
)
def test_おもかげやどし_フォルムに対応した能力が1段上昇する(form_name: str, expected_stat: Stat):
    """おもかげやどし: フォルムに応じた能力が1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon(form_name, ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank[expected_stat] == 1


def test_おもかげやどし_交代して再登場すると再発動する():
    """おもかげやどし: 交代して再び場に出たときに再度能力が上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし"), Pokemon("コイル")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["spe"] == 1
    # 一度引っ込める（交代でランクはリセットされる）
    t.run_switch(battle, 0, 1)
    assert mon.rank["spe"] == 0  # 交代後はリセット
    # 再登場するとおもかげやどしが再発動して+1
    t.run_switch(battle, 0, 0)
    assert mon.rank["spe"] == 1


def test_おもかげやどし_特性再有効化時にも発動する():
    """おもかげやどし: かがくへんかガス解除後に特性が再有効化されると再発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    # かがくへんかガスにより特性が無効化されているので S は上昇していない
    assert mon.rank["spe"] == 0
    # かがくへんかガスの無効化を解除すると特性が再発動してS+1
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert mon.rank["spe"] == 1


def test_おやこあい_がむしゃらには適用しない():
    """おやこあい: がむしゃらはHP変動の有無に関わらずいかなる状況でも連続攻撃にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["がむしゃら"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = 30
    defender.hp = 100
    t.run_move(battle, 0)
    assert defender.hits_taken == 1
    assert defender.hp == 100 - (100 - 30)


def test_おやこあい_ころがるには適用しない():
    """おやこあい: ころがるは数ターン継続する強制行動技のため、連続攻撃にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", ability_name="おやこあい", move_names=["ころがる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hits_taken == 1
    assert attacker.volatiles["ころがる"].count == 1


def test_おやこあい_単発攻撃が2ヒットする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # ダメージ計算結果を固定
    t.fix_damage(battle, 40)
    t.run_move(battle, 0)
    attacker, defender = battle.actives
    assert defender.hits_taken == 2
    assert defender.hp == defender.max_hp - 40 - 10
    assert attacker.rank["spe"] == 2


def test_おやこあい_既存連続技には適用しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["すいりゅうれんだ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hits_taken == 3


def test_オーラブレイク_登場時に特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="オーラブレイク")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed is True


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("フェアリーオーラ", "ムーンフォース"),
        ("ダークオーラ", "あくのはどう"),
    ]
)
def test_オーラブレイク_相手の攻撃を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="オーラブレイク")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.power_modifier


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("フェアリーオーラ", "ムーンフォース"),
        ("ダークオーラ", "あくのはどう"),
    ]
)
def test_オーラブレイク_自分の攻撃を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", ability_name="オーラブレイク", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert 3072 == battle.damage_calculator.power_modifier


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
