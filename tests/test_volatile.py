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
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"アクアリング": 1}
    )
    battle.actives[0].hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    actual_heal = battle.actives[0].hp - 1
    assert actual_heal == battle.actives[0].max_hp // 16


def test_アクアリング_かいふくふうじ中は回復しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"アクアリング": 1, "かいふくふうじ": 1}
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == 1

# ──────────────────────────────────────────────────────────────────
# あばれる
# ──────────────────────────────────────────────────────────────────


def test_あばれる_行動固定():
    """あばれる: 強制行動"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["あばれる"])],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=2, move_name="あばれる")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.FORCED]

    initial_pp = attacker.moves[0].pp
    battle.advance_turn()  # 1ターン進める
    assert attacker.moves[0].pp == initial_pp, "あばれるで技のPPが消費されている"


def test_あばれる_カウント進行():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"あばれる": 2}
    )
    attacker, defender = battle.actives
    ctx = BattleContext(attacker=attacker, defender=defender)
    battle.events.emit(Event.ON_DAMAGE_HIT, ctx)
    assert attacker.volatiles["あばれる"].count == 1
    battle.events.emit(Event.ON_DAMAGE_HIT, ctx)
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


# ──────────────────────────────────────────────────────────────────
# あめまみれ
# ──────────────────────────────────────────────────────────────────


def test_あめまみれ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"あめまみれ": 2}
    )
    battle.events.emit(Event.ON_TURN_END_3)
    assert battle.actives[0].rank["S"] == -1


# ──────────────────────────────────────────────────────────────────
# アンコール
# ──────────────────────────────────────────────────────────────────


def test_アンコール():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = player.active
    battle.volatile_manager.apply(mon, "アンコール", move_name="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index == 1 for cmd in commands)


def test_アンコール_実行時も技固定():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "アンコール", move_name="なきごえ")
    t.run_move(battle, 0, move_idx=0)
    assert attacker.executed_move.name == "なきごえ"


def test_アンコール_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"アンコール": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("アンコール")
        t.emit_turn_end_events(battle)
    assert not mon.has_volatile("アンコール")


def test_アンコール_対象技のPPが0だとわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    mon = battle.players[0].active
    battle.volatile_manager.apply(mon, "アンコール", move_name="たいあたり")
    mon.moves[0].pp = 0
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_アンコール_対象技がかなしばりで使えないとわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "アンコール", move_name="たいあたり")
    battle.volatile_manager.apply(mon, "かなしばり", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]

# ──────────────────────────────────────────────────────────────────
# いちゃもん
# ──────────────────────────────────────────────────────────────────


def test_いちゃもん_コマンド制限():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index == 1 for cmd in commands), "いちゃもんでlast_move_name以外の技が使用可能"


def test_いちゃもん_別の技は選択できる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ", "でんこうせっか"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    move_indices = {cmd.index for cmd in commands if cmd.is_move_family}
    assert move_indices == {1, 2}


def test_いちゃもん_技が1つしかない場合はわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]

# ──────────────────────────────────────────────────────────────────
# うちおとす
# ──────────────────────────────────────────────────────────────────


def test_うちおとす_飛行タイプにじめん技が有効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["じしん"])],
        team1=[Pokemon("ポッポ")],
        volatile1={"うちおとす": 1},
    )
    attacker, defender = battle.actives
    assert not battle.query_manager.is_floating(defender)

    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp, battle.print_logs()


def test_うちおとす_でんじふゆうより優先される():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ポッポ")],
        volatile0={"うちおとす": 1, "でんじふゆう": 5}
    )
    assert not battle.query_manager.is_floating(battle.actives[0])


# ──────────────────────────────────────────────────────────────────
# おんねん
# ──────────────────────────────────────────────────────────────────


def test_おんねん_PP枯渇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"おんねん": 1},
    )
    attacker, defender = battle.actives
    defender.hp = 1
    battle.run_move(attacker, attacker.moves[0])
    assert attacker.moves[0].pp == 0
    assert defender.fainted


def test_おんねん_倒しきれないと不発():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"おんねん": 1},
    )
    attacker, defender = battle.actives
    assert attacker.moves[0].pp > 0

# ──────────────────────────────────────────────────────────────────
# かいふくふうじ
# ──────────────────────────────────────────────────────────────────


def test_かいふくふうじ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": 1},
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.modify_hp(mon, +10)
    assert mon.hp == 1


def test_かいふくふうじ_カウント進行():
    n_turn = 1
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": n_turn},
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("かいふくふうじ")
        t.emit_turn_end_events(battle)
    assert not mon.has_volatile("かいふくふうじ")


def test_かいふくふうじ_いたみわけは防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["いたみわけ"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    battle.run_move(attacker, attacker.moves[0])
    assert attacker.hp > 1
    assert defender.hp < defender.max_hp

# ──────────────────────────────────────────────────────────────────
# かなしばり
# ──────────────────────────────────────────────────────────────────


def test_かなしばり_コマンド制限():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かなしばり", move_name="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index != 0 for cmd in commands)


def test_かなしばり_実行ブロック():
    """かなしばり: 封じた技の実行をブロックする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(attacker, "かなしばり", move_name="たいあたり")
    battle.run_move(attacker, attacker.moves[0])
    assert not battle.move_executor.action_success


