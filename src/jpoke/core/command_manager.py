"""コマンド関連ロジックを扱うマネージャー。"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .player import Player

from jpoke.utils import fast_copy
from jpoke.enums import Event, Command
from jpoke.model import Move

from .context import BattleContext


class CommandManager:
    """行動コマンドの候補生成とコマンド解決を管理する。"""

    def __init__(self, battle: Battle):
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
        self.battle = battle

    def get_available_selection_commands(self, player: Player) -> list[Command]:
        """ポケモン選出時に使用可能なコマンドを取得する。"""
        state = self.battle.player_states[player]
        return Command.selection_commands()[:len(state.team)]

    def get_available_switch_commands(self, player: Player) -> list[Command]:
        """交代可能なコマンドのリストを取得する。"""
        if not self.battle.can_switch(player):
            return []
        state = self.battle.player_states[player]
        return [Command.get_switch_command(state.team.index(mon)) for mon in state.bench]

    def get_available_action_commands(self, player: Player) -> list[Command]:
        """行動時に使用可能なコマンドを取得する。"""
        state = self.battle.player_states[player]
        active = state.active
        move_indexes = [i for i, move in enumerate(active.moves) if move.pp > 0]

        # 通常技
        commands = [Command.get_move_command(i) for i in move_indexes]

        # メガシンカ
        if state.can_use_megaevol() and active.can_megaevolve():
            commands += [Command.get_megaevol_command(i) for i in move_indexes]

        # テラスタル
        if state.can_use_terastal() and active.can_terastallize():
            commands += [Command.get_terastal_command(i) for i in move_indexes]

        # 交代コマンドを追加
        commands += self.get_available_switch_commands(player)

        # コマンド修正
        ctx = BattleContext(source=active)
        commands = self.battle.events.emit(Event.ON_MODIFY_COMMAND_OPTIONS, ctx, commands)

        # 強制行動コマンドがある場合はそれを優先
        if commands == [Command.FORCED]:
            return commands

        # 技コマンドがない場合はわるあがきを追加
        if not any(cmd.is_move_family for cmd in commands):
            commands += [Command.STRUGGLE]

        return commands

    def command_to_move(self, player: Player, command: Command) -> Move:
        """コマンドから技オブジェクトを取得する。"""
        attacker = self.battle.get_active(player)
        if command == Command.STRUGGLE:
            return Move("わるあがき")
        if command == Command.FORCED:
            move_name = self.battle.query_manager.get_forced_move_name(attacker)
            if move_name:
                return Move(move_name)
            return Move("わるあがき")
        if command.is_zmove:
            return Move("わるあがき")
        return attacker.moves[command.index]
