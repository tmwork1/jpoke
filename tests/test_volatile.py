"""揮発性状態ハンドラの単体テスト"""
from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event, Command, LogCode
import test_utils as t


def test_アクアリング():
    """アクアリング: ターン終了時回復"""
    battle = t.start_battle(
        ally_volatile={"アクアリング": 1}
    )
    battle.actives[0]._hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    actual_heal = battle.actives[0].hp - 1
    assert actual_heal == battle.actives[0].max_hp // 16
    assert t.log_contains(battle, LogCode.HEAL)


def test_あばれる_行動固定():
    """あばれる: 強制行動"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["あばれる"])],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=2, move="あばれる")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.FORCED], "あばれる状態で強制行動コマンドが利用可能"

    initial_pp = attacker.moves[0].pp
    battle.advance_turn()  # 1ターン進める
    assert attacker.moves[0].pp == initial_pp, "あばれるで技のPPが消費されている"


def test_あばれる_カウント進行():
    battle = t.start_battle(
        ally_volatile={"あばれる": 2}
    )
    attacker, defender = battle.actives
    ctx = BattleContext(attacker=attacker, defender=defender)
    battle.events.emit(Event.ON_DAMAGE, ctx)
    assert attacker.volatiles["あばれる"].count == 1
    battle.events.emit(Event.ON_DAMAGE, ctx)
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


def test_あめまみれ():
    battle = t.start_battle(
        ally_volatile={"あめまみれ": 2}
    )
    battle.events.emit(Event.ON_TURN_END_3)
    assert battle.actives[0].rank["S"] == -1
    assert t.log_contains(battle, LogCode.MODIFY_STAT)


def test_アンコール():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active
    battle.volatile_manager.apply(mon, "アンコール", move="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands)


def test_いちゃもん_コマンド制限():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active
    battle.volatile_manager.apply(mon, "いちゃもん", move="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands), "いちゃもんでlast_move_name以外の技が使用可能"


def test_うちおとす():
    battle = t.start_battle(
        ally=[Pokemon("ポッポ")],
        ally_volatile={"うちおとす": 1}
    )
    assert not battle.query_manager.is_floating(battle.actives[0])


def test_おんねん_ＰＰ減少():
    battle = t.start_battle(
        ally=[Pokemon("ライチュウ", moves=["たいあたり"])],
        foe_volatile={"おんねん": 1},
    )
    battle.actives[1]._hp = 1  # 確実にひんしになるようにHPを1にする
    battle.advance_turn()
    assert battle.actives[0].moves[0].pp == 0
    assert t.log_contains(battle, LogCode.CONSUME_PP)


def test_かいふくふうじ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かいふくふうじ": 1},
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.modify_hp(mon, 10)
    assert t.log_contains(battle, LogCode.HEAL_BLOCKED)
    assert mon.hp == 1, "かいふくふうじでHPが回復している"


def test_かなしばり_コマンド制限():
    """かなしばり: 技使用禁止"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active
    battle.volatile_manager.apply(mon, "かなしばり", move="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx != 0 for cmd in commands)


def test_きゅうしょアップ():
    battle = t.start_battle(
        ally_volatile={"きゅうしょアップ": 2}
    )
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
    battle.volatile_manager.apply(mon, "こだわり", move="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands)


def test_こんらん_自傷ダメージ():
    """こんらん: 自傷ダメージ"""
    battle = t.start_battle(
        ally_volatile={"こんらん": 2}
    )
    attacker, defender = battle.actives
    # 自傷を強制
    battle.test_option.trigger_volatile = True
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert attacker.hp < attacker.max_hp
    assert defender.hp == defender.max_hp
    assert attacker.volatiles["こんらん"].count == 1


def test_こんらん_通常行動():
    """こんらん: 通常行動可能"""
    battle = t.start_battle(
        ally_volatile={"こんらん": 2}
    )
    attacker, defender = battle.actives
    # 行動を許可
    battle.test_option.trigger_volatile = False
    assert t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert attacker.hp == attacker.max_hp
    assert attacker.volatiles["こんらん"].count == 1


def test_さわぐ_ねむりを防ぐ():
    battle = t.start_battle(
        ally_volatile={"さわぐ": 2}
    )
    assert not battle.ailment_manager.apply(battle.actives[0], "ねむり")


def test_さわぐ_ねむけを防ぐ():
    battle = t.start_battle(
        ally_volatile={"さわぐ": 2}
    )
    assert not battle.volatile_manager.apply(battle.actives[0], "ねむけ", count=2)


def test_さわがしい_ねむりを防ぐ():
    battle = t.start_battle(
        foe_volatile={"さわがしい": 2}
    )
    assert not battle.ailment_manager.apply(battle.actives[1], "ねむり")


def test_さわがしい_ねむけを防ぐ():
    battle = t.start_battle(
        foe_volatile={"さわがしい": 2}
    )
    assert not battle.volatile_manager.apply(battle.actives[1], "ねむけ", count=2)


def test_さわぐ終了時_さわがしいを解除する():
    battle = t.start_battle(
        ally_volatile={"さわぐ": 1},
        foe_volatile={"さわがしい": 2},
    )
    battle.events.emit(Event.ON_TURN_END_3)
    assert not battle.actives[0].has_volatile("さわぐ")
    assert not battle.actives[1].has_volatile("さわがしい")


def test_さわぐ交代時_さわがしいを解除する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"さわぐ": 2},
        foe_volatile={"さわがしい": 2},
    )
    battle.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.players[1].active.has_volatile("さわがしい")


