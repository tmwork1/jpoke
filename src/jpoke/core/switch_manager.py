"""交代処理を管理するモジュール。

ポケモンの交代、割り込み処理、瀕死交代などを担当。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Battle, EventManager, Player, PlayerState

from jpoke.model.pokemon import Pokemon
from jpoke.enums import Interrupt, LogCode
from jpoke.exceptions import InvalidCommandError

from .event_manager import Event
from .context import EventContext
from .log_payload import StatChangePayload
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

        # 瀕死交代（死に出し）かどうかを、割り込みフラグを破棄する前に記録する
        # （はりこみ: 死に出しで出てきた相手には発動しないため）
        fainted_switch = state.interrupt == Interrupt.FAINTED

        # 割り込みフラグを破棄
        state.interrupt = Interrupt.NONE

        # バトンタッチ（またはしっぽきり）の引き継ぎデータを確保
        baton_data = state.baton_pass_data
        state.baton_pass_data = {}

        old = state.active
        if old is not None:
            self._switch_out(old)

        # 入場
        self._switch_in(state, new)
        state.switched_in_by_faint = fainted_switch

        # バトンタッチのランク・volatile を交代先に適用する
        if baton_data:
            # ランク引き継ぎ（クリアボディ等を経由しない直接代入）
            inherited_ranks = {
                stat: v for stat, v in baton_data["boosts"].items()
                if v != new.boosts[stat]
            }
            for stat, v in baton_data["boosts"].items():
                new.boosts[stat] = v
            if inherited_ranks:
                self.battle.add_event_log(
                    new, LogCode.STAT_CHANGED,
                    payload=StatChangePayload(
                        stats=inherited_ranks, display_reason="バトンタッチ",
                    ),
                )
            # volatile 引き継ぎ
            for volatile_name, v_data in baton_data["volatiles"].items():
                # とくせいなしは、バトン先の特性が protected フラグを持つ場合や
                # とくせいガード等で特性変更がブロックされる場合、消える（付与しない）
                # .internal/spec/volatiles/とくせいなし.md 参照
                if (
                    volatile_name == "とくせいなし"
                    and (
                        new.ability.has_flag("protected")
                        or self.battle.ability_manager.is_change_blocked(new)
                    )
                ):
                    continue
                count = v_data.get("count")
                kwargs = {k: val for k, val in v_data.items() if k != "count"}
                self.battle.volatile_manager.apply(new, volatile_name, count=count, **kwargs)

        # ポケモンが場に出た時の処理
        if process_events_after_switch:
            self._process_events_after_switch(new)

    def _process_events_after_switch(self, mon: Pokemon):
        """ON_SWITCH_INイベントの処理。

        交代で場に出たポケモンに対して、ON_SWITCH_INイベントを発火する。
        だっしゅつパック・ききかいひなどの割り込み交代が発生した場合は、再帰的に処理する。

        Args:
            mon: 場に出たポケモン
        """
        self._events.emit(
            Event.ON_SWITCH_IN,
            EventContext(source=mon),
        )

        self.resolve_pending_interrupts(Interrupt.EJECTPACK_ON_AFTER_SWITCH)

    def resolve_pending_interrupts(self, ejectpack_flag: Interrupt) -> None:
        """だっしゅつパック・ききかいひ／にげごしの割り込みがなくなるまで再帰的に解決する。

        交代・メガシンカなど「ポケモンの状態が変わる処理」の直後には、その着地処理
        （ON_SWITCH_IN・ON_ABILITY_ENABLED等）でさらに別のポケモンのだっしゅつパック
        （`Interrupt.EJECTPACK_REQUESTED`）やききかいひ・にげごしの緊急交代
        （`Interrupt.EMERGENCY`）の発動条件が新たに満たされることがある
        （まきびし・ステルスロックなどの入場時ダメージ、いかく等の能力低下）。

        これらを解決せずに呼び出し元へ処理を戻すと`battle.is_new_turn()`
        （= `not battle.has_interrupt()`）がFalseのままになる。`is_new_turn()`は
        行動順解決・テラスタル・メガシンカ・技実行フェーズ等、TurnControllerの
        多くのフェーズのガード条件に使われているため、解決し忘れるとそれらの
        フェーズが丸ごとスキップされ、まだ実行されていない行動コマンドが
        pop_command()されないまま予約リストに残留してしまう（次ターンの新しい
        コマンドの手前に古いコマンドが残り、交代後のポケモンに対して不正な
        インデックスで解決されIndexErrorになる。fuzz seed=23090, 117420 で発見）。

        過去はだっしゅつパック用・ききかいひ用に別々のループを個別実装しており
        （`_resolve_ejectpack_after_switch` / `_resolve_emergency_after_switch`）、
        新しい呼び出し元（TurnController._run_megaevolve_phase等）を追加するたびに
        同種のループを手書きする再発パターンになっていた（fuzz seed=147267）。
        呼び出し元ごとに書き直さずに済むよう、この1メソッドに一元化してある。

        Args:
            ejectpack_flag: だっしゅつパックの発動条件を満たしたポケモンに割り当てる
                割り込みフラグ。呼び出し元のフェーズに応じた値
                （`Interrupt.EJECTPACK_ON_AFTER_SWITCH` /
                `Interrupt.EJECTPACK_ON_AFTER_MEGAEVOLVE` 等）を渡す。

        Note:
            ループ条件は `Interrupt.EJECTPACK_REQUESTED` / `Interrupt.EMERGENCY` の
            有無に限定する必要がある。`battle.has_interrupt()`（全プレイヤーの割り込み
            状態を問わず判定）を条件に使うと、まだ処理順が回ってきていない別プレイヤーの
            交代技（PIVOT等）による割り込みフラグが残っている間、このループが解消不能な
            条件で回り続けて無限ループになる（このメソッドが処理できるのは
            EJECTPACK_REQUESTED・EMERGENCYのみで、PIVOT等の他の割り込み種別は
            ここでは解決されないため）。

            瀕死交代（`run_faint_switch`）はこのメソッドを経由しない別経路
            （`process_event_on_each_switch=False`によるON_SWITCH_INの遅延・一括発火）
            を使うが、そちらも本メソッドを呼び出した上で、さらに
            `run_faint_switch`自身の再帰処理により同種の連鎖を解決している。
        """
        settled = False
        while not settled:
            settled = True
            if any(
                state.interrupt == Interrupt.EJECTPACK_REQUESTED
                for state in self.battle.player_states.values()
            ):
                self.override_ejectpack_interrupt(ejectpack_flag)
                self.run_interrupt_switch(ejectpack_flag)
                settled = False
            if any(
                state.interrupt == Interrupt.EMERGENCY
                for state in self.battle.player_states.values()
            ):
                self.run_interrupt_switch(Interrupt.EMERGENCY)
                settled = False

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
        self.override_ejectpack_interrupt(Interrupt.EJECTPACK_ON_START)

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
                required_item = flag.required_item_name()
                if required_item and state.active.item.name != required_item:
                    # 発動条件を満たした後、交代する前にマジシャン・わるいてぐせなどで
                    # アイテムを失っていた場合は交代しない
                    state.interrupt = Interrupt.NONE
                    continue
                self.battle.item_manager.consume_item(state.active)

            if state.command_reserved() and state.next_command.is_switch:
                # 予約されている交代コマンドを使う
                command = state.pop_command()
            else:
                # 方策関数に従う
                commands = self.battle.resolve_command("switch", player)
                command = commands[player]

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
                self._events.emit(
                    Event.ON_SWITCH_IN,
                    EventContext(source=mon),
                )

        # 上記の着地処理（例: ねばねばネットによるすばやさ低下）でだっしゅつパック・
        # ききかいひの発動条件が新たに満たされた場合、ここで解決しないと割り込み
        # フラグが誰にも処理されないまま残留し、次ターンの `is_new_turn()` 判定を
        # 壊してしまう（fuzz seed=23090 で発見）。通常の交代経路
        # （`_process_events_after_switch`）と共通の解決処理を、この遅延発火経路
        # （瀕死交代で使用）でも行う。
        self.resolve_pending_interrupts(Interrupt.EJECTPACK_ON_AFTER_SWITCH)

    def run_faint_switch(self, _depth: int = 0):
        """瀕死による交代を実行。

        HPが0になったポケモンを交代させる。
        再帰的に実行し、すべての死に出しが完了するまで処理する。

        Note:
            瀕死交代で場に出たポケモンが、まきびし等の入場時ダメージ
            （`Event.ON_HP_CHANGED`）でにげごし・ききかいひの発動条件
            （HPが半分以下になったこと）を新たに満たすことがある。この
            `Interrupt.EMERGENCY` はここで生じる ON_SWITCH_IN の遅延発火
            （`run_interrupt_switch(..., process_event_on_each_switch=False)`）の
            中で立つため、瀕死交代のみを処理して終了すると誰にも解決されずに
            残ってしまい、次ターンの `is_new_turn()`（=`not has_interrupt()`）
            判定を壊してバトルが進行不能になる（fuzz seed=18407 で発見された
            InvalidCommandError の原因）。そのため瀕死交代・緊急交代のどちらの
            割り込みもなくなるまで再帰的に処理する。

        Args:
            _depth: 内部専用の再帰深さカウンタ。方策関数が状況を進行させない
                （瀕死ポケモンが交代後も active のままになる等の）コマンドを
                返し続けると本来終了しない再帰になるため、非進行ガードとして使う。
                呼び出し元は指定しないこと。
        """
        if self.battle.judge_winner():
            return

        # 瀕死による交代フラグを設定
        if not self.battle.has_interrupt():
            for state in self.battle.player_states.values():
                if state.active.fainted:
                    state.interrupt = Interrupt.FAINTED

        # 交代を行うプレイヤー（瀕死交代・緊急交代の両方を対象にする）
        faint_players = [pl for pl, state in self.battle.player_states.items()
                         if state.interrupt == Interrupt.FAINTED]
        emergency_players = [pl for pl, state in self.battle.player_states.items()
                             if state.interrupt == Interrupt.EMERGENCY]

        # 対象プレイヤーがいなければ終了
        if not faint_players and not emergency_players:
            return

        # 非進行ガード: 両プレイヤーの総ポケモン数を超えて再帰した場合は、
        # 方策関数が瀕死交代・緊急交代を進行させるコマンドを返せていないと判断し、
        # 無限再帰（RecursionError）の代わりに診断可能な例外を送出する。
        max_depth = sum(len(state.team) for state in self.battle.player_states.values())
        if _depth > max_depth:
            raise InvalidCommandError(
                "瀕死交代が進行していません。方策関数が有効な交代コマンドを"
                "返しているか確認してください。"
            )

        # 交代
        if faint_players:
            self.run_interrupt_switch(Interrupt.FAINTED, False)
        if emergency_players:
            self.run_interrupt_switch(Interrupt.EMERGENCY)

        # 上記の交代（入場時ダメージ等）でさらに瀕死交代・緊急交代が発生していない
        # かを含め、すべての死に出し・緊急交代が完了するまで再帰的に実行
        self.run_faint_switch(_depth + 1)

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

        self.battle.add_event_log(mon, LogCode.SWITCHED_IN)

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

        # ハンドラの解除は、実際に登録されていた特性（トレース等でコピーした
        # ものを含む）に対して行う必要があるため、mon.reset_on_switch_out() で
        # mon.ability が素の特性に差し替えられる前に実行する。順序を逆にすると
        # 差し替え後の（本来登録されていない）特性のハンドラを解除しようとして
        # しまい、実際に登録されていたハンドラが解除されずに残り続けてしまう
        # （例: トレースでコピーした特性を持ったまま退場した場合）。
        self._unregister_handlers_on_switch_out(mon)
        mon.reset_on_switch_out()

        self.battle.add_event_log(mon, LogCode.SWITCHED_OUT)

    def override_ejectpack_interrupt(self, flag: Interrupt):
        """割り込みフラグを上書き。

        EJECTPACK_REQUESTED状態のプレイヤーに対して、指定したフラグを設定する。
        素早さ順に処理され、最初に見つかったプレイヤー（すばやさが一番高いポケモン）
        のフラグのみが更新される。複数のポケモンが同時にだっしゅつパックの発動条件を
        満たしていた場合、それ以外のプレイヤーの発動条件は破棄する
        （すばやさが一番高いポケモンのだっしゅつパックのみが発動する仕様のため）。

        Args:
            flag: 設定する割り込みフラグ
        """
        winner_decided = False
        for mon in self.battle.resolve_speed_order():
            player = self.battle.get_player(mon)
            state = self.battle.player_states[player]
            if state.interrupt != Interrupt.EJECTPACK_REQUESTED:
                continue
            if not winner_decided:
                state.interrupt = flag
                winner_decided = True
            else:
                state.interrupt = Interrupt.NONE

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
