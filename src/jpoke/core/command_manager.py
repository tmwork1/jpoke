"""コマンド関連ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .player import Player
    from .player_state import PlayerState

from jpoke.utils import fast_copy
from jpoke.utils.type_defs import BattlePhase
from jpoke.enums import Event, Command, Interrupt
from jpoke.model import Move

from .context import EventContext


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

    def get_available_switch_commands(self, player: Player) -> list[Command]:
        """交代可能なコマンドのリストを取得する。

        Note:
            バトンタッチによる PIVOT 交代中はとらわれ状態チェックをスキップし、
            控えに生きているポケモンがいれば交代可能とする。
        """
        state = self.battle.player_states[player]
        # PIVOT（バトンタッチ等）中はとらわれ状態に関わらず交代可能
        if state.interrupt != Interrupt.PIVOT:
            if not self.battle.can_switch(player):
                return []
        bench_alive = any(
            mon is not state.active and mon.alive
            for mon in state.team
        )
        if not bench_alive:
            return []
        return [
            Command.get_switch_command(i)
            for i, mon in enumerate(state.team)
            if mon is not state.active and mon.alive
        ]

    def get_available_action_commands(self, player: Player) -> list[Command]:
        """行動時に使用可能なコマンドを取得する。"""
        state = self.battle.player_states[player]
        active = state.active
        move_indexes = [i for i, move in enumerate(active.moves) if move.pp > 0]

        # 通常技
        commands = [Command.get_move_command(i) for i in move_indexes]

        # メガシンカ
        if self._can_use_megaevol(state):
            commands += [Command.get_megaevol_command(i) for i in move_indexes]

        # テラスタル
        if self._can_use_terastal(state):
            commands += [Command.get_terastal_command(i) for i in move_indexes]

        # 交代コマンドを追加
        commands += self.get_available_switch_commands(player)

        # コマンド修正
        ctx = EventContext(source=active)
        commands = self.battle.events.emit(
            Event.ON_MODIFY_COMMAND_OPTIONS, ctx, commands
        )

        # 強制行動コマンドがある場合はそれを優先
        if Command.FORCED in commands:
            return [Command.FORCED]

        # 技コマンドがない場合はわるあがきを追加
        if not any(cmd.is_type("move") for cmd in commands):
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
        if command == Command.STRUGGLE:
            return Move("わるあがき")

        # 強制行動ではPPを消費させないように新しくMoveインスタンスを作成する
        if command == Command.FORCED:
            move_name = self.battle.query.get_forced_move_name(attacker)
            if move_name:
                return Move(move_name)
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
                state.last_available_commands = battle.get_available_commands(ply)
                # 木探索を行う際に補完すべきコマンドタイプを指定
                state.required_command_type = "any" if battle.phase == "action" else "switch"

            # コマンドを選択
            commands: dict[Player, Command] = {}
            for ply in players:
                sim = battle.build_observation(ply)
                commands[ply] = ply.choose_command(sim)
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
            all(not mon.megaevolved for mon in selection)
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
            all(not mon.terastallized for mon in selection)
            and state.active.can_terastallize()
        )
