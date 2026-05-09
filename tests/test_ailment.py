"""状態異常ハンドラの単体テスト"""
import pytest

from jpoke.enums import Event
from jpoke.core import BattleContext
from jpoke.model import Pokemon

import test_utils as t


# ──────────────────────────────────────────────────────────────────
# どく、もうどく
# ──────────────────────────────────────────────────────────────────
def test_どく_ダメージ():
    """どく: ターン終了時ダメージ"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    battle.events.emit(Event.ON_TURN_END_3)
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 8, "Poison damage is incorrect"


def test_もうどく_ダメージ():
    """もうどく: ターン経過でダメージ増加"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")
    # nターン目: n/16ダメージ
    for i in range(3):
        hp_before = mon.hp
        battle.events.emit(Event.ON_TURN_END_3)
        damage = hp_before - mon.hp
        assert mon.ailment.elapsed_turns == i + 1
        assert damage == mon.max_hp * (i + 1) // 16


# ──────────────────────────────────────────────────────────────────
# まひ
# ──────────────────────────────────────────────────────────────────


def test_まひ_すばやさ低下():
    """まひ: 素早さ半減"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    normal_speed = battle.calc_effective_speed(mon)
    battle.ailment_manager.apply(mon, "まひ")
    paralysis_speed = battle.calc_effective_speed(mon)
    assert paralysis_speed == normal_speed // 2, "Paralysis speed reduction is incorrect"


def test_まひ_行動不能():
    """まひ: 行動不能"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動不能になる設定
    battle.test_option.trigger_ailment = True
    result = t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert not result, "Paralysis action disabled (trigger_rate=1.0)"


def test_まひ_行動成功():
    """まひ: 行動可能"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("リザードン")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動できる設定
    battle.test_option.trigger_ailment = False
    result = t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert result, "Paralysis action enabled (trigger_rate=0.0)"


# ──────────────────────────────────────────────────────────────────
# やけど
# ──────────────────────────────────────────────────────────────────
def test_やけど_ダメージ補正あり():
    """やけど: 物理技ダメージ半減"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")]
    )
    battle.ailment_manager.apply(battle.actives[0], "やけど")
    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_BURN_MODIFIER)


def test_やけど_ダメージ補正なし():
    """やけど: 特殊技ダメージは変わらず"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")]
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_BURN_MODIFIER)


def test_やけど_ダメージ():
    """やけど: ターン終了時ダメージ"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    battle.events.emit(Event.ON_TURN_END_3)
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == mon.max_hp // 16, f"Burn damage is incorrect: expected {mon.max_hp // 16} but got {actual_damage}"


# ──────────────────────────────────────────────────────────────────
# ねむり
# ──────────────────────────────────────────────────────────────────
def test_ねむり_カウント():
    """ねむり: ターン経過で回復"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ")],
                            )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "ねむり", count=2)

    # 1ターン目: count 2 → 1
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert mon.ailment.name == "ねむり"
    assert mon.ailment.count == 1

    # 2ターン目: count 1 → 0 で回復
    assert t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert not mon.ailment.is_active

# ──────────────────────────────────────────────────────────────────
# こおり
# ──────────────────────────────────────────────────────────────────


def test_こおり_行動不能():
    """こおり: 状態維持（確率テスト - trigger_rate=0.0）"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "こおり")
    # 解凍されない設定でテスト
    battle.test_option.trigger_ailment = False
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert mon.ailment.name == "こおり", "Freeze: Status persistence failed (trigger_rate=0.0)"


def test_こおり_行動成功():
    """こおり: 解凍（確率テスト - trigger_rate=1.0）"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "こおり")
    # 必ず解凍される設定でテスト
    battle.test_option.trigger_ailment = True
    assert t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert not mon.ailment.is_active, "Freeze: Thaw failed (trigger_rate=1.0)"


def test_こおり_ほのお技被弾で解凍する():
    battle = t.start_battle(
        ally=[Pokemon("リザードン", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    frozen = battle.actives[1]
    battle.ailment_manager.apply(frozen, "こおり")

    t.reserve_command(battle)
    battle.advance_turn()

    assert not frozen.ailment.is_active

# ──────────────────────────────────────────────────────────────────
# タイプによる耐性テスト
# ──────────────────────────────────────────────────────────────────
# TODO : パラメタライズでまとめる


def test_どくタイプには通常どくが入らない():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("フシギダネ")])
    target = battle.actives[0]

    assert not battle.ailment_manager.apply(target, "どく")
    assert not target.ailment.is_active


def test_はがねタイプには通常もうどくが入らない():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("コイル")])
    target = battle.actives[0]

    assert not battle.ailment_manager.apply(target, "もうどく")
    assert not target.ailment.is_active


def test_でんきタイプにはまひが入らない():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    target = battle.actives[0]

    assert not battle.ailment_manager.apply(target, "まひ")
    assert not target.ailment.is_active


def test_ほのおタイプにはやけどが入らない():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ヒトカゲ")])
    target = battle.actives[0]

    assert not battle.ailment_manager.apply(target, "やけど")
    assert not target.ailment.is_active


def test_こおりタイプにはこおりが入らない():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ラプラス")])
    target = battle.actives[0]

    assert not battle.ailment_manager.apply(target, "こおり")
    assert not target.ailment.is_active


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
