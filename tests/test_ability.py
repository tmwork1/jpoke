"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle

import pytest

from jpoke import Pokemon
from jpoke.core import AttackContext, EventContext
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import MEMORY_TO_TYPE, PLATE_TO_TYPE
from jpoke.enums import Event, Interrupt, Command, LogCode
from jpoke.utils.type_defs import Type, Stat, AilmentName, VolatileName, Weather
from jpoke.model import Move

import test_utils as t

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

ability_terrain_pairs = [
    ("エレキメイカー", "エレキフィールド"),
    ("グラスメイカー", "グラスフィールド"),
    ("サイコメイカー", "サイコフィールド"),
    ("ミストメイカー", "ミストフィールド"),
]

SKIN_CASES = [
    ("スカイスキン", "ひこう"),
    ("フェアリースキン", "フェアリー"),
    ("フリーズスキン", "こおり"),
]

CONTACT_AILMENT_CASES = [
    ("せいでんき", "まひ"),
    ("どくのトゲ", "どく"),
    ("ほのおのからだ", "やけど"),
]

MULTI_TYPE_PLATE_CASES = [
    (plate_item_name, expected_type)
    for plate_item_name, expected_type in PLATE_TO_TYPE.items()
    if plate_item_name in ITEMS
]


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
    before_hp = defender.hp
    battle.roll_damage = lambda *_args, **_kwargs: 30
    t.run_move(battle, 0)
    assert defender.hp == before_hp - 30
    assert defender.name == "コオリッポ(アイス)"


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
    battle.roll_damage = lambda *a, **k: 10
    battle.random.random = lambda: 0.09
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_あくしゅう_確率外ではひるみを付与しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あくしゅう", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    battle.roll_damage = lambda *a, **k: 10
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


def test_あとだし_高優先度技は先攻():
    """あとだし: 相手より優先度が高い技を使用した場合は先攻になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]


def test_アナライズ_確定行動順で先攻なら威力据え置き():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("コイル")],
    )
    battle.advance_turn()
    assert 4096 == battle.damage_calculator.power_modifier


def test_アナライズ_確定行動順で後攻なら威力上昇():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.advance_turn()
    assert 5325 == battle.damage_calculator.power_modifier


def test_あまのじゃく_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1


def test_あまのじゃく_能力変化量の符号を反転する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"A": 1, "B": -2, "C": 3, "D": -4, "S": 1, "ACC": -2, "EVA": 3}
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


@pytest.mark.parametrize(
    "initial_weather", strong_weathers
)
def test_あめふらし_強天候は上書き不可(initial_weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="あめふらし")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == initial_weather


@pytest.mark.parametrize(
    "initial_weather", ["はれ", "すなあらし", "ゆき"]
)
def test_あめふらし_通常天候を上書きする(initial_weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="あめふらし")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "あめ"


def test_いかく_登場時に相手攻撃1段階ダウン():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == -1


def test_いかりのこうら_HP半分超から半分以下でACSアップBDダウン():
    """いかりのこうら: HPが半分を下回ったとき A/C/S↑1、B/D↓1。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 2
    battle.roll_damage = lambda *a, **k: 5

    t.run_move(battle, 1)

    assert defender.hp <= defender.max_hp // 2
    assert defender.rank["A"] == 1
    assert defender.rank["C"] == 1
    assert defender.rank["S"] == 1
    assert defender.rank["B"] == -1
    assert defender.rank["D"] == -1


def test_いかりのこうら_ひんしになっても発動する():
    """いかりのこうら: HPが半分を下回ってひんしになっても発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.roll_damage = lambda *a, **k: defender.max_hp

    t.run_move(battle, 1)

    assert defender.fainted
    assert defender.rank["A"] == 1


def test_いかりのこうら_被弾前HPが半分以下なら発動しない():
    """いかりのこうら: すでにHP半分以下のときは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2
    battle.roll_damage = lambda *a, **k: 1

    t.run_move(battle, 1)

    assert defender.rank["A"] == 0


def test_いかりのつぼ_A最大のとき急所被弾でも変化なし():
    """いかりのつぼ: こうげきが既に最大ランクのときは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    battle.modify_stats(defender, {"A": 6}, source=defender)

    revealed_before = defender.ability.revealed
    t.run_move(battle, 1)

    assert battle.move_executor.critical is True
    assert defender.rank["A"] == 6
    assert defender.ability.revealed == revealed_before


def test_いかりのつぼ_急所でない被弾は発動しない():
    """いかりのつぼ: 急所でない被弾では発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    battle.random.random = lambda: 0.99
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert battle.move_executor.critical is False
    assert defender.rank["A"] == 0


def test_いかりのつぼ_急所被弾でこうげき最大():
    """いかりのつぼ: 急所に被弾したときこうげきが最大ランクになる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert battle.move_executor.critical is True
    assert defender.rank["A"] == 6


def test_いしあたま_反動技を使っても反動ダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["すてみタックル"])],
        team1=[Pokemon("ヤドン")],
    )
    attacker = battle.actives[0]
    battle.advance_turn()
    assert attacker.hp == attacker.max_hp


def test_いたずらごころ_あくタイプ相手には変化技が無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["でんじは"])],
        team1=[Pokemon("ヘルガー")],
    )
    ctx = t.build_context(battle, atk_idx=0)
    assert not battle.events.emit(Event.ON_BEFORE_APPLY_MOVE, ctx, True)


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
    )
    ctx = t.build_context(battle, atk_idx=0)
    assert battle.events.emit(Event.ON_BEFORE_APPLY_MOVE, ctx, True)


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
    before_attacker_hp = attacker.hp
    expected_damage = max(1, attacker.max_hp // 4)
    battle.roll_damage = lambda *_args, **_kwargs: 10
    t.run_move(battle, 0)
    assert defender.name == "ウッウ"
    assert attacker.rank["B"] == -1
    assert attacker.hp == before_attacker_hp - expected_damage


def test_うのミサイル_なみのりが命中するとHP半分以下でまるのみのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ウッウ", ability_name="うのミサイル", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, -(mon.max_hp // 2 + 1))
    assert mon.hp * 2 <= mon.max_hp
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
    battle.roll_damage = lambda *_args, **_kwargs: 10
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
        accuracy=100,
    )
    move = t.run_move(battle, 0)
    assert move.type == "みず"


def test_うるおいボイス_非音技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボイス", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_うるおいボイス_音技の威力が1_2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボイス", move_names=["ハイパーボイス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_うるおいボディ_あめ中に状態異常を回復する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボディ")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    assert mon.ailment.is_active
    t.end_turn(battle)
    assert not mon.ailment.is_active


def test_うるおいボディ_晴れ中は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボディ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert mon.ailment.is_active


def test_エアロック_すなあらしのターン終了ダメージが無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="エアロック")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END, None, None)
    assert mon.hp == mon.max_hp


@pytest.mark.parametrize("weather_name", weathers)
def test_エアロック_天候と強天候を無効化する(weather_name: str):
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
def test_エレキメイカー_別フィールドを上書きする(initial_terrain: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="エレキメイカー")],
        team1=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 99),
    )
    mon = battle.player_states[battle.players[0]].team[1]
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert mon.ability.revealed


def test_えんかく_直接攻撃でほのおのからだが発動しない():
    """えんかく所持者が直接攻撃を使っても、相手のほのおのからだが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="えんかく", move_names=["たいあたり"])],
        team1=[Pokemon("ウインディ", ability_name="ほのおのからだ")],
    )
    battle.random.random = lambda: 0.0
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert not attacker.has_ailment("やけど")


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


def test_えんかく_非所持者の直接攻撃では接触効果が発動する():
    """えんかくを持たないポケモンが直接攻撃を使えば、ほのおのからだは通常通り発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ウインディ", ability_name="ほのおのからだ")],
    )
    battle.random.random = lambda: 0.0
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_ailment("やけど")


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
    battle.print_logs()
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_攻撃技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True
    assert battle.actives[1].ability.revealed is False


def test_おうごんのからだ_相手の変化技を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    battle.print_logs()
    assert battle.move_executor.move_applied is False
    assert battle.actives[1].ability.revealed is True


def test_おうごんのからだ_自分対象の変化技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True


def test_おみとおし_アイテムありの相手のアイテムが公開される():
    """おみとおし: 場に出たとき相手のアイテムが公開される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おみとおし")],
        team1=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    foe = battle.actives[1]
    assert foe.item.revealed is True
    assert battle.actives[0].ability.revealed is True


def test_おみとおし_アイテムなしの相手には発動しない():
    """おみとおし: 相手がアイテムを持っていなければ発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おみとおし")],
        team1=[Pokemon("ピカチュウ")],
    )
    foe = battle.actives[1]
    # アイテムなしなので revealed は False のまま
    assert foe.item.revealed is False


def test_おみとおし_交代して再登場すると再度公開される():
    """おみとおし: 交代して再び場に出たとき相手のアイテムを再度公開する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おみとおし"), Pokemon("コイル")],
        team1=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    foe = battle.actives[1]
    # 最初の登場で公開済み
    assert foe.item.revealed is True
    # 一度引っ込めて再登場
    foe.item.revealed = False
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert foe.item.revealed is True


def test_おもかげやどし_オーガポン以外は発動しない():
    """おもかげやどし: オーガポン以外のポケモンには発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # どのランクも変化しない
    for stat in ("A", "B", "C", "D", "S"):
        assert mon.rank[stat] == 0


def test_おもかげやどし_テラスタルは登場時フラグに関係なく発動する():
    """おもかげやどし: activated_since_switch_in が True でもテラスタル時は発動する。"""
    from jpoke.enums import Event
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # 登場時に発動済み（フラグ = True）
    assert mon.ability.activated_since_switch_in is True
    assert mon.rank["S"] == 1
    # フラグが True でもテラスタル時は発動する
    ctx = EventContext(source=mon)
    battle.events.emit(Event.ON_TERASTALLIZE, ctx=ctx, value=None)
    assert mon.rank["S"] == 2


def test_おもかげやどし_テラスタル時に能力が上昇する():
    """おもかげやどし: テラスタル直後にフォルムに対応する能力が1段階上昇する。"""
    from jpoke.enums import Event
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["S"] == 1  # 登場時に+1
    ctx = EventContext(source=mon)
    battle.events.emit(Event.ON_TERASTALLIZE, ctx=ctx, value=None)
    assert mon.rank["S"] == 2  # テラスタル時にさらに+1


@pytest.mark.parametrize(
    "form_name, expected_stat",
    [
        ("オーガポン(みどり)", "S"),
        ("オーガポン(いど)", "D"),
        ("オーガポン(かまど)", "A"),
        ("オーガポン(いしずえ)", "B"),
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
    assert mon.rank["S"] == 1
    # 一度引っ込める（交代でランクはリセットされる）
    t.run_switch(battle, 0, 1)
    assert mon.rank["S"] == 0  # 交代後はリセット
    # 再登場するとおもかげやどしが再発動して+1
    t.run_switch(battle, 0, 0)
    assert mon.rank["S"] == 1


def test_おもかげやどし_特性再有効化時にも発動する():
    """おもかげやどし: ON_ABILITY_ENABLED（かがくへんかガス解除など）でも再発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["S"] == 1
    # ON_ABILITY_ENABLED を手動発火すると再発動する
    battle.events.emit(Event.ON_ABILITY_ENABLED,
                       EventContext(source=mon))
    assert mon.rank["S"] == 2


def test_おやこあい_単発攻撃が2ヒットする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # ダメージ計算結果を固定
    battle.roll_damage = lambda *args, **kwargs: 40
    t.run_move(battle, 0)
    attacker, defender = battle.actives
    assert defender.hits_taken == 2
    assert defender.hp == defender.max_hp - 40 - 10
    assert attacker.rank["S"] == 2


def test_おやこあい_既存連続技には適用しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["すいりゅうれんだ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    t.run_move(battle, 0)
    assert defender.hits_taken == 3


def test_おわりのだいち_らんきりゅうは上書きできない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="おわりのだいち")],
        team1=[Pokemon("ピカチュウ")],
        weather=("らんきりゅう", 1),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "らんきりゅう"


@pytest.mark.parametrize(
    "weather_name",
    normal_weathers + ["おおあめ"]
)
def test_おわりのだいち_らんきりゅう以外上書きする(weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="おわりのだいち")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "おおひでり"


def test_オーラブレイク_登場時に特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="オーラブレイク")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed is True


def test_かがくへんかガス_互いのかがくへんかガスは無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled
    assert battle.actives[1].ability.enabled


def test_かがくへんかガス_登場時に相手の特性を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert not battle.actives[1].ability.enabled
    assert not battle.actives[1].ability.revealed
    assert battle.actives[0].rank["A"] == 0


def test_かがくへんかガス_解除後は特性が再び有効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    player = battle.players[0]
    t.run_switch(battle, 0, 1)
    assert battle.actives[1].ability.enabled
    assert battle.actives[1].ability.revealed
    assert battle.actives[0].rank["A"] == 0


def test_かぜのり_おいかぜ状態でなければ登場時上昇なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    _, mon = battle.actives
    assert mon.rank["A"] == 0


def test_かぜのり_おいかぜ状態の場に出るとこうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        side1={"おいかぜ": 3},
    )
    _, mon = battle.actives
    assert mon.rank["A"] == 1


def test_かぜのり_おいかぜ発生時にこうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    _, mon = battle.actives
    battle.get_side(mon).activate("おいかぜ", 3)
    assert mon.rank["A"] == 1


