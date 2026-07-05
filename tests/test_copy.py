"""状態異常ハンドラの単体テスト"""
import pytest

from jpoke.enums import Event, Interrupt
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


def test_木探索用の観測でswitchフェーズ中の相手コマンドがrequired_command_typeでフィルタされる():
    """相手のベンチが公開済みでも、switch フェーズ中に required_command_type が
    "move" の間は観測される相手の合法手に SWITCH コマンドが混入しないことを確認する。

    修正前は公開状況（revealed）のみでフィルタしており、木探索が
    battle.get_available_commands(opponent) をそのまま itertools.product() 等に
    渡すと sim.step() の validate_command() に弾かれて ValueError になっていた
    （docs/review/code/tree_search.md CRIT-1）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ゼニガメ", move_names=["たいあたり"]), Pokemon("カメックス")],
        accuracy=100,
    )
    player0, player1 = battle.players
    # player1のベンチ（カメックス）と技（たいあたり）が既に公開済みという想定
    battle.player_states[player1].team[1].revealed = True
    battle.actives[1].moves[0].revealed = True
    # player0が先攻でこのターンの行動順が確定している想定
    battle.turn_controller.action_order = [0, 1]
    # 通常のターン開始時にresolve_command("action")が記録するスナップショットを再現する
    # （ベンチが生存しているためSWITCH_xも含む）
    battle.player_states[player1].last_available_commands = (
        battle.command_manager.get_available_action_commands(player1)
    )

    t.run_move(battle, 0)
    assert battle.player_states[player0].interrupt == Interrupt.PIVOT

    captured = {}
    original_choose = player0.choose_command

    def spy_choose(b):
        if b.phase == "switch":
            opponent = b.opponent(player0)
            captured["commands"] = b.get_available_commands(opponent)
            captured["required_command_type"] = b.player_states[opponent].required_command_type
        return original_choose(b)

    player0.choose_command = spy_choose

    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    assert captured["required_command_type"] == "move"
    assert captured["commands"]
    assert all(cmd.is_type("move") for cmd in captured["commands"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
