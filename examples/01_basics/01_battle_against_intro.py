"""Player.battle_against() を使い、最小構成でバトルを実行する。

Battle / Player を直接扱う方法（02以降）も当然必要になるが、まずは対戦相手を
指定して勝敗だけを見たい場合に一番手軽なbattle_against()（poke-env互換API）
から始める。
"""
from __future__ import annotations

from jpoke import Player


def main() -> None:
    player1 = Player("Player 1")
    player1.add_pokemon("ヒトカゲ", move_names=["ひっかく"])

    player2 = Player("Player 2")
    player2.add_pokemon("フシギダネ", move_names=["たいあたり"])

    # seed: 乱数シードを固定し、命中判定・急所判定などを再現可能にする
    # battle_against()は各対戦のBattleを内部で使い捨てるため戻り値はNone。
    # 対戦後のBattleインスタンス自体（ログ等）にアクセスしたい場合は
    # on_battle_end コールバックを渡す（docs/api/README.md の battle_against() 節、
    # 05_benchmark/01_step_time_benchmark.py の進捗表示例を参照）
    player1.battle_against(
        player2, seed=1, on_battle_end=lambda battle: battle.print_logs("all")
    )

    print(f"player1: 勝率{player1.win_rate:.0%}（{player1.n_finished_battles}戦）")

    # 試してみよう: n_battles=10 のように指定すると、同じ相手と複数回対戦させて
    # 勝率を見られる（対戦ごとに異なる展開になるようseedが自動的にずらされる）


if __name__ == "__main__":
    main()
