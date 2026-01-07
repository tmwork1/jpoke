import math
from jpoke import Pokemon
from jpoke.utils import test_utils


SHOW_LOG = True


def test():
    # いのちのたま
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", item="いのちのたま", moves=["たいあたり"])], turn=1)
    assert battle.actives[0].item.revealed
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 7/8)

    # いのちのたま: 変化技では発動しない
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", item="いのちのたま", moves=["はねる"])], turn=1)
    assert not battle.actives[0].item.revealed

    # きれいなぬけがら
    assert test_utils.check_switch(
        test_utils.generate_battle(
            ally=[Pokemon("ピカチュウ", ability="かげふみ")],
            foe=[Pokemon("ピカチュウ", item="きれいなぬけがら") for _ in range(2)]
        )
    )

    # だっしゅつパック
    battle = test_utils.generate_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつパック"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.players[0].active_idx != 0
    assert battle.players[0].team[0].item.revealed
    assert not battle.players[0].team[0].item.active

    # だっしゅつパック : 能力上昇では発動しない
    battle = test_utils.generate_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつパック", moves=["つるぎのまい"]), Pokemon("ライチュウ")],
        turn=1,
    )
    assert not battle.players[0].team[0].item.revealed

    # だっしゅつボタン
    battle = test_utils.generate_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつボタン"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        turn=1,
    )
    assert battle.players[0].active_idx != 0
    assert battle.players[0].team[0].item.revealed
    assert not battle.players[0].team[0].item.active

    # たべのこし
    mon = Pokemon("ピカチュウ", item="たべのこし")
    battle = test_utils.generate_battle(ally=[mon], turn=1)
    assert not battle.actives[0].item.revealed
    mon.hp = 1
    battle.advance_turn(print_log=test_utils.PRINT_LOG)
    assert battle.actives[0].item.revealed
    assert battle.actives[0].hp == 1 + mon.max_hp // 16


if __name__ == "__main__":
    test()