def test_かぜのり_かたやぶりで風技吸収無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.rank["A"] == 0


def test_かぜのり_対象外の技は通常被弾():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.rank["A"] == 0


def test_かぜのり_風の技を吸収してこうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp
    assert defender.rank["A"] == 1


def test_かそく_交代直後のターンは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="かそく", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # 交代したターンはかそくが発動しない
    t.reserve_command(battle,
                      command0=Command.SWITCH_1,
                      command1=Command.MOVE_0)
    battle.advance_turn()

    mon = battle.actives[0]
    assert mon.rank["S"] == 0

    # 次のターンはかそくが発動する
    t.reserve_command(battle,
                      command0=Command.MOVE_0,
                      command1=Command.MOVE_0)
    battle.advance_turn()
    assert mon.rank["S"] == 1


def test_かそく_行動後のターン終了時に素早さが上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かそく")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["S"] == 0

    mon.executed_move = mon.moves[0]
    t.end_turn(battle)
    assert mon.rank["S"] == 1


def test_かたいツメ_接触技のみ威力補正1_3倍():
    battle_contact = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたいツメ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle_contact, 0)
    assert 5325 == battle_contact.damage_calculator.power_modifier

    battle_non_contact = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたいツメ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle_non_contact, 0)
    assert 4096 == battle_non_contact.damage_calculator.power_modifier


def test_かたやぶり_場に出たときに特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed is True


def test_かちき_いかくで特攻2段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かちき")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[0].rank["C"] == 2


def test_かちき_相手由来の能力低下で発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かちき")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon, foe = battle.actives
    battle.modify_stats(mon, {"A": -1}, source=foe)
    assert mon.rank["C"] == 2


def test_かちき_自分由来の能力低下では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かちき")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_stats(mon, {"A": -1}, source=mon)
    assert mon.rank["C"] == 0


def test_カブトアーマー_かたやぶり攻撃では無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カブトアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is True


def test_カブトアーマー_急所ランクを0にする():
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
    battle.consume_item(mon)
    t.change_item(battle, mon, "オボンのみ")
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_かるわざ_アイテムを失うと素早さが2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.consume_item(mon)
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_かるわざ_アイテムを失ってから再入場しても発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.consume_item(mon)
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_かるわざ_入場時にアイテムなしなら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    boosted = battle.calc_effective_speed(mon)
    assert boosted == mon.stats["S"]


def test_かんつうドリル_接触技でまもる状態を貫通してHPを減らす():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんつうドリル", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "まもる", count=1)
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_かんつうドリル_非接触技はまもるに防がれる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんつうドリル", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "まもる", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_かんろなミツ_2回目入場では発動しない():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="かんろなミツ"),
            Pokemon("イーブイ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    foe = battle.actives[1]
    assert foe.rank["EVA"] == -1
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert foe.rank["EVA"] == -1


def test_かんろなミツ_初回入場で相手のEVAが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんろなミツ")],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.actives[1].rank["EVA"] == -1


def test_カーリーヘアー_直接攻撃で攻撃者のSが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カーリーヘアー")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["S"] == -1


def test_カーリーヘアー_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カーリーヘアー")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["S"] == 0


def test_がんじょう_HP満タン時の致死ダメージでHP1残る():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ガブリアス", move_names=["じしん"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == 1
    assert defender.ability.revealed


def test_がんじょう_かたやぶりにで一撃技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じわれ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.move_executor.move_applied is True


def test_がんじょう_かたやぶりによる致死ダメージは耐えない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ガブリアス", ability_name="かたやぶり", move_names=["じしん"])],
    )
    battle.roll_damage = lambda *_args, **_kwargs: 999
    t.run_move(battle, 1)
    assert battle.actives[0].hp == 0


def test_がんじょう_一撃必殺技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["じわれ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.move_executor.move_applied is False


def test_がんじょうあご_かみつき技で威力補正1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょうあご", move_names=["かみつく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_ききかいひ_HP半分超から半分以下で割り込み交代する():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="ききかいひ"),
            Pokemon("ピカチュウ", move_names=["たいあたり"])
        ],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]

    damage = defender.max_hp - defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: damage

    t.run_move(battle, 1)

    assert battle.player_states[battle.players[0]].interrupt == Interrupt.EMERGENCY

    battle.run_interrupt_switch(Interrupt.EMERGENCY)

    assert battle.player_states[battle.players[0]].active_index == 1


def test_ききかいひ_こんらん自傷では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability_name="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")

    assert battle.player_states[battle.players[0]].interrupt == Interrupt.NONE


def test_ききかいひ_やけどダメージでも発動する():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability_name="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"やけど": None},
    )
    mon = battle.actives[0]

    mon.hp = mon.max_hp // 2 + 1
    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))

    assert battle.player_states[battle.players[0]].interrupt == Interrupt.EMERGENCY


def test_ききかいひ_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability_name="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]

    defender.hp = defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: 1

    t.run_move(battle, 1)

    assert battle.player_states[battle.players[0]].interrupt == Interrupt.NONE
    assert battle.player_states[battle.players[0]].active_index == 0


def test_きけんよち_相手がバツグン攻撃技を持つとき特性が開示される():
    # ピカチュウ(でんき)に対してじしん(じめん、2倍) → みぶるいした
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きけんよち")],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
    )
    assert battle.actives[0].ability.revealed is True


def test_きけんよち_相手が一撃必殺技を持つとき特性が開示される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きけんよち")],
        team1=[Pokemon("ピカチュウ", move_names=["つのドリル"])],
    )
    assert battle.actives[0].ability.revealed is True


def test_きけんよち_相手が変化技のみ持つとき発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きけんよち")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
    )
    assert battle.actives[0].ability.revealed is False


def test_きけんよち_相手が等倍以下の技しか持たないとき発動しない():
    # ノーマル技はでんきタイプに等倍
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きけんよち")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    assert battle.actives[0].ability.revealed is False


def test_きもったま_いかくを無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きもったま")],
        team1=[Pokemon("ウインディ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == 0


def test_きもったま_かくとう技がゴースト複合に抜群():
    # かわらわり(かくとう) vs サーフゴー(はがね/ゴースト) → はがね×2倍
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きもったま", move_names=["かわらわり"])],
        team1=[Pokemon("サーフゴー", ability_name="")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 8192


def test_きもったま_ノーマル技がゴーストタイプに等倍で当たる():
    # たいあたり(ノーマル) vs ミミッキュ(ゴースト/フェアリー) → 等倍でHPが減る
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きもったま", move_names=["たいあたり"])],
        team1=[Pokemon("ミミッキュ", ability_name="")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert battle.damage_calculator.def_type_modifier == 4096


def test_きゅうばん_かたやぶりで無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("フシギダネ")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    defender_after = battle.actives[1]
    # かたやぶりによってきゅうばんの無効化が貫通され、交代が発生する
    assert defender_before is not defender_after


def test_きゅうばん_吹き飛ばしを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("フシギダネ")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    defender_after = battle.actives[1]
    # きゅうばんにより交代が阻止され、アクティブは変わらない
    assert defender_before is defender_after


def test_きょううん_急所ランクが1上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きょううん", move_names=["つじぎり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        AttackContext(attacker=attacker, defender=defender, move=move),
        0,
    )
    assert result == 1


def test_きよめのしお_ゴースト半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シャドーボール"])],
        team1=[Pokemon("ピカチュウ", ability_name="きよめのしお")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 2048


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"]
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


def test_きんしのちから_変化技でクリアボディを無視できる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きんしのちから", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["A"] == -1


def test_きんしのちから_変化技選択時に同優先度で最後に行動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きんしのちから", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.reserve_command(battle)
    order = battle.resolve_action_order()
    assert order[-1] == battle.actives[0]


def test_きんしのちから_攻撃技選択時は後攻化しない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="きんしのちから", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.reserve_command(battle)
    order = battle.resolve_action_order()
    # コイルより素早いピカチュウが先攻のまま
    assert order[0] == battle.actives[1]


def test_きんちょうかん_相手をきんちょうかん状態にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="きんちょうかん")],
    )
    assert battle.query.is_nervous(battle.actives[0])
    assert battle.actives[1].ability.enabled


def test_ぎゃくじょう_HP半分超から半分以下で特攻1段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    defender.hp = defender.max_hp // 2 + 2
    t.run_move(battle, 1)

    assert defender.hp <= defender.max_hp // 2
    assert defender.rank["C"] == 1
    assert defender.ability.revealed is True


def test_ぎゃくじょう_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]

    defender.hp = defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: 1

    t.run_move(battle, 1)

    assert defender.rank["C"] == 0


def test_ぎょぐん_HP1_4以下で登場してもたんどくのすがたのまま():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん", level=20)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4
    assert mon.name == "ヨワシ(むれ)"  # 登場時はむれたすがた、HPを下げた後は次のターン終了時に判定


def test_ぎょぐん_HP1_4超で登場するとむれたすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん", level=20)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヨワシ(むれ)"


def test_ぎょぐん_ターン終了時にHP1_4以下ならたんどくのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん", level=20)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヨワシ(むれ)"
    mon.hp = mon.max_hp // 4
    t.end_turn(battle)
    assert mon.name == "ヨワシ(たんどく)"


def test_ぎょぐん_ターン終了時にHP1_4超ならむれたすがたを維持する():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん", level=20)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヨワシ(むれ)"
    t.end_turn(battle)
    assert mon.name == "ヨワシ(むれ)"


def test_ぎょぐん_レベル20未満では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん", level=19)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヨワシ(たんどく)"


def test_クイックドロウ_30パーセント発動しないとき通常行動順():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 1.0  # 発動しない
    t.reserve_command(battle)
    order = battle.resolve_action_order()
    assert order[-1] == battle.actives[0]


def test_クイックドロウ_変化技選択時は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 0.0  # 乱数を0に固定しても変化技では発動しない
    t.reserve_command(battle)
    order = battle.resolve_action_order()
    assert order[-1] == battle.actives[0]


def test_クイックドロウ_攻撃技選択時に発動すると先攻になる():
    # コイル(S低い)がクイックドロウで先攻化
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 0.0  # 必ず発動
    t.reserve_command(battle)
    order = battle.resolve_action_order()
    assert order[0] == battle.actives[0]
    assert battle.actives[0].ability.revealed is True


@pytest.mark.parametrize(
    "name, stat",
    [
        ("スピアー", "A"),
        ("ゼニガメ", "B"),
        ("フシギダネ", "C"),
        ("カメックス", "D"),
        ("ピカチュウ", "S"),
    ]
)
def test_クォークチャージ_最大ステータスがバフされる(name, stat):
    battle = t.start_battle(
        team0=[Pokemon(name, ability_name="クォークチャージ", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat == stat


def test_くさのけがわ_():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_くさのけがわ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


def test_くだけるよろい_物理技でB下がりS上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["B"] == -1
    assert battle.actives[0].rank["S"] == 2


def test_くだけるよろい_特殊技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["B"] == 0
    assert battle.actives[0].rank["S"] == 0


def test_クリアボディ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1


def test_クリアボディ_能力低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stats = {"A": -1, "B": +1, "C": -3, "D": +3, "S": -5, "ACC": +5, "EVA": -6}
    expected = {k: v for k, v in stats.items() if v > 0}

    assert expected == battle.modify_stats(mon0, stats, source=mon1)


def test_クリアボディ_自己低下技は防げない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, _ = battle.actives
    stats = {"A": -1, "B": +1, "C": -3, "D": +3, "S": -5, "ACC": +5, "EVA": -6}
    expected = stats

    assert expected == battle.modify_stats(mon0, stats, source=mon0)


def test_こおりのりんぷん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_こおりのりんぷん_物理技のダメージ半減しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_こおりのりんぷん_特殊技のダメージ半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_こぼれダネ_すでにグラスフィールドなら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こぼれダネ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        terrain=("グラスフィールド", 3),
    )
    t.run_move(battle, 1)
    assert battle.terrain.name == "グラスフィールド"
    assert battle.terrain.count == 3


def test_こぼれダネ_被弾時にグラスフィールドが展開される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こぼれダネ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.terrain.name == "グラスフィールド"


def test_こんじょう_やけど時はやけど半減を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こんじょう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"やけど": None},
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144
    assert battle.damage_calculator.burn_modifier == 4096


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


def test_さまようたましい_protectedフラグ持ち攻撃者には発動しない():
    """さまようたましい: 攻撃者の特性が protected フラグを持つ場合は特性交換しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おもかげやどし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    # おもかげやどし は protected フラグを持つので入れ替わらない
    assert attacker.ability.name == "おもかげやどし"
    assert defender.ability.name == "さまようたましい"


def test_さまようたましい_特性なし攻撃者には発動しない():
    """さまようたましい: 攻撃者に特性がない（空文字）場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
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
    """さまようたましい: 非接触技を受けても特性は入れ替わらない。"""
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
def test_サンパワー_はれ中に特殊技の特攻1_5倍(weather_name: str, weather_count: int):
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


def test_サーフテール_エレキフィールド中にS2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サーフテール")],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
    )
    mon = battle.actives[0]
    speed_with = battle.speed_calculator.calc_effective_speed(mon)
    assert speed_with == mon.stats["S"] * 2


def test_サーフテール_他フィールドでは変化なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サーフテール")],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
    )
    mon = battle.actives[0]
    speed = battle.speed_calculator.calc_effective_speed(mon)
    assert speed == mon.stats["S"]


