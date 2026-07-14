"""calc_lethal(secondary=True) を使って追加効果込みの確定数を計算する。

calc_lethal(secondary=True) は技本体の追加効果（状態異常付与等）のうち、致死率計算に
組み込まれている技に限り自動的に加味する（かえんほうしゃのやけど等、組み込まれて
いない技もある）。キラースピン（どく付与）は組み込み済みで、secondary=Trueにすると
付与されたどくの毎ターンダメージ分だけ確定数が早まる。
"""
from __future__ import annotations

from jpoke import Battle, Player


def show_poison_secondary() -> None:
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


def show_self_stat_drop_is_always_applied() -> None:
    """りゅうせいぐん等の「自身のとくこうを下げる」効果は secondary の対象外。

    calc_lethal(secondary=...) が切り替えるのは、あくまで防御側に対する追加効果
    （どく付与等、発動しなくても攻撃側は損しない効果）。りゅうせいぐんの自傷効果は
    使えば必ず発生し避けようがないため、secondary の指定に関わらず常に加味される
    （calc_lethal(secondary=False) でもとくこうの低下は反映される）。
    """
    move_name = "りゅうせいぐん"
    attacker_player = Player("SelfDropAttacker")
    attacker_player.add_pokemon("ボーマンダ", move_names=[move_name])
    defender_player = Player("SelfDropDefender")
    defender_player.add_pokemon("カビゴン")

    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()
    attacker = battle.get_active(attacker_player)

    without_secondary = battle.calc_lethal(
        attacker=attacker, moves=move_name, max_attack=2, secondary=False,
    )
    with_secondary = battle.calc_lethal(
        attacker=attacker, moves=move_name, max_attack=2, secondary=True,
    )
    print(
        f"{move_name}を2発撃った時点のとくこうランク: "
        f"secondary=False → {without_secondary[-1].attacker.boosts['spa']} / "
        f"secondary=True → {with_secondary[-1].attacker.boosts['spa']}（同じ値になる）"
    )


def main() -> None:
    show_poison_secondary()
    print("-" * 50)
    show_self_stat_drop_is_always_applied()

    # 試してみよう: show_poison_secondary() の poison_move を「かえんほうしゃ」に変えると、
    # secondary=True でも確定数が変わらないこと（やけど付与が致死率計算に組み込まれて
    # いないこと）を確認できる


if __name__ == "__main__":
    main()
