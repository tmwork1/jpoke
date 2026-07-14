"""fuzz_battle.py のランダムチーム生成を使った、リプレイ再現のプロパティテスト。

完全ランダムなチーム構成・行動選択（RandomPlayer）で対戦を最後まで実行し、
build_replay_data() → replay_battle() で再現した対戦が元の対戦と完全に一致する
（勝者・全ポケモンのHP・event_logger.logs）ことを、複数シードにわたって確認する。
"""
from __future__ import annotations

import sys
from pathlib import Path
from random import Random

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "fuzz"))
from fuzz_common import build_team, random_team_spec  # noqa: E402

from jpoke import Battle, Player
from jpoke.core.replay import replay_battle
from jpoke.enums import Command

N_POKEMON = 3
MAX_TURNS = 30
FUZZ_SEEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

class _RandomPlayer(Player):
    """自前の乱数生成器で選出・行動をランダムに選ぶプレイヤー（scripts/fuzz/fuzz_battle.py 参照）。"""

    def __init__(self, username: str, rng: Random):
        super().__init__(username)
        self.rng = rng

    def choose_selection(self, battle: Battle) -> list[int]:
        n = min(battle.n_selected, len(self.team))
        return self.rng.sample(range(len(self.team)), n)

    def choose_command(self, battle: Battle) -> Command:
        commands = battle.get_available_commands(self)
        return self.rng.choice(commands)

def _run_random_battle(seed: int) -> Battle:
    """fuzz_battle.py の run_fuzz_battle と同じ手順でランダム対戦を1本実行する。"""
    master = Random(seed)
    team_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    decision_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    n_selected = master.randint(1, N_POKEMON)

    players = tuple(_RandomPlayer(f"Player{i + 1}", decision_rngs[i]) for i in range(2))
    for player, rng in zip(players, team_rngs):
        player.team = build_team(random_team_spec(rng, N_POKEMON))

    battle = Battle(*players, n_selected=n_selected, seed=seed)
    battle.start()
    while battle.judge_winner() is None and battle.turn < MAX_TURNS:
        battle.step()
    return battle


@pytest.mark.parametrize("seed", FUZZ_SEEDS)
def test_ランダム生成した対戦のリプレイが元の対戦と完全に一致する(seed):
    battle = _run_random_battle(seed)

    data = battle.build_replay_data()
    replayed = replay_battle(data, max_turns=MAX_TURNS)

    assert replayed.turn == battle.turn

    winner = battle.judge_winner()
    replayed_winner = replayed.judge_winner()
    assert (winner is None) == (replayed_winner is None)
    if winner is not None:
        assert replayed.players.index(replayed_winner) == battle.players.index(winner)

    for old_state, new_state in zip(battle.player_states.values(), replayed.player_states.values()):
        for old_mon, new_mon in zip(old_state.team, new_state.team):
            assert new_mon.hp == old_mon.hp

    assert replayed.event_logger.logs == battle.event_logger.logs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
