import math
from jpoke import Pokemon
import test_utils as t


def test():
    print("--- すなあらし ---")
    battle = t.start_battle(
        weather="すなあらし",
        turn=1,
    )
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 15/16)
    assert battle.actives[1].hp == math.ceil(battle.actives[1].max_hp * 15/16)

    print("--- すなあらし: いわタイプはダメージを受けない ---")
    battle = t.start_battle(
        ally=[Pokemon("イシツブテ")],
        weather="すなあらし",
        turn=1,
    )
    assert battle.actives[0].hp == battle.actives[0].max_hp

    print("--- すなあらし: 特性でダメージを受けない ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すなかき")],
        weather="すなあらし",
        turn=1,
    )
    assert battle.actives[0].hp == battle.actives[0].max_hp


if __name__ == "__main__":
    test()
