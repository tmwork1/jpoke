"""`jpoke.text`（盤面・コマンドのテキスト整形API）の単体テスト。"""
import subprocess
import sys

from jpoke import Battle, Pokemon, Player, describe_pokemon, describe_command, render_battle_state
from jpoke.enums import Command
from jpoke.players import CLIPlayer

from . import test_utils as t


def test_CLIPlayerの盤面表示がrender_battle_stateの出力と一致する(monkeypatch, capsys):
    player1 = CLIPlayer(username="CLIPlayer")
    player1.team = [Pokemon("ピカチュウ", item_name="", move_names=["たいあたり"])]
    player2 = Player(username="Player 2")
    player2.team = [Pokemon("カビゴン", item_name="", move_names=["たいあたり"])]

    battle = Battle(player1, player2, n_selected=1, seed=1)

    responses = iter(["0"])  # choose_selection用の応答のみ用意する

    def _input(prompt=""):
        try:
            return next(responses)
        except StopIteration:
            raise AssertionError("想定以上にinput()が呼ばれました") from None

    monkeypatch.setattr("builtins.input", _input)
    battle.start()

    # 唯一の技のPPを0にしてわるあがき1択（自動選択）の状態にし、
    # choose_command() が入力待ちせずに戻るようにする
    battle.get_active(player1).moves[0].pp = 0

    capsys.readouterr()
    with battle.phase_context("action"):
        expected_lines = render_battle_state(battle, player1)
        player1.choose_command(battle)
    captured = capsys.readouterr()

    expected_state = "\n".join(expected_lines)
    assert expected_state in captured.out


def test_describe_commandがテラスタル付きコマンドに接頭辞を付ける():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    player0 = battle.players[0]
    with battle.phase_context("action"):
        text = describe_command(battle, player0, Command.TERASTAL_0)

    assert text.startswith("テラスタル+")


def test_describe_commandがわるあがきコマンドで固定文言を返す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    player0 = battle.players[0]
    assert describe_command(battle, player0, Command.STRUGGLE) == "わるあがき"


def test_describe_commandが交代コマンドの内容とHPを含む():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["でんこうせっか"]),
            Pokemon("フシギダネ", move_names=["たいあたり"]),
        ],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    player0 = battle.players[0]
    mon = battle.get_team(player0)[1]
    with battle.phase_context("switch"):
        text = describe_command(battle, player0, Command.SWITCH_1)

    assert f"交代 → {mon.name}" in text
    assert f"HP {mon.hp}/{mon.max_hp}" in text


def test_describe_commandが技コマンドの内容を整形する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    player0 = battle.players[0]
    with battle.phase_context("action"):
        text = describe_command(battle, player0, Command.MOVE_0)

    assert "かみなり" in text
    assert "タイプ:でんき" in text
    assert "分類:special" in text
    assert "威力:110" in text
    assert "PP:" in text


def test_describe_commandの最大PP表示がmax_ppと一致する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    player0 = battle.players[0]
    with battle.phase_context("action"):
        move = battle.command_to_move(player0, Command.MOVE_0)
        text = describe_command(battle, player0, Command.MOVE_0)

    assert f"PP:{move.pp}/{move.max_pp}" in text


def test_describe_pokemonがHPを含む():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon = battle.get_active(battle.players[0])
    text = describe_pokemon(mon)
    assert f"HP {mon.hp}/{mon.max_hp}" in text


def test_describe_pokemonがテラスタル状況を含む():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon = battle.get_active(battle.players[0])
    mon.terastallize()
    assert f"(テラス:{mon.tera_type})" in describe_pokemon(mon)


def test_describe_pokemonがランク補正なしの場合は表示しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon = battle.get_active(battle.players[0])
    assert "ランク:" not in describe_pokemon(mon)


def test_describe_pokemonがランク補正を含む():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon = battle.get_active(battle.players[0])
    battle.modify_stats(mon, {"atk": 1})
    assert "ランク:[atk+1]" in describe_pokemon(mon)


def test_describe_pokemonが場に出ていない場合に専用文言を返す():
    assert describe_pokemon(None) == "(場に出ていない)"


def test_describe_pokemonが状態異常なしの場合は表示しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon = battle.get_active(battle.players[0])
    assert "状態異常:" not in describe_pokemon(mon)


def test_describe_pokemonが状態異常を含む():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        ailment0=("やけど", None),
    )
    mon = battle.get_active(battle.players[0])
    assert "状態異常:やけど" in describe_pokemon(mon)


def test_jpokeとjpoke_playersを続けてimportしても循環importにならない():
    result = subprocess.run(
        [sys.executable, "-c", "import jpoke; import jpoke.players"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_render_battle_stateがinclude_logs_Falseでログ行を含まない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    player0 = battle.players[0]
    with_logs = render_battle_state(battle, player0, include_logs=True)
    without_logs = render_battle_state(battle, player0, include_logs=False)

    log_lines = battle.get_log_lines()
    if log_lines:
        assert any(line in with_logs for line in log_lines)
    assert not any(line in without_logs for line in log_lines)


def test_render_battle_stateがlistを返し自分と相手の行を含む():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    player0 = battle.players[0]
    lines = render_battle_state(battle, player0)

    assert isinstance(lines, list)
    assert all(isinstance(line, str) for line in lines)
    joined = "\n".join(lines)
    assert "[自分]" in joined
    assert "[相手]" in joined
    assert "ピカチュウ" in joined
    assert "カビゴン" in joined


def test_render_battle_stateがサイドフィールドを張っていなければ含まない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    player0 = battle.players[0]
    joined = "\n".join(render_battle_state(battle, player0))

    assert "リフレクター" not in joined
    assert "側の場の状態" not in joined


def test_render_battle_stateがサイドフィールドを張っていれば含む():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        side0={"リフレクター": 5},
    )
    player0 = battle.players[0]
    joined = "\n".join(render_battle_state(battle, player0))

    assert "リフレクター" in joined


def test_render_battle_stateが天候と地形の行を含む():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        weather=("はれ", 5),
        terrain=("エレキフィールド", 5),
    )
    player0 = battle.players[0]
    joined = "\n".join(render_battle_state(battle, player0))

    assert "天候: はれ" in joined
    assert "フィールド: エレキフィールド" in joined


def test_トップレベルからdescribe系とrender_battle_stateがimportできる():
    from jpoke import describe_pokemon as top_describe_pokemon
    from jpoke import describe_command as top_describe_command
    from jpoke import render_battle_state as top_render_battle_state

    assert top_describe_pokemon is describe_pokemon
    assert top_describe_command is describe_command
    assert top_render_battle_state is render_battle_state
