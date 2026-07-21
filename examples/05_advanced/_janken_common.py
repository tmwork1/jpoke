"""03_janken_nash_fictitious_play.py と 04_janken_nash_cfr.py の共通ヘルパー。

両スクリプトは同じ「1体・技3つのじゃんけん」を題材にした異なる均衡近似アルゴリズムを
扱うため、対戦セットアップ・結果判定まわりのロジックが重複していた。本モジュールに
切り出すことで、片方だけ修正して両者の挙動がずれるリスクを防ぐ。単独では実行しない。
"""
from dataclasses import dataclass

from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command

MOVE_COMMANDS = (Command.MOVE_0, Command.MOVE_1, Command.MOVE_2)


@dataclass(frozen=True)
class Matchup:
    """対戦相手の構成（1体・技3つ、ちょうど3つである必要がある）。"""

    species_name: str
    ability_name: str
    nature: str
    moves: list[str]
    evs: list[int]
    ivs: list[int]

    def add_team_pokemon(self, player: Player) -> Pokemon:
        """`player` のチームにこの構成のポケモンを1体追加する。

        `Player.add_pokemon()` が jpoke の正規の追加ルート（`team.append(Pokemon(...))`
        を使わない）。努力値・個体値は `add_pokemon()` の引数に無いため、返された
        インスタンスに対して追加で設定する。
        """
        mon = player.add_pokemon(
            name=self.species_name, ability=self.ability_name,
            nature=self.nature, moves=self.moves,
        )
        mon.set_evs(self.evs)
        mon.set_ivs(self.ivs, hp_policy="reset")  # 新規構築なので満タンにする
        return mon

    def strategy_text(self, probs: tuple[float, float, float]) -> str:
        return ", ".join(f"{m}:{p:.3f}" for m, p in zip(self.moves, probs))


def add_vec(
    a: tuple[float, float, float], b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def result_point(battle: Battle, p0: Player, p1: Player) -> float:
    """決着済みのバトルから、p0視点のポイントを返す。

    Returns:
        1.0: p0勝利 / 0.5: 引き分け（ターン上限に達し、TOD（Time Over Draw）判定でも
        互角） / 0.0: p1勝利
    """
    winner = battle.winner
    if winner is p0:
        return 1.0
    if winner is p1:
        return 0.0

    score0 = battle.calc_tod_score(p0)
    score1 = battle.calc_tod_score(p1)
    if abs(score0 - score1) < 1e-9:
        return 0.5
    return 1.0 if score0 > score1 else 0.0
