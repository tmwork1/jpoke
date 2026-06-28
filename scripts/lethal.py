"""
行動選択の方策関数で木探索を行うテスト
"""

from jpoke import Battle, Player, Pokemon, Move


def main(attacker_name: str,
         defender_name: str,
         move_name: str):
    # Attacker
    player1 = Player()
    player1.team = [
        Pokemon(attacker_name)
    ]

    player2 = Player(name="RandomPlayer")
    player2.team = [
        Pokemon(defender_name)
    ]

    # バトルを作成・実行
    battle = Battle((player1, player2), n_selected=1)
    battle.start()

    battle.calc_lethal(
        attacker=battle.actives[0],
        move=Move(move_name),
    )


if __name__ == "__main__":
    main("ガブリアス", "ブリジュラス", "ドラゴンテール")
