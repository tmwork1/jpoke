"""状態異常ハンドラの単体テスト"""
import pytest

from jpoke.enums import Event
from jpoke.core import BattleContext
from jpoke.model import Pokemon

import test_utils as t


def test_poison_turn_end_damage():
    """どく: ターン終了時ダメージ"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle, "どく")
    battle.events.emit(Event.ON_TURN_END_3)
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 8, "Poison damage is incorrect"


def test_badly_poison_damage_increase():
    """もうどく: ターン経過でダメージ増加"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle, "もうどく")
    # nターン目: n/16ダメージ
    for i in range(3):
        expected_damage = mon.max_hp * (i + 1) // 16
        hp_before = mon.hp
        battle.events.emit(Event.ON_TURN_END_3)
        damage = hp_before - mon.hp
        assert damage == expected_damage, f"Badly Poisoned turn {i+1}: damage {damage} != expected {expected_damage}"
        assert mon.ailment.count == i + 1, f"Badly Poisoned count: {mon.ailment.count} != {i+1}"


def test_paralysis_speed_reduction():
    """まひ: 素早さ半減"""
    battle = t.start_battle(ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    normal_speed = battle.calc_effective_speed(mon)
    mon.apply_ailment(battle, "まひ")
    paralysis_speed = battle.calc_effective_speed(mon)
    assert paralysis_speed == normal_speed // 2, "Paralysis speed reduction is incorrect"


def test_paralysis_action_disabled_high_rate():
    """まひ: 行動不能"""
    battle = t.start_battle(ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    mon.apply_ailment(battle, "まひ")
    # 必ず行動不能になる設定
    battle.test_option.trigger_ailment = True
    result = t.get_try_result(battle, Event.ON_TRY_ACTION)
    assert not result, "Paralysis action disabled (trigger_rate=1.0)"


def test_paralysis_action_enabled_low_rate():
    """まひ: 行動可能"""
    battle = t.start_battle(ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    mon.apply_ailment(battle, "まひ")
    # 必ず行動できる設定
    battle.test_option.trigger_ailment = False
    result = t.get_try_result(battle, Event.ON_TRY_ACTION)
    assert result, "Paralysis action enabled (trigger_rate=0.0)"


def test_burn_physical_move_damage_reduction():
    """やけど: 物理技ダメージ半減"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")]
    )
    battle.actives[0].apply_ailment(battle, "やけど")
    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_BURN_MODIFIER)


def test_burn_special_move_no_damage_change():
    """やけど: 特殊技ダメージは変わらず"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")]
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_BURN_MODIFIER)


def test_burn_turn_end_damage():
    """やけど: ターン終了時ダメージ"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle, "やけど")
    battle.events.emit(Event.ON_TURN_END_3)
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == mon.max_hp // 16, f"Burn damage is incorrect: expected {mon.max_hp // 16} but got {actual_damage}"


def test_sleep_turn_progression_recovery():
    """ねむり: ターン経過で回復"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.apply_ailment(battle, "ねむり")
    mon.ailment.count = 2  # 2ターンで回復

    # 1ターン目: count 2 → 1
    assert not t.get_try_result(battle, Event.ON_TRY_ACTION)
    assert mon.ailment.name == "ねむり", "Sleep: Still asleep on turn 1"
    assert mon.ailment.count == 1, f"Sleep: Count should be 1 on turn 1: {mon.ailment.count}"

    # 2ターン目: count 1 → 0 で回復
    assert t.get_try_result(battle, Event.ON_TRY_ACTION)
    assert not mon.ailment.is_active


def test_freeze_thaw_high_rate():
    """こおり: 解凍（確率テスト - trigger_rate=1.0）"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle, "こおり")
    # 必ず解凍される設定でテスト
    battle.test_option.trigger_ailment = True
    assert t.get_try_result(battle, Event.ON_TRY_ACTION)
    assert not mon.ailment.is_active, "Freeze: Thaw failed (trigger_rate=1.0)"


def test_freeze_persist_low_rate():
    """こおり: 状態維持（確率テスト - trigger_rate=0.0）"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle, "こおり")
    # 解凍されない設定でテスト
    battle.test_option.trigger_ailment = False
    assert not t.get_try_result(battle, Event.ON_TRY_ACTION)
    assert mon.ailment.name == "こおり", "Freeze: Status persistence failed (trigger_rate=0.0)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
