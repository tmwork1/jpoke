"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Move, Pokemon
from jpoke.data.ability import ABILITIES
from jpoke.enums import Command, Event
from jpoke.types import Stat, AilmentName, VolatileName, WeatherName

from .. import test_utils as t

ability_weather_defaultcount = [
    ("あめふらし", "あめ", 5),
    ("ひでり", "はれ", 5),
    ("すなおこし", "すなあらし", 5),
    ("ゆきふらし", "ゆき", 5),
    ("おわりのだいち", "おおひでり", 1),
    ("はじまりのうみ", "おおあめ", 1),
    ("デルタストリーム", "らんきりゅう", 1),
]
weathers = [x[1] for x in ability_weather_defaultcount]
strong_weathers = weathers[4:]


def test_はがねのせいしん_はがね以外の技は威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はがねのせいしん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_はがねのせいしん_はがね技の威力が1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はがねのせいしん", move_names=["アイアンヘッド"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_はがねのせいしん_はめつのねがいの威力も上がる():
    """はめつのねがい: 溜め処理（ON_MOVE_CHARGE）時点でダメージが確定するため、
    その時点の攻撃者である特性所持者自身の威力補正が反映される。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", ability_name="はがねのせいしん", move_names=["はめつのねがい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_はっこう_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["accuracy"] == -1


def test_はっこう_命中率低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう")],
        team1=[Pokemon("カビゴン", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["accuracy"] == 0


def test_はっこう_相手の回避率ランクを無視する():
    """はっこう: 攻撃時に相手の回避率ランク上昇を無視する（第九世代以降）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].boosts["evasion"] = 6
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_はっこう_相手の回避率ランク低下も無視する():
    """はっこう: 相手の回避率ランクが下がっていても命中率を上げない（第九世代以降の仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう", move_names=["ストーンエッジ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].boosts["evasion"] = -1
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_ハドロンエンジン_エレキフィールドが有効時は継続ターンを更新しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ハドロンエンジン")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 2),
    )
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 2
    assert not battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("でんきショック", 5461),
        ("たいあたり", 4096),
    ]
)
def test_ハドロンエンジン_エレキフィールドを展開して特攻1_33倍(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed

    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.atk_modifier


def test_ハドロンエンジン_エレキフィールド以外では補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        terrain=("グラスフィールド", 5)
    )
    assert battle.terrain.name == "グラスフィールド"

    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_はやあし_状態異常で素早さ1_5倍(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はやあし")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(ailment_name, None),
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] * 3 // 2


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "まひ", "やけど"],
)
def test_はやあし_素早さが奇数でも小数にならず切り捨てられる(ailment_name: AilmentName):
    """種族値が奇数でステータス素早さが奇数になる個体でも、
    まひ・まひ以外いずれの状態異常でも floor(素早さ*1.5) の整数値になることを確認する。
    （まひ以外でfloat演算になっていた・まひで切り捨て順序がずれるという2種の回帰を防ぐ）
    """
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", ability_name="はやあし")],
        team1=[Pokemon("チャーレム")],
        ailment0=(ailment_name, None),
    )
    mon = battle.actives[0]
    assert mon.stats["spe"] % 2 == 1
    result = battle.speed_calculator.calc_effective_speed(mon)
    assert result == mon.stats["spe"] * 3 // 2
    assert isinstance(result, int)


def test_はやおき_ねごと使用時も1ターンに2回のみ消費される():
    """はやおき: ねごとのサブ実行中の ON_TRY_ACTION では追加tickを行わない
    （ねごと自身の ON_TRY_ACTION で既に2回消費済みのため、合計は通常通り2回のみ）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやおき", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 5),
        accuracy=100,
    )
    mon = battle.actives[0]
    count_before = mon.ailment.count

    t.run_move(battle, 0, 0)

    count_after = mon.ailment.count
    assert count_after == count_before - 2, (
        f"はやおき+ねごとでも2回消費のみ: {count_before} → {count_after}"
    )


def test_はやおき_ねむりカウンタが通常の2倍速で減る():
    """はやおき: ねむり状態のとき1ターンで2回カウントが減る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやおき", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 4),  # カウント4で眠らせる
    )
    attacker, _ = battle.actives
    assert attacker.has_ailment("ねむり")
    count_before = attacker.ailment.count
    # 行動を試みる (はやおき + 通常のねむりtick = 2回消費)
    t.run_move(battle, 0)
    count_after = attacker.ailment.count
    # 2回消費でcount_before - 2になるはず
    assert count_after == count_before - 2, f"はやおきで2回消費: {count_before} → {count_after}"


def test_はやてのつばさ_HPが減ると優先度が上がらない():
    """はやてのつばさ: HP満タンでないときはひこう技の優先度は変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやてのつばさ", move_names=["つばさでうつ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, _ = battle.actives
    attacker.hp = 1
    assert 0 == t.calc_move_priority(battle, 0)


@pytest.mark.parametrize(
    "move_name, priority",
    [
        ("つばさでうつ", 1),
        ("たいあたり", 0),
    ]
)
def test_はやてのつばさ_HP満タン時にひこう技の優先度が1上がる(move_name: str, priority: int):
    """はやてのつばさ: HP満タン時にひこうタイプ技の優先度が+1される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやてのつばさ", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
    )
    assert priority == t.calc_move_priority(battle, 0)


def test_はらぺこスイッチ_かがくへんかガス中はターン終了時に切り替わらない():
    """はらぺこスイッチ: かがくへんかガスの効果が発動している間は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ")],
        team1=[Pokemon("ドガース", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    assert not mon.ability.enabled
    assert mon.ability.is_hangry is False

    battle.step()
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_ターン終了時にフォルムが交互に切り替わる():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability.is_hangry is False

    battle.step()
    assert mon.ability.is_hangry is True

    battle.step()
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_ダルマモード等のフォルムチェンジより後の優先度で登録されている():
    """はらぺこスイッチ: 一次情報に「ダルマモード/リミットシールド/スワームチェンジ/
    ぎょぐんのポケモンとは、すばやさに関係なくはらぺこスイッチが後に発動する」とある。
    docs/spec/turn.md の ON_TURN_END では両者とも priority=160 の同グループとして
    記載されているが、同じ priority のままだと _sort_handlers の (priority, -speed)
    tie-break によりすばやさ次第で順序が入れ替わってしまう。はらぺこスイッチの
    priority がそれらより大きい（＝必ず後に実行される）ことを確認する。"""
    hangry_priority = ABILITIES["はらぺこスイッチ"].handlers[Event.ON_TURN_END].priority
    for name in ("ダルマモード", "リミットシールド", "スワームチェンジ", "ぎょぐん"):
        assert hangry_priority > ABILITIES[name].handlers[Event.ON_TURN_END].priority


def test_はらぺこスイッチ_テラスタル中にひんしになるとまんぷくもように戻る():
    """はらぺこスイッチ: テラスタル中の交代はフォルムを維持するが、テラスタル中に
    ひんしになった場合は例外的にまんぷくもように戻る（一次情報:
    「はらぺこもようでテラスタルした後に交代したときは、はらぺこもようを維持する。
    ...テラスタルしてひんしになった場合は、まんぷくもように戻る」）。"""
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ", tera_type="あく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    mon.ability.is_hangry = True
    mon.terastallize()
    battle.faint(mon)
    t.run_switch(battle, 0, 1)

    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル中はターン終了時に切り替わらない():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ", tera_type="あく")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle, command0=Command.TERASTAL_0)
    battle.step()
    mon = battle.actives[0]

    assert mon.is_terastallized is True
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


def test_はらぺこスイッチ_とくせいなし中はターン終了時に切り替わらない():
    """はらぺこスイッチ: 一次情報に「いえきによりとくせいなし状態になる。
    かがくへんかガスの効果が発動している間は、はらぺこスイッチは発動しなくなる」
    とある。AbilityHandler は source="ability" のため、とくせいなし状態では
    enabled_ignoring による自動チェックでハンドラがスキップされるはずである。"""
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"とくせいなし": 3},
    )
    mon = battle.actives[0]
    assert mon.ability.is_hangry is False

    battle.step()
    assert mon.ability.is_hangry is False


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


