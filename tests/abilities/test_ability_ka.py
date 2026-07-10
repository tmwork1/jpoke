"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.enums import Command
from jpoke.types import AilmentName

from .. import test_utils as t

ALL_AILMENTS = ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"]


def test_かがくへんかガス_登場時に相手の特性を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ピカチュウ", ability_name="ふとうのけん")],
    )
    mon = battle.actives[1]
    assert not mon.ability.enabled
    assert not mon.ability.revealed
    assert mon.rank["atk"] == 0


def test_かがくへんかガス_解除後は特性が再び有効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ふとうのけん")],
    )
    mon = battle.actives[1]
    assert mon.rank["atk"] == 0

    t.run_switch(battle, 0, 1)
    assert mon.rank["atk"] == 1


def test_かぜのり_おいかぜ状態でなければ登場時上昇なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    assert battle.actives[1].rank["atk"] == 0


def test_かぜのり_おいかぜ状態で登場時こうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        side1={"おいかぜ": 3},
    )
    assert battle.actives[1].rank["atk"] == 1


def test_かぜのり_おいかぜ発生時にこうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    mon = battle.actives[1]
    battle.get_side(mon).activate("おいかぜ", 3)
    assert mon.rank["atk"] == 1


def test_かぜのり_かたやぶりで風技吸収無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.rank["atk"] == 0


def test_かぜのり_対象外の技は通常被弾():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.rank["atk"] == 0


def test_かぜのり_風の技を吸収してこうげき上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp
    assert defender.rank["atk"] == 1


def test_かぜのり_みがわり状態でも風の技を吸収して発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり")],
        accuracy=100,
    )
    _, defender = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    assert defender.volatiles["みがわり"].hp == 999
    assert defender.rank["atk"] == 1


def test_かそく_交代直後のターンは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="かそく", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # 交代したターンはかそくが発動しない
    t.reserve_command(battle, command0=Command.SWITCH_1)
    battle.step()

    mon = battle.actives[0]
    assert mon.rank["spe"] == 0

    # 次のターンはかそくが発動する
    t.reserve_command(battle, command0=Command.MOVE_0)
    battle.step()
    assert mon.rank["spe"] == 1


@pytest.mark.parametrize(
    "move_name, expected_boost",
    [
        ("たいあたり", 5325),
        ("でんきショック", 4096),
    ]
)
def test_かたいツメ_接触技のみ威力補正1_3倍(move_name, expected_boost):
    battle_contact = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたいツメ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle_contact, 0)
    assert expected_boost == battle_contact.damage_calculator.power_modifier


def test_かたいツメ_パンチグローブ所持時はパンチ技に発動しない():
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ",
            ability_name="かたいツメ",
            item_name="パンチグローブ",
            move_names=["ほのおのパンチ"],
        )],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    # パンチグローブによる1.1倍（4506）のみが適用され、かたいツメの補正はかからない
    assert battle.damage_calculator.power_modifier == 4506


def test_かたやぶり_場に出たときに特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed


def test_カブトアーマー_かたやぶりで無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カブトアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is True


def test_カブトアーマー_急所に当たらない():
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
    battle.item_manager.consume_item(mon)
    t.change_item(battle, mon, "オボンのみ")
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_かるわざ_アイテムを失うと素早さが2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] * 2


def test_かるわざ_アイテムを失ってから再入場しても発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.item_manager.consume_item(mon)
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_かるわざ_入場時にアイテムなしなら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_かんろなミツ_入場時一度だけ発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かんろなミツ"), Pokemon("イーブイ")],
        team1=[Pokemon("カビゴン")],
    )
    mon, foe = battle.actives
    assert foe.rank["evasion"] == -1
    assert mon.ability.revealed
    assert not mon.ability.enabled

    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert foe.rank["evasion"] == -1


def test_カーリーヘアー_直接攻撃で攻撃者のSが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カーリーヘアー")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.ability.revealed
    assert attacker.rank["spe"] == -1


def test_カーリーヘアー_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カーリーヘアー")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert not defender.ability.revealed
    assert attacker.rank["spe"] == 0


def test_がんじょう_HP満タン時の致死ダメージでHP1残る():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ガブリアス", move_names=["じしん"])],
    )
    defender, _ = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == 1
    assert defender.ability.revealed


def test_がんじょう_かたやぶりで一撃技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じわれ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.move_executor.move_applied is True


def test_がんじょう_かたやぶりで耐えない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ガブリアス", ability_name="かたやぶり", move_names=["じしん"])],
    )
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


def test_ききかいひ_HPが半分以下になると交代():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.step()

    assert battle.actives[0] is not defender


def test_ききかいひ_こんらん自傷では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.modify_hp(defender, v=-1, reason="self_attack")

    assert battle.actives[0] is defender


def test_ききかいひ_やけどダメージでも発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("やけど", None),
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    battle.step()

    assert battle.actives[0] is not defender


def test_ききかいひ_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ききかいひ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2
    battle.step()

    assert battle.actives[0] is defender


@pytest.mark.parametrize(
    "move_name, revealed",
    [
        ("じしん", True),
        ("つのドリル", True),
        ("なきごえ", False),
        ("たいあたり", False)
    ]
)
def test_きけんよち_特性が開示される(move_name, revealed):
    # ピカチュウ(でんき)に対してじしん(じめん、2倍) → みぶるいした
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きけんよち")],
        team1=[Pokemon("ピカチュウ", move_names=[move_name])],
    )
    assert battle.actives[0].ability.revealed is revealed


