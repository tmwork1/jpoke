"""揮発性状態ハンドラの単体テスト"""
import pytest
from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event, Command, LogCode
import test_utils as t

# TODO : 崩れたインデントの修正

# ──────────────────────────────────────────────────────────────────
# アクアリング
# ──────────────────────────────────────────────────────────────────


def test_アクアリング_回復():
    """アクアリング: ターン終了時回復"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"アクアリング": 1}
    )
    battle.actives[0]._hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    actual_heal = battle.actives[0].hp - 1
    assert actual_heal == battle.actives[0].max_hp // 16
    assert t.log_contains(battle, LogCode.HP_CHANGED)


def test_アクアリング_かいふくふうじ中は回復しない():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"アクアリング": 1, "かいふくふうじ": 1}
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == 1
    assert t.log_contains(battle, LogCode.HEAL_BLOCKED)

# ──────────────────────────────────────────────────────────────────
# あばれる
# ──────────────────────────────────────────────────────────────────


def test_あばれる_行動固定():
    """あばれる: 強制行動"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
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
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"あばれる": 2}
    )
    attacker, defender = battle.actives
    ctx = BattleContext(attacker=attacker, defender=defender)
    battle.events.emit(Event.ON_DAMAGE, ctx)
    assert attacker.volatiles["あばれる"].count == 1
    battle.events.emit(Event.ON_DAMAGE, ctx)
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


# ──────────────────────────────────────────────────────────────────
# あめまみれ
# ──────────────────────────────────────────────────────────────────


def test_あめまみれ():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"あめまみれ": 2}
    )
    battle.events.emit(Event.ON_TURN_END_3)
    assert battle.actives[0].rank["S"] == -1
    assert t.log_contains(battle, LogCode.MODIFY_STAT)


# ──────────────────────────────────────────────────────────────────
# アンコール
# ──────────────────────────────────────────────────────────────────


def test_アンコール():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active_mon
    battle.volatile_manager.apply(mon, "アンコール", move="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands)


def test_アンコール_実行時も技固定():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "アンコール", move="なきごえ")
    result = battle.events.emit(
        Event.ON_MODIFY_MOVE,
        BattleContext(attacker=mon, defender=battle.actives[1], move=mon.moves[0]),
        mon.moves[0],
    )
    assert result.name == "なきごえ"


def test_アンコール_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"アンコール": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("アンコール")
        battle.events.emit(Event.ON_TURN_END_3)
    assert not mon.has_volatile("アンコール")


def test_アンコール_対象技のPPが0だとわるあがきになる():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    mon = battle.players[0].active_mon
    battle.volatile_manager.apply(mon, "アンコール", move="たいあたり")
    mon.moves[0]._pp = 0
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_アンコール_対象技がかなしばりで使えないとわるあがきになる():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    mon = battle.players[0].active_mon
    battle.volatile_manager.apply(mon, "アンコール", move="たいあたり")
    battle.volatile_manager.apply(mon, "かなしばり", move="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]

# ──────────────────────────────────────────────────────────────────
# いちゃもん
# ──────────────────────────────────────────────────────────────────


def test_いちゃもん_コマンド制限():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active_mon
    battle.volatile_manager.apply(mon, "いちゃもん", move="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands), "いちゃもんでlast_move_name以外の技が使用可能"


def test_いちゃもん_別の技は選択できる():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ", "でんこうせっか"])],
    )
    mon = battle.players[0].active_mon
    battle.volatile_manager.apply(mon, "いちゃもん", move="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    move_indices = {cmd.idx for cmd in commands if cmd.is_move_family()}
    assert move_indices == {1, 2}


def test_いちゃもん_技が1つしかない場合はわるあがきになる():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    mon = battle.players[0].active_mon
    battle.volatile_manager.apply(mon, "いちゃもん", move="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]

# ──────────────────────────────────────────────────────────────────
# うちおとす
# ──────────────────────────────────────────────────────────────────


def test_うちおとす_浮遊無効():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ポッポ")],
        ally_volatile={"うちおとす": 1}
    )
    assert not battle.query_manager.is_floating(battle.actives[0])


def test_うちおとす_でんじふゆうより優先される():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ポッポ")],
        ally_volatile={"うちおとす": 1, "でんじふゆう": 5}
    )
    assert not battle.query_manager.is_floating(battle.actives[0])


def test_うちおとす_飛行タイプにじめん技が有効():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["じしん"])],
        foe=[Pokemon("ポッポ", moves=["はねる"])],
        foe_volatile={"うちおとす": 1},
    )
    defender = battle.actives[1]
    hp = defender.hp
    battle.advance_turn()
    assert defender.hp < hp

