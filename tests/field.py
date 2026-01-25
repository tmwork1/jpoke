import math
from jpoke import Pokemon
from jpoke.utils import test_utils


SHOW_LOG = True


def test():
    print("--- すなあらし ---")
    battle = test_utils.generate_battle()
    battle.field.activate_weather("すなあらし", 5)
    battle.advance_turn(print_log=SHOW_LOG)
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 15/16)
    assert battle.actives[1].hp == math.ceil(battle.actives[1].max_hp * 15/16)


if __name__ == "__main__":
    test()
