import math
from jpoke import Pokemon
import test_utils as t


def test():
    print("--- やどりぎのタネ ---")
    battle = t.start_battle(
        turn=1,
        ally_volatile={"やどりぎのタネ": 1},
    )
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 7/8)


if __name__ == "__main__":
    test()
