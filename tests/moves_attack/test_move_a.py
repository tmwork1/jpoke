"""攻撃技ハンドラの単体テスト（あ行）。"""

import pytest
from unittest.mock import MagicMock
from jpoke import Pokemon
from .. import test_utils as t


def test_あやしいかぜ_全能力1段階上昇が発動する():
    """あやしいかぜ: 確率10%の副作用でA/B/C/D/Sが各1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["あやしいかぜ"])],
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


def test_いかりのまえば_最低1ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いかりのまえば"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.hp == 0


@pytest.mark.parametrize(
    ("defender_hp", "expected_damage"),
    [
        (100, 50),
        (101, 50),
    ],
)
def test_いかりのまえば_相手HP半分のダメージ(defender_hp: int, expected_damage: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いかりのまえば"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = defender_hp
    t.run_move(battle, 0)
    assert defender.hp == defender_hp - expected_damage


def test_いじげんラッシュ_防御1段階低下が発動する():
    """いじげんラッシュ: 命中時に使用者のBが1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("イーブイ", move_names=["いじげんラッシュ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["B"] == -1


def test_いてつくしせん_こおりが発動する():
    """いてつくしせん: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["いてつくしせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_いのちがけ_与ダメージは現在HPで使用者はひんし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちがけ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = 40
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp - 40
    assert attacker.hp == 0


def test_おしゃべり_こんらんが発動する():
    """おしゃべり: 100%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", move_names=["おしゃべり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_オーラウイング_素早さ1段階上昇が発動する():
    """オーラウイング: 命中時に使用者のSが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["オーラウイング"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["S"] == 1
