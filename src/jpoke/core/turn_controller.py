"""ターン進行を管理するクラス。

Battleクラスの責務を分離し、ターン管理に関連するロジックを担当する。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player
    from jpoke.model import Pokemon

from jpoke.core import BattleContext
from jpoke.enums import Event, Command, Interrupt, LogCode
from jpoke.utils import fast_copy


class TurnController:
    """ターン進行を管理するクラス。

    担当する責務:
    - ターン初期化
    - ポケモン選出処理
    - ターン進行のオーケストレーション（コマンド処理、技発動、交代など）
    - 勝敗判定とスコア計算
    """

    def __init__(self, battle: Battle):
        """TurnControllerを初期化。

        Args:
            battle: Battleインスタンスへの参照
        """
        self.battle = battle

    def __deepcopy__(self, memo):
        """Battleインスタンスのディープコピーを作成する。

        Args:
            memo: コピー済みオブジェクトのメモ辞書

        Returns:
            Battle: コピーされたBattleインスタンス
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[])
        return new

    def update_reference(self, battle: Battle):
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

    def _calc_tod_score(self, player: Player, alpha: float = 1) -> float:
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

    def judge_winner(self) -> Player | None:
        """勝者を判定して返す。

        Returns:
            勝者のPlayerインスタンス、勝負がついていない場合はNone
        """
        if self.battle.winner is not None:
            return self.battle.winner

        TOD_scores = [self._calc_tod_score(pl) for pl in self.battle.players]
        if 0 in TOD_scores:
            loser_idx = TOD_scores.index(0)
            loser = self.battle.players[loser_idx]
            winner = self.battle.players[loser_idx - 1]
            self.battle.add_event_log(winner, LogCode.GAME_WON)
            self.battle.add_event_log(loser, LogCode.GAME_LOST)
            self.battle.winner = winner
            return winner

        return None

    def start_battle(self, commands: dict[Player, list[Command]]):
        """バトル開始処理を実行する。

        選出と初期繰り出しを行い、バトルを0ターン目の開始状態にする。
        """
        if self.battle.turn > 0:
            raise RuntimeError("Battle already started.")

        self.battle.add_event_log(0, LogCode.GAME_STARTED)

        # ポケモンを選出
        for player, cmds in commands.items():
            player.selection_indexes = [c.index for c in cmds]

        # ポケモンを場に出す
        self.battle.run_initial_switch()

        # だっしゅつパックによる交代
        self.battle.run_interrupt_switch(Interrupt.EJECTPACK_ON_START)

        # ターンを1つ進める
        self.battle.turn += 1

    def advance_turn(self, commands: dict["Player", Command]):
        """ターンを1つ進める。

        Args:
            commands: 各プレイヤーのコマンド辞書（Noneの場合は予約済みコマンドを使用）
        """
        if self.battle.turn == 0:
            raise RuntimeError("Battle is not started. Call battle.start() before advance_turn().")

        # 引数のコマンドをスケジュールに追加する
        for player, cmd in commands.items():
            player.reserve_command(cmd)

        # ターン開始処理
        self._begin_turn(commands)

        # 交代フェーズ
        self._run_switch_phase()

        # テラスタル
        self._run_terastal_phase()

        # メガシンカ
        self._run_megaevolve_phase()

        # 技の処理
        self._run_move_phase()

        # ターン終了時の処理
        self._run_end_phase()

    def _begin_turn(self, commands: dict[Player, Command]):
        """ターン開始処理を実行する。"""
        if self.battle.is_new_turn():
            self.init_turn()

    def _run_switch_phase(self):
        """交代フェーズを実行する。"""
        for attacker in self.battle.calc_speed_order():
            idx = self.battle.actives.index(attacker)
            player = self.battle.players[idx]

            # だっしゅつパックによる交代フラグを用意
            interrupt = Interrupt.ejectpack_on_switch(idx)

            # 交代
            if self.battle.is_new_turn():
                if player.reserved_commands[0].is_switch:
                    # 予約されている交代コマンドを取得
                    command = player.reserved_commands.pop(0)

                    # 交代を実行
                    new = player.team[command.index]
                    self.battle.run_switch(player, new)

                # だっしゅつパックによる割り込みフラグを更新
                self.battle.override_interrupt(interrupt)

            # だっしゅつパックによる交代
            self.battle.run_interrupt_switch(interrupt)

    def _run_terastal_phase(self):
        """テラスタルを実行する。"""
        for mon in self.battle.calc_action_order():
            player = self.battle.get_player(mon)
            if not player.reserved_commands:
                continue

            # コマンドがテラスタルで、かつテラスタル可能な場合にテラスタルを実行
            command = player.reserved_commands[0]
            if command.is_terastal and mon.can_terastallize():
                mon.terastallize()
                self.battle.add_event_log(mon, LogCode.TERASALLIZED,
                                          payload={"type": mon.tera_type})

    def _run_megaevolve_phase(self):
        """メガシンカを実行する。"""
        for mon in self.battle.calc_action_order():
            player = self.battle.get_player(mon)
            if not player.reserved_commands:
                continue

            # コマンドがメガシンカで、かつメガシンカ可能な場合にメガシンカを実行
            command = player.reserved_commands[0]
            if command.is_megaevol and mon.can_megaevolve():
                # メガシンカ前の特性を無効化し、メガシンカ後に特性を有効化する
                mon.ability.unregister_handlers(self.events, mon)
                mon.megaevolve()
                mon.ability.register_handlers(self.events, mon)
                self.battle.add_event_log(mon, LogCode.MEGA_EVOLVED,
                                          payload={"pokemon": mon.name})

                # メガシンカ後の特性が発動するイベントを追加
                self.events.emit(Event.ON_ABILITY_ENABLED, BattleContext(source=mon))

    def _run_move_phase(self):
        """技発動フェーズを実行する。"""
        self.events.emit(Event.ON_BEFORE_MOVE)

        for attacker in self.battle.calc_action_order():
            player = self.battle.get_player(attacker)

            if player.has_switched:
                continue

            if self.battle.is_new_turn():
                # コマンドを取得
                command = player.reserved_commands.pop(0)

                # 技を実行
                move = self.battle.command_to_move(player, command)
                self.battle.run_move(attacker, move)

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

    def _run_end_phase(self):
        """ターン終了時の処理を実行する。"""
        # ターン終了時の処理 (1~4)
        turn_end_events = [
            Event.ON_TURN_END_1,
            Event.ON_TURN_END_2,
            Event.ON_TURN_END_3,
            Event.ON_TURN_END_4,
        ]
        for event in turn_end_events:
            if self.battle.is_new_turn():
                self.events.emit(event)

                # ききかいひによる交代
                self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

        # ターン終了時の処理 (5)
        if self.battle.is_new_turn():
            self.events.emit(Event.ON_TURN_END_5)

            # だっしゅつパックによる割り込みフラグを更新
            self.battle.override_interrupt(Interrupt.EJECTPACK_ON_TURN_END)

        # だっしゅつパックによる交代
        self.battle.run_interrupt_switch(Interrupt.EJECTPACK_ON_TURN_END)

        # 瀕死による交代
        self.battle.run_faint_switch()

        # ターン終了時の処理 (6)
        if self.battle.is_new_turn():
            self.battle.events.emit(Event.ON_TURN_END_6)
            self.battle.turn += 1
