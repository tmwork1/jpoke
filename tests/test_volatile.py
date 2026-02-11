"""揮発性状態ハンドラの単体テスト"""
import math
from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event
import test_utils as t


def test_やどりぎのタネ():
    """やどりぎのタネ: ターン終了時ダメージ"""
    battle = t.start_battle(
        turn=1,
        ally_volatile={"やどりぎのタネ": 1},
    )
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 7/8)
    # ログにHP変化が記録されているか確認
    t.assert_log_contains(battle, "HP")


def test_こんらん_自傷():
    """こんらん: 自傷ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 2},
    )
    # 自傷を強制して動作を確認
    battle.test_option.ailment_trigger_rate = 1.0
    initial_hp = battle.actives[0].hp
    foe_initial_hp = battle.actives[1].hp
    battle.events.emit(Event.ON_TRY_ACTION, BattleContext(target=battle.actives[0]), None)
    battle.print_logs()
    # 自傷ダメージでHPが減少（技が使えなかった）
    assert battle.actives[0].hp < initial_hp
    # 相手にダメージを与えていない（技が失敗した）
    assert battle.actives[1].hp == foe_initial_hp
    # 混乱カウントが減少
    assert battle.actives[0].volatiles["こんらん"].count == 1
    # ログに混乱メッセージが含まれるか確認
    t.assert_log_contains(battle, "混乱")
    t.assert_log_contains(battle, "自分を攻撃")


def test_こんらん_通常行動():
    """こんらん: 通常行動可能"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 2},
    )
    # 自傷を防止して通常行動を確認
    battle.test_option.ailment_trigger_rate = 0.0
    battle.events.emit(Event.ON_TRY_ACTION, BattleContext(target=battle.actives[0]), None)
    battle.print_logs()
    # 混乱カウントが減少（技は使用できた）
    assert battle.actives[0].volatiles["こんらん"].count == 1


def test_こんらん_解除():
    """こんらん: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 1},
    )
    battle.events.emit(Event.ON_TRY_ACTION, BattleContext(target=battle.actives[0]), None)
    battle.print_logs()
    # 混乱が解ける
    assert "こんらん" not in battle.actives[0].volatiles
    # ログに治癒メッセージが含まれるか確認
    t.assert_log_contains(battle, "混乱が解けた")


def test_ちょうはつ_変化技禁止():
    """ちょうはつ: 変化技使用不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["ひかりのかべ"])],
        ally_volatile={"ちょうはつ": 3},
    )
    # ひかりのかべ（変化技）を使おうとする
    initial_side_fields = len([f for f in battle.side_manager[0].fields.values() if f.is_active])
    ctx = BattleContext(source=battle.actives[0], target=battle.actives[0])
    battle.events.emit(Event.ON_BEFORE_MOVE, ctx, battle.actives[0].moves[0])
    battle.print_logs()
    # ひかりのかべが発動していない（技が失敗した）
    active_side_fields = len([f for f in battle.side_manager[0].fields.values() if f.is_active])
    assert active_side_fields == initial_side_fields
    # ちょうはつ状態が維持
    assert battle.actives[0].check_volatile("ちょうはつ")
    # ログにちょうはつメッセージが含まれるか確認
    t.assert_log_contains(battle, "ちょうはつ")


def test_ちょうはつ_解除():
    """ちょうはつ: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        ally_volatile={"ちょうはつ": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    assert not battle.actives[0].check_volatile("ちょうはつ")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "ちょうはつが解けた")


def test_バインド_ダメージ():
    """バインド: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 3},
    )
    initial_hp = battle.actives[0].hp
    expected_damage = battle.actives[0].max_hp // 8
    # 1ターン進める
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    # バインドダメージが発生
    assert battle.actives[0].hp == initial_hp - expected_damage
    # ログにバインドメッセージが含まれるか確認
    t.assert_log_contains(battle, "バインド")


def test_バインド_解除():
    """バインド: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 1},
    )
    # 1ターン進めてバインドを解除
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    # バインドが解除される
    assert not battle.actives[0].check_volatile("バインド")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "バインド状態から解放")


def test_バインド_ゴースト交代可():
    """バインド: ゴーストタイプは交代可能"""
    battle = t.start_battle(
        ally=[Pokemon("ゲンガー"), Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 3},
    )
    # ゴーストタイプなので交代可能
    assert t.can_switch(battle, 0)


def test_バインド_通常交代不可():
    """バインド: 通常タイプは交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"バインド": 3},
    )
    # ゴーストタイプでないので交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"バインド状態で交代コマンドが利用可能: {[str(c) for c in commands]}"


