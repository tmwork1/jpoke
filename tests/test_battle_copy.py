"""状態異常ハンドラの単体テスト"""
import pytest

from jpoke.enums import Event
from jpoke.core import BattleContext
from jpoke.model import Pokemon

import test_utils as t


def test_copy():
    """どく: ターン終了時ダメージ"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ", item="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    new = old.copy()

    assert new is not old
    assert new.actives[0] is not old.actives[0]
    assert new.actives[0].item.name == "たべのこし"
    assert new.actives[0].item is not old.actives[0].item

    old_handler = old.events.handlers[Event.ON_TURN_END_2][0]
    new_handler = new.events.handlers[Event.ON_TURN_END_2][0]
    assert old_handler is not new_handler


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
