import math
from jpoke import Pokemon
from jpoke.utils import test_utils


def test():
    # アームハンマー
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", moves=["アームハンマー"])], turn=1)
    assert battle.actives[0].rank["S"] == -1

    # すなあらし
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", moves=["すなあらし"])], turn=1)
    assert battle.field.fields["weather"].name == "すなあらし"

    exit()

    # でんじほう
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", moves=["でんじほう"])],
                                        foe=[Pokemon("フシギバナ")], turn=1)
    assert battle.actives[1].ailment == "まひ"

    # とんぼがえり
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", moves=["とんぼがえり"]) for _ in range(2)], turn=1)
    assert battle.players[0].active_idx != 0

    # わるあがき
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", moves=["わるあがき"])], turn=1)
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 3/4)


if __name__ == "__main__":
    test()
