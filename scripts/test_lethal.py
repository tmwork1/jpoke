"""
行動選択の方策関数で木探索を行うテスト
"""

from jpoke import Battle, Player, Pokemon, Move
from jpoke.utils.type_defs import VolatileName


def main(attacker: str,
         defender: str,
         moves: list[tuple[str, int]],
         defender_ability: str = "",
         defender_item: str = "",
         defender_volatiles: dict[VolatileName, int] | None = None):
    # Attacker
    player1 = Player()
    player1.team = [
        Pokemon(attacker)
    ]

    player2 = Player(name="RandomPlayer")
    player2.team = [
        Pokemon(defender, ability_name=defender_ability, item_name=defender_item)
    ]

    # バトルを作成・実行
    battle = Battle((player1, player2), n_selected=1)
    battle.start()

    results = battle.calc_lethal(
        attacker=battle.actives[0],
        moves=[(Move(m), v) for m, v in moves],
    )
    result = results[-1]

    attacker_mon = player1.team[0]
    defender_mon = player2.team[0]

    print(f"Attacker: {attacker_mon.name}")
    print(f"Defender: {defender_mon.name} HP={defender_mon.max_hp}")
    print(f"Damages: {result.min_damage}~{result.max_damage}")
    print(f"Lethal count: {result.n_attack}")
    print(f"Lethal probability: {result.lethal_probability: .2%}")


if __name__ == "__main__":
    # main("ガブリアス", "カイリュー", [("ドラゴンテール", 1)])
    main("ガブリアス", "カイリュー", [("ドラゴンテール", 1)], defender_item="オボンのみ")  # 乱2 (5.9%)
    # main("ガブリアス", "カイリュー", [("ドラゴンテール", 1)], defender_ability="マルチスケイル")
    # main("ガブリアス", "カイリュー", [("ドラゴンテール",1), ("ドラゴンクロー",1)], defender_ability="マルチスケイル")
    # main("ガブリアス", "カイリュー", [("スケイルショット", 4)], defender_ability="マルチスケイル")
    # main("ガブリアス", "カイリュー", [("スケイルショット", 4)], defender_ability="マルチスケイル")