def test_きもったま_いかくを無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きもったま")],
        team1=[Pokemon("ウインディ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["atk"] == 0


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("かわらわり", 8192),  # かくとう技 → はがねに2倍
        ("たいあたり", 2048),  # ノーマル技 → ゴーストに等倍
    ]
)
def test_きもったま_かくとう技がゴースト複合に抜群(move_name, expected_modifier):
    # かわらわり(かくとう) vs サーフゴー(はがね/ゴースト) → はがね×2倍
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きもったま", move_names=[move_name])],
        team1=[Pokemon("サーフゴー", ability_name="")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected_modifier


def test_きゅうばん_かたやぶりで無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("フシギダネ")],
    )
    mon = battle.actives[1]
    t.run_move(battle, 0)
    # かたやぶりによってきゅうばんの無効化が貫通され、交代が発生する
    assert mon is not battle.actives[1]


def test_きゅうばん_吹き飛ばしを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("フシギダネ")],
    )
    mon = battle.actives[1]
    t.run_move(battle, 0)
    # きゅうばんにより交代が阻止され、アクティブは変わらない
    assert mon is battle.actives[1]


def test_きょううん_急所ランクが1上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きょううん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 1


def test_きよめのしお_ゴースト半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シャドーボール"])],
        team1=[Pokemon("ピカチュウ", ability_name="きよめのしお")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 2048


@pytest.mark.parametrize(
    "ailment_name",
    ALL_AILMENTS
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
    assert battle.actives[1].rank["atk"] == -1


def test_きんしのちから_変化技選択時に同優先度で最後に行動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きんしのちから", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]


def test_きんしのちから_攻撃技選択時は後攻化しない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="きんしのちから", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    # コイルより素早いピカチュウが先攻のまま
    assert order[0] == battle.actives[1]


def test_きんちょうかん_相手をきんちょうかん状態にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="きんちょうかん")],
    )
    assert battle.actives[1].ability.revealed
    assert battle.query.is_nervous(battle.actives[0])


def test_ぎゃくじょう_HPが半分以下になると攻撃が1段階上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender, _ = battle.actives
    defender.hp = defender.max_hp // 2 + 1
    t.run_move(battle, 1)

    assert defender.rank["spa"] == 1
    assert defender.ability.revealed is True


def test_ぎゃくじょう_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2
    t.run_move(battle, 1)

    assert defender.rank["spa"] == 0


def test_ぎょぐん_HP1_4超で登場するとむれたすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(たんどく)", ability_name="ぎょぐん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヨワシ(むれ)"


def test_ぎょぐん_ターン終了時にHP1_4以下ならたんどくのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(むれ)", ability_name="ぎょぐん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4
    t.end_turn(battle)
    assert mon.name == "ヨワシ(たんどく)"


def test_ぎょぐん_ターン終了時にHP1_4超ならむれたすがたを維持する():
    battle = t.start_battle(
        team0=[Pokemon("ヨワシ(むれ)", ability_name="ぎょぐん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.name == "ヨワシ(むれ)"


def test_ぎょぐん_ヨワシ以外はターン終了時にフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎょぐん")],
        team1=[Pokemon("コラッタ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4
    t.end_turn(battle)
    assert mon.name == "ピカチュウ"


def test_ぎょぐん_ヨワシ以外は登場時にフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎょぐん")],
        team1=[Pokemon("コラッタ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ピカチュウ"


def test_クイックドロウ_30パーセント発動しないとき通常行動順():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 1.0  # 発動しない
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]


def test_クイックドロウ_変化技選択時は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 0.0  # 乱数を0に固定しても変化技では発動しない
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]
    assert battle.actives[0].ability.revealed is False


def test_クイックドロウ_攻撃技選択時に発動すると先攻になる():
    # コイル(S低い)がクイックドロウで先攻化
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="クイックドロウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 0.0  # 必ず発動
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]
    assert battle.actives[0].ability.revealed is True


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
    assert battle.actives[0].rank["def"] == -1
    assert battle.actives[0].rank["spe"] == 2


def test_くだけるよろい_特殊技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="くだけるよろい")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["def"] == 0
    assert battle.actives[0].rank["spe"] == 0


def test_クリアボディ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["atk"] == -1


def test_クリアボディ_能力低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = {k: v for k, v in stats.items() if v > 0}

    assert expected == battle.modify_stats(mon0, stats, source=mon1)


def test_クリアボディ_自己低下は防げない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, _ = battle.actives
    stats = {"atk": -1, "def": +1, "spa": -3, "spd": +3, "spe": -5, "accuracy": +5, "evasion": -6}
    expected = stats

    assert expected == battle.modify_stats(mon0, stats, source=mon0)


def test_こおりのりんぷん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("でんきショック", 2048),
        ("たいあたり", 4096),
    ],
)
def test_こおりのりんぷん_特殊技のダメージ半減(move_name, expected_modifier):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.damage_modifier


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
    assert battle.terrain.count == 5


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
    assert battle.damage_calculator.burn_modifier == 4096  # やけどによる攻撃半減を無効


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
