"""
fuzz_battle.py の派生版。行動選択にランダムプレイヤーの代わりに
jpoke.players.TreeSearchPlayer（1手先の総当たりミニマックス）
を使い、より「実戦的」な行動選択のもとでのみ顕在化するバグ
（見え方が変わるだけの通常の合法手網羅では踏まないコマンドの組み合わせ等）を検出する。

木探索は1ターンあたり len(自分の合法手) * len(相手の合法手) 回だけ盤面を複製して
評価するため、fuzz_battle.py よりもバトル1本あたりのコストが大きい。
デフォルトの n_pokemon・max_turns を fuzz_battle.py より小さくしているのはそのため。

チーム構成の生成（種族・性別・性格・レベル・テラスタイプ・個体値・努力値・
特性・持ち物・技）とレポート出力の形式は fuzz_battle.py と共通
（scripts/fuzz_common.py）。乱数シード（int）1つだけで、チーム構成・選出数・
行動選択（木探索中の割り込み交代時のフォールバックを含む）まで完全に再現できる。

使い方:
    # 単発再現モード
    python scripts/tsfuzz_battle.py --seed 12345

    # バッチ探索モード（失敗が出るまでシードを進める）
    python scripts/tsfuzz_battle.py --search --start-seed 0 --count 50
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from random import Random

from jpoke import Battle
from jpoke.enums import Command
from jpoke.players import TreeSearchPlayer

from fuzz_common import (
    FuzzResult,
    build_team,
    failure_signature,
    format_full_log,
    random_team_spec,
    search,
    write_failure_report,
)

FAILURE_DIR = Path(__file__).resolve().parent.parent / ".loop" / "tsfuzz_failures"

# 木探索1回あたりのコストが大きいため、fuzz_battle.py より小さいデフォルト値にする
DEFAULT_MAX_TURNS = 20
DEFAULT_N_POKEMON = 3


class TreeSearchFuzzPlayer(TreeSearchPlayer):
    """fuzzテスト用の TreeSearchPlayer。

    選出と、探索中の割り込み交代（フォールバック）に、master シードから
    独立に派生させた専用の Random インスタンスを使うことで、選出・木探索の
    フォールバック・チーム構成それぞれの乱数系列を分離し、シードだけで
    完全に再現できるようにする。
    """

    def __init__(self, name: str, rng: Random, max_plies: int = 1):
        super().__init__(name=name, max_plies=max_plies)
        self.rng = rng

    def fallback(self, battle: Battle) -> Command:
        return self.rng.choice(battle.get_available_commands(self))

    def choose_selection(self, battle: Battle) -> list[int]:
        n = min(battle.n_selected, len(self.team))
        return self.rng.sample(range(len(self.team)), n)


def run_fuzz_battle(seed: int,
                     max_turns: int = DEFAULT_MAX_TURNS,
                     n_pokemon: int = DEFAULT_N_POKEMON,
                     max_plies: int = 1) -> FuzzResult:
    """指定シードで1バトルを実行する。未捕捉例外を検知して結果にまとめる。

    選出数（n_selected、1〜n_pokemon）・各匹の技数（1〜MAX_MOVES）を含め、
    チーム構成は全てシードから決まる（CLI 引数では指定しない＝seedだけで完全に再現できる）。
    """
    master = Random(seed)
    team_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    decision_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    n_selected = master.randint(1, n_pokemon)

    team_specs = [random_team_spec(r, n_pokemon) for r in team_rngs]

    players = [
        TreeSearchFuzzPlayer(f"Player{i + 1}", decision_rngs[i], max_plies=max_plies)
        for i in range(2)
    ]
    for player, spec in zip(players, team_specs):
        player.team = build_team(spec)

    battle = Battle(tuple(players), n_selected=n_selected, seed=seed)

    try:
        battle.start()
        while battle.judge_winner() is None and battle.turn < max_turns:
            battle.step()
    except Exception as e:
        return FuzzResult(
            seed=seed, ok=False, turn=battle.turn,
            n_selected=n_selected, max_turns=max_turns,
            n_pokemon=n_pokemon,
            teams=team_specs,
            error=f"{type(e).__name__}: {e}",
            signature=failure_signature(e),
            traceback_text=traceback.format_exc(),
            log_text=format_full_log(battle),
        )

    winner = battle.judge_winner()
    return FuzzResult(
        seed=seed, ok=True, turn=battle.turn,
        winner=winner.name if winner else None,
        n_selected=n_selected, max_turns=max_turns,
        n_pokemon=n_pokemon,
        teams=team_specs,
    )


def _repro_cmd(result: FuzzResult, max_plies: int) -> str:
    return (
        f"python scripts/tsfuzz_battle.py --seed {result.seed} "
        f"--max-turns {result.max_turns} --n-pokemon {result.n_pokemon} "
        f"--max-plies {max_plies}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, help="単発再現モードのシード")
    parser.add_argument("--search", action="store_true", help="バッチ探索モード")
    parser.add_argument("--start-seed", type=int, default=0, help="探索開始シード")
    parser.add_argument("--count", type=int, default=50, help="探索するバトル数")
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--n-pokemon", type=int, default=DEFAULT_N_POKEMON)
    parser.add_argument("--max-plies", type=int, default=1, help="木探索の先読み手数")
    args = parser.parse_args()

    kwargs = dict(
        max_turns=args.max_turns,
        n_pokemon=args.n_pokemon,
        max_plies=args.max_plies,
    )

    if args.search:
        result = search(run_fuzz_battle, args.start_seed, args.count, **kwargs)
        if result is None:
            print(f"OK: {args.count}件すべて成功（seed {args.start_seed}〜{args.start_seed + args.count - 1}）")
            sys.exit(0)
        path = write_failure_report(result, FAILURE_DIR, _repro_cmd(result, args.max_plies))
        print(f"FAIL: seed={result.seed} signature={result.signature}")
        print(f"report: {path}")
        sys.exit(1)

    if args.seed is None:
        parser.error("--seed か --search のいずれかを指定してください。")

    result = run_fuzz_battle(args.seed, **kwargs)
    if result.ok:
        print(f"OK: seed={result.seed} turn={result.turn} winner={result.winner}")
        sys.exit(0)

    path = write_failure_report(result, FAILURE_DIR, _repro_cmd(result, args.max_plies))
    print(f"FAIL: seed={result.seed} signature={result.signature}")
    print(result.error)
    print(f"report: {path}")
    sys.exit(1)


if __name__ == "__main__":
    main()
