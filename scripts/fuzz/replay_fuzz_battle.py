"""完全ランダムな対戦を実行し、Battle.build_replay_data() → replay_battle() による
リプレイ再現が元の対戦と完全に一致するかを検証するバグ出し用スクリプト。

チーム生成・行動選択（RandomPlayer）は scripts/fuzz/fuzz_battle.py と同じ
（`fuzz_common.py` に共通化されたロジックを再利用する）。fuzz_battle.py が
「未捕捉例外」を検出するのに対し、こちらは「対戦は正常終了するがリプレイが
元と食い違う」バグ（tests/test_replay_fuzz.py のプロパティテストが検証する内容）
をシード探索で継続的に検出する。

食い違いは以下の優先順で判定する（tests/test_replay_fuzz.py と同じ順序）:
    1. ターン数
    2. 勝者
    3. 全ポケモンのHP
    4. event_logger.logs の完全一致

使い方:
    # 単発再現モード
    python scripts/fuzz/replay_fuzz_battle.py --seed 12345

    # バッチ探索モード（count 件を worker プロセスに分散して並列実行）
    python scripts/fuzz/replay_fuzz_battle.py --search --start-seed 0 --count 200
"""

from __future__ import annotations

import argparse
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from random import Random

from jpoke import Battle
from jpoke.core.replay import replay_battle

from fuzz_battle import RandomPlayer
from fuzz_common import (
    build_team,
    failure_signature,
    format_full_log,
    format_team,
    parallel_search,
    random_team_spec,
)

_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_MAX_TURNS = 30
DEFAULT_N_POKEMON = 3
FAILURE_DIR_NAME = "replay_fuzz_failures"


@dataclass
class ReplayFuzzResult:
    seed: int
    ok: bool
    turn: int = 0
    n_selected: int = 3
    max_turns: int = DEFAULT_MAX_TURNS
    n_pokemon: int = DEFAULT_N_POKEMON
    teams: list[list[dict]] = field(default_factory=list)
    mismatch_kind: str | None = None  # original_exception | replay_exception | turn | winner | hp | logs
    detail: str = ""
    signature: str | None = None
    traceback_text: str | None = None
    original_log_text: str | None = None
    replayed_log_text: str | None = None


def run_replay_fuzz_battle(seed: int,
                            max_turns: int = DEFAULT_MAX_TURNS,
                            n_pokemon: int = DEFAULT_N_POKEMON) -> ReplayFuzzResult:
    """指定シードで1バトルを実行し、リプレイ再現が完全一致するか検証する。

    チーム構成・選出数・行動選択は tests/test_replay_fuzz.py と同じ手順で
    シードのみから決定する（fuzz_battle.py の random プレイヤーモードと同一）。
    """
    master = Random(seed)
    team_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    decision_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    n_selected = master.randint(1, n_pokemon)

    team_specs = [random_team_spec(r, n_pokemon) for r in team_rngs]
    players = [RandomPlayer(f"Player{i + 1}", decision_rngs[i]) for i in range(2)]
    for player, spec in zip(players, team_specs):
        player.team = build_team(spec)

    battle = Battle(*players, n_selected=n_selected, seed=seed)

    base_kwargs = dict(
        n_selected=n_selected, max_turns=max_turns, n_pokemon=n_pokemon, teams=team_specs,
    )

    try:
        battle.start()
        while battle.judge_winner() is None and battle.turn < max_turns:
            battle.step()
    except Exception as e:
        return ReplayFuzzResult(
            seed=seed, ok=False, turn=battle.turn, **base_kwargs,
            mismatch_kind="original_exception",
            detail=f"{type(e).__name__}: {e}",
            signature=f"ORIGINAL_EXC:{failure_signature(e)}",
            traceback_text=traceback.format_exc(),
        )

    try:
        data = battle.build_replay_data()
        replayed = replay_battle(data, max_turns=max_turns)
    except Exception as e:
        return ReplayFuzzResult(
            seed=seed, ok=False, turn=battle.turn, **base_kwargs,
            mismatch_kind="replay_exception",
            detail=f"{type(e).__name__}: {e}",
            signature=f"REPLAY_EXC:{failure_signature(e)}",
            traceback_text=traceback.format_exc(),
            original_log_text=format_full_log(battle),
        )

    if replayed.turn != battle.turn:
        return ReplayFuzzResult(
            seed=seed, ok=False, turn=battle.turn, **base_kwargs,
            mismatch_kind="turn",
            detail=f"original={battle.turn} replayed={replayed.turn}",
            signature="REPLAY_MISMATCH:turn",
            original_log_text=format_full_log(battle),
            replayed_log_text=format_full_log(replayed),
        )

    winner = battle.judge_winner()
    replayed_winner = replayed.judge_winner()
    winner_mismatch = (winner is None) != (replayed_winner is None) or (
        winner is not None and
        battle.players.index(winner) != replayed.players.index(replayed_winner)
    )
    if winner_mismatch:
        return ReplayFuzzResult(
            seed=seed, ok=False, turn=battle.turn, **base_kwargs,
            mismatch_kind="winner",
            detail=(
                f"original={winner.username if winner else None} "
                f"replayed={replayed_winner.username if replayed_winner else None}"
            ),
            signature="REPLAY_MISMATCH:winner",
            original_log_text=format_full_log(battle),
            replayed_log_text=format_full_log(replayed),
        )

    for p_idx, (old_state, new_state) in enumerate(
        zip(battle.player_states.values(), replayed.player_states.values())
    ):
        for m_idx, (old_mon, new_mon) in enumerate(zip(old_state.team, new_state.team)):
            if old_mon.hp != new_mon.hp:
                return ReplayFuzzResult(
                    seed=seed, ok=False, turn=battle.turn, **base_kwargs,
                    mismatch_kind="hp",
                    detail=(
                        f"player{p_idx} team[{m_idx}] {old_mon.name}: "
                        f"original_hp={old_mon.hp} replayed_hp={new_mon.hp}"
                    ),
                    signature="REPLAY_MISMATCH:hp",
                    original_log_text=format_full_log(battle),
                    replayed_log_text=format_full_log(replayed),
                )

    old_logs = battle.event_logger.logs
    new_logs = replayed.event_logger.logs
    if old_logs != new_logs:
        i = next(
            (i for i in range(min(len(old_logs), len(new_logs))) if old_logs[i] != new_logs[i]),
            min(len(old_logs), len(new_logs)),
        )
        diff_code = old_logs[i].log.name if i < len(old_logs) else "(不足)"
        return ReplayFuzzResult(
            seed=seed, ok=False, turn=battle.turn, **base_kwargs,
            mismatch_kind="logs",
            detail=(
                f"最初に食い違うログ index={i}: {diff_code} "
                f"(original件数={len(old_logs)} replayed件数={len(new_logs)})"
            ),
            signature=f"REPLAY_MISMATCH:logs:{diff_code}",
            original_log_text=format_full_log(battle),
            replayed_log_text=format_full_log(replayed),
        )

    return ReplayFuzzResult(seed=seed, ok=True, turn=battle.turn, **base_kwargs)