def test_しぜんかいふく_交代時に状態異常回復():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しぜんかいふく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"どく": None},
    )
    mon = battle.actives[0]
    assert mon.ailment.is_active
    t.run_switch(battle, 0, 1)
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
        team0=[Pokemon("ピカチュウ", ability_name="しょうりのほし", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100 * 4506 // 4096


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
    battle.modify_stats(attacker, {"ACC": -2}, source=foe)
    # しんがん所持者のACCランクは変化しないはず
    assert attacker.rank["ACC"] == 0


def test_しんがん_相手の回避ランクを無視する():
    """しんがん: 相手の回避ランク上昇を命中計算で無視する"""
    from jpoke.enums import Event
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しんがん", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    # 相手のEVAランクを最大に上げる
    defender.rank["EVA"] = 6
    ctx = AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    # ON_GET_STAT_RANK でEVAが0に設定されるはず
    ranks = battle.events.emit(
        Event.ON_GET_STAT_RANK,
        ctx=ctx,
        value={"ACC": attacker.rank["ACC"], "EVA": defender.rank["EVA"]},
    )
    assert ranks["EVA"] == 0, "しんがんで相手のEVAランクが無視される"


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


@pytest.mark.parametrize("ailment_name", ["どく", "もうどく", "まひ", "やけど"])
def test_シンクロ_状態異常が相手に伝染する(ailment_name: str):
    """シンクロ: どく/もうどく/まひ/やけど を受けたとき相手にも同じ状態異常を与える。
    ノーマルタイプのカビゴン同士は全状態異常に対して免疫がない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="シンクロ")],
        team1=[Pokemon("カビゴン")],
    )
    sync_mon, foe = battle.actives
    # 相手からシンクロ所持者に状態異常を付与する
    battle.ailment_manager.apply(sync_mon, ailment_name, source=foe)
    assert sync_mon.has_ailment(ailment_name), "シンクロ所持者が状態異常を持つ"
    assert foe.has_ailment(ailment_name), "相手にも同じ状態異常が伝染するはず"


def test_シンクロ_自傷の場合は伝染しない():
    """シンクロ: 自分自身が原因の状態異常(かえんだま等)は伝染しない"""
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


def test_じきゅうりょく_特殊技でもBが上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["B"] == 1


def test_じきゅうりょく_被弾でBが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["B"] == 1


def test_じょうきっかん_ほのお技でSが6段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうきっかん")],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["S"] == 6


def test_じょうきっかん_みず技でSが6段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうきっかん")],
        team1=[Pokemon("カビゴン", move_names=["バブルこうせん"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["S"] == 6


def test_じょうきっかん_他タイプでは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="じょうきっかん")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["S"] == 0


def test_じょおうのいげん_かたやぶりで無効化される():
    """じょおうのいげん: かたやぶり持ちには先制技が通る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", ability_name="じょおうのいげん")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_じょおうのいげん_優先度ゼロの技は通る():
    """じょおうのいげん: 優先度0の技は通常通り当たる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="じょおうのいげん")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_じょおうのいげん_優先度プラスの技を無効化する():
    """じょおうのいげん: 優先度+1の技（でんこうせっか）を無効化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", ability_name="じょおうのいげん")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    assert defender.hp == defender.max_hp


def test_じんばいったい_相手をきんちょうかん状態にする():
    """じんばいったい: きんちょうかんと同様に相手のきのみ使用を禁止する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="じんばいったい")],
    )
    assert battle.query.is_nervous(battle.actives[0])


def test_すいほう_ほのお技弱化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すいほう")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    t.run_move(battle, 1)
    assert 2048 == battle.damage_calculator.atk_modifier


def test_すいほう_みず技強化():
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
    _, defender = battle.actives
    assert defender.hits_taken == 5


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン_ノーマル技を対応タイプに変換する(
    ability_name: str,
    expected_type: str,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    move = t.run_move(battle, 0)
    assert move.type == expected_type


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン_変換した技の威力が4915倍になる(
    ability_name: str,
    expected_type: str,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_すてみ_反動技の威力が1_2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すてみ", move_names=["すてみタックル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_すてみ_非反動技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すてみ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_スナイパー_急所時の最終ダメージを1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スナイパー", move_names=["トリックフラワー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.crit_rank == 3
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


@pytest.mark.parametrize(
    "move_name",
    ["いわなだれ", "じならし", "アイアンヘッド"],
)
def test_すなのちから_すなあらし以外では威力補正なし(move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなのちから", move_names=[move_name])],
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
    "wall_name, move_name",
    [
        ("リフレクター", "たいあたり"),
        ("ひかりのかべ", "でんきショック"),
        ("オーロラベール", "たいあたり"),
        ("オーロラベール", "でんきショック"),
    ],
)
def test_すりぬけ_壁を無視する(wall_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        side1={wall_name: 5},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_するどいめ_かたやぶりで無効():
    """するどいめ: かたやぶり持ちによる命中率低下はするどいめを貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["ACC"] == -1


def test_するどいめ_命中率低下を防ぐ():
    """するどいめ: 相手による命中率ランク低下を防ぐ。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ")],
        team1=[Pokemon("ピカチュウ", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["ACC"] == 0


def test_するどいめ_相手の回避率ランクを無視する():
    """するどいめ: 攻撃時に相手の回避率ランク上昇を無視する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].rank["EVA"] = 6
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
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier

    battle.turn = battle.actives[0].ability.count + 5
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_スワームチェンジ_ターン終了時にHP1_2以下ならパーフェクトフォルムになる():
    battle = t.start_battle(
        team0=[Pokemon("ジガルデ(10%)", ability_name="スワームチェンジ", level=50)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    damage = mon.max_hp // 2
    mon.hp = damage
    hp_before = mon.hp
    t.end_turn(battle)
    assert mon.name == "ジガルデ(パーフェクト)"
    assert mon.hp > hp_before


def test_スワームチェンジ_ターン終了時にHP1_2超ならフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ジガルデ(50%)", ability_name="スワームチェンジ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    t.end_turn(battle)
    assert mon.name == "ジガルデ(50%)"


def test_スワームチェンジ_パーフェクトフォルムでは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ジガルデ(パーフェクト)", ability_name="スワームチェンジ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "ジガルデ(パーフェクト)"


def test_せいぎのこころ_あく以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == 0


def test_せいぎのこころ_あく技でAが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいぎのこころ")],
        team1=[Pokemon("カビゴン", move_names=["かみつく"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == 1


def test_せいしんりょく_いかくを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        team1=[Pokemon("ウインディ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == 0


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
    battle.advance_turn()
    assert battle.weather.name == "", "ゼロフォーミングで天候が消去される"
    assert battle.terrain.name == "", "ゼロフォーミングでフィールドが消去される"


def test_そうだいしょう_ひんし味方なしでは補正なし():
    # TODO : そうだいしょうのテストはすべて、ability.stateを検証するのではなく、ダメージ計算に使われた補正値が正しいか検証する。
    """そうだいしょう: ひんし味方がいない場合はability.stateが0のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="そうだいしょう")],
        team1=[Pokemon("フシギダネ")],
    )
    mon = t.run_switch(battle, 0, 1)
    assert not mon.ability.state


def test_そうだいしょう_味方1体ひんしで補正率0_1():
    """そうだいしょう: ひんし味方1体でability.stateが0.1になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ"), Pokemon("カビゴン", ability_name="そうだいしょう")],
        team1=[Pokemon("フシギダネ")],
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    bench[0].hp = 0

    mon = t.run_switch(battle, 0, 2)
    assert mon.ability.state == pytest.approx(0.1)


def test_そうだいしょう_味方5体ひんしで補正率上限0_5():
    """そうだいしょう: ひんし味方5体でも上限の0.5になる。"""
    team = [Pokemon("ピカチュウ")] * 5 + [Pokemon("カビゴン", ability_name="そうだいしょう")]
    battle = t.start_battle(
        team0=team,
        team1=[Pokemon("フシギダネ")],
    )
    player0 = battle.players[0]
    state = battle.player_states[player0]
    soudaisho = state.team[5]
    for mon in state.selection:
        if mon is not soudaisho:
            mon.hp = 0

    switched_in = t.run_switch(battle, 0, 5)
    assert switched_in.ability.state == pytest.approx(0.5)


def test_ソウルハート_KO時にCが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ソウルハート", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
    )
    foe = battle.actives[1]
    foe.hp = 1
    t.run_move(battle, 0)
    assert foe.fainted
    assert battle.actives[0].rank["C"] == 1


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("あついしぼう", "ひのこ"),
        ("あついしぼう", "れいとうビーム"),
        ("たいねつ", "ひのこ"),
    ],
)
def test_タイプ半減系(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("あついしぼう", "ひのこ"),
        ("たいねつ", "ひのこ"),
    ],
)
def test_タイプ半減系_かたやぶりで無効(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability_name, move_name, expected",
    [
        ("いわはこび", "いわなだれ", 6144),
        ("はがねつかい", "アイアンヘッド", 6144),
        ("りゅうのあぎと", "りゅうのはどう", 6144),
        ("トランジスタ", "でんきショック", 5325),
    ],
)
def test_タイプ強化系(ability_name: str, move_name: str, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert expected == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability, move, stat, rank",
    [
        ("こんがりボディ", "ひのこ", "B", 2),
        ("そうしょく", "このは", "A", 1),
        ("でんきエンジン", "でんきショック", "S", 1),
        ("ひらいしん", "でんきショック", "C", 1),
        ("よびみず", "みずでっぽう", "C", 1),
    ],
)
def test_タイプ無効バフ系(ability: str, move: str, stat: Stat, rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move])],
        team1=[Pokemon("ピカチュウ", ability_name=ability)],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.hp == defender.max_hp
    assert defender.rank[stat] == rank


@pytest.mark.parametrize(
    "ability, move, stat, rank",
    [
        ("こんがりボディ", "ひのこ", "B", 2),
        ("そうしょく", "このは", "A", 1),
        ("でんきエンジン", "でんきショック", "S", 1),
        ("ひらいしん", "でんきショック", "C", 1),
        ("よびみず", "でんきショック", "C", 1),
    ],
)
def test_タイプ無効バフ系_かたやぶりで無効(ability: str, move: str, stat: Stat, rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
        team1=[Pokemon("ピカチュウ", ability_name=ability)],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.rank[stat] == 0


@pytest.mark.parametrize(
    "ability, move",
    [
        ("ちくでん", "スパーク"),
        ("ちょすい", "なみのり"),
        ("どしょく", "じしん"),
    ],
)
def test_タイプ無効回復(ability, move):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", move_names=[move])],
    )
    defender, attacker = battle.actives
    defender.hp = 1
    t.run_move(battle, 1)
    assert defender.hp == 1 + defender.max_hp // 4
    assert defender.ability.revealed


@pytest.mark.parametrize(
    "ability, move",
    [
        ("ちくでん", "スパーク"),
        ("ちょすい", "なみのり"),
        ("どしょく", "じしん"),
    ],
)
def test_タイプ無効回復_かたやぶりで無効(ability, move):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp
    assert not defender.ability.revealed


def test_たんじゅん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1


def test_たんじゅん_能力上昇量が2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"A": 1, "B": -2, "C": 3, "D": -4, "S": 1, "ACC": -2, "EVA": 3}
    battle.modify_stats(target, stats, source=source)
    for stat, change in stats.items():
        assert target.rank[stat] == max(-6, min(6, change * 2))


@pytest.mark.parametrize(
    "foe_name, stat",
    [
        ("フシギダネ", "A"),
        ("ゼニガメ", "C"),
        ("ウインディ", "C"),  # BD同じならCアップ
    ],
)
def test_ダウンロード_能力アップ(foe_name, stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダウンロード")],
        team1=[Pokemon(foe_name)],
    )
    assert battle.actives[0].rank[stat] == 1


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_だっぴ_ターン終了時に状態異常を回復する(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={ailment_name: None},
    )
    mon = battle.actives[0]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.end_turn(battle)
    finally:
        battle.random.random = orig_random

    assert not mon.ailment.is_active


def test_だっぴ_発動ターンはどくダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"どく": None},
    )
    mon = battle.actives[0]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.end_turn(battle)
    finally:
        battle.random.random = orig_random

    assert mon.hp == mon.max_hp


def test_だっぴ_非発動時は状態異常が残る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"どく": None},
    )
    mon = battle.actives[0]

    orig_random = battle.random.random
    battle.random.random = lambda: 1
    try:
        t.end_turn(battle)
    finally:
        battle.random.random = orig_random

    assert mon.ailment.is_active


def test_ダルマモード_ターン終了時にHP1_2以下ならダルマのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ノーマル)", ability_name="ダルマモード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "ヒヒダルマ(ダルマ)"


def test_ダルマモード_ターン終了時にHP1_2超なら元のすがたに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ノーマル)", ability_name="ダルマモード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "ヒヒダルマ(ダルマ)"
    mon.hp = mon.max_hp // 2 + 1
    t.end_turn(battle)
    assert mon.name == "ヒヒダルマ(ノーマル)"


def test_ダルマモード_交代するとノーマルのすがたに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ノーマル)", ability_name="ダルマモード"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "ヒヒダルマ(ダルマ)"
    t.run_switch(battle, 0, 1)
    assert mon.name == "ヒヒダルマ(ノーマル)"


def test_ダルマモード_登場時には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ノーマル)", ability_name="ダルマモード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヒヒダルマ(ノーマル)"


def test_ダークオーラ_オーラブレイクがいるとあく技の威力が0_75倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダークオーラ", move_names=["あくのはどう"])],
        team1=[Pokemon("ピカチュウ", ability_name="オーラブレイク")],
    )
    # TODO : t.run_move して modifier を検証する方式に修正
    attacker, defender = battle.actives
    result = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert result == 3072


