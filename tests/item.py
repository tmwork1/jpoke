import math
from jpoke import Pokemon
from jpoke.utils import test_utils as t


def test():
    print("--- いのちのたま ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="いのちのたま", moves=["たいあたり"])],
        turn=1
    )
    assert battle.actives[0].item.revealed
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 7/8)

    print("--- いのちのたま: 変化技では発動しない ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="いのちのたま", moves=["はねる"])],
        turn=1
    )
    assert not battle.actives[0].item.revealed

    print("--- きれいなぬけがら ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="きれいなぬけがら") for _ in range(2)],
        foe=[Pokemon("ピカチュウ", ability="かげふみ")],
    )
    assert t.can_switch(battle, 0)

    print("--- さらさらいわ ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="さらさらいわ")],
    )
    battle.weather_mgr.activate("すなあらし", 5, source=battle.actives[0])
    assert battle.weather.count == 8

    print("--- だっしゅつパック ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつパック"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.players[0].active_idx != 0
    assert battle.players[0].team[0].item.revealed
    assert not battle.players[0].team[0].item.effect_enabled

    print("--- だっしゅつパック : 能力上昇では発動しない ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつパック", moves=["つるぎのまい"]), Pokemon("ライチュウ")],
        turn=1,
    )
    assert not battle.players[0].team[0].item.revealed

    print("--- だっしゅつボタン ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつボタン"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        turn=1,
    )
    assert battle.players[0].active_idx != 0
    assert battle.players[0].team[0].item.revealed
    assert not battle.players[0].team[0].item.effect_enabled

    print("--- たべのこし ---")
    mon = Pokemon("ピカチュウ", item="たべのこし")
    battle = t.start_battle(ally=[mon], turn=1)
    assert not battle.actives[0].item.revealed
    mon.hp = 1
    battle.advance_turn(print_log=t.PRINT_LOG)
    assert battle.actives[0].item.revealed
    assert battle.actives[0].hp == 1 + mon.max_hp // 16


if __name__ == "__main__":
    test()
