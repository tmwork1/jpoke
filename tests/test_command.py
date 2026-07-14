"""Command enum・コマンド解決の回帰テスト。

対象範囲外（ダイマックス・Zワザ）に対応する GIGAMAX_*/ZMOVE_* コマンドが、
`docs/api/README.md` の注記通り「候補として提示されず、明示的に渡してもわるあがき
扱いになる」ことを検証する。将来この挙動が変わった場合にドキュメントの追従漏れに
気づけるようにするための軽量な回帰テスト。

また `Command.is_type()` が `docs/api/README.md` の Command 章「インスタンス
プロパティ・メソッド」表の記載通りに動作することも検証する。
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


def test_is_type_Noneを渡すと偽を返す():
    """command_typeにNoneを渡した場合は種別を問わず偽になる。"""
    assert not Command.MOVE_0.is_type(None)
    assert not Command.SWITCH_0.is_type(None)


def test_is_type_anyを指定すると全てのコマンドが真になる():
    """docs/api/README.mdのCommand章の記載通り、"any"は種別を問わず真を返す。"""
    assert Command.MOVE_0.is_type("any")
    assert Command.SWITCH_0.is_type("any")
    assert Command.TERASTAL_0.is_type("any")
    assert Command.STRUGGLE.is_type("any")
    assert Command.FORCED.is_type("any")


def test_is_type_moveを指定すると技系コマンドのみ真になる():
    """"move"は通常技コマンドに加え、テラスタル・メガシンカ・ダイマックス・Zワザを
    伴う技コマンドも真になる（is_regular_moveは通常技コマンドのみ）。
    わるあがき・強制行動コマンドもresolve_move_from_command()で技に解決されるため
    真になる。
    """
    assert Command.MOVE_0.is_type("move")
    assert Command.TERASTAL_0.is_type("move")
    assert Command.MEGAEVOL_0.is_type("move")
    assert Command.GIGAMAX_0.is_type("move")
    assert Command.ZMOVE_0.is_type("move")
    assert Command.STRUGGLE.is_type("move")
    assert Command.FORCED.is_type("move")
    assert not Command.SWITCH_0.is_type("move")


def test_is_type_switchを指定すると交代コマンドのみ真になる():
    """"switch"はSWITCH_*コマンドのみ真になる。"""
    assert Command.SWITCH_0.is_type("switch")
    assert not Command.MOVE_0.is_type("switch")
    assert not Command.STRUGGLE.is_type("switch")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
