"""jpoke.players.TreeSearchPlayer の単体テスト。

木探索フレームワーク（docs/plan/archives/tree_search_framework.md）が解消する
CRIT-1（相手の合法手が required_command_type でフィルタされない）と
ISSUE-1（探索中の割り込み交代による再帰呼び出しが copy_depth の決め打ちで
クラッシュする）の回帰確認を兼ねる。
"""
import pytest

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command
from jpoke.model import Move
from jpoke.players import TreeSearchPlayer


def test_configure_simが各分岐でsim_step実行前に呼ばれる():
    """FW-U4残: configure_sim に渡した関数が、各分岐の sim.step() 実行前に
    確実に呼ばれること。呼び出し回数が展開されたノード数と一致することで
    「各分岐で1回ずつ」呼ばれていることを確認する。
    """
    class TrackingPlayer(TreeSearchPlayer):
        def __init__(self, username: str):
            super().__init__(username=username)
            self.configure_sim_calls: list[int] = []

        def configure_sim(self, sim: Battle) -> None:
            self.configure_sim_calls.append(1)

    player1 = TrackingPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり", "みずでっぽう"])]
    for move in player2.team[0].moves:
        move.revealed = True

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()

    assert player1.configure_sim_calls, "configure_simが一度も呼ばれていない"
    assert len(player1.configure_sim_calls) == player1.nodes_expanded


def test_evaluate_commandsがmax_nodesを無視して全合法手を評価する():
    """r6-9回帰: evaluate_commands() は呼び出し中 max_nodes を一時的に無効化し、
    自分の全合法手 × 相手の全合法手を打ち切りなく評価すること。

    max_nodes を1という極端に小さい値に設定した状態で呼び出しても、
    choose_command()（_best_command 経由）のようにノード数上限で打ち切られず
    （途中で打ち切られると評価未了のコマンドが float("inf") のままになる）、
    全てのコマンドの評価値が有限値になることを確認する。呼び出し後は
    max_nodes・nodes_expanded とも呼び出し前の値に復元されることも合わせて
    確認する。
    """
    player1 = TreeSearchPlayer(username="SearchPlayer", max_nodes=1)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり", "みずでっぽう"])]
    for move in player2.team[0].moves:
        move.revealed = True

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    before_max_nodes, before_nodes = player1.max_nodes, player1.nodes_expanded

    with battle.phase_context("action"):
        result = player1.evaluate_commands(battle)

    assert len(result) >= 2, "自分の合法手（技2種）が両方とも評価対象になっていない"
    for command, value in result.items():
        assert value not in (float("inf"), float("-inf")), (
            f"{command} の評価値がノード数上限で打ち切られ未評価のままになっている: {value}"
        )
    # 呼び出し前の max_nodes・nodes_expanded が復元されていること
    assert player1.max_nodes == before_max_nodes == 1
    assert player1.nodes_expanded == before_nodes


def test_evaluate_commandsが非破壊的に評価値一覧を返す():
    """FW-U6: evaluate_commands(battle) が探索本体（choose_command）の状態
    （_searching・nodes_expanded）を変更せず、各合法手の評価値一覧を辞書で
    返すこと。
    """
    player1 = TreeSearchPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]
    player2.team[0].moves[0].revealed = True

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    before_searching = player1._searching
    before_nodes = player1.nodes_expanded

    with battle.phase_context("action"):
        result = player1.evaluate_commands(battle)
        expected_commands = set(battle.get_available_commands(player1))

    assert isinstance(result, dict)
    assert set(result.keys()) == expected_commands
    assert player1._searching == before_searching
    assert player1.nodes_expanded == before_nodes


def test_evaluateの既定実装がget_team経由で対戦中の実データを反映する():
    """r6-8回帰: evaluate() の既定実装（残りHP割合差）は battle.get_team() を
    使って対戦中のチームを取得すること。コンストラクタ時点の player.team
    スナップショットではなく、対戦開始後のHP変化・瀕死状態が正しく
    反映されることを、evaluate() の戻り値を手計算した期待値と突き合わせて
    確認する。
    """
    player1 = TreeSearchPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    # 対戦開始後にアクティブのHPを変化させ、evaluateが最新状態を反映することを確認する
    battle.modify_hp(battle.actives[0], r=-0.5)
    # ベンチのリザードンを瀕死にし、合計HP割合の計算から除外されることを確認する
    battle.modify_hp(battle.get_team(player1)[1], r=-1.0)

    value = player1.evaluate(battle)

    expected = (
        sum(mon.hp / mon.max_hp for mon in battle.get_team(player1) if not mon.fainted)
        - sum(mon.hp / mon.max_hp for mon in battle.get_team(player2) if not mon.fainted)
    )
    assert value == pytest.approx(expected)
    # 生存中の自分のポケモンは1体（ヒトカゲ、HP半分）のみのはず
    assert value == pytest.approx(0.5 - 2.0)


