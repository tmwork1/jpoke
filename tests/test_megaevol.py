"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke.data import MEGA_STONES
from jpoke.utils.type_defs import Type
from jpoke.model import Pokemon
from jpoke.core import EventContext
from jpoke.enums import Command

import test_utils as t


stones = list(MEGA_STONES.keys())
normal_names = [x[0] for x in MEGA_STONES.values()]
mega_names = [x[-1] for x in MEGA_STONES.values()]

stone_normal_mega = list(zip(stones, normal_names, mega_names))


@pytest.mark.parametrize(
    ("stone", "normal_name", "mega_name"),
    stone_normal_mega[:1]
)
def test_メガシンカ_コマンドが追加される(stone: str, normal_name: str, mega_name: str):
    battle = t.start_battle(
        team0=[Pokemon(normal_name, item_name=stone)],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    commands = battle.get_available_action_commands(player)
    assert Command.MEGAEVOL_0 in commands


@pytest.mark.parametrize(
    ("stone", "normal_name", "mega_name"),
    stone_normal_mega
)
def test_メガシンカ_フォルムが変わる(stone: str, normal_name: str, mega_name: str):
    battle = t.start_battle(
        team0=[Pokemon(normal_name, item_name=stone)],
        team1=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle, Command.MEGAEVOL_0)
    battle.advance_turn()

    mon = battle.actives[0]
    assert mon.name == mega_name
    assert mon.ability.name == mon.data.abilities[0]


def test_メガシンカ_直後に特性が起動する():
    battle = t.start_battle(
        team0=[Pokemon("バンギラス", item_name="バンギラスナイト")],
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
