# TODO: カウント進行は別のテストファイルにまとめる

"""揮発性状態ハンドラの単体テスト"""
from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event
import test_utils as t


def test_アクアリング():
    """アクアリング: ターン終了時回復"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"アクアリング": 1},
    )
    battle.actives[0]._hp = 1
    expected_heal = battle.actives[0].max_hp // 16
    battle.events.emit(Event.ON_TURN_END_3)
    assert battle.actives[0].hp == 1 + expected_heal
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")


def test_あばれる():
    # TODO: 実装
    pass


def test_あめまみれ():
    # TODO: 実装
    pass


def test_アンコール():
    # TODO: 実装
    pass


def test_いちゃもん():
    # TODO: 実装
    pass


def test_うちおとす():
    # TODO: 実装
    pass


def test_おんねん():
    # TODO: 実装保留
    pass


def test_かいふくふうじ():
    # TODO: 実装
    pass


def test_かなしばり():
    """かなしばり: 技使用禁止"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かなしばり": 4},
    )
    # 禁止技を設定
    battle.actives[0].volatiles["かなしばり"].disabled_move_name = "はねる"
    assert battle.actives[0].has_volatile("かなしばり")


def test_きゅうしょアップ():
    # TODO: 実装
    pass


def test_こだわり():
    # TODO: 実装
    pass


def test_こんらん_self_damage():
    """こんらん: 自傷ダメージ"""
    battle = t.start_battle(ally_volatile={"こんらん": 2})
    # 自傷を強制
    battle.test_option.trigger_volatile = True
    battle.events.emit(
        Event.ON_TRY_ACTION,
        BattleContext(attacker=battle.actives[0], defender=battle.actives[1]),
    )
    battle.print_logs()
    # 技が失敗して自傷ダメージを受けている
    assert battle.actives[0].hp < battle.actives[0].max_hp
    # 混乱カウントが減少
    assert battle.actives[0].volatiles["こんらん"].count == 1
    # ログに混乱メッセージが含まれるか確認
    t.assert_log_contains(battle, "混乱")
    t.assert_log_contains(battle, "自分を攻撃")


def test_こんらん_action():
    """こんらん: 通常行動可能"""
    battle = t.start_battle(ally_volatile={"こんらん": 2})
    # 自傷を防止
    battle.test_option.trigger_volatile = False
    battle.events.emit(
        Event.ON_TRY_ACTION,
        BattleContext(attacker=battle.actives[0], defender=battle.actives[1]),
    )
    battle.print_logs()
    # 技が成功して相手にダメージを与えている
    assert battle.actives[0].hp == battle.actives[0].max_hp
    # 混乱カウントが減少
    assert battle.actives[0].volatiles["こんらん"].count == 1

# TODO: さわぐのテスト実装(保留)


def test_しおづけ():
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


def test_じごくずき():
    # TODO: 実装
    pass


def test_じゅうでん():
    # TODO: 実装
    pass


def test_タールショット():
    # TODO: 実装
    pass


def test_ちいさくなる():
    # TODO: 実装
    pass


def test_ちょうはつ():
    """ちょうはつ: 変化技使用不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["ひかりのかべ"])],
        ally_volatile={"ちょうはつ": 3},
    )
    # ひかりのかべ（変化技）を使おうとする
    initial_side_fields = len([f for f in battle.side_manager[0].fields.values() if f.is_active])
    ctx = BattleContext(source=battle.actives[0], target=battle.actives[0])
    battle.events.emit(Event.ON_CHECK_MOVE, ctx, battle.actives[0].moves[0])
    battle.print_logs()
    # ひかりのかべが発動していない（技が失敗した）
    active_side_fields = len([f for f in battle.side_manager[0].fields.values() if f.is_active])
    assert active_side_fields == initial_side_fields
    # ちょうはつ状態が維持
    assert battle.actives[0].has_volatile("ちょうはつ")
    # ログにちょうはつメッセージが含まれるか確認
    t.assert_log_contains(battle, "ちょうはつ")


def test_でんじふゆう():
    # TODO: 実装
    pass


def test_とくせいなし():
    # TODO: 実装
    pass


def test_にげられない():
    """にげられない: 交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"にげられない状態で交代コマンドが利用可能: {[str(c) for c in commands]}"


def test_ねをはる_heal():
    """ねをはる: ターン終了時回復"""
    battle = t.start_battle(ally_volatile={"ねをはる": 1})
    battle.actives[0]._hp = 1
    expected_heal = battle.actives[0].max_hp // 16
    battle.events.emit(Event.ON_TURN_END_3)
    assert battle.actives[0].hp == 1 + expected_heal
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")