def test_しおづけ_一倍():
    """しおづけ: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally_volatile={"しおづけ": 1}
    )
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 8
    battle.events.emit(Event.ON_TURN_END_3)
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == expected_damage
    assert t.log_contains(battle, LogCode.DAMAGE)


def test_しおづけ_二倍():
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
    assert t.log_contains(battle, LogCode.DAMAGE)


def test_じごくずき_コマンド制限():
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
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)
    assert not battle.actives[0].has_volatile("じゅうでん")


def test_タールショット():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["ひのこ"])],
        foe_volatile={"タールショット": 1}
    )
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER)


def test_ちいさくなる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["のしかかり"])],
        foe_volatile={"ちいさくなる": 1}
    )
    # 必中
    assert t.calc_accuracy(battle, base=30) is None

    # 威力2倍
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_ちょうはつ():
    """ちょうはつ: 変化技使用不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["ひかりのかべ"])],
        ally_volatile={"ちょうはつ": 3},
    )
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED)


def test_でんじふゆう():
    battle = t.start_battle(
        ally_volatile={"でんじふゆう": 1},
    )
    assert battle.query_manager.is_floating(battle.actives[0])


def test_とくせいなし():
    battle = t.start_battle(
        foe_volatile={"とくせいなし": 1},
    )
    attacker, defender = battle.actives
    result = battle.events.emit(
        Event.ON_CHECK_DEF_ABILITY,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        defender.ability.name,
    )
    assert result is None


def test_にげられない():
    """にげられない: 交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    assert not t.can_switch(battle, 0)


def test_ねむけ():
    battle = t.start_battle(
        ally_volatile={"ねむけ": 2}
    )
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.has_volatile("ねむけ")
    assert not mon.has_ailment("ねむり")
    battle.events.emit(Event.ON_TURN_END_3)
    assert not mon.has_volatile("ねむけ")
    assert mon.has_ailment("ねむり")


def test_ねをはる_回復():
    """ねをはる: ターン終了時回復"""
    battle = t.start_battle(
        ally_volatile={"ねをはる": 1}
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == 1 + mon.max_hp // 16
    assert t.log_contains(battle, LogCode.HEAL)


def test_ねをはる_交代不可():
    """ねをはる: 交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"ねをはる": 1},
    )
    assert not t.can_switch(battle, 0)


def test_のろい_ダメージ():
    """のろい: ターン終了時ダメージ"""
    battle = t.start_battle(ally_volatile={"のろい": 1})
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END_3)
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 4
    assert t.log_contains(battle, LogCode.DAMAGE)


def test_バインド_ダメージ():
    """バインド: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally_volatile={"バインド": 2},
    )
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 8
    # 1ターン進めてダメージを受ける
    battle.events.emit(Event.ON_TURN_END_3)
    hp = mon.hp
    assert hp == mon.max_hp - expected_damage
    assert t.log_contains(battle, LogCode.DAMAGE)
    # 1ターン進めて解除される
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == hp
    assert t.log_contains(battle, LogCode.VOLATILE_REMOVED)


def test_バインド_交代不可():
    """バインド: 交代不可"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"バインド": 3},
    )
    assert not t.can_switch(battle, 0)


def test_バインド_発生源交代解除():
    """バインドの発生源が退場した場合、バインドが解除される"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        foe_volatile={"バインド": 3},
    )
    t.reserve_command(battle, ally_command=Command.SWITCH_1)
    battle.advance_turn()
    assert not battle.actives[1].has_volatile("バインド")


def test_ひるみ():
    """ひるみ: 行動不能（1ターン）"""
    battle = t.start_battle(ally_volatile={"ひるみ": 1})
    attacker, defender = battle.actives
    battle.events.emit(
        Event.ON_CHECK_ACTION,
        BattleContext(attacker=attacker, defender=defender)
    )
    assert not attacker.has_volatile("ひるみ")
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED)


def test_ふういん():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_volatile={"ふういん": 1},
    )
    attacker, defender = battle.actives
    can_move = battle.events.emit(
        Event.ON_CHECK_ACTION,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        attacker.moves[0],
    )
    assert not can_move


def test_ほろびのうた():
    battle = t.start_battle(ally_volatile={"ほろびのうた": 1})
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == 0
    assert t.log_contains(battle, LogCode.DAMAGE)


def test_マジックコート():
    class DummyMove:
        def __init__(self):
            self.name = "ダミー技"

        def has_label(self, label):
            return label == "reflectable"

    battle = t.start_battle()
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "マジックコート", count=1)
    assert battle.events.emit(
        Event.ON_CHECK_REFLECT,
        BattleContext(attacker=attacker, defender=defender, move=DummyMove()),
        False,
    )


def test_まるくなる():
    # まるくなる状態自体には効果はない
    pass


def test_みがわり_無効化():
    """みがわり: 技を無効化する"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["キノコのほうし"])],
        foe_volatile={"みがわり": 1},
    )
    assert t.check_event_result(battle, Event.ON_CHECK_IMMUNE)
    assert t.log_contains(battle, LogCode.MOVE_IMMUNE)