def test_はりきり_一撃必殺技は命中率が下がらない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 30


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 6144),
        ("ひのこ", 4096),
    ]
)
def test_はりきり_物理技が1_5倍になる(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == expected_modifier


@pytest.mark.parametrize(
    "move_name, expected_accuracy",
    [
        ("たいあたり", 100 * 3277 // 4096),
        ("ひのこ", 100),
        ("つのドリル", 30),
    ]
)
def test_はりきり_物理技の命中率が下がる(move_name: str, expected_accuracy: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == expected_accuracy


def test_はりこみ_交代直後の相手への攻撃強化():
    """はりこみ: 交代直後の相手に攻撃すると atk_modifier が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりこみ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
    )
    # 相手を交代させてから攻撃する
    t.run_switch(battle, 1, 1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 8192


def test_はりこみ_初手の相手には発動しない():
    """はりこみ: 初手（0ターン目の初期交代）で繰り出された相手には発動しない。

    has_switched は初期交代でも True になるが、1ターン目の開始時
    （_begin_turn の reset_turn_state）でリセットされるため、
    実際のターン進行（battle.step）を経由して検証する必要がある
    （t.run_move を直接呼ぶだけでは初期交代の has_switched がリセットされず
    誤って発動してしまう）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりこみ", move_names=["たいあたり"])],
        team1=[Pokemon("ライチュウ")],
        accuracy=100,
    )
    t.reserve_command(battle, command0=Command.MOVE_0, command1=Command.MOVE_0)
    battle.step()
    assert battle.damage_calculator.atk_modifier == 4096


def test_はりこみ_死に出しの相手には発動しない():
    """はりこみ: 死に出し（瀕死交代）で繰り出された相手には発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりこみ", move_names=["たいあたり"])],
        team1=[Pokemon("コイキング"), Pokemon("ライチュウ")],
    )
    defender = battle.actives[1]
    battle.modify_hp(defender, v=-defender.max_hp)
    battle.switch_manager.run_faint_switch()

    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_はんすう_HP割合条件を無視して2ターン後の終了時に同じきのみを食べ直す():
    """はんすう: きのみ消費のターン自身の終了時ではなく、次のターンの終了時に
    同じきのみを再度食べる。オボンのみの通常発動条件（HP50%以下）を満たさなくても
    強制的に効果を得る。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はんすう", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-round(mon.max_hp * 0.1))  # 50%は超えているが満タンではない
    hp_before = mon.hp
    battle.item_manager.consume_item(mon)
    assert mon.ability.cud_chew_item == "オボンのみ"
    assert mon.ability.cud_chew_turns == 2
    assert not mon.has_item()

    t.end_turn(battle)  # 消費したターン自身の終了時: 2→1、まだ発動しない
    assert mon.ability.cud_chew_turns == 1
    assert mon.hp == hp_before
    assert not mon.has_item()

    t.end_turn(battle)  # 次のターンの終了時: 1→0、発動してHP50%超でも回復する
    assert mon.ability.cud_chew_turns == 0
    assert mon.hp > hp_before
    assert not mon.has_item()  # 再度消費されるため持ち物としては残らない


def test_はんすう_かがくへんかガス中はカウントが進まず解除後に再開する():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はんすう", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    assert mon.ability.cud_chew_turns == 2

    battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    t.end_turn(battle)
    assert mon.ability.cud_chew_turns == 2  # 無効化中は判定自体が発火しないため進まない

    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    t.end_turn(battle)
    assert mon.ability.cud_chew_turns == 1

    t.end_turn(battle)
    assert mon.ability.cud_chew_turns == 0


def test_はんすう_かがくへんかガス発動中に消費したきのみは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はんすう", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    battle.item_manager.consume_item(mon)
    assert mon.ability.cud_chew_turns == 0

    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    t.end_turn(battle)
    t.end_turn(battle)
    assert not mon.has_item()  # ガス解除後もこのきのみに対してはんすうは発動しない


def test_はんすう_なげつけるで効果の無いきのみを受けても対象にならない():
    """はんすう: 半減系きのみ等、なげつけるを受けても効果の無いきのみは対象にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="オッカのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", ability_name="はんすう")],
    )
    defender = battle.actives[1]

    t.run_move(battle, 0)
    assert defender.ability.cud_chew_turns == 0
    assert defender.ability.cud_chew_item == ""


def test_はんすう_なげつけるで自分のきのみを投げると次のターンに使用者が効果を得る():
    """はんすう: なげつけるで自分の持ち物（きのみ）を消費した場合も対象になり、
    次のターンの終了時に使用者自身がきのみの効果を得る。"""
    battle = t.start_battle(
        team0=[Pokemon(
            "カビゴン", ability_name="はんすう", item_name="オボンのみ",
            move_names=["なげつける"],
        )],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.modify_hp(attacker, v=-round(attacker.max_hp * 0.1))
    hp_before = attacker.hp

    t.run_move(battle, 0)
    assert not attacker.has_item()
    assert attacker.ability.cud_chew_item == "オボンのみ"
    assert attacker.ability.cud_chew_turns == 2

    t.end_turn(battle)
    t.end_turn(battle)
    assert attacker.hp > hp_before


def test_はんすう_なげつけるを受けて効果が発動すると次のターンに対象が効果を得る():
    """はんすう: なげつけるを受けてきのみの効果が発動した場合も対象になり、
    次のターンの終了時に対象がもう一度効果を得る。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="オボンのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", ability_name="はんすう")],
    )
    defender = battle.actives[1]
    battle.modify_hp(defender, v=-round(defender.max_hp * 0.4))

    t.run_move(battle, 0)
    assert defender.ability.cud_chew_item == "オボンのみ"
    assert defender.ability.cud_chew_turns == 2
    hp_after_hit = defender.hp
    assert hp_after_hit > defender.max_hp * 0.6 - 1  # なげつける時点で即座に回復済み

    t.end_turn(battle)
    t.end_turn(battle)
    assert defender.hp > hp_after_hit  # 次のターンの終了時にもう一度回復する


def test_はんすう_むしくいで奪ったきのみも対象になる():
    """はんすう: むしくい・ついばむで奪って消費したきのみも対象になり、
    次のターンの終了時にもう一度効果を得る。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はんすう", move_names=["むしくい"])],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.modify_hp(attacker, v=-round(attacker.max_hp * 0.6))
    hp_before = attacker.hp

    t.run_move(battle, 0)
    assert not defender.has_item()
    hp_after_steal = attacker.hp
    assert hp_after_steal > hp_before  # むしくいで即座に効果を得る
    assert attacker.ability.cud_chew_item == "オボンのみ"
    assert attacker.ability.cud_chew_turns == 2

    t.end_turn(battle)
    t.end_turn(battle)
    assert attacker.hp > hp_after_steal  # はんすうでもう一度効果を得る


def test_はんすう_効果の無いきのみは消費されるが効果は発動しない():
    """はんすう: 半減系きのみ等、はんすうの強制発動イベントに登録されていないきのみは、
    効果を発動させずに消費だけが行われる（アニメーションのみで効果無し、に相当）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はんすう", item_name="オッカのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    assert mon.ability.cud_chew_item == "オッカのみ"

    t.end_turn(battle)
    t.end_turn(battle)
    assert mon.ability.cud_chew_turns == 0
    assert mon.ability.cud_chew_item == ""
    assert not mon.has_item()


def test_はんすう_特性が書き換わるとカウントが失われる():
    """はんすう: 特性が書き換わるとカウントは失われ、はんすうに戻っても発動しない
    （スキルスワップ等で新しいAbilityインスタンスに切り替わるため）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はんすう", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    assert mon.ability.cud_chew_turns == 2

    battle.ability_manager.change_ability(mon, "あついしぼう")
    battle.ability_manager.change_ability(mon, "はんすう")
    assert mon.ability.cud_chew_turns == 0

    t.end_turn(battle)
    t.end_turn(battle)
    assert not mon.has_item()


def test_はんすう_発動前に交代すると発動しない():
    battle = t.start_battle(
        team0=[
            Pokemon("カビゴン", ability_name="はんすう", item_name="オボンのみ"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("コイキング")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    assert mon.ability.cud_chew_turns == 2

    t.run_switch(battle, 0, 1)
    assert mon.ability.cud_chew_turns == 0
    assert mon.ability.cud_chew_item == ""

    t.run_switch(battle, 0, 0)
    assert battle.actives[0] is mon
    t.end_turn(battle)
    t.end_turn(battle)
    assert not mon.has_item()  # 場に戻っても発動しない


def test_はんすう_発動時に別の持ち物を持っている場合は効果を再現しない():
    """はんすう: 特性で持ち物が復活するわけではないため、発動タイミングで既に
    別の持ち物を持っている場合はそれを上書きせず、効果の再現も行わない（既知の制約）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はんすう", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    battle.item_manager.gain_item(mon, "たべのこし")

    t.end_turn(battle)
    t.end_turn(battle)
    assert mon.ability.cud_chew_turns == 0
    assert mon.has_item("たべのこし")  # 上書きされない


def test_はんすう_複数のきのみを消費した場合は最後のきのみのみが対象になる():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はんすう", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    assert mon.ability.cud_chew_item == "オボンのみ"

    battle.item_manager.gain_item(mon, "ラムのみ")
    battle.item_manager.consume_item(mon)
    # 対象が最後に消費したラムのみに更新され、カウントも消費時点にリセットされる
    assert mon.ability.cud_chew_item == "ラムのみ"
    assert mon.ability.cud_chew_turns == 2


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
    t.fix_damage(battle, 30)

    # 1回目
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp - defender.max_hp // 8
    assert defender.ability.enabled is False

    # 2回目
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before - 30


