"""jpoke で学べること: CFR風の自己対戦学習で「状態に応じて手を変える」読み合いAIを作る。

## 08との違い

`08_janken_nash_fictitious_play.py` は「毎ターン同じ確率で技を選び続ける」固定の混合戦略の
Nash均衡を求めた。しかし実戦の読み合いはもっと現実的で、「自分のHPが少ない
ときはリスクを避けて手堅い技を選ぶ」「相手を追い詰めたら一発逆転を警戒して
別の技を増やす」といった、局面（HP状況）に応じて確率を変える適応的な戦略の
方が強くなりうる。このサンプルは、その「状態に応じた戦略」を自己対戦から
学習する。対戦するポケモン・技3つはファイル先頭の「対戦相手の構成」で指定する
（08と同じ既定値・同じ制約。詳細は08のモジュールdocstring「題材」を参照）。

## 状態（information set）の定義

状態は `(自分のHP割合バケット, 相手のHP割合バケット)` の組で表す
（`HP_BUCKETS` 段階に離散化。既定は3段階 = 「多い/中/少ない」）。
ターン数などは状態に含めない単純化をしている（詳しくは `hp_bucket()` 参照）。
この状態ごとに「MOVES の3つの技をそれぞれ何%選ぶか」という戦略テーブルを
学習する。

## アルゴリズム: ロールアウトベースのregret matching（CFR風）

CFR（Counterfactual Regret Minimization）は本来、ゲーム木の分岐を厳密に
辿れる小さなゲーム向けの手法で、各状態（information set）ごとに
「実際に選んだ手」と「もし別の手を選んでいたら」の差（regret、後悔）を
蓄積し、正の後悔が大きい手ほど次回選ばれやすくする regret matching という
更新則でNash均衡に収束させる。

このサンプルの対戦は実際のダメージ乱数・急所判定を含む本物のバトル
シミュレーションであり、厳密なゲーム木を毎回全展開するのは非現実的なため、
以下のように近似する（`docs/plan/archives/janken_nash_equilibrium_methods.md`
の「案4」も参照）:

1. 各ターン、両者は現在の状態の戦略テーブルから技を確率的に選ぶ
2. 実際に選んだ手を確定する前に、`battle.copy()` で盤面を複製し、
   「もし別の手を選んでいたら」を3通り（自分の手だけ差し替え、相手の手は
   実際に選んだ手のまま固定）フォークして、それぞれ以降を現在の戦略で
   決着まで進めた場合の勝率を評価する（`_rollout_value()`）
3. その3通りの勝率と、実際に選んだ確率分布での期待勝率との差を後悔として
   蓄積し（regret matching）、次にこの状態を再訪したときの戦略に反映する
4. 実際の対戦は、フォークとは別に実際に選んだ手で1ターンだけ進める

厳密な教科書通りのCFR（到達確率で重み付けした反実仮想価値を使う
outcome-sampling MCCFR等）ではなく、`battle.copy()` によるロールアウトで
反実仮想的な価値を近似する実用的な簡略版である点に注意
（`TreeSearchPlayer` が使っているのと同じ `Battle.copy()` の仕組みを流用している）。

## 出力の見方

学習後、状態ごとの平均戦略（累積戦略の平均。regret matchingは瞬間戦略が
振動しうるため、収束の目安には累積平均を使うのが定石）を一覧表示する。
自分のHPが少ない状態と多い状態で技の選び方に違いが出るかを観察できる。

## 実行時間とサンプル数

`battle.copy()` を伴うフォーク評価を1ターンにつき最大6回（両陣営×3手）行うため、
08よりも重く、手元では数十秒程度かかる。`N_EPISODES` / `HP_BUCKETS` を増やすと
学習は安定するが実行時間も増える。
"""
from __future__ import annotations

from collections import defaultdict

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command

# ---- 対戦相手の構成 ----
# ここを書き換えるだけで、別のポケモン・技3つの読み合いに変更できる
# （MOVES はちょうど3つ指定する。08と同じ制約）
SPECIES_NAME = "エビワラー"
ABILITY_NAME = "てつのこぶし"
NATURE = "いじっぱり"
MOVES = ["マッハパンチ", "はやてがえし", "きあいパンチ"]
EVS = [0, 0, 0, 0, 0, 0]
IVS = [31, 31, 31, 31, 31, 31]

MOVE_COMMANDS = (Command.MOVE_0, Command.MOVE_1, Command.MOVE_2)

# ---- 実行設定 ----
BASE_SEED = 20260323
MAX_TURNS = 10  # 1エピソードあたりの最大ターン数

