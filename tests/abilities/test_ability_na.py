"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon

from .. import test_utils as t


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


def test_ナイトメア_ダメージ量は最大HPの1_8切り捨て():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3)
    )
    _, foe = battle.actives
    t.end_turn(battle)
    assert foe.hp == foe.max_hp - foe.max_hp // 8


def test_ナイトメア_マジックガードでダメージ無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ナイトメア")],
        team1=[Pokemon("カビゴン", ability_name="マジックガード")],
        ailment1=("ねむり", 3)
    )
    _, foe = battle.actives
    t.end_turn(battle)
    assert foe.hp == foe.max_hp


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


def test_ねつこうかん_ほのお技を受けるとこうげき1段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert defender.rank["atk"] == 1
    assert defender.ability.revealed


def test_ねつこうかん_やけど状態にならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert not battle.ailment_manager.apply(battle.actives[0], "やけど")


def test_ねつぼうそう_やけど状態でない場合は倍率なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつぼうそう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 6144),
        ("でんきショック", 4096),
    ]
)
def test_ねつぼうそう_やけど状態で物理技の威力が1_5倍(move_name: str, expected_modifier: int):
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