def test_かなしばり_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"かなしばり": n_turn}
    )
    mon = battle.actives[0]
    mon.volatiles["かなしばり"].move_name = "たいあたり"
    for _ in range(n_turn):
        assert mon.has_volatile("かなしばり")
        battle.events.emit(Event.ON_TURN_END_3)
    assert not mon.has_volatile("かなしばり")


def test_かなしばり_交代で解除():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        volatile0={"かなしばり": 99},
    )
    mon = battle.actives[0]
    mon.volatiles["かなしばり"].move_name = "たいあたり"
    battle.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.players[0].active.has_volatile("かなしばり")

# ──────────────────────────────────────────────────────────────────
# きゅうしょアップ
# ──────────────────────────────────────────────────────────────────


def test_きゅうしょアップ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"きゅうしょアップ": 1}
    )
    attacker, defender = battle.actives
    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender),
        2
    )
    assert rank == 3


# ──────────────────────────────────────────────────────────────────
# こだわり
# ──────────────────────────────────────────────────────────────────


def test_こだわり():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こだわり", move_name="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index == 1 for cmd in commands)


def test_こだわり_交代で解除():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        volatile0={"こだわり": 1},
    )
    mon = battle.actives[0]
    mon.volatiles["こだわり"].move_name = "たいあたり"
    battle.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.players[0].active.has_volatile("こだわり")


def test_こだわり_固定技のPPが0だとわるあがきになる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.moves[0].pp = 0
    battle.volatile_manager.apply(mon, "こだわり", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_こだわり_固定技がかなしばりで使えないとわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり", "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こだわり", move_name="たいあたり")
    battle.volatile_manager.apply(mon, "かなしばり", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]

# ──────────────────────────────────────────────────────────────────
# こんらん
# ──────────────────────────────────────────────────────────────────


def test_こんらん_自傷ダメージ():
    """こんらん: 自傷ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2}
    )
    attacker, defender = battle.actives
    # 自傷を強制
    battle.test_option.trigger_volatile = True
    battle.run_move(attacker, attacker.moves[0])
    assert not battle.move_executor.action_success
    assert attacker.hp < attacker.max_hp
    assert defender.hp == defender.max_hp


def test_こんらん_通常行動():
    """こんらん: 通常行動可能"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2}
    )
    attacker, defender = battle.actives
    # 行動を許可
    battle.test_option.trigger_volatile = False
    battle.run_move(attacker, attacker.moves[0])
    assert battle.move_executor.action_success
    assert attacker.hp == attacker.max_hp


def test_こんらん_カウント満了で解除():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 1}
    )
    attacker, defender = battle.actives
    assert attacker.has_volatile("こんらん")
    battle.run_move(attacker, attacker.moves[0])
    assert not attacker.has_volatile("こんらん")

# ──────────────────────────────────────────────────────────────────
# さわぐ / さわがしい
# ──────────────────────────────────────────────────────────────────

# TODO : さわぐ・さわがしいで共通化できるテストはパラメタライズする


def test_さわぐ_ねむりを防ぐ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"さわぐ": 2}
    )
    assert not battle.ailment_manager.apply(battle.actives[0], "ねむり")


def test_さわぐ_ねむけを防ぐ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"さわぐ": 2}
    )
    assert not battle.volatile_manager.apply(battle.actives[0], "ねむけ", count=2)


def test_さわがしい_ねむりを防ぐ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile1={"さわがしい": 2}
    )
    assert not battle.ailment_manager.apply(battle.actives[1], "ねむり")


def test_さわがしい_ねむけを防ぐ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile1={"さわがしい": 2}
    )
    assert not battle.volatile_manager.apply(battle.actives[1], "ねむけ", count=2)


