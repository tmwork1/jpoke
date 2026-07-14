"""battle.calc_lethal() を使った確定数・乱数ダメージの基本的な計算方法を扱う。

01で見た1発分のダメージロールを踏まえ、対戦を進行させずに「この技を何回当てれば
倒せるか」「乱数でダメージ幅はどのくらいか」を複数発分まとめて計算する。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    move_name = "ドラゴンテール"

    attacker_player = Player("Attacker")
    # add_pokemon() の第1引数は Pokemon.__init__ と同じく "name"（"_name" 等のサフィックスは
    # 付いていない）ため、これ以上の引数名短縮は不要。
    # こうげき努力値をChampions形式（0〜32、poke-envの0〜252スケールとは異なる）で最大まで振る
    attacker_player.add_pokemon(
        "ガブリアス", move_names=[move_name], evs={"atk": 32},
    )

    defender_player = Player("Defender")
    defender_player.add_pokemon("カイリュー", ability_name="マルチスケイル")

    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()

    attacker = battle.get_active(attacker_player)
    defender = battle.get_active(defender_player)

    # Pokemon.show() で実数値・性格・特性・持ち物・テラスタイプ・技構成をまとめて確認できる
    attacker.show()

    # moves には技名の文字列 / Move 単体 / (Move, ヒット数) / それらのリストを渡せる
    results = battle.calc_lethal(
        attacker=attacker,
        moves=move_name,
        max_attack=5,  # 最大5回攻撃するまで計算する（確定数が出た時点で打ち切り）
    )

    print(f"Attacker: {attacker.name} A{attacker.stats['atk']}, ability={attacker.ability.name}, item={attacker.item.name}")
    print(f"Defender: {defender.name} H{defender.max_hp}/B{defender.stats['def']}/D{defender.stats['spd']}, ability={defender.ability.name}, item={defender.item.name}")
    print("-" * 50)

    for result in results:
        print(
            f"{result.n_attack}発目: ダメージ {result.min_damage}~{result.max_damage} "
            f"/ 致死率 {result.lethal_probability:.2%}"
        )

    final = results[-1]
    print("-" * 50)
    print(f"{final.n_attack}回攻撃した時点での致死率: {final.lethal_probability:.2%}")

    # 試してみよう: move_name を別の技に変えたり、defender_player のアイテムを
    # 変えたりすると、確定数や致死率がどう変わるか比較できる


if __name__ == "__main__":
    main()