# ──────────────────────────────────────────────────────────────────
# おんねん
# ──────────────────────────────────────────────────────────────────


def test_おんねん_PP枯渇():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ライチュウ", moves=["たいあたり"])],
        foe_volatile={"おんねん": 1},
    )
    battle.actives[1]._hp = 1  # 確実にひんしになるようにHPを1にする
    battle.advance_turn()
    assert battle.actives[0].moves[0].pp == 0
    assert t.log_contains(battle, LogCode.CONSUME_PP)


def test_おんねん_倒しきれないと不発():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ライチュウ", moves=["たいあたり"])],
        foe_volatile={"おんねん": 1},
    )
    initial_pp = battle.actives[0].moves[0].pp
    battle.advance_turn()
    assert battle.actives[1].hp > 0
    assert battle.actives[0].moves[0].pp == initial_pp - 1

# ──────────────────────────────────────────────────────────────────
# かいふくふうじ
# ──────────────────────────────────────────────────────────────────


def test_かいふくふうじ():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かいふくふうじ": 1},
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.modify_hp(mon, 10)
    assert t.log_contains(battle, LogCode.HEAL_BLOCKED)
    assert mon.hp == 1, "かいふくふうじでHPが回復している"


def test_かいふくふうじ_カウント進行():
    n_turn = 1
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かいふくふうじ": n_turn},
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("かいふくふうじ")
        battle.events.emit(Event.ON_TURN_END_3)

    assert not mon.has_volatile("かいふくふうじ")


def test_かいふくふうじ_いたみわけは防がない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["いたみわけ"])],
        foe=[Pokemon("カビゴン")],
        ally_volatile={"かいふくふうじ": 1},
    )
    attacker, defender = battle.actives
    attacker._hp = 1
    defender._hp = defender.max_hp
    battle.advance_turn()
    assert attacker.hp > 1
    assert defender.hp < defender.max_hp

# ──────────────────────────────────────────────────────────────────
# かなしばり
# ──────────────────────────────────────────────────────────────────


