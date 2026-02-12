"""ターン進行を管理するクラス。

Battleクラスの責務を分離し、ターン管理に関連するロジックを担当する。
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player
    from jpoke.model import Pokemon

from jpoke.enums import Event, Command, Interrupt
from .context import BattleContext


class TurnController:
    """ターン進行を管理するクラス。

    担当する責務:
    - ターン初期化
    - ポケモン選出処理
    - ターン進行のオーケストレーション（コマンド処理、技発動、交代など）
    - 勝敗判定とスコア計算
    """

    def __init__(self, battle: "Battle"):
        """TurnControllerを初期化。

        Args:
            battle: Battleインスタンスへの参照
        """
        self.battle = battle

    def update_reference(self, battle: "Battle"):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    @property
    def events(self):
        """BattleのEventManagerへの参照を返す。"""
        return self.battle.events

    def init_turn(self):
        """ターンを初期化し、各プレイヤーの状態をリセット。"""
        for player in self.battle.players:
            player.init_turn()

    def run_selection(self):
        """ポケモン選出処理を実行。

        各プレイヤーが選出していない場合、方策関数に従って選出を行う。
        """
        for pl in self.battle.players:
            if not pl.selection_idxes:
                commands = pl.choose_selection_commands(self.battle)
                pl.selection_idxes = [c.idx for c in commands]

    def calc_tod_score(self, player: "Player", alpha: float = 1) -> float:
        """プレイヤーのTime Over Death（TOD）スコアを計算。

        Args:
            player: スコアを計算するプレイヤー
            alpha: HP割合の重み係数

        Returns:
            TODスコア（生存ポケモン数 + HP割合）
        """
        n_alive, total_max_hp, total_hp = 0, 0, 0
        for mon in player.selection:
            total_max_hp += mon.max_hp
            total_hp += mon.hp
            if mon.hp:
                n_alive += 1
        return n_alive + alpha * total_hp / total_max_hp

    def judge_winner(self) -> "Player | None":
        """勝者を判定して返す。

        Returns:
            勝者のPlayerインスタンス、勝負がついていない場合はNone
        """
        if self.battle.winner_idx is not None:
            return self.battle.players[self.battle.winner_idx]

        TOD_scores = [self.calc_tod_score(pl) for pl in self.battle.players]
        if 0 in TOD_scores:
            loser_idx = TOD_scores.index(0)
            self.battle.winner_idx = int(not loser_idx)
            self.battle.add_event_log(self.battle.players[self.battle.winner_idx], "勝ち")
            self.battle.add_event_log(self.battle.players[loser_idx], "負け")
            return self.battle.players[self.battle.winner_idx]

        return None

    def advance_turn(self, commands: dict["Player", Command] | None = None):
        """ターンを1つ進める。

        Args:
            commands: 各プレイヤーのコマンド辞書（Noneの場合は予約済みコマンドを使用）
        """
        # 引数のコマンドをスケジュールに追加する
        if commands:
            for player, command in commands.items():
                player.reserve_command(command)
                self.battle.add_command_log(player, command)
        self._process_turn_phases()

    def update_turn_count(self):
        """ターンカウントを進行させる。"""
        self.battle.turn += 1

    def _process_turn_phases(self):
        """内部的なターン進行処理を実行。

        割り込みの有無に応じて、ターンの各フェーズを順番に処理する。
        """
        # ターンの更新
        if not self.battle.has_interrupt():
            self.update_turn_count()

        # 0ターン目の処理
        if self.battle.turn == 0:
            if not self.battle.has_interrupt():
                # ポケモンを選出
                self.run_selection()
                # ポケモンを場に出す
                self.battle.run_initial_switch()

            # だっしゅつパックによる交代
            self.battle.run_interrupt_switch(Interrupt.EJECTPACK_ON_START)

            return

        # 通常ターンの処理
        if not self.battle.has_interrupt():
            # ターン初期化
            self.init_turn()

            for player in self.battle.players:
                # コマンドが予約されていなければ、方策関数に従ってコマンドを予約する
                if not player.reserved_commands:
                    command = player.choose_action_command(self.battle)
                    player.reserve_command(command)
                    self.battle.add_command_log(player, command)

            # 行動前の処理
            self.events.emit(Event.ON_BEFORE_ACTION)

        # 交代処理
        for mon in self.battle.determine_speed_order():
            # 交代フラグ
            idx = self.battle.actives.index(mon)
            interrupt = Interrupt.ejectpack_on_switch(idx)

            # 交代
            if not self.battle.has_interrupt():
                player = self.battle.players[idx]
                if player.reserved_commands[0].is_switch():
                    # 予約されている交代コマンドを取得
                    command = player.reserved_commands.pop(0)
                    # 交代を実行
                    new = player.team[command.idx]
                    self.battle.run_switch(player, new)

                # だっしゅつパックによる割り込みフラグを更新
                self.battle.override_interrupt(interrupt)

            # だっしゅつパックによる交代
            self.battle.run_interrupt_switch(interrupt)

        # 技の処理
        for mon in self.battle.determine_action_order():
            player = self.battle.find_player(mon)

            # 行動前に交代していたらスキップ
            if player.has_switched:
                continue

            if not self.battle.has_interrupt():
                self.battle.add_event_log(player, f"{player.active.name}の行動")

                # コマンドを取得
                command = player.reserved_commands.pop(0)

                # 技に変換
                move = self.battle.command_to_move(player, command)

                # 行動前の処理（各ポケモンごとに技を渡して発火）
                result_move = self.events.emit(
                    Event.ON_CHECK_MOVE,
                    ctx=BattleContext(attacker=mon, defender=self.battle.foe(mon), move=move),
                    value=move
                )

                # ハンドラーが技をNoneにした場合（ブロック）はスキップ
                if result_move is not None:
                    self.battle.run_move(mon, result_move)

            # だっしゅつボタンによる交代
            self.battle.run_interrupt_switch(Interrupt.EJECTBUTTON)

            # ききかいひによる交代
            self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

            # 交代技による交代
            self.battle.run_interrupt_switch(Interrupt.PIVOT)

            # だっしゅつパックによる割り込みフラグを更新
            interrupt = Interrupt.ejectpack_on_after_move(
                self.battle.players.index(player)
            )
            self.battle.override_interrupt(interrupt)

            # だっしゅつパックによる交代
            self.battle.run_interrupt_switch(interrupt)

        # ターン終了時の処理 (1)
        if not self.battle.has_interrupt():
            self.events.emit(Event.ON_TURN_END_1)

        # ききかいひによる交代 (1)
        self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

        # ターン終了時の処理 (2)
        if not self.battle.has_interrupt():
            self.events.emit(Event.ON_TURN_END_2)

        # ききかいひによる交代 (2)
        self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

        # ターン終了時の処理 (3)
        if not self.battle.has_interrupt():
            self.events.emit(Event.ON_TURN_END_3)

        # ききかいひによる交代 (3)
        self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

        # ターン終了時の処理 (4)
        if not self.battle.has_interrupt():
            self.events.emit(Event.ON_TURN_END_4)

        # ききかいひによる交代 (4)
        self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

        # ターン終了時の処理 (5)
        if not self.battle.has_interrupt():
            self.events.emit(Event.ON_TURN_END_5)

            # だっしゅつパックによる割り込みフラグを更新
            self.battle.override_interrupt(Interrupt.EJECTPACK_ON_TURN_END)

        # だっしゅつパックによる交代
        self.battle.run_interrupt_switch(Interrupt.EJECTPACK_ON_TURN_END)

        # 瀕死による交代
        self.battle.run_faint_switch()

        # ターン終了時の処理 (6)
        if not self.battle.has_interrupt():
            self.battle.events.emit(Event.ON_TURN_END_6)
