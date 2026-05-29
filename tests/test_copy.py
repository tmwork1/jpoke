"""状態異常ハンドラの単体テスト"""
import pytest

from jpoke.enums import Event
from jpoke.core import BattleContext
from jpoke.model import Pokemon

import test_utils as t


def test_mon():
    """BattleContextのコピーが正しく行われることを確認する。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ", item="たべのこし"), Pokemon("ヒトカゲ")],
        team1=[Pokemon("フシギダネ")],
    )
    new = old.copy()

    assert new is not old
    assert new.actives[0] is not old.actives[0]
    assert new.actives[0].item.name == "たべのこし"
    assert new.actives[0].item is not old.actives[0].item
    assert new._player_states[0].team[0] is not old._player_states[0].team[0]

    old_handler = old.events.handlers[Event.ON_TURN_END][0]
    new_handler = new.events.handlers[Event.ON_TURN_END][0]
    assert old_handler is not new_handler
    assert new_handler._subject is new.actives[0]

    # コピー後のBattleContextでハンドラが正しく除去されることを確認する
    t.run_switch(new, 0, 1)
    assert new.actives[0].name == "ヒトカゲ"
    assert new.events.handlers == {}


def test_terrain():
    """BattleContextのコピーが正しく行われることを確認する。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("フシギダネ")],
        terrain=("グラスフィールド", 1),
    )
    assert Event.ON_TURN_END in old.events.handlers

    new = old.copy()
    assert old.terrain is not new.terrain


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
