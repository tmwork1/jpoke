"""完全ランダムなポケモン・性別・性格・レベル・テラスタイプ・個体値・努力値・
特性・持ち物・技（1〜10個）で組んだパーティ同士を戦わせ、未捕捉例外を検出する
バグ出し用スクリプト。

行動選択の方策（プレイヤーモデル）を `--player` で切り替える:

- `random`（既定）: `RandomPlayer`。合法手から一様ランダムに選ぶ。1バトルが安価なので
  6匹・100ターンといった広い状態空間を広く浅く掘る。
- `tree_search`: `TreeSearchFuzzPlayer`（1手先の総当たりミニマックス）。より「実戦的」な
  行動選択のもとでのみ顕在化するバグを狙う。1ターンあたり
  `len(自分の合法手) * len(相手の合法手)` 回だけ盤面を複製して評価するため1バトルのコストが
  大きく、既定の n_pokemon・max_turns を小さめにする。

いずれのモードでも、乱数シード（int）1つだけでチーム構成・選出数・選出・行動選択
（木探索中の割り込み交代時のフォールバックを含む）まで完全に再現できる。
チーム生成・失敗レポートの形式は `scripts/fuzz/fuzz_common.py` に共通化している。

使い方:
    # 単発再現モード
    python scripts/fuzz/fuzz_battle.py --seed 12345
    python scripts/fuzz/fuzz_battle.py --seed 12345 --player tree_search --max-plies 1

    # バッチ探索モード（count 件を worker プロセスに分散して並列実行）
    python scripts/fuzz/fuzz_battle.py --search --start-seed 0 --count 200
    python scripts/fuzz/fuzz_battle.py --search --player tree_search --start-seed 0 --count 50
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from random import Random

from jpoke import Battle, Player
from jpoke.enums import Command
from jpoke.players import TreeSearchPlayer

from fuzz_common import (
    FuzzResult,
    build_team,
    failure_signature,
    format_full_log,
    parallel_search,
    random_team_spec,
    write_failure_report,
)

_ROOT = Path(__file__).resolve().parent.parent.parent

# プレイヤーモデルごとの既定値。木探索は1バトルのコストが大きいため
# n_pokemon・max_turns を random より小さくし、レポート出力先も分ける
# （両モードの signature を突き合わせやすくするため別ディレクトリに保存する）。
PLAYER_DEFAULTS = {
    "random":      {"max_turns": 100, "n_pokemon": 6, "failure_dir": "fuzz_failures"},
    "tree_search": {"max_turns": 20,  "n_pokemon": 3, "failure_dir": "tsfuzz_failures"},
}


class RandomPlayer(Player):
    """自前の乱数生成器で選出・行動をランダムに選ぶプレイヤー。

    battle.random は choose_selection/choose_command 呼び出し時点で
    deepcopy された Observation のものであり、実バトルの乱数列とは
    別物に分岐してしまうため使わない（シードからの再現性が壊れる）。
    """

    def __init__(self, username: str, rng: Random):
        super().__init__(username)
        self.rng = rng

    def choose_selection(self, battle: Battle) -> list[int]:
        n = min(battle.n_selected, len(self.team))
        return self.rng.sample(range(len(self.team)), n)

    def choose_command(self, battle: Battle) -> Command:
        commands = battle.available_commands(self)
        return self.rng.choice(commands)


class TreeSearchFuzzPlayer(TreeSearchPlayer):
    """fuzzテスト用の TreeSearchPlayer。

    選出と、探索中の割り込み交代（フォールバック）に、master シードから
    独立に派生させた専用の Random インスタンスを使うことで、選出・木探索の
    フォールバック・チーム構成それぞれの乱数系列を分離し、シードだけで
    完全に再現できるようにする。
    """

    def __init__(self, username: str, rng: Random, max_plies: int = 1):
        super().__init__(username=username, max_plies=max_plies)
        self.rng = rng

    def fallback(self, battle: Battle) -> Command:
        # _available_commands_with_recovery(): switch フェーズで観測マスクの
        # 副作用により合法手が空になる場合の復元付き列挙（TreeSearchPlayer
        # 基底クラス参照）。ここでも同じ復元を使わないと、素の
        # battle.get_available_commands(self) が空リストを返して
        # self.rng.choice() が IndexError になる（fuzz seed=4698 で発見）。
        return self.rng.choice(self._available_commands_with_recovery(battle, self))

    def choose_selection(self, battle: Battle) -> list[int]:
        n = min(battle.n_selected, len(self.team))
        return self.rng.sample(range(len(self.team)), n)


def _make_players(player_kind: str,
                  decision_rngs: list[Random],
                  max_plies: int) -> list[Player]:
    """プレイヤーモデルに応じた2体のプレイヤーを生成する。"""
    if player_kind == "random":
        return [RandomPlayer(f"Player{i + 1}", decision_rngs[i]) for i in range(2)]
    return [
        TreeSearchFuzzPlayer(f"Player{i + 1}", decision_rngs[i], max_plies=max_plies)
        for i in range(2)
    ]


def run_fuzz_battle(seed: int,
                     player_kind: str = "random",
                     max_turns: int = 100,
                     n_pokemon: int = 6,
                     max_plies: int = 1) -> FuzzResult:
    """指定シードで1バトルを実行する。未捕捉例外を検知して結果にまとめる。

    選出数（n_selected、1〜n_pokemon）・各匹の技数（1〜MAX_MOVES）を含め、
    チーム構成は全てシードから決まる（CLI 引数では指定しない＝seedだけで完全に再現できる）。
    行動選択の方策は player_kind で切り替える。
    """
    master = Random(seed)
    team_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    decision_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    n_selected = master.randint(1, n_pokemon)

    team_specs = [random_team_spec(r, n_pokemon) for r in team_rngs]

    players = _make_players(player_kind, decision_rngs, max_plies)
    for player, spec in zip(players, team_specs):
        player.team = build_team(spec)

    battle = Battle(*players, n_selected=n_selected, seed=seed)

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
        winner=winner.username if winner else None,
        n_selected=n_selected, max_turns=max_turns,
        n_pokemon=n_pokemon,
        teams=team_specs,
    )


def _repro_cmd(result: FuzzResult, player_kind: str, max_plies: int) -> str:
    cmd = (
        f"python scripts/fuzz/fuzz_battle.py --seed {result.seed} "
        f"--player {player_kind} "
        f"--max-turns {result.max_turns} --n-pokemon {result.n_pokemon}"
    )
    if player_kind == "tree_search":
        cmd += f" --max-plies {max_plies}"
    return cmd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, help="単発再現モードのシード")
    parser.add_argument("--search", action="store_true", help="バッチ探索モード")
    parser.add_argument("--start-seed", type=int, default=0, help="探索開始シード")
    parser.add_argument("--count", type=int, default=100, help="探索するバトル数")
    parser.add_argument("--player", choices=list(PLAYER_DEFAULTS), default="random",
                        help="行動選択の方策（既定: random）")
    parser.add_argument("--max-turns", type=int, default=None,
                        help="1バトルの最大ターン数（既定はプレイヤーモデル依存）")
    parser.add_argument("--n-pokemon", type=int, default=None,
                        help="1チームの匹数（既定はプレイヤーモデル依存）")
    parser.add_argument("--max-plies", type=int, default=1,
                        help="木探索の先読み手数（player=tree_search のときのみ有効）")
    parser.add_argument("--workers", type=int, default=None,
                        help="バッチ探索モードでの並列worker数（既定: CPU数とcountの小さい方）")
    args = parser.parse_args()

    defaults = PLAYER_DEFAULTS[args.player]
    max_turns = args.max_turns if args.max_turns is not None else defaults["max_turns"]
    n_pokemon = args.n_pokemon if args.n_pokemon is not None else defaults["n_pokemon"]
    failure_dir = _ROOT / ".loop" / defaults["failure_dir"]

    kwargs = dict(
        player_kind=args.player,
        max_turns=max_turns,
        n_pokemon=n_pokemon,
        max_plies=args.max_plies,
    )

    if args.search:
        failures = parallel_search(run_fuzz_battle, args.start_seed, args.count,
                                    workers=args.workers, **kwargs)
        if not failures:
            print(f"OK: {args.count}件すべて成功（seed {args.start_seed}〜{args.start_seed + args.count - 1}）")
            sys.exit(0)
        for result in sorted(failures, key=lambda r: r.seed):
            path = write_failure_report(result, failure_dir, _repro_cmd(result, args.player, args.max_plies))
            print(f"FAIL: seed={result.seed} signature={result.signature}")
            print(f"report: {path}")
        sys.exit(1)

    if args.seed is None:
        parser.error("--seed か --search のいずれかを指定してください。")

    result = run_fuzz_battle(args.seed, **kwargs)
    if result.ok:
        print(f"OK: seed={result.seed} turn={result.turn} winner={result.winner}")
        sys.exit(0)

    path = write_failure_report(result, failure_dir, _repro_cmd(result, args.player, args.max_plies))
    print(f"FAIL: seed={result.seed} signature={result.signature}")
    print(result.error)
    print(f"report: {path}")
    sys.exit(1)


if __name__ == "__main__":
    main()
