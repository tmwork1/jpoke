"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.enums import Command
from jpoke.types import Stat, AilmentName, VolatileName

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
    assert battle.actives[0].rank["accuracy"] == -1


def test_はっこう_命中率低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう")],
        team1=[Pokemon("カビゴン", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["accuracy"] == 0


def test_はっこう_相手の回避率ランクを無視する():
    """はっこう: 攻撃時に相手の回避率ランク上昇を無視する（第九世代以降）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].rank["evasion"] = 6
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_はっこう_相手の回避率ランク低下も無視する():
    """はっこう: 相手の回避率ランクが下がっていても命中率を上げない（第九世代以降の仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はっこう", move_names=["ストーンエッジ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].rank["evasion"] = -1
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


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


def test_はらぺこスイッチ_テラスタル中はターン終了時に切り替わらない():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ", tera_type="あく")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle, command0=Command.TERASTAL_0)
    battle.step()
    mon = battle.actives[0]

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


def test_はりきり_命中率が低下():
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


def test_バトルスイッチ_交代時はシールドへ戻る():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability_name="バトルスイッチ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "ギルガルド(シールド)"


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


def test_バトルスイッチ_わるあがきでもブレードになる():
    """わるあがきは攻撃技扱いのため、変化技しか覚えていなくてもブレードフォルムになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["わるあがき"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == "ギルガルド(ブレード)"


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


def test_バトルスイッチ_溜め技の1ターン目でも発動する():
    """ソーラーブレード等の溜め技を使用した場合、溜めるターンでバトルスイッチが発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["ソーラーブレード"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == "ギルガルド(ブレード)"


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
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばんけん")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].rank["atk"] == 1


def test_ばんけん_ほえるを無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばんけん"), Pokemon("イーブイ")],
        team1=[Pokemon("カビゴン", move_names=["ほえる"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].name == "ピカチュウ"


def test_パンクロック_かたやぶりで無効():
    """パンクロック: かたやぶり持ちの音技はパンクロックの被ダメ軽減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability_name="パンクロック")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


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
    assert battle.actives[0].rank["spe"] == rank


def test_びんじょう_相手のランク上昇をコピーする():
    """びんじょう: 相手のランクが上昇したとき自分も同じランク上昇をする"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives

    assert battle.modify_stats(foe, {"atk": 2}, source=foe)
    assert binjou_mon.rank["atk"] == 2


def test_びんじょう_相手のランク低下はコピーしない():
    """びんじょう: 相手のランク低下はコピーしない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="びんじょう")],
        team1=[Pokemon("ピカチュウ")],
    )
    binjou_mon, foe = battle.actives

    assert battle.modify_stats(foe, {"atk": -2}, source=foe)
    assert binjou_mon.rank["atk"] == 0


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

    assert attacker.rank[stat] == 1


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


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 8192),
        ("でんきショック", 4096)
    ],
)
def test_ファーコート_物理技の防御が2倍になる(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="ファーコート")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == expected_modifier


def test_ふうりょくでんき_おいかぜ発生でじゅうでん():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
    )
    battle.side_managers[1].activate("おいかぜ", 4)
    assert battle.actives[1].has_volatile("じゅうでん")


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
    ]
)
def test_ふうりょくでんき_風技を受けるとじゅうでん(move_name: str, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="ふうりょくでんき")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("じゅうでん") == result


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
    assert mon.rank["spe"] == expected_rank


def test_ふしぎなうろこ_かたやぶりで無効():
    """ふしぎなうろこ: かたやぶり持ちの物理技はふしぎなうろこの防御補正を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
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


def test_ふしぎなまもり_変化技は通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ピジョット", ability_name="ふしぎなまもり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.rank["atk"] == -1


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


def test_ふゆう_浮いている():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ")]
    )
    assert battle.query.is_floating(battle.actives[0])


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
    battle.ailment_manager.apply(mon, "ねむり")
    assert mon.ailment.is_active


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_フラワーベール_くさタイプへの状態異常を防ぐ(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", ability_name="フラワーベール")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, ailment_name)
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
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこさいせい"])],
        team1=[Pokemon("カビゴン", ability_name="ヘドロえき")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


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
