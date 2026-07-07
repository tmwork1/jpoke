"""対戦のリプレイ再生に必要なデータ構造を定義するモジュール。

対戦を完全に再現するために必要な「チーム＋シード＋選出＋コマンド列」を
記録・シリアライズする。記録フックは `Battle` / `CommandManager` 側にあり、
このモジュールはデータ構造のみを扱う。
"""
from __future__ import annotations
from dataclasses import dataclass, field

from jpoke.types import BattlePhase
from jpoke.enums import Command


@dataclass(frozen=True)
class RecordedCommand:
    """記録された1件のコマンド（行動 / 交代）。"""
    turn: int
    player_idx: int
    phase: BattlePhase  # "action" | "switch"
    command: Command

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "player_idx": self.player_idx,
            "phase": self.phase,
            "command": self.command.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecordedCommand":
        return cls(
            turn=data["turn"],
            player_idx=data["player_idx"],
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
