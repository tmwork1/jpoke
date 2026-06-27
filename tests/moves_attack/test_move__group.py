"""攻撃技ハンドラの単体テスト（グループ）。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import Command
from .. import test_utils as t


def test_ダブルアタック_2回ヒットする():
    """ダブルアタック: 必ず2回ヒットする固定2回攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ダブルアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


def test_ダブルウイング_2回ヒットする():
    """ダブルウイング: 必ず2回ヒットする固定2回攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["ダブルウイング"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


def test_ツインビーム_2回ヒットする():
    """ツインビーム: 必ず2回ヒットする固定2回特殊攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ツインビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


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
    battle.step()

    assert battle.actives[1].hp == before_foe_hp
