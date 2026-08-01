"""jpoke.players の公開フック（TreeSearchPlayer.filter_commands）と
RandomSelectionMixin の単体テスト。

`filter_commands` は外部ライブラリが非公開の `TreeSearchPlayer._toplevel_commands()`
をオーバーライドして候補手を枝刈りしていた依存を解消するための公開フック。
`RandomSelectionMixin` は `RandomPlayer.choose_selection` と同一実装を
`TreeSearchPlayer`/`MinimaxPlayer` 等にも混ぜ込めるようにする Mixin。
"""
import pytest

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command
from jpoke.players import MinimaxPlayer, RandomPlayer, RandomSelectionMixin

def _make_selection_team() -> list[Pokemon]:
    return [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"]),
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("フシギダネ", item_name="", move_names=["たいあたり"]),
        Pokemon("ポッポ", item_name="", move_names=["たいあたり"]),
        Pokemon("コラッタ", item_name="", move_names=["たいあたり"]),
    ]


def test_RandomPlayerのリファクタ後も選出挙動が変わらない():
    """RandomPlayer を RandomSelectionMixin 経由の実装に変更した後も、
    battle.decision_random.sample の呼び方（引数・使うタイミング）が
    従来のべた書き実装と完全に同一であること。
    """
    player1 = RandomPlayer(username="RandomPlayer1")
    player1.team = _make_selection_team()

    player2 = RandomPlayer(username="RandomPlayer2")
    player2.team = _make_selection_team()

    battle_a = Battle(player1, player2, n_selected=3, seed=7)
    result_a = player1.choose_selection(battle_a)

    # 同じ seed の別インスタンスで decision_random.sample を直接呼んだ結果と
    # 一致すれば、内部実装が変わっても挙動は完全に同一だと確認できる。
    battle_b = Battle(player1, player2, n_selected=3, seed=7)
    expected = battle_b.decision_random.sample(range(len(player1.team)), battle_b.n_selected)

    assert result_a == expected


def test_RandomSelectionMixinが同じシードなら同じ選出を返す():
    class RandomSelectionMinimaxPlayer(RandomSelectionMixin, MinimaxPlayer):
        pass

    player1 = RandomSelectionMinimaxPlayer(username="SearchPlayer")
    player1.team = _make_selection_team()

    player2 = Player(username="Opponent")
    player2.team = _make_selection_team()

    battle1 = Battle(player1, player2, n_selected=3, seed=42)
    battle2 = Battle(player1, player2, n_selected=3, seed=42)

    assert player1.choose_selection(battle1) == player1.choose_selection(battle2)


def test_RandomSelectionMixinをMinimaxPlayerに混ぜると選出がランダムになる():
    """MinimaxPlayer（Player.choose_selection＝先頭n体の決定的選出を継承）に
    RandomSelectionMixin を混ぜると、既定の先頭からの選出とは異なる選出が
    複数シードのいずれかで決定的に得られること。
    """
    class RandomSelectionMinimaxPlayer(RandomSelectionMixin, MinimaxPlayer):
        pass

    player1 = RandomSelectionMinimaxPlayer(username="SearchPlayer")
    player1.team = _make_selection_team()

    player2 = Player(username="Opponent")
    player2.team = _make_selection_team()

    default_selection = tuple(range(3))
    selections = set()
    for seed in range(20):
        battle = Battle(player1, player2, n_selected=3, seed=seed)
        selections.add(tuple(player1.choose_selection(battle)))

    assert selections != {default_selection}, "先頭3体の決定的選出から変わっていない"


def test_RandomSelectionMixinをplayersパッケージからimportできる():
    from jpoke.players import RandomSelectionMixin as ImportedMixin

    assert ImportedMixin is RandomSelectionMixin


def test_filter_commandsがlast_available_commandsのスナップショットを破壊しない():
    """filter_commands に渡される commands は last_available_commands の
    コピーであり、フィルタ内で破壊的に操作（clear/append 等）しても
    player_states[opponent].last_available_commands 本体には影響しないこと。
    """
    class MutatingFilterPlayer(MinimaxPlayer):
        def __init__(self, username: str):
            super().__init__(username=username)
            self.identity_checks: list[bool] = []
            self.mutation_leaked: list[bool] = []

        def filter_commands(self, battle: Battle, player: Player, commands: list[Command]) -> list[Command]:
            if player is not self:
                opponent = battle.opponent(self)
                snapshot = battle.player_states[opponent].last_available_commands
                before = list(snapshot)
                self.identity_checks.append(commands is not snapshot)
                # フィルタ内でリストを破壊的に操作してみる
                commands.clear()
                commands.append(Command.STRUGGLE)
                self.mutation_leaked.append(snapshot != before)
            return commands

    player1 = MutatingFilterPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり", "みずでっぽう"])]

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    for move in battle.player_states[player2].team[0].moves:
        move.revealed = True

    battle.step()

    assert player1.identity_checks, "filter_commandsが相手側で呼ばれていない"
    assert all(player1.identity_checks), "commandsがスナップショットの実体そのものだった"
    assert not any(player1.mutation_leaked), "commandsへの破壊的操作がスナップショット本体に伝播した"