def test_ちからずく_追加効果技の威力が1_3倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 5325
    assert attacker.rank["S"] == 0


def test_ちからもち_イカサマで攻撃するときも2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=["イカサマ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_ちからもち_イカサマを受けるときは補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち")],
        team1=[Pokemon("ピカチュウ", move_names=["イカサマ"])],
    )
    t.run_move(battle, 1)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_ちからもち_物理技で攻撃補正2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_ちからもち_特殊技では攻撃補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_ちどりあし_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちどりあし")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[0], "こんらん")
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 100


def test_ちどりあし_こんらんでないとき変化なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちどりあし")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 100


def test_ちどりあし_こんらん中命中率が半減する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちどりあし")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[0], "こんらん")
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 50


def test_テイルアーマー_かたやぶりで無効化される():
    """テイルアーマー: かたやぶり持ちには先制技が通る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", ability_name="テイルアーマー")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_テイルアーマー_優先度ゼロの技は通る():
    """テイルアーマー: 優先度0の技は通常通り当たる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="テイルアーマー")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_テイルアーマー_優先度プラスの技を無効化する():
    """テイルアーマー: 優先度+1の技を無効化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", ability_name="テイルアーマー")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


@pytest.mark.parametrize(
    "name, tera_type, move_name, expected_modifier",
    [
        ("ピカチュウ", "", "でんきショック", 4096 * 2),
        ("ピカチュウ", "でんき", "でんきショック", 4096 * 2.25),
        ("ピカチュウ", "", "ひのこ", 4096),
    ]
)
def test_てきおうりょく_STAB補正(
    name: str,
    tera_type: Type,
    move_name: str,
    expected_modifier: float,
):
    battle = t.start_battle(
        team0=[Pokemon(name, ability_name="てきおうりょく", tera_type=tera_type, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    if tera_type:
        battle.actives[0].terastallize()
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == expected_modifier


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 6144),  # 威力40の技は1.5倍
        ("すてみタックル", 4096),  # 威力90の技
    ]
)
def test_テクニシャン_威力補正(move_name, expected_modifier):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


def test_テクニシャン_連続技でもヒット毎に判定がぶれない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=["タネマシンガン"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    v1 = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=move, hit_index=1, hit_count=5),
        4096,
    )
    v2 = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=move, hit_index=5, hit_count=5),
        4096,
    )

    assert v1 == 6144
    assert v2 == 6144


def test_てつのこぶし_パンチ技以外は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てつのこぶし", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_てつのこぶし_パンチ技威力補正():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てつのこぶし", move_names=["かみなりパンチ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4915 == battle.damage_calculator.power_modifier


def test_テラスシェル_HP満タンでないと発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="テラスシェル")],
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp - 1
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_テラスシェル_かたやぶりで無効():
    """テラスシェル: かたやぶり持ちの技はテラスシェルの半減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="テラスシェル")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


@pytest.mark.parametrize(
    "defender_name, move_name, expected",
    [
        ("コイル", "なみのり", 4096*0.5),       # x1 -> x1/2
        ("コイル", "ひのこ", 4096*0.5),       # x2 -> x1/2
        ("コイル", "じしん", 4096*0.5),           # x4 -> x1/2
        ("コイル", "でんきショック", 4096*0.5),   # x1/2 -> x1/2
        ("コイル", "バレットパンチ", 4096*0.25),   # x1/4 -> x1/4
    ]
)
def test_テラスシェル_等倍以上を半減(defender_name, move_name, expected):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon(defender_name, ability_name="テラスシェル")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected


def test_テラスチェンジ_かがくへんかガス中でも発動する():
    battle = t.start_battle(
        team0=[Pokemon("テラパゴス(ノーマル)", ability_name="テラスチェンジ")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    assert mon.name == "テラパゴス(テラスタル)"


def test_テラスチェンジ_登場時にテラスタルフォルムになる():
    battle = t.start_battle(
        team0=[Pokemon("テラパゴス(ノーマル)", ability_name="テラスチェンジ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "テラパゴス(テラスタル)"


def test_てんきや_エアロック中はフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ラティアス", ability_name="エアロック")],
    )
    mon = battle.actives[0]
    battle.weather_manager.apply("はれ", 5)
    assert mon.name == "ポワルン"


@pytest.mark.parametrize(
    "weather, form",
    [
        ("はれ", "ポワルン(たいよう)"),
        ("おおひでり", "ポワルン(たいよう)"),
        ("あめ", "ポワルン(あまみず)"),
        ("おおあめ", "ポワルン(あまみず)"),
        ("ゆき", "ポワルン(ゆきぐも)"),
    ],
)
def test_てんきや_フォルムチェンジ(weather: str, form: str):
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 5),
    )
    mon = battle.actives[0]
    assert mon.name == form


def test_てんきや_天候なしで通常フォルム():
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ポワルン"


def test_てんきや_天候変化で即座にフォルムチェンジ():
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ポワルン"
    battle.weather_manager.apply("はれ", 5)
    assert mon.name == "ポワルン(たいよう)"


@pytest.mark.parametrize(
    "move_name, stat",
    [
        ("たいあたり", "B"),
        ("ひのこ", "D"),
    ]
)
def test_てんねん_攻撃側は防御ランク補正を無視する(move_name, stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんねん", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.rank[stat] = 2
    ctx = AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_DEF_RANK_MODIFIER, ctx, 2.0)
    assert result == 1.0


@pytest.mark.parametrize(
    "move_name, stat",
    [
        ("たいあたり", "A"),
        ("ひのこ", "C"),
    ]
)
def test_てんねん_防御側はACランク無視(move_name, stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="てんねん")],
    )
    attacker, defender = battle.actives
    attacker.rank[stat] = 2
    ctx = AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_ATK_RANK_MODIFIER, ctx, 2)
    assert result == 1


@pytest.mark.parametrize(
    "chance_before, chance_after",
    [
        (0.3, 0.6),
        (0.7, 1.0),
    ]
)
def test_てんのめぐみ_追加効果確率が2倍になる(chance_before, chance_after):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんのめぐみ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    ctx = AttackContext(attacker=attacker, move=attacker.moves[0])
    assert chance_after == battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, chance_before)


def test_でんきにかえる_被弾でじゅうでん状態になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="でんきにかえる")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].has_volatile("じゅうでん")


def test_とうそうしん_同性で攻撃が1_25倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="とうそうしん", move_names=["たいあたり"], gender="♂")],
        team1=[Pokemon("カビゴン", gender="♂")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 5120


def test_とうそうしん_異性で攻撃が0_75倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="とうそうしん", move_names=["たいあたり"], gender="♂")],
        team1=[Pokemon("カビゴン", gender="♀")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 3072


def test_とびだすなかみ_KOされなければダメージなし():
    """とびだすなかみ: KOされなければ攻撃者へのダメージは発生しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ヤドン", ability_name="とびだすなかみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.roll_damage = lambda *_args, **_kwargs: 1
    t.run_move(battle, 0)
    assert not defender.fainted
    assert attacker.hp == attacker.max_hp


def test_とびだすなかみ_KOされると攻撃者に反撃ダメージを与える():
    """とびだすなかみ: 攻撃技でひんしにされたとき攻撃者に反撃ダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("コイル", ability_name="とびだすなかみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    hp_before = defender.hp
    # ダメージを確定KOに設定
    battle.roll_damage = lambda *_args, **_kwargs: 9999
    t.run_move(battle, 0)
    assert defender.fainted
    # 反撃ダメージ = KO直前のHP
    assert attacker.hp == attacker.max_hp - hp_before


def test_とびだすなかみ_多段技では最初のヒット前HPが基準():
    """とびだすなかみ: 多段技でも ON_BEGIN_MOVE 時に保存した HP が反撃ダメージ基準になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ダブルアタック"])],
        team1=[Pokemon("コイル", ability_name="とびだすなかみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    hp_before = defender.hp
    # 2ヒット目でKOするよう設定（1ヒット目では残る）
    hit_count = [0]

    def controlled_damage(*_args, **_kwargs):
        hit_count[0] += 1
        return hp_before // 2 + 5 if hit_count[0] == 1 else 9999
    battle.roll_damage = controlled_damage
    t.run_move(battle, 0)
    assert defender.fainted
    # 反撃ダメージは最初のヒット前の HP が基準
    assert attacker.hp == attacker.max_hp - hp_before


def test_とびだすハバネロ_ほのおタイプの攻撃者はやけどにならない():
    """とびだすハバネロ: ほのおタイプの攻撃者にはやけどが入らない。"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすハバネロ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert not attacker.has_ailment("やけど")


def test_とびだすハバネロ_攻撃を受けた後に攻撃者がやけどになる():
    """とびだすハバネロ: 攻撃技のダメージを受けた後、攻撃者をやけど状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすハバネロ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_ailment("やけど")


def test_とびだすハバネロ_特殊攻撃でもやけどになる():
    """とびだすハバネロ: 直接攻撃に限らず特殊技でもやけどが適用される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすハバネロ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_ailment("やけど")


def test_とれないにおい_接触技で攻撃したら攻撃者の特性がとれないにおいになる():
    """とれないにおい: 接触技でダメージを与えた攻撃者の特性がとれないにおいに書き換わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="とれないにおい")],
        accuracy=100,
    )
    attacker, _ = battle.actives
    assert attacker.ability.name != "とれないにおい"
    t.run_move(battle, 0)
    assert attacker.ability.name == "とれないにおい"


def test_とれないにおい_非接触技では変わらない():
    """とれないにおい: 非接触技では攻撃者の特性が書き換わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", ability_name="とれないにおい")],
        accuracy=100,
    )
    attacker, _ = battle.actives
    original_ability = attacker.ability.name
    t.run_move(battle, 0)
    assert attacker.ability.name == original_ability, "非接触技では特性が変わらないはず"


def test_トレース_uncopyable特性だと不発():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="トレース")],
        team1=[Pokemon("ピカチュウ", ability_name="トレース")],
    )
    assert battle.actives[0].ability.base_name == "トレース"
    assert battle.actives[0].ability.revealed is False  # 不発なので False のまま


def test_トレース_いかくをコピーすると即発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="トレース")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].ability.base_name == "いかく"
    assert battle.actives[1].rank["A"] == -1


def test_トレース_交代で元の特性に戻り再入場で再コピーする():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="トレース"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("ピカチュウ", ability_name="すなかき")],
    )

    tracer = battle.player_states[battle.players[0]].team[0]
    assert tracer.ability.base_name == "すなかき"

    t.run_switch(battle, 0, 1)
    assert tracer.ability.base_name == "トレース"

    t.run_switch(battle, 0, 0)
    assert tracer.ability.base_name == "すなかき"


def test_どくくぐつ_どく付与時にこんらんになる():
    """どくくぐつ: どく付与と同時に相手がこんらんになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくくぐつ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, "どく", source=attacker)

    assert defender.ailment.name == "どく"
    assert defender.has_volatile("こんらん")


def test_どくくぐつ_まひ付与ではこんらんにならない():
    """どくくぐつ: まひ付与ではこんらんにならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくくぐつ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, "まひ", source=attacker)

    assert defender.ailment.name == "まひ"
    assert not defender.has_volatile("こんらん")


def test_どくくぐつ_もうどく付与時もこんらんになる():
    """どくくぐつ: もうどく付与でもこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくくぐつ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, "もうどく", source=attacker)

    assert defender.ailment.name == "もうどく"
    assert defender.has_volatile("こんらん")


def test_どくげしょう_1層から2層に増える():
    """どくげしょう: どくびし1層のとき被弾すると2層になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
        side1={"どくびし": 1},
    )
    t.run_move(battle, 1)
    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 2


def test_どくげしょう_2層でそれ以上設置されない():
    """どくげしょう: どくびしが2層のときは追加されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
        side1={"どくびし": 2},
    )
    t.run_move(battle, 1)
    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 2


def test_どくげしょう_物理技被弾で攻撃者側にどくびし1層():
    """どくげしょう: 物理技を受けると攻撃者の場にどくびしを1層設置する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 1


def test_どくげしょう_特殊技では発動しない():
    """どくげしょう: 特殊技を受けても発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 0


def test_どくしゅ_どく付与():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    _, defender = battle.actives

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.run_move(battle, 0)
    finally:
        battle.random.random = orig_random

    assert defender.has_ailment("どく")


def test_どくしゅ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("イーブイ", ability_name="どくしゅ", move_names=["はどうだん"])],
        team1=[Pokemon("ピカチュウ")],
    )
    _, defender = battle.actives

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.run_move(battle, 0)
    finally:
        battle.random.random = orig_random

    assert not defender.ailment.is_active


def test_どくのくさり_30パーセントでもうどくを付与する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.roll_damage = lambda *a, **k: 1
    battle.random.random = lambda: 0.29
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_どくのくさり_確率外ではもうどくにならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.roll_damage = lambda *a, **k: 1
    battle.random.random = lambda: 0.31
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_どくぼうそう_どく状態でない場合は倍率なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくぼうそう", move_names=["ねっとう"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_どくぼうそう_どく状態で特殊技の威力が1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくぼうそう", move_names=["ねっとう"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"どく": None},
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_どくぼうそう_物理技は倍率なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくぼうそう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"どく": None},
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ドラゴンスキン_ノーマル技がドラゴンタイプに変換されて威力1_2倍():
    """ドラゴンスキン: ノーマル技をドラゴンタイプに変換し威力を1.2倍にする。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ドラゴンスキン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    # 4096 * 4915/4096 = 4915 (1.2倍)
    assert battle.damage_calculator.power_modifier == 4915


