from dataclasses import dataclass

from jpoke.utils.enums import Command
from jpoke.utils import fast_copy


@dataclass
class BaseLog:
    turn: int
    player_idx: int

    def dump(self):
        return vars(self).copy()


@dataclass
class TurnLog(BaseLog):
    text: str


@dataclass
class CommandLog(BaseLog):
    command: Command


@dataclass
class DamageLog(BaseLog):
    text: str


class Logger:
    def __init__(self):
        self.turn_logs: list[TurnLog] = []
        self.command_logs: list[CommandLog] = []
        self.damage_logs: list[DamageLog] = []

    def clear(self):
        for x in [self.turn_logs, self.command_logs]:
            for logs in x:
                logs.clear()

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def get_turn_logs(self, turn: int, player_idx: int) -> list[str]:
        return [log.text for log in self.turn_logs if
                log.turn == turn and log.player_idx == player_idx]

    def get_command_logs(self, turn: int, player_idx: int) -> list[Command]:
        return [log.command for log in self.command_logs if
                log.turn == turn and log.player_idx == player_idx]

    def get_damage_logs(self, turn: int, player_idx: int) -> list[str]:
        return [log.text for log in self.damage_logs if
                log.turn == turn and log.player_idx == player_idx]

    def add_turn_log(self, turn: int, player_idx: int, text: str):
        self.turn_logs.append(TurnLog(turn, player_idx, text))

    def add_command_log(self, turn: int, player_idx: int, command: Command):
        self.command_logs.append(CommandLog(turn, player_idx, command))

    def add_damage_log(self, turn: int, player_idx: int, text: str):
        self.damage_logs.append(DamageLog(turn, player_idx, text))
