"""jpoke.players.CLIPlayer の単体テスト。"""
from jpoke import Battle, Pokemon, Player
from jpoke.enums import Command
from jpoke.players import CLIPlayer

def _make_team() -> list[Pokemon]:
    return [
        Pokemon("ピカチュウ", item_name="", move_names=["でんこうせっか", "かみなり"]),
        Pokemon("フシギダネ", item_name="", move_names=["たいあたり"]),
    ]

def _make_opponent_team() -> list[Pokemon]:
    # n_selected=2 のテストでも選出できるよう2体用意する
    return [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"]),
    ]

def _scripted_input(monkeypatch, *responses):
    """`builtins.input` を差し替え、決められた順で応答を返すようにする。

    responsesを使い切った後にさらに `input()` が呼ばれた場合はAssertionErrorに
    する（＝想定外の追加入力要求がないことを検証できる）。
    """
    it = iter(responses)

    def _input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise AssertionError("想定以上にinput()が呼ばれました") from None

    monkeypatch.setattr("builtins.input", _input)


def test__describe_commandが交代コマンドの内容を整形する(monkeypatch):
    player1 = CLIPlayer(username="CLIPlayer")
    player1.team = _make_team()
    player2 = Player(username="Player 2")
    player2.team = _make_opponent_team()

    battle = Battle(player1, player2, n_selected=2, seed=1)
    _scripted_input(monkeypatch, "0 1")
    battle.start()

    with battle.phase_context("action"):
        text = player1._describe_command(battle, Command.SWITCH_1)

    assert "フシギダネ" in text


def test__describe_commandが技コマンドの内容を整形する(monkeypatch):
    player1 = CLIPlayer(username="CLIPlayer")
    player1.team = [Pokemon("ピカチュウ", item_name="", move_names=["かみなり"])]
    player2 = Player(username="Player 2")
    player2.team = _make_opponent_team()

    battle = Battle(player1, player2, n_selected=1, seed=1)
    _scripted_input(monkeypatch, "0")
    battle.start()

    with battle.phase_context("action"):
        text = player1._describe_command(battle, Command.MOVE_0)

    assert "かみなり" in text
    assert "PP" in text


def test_choose_commandが不正な入力を再入力させる(monkeypatch):
    player1 = CLIPlayer(username="CLIPlayer")
    player1.team = [Pokemon("ピカチュウ", item_name="", move_names=["でんこうせっか", "かみなり"])]
    player2 = Player(username="Player 2")
    player2.team = _make_opponent_team()

    battle = Battle(player1, player2, n_selected=1, seed=1)
    _scripted_input(monkeypatch, "0", "abc", "99", "0")
    battle.start()

    with battle.phase_context("action"):
        assert player1.choose_command(battle) == Command.MOVE_0


def test_choose_commandが番号入力でコマンドを選ぶ(monkeypatch):
    player1 = CLIPlayer(username="CLIPlayer")
    player1.team = [Pokemon("ピカチュウ", item_name="", move_names=["でんこうせっか", "かみなり"])]
    player2 = Player(username="Player 2")
    player2.team = _make_opponent_team()

    battle = Battle(player1, player2, n_selected=1, seed=1)
    _scripted_input(monkeypatch, "0", "1")
    battle.start()

    with battle.phase_context("action"):
        # 選択可能なコマンドは [MOVE_0, MOVE_1, TERASTAL_0, TERASTAL_1] の順のため、
        # 番号"1"はかみなり(MOVE_1)を指す
        assert player1.choose_command(battle) == Command.MOVE_1


def test_choose_commandが選択肢1つのとき入力を求めず自動選択する(monkeypatch):
    player1 = CLIPlayer(username="CLIPlayer")
    player1.team = [Pokemon("ピカチュウ", item_name="", move_names=["たいあたり"])]
    player2 = Player(username="Player 2")
    player2.team = _make_opponent_team()

    battle = Battle(player1, player2, n_selected=1, seed=1)
    # choose_selection用の応答のみ用意し、choose_command側では input() が
    # 呼ばれないこと（=自動選択されること）を _scripted_input の枯渇チェックで確認する
    _scripted_input(monkeypatch, "0")
    battle.start()

    # 唯一の技のPPを0にすることで、テラスタル等の分岐を持たない
    # わるあがき1択の状態を作る（交代先も居ないため選択肢は1つだけになる）
    battle.get_active(player1).moves[0].pp = 0

    with battle.phase_context("action"):
        assert player1.choose_command(battle) == Command.STRUGGLE


def test_choose_selectionが不正な入力を再入力させる(monkeypatch):
    player1 = CLIPlayer(username="CLIPlayer")
    player1.team = _make_team()
    player2 = Player(username="Player 2")
    player2.team = _make_opponent_team()

    battle = Battle(player1, player2, n_selected=2, seed=1)
    # 数字でない、重複、範囲外の順に無効な入力を経て最後に有効な入力を返す
    _scripted_input(monkeypatch, "abc", "0 0", "5 0", "0 1")

    assert player1.choose_selection(battle) == [0, 1]


def test_choose_selectionが有効な入力をパースする(monkeypatch):
    player1 = CLIPlayer(username="CLIPlayer")
    player1.team = _make_team()
    player2 = Player(username="Player 2")
    player2.team = _make_opponent_team()

    battle = Battle(player1, player2, n_selected=2, seed=1)
    _scripted_input(monkeypatch, "1 0")

    assert player1.choose_selection(battle) == [1, 0]