def test_ねをはる_switch_denied():
    """ねをはる: 交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"ねをはる": 1},
    )
    # 交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"ねをはる状態で交代コマンドが利用可能: {[str(c) for c in commands]}"


def test_のろい():
    """のろい: ターン終了時ダメージ"""
    battle = t.start_battle(ally_volatile={"のろい": 1})
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 4
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon), None)
    # のろいダメージが発生
    assert mon.hp == mon.max_hp - expected_damage
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "HP")


def test_バインド_damage():
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


def test_バインド_switch_denied():
    """バインド: 通常タイプは交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"バインド": 3},
    )
    # ゴーストタイプでないので交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"バインド状態で交代コマンドが利用可能: {[str(c) for c in commands]}"


def test_バインド_ghost_can_switch():
    """バインド: ゴーストタイプは交代可能"""
    battle = t.start_battle(
        ally=[Pokemon("ゲンガー"), Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 3},
    )
    # ゴーストタイプなので交代可能
    assert t.can_switch(battle, 0)


def test_ひるみ():
    """ひるみ: 行動不能（1ターン）"""
    battle = t.start_battle(ally_volatile={"ひるみ": 1})
    battle.events.emit(
        Event.ON_TRY_ACTION,
        BattleContext(attacker=battle.actives[0])
    )
    battle.print_logs()
    # ひるみ状態が解除されていることを確認
    assert not battle.actives[0].has_volatile("ひるみ")
    # ログにひるみメッセージが含まれるか確認
    t.assert_log_contains(battle, "ひるんだ")


def test_ふういん():
    # TODO: 実装保留
    pass


def test_マジックコート():
    # TODO: 実装保留
    pass


def test_まるくなる():
    # TODO: 実装保留
    pass


def test_みがわり_immune():
    # TODO: 実装
    pass


def test_みがわり_damage():
    # TODO: 実装
    pass


def test_みちづれ():
    # TODO: 実装保留
    pass


def test_メロメロ_行動不能():
    """メロメロ: 行動不能（永続効果）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"メロメロ": 1},
    )
    # 行動不能を強制
    battle.test_option.trigger_volatile = True
    battle.events.emit(Event.ON_TRY_ACTION, BattleContext(target=battle.actives[0]), None)
    battle.print_logs()
    # メロメロ状態が維持されていることを確認（永続効果）
    assert battle.actives[0].has_volatile("メロメロ")
    # ログにメロメロメッセージが含まれるか確認
    t.assert_log_contains(battle, "メロメロで動けない")


def test_メロメロ_行動可能():
    """メロメロ: 行動可能（永続効果維持）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"メロメロ": 1},
    )
    # 行動を許可
    battle.test_option.trigger_volatile = False
    battle.events.emit(Event.ON_TRY_ACTION, BattleContext(target=battle.actives[0]), None)
    battle.print_logs()
    # メロメロ状態が維持されていることを確認（永続効果）
    assert battle.actives[0].has_volatile("メロメロ")


def test_やどりぎのタネ():
    """やどりぎのタネ: ターン終了時ダメージ"""
    battle = t.start_battle(ally_volatile={"やどりぎのタネ": 1})
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 8
    battle.events.emit(Event.ON_TURN_END_3)
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == expected_damage, "Incorect damage"
    t.assert_log_contains(battle, "やどりぎのタネ")


def test_ロックオン():
    # TODO: 実装保留
    pass


def test_トーチカ():
    # TODO: 実装
    pass


def test_キングシールド():
    # TODO: 実装
    pass


def test_スレッドトラップ():
    # TODO: 実装
    pass


def test_かえんのまもり():
    # TODO: 実装
    pass


def test_あなをほる_evade():
    """技を回避する"""
    # TODO: 実装
    pass


def test_あなをほる_hit():
    """技が命中する"""
    # TODO: 実装
    pass


def test_そらをとぶ_evade():
    """技を回避する"""
    # TODO: 実装
    pass


def test_そらをとぶ_hit():
    """技が命中する"""
    # TODO: 実装
    pass


def test_ダイビング_evade():
    """技を回避する"""
    # TODO: 実装
    pass


def test_ダイビング_hit():
    """技が命中する"""
    # TODO: 実装
    pass


def test_シャドーダイブ_evade():
    """技を回避する"""
    # TODO: 実装
    pass


def test_シャドーダイブ_hit():
    """技が命中する"""
    # TODO: 実装
    pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
