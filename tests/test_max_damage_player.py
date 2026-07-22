"""jpoke.players.MaxDamagePlayer の単体テスト。"""
from jpoke import Battle, Pokemon, Player
from jpoke.enums import Command
from jpoke.players import MaxDamagePlayer


def test_choose_commandが交代コマンドを選ばない():
    """技以外のコマンド（交代）は `_damage()` が -1 を返すため選ばれない。"""
    player1 = MaxDamagePlayer(username="MaxDamagePlayer")
    player1.team = [
        Pokemon("ピカチュウ", item_name="", move_names=["たいあたり"]),
        Pokemon("フシギダネ", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(username="Player 2")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"]),
    ]

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.start()

    with battle.phase_context("action"):
        assert player1.choose_command(battle).is_move


def test_choose_commandが最大ダメージの技を選ぶ():
    player1 = MaxDamagePlayer(username="MaxDamagePlayer")
    player1.team = [
        Pokemon("ピカチュウ", item_name="", move_names=["でんこうせっか", "かみなり", "なきごえ"]),
    ]

    player2 = Player(username="Player 2")
    player2.team = [Pokemon("フシギダネ", item_name="", move_names=["たいあたり"])]

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.start()

    with battle.phase_context("action"):
        # でんこうせっか（威力40）よりかみなり（威力95）の方がダメージが大きい
        assert player1.choose_command(battle) == Command.MOVE_1


def test_damageが技以外のコマンドに負の値を返す():
    player1 = MaxDamagePlayer(username="MaxDamagePlayer")
    player1.team = [
        Pokemon("ピカチュウ", item_name="", move_names=["たいあたり"]),
        Pokemon("フシギダネ", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(username="Player 2")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"]),
    ]

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.start()

    with battle.phase_context("action"):
        assert player1._damage(battle, Command.SWITCH_1) == -1
