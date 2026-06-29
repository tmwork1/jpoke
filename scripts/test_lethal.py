"""
行動選択の方策関数で木探索を行うテスト
"""

from jpoke import Battle, Player, Pokemon, Move


def main(attacker: str,
         defender: str,
         moves: list[str],
         defender_ability: str = "",
         defender_item: str = ""):
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

    battle.calc_lethal(
        attacker=battle.actives[0],
        move=[Move(m) for m in moves],
    )


if __name__ == "__main__":
    # main("ガブリアス", "ブリジュラス", ["ドラゴンテール"], defender_item="")
    # main("ガブリアス", "ブリジュラス", ["ドラゴンテール"], defender_item="たべのこし")
    # main("ガブリアス", "カイリュー", ["ドラゴンテール"], defender_ability="マルチスケイル")
    main("ガブリアス", "カイリュー", ["ドラゴンテール", "ドラゴンクロー"], defender_ability="マルチスケイル")