def test_evaluate関数が例外を投げてもsearchingフラグは解除される():
    """探索中に評価関数が例外を投げても _searching が True のまま残らないこと。

    残ってしまうと、以降ずっとフォールバック方策しか使われなくなる。
    """
    class BrokenEvaluatePlayer(TreeSearchPlayer):
        def evaluate(self, battle: Battle) -> float:
            raise RuntimeError("評価関数が壊れている")

    player1 = BrokenEvaluatePlayer(username="SearchPlayer")
    player1.team = [Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり"])]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]
    player2.team[0].moves[0].revealed = True  # 相手の技を公開し合法手が空にならないようにする

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    with pytest.raises(RuntimeError):
        battle.step()

    assert player1._searching is False


def test_fallbackに独自関数を指定するとそれが使われる():
    """`fallback` に渡した独自関数が、探索中の割り込み交代（再入）で実際に
    使われること。"""
    class CustomFallbackPlayer(TreeSearchPlayer):
        def __init__(self, username: str, max_plies: int = 1):
            super().__init__(username=username, max_plies=max_plies)
            self.fallback_calls: list[int] = []

        def fallback(self, battle: Battle) -> Command:
            self.fallback_calls.append(1)
            return battle.get_available_commands(self)[0]

    player1 = CustomFallbackPlayer(username="SearchPlayer", max_plies=2)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="いのちのたま", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]
    player2.team[0].moves[0].revealed = True  # 相手の技を公開し合法手が空にならないようにする

    # 先頭同士のHPを1にして、探索中の同時瀕死交代を誘発する
    player1.team[0].hp = 1
    player2.team[0].hp = 1

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()

    assert player1.fallback_calls, "独自fallbackが一度も呼ばれていない"
    assert player1._searching is False


def test_max_nodesでノード数上限が機能する():
    """FW-U3: max_nodes を小さい値に設定すると、実際にノード数がその値付近で
    頭打ちになり、探索が例外にならず何らかのコマンドを返して完了すること。
    """
    player1 = TreeSearchPlayer(username="SearchPlayer", max_plies=2, max_nodes=3)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト", "でんこうせっか"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり", "みずでっぽう", "たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]
    for move in player2.team[0].moves:
        move.revealed = True

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()  # 例外にならないこと

    assert player1.nodes_expanded >= player1.max_nodes
    # 上限付近で頭打ちになっている（相手コマンド数超過分だけの余裕を許容する）
    assert player1.nodes_expanded <= player1.max_nodes + len(player2.team[0].moves)


def test_max_plies2で相手の未公開技が2手目の分岐にも現れない():
    """FW-U5: max_plies=2 の探索で、1手目は情報隠蔽済みの観測（last_available_
    commands）を尊重し、2手目以降は CommandManager から合法手を直接再計算する
    「全知」寄りの経路になる。しかし盤面そのものは1手目の観測構築時に相手の
    未公開技が物理的に削除されたコピーのままのため、2手目の分岐でも相手の
    未公開技は決して出現しないことを確認する（configure_sim フックで各分岐の
    sim を覗き見る）。
    """
    class InspectSimPlayer(TreeSearchPlayer):
        def __init__(self, username: str, max_plies: int = 1):
            super().__init__(username=username, max_plies=max_plies)
            self.observed_move_names: list[set[str]] = []

        def configure_sim(self, sim: Battle) -> None:
            opponent_state = sim.player_states[sim.players[1]]
            self.observed_move_names.append({m.name for m in opponent_state.active.moves})

    player1 = InspectSimPlayer(username="SearchPlayer", max_plies=2)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり", "みずでっぽう"])]
    player2.team[0].moves[0].revealed = True  # みずでっぽうは未公開のまま

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()

    assert player1.observed_move_names, "configure_simが一度も呼ばれていない"
    for move_names in player1.observed_move_names:
        assert "みずでっぽう" not in move_names, (
            "未公開技が探索対象の盤面に現れている（マスクが1手目より後で漏れている）"
        )


