"""交代処理を管理するモジュール。

ポケモンの交代、割り込み処理、瀕死交代などを担当。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .event_manager import EventManager
    from .player import Player

from jpoke.model import Pokemon
from jpoke.enums import Interrupt, LogCode

from .event_manager import Event
from .context import BattleContext


class SwitchManager:
    """交代処理を管理するクラス。

    ポケモンの交代、割り込み処理、瀕死交代などを担当。
    Battleクラスから交代関連の処理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: 'Battle'):
        """SwitchManagerを初期化。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def update_reference(self, battle: 'Battle'):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    @property
    def events(self) -> EventManager:
        """Battleのイベントシステムへのショートカットプロパティ。"""
        return self.battle.events

    def switch_in(self, mon: Pokemon):
        """ポケモンの入場時ハンドラーを登録する。

        Args:
            mon: 場に出るポケモン
        """
        mon.revealed = True
        mon.ability.register_handlers(self.events, mon)
        mon.item.register_handlers(self.events, mon)
        mon.ailment.register_handlers(self.events, mon)
        for volatile in mon.volatiles.values():
            volatile.register_handlers(self.events, mon)

    def switch_out(self, mon: Pokemon):
        """ポケモンの退場時ハンドラーを解除する。

        Args:
            mon: 引っ込むポケモン
        """
        mon.ability.unregister_handlers(self.events, mon)
        mon.item.unregister_handlers(self.events, mon)
        mon.ailment.unregister_handlers(self.events, mon)
        for volatile in mon.volatiles.values():
            volatile.unregister_handlers(self.events, mon)

    def has_interrupt(self) -> bool:
        """割り込みフラグが設定されているか確認。

        Returns:
            いずれかのプレイヤーに割り込みフラグがある場合True
        """
        return any(pl.interrupt != Interrupt.NONE for pl in self.battle.players)

    def override_interrupt(self, flag: Interrupt, only_first: bool = True):
        """割り込みフラグを上書き。

        REQUESTED状態のプレイヤーに対して、指定したフラグを設定する。
        素早さ順に処理され、デフォルトでは最初の1体のみ設定。

        Args:
            flag: 設定する割り込みフラグ
            only_first: 最初の1体のみに設定する場合True
        """
        for mon in self.battle.calc_speed_order():
            player = self.battle.get_player(mon)
            if player.interrupt == Interrupt.REQUESTED:
                player.interrupt = flag
                if only_first:
                    return

    def run_switch(self, player: Player, new: Pokemon, emit: bool = True):
        """ポケモンを交代。

        退場処理、入場処理、イベント発火を行う。

        Args:
            player: 交代を行うプレイヤー
            new: 場に出す新しいポケモン
            emit: ON_SWITCH_INイベントを発火する場合True
        """
        # 割り込みフラグを破棄
        player.interrupt = Interrupt.NONE

        # 退場
        old = player.active
        if old is not None:
            self.events.emit(Event.ON_SWITCH_OUT, BattleContext(source=old))

            # 交代時に消える揮発状態は manager 経由で解除し、終了イベントを発火する。
            for name in list(old.volatiles.keys()):
                self.battle.volatile_manager.remove(old, name)

            self.switch_out(old)

            # TODO : 以下の処理もswitch_outメソッドに含める
            old.bench_reset()
            self.battle.add_event_log(player, LogCode.SWITCH_OUT,
                                      payload={"pokemon": old.name})

        # 入場
        player.active_idx = player.team.index(new)
        self.switch_in(new)

        # TODO : 以下の処理もswitch_inメソッドに含める
        self.battle.refresh_effect_enabled_states()
        self.battle.add_event_log(player, LogCode.SWITCH_IN,
                                  payload={"pokemon": new.name})

        # ポケモンが場に出た時の処理
        if emit:
            self.events.emit(Event.ON_SWITCH_IN, BattleContext(source=new))

            # リクエストがなくなるまで再帰的に交代する
            while self.has_interrupt():
                flag = Interrupt.EJECTPACK_ON_AFTER_SWITCH
                self.override_interrupt(flag)
                self.run_interrupt_switch(flag)

        # その他の処理
        player.has_switched = True

    def run_initial_switch(self):
        """バトル開始時の初期交代。

        選出されたポケモンを場に出し、着地処理を実行する。
        """
        # ポケモンを場に出す
        for pl in self.battle.players:
            new = pl.selection[0]
            self.run_switch(pl, new, emit=False)

        # ポケモンが場に出たときの処理は、両者の交代が完了した後に行う
        self.battle.refresh_effect_enabled_states()
        self.events.emit(Event.ON_SWITCH_IN)

        # だっしゅつパックによる割り込みフラグを更新
        self.override_interrupt(Interrupt.EJECTPACK_ON_START)

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

        for player in self.battle.players:
            if player.interrupt != flag:
                continue

            # 交代を引き起こしたアイテムを消費させる
            if flag.consume_item():
                self.battle.add_event_log(player, LogCode.CONSUME_ITEM,
                                          payload={"item": player.active.item.name})
                self.battle.consume_item(player.active)

            # 予約されているコマンドを破棄し、方策関数に従って交代コマンドを取得
            player.clear_reserved_commands()
            command = player.choose_switch_command(self.battle)

            self.battle.add_command_log(player, command)
            self.run_switch(player, player.team[command.idx], emit=emit_on_each_switch)
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

        # 交代フラグを設定
        if not self.has_interrupt():
            for player in self.battle.players:
                if player.active.fainted:
                    player.interrupt = Interrupt.FAINTED

        # 交代を行うプレイヤー
        switch_players = [pl for pl in self.battle.players if pl.interrupt == Interrupt.FAINTED]

        # 対象プレイヤーがいなければ終了
        if not switch_players:
            return

        # 交代
        self.run_interrupt_switch(Interrupt.FAINTED, False)

        # すべての死に出しが完了するまで再帰的に実行
        self.run_faint_switch()
