"""エビワラーじゃんけんの勝率Nash均衡を推定するスクリプト。"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command

MOVES = ["マッハパンチ", "はやてがえし", "きあいパンチ"]

# ---- 実行設定 ----
BASE_SEED = 20260323
MAX_TURNS = 10

EVAL_TRIALS = 200  # 戦略ペアの勝率を推定する試行回数。大きいほど精密だが計算量が増える
GRID_STEP = 0.1  # 混合戦略の候補を生成するグリッドの刻み幅。小さいほど精密だが計算量が増える
ITERATIONS = 30  # 反復最適反応の繰り返し回数。多いほど均衡に近づく傾向があるが計算量が増える

N_WORKERS: int | None = None  # None のときは CPU 論理コア数を自動利用
CHUNK_SIZE = 8  # 1ワーカーがまとめて処理する試行数。大きすぎると負荷が偏る
SHOW_PROGRESS = True  # 進捗ログを見たいときだけ True


class MixedMovePlayer(Player):
    """毎ターン、指定確率で技を選ぶプレイヤー。"""

    def __init__(self, probs: tuple[float, float, float], name: str = ""):
        super().__init__(name)
        self.probs = probs

    def choose_selection_commands(self, battle: Battle) -> list[Command]:
        return [Command.SELECT_0]

    def choose_action_command(self, battle: Battle) -> Command:
        r = battle.random.random()
        p0, p1, _p2 = self.probs
        if r < p0:
            return Command.MOVE_0
        if r < p0 + p1:
            return Command.MOVE_1
        return Command.MOVE_2


def make_hitmonchan() -> Pokemon:
    """仕様書条件のエビワラーを構築する。"""
    mon = Pokemon(
        "エビワラー",
        ability="てつのこぶし",
        nature="いじっぱり",
        moves=MOVES,
    )
    mon.effort = [0, 0, 0, 0, 0, 0]
    mon.indiv = [31, 31, 31, 31, 31, 31]
    return mon


def play_game(row_probs: tuple[float, float, float],
              col_probs: tuple[float, float, float],
              seed: int,
              max_turns: int = 10) -> float:
    """1ゲーム実行して、行側プレイヤーのポイントを返す。

    Returns:
        1.0: 行側勝利
        0.5: 引き分け
        0.0: 列側勝利
    """
    p0 = MixedMovePlayer(row_probs, name="p0")
    p1 = MixedMovePlayer(col_probs, name="p1")
    p0.team.append(make_hitmonchan())
    p1.team.append(make_hitmonchan())

    battle = Battle([p0, p1], seed=seed)
    battle.test_option.accuracy = 100
    battle.advance_turn()  # Turn 0: 初期繰り出し

    while battle.judge_winner() is None and battle.turn <= max_turns:
        battle.advance_turn()

    winner = battle.judge_winner()
    if winner is p0:
        return 1.0
    if winner is p1:
        return 0.0

    score0 = battle.determine_tod_score(p0)
    score1 = battle.determine_tod_score(p1)
    if abs(score0 - score1) < 1e-9:
        return 0.5
    return 1.0 if score0 > score1 else 0.0


def simplex_grid(step: float) -> list[tuple[float, float, float]]:
    """3次元単体上の候補戦略を格子で生成する。

    理論初心者向けメモ:
    - 混合戦略は「各手を出す確率」の組 (p1, p2, p3)
    - 条件は p1+p2+p3=1, かつ各 pi >= 0
    - この集合を単体(simplex)と呼ぶ
    """
    n = int(round(1.0 / step))
    out: list[tuple[float, float, float]] = []
    for i in range(n + 1):
        for j in range(n + 1 - i):
            k = n - i - j
            out.append((i / n, j / n, k / n))
    return out


def strategy_text(probs: tuple[float, float, float]) -> str:
    return ", ".join(f"{m}:{p:.3f}" for m, p in zip(MOVES, probs))


def _chunk_total(args: tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    int,
    int,
    int,
]) -> float:
    """並列ワーカー用: 指定範囲の試行合計を返す。"""
    row_probs, col_probs, start_seed, chunk_trials, max_turns = args
    total = 0.0
    for offset in range(chunk_trials):
        total += play_game(row_probs, col_probs, seed=start_seed + offset, max_turns=max_turns)
    return total


def estimate_value(row_probs: tuple[float, float, float],
                   col_probs: tuple[float, float, float],
                   trials: int,
                   seed_base: int,
                   max_turns: int,
                   executor: ProcessPoolExecutor) -> float:
    """戦略ペアの期待勝率ポイントをモンテカルロ推定する。

    理論初心者向けメモ:
    - 閉形式で計算しづらいので、同じ条件の試行をたくさん回して平均を取る
    - これがモンテカルロ推定
    """
    tasks = []
    start = 0
    while start < trials:
        chunk_trials = min(CHUNK_SIZE, trials - start)
        tasks.append((row_probs, col_probs, seed_base + start, chunk_trials, max_turns))
        start += chunk_trials

    total = sum(executor.map(_chunk_total, tasks))
    return total / trials


def best_response_to_col(col_probs: tuple[float, float, float],
                         candidates: Iterable[tuple[float, float, float]],
                         trials: int,
                         seed_base: int,
                         max_turns: int,
                         executor: ProcessPoolExecutor) -> tuple[tuple[float, float, float], float]:
    """列側固定戦略に対する行側の最適反応を返す。"""
    best_p: tuple[float, float, float] | None = None
    best_v = -1.0
    for i, row_probs in enumerate(candidates):
        v = estimate_value(row_probs, col_probs, trials, seed_base + i * 10_000, max_turns, executor)
        if v > best_v:
            best_v = v
            best_p = row_probs
    assert best_p is not None
    return best_p, best_v


def best_response_to_row(row_probs: tuple[float, float, float],
                         candidates: Iterable[tuple[float, float, float]],
                         trials: int,
                         seed_base: int,
                         max_turns: int,
                         executor: ProcessPoolExecutor) -> tuple[tuple[float, float, float], float]:
    """行側固定戦略に対する列側の最適反応を返す。"""
    best_q: tuple[float, float, float] | None = None
    best_v = 2.0
    for j, col_probs in enumerate(candidates):
        v = estimate_value(row_probs, col_probs, trials, seed_base + j * 10_000, max_turns, executor)
        if v < best_v:
            best_v = v
            best_q = col_probs
    assert best_q is not None
    return best_q, best_v


def add_vec(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def div_vec(a: tuple[float, float, float], d: float) -> tuple[float, float, float]:
    return (a[0] / d, a[1] / d, a[2] / d)


def approximate_nash(candidates: list[tuple[float, float, float]],
                     iterations: int,
                     trials: int,
                     seed_base: int,
                     max_turns: int,
                     executor: ProcessPoolExecutor) -> tuple[tuple[float, float, float], tuple[float, float, float], float, float]:
    """反復最適反応（fictitious play）で混合戦略を近似する。

    - 相手の平均戦略に対して「今の最善手(最適反応)」を毎回計算
    - その最適反応の平均を取ると、均衡に近づいていくことが多い
    """
    row_sum = (0.0, 0.0, 0.0)
    col_sum = (0.0, 0.0, 0.0)
    row_avg = (1 / 3, 1 / 3, 1 / 3)
    col_avg = (1 / 3, 1 / 3, 1 / 3)

    for t in range(1, iterations + 1):
        row_br, row_br_val = best_response_to_col(
            col_avg,
            candidates,
            trials,
            seed_base + t * 1_000_000,
            max_turns,
            executor,
        )
        col_br, col_br_val = best_response_to_row(
            row_avg,
            candidates,
            trials,
            seed_base + t * 2_000_000,
            max_turns,
            executor,
        )

        row_sum = add_vec(row_sum, row_br)
        col_sum = add_vec(col_sum, col_br)
        row_avg = div_vec(row_sum, float(t))
        col_avg = div_vec(col_sum, float(t))

        if SHOW_PROGRESS:
            print(f"iter={t:02d}  row_br={row_br_val:.4f}  col_br={col_br_val:.4f}")

    est_value = estimate_value(row_avg, col_avg, trials * 2, seed_base + 99_000_000, max_turns, executor)
    row_exploit = best_response_to_col(col_avg, candidates, trials, seed_base + 77_000_000, max_turns, executor)[1] - est_value
    col_exploit = est_value - best_response_to_row(row_avg, candidates, trials, seed_base + 88_000_000, max_turns, executor)[1]
    return row_avg, col_avg, est_value, max(row_exploit, col_exploit)


def main() -> None:
    """スクリプト本体。

    設定値はファイル先頭の定数を編集して調整する。
    """
    workers = N_WORKERS if N_WORKERS is not None else max(1, (os.cpu_count() or 1) - 1)

    candidates = simplex_grid(GRID_STEP)
    print("=== Hitmonchan Janken Nash Approx ===")
    print(f"candidates={len(candidates)}, step={GRID_STEP}, iter={ITERATIONS}, trials={EVAL_TRIALS}, workers={workers}")

    with ProcessPoolExecutor(max_workers=workers) as executor:
        x, y, value, exploit_gap = approximate_nash(
            candidates=candidates,
            iterations=ITERATIONS,
            trials=EVAL_TRIALS,
            seed_base=BASE_SEED,
            max_turns=MAX_TURNS,
            executor=executor,
        )

    # 最終出力は重複しないように1回ずつ簡潔に表示
    print(f"row_mix: {strategy_text(x)}")
    print(f"col_mix: {strategy_text(y)}")
    print(f"value={value:.4f}, exploitability={exploit_gap:.4f}")


if __name__ == "__main__":
    main()