def test_ドラゴンスキン_ノーマル技の実際のタイプがドラゴンになる():
    """ドラゴンスキン: 技のタイプがドラゴンに変換されている。"""
    from jpoke.enums import Event
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ドラゴンスキン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    result = battle.events.emit(
        Event.ON_MODIFY_MOVE_TYPE,
        EventContext(source=attacker, move=move),
        move.type,
    )
    assert result == "ドラゴン"


def test_ドラゴンスキン_非ノーマル技は威力補正なし():
    """ドラゴンスキン: 非ノーマル技には威力補正が適用されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ドラゴンスキン", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ナイトメア_ねむりでないとき発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン")],
    )
    foe = battle.actives[1]
    hp_before = foe.hp
    t.end_turn(battle)
    assert foe.hp == hp_before


def test_ナイトメア_ねむり中相手のHPを削る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン")],
    )
    foe = battle.actives[1]
    battle.ailment_manager.apply(foe, "ねむり")
    hp_before = foe.hp
    t.end_turn(battle)
    assert foe.hp < hp_before


def test_なまけ_1ターン行動して次のターンはさぼる():
    """なまけ: 1ターン行動すると次のターンは行動スキップになる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="なまけ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    # 初期状態: can_act
    assert attacker.ability.state == "can_act"
    hp_before = defender.hp
    # ターン1: 行動できる
    t.run_move(battle, 0)
    assert defender.hp < hp_before, "ターン1は行動できるはず"
    assert attacker.ability.state == "skip_next"


def test_なまけ_さぼった後は再び行動できる():
    """なまけ: さぼった次のターンは再び行動できる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="なまけ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    # T1: 行動
    t.run_move(battle, 0)
    # T2: さぼる
    t.run_move(battle, 0)
    # T3: 行動できる
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before, "さぼった後は再び行動できるはず"


def test_なまけ_さぼるターンはダメージを与えない():
    """なまけ: skip_next のターンは技を使えず、相手にダメージが入らない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="なまけ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    # ターン1: 行動
    t.run_move(battle, 0)
    # ターン2: さぼる
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before, "さぼるターンはダメージが入らないはず"
    assert attacker.ability.state == "can_act"


def test_ぬめぬめ_直接攻撃で攻撃者のSが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぬめぬめ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["S"] == -1


def test_ぬめぬめ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぬめぬめ")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["S"] == 0


def test_ねつこうかん_ほのお技を受けるとこうげき1段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert defender.rank["A"] == 1
    assert defender.ability.revealed


def test_ねつこうかん_やけど状態にならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    battle.ailment_manager.apply(target, "やけど")
    assert not target.ailment.is_active


def test_ねつぼうそう_やけど状態でない場合は倍率なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつぼうそう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ねつぼうそう_やけど状態で物理技の威力が1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつぼうそう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"やけど": None},
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_ねつぼうそう_特殊技は倍率なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつぼうそう", move_names=["ねっとう"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"やけど": None},
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ねんちゃく_相手による道具変更をブロックする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.can_change_item(source=source, target=target)


def test_ねんちゃく_自己起因の道具変更は阻害しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, _ = battle.actives
    assert battle.can_change_item(target, target)


def test_ねんちゃく_道具なしでも相手による道具変更をブロックする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.can_change_item(source=source, target=target)


def test_のろわれボディ_接触攻撃30パーセントでかなしばり():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="のろわれボディ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    battle.roll_damage = lambda *a, **k: 1
    battle.random.random = lambda: 0.29
    t.run_move(battle, 1)
    assert battle.actives[1].has_volatile("かなしばり")


def test_のろわれボディ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="のろわれボディ")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    battle.roll_damage = lambda *a, **k: 1
    battle.random.random = lambda: 0.29
    t.run_move(battle, 1)
    assert not battle.actives[1].has_volatile("かなしばり")


def test_ノーガード_攻撃側で必中化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーガード", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")]
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


def test_ノーガード_防御側で必中化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーガード")]
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


def test_ノーマルスキン_ノーマルタイプに変えた技は強化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    result = battle.move_executor.resolve_move_type(attacker, move)
    assert result == "ノーマル"

    ctx = AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_ノーマルスキン_元からノーマルタイプの技は威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    ctx = AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


def test_はっこう_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["ACC"] == -1


def test_はっこう_命中率上昇は適用される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.modify_stats(mon, {"ACC": +1}, source=battle.actives[1])
    assert mon.rank["ACC"] == 1


def test_はっこう_命中率低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう")],
        team1=[Pokemon("カビゴン", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["ACC"] == 0


def test_ハドロンエンジン_エレキフィールド中に攻撃が1_33倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5461 == battle.damage_calculator.atk_modifier


def test_ハドロンエンジン_エレキフィールド以外では補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # バトル開始後にグラスフィールドで上書き
    battle.terrain_manager.apply("グラスフィールド", 5)
    assert battle.terrain.name == "グラスフィールド"
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "initial_terrain",
    ["グラスフィールド", "サイコフィールド", "ミストフィールド"],
)
def test_ハドロンエンジン_別フィールドをエレキフィールドで上書きする(initial_terrain: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ハドロンエンジン")],
        team1=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


def test_ハドロンエンジン_登場時にエレキフィールドを展開する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


def test_はやあし_まひ状態で素早さ低下を無視して1_5倍():
    # ピカチュウはでんきタイプでまひ免疫があるためカビゴン（ノーマル）を使用
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はやあし")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"まひ": None},
    )
    mon = battle.actives[0]
    base = mon.stats["S"]
    # まひによる1/2ペナルティを打ち消して1.5倍（*3）
    assert battle.calc_effective_speed(mon) == (base // 2) * 3


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "やけど", "ねむり", "こおり"],
)
def test_はやあし_状態異常で素早さ1_5倍(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやあし")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={ailment_name: None},
    )
    mon = battle.actives[0]
    base = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base * 3 // 2


def test_はやおき_ねむりカウンタが通常の2倍速で減る():
    """はやおき: ねむり状態のとき1ターンで2回カウントが減る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやおき", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment0={"ねむり": 4},  # カウント4で眠らせる
    )
    attacker, _ = battle.actives
    assert attacker.has_ailment("ねむり")
    count_before = attacker.ailment.count
    # 行動を試みる (はやおき + 通常のねむりtick = 2回消費)
    t.run_move(battle, 0)
    count_after = attacker.ailment.count
    # 2回消費でcount_before - 2になるはず
    assert count_after == count_before - 2, f"はやおきで2回消費: {count_before} → {count_after}"


def test_はやおき_ねむりでないときは通常通り():
    """はやおき: ねむり状態でないときは効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやおき", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 通常通りダメージが入るはず
    assert defender.hp < hp_before


def test_はやてのつばさ_HPが減ると優先度が上がらない():
    """はやてのつばさ: HP満タンでないときはひこう技の優先度は変わらない"""
    from jpoke.enums import DomainEvent
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやてのつばさ", move_names=["つばさでうつ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    # HPを1減らす
    battle.modify_hp(attacker, -1)
    assert attacker.hp < attacker.max_hp
    ctx = EventContext(source=attacker, move=attacker.moves[0])
    priority = battle.events.emit(DomainEvent.ON_MODIFY_MOVE_PRIORITY, ctx=ctx, value=0)
    assert priority == 0, "HP満タンでないときはひこう技の優先度は変わらないはず"


def test_はやてのつばさ_HP満タン時にひこう技の優先度が1上がる():
    """はやてのつばさ: HP満タン時にひこうタイプ技の優先度が+1される"""
    from jpoke.enums import DomainEvent
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやてのつばさ", move_names=["つばさでうつ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert attacker.hp == attacker.max_hp, "HP満タンであることを確認"
    ctx = EventContext(source=attacker, move=attacker.moves[0])
    priority = battle.events.emit(DomainEvent.ON_MODIFY_MOVE_PRIORITY, ctx=ctx, value=0)
    assert priority == 1, f"HP満タン時にひこう技の優先度が+1されるはず (got {priority})"


def test_はやてのつばさ_ひこう以外の技は優先度が上がらない():
    """はやてのつばさ: HP満タンでもひこうタイプ以外の技は優先度が変わらない"""
    from jpoke.enums import DomainEvent
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやてのつばさ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert attacker.hp == attacker.max_hp
    ctx = EventContext(source=attacker, move=attacker.moves[0])
    priority = battle.events.emit(DomainEvent.ON_MODIFY_MOVE_PRIORITY, ctx=ctx, value=0)
    assert priority == 0, "ひこう以外の技は優先度が変わらないはず"


def test_はらぺこスイッチ_ターン終了時にフォルムが交互に切り替わる():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability.is_hangry is False

    battle.advance_turn()
    assert mon.ability.is_hangry is True

    battle.advance_turn()
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル中はターン終了時に切り替わらない():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ", tera_type="あく")],
        team1=[Pokemon("ピカチュウ", move_names=["はねる"])],
    )
    mon = battle.actives[0]

    t.reserve_command(battle,
                      command0=Command.TERASTAL_0,
                      command1=Command.MOVE_0)
    battle.advance_turn()

    assert mon.terastallized is True
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル交代時はフォルム維持する():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ", tera_type="あく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    mon.ability.is_hangry = True
    mon.terastallize()
    t.run_switch(battle, 0, 1)

    assert mon.ability.is_hangry is True


def test_はらぺこスイッチ_交代時は通常まんぷくへ戻る():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    mon.ability.is_hangry = True
    t.run_switch(battle, 0, 1)

    assert mon.ability.is_hangry is False


def test_はりきり_一撃必殺技の命中率は下がらない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    # 命中率ペナルティがかからない
    assert battle.move_executor.accuracy == 30


def test_はりきり_物理技の攻撃補正が1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    move = attacker.moves[0]
    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=move),
        4096,
    )
    assert atk_modifier == 6144

    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100 * 3277 // 4096


def test_はりきり_特殊技には補正がかからない():
    """はりきり特性: 特殊技には攻撃補正と命中率補正がかからない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    move = attacker.moves[0]
    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=move),
        4096,
    )
    assert atk_modifier == 4096

    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100


def test_はりこみ_交代直後の相手への攻撃強化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりこみ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender_player = battle.get_player(defender)
    battle.player_states[defender_player].has_switched = True

    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert atk_modifier == 8192


def test_ハードロック_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="ハードロック")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_ハードロック_効果抜群ダメージを0_75倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="ハードロック")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


def test_ばけのかわ_2回目以降の攻撃は防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
    )
    _, defender = battle.actives

    # ダメージ計算結果を固定
    battle.roll_damage = lambda attacker, defender, move, critical=False: 30

    # 1回目
    t.run_move(battle, 0)
    assert defender.ability.enabled is False
    assert defender.hp == defender.max_hp - defender.max_hp // 8

    # 2回目
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before - 30


def test_ばけのかわ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ミミッキュ", ability_name="ばけのかわ")],
    )
    assert battle.actives[1].ability.enabled


def test_ばけのかわ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
    )
    _, defender = battle.actives
    battle.roll_damage = (
        lambda attacker, defender, move, critical=False: 10
    )

    t.run_move(battle, 0)

    assert defender.ability.enabled is True
    assert defender.hp == defender.max_hp - 10


def test_ばけのかわ_交代しても再有効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ"), Pokemon("ピカチュウ")],
    )
    # 初回被弾でばけのかわを消費
    t.run_move(battle, 0)
    assert battle.actives[1].ability.enabled is False

    # 交代して戻っても per_battle_once 特性は再有効化されない
    t.run_switch(battle, 1, 1)
    t.run_switch(battle, 1, 0)
    assert battle.actives[1].ability.enabled is False


def test_ばけのかわ_連続技の2発目以降は防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にどげり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
    )
    _, defender = battle.actives
    before_hp = defender.hp

    battle.roll_damage = (
        lambda attacker, defender, move, critical=False: 10
    )
    t.run_move(battle, 0)

    assert defender.ability.enabled is False
    assert defender.hp == before_hp - defender.max_hp // 8 - 10


def test_バトルスイッチ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ")],
    )
    assert battle.actives[1].ability.enabled


def test_バトルスイッチ_シールドで変化技なら変化しない():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["つるぎのまい"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ギルガルド(シールド)"


def test_バトルスイッチ_シールドで攻撃技を使うとブレードへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == "ギルガルド(ブレード)"


def test_バトルスイッチ_ブレードでキングシールドを使うとシールドへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability_name="バトルスイッチ", move_names=["キングシールド"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == "ギルガルド(シールド)"


def test_バトルスイッチ_ブレードでまもるなら変化しない():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability_name="バトルスイッチ", move_names=["まもる"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ギルガルド(ブレード)"


def test_バトルスイッチ_交代時はシールドへ戻る():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability_name="バトルスイッチ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_switch(battle, 0, 1)
    assert battle.player_states[battle.players[0]].team[0].name == "ギルガルド(シールド)"


def test_バリアフリー_入場で相手のリフレクターを解除():
    """バリアフリー: 入場時に相手のリフレクターを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="バリアフリー")],
        team1=[Pokemon("フシギダネ")],
        side1={"リフレクター": 5},
    )
    t.run_switch(battle, 0, 1)
    foe_side = battle.get_side(battle.players[1])
    assert not foe_side.get("リフレクター").is_active


