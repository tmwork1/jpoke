"""攻撃技ハンドラの単体テスト（か行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_かかとおとし_こんらんが発動する():
    """かかとおとし: 30%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_かみなり_まひが発動する():
    """かみなり: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_かみなりあらし_まひが発動する():
    """かみなりあらし: 20%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなりあらし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_かみなりのキバ_まひが発動する():
    """かみなりのキバ: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["かみなりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_かみなりパンチ_まひが発動する():
    """かみなりパンチ: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かみなりパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


@pytest.mark.parametrize(
    ("attacker_hp", "defender_hp", "expected_damage"),
    [
        (30, 100, 70),
        (80, 60, 0),
    ],
)
def test_がむしゃら_相手HPとの差分ダメージ(attacker_hp: int, defender_hp: int, expected_damage: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["がむしゃら"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = attacker_hp
    defender.hp = defender_hp
    t.run_move(battle, 0)
    battle.print_logs()
    assert defender.hp == defender_hp - expected_damage


def test_きあいパンチ_みがわりへの被弾では中断しない():
    """きあいパンチ: みがわりが被弾しても使用者は中断されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    battle.volatile_manager.apply(battle.actives[0], "みがわり", hp=999)
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    battle.advance_turn()

    assert battle.actives[1].hp < before_foe_hp
    assert battle.actives[0].hp == before_ally_hp


def test_きあいパンチ_攻撃ダメージを受けると失敗():
    """きあいパンチ: 行動前に攻撃ダメージを受けた場合は不発。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp


def test_きあいパンチ_行動前にダメージを受けず成功():
    """きあいパンチ: 行動前に被弾していなければ成功する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["はねる"])],
    )
    before_foe_hp = battle.actives[1].hp

    battle.advance_turn()

    assert battle.actives[1].hp < before_foe_hp


def test_キラースピン_どくが発動する():
    """キラースピン: 100%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["キラースピン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_ぎんいろのかぜ_全能力1段階上昇が発動する():
    """ぎんいろのかぜ: 確率10%でA/B/C/D/Sが各1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["ぎんいろのかぜ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["A"] == 1
    assert attacker.rank["B"] == 1
    assert attacker.rank["C"] == 1
    assert attacker.rank["D"] == 1
    assert attacker.rank["S"] == 1


def test_くさわけ_素早さ1段階上昇が発動する():
    """くさわけ: 命中時に使用者のSが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["くさわけ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["S"] == 1


def test_クロスポイズン_どくが発動する():
    """クロスポイズン: 10%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["クロスポイズン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_グロウパンチ_攻撃1段階上昇が発動する():
    """グロウパンチ: 命中時に使用者のAが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["グロウパンチ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["A"] == 1


def test_げんしのちから_全能力1段階上昇が発動する():
    """げんしのちから: 確率10%でA/B/C/D/Sが各1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("プテラ", move_names=["げんしのちから"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["A"] == 1
    assert attacker.rank["B"] == 1
    assert attacker.rank["C"] == 1
    assert attacker.rank["D"] == 1
    assert attacker.rank["S"] == 1


def test_こうそくスピン_素早さ1段階上昇が発動する():
    """こうそくスピン: 命中時に使用者のSが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうそくスピン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["S"] == 1


def test_こおりのキバ_こおりが発動する():
    """こおりのキバ: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["こおりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_こなゆき_こおりが発動する():
    """こなゆき: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_ゴールドラッシュ_特攻1段階低下が発動する():
    """ゴールドラッシュ: 命中時に使用者のCが1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ゴールドラッシュ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["C"] == -1
