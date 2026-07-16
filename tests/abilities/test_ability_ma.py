"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import PLATE_TO_TYPE
from jpoke.enums import LogCode

from .. import test_utils as t

MULTI_TYPE_PLATE_CASES = [
    (plate_item_name, expected_type)
    for plate_item_name, expected_type in PLATE_TO_TYPE.items()
    if plate_item_name in ITEMS
]


def test_マイティチェンジ_だっしゅつボタンの交代でも変化する():
    """マイティチェンジ: だっしゅつボタンによる割り込み交代でも発動する。"""
    battle = t.start_battle(
        team0=[
            Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ", item_name="だっしゅつボタン"),
            Pokemon("ライチュウ"),
        ],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.step()
    assert mon.name == "イルカマン(マイティ)"


def test_マイティチェンジ_ナイーブで交代するとマイティへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "イルカマン(マイティ)"


def test_マイティチェンジ_ひんし退場時は変化しない():
    battle = t.start_battle(
        team0=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    battle.modify_hp(mon, -mon.hp)
    assert not mon.alive
    t.run_switch(battle, 0, 1)
    assert mon.name == "イルカマン(ナイーブ)"


def test_マイティチェンジ_マイティ化後の再登場でもフォルムを維持する():
    battle = t.start_battle(
        team0=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "イルカマン(マイティ)"
    t.run_switch(battle, 0, 0)
    t.run_switch(battle, 0, 1)
    assert mon.name == "イルカマン(マイティ)"


def test_マイティチェンジ_既にマイティフォルムの場合は再変化しない():
    battle = t.start_battle(
        team0=[Pokemon("イルカマン(マイティ)", ability_name="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "イルカマン(マイティ)"
    assert not any(
        log.log == LogCode.ABILITY_TRIGGERED
        for log in battle.event_logger.logs
    )


def test_マイティチェンジ_発動時にABILITY_TRIGGEREDログが記録される():
    battle = t.start_battle(
        team0=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_switch(battle, 0, 1)
    triggered = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED
        and log.payload is not None
        and getattr(log.payload, "ability", None) == "マイティチェンジ"
    ]
    assert len(triggered) == 1


def test_マイペース_あばれる終了時の自傷こんらんを防ぐ():
    """マイペース: あばれる状態が終了して自身にこんらんが発生する際も防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース", move_names=["あばれる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=1, move_name="あばれる")
    battle.step()
    assert not attacker.has_volatile("あばれる")
    assert not attacker.has_volatile("こんらん")


def test_マイペース_あやしいひかりでこんらんにならない():
    """マイペース: 変化技（あやしいひかり）の効果によるこんらんも防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース")],
        team1=[Pokemon("ピカチュウ", move_names=["あやしいひかり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert not defender.has_volatile("こんらん")


def test_マイペース_いかくを無効化する():
    """マイペース: 第八世代からいかくによるこうげきランク低下を無効化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].boosts["atk"] == 0


def test_マイペース_いばるを受けてもランクは上昇しこんらんにならない():
    """マイペース: いばるの効果でこうげきは上昇するが、こんらんは防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース")],
        team1=[Pokemon("ピカチュウ", move_names=["いばる"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 2
    assert not defender.has_volatile("こんらん")


def test_まけんき_こうげきが最大のときはそれ以上上がらない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="まけんき")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.boosts["atk"] = 6
    battle.modify_stats(mon, {"def": -1}, source=battle.actives[1])
    assert mon.boosts["atk"] == 6


def test_まけんき_複数能力低下技で下がった数だけ発動する():
    # くすぐるはこうげき・ぼうぎょを1段階ずつ下げる技のため、まけんきが2回発動してこうげきが4段階分上昇する。
    # ただし上昇対象のこうげき自身もくすぐるで1段階下がっているため、差し引きの最終値は+3となる。
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="まけんき")],
        team1=[Pokemon("ピカチュウ", move_names=["くすぐる"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 3
    assert mon.boosts["def"] == -1


def test_マジシャン_なげつけるでダメージを与えても発動しない():
    """マジシャン: なげつけるは使用者自身のアイテムを消費して攻撃する技のため、
    ダメージを与えても相手のアイテムは奪えない（docs/spec/abilities/マジシャン.md）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", item_name="するどいくちばし", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not attacker.has_item()  # なげつけるの消費で自身のアイテムは失う
    assert defender.has_item()  # 相手のアイテムは奪えない


def test_マジシャン_ねんちゃくの相手からは奪えない():
    """マジシャン: 特性ねんちゃくの相手を倒さなかった場合、アイテムの奪取は阻止される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ねんちゃく", item_name="たべのこし")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not attacker.has_item()
    assert defender.has_item()


def test_マジシャン_ねんちゃくの相手でもひんしにさせれば奪える():
    """マジシャン: 特性ねんちゃくの相手でも、その攻撃でひんしにさせた場合は奪取を阻止されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ねんちゃく", item_name="たべのこし")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.modify_hp(defender, v=-(defender.hp - 1))
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.item.name == "たべのこし"
    assert not defender.has_item()


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


def test_マジックガード_いたみわけを受ける():
    """いたみわけ(pain_split)はマジックガードのブロック対象外なのでHP均等化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いたみわけ"])],
        team1=[Pokemon("ピカチュウ", ability_name="マジックガード")],
    )
    attacker, defender = battle.actives
    # マジックガードを持たないattacker側のHPを減らす
    battle.modify_hp(attacker, -(attacker.max_hp - 10))
    defender_hp = defender.hp  # 満タン
    expected_hp = (10 + defender_hp) // 2
    t.run_move(battle, 0)
    assert defender.hp == expected_hp


def test_マジックガード_いのちのたまの反動ダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ", ability_name="マジックガード", item_name="いのちのたま",
            move_names=["たいあたり"],
        )],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_マジックガード_こんらんの自傷ダメージは防げない():
    """マジックガード: こんらん状態の自傷ダメージ(self_attack)は無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    # 自傷を強制
    battle.test_option.trigger_volatile = True
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_マジックガード_すなあらしダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_マジックガード_どくダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_マジックガード_はらだいこの自己HP消費は防げない():
    """マジックガード: はらだいこ等の自己HP消費(self_cost)は無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == max_hp - (max_hp // 2)


def test_マジックガード_やけどダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_マジックガード_わるあがきの反動ダメージは防げない():
    """マジックガード: わるあがきの反動は通常の反動技と異なる仕様のため無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード", move_names=["わるあがき"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_マジックガード_技ダメージを受ける():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="マジックガード")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_マジックミラー_unreflectableフラグを持つ技は跳ね返さない():
    """マジックミラー: unreflectableフラグを持つうつしえは跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    # 跳ね返されず、通常通り相手の特性がコピーされる
    assert attacker.ability.name == "マジックミラー"


def test_マジックミラー_かがくへんかガスで無効化されている間は跳ね返さない():
    """マジックミラー: かがくへんかガス等で特性が無効化されている間は反射しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    battle.add_ability_disabled_reason(defender, "かがくへんかガス")
    t.run_move(battle, 0)
    assert not any(log.log == LogCode.MOVE_REFLECTED for log in battle.event_logger.logs)
    assert defender.boosts["atk"] == -1
    assert attacker.boosts["atk"] == 0


def test_マジックミラー_かたやぶりを持つ相手には発動しない():
    """マジックミラー: 攻撃側がかたやぶりを持つ場合、防御側特性が無効化され跳ね返せない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not any(log.log == LogCode.MOVE_REFLECTED for log in battle.event_logger.logs)
    assert defender.boosts["atk"] == -1
    assert attacker.boosts["atk"] == 0


def test_マジックミラー_ステルスロックを跳ね返す():
    """マジックミラー: ステルスロックを跳ね返し、使用者側に設置する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ステルスロック"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.get_side(attacker).get("ステルスロック").is_active
    assert not battle.get_side(defender).get("ステルスロック").is_active


def test_マジックミラー_ミラーアーマー持ちから受けた技はミラーアーマーで再度跳ね返される():
    """マジックミラー: ミラーアーマー持ちから能力を下げる変化技を受けた場合、
    マジックミラーで跳ね返した効果はミラーアーマーで跳ね返される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    # マジックミラーで跳ね返した効果がミラーアーマーで再度跳ね返され、マジックミラー側に低下が生じる
    assert attacker.boosts["atk"] == 0
    assert defender.boosts["atk"] == -1


def test_マジックミラー_ミラーアーマー持ちを攻撃した場合はミラーアーマーの反射が再度跳ね返されない():
    """マジックミラー: マジックミラー持ちがミラーアーマー持ちのランクを下げようとした場合、
    ミラーアーマーで跳ね返された効果はマジックミラーで跳ね返されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックミラー", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="ミラーアーマー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not any(log.log == LogCode.MOVE_REFLECTED for log in battle.event_logger.logs)
    # ミラーアーマーの反射で攻撃側(マジックミラー持ち)に低下が生じ、防御側は無傷
    assert attacker.boosts["atk"] == -1
    assert defender.boosts["atk"] == 0


def test_マジックミラー_変化技を跳ね返す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.boosts["atk"] == -1
    assert defender.boosts["atk"] == 0


def test_マジックミラー_攻撃技は跳ね返さない():
    """マジックミラー: 分類が変化以外の技（攻撃技）は反射対象外。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    _, defender = battle.actives
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert not any(log.log == LogCode.MOVE_REFLECTED for log in battle.event_logger.logs)
    assert defender.hp < hp_before


def test_マジックミラー_跳ね返った効果を自分のマジックミラーで再び跳ね返さない():
    """マジックミラー: 自分のマジックミラーで跳ね返ってきた効果を再び跳ね返すことはできない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックミラー", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    # 跳ね返された効果は使用者(attacker)に1回だけ適用され、再度跳ね返されない
    assert attacker.boosts["atk"] == -1
    assert defender.boosts["atk"] == 0


def test_マルチスケイル_HP満タンのとき半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="マルチスケイル")],
    )
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
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_マルチスケイル_こんらんの自傷ダメージは半減しない():
    """マルチスケイル: HPが満タンでも、こんらんの自傷ダメージ（内部技"_こんらん"）は半減しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マルチスケイル")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096
    assert attacker.hp < attacker.max_hp


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


def test_マルチタイプ_プレートなしなら自分の道具変更は防がれない():
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ", item_name="いのちのたま")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert battle.item_manager.can_change_item(target=target, source=source)


def test_マルチタイプ_プレートの奪取を阻止する():
    """マルチタイプ: はたきおとすでプレートを奪取できない。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ", item_name="せいれいプレート")],
        team1=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    # プレートが奪取されずに残っている
    assert mon.item.name == "せいれいプレート"
    assert mon.has_item()


def test_マルチタイプ_相手がプレートを持たなければ通常の道具変更を防がない():
    """交換判定であっても、自分・相手ともプレートを持たなければ道具変更は妨げられない"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ")],
        team1=[Pokemon("ピカチュウ", item_name="いのちのたま")],
    )
    target, source = battle.actives
    assert battle.item_manager.can_change_item(target=target, source=source, is_exchange=True)


def test_マルチタイプ_相手がプレートを持つ場合トリックすりかえ相当の交換が失敗する():
    """相手がプレートを持っている場合、自分がプレートを持っていなくても道具交換自体が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ")],
        team1=[Pokemon("ピカチュウ", item_name="せいれいプレート")],
    )
    before = [mon.item.name for mon in battle.actives]
    assert not battle.item_manager.swap_items()
    assert [mon.item.name for mon in battle.actives] == before


def test_ミイラ_かがくへんかガス保持者がとくせいなし状態なら上書きできる():
    """ミイラ: かがくへんかガス保持者自身がとくせいなし状態（いえき等）の場合は例外的に上書きできる"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", ability_name="かがくへんかガス", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ミイラ")],
        volatile0={"とくせいなし": 3},
    )
    attacker, defender = battle.actives
    # とくせいなしによりガス効果が切れ、相手のミイラが有効化されていることを確認
    assert defender.ability.enabled
    t.run_move(battle, 0)
    assert attacker.ability.base_name == "ミイラ"


def test_ミイラ_かがくへんかガス保持者には発動しない():
    """ミイラ: かがくへんかガスはuncopyableのため上書きできない"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", ability_name="かがくへんかガス", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ミイラ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.base_name == "かがくへんかガス"


def test_ミイラ_接触技で攻撃した相手の特性がミイラになる():
    """ミイラ: 直接攻撃でダメージを受けたとき攻撃者の特性をミイラにする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ミイラ")],
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


def test_ミストメイカー_特性再有効化時にも発動する():
    """ミストメイカー: かがくへんかガス解除後に特性が再有効化されると再発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミストメイカー")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    # かがくへんかガスにより特性が無効化されているのでフィールドは展開されていない
    assert battle.terrain.name == ""
    # かがくへんかガスの無効化を解除すると特性が再発動してミストフィールドが展開される
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert battle.terrain.name == "ミストフィールド"
    assert battle.terrain.count == 5


@pytest.mark.parametrize(
    "move_name",
    ["アクアブレイク", "シェルブレード"],
)
def test_みずがため_アクアブレイクとシェルブレードでは追加効果の後に発動する(move_name: str):
    """みずがため: アクアブレイク/シェルブレードを受けた場合、
    ぼうぎょ低下の追加効果が先に適用されてからみずがための2段階上昇が発動する。
    順序によってランク上限のクランプ挙動が変わるため、B+5から検証する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="みずがため")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    assert battle.modify_stats(defender, {"def": 5}, source=defender)
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)  # 追加効果(ぼうぎょ低下)を確定発動させる
    t.run_move(battle, 1)
    # 追加効果(B-1)が先に適用され 5→4、その後にみずがため(B+2)が発動し 4→6。
    # 順序が逆であれば 5→7(+6にクランプ)→+5 になってしまう。
    assert defender.boosts["def"] == 6


@pytest.mark.parametrize(
    "move_name, expected_rank",
    [
        ("みずでっぽう", 2),
        ("たいあたり", 0)
    ],
)
def test_みずがため_みず技でBが2段階上がる(move_name: str, expected_rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="みずがため")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["def"] == expected_rank


def test_みずがため_被弾して瀕死になった場合はぼうぎょが上がらない():
    """みずがため: みず技を受けて瀕死になった場合、自分自身のランク変化は発動しない
    （へんしょく・ぎゃくじょう等の既存特性と同じ規約）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="みずがため")],
        team1=[Pokemon("カビゴン", move_names=["みずでっぽう"])],
    )
    defender = battle.actives[0]
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)
    assert defender.fainted is True
    assert defender.boosts["def"] == 0


def test_みずのベール_すでにやけど状態のポケモンを場に出すと即座に回復する():
    """みずのベール: 元の特性がみずのベールのポケモンが、特性を書き換えられてやけど状態に
    なった後、交代でベンチに戻ると特性はみずのベールに戻る（やけどは残る）。この状態の
    ポケモンを再び場に出すと、場に出た直後に特性の効果でやけどが治る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["スキルスワップ"])],
        team1=[
            Pokemon("カビゴン", ability_name="みずのベール"),
            Pokemon("ラッキー"),
        ],
        accuracy=100,
    )
    defender = battle.actives[1]
    # スキルスワップで特性を入れ替え、みずのベールの効果を持たない状態にする
    t.run_move(battle, 0)
    assert defender.ability.name == "せいでんき"
    assert defender.base_ability == "みずのベール"

    # 特性がみずのベールでない間にやけど状態にする
    assert battle.ailment_manager.apply(defender, "やけど")

    # ベンチに戻ると特性は元のみずのベールに戻るが、やけどはそのまま残る
    t.run_switch(battle, 1, 1)
    bench = battle.get_team(battle.players[1])[0]
    assert bench.ability.name == "みずのベール"
    assert bench.ailment.name == "やけど"

    # 再び場に出すと、場に出た直後にみずのベールの効果でやけどが治る
    t.run_switch(battle, 1, 0)
    active = battle.actives[1]
    assert active.ability.name == "みずのベール"
    assert not active.ailment.is_active


def test_みずのベール_どくびしと同時に発生した場合はどくびしの毒付与が不発してから回復する():
    """みずのベール: すでにやけど状態のみずのベールのポケモンを、どくびしが設置された
    サイドに出した場合、どくびしのどく付与判定はやけど状態により不発してから、
    みずのベールの効果でやけどが治る（どくびしの効果は防がれる）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["スキルスワップ"])],
        team1=[
            Pokemon("カビゴン", ability_name="みずのベール"),
            Pokemon("ラッキー"),
        ],
        accuracy=100,
        side1={"どくびし": 2},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.ailment_manager.apply(defender, "やけど")

    t.run_switch(battle, 1, 1)
    t.run_switch(battle, 1, 0)
    active = battle.actives[1]

    # やけどは治り、どくびしのどくも付与されない
    assert not active.ailment.is_active


def test_ミラクルスキン_かたやぶりで無効化される():
    """ミラクルスキン: かたやぶりの効果がある変化技に対しては発動せず、
    変化技本来の命中率のまま判定される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラクルスキン")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["どくどく"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 90


@pytest.mark.parametrize(
    "move_name, expected_accuracy",
    [
        ("どくどく", 50),
        ("たいあたり", 100)
    ],
)
def test_ミラクルスキン_変化技の命中率を50パーセントに固定する(move_name: str, expected_accuracy: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラクルスキン")],
        team1=[Pokemon("カビゴン", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == expected_accuracy


def test_ミラーアーマー_かたやぶりで反射されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == -1
    assert battle.actives[1].boosts["atk"] == 0


def test_ミラーアーマー_しろいきりで無効化されたときは反射しない():
    """ミラーアーマー: 自身のしろいきりで能力低下を無効にした場合は反射も発動しない
    （docs/spec/abilities/ミラーアーマー.md「自身のみがわり/しろいきり状態...により
    無効にしたとき...ミラーアーマーは発動しない」）。

    side0 はバトル開始時点（battle.start()）より後に設置されるため、初手の
    いかくで検証すると場の効果が間に合わない。中盤の交代で発動するいかくを使う。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="いかく")],
        side0={"しろいきり": 1},
    )
    mon = battle.actives[0]
    t.run_switch(battle, 1, 1)
    foe = battle.actives[1]
    assert mon.boosts["atk"] == 0
    assert foe.boosts["atk"] == 0


def test_ミラーアーマー_反射により相手のかちきが発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かちき")],
    )
    ally, foe = battle.actives
    battle.modify_stats(ally, {"atk": -1}, source=foe)
    assert ally.boosts["atk"] == 0
    assert foe.boosts["atk"] == -1
    assert foe.boosts["spa"] == 2


def test_ミラーアーマー_反射成功時に特性バーが出る():
    """ミラーアーマー: 反射に成功した場合、ABILITY_TRIGGERED ログが記録される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    triggered = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED and log.payload.ability == "ミラーアーマー"
    ]
    assert len(triggered) == 1


def test_ミラーアーマー_相手が最低ランクのときは特性バーが出ない():
    """ミラーアーマー: 反射先（相手）が既に最低ランクで実際には変化しない場合、
    特性バーは出ずにランクが変わらない旨のメッセージだけが出る
    （一次情報: docs/wiki/abilities/ミラーアーマー.html 特性の仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
    )
    _, foe = battle.actives
    foe.boosts["atk"] = -6
    t.run_move(battle, 1)
    triggered = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED and log.payload.ability == "ミラーアーマー"
    ]
    assert not triggered
    assert foe.boosts["atk"] == -6
    assert battle.actives[0].boosts["atk"] == 0


def test_ミラーアーマー_能力低下のみ反射する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ")],
    )
    ally, foe = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -2}
    battle.modify_stats(ally, stats, source=foe)  # type: ignore
    assert ally.boosts["atk"] == 0
    assert ally.boosts["def"] == 1
    assert ally.boosts["spa"] == 0
    assert foe.boosts["atk"] == -1
    assert foe.boosts["def"] == 0
    assert foe.boosts["spa"] == -2


def test_ミラーアーマー_自己能力低下は反射しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
    )
    target, source = battle.actives
    battle.modify_stats(target, {"atk": -1}, source=target)
    assert battle.actives[0].boosts["atk"] == -1
    assert battle.actives[1].boosts["atk"] == 0


def test_ムラっけ_しろいきりでは能力低下を防げない():
    """ムラっけの能力低下は自発的な変化のため、しろいきりでも防げない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
        side0={"しろいきり": 1},
    )
    mon = battle.actives[0]
    t.end_turn(battle)

    assert 2 in mon.boosts.values()
    assert -1 in mon.boosts.values()


def test_ムラっけ_ターン終了時に別々の能力が上昇と下降する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)

    assert 2 in mon.boosts.values()
    assert -1 in mon.boosts.values()


def test_ムラっけ_全能力が最大なら下降のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd", "spe"):
        mon.boosts[stat] = 6
    t.end_turn(battle)

    assert 5 in mon.boosts.values()


def test_ムラっけ_全能力が最小なら上昇のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd", "spe"):
        mon.boosts[stat] = -6
    t.end_turn(battle)

    assert -4 in mon.boosts.values()


def test_ムラっけ_同ターン内で先にひんしになった場合は発動しない():
    """同ターン中に他の効果で先にひんしになったポケモンには、
    ターン終了時のランク変化が発動しない
    （fuzz_log seed=1122で発見: 瀕死ガード漏れの回帰確認）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ"), Pokemon("コラッタ")],
        team1=[Pokemon("カビゴン", move_names=["はかいこうせん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.fix_damage(battle, mon.max_hp)
    t.run_move(battle, 1)

    assert mon.fainted
    assert battle.winner is None

    t.end_turn(battle)

    assert all(v == 0 for v in mon.boosts.values())


def test_メガソーラー_あめ中でもほのお技が1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["ひのこ"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_メガソーラー_ソーラービームが溜めずに1ターンで攻撃できる():
    """メガソーラー: 実際の天候に関わらず、ソーラービームがはれ扱いで即座に攻撃できる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="メガソーラー", move_names=["ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert not attacker.has_volatile("ソーラービーム")
    assert defender.hp < hp_before


def test_メガソーラー_にほんばれの技で実際の天候を変更できる():
    """メガソーラーの仮想的な「はれ」上書きに阻まれず、にほんばれ自身は
    実際の天候をあめからはれに変更でき、変更後もその状態が維持される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["にほんばれ"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "はれ"
    assert battle.raw_weather.count == 5


def test_メガソーラー_ノーてんき相手でも有効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_メガソーラー_まねっこでネストしても天候が正しく元に戻る():
    """まねっこ経由で技実行がネストしても（ON_BEGIN_MOVE/ON_END_MOVEが二重発火しても）、
    行動全体が終わった後には実際の天候が正しく元に戻る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガソーラー", move_names=["まねっこ"])],
        team1=[Pokemon("コラッタ", move_names=["でんこうせっか"])],
        weather=("あめ", 5),
    )
    t.run_move(battle, 1)  # コラッタ: でんこうせっか（まねっこのコピー対象を作る）
    t.run_move(battle, 0)  # ピカチュウ: まねっこ（内部でrun_moveがネストする）
    assert battle.weather.name == "あめ"
    assert battle.actives[0].ability.state == ""
    assert battle.actives[0].ability.weather_override_depth == 0


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


def test_メガランチャー_だいちのはどうとフィールドの複合補正():
    """メガランチャー: フィールド一致で威力2倍になるだいちのはどうに、
    フィールドのタイプ一致ボーナス（でんきタイプ化後の1.3倍）とメガランチャーの1.5倍が重ねて乗る。
    power_modifier = floor(floor(4096*6144/4096)*5325/4096)*2 = floor(6144*5325/4096)*2 = 7987*2 = 15974
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="メガランチャー", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 15974


def test_メタルプロテクト_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メタルプロテクト")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == 0


def test_メタルプロテクト_能力低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メタルプロテクト")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = {k: v for k, v in stats.items() if v > 0}

    assert expected == battle.modify_stats(mon0, stats, source=mon1)


def test_メタルプロテクト_自己低下は防げない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メタルプロテクト")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, _ = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = stats

    assert expected == battle.modify_stats(mon0, stats, source=mon0)


def test_メロメロボディ_かたやぶりの技に対しても発動する():
    """メロメロボディ: かたやぶりの効果がある技に対しても発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メロメロボディ", gender="female")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["たいあたり"], gender="male")],
    )
    battle.random.random = lambda: 0.29
    t.run_move(battle, 1)
    assert battle.actives[1].has_volatile("メロメロ")