def test_バリアフリー_入場で自分側のひかりのかべを解除():
    """バリアフリー: 入場時に自分側のひかりのかべも解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="バリアフリー")],
        team1=[Pokemon("フシギダネ")],
        side0={"ひかりのかべ": 5},
    )
    t.run_switch(battle, 0, 1)
    own_side = battle.get_side(battle.players[0])
    assert not own_side.get("ひかりのかべ").is_active


def test_バリアフリー_壁がない場合アナウンスなし():
    """バリアフリー: 壁がない場合は特性発動アナウンスが出ない。"""
    from jpoke.enums import LogCode
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="バリアフリー")],
        team1=[Pokemon("フシギダネ")],
    )
    t.run_switch(battle, 0, 1)
    logs = battle.get_event_logs()
    all_logs = [log for logs_per_player in logs.values() for log in logs_per_player]
    assert not any(log.log == LogCode.ABILITY_TRIGGERED for log in all_logs)


def test_ばんけん_いかくでAが下がった後に上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばんけん")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == 0


def test_ばんけん_ほえるを無効化する():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="ばんけん"),
            Pokemon("イーブイ"),
        ],
        team1=[Pokemon("カビゴン", move_names=["ほえる"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].name == "ピカチュウ"


@pytest.mark.parametrize(
    "ability_name, setup_kwargs, expected_source, keep_item_before_release",
    [
        ("クォークチャージ", {}, "item", False),
        ("こだいかっせい", {"weather": ("はれ", 5)}, "field", True),
        ("クォークチャージ", {"terrain": ("エレキフィールド", 5)}, "field", True),
    ],
)
def test_パラドックス特性_ブーストエナジーと場条件の優先関係(
    ability_name: str,
    setup_kwargs: dict,
    expected_source: str,
    keep_item_before_release: bool,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ", ability_name="ひでり" if setup_kwargs.get("weather") else "エレキメイカー" if setup_kwargs.get("terrain") else "")],
        **setup_kwargs,
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_source == expected_source
    assert mon.paradox_boost_active
    assert mon.has_item("ブーストエナジー") is keep_item_before_release

    if expected_source == "field":
        if setup_kwargs.get("weather"):
            battle.weather_manager.remove()
        else:
            battle.terrain_manager.remove()
        assert mon.paradox_boost_active
        assert mon.paradox_boost_source == "item"
        assert not mon.has_item("ブーストエナジー")


def test_パンクロック_かたやぶりで音技軽減が無効化される():
    """パンクロック: かたやぶり持ちの音技はパンクロックの被ダメ軽減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability_name="パンクロック")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_パンクロック_音技で威力1_3倍かつ被ダメ0_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="パンクロック", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier

    battle2 = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability_name="パンクロック", move_names=["バークアウト"])],
    )
    t.run_move(battle2, 0)
    assert 2048 == battle2.damage_calculator.damage_modifier


@pytest.mark.parametrize("ailment_name", ["どく", "もうどく"])
def test_ひとでなし_どく系状態の相手には急所ランク最大になる(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひとでなし", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, ailment_name, source=attacker)

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank >= 3


def test_ひとでなし_非どく状態の相手には急所ランクを変更しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひとでなし", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank == 0


def test_ひひいろのこどう_はれ中に攻撃が1_33倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5461 == battle.damage_calculator.atk_modifier


def test_ひひいろのこどう_はれ以外では補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # バトル開始後にあめで上書き
    battle.weather_manager.apply("あめ", 5)
    assert battle.weather.name == "あめ"
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "initial_weather", strong_weathers
)
def test_ひひいろのこどう_強天候は上書き不可(initial_weather: Weather):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ひひいろのこどう")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == initial_weather


def test_ひひいろのこどう_登場時にはれを展開する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == "はれ"
    assert battle.weather.count == 5
    assert battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "initial_weather", ["あめ", "すなあらし", "ゆき"]
)
def test_ひひいろのこどう_通常天候をはれで上書きする(initial_weather: Weather):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ひひいろのこどう")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "はれ"


def test_ヒーリングシフト_回復技の優先度が3上がる():
    """ヒーリングシフト: 回復技の優先度が+3される"""
    from jpoke.enums import DomainEvent
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ヒーリングシフト", move_names=["なまける"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    ctx = EventContext(source=attacker, move=attacker.moves[0])
    priority = battle.events.emit(DomainEvent.ON_MODIFY_MOVE_PRIORITY, ctx=ctx, value=0)
    assert priority == 3, f"ヒーリングシフトで回復技の優先度が+3されるはず (got {priority})"


def test_ヒーリングシフト_通常技は優先度が変わらない():
    """ヒーリングシフト: 攻撃技の優先度は変わらない"""
    from jpoke.enums import DomainEvent
    from jpoke.core import AttackContext, EventContext
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ヒーリングシフト", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    ctx = EventContext(source=attacker, move=attacker.moves[0])
    priority = battle.events.emit(DomainEvent.ON_MODIFY_MOVE_PRIORITY, ctx=ctx, value=0)
    assert priority == 0, "攻撃技の優先度は変わらないはず"


def test_ビビッドボディ_かたやぶりで無効化される():
    """ビビッドボディ: かたやぶり持ちには先制技が通る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", ability_name="ビビッドボディ")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_ビビッドボディ_優先度ゼロの技は通る():
    """ビビッドボディ: 優先度0の技は通常通り当たる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ビビッドボディ")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_ビビッドボディ_優先度プラスの技を無効化する():
    """ビビッドボディ: 優先度+1の技を無効化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", ability_name="ビビッドボディ")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    assert defender.hp == defender.max_hp


def test_びびり_あく技でSが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり")],
        team1=[Pokemon("カビゴン", move_names=["かみつく"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["S"] == 1


def test_びびり_ゴースト技でSが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり")],
        team1=[Pokemon("カビゴン", move_names=["したでなめる"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["S"] == 1


def test_びびり_他タイプでは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["S"] == 0


def test_びんじょう_ランク低下はコピーしない():
    """びんじょう: 相手のランク低下はコピーしない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives
    # 相手のAランクを下げる
    battle.modify_stats(foe, {"A": -2}, source=foe)
    assert foe.rank["A"] == -2
    # びんじょうはランク低下に反応しないはず
    assert binjou_mon.rank["A"] == 0, "びんじょうはランク低下をコピーしないはず"


def test_びんじょう_相手のランク上昇を自分もコピーする():
    """びんじょう: 相手のランクが上昇したとき自分も同じランク上昇をする"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives
    assert binjou_mon.rank["A"] == 0
    # 相手のAランクを上げる
    battle.modify_stats(foe, {"A": 2}, source=foe)
    assert foe.rank["A"] == 2
    # びんじょうで自分も+2されるはず
    assert binjou_mon.rank["A"] == 2, "びんじょうで相手のランク上昇をコピーするはず"


def test_ビーストブースト_倒すと最高実数値の能力が上がる():
    """ビーストブースト: 攻撃技で倒すと最高実数値の能力が1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ビーストブースト", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.roll_damage = lambda *a, **k: 9999

    t.run_move(battle, 0)

    best_stat = max(("A", "B", "C", "D", "S"), key=lambda s: attacker.stats[s])
    assert attacker.rank[best_stat] == 1


def test_ビーストブースト_同値はA優先():
    """ビーストブースト: 全実数値が同値のときはA優先でA↑1。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ビーストブースト", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # 全ステータスを同値に設定（_statsリストを直接書き換え: [HP, A, B, C, D, S]）
    for i in range(1, 6):
        attacker._stats_manager._stats[i] = 100
    battle.roll_damage = lambda *a, **k: 9999

    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["B"] == 0


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("しんりょく", "エナジーボール"),
        ("もうか", "ひのこ"),
        ("げきりゅう", "なみのり"),
        ("むしのしらせ", "むしのていこう"),
    ],
)
def test_ピンチ系特性_HP1_3以下で攻撃補正1_5倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.atk_modifier


def test_ファントムガード_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ファントムガード")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_ファーコート_かたやぶりで無効():
    """ファーコート: かたやぶり持ちの物理技はファーコートの防御補正を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ファーコート")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


def test_ファーコート_物理技の防御が2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ファーコート")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 8192


def test_ふうりょくでんき_味方のおいかぜ発生でじゅうでん状態になる():
    """ふうりょくでんき: 味方サイドにおいかぜが発生したらじゅうでん状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
    )
    _, defender = battle.actives
    # 味方サイド（player1側）においかぜを発生させる
    battle.side_managers[1].activate("おいかぜ", 4)
    assert defender.has_volatile("じゅうでん")


def test_ふうりょくでんき_相手のおいかぜには反応しない():
    """ふうりょくでんき: 相手サイドのおいかぜには反応しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
    )
    _, defender = battle.actives
    # 相手サイド（player0側）においかぜを発生させる
    battle.side_managers[0].activate("おいかぜ", 4)
    assert not defender.has_volatile("じゅうでん")


def test_ふうりょくでんき_風ラベルなし技を受けてもじゅうでんにならない():
    """ふうりょくでんき: 風ラベルのない技を受けてもじゅうでん状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_volatile("じゅうでん")


def test_ふうりょくでんき_風技を受けるとじゅうでん状態になる():
    """ふうりょくでんき: 風ラベルを持つ技のダメージを受けたらじゅうでん状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はなふぶき"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.has_volatile("じゅうでん")


def test_フェアリーオーラ_オーラブレイクがいるとフェアリー技の威力が0_75倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリーオーラ", move_names=["じゃれつく"])],
        team1=[Pokemon("ピカチュウ", ability_name="オーラブレイク")],
    )
    attacker, defender = battle.actives
    result = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert result == 3072


def test_フェアリーオーラ_フェアリー技の威力が1_33倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリーオーラ", move_names=["じゃれつく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    result = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert result == 5448


def test_フェアリーオーラ_相手のフェアリー技にも0_75倍が適用される():
    """フェアリーオーラ側が防御時にもオーラブレイクによる反転が適用される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリーオーラ")],
        team1=[Pokemon("ピカチュウ", ability_name="オーラブレイク", move_names=["じゃれつく"])],
    )
    attacker, defender = battle.actives[1], battle.actives[0]
    result = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        AttackContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert result == 3072


def test_ふかしのこぶし_まもる貫通後も揮発性状態が残る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふかしのこぶし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "まもる", count=1)
    t.run_move(battle, 0)
    assert defender.has_volatile("まもる")


def test_ふかしのこぶし_まもる貫通時のダメージが4分の1():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふかしのこぶし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.protect_modifier == 1024


@pytest.mark.parametrize("volatile_name", [
    "まもる", "トーチカ", "キングシールド", "スレッドトラップ", "かえんのまもり"
])
def test_ふかしのこぶし_接触技でまもる系揮発性状態を貫通してHPを減らす(volatile_name):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふかしのこぶし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, volatile_name, count=1)
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_ふかしのこぶし_非接触技はまもるに防がれる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふかしのこぶし", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_ふくがん_一撃必殺技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくがん", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 30


def test_ふくがん_命中率を1_3倍にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくがん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100 * 5325 // 4096


def test_ふくつのこころ_ひるみ時にSが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくつのこころ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "ひるみ")
    assert mon.rank["S"] == 1


def test_ふくつのこころ_他のvolatileでは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくつのこころ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こんらん")
    assert mon.rank["S"] == 0


def test_ふくつのたて_2回目入場では発動しない():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="ふくつのたて"),
            Pokemon("イーブイ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.actives[0].rank["B"] == 1
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert battle.actives[0].rank["B"] == 0


def test_ふくつのたて_初回入場でBが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくつのたて")],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.actives[0].rank["B"] == 1


def test_ふしぎなうろこ_かたやぶりで無効():
    """ふしぎなうろこ: かたやぶり持ちの物理技はふしぎなうろこの防御補正を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふしぎなうろこ")],
        ailment1={"やけど": None},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_ふしぎなうろこ_状態異常でB上昇(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("コラッタ", ability_name="ふしぎなうろこ")],
        ailment1={ailment_name: None},
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_ふしぎなまもり_いまひとつ技も無効化される():
    """ふしぎなまもり: いまひとつ（半減）の攻撃技も無効化される。"""
    # ピジョット(ひこう/ノーマル)にくさ技は等倍、いわ技は半減
    # くさ -> ひこう: 半減, ノーマル: 等倍 => 0.5倍 = いまひとつ
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["タネマシンガン"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp


def test_ふしぎなまもり_かたやぶりで無効化される():
    """ふしぎなまもり: かたやぶり持ちの攻撃者には無効化が貫通される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_ふしぎなまもり_効果抜群でない技は無効化される():
    """ふしぎなまもり: 等倍の攻撃技を受けてもダメージを受けない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp


def test_ふしぎなまもり_効果抜群の技は通る():
    """ふしぎなまもり: 効果抜群の攻撃技はダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_ふしぎなまもり_変化技は通る():
    """ふしぎなまもり: 変化技はダメージ無関係なので通る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    # なきごえは通る（こうげきが下がる）
    assert defender.rank["A"] == -1


@pytest.mark.parametrize(
    "target_name",
    ["フシギダネ", "コイル"],  # くさ/どくタイプ、でんき/はがねタイプ
)
def test_ふしょく持ち由来ならどく免疫タイプにもどくが入る(target_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふしょく")],
        team1=[Pokemon(target_name)],
    )
    source = battle.actives[0]
    target = battle.actives[1]

    assert battle.ailment_manager.apply(target, "どく", source=source)
    assert target.ailment.name == "どく"


def test_ふとうのけん_初回入場でAが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふとうのけん")],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.actives[0].rank["A"] == 1


def test_ふゆう_floating():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]
    floating = battle.events.emit(
        Event.ON_CHECK_FLOATING,
        EventContext(source=mon),
        False
    )
    assert floating is True