def test_ばけのかわ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
    )
    _, defender = battle.actives
    t.fix_damage(battle, 30)
    t.run_move(battle, 0)

    assert defender.ability.enabled is True
    assert defender.hp == defender.max_hp - 30


def test_ばけのかわ_こんらんの自傷ダメージも防ぐ():
    """こんらんの自傷ダメージ（ON_MODIFY_NON_MOVE_DAMAGE 経由）もばけのかわで防ぎ、
    最大HPの1/8のみ消費する（docs/spec/abilities/ばけのかわ.md「こんらん時の自分への
    攻撃には発動し、ダメージを防ぐ」参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"こんらん": 2},
    )
    mon = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.fix_damage(battle, mon.max_hp)
    t.run_move(battle, 0)

    assert mon.hp == mon.max_hp - mon.max_hp // 8
    assert mon.ability.enabled is False


def test_ばけのかわ_交代しても再有効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ"), Pokemon("ピカチュウ")],
    )
    mon = battle.actives[1]
    t.run_move(battle, 0)

    # 交代して戻っても per_battle_once 特性は再有効化されない
    assert mon.ability.enabled is False
    t.run_switch(battle, 1, 1)
    t.run_switch(battle, 1, 0)
    assert mon.ability.enabled is False


def test_ばけのかわ_連続技の2発目以降は防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にどげり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
    )
    _, defender = battle.actives
    before_hp = defender.hp
    t.fix_damage(battle, 30)
    t.run_move(battle, 0)

    assert defender.ability.enabled is False
    assert defender.hp == before_hp - defender.max_hp // 8 - 30


def test_バトルスイッチ_ねごとで選ばれた技に応じて発動する():
    """ねごとを使用した場合、出た技に応じてバトルスイッチは発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("ねむり", 3),
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)  # ねごと -> 候補はたいあたりのみ

    assert mon.name == "ギルガルド(ブレード)"


@pytest.mark.parametrize(
    "form_before, form_after, move_name",
    [
        ("シールド", "シールド", "つるぎのまい"),
        ("シールド", "ブレード", "たいあたり"),
        ("ブレード", "シールド", "キングシールド"),
        ("ブレード", "ブレード", "まもる"),
    ]
)
def test_バトルスイッチ_フォルムチェンジ(form_before: str, form_after: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon(f"ギルガルド({form_before})", ability_name="バトルスイッチ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == f"ギルガルド({form_after})"


def test_バトルスイッチ_まひで行動できない場合は発動しない():
    """第七世代以降の仕様: 行動の判定を決めてから特性を発動するため、
    まひ等で行動できなかった場合はフォルムチェンジしない。"""
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("まひ", None),
    )
    mon = battle.actives[0]
    battle.test_option.trigger_ailment = True  # 必ず行動不能にする

    t.run_move(battle, 0)

    assert not battle.move_executor.action_success
    assert mon.name == "ギルガルド(シールド)"


def test_バトルスイッチ_まもるで無効化されても発動する():
    """シールドフォルムで選んだ攻撃技がまもる等で無効化されても、
    バトルスイッチは発動してブレードフォルムになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"まもる": 1},
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == "ギルガルド(ブレード)"


def test_バトルスイッチ_わるあがきでもブレードになる():
    """わるあがきは攻撃技扱いのため、変化技しか覚えていなくてもブレードフォルムになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["わるあがき"])],
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
    mon = battle.actives[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "ギルガルド(シールド)"


def test_バトルスイッチ_溜め技の1ターン目でも発動する():
    """ソーラーブレード等の溜め技を使用した場合、溜めるターンでバトルスイッチが発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["ソーラーブレード"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == "ギルガルド(ブレード)"


def test_バリアフリー_オーロラベールも解除される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="バリアフリー")],
        team1=[Pokemon("フシギダネ")],
        side0={"オーロラベール": 5},
        side1={"オーロラベール": 5},
    )
    t.run_switch(battle, 0, 1)
    side0 = battle.get_side(battle.players[0])
    side1 = battle.get_side(battle.players[1])

    assert battle.actives[0].ability.revealed
    assert not side0.get("オーロラベール").is_active
    assert not side1.get("オーロラベール").is_active


def test_バリアフリー_しんぴのまもりしろいきり設置技は解除しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="バリアフリー")],
        team1=[Pokemon("フシギダネ")],
        side0={"しんぴのまもり": 5, "しろいきり": 5, "まきびし": 1},
        side1={"しんぴのまもり": 5, "しろいきり": 5, "まきびし": 1},
    )
    t.run_switch(battle, 0, 1)
    side0 = battle.get_side(battle.players[0])
    side1 = battle.get_side(battle.players[1])

    assert side0.get("しんぴのまもり").is_active
    assert side0.get("しろいきり").is_active
    assert side0.get("まきびし").is_active
    assert side1.get("しんぴのまもり").is_active
    assert side1.get("しろいきり").is_active
    assert side1.get("まきびし").is_active


def test_バリアフリー_入場で壁を解除():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="バリアフリー")],
        team1=[Pokemon("フシギダネ")],
        side0={"リフレクター": 5, "ひかりのかべ": 5},
        side1={"リフレクター": 5, "ひかりのかべ": 5},
    )
    t.run_switch(battle, 0, 1)
    side0 = battle.get_side(battle.players[0])
    side1 = battle.get_side(battle.players[1])

    assert battle.actives[0].ability.revealed
    assert not side0.get("リフレクター").is_active
    assert not side0.get("ひかりのかべ").is_active
    assert not side1.get("リフレクター").is_active
    assert not side1.get("ひかりのかべ").is_active


def test_バリアフリー_壁がない場合アナウンスなし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="バリアフリー")],
        team1=[Pokemon("フシギダネ")],
    )
    t.run_switch(battle, 0, 1)
    assert not battle.actives[0].ability.revealed


def test_ばんけん_いかくで下がらずAが1段階上がる():
    """ばんけん: いかくを受けると下がらず逆にAが1段階上がり、特性バーが表れる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばんけん")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 1
    assert mon.ability.revealed


def test_ばんけん_かたやぶりには無効化されて交代させられる():
    """ばんけん: かたやぶりの効果がある技を受けた場合は無効化され、強制交代させられる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばんけん"), Pokemon("イーブイ")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["ほえる"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].name == "イーブイ"


def test_ばんけん_こうげきが最大ランクの場合はいかくが不発で発動しない():
    """ばんけん: こうげきが既に最大ランク（+6）の場合、いかくが不発でばんけんも発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばんけん")],
        team1=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.boosts["atk"] = 6
    t.run_switch(battle, 1, 1)
    assert mon.boosts["atk"] == 6
    assert not mon.ability.revealed


def test_ばんけん_ほえるを無効化する():
    """ばんけん: ほえるによる強制交代を防ぎ、特性バーは表れない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばんけん"), Pokemon("イーブイ")],
        team1=[Pokemon("カビゴン", move_names=["ほえる"])],
    )
    t.run_move(battle, 1)
    mon = battle.actives[0]
    assert mon.name == "ピカチュウ"
    assert not mon.ability.revealed


def test_ばんけん_レッドカードの相手は交代させられない():
    """ばんけん: レッドカードによる強制交代を防ぐが、アイテムは消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", ability_name="ばんけん", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    attacker_name = battle.actives[1].name
    t.run_move(battle, 1)
    assert battle.actives[1].name == attacker_name
    assert not battle.actives[0].has_item()


def test_パンクロック_かたやぶりで無効():
    """パンクロック: かたやぶり持ちの音技はパンクロックの被ダメ軽減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability_name="パンクロック")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_パンクロック_音の変化技には威力上昇も被ダメ軽減も発動しない():
    """パンクロック: 音の技であっても変化技の使用・被弾では特性が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="パンクロック", move_names=["うたう"])],
        team1=[Pokemon("ピカチュウ", move_names=["うたう"])],
        accuracy=100,
    )
    # 自身が音の変化技を使用しても威力補正イベントは発動しない
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier is None

    # 音の変化技を受けてもダメージ補正イベントは発動しない
    t.run_move(battle, 1)
    assert battle.damage_calculator.damage_modifier is None


def test_パンクロック_音技与ダメ1_3倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="パンクロック", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier


def test_パンクロック_音技被ダメ半減():
    battle2 = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability_name="パンクロック", move_names=["バークアウト"])],
        accuracy=100,
    )
    t.run_move(battle2, 0)
    assert 2048 == battle2.damage_calculator.damage_modifier