def test_かなしばり_コマンド制限():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active_mon
    battle.volatile_manager.apply(mon, "かなしばり", move="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx != 0 for cmd in commands)


def test_かなしばり_実行ブロック():
    """かなしばり: 封じた技の実行をブロックする"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かなしばり", move="たいあたり")
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED)


def test_かなしばり_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かなしばり": n_turn}
    )
    mon = battle.actives[0]
    mon.volatiles["かなしばり"].move_name = "たいあたり"
    for _ in range(n_turn):
        assert mon.has_volatile("かなしばり")
        battle.events.emit(Event.ON_TURN_END_3)
    assert not mon.has_volatile("かなしばり")


def test_かなしばり_交代で解除():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"かなしばり": 99},
    )
    mon = battle.actives[0]
    mon.volatiles["かなしばり"].move_name = "たいあたり"
    battle.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.players[0].active_mon.has_volatile("かなしばり")

# ──────────────────────────────────────────────────────────────────
# きゅうしょアップ
# ──────────────────────────────────────────────────────────────────


def test_きゅうしょアップ():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"きゅうしょアップ": rank}
    )
    attacker, defender = battle.actives
    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender),
        2
    )
    assert 3 == attacker.volatiles["きゅうしょアップ"].count


# ──────────────────────────────────────────────────────────────────
# こだわり
# ──────────────────────────────────────────────────────────────────


def test_こだわり():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active_mon
    battle.volatile_manager.apply(mon, "こだわり", move="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx == 1 for cmd in commands)


def test_こだわり_交代で解除():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"こだわり": 1},
    )
    mon = battle.actives[0]
    mon.volatiles["こだわり"].move_name = "たいあたり"
    battle.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.players[0].active_mon.has_volatile("こだわり")


def test_こだわり_固定技のPPが0だとわるあがきになる():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    mon = battle.players[0].active_mon
    battle.volatile_manager.apply(mon, "こだわり", move="たいあたり")
    mon.moves[0]._pp = 0
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_こだわり_固定技がかなしばりで使えないとわるあがきになる():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    mon = battle.players[0].active_mon
    battle.volatile_manager.apply(mon, "こだわり", move="たいあたり")
    battle.volatile_manager.apply(mon, "かなしばり", move="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]

# ──────────────────────────────────────────────────────────────────
# こんらん
# ──────────────────────────────────────────────────────────────────


def test_こんらん_自傷ダメージ():
    """こんらん: 自傷ダメージ"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 2}
    )
    attacker, defender = battle.actives
    # 自傷を強制
    battle.test_option.trigger_volatile = True
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert attacker.hp < attacker.max_hp
    assert defender.hp == defender.max_hp


def test_こんらん_通常行動():
    """こんらん: 通常行動可能"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 2}
    )
    attacker, defender = battle.actives
    # 行動を許可
    battle.test_option.trigger_volatile = False
    assert t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert attacker.hp == attacker.max_hp


def test_こんらん_カウント満了で解除():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 1}
    )
    mon = battle.actives[0]
    battle.test_option.trigger_volatile = False
    assert mon.has_volatile("こんらん")
    t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert not mon.has_volatile("こんらん")

# ──────────────────────────────────────────────────────────────────
# さわぐ / さわがしい
# ──────────────────────────────────────────────────────────────────

# TODO : さわがしいとパラメタライズで共通化する


def test_さわぐ_ねむりを防ぐ():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"さわぐ": 2}
    )
    assert not battle.ailment_manager.apply(battle.actives[0], "ねむり")


def test_さわぐ_ねむけを防ぐ():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"さわぐ": 2}
    )
    assert not battle.volatile_manager.apply(battle.actives[0], "ねむけ", count=2)


def test_さわがしい_ねむりを防ぐ():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        foe_volatile={"さわがしい": 2}
    )
    assert not battle.ailment_manager.apply(battle.actives[1], "ねむり")


def test_さわがしい_ねむけを防ぐ():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        foe_volatile={"さわがしい": 2}
    )
    assert not battle.volatile_manager.apply(battle.actives[1], "ねむけ", count=2)


def test_さわぐ終了時_さわがしいを解除する():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")],
        ally_volatile={"さわぐ": 1},
        foe_volatile={"さわがしい": 2},
    )
    battle.events.emit(Event.ON_TURN_END_3)
    assert not battle.actives[0].has_volatile("さわぐ")
    assert not battle.actives[1].has_volatile("さわがしい")


def test_さわぐ交代時_さわがしいを解除する():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"さわぐ": 2},
        foe_volatile={"さわがしい": 2},
    )
    battle.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.players[1].active_mon.has_volatile("さわがしい")


def test_さわぐ_技固定():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["さわぐ", "たいあたり"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "さわぐ", count=2, move="さわぐ")
    result = battle.events.emit(
        Event.ON_MODIFY_MOVE,
        BattleContext(attacker=mon, defender=battle.actives[1], move=mon.moves[1]),
        mon.moves[1],
    )
    assert result.name == "さわぐ"

# ──────────────────────────────────────────────────────────────────
# しおづけ
# ──────────────────────────────────────────────────────────────────


# TODO : 等倍、二倍条件をすべてパラメタライズでまとめる
def test_しおづけ_一倍():
    """しおづけ: ターン終了時ダメージ"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")],
        ally_volatile={"しおづけ": 1}
    )
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 8
    battle.events.emit(Event.ON_TURN_END_3)
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == expected_damage
    assert t.log_contains(battle, LogCode.HP_CHANGED)


