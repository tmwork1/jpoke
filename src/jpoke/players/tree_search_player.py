"""木探索プレイヤーの共通フレームワーク。

tree_search_1〜4.py に重複していた「合法手の総当たり列挙」「盤面複製」
「割り込み交代での再帰呼び出しの処理」を1箇所にまとめる。
利用者は `TreeSearchPlayer` を継承し、`evaluate`（葉ノード評価）など
必要なフックだけをオーバーライドすれば木探索プレイヤーを作れる。

設計の詳細・根拠は docs/plan/archives/tree_search_framework.md を参照。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


class TreeSearchPlayer(Player):
    """合法手を総当たりで評価する木探索プレイヤーの基底クラス。

    自分の各合法手について、相手が最善（自分にとって最悪）の手を選ぶと
    仮定したミニマックスで評価する。max_plies を2以上にすると、相手の
    応手も含めた複数ターン先までを直接の関数再帰で評価する。

    利用者は本クラスを継承し、以下のフックメソッドを必要な分だけ
    オーバーライドする（いずれも既定実装があり、オーバーライド不要なら
    そのまま使える）。

    - `evaluate(battle)`: 葉ノードの盤面評価。既定は残りHP割合差。
    - `fallback(battle)`: 探索できない・再入時の代替方策。既定はランダム。
    - `opponent_estimator(battle, opponent)`: 相手の合法手が未公開で空の
      ときに呼ばれる推定フック。既定は何もしない（fallback に委譲される）。
    - `configure_sim(sim)`: 各分岐の `sim.step()` 実行前に呼ばれるフック。
      既定は何もしない。

    相手の情報が未公開の局面（実対戦の初手など）では、相手の合法手が
    空リストになり探索できない。既定ではこの場合探索を行わず即座に
    `fallback` に委譲する。`opponent_estimator` をオーバーライドすると、
    相手の推定される技・アイテムなどを盤面（相手ポケモンのモデル）に
    書き込め、そこから実際に選べるコマンドの列挙は `CommandManager` に
    任せられる。利用者は `Move`/`Item` など見慣れたドメインオブジェクトを
    推定するだけでよく、`Command` 自体を組み立てる必要はない。

    Attributes:
        max_plies: 探索する手数（1以上）。1手ごとに
            len(my_commands) * len(opponent_commands) 倍に分岐が増えるため、
            2以上を指定する場合は評価関数の呼び出し回数に注意する。
        max_nodes: 展開してよいノード数（`sim.step()` の呼び出し回数）の上限。
            None なら無制限。到達すると以降の展開を打ち切り、その時点で
            見つかっている最善手を返す。
        nodes_expanded: 直近の探索で展開したノード数（診断用）。
    """

    def __init__(self,
                 username: str,
                 max_plies: int = 1,
                 max_nodes: int | None = None):
        super().__init__(username=username)
        self.max_plies = max_plies
        self.max_nodes = max_nodes
        self.nodes_expanded = 0
        self._searching = False

    def evaluate(self, battle: Battle) -> float:
        """葉ノードの盤面を評価する。値が大きいほど自分に有利。

        既定は自分と相手の残りHP割合の差。決着がついている場合は
        勝敗を最優先する（±inf）。差し替える場合はオーバーライドする。
        """
        opponent = battle.opponent(self)
        winner = battle.judge_winner()
        if winner is self:
            return float("inf")
        if winner is opponent:
            return float("-inf")

        def hp_ratio(target: Player) -> float:
            team = battle.get_team(target)
            return sum(mon.hp / mon.max_hp for mon in team if not mon.fainted)

        return hp_ratio(self) - hp_ratio(opponent)

    def fallback(self, battle: Battle) -> Command:
        """探索の再入時（割り込み交代など）や、相手の合法手が未公開で
        空のまま推定もできない場合に使う既定の方策。

        評価値付きの探索は行わず、合法手からランダムに1つ選ぶだけの軽量な
        方策。`battle.decision_random`（行動選択専用の乱数系列）を使うため、
        `Battle(seed=...)` で固定した対戦全体の再現性を壊さない。
        差し替える場合はオーバーライドする。
        """
        return battle.decision_random.choice(battle.get_available_commands(self))

    def opponent_estimator(self, battle: Battle, opponent: Player) -> None:
        """相手の合法手が未公開で空のときに呼ばれる推定フック。

        既定では何もしない（推定を行わず fallback に委譲される）。
        オーバーライドし、`battle.player_states[opponent].active` の
        moves/item 等に推定値を書き込むと、そこから実際に選べるコマンドの
        列挙は `CommandManager` に任せられる。
        """
        pass

    def configure_sim(self, sim: Battle) -> None:
        """`battle.copy()` 直後・`sim.step()` 実行前に呼ばれるフック。

        既定では何もしない。オーバーライドして、探索中だけ有効にしたい
        オプション（命中固定・平均ダメージなど）を sim に設定する。
        """
        pass

    def choose_command(self, battle: Battle) -> Command:
        if self._searching:
            # sim.step() の内部で発生した割り込み交代（瀕死・だっしゅつボタン・
            # だっしゅつパック・とんぼがえり等）による再帰呼び出し。この局面は
            # 探索木の分岐には含めず、フォールバック方策で即決する。
            # 「copy_depth > 1 なら raise」という決め打ちの代わりに、探索の
            # 最上位呼び出しかどうかを明示的なフラグで判定している
            # （docs/plan/archives/tree_search_framework.md ISSUE-1 参照）。
            return self.fallback(battle)

        self._searching = True
        self.nodes_expanded = 0
        try:
            command, _ = self._best_command(battle, self.max_plies)
            return command
        finally:
            self._searching = False

    def evaluate_commands(self, battle: Battle) -> dict[Command, float]:
        """現在の盤面での自分の各合法手の評価値一覧を返す（デバッグ・読み筋確認用）。

        `_searching` やノードカウンタなど、探索本体（choose_command）の状態を
        変更しない副作用なしのメソッド。相手の合法手が未公開で空
        （かつ opponent_estimator も推定できず、推定後もコマンドが空）の
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
        my_commands, opponent_commands = self._toplevel_commands(battle, opponent)
        if not opponent_commands:
            return {}

        saved_nodes, saved_max_nodes = self.nodes_expanded, self.max_nodes
        self.nodes_expanded, self.max_nodes = 0, None
        try:
            return {
                my_cmd: self._worst_case_over_opponent(
                    battle, my_cmd, opponent, opponent_commands, self.max_plies
                )
                for my_cmd in my_commands
            }
        finally:
            self.nodes_expanded, self.max_nodes = saved_nodes, saved_max_nodes

    def _toplevel_commands(self,
                           battle: Battle,
                           opponent: Player) -> tuple[list[Command], list[Command]]:
        """探索の最上位（実際のゲームエンジンから呼ばれた局面）で使う
        自分・相手の合法手を返す。

        battle はエンジンが用意した観測用コピーで、相手の合法手は情報隠蔽済みの
        スナップショット（last_available_commands）を尊重する。相手の技・控えが
        1つも公開されていない盤面（実対戦の初手など）では相手の合法手が空になる。
        その場合 opponent_estimator に相手ポケモンのモデル（moves/item 等）へ
        推定値を書き込ませた上で、実際のコマンド列挙を CommandManager に
        やり直させて補う。それでも空なら空リストのまま返し、
        呼び出し元でフォールバック判定に使わせる。
        """
        my_commands = battle.get_available_commands(self)
        opponent_commands = battle.get_available_commands(opponent)
        if not opponent_commands and self._has_opponent_estimator():
            self.opponent_estimator(battle, opponent)
            opponent_commands = self._resolve_estimated_commands(battle, opponent)
        return my_commands, opponent_commands

    def _has_opponent_estimator(self) -> bool:
        """opponent_estimator がサブクラスでオーバーライドされているか判定する。

        既定実装（何もしない）のまま `_resolve_estimated_commands` を呼ぶと、
        `CommandManager.get_available_action_commands()` は技候補が0件でも
        「わるあがき」コマンドを補って返すため、推定を一切行っていなくても
        opponent_commands が非空になり fallback への委譲が起きなくなる
        （オーバーライドの有無で呼び出し自体を分岐する必要がある）。
        """
        return type(self).opponent_estimator is not TreeSearchPlayer.opponent_estimator

    def _resolve_estimated_commands(self, battle: Battle, opponent: Player) -> list[Command]:
        """opponent_estimator が相手ポケモンのモデルに書き込んだ推定情報から、
        実際に選べるコマンドを CommandManager に列挙させる。

        利用者は Command の組み立て（インデックス対応・テラスタル/メガシンカ
        変種・交代コマンドの併記など）を意識する必要がなく、推定した
        moves/item だけを書けばよい。
        """
        required = battle.player_states[opponent].required_command_type
        if required == "switch":
            return battle.command_manager.get_available_switch_commands(opponent)
        return battle.command_manager.get_available_action_commands(opponent)

    def _node_limit_reached(self) -> bool:
        return self.max_nodes is not None and self.nodes_expanded >= self.max_nodes

    def _best_command(self, battle: Battle, plies: int) -> tuple[Command, float]:
        """自分の各合法手について、相手が最善に対抗した場合の評価値を求め、
        その中で最大の評価値を持つ手を返す（ミニマックス）。
        """
        opponent = battle.opponent(self)

        if plies == self.max_plies:
            # 探索の最上位（実際のゲームエンジンから choose_command() が
            # 呼ばれた最初の1回）。
            my_commands, opponent_commands = self._toplevel_commands(battle, opponent)
            if not opponent_commands:
                # 相手の合法手が未公開で空のまま（推定手も得られなかった）。
                # 探索を行わず即座にフォールバック方策に委譲する。このトップ
                # レベル分岐は choose_command から1回しか呼ばれないため、
                # score（nan）を捨てて command だけ使う呼び出し元には安全。
                return self.fallback(battle), float("nan")
        else:
            # 2手目以降の内部シミュレーション。sim.step(commands) は
            # resolve_command() を経由せず直接呼ぶため、required_command_type /
            # last_available_commands は前のシミュレーション内のターンの値
            # （割り込み交代フェーズ等）のまま残っており、新しいターンの
            # 行動コマンド選択としては使えない。ここでは内部探索用の
            # 全知シミュレーションとして CommandManager から現在の合法手を
            # 直接再計算し、required_command_type も行動フェーズ用に
            # 明示的にリセットする（is_observation() が真の盤面では
            # build_observation() がマスク処理をスキップするため、
            # 情報隠蔽つきスナップショットを新しいターン用に作り直す手段が
            # 元々存在しない。docs/plan/archives/tree_search_framework.md 参照）。
            my_commands = battle.command_manager.get_available_action_commands(self)
            opponent_commands = battle.command_manager.get_available_action_commands(opponent)
            battle.player_states[self].required_command_type = "any"
            battle.player_states[opponent].required_command_type = "any"

        best_command, best_score = my_commands[0], float("-inf")
        for my_cmd in my_commands:
            if self._node_limit_reached():
                # ノード数上限に達した。以降のコマンドは展開せず、
                # その時点で見つかっている最善手を返す。
                break
            score = self._worst_case_over_opponent(
                battle, my_cmd, opponent, opponent_commands, plies
            )
            if score > best_score:
                best_command, best_score = my_cmd, score
        return best_command, best_score

    def _worst_case_over_opponent(self,
                                   battle: Battle,
                                   my_cmd: Command,
                                   opponent: Player,
                                   opponent_commands: list[Command],
                                   plies: int) -> float:
        """相手が自分にとって最も不利な手を選ぶと仮定し、その評価値を返す。"""
        worst = float("inf")
        for opp_cmd in opponent_commands:
            if self._node_limit_reached():
                # ノード数上限に達した。この my_cmd の残りの相手コマンドは
                # 展開せず、ここまでに評価済みの分だけで worst を確定する。
                break
            sim = battle.copy(reseed=True)
            # reseed=True により、同じ my_cmd に対する各 opp_cmd 分岐・各 my_cmd 分岐が
            # 複製元の random/decision_random の状態をそのまま共有せず、分岐ごとに
            # 派生シードで再初期化された独立の乱数系列を使う（Battle.copy() のdocstring
            # 参照）。reseedしないと兄弟ノード間で同じ乱数系列を引いてしまい、命中判定・
            # ダメージ乱数等を固定していない探索では評価値が相関し歪む
            # （configure_sim で確率的要素を固定している場合は影響しない）。
            # battle が観測済み盤面（is_observation() が真）の場合、Battle.copy() は
            # observer をそのまま引き継ぐ。sim.step() の内部で瀕死交代などの割り込みが
            # 発生すると、エンジンは resolve_command() 経由で（self とは限らない）
            # 任意のプレイヤーに対して build_observation() を呼び直すが、
            # build_observation() は is_observation() が真の盤面ではマスク処理自体を
            # スキップして単純にコピーを返すだけなので、引き継がれた古い observer
            # （このターンの開始時点で self を観測者として構築されたもの）が
            # そのまま残り続ける。get_available_commands() は
            # `self.observer == self.opponent(player)` を「相手観測分岐」の判定に
            # 使っているため、observer が新しいターンの実際の要求元と食い違うと
            # 前のターンの stale な last_available_commands（例: まだ瀕死になる前の
            # ポケモンへの SWITCH コマンド）を返してしまう。これを選び続けると
            # 交代が一切進行せず、run_faint_switch() が同じ局面のまま無限に再帰する
            # （テストで確認済みのバグ。エンジン側には非進行ガードも別途入っている）。
            # sim はこれから新しいターンを進める内部シミュレーション用の盤面であり、
            # 前のターンの観測コンテキストを引き継ぐ意味がないため、ここで observer を
            # 明示的にリセットし、ターン内で発生する各プレイヤーの意思決定が
            # 常にその時点の正しい盤面から新しく（必要なら再マスクして）解決される
            # ようにする。
            sim.observer = None
            # 探索専用の決定論化オプション（例: 命中固定・平均ダメージ）を
            # sim にだけ設定する。実盤面（battle）には影響しない。
            self.configure_sim(sim)
            sim.step({self: my_cmd, opponent: opp_cmd})
            self.nodes_expanded += 1
            score = self._evaluate_node(sim, plies)
            worst = min(worst, score)
        return worst

    def _evaluate_node(self, sim: Battle, plies: int) -> float:
        if sim.judge_winner() is not None or plies <= 1:
            return self.evaluate(sim)
        # 残りプライ数分だけ自分の視点で再帰する。sim.step() ではなく直接
        # _best_command() を呼ぶことで、意図した多段探索の再帰と、
        # 割り込み交代によるエンジン起因の再帰（choose_command() 経由）を
        # 明確に分離している（後者だけが _searching フラグの対象になる）。
        _, score = self._best_command(sim, plies - 1)
        return score
