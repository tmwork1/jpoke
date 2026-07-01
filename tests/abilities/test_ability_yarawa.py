"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle

import pytest

from jpoke import Pokemon
from jpoke.types import AilmentName, WeatherName

from .. import test_utils as t


def test_ゆうばく_直接攻撃KO時に攻撃者に1_4ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon, foe = battle.actives
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.hp == foe.max_hp - foe.max_hp // 4


def test_ゆうばく_非接触KOでは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    mon, foe = battle.actives
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


def test_よちむ_変化技も公開される():
    """よちむ: 変化技のみの場合は(威力0の技の中から)いずれかが公開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よちむ")],
        team1=[Pokemon("カビゴン", move_names=["つるぎのまい"])],
    )
    _, foe = battle.actives
    assert foe.moves[0].revealed


@pytest.mark.parametrize(
    "move_name",
    ["でんきショック", "たいあたり"]
)
def test_よわき_HP半分以下で攻撃補正0_5倍(move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よわき", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier


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


def test_りんぷん_追加効果を受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.is_active is False


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_リーフガード_すべての状態異常を防ぐ(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5)
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, ailment_name) is False


@pytest.mark.parametrize(
    "weather, result",
    [
        ("はれ", False),
        ("おおひでり", False),
        ("あめ", True),
        ("すなあらし", True),
        ("ゆき", True),
        (None, True),
    ],
)
def test_リーフガード_はれ中に状態異常を防ぐ(weather: WeatherName | None, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 5) if weather else None
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく") is result


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
    assert battle.actives[1].rank["spe"] == 0


def test_わたげ_被弾で攻撃者のSが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="わたげ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["spe"] == -1


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
        team0=[Pokemon("ピカチュウ", item_name="たべのこし", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_item()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