def test_ふゆう_かたやぶりでじめん技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp


def test_ふゆう_じめん技が通らない():
    """ふゆう: ふゆう持ちはじめん技を無効化できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp


def test_フラワーギフト_晴れ中攻撃が1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("チェリム", ability_name="フラワーギフト", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_フラワーギフト_雨中では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("チェリム", ability_name="フラワーギフト", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_フラワーベール_くさタイプでないと保護しない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="フラワーベール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert "くさ" not in mon.types
    battle.ailment_manager.apply(mon, "ねむり")
    assert mon.ailment.is_active


def test_フラワーベール_くさタイプへの状態異常を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="フラワーベール")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    assert "くさ" in mon.types
    result = battle.ailment_manager.apply(mon, "まひ")
    assert not result
    assert not mon.ailment.is_active


def test_ぶきよう_アイテムが無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぶきよう", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not mon.item.enabled

    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_ブレインフォース_効果抜群のとき強化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ブレインフォース", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ")],
    )
    t.run_move(battle, 0)
    assert 5120 == battle.damage_calculator.damage_modifier


def test_プリズムアーマー_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="プリズムアーマー")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


def test_プレッシャー_場に出たときに開示される():
    """プレッシャー: 場に出たときABILITY_TRIGGEREDログが記録される"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="プレッシャー")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed


def test_プレッシャー_相手の技のPP消費が1増える():
    """プレッシャー: プレッシャー持ちを対象にした技のPP消費が通常+1になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
        accuracy=100,
    )
    attacker, _ = battle.actives
    move = attacker.moves[0]
    pp_before = move.pp
    t.run_move(battle, 0)
    pp_consumed = pp_before - move.pp
    assert pp_consumed == 2, f"プレッシャーでPP消費が2になるはず (got {pp_consumed})"


def test_ヘドロえき_回復がダメージになる():
    """ヘドロえき: ドレイン回収(drain)でヘドロえき所持者が吸収される際、
    回復する側の回復量だけ逆にダメージを受ける"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン", ability_name="ヘドロえき")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.hp < attacker.max_hp
    assert defender.hp < defender.max_hp


def test_ヘドロえき_通常の回復には影響しない():
    """ヘドロえき: drain以外の理由の回復には影響しない"""
    # TODO : 技じこさいせい実装後にテストする


def test_へんげんじざい_交代でリセットされ再発動できる():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="へんげんじざい", move_names=["たいあたり", "ひのこ"]),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert mon.types == ["ノーマル"]

    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    t.run_move(battle, 0, 1)

    assert mon.types == ["ほのお"]


def test_へんげんじざい_同一滞在で1回のみ発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="へんげんじざい", move_names=["たいあたり", "ひのこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert attacker.types == ["ノーマル"]

    t.run_move(battle, 0, 1)
    assert attacker.types == ["ノーマル"]


def test_へんしょく_ひんし状態では発動しない():
    """へんしょく: KOされた場合はタイプ変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ", ability_name="へんしょく")],
        accuracy=100,
    )
    _, defender = battle.actives
    original_types = list(defender.types)
    battle.roll_damage = lambda *_args, **_kwargs: 9999
    t.run_move(battle, 0)
    assert defender.fainted
    assert defender.types == original_types


def test_へんしょく_多段技では最終ヒット後にタイプ変化する():
    """へんしょく: 多段技の最終ヒット後にのみタイプが変化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ダブルアタック"])],
        team1=[Pokemon("ヤドン", ability_name="へんしょく")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    # ダブルアタックはノーマルタイプ
    assert "ノーマル" in defender.types


def test_へんしょく_攻撃技を受けた後に技タイプになる():
    """へんしょく: 攻撃技のダメージを受けた後、その技のタイプに変化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ", ability_name="へんしょく")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert "みず" in defender.types


def test_へんしょく_既に同タイプなら発動しない():
    """へんしょく: 既に技と同じタイプを持つ場合はタイプ変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ", ability_name="へんしょく")],
        accuracy=100,
    )
    _, defender = battle.actives
    # ピカチュウはでんきタイプなので10まんボルト後もでんきのまま
    t.run_move(battle, 0)
    assert defender.types == ["でんき"]


def test_ヘヴィメタル_体重が2倍になる():
    """ヘヴィメタル: ポケモンの体重が基本値の2倍になる。"""
    mon = Pokemon("ピカチュウ", ability_name="ヘヴィメタル")
    base_weight = mon.data.weight
    assert mon.weight == base_weight * 2


def test_ほうし_接触技でどく付与():
    """ほうし: 接触技を受けたとき、乱数がどく範囲(0.09未満)ならどく付与。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほうし")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    battle.random.random = lambda: 0.0

    t.run_move(battle, 1)

    assert battle.actives[1].ailment.name == "どく"


def test_ほうし_接触技でまひ付与():
    """ほうし: 乱数がまひ範囲(0.09以上0.19未満)ならまひ付与。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほうし")],
        team1=[Pokemon("フシギダネ", move_names=["たいあたり"])],
        accuracy=100,
    )
    battle.random.random = lambda: 0.09

    t.run_move(battle, 1)

    assert battle.actives[1].ailment.name == "まひ"


def test_ほうし_非接触技では発動しない():
    """ほうし: 非接触技を受けても発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほうし")],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        accuracy=100,
    )
    battle.random.random = lambda: 0.0

    t.run_move(battle, 1)

    assert not battle.actives[1].ailment.is_active


def test_ほろびのボディ_すでにほろびのうた状態なら追加しない():
    """ほろびのボディ: 既にほろびのうた状態のときは追加されない（重複なし）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほろびのボディ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    battle.volatile_manager.apply(attacker, "ほろびのうた", source=defender)

    t.run_move(battle, 1)

    assert attacker.has_volatile("ほろびのうた")
    assert defender.has_volatile("ほろびのうた")


def test_ほろびのボディ_接触技で双方ほろびのうた():
    """ほろびのボディ: 直接攻撃を受けると自分と攻撃者の双方がほろびのうた状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほろびのボディ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)

    assert defender.has_volatile("ほろびのうた")
    assert attacker.has_volatile("ほろびのうた")


def test_ほろびのボディ_非接触技では発動しない():
    """ほろびのボディ: 非接触技を受けても発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほろびのボディ")],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)

    assert not defender.has_volatile("ほろびのうた")
    assert not attacker.has_volatile("ほろびのうた")


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("ぼうおん", "バークアウト"),
        ("ぼうだん", "かえんボール"),
    ],
)
def test_ぼうおん系_かたやぶりで無効(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move_name])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp
    assert defender.ability.revealed is False


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("ぼうおん", "バークアウト"),
        ("ぼうだん", "かえんボール"),
    ],
)
def test_ぼうおん系_技を無効化する(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", move_names=[move_name])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp
    assert defender.ability.revealed is True


def test_ぼうじん_粉技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぼうじん")],
        team1=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert not defender.ailment.is_active
    assert defender.ability.revealed is True


def test_ポイズンヒール_かいふくふうじ中は回復もダメージも受けない():
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability_name="ポイズンヒール")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={"どく": None},
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かいふくふうじ")
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))
    assert mon.hp == before


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく"]
)
def test_ポイズンヒール_どく系状態で1_8回復する(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability_name="ポイズンヒール")],
        team1=[Pokemon("ピカチュウ")],
        ailment0={ailment_name: None},
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    t.end_turn(battle)
    assert mon.hp == before + mon.max_hp // 8


def test_マイティチェンジ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ")],
    )
    assert battle.actives[1].ability.enabled


def test_マイティチェンジ_ナイーブで交代するとマイティへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "イルカマン(マイティ)"


def test_まけんき_相手からの能力低下でAが2段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="まけんき")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == 1


def test_まけんき_自分由来では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="まけんき")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.modify_stats(mon, {"A": -1}, source=mon)
    assert mon.rank["A"] == -1
    assert mon.rank["C"] == 0


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


@pytest.mark.parametrize(
    "reason, result",
    [
        ("move_damage", True),
        ("self_attack", True),
        ("pain_split", True),
        ("self_cost", True),
        ("", False),
    ],
)
def test_マジックガード_HPChangeReasonごとの挙動(reason: str, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    delta = battle.modify_hp(mon, v=-10, reason=reason)
    assert bool(delta) == result


def test_マジックミラー_変化技を跳ね返す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.rank["A"] == -1
    assert defender.rank["A"] == 0


def test_マルチスケイル_HP満タンのとき半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="マルチスケイル")],
    )
    attacker, defender = battle.actives

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
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_マルチタイプ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("アルセウス", ability_name="マルチタイプ")],
    )
    assert battle.actives[1].ability.enabled


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
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ", item_name="せいれいプレート")],
        team1=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    # ON_CHECK_ITEM_CHANGE: target=アルセウス, source=ピカチュウ → 奪取を阻止
    ctx = AttackContext(attacker=attacker, defender=mon, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CHECK_ITEM_CHANGE, ctx, True)
    assert result is False


def test_ミイラ_接触技で攻撃した相手の特性がミイラになる():
    """ミイラ: 直接攻撃でダメージを受けたとき攻撃者の特性をミイラにする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ミイラ")],
        accuracy=100,
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


def test_みずがため_みず技でBが2段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="みずがため")],
        team1=[Pokemon("カビゴン", move_names=["バブルこうせん"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["B"] == 2


def test_みずがため_他タイプでは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="みずがため")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["B"] == 0


def test_ミラクルスキン_変化技の命中率を50パーセントに固定する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラクルスキン")],
        team1=[Pokemon("カビゴン", move_names=["どくどく"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 50


def test_ミラクルスキン_攻撃技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラクルスキン")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 100


def test_ミラーアーマー_かたやぶりで反射されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[1].rank["A"] == 0


def test_ミラーアーマー_反射により相手のかちきが発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かちき")],
    )
    ally, foe = battle.actives
    battle.modify_stats(ally, {"A": -1}, source=foe)
    assert ally.rank["A"] == 0
    assert foe.rank["A"] == -1
    assert foe.rank["C"] == 2


def test_ミラーアーマー_能力低下のみ反射する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ")],
    )
    ally, foe = battle.actives
    stats = {"A": -1, "B": +1, "C": -2}
    battle.modify_stats(ally, stats, source=foe)
    assert ally.rank["A"] == 0
    assert ally.rank["B"] == 1
    assert ally.rank["C"] == 0
    assert foe.rank["A"] == -1
    assert foe.rank["B"] == 0
    assert foe.rank["C"] == -2


def test_ミラーアーマー_自己能力低下は反射しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
    )
    target, source = battle.actives
    battle.modify_stats(target, {"A": -1}, source=target)
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[1].rank["A"] == 0


def test_ムラっけ_ターン終了時に別々の能力が上昇と下降する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    choices = iter(["A", "B"])
    battle.random.choice = lambda seq: next(choices)

    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))

    assert mon.rank["A"] == 2
    assert mon.rank["B"] == -1


def test_ムラっけ_全能力が最大なら下降のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("A", "B", "C", "D", "S"):
        mon.rank[stat] = 6
    battle.random.choice = lambda seq: seq[0]

    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))

    assert mon.rank["A"] == 5
    assert mon.rank["B"] == 6


def test_ムラっけ_全能力が最小なら上昇のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("A", "B", "C", "D", "S"):
        mon.rank[stat] = -6
    battle.random.choice = lambda seq: seq[0]

    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))

    assert mon.rank["A"] == -4
    assert mon.rank["B"] == -6


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
    assert battle.actives[0].rank["A"] == 0


def test_メロメロボディ_接触攻撃30パーセントでメロメロ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メロメロボディ", gender="♀")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"], gender="♂")],
    )
    battle.roll_damage = lambda *a, **k: 1
    battle.random.random = lambda: 0.29
    t.run_move(battle, 1)
    assert battle.actives[1].has_volatile("メロメロ")


def test_ものひろい_相手がアイテムを消費していない場合は拾わない():
    """ものひろい: 相手がアイテムを消費していない場合は何も起きない"""

    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ")],
    )
    pickup_mon, _ = battle.actives
    t.end_turn(battle)
    assert not pickup_mon.has_item(), "相手がアイテムを消費していないときは何も拾わないはず"


def test_ものひろい_相手が消費したアイテムをターン終了時に拾う():
    """ものひろい: ターン終了時に相手が消費したアイテムを自分が拾う"""

    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    assert not pickup_mon.has_item()
    # 相手のアイテムを消費させる
    battle.remove_item(foe)
    assert not foe.has_item()
    assert foe.last_lost_item_name == "オボンのみ"
    # ターン終了でものひろい発動
    t.end_turn(battle)
    assert pickup_mon.has_item("オボンのみ"), "ものひろいで相手のアイテムを拾うはず"


def test_ものひろい_自分がアイテムを持っているときは拾わない():
    """ものひろい: 自分がアイテムを持っているときは拾わない"""

    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    battle.remove_item(foe)
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


def test_ゆうばく_直接攻撃KO時に攻撃者に1_4ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    expected_damage = max(1, foe.max_hp // 4)
    assert foe.hp == foe.max_hp - expected_damage


def test_ゆうばく_非接触KOでは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.hp == foe.max_hp


def test_よちむ_場に出たとき相手の最高威力の技が公開される():
    """よちむ: 登場時に相手の技のうち最高威力の技が公開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よちむ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり", "10まんボルト"])],
    )
    _, foe = battle.actives
    assert foe.moves[1].revealed
    assert not foe.moves[0].revealed


