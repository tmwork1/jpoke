"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke.data import MEGA_STONES
from jpoke.utils.type_defs import Type
from jpoke.model import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Command

import test_utils as t


stones = list(MEGA_STONES.keys())
forms_before = [x[0] for x in MEGA_STONES.values()]
forms_after = [x[1] for x in MEGA_STONES.values()]

stone_before_after = list(zip(stones, forms_before, forms_after))


@pytest.mark.parametrize(
    ("stone", "name_before", "name_after"),
    stone_before_after[:1]
)
def test_メガシンカ_コマンドが追加される(stone: str, name_before: str, name_after: str):
    battle = t.start_battle(
        team0=[Pokemon(name_before, item=stone)],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    commands = battle.get_available_action_commands(player)
    assert Command.MEGAEVOL_0 in commands


@pytest.mark.parametrize(
    ("stone", "name_before", "name_after"),
    stone_before_after
)
def test_メガシンカ_直接起動(stone: str, name_before: str, name_after: str):
    battle = t.start_battle(
        team0=[Pokemon(name_before, item=stone)],
        team1=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle, Command.MEGAEVOL_0)
    battle.turn_controller._run_megaevolve()

    mon = battle.actives[0]
    assert mon.name == name_after
    assert mon.ability.name == mon.data.abilities[0]


def test_メガシンカ_直後に特性が起動する():
    battle = t.start_battle(
        team0=[Pokemon("バンギラス", item="バンギラスナイト")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == ""

    t.reserve_command(battle, Command.MEGAEVOL_0)
    battle.advance_turn()

    mon = battle.actives[0]
    assert mon.name == "メガバンギラス"
    assert mon.ability.name == "すなおこし"
    assert battle.weather.name == "すなあらし"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
