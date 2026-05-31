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
from .context import BattleContext
from jpoke.utils import fast_copy


class SwitchManager:
    """交代処理を管理するクラス。

    ポケモンの交代、割り込み処理、瀕死交代などを担当。
    Battleクラスから交代関連の処理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        """SwitchManagerを初期化。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def __deepcopy__(self, memo):
        """SwitchManagerインスタンスのディープコピーを作成する。

        Args:
            memo: コピー済みオブジェクトのメモ辞書

        Returns:
            SwitchManager: コピーされたSwitchManagerインスタンス
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
    def events(self) -> EventManager:
        """Battleのイベントシステムへのショートカットプロパティ。"""
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
        if self.battle.query_manager.is_trapped(state.active):
            return False

        return True

    def _switch_in(self, state: PlayerState, mon: Pokemon):
        # TODO : 関数内の処理はハンドラの登録に限定すべきか
        """ポケモンの入場時ハンドラーを登録する。

        Args:
            state: 交代を行うプレイヤーの状態
            mon: 場に出るポケモン
        """
        state.active_index = state.team.index(mon)
        state.has_switched = True

        mon.revealed = True
        mon.ability.register_handlers(self.events, mon)
        mon.item.register_handlers(self.events, mon)
        mon.ailment.register_handlers(self.events, mon)
        for volatile in mon.volatiles.values():
            volatile.register_handlers(self.events, mon)

        self.battle.add_event_log(mon, LogCode.SWITCHED_IN,
                                  payload={"pokemon": mon.name})

    def _switch_out(self, mon: Pokemon):
        # TODO : ハンドラの解除とその他のリセットは関数を分けるべきか
        """ポケモンの退場時ハンドラーを解除する。

        Args:
            mon: 引っ込むポケモン
        """
        self.events.emit(Event.ON_SWITCH_OUT, BattleContext(source=mon))

        # 交代時に消える揮発状態は manager 経由で解除し、終了イベントを発火する。
        for name in list(mon.volatiles.keys()):
            self.battle.volatile_manager.remove(mon, name)

        mon.ability.unregister_handlers(self.events, mon)
        mon.item.unregister_handlers(self.events, mon)
        mon.ailment.unregister_handlers(self.events, mon)
        for volatile in mon.volatiles.values():
            volatile.unregister_handlers(self.events, mon)

        mon.reset_on_switch_out()
        if mon.ability.base_name != mon.base_ability_name:
            mon.ability = Ability(mon.base_ability_name)
        else:
            mon.ability.reset_on_switch_out()
        mon.item.reset_on_switch_out()

        self.battle.add_event_log(mon, LogCode.SWITCHED_OUT,
                                  payload={"pokemon": mon.name})

    def override_ejectpack_interrupt(self, flag: Interrupt):
        """割り込みフラグを上書き。

        EJECTPACK_REQUESTED状態のプレイヤーに対して、指定したフラグを設定する。
        素早さ順に処理され、最初に見つかったプレイヤーのフラグが更新される。

        Args:
            flag: 設定する割り込みフラグ
        """
        for mon in self.battle.calc_speed_order():
            player = self.battle.get_player(mon)
            state = self.battle.player_states[player]
            if state.interrupt == Interrupt.EJECTPACK_REQUESTED:
                state.interrupt = flag
                return

    def run_switch(self,
                   player: Player,
                   new: Pokemon,
                   emit_switch_in_event: bool = True):
        """ポケモンを交代。

        退場処理、入場処理、イベント発火を行う。

        Args:
            player: 交代を行うプレイヤー
            new: 場に出す新しいポケモン
            emit_switch_in_event: ON_SWITCH_INイベントを発火する場合True
        """
        state = self.battle.player_states[player]

        # 割り込みフラグを破棄
        state.interrupt = Interrupt.NONE

        # 退場
        old = state.active
        if old is not None:
            self._switch_out(old)

        # 入場
        self._switch_in(state, new)

        # ポケモンが場に出た時の処理
        if emit_switch_in_event:
            self.events.emit(Event.ON_SWITCH_IN, BattleContext(source=new))

            # リクエストがなくなるまで再帰的に交代する
            while self.battle.has_interrupt():
                flag = Interrupt.EJECTPACK_ON_AFTER_SWITCH
                self.override_ejectpack_interrupt(flag)
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
        self.events.emit(Event.ON_SWITCH_IN)

        # だっしゅつパックによる割り込みフラグをフェーズに合わせて設定
        self.override_ejectpack_interrupt(Interrupt.EJECTPACK_ON_START)

    def run_interrupt_switch(self, flag: Interrupt, emit_on_each_switch: bool = True):
        """割り込み交代を実行。

        指定したフラグを持つプレイヤーの交代を処理する。
        だっしゅつパック、だっしゅつボタン、ききかいひなどの
        アイテム・特性による交代を処理。

        Args:
            flag: 対象とする割り込みフラグ
            emit_on_each_switch: 各交代ごとにON_SWITCH_INを発火する場合True
        """
        switched_players = []

        for player, state in self.battle.player_states.items():
            if state.interrupt != flag:
                continue

            # 交代を引き起こしたアイテムを消費させる
            if flag.requires_item_consumption():
                self.battle.consume_item(state.active)

            # 予約されているコマンドを破棄し、方策関数に従って交代コマンドを取得
            command = self.battle.resolve_switch_command(player)

            self.run_switch(
                player,
                state.team[command.index],
                emit_switch_in_event=emit_on_each_switch
            )
            switched_players.append(player)

        # 全員の着地処理を同時に実行
        if not emit_on_each_switch:
            for mon in self.battle.calc_speed_order():
                player = self.battle.get_player(mon)
                if player in switched_players:
                    self.events.emit(Event.ON_SWITCH_IN, BattleContext(source=mon))

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
