"""コマンド関連ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from .battle import Battle
    from .player import Player
    from .player_state import PlayerState

from jpoke.utils import fast_copy
from jpoke.types import BattlePhase, MoveName
from jpoke.enums import Event, Command, Interrupt
from jpoke.model.move import Move

from .context import EventContext
from .replay import RecordedCommand


class CommandManager:
    """行動コマンドの候補生成とコマンド解決を管理する。"""

    def __init__(self, battle: Battle):
        self.battle = battle

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[])
        return new

    def update_reference(self, battle: Battle):
        self.battle = battle

    def available_switch_commands(self, player: Player, force: bool = False) -> list[Command]:
        """交代可能なコマンドのリストを取得する。

        Args:
            player: 対象プレイヤー
            force: True の場合、とらわれ状態チェックを無視する。
                ほえる・ふきとばし・ともえなげ・ドラゴンテール等、相手を強制的に
                交代させる技から呼び出す際に使う（にげられない・バインド・
                フェアリーロックや特性かげふみ・ありじごく・じりょくを無視して
                発動するため）。ねをはる状態のみ `Event.ON_TRY_BLOW` 経由で
                別途無効化されるため、ここでは考慮しない。

        Note:
            バトンタッチによる PIVOT 交代中や、だっしゅつパック・だっしゅつボタンに
            よる交代中はとらわれ状態チェックをスキップし、控えに生きているポケモンが
            いれば交代可能とする（にげられない・バインド・ねをはる・フェアリーロックや
            特性かげふみ・ありじごく・じりょくを無視して発動するため）。
            瀕死による交代（FAINTED）も同様にスキップする。瀕死になったポケモンは
            退場処理（バインドなどの揮発性状態解除）より前に交代コマンドを解決するため、
            とらわれ状態の判定に瀕死ポケモン自身のバインド等が残っていても交代を
            妨げてはならない。
            ききかいひ・にげごしによる緊急交代（EMERGENCY）も同様にスキップする。
            .internal/spec/abilities/にげごし.md「特性かげふみ/ありじごく/じりょくの影響や、
            にげられない/バインド/ねをはる/フェアリーロック状態の効果を無視して発動する」
            の通り、ダメージを受けた技自身がにげられない等を同時に付与した場合でも
            交代先を選べなければならない。
        """
        state = self.battle.player_states[player]
        # PIVOT（バトンタッチ等）・だっしゅつパック・だっしゅつボタン・瀕死交代・
        # ききかいひ/にげごしの緊急交代発動中や強制交代技（force=True）は
        # とらわれ状態に関わらず交代可能
        if (
            not force
            and state.interrupt != Interrupt.PIVOT
            and state.interrupt != Interrupt.EJECTBUTTON
            and state.interrupt != Interrupt.FAINTED
            and state.interrupt != Interrupt.EMERGENCY
            and not state.interrupt.name.startswith("EJECTPACK")
        ):
            if not self.battle.query.can_switch(player):
                return []
        bench = state.bench
        bench_alive = any(mon.alive for mon in bench)
        if not bench_alive:
            return []
        return [
            Command.get_switch_command(i)
            for i, mon in enumerate(state.team)
            if mon in bench and mon.alive
        ]

    def available_action_commands(self, player: Player) -> list[Command]:
        """行動時に使用可能なコマンドを取得する。"""
        state = self.battle.player_states[player]
        active = state.active
        move_indexes = [
            i for i, move in enumerate(active.moves)
            if move.pp > 0 and (
                move.name != "とっておき"
                or self.battle.query.can_use_last_resort(active)
            )
        ]

        # 通常技
        commands = [Command.get_move_command(i) for i in move_indexes]

        # メガシンカ
        if self._can_use_megaevol(state):
            commands += [Command.get_megaevol_command(i) for i in move_indexes]

        # テラスタル
        if self._can_use_terastal(state):
            commands += [Command.get_terastal_command(i) for i in move_indexes]

        # 交代コマンドを追加
        commands += self.available_switch_commands(player)

        # コマンド修正
        ctx = EventContext(source=active)
        commands = self.battle.events.emit(
            Event.ON_MODIFY_COMMAND_OPTIONS, ctx, commands
        )

        # 強制行動コマンドがある場合はそれを優先
        if Command.FORCED in commands:
            return [Command.FORCED]

        # 技コマンドがない場合はわるあがきを追加
        if not any(cmd.is_move for cmd in commands):
            commands += [Command.STRUGGLE]

        return commands

    def resolve_move_from_command(self, player: Player, command: Command) -> Move:
        """コマンドから技を解決する。わるあがきや強制行動コマンドもここで処理する。

        Args:
            player: コマンドを出したプレイヤー
            command: 解決するコマンド

        Returns:
            Move: コマンドに対応する技。わるあがきや強制行動も含む
        """
        attacker = self.battle.get_active(player)
        assert attacker is not None
        if command == Command.STRUGGLE:
            return Move("わるあがき")

        # 強制行動ではPPを消費させないように新しくMoveインスタンスを作成する
        if command == Command.FORCED:
            move_name = self.battle.query.get_forced_move_name(attacker)
            if move_name:
                return Move(cast(MoveName, move_name), is_forced_continuation=True)
            return Move("わるあがき")

        if command.is_gigamax:
            return Move("わるあがき")

        if command.is_zmove:
            return Move("わるあがき")

        return attacker.moves[command.index]

    def resolve_command(self, phase: BattlePhase, player: Player | None = None) -> dict[Player, Command]:
        """コマンドを解決する。

        Args:
            phase: コマンド選択を行うフェーズ
            player: 対象プレイヤー。Noneの場合は全プレイヤーを対象にする。

        Returns:
            各プレイヤーのコマンド辞書
        """
        battle = self.battle
        players = [player] if player else battle.players

        with battle.phase_context(phase):
            # 方策関数を呼び出す前準備
            for ply in players:
                state = battle.player_states[ply]
                # 利用できるコマンドを記録
                state.last_available_commands = battle.available_commands(ply)
                # 木探索を行う際に補完すべきコマンドタイプを指定
                state.required_command_type = "any" if battle.phase == "action" else "switch"

            # コマンドを選択
            commands: dict[Player, Command] = {}
            for ply in players:
                sim = battle.build_observation(ply)
                commands[ply] = ply.choose_command(sim)
                if phase == "switch":
                    # "action" は Battle.step() 側で既に記録済みのため、ここでは
                    # 瀕死交代・だっしゅつパック等の割り込み交代のみを記録する。
                    battle.command_log.append(RecordedCommand(
                        turn=battle.turn,
                        player_index=battle.players.index(ply),
                        phase="switch",
                        command=commands[ply],
                    ))
        return commands

    def validate_command(self, player: Player, command: Command | None) -> bool:
        """コマンドがコンテキストに合致しているか検証する。

        Args:
            player: コマンドを出したプレイヤー
            command: 実行するコマンド

        Returns:
            bool: コマンドの型が状態に適合する場合は True、そうでない場合は False
        """
        state = self.battle.player_states[player]
        required_type = state.required_command_type
        return (
            command is None
            or required_type in {None, "any"}
            or command.is_type(required_type)
        )

    def _can_use_megaevol(self, state: PlayerState) -> bool:
        """メガシンカが使用可能かどうかを判定する。

        選出したポケモンのうち、メガシンカ可能なポケモンがいる場合に使用可能。

        Returns:
            メガシンカが使用可能な場合True
        """
        selection = state.selection
        return (
            self.battle.option.mega_evolution
            and all(not mon.megaevolved for mon in selection)
            and state.active.can_megaevolve()
        )

    def _can_use_terastal(self, state: PlayerState) -> bool:
        """テラスタルが使用可能かどうかを判定する。

        選出したポケモン全てがテラスタルしていない場合に使用可能。

        Returns:
            テラスタルが使用可能な場合True
        """
        selection = state.selection
        return (
            self.battle.option.terastal
            and all(not mon.is_terastallized for mon in selection)
            and state.active.can_terastallize()
        )
