from jpoke import Pokemon
from jpoke.utils import test_utils


def test():
    # ニュートラル
    assert test_utils.check_switch(
        test_utils.generate_battle(
            foe=[Pokemon("ピカチュウ") for _ in range(2)]
        )
    )
    # ありじごく
    assert not test_utils.check_switch(
        test_utils.generate_battle(
            ally=[Pokemon("ピカチュウ", ability="ありじごく")],
            foe=[Pokemon("ピカチュウ") for _ in range(2)]
        )
    )
    # ありじごく: 飛行タイプに無効
    assert test_utils.check_switch(
        test_utils.generate_battle(
            ally=[Pokemon("ピカチュウ", ability="ありじごく")],
            foe=[Pokemon("リザードン") for _ in range(2)]
        )
    )
    # ありじごく: ゴーストタイプには無効
    assert test_utils.check_switch(
        test_utils.generate_battle(
            ally=[Pokemon("ピカチュウ", ability="ありじごく")],
            foe=[Pokemon("ゲンガー") for _ in range(2)]
        )
    )

    # かげふみ
    assert not test_utils.check_switch(
        test_utils.generate_battle(
            ally=[Pokemon("ピカチュウ", ability="かげふみ")],
            foe=[Pokemon("ピカチュウ") for _ in range(2)]
        )
    )
    # かげふみ: かげふみ相手には無効
    assert test_utils.check_switch(
        test_utils.generate_battle(
            ally=[Pokemon("ピカチュウ", ability="かげふみ")],
            foe=[Pokemon("ピカチュウ", ability="かげふみ") for _ in range(2)]
        )
    )

    # じりょく
    assert not test_utils.check_switch(
        test_utils.generate_battle(
            ally=[Pokemon("ピカチュウ", ability="じりょく")],
            foe=[Pokemon("ハッサム") for _ in range(2)]
        )
    )
    # じりょく: はがねタイプ以外には無効
    assert test_utils.check_switch(
        test_utils.generate_battle(
            ally=[Pokemon("ピカチュウ", ability="じりょく")],
            foe=[Pokemon("ピカチュウ") for _ in range(2)]
        )
    )

    # いかく
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", ability="いかく")])
    assert battle.actives[0].ability.revealed
    assert battle.actives[1].rank["A"] == -1

    # かちき
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", ability="かちき")])
    battle.modify_stat(battle.actives[0], "A", -1, by_foe=True)
    assert battle.actives[0].ability.revealed
    assert battle.actives[0].rank["C"] == 2

    # かちき: 相手による能力ダウンでなければ発動しない
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", ability="かちき")])
    battle.modify_stat(battle.actives[0], "A", -1, by_foe=False)
    assert not battle.actives[0].ability.revealed
    assert battle.actives[0].rank["C"] == 0

    # かちき: 相手のいかくにより発動
    battle = test_utils.generate_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ", ability="いかく")]
    )
    assert battle.actives[0].ability.revealed

    # きんちょうかん
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", ability="きんちょうかん")])
    assert battle.actives[0].ability.revealed
    assert battle.actives[1].nervous(battle.events)
    assert not battle.actives[0].nervous(battle.events)

    # ぜったいねむり
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", ability="ぜったいねむり")])
    assert battle.actives[0].ability.revealed
    assert battle.actives[0].ailment == "ねむり"

    # グラスメイカー
    battle = test_utils.generate_battle(ally=[Pokemon("ピカチュウ", ability="グラスメイカー")])
    assert battle.actives[0].ability.revealed
    assert battle.field.fields["terrain"] == "グラスフィールド"


if __name__ == "__main__":
    test()
