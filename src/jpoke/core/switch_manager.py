"""交代処理を管理するモジュール。

ポケモンの交代、割り込み処理、瀕死交代などを担当。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Battle, EventManager, Player, PlayerState

from jpoke.model import Pokemon, Ability
from jpoke.enums import Interrupt, LogCode

from .event_manager import Event
from .context import EventContext
from jpoke.utils import fast_copy


class SwitchManager:
    """交代処理を管理するクラス。

    ポケモンの交代、割り込み処理、瀕死交代などを担当。
    Battleクラスから交代関連の処理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        self.battle = battle
        # 交代退場処理中のポケモン（退場処理中はねむけ→ねむりなどの移行を抑制する）
        self.switching_out_mon: Pokemon | None = None

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
    def _events(self) -> EventManager:
        return self.battle.events

    def can_switch(self, state: PlayerState) -> bool:
        """プレイヤーが交代可能かどうかを判定する。

        Args:
            state: 交代可能かを判定するプレイヤーの状態

        Returns:
            bool: 交代可能な場合True、そうでない場合False
        """
        # 控えのポケモンがすべて瀕死の場合は交代不可
        if all(mon.fainted for mon in state.bench):
            return False

        # 場のポケモンがとらわれ状態にある場合は交代不可
        if self.battle.query.is_trapped(state.active):
            return False

        return True

    def run_switch(self,
                   player: Player,
                   new: Pokemon,
                   process_events_after_switch: bool = True):
        """ポケモンを交代。

        退場処理、入場処理、イベント発火を行う。

        Args:
            player: 交代を行うプレイヤー
            new: 場に出す新しいポケモン
            process_switch_in_events: ON_SWITCH_INイベントを発火する場合True
        """
        state = self.battle.player_states[player]

        # 割り込みフラグを破棄
        state.interrupt = Interrupt.NONE

        # バトンタッチ（またはしっぽきり）の引き継ぎデータを確保
        baton_data = state.baton_pass_data
        state.baton_pass_data = None

        old = state.active
        if old is not None:
            self._switch_out(old)

        # 入場
        self._switch_in(state, new)

        # バトンタッチのランク・volatile を交代先に適用する
        if baton_data is not None:
            # ランク引き継ぎ（クリアボディ等を経由しない直接代入）
            for stat, v in baton_data["rank"].items():
                new.rank[stat] = v
            # volatile 引き継ぎ
            for volatile_name, v_data in baton_data["volatiles"].items():
                count = v_data.get("count")
                kwargs = {k: val for k, val in v_data.items() if k != "count"}
                self.battle.volatile_manager.apply(new, volatile_name, count=count, **kwargs)

        # ポケモンが場に出た時の処理
        if process_events_after_switch:
            self._process_events_after_switch(new)

    def _process_events_after_switch(self, mon: Pokemon):
        """ON_SWITCH_INイベントの処理。

        交代で場に出たポケモンに対して、ON_SWITCH_INイベントを発火する。
        だっしゅつパックなどの割り込み交代が発生した場合は、再帰的に処理する。

        Args:
            mon: 場に出たポケモン
        """
        self._events.emit(
            Event.ON_SWITCH_IN,
            EventContext(source=mon)
        )

        # リクエストがなくなるまで再帰的に交代する
        while self.battle.has_interrupt():
            flag = Interrupt.EJECTPACK_ON_AFTER_SWITCH
            self._override_ejectpack_interrupt(flag)
            self.run_interrupt_switch(flag)

    def run_initial_switch(self):
        """バトル開始時の初期交代。

        選出されたポケモンを場に出し、着地処理を実行する。
        """
        # ポケモンを場に出す
        for state in self.battle.player_states.values():
            new = state.selection[0]
            self._switch_in(state, new)

        # ポケモンが場に出たときの処理は、両者の交代が完了した後に行う
        self._events.emit(Event.ON_SWITCH_IN)

        # だっしゅつパックによる割り込みフラグをフェーズに合わせて設定
        self._override_ejectpack_interrupt(Interrupt.EJECTPACK_ON_START)

    def run_interrupt_switch(self,
                             flag: Interrupt,
                             process_event_on_each_switch: bool = True):
        """割り込み交代を実行。

        指定したフラグを持つプレイヤーの交代を処理する。
        だっしゅつパック、だっしゅつボタン、ききかいひなどの
        アイテム・特性による交代を処理。

        Args:
            flag: 対象とする割り込みフラグ
            process_event_on_each_switch: 各交代ごとにON_SWITCH_INを発火する場合True
        """
        switched_players = set()

        for player, state in self.battle.player_states.items():
            if state.interrupt != flag:
                continue

            # 消費アイテムによる交代の場合はアイテムを消費させる
            if flag.requires_item_consumption():
                self.battle.consume_item(state.active)

            if state.command_reserved() and state.next_command.is_switch():
                # 予約されている交代コマンドを使う
                command = state.pop_command()
            else:
                # 方策関数に従う
                command = self.battle.resolve_switch_command(player)

            self.run_switch(
                player,
                state.team[command.index],
                process_events_after_switch=process_event_on_each_switch
            )
            switched_players.add(player)

        if process_event_on_each_switch:
            return

        # 交代したプレイヤー全員の着地処理を同時に実行
        for mon in self.battle.resolve_speed_order():
            player = self.battle.get_player(mon)
            if player in switched_players:
                self._events.emit(Event.ON_SWITCH_IN, EventContext(source=mon))

    def run_faint_switch(self):
        """瀕死による交代を実行。

        HPが0になったポケモンを交代させる。
        再帰的に実行し、すべての死に出しが完了するまで処理する。
        """
        if self.battle.judge_winner():
            return

        # 瀕死による交代フラグを設定
        if not self.battle.has_interrupt():
            for state in self.battle.player_states.values():
                if state.active.fainted:
                    state.interrupt = Interrupt.FAINTED

        # 交代を行うプレイヤー
        switch_players = [pl for pl, state in self.battle.player_states.items()
                          if state.interrupt == Interrupt.FAINTED]

        # 対象プレイヤーがいなければ終了
        if not switch_players:
            return

        # 交代
        self.run_interrupt_switch(Interrupt.FAINTED, False)

        # すべての死に出しが完了するまで再帰的に実行
        self.run_faint_switch()

    def _switch_in(self, state: PlayerState, mon: Pokemon):
        """ポケモンの入場処理。

        Args:
            state: 交代を行うプレイヤーの状態
            mon: 入場するポケモン
        """
        state.active_index = state.team.index(mon)
        state.has_switched = True

        mon.reset_on_switch_in()
        self._register_handlers_on_switch_in(mon)

        self.battle.add_event_log(
            mon,
            LogCode.SWITCHED_IN,
            payload={"pokemon": mon.name}
        )

    def _switch_out(self, mon: Pokemon):
        """ポケモンの退場処理。

        Args:
            mon: 退場するポケモン
        """
        self._events.emit(
            Event.ON_SWITCH_OUT,
            EventContext(source=mon)
        )

        # 揮発状態をすべて解除（退場処理中フラグを立てて揮発終了時の副作用を抑制）
        self.switching_out_mon = mon
        self.battle.remove_all_volatiles(mon)
        self.switching_out_mon = None

        mon.reset_on_switch_out()
        self._unregister_handlers_on_switch_out(mon)

        self.battle.add_event_log(
            mon, LogCode.SWITCHED_OUT,
            payload={"pokemon": mon.name}
        )

    def _override_ejectpack_interrupt(self, flag: Interrupt):
        """割り込みフラグを上書き。

        EJECTPACK_REQUESTED状態のプレイヤーに対して、指定したフラグを設定する。
        素早さ順に処理され、最初に見つかったプレイヤーのフラグが更新される。

        Args:
            flag: 設定する割り込みフラグ
        """
        for mon in self.battle.resolve_speed_order():
            player = self.battle.get_player(mon)
            state = self.battle.player_states[player]
            if state.interrupt == Interrupt.EJECTPACK_REQUESTED:
                state.interrupt = flag
                return

    def _register_handlers_on_switch_in(self, mon: Pokemon):
        """特性とアイテムのハンドラをバトルに登録する。

        Args:
            events: イベントマネージャー
        """
        mon.ability.register_handlers(self._events, mon)
        mon.item.register_handlers(self._events, mon)
        mon.ailment.register_handlers(self._events, mon)

    def _unregister_handlers_on_switch_out(self, mon: Pokemon):
        """特性とアイテムのハンドラをバトルから解除する。

        Args:
            events: イベントマネージャー
        """
        mon.ability.unregister_handlers(self._events, mon)
        mon.item.unregister_handlers(self._events, mon)
        mon.ailment.unregister_handlers(self._events, mon)