def test_opponent_estimatorを指定すると推定情報から探索が継続される():
    """FW-U1: 相手の合法手が未公開で空でも、opponent_estimator が相手ポケモンの
    moves に推定した技を書き込めば、実際のコマンド列挙は CommandManager が
    代行し、evaluate が実際に呼ばれ探索が継続されること（fallbackへ即座に
    委譲されるのではなく、シミュレーションが実行されること）。利用者は
    Command を直接組み立てる必要がない。
    """
    class EstimatorPlayer(TreeSearchPlayer):
        def __init__(self, username: str):
            super().__init__(username=username)
            self.evaluate_calls: list[int] = []

        def evaluate(self, battle: Battle) -> float:
            self.evaluate_calls.append(1)
            return super().evaluate(battle)

        def opponent_estimator(self, battle: Battle, opponent: Player) -> None:
            # Command を組み立てず、推定した技（Move）を書き込むだけでよい。
            active = battle.player_states[opponent].active
            active.moves = [Move("たいあたり"), Move("みずでっぽう")]

    player1 = EstimatorPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり", "みずでっぽう"])]
    # 相手の技は一切 revealed にしない -> estimator がなければ空リストになる盤面

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()

    assert player1.evaluate_calls, "opponent_estimator指定時はevaluateが呼ばれ探索が行われるはず"


def test_とんぼがえり使用時に相手のベンチが公開済みでもValueErrorにならない():
    """CRIT-1回帰: 相手のベンチが公開済みの状態でとんぼがえりを使い、
    switch フェーズに入っても sim.step() が例外にならず探索が完了すること。
    """
    player1 = TreeSearchPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["とんぼがえり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]
    player2.team[0].moves[0].revealed = True
    player2.team[1].revealed = True  # ベンチのカメックスを公開済みにする

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()  # ここで ValueError が起きないことを確認する

    assert player1._searching is False


def test_探索中に割り込み交代が発生してもフォールバックで完了する():
    """ISSUE-1回帰: 探索対象の各分岐で瀕死交代が発生しても、フォールバック
    方策により choose_command() が例外にならず正常にコマンドを返すこと。
    """
    player1 = TreeSearchPlayer(username="SearchPlayer", max_plies=2)
    player1.team = [
        Pokemon("ヒトカゲ", item_name="いのちのたま", move_names=["たいあたり"]),
        Pokemon("リザードン", item_name="", move_names=["たいあたり"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [
        Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"]),
        Pokemon("カメックス", item_name="", move_names=["たいあたり"]),
    ]
    player2.team[0].moves[0].revealed = True  # 相手の技を公開し合法手が空にならないようにする

    # 先頭同士のHPを1にして、同時瀕死交代が起きやすくする
    player1.team[0].hp = 1
    player2.team[0].hp = 1

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()  # 探索中の瀕死交代でも例外にならないことを確認する

    assert player1._searching is False


def test_有利な技を選択する():
    """max_plies=1 で、明確に有利な技（相手を倒せる）を選ぶこと。"""
    player1 = TreeSearchPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]
    player2.team[0].moves[0].revealed = True  # 相手の技を公開し合法手が空にならないようにする

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    # ダメージを固定し、たいあたりでは倒せず10まんボルトなら確実に倒せるようにする
    battle.actives[1].hp = 50
    battle.roll_damage = lambda attacker, defender, move, critical=False: (
        200 if move.name == "10まんボルト" else 1
    )

    battle.step()

    assert battle.actives[0].last_move.name == "10まんボルト"


def test_相手の合法手が未公開の場合fallbackに委譲される():
    """FW-U1: 相手の技・控えが1つも revealed でない盤面（実対戦の初手相当）では、
    相手の合法手が空になり探索は行われず、明示的に fallback 方策へ委譲されること。
    無言で先頭コマンドへ退化するのではなく fallback が実際に呼ばれることを確認する。
    """
    class TrackingFallbackPlayer(TreeSearchPlayer):
        def __init__(self, username: str):
            super().__init__(username=username)
            self.fallback_calls: list[int] = []

        def fallback(self, battle: Battle) -> Command:
            # fallback呼び出し時点で相手の合法手が空であることも併せて確認する
            opponent = battle.opponent(self)
            assert battle.get_available_commands(opponent) == []
            self.fallback_calls.append(1)
            return battle.get_available_commands(self)[0]

    player1 = TrackingFallbackPlayer(username="SearchPlayer")
    player1.team = [
        Pokemon("ヒトカゲ", item_name="", move_names=["たいあたり", "10まんボルト"]),
    ]

    player2 = Player(username="RandomPlayer")
    player2.team = [Pokemon("ゼニガメ", item_name="", move_names=["たいあたり"])]
    # 相手の技を一切 revealed にしない -> 合法手が空になる

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.test_option.accuracy = 100
    battle.start()

    battle.step()  # 例外にならないこと

    assert player1.fallback_calls == [1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