def test_メロメロボディ_同性には発動しない():
    """メロメロボディ: 相手が同性の場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メロメロボディ", gender="female")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"], gender="female")],
    )
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    assert not battle.actives[1].has_volatile("メロメロ")


def test_メロメロボディ_性別不明には発動しない():
    """メロメロボディ: 相手が性別不明の場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メロメロボディ", gender="female")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"], gender="")],
    )
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    assert not battle.actives[1].has_volatile("メロメロ")


def test_メロメロボディ_接触攻撃30パーセントでメロメロ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メロメロボディ", gender="female")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"], gender="male")],
    )
    battle.random.random = lambda: 0.29
    t.run_move(battle, 1)
    assert battle.actives[1].has_volatile("メロメロ")


def test_メロメロボディ_攻撃者が既にメロメロ状態のときは発動ログが出ない():
    """メロメロボディ: 攻撃者が既にメロメロ状態のときは揮発性状態の再付与に失敗し、
    発動ログ（ABILITY_TRIGGERED）自体が出ない（fuzzログ回帰）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メロメロボディ", gender="female")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"], gender="male")],
    )
    attacker, defender = battle.actives[1], battle.actives[0]
    battle.volatile_manager.apply(attacker, "メロメロ", source=defender)
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    triggered = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED
        and log.payload is not None
        and getattr(log.payload, "ability", None) == "メロメロボディ"
    ]
    assert triggered == []


def test_ものひろい_ターン終了時の毒ダメージで消費されたアイテムも同ターンに拾う():
    """ものひろい: docs/spec/turn.md の ON_TURN_END priority表どおり、どく等のダメージ
    （priority=90）より後（priority=150）に発動するため、同じターン終了処理内で
    毒ダメージにより消費されたきのみもそのターンのうちに拾える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    t.apply_ailment(battle, 1, "どく")
    # 毒ダメージ（最大HPの1/8）でHPが半分以下になるようにHPを調整し、オボンのみを発動させる
    battle.modify_hp(foe, int(foe.max_hp * 0.55) - foe.hp)
    t.end_turn(battle)
    assert not foe.has_item(), "オボンのみは毒ダメージ後に消費されているはず"
    assert pickup_mon.has_item("オボンのみ"), "同じターン内の消費でもものひろいで拾えるはず"


