"""実際のバトルシミュレーションからNash均衡（混合戦略）を近似する。

## ゲーム理論の用語ミニ解説（対戦知識はあるがゲーム理論は初めての人向け）

このファイルと `04_janken_nash_cfr.py` は、ここまでのexamplesと比べて構文・
専門用語の両面で難易度が上がる。先に出てくる用語だけ対戦の感覚に結び付けて
おく（詳細はコード中の各docstringで随時補足する）。

* **混合戦略（mixed strategy）**: 「毎ターンどの技を何%の確率で選ぶか」という
  確率の組。対人戦で「同じ技を固定で使うと読まれるので、あえて確率的に
  技を散らす」という発想そのもの
* **Nash均衡**: お互いにこれ以上一方的に戦略を変えても得をしない、確率配分の
  落としどころ。「これ以上崩しようがない読み合いの配分」を数値で求めたもの、
  とイメージすると分かりやすい
* **fictitious play（このスクリプトのアルゴリズム）**: 「相手のこれまでの
  対戦傾向（平均戦略）に対して、今なら一番勝てる手（最適反応）を選ぶ」ことを
  何度も繰り返し、選ばれた最適反応の平均を取る手法。対人戦で言う「相手の
  使用率統計を取り、それへの回答を積み重ねていく」を機械的に繰り返す
  イメージ（対称ゼロサムゲームではこの平均がNash均衡に収束することが
  知られている＝fictitious playの収束定理）
* **exploitability（付け入る隙）**: 相手が今の戦略から動かないと仮定したとき、
  自分が最適反応に切り替えるとどれだけ得できるか。0に近いほど「隙がない＝
  均衡に近い」と判断できる

## 04との違い

このスクリプトが求める戦略は「毎ターン同じ確率 (p1, p2, p3) で技を選び続ける」
固定の混合戦略で、自分・相手のHP状況によって確率を変えることはしない
（`MixedMovePlayer.choose_command()` 参照）。まずはこの「固定の確率配分での
Nash均衡」を理解してから、局面（HP状況）に応じて確率を変える適応的な戦略へ
発展させた `04_janken_nash_cfr.py` に進むと理解しやすい。

## 題材

1体・3つの技だけで対戦させ、「毎ターンどの技を何%の確率で選ぶか」という
混合戦略（mixed strategy）のNash均衡を近似する。3つの技がじゃんけんのような
三すくみの関係にある場合、単一の技を固定で使い続ける戦略は必ず弱点を突かれるため、
確率配分の設計が課題になる。両者がこれ以上一方的に得をする変更をする余地がない
状態を Nash均衡 と呼ぶ。

対戦するポケモン・技3つはファイル先頭の `MATCHUP` で指定する（既定値はマッハパンチ/
はやてがえし/きあいパンチを覚えたエビワラーで、三すくみになる理由など技の仕様の詳細は
`.internal/spec/moves/` の各技の仕様書を参照）。ここを別のポケモン・技3つに書き換えれば、
そちらの読み合いでも同じように均衡を近似できる（アルゴリズム自体は技の内容に依存しない。
ただし戦略を3次元の確率分布として扱うため、技はちょうど3つである必要がある）。

## このスクリプトのアプローチ

じゃんけんの勝敗表のような固定の利得行列は用意しない。ダメージ乱数・命中判定・
急所判定・行動順序などを含む実際の jpoke バトルを『毎ターン確率 p で技を選ぶ』
プレイヤー同士で多数回対戦させ、その勝率を Nash均衡の近似計算に使う
（詳しい理由は `simplex_grid()` のdocstringを参照）。

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
from dataclasses import dataclass
from typing import Iterable, NamedTuple

from jpoke import Battle, Player
from jpoke.enums import Command

from _janken_common import MOVE_COMMANDS, Matchup, add_vec, result_point

# ---- 対戦相手の構成 ----
# ここを書き換えるだけで、別のポケモン・技3つの読み合いに変更できる
# （moves はちょうど3つ指定する）
MATCHUP = Matchup(
    species_name="エビワラー",
    ability_name="てつのこぶし",
    nature="いじっぱり",
    moves=["マッハパンチ", "はやてがえし", "きあいパンチ"],
    evs=[0, 0, 0, 0, 0, 0],
    ivs=[31, 31, 31, 31, 31, 31],
)

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


@dataclass(frozen=True)
class SimConfig:
    """勝率推定に使う、実行全体を通して変わらない設定をまとめたもの。

    `estimate_value()` 以降の関数はどれも (trials, max_turns, executor) を
    そのまま次に渡すだけなので、引数のバケツリレーと順序間違いを防ぐために
    まとめている。`seed_base` は呼び出しごとに値が変わるため、あえて含めず
    各関数の独立した引数のままにしてある。
    """

    trials: int
    max_turns: int
    executor: ProcessPoolExecutor


class NashResult(NamedTuple):
    """`approximate_nash()` の戻り値。"""

    row_mix: tuple[float, float, float]
    col_mix: tuple[float, float, float]
    value: float
    exploitability: float


class MixedMovePlayer(Player):
    """毎ターン、指定確率で3つの技のどれかを選ぶプレイヤー。

    `battle.decision_random`（既存プレイヤーの行動選択にも使われる乱数源）の詳細は
    docs/api/README.md の Player「choose_command()のオーバーライド」節を参照。
    """

    def __init__(self, probs: tuple[float, float, float], username: str = ""):
        super().__init__(username)
        self.probs = probs  # MATCHUP.moves の3つの技を選ぶ確率（順に対応）

    def choose_command(self, battle: Battle) -> Command:
        r = battle.decision_random.random()
        p0, p1, _p2 = self.probs
        if r < p0:
            return MOVE_COMMANDS[0]
        if r < p0 + p1:
            return MOVE_COMMANDS[1]
        return MOVE_COMMANDS[2]  # 残りの確率（1 - p0 - p1）


def play_game(row_probs: tuple[float, float, float],
              col_probs: tuple[float, float, float],
              seed: int,
              max_turns: int = 10) -> float:
    """1ゲーム実行して、行側プレイヤーのポイントを返す（詳細は `result_point()` 参照）。"""
    p0 = MixedMovePlayer(row_probs, username="p0")
    p1 = MixedMovePlayer(col_probs, username="p1")
    MATCHUP.add_team_pokemon(p0)
    MATCHUP.add_team_pokemon(p1)

    # accuracy_fix_threshold=0 で命中率のブレを消し、技選択の駆け引きだけを見る
    battle = Battle(p0, p1, seed=seed, accuracy_fix_threshold=0)
    battle.start()  # Turn 0: 初期繰り出し

    while not battle.finished and battle.turn <= max_turns:
        battle.step()

    return result_point(battle, p0, p1)


def simplex_grid(step: float) -> list[tuple[float, float, float]]:
    """3次元単体（simplex。「各手を出す確率」の組 (p1, p2, p3) で p1+p2+p3=1, pi>=0
    を満たす集合）上の候補戦略を格子で生成する。

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
                    seed_base: int,
                    cfg: SimConfig) -> float:
    """戦略ペアの期待勝率ポイントをモンテカルロ推定する。

    閉形式で計算しづらいので、同じ条件の試行をたくさん回して平均を取る
    （モンテカルロ推定）。`cfg.trials` を大きくするほど推定のブレ（分散）は
    小さくなるが、その分実行時間も増える。
    """
    tasks = []
    start = 0
    while start < cfg.trials:
        chunk_trials = min(CHUNK_SIZE, cfg.trials - start)
        tasks.append((row_probs, col_probs, seed_base + start, chunk_trials, cfg.max_turns))
        start += chunk_trials

    total = sum(cfg.executor.map(_chunk_total, tasks))
    return total / cfg.trials


