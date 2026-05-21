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
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    t.emit_turn_end_events(battle)
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 8, "Poison damage is incorrect"


def test_もうどく_ダメージ():
    """もうどく: ターン経過でダメージ増加"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")
    # nターン目: n/16ダメージ
    for i in range(3):
        hp_before = mon.hp
        t.emit_turn_end_events(battle)
        damage = hp_before - mon.hp
        assert mon.ailment.elapsed_turns == i + 1
        assert damage == mon.max_hp * (i + 1) // 16


# ──────────────────────────────────────────────────────────────────
# まひ
# ──────────────────────────────────────────────────────────────────


def test_まひ_すばやさ低下():
    """まひ: 素早さ半減"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("リザードン")]
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    assert battle.calc_effective_speed(mon) == mon.stats["S"] // 2


def test_まひ_行動不能():
    """まひ: 行動不能"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動不能になる設定
    battle.test_option.trigger_ailment = True
    battle.run_move(mon, mon.moves[0])

    assert not battle.move_executor.action_success


def test_まひ_行動成功():
    """まひ: 行動可能"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("リザードン")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動できる設定
    battle.test_option.trigger_ailment = False
    battle.run_move(mon, mon.moves[0])
    assert battle.move_executor.action_success, "Paralysis action enabled (trigger_rate=0.0)"


# ──────────────────────────────────────────────────────────────────
# やけど
# ──────────────────────────────────────────────────────────────────
def test_やけど_物理技ダメージ半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")]
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "やけど")
    battle.run_move(attacker, attacker.moves[0])
    assert battle.damage_calculator.burn_modifier == 2048


def test_やけど_特殊技ダメージは半減しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ")]
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "やけど")
    battle.run_move(attacker, attacker.moves[0])
    assert battle.damage_calculator.burn_modifier == 4096


def test_やけど_ダメージ():
    """やけど: ターン終了時ダメージ"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.emit_turn_end_events(battle)
    assert mon.hp == mon.max_hp - mon.max_hp // 16


# ──────────────────────────────────────────────────────────────────
# ねむり
# ──────────────────────────────────────────────────────────────────
def test_ねむり_カウント():
    """ねむり: ターン経過で回復"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ニャース")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=2)

    # 1ターン目: count 2 → 1
    battle.run_move(attacker, attacker.moves[0])
    assert not battle.move_executor.action_success
    assert attacker.ailment.name == "ねむり"
    assert attacker.ailment.count == 1

    # 2ターン目: count 1 → 0 で回復
    battle.run_move(attacker, attacker.moves[0])
    assert battle.move_executor.action_success
    assert not attacker.ailment.is_active

# ──────────────────────────────────────────────────────────────────
# こおり
# ──────────────────────────────────────────────────────────────────


def test_こおり_行動不能():
    """こおり: 状態維持（確率テスト - trigger_rate=0.0）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "こおり")
    # 解凍されない設定でテスト
    battle.test_option.trigger_ailment = False
    battle.run_move(mon, mon.moves[0])
    assert not battle.move_executor.action_success
    assert mon.ailment.name == "こおり"


def test_こおり_行動成功():
    """こおり: 解凍（確率テスト - trigger_rate=1.0）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "こおり")
    # 必ず解凍される設定でテスト
    battle.test_option.trigger_ailment = True
    battle.run_move(mon, mon.moves[0])
    assert battle.move_executor.action_success
    assert not mon.ailment.is_active


def test_こおり_ほのお技被弾で解凍する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, "こおり")
    battle.run_move(attacker, attacker.moves[0])
    assert not defender.ailment.is_active

# ──────────────────────────────────────────────────────────────────
# タイプによる耐性テスト
# ──────────────────────────────────────────────────────────────────
# TODO : パラメタライズでまとめる


def test_どくタイプには通常どくが入らない():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    assert not battle.ailment_manager.apply(target, "どく")


def test_はがねタイプには通常もうどくが入らない():
    battle = t.start_battle(
        team0=[Pokemon("コイル")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    assert not battle.ailment_manager.apply(target, "もうどく")


def test_でんきタイプにはまひが入らない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    assert not battle.ailment_manager.apply(target, "まひ")


def test_ほのおタイプにはやけどが入らない():
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    assert not battle.ailment_manager.apply(target, "やけど")


def test_こおりタイプにはこおりが入らない():
    battle = t.start_battle(
        team0=[Pokemon("ラプラス")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    assert not battle.ailment_manager.apply(target, "こおり")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