def test_ものひろい_どろぼうで奪われたアイテムは拾わない():
    """ものひろい: take_item（どろぼう相当）で奪われた道具は場に存在し続けるため拾わない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    # どろぼう相当の奪取をtake_itemで再現する（pickup_monがfoeの道具を奪う）
    battle.item_manager.take_item(foe)
    assert pickup_mon.has_item("オボンのみ")
    assert foe.last_lost_item_name == ""

    # 奪った道具をpickup_monが手放す（既にアイテムを保持している間はものひろいが発動しないため）
    battle.item_manager.remove_item(pickup_mon)
    assert not pickup_mon.has_item()
    t.end_turn(battle)
    # foeのlast_lost_item_nameが空のため、ものひろいは発動しない
    assert not pickup_mon.has_item()


def test_ものひろい_相手がアイテムを消費していない場合は拾わない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ")],
    )
    pickup_mon, _ = battle.actives
    t.end_turn(battle)
    assert not pickup_mon.has_item(), "相手がアイテムを消費していないときは何も拾わないはず"


def test_ものひろい_相手が消費したアイテムをターン終了時に拾う():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    assert not pickup_mon.has_item()
    # 相手のアイテムを消費させる
    battle.item_manager.remove_item(foe)
    assert not foe.has_item()
    assert foe.last_lost_item_name == "オボンのみ"
    # ターン終了でものひろい発動
    t.end_turn(battle)
    assert pickup_mon.has_item("オボンのみ"), "ものひろいで相手のアイテムを拾うはず"


def test_ものひろい_自分がアイテムを持っているときは拾わない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    battle.item_manager.remove_item(foe)
    t.end_turn(battle)
    assert pickup_mon.has_item("たべのこし"), "アイテム持ちのときは拾わないはず"


def test_ものひろい_過去のターンに消費されたアイテムは拾わない():
    """ものひろい: 「そのターン」限定の効果。過去のターンに相手が消費した道具は、
    以降そのターン中に何も消費していなければ拾わない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ものひろい", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ", item_name="オボンのみ")],
    )
    pickup_mon, foe = battle.actives
    # 1ターン目: foeがアイテムを消費するが、pickup_monはまだアイテムを持っているため拾わない
    battle.item_manager.remove_item(foe)
    t.end_turn(battle)
    assert pickup_mon.has_item("たべのこし")

    # 2ターン目: pickup_monがアイテムを失う（はたきおとす相当。track_loss=Falseで自身の
    # last_lost_item_nameは更新しない）が、foeはこのターン何も消費していない
    battle.turn += 1
    battle.item_manager.remove_item(pickup_mon, track_loss=False)
    assert not pickup_mon.has_item()
    t.end_turn(battle)
    # foeがこのターンに消費したアイテムはないため、過去のオボンのみを拾ってはいけない
    assert not pickup_mon.has_item(), "そのターンに相手が消費していないアイテムは拾わないはず"