def best_response_to_col(col_probs: tuple[float, float, float],
                          candidates: Iterable[tuple[float, float, float]],
                          seed_base: int,
                          cfg: SimConfig) -> tuple[tuple[float, float, float], float]:
    """列側固定戦略に対する行側の最適反応（勝率が最大になる候補）を返す。"""
    best_p: tuple[float, float, float] | None = None
    best_v = -1.0
    for i, row_probs in enumerate(candidates):
        v = estimate_value(row_probs, col_probs, seed_base + i * 10_000, cfg)
        if v > best_v:
            best_v = v
            best_p = row_probs
    assert best_p is not None
    return best_p, best_v


def best_response_to_row(row_probs: tuple[float, float, float],
                          candidates: Iterable[tuple[float, float, float]],
                          seed_base: int,
                          cfg: SimConfig) -> tuple[tuple[float, float, float], float]:
    """行側固定戦略に対する列側の最適反応（行側の勝率が最小になる候補）を返す。"""
    best_q: tuple[float, float, float] | None = None
    best_v = 2.0
    for j, col_probs in enumerate(candidates):
        v = estimate_value(row_probs, col_probs, seed_base + j * 10_000, cfg)
        if v < best_v:
            best_v = v
            best_q = col_probs
    assert best_q is not None
    return best_q, best_v


