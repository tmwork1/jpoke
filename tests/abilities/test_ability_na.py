"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.enums import Interrupt

from .. import test_utils as t


def test_ナイトメア_ぜったいねむりのゆめうつつ状態でもダメージを受ける():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン")],
        ailment1=("ゆめうつつ", None)
    )
    mon, foe = battle.actives
    t.end_turn(battle)
    assert mon.ability.revealed
    assert foe.hp == foe.max_hp - foe.max_hp // 8


def test_ナイトメア_ダメージ量は最大HPの1_8切り捨て():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3)
    )
    _, foe = battle.actives
    t.end_turn(battle)
    assert foe.hp == foe.max_hp - foe.max_hp // 8


def test_ナイトメア_ねむりでないとき発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン")],
    )
    mon, foe = battle.actives
    t.end_turn(battle)
    assert not mon.ability.revealed
    assert foe.hp == foe.max_hp


def test_ナイトメア_ねむり中相手のHPを削る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3)
    )
    mon, foe = battle.actives
    t.end_turn(battle)
    assert mon.ability.revealed
    assert foe.hp < foe.max_hp


def test_ナイトメア_マジックガードでダメージ無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン", ability_name="マジックガード")],
        ailment1=("ねむり", 3)
    )
    _, foe = battle.actives
    t.end_turn(battle)
    assert foe.hp == foe.max_hp


def test_なまけ_1ターン行動して次のターンはさぼる():
    """なまけ: 1ターン行動すると次のターンは行動スキップになる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="なまけ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    _, defender = battle.actives

    # ターン1: 行動できる
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp

    # ターン2: 行動できない
    hp = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp

    # ターン3: 行動できる
    t.run_move(battle, 0)
    assert defender.hp < hp


def test_なまけ_ねむり中は行動可否のカウントが消費されない():
    """なまけ: ねむり状態で行動できないターンはXを消費しない（第五世代以降仕様）。
    起きたターンには通常通り行動でき、その後は行動→なまけの交互パターンに戻る。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="なまけ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon, defender = battle.actives

    # ねむり中（2ターン）はなまけの行動可否状態が変化しない
    t.run_move(battle, 0)
    assert mon.ability.state == "can_act"
    assert defender.hp == defender.max_hp
    t.run_move(battle, 0)
    assert mon.ability.state == "can_act"
    assert defender.hp == defender.max_hp

    # 起きたターンは通常通り行動できる（Xが消費されていなかったので行動可能）
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert not mon.has_ailment("ねむり")
    assert defender.hp < hp_before

    # 次のターンはなまけて行動できない
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_にげごし_HPが半分以下になると交代():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.step()

    assert battle.actives[0] is not defender


def test_にげごし_こんらん自傷では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.modify_hp(defender, v=-1, reason="self_attack")

    assert battle.actives[0] is defender


def test_にげごし_ちからずくの技のダメージでも発動する():
    """相手がちからずくで追加効果技（secondary_effect フラグ持ち）を使用した場合の
    ダメージ(move_damage)でも、Championsではにげごしが通常どおり発動する
    （第七世代からSVまでは不発だったが、Championsではこの制限が撤廃されている。
    docs/spec/abilities/にげごし.md参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", ability_name="ちからずく", move_names=["かえんほうしゃ"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    attacker.executed_move = attacker.moves[0]
    defender.hp = defender.max_hp
    battle.modify_hp(defender, v=-(defender.max_hp // 2 + 1), source=attacker, reason="move_damage")

    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.EMERGENCY


def test_にげごし_はらだいこの自己HP消費では発動しない():
    """はらだいこのHP消費(self_cost)ではにげごしが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし", move_names=["はらだいこ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp * 9 // 10
    t.run_move(battle, 0)

    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_にげごし_みがわりの自己HP消費では発動しない():
    """みがわりのHP消費(self_cost)ではにげごしが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし", move_names=["みがわり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp * 6 // 10
    t.run_move(battle, 0)

    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_にげごし_やけどダメージでも発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("やけど", None),
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.step()

    assert battle.actives[0] is not defender


def test_にげごし_控えがいない場合は発動しない():
    """交代先の控えがいない場合はにげごしが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.step()

    assert battle.actives[0] is defender


def test_にげごし_相手のいたみわけを受けても発動しない():
    """相手のいたみわけによるHP均等化(pain_split)ではにげごしが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", move_names=["いたみわけ"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp
    attacker = battle.actives[1]
    attacker.hp = 1
    t.run_move(battle, 1)

    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_にげごし_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="にげごし"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2
    battle.step()

    assert battle.actives[0] is defender


def test_ぬめぬめ_すばやさが最低ランクのときは特性が発動しない():
    """ぬめぬめ: 攻撃者のすばやさがすでに最低ランクのときは、ランクが変化せず特性バーも現れない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぬめぬめ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    attacker.rank["spe"] = -6
    t.run_move(battle, 1)

    assert not defender.ability.revealed
    assert attacker.rank["spe"] == -6


def test_ぬめぬめ_ひんしになっても発動する():
    """ぬめぬめ: 自身が直接攻撃でひんしになったときも攻撃者のすばやさを下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぬめぬめ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    battle.modify_hp(defender, v=-(defender.max_hp - 1))
    t.run_move(battle, 1)

    assert defender.fainted
    assert attacker.rank["spe"] == -1


def test_ぬめぬめ_みがわりで防いだときは発動しない():
    """ぬめぬめ: 自身のみがわりが技を防いだとき（実HPダメージ0）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぬめぬめ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 1)

    assert not defender.ability.revealed
    assert attacker.rank["spe"] == 0


def test_ぬめぬめ_直接攻撃で攻撃者のSが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぬめぬめ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.ability.revealed
    assert attacker.rank["spe"] == -1


