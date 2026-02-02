from jpoke import Pokemon
import test_utils as t


def test():
    print("--- めんえき: どく・もうどくを防ぐ ---")
    battle = t.start_battle(
        ally=[Pokemon("ゴクリン", ability="めんえき")]
    )
    assert not battle.actives[0].apply_ailment(battle.events, "どく")
    assert not battle.actives[0].ailment.is_active
    assert not battle.actives[0].apply_ailment(battle.events, "もうどく")
    assert not battle.actives[0].ailment.is_active
    # 他の状態異常は防がない
    assert battle.actives[0].apply_ailment(battle.events, "まひ")
    assert battle.actives[0].ailment.is_active

    print("--- ふみん: ねむりを防ぐ ---")
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", ability="ふみん")]
    )
    assert not battle.actives[0].apply_ailment(battle.events, "ねむり")
    assert not battle.actives[0].ailment.is_active
    # 他の状態異常は防がない
    assert battle.actives[0].apply_ailment(battle.events, "まひ")
    assert battle.actives[0].ailment.is_active

    print("--- やるき: ねむりを防ぐ ---")
    battle = t.start_battle(
        ally=[Pokemon("デリバード", ability="やるき")]
    )
    assert not battle.actives[0].apply_ailment(battle.events, "ねむり")
    assert not battle.actives[0].ailment.is_active

    print("--- じゅうなん: まひを防ぐ ---")
    battle = t.start_battle(
        ally=[Pokemon("マダツボミ", ability="じゅうなん")]
    )
    assert not battle.actives[0].apply_ailment(battle.events, "まひ")
    assert not battle.actives[0].ailment.is_active

    print("--- みずのベール: やけどを防ぐ ---")
    battle = t.start_battle(
        ally=[Pokemon("ギャラドス", ability="みずのベール")]
    )
    assert not battle.actives[0].apply_ailment(battle.events, "やけど")
    assert not battle.actives[0].ailment.is_active

    print("--- マグマのよろい: こおりを防ぐ ---")
    battle = t.start_battle(
        ally=[Pokemon("マグカルゴ", ability="マグマのよろい")]
    )
    assert not battle.actives[0].apply_ailment(battle.events, "こおり")
    assert not battle.actives[0].ailment.is_active


if __name__ == "__main__":
    test()
    print("\n✅ すべてのテストが成功しました！")
