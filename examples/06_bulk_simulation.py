"""jpoke で学べること: Player.battle_against() を使った多数回対戦による構成比較。

同じポケモンでアイテムだけを変えた2つの構成を、共通の対戦相手と多数回戦わせて
勝率を比較する。poke-env 互換 API（battle_against）を使った、戦術研究ユースケース
（構成比較）の入口。
"""
from __future__ import annotations

from jpoke import Player, Pokemon


def build_player(username: str, item_name: str) -> Player:
    """アイテムだけが異なるガブリアスを1体持つプレイヤーを作る。"""
    player = Player(username)
    player.team.append(
        Pokemon("ガブリアス", item_name=item_name, move_names=["ドラゴンクロー"])
    )
    return player


def build_opponent() -> Player:
    # ドラパルト（素早さ実数値162）はガブリアス（同122）より速いため、
    # こだわりハチマキ（火力+50%、素早さ変化なし）では後攻になり先制攻撃を受けるが、
    # こだわりスカーフ（素早さ+50%、実数値183）なら先攻を取れる
    # ——という素早さ逆転がアイテムで起きる組み合わせにして、構成差が勝率に出るようにする
    opponent = Player("Opponent")
    opponent.team.append(Pokemon("ドラパルト", move_names=["げきりん"]))
    return opponent


def main() -> None:
    n_battles = 30

    for item_name in ("こだわりスカーフ", "こだわりハチマキ"):
        player = build_player(item_name, item_name)

        # 注意: Battle は seed 省略時 int(time.time())（秒単位）を既定値として使う。
        # そのため battle_against(..., n_battles=N) を seed 指定なしで1回呼ぶと、
        # 短時間に実行される N 回の対戦がすべて同一 seed になり、まったく同じ対戦の
        # 繰り返しになってしまう（勝率が 0% か 100% にしかならない）。
        # ここでは対戦ごとに異なる seed を明示的に指定し、n_battles=1 の
        # battle_against() 呼び出しを繰り返すことで、統計的に意味のある勝率を得る。
        for seed in range(n_battles):
            player.battle_against(build_opponent(), n_battles=1, n_selected=1, seed=seed)

        print(
            f"{item_name}: {player.n_won_battles}/{player.n_finished_battles} 勝"
            f"（勝率 {player.win_rate:.1%}）"
        )


if __name__ == "__main__":
    main()
