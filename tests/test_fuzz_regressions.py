"""fuzzテストで発見されたバグの回帰テスト。

再現性のあるランダムシードをそのまま固定するのではなく、原因箇所を特定した上で
core/エンジン共通ロジックの最小ケースとして再現する。
"""
from jpoke.model import Pokemon
from jpoke.enums import Command

from . import test_utils as t


def test_こだわり_技を4つ持つ状態で控えが5匹以上いてもコマンド取得でIndexErrorが発生しない():
    """seed=109 (IndexError@volatile.py:restrict_commands:126) の回帰テスト。

    restrict_commandsは、コマンド候補が交代コマンドか技コマンドかを判定する前に
    `mon.moves[cmd.index]` へアクセスしていたため、技を4つしか持たないポケモンが
    こだわり状態で控えを5匹以上（SWITCH_5など、index>=4のスロット番号）抱えている場合、
    交代コマンドの評価時にIndexErrorが発生していた。
    技コマンドか交代コマンドかを判定した後にのみmovesへアクセスすることで、
    交代コマンドが正しく候補に含まれ、固定技以外の技コマンドは除外されることを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["たいあたり", "でんきショック", "なきごえ", "でんこうせっか"]),
            Pokemon("コラッタ"),
            Pokemon("ポッポ"),
            Pokemon("キャタピー"),
            Pokemon("ビードル"),
            Pokemon("イーブイ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こだわり", move_name="たいあたり")

    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])

    # 固定技（MOVE_0）以外の技コマンドは除外され、控え5匹分の交代コマンドは全て候補に含まれる
    move_commands = [cmd for cmd in commands if cmd.is_regular_move]
    switch_commands = [cmd for cmd in commands if cmd.is_type("switch")]
    assert move_commands == [Command.MOVE_0]
    assert switch_commands == [
        Command.SWITCH_1,
        Command.SWITCH_2,
        Command.SWITCH_3,
        Command.SWITCH_4,
        Command.SWITCH_5,
    ]


def test_バインド_瀕死交代時にとらわれ状態チェックが誤って適用されない():
    """seed=4 (IndexError@command_manager.py:resolve_command:156) の回帰テスト。

    バインドなどのとらわれ状態を持ったまま瀕死になったポケモンの強制交代は、
    退場処理（とらわれ状態の解除）より前にコマンド解決が行われるため、
    とらわれ状態チェックによって交代コマンド候補が空にならず、
    生存している控えへ正常に交代できることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("コラッタ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"バインド": 5},
    )
    mon = battle.actives[0]
    # バインドのターン終了時ダメージ（最低1）で確実に瀕死になるようHPを1にしておく
    battle.modify_hp(mon, v=-(mon.max_hp - 1))
    assert mon.hp == 1

    # ターンを進めると、ターン終了時のバインドダメージで瀕死になり、
    # 瀕死交代が発生する。修正前はcommand_manager.get_available_switch_commandsが
    # とらわれ状態チェックを行い、交代コマンド候補が空になってIndexErrorが発生していた。
    battle.step()

    assert mon.fainted
    assert battle.actives[0] is not mon
    assert battle.actives[0].name == "コラッタ"
