"""jpoke で学べること: Player.battle_against() を使った多数回対戦による構成比較。

同じポケモンでアイテムだけを変えた2つの構成を、共通の対戦相手と多数回戦わせて
勝率を比較する。poke-env 互換 API（battle_against）を使った、戦術研究ユースケース
（構成比較）の入口。
"""
from __future__ import annotations

from jpoke import Player


def build_player(username: str, item_name: str) -> Player:
    """アイテムだけが異なるガブリアスを1体持つプレイヤーを作る。"""
    player = Player(username)
    # add_pokemon() は追加したPokemonインスタンスを返すので、そのまま追加設定に使える
    mon = player.add_pokemon("ガブリアス", item_name=item_name, move_names=["ドラゴンクロー"])
    mon.set_evs([0, 32, 0, 0, 0, 0])
    return player


def build_opponent() -> Player:
    # ドラパルト（素早さ実数値162）はガブリアス（同122）より速いため、こだわりハチマキ
    # （火力+50%、素早さ変化なし）では後攻になるが、こだわりスカーフ（素早さ+50%）なら
    # 先攻を取れる——というアイテムによる素早さ逆転で構成差が勝率に出るようにする
    opponent = Player("Opponent")
    opponent.add_pokemon("ドラパルト", move_names=["げきりん"])
    return opponent


def main() -> None:
    n_battles = 30

    for item_name in ("こだわりスカーフ", "こだわりハチマキ"):
        player = build_player(username=item_name, item_name=item_name)

        # seed を指定すると、battle_against() は対戦ごとに seed+対戦通番の
        # 派生シードを自動的に使う（n_battles 回すべてが同一の展開になるのを防ぐ）
        player.battle_against(build_opponent(), n_battles=n_battles, seed=1)

        print(
            f"{item_name}: {player.n_won_battles}勝{player.n_lost_battles}敗 (勝率 {player.win_rate:.0%})"
        )
        # n_tied_battles はpoke-env互換のため用意されているが、jpokeに引き分けは
        # 存在しないため常に0（n_lost_battles = n_finished_battles - n_won_battles - n_tied_battles）

    # 試してみよう: n_battles を増やして勝率を安定させたり、
    # 比較するアイテム・技の組み合わせを変えてみる


if __name__ == "__main__":
    main()