def test_しおづけ_二倍():
    """しおづけ: ターン終了時ダメージ"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ゼニガメ")],
        ally_volatile={"しおづけ": 1}
    )
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 4
    battle.events.emit(Event.ON_TURN_END_3)
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == expected_damage
    assert t.log_contains(battle, LogCode.HP_CHANGED)


def test_しおづけ_はがねタイプも二倍():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("コイル")],
        ally_volatile={"しおづけ": 1}
    )
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.max_hp - mon.hp == mon.max_hp // 4

# ──────────────────────────────────────────────────────────────────
# じごくづき
# ──────────────────────────────────────────────────────────────────


def test_じごくづき_コマンド制限():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["うたう", "たいあたり"])],
        ally_volatile={"じごくづき": 2}
    )
    player = battle.players[0]
    commands = battle.get_available_action_commands(player)
    assert all(cmd.idx != 0 for cmd in commands)


def test_じごくづき_実行ブロック():
    """じごくづき: 音技の実行をブロックする"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["うたう"])],
        ally_volatile={"じごくづき": 2}
    )
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)


def test_じごくづき_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
            foe=[Pokemon("ピカチュウ")],
            ally=[Pokemon("ピカチュウ")],
              ally_volatile={"じごくづき": n_turn}
            )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("じごくづき")
        battle.events.emit(Event.ON_TURN_END_3)
    assert not mon.has_volatile("じごくづき")


def test_じごくづき_交代で解除():
    battle = t.start_battle(
            foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"じごくづき": 99}
    )
    battle.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.players[0].active_mon.has_volatile("じごくづき")


def test_使える技がなければわるあがきになる():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["うたう"])],
        ally_volatile={"じごくづき": 2}
    )
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]

# ──────────────────────────────────────────────────────────────────
# じゅうでん
# ──────────────────────────────────────────────────────────────────


def test_じゅうでん_でんき技強化():
    battle = t.start_battle(
            foe=[Pokemon("ピカチュウ")],
            ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
            ally_volatile={"じゅうでん": 1}
    )
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)
    assert not battle.actives[0].has_volatile("じゅうでん")


def test_じゅうでん_非でんき技では残る():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        ally_volatile={"じゅうでん": 1}
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)
    assert battle.actives[0].has_volatile("じゅうでん")

# ──────────────────────────────────────────────────────────────────
# タールショット
# ──────────────────────────────────────────────────────────────────


def test_タールショット_ほのお弱点付与():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["ひのこ"])],
        foe_volatile={"タールショット": 1}
    )
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER)


def test_タールショット_ほのお以外は変化しない():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
    ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    foe_volatile={"タールショット": 1}
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER)

# ──────────────────────────────────────────────────────────────────
# ちいさくなる
# ──────────────────────────────────────────────────────────────────


minimize_enhance_moves = [
    "ふみつけ", "のしかかり", "ドラゴンダイブ", "ヒートスタンプ", "ヘビーボンバー",
    "フライングプレス", "サンダーダイブ"
]

# TODO : パラメタライズしてminimize_enhance_movesの技すべてでテストする


def test_ちいさくなる_minimize技が必中化して威力2倍():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["のしかかり"])],
        foe_volatile={"ちいさくなる": 1}
    )
    assert t.calc_accuracy(battle) is None
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_ちいさくなる_対象外技には影響しない():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe_volatile={"ちいさくなる": 1}
    )
    assert t.calc_accuracy(battle, base=30) == 30
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096

# ──────────────────────────────────────────────────────────────────
# ちょうはつ
# ──────────────────────────────────────────────────────────────────