def test_みがわり_命中():
    """みがわり: 技が命中する"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=100)
    volatile = defender.volatiles["みがわり"]
    battle.advance_turn()
    assert 0 < volatile.hp < 100
    assert t.log_contains(battle, LogCode.HIT_SUBSTITUTE)


def test_みがわり_破壊():
    """みがわり: 技が命中する"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=1)
    battle.advance_turn()
    assert not defender.has_volatile("みがわり")
    assert t.log_contains(battle, LogCode.HIT_SUBSTITUTE)


def test_みちづれ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_volatile={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    defender._hp = 1  # 確実にひんしになるようにHPを1にする
    battle.advance_turn()  # 1ターン進める
    assert attacker.hp == 0
    assert defender.hp == 0
    assert t.log_contains(battle, LogCode.DAMAGE)


def test_メロメロ_行動不能():
    """メロメロ: 行動不能（永続効果）"""
    battle = t.start_battle(
        ally_volatile={"メロメロ": 1},
    )
    # 行動不能を強制
    battle.test_option.trigger_volatile = True
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED)


def test_メロメロ_行動可能():
    """メロメロ: 行動可能（永続効果維持）"""
    battle = t.start_battle(
        ally_volatile={"メロメロ": 1},
    )
    # 行動を許可
    battle.test_option.trigger_volatile = False
    assert t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert t.log_contains(battle, LogCode.VOLATILE_STATUS)


def test_やどりぎのタネ():
    """やどりぎのタネ: ターン終了時ダメージ"""
    battle = t.start_battle(
        ally_volatile={"やどりぎのタネ": 1}
    )
    from_mon, to_mon = battle.actives
    to_mon._hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    damage = from_mon.max_hp - from_mon.hp
    assert damage == from_mon.max_hp // 8
    assert to_mon.hp == 1 + damage
    assert t.log_contains(battle, LogCode.DAMAGE)


def test_ロックオン():
    battle = t.start_battle(
        ally_volatile={"ロックオン": 1},
    )
    assert t.calc_accuracy(battle, base=30) is None
    assert not battle.actives[0].has_volatile("ロックオン")


def test_まもる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)


def test_まもる_自分対象():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["つるぎのまい"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE)


def test_トーチカ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)
    assert battle.actives[0].has_ailment("どく")


def test_トーチカ_非接触では毒にならない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert not battle.actives[0].ailment.is_active


def test_キングシールド():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)
    assert battle.actives[0].rank["A"] == -1


def test_キングシールド_非接触では攻撃が下がらない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert battle.actives[0].rank["A"] == 0


def test_スレッドトラップ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)
    assert battle.actives[0].rank["S"] == -1


def test_スレッドトラップ_非接触では素早さが下がらない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert battle.actives[0].rank["S"] == 0


def test_かえんのまもり():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)
    assert battle.actives[0].has_ailment("やけど")


def test_かえんのまもり_非接触ではやけどにならない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert not battle.actives[0].ailment.is_active


def test_かえんのまもり_変化技は防げない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんじは"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE)


def test_あなをほる_回避():
    """技を回避する"""
    battle = t.start_battle()
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="あなをほる")
    result = battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert not result


def test_あなをほる_命中():
    """技が命中する"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["じしん"])],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="あなをほる")
    result = battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert result


def test_そらをとぶ_回避():
    """技を回避する"""
    battle = t.start_battle()
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="そらをとぶ")
    result = battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert not result


def test_そらをとぶ_命中():
    """技が命中する"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["かみなり"])],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="そらをとぶ")
    result = battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert result


def test_ダイビング_回避():
    """技を回避する"""
    battle = t.start_battle()
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="ダイビング")
    result = battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert not result


def test_ダイビング_命中():
    """技が命中する"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["なみのり"])],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="ダイビング")
    result = battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert result


def test_シャドーダイブ_回避():
    """技を回避する"""
    battle = t.start_battle()
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="シャドーダイブ")
    result = battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert not result


def test_シャドーダイブ_命中():
    """技が命中しない"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["シャドーダイブ"])],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="シャドーダイブ")
    result = battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert not result


def test_あなをほる_潜伏中は交代できない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["あなをほる"]), Pokemon("ライチュウ")],
    )
    battle.volatile_manager.apply(battle.actives[0], "かくれる", count=1, move="あなをほる")
    assert not t.can_switch(battle, 0)


def test_あなをほる_潜伏中はコマンドが固定される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["あなをほる", "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かくれる", count=1, move="あなをほる")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.FORCED]


def test_あなをほる_強制行動ターンはPPを消費しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["あなをほる"])],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "かくれる", count=1, move="あなをほる")
    initial_pp = attacker.moves[0].pp
    battle.advance_turn()
    assert attacker.moves[0].pp == initial_pp


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
