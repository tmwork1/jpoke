"""対戦のリプレイ再生に必要なデータ構造・再生ロジックを提供するモジュール。

対戦を完全に再現するために必要な「チーム＋シード＋選出＋コマンド列」を
記録・シリアライズするデータ構造（`RecordedCommand`, `BattleReplayData`）と、
それを使って記録済みの選出・コマンド列をそのまま払い出す `ReplayPlayer`、
対戦を最後まで進める `replay_battle()` をまとめて扱う。
記録フックは `Battle` / `CommandManager` 側にある。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle

from collections import deque
from dataclasses import dataclass, field

from jpoke.types import BattlePhase
from jpoke.enums import Command
from jpoke.model.pokemon import Pokemon

from .player import Player


@dataclass(frozen=True)
class RecordedCommand:
    """記録された1件のコマンド（行動 / 交代）。"""
    turn: int
    player_index: int
    phase: BattlePhase  # "action" | "switch"
    command: Command

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "player_index": self.player_index,
            "phase": self.phase,
            "command": self.command.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecordedCommand":
        return cls(
            turn=data["turn"],
            player_index=data["player_index"],
            phase=data["phase"],
            command=Command[data["command"]],
        )


@dataclass
class BattleReplayData:
    """対戦を完全に再現するために必要な情報一式。"""
    seed: int
    n_selected: int
    battle_option: dict          # BattleOption の各フィールド
    teams: tuple[list[dict], list[dict]]       # Pokemon.to_dict() の対戦開始前スナップショット
    selections: tuple[list[int], list[int]]
    commands: list[RecordedCommand] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "n_selected": self.n_selected,
            "battle_option": self.battle_option,
            "teams": list(self.teams),
            "selections": list(self.selections),
            "commands": [c.to_dict() for c in self.commands],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BattleReplayData":
        return cls(
            seed=data["seed"],
            n_selected=data["n_selected"],
            battle_option=data["battle_option"],
            teams=tuple(data["teams"]),
            selections=tuple(data["selections"]),
            commands=[RecordedCommand.from_dict(c) for c in data["commands"]],
        )


class ReplayPlayer(Player):
    """記録済みの選出・コマンド列をそのまま再生するプレイヤー。

    方策判断を一切行わず、記録された決定を発生順に払い出すだけなので、
    盤面が記録時と完全に一致する限り常に正しい決定を返す。
    """

    def __init__(self, username: str, team_spec: list[dict],
                 selection: list[int], commands: list[Command]):
        super().__init__(username=username)
        self.team = [Pokemon.from_dict(spec) for spec in team_spec]
        self._selection = selection
        self._queue: deque[Command] = deque(commands)

    def choose_selection(self, battle: Battle) -> list[int]:
        return self._selection

    def choose_command(self, battle: Battle) -> Command:
        if not self._queue:
            raise RuntimeError("リプレイデータのコマンドが不足しています。記録漏れの可能性があります。")
        return self._queue.popleft()


def replay_battle(data: BattleReplayData, max_turns: int = 300) -> Battle:
    """記録済みデータから対戦を再現する。

    Returns:
        再生し終えた Battle インスタンス（event_logger 等で経過を確認できる）。
    """
    from .battle import Battle  # battle.py -> replay.py の循環importを避けるための遅延import

    commands_by_player: tuple[list[Command], list[Command]] = ([], [])
    for rec in data.commands:
        commands_by_player[rec.player_index].append(rec.command)

    players = (
        ReplayPlayer("Player 1", data.teams[0], data.selections[0], commands_by_player[0]),
        ReplayPlayer("Player 2", data.teams[1], data.selections[1], commands_by_player[1]),
    )
    battle = Battle(*players, n_selected=data.n_selected, seed=data.seed, **data.battle_option)
    battle.start()

    while battle.judge_winner() is None and battle.turn < max_turns:
        battle.step()

    return battle