def test_もふもふ_かたやぶりで両方の効果が無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_もふもふ_こんらんの自傷ダメージは半減しない():
    """こんらんの自傷ダメージ（"_こんらん"）は接触技・ほのお技のいずれでもないため補正されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もふもふ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier
    assert attacker.hp < attacker.max_hp


def test_もふもふ_テラスタルでほのおタイプに変化した技にも発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="ほのお", move_names=["テラバースト"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    attacker = battle.actives[0]
    attacker.terastallize()
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ほのお"
    assert 8192 == battle.damage_calculator.damage_modifier


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


def test_もふもふ_みがわり状態で防いだときも発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_もふもふ_接触技を半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_もらいび_おにびなど状態異常技も無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もらいび")],
        team1=[Pokemon("ピカチュウ", move_names=["おにび"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)

    assert not defender.has_ailment("やけど")
    assert defender.ability.state == "charged"


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


def test_もらいび_まもるで防がれた場合は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もらいび", move_names=["まもる"])],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 0)
    t.run_move(battle, 1)

    assert defender.ability.state == "idle"
    assert defender.ability.revealed is False


def test_もらいび_交代で状態がリセットされる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もらいび"), Pokemon("コラッタ")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]

    # ひのこを吸収してチャージ状態へ
    t.run_move(battle, 1)
    assert defender.ability.state == "charged"

    # 交代して戻ってくると状態がリセットされる
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert defender.ability.state == "idle"


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


def test_もらいび_非ほのお技を挟んでも次のほのお技で1回だけ強化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もらいび", move_names=["でんきショック", "ひのこ"])],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender, attacker = battle.actives

    # ひのこを吸収してチャージ状態へ
    t.run_move(battle, 1)
    assert defender.ability.state == "charged"

    # 非ほのお技を挟んでもチャージ状態のまま維持される
    t.run_move(battle, 0, move_idx=0)
    assert defender.ability.state == "charged"

    # 次のほのお技で1.5倍になり、消費後はidleに戻る
    t.run_move(battle, 0, move_idx=1)
    assert battle.damage_calculator.power_modifier == 6144
    assert defender.ability.state == "idle"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
