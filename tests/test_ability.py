"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle

import pytest

from jpoke import Pokemon
from jpoke.core import AttackContext, EventContext
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import PLATE_TO_TYPE
from jpoke.enums import Event, Command
from jpoke.utils.type_defs import AilmentName, WeatherName

import test_utils as t


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

MULTI_TYPE_PLATE_CASES = [
    (plate_item_name, expected_type)
    for plate_item_name, expected_type in PLATE_TO_TYPE.items()
    if plate_item_name in ITEMS
]


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
def test_ひひいろのこどう_強天候は上書き不可(initial_weather: WeatherName):
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
def test_ひひいろのこどう_通常天候をはれで上書きする(initial_weather: WeatherName):
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
