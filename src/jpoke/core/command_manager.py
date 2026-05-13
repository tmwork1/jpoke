"""コマンド関連ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .player import Player

from jpoke.enums import Event, Command
from jpoke.model import Move

from .context import BattleContext


class CommandManager:
    """行動コマンドの候補生成とコマンド解決を管理する。"""

    def __init__(self, battle: Battle):
        self.battle = battle

    def update_reference(self, battle: Battle):
        self.battle = battle

    def get_available_selection_commands(self, player: Player) -> list[Command]:
        """ポケモン選出時に使用可能なコマンドを取得する。"""
        return Command.selection_commands()[:len(player.team)]

    def get_available_switch_commands(self, player: Player) -> list[Command]:
        """交代可能なコマンドのリストを取得する。"""
        if self.battle.query_manager.is_trapped(player.active_mon):
            return []
        return [cmd for mon, cmd in zip(player.team, Command.switch_commands())
                if mon in player.selection and mon is not player.active_mon]

    def get_available_action_commands(self, player: Player) -> list[Command]:
        """行動時に使用可能なコマンドを取得する。"""
        n = len(player.active_mon.moves)

        # 通常技
        commands = Command.regular_move_commands()[:n]

        # テラスタル
        if player.can_use_terastal():
            commands += Command.terastal_commands()[:n]

        # コマンド修正
        commands = self.battle.events.emit(
            Event.ON_MODIFY_COMMAND_OPTIONS,
            BattleContext(source=player.active_mon),
            commands
        )

        if Command.FORCED in commands:
            return [Command.FORCED]

        # 技がない場合はわるあがきを追加
        if not commands:
            commands = [Command.STRUGGLE]

        # 交代コマンドを追加
        commands += self.get_available_switch_commands(player)

        return commands

    def command_to_move(self, player: Player, command: Command) -> Move:
        """コマンドから技オブジェクトを取得する。"""
        attacker = player.active_mon
        if command == Command.STRUGGLE:
            return Move("わるあがき")
        if command == Command.FORCED:
            move_name = self.battle.query_manager.get_forced_move_name(attacker)
            if move_name:
                return Move(move_name)
            return Move("わるあがき")
        if command.is_z_move():
            return Move("わるあがき")
        return attacker.moves[command.idx]
