"""固定ダメージ技の単体テスト。"""

import pytest

from jpoke import Pokemon
from jpoke.enums import Command, LogCode
import test_utils as t


def test_ナイトヘッド_与ダメージは使用者レベル固定():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", level=50, moves=["ナイトヘッド"])],
    )
    before_hp = battle.actives[1].hp
    battle.advance_turn()
    assert before_hp - battle.actives[1].hp == 50


def test_ちきゅうなげ_ゴーストには無効():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["ちきゅうなげ"])],
        foe=[Pokemon("ゴース", moves=["はねる"])],
    )
    battle.advance_turn()
    assert battle.actives[1].hp == battle.actives[1].max_hp
    assert t.log_contains(battle, LogCode.MOVE_IMMUNE, player_idx=1)


def test_いかりのまえば_現在HPの半分を与える_最低1():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["いかりのまえば"])],
    )
    battle.actives[1]._hp = 1
    battle.advance_turn()
    assert battle.actives[1].hp == 0


@pytest.mark.parametrize(
    ("attacker_hp", "defender_hp", "expected_damage"),
    [
        (30, 100, 70),
        (80, 60, 0),
    ],
)
def test_がむしゃら_相手HPとの差分ダメージ(attacker_hp: int, defender_hp: int, expected_damage: int):
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["がむしゃら"])],
    )
    battle.modify_hp(battle.actives[0], v=attacker_hp - battle.actives[0].hp)
    battle.modify_hp(battle.actives[1], v=defender_hp - battle.actives[1].hp)
    before_hp = battle.actives[1].hp
    battle.advance_turn()
    assert before_hp - battle.actives[1].hp == expected_damage


def test_いのちがけ_与ダメージは現在HPで使用者はひんし():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["いのちがけ"])],
    )
    battle.actives[0]._hp = 40
    battle.advance_turn()
    assert battle.actives[1].damage_taken == 40
    assert battle.actives[0].hp == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

