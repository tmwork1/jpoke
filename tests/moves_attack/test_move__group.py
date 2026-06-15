"""攻撃技ハンドラの単体テスト（グループ）。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import Command
from .. import test_utils as t


@pytest.mark.parametrize(
    ("move_name", "foe_name"),
    [
        ("つのドリル", "ゴース"),
        # ("じわれ", "ピジョン"),
    ],
)
def test_一撃必殺技_タイプ相性で無効化される(move_name: str, foe_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon(foe_name)],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].hp == battle.actives[1].max_hp


def test_一撃必殺技_命中時は相手を一撃で倒す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].hp == 0


def test_一撃必殺技_外した時はダメージを与えない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ", move_names=["はねる"])],
        accuracy=0,
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle,
                      command0=Command.MOVE_0,
                      command1=Command.MOVE_0)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
