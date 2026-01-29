from jpoke import Pokemon
from jpoke.utils import test_utils as t


def test():
    print("--- ニュートラル ---")
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ") for _ in range(2)]
    )
    assert t.can_switch(battle, 1)

    print("--- ありじごく ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ありじごく")],
        foe=[Pokemon("ピカチュウ") for _ in range(2)]
    )
    assert not t.can_switch(battle, 1)

    print("--- ありじごく: 飛行タイプに無効 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ありじごく")],
        foe=[Pokemon("リザードン") for _ in range(2)]
    )
    assert t.can_switch(battle, 1)

    print("--- ありじごく: ゴーストタイプには無効 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ありじごく")],
        foe=[Pokemon("ゲンガー") for _ in range(2)]
    )
    assert t.can_switch(battle, 1)

    print("--- かげふみ ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かげふみ")],
        foe=[Pokemon("ピカチュウ") for _ in range(2)]
    )
    assert not t.can_switch(battle, 1)

    print("--- かげふみ: かげふみ相手には無効 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かげふみ")],
        foe=[Pokemon("ピカチュウ", ability="かげふみ") for _ in range(2)]
    )
    assert t.can_switch(battle, 1)

    print("--- じりょく ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じりょく")],
        foe=[Pokemon("ハッサム") for _ in range(2)]
    )
    assert not t.can_switch(battle, 1)

    print("--- じりょく: はがねタイプ以外には無効 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じりょく")],
        foe=[Pokemon("ピカチュウ") for _ in range(2)]
    )
    assert t.can_switch(battle, 1)

    print("--- いかく ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いかく")]
    )
    assert battle.actives[0].ability.revealed
    assert battle.actives[1].rank["A"] == -1

    print("--- かちき ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")]
    )
    battle.modify_stat(battle.actives[0], "S", -1, source=battle.actives[1])
    assert battle.actives[0].ability.revealed
    assert battle.actives[0].rank["C"] == 2

    print("--- かちき: 自分による能力ダウンでは発動しない ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")]
    )
    battle.modify_stat(battle.actives[0], "A", -1, source=battle.actives[0])
    assert not battle.actives[0].ability.revealed

    print("--- かちき: 相手のいかくにより発動 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ", ability="いかく")]
    )
    assert battle.actives[0].ability.revealed

    print("--- きんちょうかん ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きんちょうかん")]
    )
    assert battle.actives[0].ability.revealed
    assert battle.actives[1].is_nervous(battle.events)
    assert not battle.actives[0].is_nervous(battle.events)

    print("--- グラスメイカー ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="グラスメイカー")]
    )
    assert battle.actives[0].ability.revealed
    assert battle.terrain == "グラスフィールド"
    assert battle.terrain.count == 5

    print("--- ぜったいねむり ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぜったいねむり")]
    )
    assert battle.actives[0].ability.revealed
    assert battle.actives[0].ailment == "ねむり"


if __name__ == "__main__":
    test()
