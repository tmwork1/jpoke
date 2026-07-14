"""完全ランダムな対戦をシード付きでバッチ実行し、各バトルの全ターン分イベントログを
レポートファイルに書き出すスクリプト。

`fuzz_battle.py` が「未捕捉例外」を検出するのに対し、こちらは対戦の成否を問わず
（正常終了・道中クラッシュの両方で）ログをそのまま書き出す。書き出したログを
`.claude/loop/fuzz_log.md` フローが sub agent（Explore）に読ませ、HP・ランク変化等の
数値がログの記述と食い違っていないかという「整合性」の観点でレビューさせる。

チーム生成・行動選択（RandomPlayer）は fuzz_battle.py と同じ
（`fuzz_common.py` に共通化されたロジックを再利用する）。ただし本スクリプトのみ
`--effect-bias` で `random_team_spec()` の `effect_bias` を非ゼロにでき、状態異常・
揮発性状態・場の状態を誘発する特性・持ち物・技（`scripts/fuzz/effect_bias.py` が
実装を静的解析して機械的に判定する）が選ばれる確率を高められる（既定は0.0＝無効。
fuzz_battle.py・replay_fuzz_battle.py の再現性には影響しない）。

使い方:
    python scripts/fuzz/fuzz_log_battle.py --start-seed 0 --count 10
    python scripts/fuzz/fuzz_log_battle.py --start-seed 0 --count 10 --max-turns 30 --n-pokemon 3
    python scripts/fuzz/fuzz_log_battle.py --start-seed 0 --count 10 --effect-bias 0.5
"""

from __future__ import annotations

import argparse
import os
import traceback
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from random import Random

from jpoke import Battle

from fuzz_battle import RandomPlayer
from fuzz_common import build_team, format_full_log, format_team, random_team_spec

_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_MAX_TURNS = 30
DEFAULT_N_POKEMON = 3
REPORT_DIR_NAME = "fuzz_log_reports"


def run_one(seed: int, max_turns: int, n_pokemon: int, effect_bias: float = 0.0) -> tuple[Path, bool]:
    """指定シードで1バトルを実行し、成否によらずログレポートを書き出す。

    戻り値はレポートパスと crashed フラグ（未捕捉例外で終了したか）。
    effect_bias > 0 の場合、状態異常・揮発性状態・場の状態を誘発する特性・持ち物・技が
    選ばれる確率を高める（`fuzz_common.random_team_spec()` を参照）。
    """
    master = Random(seed)
    team_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    decision_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    n_selected = master.randint(1, n_pokemon)

    team_specs = [random_team_spec(r, n_pokemon, effect_bias=effect_bias) for r in team_rngs]
    players = [RandomPlayer(f"Player{i + 1}", decision_rngs[i]) for i in range(2)]
    for player, spec in zip(players, team_specs):
        player.team = build_team(spec)

    battle = Battle(*players, n_selected=n_selected, seed=seed)

    crashed = False
    error_text = ""
    try:
        battle.start()
        while battle.judge_winner() is None and battle.turn < max_turns:
            battle.step()
        winner = battle.judge_winner()
        winner_name = winner.username if winner else None
    except Exception as e:
        crashed = True
        error_text = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        winner_name = None

    report_dir = _ROOT / ".loop" / REPORT_DIR_NAME
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"seed_{seed}.log"

    repro_cmd = (
        f"python scripts/fuzz/fuzz_log_battle.py --start-seed {seed} --count 1 "
        f"--max-turns {max_turns} --n-pokemon {n_pokemon}"
    )
    if effect_bias > 0:
        repro_cmd += f" --effect-bias {effect_bias}"

    parts = [
        f"再現コマンド: {repro_cmd}",
        f"crashed: {crashed}",
        f"n_selected（seedから自動決定）: {n_selected}",
        f"turn: {battle.turn}",
        f"winner: {winner_name}",
        "",
        "== Player1 team ==",
        format_team(team_specs[0]),
        "",
        "== Player2 team ==",
        format_team(team_specs[1]),
        "",
        "== error ==" if crashed else "",
        error_text,
        "",
        "== battle log ==",
        format_full_log(battle),
    ]
    path.write_text("\n".join(parts), encoding="utf-8")
    return path, crashed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-seed", type=int, default=0, help="開始シード")
    parser.add_argument("--count", type=int, default=10, help="実行するバトル数")
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS, help="1バトルの最大ターン数")
    parser.add_argument("--n-pokemon", type=int, default=DEFAULT_N_POKEMON, help="1チームの匹数")
    parser.add_argument("--workers", type=int, default=None,
                        help="並列worker数（既定: CPU数とcountの小さい方）")
    parser.add_argument("--effect-bias", type=float, default=0.0,
                        help="状態異常・揮発性状態・場の状態を誘発する特性・持ち物・技が"
                             "選ばれる確率を高める（0.0〜1.0、既定: 0.0=無効）")
    args = parser.parse_args()

    seeds = range(args.start_seed, args.start_seed + args.count)
    workers = args.workers if args.workers is not None else min(args.count, os.cpu_count() or 4)
    worker = partial(run_one, max_turns=args.max_turns, n_pokemon=args.n_pokemon,
                      effect_bias=args.effect_bias)
    with Pool(workers) as pool:
        results = pool.map(worker, seeds)
    for seed, (path, crashed) in zip(seeds, results):
        print(f"report: {path} crashed={crashed}")


if __name__ == "__main__":
    main()