HP_BUCKETS = 3  # HP割合を何段階に離散化するか。増やすほど状態が細かくなるが学習に必要な試行数も増える
N_EPISODES = 600  # 自己対戦の試行回数。多いほど学習は安定するが実行時間が増える
SHOW_PROGRESS_EVERY = 30  # このエピソード数ごとに進捗を表示する（0で非表示）


def hp_bucket(mon: Pokemon, n_buckets: int = HP_BUCKETS) -> int:
    """HP割合を0〜n_buckets-1の段階に離散化する（大きいほどHPが多い）。

    ターン数は状態に含めない単純化をしている。ターン上限に近いほど
    TOD（Time Over Draw）判定の影響が強くなるが、このサンプルでは
    「HP状況だけを見て手を選ぶ」戦略で十分学習できる範囲に留めている。
    """
    fraction = mon.hp / mon.max_hp
    return min(int(fraction * n_buckets), n_buckets - 1)


def regret_matching_strategy(regret: list[float]) -> tuple[float, float, float]:
    """累積後悔（regret）から regret matching で確率分布を作る。

    正の後悔だけを使い、後悔が大きい手ほど選ばれやすくする
    （Hart & Mas-Colell の regret matching）。後悔が全て0以下
    （学習開始直後や、どの手も互角だった場合）は一様分布にする。
    """
    positive = [max(r, 0.0) for r in regret]
    total = sum(positive)
    if total <= 0:
        return (1 / 3, 1 / 3, 1 / 3)
    return tuple(p / total for p in positive)  # type: ignore[return-value]


def sample_command(strategy: tuple[float, float, float], rng) -> Command:
    """確率分布に従って技コマンドを1つサンプルする。"""
    r = rng.random()
    p0, p1, _p2 = strategy
    if r < p0:
        return MOVE_COMMANDS[0]
    if r < p0 + p1:
        return MOVE_COMMANDS[1]
    return MOVE_COMMANDS[2]


