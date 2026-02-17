# TODO: カウント進行は別のテストファイルにまとめる

"""揮発性状態ハンドラの単体テスト"""
from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event, Command
import test_utils as t


def test_アクアリング():
    """アクアリング: ターン終了時回復"""
    battle = t.start_battle(ally_volatile={"アクアリング": 1})
    battle.actives[0]._hp = 1
    expected_heal = battle.actives[0].max_hp // 16
    battle.events.emit(Event.ON_TURN_END_3)
    actual_heal = battle.actives[0].hp - 1
    assert actual_heal == expected_heal, "Incorect heal amount"
    # ログにHP変化が含まれるか確認
    t.assert_log_contains(battle, "アクアリング")


def test_あばれる_action():
    """あばれる: 強制行動"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["あばれる"])],
    )
    attacker = battle.actives[0]
    attacker.apply_volatile(battle, "あばれる", count=2, move="あばれる")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.RAMPAGE], "あばれる状態で強制行動コマンドが利用可能"

    initial_pp = attacker.moves[0].pp
    battle.advance_turn()  # 1ターン進める
    battle.print_logs()
    assert attacker.moves[0].pp == initial_pp, "あばれるで技のPPが消費されている"


def test_あばれる_tick():
    battle = t.start_battle(ally_volatile={"あばれる": 2})
    attacker, defender = battle.actives
    ctx = BattleContext(attacker=attacker, defender=defender)
    battle.events.emit(Event.ON_DAMAGE, ctx)
    assert attacker.volatiles["あばれる"].count == 1
    battle.events.emit(Event.ON_DAMAGE, ctx)
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


def test_あめまみれ():
    battle = t.start_battle(ally_volatile={"あめまみれ": 2})
    battle.events.emit(Event.ON_TURN_END_3)
    assert battle.actives[0].rank["S"] == -1
    t.assert_log_contains(battle, "あめまみれ")


def test_アンコール():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active
    mon.apply_volatile(battle, "アンコール", move="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands)


def test_いちゃもん_modify_command_options():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active
    mon.apply_volatile(battle, "いちゃもん", move="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands), "いちゃもんでlast_move_name以外の技が使用可能"


def test_うちおとす():
    battle = t.start_battle(
        ally=[Pokemon("ポッポ")],
        ally_volatile={"うちおとす": 1}
    )
    assert not battle.actives[0].is_floating(battle)


def test_おんねん():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_volatile={"おんねん": 1},
    )
    battle.actives[1]._hp = 1  # 確実にひんしになるようにHPを1にする
    battle.advance_turn()  # 1ターン進める
    battle.print_logs()
    # おんねんで技のPPが0になっていることを確認
    assert battle.actives[0].moves[0].pp == 0
    # ログにおんねんメッセージが含まれるか確認
    t.assert_log_contains(battle, "おんねん")


def test_かいふくふうじ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かいふくふうじ": 1},
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.modify_hp(mon, 10)  # 回復を強制
    battle.print_logs()
    assert mon.hp == 1, "かいふくふうじでHPが回復している"


def test_かなしばり_modify_command_options():
    """かなしばり: 技使用禁止"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active
    mon.apply_volatile(battle, "かなしばり", move="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx != 0 for cmd in commands)


def test_きゅうしょアップ():
    battle = t.start_battle(ally_volatile={"きゅうしょアップ": 2})
    attacker, defender = battle.actives
    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender),
        0
    )
    assert rank == attacker.volatiles["きゅうしょアップ"].count


def test_こだわり():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active
    mon.apply_volatile(battle, "こだわり", move="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands)


def test_こんらん_self_damage():
    """こんらん: 自傷ダメージ"""
    battle = t.start_battle(ally_volatile={"こんらん": 2})
    attacker, defender = battle.actives
    # 自傷を強制
    battle.test_option.trigger_volatile = True
    result = battle.events.emit(
        Event.ON_TRY_ACTION,
        BattleContext(attacker=attacker, defender=defender),
    )
    battle.print_logs()
    # 技が失敗して自傷ダメージを受けている
    assert not result
    assert attacker.hp < attacker.max_hp
    assert defender.hp == defender.max_hp
    assert attacker.volatiles["こんらん"].count == 1
    # ログに混乱メッセージが含まれるか確認
    t.assert_log_contains(battle, "混乱")
    t.assert_log_contains(battle, "自傷")


def test_こんらん_action():
    """こんらん: 通常行動可能"""
    battle = t.start_battle(ally_volatile={"こんらん": 2})
    attacker, defender = battle.actives
    # 行動を許可
    battle.test_option.trigger_volatile = False
    result = battle.events.emit(
        Event.ON_TRY_ACTION,
        BattleContext(attacker=attacker, defender=defender),
    )
    battle.print_logs()
    # 技が成功
    assert result
    assert attacker.hp == attacker.max_hp
    assert attacker.volatiles["こんらん"].count == 1
    # ログに混乱メッセージが含まれるか確認
    t.assert_log_contains(battle, "混乱")
    t.assert_log_not_contains(battle, "自傷")

# TODO: さわぐのテスト実装(低優先度)


def test_しおづけ():
    """しおづけ: ターン終了時ダメージ"""
    battle = t.start_battle(ally_volatile={"しおづけ": 1})
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 8
    battle.events.emit(Event.ON_TURN_END_3)
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == expected_damage
    t.assert_log_contains(battle, "しおづけ")


def test_しおづけ_():
    """しおづけ: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ")],
        ally_volatile={"しおづけ": 1}
    )
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 4
    battle.events.emit(Event.ON_TURN_END_3)
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == expected_damage
    t.assert_log_contains(battle, "しおづけ")


def test_じごくずき_restrict_commands():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["うたう", "たいあたり"])],
        ally_volatile={"じごくずき": 2}
    )
    player = battle.players[0]
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx != 0 for cmd in commands)


def test_じゅうでん():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        ally_volatile={"じゅうでん": 1}
    )
    attacker, defender = battle.actives
    v = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096
    )
    assert v == 8192
    assert not attacker.has_volatile("じゅうでん")


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
    battle.events.emit(Event.ON_TRY_ACTION, ctx, battle.actives[0].moves[0])
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
    # ログにねをはるメッセージが含まれるか確認
    t.assert_log_contains(battle, "ねをはる")


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
    # ログにのろいメッセージが含まれるか確認
    t.assert_log_contains(battle, "のろい")


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