def test_メロメロ_行動不能():
    """メロメロ: 行動不能（永続効果）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"メロメロ": 1},
    )
    # 行動不能を強制
    battle.test_option.ailment_trigger_rate = 1.0
    battle.events.emit(Event.ON_TRY_ACTION, BattleContext(target=battle.actives[0]), None)
    battle.print_logs()
    # メロメロ状態が維持されていることを確認（永続効果）
    assert battle.actives[0].check_volatile("メロメロ")
    # ログにメロメロメッセージが含まれるか確認
    t.assert_log_contains(battle, "メロメロで動けない")


def test_メロメロ_行動可能():
    """メロメロ: 行動可能（永続効果維持）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"メロメロ": 1},
    )
    # 行動を許可
    battle.test_option.ailment_trigger_rate = 0.0
    battle.events.emit(Event.ON_TRY_ACTION, BattleContext(target=battle.actives[0]), None)
    battle.print_logs()
    # メロメロ状態が維持されていることを確認（永続効果）
    assert battle.actives[0].check_volatile("メロメロ")


def test_かなしばり():
    """かなしばり: 技使用禁止"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かなしばり": 4},
    )
    # 禁止技を設定
    battle.actives[0].volatiles["かなしばり"].disabled_move_name = "はねる"
    assert battle.actives[0].check_volatile("かなしばり")


def test_かなしばり_解除():
    """かなしばり: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かなしばり": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    battle.print_logs()
    assert not battle.actives[0].check_volatile("かなしばり")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "かなしばりが解けた")


def test_アクアリング_回復():
    """アクアリング: ターン終了時回復"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"アクアリング": 1},
    )
    battle.modify_hp(battle.actives[0], v=-50)  # ダメージを与える
    initial_hp = battle.actives[0].hp
    expected_heal = battle.actives[0].max_hp // 16
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    # アクアリングで回復
    assert battle.actives[0].hp == initial_hp + expected_heal
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")


def test_しおづけ_ダメージ():
    """しおづけ: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"しおづけ": 1},
    )
    initial_hp = battle.actives[0].hp
    expected_damage = battle.actives[0].max_hp // 8
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    # しおづけダメージが発生
    assert battle.actives[0].hp == initial_hp - expected_damage
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")


def test_のろい_ダメージ():
    """のろい: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"のろい": 1},
    )
    initial_hp = battle.actives[0].hp
    expected_damage = battle.actives[0].max_hp // 4
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    # のろいダメージが発生
    assert battle.actives[0].hp == initial_hp - expected_damage
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")


def test_にげられない_交代不可():
    """にげられない: 交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"にげられない状態で交代コマンドが利用可能: {[str(c) for c in commands]}"


def test_ねをはる_交代不可():
    """ねをはる: 交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"ねをはる": 1},
    )
    # 交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"ねをはる状態で交代コマンドが利用可能: {[str(c) for c in commands]}"


def test_あめまみれ_解除():
    """あめまみれ: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"あめまみれ": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    assert not battle.actives[0].check_volatile("あめまみれ")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "あめまみれが解けた")


def test_かいふくふうじ_解除():
    """かいふくふうじ: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かいふくふうじ": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    assert not battle.actives[0].check_volatile("かいふくふうじ")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "かいふくふうじが解けた")


def test_じごくずき_解除():
    """じごくずき: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"じごくずき": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    assert not battle.actives[0].check_volatile("じごくずき")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "じごくずきが解けた")


def test_じゅうでん_解除():
    """じゅうでん: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"じゅうでん": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    assert not battle.actives[0].check_volatile("じゅうでん")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "じゅうでんが解けた")


def test_でんじふゆう_解除():
    """でんじふゆう: カウント消滅で解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"でんじふゆう": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    assert not battle.actives[0].check_volatile("でんじふゆう")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "でんじふゆうが解けた")


def test_ねむけ_ねむり変化():
    """ねむけ: カウント消滅でねむり状態に"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"ねむけ": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    assert not battle.actives[0].check_volatile("ねむけ")
    # ログに眠りメッセージが含まれるか確認
    t.assert_log_contains(battle, "眠ってしまった")


def test_ほろびのうた_瀕死():
    """ほろびのうた: カウント消滅で瀕死"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"ほろびのうた": 1},
    )
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=battle.actives[0]), None)
    # ほろびのうたで倒れる
    assert battle.actives[0].hp == 0
    assert not battle.actives[0].check_volatile("ほろびのうた")
    # ログにほろびのうたメッセージが含まれるか確認
    t.assert_log_contains(battle, "ほろびのうたで倒れた")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