def test_さわぐ終了時_さわがしいを解除する():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")],
        volatile0={"さわぐ": 1},
        volatile1={"さわがしい": 2},
    )
    battle.events.emit(Event.ON_TURN_END_3)
    assert not battle.actives[0].has_volatile("さわぐ")
    assert not battle.actives[1].has_volatile("さわがしい")


def test_さわぐ交代時_さわがしいを解除する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"さわぐ": 2},
        volatile1={"さわがしい": 2},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert not battle.actives[1].has_volatile("さわがしい")


def test_さわぐ_技固定():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["さわぐ", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "さわぐ", count=2, move_name="さわぐ")
    assert battle.get_available_action_commands(battle.players[0]) == [Command.FORCED]

# ──────────────────────────────────────────────────────────────────
# しおづけ
# ──────────────────────────────────────────────────────────────────


# TODO : 1倍、2倍条件をすべてパラメタライズでまとめる
@pytest.mark.parametrize(
    "pokemon, expected_frac",
    [
        ("ピカチュウ", 8),
        ("ゼニガメ", 4),
        ("コイル", 4),
        ("エンペルト", 4),
    ]
)
def test_しおづけ(pokemon, expected_frac):
    """しおづけ: ターン終了時ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon)],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"しおづけ": 1}
    )
    mon = battle.actives[0]
    t.emit_turn_end_events(battle)
    assert mon.max_hp - mon.hp == mon.max_hp // expected_frac


# ──────────────────────────────────────────────────────────────────
# じごくづき
# ──────────────────────────────────────────────────────────────────


def test_じごくづき_コマンド制限():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["うたう", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    player = battle.players[0]
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index != 0 for cmd in commands)


def test_じごくづき_実行ブロック():
    """じごくづき: 音技の実行をブロックする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["うたう"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert not battle.move_executor.action_success


def test_じごくづき_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("じごくづき")
        t.emit_turn_end_events(battle)
    assert not mon.has_volatile("じごくづき")


def test_使える技がなければわるあがきになる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["うたう"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]

# ──────────────────────────────────────────────────────────────────
# じゅうでん
# ──────────────────────────────────────────────────────────────────


def test_じゅうでん_でんき技強化():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        volatile0={"じゅうでん": 1}
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert 8192 == battle.damage_calculator.power_modifier
    assert not battle.actives[0].has_volatile("じゅうでん")


def test_じゅうでん_非でんき技では残る():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        volatile0={"じゅうでん": 1}
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert 4096 == battle.damage_calculator.power_modifier
    assert battle.actives[0].has_volatile("じゅうでん")

# ──────────────────────────────────────────────────────────────────
# タールショット
# ──────────────────────────────────────────────────────────────────


def test_タールショット_ほのお弱点付与():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["ひのこ"])],
        volatile1={"タールショット": 1}
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert 8192 == battle.damage_calculator.def_type_modifier


def test_タールショット_ほのお以外は変化しない():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
                            volatile1={"タールショット": 1}
                            )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert 4096 == battle.damage_calculator.def_type_modifier

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
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["のしかかり"])],
        volatile1={"ちいさくなる": 1}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None
    assert 8192 == battle.damage_calculator.power_modifier


def test_ちいさくなる_対象外技には影響しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        volatile1={"ちいさくなる": 1}
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy
    assert 4096 == battle.damage_calculator.power_modifier

# ──────────────────────────────────────────────────────────────────
# ちょうはつ
# ──────────────────────────────────────────────────────────────────


def test_ちょうはつ_変化技は使えない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["ひかりのかべ"])],
        volatile0={"ちょうはつ": 3},
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert not battle.move_executor.action_success


def test_ちょうはつ_攻撃技は使える():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        volatile0={"ちょうはつ": 3},
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert battle.move_executor.action_success


def test_ちょうはつ_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ちょうはつ": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("ちょうはつ")
        t.emit_turn_end_events(battle)
    assert not mon.has_volatile("ちょうはつ")

# ──────────────────────────────────────────────────────────────────
# でんじふゆう
# ──────────────────────────────────────────────────────────────────


def test_でんじふゆう_じめん技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", moves=["じしん"])],
        volatile0={"でんじふゆう": 5},
    )
    assert battle.query_manager.is_floating(battle.actives[0])

    t.run_move(battle, 1)
    assert battle.damage_calculator.def_type_modifier is None
    assert battle.actives[0].hp == battle.actives[0].max_hp