def test_filter_commandsが候補を1つに絞ると実際にその手が選ばれる():
    """フィルタなしなら確殺の10まんボルトが選ばれるはずの盤面で、
    filter_commands が自分側の候補をたいあたりのみに絞ると、
    実際にたいあたりが選ばれること。
    """
    class ForceStruggleLikeFilterPlayer(MinimaxPlayer):
        def filter_commands(self, battle: Battle, player: Player, commands: list[Command]) -> list[Command]:
            if player is self:
                return [Command.MOVE_0]  # たいあたりのみに強制する
            return commands

    player1 = ForceStruggleLikeFilterPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    battle.player_states[player2].team[0].moves[0].revealed = True
    battle.actives[1].hp = 50
    battle.roll_damage = lambda attacker, defender, move, critical=False: (
        200 if move.name == "10まんボルト" else 1
    )

    battle.step()

    assert battle.actives[0].last_move.name == "たいあたり"


def test_filter_commandsが空リストを返した場合絞り込み前の候補が使われ対戦が続行する():
    """フィルタが常に空リストを返しても、フレームワーク側が絞り込み前の
    候補にフォールバックし、例外にならず探索（nodes_expanded>0）が続行する
    こと（fallback() へ静かに縮退しないことも合わせて確認する）。
    """
    class EmptyFilterPlayer(MinimaxPlayer):
        def filter_commands(self, battle: Battle, player: Player, commands: list[Command]) -> list[Command]:
            return []

    player1 = EmptyFilterPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    battle.player_states[player2].team[0].moves[0].revealed = True

    battle.step()  # 例外にならないこと

    assert player1._searching is False
    assert battle.actives[0].last_move is not None
    assert player1.nodes_expanded > 0, "空リストにフォールバックせず通常どおり探索が行われたはず"


def test_filter_commandsのplayer引数で自分側と相手側の候補手が区別される():
    """player is self の判定で、自分側の合法手（player1）と相手側の合法手
    （player2）が正しく区別できること。トップレベル（max_plies=1）では
    自分・相手それぞれ1回ずつ呼ばれ、渡される候補手も実際の合法手と
    一致することを確認する。
    """
    class RecordingFilterPlayer(MinimaxPlayer):
        def __init__(self, username: str):
            super().__init__(username=username)
            self.calls: list[tuple[bool, list[Command]]] = []

        def filter_commands(self, battle: Battle, player: Player, commands: list[Command]) -> list[Command]:
            self.calls.append((player is self, list(commands)))
            return commands

    player1 = RecordingFilterPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    battle.player_states[player2].team[0].moves[0].revealed = True

    opponent = battle.opponent(player1)
    with battle.phase_context("action"):
        expected_self_commands = set(battle.available_commands(player1))
        expected_opponent_commands = set(battle.available_commands(opponent))

    battle.step()

    assert len(player1.calls) == 2, "トップレベルでは自分・相手それぞれ1回ずつ呼ばれるはず"
    self_calls = [commands for is_self, commands in player1.calls if is_self]
    opponent_calls = [commands for is_self, commands in player1.calls if not is_self]
    assert len(self_calls) == 1
    assert len(opponent_calls) == 1
    assert set(self_calls[0]) == expected_self_commands
    assert set(opponent_calls[0]) == expected_opponent_commands


def test_filter_commands未オーバーライドでは選ばれる手が従来と変わらない():
    """既定実装（恒等関数）のままフックを通しても、探索結果はフック追加前と
    同じであること。同一盤面・同一 seed で2回構築しても常に同じ手が
    選ばれる（決定的である）ことも合わせて確認する。
    """
    def build_battle() -> Battle:
        player1 = MinimaxPlayer(username="SearchPlayer")
        player1.team = [
            Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
        ]
        player2 = Player(username="RandomPlayer")
        player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]

        battle = Battle(player1, player2, n_selected=1, seed=1)
        battle.test_option.accuracy = 100
        battle.start()
        battle.player_states[player2].team[0].moves[0].revealed = True
        # ダメージを固定し、たいあたりでは倒せず10まんボルトなら確実に倒せるようにする
        battle.actives[1].hp = 50
        battle.roll_damage = lambda attacker, defender, move, critical=False: (
            200 if move.name == "10まんボルト" else 1
        )
        return battle

    battle_a = build_battle()
    battle_a.step()
    battle_b = build_battle()
    battle_b.step()

    assert battle_a.actives[0].last_move.name == "10まんボルト"
    assert battle_a.actives[0].last_move.name == battle_b.actives[0].last_move.name


def test_max_plies2の内側再帰でもfilter_commandsが自分側相手側とも呼ばれる():
    """max_plies>=2 の内側再帰（_best_command の非トップレベル分岐）でも
    filter_commands が呼ばれること。トップレベルでは自分・相手それぞれ
    1回ずつしか呼ばれないため、内側再帰でも呼ばれていれば呼び出し回数は
    それぞれ1を上回るはず。
    """
    class TrackingFilterPlayer(MinimaxPlayer):
        def __init__(self, username: str, max_plies: int = 1):
            super().__init__(username=username, max_plies=max_plies)
            self.self_calls: list[int] = []
            self.opponent_calls: list[int] = []

        def filter_commands(self, battle: Battle, player: Player, commands: list[Command]) -> list[Command]:
            if player is self:
                self.self_calls.append(1)
            else:
                self.opponent_calls.append(1)
            return commands

    player1 = TrackingFilterPlayer(username="SearchPlayer", max_plies=2)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり", "みずでっぽう"])]

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    for move in battle.player_states[player2].team[0].moves:
        move.revealed = True

    battle.step()

    assert len(player1.self_calls) > 1, "内側再帰でfilter_commands（自分側）が呼ばれていない"
    assert len(player1.opponent_calls) > 1, "内側再帰でfilter_commands（相手側）が呼ばれていない"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