def test_ひでり_同じ晴れが既に有効なときは特性が発動しない():
    """ひでり: 既に晴れ状態のときは発動せず、継続ターンも書き換わらない（特性バーも表示されない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ひでり")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 3),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "はれ"
    assert battle.weather.count == 3
    assert battle.actives[0].ability.revealed is False


@pytest.mark.parametrize(
    "strong_weather",
    ["おおひでり", "おおあめ", "らんきりゅう"]
)
def test_ひでり_強天候中は天候を変えないが特性は発動する(strong_weather: WeatherName):
    """ひでり: おおひでり・おおあめ・らんきりゅう状態のときは晴れに変えられないが、
    特性バー（発動ログ・ability.revealed）は表示される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ひでり")],
        team1=[Pokemon("ピカチュウ")],
        weather=(strong_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == strong_weather
    assert battle.actives[0].ability.revealed is True


def test_ひとでなし_どくの追加効果で新たに付与した状態は同じ攻撃の急所判定に反映されない():
    """どくづきのようにどくの追加効果を持つ技は、急所判定を含むダメージ計算の後に
    追加効果の発動判定が行われるため、その攻撃自体にはひとでなしの効果が無い。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひとでなし", move_names=["どくづき"])],
        team1=[Pokemon("カビゴン")],
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 0
    assert battle.actives[1].has_ailment("どく")


@pytest.mark.parametrize(
    "ailment_name, critical_rank",
    [
        ("どく", 3),
        ("もうどく", 3),
        ("まひ", 0),
        ("やけど", 0),
        ("ねむり", 0),
        ("こおり", 0),
    ],
)
def test_ひとでなし_どく状態の相手に確定急所(ailment_name: AilmentName, critical_rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひとでなし", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment1=(ailment_name, 1),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == critical_rank


def test_ひひいろのこどう_あなをほるのダメージにも補正がかかる():
    """ひひいろのこどう: あなをほるで与えるダメージにも攻撃補正がかかる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう", move_names=["あなをほる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    t.run_move(battle, 0)
    assert 5461 == battle.damage_calculator.atk_modifier


def test_ひひいろのこどう_イカサマを受けるときは補正なし():
    """ひひいろのこどう: 自分がイカサマを受ける側（実数値を攻撃力として使われる側）の
    ときは、実際にイカサマを使う相手にひひいろのこどうの効果は乗らない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう")],
        team1=[Pokemon("ピカチュウ", move_names=["イカサマ"])],
    )
    t.run_move(battle, 1)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_ひひいろのこどう_こんらん自傷ダメージには補正なし():
    """ひひいろのこどう: こんらんの自傷ダメージには攻撃補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096
    assert attacker.hp < attacker.max_hp


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 5461),
        ("でんきショック", 4096),
    ]
)
def test_ひひいろのこどう_はれ中に攻撃が1_33倍(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == "はれ"
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.atk_modifier


def test_ひひいろのこどう_はれ以外では補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("あめ", 5),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_ひひいろのこどう_ボディプレスで自分の防御を1_33倍にする():
    """ひひいろのこどう: ボディプレス使用時は自分の防御実数値に補正をかけてダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう", move_names=["ボディプレス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5461 == battle.damage_calculator.atk_modifier


def test_ひらいしん_エレキフィールドなど場を対象とするでんき技には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキフィールド"])],
        team1=[Pokemon("カビゴン", ability_name="ひらいしん")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.terrain.name == "エレキフィールド"
    assert defender.boosts["spa"] == 0
    assert not defender.ability.revealed


def test_ひらいしん_じゅうでんなど自分自身を対象とするでんき技には発動しない():
    """ひらいしん: じゅうでんは自分自身が対象の技のため、自分のひらいしんには発動しない
    （じゅうでん自体の効果＝とくぼう+1は通常どおり発生する）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひらいしん", move_names=["じゅうでん"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.has_volatile("じゅうでん")
    assert mon.boosts["spd"] == 1
    assert mon.boosts["spa"] == 0


def test_ひらいしん_でんきタイプの変化技も無効化する():
    """ひらいしん: でんじはのようなでんきタイプの変化技を受けても無効化し、まひにならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        team1=[Pokemon("カビゴン", ability_name="ひらいしん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.boosts["spa"] == 1
    assert defender.ailment.name == ""


def test_ひらいしん_マジックコートで跳ね返された変化技を受けるととくこうが上がる():
    """ひらいしん: 自分が使ったでんきタイプの変化技が相手のマジックコートで跳ね返され、
    跳ね返った技を自分自身が受けた場合はひらいしんが発動してとくこうが上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひらいしん", move_names=["でんじは"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.boosts["spa"] == 1
    assert mon.ailment.name == ""


def test_ひらいしん_マジックコート状態では変化技を跳ね返しとくこうが上がらない():
    """ひらいしん: マジックコート状態のひらいしん持ちがでんきタイプの変化技を受けても、
    先に跳ね返されるためひらいしんは発動せずとくこうは上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        team1=[Pokemon("カビゴン", ability_name="ひらいしん")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.boosts["spa"] == 0
    assert not defender.ability.revealed


def test_ひらいしん_まもるで防がれたときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", ability_name="ひらいしん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "まもる", count=1)
    t.run_move(battle, 0)
    assert defender.boosts["spa"] == 0
    assert not defender.ability.revealed


def test_ひらいしん_みがわり状態の攻撃技でも発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", ability_name="ひらいしん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", count=defender.max_hp // 4)
    t.run_move(battle, 0)
    assert defender.boosts["spa"] == 1
    assert defender.has_volatile("みがわり")


def test_ひらいしん_無効化時にじゅうでんちは発動しない():
    """ひらいしん: じゅうでんちのようなでんき被弾で発動するアイテムは、
    ひらいしんで無効化されたときは発動しない（ダメージ処理自体が行われないため）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", ability_name="ひらいしん", item_name="じゅうでんち")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp
    assert defender.boosts["spa"] == 1
    assert defender.boosts["atk"] == 0
    assert defender.has_item()


@pytest.mark.parametrize(
    "move_name, priority",
    [
        ("なまける", 3),
        ("ギガドレイン", 3),
        ("でんきショック", 0),
        ("かふんだんご", 0),
    ]
)
def test_ヒーリングシフト_回復技の優先度が3上がる(move_name: str, priority: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ヒーリングシフト", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
    )
    assert t.calc_move_priority(battle, 0) == priority


@pytest.mark.parametrize(
    "move_name, rank",
    [
        ("かみつく", 1),
        ("したでなめる", 1),
        ("たいあたり", 0),
    ]
)
def test_びびり_Sが1段階上がる(move_name: str, rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["spe"] == rank


def test_びびり_いかくでS上昇():
    """びびり: いかくによってこうげきが下がったときすばやさ+1（第八世代以降）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.boosts["atk"] == -1
    assert mon.boosts["spe"] == 1


def test_びびり_クリアチャームでいかくが無効化されたときは発動しない():
    """びびり: ビビリだまと異なり、クリアチャームでいかくの効果が無効化された場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり", item_name="クリアチャーム")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 0
    assert mon.boosts["spe"] == 0


def test_びびり_こうげきが最低ランクで変化しない場合は発動しない():
    """びびり: こうげきが既に最低ランクでいかくが不発だった場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり")],
        team1=[Pokemon("ピカチュウ"), Pokemon("コラッタ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.boosts["atk"] = -6
    t.run_switch(battle, 1, 1)
    assert mon.boosts["atk"] == -6
    assert mon.boosts["spe"] == 0


def test_びびり_しろいきりでいかくが無効化されたときは発動しない():
    """びびり: ビビリだまと異なり、しろいきりでいかくの効果が無効化された場合は発動しない

    side0 はバトル開始時点（battle.start()）より後に設置されるため、初手の
    いかくで検証すると場の効果が間に合わない。中盤の交代で発動するいかくを使う。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり")],
        team1=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="いかく")],
        side0={"しろいきり": 1},
    )
    mon = battle.actives[0]
    t.run_switch(battle, 1, 1)
    assert mon.boosts["atk"] == 0
    assert mon.boosts["spe"] == 0


def test_びびり_すばやさが最大ランクの場合は発動しない():
    """びびり: すばやさが既に最大ランクの場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びびり")],
        team1=[Pokemon("ピカチュウ"), Pokemon("コラッタ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.boosts["spe"] = 6
    t.run_switch(battle, 1, 1)
    assert mon.boosts["atk"] == -1
    assert mon.boosts["spe"] == 6


def test_びんじょう_味方のランク上昇はコピーしない():
    """びんじょう: 味方（自分自身）のランク上昇では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives

    assert battle.modify_stats(binjou_mon, {"def": 2}, source=binjou_mon)
    assert binjou_mon.boosts["def"] == 2
    assert foe.boosts["def"] == 0


def test_びんじょう_相手のランク上昇をコピーする():
    """びんじょう: 相手のランクが上昇したとき自分も同じランク上昇をする"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives

    assert battle.modify_stats(foe, {"atk": 2}, source=foe)
    assert binjou_mon.boosts["atk"] == 2


def test_びんじょう_相手のランク低下はコピーしない():
    """びんじょう: 相手のランク低下はコピーしない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives

    assert battle.modify_stats(foe, {"atk": -2}, source=foe)
    assert binjou_mon.boosts["atk"] == 0


