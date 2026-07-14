# TODO: りゅうせいぐんによるC低下のほうが実践的で、例としてはより適切
"""jpoke で学べること: calc_lethal(secondary=True) による追加効果込みの確定数計算。

calc_lethal(secondary=True) は技本体の追加効果（状態異常付与等）のうち、致死率計算に
組み込まれている技に限り自動的に加味する（かえんほうしゃのやけど等、組み込まれて
いない技もある）。キラースピン（どく付与）は組み込み済みで、secondary=Trueにすると
付与されたどくの毎ターンダメージ分だけ確定数が早まる。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    poison_move = "キラースピン"
    secondary_attacker_player = Player("SecondaryAttacker")
    secondary_attacker_player.add_pokemon("ドクロッグ", move_names=[poison_move])
    secondary_defender_player = Player("SecondaryDefender")
    secondary_defender_player.add_pokemon("フシギダネ")

    secondary_battle = Battle(secondary_attacker_player, secondary_defender_player, seed=1)
    secondary_battle.start()
    secondary_attacker = secondary_battle.get_active(secondary_attacker_player)

    without_secondary = secondary_battle.calc_lethal(
        attacker=secondary_attacker, moves=poison_move, max_attack=8, secondary=False,
    )[-1]
    with_secondary = secondary_battle.calc_lethal(
        attacker=secondary_attacker, moves=poison_move, max_attack=8, secondary=True,
    )[-1]
    print(
        f"{poison_move}の確定数: secondary=False → {without_secondary.n_attack}発 / "
        f"secondary=True → {with_secondary.n_attack}発（どくの蓄積ダメージ分早まる）"
    )

    # 試してみよう: poison_move を「かえんほうしゃ」に変えると、secondary=True でも
    # 確定数が変わらないこと（やけど付与が致死率計算に組み込まれていないこと）を確認できる


if __name__ == "__main__":
    main()
