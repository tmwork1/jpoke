"""jpoke.players.RandomPlayer の単体テスト。"""
from jpoke import Battle, Pokemon
from jpoke.players import RandomPlayer

def _make_team() -> list[Pokemon]:
    return [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"]),
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("フシギダネ", item_name="", move_names=["たいあたり"]),
        Pokemon("ポッポ", item_name="", move_names=["たいあたり"]),
        Pokemon("コラッタ", item_name="", move_names=["たいあたり"]),
    ]


def test_choose_selectionが同じシードなら同じ選出を返す():
    player1 = RandomPlayer(username="RandomPlayer1")
    player1.team = _make_team()

    player2 = RandomPlayer(username="RandomPlayer2")
    player2.team = _make_team()

    battle1 = Battle(player1, player2, n_selected=3, seed=42)
    battle2 = Battle(player1, player2, n_selected=3, seed=42)

    assert player1.choose_selection(battle1) == player1.choose_selection(battle2)


def test_choose_selectionが常に先頭からの選出にはならない():
    """RandomPlayer化前のPlayer既定実装（先頭から順に選出）と異なり、
    複数シードで試せば選出順が固定されないことを確認する。
    """
    player1 = RandomPlayer(username="RandomPlayer1")
    player1.team = _make_team()

    player2 = RandomPlayer(username="RandomPlayer2")
    player2.team = _make_team()

    default_selection = list(range(3))
    selections = set()
    for seed in range(20):
        battle = Battle(player1, player2, n_selected=3, seed=seed)
        selections.add(tuple(player1.choose_selection(battle)))

    assert selections != {tuple(default_selection)}


def test_choose_selectionが選出数と重複のない有効なインデックスを返す():
    player1 = RandomPlayer(username="RandomPlayer1")
    player1.team = _make_team()

    player2 = RandomPlayer(username="RandomPlayer2")
    player2.team = _make_team()

    battle = Battle(player1, player2, n_selected=3, seed=1)

    indexes = player1.choose_selection(battle)

    assert len(indexes) == battle.n_selected
    assert len(set(indexes)) == len(indexes)
    assert all(0 <= i < len(player1.team) for i in indexes)
