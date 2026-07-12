"""Command enum・コマンド解決の回帰テスト。

対象範囲外（ダイマックス・Zワザ）に対応する GIGAMAX_*/ZMOVE_* コマンドが、
`docs/api/README.md` の注記通り「候補として提示されず、明示的に渡してもわるあがき
扱いになる」ことを検証する。将来この挙動が変わった場合にドキュメントの追従漏れに
気づけるようにするための軽量な回帰テスト。
"""
import pytest

from jpoke.model import Pokemon
from jpoke.enums import Command

from . import test_utils as t


def test_GIGAMAXコマンド_明示的に渡すとわるあがきになる():
    """command_to_move()にGIGAMAX_*を明示的に渡しても、わるあがき扱いになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    move = battle.command_to_move(player, Command.GIGAMAX_0)
    assert move.name == "わるあがき"


def test_GIGAMAXコマンド_行動候補に含まれない():
    """get_available_commands()はGIGAMAX_*を選択肢として返さない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert not any(cmd.is_gigamax for cmd in commands)


def test_ZMOVEコマンド_明示的に渡すとわるあがきになる():
    """command_to_move()にZMOVE_*を明示的に渡しても、わるあがき扱いになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    move = battle.command_to_move(player, Command.ZMOVE_0)
    assert move.name == "わるあがき"


def test_ZMOVEコマンド_行動候補に含まれない():
    """get_available_commands()はZMOVE_*を選択肢として返さない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert not any(cmd.is_zmove for cmd in commands)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