def test_でんじふゆう_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"でんじふゆう": n_turn},
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("でんじふゆう")
        t.emit_turn_end_events(battle)
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
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        volatile0={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    assert not t.can_switch(battle, 0)


# ──────────────────────────────────────────────────────────────────
# ねむけ
# ──────────────────────────────────────────────────────────────────

def test_ねむけ_ターン経過でねむりになる():
    n_turn = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ねむけ": n_turn}
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
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1}
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == 1 + mon.max_hp // 16


def test_ねをはる_交代不可():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        volatile0={"ねをはる": 1},
    )
    assert not t.can_switch(battle, 0)


def test_ねをはる_浮遊無効():
    battle = t.start_battle(
        team0=[Pokemon("ポッポ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1},
    )
    assert not battle.query_manager.is_floating(battle.actives[0])


# ──────────────────────────────────────────────────────────────────
# のろい
# ──────────────────────────────────────────────────────────────────


def test_のろい_ダメージ():
    """のろい: ターン終了時ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"のろい": 1}
    )
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END_3)
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 4


# ──────────────────────────────────────────────────────────────────
# バインド
# ──────────────────────────────────────────────────────────────────


def test_バインド_ターン経過でダメージ():
    n_turn = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"バインド": 2},
    )
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 8

    # 1ターン目の終了時にダメージ
    t.emit_turn_end_events(battle)
    assert mon.has_volatile("バインド")
    assert mon.hp == mon.max_hp - expected_damage

    # 解除されるターンにはダメージを受けない
    t.emit_turn_end_events(battle)
    assert not mon.has_volatile("バインド")
    assert mon.hp == mon.max_hp - expected_damage


def test_バインド_交代不可():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        volatile0={"バインド": 99},
    )
    assert not t.can_switch(battle, 0)


def test_バインド_発生源が交代すると解除():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"バインド": 99},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert not battle.actives[1].has_volatile("バインド")

# ──────────────────────────────────────────────────────────────────
# ひるみ
# ──────────────────────────────────────────────────────────────────


def test_ひるみ_行動不能():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ひるみ": 1}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False

# ──────────────────────────────────────────────────────────────────
# ふういん
# ──────────────────────────────────────────────────────────────────


def test_ふういん_共通技は使えない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        volatile1={"ふういん": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False


def test_ふういん_非共通技は使える():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        volatile1={"ふういん": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is True

# ──────────────────────────────────────────────────────────────────
# ほろびのうた
# ──────────────────────────────────────────────────────────────────


def test_ほろびのうた_ターン経過で瀕死():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 2}
    )
    mon = battle.actives[0]

    t.emit_turn_end_events(battle)
    assert mon.volatiles["ほろびのうた"].count == 1
    assert mon.alive

    t.emit_turn_end_events(battle)
    assert not mon.has_volatile("ほろびのうた")
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
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["ころがる"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"まるくなる": 1}
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert 8192 == battle.damage_calculator.power_modifier


def test_まるくなる_他技は倍にならない():
    """まるくなる: ころがる以外では威力変化なし"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        volatile0={"まるくなる": 1}
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert 4096 == battle.damage_calculator.power_modifier


# ──────────────────────────────────────────────────────────────────
# みがわり
# ──────────────────────────────────────────────────────────────────

def test_みがわり_無効化():
    """みがわり: 技を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["キノコのほうし"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みがわり": 1},
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert not battle.move_executor.move_applied


# TODO : 技の威力を固定して、みがわりのHP減少量が正しいか確認するように修正
def test_みがわり_攻撃によりみがわりのHPが減る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=100)
    volatile = defender.volatiles["みがわり"]
    battle.advance_turn()
    assert 0 < volatile.hp < 100


def test_みがわり_破壊():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=1)
    t.run_move(battle, 1)
    assert not defender.has_volatile("みがわり")

# ──────────────────────────────────────────────────────────────────
# みちづれ
# ──────────────────────────────────────────────────────────────────


def test_みちづれ_発動条件を満たせば両者ひんし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    defender.hp = 1  # 確実にひんしになるようにHPを1にする
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.fainted, battle.print_logs()
    assert battle.judge_winner() is battle.players[0]


def test_みちづれ_倒しきれなければ不発():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        volatile1={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 1)
    assert attacker.alive
    assert defender.alive

# ──────────────────────────────────────────────────────────────────
# メロメロ
# ──────────────────────────────────────────────────────────────────


def test_メロメロ_行動不能():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"メロメロ": 1},
    )
    # 行動不能を強制
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success


def test_メロメロ_行動可能():
    """メロメロ: 行動可能（永続効果維持）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"メロメロ": 1},
    )
    # 行動を許可
    battle.test_option.trigger_volatile = False
    t.run_move(battle, 0)
    assert battle.move_executor.action_success

