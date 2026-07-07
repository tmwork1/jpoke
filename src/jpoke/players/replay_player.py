"""記録済みリプレイデータから対戦を再現するプレイヤー・実行ドライバ。

`Battle.build_replay_data()` が組み立てた `BattleReplayData` を受け取り、
選出・コマンド列を発生順にそのまま払い出すだけの `ReplayPlayer` と、
それを使って対戦を最後まで進める `replay_battle()` を提供する。
"""
from __future__ import annotations

from collections import deque

from jpoke.core import Battle, Player
from jpoke.core.replay import BattleReplayData
from jpoke.enums import Command
from jpoke.model import Pokemon


class ReplayPlayer(Player):
    """記録済みの選出・コマンド列をそのまま再生するプレイヤー。

    方策判断を一切行わず、記録された決定を発生順に払い出すだけなので、
    盤面が記録時と完全に一致する限り常に正しい決定を返す。
    """

    def __init__(self, name: str, team_spec: list[dict],
                 selection: list[int], commands: list[Command]):
        super().__init__(name=name)
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
    commands_by_player: tuple[list[Command], list[Command]] = ([], [])
    for rec in data.commands:
        commands_by_player[rec.player_idx].append(rec.command)

    players = (
        ReplayPlayer("Player 1", data.teams[0], data.selections[0], commands_by_player[0]),
        ReplayPlayer("Player 2", data.teams[1], data.selections[1], commands_by_player[1]),
    )
    battle = Battle(players, n_selected=data.n_selected, seed=data.seed, **data.battle_option)
    battle.start()

    while battle.judge_winner() is None and battle.turn < max_turns:
        battle.step()

    return battle