def _repro_cmd(result: ReplayFuzzResult) -> str:
    return (
        f"python scripts/fuzz/replay_fuzz_battle.py --seed {result.seed} "
        f"--max-turns {result.max_turns} --n-pokemon {result.n_pokemon}"
    )


def write_failure_report(result: ReplayFuzzResult, failure_dir: Path, repro_cmd: str) -> Path:
    """食い違い結果を再現可能な形でレポートファイルに書き出す（.log は git 管理外）。"""
    failure_dir.mkdir(parents=True, exist_ok=True)
    path = failure_dir / f"seed_{result.seed}.log"

    parts = [
        f"再現コマンド: {repro_cmd}",
        f"signature: {result.signature}",
        f"mismatch_kind: {result.mismatch_kind}",
        f"detail: {result.detail}",
        f"n_selected（seedから自動決定）: {result.n_selected}",
        f"failed at turn: {result.turn}",
        "",
        "== Player1 team ==",
        format_team(result.teams[0]),
        "",
        "== Player2 team ==",
        format_team(result.teams[1]),
        "",
        "== traceback ==",
        result.traceback_text or "(例外なし)",
        "",
        "== original battle log ==",
        result.original_log_text or "",
        "",
        "== replayed battle log ==",
        result.replayed_log_text or "",
    ]

    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, help="単発再現モードのシード")
    parser.add_argument("--search", action="store_true", help="バッチ探索モード")
    parser.add_argument("--start-seed", type=int, default=0, help="探索開始シード")
    parser.add_argument("--count", type=int, default=100, help="探索するバトル数")
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS, help="1バトルの最大ターン数")
    parser.add_argument("--n-pokemon", type=int, default=DEFAULT_N_POKEMON, help="1チームの匹数")
    parser.add_argument("--workers", type=int, default=None,
                        help="バッチ探索モードでの並列worker数（既定: CPU数とcountの小さい方）")
    args = parser.parse_args()

    failure_dir = _ROOT / ".loop" / FAILURE_DIR_NAME
    kwargs = dict(max_turns=args.max_turns, n_pokemon=args.n_pokemon)

    if args.search:
        failures = parallel_search(run_replay_fuzz_battle, args.start_seed, args.count,
                                    workers=args.workers, **kwargs)
        if not failures:
            print(f"OK: {args.count}件すべて一致（seed {args.start_seed}〜{args.start_seed + args.count - 1}）")
            sys.exit(0)
        for result in sorted(failures, key=lambda r: r.seed):
            path = write_failure_report(result, failure_dir, _repro_cmd(result))
            print(f"FAIL: seed={result.seed} signature={result.signature}")
            print(f"report: {path}")
        sys.exit(1)

    if args.seed is None:
        parser.error("--seed か --search のいずれかを指定してください。")

    result = run_replay_fuzz_battle(args.seed, **kwargs)
    if result.ok:
        print(f"OK: seed={result.seed} turn={result.turn}")
        sys.exit(0)

    path = write_failure_report(result, failure_dir, _repro_cmd(result))
    print(f"FAIL: seed={result.seed} signature={result.signature}")
    print(result.detail)
    print(f"report: {path}")
    sys.exit(1)


if __name__ == "__main__":
    main()