def test_ちょうはつ_変化技は使えない():
    battle = t.start_battle(
            foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["ひかりのかべ"])],
        ally_volatile={"ちょうはつ": 3},
    )
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED)


def test_ちょうはつ_攻撃技は使える():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        ally_volatile={"ちょうはつ": 3},
    )
    assert t.check_event_result(battle, Event.ON_CHECK_ACTION)


def test_ちょうはつ_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"ちょうはつ": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("ちょうはつ")
        battle.events.emit(Event.ON_TURN_END_3)
    assert not mon.has_volatile("ちょうはつ")

# ──────────────────────────────────────────────────────────────────
# でんじふゆう
# ──────────────────────────────────────────────────────────────────


def test_でんじふゆう():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"でんじふゆう": 1},
    )
    assert battle.query_manager.is_floating(battle.actives[0])


def test_でんじふゆう_じめん技を無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("サンド", moves=["じしん"])],
        ally_volatile={"でんじふゆう": 5},
    )
    mon = battle.actives[0]
    hp = mon.hp
    battle.advance_turn()
    assert mon.hp == hp


def test_でんじふゆう_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"でんじふゆう": n_turn},
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("でんじふゆう")
        battle.events.emit(Event.ON_TURN_END_3)
    assert not mon.has_volatile("でんじふゆう")


# ──────────────────────────────────────────────────────────────────
# とくせいなし
# ──────────────────────────────────────────────────────────────────


# TODO : テスト実装


# ──────────────────────────────────────────────────────────────────
# にげられない
# ──────────────────────────────────────────────────────────────────


def test_にげられない_交代不可():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    assert not t.can_switch(battle, 0)


# ──────────────────────────────────────────────────────────────────
# ねむけ
# ──────────────────────────────────────────────────────────────────

def test_ねむけ_ターン経過でねむりになる():
    n_turn = 2
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"ねむけ": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("ねむけ")
        assert not mon.has_ailment("ねむり")
        battle.events.emit(Event.ON_TURN_END_3)
    assert not mon.has_volatile("ねむけ")
    assert mon.has_ailment("ねむり")


# ──────────────────────────────────────────────────────────────────
# ねをはる
# ──────────────────────────────────────────────────────────────────


def test_ねをはる_回復():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"ねをはる": 1}
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == 1 + mon.max_hp // 16
    assert t.log_contains(battle, LogCode.HP_CHANGED)


def test_ねをはる_交代不可():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"ねをはる": 1},
    )
    assert not t.can_switch(battle, 0)


def test_ねをはる_浮遊無効():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ポッポ")],
    )
    assert not battle.query_manager.is_floating(battle.actives[0])


# ──────────────────────────────────────────────────────────────────
# のろい
# ──────────────────────────────────────────────────────────────────


