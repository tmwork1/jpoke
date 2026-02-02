import math
from jpoke import Pokemon
from jpoke.utils.enums import Event
import test_utils as t


def test():
    print("--- やどりぎのタネ ---")
    battle = t.start_battle(
        turn=1,
        ally_volatile={"やどりぎのタネ": 1},
    )
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 7/8)
    # ログにHP変化が記録されているか確認
    t.assert_log_contains(battle, "HP")

    print("--- こんらん: 自傷ダメージが発生する場合 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 2},
    )
    # 自傷を強制して動作を確認
    battle.test_option.ailment_trigger_rate = 1.0
    initial_hp = battle.actives[0].hp
    foe_initial_hp = battle.actives[1].hp
    battle.advance_turn()
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

    print("--- こんらん: 自傷が発生しない場合 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 2},
    )
    # 自傷を防止して通常行動を確認
    battle.test_option.ailment_trigger_rate = 0.0
    battle.advance_turn()
    battle.print_logs()
    # 混乱カウントが減少（技は使用できた）
    assert battle.actives[0].volatiles["こんらん"].count == 1

    print("--- こんらん: 自然治癒 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    # 混乱が解ける
    assert "こんらん" not in battle.actives[0].volatiles
    # ログに治癒メッセージが含まれるか確認
    t.assert_log_contains(battle, "混乱が解けた")

    print("--- ちょうはつ: 変化技禁止 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["ひかりのかべ"])],
        ally_volatile={"ちょうはつ": 3},
    )
    # ひかりのかべ（変化技）を使おうとする
    from jpoke.utils.enums import Command
    initial_side_fields = len([f for f in battle.side_mgrs[0].fields.values() if f.is_active])
    battle.players[0].reserve_command(Command.MOVE_0)
    battle.players[1].reserve_command(Command.MOVE_0)
    battle.advance_turn()
    battle.print_logs()
    # ひかりのかべが発動していない（技が失敗した）
    active_side_fields = len([f for f in battle.side_mgrs[0].fields.values() if f.is_active])
    assert active_side_fields == initial_side_fields
    # ちょうはつ状態が維持
    assert battle.actives[0].check_volatile("ちょうはつ")
    # ログにちょうはつメッセージが含まれるか確認
    t.assert_log_contains(battle, "ちょうはつ")

    print("--- ちょうはつ: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        ally_volatile={"ちょうはつ": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    assert not battle.actives[0].check_volatile("ちょうはつ")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "ちょうはつが解けた")

    print("--- バインド: ターン終了時ダメージ ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 3},
    )
    initial_hp = battle.actives[0].hp
    expected_damage = battle.actives[0].max_hp // 8
    # 1ターン進める
    battle.advance_turn()
    battle.print_logs()
    # バインドダメージが発生
    assert battle.actives[0].hp == initial_hp - expected_damage
    # ログにバインドメッセージが含まれるか確認
    t.assert_log_contains(battle, "バインド")

    print("--- バインド: カウント減少と解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 1},
    )
    # 1ターン進めてバインドを解除
    battle.advance_turn()
    battle.print_logs()
    # バインドが解除される
    assert not battle.actives[0].check_volatile("バインド")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "バインド状態から解放")

    print("--- メロメロ: 行動不能になる場合 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"メロメロ": 1},
    )
    # 行動不能を強制
    battle.test_option.ailment_trigger_rate = 1.0
    battle.advance_turn()
    battle.print_logs()
    # メロメロ状態が維持されていることを確認（永続効果）
    assert battle.actives[0].check_volatile("メロメロ")
    # ログにメロメロメッセージが含まれるか確認
    t.assert_log_contains(battle, "メロメロで動けない")

    print("--- メロメロ: 行動できる場合 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"メロメロ": 1},
    )
    # 行動を許可
    battle.test_option.ailment_trigger_rate = 0.0
    battle.advance_turn()
    battle.print_logs()
    # メロメロ状態が維持されていることを確認（永続効果）
    assert battle.actives[0].check_volatile("メロメロ")

    print("--- かなしばり: 技使用禁止 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かなしばり": 4},
    )
    # 禁止技を設定
    battle.actives[0].volatiles["かなしばり"].disabled_move_name = "はねる"
    assert battle.actives[0].check_volatile("かなしばり")

    print("--- かなしばり: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かなしばり": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    assert not battle.actives[0].check_volatile("かなしばり")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "かなしばりが解けた")

    print("--- バインド: ゴーストタイプは交代可能 ---")
    battle = t.start_battle(
        ally=[Pokemon("ゲンガー"), Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 3},
    )
    # ゴーストタイプなので交代可能
    assert t.can_switch(battle, 0)

    print("--- バインド: 非ゴーストタイプは交代不可 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"バインド": 3},
    )
    # ゴーストタイプでないので交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"バインド状態で交代コマンドが利用可能: {[str(c) for c in commands]}"

    print("--- アクアリング: ターン終了時回復 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"アクアリング": 1},
    )
    battle.modify_hp(battle.actives[0], v=-50)  # ダメージを与える
    initial_hp = battle.actives[0].hp
    expected_heal = battle.actives[0].max_hp // 16
    battle.advance_turn()
    battle.print_logs()
    # アクアリングで回復
    assert battle.actives[0].hp == initial_hp + expected_heal
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")

    print("--- しおづけ: ターン終了時ダメージ ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"しおづけ": 1},
    )
    initial_hp = battle.actives[0].hp
    expected_damage = battle.actives[0].max_hp // 8
    battle.advance_turn()
    battle.print_logs()
    # しおづけダメージが発生
    assert battle.actives[0].hp == initial_hp - expected_damage
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")

    print("--- のろい（ゴースト型）: ターン終了時ダメージ ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"のろい": 1},
    )
    initial_hp = battle.actives[0].hp
    expected_damage = battle.actives[0].max_hp // 4
    battle.advance_turn()
    battle.print_logs()
    # のろいダメージが発生
    assert battle.actives[0].hp == initial_hp - expected_damage
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")

    print("--- にげられない: 交代不可 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"にげられない状態で交代コマンドが利用可能: {[str(c) for c in commands]}"

    print("--- ねをはる: 交代不可 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"ねをはる": 1},
    )
    # 交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"ねをはる状態で交代コマンドが利用可能: {[str(c) for c in commands]}"

    print("--- あめまみれ: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"あめまみれ": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    assert not battle.actives[0].check_volatile("あめまみれ")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "あめまみれが解けた")

    print("--- かいふくふうじ: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かいふくふうじ": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    assert not battle.actives[0].check_volatile("かいふくふうじ")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "かいふくふうじが解けた")

    print("--- じごくずき: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"じごくずき": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    assert not battle.actives[0].check_volatile("じごくずき")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "じごくずきが解けた")

    print("--- じゅうでん: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"じゅうでん": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    assert not battle.actives[0].check_volatile("じゅうでん")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "じゅうでんが解けた")

    print("--- でんじふゆう: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"でんじふゆう": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    assert not battle.actives[0].check_volatile("でんじふゆう")
    # ログに解除メッセージが含まれるか確認
    t.assert_log_contains(battle, "でんじふゆうが解けた")

    print("--- ねむけ: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"ねむけ": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    assert not battle.actives[0].check_volatile("ねむけ")
    # ログに眠りメッセージが含まれるか確認
    t.assert_log_contains(battle, "眠ってしまった")

    print("--- ほろびのうた: カウント減少と倒れる ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"ほろびのうた": 1},
    )
    battle.advance_turn()
    battle.print_logs()
    # ほろびのうたで倒れる
    assert battle.actives[0].hp == 0
    assert not battle.actives[0].check_volatile("ほろびのうた")
    # ログにほろびのうたメッセージが含まれるか確認
    t.assert_log_contains(battle, "ほろびのうたで倒れた")

    print("All volatile tests passed!")


if __name__ == "__main__":
    test()
