"""jpoke で学べること: 実際のバトルシミュレーションからNash均衡（混合戦略）を近似する。

## 題材

1体・3つの技だけで対戦させ、「毎ターンどの技を何%の確率で選ぶか」という
混合戦略（mixed strategy）のNash均衡を近似する。3つの技がじゃんけんのような
三すくみの関係にある場合、単一の技を固定で使い続ける戦略は必ず弱点を突かれるため、
確率配分の設計が課題になる。両者がこれ以上一方的に得をする変更をする余地がない
状態を Nash均衡 と呼ぶ。

対戦するポケモン・技3つはファイル先頭の「対戦相手の構成」で指定する。既定値
（マッハパンチ/はやてがえし/きあいパンチを覚えたエビワラー）が三すくみになる
理由など技の仕様の詳細は `docs/spec/moves/` の各技の仕様書を参照。ここを別の
ポケモン・技3つに書き換えれば、そちらの読み合いでも同じように均衡を近似できる
（アルゴリズム自体は技の内容に依存しない。ただし戦略を3次元の確率分布として
扱うため、技はちょうど3つである必要がある）。

## このスクリプトのアプローチ

じゃんけんの勝敗表のような固定の利得行列は用意しない。ダメージ乱数・命中判定・
急所判定・行動順序などを含む実際の jpoke バトルを『毎ターン確率 p で技を選ぶ』
プレイヤー同士で多数回対戦させ、その勝率を Nash均衡の近似計算に使う
（詳しい理由は `simplex_grid()` / `approximate_nash()` のdocstringを参照）。

処理の流れ:

1. `simplex_grid()` で「3つの技を選ぶ確率」の候補を格子状に列挙する
2. `estimate_value()` で、2つの混合戦略同士を対戦させたときの期待勝率を
   モンテカルロ推定する（`ProcessPoolExecutor` で並列化）
3. `approximate_nash()` で反復最適反応（fictitious play）を繰り返し、
   互いに一方的な得のない均衡へ近づける

戦術研究（読み合いの定量分析）ユースケースの発展形。

## 精度とデータ量のトレードオフ

実際にバトルを多数回シミュレートして勝率を推定する都合上、他のexamplesより実行に
時間がかかる（手元では十数秒程度）。それでも実行時間を抑えるため、`GRID_STEP` /
`EVAL_TRIALS` / `ITERATIONS` は小さめに設定してあり、近似の精度はまだ粗い
（`exploitability` の値が大きめに出ることがある）。
本格的に精度を求める分析をしたい場合は、ファイル先頭の「実行設定」を以下のように
大きくすると良い（計算量はおおむね積で増え、実行時間も比例して延びる点に注意）:

* `GRID_STEP = 0.02`（候補数が増え、より細かい確率の組み合わせを検討できる）
* `EVAL_TRIALS = 500`（1組の勝率推定がより安定する）
* `ITERATIONS = 50`（fictitious play がより収束に近づく）
"""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command

# ---- 対戦相手の構成 ----
# ここを書き換えるだけで、別のポケモン・技3つの読み合いに変更できる
# （MOVES はちょうど3つ指定する）
SPECIES_NAME = "エビワラー"
ABILITY_NAME = "てつのこぶし"
NATURE = "いじっぱり"
MOVES = ["マッハパンチ", "はやてがえし", "きあいパンチ"]
EVS = [0, 0, 0, 0, 0, 0]
IVS = [31, 31, 31, 31, 31, 31]

# ---- 実行設定 ----
# 実行時間を抑えつつ動作を確認できる値にしてある。本格的な精度が欲しい場合は
# モジュールdocstringの「精度とデータ量のトレードオフ」を参照して値を大きくする
BASE_SEED = 20260323
MAX_TURNS = 10  # 1ゲームあたりの最大ターン数

