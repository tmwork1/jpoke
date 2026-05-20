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
    ("stone", "form_before", "form_after"),
    stone_before_after
)
def test_mega(stone: str, form_before: str, form_after: str):
    battle = t.start_battle(
        team0=[Pokemon(form_before, item=stone)],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    commands = battle.get_available_action_commands(player)
    assert commands == [Command.MEGAEVOL_0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