def test_びんじょう_自分がすでに最大なら発動しない():
    """びんじょう: 自分の該当ランクがすでに最大(+6)のときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives
    binjou_mon.boosts["atk"] = 6

    assert battle.modify_stats(foe, {"atk": 2}, source=foe)
    assert binjou_mon.boosts["atk"] == 6


def test_びんじょう_複数の能力の上昇を同時にコピーする():
    """びんじょう: 相手がめいそうなどで複数の能力を同時に上げたとき、全てコピーする"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives

    assert battle.modify_stats(foe, {"spa": 1, "spd": 1}, source=foe)
    assert binjou_mon.boosts["spa"] == 1
    assert binjou_mon.boosts["spd"] == 1


def test_ビーストブースト_ワンダールーム下では防御と特防の実数値を入れ替えて比較する():
    """フシギダネは特攻・特防が同値で最も高い（通常なら特攻が上がる）。

    ワンダールーム下では防御・特防の実数値が入れ替わるため、
    防御の実数値が特攻と同値になり、優先順（防御→特攻）により防御が上がる。
    """
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="ビーストブースト", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        field={"ワンダールーム": 99},
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)

    assert attacker.boosts["def"] == 1
    assert attacker.boosts["spa"] == 0


@pytest.mark.parametrize(
    "name, stat",
    [
        ("ウインディ", "atk"),
        ("ピカチュウ", "spe"),
    ]
)
def test_ビーストブースト_倒すと最高実数値の能力が上がる(name: str, stat: Stat):
    """ビーストブースト: 攻撃技で倒すと最高実数値の能力が1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon(name, ability_name="ビーストブースト", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)

    assert attacker.boosts[stat] == 1


def test_ビーストブースト_同値のときは優先順で決まる():
    """ヤドンは攻撃・防御の実数値が同値で最も高い。優先順（攻撃→防御）により攻撃が上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="ビーストブースト", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)

    assert attacker.boosts["atk"] == 1
    assert attacker.boosts["def"] == 0


def test_ビーストブースト_最高実数値の能力が既に最大ランクなら発動しない():
    """上げるはずの能力が既に+6の場合、2番目に高い能力に代わりに発動することはない。"""
    battle = t.start_battle(
        team0=[Pokemon("ウインディ", ability_name="ビーストブースト", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    attacker.boosts["atk"] = 6
    defender.hp = 1
    t.run_move(battle, 0)

    assert attacker.boosts["atk"] == 6
    assert attacker.boosts["spa"] == 0


def test_ファントムガード_HP満タンのとき半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ファントムガード")],
    )
    # 1発目は半減
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier

    # 2発目は半減しない
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_ファントムガード_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ファントムガード")],
    )
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


def test_ファーコート_こんらんの自傷ダメージには発動しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ", ability_name="ファーコート")],
        team0=[Pokemon("ピカチュウ")],
        volatile1={"こんらん": 2},
    )
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 1)
    assert 4096 == battle.damage_calculator.def_modifier


def test_ファーコート_ボディプレス使用時は自分の防御実数値を2倍にしない():
    """ファーコート: ボディプレスを使用するときは特性の効果は発動せず、
    自分の防御（攻撃力として参照される実数値）を2倍にすることは無い。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ファーコート", move_names=["ボディプレス"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_ファーコート_ワンダールームでとくぼうが2倍になる():
    """ワンダールーム中は物理技でも防御と特防が入れ替わり参照されるため、
    ファーコートの効果は実質的に特防を2倍にする形になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ファーコート")],
        field={"ワンダールーム": 5},
    )
    defender = battle.actives[1]
    before = defender.stats["spd"]
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_defense == before * 2


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 8192),
        ("でんきショック", 4096),
        ("サイコショック", 8192),  # 特殊技だがぼうぎょを参照するため発動する
    ],
)
def test_ファーコート_物理技の防御が2倍になる(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="ファーコート")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == expected_modifier


def test_フィルター_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="フィルター")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_フィルター_効果抜群ダメージを0_75倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="フィルター")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


def test_ふうりょくでんき_おいかぜ発生でじゅうでん():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
    )
    battle.side_managers[1].activate("おいかぜ", 4)
    assert battle.actives[1].has_volatile("じゅうでん")


def test_ふうりょくでんき_こらえるでHP1のまま耐えたときも発動する():
    """ふうりょくでんき: こらえるでHP1のまま耐えた（実HPダメージ0）ときも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かぜおこし"])],
        team1=[Pokemon("カビゴン", ability_name="ふうりょくでんき")],
    )
    defender = battle.actives[1]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)

    t.run_move(battle, 0)

    assert defender.hp == 1
    assert defender.has_volatile("じゅうでん")


def test_ふうりょくでんき_みがわりに阻まれたときは発動しない():
    """ふうりょくでんき: みがわりに風技を防がれたとき（実HPダメージ0）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かぜおこし"])],
        team1=[Pokemon("カビゴン", ability_name="ふうりょくでんき")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)

    t.run_move(battle, 0)

    assert not defender.has_volatile("じゅうでん")


def test_ふうりょくでんき_相手のおいかぜには反応しない():
    """ふうりょくでんき: 相手サイドのおいかぜには反応しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
    )
    # 相手サイド（player0側）においかぜを発生させる
    battle.side_managers[0].activate("おいかぜ", 4)
    assert not battle.actives[1].has_volatile("じゅうでん")


@pytest.mark.parametrize(
    "move_name, result",
    [
        ("かぜおこし", True),
        ("たいあたり", False),
        ("あやしいかぜ", False),  # 名前に「かぜ」を含むが風技ラベルは無い
        ("ぎんいろのかぜ", False),  # 同上
    ]
)
def test_ふうりょくでんき_風技を受けるとじゅうでん(move_name: str, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("じゅうでん") == result


def test_フェアリーオーラ_かたやぶりでも威力補正は無効化されない():
    """現行世代ではかたやぶりの効果がある技はフェアリーオーラの影響を受ける（無視されない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリーオーラ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ムーンフォース"])],
    )
    t.run_move(battle, 1)
    assert 5448 == battle.damage_calculator.power_modifier


def test_フェアリーオーラ_フェアリー技以外には効果がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリーオーラ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_フェアリーオーラ_登場時に特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリーオーラ")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed is True


def test_フェアリーオーラ_相手のフェアリー技威力も5448_4096倍になる():
    """フェアリーオーラの効果対象は場にいるポケモン全員のため、敵のフェアリー技威力も上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリーオーラ")],
        team1=[Pokemon("ピカチュウ", move_names=["ムーンフォース"])],
    )
    t.run_move(battle, 1)
    assert 5448 == battle.damage_calculator.power_modifier


def test_フェアリーオーラ_自分のフェアリー技威力が5448_4096倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリーオーラ", move_names=["ムーンフォース"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5448 == battle.damage_calculator.power_modifier


@pytest.mark.parametrize(
    "move_name, expected_accuracy",
    [
        ("でんじほう", 50 * 5325 // 4096),
        ("つのドリル", 30),  # 一撃必殺技には適用されない
    ]
)
def test_ふくがん_命中率を1_3倍にする(move_name: str, expected_accuracy: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくがん", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == expected_accuracy


def test_ふくつのこころ_S最大時は上昇しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくつのこころ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.boosts["spe"] = 6
    battle.volatile_manager.apply(mon, "ひるみ")
    assert mon.boosts["spe"] == 6


@pytest.mark.parametrize(
    "volatile_name, expected_rank",
    [
        ("ひるみ", 1),
        ("こんらん", 0),
    ]
)
def test_ふくつのこころ_ひるみ時にS上昇(volatile_name: VolatileName, expected_rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくつのこころ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, volatile_name)
    assert mon.boosts["spe"] == expected_rank


def test_ふくつのたて_Bが既に最大でも特性は消費される():
    """ふくつのたて: ぼうぎょが既に最大まで上がっているため特性が不発した場合でも、
    その戦闘で特性を再度発動させることはできなくなる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ザマゼンタ(れきせん)", ability_name="ふくつのたて")],
        team1=[Pokemon("カビゴン")],
    )
    bench = battle.get_team(battle.players[0])[1]
    battle.modify_stats(bench, {"def": +6})

    t.run_switch(battle, 0, 1)
    mon = battle.actives[0]
    assert mon.boosts["def"] == 6
    assert not mon.ability.enabled

    t.run_switch(battle, 0, 0)
    t.run_switch(battle, 0, 1)
    assert mon.boosts["def"] == 0


def test_ふくつのたて_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ザマゼンタ(れきせん)", ability_name="ふくつのたて")],
    )
    mon = battle.actives[1]
    assert not mon.ability.enabled
    assert mon.boosts["def"] == 0


def test_ふくつのたて_かがくへんかガス解除後に発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス"), Pokemon("ライチュウ")],
        team1=[Pokemon("ザマゼンタ(れきせん)", ability_name="ふくつのたて")],
    )
    mon = battle.actives[1]
    assert mon.boosts["def"] == 0

    t.run_switch(battle, 0, 1)
    assert mon.boosts["def"] == 1