EVAL_TRIALS = 15  # 戦略ペアの勝率を推定する試行回数。大きいほど精密だが計算量が増える
GRID_STEP = 0.25  # 混合戦略の候補を生成するグリッドの刻み幅。小さいほど精密だが計算量が増える
ITERATIONS = 4  # 反復最適反応の繰り返し回数。多いほど均衡に近づく傾向があるが計算量が増える

N_WORKERS: int | None = None  # None のときは CPU 論理コア数を自動利用
CHUNK_SIZE = 8  # 1ワーカーがまとめて処理する試行数。大きすぎると負荷が偏る
SHOW_PROGRESS = True  # 進捗ログを見たいときだけ True


class MixedMovePlayer(Player):
    """毎ターン、指定確率で3つの技のどれかを選ぶプレイヤー。

    `battle.decision_random` は jpoke の既存プレイヤー（`RandomPlayer` 等）が
    行動選択に使っているものと同じ乱数源（ゲーム進行用の `battle.random` とは
    独立）で、ここでもそれに合わせている。
    """

    def __init__(self, probs: tuple[float, float, float], username: str = ""):
        super().__init__(username)
        self.probs = probs  # MOVES の3つの技を選ぶ確率（順に対応）

    def choose_command(self, battle: Battle) -> Command:
        r = battle.decision_random.random()
        p0, p1, _p2 = self.probs
        if r < p0:
            return Command.MOVE_0
        if r < p0 + p1:
            return Command.MOVE_1
        return Command.MOVE_2  # 残りの確率（1 - p0 - p1）


def build_pokemon() -> Pokemon:
    """「対戦相手の構成」から対戦用ポケモンを1体構築する。"""
    mon = Pokemon(SPECIES_NAME, ability_name=ABILITY_NAME, nature=NATURE, move_names=MOVES)
    mon.set_evs(EVS)
    mon.set_ivs(IVS, hp_policy="reset")  # 新規構築なので満タンにする
    return mon


def play_game(row_probs: tuple[float, float, float],
              col_probs: tuple[float, float, float],
              seed: int,
              max_turns: int = 10) -> float:
    """1ゲーム実行して、行側プレイヤーのポイントを返す。

    Returns:
        1.0: 行側勝利
        0.5: 引き分け（ターン上限に達し、TOD（Time Over Draw）判定でも互角）
        0.0: 列側勝利
    """
    p0 = MixedMovePlayer(row_probs, username="p0")
    p1 = MixedMovePlayer(col_probs, username="p1")
    p0.team.append(build_pokemon())
    p1.team.append(build_pokemon())

    battle = Battle(p0, p1, seed=seed)
    battle.test_option.accuracy = 100  # 命中率のブレを消し、技選択の駆け引きだけを見る
    battle.start()  # Turn 0: 初期繰り出し

    while battle.judge_winner() is None and battle.turn <= max_turns:
        battle.step()

    winner = battle.judge_winner()
    if winner is p0:
        return 1.0
    if winner is p1:
        return 0.0

    # ターン上限に達しても決着しない場合は、TOD（Time Over Draw）スコアで優劣を決める
    score0 = battle.calc_tod_score(p0)
    score1 = battle.calc_tod_score(p1)
    if abs(score0 - score1) < 1e-9:
        return 0.5
    return 1.0 if score0 > score1 else 0.0