# ──────────────────────────────────────────────────────────────────
# やどりぎのタネ
# ──────────────────────────────────────────────────────────────────


def test_やどりぎのタネ():
    """やどりぎのタネ: ターン終了時ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"やどりぎのタネ": 1}
    )
    from_mon, to_mon = battle.actives
    to_mon.hp = 1
    battle.events.emit(Event.ON_TURN_END_3)
    damage = from_mon.max_hp - from_mon.hp
    assert damage == from_mon.max_hp // 8
    assert to_mon.hp == 1 + damage


def test_やどりぎのタネ_回復先満タンでも対象のHPは減る():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"やどりぎのタネ": 1}
    )
    target_mon, heal_mon = battle.actives
    heal_hp = heal_mon.hp
    battle.events.emit(Event.ON_TURN_END_3)
    assert target_mon.hp == target_mon.max_hp - target_mon.max_hp // 8
    assert heal_mon.hp == heal_hp

# ──────────────────────────────────────────────────────────────────
# ロックオン
# ──────────────────────────────────────────────────────────────────


def test_ロックオン_必中化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ロックオン": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


# ──────────────────────────────────────────────────────────────────
# まもる、トーチカ、キングシールド、スレッドトラップ、かえんのまもり
# ──────────────────────────────────────────────────────────────────
# TODO : これらの効果は似ているので、パラメタライズしてまとめる
def test_まもる_攻撃技を無効化():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_まもる_相手が対象の変化技を無効化():
    # TODO : かえんのまもりは変化技を防げないので、結果もパラメタライズで切り替える
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["キノコのほうし"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_まもる_相手自身が対象の技は無効化しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["つるぎのまい"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


def test_まもる_ターン終了で解除():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "まもる", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("まもる")


def test_トーチカ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    assert battle.actives[0].has_ailment("どく")


def test_トーチカ_非接触では毒にならない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    t.run_move(battle, 0)
    assert not battle.actives[0].ailment.is_active


def test_トーチカ_ターン終了で解除():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "トーチカ", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("トーチカ")


def test_キングシールド():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    assert battle.actives[0].rank["A"] == -1


def test_キングシールド_非接触では攻撃が下がらない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["A"] == 0


def test_キングシールド_ターン終了で解除():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "キングシールド", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("キングシールド")


def test_スレッドトラップ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    assert battle.actives[0].rank["S"] == -1


def test_スレッドトラップ_非接触では素早さが下がらない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["S"] == 0


def test_スレッドトラップ_ターン終了で解除():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "スレッドトラップ", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("スレッドトラップ")


def test_かえんのまもり():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    assert battle.actives[0].has_ailment("やけど")


def test_かえんのまもり_非接触ではやけどにならない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    t.run_move(battle, 0)
    assert not battle.actives[0].ailment.is_active


def test_かえんのまもり_変化技は防げない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんじは"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


def test_かえんのまもり_ターン終了で解除():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かえんのまもり", count=1)
    battle.events.emit(Event.ON_TURN_END_1)
    assert not mon.has_volatile("かえんのまもり")

# ──────────────────────────────────────────────────────────────────
# あなをほる、そらをとぶ、ダイビング、シャドーダイブ
# ──────────────────────────────────────────────────────────────────

# TODO : 類似効果のテストはパラメタライズしてまとめる


def test_あなをほる_回避():
    """技を回避する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move_name="あなをほる")
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_あなをほる_命中():
    """技が命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["じしん"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "かくれる", count=1, move_name="あなをほる")
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


def test_あなをほる_潜伏中は交代できない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["あなをほる"]), Pokemon("ライチュウ")],
    )
    battle.volatile_manager.apply(battle.actives[0], "かくれる", count=1, move_name="あなをほる")
    assert not t.can_switch(battle, 0)


def test_あなをほる_潜伏中はコマンドが固定される():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["あなをほる", "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かくれる", count=1, move_name="あなをほる")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.FORCED]


def test_あなをほる_強制行動ターンはPPを消費しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["あなをほる"])],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "かくれる", count=1, move_name="あなをほる")
    initial_pp = attacker.moves[0].pp
    battle.advance_turn()
    assert attacker.moves[0].pp == initial_pp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
