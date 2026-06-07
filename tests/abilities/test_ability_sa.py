"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle

import pytest

from jpoke import Pokemon
from jpoke.enums import Command

from .. import test_utils as t


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
    assert battle.move_executor.critical_rank == 3
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