def simplex_grid(step: float) -> list[tuple[float, float, float]]:
    """3次元単体上の候補戦略を格子で生成する。

    理論初心者向けメモ:

    * 混合戦略は「各手を出す確率」の組 (p1, p2, p3)
    * 条件は p1+p2+p3=1, かつ各 pi >= 0
    * この集合を単体（simplex）と呼ぶ

    なぜ固定の利得行列ではなく候補戦略を実際に対戦させるのか:
    このゲームは「毎ターン確率通りに技を選び直す」という多ターンの逐次ゲームであり、
    1ターン分の技同士の勝敗表だけでは複数ターンにわたるHPの削り合いや行動順の
    駆け引きを表せない。そのため、確率の組ごとに実際のバトルを多数回シミュレート
    して期待勝率を求める。
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
    """並列ワーカー用: 指定範囲の試行合計を返す。

    `ProcessPoolExecutor.map()` に渡すため、引数はpickle可能なタプルにまとめている。
    """
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

    * 閉形式で計算しづらいので、同じ条件の試行をたくさん回して平均を取る
    * これがモンテカルロ推定
    * `trials` を大きくするほど推定のブレ（分散）は小さくなるが、その分実行時間も増える
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
    """列側固定戦略に対する行側の最適反応（勝率が最大になる候補）を返す。"""
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
    """行側固定戦略に対する列側の最適反応（行側の勝率が最小になる候補）を返す。"""
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

    理論初心者向けメモ:

    * 相手の「これまでの平均戦略」に対して、今の自分にとっての最善手（最適反応）を
      毎回計算する
    * その最適反応を積み上げて平均を取ると、対称ゼロサムゲームでは Nash均衡に
      近づいていくことが知られている（fictitious play の収束定理）
    * `exploitability`（付け入る隙）が小さいほど、互いに一方的な得をする余地が
      少ない＝均衡に近いと判断できる
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

    # 最終的な平均戦略同士の期待勝率（ゲームの値）を、より多くの試行で推定し直す
    est_value = estimate_value(row_avg, col_avg, trials * 2, seed_base + 99_000_000, max_turns, executor)
    # exploitability: 相手が現状の平均戦略から動かないと仮定したとき、
    # 自分が最適反応に切り替えることでどれだけ得ができるか（0に近いほど均衡に近い）
    row_exploit = best_response_to_col(col_avg, candidates, trials, seed_base + 77_000_000, max_turns, executor)[1] - est_value
    col_exploit = est_value - best_response_to_row(row_avg, candidates, trials, seed_base + 88_000_000, max_turns, executor)[1]
    return row_avg, col_avg, est_value, max(row_exploit, col_exploit)


def main() -> None:
    """スクリプト本体。

    設定値はファイル先頭の「実行設定」を編集して調整する
    （精度と実行時間のトレードオフはモジュールdocstring参照）。
    """
    workers = N_WORKERS if N_WORKERS is not None else max(1, (os.cpu_count() or 1) - 1)

    candidates = simplex_grid(GRID_STEP)
    print(f"=== {SPECIES_NAME} Janken Nash Approx ({'/'.join(MOVES)}) ===")
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

    print(f"row_mix: {strategy_text(x)}")
    print(f"col_mix: {strategy_text(y)}")
    print(f"value={value:.4f}, exploitability={exploit_gap:.4f}")

    # 試してみよう:
    # * GRID_STEP / EVAL_TRIALS / ITERATIONS を大きくして、結果がどれだけ安定するか比較する
    # * ファイル先頭の「対戦相手の構成」で別のポケモン・技3つに変えて、
    #   三すくみになる組み合わせ・ならない組み合わせでどう均衡が変わるか
    #   （あるいは支配戦略が生まれるか）を観察する
    # * 他のNash均衡の求め方との比較:
    #   このスクリプトは「候補戦略を格子状に列挙し、反復最適反応で均衡へ近づける」という
    #   汎用的だが計算量の大きい方法を使っている。もし「1ターンだけの技同士の勝率」が
    #   全体の均衡を決めると仮定できるなら、3x3の利得行列をモンテカルロ推定した上で
    #   `scipy.optimize.linprog` や `nashpy` のようなライブラリで線形計画問題として
    #   厳密に解く方がはるかに高速（候補の格子分割やfictitious playの反復が不要になる）。
    #   ただしこのゲームは複数ターンにわたるHPの削り合いを含む逐次ゲームのため、
    #   1ターン分の勝率表だけでは不十分という前提でこの実装を選んでいる


if __name__ == "__main__":
    main()