def test_ふくつのたて_初登場でBが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ザマゼンタ(れきせん)", ability_name="ふくつのたて")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.boosts["def"] == 1


def test_ふしぎなうろこ_かたやぶりで無効():
    """ふしぎなうろこ: かたやぶり持ちの物理技はふしぎなうろこの防御補正を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふしぎなうろこ")],
        ailment1=("やけど", None),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


def test_ふしぎなうろこ_こんらんのみでは発動しない():
    """ふしぎなうろこ: こんらん（状態変化）だけでは発動しない。状態異常でないと発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふしぎなうろこ")],
        volatile1={"こんらん": 2},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


def test_ふしぎなうろこ_こんらんの自傷ダメージには発動しない():
    """ふしぎなうろこ: こんらんの自傷ダメージ（"_こんらん"）には効果が無い（第五世代以降の仕様）。"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ", ability_name="ふしぎなうろこ")],
        team0=[Pokemon("ピカチュウ")],
        ailment1=("やけど", None),
        volatile1={"こんらん": 2},
    )
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 1)
    assert 4096 == battle.damage_calculator.def_modifier


def test_ふしぎなうろこ_ぼうぎょ参照の特殊技には発動する():
    """サイコショック等、特殊技だがぼうぎょを参照する技には効果が乗る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["サイコショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふしぎなうろこ")],
        ailment1=("やけど", None),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_ふしぎなうろこ_ワンダールームでとくぼうが1_5倍になる():
    """ワンダールーム中は物理技でも防御と特防が入れ替わり参照されるため、
    ふしぎなうろこの効果は実質的に特防を1.5倍にする形になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふしぎなうろこ")],
        ailment1=("やけど", None),
        field={"ワンダールーム": 5},
    )
    defender = battle.actives[1]
    before = defender.stats["spd"]
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_defense == round(before * 1.5)


def test_ふしぎなうろこ_特殊技には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふしぎなうろこ")],
        ailment1=("やけど", None),
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
        ailment1=(ailment_name, None),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_ふしぎなまもり_かたやぶりで無効化される():
    """ふしぎなまもり: かたやぶり持ちの攻撃者には無効化が貫通される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_ふしぎなまもり_こんらんの自傷ダメージは無効化されない():
    """ふしぎなまもり: こんらんの自傷ダメージは通常の攻撃フローを経由しないため無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", ability_name="ふしぎなまもり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    mon = battle.actives[0]
    before = mon.hp
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert mon.hp < before


def test_ふしぎなまもり_わるあがきは無効化されない():
    """ふしぎなまもり: タイプを持たないわるあがきは相性判定の対象外のため無効化できない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, Move("わるあがき"))
    assert defender.hp < defender.max_hp


def test_ふしぎなまもり_変化技は通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.boosts["atk"] == -1


@pytest.mark.parametrize(
    "move_name, move_blocked",
    [
        ("でんきショック", False),
        ("たいあたり", True),
        ("つるのムチ", True),
    ]
)
def test_ふしぎなまもり_弱点技以外を無効化(move_name: str, move_blocked: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert move_blocked == (defender.hp == defender.max_hp)


def test_ふしぎなまもり_発動時に特性バーとログを表示する():
    """ふしぎなまもり: 攻撃を無効化したときは特性発動が公開され、無効化ログが記録される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    assert not defender.ability.revealed
    t.run_move(battle, 0)
    assert defender.ability.revealed


def test_ふしょく_どくどくではがねタイプにももうどくが入る():
    """ふしょく: 技（どくどく）経由でも、はがねタイプの相手にもうどくを付与できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ヤトウモリ", ability_name="ふしょく", move_names=["どくどく"])],
        team1=[Pokemon("コイル")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_ふしょく_どく技がはがねタイプに無効化されると追加効果も発動しない():
    """ふしょく: どく技自体がはがねタイプへのタイプ相性で無効化された場合、
    ふしょくを持っていても追加効果（どく付与）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ヤトウモリ", ability_name="ふしょく", move_names=["どくづき"])],
        team1=[Pokemon("コイル")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    defender = battle.actives[1]
    assert defender.hp == defender.max_hp
    assert not defender.ailment.is_active


@pytest.mark.parametrize(
    "target_name, ailment_name",
    [
        ("フシギダネ", "どく"),  # くさ/どくタイプ
        ("フシギダネ", "もうどく"),  # くさ/どくタイプ
        ("コイル", "どく"),  # でんき/はがねタイプ
        ("コイル", "もうどく"),  # でんき/はがねタイプ
    ]
)
def test_ふしょく_免疫タイプにもどくが入る(target_name: str, ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふしょく")],
        team1=[Pokemon(target_name)],
    )
    source = battle.actives[0]
    target = battle.actives[1]

    assert battle.ailment_manager.apply(target, ailment_name, source=source)
    assert target.ailment.name == ailment_name


def test_ふしょく_相手のどくのトゲには効果がない():
    """ふしょく: 相手の特性どくのトゲによる付与はふしょくの効果対象外であり、
    ふしょく持ちがはがね・どくタイプなら通常どおり毒状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくのトゲ")],
        team1=[Pokemon("コイル", ability_name="ふしょく", move_names=["たいあたり"])],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 1)
    assert not battle.actives[1].ailment.is_active


def test_ふとうのけん_Aが既に最大でも特性は消費される():
    """ふとうのけん: こうげきが既に最大まで上がっているため特性が不発した場合でも、
    その戦闘で特性を再度発動させることはできなくなる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ザシアン(れきせん)", ability_name="ふとうのけん")],
        team1=[Pokemon("カビゴン")],
    )
    bench = battle.get_team(battle.players[0])[1]
    battle.modify_stats(bench, {"atk": +6})

    t.run_switch(battle, 0, 1)
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 6
    assert not mon.ability.enabled

    t.run_switch(battle, 0, 0)
    t.run_switch(battle, 0, 1)
    assert mon.boosts["atk"] == 0


def test_ふとうのけん_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ザシアン(れきせん)", ability_name="ふとうのけん")],
    )
    mon = battle.actives[1]
    assert not mon.ability.enabled
    assert mon.boosts["atk"] == 0


def test_ふとうのけん_かがくへんかガス解除後に発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス"), Pokemon("ライチュウ")],
        team1=[Pokemon("ザシアン(れきせん)", ability_name="ふとうのけん")],
    )
    mon = battle.actives[1]
    assert mon.boosts["atk"] == 0

    t.run_switch(battle, 0, 1)
    assert mon.boosts["atk"] == 1


def test_ふとうのけん_初登場でAが1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ザシアン(れきせん)", ability_name="ふとうのけん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 1


def test_ふみん_すでにねむり状態のポケモンを場に出すと即座に回復する():
    """ふみん: 元の特性がふみんのポケモンが、特性を書き換えられてねむり状態になった後、
    交代でベンチに戻ると特性はふみんに戻る（ねむりは残る）。この状態のポケモンを再び
    場に出すと、場に出た直後に特性の効果でねむりが治る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["スキルスワップ"])],
        team1=[
            Pokemon("カビゴン", ability_name="ふみん"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
    )
    defender = battle.actives[1]
    # スキルスワップで特性を入れ替え、ふみんの効果を持たない状態にする
    t.run_move(battle, 0)
    assert defender.ability.name == "せいでんき"
    assert defender.base_ability == "ふみん"

    # 特性がふみんでない間にねむり状態にする
    assert battle.ailment_manager.apply(defender, "ねむり", count=3)

    # ベンチに戻ると特性は元のふみんに戻るが、ねむりはそのまま残る
    t.run_switch(battle, 1, 1)
    bench = battle.get_team(battle.players[1])[0]
    assert bench.ability.name == "ふみん"
    assert bench.ailment.name == "ねむり"

    # 再び場に出すと、場に出た直後にふみんの効果でねむりが治る
    t.run_switch(battle, 1, 0)
    active = battle.actives[1]
    assert active.ability.name == "ふみん"
    assert not active.ailment.is_active


def test_ふみん_どくびしと同時に発生した場合はどくびしの毒付与が不発してから回復する():
    """ふみん: すでにねむり状態のふみんのポケモンを、どくびしが設置されたサイドに
    出した場合、どくびしのどく付与判定はねむり状態により不発してから、ふみんの
    効果でねむりが治る（どくびしの効果は防がれる）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["スキルスワップ"])],
        team1=[
            Pokemon("カビゴン", ability_name="ふみん"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
        side1={"どくびし": 2},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.ailment_manager.apply(defender, "ねむり", count=3)

    t.run_switch(battle, 1, 1)
    t.run_switch(battle, 1, 0)
    active = battle.actives[1]

    # ねむりは治り、どくびしのどくも付与されない
    assert not active.ailment.is_active


def test_ふゆう_かがくへんかガスで浮遊が無効化される():
    """ふゆう: かがくへんかガスの効果中は特性が無効化され、地面にいる扱いになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ドガース", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    assert not mon.ability.enabled
    assert not battle.query.is_floating(mon)


def test_ふゆう_かたやぶりでじめん技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
    )
    defender, _ = battle.actives
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp


def test_ふゆう_じめん技が通らない():
    """ふゆう: ふゆう持ちはじめん技を無効化できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
    )
    defender, _ = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp


def test_ふゆう_じゅうりょく中は浮遊が無効化される():
    """ふゆう: じゅうりょく状態では地面にいる扱いになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ")],
        field={"じゅうりょく": 99},
    )
    assert not battle.query.is_floating(battle.actives[0])


def test_ふゆう_浮いている():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ")]
    )
    assert battle.query.is_floating(battle.actives[0])


def test_フラワーギフト_ばんのうがさ所持時は攻撃補正が発動しない():
    battle = t.start_battle(
        team0=[Pokemon(
            "チェリム",
            ability_name="フラワーギフト",
            item_name="ばんのうがさ",
            move_names=["たいあたり"],
        )],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_フラワーギフト_晴れ中でも物理技を受けたときの防御補正は変化しない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("チェリム", ability_name="フラワーギフト")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 4096


def test_フラワーギフト_晴れ中でも特殊技の攻撃補正は変化しない():
    battle = t.start_battle(
        team0=[Pokemon("チェリム", ability_name="フラワーギフト", move_names=["はかいこうせん"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_フラワーギフト_晴れ中に特殊技を受けると特防補正が1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はかいこうせん"])],
        team1=[Pokemon("チェリム", ability_name="フラワーギフト")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 6144


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


def test_フラワーベール_あくびのねむけを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="フラワーベール")],
        team1=[Pokemon("ピカチュウ", move_names=["あくび"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert not battle.actives[0].has_volatile("ねむけ")


def test_フラワーベール_いかくによる能力低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="フラワーベール")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].boosts["atk"] == 0


def test_フラワーベール_かたやぶりで状態異常を防げない():
    battle = t.start_battle(
        team0=[Pokemon("チコリータ", ability_name="フラワーベール")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["どくどく"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.ailment.name == "もうどく"


def test_フラワーベール_かたやぶりで能力低下を防げない():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="フラワーベール")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == -1


def test_フラワーベール_くさタイプでないと保護しない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="フラワーベール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "ねむり")
    assert mon.ailment.is_active


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_フラワーベール_くさタイプへの状態異常を防ぐ(ailment_name: AilmentName):
    # くさ単タイプのチコリータを使い、どく等の複合タイプによる免疫と混同しないようにする
    battle = t.start_battle(
        team0=[Pokemon("チコリータ", ability_name="フラワーベール")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, ailment_name)
    assert not mon.ailment.is_active


def test_フラワーベール_相手由来の能力低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="フラワーベール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = {k: v for k, v in stats.items() if v > 0}

    assert expected == battle.modify_stats(mon0, stats, source=mon1)


def test_フラワーベール_自己による能力低下は防げない():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="フラワーベール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, _ = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}

    assert stats == battle.modify_stats(mon0, stats, source=mon0)


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


def test_ぶきよう_くろいてっきゅうの効果を無視する():
    """ぶきよう: くろいてっきゅうの浮遊無効化・すばやさ半減の効果をともに無視する"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", ability_name="ぶきよう", item_name="くろいてっきゅう")],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    base_speed = mon.stats["spe"]
    assert battle.speed_calculator.calc_effective_speed(mon) == base_speed

    # くろいてっきゅうの浮遊無効化を受けないため、ひこうタイプの免疫が残りじしんが無効
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp


def test_ぶきよう_フォルムチェンジアイテムの効果が発動しない():
    """ぶきよう: だいこんごうだまを持っていてもディアルガはオリジンフォルムにならない"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", ability_name="ぶきよう", item_name="だいこんごうだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ディアルガ"


def test_ブレインフォース_たつじんのおびと併用すると累積して1_5倍になる():
    """ブレインフォース: たつじんのおびと両立すると効果が累積してダメージ1.5倍になる"""
    battle = t.start_battle(
        team0=[
            Pokemon(
                "ピカチュウ",
                ability_name="ブレインフォース",
                item_name="たつじんのおび",
                move_names=["でんきショック"],
            )
        ],
        team1=[Pokemon("ゼニガメ")],
    )
    t.run_move(battle, 0)
    # 1.25倍(5120)と1.2倍(4915)が固定小数点演算で逐次適用されるため、
    # 端数処理の結果ちょうど1.5倍(6144)ではなく6143になる
    assert 6143 == battle.damage_calculator.damage_modifier


def test_ブレインフォース_効果抜群のとき強化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ブレインフォース", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ")],
    )
    t.run_move(battle, 0)
    assert 5120 == battle.damage_calculator.damage_modifier


def test_ブレインフォース_等倍のときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ブレインフォース", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    # でんきショックはノーマルタイプに等倍のため、ブレインフォースは発動しない
    assert 4096 == battle.damage_calculator.damage_modifier


def test_プリズムアーマー_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="プリズムアーマー")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


def test_プリズムアーマー_効果抜群ダメージを0_75倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じしん"])],
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


def test_プレッシャー_相手のPP消費が1増える():
    """プレッシャー: プレッシャー持ちを対象にした技のPP消費が通常+1になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
    )
    attacker, _ = battle.actives
    move = attacker.moves[0]
    pp_before = move.pp
    t.run_move(battle, 0)
    assert pp_before - move.pp == 2


def test_プレッシャー_かたやぶりの影響を受けない():
    """プレッシャー: PP消費はかたやぶりが適用されるより前に確定するため、
    かたやぶり所持者が技を使ってもPP消費が通常+1になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
    )
    attacker, _ = battle.actives
    move = attacker.moves[0]
    pp_before = move.pp
    t.run_move(battle, 0)
    assert pp_before - move.pp == 2


def test_プレッシャー_ふういんは自分対象の技だがPP消費が増える():
    """プレッシャー: ふういんは自分を対象に選択する技だが、例外的にプレッシャーの影響を受ける"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふういん"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
    )
    attacker, _ = battle.actives
    move = attacker.moves[0]
    pp_before = move.pp
    t.run_move(battle, 0)
    assert pp_before - move.pp == 2


def test_プレッシャー_まもるで防がれてもPP消費が増える():
    """プレッシャー: まもる状態で防いだときであってもPP消費が通常+1になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "まもる", count=1)
    move = attacker.moves[0]
    pp_before = move.pp
    t.run_move(battle, 0)
    assert pp_before - move.pp == 2


def test_プレッシャー_命中しなかった場合もPP消費が増える():
    """プレッシャー: 技が命中しなかったときであってもPP消費が通常+1になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふぶき"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
        accuracy=0,
    )
    attacker, _ = battle.actives
    move = attacker.moves[0]
    pp_before = move.pp
    t.run_move(battle, 0)
    assert pp_before - move.pp == 2


def test_プレッシャー_のろいはゴーストタイプのときのみPP消費が増える():
    """プレッシャー: のろいはゴーストタイプが使う"呪い"のときのみ影響を受け、
    それ以外のタイプが使う"鈍い"は影響を受けない"""
    battle_ghost = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
    )
    attacker_ghost, _ = battle_ghost.actives
    move_ghost = attacker_ghost.moves[0]
    pp_before_ghost = move_ghost.pp
    t.run_move(battle_ghost, 0)
    assert pp_before_ghost - move_ghost.pp == 2

    battle_normal = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["のろい"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
    )
    attacker_normal, _ = battle_normal.actives
    move_normal = attacker_normal.moves[0]
    pp_before_normal = move_normal.pp
    t.run_move(battle_normal, 0)
    assert pp_before_normal - move_normal.pp == 1


def test_プレッシャー_自分を対象にする技はPP消費が増えない():
    """プレッシャー: 基本的に自分が対象の技（つるぎのまい等）はプレッシャーの影響を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
        team1=[Pokemon("カビゴン", ability_name="プレッシャー")],
    )
    attacker, _ = battle.actives
    move = attacker.moves[0]
    pp_before = move.pp
    t.run_move(battle, 0)
    assert pp_before - move.pp == 1


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


def test_ヘドロえき_おおきなねっこ持ちの相手には1_3倍のダメージを与える():
    """ヘドロえき: 攻撃側がおおきなねっこを持つ場合、ヘドロえきのダメージは1.3倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="おおきなねっこ", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン", ability_name="ヘドロえき")],
    )
    t.fix_damage(battle, 100)
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # 吸収量50に対しおおきなねっこ補正(5324/4096倍、五捨五超入)をかけた65がダメージになる
    assert hp_before - attacker.hp == 65


def test_ヘドロえき_通常の回復には影響しない():
    """ヘドロえき: drain以外の理由の回復には影響しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこさいせい"])],
        team1=[Pokemon("カビゴン", ability_name="ヘドロえき")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ヘヴィメタル_かたやぶりで無効化されおもさが基本値になる():
    """ヘヴィメタル: かたやぶり持ちの技を受けると特性が無視され、
    おもさを参照する技（くさむすび）の威力が基本のおもさ基準になる。
    ドータクン(187.0kg)はヘヴィメタルで374.0kg扱いとなり本来威力120だが、
    かたやぶりを受けると187.0kgのまま(威力100)で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", ability_name="かたやぶり", move_names=["くさむすび"])],
        team1=[Pokemon("ドータクン", ability_name="ヘヴィメタル")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_ヘヴィメタル_おもさが基本値の2倍になる():
    """ヘヴィメタル: 通常時はおもさを2倍にする。
    ドータクン(187.0kg)は374.0kgとなり、くさむすびの威力は120になる。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさむすび"])],
        team1=[Pokemon("ドータクン", ability_name="ヘヴィメタル")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 120


def test_ヘドロえき_マジックガード持ちの相手にはダメージを与えられない():
    """ヘドロえき: 攻撃側がマジックガードを持つ場合、ダメージを与えられない（回復効果も無くなる）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン", ability_name="ヘドロえき")],
    )
    attacker, defender = battle.actives
    hp_a0, hp_d0 = attacker.hp, defender.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_a0
    assert defender.hp < hp_d0


def test_ヘドロえき_みがわり状態の相手にもダメージを与える():
    """ヘドロえき: 相手のみがわり状態を無視してダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン", ability_name="ヘドロえき", move_names=["みがわり"])],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 1)
    assert defender.has_volatile("みがわり")
    hp_a0, hp_d0 = attacker.hp, defender.hp
    t.run_move(battle, 0)
    # みがわりがダメージを肩代わりするため本体のHPは変化しない
    assert defender.hp == hp_d0
    # ヘドロえきのダメージはみがわりを無視して攻撃側に入る
    assert attacker.hp < hp_a0


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


def test_へんげんじざい_単タイプで技タイプと一致する場合は発動しない():
    """既に単タイプで使用技のタイプと一致している場合は特性が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="へんげんじざい", move_names=["10まんボルト", "ひのこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert attacker.types == ["でんき"]
    # 発動していないため、続けて別タイプの技を出すと発動する
    t.run_move(battle, 0, 1)
    assert attacker.types == ["ほのお"]


def test_へんげんじざい_複合タイプの片方が技タイプと一致していても単タイプになる():
    """複合タイプを持つ場合、片方が技タイプと一致していても、技タイプの単タイプに変化する。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", ability_name="へんげんじざい", move_names=["はっぱカッター"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.types == ["くさ", "どく"]

    t.run_move(battle, 0, 0)
    assert attacker.types == ["くさ"]


def test_へんげんじざい_変化技でも発動する():
    """攻撃技だけでなく変化技を使用したときも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="へんげんじざい", move_names=["おにび"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert attacker.types == ["ほのお"]


def test_へんげんじざい_テラスタル中は発動しない():
    """テラスタル中はへんげんじざいが発動せず、テラスタイプが維持される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="へんげんじざい", move_names=["ひのこ"], tera_type="みず")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.terastallize()

    t.run_move(battle, 0, 0)
    assert attacker.types == ["みず"]


def test_へんげんじざい_かがくへんかガスの効果中は発動しない():
    """かがくへんかガスで特性が無効化されている間は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="へんげんじざい", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    attacker = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert attacker.types == ["ノーマル"]


def test_へんげんじざい_わるあがきでは発動しない():
    """PP切れでわるあがきになった場合はタイプを持たないため発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="へんげんじざい", move_names=["ひのこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.moves[0].pp = 0

    t.run_move(battle, 0, 0)
    assert attacker.types == ["ノーマル"]


def test_へんげんじざい_ほのおタイプでないもえつきるは失敗し発動しない():
    """もえつきるがほのおタイプ不足で失敗する場合、失敗判定がタイプ変化より先に行われるため発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="へんげんじざい", move_names=["もえつきる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    t.run_move(battle, 0, 0)
    assert battle.move_executor.action_success is False
    assert attacker.types == ["ノーマル"]
    assert defender.hp == hp_before


def test_へんげんじざい_でんきタイプでないでんこうそうげきは失敗し発動しない():
    """でんこうそうげきがでんきタイプ不足で失敗する場合、失敗判定がタイプ変化より先に行われるため発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="へんげんじざい", move_names=["でんこうそうげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    t.run_move(battle, 0, 0)
    assert battle.move_executor.action_success is False
    assert attacker.types == ["ノーマル"]
    assert defender.hp == hp_before


def test_へんげんじざい_もりののろいで追加されたタイプは発動時にリセットされる():
    """もりののろいで追加されたタイプを持つ状態から発動すると、技タイプの単タイプになる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="へんげんじざい", move_names=["もりののろい", "ひのこ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert attacker.types == ["くさ"]

    # 既にへんげんじざいは発動済みのため、以降のタイプは変化しない
    t.run_move(battle, 0, 1)
    assert attacker.types == ["くさ"]


def test_へんしょく_ちからずくの技を受けてもタイプ変化しない():
    """へんしょく: 特性ちからずくの効果が発動した技（secondary_effect フラグ持ち）を
    受けた場合はタイプが変化しない（docs/spec/abilities/へんしょく.md参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["かえんほうしゃ"])],
        team1=[Pokemon("ピカチュウ", ability_name="へんしょく")],
        accuracy=100,
        secondary_chance=0.0,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert "ほのお" not in defender.types


def test_へんしょく_多段技では最終ヒット後にタイプ変化する():
    """へんしょく: 多段技の最終ヒット後にのみタイプが変化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ダブルアタック"])],
        team1=[Pokemon("ヤドン", ability_name="へんしょく")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert "ノーマル" in defender.types


def test_へんしょく_攻撃技を受けた後に技タイプになる():
    """へんしょく: 攻撃技のダメージを受けた後、その技のタイプに変化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
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
    t.run_move(battle, 0)
    assert defender.types == ["でんき"]


def test_へんしょく_ひんし時は発動しない():
    """へんしょく: 攻撃技でひんしになったときはタイプ変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("カクレオン", ability_name="へんしょく")],
        accuracy=100,
    )
    _, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert defender.types == ["ノーマル"]


def test_へんしょく_わるあがきでは発動しない():
    """へんしょく: わるあがき（type == ""）を受けてもタイプ変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["わるあがき"])],
        team1=[Pokemon("カクレオン", ability_name="へんしょく")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.types == ["ノーマル"]


def test_へんしょく_特性によるタイプ変換後の技タイプになる():
    """へんしょく: フェアリースキン等でタイプ変換された技を受けた場合、最終タイプに変化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリースキン", move_names=["ハイパーボイス"])],
        team1=[Pokemon("カクレオン", ability_name="へんしょく")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.types == ["フェアリー"]


@pytest.mark.parametrize("attacker_name, random_val, expected_ailment", [
    ("ピカチュウ", 0.0, "どく"),
    ("フシギダネ", 0.09, "まひ"),
])
def test_ほうし_接触技で状態異常付与(attacker_name: str, random_val: float, expected_ailment: str):
    """ほうし: 乱数範囲によってどく・まひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほうし")],
        team1=[Pokemon(attacker_name, move_names=["たいあたり"])],
        accuracy=100,
    )
    battle.random.random = lambda: random_val

    t.run_move(battle, 1)

    assert battle.actives[1].ailment.name == expected_ailment


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
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほろびのボディ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"ほろびのうた": 3}
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)

    assert attacker.has_volatile("ほろびのうた")
    assert defender.has_volatile("ほろびのうた")


