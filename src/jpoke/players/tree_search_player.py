"""木探索プレイヤーの共通フレームワーク。

`TreeSearchPlayer` 自体は合法手の列挙・ノード数管理・再帰などの探索インフラのみを
提供する抽象度の高い基底クラスで、自分の合法手をどう評価するか（`_score_command`）は
サブクラスが実装する。相手が最悪の手を選ぶと仮定して評価する具体的な実装は
`jpoke.players.minimax_player.MinimaxPlayer` を参照。

利用者は `MinimaxPlayer`（または他の `_score_command` 実装を持つサブクラス）を継承し、
`evaluate`（葉ノード評価）など必要なフックだけをオーバーライドすれば木探索プレイヤーを作れる。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


def total_hp_ratio(battle: Battle, target: Player) -> float:
    """指定プレイヤーの残りHP割合の合計を返す。"""
    team = battle.get_team(target)
    return sum(mon.hp / mon.max_hp for mon in team if not mon.fainted)


class TreeSearchPlayer(Player):
    """合法手を総当たりで評価する木探索プレイヤーの基底クラス。

    自分の各合法手をどう評価するか（`_score_command`）は具体的な評価アルゴリズムを
    実装するサブクラス（`jpoke.players.minimax_player.MinimaxPlayer` 等）に委ねる。
    本クラス単体はインスタンス化できるが、`choose_command()` 実行時に `_score_command`
    が呼ばれると `NotImplementedError` になる。
    max_plies を2以上にすると、相手の応手も含めた複数ターン先までを直接の関数再帰で評価する。

    利用者は `MinimaxPlayer` 等を継承し、以下のフックメソッドを必要な分だけオーバーライドする。
    いずれも既定実装があり、オーバーライド不要ならそのまま使える。

    - `evaluate(battle)`: 葉ノードの盤面評価。既定は残りHP割合差。
    - `fallback(battle)`: 探索できない・再入時の代替方策。既定はランダム。
    - `estimate_opponent(battle, opponent)`: 相手の合法手が未公開で空のときに呼ばれる推定フック。既定は何もしない（fallback に委譲される）。
    - `configure_sim(sim)`: 各分岐の `sim.step()` 実行前に呼ばれるフック。既定は何もしない。

    相手の情報が未公開の局面では、相手の合法手が空リストになり探索できない。
    この場合、既定では探索を行わず即座に `fallback` に委譲する。
    `estimate_opponent` をオーバーライドすると、相手ポケモンの技やアイテムなどを書きこむことができる。

    Attributes:
        max_plies:
            探索する手数。1以上。
            1手ごとに len(my_commands) * len(opponent_commands) 倍に分岐が増える。
        max_nodes:
            展開できるノード数の上限。
            None なら無制限。到達すると以降の展開を打ち切り、その時点で見つかっている最善手を返す。
        nodes_expanded:
            直近の探索で展開したノード数。診断用。
    """

    def __init__(self,
                 username: str,
                 max_plies: int = 1,
                 max_nodes: int | None = None):
        super().__init__(username=username)
        self.max_plies: int = max_plies
        self.max_nodes: int | None = max_nodes
        self.nodes_expanded: int = 0
        self._searching: bool = False

    def evaluate(self, battle: Battle) -> float:
        """葉ノード（盤面）の評価値を返す。

        値が大きいほど自分に有利。
        既定は自分と相手の残りHP割合の差。決着がついている場合は勝敗を最優先する（±inf）。
        """
        winner = battle.judge_winner()
        opponent = battle.opponent(self)
        if winner is self:
            return float("inf")
        if winner is opponent:
            return float("-inf")
        return total_hp_ratio(battle, self) - total_hp_ratio(battle, opponent)

    def fallback(self, battle: Battle) -> Command:
        """探索の再入時（割り込み交代など）や、相手の合法手が空で推定できない場合に使われる既定の方策。

        デフォルトでは合法手からランダムに1つ選ぶ。
        `battle.decision_random`（行動選択専用の乱数系列）を使うため、`Battle(seed=...)` で固定した対戦全体の再現性を壊さない。
        """
        commands = self._available_commands_with_recovery(battle, self)
        return battle.decision_random.choice(commands)

    def estimate_opponent(self, battle: Battle, opponent: Player) -> None:
        """相手の合法手が未公開で空のときに呼ばれる推定フック。

        既定では何もせず fallback に委譲される。

        Args:
            battle: 探索中のシミュレーション用 Battle
            opponent: 推定対象の相手プレイヤー
        """
        # TODO: 相手チームのポケモンの情報(特性・アイテム・技など)と相手の選出番号では補完方法は異なる。estimate_opponentに集約するより、項目ごとにフックを分けたほうがエラーを防止できるかもしれない
        pass

    def configure_sim(self, sim: Battle) -> None:
        """`battle.copy()` 直後・`sim.step()` 実行前に呼ばれるフック。

        既定では何もしない。オーバーライドして、探索中だけ有効にしたい
        オプション（命中固定・平均ダメージなど）を sim に設定する。
        """
        pass

    def choose_command(self, battle: Battle) -> Command:
        # 割り込み交代はフォールバック方策で即決する。
        if self._searching:
            return self.fallback(battle)

        self._searching = True
        self.nodes_expanded = 0
        try:
            command, _ = self._best_command(battle, self.max_plies)
            return command
        finally:
            self._searching = False

    def _best_command(self, battle: Battle, plies: int) -> tuple[Command, float]:
        """自分の各合法手について `_score_command()` でスコアを求め、
        その中で最大のスコアを持つ手を返す。
        """
        opponent = battle.opponent(self)

        if plies == self.max_plies:
            # 探索の最上位
            my_commands, opp_commands = self._toplevel_commands(battle)
            if not my_commands or not opp_commands:
                return self.fallback(battle), float("nan")
        else:
            # 2手目以降。sim.step()完了直後の全知シミュレーションかつ新規ターン開始
            # 直後（中断的な交代は再入した choose_command 側のfallbackで既に解決済み）
            # であるため、phaseは必ず"action"であり、battle.available_commands()の
            # phase分岐に委ねてよい。
            my_commands = battle.available_commands(self)
            opp_commands = battle.available_commands(opponent)
            battle.player_states[self].required_command_type = "any"
            battle.player_states[opponent].required_command_type = "any"

        scores = self._score_commands(
            battle, my_commands, opponent, opp_commands, plies, respect_node_limit=True
        )
        best_command = my_commands[0]
        best_score = float("-inf")
        for my_cmd, score in scores.items():
            if score > best_score:
                best_command, best_score = my_cmd, score
        return best_command, best_score

    def _score_commands(self,
                         battle: Battle,
                         my_commands: list[Command],
                         opponent: Player,
                         opp_commands: list[Command],
                         plies: int,
                         *,
                         respect_node_limit: bool) -> dict[Command, float]:
        """自分の各合法手について、`_score_command()` で評価値を求める。

        `respect_node_limit=True` の場合、ノード上限に達した時点でそれ以降の
        合法手の評価を打ち切る（`_best_command` の探索用）。`False` の場合は
        `max_nodes` を無視して全ての合法手を評価する（`evaluate_commands` の
        デバッグ用）。
        """
        scores: dict[Command, float] = {}
        for my_cmd in my_commands:
            if respect_node_limit and self._node_limit_reached():
                break
            scores[my_cmd] = self._score_command(
                battle, my_cmd, opponent, opp_commands, plies
            )
        return scores

    def _score_command(self,
                        battle: Battle,
                        my_cmd: Command,
                        opponent: Player,
                        opp_commands: list[Command],
                        plies: int) -> float:
        """自分の合法手 `my_cmd` を、相手の候補手 `opp_commands` を踏まえてスコア化する。

        具体的な評価アルゴリズム（相手が最悪の手を選ぶミニマックスか、期待値か等）は
        サブクラスが実装する拡張ポイント。`TreeSearchPlayer` 単体はインスタンス化
        できるが、`choose_command()` 実行時にこのメソッドが呼ばれると
        `NotImplementedError` になる。既定実装は `MinimaxPlayer` を参照。
        """
        raise NotImplementedError

    def _node_limit_reached(self) -> bool:
        return self.max_nodes is not None and self.nodes_expanded >= self.max_nodes

    def _toplevel_commands(self, battle: Battle) -> tuple[list[Command], list[Command]]:
        # TODO: 相手のコマンド候補がある場合でもestimate_opponentを呼び、相手の推定値を更新させるようにする(実対戦における型推定に相当する)。
        """探索の最上位（実際のゲームエンジンから呼ばれた局面）で使う
        自分・相手の合法手を返す。

        battle はエンジンが用意した観測用コピーで、相手の合法手は情報隠蔽済みの
        スナップショット（last_available_commands）を尊重する。相手の技・控えが
        1つも公開されていない盤面（実対戦の初手など）では相手の合法手が空になる。
        その場合 estimate_opponent に相手ポケモンのモデル（moves/item 等）へ
        推定値を書き込ませた上で、実際のコマンド列挙を CommandManager に
        やり直させて補う。それでも空なら空リストのまま返し、
        呼び出し元でフォールバック判定に使わせる。
        """
        opponent = battle.opponent(self)
        my_commands = self._available_commands_with_recovery(battle, self)
        opponent_commands = battle.available_commands(opponent)
        if not opponent_commands and self._has_estimate_opponent():
            self.estimate_opponent(battle, opponent)
            opponent_commands = self._resolve_estimated_commands(battle, opponent)
        return my_commands, opponent_commands

    def _available_commands_with_recovery(self, battle: Battle, player: Player) -> list[Command]:
        """`battle.available_commands(player)` を呼び、switch フェーズで
        結果が空になった場合のみ `state.team`（選出制限を無視したチーム全体）
        から交代先候補を復元するフォールバック付きの合法手取得。

        背景: 木探索の内部シミュレーション（`sim.step()`）中に、相手プレイヤー
        自身がとんぼがえり・ききかいひ・だっしゅつパックなどの割り込み交代を要求されることがある。
        この時 `battle` は「探索している側（player の相手）の視点で情報隠蔽
        された観測」の子孫であることがあり、`observation_builder._mask()` が
        `state.selected_indexes` を「相手から見て公開済みの控えのみ」に
        絞り込んでいる（`state.bench`/`state.selection` はこの値を使う）。
        PIVOT/EMERGENCY等の割り込みは本来「有効な交代先が実在する」ことが
        前提で発火するため、この局面で `available_commands()` が空を
        返すのは情報隠蔽による見かけ上の欠落であり、実際に交代先が
        存在しないわけではない（fuzz seed=4698 で発見: `_best_command()` が
        `my_commands[0]` で `IndexError` になっていた）。

        ここでは `state.team` から生存している非アクティブの個体を交代先
        候補として復元する。実際には選出されていない個体を誤って含める
        可能性があるが、この経路は探索専用の使い捨てシミュレーション内でしか
        使われず、実対戦の状態には一切影響しない（`TreeSearchPlayer` の
        トップレベル `choose_command()` は常に「観測している側自身」の
        `state` を渡されるため、自分自身のデータが隠蔽されることはなく、
        この復元が必要になるのは相手プレイヤーの `choose_command()` が
        探索内から再帰的に呼ばれた場合に限られる）。
        """
        commands = battle.available_commands(player)
        if commands or battle.phase != "switch":
            return commands
        state = battle.player_states[player]
        active = state.active
        return [
            Command.get_switch_command(i)
            for i, mon in enumerate(state.team)
            if mon is not active and mon.alive
        ]

    def _evaluate_node(self, sim: Battle, plies: int) -> float:
        """探索木の葉ノード（盤面）を評価する。"""
        if sim.judge_winner() is not None or plies <= 1:
            return self.evaluate(sim)
        # 残りプライ数分だけ自分の視点で再帰する。
        _, score = self._best_command(sim, plies - 1)
        return score

    def _has_estimate_opponent(self) -> bool:
        """estimate_opponent がサブクラスでオーバーライドされているか判定する。

        既定実装（何もしない）のまま `_resolve_estimated_commands` を呼ぶと、
        `CommandManager.get_available_action_commands()` は技候補が0件でも
        「わるあがき」コマンドを補って返すため、推定を一切行っていなくても
        opponent_commands が非空になり fallback への委譲が起きなくなる
        （オーバーライドの有無で呼び出し自体を分岐する必要がある）。
        """
        return type(self).estimate_opponent is not TreeSearchPlayer.estimate_opponent

    def _resolve_estimated_commands(self, battle: Battle, opponent: Player) -> list[Command]:
        """estimate_opponent が相手ポケモンのモデルに書き込んだ推定情報から、
        実際に選べるコマンドを CommandManager に列挙させる。

        利用者は Command の組み立て（インデックス対応・テラスタル/メガシンカ
        変種・交代コマンドの併記など）を意識する必要がなく、推定した
        moves/item だけを書けばよい。
        """
        required = battle.player_states[opponent].required_command_type
        if required == "switch":
            return battle.command_manager.available_switch_commands(opponent)
        return battle.command_manager.available_action_commands(opponent)

    def evaluate_commands(self, battle: Battle) -> dict[Command, float]:
        """現在の盤面での自分の各合法手の評価値一覧を返す（デバッグ・読み筋確認用）。

        `_searching` やノードカウンタなど、探索本体（choose_command）の状態を
        変更しない副作用なしのメソッド。相手の合法手が未公開で空
        （かつ estimate_opponent も推定できず、推定後もコマンドが空）の
        場合は空の辞書を返す。

        注意: 呼び出し中は `max_nodes` によるノード数上限を一時的に無効化し、
        自分の全合法手 × 相手の全合法手を `max_plies` の深さまで打ち切りなく
        評価する（`choose_command` の探索とは異なりノード数では打ち切らない）。
        そのため実行コストは `max_plies` が大きいほど大きくなりうる。
        `choose_command` の呼び出しごと（毎ターン）にこのメソッドも呼ぶような
        デバッグ表示などに組み込む場合は、探索コストが `max_nodes` で
        抑えられないことに注意すること。
        """
        opponent = battle.opponent(self)
        my_commands, opponent_commands = self._toplevel_commands(battle)
        if not opponent_commands:
            return {}

        saved_nodes, saved_max_nodes = self.nodes_expanded, self.max_nodes
        self.nodes_expanded, self.max_nodes = 0, None
        try:
            return self._score_commands(
                battle, my_commands, opponent, opponent_commands, self.max_plies,
                respect_node_limit=False,
            )
        finally:
            self.nodes_expanded, self.max_nodes = saved_nodes, saved_max_nodes

