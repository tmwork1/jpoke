"""状態異常ハンドラの単体テスト"""
import pytest

from jpoke.model import Pokemon
from jpoke.utils.type_defs import AilmentName

from . import test_utils as t


def test_faint_HPが0になる():
    """battle.faint(): 対象のHPが0になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.faint(mon)

    assert mon.hp == 0


def test_faint_faintedがTrueになる():
    """battle.faint(): 対象がひんし状態（fainted=True）になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.faint(mon)

    assert mon.fainted


def test_こおり_3回目行動時に強制解凍():
    """こおり: Champions仕様 - 行動不能2回の後（3回目の行動時）は必ず解凍する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "こおり")
    # 解凍しない設定で2回行動不能にする
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert mon.ailment.elapsed_turns == 1

    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert mon.ailment.elapsed_turns == 2

    # 3回目の行動時はtrigger_ailmentに関係なく必ず解凍される
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert not mon.ailment.is_active


def test_こおり_ほのお技被弾で解凍する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


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
    t.run_move(battle, 0)
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
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert not mon.ailment.is_active


@pytest.mark.parametrize(
    "target_name, ailment_name",
    [
        ("フシギダネ", "どく"),
        ("コイル", "もうどく"),
        ("ピカチュウ", "まひ"),
        ("ヒトカゲ", "やけど"),
        ("ラプラス", "こおり"),
    ],
)
def test_タイプ一致の状態異常は入らない(target_name: str, ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon(target_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    assert not battle.ailment_manager.apply(target, ailment_name)


def test_どく_ダメージ():
    """どく: ターン終了時ダメージ"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    t.end_turn(battle)
    assert mon.hp == mon.max_hp - mon.max_hp // 8, "Poison damage is incorrect"


def test_ねむり_いびきは行動できる():
    """ねむり: いびきを選択していれば行動不能にならない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いびき"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=3)

    # いびきはねむり中でも使える
    t.run_move(battle, 0)
    assert battle.move_executor.action_success


def test_ねむり_カウント():
    """ねむり: count=2 のとき2ターン目で回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ニャース")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=2)

    # 1ターン目: count 2 → 1
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.ailment.name == "ねむり"
    assert attacker.ailment.count == 1

    # 2ターン目: count 1 → 0 で回復
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert not attacker.ailment.is_active


def test_ねむり_カウント3_3ターン目で回復():
    """ねむり: count=3 のとき3ターン目で回復する（ねむる技 Champions 仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ニャース")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=3)

    # 1ターン目: count 3 → 2、行動不能
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.ailment.count == 2

    # 2ターン目: count 2 → 1、行動不能
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.ailment.count == 1

    # 3ターン目: count 1 → 0 で回復、行動成功
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert not attacker.ailment.is_active


def test_ねむり_通常付与のcountは2か3():
    """ねむり: 通常付与（count省略時）のカウントは2または3（Champions仕様）"""
    results = set()
    for _ in range(100):
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ")],
            team1=[Pokemon("カビゴン")],
        )
        mon = battle.actives[0]
        battle.ailment_manager.apply(mon, "ねむり")
        results.add(mon.ailment.count)
        if results == {2, 3}:
            break
    assert results <= {2, 3}, f"count の範囲外の値が検出された: {results}"
    assert 2 in results or 3 in results, "count が 2 または 3 のどちらかしか出なかった（偏り）"


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
    """まひ: 行動不能（Champions仕様: 12.5%の確率）"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動不能になる設定（trigger_ailment=True）
    battle.test_option.trigger_ailment = True
    t.run_move(battle, 0)

    assert not battle.move_executor.action_success


def test_まひ_行動成功():
    """まひ: 行動可能（trigger_ailment=Falseで必ず行動できる）"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("リザードン")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動できる設定
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)
    assert battle.move_executor.action_success, "まひでも行動不能トリガーなしなら行動できる"


def test_もうどく_15ターン上限():
    """もうどく: 16ターン以降もダメージは15/16で頭打ち"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("カビゴン")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")
    # 14ターン進める（各ターン後にHPを回復して続行）
    for _ in range(14):
        t.end_turn(battle)
        battle.modify_hp(mon, v=mon.max_hp)

    # 15ターン目: 15/16ダメージ
    hp_before = mon.hp
    t.end_turn(battle)
    damage15 = hp_before - mon.hp
    assert mon.ailment.elapsed_turns == 15
    assert damage15 == mon.max_hp * 15 // 16

    # 16ターン目: 上限15/16で頭打ち（増加しない）
    battle.modify_hp(mon, v=mon.max_hp)
    hp_before = mon.hp
    t.end_turn(battle)
    damage16 = hp_before - mon.hp
    assert mon.ailment.elapsed_turns == 16
    assert damage16 == mon.max_hp * 15 // 16  # 上限は15ターン分（15/16）


def test_もうどく_ダメージ():
    """もうどく: ターン経過でダメージ増加"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")
    # nターン目: n/16ダメージ
    for i in range(3):
        hp_before = mon.hp
        t.end_turn(battle)
        damage = hp_before - mon.hp
        assert mon.ailment.elapsed_turns == i + 1
        assert damage == mon.max_hp * (i + 1) // 16


def test_もうどく_交代でカウントリセット():
    """もうどく: 交代するとダメージカウントが1/16にリセット"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ニャース")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")

    # 2ターン経過（elapsed_turns=2, ダメージ2/16）
    t.end_turn(battle)
    t.end_turn(battle)
    assert mon.ailment.elapsed_turns == 2

    # 交代するとカウントリセット
    t.run_switch(battle, 0, 1)
    assert mon.ailment.elapsed_turns == 0, "交代後はelapsed_turnsが0にリセットされる"

    # 交代して戻ってきたとき、カウントが0からになる
    t.run_switch(battle, 0, 0)
    hp_before = mon.hp
    t.end_turn(battle)
    damage = hp_before - mon.hp
    assert mon.ailment.elapsed_turns == 1
    assert damage == mon.max_hp * 1 // 16  # 交代後1ターン目は1/16ダメージ


def test_やけど_ダメージ():
    """やけど: ターン終了時ダメージ"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert mon.hp == mon.max_hp - mon.max_hp // 16


def test_やけど_物理技ダメージ半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")]
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "やけど")
    t.run_move(battle, 0)
    assert battle.damage_calculator.burn_modifier == 2048


def test_やけど_特殊技ダメージは半減しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ")]
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "やけど")
    t.run_move(battle, 0)
    assert battle.damage_calculator.burn_modifier == 4096


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
