"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.types import Type, AilmentName, WeatherName, Gender

from .. import test_utils as t


def test_たんじゅん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == -1


def test_たんじゅん_能力変化量が2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"atk": 1, "def": -2, "spa": 3, "spd": -4, "spe": 1, "accuracy": -2, "evasion": 3}
    battle.modify_stats(target, stats, source=source)
    for stat, change in stats.items():
        assert target.boosts[stat] == max(-6, min(6, change * 2))


@pytest.mark.parametrize(
    "foe_name, stat",
    [
        ("フシギダネ", "atk"),
        ("ゼニガメ", "spa"),
        ("ウインディ", "spa"),  # BD同じならCアップ
    ],
)
def test_ダウンロード_能力アップ(foe_name, stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダウンロード")],
        team1=[Pokemon(foe_name)],
    )
    assert battle.actives[0].boosts[stat] == 1


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_だっぴ_ターン終了時に状態異常を回復する(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(ailment_name, None),
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
        ailment0=("どく", None),
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
        ailment0=("どく", None),
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
        team0=[Pokemon("ヒヒダルマ(ダルマ)", ability_name="ダルマモード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    t.end_turn(battle)
    assert mon.name == "ヒヒダルマ(ノーマル)"


def test_ダルマモード_交代するとノーマルのすがたに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ダルマ)", ability_name="ダルマモード"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "ヒヒダルマ(ノーマル)"


def test_ちからずく_いっちょうあがりは追加効果がなくても威力が1_3倍になる():
    """いっちょうあがり: 追加効果は無いがちからずく対象フラグを持つため、威力が1.3倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["いっちょうあがり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert attacker.boosts["atk"] == 0


def test_ちからずく_ねっとうで相手のこおりを治せない():
    """ちからずく: ねっとうはみずタイプでこおり解凍効果を持つが、
    ほのおタイプ由来の効果ではなく追加効果扱いのため、ちからずくで発動しなくなる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability_name="ちからずく", move_names=["ねっとう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert defender.ailment.name == "こおり"
    assert 5325 == battle.damage_calculator.power_modifier


def test_ちからずく_ハイドロスチームでも相手のこおりを治せる():
    """ちからずく: ハイドロスチームはちからずくの対象技ではないため、
    ちからずく所持でも威力は上がらず、相手のこおりを治す効果は通常通り発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", ability_name="ちからずく", move_names=["ハイドロスチーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert 4096 == battle.damage_calculator.power_modifier


def test_ちからずく_追加効果が発動せず威力が1_3倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert attacker.boosts["spe"] == 0


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


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり",  8192),
        ("でんきショック", 4096)
    ]
)
def test_ちからもち_物理技で攻撃補正2倍(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.atk_modifier


def test_ちどりあし_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちどりあし")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["たいあたり"])],
        volatile0={"こんらん": 3}
    )
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
        volatile0={"こんらん": 3}
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 50


@pytest.mark.parametrize(
    "name, tera_type, move_name, expected_modifier",
    [
        ("ピカチュウ", "", "でんきショック", 4096 * 2),
        ("ピカチュウ", "でんき", "でんきショック", 4096 * 2.25),
        ("ピカチュウ", "", "ひのこ", 4096),
    ]
)
def test_てきおうりょく_STAB補正(name: str, tera_type: Type, move_name: str, expected_modifier: float):
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
        ("すてみタックル", 4096),  # 威力 > 60の技
        ("タネマシンガン", 6144),  # 連続技
    ]
)
def test_テクニシャン_威力補正(move_name, expected_modifier):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("マッハパンチ", 4915),
        ("でんきショック", 4096)
    ]
)
def test_てつのこぶし_パンチ技以外は補正なし(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てつのこぶし", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.power_modifier


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
        team1=[Pokemon("ピカチュウ", ability_name="エアロック")],
        weather=("はれ", 5)
    )
    mon = battle.actives[0]
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
def test_てんきや_フォルムチェンジ(weather: WeatherName, form: str):
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 5),
    )
    mon = battle.actives[0]
    assert mon.name == form


def test_てんきや_ポワルン以外は天候変化でもフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんきや")],
        team1=[Pokemon("コラッタ")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    assert mon.name == "ピカチュウ"

    battle.weather_manager.apply("はれ", 5)
    assert mon.name == "ピカチュウ"


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
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    assert mon.name == "ポワルン(あまみず)"

    battle.weather_manager.apply("はれ", 5)
    assert mon.name == "ポワルン(たいよう)"


@pytest.mark.parametrize(
    "move_name, stat",
    [
        ("たいあたり", "def"),
        ("ひのこ", "spd"),
    ]
)
def test_てんねん_攻撃側は防御ランク補正を無視する(move_name, stat):
    """てんねん攻撃側: 防御ランク+2でも防御の実効値がランクなし（+0）と同じになる。

    急所は防御側の正ランク補正を無視するため、乱数を固定して急所を回避しないと
    ランダムに急所が発生した際に defense_with_rank が偶然 defense_without_rank
    と同値になり flaky になる。
    """
    # てんねんなし: 防御ランク+2でfinal_defenseが上昇する
    without_ten = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(without_ten, 0.9)
    without_ten.actives[1].boosts[stat] = 2
    t.run_move(without_ten, 0)
    defense_with_rank = without_ten.damage_calculator.final_defense

    # ランクなし: 通常の防御値
    without_rank = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(without_rank, 0.9)
    t.run_move(without_rank, 0)
    defense_without_rank = without_rank.damage_calculator.final_defense

    # てんねんあり: 防御ランク+2でもランクなしと同じ防御値になる
    with_ten = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんねん", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(with_ten, 0.9)
    with_ten.actives[1].boosts[stat] = 2
    t.run_move(with_ten, 0)
    defense_tennen = with_ten.damage_calculator.final_defense

    assert defense_with_rank > defense_without_rank  # ランクあり > ランクなし（対照確認）
    assert defense_tennen == defense_without_rank  # てんねんはランクを無視する


@pytest.mark.parametrize(
    "move_name, stat",
    [
        ("たいあたり", "atk"),
        ("ひのこ", "spa"),
    ]
)
def test_てんねん_防御側はACランク無視(move_name, stat):
    """てんねん防御側: 攻撃ランク+2でも攻撃の実効値がランクなし（+0）と同じになる。"""
    # てんねんなし: 攻撃ランク+2でfinal_attackが上昇する
    without_ten = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    without_ten.actives[0].boosts[stat] = 2
    t.run_move(without_ten, 0)
    attack_with_rank = without_ten.damage_calculator.final_attack

    # ランクなし: 通常の攻撃値
    without_rank = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(without_rank, 0)
    attack_without_rank = without_rank.damage_calculator.final_attack

    # てんねんあり: 攻撃ランク+2でもランクなしと同じ攻撃値になる
    with_ten = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="てんねん")],
        accuracy=100,
    )
    with_ten.actives[0].boosts[stat] = 2
    t.run_move(with_ten, 0)
    attack_tennen = with_ten.damage_calculator.final_attack

    assert attack_with_rank > attack_without_rank  # ランクあり > ランクなし（対照確認）
    assert attack_tennen == attack_without_rank  # てんねんはランクを無視する


def test_てんのめぐみ_追加効果確率が2倍になる():
    """てんのめぐみ: 20%追加効果が2倍（40%）になることを、シャドーボールを使って確認する。
    乱数0.35はてんのめぐみなし（20%）では発動しないが、てんのめぐみあり（40%）では発動する。"""
    # てんのめぐみなし: 乱数0.35ではD低下が発動しない（境界: 0.20未満で発動）
    without_megumi = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シャドーボール"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    without_megumi.random.random = lambda: 0.35
    t.run_move(without_megumi, 0)
    assert without_megumi.actives[1].boosts["spd"] == 0

    # てんのめぐみあり: 乱数0.35でD低下が発動する（確率2倍で境界: 0.40未満で発動）
    with_megumi = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんのめぐみ", move_names=["シャドーボール"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    with_megumi.random.random = lambda: 0.35
    t.run_move(with_megumi, 0)
    assert with_megumi.actives[1].boosts["spd"] == -1


def test_でんきにかえる_被弾でじゅうでん状態になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="でんきにかえる")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].has_volatile("じゅうでん")


@pytest.mark.parametrize(
    "gendar0, gendar1, expected_modifier",
    [
        ("male", "male", 5120),
        ("female", "female", 5120),
        ("male", "female", 3072),
        ("male", "", 4096),
        ("", "", 4096),
    ]
)
def test_とうそうしん_攻撃補正(gendar0: Gender, gendar1: Gender, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="とうそうしん", move_names=["たいあたり"], gender=gendar0)],
        team1=[Pokemon("カビゴン", gender=gendar1)],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.atk_modifier


def test_とびだすなかみ_KOされなければダメージなし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.fainted
    assert attacker.hp == attacker.max_hp


def test_とびだすなかみ_KOされると攻撃者に反撃ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
    )
    attacker, defender = battle.actives
    t.fix_damage(battle, 999)
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.hp == attacker.max_hp - defender.max_hp


def test_とびだすなかみ_多段技では最初のヒット前HPが基準():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["すいりゅうれんだ"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
    )
    attacker, defender = battle.actives
    t.fix_damage(battle, 50)
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.hp == attacker.max_hp - defender.max_hp


@pytest.mark.parametrize(
    "move_name, result",
    [
        ("たいあたり", True),
        ("でんきショック", True),
        ("すなかけ", False),
    ]
)
def test_とびだすハバネロ_被弾するとやけどにする(move_name: str, result: bool):
    """とびだすハバネロ: 攻撃技のダメージを受けた後、攻撃者をやけど状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすハバネロ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_ailment("やけど") is result


@pytest.mark.parametrize(
    "move_name, result",
    [
        ("たいあたり", True),
        ("でんきショック", False),
    ]
)
def test_とれないにおい_接触した相手の特性を上書き(move_name: str, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("カビゴン", ability_name="とれないにおい")],
        accuracy=100,
    )
    attacker, _ = battle.actives
    assert attacker.ability.name != "とれないにおい"
    t.run_move(battle, 0)
    assert (attacker.ability.name == "とれないにおい") is result


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
    assert battle.actives[1].boosts["atk"] == -1


def test_トレース_交代で元の特性に戻る():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="トレース"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )

    tracer = battle.player_states[battle.players[0]].team[0]
    assert tracer.ability.base_name == "いかく"

    t.run_switch(battle, 0, 1)
    assert tracer.ability.base_name == "トレース"


@pytest.mark.parametrize(
    "ailment_name, result",
    [
        ("どく", True),
        ("もうどく", True),
        ("まひ", False),
    ]
)
def test_どくくぐつ_どく付与時にこんらん付与(ailment_name: AilmentName, result: bool):
    """どくくぐつ: どく付与と同時に相手がこんらんになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくくぐつ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert battle.ailment_manager.apply(defender, ailment_name, source=attacker)
    assert defender.has_volatile("こんらん") is result


def test_どくげしょう_物理技をくらうとどくびしを設置():
    """どくげしょう: どくびし1層のとき被弾すると2層になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    foe_side = battle.get_side(battle.players[1])
    for i in range(3):
        t.run_move(battle, 1)
        assert foe_side.get("どくびし").count == min(2, i+1)
    assert battle.actives[0].ability.revealed


def test_どくげしょう_特殊技では発動しない():
    """どくげしょう: 特殊技を受けても発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    t.run_move(battle, 1)
    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 0
    assert not battle.actives[0].ability.revealed


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

    battle.random.random = lambda: 0.0
    t.run_move(battle, 0)

    assert not defender.ailment.is_active


def test_どくのくさり_30パーセントでもうどくを付与する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.29)
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_どくのくさり_確率外ではもうどくにならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.31)
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_どくぼうそう_どく状態でない場合は倍率なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくぼうそう", move_names=["ねっとう"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("でんきショック", 6144),
        ("たいあたり", 4096),
    ]
)
def test_どくぼうそう_どく状態で特殊技の威力が1_5倍(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくぼうそう", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.power_modifier


def test_どんかん_いかくを無効化する():
    """どんかん: いかくによるこうげきランク低下を無効化する（第八世代以降）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どんかん")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].boosts["atk"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
