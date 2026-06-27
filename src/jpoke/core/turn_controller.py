"""ターン進行を管理するクラス。

Battleクラスの責務を分離し、ターン管理に関連するロジックを担当する。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player
    from jpoke.model import Pokemon

from jpoke.core import EventContext
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
        self.battle = battle

    def __deepcopy__(self, memo):
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
    def _events(self):
        return self.battle.events

    def judge_winner(self) -> Player | None:
        """勝者を判定して返す。

        Returns:
            勝者のPlayerインスタンス、勝負がついていない場合はNone
        """
        if self.battle.winner is not None:
            return self.battle.winner

        TOD_scores = [state.tod_score() for state in self.battle.player_states.values()]
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
        if self.battle.turn >= 0:
            raise RuntimeError("Battle already started.")

        self.battle.turn = 0
        self.battle.add_event_log(0, LogCode.GAME_STARTED)

        # ポケモンを選出
        for player, cmds in commands.items():
            self.battle.player_states[player].selection_indexes = [c.index for c in cmds]

        # ポケモンを場に出す
        self.battle.run_initial_switch()

        # だっしゅつパックによる交代
        self.battle.run_interrupt_switch(Interrupt.EJECTPACK_ON_START)

    def step(self, commands: dict[Player, Command]):
        """ターンを1つ進める。

        Args:
            commands: 各プレイヤーのコマンド辞書（Noneの場合は予約済みコマンドを使用）
        """
        if self.battle.turn < 0:
            raise RuntimeError("Battle is not started. Call battle.start() before step().")

        # ターン開始処理
        self._begin_turn()

        # 引数のコマンドをスケジュールに追加する
        for player, cmd in commands.items():
            self.battle.player_states[player].reserve_command(cmd)

        # 交代フェーズ
        self._run_switch_phase()

        # 行動順を確定し、ターン中に参照できるよう記録
        action_order = self.battle.resolve_action_order()
        self._record_action_order(action_order)

        # テラスタル
        self._run_terastal_phase(action_order)

        # メガシンカ
        self._run_megaevolve_phase(action_order)

        # 技の処理
        self._run_move_phase(action_order)

        # ターン終了時の処理
        self._run_end_phase()

    def _begin_turn(self):
        """ターン開始処理を実行する。"""
        self.battle.turn += 1
        if self.battle.is_new_turn():
            for state in self.battle.player_states.values():
                state.reset_turn_state()

    def _run_switch_phase(self):
        """交代フェーズを実行する。"""
        for attacker in self.battle.resolve_speed_order():
            idx = self.battle.actives.index(attacker)
            player = self.battle.players[idx]
            state = self.battle.player_states[player]

            # だっしゅつパックによる交代フラグを用意
            interrupt = Interrupt.ejectpack_on_switch(idx)

            # 交代
            if self.battle.is_new_turn():
                if state.next_command.is_type("switch"):
                    # 予約されている交代コマンドを取得
                    command = state.pop_command()

                    # 交代を実行
                    new = state.team[command.index]
                    self.battle.run_switch(player, new)

                # だっしゅつパックによる割り込みフラグをフェーズに合わせて設定
                self.battle.override_ejectpack_interrupt(interrupt)

            # だっしゅつパックによる交代
            self.battle.run_interrupt_switch(interrupt)

    def _record_action_order(self, action_order: list[Pokemon]):
        """確定した行動順をプレイヤー状態へ記録する。"""
        for index, mon in enumerate(action_order):
            player = self.battle.get_player(mon)
            self.battle.player_states[player].action_order_index = index

    def _run_terastal_phase(self, action_order: list[Pokemon]):
        """テラスタルを実行する。"""
        for mon in action_order:
            player = self.battle.get_player(mon)
            state = self.battle.player_states[player]
            if not state.command_reserved():
                continue

            # コマンドがテラスタルで、かつテラスタル可能な場合にテラスタルを実行
            command = state.next_command
            if command.is_terastal and mon.can_terastallize():
                mon.terastallize()
                self.battle.add_event_log(
                    mon, LogCode.TERASALLIZED,
                    payload={"type": mon.tera_type}
                )
                self._events.emit(Event.ON_TERASTALLIZE, EventContext(source=mon))

    def _run_megaevolve_phase(self, action_order: list[Pokemon]):
        """メガシンカを実行する。"""
        for mon in action_order:
            player = self.battle.get_player(mon)
            state = self.battle.player_states[player]
            if not state.command_reserved():
                continue

            # コマンドがメガシンカで、かつメガシンカ可能な場合にメガシンカを実行
            command = state.next_command
            if command.is_megaevol and mon.can_megaevolve():
                # メガシンカ前の特性を無効化し、メガシンカ後に特性を有効化する
                mon.ability.unregister_handlers(self._events, mon)
                mon.megaevolve()
                mon.ability.register_handlers(self._events, mon)
                self.battle.add_event_log(
                    mon,
                    LogCode.MEGA_EVOLVED,
                    payload={"pokemon": mon.name}
                )

                # メガシンカ後の特性が発動するイベントを追加
                self._events.emit(Event.ON_ABILITY_ENABLED, EventContext(source=mon))

    def _run_move_phase(self, action_order: list[Pokemon]):
        """技発動フェーズを実行する。"""
        self._events.emit(Event.ON_BEFORE_MOVE)

        for attacker in action_order:
            player = self.battle.get_player(attacker)
            state = self.battle.player_states[player]

            if state.has_switched:
                continue

            if self.battle.is_new_turn():
                # コマンドを取得
                command = state.pop_command()

                # 技を実行
                move = self.battle.command_to_move(player, command)
                self.battle.run_move(attacker, move)

            # だっしゅつボタンによる交代
            self.battle.run_interrupt_switch(Interrupt.EJECTBUTTON)

            # ききかいひによる交代
            self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

            # 交代技による交代
            self.battle.run_interrupt_switch(Interrupt.PIVOT)

            # だっしゅつパックによる割り込みフラグをフェーズに合わせて設定
            interrupt = Interrupt.ejectpack_on_after_move(
                self.battle.players.index(player)
            )
            self.battle.override_ejectpack_interrupt(interrupt)

            # だっしゅつパックによる交代
            self.battle.run_interrupt_switch(interrupt)

    def _run_end_phase(self):
        """ターン終了時の処理を実行する。"""
        if self.battle.is_new_turn():
            self._events.emit(Event.ON_TURN_END)

            # だっしゅつパックによる割り込みフラグをフェーズに合わせて設定
            self.battle.override_ejectpack_interrupt(Interrupt.EJECTPACK_ON_TURN_END)

        # ききかいひによる交代
        self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

        # だっしゅつパックによる交代
        self.battle.run_interrupt_switch(Interrupt.EJECTPACK_ON_TURN_END)

        # 瀕死による交代
        self.battle.run_faint_switch()
