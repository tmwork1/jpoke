"""ターン進行を管理するクラス。

Battleクラスの責務を分離し、ターン管理に関連するロジックを担当する。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player

from .context import EventContext
from jpoke.core.log_payload import TerastalPayload
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
        self.action_order: list[int] = []
        # judge_winner() で勝者が確定した際、GAME_WON/GAME_LOST ログの記録を
        # 遅延させる場合に一時保持する (winner, loser) のペア。
        # flush_winner_log() で実際にログへ記録する。
        self._pending_winner_log: tuple[Player, Player] | None = None
        # 勝敗ログの自動フラッシュを抑制する区間の深さ（ネスト可能なカウンタ）。
        # begin_deferred_winner_log() 〜 end_deferred_winner_log() の間は、
        # この区間の内側で発生した他の modify_hp 呼び出し（技のダメージによる
        # 撃破に付随するさめはだ等の反撃ダメージ・状態異常付与など）が
        # flush_winner_log() を呼んでも、区間を開いた呼び出し元が明示的に
        # end_deferred_winner_log() を呼ぶまでログ記録を遅延させる。
        # 区間は Python の呼び出しスタック上ではネストしない（対象の modify_hp
        # 呼び出しは既に return しており、後続のイベント発火中に別の
        # modify_hp 呼び出しが行われる）ため、真偽値ではなくカウンタで管理する。
        self._deferred_flush_depth = 0

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

    @property
    def _switch(self):
        return self.battle.switch_manager

    def judge_winner(self) -> Player | None:
        """勝者を判定して返す。

        勝者の確定（`self.battle.winner` への設定）はこの呼び出しの中で即座に行うが、
        GAME_WON/GAME_LOST ログの記録は `flush_winner_log()` が呼ばれるまで保留する
        場合がある（`begin_deferred_winner_log()` / `end_deferred_winner_log()` を
        参照）。瀕死の同時発生（例: みちづれによる相打ち）で勝者判定そのものが
        呼び出し順に依存するケースがあるため、判定タイミング自体は変更しない。

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
            self.battle.winner = winner
            self._pending_winner_log = (winner, loser)
            return winner

        return None

    def flush_winner_log(self) -> None:
        """保留中のGAME_WON/GAME_LOSTログがあれば記録する。

        `begin_deferred_winner_log()` 〜 `end_deferred_winner_log()` の抑制区間
        （デフォルトでは開かれていない）の内側では何もしない。区間の内側で
        この関数を呼んでも記録は行われず、区間が閉じられた時点
        （`end_deferred_winner_log()`）で改めて評価される。保留がなければ
        （抑制区間の外でも）何もしない。
        """
        if self._deferred_flush_depth > 0:
            return
        if self._pending_winner_log is None:
            return
        winner, loser = self._pending_winner_log
        self.battle.add_event_log(winner, LogCode.GAME_WON)
        self.battle.add_event_log(loser, LogCode.GAME_LOST)
        self._pending_winner_log = None

    def begin_deferred_winner_log(self) -> None:
        """勝敗ログの自動フラッシュを抑制する区間を開始する（ネスト可）。

        技の1ヒット処理（move_executor._execute_hit）のように、1回の
        HP変化とそれに付随する後続イベント（ON_HIT・ON_DAMAGE_HIT・ON_MOVE_KO
        等）をひとまとまりとして扱いたい場合に、その処理の先頭で呼ぶ。
        区間の内側で発生した他の modify_hp 呼び出し（撃破に付随する
        さめはだ等の反撃ダメージ・状態異常付与など）による自動フラッシュは
        抑制され、対応する `end_deferred_winner_log()` が呼ばれるまで
        GAME_WON/GAME_LOST ログの記録が遅延する。
        """
        self._deferred_flush_depth += 1

    def end_deferred_winner_log(self) -> None:
        """`begin_deferred_winner_log()` に対応する抑制区間を終了する。

        区間の深さが0に戻った時点で、保留中のログがあれば記録する。
        """
        if self._deferred_flush_depth > 0:
            self._deferred_flush_depth -= 1
        self.flush_winner_log()

    def start_battle(self):
        """バトル開始処理を実行する。

        選出と初期繰り出しを行い、バトルを0ターン目の開始状態にする。
        """
        if self.battle.turn >= 0:
            raise RuntimeError("Battle already started.")

        self.battle.turn = 0

        # ポケモンを選出する
        self._run_selection()

        self.battle.add_event_log(0, LogCode.GAME_STARTED)

        # 先頭のポケモンを場に出す
        self._switch.run_initial_switch()

        # だっしゅつパックによる交代
        self._switch.run_interrupt_switch(Interrupt.EJECTPACK_ON_START)

    def _run_selection(self):
        with self.battle.phase_context("selection"):
            for player in self.battle.players:
                observed = self.battle.build_observation(player)
                indexes = player.choose_selection(observed)
                self.battle.player_states[player].selected_indexes = indexes

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

        # 行動順解決
        self._resolve_action_order()

        # テラスタル
        self._run_terastal_phase()

        # メガシンカ
        self._run_megaevolve_phase()

        # 予備動作（きあいパンチ・くちばしキャノン等の準備行動）
        self._run_before_move_phase()

        # 技の処理
        self._run_move_phase()

        # ターン終了時の処理
        self._run_end_phase()

    def _begin_turn(self):
        """ターン開始処理を実行する。"""
        self.battle.turn += 1
        if self.battle.is_new_turn():
            self.action_order = []
            for state in self.battle.player_states.values():
                state.reset_turn_state()

    def _run_switch_phase(self):
        """交代フェーズを実行する。

        Note:
            対象プレイヤーは `resolve_speed_order()` の時点（このフェーズ開始時）で
            決定し、以降はプレイヤー単位で処理する。ループの途中でいかく・
            だっしゅつパックなどの割り込みにより一方のプレイヤーが先に交代すると、
            `self.battle.actives` の中身が変化し、まだ処理していない側の元の
            ポケモン参照が `actives` から消えてしまう。ループのたびに
            `self.battle.actives.index(attacker)` で交代後の場を引き直すと
            ValueError（値が見つからない）を起こすため、所属プレイヤーを
            ポケモンの所有関係（`get_player`）から一度だけ解決し、以降は
            プレイヤー・状態を使って処理する。
        """
        order = [
            self.battle.players.index(self.battle.get_player(attacker))
            for attacker in self.battle.resolve_speed_order()
        ]
        for idx in order:
            # ターン中に勝敗が既に確定している場合、残りのキュー済み交代は
            # 実行しない（瀕死による事前確定など、稀なケース向けの保険）。
            if self.battle.winner is not None:
                break

            player = self.battle.players[idx]
            state = self.battle.player_states[player]

            # だっしゅつパックによる交代フラグを用意
            interrupt = Interrupt.ejectpack_on_switch(idx)

            # 交代
            if self.battle.is_new_turn():
                if not state.has_switched and state.next_command.is_type("switch"):
                    # 行動順を記録
                    self.action_order.append(idx)

                    # 予約されている交代コマンドを取得
                    command = state.pop_command()

                    # 交代を実行
                    new = state.team[command.index]
                    self.battle.run_switch(player, new)

                # だっしゅつパックによる割り込みフラグをフェーズに合わせて設定
                self._switch.override_ejectpack_interrupt(interrupt)

            # だっしゅつパックによる交代
            self._switch.run_interrupt_switch(interrupt)

        # いかく・だっしゅつパックなどの割り込みにより、あるプレイヤーの
        # 交代がループの途中（自分の番より後に処理される別プレイヤーの交代
        # に付随して）発生することがある。この場合、今ターン用に予約されて
        # いたコマンド（例: MOVE_x や SWITCH_x）が一度も使われないまま予約
        # リストに残ってしまう（割り込み交代は別経路で解決されるため）。
        # ループの途中で対象プレイヤーの番を判定して破棄しようとすると、
        # 自分の番より後に発生した割り込み交代を取りこぼす（ループが既に
        # そのプレイヤーの番を通過済みのため）。残しておくと次ターンの
        # 新しいコマンドの手前に古いコマンドが残留し、交代後のポケモンに
        # 対して不正なインデックスのコマンドが誤って使われてしまう
        # （IndexError の原因）。そのためループ全体が終わった時点で、
        # 交代済みかつコマンドが残っている全プレイヤーをまとめて破棄する。
        if self.battle.is_new_turn():
            for state in self.battle.player_states.values():
                if state.has_switched and state.command_reserved():
                    state.pop_command()

    def _resolve_action_order(self):
        """行動順を解決する。"""
        if not self.battle.is_new_turn():
            return

        action_order = self.battle.speed_calculator.resolve_action_order()
        for mon in action_order:
            index = self.battle.actives.index(mon)
            self.action_order.append(index)

    def _run_terastal_phase(self):
        """テラスタルを実行する。"""
        if not self.battle.is_new_turn():
            return

        for index in self.action_order:
            player = self.battle.players[index]
            state = self.battle.player_states[player]
            if not state.command_reserved():
                continue

            # コマンドがテラスタルで、かつテラスタル可能な場合にテラスタルを実行
            mon = state.active
            command = state.next_command
            if command.is_terastal and mon.can_terastallize():
                mon.terastallize()
                self.battle.add_event_log(
                    mon, LogCode.TERASALLIZED,
                    payload=TerastalPayload(type=mon.tera_type)
                )
                self._events.emit(Event.ON_TERASTALLIZE, EventContext(source=mon))

    def _run_megaevolve_phase(self):
        """メガシンカを実行する。"""
        if not self.battle.is_new_turn():
            return

        for index in self.action_order:
            player = self.battle.players[index]
            state = self.battle.player_states[player]
            if not state.command_reserved():
                continue

            # コマンドがメガシンカで、かつメガシンカ可能な場合にメガシンカを実行
            mon = state.active
            command = state.next_command
            if command.is_megaevol and mon.can_megaevolve():
                # メガシンカ前の特性を無効化し、メガシンカ後に特性を有効化する
                mon.ability.unregister_handlers(self._events, mon)
                mon.megaevolve()
                mon.ability.register_handlers(self._events, mon)
                self.battle.add_event_log(mon, LogCode.MEGA_EVOLVED)

                # メガシンカ後の特性が発動するイベントを追加
                self._events.emit(Event.ON_ABILITY_ENABLED, EventContext(source=mon))

    def _run_before_move_phase(self):
        """予備動作フェーズを実行する。

        行動順解決後・実際の技実行前に、各プレイヤーの予約コマンドを技に解決した上で
        Event.ON_BEFORE_MOVE を発火する（くちばしキャノンの加熱等、行動可否の判定より
        前に「この技を選んだ」時点で発動する効果向け）。技本体の実行ではないため、
        対象の技ハンドラは発火直後に解除し、後続の run_move での登録と重複させない。
        """
        if not self.battle.is_new_turn():
            return

        for index in self.action_order:
            player = self.battle.players[index]
            state = self.battle.player_states[player]
            if not state.command_reserved():
                continue

            mon = state.active
            command = state.next_command
            if not command.is_type("move") or mon.fainted:
                continue

            move = self.battle.command_to_move(player, command)
            move.register_handlers(self._events, mon)
            try:
                self._events.emit(Event.ON_BEFORE_MOVE, EventContext(source=mon))
            finally:
                move.unregister_handlers(self._events, mon)

    def _run_move_phase(self):
        """技発動フェーズを実行する。"""
        for index in self.action_order:
            # ターン中に勝敗が既に確定している場合、残りのキュー済み行動
            # （さいはい等の割り込みで先に決着がついた後に残っている本来の
            # 行動コマンドなど）は実行しない。
            if self.battle.winner is not None:
                break

            player = self.battle.players[index]
            state = self.battle.player_states[player]

            if state.has_switched:
                # ききかいひ・だっしゅつパックなどの割り込み交代によって、この
                # ターンの本来の行動コマンド（例: MOVE_x）が一度も
                # pop_command() されないまま予約リストに残っていることがある
                # （交代が優先されて技コマンドの実行がスキップされるため）。
                # 残しておくと次のターンの新しいコマンドの手前に古いコマンドが
                # 残留し、交代後のポケモンに対して不正なインデックスの技コマンド
                # が誤って使われてしまう（IndexError の原因）。そのためここで
                # 使われなかったコマンドを破棄しておく。
                if self.battle.is_new_turn() and state.command_reserved():
                    state.pop_command()
                continue

            if self.battle.is_new_turn():
                # コマンドを取得
                command = state.pop_command()

                attacker = state.active
                if attacker.fainted:
                    continue

                # 技を実行
                move = self.battle.command_to_move(player, command)
                self.battle.run_move(attacker, move)

                # 今の技の実行で勝敗が確定した場合、割り込み交代を含め
                # このターンの残りの処理は行わない。
                if self.battle.winner is not None:
                    break

            # だっしゅつボタンによる交代
            self._switch.run_interrupt_switch(Interrupt.EJECTBUTTON)

            # ききかいひによる交代
            self._switch.run_interrupt_switch(Interrupt.EMERGENCY)

            # 交代技による交代
            self._switch.run_interrupt_switch(Interrupt.PIVOT)

            # だっしゅつパックによる割り込みフラグをフェーズに合わせて設定
            interrupt = Interrupt.ejectpack_on_after_move(
                self.battle.players.index(player)
            )
            self._switch.override_ejectpack_interrupt(interrupt)

            # だっしゅつパックによる交代
            self._switch.run_interrupt_switch(interrupt)

    def _run_end_phase(self):
        """ターン終了時の処理を実行する。"""
        # ターン中の技実行等で既に勝敗が確定している場合、どく・やけど等の
        # ターン終了時の継続ダメージ処理（ON_TURN_END）は実行しない
        # （決着後に敗者側の追加行動や勝者側への継続ダメージが記録される
        # のを防ぐ）。ただし瀕死交代処理（run_faint_switch）は決着後でも
        # 内部で battle.judge_winner() を確認した上で早期returnする既存の
        # 安全策があるため、そのまま呼び出す。
        # なお ON_TURN_END は速度順に複数個体（どく・やけど・天候ダメージ等）
        # のハンドラをまとめて処理するため、フェーズ開始時点のガードだけでは
        # 不十分（先に処理された個体の瀕死でイベント処理の途中に決着が
        # ついても、残りのハンドラがそのまま実行されてしまう）。
        # stop_if_winner_determined=True で、途中で決着した場合に残りの
        # ハンドラの実行を打ち切る。
        if self.battle.is_new_turn() and self.battle.winner is None:
            self._events.emit(Event.ON_TURN_END, stop_if_winner_determined=True)

            # だっしゅつパックによる割り込みフラグをフェーズに合わせて設定
            self._switch.override_ejectpack_interrupt(Interrupt.EJECTPACK_ON_TURN_END)

        # ききかいひによる交代
        self._switch.run_interrupt_switch(Interrupt.EMERGENCY)

        # だっしゅつパックによる交代
        self._switch.run_interrupt_switch(Interrupt.EJECTPACK_ON_TURN_END)

        # 瀕死による交代
        self._switch.run_faint_switch()
