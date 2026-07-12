"""jpoke で学べること: 完全ランダムな3vs3全選出バトルを繰り返し、
`Battle.step()` 1回あたりの所要時間を計測する計算速度ベンチマーク。

README の「計算速度」節に載せる数値（mean ± σ）はこのスクリプトの出力を使う。
選出フェーズ・`Battle.start()`（場に出す際の特性発動等）は計測対象に含めない
（ターン進行そのものの「純粋な計算速度」を見たいため）。

技は実際のゲーム仕様（最大4つ）に合わせて4つに固定する。`scripts/fuzz_battle.py`
の1〜10技はバグ出し用に状態空間を広く浅く掘るための設定であり、ここでは
実戦に近い負荷を計測したいため踏襲しない。
"""
from __future__ import annotations

import argparse
import statistics
import time
from random import Random

from jpoke import Battle, Pokemon
from jpoke.data.ability import ABILITIES
from jpoke.data.item import ITEMS
from jpoke.data.move import MOVES
from jpoke.data.pokedex import POKEDEX
from jpoke.players import RandomPlayer
from jpoke.types import Gender, Nature, Type
from typing import get_args

GENDERS = list(get_args(Gender))
NATURES = list(get_args(Nature))
TERA_TYPES = [t for t in get_args(Type) if t]
# "_"始まりはこんらん自傷などエンジン内部専用の技で、実際のポケモンは覚えられない
MOVE_POOL = [name for name in MOVES if not name.startswith("_")]
N_MOVES = min(4, len(MOVE_POOL))


def build_random_pokemon(rng: Random) -> Pokemon:
    """種族・性別・性格・レベル・テラスタイプ・個体値・努力値・特性・持ち物・技が
    すべて完全ランダムな1匹を作る。
    """
    mon = Pokemon(
        rng.choice(list(POKEDEX.keys())),
        gender=rng.choice(GENDERS),
        nature=rng.choice(NATURES),
        level=rng.randint(1, 100),
        ability_name=rng.choice(list(ABILITIES.keys())),
        item_name=rng.choice(list(ITEMS.keys())),
        move_names=rng.sample(MOVE_POOL, N_MOVES),
        tera_type=rng.choice(TERA_TYPES),
    )
    mon.set_ivs([rng.randint(0, 31) for _ in range(6)])
    mon.set_evs([rng.randint(0, 32) for _ in range(6)], hp_policy="reset")
    return mon


def build_random_team(rng: Random, n: int = 3) -> list[Pokemon]:
    return [build_random_pokemon(rng) for _ in range(n)]


def run_benchmark(n_battles: int, max_turns: int, seed: int) -> tuple[list[float], int]:
    """n_battles回のランダム3vs3全選出バトルを実行し、step()ごとの所要時間（秒）と
    スキップしたバトル数を返す。

    master seedからチーム生成用・バトル用の乱数を分離することで、
    同一プロセス内では同じseedなら常に同じ計測条件（チーム構成・展開）を再現できる。

    完全ランダム編成は `scripts/fuzz_battle.py` が拾うような未実装組み合わせの
    エッジケースを踏むことがある。ベンチマークの主目的は計算速度の計測であり
    バグ調査ではないため、バトル単位で例外を捕捉してそのバトルの計測値は捨て、
    次のバトルへ進む（バグ自体は別途 fuzz スクリプトで追う）。
    """
    master = Random(seed)
    team_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    step_times: list[float] = []
    n_skipped = 0

    for _ in range(n_battles):
        battle_seed = master.randrange(2**31)
        player1 = RandomPlayer("Player1")
        player2 = RandomPlayer("Player2")
        player1.team = build_random_team(team_rngs[0])
        player2.team = build_random_team(team_rngs[1])

        # n_selected=3・手持ち3匹なので選出フェーズは常に全選出になる
        battle = Battle(player1, player2, n_selected=3, seed=battle_seed)
        battle.start()

        battle_step_times: list[float] = []
        try:
            while battle.judge_winner() is None and battle.turn < max_turns:
                t0 = time.perf_counter()
                battle.step()
                battle_step_times.append(time.perf_counter() - t0)
        except Exception:
            n_skipped += 1
            continue

        step_times.extend(battle_step_times)

    return step_times, n_skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-battles", type=int, default=300, help="実行するバトル数（既定: 300）")
    parser.add_argument("--max-turns", type=int, default=100, help="1バトルの最大ターン数（既定: 100）")
    parser.add_argument("--seed", type=int, default=0, help="乱数シード（既定: 0）")
    args = parser.parse_args()

    step_times, n_skipped = run_benchmark(args.n_battles, args.max_turns, args.seed)

    n = len(step_times)
    total = sum(step_times)
    mean = statistics.mean(step_times)
    sigma = statistics.pstdev(step_times)
    n_ok = args.n_battles - n_skipped

    print(f"バトル数: {args.n_battles} / 最大ターン数: {args.max_turns} / seed: {args.seed}")
    if n_skipped:
        print(f"未捕捉例外によりスキップしたバトル数: {n_skipped}（完全ランダム編成のエッジケース。scripts/fuzz_battle.py 参照）")
    print(f"stepサンプル数: {n}")
    print(f"1step所要時間: {mean * 1000:.3f} ms ± {sigma * 1000:.3f} ms (mean ± σ)")
    print(f"battles/sec: {n_ok / total:.1f}")
    print(f"turns/sec: {n / total:.1f}")

    # 試してみよう: --n-battles を増やしてサンプル数を増やしたり、
    # --seed を変えて別の乱数系列で再計測してみる


if __name__ == "__main__":
    main()
