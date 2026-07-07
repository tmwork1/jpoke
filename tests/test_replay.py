"""対戦ログ出力・リプレイ再生機能のテスト。"""
import pytest

from jpoke.core.replay import BattleReplayData, RecordedCommand
from jpoke.enums import Command
from jpoke.model import Pokemon
from jpoke.players import ReplayPlayer, replay_battle

from . import test_utils as t

def _play_to_finish(battle, max_turns: int = 50):
    turns = 0
    while battle.judge_winner() is None and turns < max_turns:
        battle.step()
        turns += 1
    assert battle.judge_winner() is not None, "対戦が決着しなかった"


def test_ReplayPlayerはコマンド不足の場合に例外を送出する():
    data = BattleReplayData(
        seed=1,
        n_selected=1,
        battle_option={
            "mega_evolution": True, "terastal": True, "critical_mode": "通常",
            "damage_roll": "通常", "accuracy_fix_threshold": None,
            "effect_chance_threshold": None,
        },
        teams=(
            [Pokemon("ピカチュウ").to_dict()],
            [Pokemon("コラッタ").to_dict()],
        ),
        selections=([0], [0]),
        commands=[],
    )

    with pytest.raises(RuntimeError):
        replay_battle(data)


def test_pokemonのto_dictとfrom_dictの往復で同じ状態が復元される():
    mon = Pokemon(
        "ピカチュウ", gender="male", nature="ようき", level=73,
        ability_name="せいでんき", item_name="たべのこし",
        move_names=["10まんボルト", "でんこうせっか"], tera_type="みず",
    )
    mon.set_effort_at(0, 20)

    data = mon.to_dict()
    restored = Pokemon.from_dict(data)

    assert restored.to_dict() == data
    assert restored.max_hp == mon.max_hp
    assert [m.name for m in restored.moves] == [m.name for m in mon.moves]


def test_recordedcommandのto_dictとfrom_dictの往復で同じ内容が復元される():
    rec = RecordedCommand(turn=3, player_idx=1, phase="switch", command=Command.SWITCH_2)
    restored = RecordedCommand.from_dict(rec.to_dict())
    assert restored == rec


def test_テラスタルコマンドを含む対戦のリプレイが再現される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"], tera_type="みず")],
        team1=[Pokemon("コラッタ", level=1, move_names=["たいあたり"])],
    )
    player0, player1 = battle.players
    battle.step({player0: Command.TERASTAL_0, player1: Command.MOVE_0})
    assert battle.judge_winner() is not None
    assert battle.actives[0].terastallized

    data = battle.build_replay_data()
    replayed = replay_battle(data)

    new_mon = replayed.player_states[replayed.players[0]].team[0]
    assert new_mon.terastallized
    assert new_mon.tera_type == "みず"
    assert replayed.event_logger.logs == battle.event_logger.logs


def test_瀕死による強制交代を含む対戦のリプレイが同じ結果を再現する():
    """ドキュメント: docs/plan/battle_log_replay.md のテスト観点参照。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[
            Pokemon("コラッタ", level=1, move_names=["たいあたり"]),
            Pokemon("イーブイ", level=1, move_names=["たいあたり"]),
        ],
    )
    _play_to_finish(battle)

    # 瀕死交代のコマンドが記録されていること
    assert any(c.phase == "switch" for c in battle.command_log)

    data = battle.build_replay_data()
    replayed = replay_battle(data)

    winner_idx = battle.players.index(battle.winner)
    replayed_winner_idx = replayed.players.index(replayed.winner)
    assert replayed_winner_idx == winner_idx

    for old_state, new_state in zip(battle.player_states.values(), replayed.player_states.values()):
        for old_mon, new_mon in zip(old_state.team, new_state.team):
            assert new_mon.hp == old_mon.hp

    assert replayed.event_logger.logs == battle.event_logger.logs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