def test_よちむ_変化技は威力0として扱われる():
    """よちむ: 変化技のみの場合は(威力0の技の中から)いずれかが公開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よちむ")],
        team1=[Pokemon("カビゴン", move_names=["つるぎのまい"])],
    )
    _, foe = battle.actives
    assert foe.moves[0].revealed


@pytest.mark.parametrize("move_name", ["でんきショック", "たいあたり"])
def test_よわき_HP半分以下で攻撃補正0_5倍(move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よわき", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier


def test_ライトメタル_体重が半分になる():
    """ライトメタル: ポケモンの体重が基本値の半分になる。"""
    mon = Pokemon("ピカチュウ", ability_name="ライトメタル")
    base_weight = mon.data.weight
    assert mon.weight == int(base_weight * 0.5 * 10) / 10


@pytest.mark.parametrize(
    "weather_name",
    weathers
)
def test_らんきりゅう_すべての天候を上書きする(weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="デルタストリーム")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "らんきりゅう"


def test_リミットシールド_HP1_2以下で登場してもコアの姿のまま():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    # ターン終了時に判定される（登場直後はまだりゅうせい）
    assert mon.name == "メテノ(りゅうせい)"


def test_リミットシールド_HP1_2超で登場するとりゅうせいのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"


def test_リミットシールド_コアのすがたでは状態異常になる():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "メテノ(コア)"
    assert t.apply_ailment(battle, 0, "まひ")


def test_リミットシールド_ターン終了時にHP1_2以下ならコアの姿になる():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "メテノ(コア)"


def test_リミットシールド_ターン終了時にHP1_2超ならりゅうせいのすがたを維持する():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    t.end_turn(battle)
    assert mon.name == "メテノ(りゅうせい)"


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_リミットシールド_りゅうせいのすがたで状態異常にならない(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    assert not t.apply_ailment(battle, 0, ailment_name)


def test_リミットシールド_交代するとコアの姿に戻る():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    t.run_switch(battle, 0, 1)
    assert mon.name == "メテノ(コア)"


def test_りんぷん_かたやぶりで無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_りんぷん_追加効果確率を0にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.is_active is False


@pytest.mark.parametrize("weather_name,weather_count", [("はれ", 5), ("おおひでり", 999)])
@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_リーフガード_はれおおひでり中に状態異常を防ぐ(weather_name: str, weather_count: int, ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, ailment_name)
    assert not mon.ailment.is_active


@pytest.mark.parametrize(
    "weather",
    [None, ("あめ", 5), ("すなあらし", 5), ("ゆき", 5)],
)
def test_リーフガード_はれ以外では発動しない(weather):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=weather,
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.is_active


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのおふだ", "たいあたり"),
        ("わざわいのうつわ", "ひのこ"),
    ],
)
def test_わざわい_相手攻撃補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのつるぎ", "たいあたり"),
        ("わざわいのたま", "ひのこ"),
    ],
)
def test_わざわい_相手防御補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.def_modifier


def test_わざわいのおふだ_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わざわいのおふだ")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.atk_modifier


def test_わたげ_クリアボディではブロックされる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="わたげ")],
        team1=[Pokemon("カビゴン", ability_name="クリアボディ", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["S"] == 0


def test_わたげ_被弾で攻撃者のSが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="わたげ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["S"] == -1


def test_わるいてぐせ_接触技を受けたら相手のアイテムを奪う():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.item.name == "たべのこし"
    assert not attacker.has_item()


def test_わるいてぐせ_自分がアイテムを持っている場合は奪わない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ", item_name="いのちのたま")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_item()


def test_わるいてぐせ_非接触技には反応しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし", move_names=["いわなだれ"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_item()


@pytest.mark.parametrize(
    "ability_name, attacker_name, attacker_ability, expected_can_switch",
    [
        ("ありじごく", "ピカチュウ", "", False),
        ("ありじごく", "ピジョン", "", True),
        ("かげふみ", "ピカチュウ", "", False),
        ("かげふみ", "ピカチュウ", "かげふみ", True),
        ("じりょく", "コイル", "", False),
        ("じりょく", "ピカチュウ", "", True),
    ],
)
def test_交代抑制特性_param(ability_name: str, attacker_name: str, attacker_ability: str, expected_can_switch: bool):
    team0 = [Pokemon(attacker_name, ability_name=attacker_ability), Pokemon("ピカチュウ")]
    battle = t.start_battle(
        team0=team0,
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    assert t.can_switch(battle, 0) is expected_can_switch


@pytest.mark.parametrize(
    "ability_name, stat",
    [
        ("じしんかじょう", "A"),
        ("しろのいななき", "A"),
        ("くろのいななき", "C"),
    ],
)
def test_倒すと能力上昇系_相手を倒すと指定ステータスが1段階上昇する(ability_name: str, stat: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.rank[stat] == 1


@pytest.mark.parametrize(
    "ability_name, stat",
    [
        ("じしんかじょう", "A"),
        ("しろのいななき", "A"),
        ("くろのいななき", "C"),
    ],
)
def test_倒すと能力上昇系_相手を倒せないと発動しない(ability_name: str, stat: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.fainted
    assert attacker.rank[stat] == 0


@pytest.mark.parametrize(
    "ability_name, terrain_name",
    ability_terrain_pairs
)
def test_地形始動特性_同一地形が有効時は継続ターンを更新しない(ability_name: str, terrain_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
        terrain=(terrain_name, 2)
    )
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 2
    assert not battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "ability_name, terrain_name",
    ability_terrain_pairs
)
def test_地形始動特性_登場時に対応地形を展開する(ability_name: str, terrain_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "ability_name, weather",
    [
        ("ゆきがくれ", "ゆき"),
        ("すながくれ", "すなあらし"),
    ],
)
def test_天候がくれ系_かたやぶりで命中率補正なし(ability_name: str, weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
        weather=(weather, 5),  # type: ignore[arg-type]
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


@pytest.mark.parametrize(
    "ability_name, weather",
    [
        ("ゆきがくれ", "ゆき"),
        ("すながくれ", "すなあらし"),
    ],
)
def test_天候がくれ系_対応天候で命中低下(ability_name: str, weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
        weather=(weather, 5),  # type: ignore[arg-type]
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 3277 // 4096


@pytest.mark.parametrize(
    "ability_name",
    ["ゆきがくれ", "すながくれ"],
)
def test_天候がくれ系_対応天候以外では命中率変化なし(ability_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


@pytest.mark.parametrize(
    "ability, weather, expected_mult",
    [
        ("すなかき", "すなあらし", 2),
        ("すいすい", "あめ", 2),
        ("ようりょくそ", "はれ", 2),
        ("ゆきかき", "ゆき", 2),
    ],
)
def test_天候依存素早さ上昇(ability: str, weather: str, expected_mult: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 999),
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * expected_mult


@pytest.mark.parametrize(
    "ability",
    ["すなかき", "すいすい", "ようりょくそ", "ゆきかき"],
)
def test_天候依存素早さ上昇_非対応天候は据え置き(ability: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


@pytest.mark.parametrize(
    "ability_name,weather_name,weather_count",
    [
        ("あめうけざら", "あめ", 5),
        ("あめうけざら", "おおあめ", 999),
        ("アイスボディ", "ゆき", 5),
    ]
)
def test_天候回復特性_対応天候中に回復(ability_name: str, weather_name: str, weather_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16


@pytest.mark.parametrize(
    "ability_name, weather_name, default_count",
    ability_weather_defaultcount
)
def test_天候始動特性_登場時に発動(ability_name: str, weather_name: str, default_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == weather_name
    assert battle.weather.count == default_count
    assert battle.actives[0].ability.revealed is True


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("おわりのだいち", "おおひでり"),
        ("はじまりのうみ", "おおあめ"),
        ("デルタストリーム", "らんきりゅう"),
    ],
)
def test_強天候始動特性_相手も同じ特性だと退場しても解除されない(ability_name: str, weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == weather_name


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("おわりのだいち", "おおひでり"),
        ("はじまりのうみ", "おおあめ"),
        ("デルタストリーム", "らんきりゅう"),
    ],
)
def test_強天候始動特性_退場時に解除される(ability_name: str, weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_switch(battle, 0, 1)
    assert not battle.weather.is_active


@pytest.mark.parametrize(
    "ability_name, move_name, expected_power",
    [
        ("かたいツメ", "たいあたり", 5325),
        ("かたいツメ", "でんきショック", 4096),
        ("がんじょうあご", "かみつく", 6144),
        ("きれあじ", "きりさく", 6144),
        ("てつのこぶし", "かみなりパンチ", 4915),
        ("パンクロック", "バークアウト", 5325),
    ],
)
def test_技カテゴリによる威力補正_param(ability_name: str, move_name: str, expected_power: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert expected_power == battle.damage_calculator.power_modifier


@pytest.mark.parametrize(
    "ability_name, ailment_name",
    CONTACT_AILMENT_CASES
)
def test_接触時に状態異常付与_接触技で状態異常を付与する(ability_name: str, ailment_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=["たいあたり"])],
    )
    attacker = battle.actives[1]
    battle.random.random = lambda: 0.0  # 確率操作
    t.run_move(battle, 1)
    assert attacker.has_ailment(ailment_name)


@pytest.mark.parametrize(
    "ability_name, ailment_name",
    CONTACT_AILMENT_CASES
)
def test_接触時に状態異常付与_非接触技では発動しない(ability_name: str, ailment_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=["はどうだん"])],
    )
    attacker = battle.actives[1]
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    assert not attacker.has_ailment(ailment_name)


@pytest.mark.parametrize(
    "ability, volatile, result",
    [
        ("アロマベール", "アンコール", False),
        ("アロマベール", "いちゃもん", False),
        ("アロマベール", "かいふくふうじ", False),
        ("アロマベール", "かなしばり", False),
        ("アロマベール", "ちょうはつ", False),
        ("アロマベール", "メロメロ", False),
        ("スイートベール", "ねむけ", False),
        ("どんかん", "ちょうはつ", False),
        ("どんかん", "メロメロ", False),
        ("マイペース", "こんらん", False),
    ]
)
def test_揮発状態耐性(ability: str, volatile: VolatileName, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.volatile_manager.apply(battle.actives[0], volatile) == result


@pytest.mark.parametrize(
    "ability, ailment",
    [
        ("めんえき", "どく"),
        ("めんえき", "もうどく"),
        ("パステルベール", "どく"),
        ("パステルベール", "もうどく"),
        ("じゅうなん", "まひ"),
        ("ふみん", "ねむり"),
        ("やるき", "ねむり"),
        ("スイートベール", "ねむり"),
        ("みずのベール", "やけど"),
        ("マグマのよろい", "こおり"),
    ],
)
def test_状態異常無効(ability: str, ailment: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, ailment)
    assert not mon.ailment.is_active


@pytest.mark.parametrize(
    "ability, ailment, move",
    [
        ("めんえき", "どく", "どくのこな"),
        ("めんえき", "もうどく", "どくどく"),
        ("パステルベール", "どく", "どくのこな"),
        ("パステルベール", "もうどく", "どくどく"),
        ("じゅうなん", "まひ", "でんじは"),
        ("ふみん", "ねむり", "ねむりごな"),
        ("やるき", "ねむり", "ねむりごな"),
        ("スイートベール", "ねむり", "ねむりごな"),
        ("みずのベール", "やけど", "おにび"),
        # ("マグマのよろい", "こおり", ""),
    ],
)
def test_状態異常無効_かたやぶりで無効(ability: str, ailment: AilmentName, move: str):
    # カビゴン（ノーマル）はまひ・ねむり・やけど・どく全てのタイプ耐性を持たないため使用
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.actives[0].ailment.is_active


@pytest.mark.parametrize(
    "ability_name, stats, source_is_self, expected",
    [
        ("かいりきバサミ", {"A": -1, "B": -1, "C": -2}, False, {"B": -1, "C": -2}),
        ("かいりきバサミ", {"A": -1}, True, {"A": -1}),
        ("はとむね", {"A": -1, "B": -1, "C": -2}, False, {"A": -1, "C": -2}),
    ],
)
def test_能力低下防止特性_param(ability_name: str, stats: dict, source_is_self: bool, expected: dict):
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    target, foe = battle.actives
    source = target if source_is_self else foe
    result = battle.modify_stats(target, stats, source=source)
    assert result == expected


@pytest.mark.parametrize(
    "defender_ability, attacker_ability, move_name, should_block",
    [
        ("ぼうおん", "", "バークアウト", True),
        ("ぼうおん", "かたやぶり", "バークアウト", False),
        ("ぼうだん", "", "かえんボール", True),
        ("ぼうだん", "かたやぶり", "かえんボール", False),
    ],
)
def test_音ラベル無効系_param(defender_ability: str, attacker_ability: str, move_name: str, should_block: bool):
    # attacker_ability may be empty string for no ability
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=attacker_ability, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=defender_ability)],
    )
    # attacker is index 0 or 1 depending on order
    # attacker chosen is battle.actives[0] when team0 provided
    t.run_move(battle, 0)
    defender = battle.actives[1]
    if should_block:
        # damage should be unchanged (no hit)
        assert defender.hp == defender.max_hp
        assert defender.ability.revealed is True
    else:
        assert defender.hp < defender.max_hp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