def test_のろい_ダメージ():
    """のろい: ターン終了時ダメージ"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"のろい": 1}
    )
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END_3)
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 4
    assert t.log_contains(battle, LogCode.HP_CHANGED)


# ──────────────────────────────────────────────────────────────────
# バインド
# ──────────────────────────────────────────────────────────────────


def test_バインド_ターン経過でダメージ():
    n_turn = 2
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 2},
    )
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 8
    for t in range(n_turn):
        assert mon.has_volatile("バインド")
        battle.events.emit(Event.ON_TURN_END_3)
        assert mon.hp == mon.max_hp - expected_damage*(t + 1)
        assert t.log_contains(battle, LogCode.HP_CHANGED)

    assert not mon.has_volatile("バインド")


def test_バインド_交代不可():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"バインド": 99},
    )
    assert not t.can_switch(battle, 0)


def test_バインド_発生源が交代すると解除():
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        foe_volatile={"バインド": 99},
    )
    t.reserve_command(battle, ally_command=Command.SWITCH_1)
    battle.advance_turn()
    assert not battle.actives[1].has_volatile("バインド")

# ──────────────────────────────────────────────────────────────────
# ひるみ
# ──────────────────────────────────────────────────────────────────


def test_ひるみ_行動不能():
    battle = t.start_battle(
          foe=[Pokemon("ピカチュウ")],
          ally=[Pokemon("ピカチュウ")],
          ally_volatile={"ひるみ": 1}
          )
    attacker, defender = battle.actives
    can_move = battle.events.emit(
        Event.ON_CHECK_ACTION,
        BattleContext(attacker=attacker, defender=defender)
    )
    assert not can_move
    assert not attacker.has_volatile("ひるみ")
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED)

# ──────────────────────────────────────────────────────────────────
# ふういん
# ──────────────────────────────────────────────────────────────────


def test_ふういん_共通技は使えない():
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


def test_ふういん_非共通技は使える():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["なきごえ"])],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_volatile={"ふういん": 1},
    )
    attacker, defender = battle.actives
    can_move = battle.events.emit(
        Event.ON_CHECK_ACTION,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        attacker.moves[0],
    )
    assert can_move

# ──────────────────────────────────────────────────────────────────
# ほろびのうた
# ──────────────────────────────────────────────────────────────────


def test_ほろびのうた_ターン経過で瀕死():
    n_turn = 3
    battle = t.start_battle(
          foe=[Pokemon("ピカチュウ")],
          ally=[Pokemon("ピカチュウ")],
          ally_volatile={"ほろびのうた": n_turn}
    )
    mon = battle.actives[0]
    for t in range(n_turn):
        assert mon.has_volatile("ほろびのうた")
        assert mon.alive
        battle.events.emit(Event.ON_TURN_END_3)
        assert mon.volatiles["ほろびのうた"].count == n_turn - (t + 1)

    assert mon.fainted

# ──────────────────────────────────────────────────────────────────
# マジックコート
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# まるくなる
# ──────────────────────────────────────────────────────────────────

# TODO : アイスボールもパラメタライズでテスト
 def test_まるくなる():
    """まるくなる: ころがる・アイスボールの威力が2倍になる"""
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["ころがる"])],
        ally_volatile = {"まるくなる": 1}
    )
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_まるくなる_他技は倍にならない():
    """まるくなる: ころがる以外では威力変化なし"""
    battle= t.start_battle(
            foe=[Pokemon("ピカチュウ")],
            ally = [Pokemon("ピカチュウ", moves=["たいあたり"])],
            ally_volatile = {"まるくなる": 1}
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


# ──────────────────────────────────────────────────────────────────
# みがわり
# ──────────────────────────────────────────────────────────────────

def test_みがわり_無効化():
    """みがわり: 技を無効化する"""
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")],
                            ally = [Pokemon("ピカチュウ", moves=["キノコのほうし"])],
                            foe_volatile = {"みがわり": 1},
                            )
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE_IMMUNE)
    assert t.log_contains(battle, LogCode.MOVE_IMMUNE)


# TODO : 技の威力を固定して、みがわりのHP減少量が正しいか確認するように修正
def test_みがわり_攻撃によりみがわりのHPが減る():
    battle= t.start_battle(
           ally=[Pokemon("ピカチュウ")],
            foe = [Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=100)
    volatile = defender.volatiles["みがわり"]
    battle.advance_turn()
    assert 0 < volatile.hp < 100
    assert t.log_contains(battle, LogCode.HIT_SUBSTITUTE)


def test_みがわり_破壊():
    battle= t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe = [Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=1)
    battle.advance_turn()
    assert not defender.has_volatile("みがわり")
    assert t.log_contains(battle, LogCode.HIT_SUBSTITUTE)

# ──────────────────────────────────────────────────────────────────
# みちづれ
# ──────────────────────────────────────────────────────────────────


def test_みちづれ_発動条件を満たせば両者ひんし():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_volatile = {"みちづれ": 1},
    )
    attacker, defender = battle.actives
    defender._hp = 1  # 確実にひんしになるようにHPを1にする
    battle.advance_turn()  # 1ターン進める
    assert attacker.fainted
    assert defender.fainted
    assert battle.judge_winner() is battle.players[1]
    assert t.log_contains(battle, LogCode.HP_CHANGED)


def test_みちづれ_倒しきれなければ不発():
    battle= t.start_battle(
           foe=[Pokemon("ピカチュウ")],
                            ally = [Pokemon("ピカチュウ", moves=["たいあたり"])],
                            foe_volatile = {"みちづれ": 1},
                            )
    attacker, defender = battle.actives
    battle.advance_turn()
    assert attacker.alive
    assert defender.alive

# ──────────────────────────────────────────────────────────────────
# メロメロ
# ──────────────────────────────────────────────────────────────────


def test_メロメロ_行動不能():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ")],
        ally_volatile = {"メロメロ": 1},
    )
    # 行動不能を強制
    battle.test_option.trigger_volatile = True
    assert not t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED)


def test_メロメロ_行動可能():
    """メロメロ: 行動可能（永続効果維持）"""
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ")],
        ally_volatile = {"メロメロ": 1},
    )
    # 行動を許可
    battle.test_option.trigger_volatile = False
    assert t.check_event_result(battle, Event.ON_CHECK_ACTION)
    assert t.log_contains(battle, LogCode.VOLATILE_STATUS)

# ──────────────────────────────────────────────────────────────────
# やどりぎのタネ
# ──────────────────────────────────────────────────────────────────


def test_やどりぎのタネ():
    """やどりぎのタネ: ターン終了時ダメージ"""
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ")],
        ally_volatile = {"やどりぎのタネ": 1}
    )
    from_mon, to_mon = battle.actives
    to_mon._hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    damage = from_mon.max_hp - from_mon.hp
    assert damage == from_mon.max_hp // 8
    assert to_mon.hp == 1 + damage
    assert t.log_contains(battle, LogCode.HP_CHANGED)


def test_やどりぎのタネ_回復先満タンでも対象のHPは減る():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ")],
        ally_volatile = {"やどりぎのタネ": 1}
    )
    target_mon, heal_mon = battle.actives
    heal_hp = heal_mon.hp
    battle.events.emit(Event.ON_TURN_END_3)
    assert target_mon.hp == target_mon.max_hp - target_mon.max_hp // 8
    assert heal_mon.hp == heal_hp

# ──────────────────────────────────────────────────────────────────
# ロックオン
# ──────────────────────────────────────────────────────────────────


def test_ロックオン():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ")],
        ally_volatile = {"ロックオン": 1},
    )
    assert t.calc_accuracy(battle, base=30) is None
    assert not battle.actives[0].has_volatile("ロックオン")


def test_ロックオン_無効相手でも解除される():
    battle= t.start_battle(
        ally = [Pokemon("ピカチュウ", moves=["じしん"])],
        foe = [Pokemon("ポッポ")],
        ally_volatile = {"ロックオン": 1},
    )
    assert t.calc_accuracy(battle, base=30) is None
    assert not battle.actives[0].has_volatile("ロックオン")


# ──────────────────────────────────────────────────────────────────
# まもる、トーチカ、キングシールド、スレッドトラップ、かえんのまもり
# ──────────────────────────────────────────────────────────────────
# TODO : これらの効果は似ているので、パラメタライズしてまとめる
def test_まもる_攻撃技を無効化():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)

def test_まもる_相手が対象の変化技を無効化():
    # TODO : かえんのまもりは変化技を防げないので、結果もパラメタライズで切り替える
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["キノコのほうし"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)


def test_まもる_相手自身が対象の技は無効化しない():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["つるぎのまい"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE)


def test_まもる_ターン終了で解除():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ")]
    )
    mon= battle.actives[0]
    battle.volatile_manager.apply(mon, "まもる", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("まもる")


def test_トーチカ():
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")], 
          ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
                            )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)
    assert battle.actives[0].has_ailment("どく")


def test_トーチカ_非接触では毒にならない():
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")],
          ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
                            )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert not battle.actives[0].ailment.is_active


def test_トーチカ_ターン終了で解除():
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon= battle.actives[0]
    battle.volatile_manager.apply(mon, "トーチカ", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("トーチカ")


def test_キングシールド():
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")],
          ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)
    assert battle.actives[0].rank["A"] == -1


def test_キングシールド_非接触では攻撃が下がらない():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert battle.actives[0].rank["A"] == 0


def test_キングシールド_ターン終了で解除():
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon= battle.actives[0]
    battle.volatile_manager.apply(mon, "キングシールド", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("キングシールド")


def test_スレッドトラップ():
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")],
                            ally = [Pokemon("ピカチュウ", moves=["たいあたり"])],
                            )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)
    assert battle.actives[0].rank["S"] == -1


def test_スレッドトラップ_非接触では素早さが下がらない():
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")],
          ally = [Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert battle.actives[0].rank["S"] == 0


def test_スレッドトラップ_ターン終了で解除():
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon= battle.actives[0]
    battle.volatile_manager.apply(mon, "スレッドトラップ", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("スレッドトラップ")


def test_かえんのまもり():
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")],
          ally = [Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert t.log_contains(battle, LogCode.PROTECT_SUCCESS)
    assert battle.actives[0].has_ailment("やけど")


def test_かえんのまもり_非接触ではやけどにならない():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert not battle.actives[0].ailment.is_active


def test_かえんのまもり_変化技は防げない():
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["でんじは"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE)


def test_かえんのまもり_ターン終了で解除():
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    mon= battle.actives[0]
    battle.volatile_manager.apply(mon, "かえんのまもり", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("かえんのまもり")

# ──────────────────────────────────────────────────────────────────
# あなをほる、そらをとぶ、ダイビング、シャドーダイブ
# ──────────────────────────────────────────────────────────────────

# TODO : 類似効果のテストはパラメタライズしてまとめる

def test_あなをほる_回避():
    """技を回避する"""
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    attacker, defender= battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="あなをほる")
    result= battle.events.emit(
        Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert not result


def test_あなをほる_命中():
    """技が命中する"""
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["じしん"])],
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
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    attacker, defender= battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="そらをとぶ")
    result= battle.events.emit(
       Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert not result


def test_そらをとぶ_命中():
    """技が命中する"""
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["かみなり"])],
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
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    attacker, defender= battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="ダイビング")
    result= battle.events.emit(
       Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert not result


def test_ダイビング_命中():
    """技が命中する"""
    battle= t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally = [Pokemon("ピカチュウ", moves=["なみのり"])],
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
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    attacker, defender= battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move="シャドーダイブ")
    result= battle.events.emit(
       Event.ON_CHECK_MOVE,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
        assert not result


def test_シャドーダイブ_命中():
    """技が命中しない"""
    battle= t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally = [Pokemon("ピカチュウ", moves=["シャドーダイブ"])],
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
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")],
          ally=[Pokemon("ピカチュウ", moves=["あなをほる"]), Pokemon("ライチュウ")],
          )
                            battle.volatile_manager.apply(battle.actives[0], "かくれる", count=1, move="あなをほる")
                            assert not t.can_switch(battle, 0)


def test_あなをほる_潜伏中はコマンドが固定される():
                            battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally = [Pokemon("ピカチュウ", moves=["あなをほる", "なきごえ"])],
                            )
                            mon = battle.actives[0]
                                battle.volatile_manager.apply(mon, "かくれる", count=1, move="あなをほる")
                                commands = battle.get_available_action_commands(battle.players[0])
                                assert commands == [Command.FORCED]


def test_あなをほる_強制行動ターンはPPを消費しない():
    battle= t.start_battle(
          foe=[Pokemon("ピカチュウ")],
                            ally = [Pokemon("ピカチュウ", moves=["あなをほる"])],
                            )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "かくれる", count=1, move="あなをほる")
    initial_pp = attacker.moves[0].pp
    battle.advance_turn()
    assert attacker.moves[0].pp == initial_pp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