def add_vec(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def build_pokemon() -> Pokemon:
    """「対戦相手の構成」から対戦用ポケモンを1体構築する。"""
    mon = Pokemon(SPECIES_NAME, ability_name=ABILITY_NAME, nature=NATURE, move_names=MOVES)
    mon.set_evs(EVS)
    mon.set_ivs(IVS, hp_policy="reset")  # 新規構築なので満タンにする
    return mon


class CFRMovePlayer(Player):
    """現在のHP状況（information set）に応じた戦略テーブルから技を選ぶプレイヤー。

    `regrets` は学習中に更新され続ける辞書で、複数のプレイヤーインスタンス・
    複数のエピソードにまたがって共有される（自己対戦なので、両陣営が
    同じ「状態→戦略」テーブルを参照・更新する）。
    """

    def __init__(self, regrets: dict[tuple[int, int], list[float]], username: str = ""):
        super().__init__(username)
        self.regrets = regrets

    def info_set(self, battle: Battle) -> tuple[int, int]:
        own = battle.get_active(self)
        opponent = battle.get_active(battle.opponent(self))
        return (hp_bucket(own), hp_bucket(opponent))

    def choose_command(self, battle: Battle) -> Command:
        strategy = regret_matching_strategy(self.regrets[self.info_set(battle)])
        return sample_command(strategy, battle.decision_random)


def result_point(battle: Battle, p0: Player, p1: Player) -> float:
    """決着済みのバトルから、p0視点のポイント（1.0/0.5/0.0）を求める。"""
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


def rollout_value(battle: Battle,
                   p0: Player,
                   p1: Player,
                   cmd0: Command,
                   cmd1: Command,
                   max_turns: int) -> float:
    """盤面を複製し、今ターンに (cmd0, cmd1) を強制した後、以降は現在の
    戦略テーブル（choose_command）に従って決着まで進め、p0視点のポイントを返す。

    `Battle.copy()` は `TreeSearchPlayer` の探索と同じ仕組みで、Player
    インスタンス（p0, p1）自体は複製されず元のオブジェクトと共有される
    （盤面・ポケモンの状態だけが複製される）。そのため複製後の盤面
    （fork）に対しても `fork.step({p0: cmd0, p1: cmd1})` のように元の
    p0/p1 をそのままキーに使える。
    """
    fork = battle.copy(reseed=True)
    fork.step({p0: cmd0, p1: cmd1})
    while fork.judge_winner() is None and fork.turn <= max_turns:
        fork.step()  # 以降は両者ともchoose_command()（現在の戦略テーブル）に従う
    return result_point(fork, p0, p1)


def play_training_episode(regrets: dict[tuple[int, int], list[float]],
                          strategy_sums: dict[tuple[int, int], tuple[float, float, float]],
                          visit_counts: dict[tuple[int, int], int],
                          seed: int,
                          max_turns: int) -> float:
    """1エピソード分の自己対戦を行い、regrets/strategy_sums/visit_countsを更新する。

    Returns:
        p0視点のポイント（1.0/0.5/0.0）。
    """
    p0 = CFRMovePlayer(regrets, username="p0")
    p1 = CFRMovePlayer(regrets, username="p1")
    p0.team.append(build_pokemon())
    p1.team.append(build_pokemon())

    battle = Battle(p0, p1, seed=seed)
    battle.test_option.accuracy = 100  # 命中率のブレを消し、技選択の駆け引きだけを見る
    battle.start()  # Turn 0: 初期繰り出し

    while battle.judge_winner() is None and battle.turn <= max_turns:
        info0 = p0.info_set(battle)
        info1 = p1.info_set(battle)

        strategy0 = regret_matching_strategy(regrets[info0])
        strategy1 = regret_matching_strategy(regrets[info1])
        strategy_sums[info0] = add_vec(strategy_sums[info0], strategy0)
        strategy_sums[info1] = add_vec(strategy_sums[info1], strategy1)
        visit_counts[info0] += 1
        visit_counts[info1] += 1

        actual_cmd0 = sample_command(strategy0, battle.decision_random)
        actual_cmd1 = sample_command(strategy1, battle.decision_random)

        # p0の反実仮想価値: p1の手は実際にサンプルされた手に固定し、p0の3手を評価する
        values0 = [
            rollout_value(battle, p0, p1, cmd, actual_cmd1, max_turns)
            for cmd in MOVE_COMMANDS
        ]
        baseline0 = sum(s * v for s, v in zip(strategy0, values0))
        for i in range(3):
            regrets[info0][i] += values0[i] - baseline0

        # p1の反実仮想価値: p0の手を固定し、p1の3手を評価する（p1視点 = 1 - p0視点）
        values1 = [
            1.0 - rollout_value(battle, p0, p1, actual_cmd0, cmd, max_turns)
            for cmd in MOVE_COMMANDS
        ]
        baseline1 = sum(s * v for s, v in zip(strategy1, values1))
        for i in range(3):
            regrets[info1][i] += values1[i] - baseline1

        # フォークとは別に、実際に選んだ手でこのターンを1つ進める
        battle.step({p0: actual_cmd0, p1: actual_cmd1})

    return result_point(battle, p0, p1)


def strategy_text(probs: tuple[float, float, float]) -> str:
    return ", ".join(f"{m}:{p:.3f}" for m, p in zip(MOVES, probs))


def main() -> None:
    """スクリプト本体。設定値はファイル先頭の「実行設定」を編集して調整する。"""
    regrets: dict[tuple[int, int], list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    strategy_sums: dict[tuple[int, int], tuple[float, float, float]] = defaultdict(lambda: (0.0, 0.0, 0.0))
    visit_counts: dict[tuple[int, int], int] = defaultdict(int)

    print(f"=== {SPECIES_NAME} Janken CFR-style Self-play ({'/'.join(MOVES)}) ===")
    print(f"episodes={N_EPISODES}, hp_buckets={HP_BUCKETS}, max_turns={MAX_TURNS}")

    row_wins = 0.0
    for i in range(N_EPISODES):
        point = play_training_episode(
            regrets, strategy_sums, visit_counts,
            seed=BASE_SEED + i, max_turns=MAX_TURNS,
        )
        row_wins += point
        if SHOW_PROGRESS_EVERY and (i + 1) % SHOW_PROGRESS_EVERY == 0:
            print(f"episode={i + 1:03d}  p0 win rate so far={row_wins / (i + 1):.3f}")

    print("-" * 60)
    print("状態別の平均戦略（自分HP割合バケット, 相手HP割合バケット）:")
    for info in sorted(visit_counts):
        own_bucket, opp_bucket = info
        n = visit_counts[info]
        avg = tuple(s / n for s in strategy_sums[info])
        print(f"  own={own_bucket} opp={opp_bucket} (訪問{n:4d}回): {strategy_text(avg)}")

    # 試してみよう:
    # * HP_BUCKETS を増やす、または状態にターン数を加えると、より細かい読み合いを
    #   学習できるが、その分エピソード数(N_EPISODES)を増やさないと学習が安定しない
    # * 08_janken_nash_fictitious_play.py の固定混合戦略の結果と比較し、「own（自分HP）が
    #   少ない状態だけ特定の技に偏る」といった適応的な傾向が出ているか観察する
    # * rollout_value() の呼び出しを毎回1回ではなく複数回平均するようにすると、
    #   反実仮想価値の推定分散が減り学習が安定するが、実行時間は増える


if __name__ == "__main__":
    main()
