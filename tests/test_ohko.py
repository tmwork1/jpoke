"""一撃必殺技の単体テスト。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import Command, LogCode
import test_utils as t


def test_一撃必殺技_命中時は相手を一撃で倒す():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["つのドリル"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
        accuracy=100,
    )

    t.reserve_command(battle, ally_command=Command.MOVE_0, foe_command=Command.MOVE_0)
    battle.advance_turn()

    assert battle.actives[1].hp == 0


def test_一撃必殺技_外した時はダメージを与えない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["つのドリル"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
        accuracy=0,
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle, ally_command=Command.MOVE_0, foe_command=Command.MOVE_0)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp


@pytest.mark.parametrize(
    ("move_name", "foe_name"),
    [
        ("つのドリル", "ゴース"),
        ("じわれ", "ピジョン"),
    ],
)
def test_一撃必殺技_タイプ相性で無効化される(move_name: str, foe_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon(foe_name, moves=["はねる"])],
        accuracy=100,
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle, ally_command=Command.MOVE_0, foe_command=Command.MOVE_0)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert t.log_contains(battle, LogCode.MOVE_IMMUNE, player_idx=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