def approximate_nash(candidates: list[tuple[float, float, float]],
                      iterations: int,
                      seed_base: int,
                      cfg: SimConfig) -> NashResult:
    """反復最適反応（fictitious play）で混合戦略を近似する（用語はモジュールdocstring参照）。"""
    row_sum = (0.0, 0.0, 0.0)
    col_sum = (0.0, 0.0, 0.0)
    row_avg = (1 / 3, 1 / 3, 1 / 3)
    col_avg = (1 / 3, 1 / 3, 1 / 3)

    for t in range(1, iterations + 1):
        row_br, row_br_val = best_response_to_col(
            col_avg, candidates, seed_base + t * 1_000_000, cfg,
        )
        col_br, col_br_val = best_response_to_row(
            row_avg, candidates, seed_base + t * 2_000_000, cfg,
        )

        row_sum = add_vec(row_sum, row_br)
        col_sum = add_vec(col_sum, col_br)
        row_avg = div_vec(row_sum, float(t))
        col_avg = div_vec(col_sum, float(t))

        if SHOW_PROGRESS:
            print(f"iter={t:02d}  row_br={row_br_val:.4f}  col_br={col_br_val:.4f}")

    # 最終的な平均戦略同士の期待勝率（ゲームの値）を、より多くの試行で推定し直す
    final_cfg = SimConfig(trials=cfg.trials * 2, max_turns=cfg.max_turns, executor=cfg.executor)
    est_value = estimate_value(row_avg, col_avg, seed_base + 99_000_000, final_cfg)
    # exploitability: 相手が現状の平均戦略から動かないと仮定したとき、
    # 自分が最適反応に切り替えることでどれだけ得ができるか（0に近いほど均衡に近い）
    row_exploit_v = best_response_to_col(col_avg, candidates, seed_base + 77_000_000, cfg)[1]
    col_exploit_v = best_response_to_row(row_avg, candidates, seed_base + 88_000_000, cfg)[1]
    row_exploit = row_exploit_v - est_value
    col_exploit = est_value - col_exploit_v
    return NashResult(row_avg, col_avg, est_value, max(row_exploit, col_exploit))


def div_vec(a: tuple[float, float, float], d: float) -> tuple[float, float, float]:
    return (a[0] / d, a[1] / d, a[2] / d)


def main() -> None:
    """スクリプト本体。

    設定値はファイル先頭の「実行設定」を編集して調整する
    （精度と実行時間のトレードオフはモジュールdocstring参照）。
    """
    workers = N_WORKERS if N_WORKERS is not None else max(1, (os.cpu_count() or 1) - 1)

    candidates = simplex_grid(GRID_STEP)
    print(f"=== {MATCHUP.species_name} Janken Nash Approx ({'/'.join(MATCHUP.moves)}) ===")
    print(f"candidates={len(candidates)}, step={GRID_STEP}, iter={ITERATIONS}, "
          f"trials={EVAL_TRIALS}, workers={workers}")

    with ProcessPoolExecutor(max_workers=workers) as executor:
        cfg = SimConfig(trials=EVAL_TRIALS, max_turns=MAX_TURNS, executor=executor)
        result = approximate_nash(candidates, iterations=ITERATIONS, seed_base=BASE_SEED, cfg=cfg)

    print(f"row_mix: {MATCHUP.strategy_text(result.row_mix)}")
    print(f"col_mix: {MATCHUP.strategy_text(result.col_mix)}")
    print(f"value={result.value:.4f}, exploitability={result.exploitability:.4f}")

    # 試してみよう:
    # * GRID_STEP / EVAL_TRIALS / ITERATIONS を大きくして、結果がどれだけ安定するか比較する
    # * ファイル先頭の MATCHUP を書き換えて、別のポケモン・技3つに変えて、
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
    # * 次のステップ: `04_janken_nash_cfr.py` では、ここで求めた「固定の確率配分」を
    #   自分・相手のHP状況（information set）に応じて変える適応的な戦略に発展させる


if __name__ == "__main__":
    main()
