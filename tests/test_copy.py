"""状態異常ハンドラの単体テスト"""
import pytest

from jpoke.enums import Event
from jpoke.model import Pokemon

from . import test_utils as t


def test_mon():
    """pokemonのコピーが正しく行われることを確認する。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし"), Pokemon("ヒトカゲ")],
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
    assert new_handler.registered_subject is new.actives[0]

    # コピー後のEventContextでハンドラが正しく除去されることを確認する
    t.run_switch(new, 0, 1)
    assert new.actives[0].name == "ヒトカゲ"
    assert new.events.handlers == {}


def test_weather():
    """天候のコピーが正しく行われることを確認する。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("フシギダネ")],
        weather=("すなあらし", 2),
    )
    new = old.copy()
    assert new.weather is not old.weather

    # newの天候が正しく機能することを確認する
    t.end_turn(new)
    assert new.weather.count == 1
    assert old.weather.count == 2
    assert new.actives[0].hp < new.actives[0].max_hp
    assert old.actives[0].hp == old.actives[0].max_hp


def test_terrain():
    """地形のコピーが正しく行われることを確認する。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("フシギダネ")],
        terrain=("グラスフィールド", 2),
    )
    old.actives[0].hp = 1
    assert Event.ON_TURN_END in old.events.handlers

    new = old.copy()
    assert new.terrain is not old.terrain

    t.end_turn(new)
    assert new.terrain.count == 1
    assert old.terrain.count == 2
    assert old.actives[0].hp == 1
    assert new.actives[0].hp > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
