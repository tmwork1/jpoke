# TODO: assert 文は英語表記

"""状態異常ハンドラの単体テスト"""
import math
from jpoke.core.event import Event, EventContext
from jpoke import Pokemon
import test_utils as t


POISON_DAMAGE_RATE = 1 / 8
BADLY_POISON_BASE_RATE = 1 / 16
PARALYSIS_SPEED_REDUCTION = 0.5
BURN_DAMAGE_MODIFIER = 0.5
BURN_DAMAGE_RATIO = 1 / 16


def test_poison_turn_end_damage():
    """どく: ターン終了時ダメージ"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "どく")
    battle.events.emit(Event.ON_TURN_END_3, EventContext(source=mon))
    damage = mon.max_hp - mon.hp
    assert damage == int(mon.max_hp * POISON_DAMAGE_RATE), "Poison damage is incorrect"


def test_badly_poison_damage_increase():
    """もうどく: ターン経過でダメージ増加"""
    battle = t.start_battle()
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "もうどく")

    # nターン目: n/16ダメージ
    for i in range(3):
        hp_before = mon.hp
        battle.events.emit(Event.ON_TURN_END_3, EventContext(source=mon))
        damage = hp_before - mon.hp
        expected = int(mon.max_hp * (i + 1) * BADLY_POISON_BASE_RATE)
        assert damage == expected, f"Badly Poisoned turn {i+1}: damage {damage} != expected {expected}"
        assert mon.ailment.count == i + 1, f"Badly Poisoned count: {mon.ailment.count} != {i+1}"


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
    assert paralyzed_speed == int(normal_speed * PARALYSIS_SPEED_REDUCTION), "Paralysis speed reduction is incorrect"


def test_paralysis_action_disabled_high_rate():
    """まひ: 行動不能"""
    battle = t.start_battle(ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "まひ")
    # 必ず行動不能になる設定
    battle.test_option.ailment_trigger_rate = 1.0
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(attacker=mon), True)
    # HandlerReturnがFalseを返すことを確認（行動不能）
    assert not result, "Paralysis action disabled (trigger_rate=1.0)"


def test_paralysis_action_enabled_low_rate():
    """まひ: 行動可能"""
    battle = t.start_battle(ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "まひ")

    # 必ず行動できる設定
    battle.test_option.ailment_trigger_rate = 0.0
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(attacker=mon), True)
    # 行動可能であることを確認（Noneではなくsuccessがあればよい）
    # ON_TRY_ACTIONはコントロールフロー用のイベントなのでNoneが返ることもある
    # まひ状態でもtrigger_rate=0.0なら行動不能にならない（Falseが返らない）
    assert result is not False, "Paralysis action enabled (trigger_rate=0.0)"


def test_burn_physical_move_damage_reduction():
    """やけど: 物理技ダメージ半減"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")]
    )

    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]  # たいあたり

    # やけど状態にする
    attacker.apply_ailment(battle.events, "やけど")

    # やけど状態でのやけど補正値を取得
    burned_modifier = battle.events.emit(
        Event.ON_CALC_BURN_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move),
        4096  # 基準値
    )
    assert burned_modifier == int(4096 * BURN_DAMAGE_MODIFIER), "Burn: Physical move damage reduction is incorrect"


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
    assert burned_modifier == 4096, "Burn: Special move damage unchanged"


def test_burn_turn_end_damage():
    """やけど: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン")],  # HP高めのポケモンでテスト
    )

    mon = battle.actives[0]
    initial_hp = mon.hp
    mon.apply_ailment(battle.events, "やけど")

    # ターン終了時イベントを発火
    battle.events.emit(Event.ON_TURN_END_3, EventContext(source=mon), None)

    # 最大HPの1/16のダメージを受けているはず
    expected_damage = int(mon.max_hp * BURN_DAMAGE_RATIO)
    actual_damage = initial_hp - mon.hp
    assert actual_damage == expected_damage, "Burn turn end damage is incorrect"


def test_sleep_turn_progression_recovery():
    """ねむり: ターン経過で回復"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )

    mon = battle.actives[0]
    mon.apply_ailment(battle.events, "ねむり")
    mon.ailment.count = 2  # 2ターンで回復

    # 1ターン目: count 2 → 1
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(attacker=mon), None)
    assert mon.ailment.name == "ねむり", "Sleep: Still asleep on turn 1"
    assert mon.ailment.count == 1, f"Sleep: Count should be 1 on turn 1: {mon.ailment.count}"

    # 2ターン目: count 1 → 0 で回復
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(attacker=mon), None)
    assert mon.ailment.name == "", "Sleep: Should recover on turn 2"


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
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(attacker=mon), True)
    assert mon.ailment.name == "", "Freeze: Thaw failed (trigger_rate=1.0)"


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
    result = battle.events.emit(Event.ON_TRY_ACTION, EventContext(attacker=mon), True)
    assert mon.ailment.name == "こおり", "Freeze: Status persistence failed (trigger_rate=0.0)"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