def test_ほろびのボディ_接触技で双方ほろびのうた():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほろびのボディ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)

    assert defender.has_volatile("ほろびのうた")
    assert attacker.has_volatile("ほろびのうた")


def test_ほろびのボディ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほろびのボディ")],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)

    assert not defender.has_volatile("ほろびのうた")
    assert not attacker.has_volatile("ほろびのうた")


def test_ぼうじん_すなあらしダメージを無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぼうじん")],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 5),
    )
    defender, attacker = battle.actives
    t.end_turn(battle)
    assert defender.hp == defender.max_hp


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
        ailment0=("どく", None),
        volatile0={"かいふくふうじ": 3},
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_ポイズンヒール_かがくへんかガス中は通常のどくダメージを受ける():
    """かがくへんかガスでポイズンヒールが無効化されている間は、通常どおりどくダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability_name="ポイズンヒール")],
        team1=[Pokemon("ドガース", ability_name="かがくへんかガス")],
        ailment0=("どく", None),
    )
    mon = battle.actives[0]
    hp_before = mon.hp
    t.end_turn(battle)
    assert mon.hp == hp_before - max(1, mon.max_hp // 8)


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく"]
)
def test_ポイズンヒール_どく状態で1_8回復する(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability_name="ポイズンヒール")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(ailment_name, None),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
