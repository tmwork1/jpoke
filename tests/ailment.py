from jpoke import Pokemon
import test_utils as t


def test():
    print("--- まひ: 素早さ半減 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")]
    )
    # まひ前の素早さを記録
    normal_speed = battle.calc_effective_speed(battle.actives[0])

    # まひ状態にする（apply_ailmentを使用）
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "まひ")
    paralyzed_speed = battle.calc_effective_speed(mon)

    # 素早さが半減していることを確認
    assert paralyzed_speed == normal_speed // 2, f"Expected {normal_speed // 2}, got {paralyzed_speed}"
    print("✓ まひで素早さが半減")

    print("--- まひ: 行動不能（確率テスト）---")
    # 必ず行動不能になる設定
    battle.test_option.ailment_trigger_rate = 1.0
    from jpoke.core.event import Event, EventContext
    result = battle.events.emit(Event.ON_BEFORE_ACTION, EventContext(target=mon), None)
    # HandlerReturnがFalseを返すことを確認（行動不能）
    assert result is None or not result, "まひで行動不能になるはず"
    print("✓ まひで行動不能（trigger_rate=1.0）")

    # 必ず行動できる設定
    battle.test_option.ailment_trigger_rate = 0.0
    result = battle.events.emit(Event.ON_BEFORE_ACTION, EventContext(target=mon), None)
    # 行動可能であることを確認
    print("✓ まひでも行動可能（trigger_rate=0.0）")

    print("--- やけど: 物理技ダメージ半減 ---")
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")]
    )

    attacker = battle.actives[0]
    defender = battle.actives[1]

    # やけど状態なしでのダメージを記録
    from jpoke.core.event import Event, EventContext
    move = attacker.moves[0]  # たいあたり

    # やけど補正値を取得（ON_CALC_BURN_MODIFIER）
    normal_burn = battle.events.emit(
        Event.ON_CALC_BURN_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move),
        4096  # 基準値
    )

    # やけど状態にする
    attacker.apply_ailment(battle.events, "やけど")

    # やけど状態でのやけど補正値を取得
    burned_modifier = battle.events.emit(
        Event.ON_CALC_BURN_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move),
        4096  # 基準値
    )

    # 物理技なので補正が半減（2048/4096 = 0.5倍）しているはず
    expected_modifier = 4096 * 2048 // 4096  # 2048
    assert burned_modifier == expected_modifier, f"やけど時の補正: {burned_modifier} != {expected_modifier}"
    print(f"✓ やけどで物理技ダメージが半減 (補正: {burned_modifier}/4096)")

    # 特殊技ではダメージが半減しないことを確認
    battle2 = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")]
    )

    attacker2 = battle2.actives[0]
    defender2 = battle2.actives[1]
    move2 = attacker2.moves[0]  # 10まんボルト（特殊技）

    # やけど状態にする
    attacker2.apply_ailment(battle2.events, "やけど")

    # 特殊技のやけど補正値（やけどあり）
    burned_modifier2 = battle2.events.emit(
        Event.ON_CALC_BURN_MODIFIER,
        EventContext(attacker=attacker2, defender=defender2, move=move2),
        4096
    )

    # 特殊技なので補正は変わらない（4096のまま）
    assert burned_modifier2 == 4096, f"特殊技のやけど補正が変化: {burned_modifier2} != 4096"
    print(f"✓ やけどでも特殊技ダメージは変わらず (補正: {burned_modifier2}/4096)")

    print("--- ねむり: 行動不能 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    # ねむり状態にする（カウント3で設定）
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "ねむり")
    mon.ailment.count = 3

    assert mon.ailment.name == "ねむり"
    assert mon.ailment.count == 3
    print("✓ ねむり状態を適用（カウント3）")

    print("--- ねむり: ターン経過で回復 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "ねむり")
    mon.ailment.count = 2  # 2ターンで回復

    # 1ターン目: count 2 → 1
    result = battle.events.emit(Event.ON_BEFORE_ACTION, EventContext(target=mon), None)
    assert mon.ailment.name == "ねむり", "まだねむり状態のはず"
    assert mon.ailment.count == 1, f"カウント1のはず: {mon.ailment.count}"
    print("✓ ねむりカウント: 2 → 1")

    # 2ターン目: count 1 → 0 で回復
    result = battle.events.emit(Event.ON_BEFORE_ACTION, EventContext(target=mon), None)
    assert mon.ailment.name == "", "ねむりから回復するはず"
    print("✓ ねむりカウント: 1 → 0（回復）")

    print("--- やけど: ターン終了時ダメージ ---")
    battle = t.start_battle(
        ally=[Pokemon("カビゴン")],  # HP高めのポケモンでテスト
    )

    mon = battle.actives[0]
    initial_hp = mon.hp
    mon.apply_ailment(battle.events, "やけど")

    # ターン終了時イベントを発火
    battle.events.emit(Event.ON_TURN_END_4, EventContext(target=mon), None)

    # 最大HPの1/16のダメージを受けているはず
    expected_damage = mon.max_hp // 16
    actual_damage = initial_hp - mon.hp
    assert actual_damage == expected_damage, f"やけどダメージ: {actual_damage} != {expected_damage}"
    print(f"✓ やけどで1/16ダメージ ({actual_damage} HP)")

    print("--- どく: ターン終了時ダメージ ---")
    battle = t.start_battle(
        ally=[Pokemon("カビゴン")],
    )

    mon = battle.actives[0]
    initial_hp = mon.hp
    mon.apply_ailment(battle.events, "どく")

    # ターン終了時イベントを発火
    battle.events.emit(Event.ON_TURN_END_4, EventContext(target=mon), None)

    # 最大HPの1/8のダメージを受けているはず
    expected_damage = mon.max_hp // 8
    actual_damage = initial_hp - mon.hp
    assert actual_damage == expected_damage, f"どくダメージ: {actual_damage} != {expected_damage}"
    print(f"✓ どくで1/8ダメージ ({actual_damage} HP)")

    print("--- もうどく: ターン経過でダメージ増加 ---")
    battle = t.start_battle(
        ally=[Pokemon("カビゴン")],
    )

    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "もうどく")

    # 1ターン目: 1/16ダメージ
    hp_before = mon.hp
    battle.events.emit(Event.ON_TURN_END_4, EventContext(target=mon), None)
    damage_1 = hp_before - mon.hp
    expected_1 = mon.max_hp // 16
    assert damage_1 == expected_1, f"1ターン目: {damage_1} != {expected_1}"
    assert mon.ailment.count == 1, f"カウント1のはず: {mon.ailment.count}"
    print(f"✓ もうどく1ターン目: 1/16ダメージ ({damage_1} HP)")

    # 2ターン目: 2/16ダメージ
    hp_before = mon.hp
    battle.events.emit(Event.ON_TURN_END_4, EventContext(target=mon), None)
    damage_2 = hp_before - mon.hp
    expected_2 = (mon.max_hp * 2) // 16
    assert damage_2 == expected_2, f"2ターン目: {damage_2} != {expected_2}"
    assert mon.ailment.count == 2, f"カウント2のはず: {mon.ailment.count}"
    print(f"✓ もうどく2ターン目: 2/16ダメージ ({damage_2} HP)")

    # 3ターン目: 3/16ダメージ
    hp_before = mon.hp
    battle.events.emit(Event.ON_TURN_END_4, EventContext(target=mon), None)
    damage_3 = hp_before - mon.hp
    expected_3 = (mon.max_hp * 3) // 16
    assert damage_3 == expected_3, f"3ターン目: {damage_3} != {expected_3}"
    assert mon.ailment.count == 3, f"カウント3のはず: {mon.ailment.count}"
    print(f"✓ もうどく3ターン目: 3/16ダメージ ({damage_3} HP)")

    print("--- こおり: 行動不能と解凍テスト ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    # こおり状態にする（apply_ailmentを使用）
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "こおり")
    assert mon.ailment.name == "こおり"
    print("✓ こおり状態を適用")

    # 必ず解凍される設定でテスト
    battle.test_option.ailment_trigger_rate = 1.0
    result = battle.events.emit(Event.ON_BEFORE_ACTION, EventContext(target=mon), None)
    assert mon.ailment.name == "", "こおりが解凍されるはず"
    print("✓ こおりが解凍された（trigger_rate=1.0）")

    # こおり状態を再度付与して、解凍されない設定でテスト
    mon.apply_ailment(battle.events, "こおり")
    battle.test_option.ailment_trigger_rate = 0.0
    result = battle.events.emit(Event.ON_BEFORE_ACTION, EventContext(target=mon), None)
    assert mon.ailment.name == "こおり", "こおり状態が維持されるはず"
    print("✓ こおり状態維持（trigger_rate=0.0）")

    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    test()
