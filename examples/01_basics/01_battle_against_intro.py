"""jpoke で学べること: Player.battle_against() を使った最小構成のバトル実行。

Battle / Player を手動で管理してターンを1つずつ進める方法（02のquickstart）も
当然必要になるが、まずは対戦相手を指定して勝敗だけを見たい場合に一番手軽な
battle_against()（poke-env互換API）から始める。
"""
from __future__ import annotations

from jpoke import Player


def main() -> None:
    player1 = Player("Player 1")
    player1.add_pokemon("ヒトカゲ", move_names=["ひっかく"])

    player2 = Player("Player 2")
    player2.add_pokemon("フシギダネ", move_names=["たいあたり"])

    # seed: 乱数シードを固定し、命中判定・急所判定などを再現可能にする
    player1.battle_against(player2, seed=1)

    print(f"player1: {player1.n_won_battles}勝{player1.n_lost_battles}敗/{player1.n_finished_battles}戦")

    # 試してみよう: n_battles=10 のように指定すると、同じ相手と複数回対戦させて
    # 勝率を見られる（対戦ごとに異なる展開になるようseedが自動的にずらされる）


if __name__ == "__main__":
    main()
