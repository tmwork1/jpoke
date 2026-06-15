"""攻撃技ハンドラの単体テスト（あ行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


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