def test_ぬめぬめ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぬめぬめ")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)

    assert not defender.ability.revealed
    assert attacker.rank["spe"] == 0


def test_ねつこうかん_こうげきがすでに最大なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    defender.rank["atk"] = 6
    t.run_move(battle, 1)

    assert defender.rank["atk"] == 6
    assert not defender.ability.revealed


def test_ねつこうかん_ひんし時は発動しない():
    """ねつこうかん: ほのお技でひんしになった場合はこうげきが上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ねつこうかん"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)

    assert defender.fainted
    assert defender.rank["atk"] == 0


def test_ねつこうかん_ほのお以外の技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert defender.rank["atk"] == 0
    assert not defender.ability.revealed


def test_ねつこうかん_ほのお技を受けるとこうげき1段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert defender.rank["atk"] == 1
    assert defender.ability.revealed


def test_ねつこうかん_まもるで防がれたときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        volatile0={"まもる": 1},
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert defender.rank["atk"] == 0
    assert not defender.ability.revealed


def test_ねつこうかん_みがわり状態では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 1)

    assert defender.rank["atk"] == 0
    assert not defender.ability.revealed


def test_ねつこうかん_やけど状態にならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert not battle.ailment_manager.apply(battle.actives[0], "やけど")


def test_ねつぼうそう_やけど状態でない場合は倍率なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつぼうそう", move_names=["でんきショック"])],
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
def test_ねつぼうそう_やけど状態で特殊技の威力が1_5倍(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつぼうそう", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("やけど", None),
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.power_modifier


def test_ねんちゃく_相手による道具変更をブロックする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.item_manager.can_change_item(target=target, source=source)


def test_ねんちゃく_自己起因の道具変更は阻害しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, _ = battle.actives
    assert battle.item_manager.can_change_item(target=target, source=target)


def test_ねんちゃく_道具なしでも相手による道具変更をブロックする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.item_manager.can_change_item(source=source, target=target)


def test_のろわれボディ_接触時に30パーセントでかなしばり():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="のろわれボディ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.29)
    t.run_move(battle, 1)
    assert battle.actives[1].has_volatile("かなしばり")


def test_のろわれボディ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="のろわれボディ")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.29)
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


def test_ノーガード_すながくれの命中率低下を無視して必中になる():
    """攻撃側ノーガード（すばやさで勝る）・防御側すながくれ、すなあらし下。
    ON_MODIFY_ACCURACYの実行順（すばやさ順）次第でノーガードが先に必中確定し、
    後続のすながくれハンドラがNoneに乗算してクラッシュしないことの回帰テストも兼ねる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーガード", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="すながくれ")],
        weather=("すなあらし", 5),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


def test_ノーガード_はりきりの命中率低下を無視して必中になる():
    """防御側ノーガード（すばやさで劣る）・攻撃側はりきりの物理技。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ノーガード")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


def test_ノーガード_ミラクルスキンの変化技命中率低下を無視して必中になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーガード", move_names=["どくどく"])],
        team1=[Pokemon("カビゴン", ability_name="ミラクルスキン")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None
    assert battle.actives[1].has_ailment("もうどく")


def test_ノーガード_一撃必殺技でも必中になる():
    """こおりタイプでない攻撃側がぜったいれいどを使っても必中になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーガード", move_names=["ぜったいれいど"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None
    assert battle.actives[1].fainted


def test_ノーガード_半無敵状態の相手にも命中する():
    """そらをとぶ中の相手にも、技限定の回避判定を経由せず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーガード", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"そらをとぶ": 1},
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


@pytest.mark.parametrize("weather,pokemon_name,move_name", [
    ("はれ", "ヒトカゲ", "ひのこ"),
    ("あめ", "ゼニガメ", "みずでっぽう"),
])
def test_ノーてんき_はれあめ威力補正が無効化される(weather: str, pokemon_name: str, move_name: str):
    """ノーてんき: 場にいる間ははれ/あめによるタイプ一致技の威力補正が無効になる"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき")],
        weather=(weather, 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_ノーてんき_かたやぶりでも天候効果無効化は貫通されない():
    """ノーてんき: 天候の影響を無くす効果はかたやぶりでも無視されない
    （エアロック・ノーてんきは mold_breaker_ignorable フラグを持たない）"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", ability_name="かたやぶり", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき")],
        weather=("はれ", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_ノーてんき_天候自体は解除されない():
    """ノーてんき: 天候の効果を無くすだけで天候自体は解除されず、経過ターンもカウントされ続ける。
    既に発動している天候をあまごい等で発動させようとすると失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン", ability_name="ノーてんき")],
        weather=("あめ", 3),
    )
    assert battle.raw_weather.name == "あめ"
    t.run_move(battle, 0)
    # 既にあめが降っているためあまごいは失敗し、天候・カウントとも変化しない
    assert battle.raw_weather.name == "あめ"
    assert battle.raw_weather.count == 3


def test_ノーてんき_場から退場すると天候効果が復活する():
    """ノーてんき: 交代して場から去ると天候の効果（威力補正）が復活する"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき"), Pokemon("コイル")],
        weather=("はれ", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier

    t.run_switch(battle, 1, 1)  # ノーてんき持ちを引っ込める
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_ノーマルスキン_ノーマルタイプに変えた技は強化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert "ノーマル" == battle.move_executor.move_type
    assert 4915 == battle.damage_calculator.power_modifier


def test_ノーマルスキン_元からノーマルタイプの技は威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_ノーマルスキン_わるあがきはタイプ変換も威力補正も対象外():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["わるあがき"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert "" == battle.move_executor.move_type
    assert 4096 == battle.damage_calculator.power_modifier


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
