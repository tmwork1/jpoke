import math
from jpoke.core.event import Event, EventContext
from jpoke import Pokemon
import test_utils as t


def test_poison_turn_end_damage():
    """どく: ターン終了時ダメージ"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "どく")
    battle.advance_turn()
    battle.print_logs()
    # 最大HPの1/8のダメージを受けているはず
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 8, f"どく: ターン終了時ダメージ: {damage} != {mon.max_hp // 8}"


def test_badly_poison_damage_increase():
    """もうどく: ターン経過でダメージ増加"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "もうどく")

    # nターン目: n/16ダメージ
    for i in range(3):
        hp_before = mon.hp
        battle.advance_turn()
        battle.print_logs()
        damage = hp_before - mon.hp
        expected = mon.max_hp * (i + 1) // 16
        assert damage == expected, f"もうどく {i+1}ターン目: {damage=} != {expected=}"
        assert mon.ailment.count == i + 1, f"もうどくカウント: {mon.ailment.count=} != {i+1}"


def test_paralysis_speed_reduction():
    """まひ: 素早さ半減"""
    battle = t.start_battle(ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    # まひ前の素早さを記録
    normal_speed = battle.calc_effective_speed(mon)
    # まひ状態にする
    mon.apply_ailment(battle.events, "まひ")
    paralyzed_speed = battle.calc_effective_speed(mon)
    # 素早さが半減していることを確認
    assert paralyzed_speed == normal_speed // 2, f"まひ: 素早さ半減: Expected {normal_speed // 2}, got {paralyzed_speed}"


def test_paralysis_action_disabled_high_rate():
    """まひ: 行動不能"""
    battle = t.start_battle(ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "まひ")
    # 必ず行動不能になる設定
    battle.test_option.ailment_trigger_rate = 1.0
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(target=mon), None)
    # HandlerReturnがFalseを返すことを確認（行動不能）
    assert not result, "まひ: 行動不能（trigger_rate=1.0）"


def test_paralysis_action_enabled_low_rate():
    """まひ: 行動可能"""
    battle = t.start_battle(ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "まひ")

    # 必ず行動できる設定
    battle.test_option.ailment_trigger_rate = 0.0
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(target=mon), None)
    # 行動可能であることを確認
    assert result, "まひ: 行動可能"

def test_burn_physical_move_damage_reduction():
    """やけど: 物理技ダメージ半減"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")]
    )

    attacker = battle.actives[0]
    defender = battle.actives[1]

    # やけど状態なしでのダメージを記録
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
    assert burned_modifier == expected_modifier, f"やけど: 物理技ダメージ半減: {burned_modifier} != {expected_modifier}"


def test_burn_special_move_no_damage_change():
    """やけど: 特殊技ダメージは変わらず"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")]
    )

    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]  # 10まんボルト（特殊技）

    # やけど状態にする
    attacker.apply_ailment(battle.events, "やけど")

    # 特殊技のやけど補正値（やけどあり）
    burned_modifier = battle.events.emit(
        Event.ON_CALC_BURN_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move),
        4096
    )

    # 特殊技なので補正は変わらない（4096のまま）
    assert burned_modifier == 4096, f"やけど: 特殊技ダメージ変わらず: {burned_modifier} != 4096"


def test_sleep_application():
    """ねむり: 状態適用"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    # ねむり状態にする（カウント3で設定）
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "ねむり")
    mon.ailment.count = 3

    assert mon.ailment.name == "ねむり", "ねむり: 状態適用失敗"
    assert mon.ailment.count == 3, "ねむり: カウント設定失敗"


def test_sleep_turn_progression_recovery():
    """ねむり: ターン経過で回復"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "ねむり")
    mon.ailment.count = 2  # 2ターンで回復

    # 1ターン目: count 2 → 1
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(target=mon), None)
    assert mon.ailment.name == "ねむり", "ねむり: 1ターン目でもまだねむり状態のはず"
    assert mon.ailment.count == 1, f"ねむり: 1ターン目カウント1のはず: {mon.ailment.count}"

    # 2ターン目: count 1 → 0 で回復
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(target=mon), None)
    assert mon.ailment.name == "", "ねむり: 2ターン目で回復するはず"


def test_burn_turn_end_damage():
    """やけど: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン")],  # HP高めのポケモンでテスト
    )

    mon = battle.actives[0]
    initial_hp = mon.hp
    mon.apply_ailment(battle.events, "やけど")

    # ターン終了時イベントを発火
    battle.events.emit(Event.ON_TURN_END_3, EventContext(target=mon), None)

    # 最大HPの1/16のダメージを受けているはず
    expected_damage = mon.max_hp // 16
    actual_damage = initial_hp - mon.hp
    assert actual_damage == expected_damage, f"やけど: ターン終了時ダメージ: {actual_damage} != {expected_damage}"


def test_freeze_application():
    """こおり: 状態適用"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    # こおり状態にする（apply_ailmentを使用）
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "こおり")
    assert mon.ailment.name == "こおり", "こおり: 状態適用失敗"


def test_freeze_thaw_high_rate():
    """こおり: 解凍（確率テスト - trigger_rate=1.0）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    # こおり状態にする
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "こおり")

    # 必ず解凍される設定でテスト
    battle.test_option.ailment_trigger_rate = 1.0
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(target=mon), None)
    assert mon.ailment.name == "", "こおり: 解凍失敗（trigger_rate=1.0）"


def test_freeze_persist_low_rate():
    """こおり: 状態維持（確率テスト - trigger_rate=0.0）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    # こおり状況を付与
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "こおり")

    # 解凍されない設定でテスト
    battle.test_option.ailment_trigger_rate = 0.0
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(target=mon), None)
    assert mon.ailment.name == "こおり", "こおり: 状態維持失敗（trigger_rate=0.0）"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
