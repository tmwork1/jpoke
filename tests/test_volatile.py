"""揮発性状態ハンドラの単体テスト"""
import pytest
from jpoke import Move, Pokemon
from jpoke.enums import Command
from . import test_utils as t

minimize_enhance_moves = [
    "ふみつけ", "のしかかり", "ドラゴンダイブ", "ヒートスタンプ", "ヘビーボンバー",
    "フライングプレス", "サンダーダイブ"
]


def test_アクアリング_かいふくふうじ中は回復しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"アクアリング": 1, "かいふくふうじ": 1}
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_アクアリング_交代で解除():
    """アクアリング: 交代するとアクアリング状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"アクアリング": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("アクアリング")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("アクアリング")


def test_アクアリング_回復():
    """アクアリング: ターン終了時回復"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"アクアリング": 1}
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16


def test_あなをほる_じしんは2倍ダメージ():
    """あなをほる状態の相手にじしんを使うと威力補正が2倍（8192）になる"""
    battle = t.start_battle(
        team0=[Pokemon("ディグダ", move_names=["じしん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "あなをほる", count=1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_あばれる_3ターンで解除されこんらんになる():
    """あばれる: 3ターン後に揮発性状態が解除されてこんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あばれる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=3, move_name="あばれる")
    battle.advance_turn()
    assert attacker.has_volatile("あばれる")
    battle.advance_turn()
    assert attacker.has_volatile("あばれる")
    battle.advance_turn()
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


def test_あばれる_カウント進行():
    """あばれる: 2ターン後に揮発性状態が解除されてこんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あばれる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=2, move_name="あばれる")
    battle.advance_turn()
    assert attacker.has_volatile("あばれる")
    assert not attacker.has_volatile("こんらん")
    battle.advance_turn()
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


def test_あばれる_技使用で揮発性状態付与():
    """あばれる: 技使用（ON_HIT経由）で揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あばれる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert not attacker.has_volatile("あばれる")
    t.run_move(battle, 0)
    assert attacker.has_volatile("あばれる")


def test_あばれる_行動固定():
    """あばれる: 強制行動"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["あばれる"])],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=2, move_name="あばれる")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.FORCED]

    initial_pp = attacker.moves[0].pp
    battle.advance_turn()  # 1ターン進める
    assert attacker.moves[0].pp == initial_pp, "あばれるで技のPPが消費されている"


def test_あめまみれ_1ターン経過でSマイナス1():
    """あめまみれ: ターン終了時にすばやさランクが1段階下がる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"あめまみれ": 2}
    )
    t.end_turn(battle)
    assert battle.actives[0].rank["S"] == -1


def test_あめまみれ_3ターンで合計3回Sが下がる():
    """あめまみれ: count=3の場合、3ターン連続でSランクが下がる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"あめまみれ": 3}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.rank["S"] == -1
    t.end_turn(battle)
    assert mon.rank["S"] == -2
    t.end_turn(battle)
    assert mon.rank["S"] == -3
    assert not mon.has_volatile("あめまみれ")


def test_あめまみれ_3ターン後は解除される():
    """あめまみれ: 3ターン経過後に状態が解除される"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"あめまみれ": 3}
    )
    mon = battle.actives[0]
    for _ in range(3):
        assert mon.has_volatile("あめまみれ")
        t.end_turn(battle)
    assert not mon.has_volatile("あめまみれ")


def test_アンコール():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "アンコール", move_name="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index == 1 for cmd in commands)


def test_アンコール_non_encoreラベルの技を使った相手には失敗する():
    """アンコール技: 相手がnon_encoreラベルを持つ技を最後に使っていた場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アンコール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # わるあがき（non_encoreラベル）を最後に使った状態にする
    defender.executed_move = Move("わるあがき")
    t.run_move(battle, 0)
    assert not defender.has_volatile("アンコール")


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
        t.end_turn(battle)
    assert not mon.has_volatile("アンコール")


def test_アンコール_実行時も技固定():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "アンコール", move_name="なきごえ")
    t.run_move(battle, 0, move_idx=0)
    assert attacker.executed_move.name == "なきごえ"


def test_アンコール_対象技がかなしばりで使えないとわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "アンコール", move_name="たいあたり")
    battle.volatile_manager.apply(mon, "かなしばり", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_アンコール_対象技のPPが0だとわるあがきになる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "アンコール", move_name="たいあたり")
    mon.moves[0].pp = 0
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_アンコール_未行動の相手には失敗する():
    """アンコール技: 相手がまだ技を使っていない場合（executed_moveがNone）はアンコール状態が付与されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アンコール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # executed_move は None のまま（デフォルト）
    assert defender.executed_move is None
    t.run_move(battle, 0)
    assert not defender.has_volatile("アンコール")


def test_いちゃもん_コマンド制限():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index == 1 for cmd in commands), "いちゃもんでlast_move_name以外の技が使用可能"


def test_いちゃもん_ターン経過で消えない():
    """いちゃもん: ターン終了を経過しても状態が解除されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    t.end_turn(battle)
    assert mon.has_volatile("いちゃもん"), "いちゃもんはターン経過で解除されてはならない"


def test_いちゃもん_交代で解除される():
    """いちゃもん: 交代するといちゃもん状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"]), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    assert mon.has_volatile("いちゃもん")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("いちゃもん")


def test_いちゃもん_別の技は選択できる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ", "でんこうせっか"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    move_indices = {cmd.index for cmd in commands if cmd.is_move_family}
    assert move_indices == {1, 2}


def test_いちゃもん_技が1つしかない場合はわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_うちおとす_でんじふゆうより優先される():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ポッポ")],
        volatile0={"うちおとす": 1, "でんじふゆう": 5}
    )
    assert not battle.query.is_floating(battle.actives[0])


def test_うちおとす_ふうせんより優先される():
    """うちおとす状態のポケモンはふうせん持ちでも地面扱いになる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ポッポ", item_name="ふうせん")],
        volatile0={"うちおとす": 1}
    )
    assert not battle.query.is_floating(battle.actives[0])


def test_うちおとす_ふゆう特性より優先される():
    """うちおとす状態のポケモンはふゆう特性持ちでも地面扱いになる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ポッポ", ability_name="ふゆう")],
        volatile0={"うちおとす": 1}
    )
    assert not battle.query.is_floating(battle.actives[0])


def test_うちおとす_交代で解除される():
    """うちおとす状態は交代すると解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ポッポ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"うちおとす": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("うちおとす")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("うちおとす")


def test_うちおとす_飛行タイプにじめん技が有効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じしん"])],
        team1=[Pokemon("ポッポ")],
        volatile1={"うちおとす": 1},
    )
    attacker, defender = battle.actives
    assert not battle.query.is_floating(defender)

    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_おんねん_PP既に0なら不発():
    """おんねん: 技のPPがすでに0の場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"おんねん": 1},
    )
    attacker, defender = battle.actives
    attacker.moves[0].pp = 0
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.moves[0].pp == 0


def test_おんねん_PP枯渇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"おんねん": 1},
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.moves[0].pp == 0


def test_おんねん_わるあがきは対象外():
    """おんねん: わるあがきでひんしにしてもPPは消失しない"""
    from jpoke.model import Move
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"おんねん": 1},
    )
    attacker, defender = battle.actives
    defender.hp = 1
    # わるあがきを直接実行する
    battle.run_move(attacker, Move("わるあがき"))
    assert defender.fainted
    # わるあがきのPPは初期値（99999）のまま変化しない
    from jpoke.data.move import MOVES
    assert MOVES["わるあがき"].pp == 99999


def test_おんねん_交代で解除():
    """おんねん: おんねん状態は交代で解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        volatile1={"おんねん": 1},
    )
    defender = battle.actives[1]
    assert defender.has_volatile("おんねん")
    t.run_switch(battle, 1, 1)
    assert not defender.has_volatile("おんねん")


def test_おんねん_倒しきれないと不発():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"おんねん": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.fainted
    assert attacker.moves[0].pp > 0


def test_おんねん_次のターン行動で解除():
    """おんねん: おんねん状態のポケモンが次に行動しようとすると解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        volatile1={"おんねん": 1},
    )
    defender = battle.actives[1]
    assert defender.has_volatile("おんねん")
    # defender が行動する（ON_TRY_ACTION でおんねんが解除される）
    t.run_move(battle, 1)
    assert not defender.has_volatile("おんねん")


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


def test_かいふくふうじ_いたみわけは防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いたみわけ"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp > 1
    assert defender.hp < defender.max_hp


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
        t.end_turn(battle)
    assert not mon.has_volatile("かいふくふうじ")


def test_かいふくふうじ_交代で解除():
    """かいふくふうじ状態で交代すると状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": 99},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("かいふくふうじ")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("かいふくふうじ")


def test_かえんのまもり_接触技でやけどを付与():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].has_ailment("やけど")


def test_かえんのまもり_非接触ではやけどにならない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    t.run_move(battle, 0)
    assert not battle.actives[0].ailment.is_active


@pytest.mark.parametrize("hidden_move_name", ["あなをほる", "そらをとぶ", "ダイビング", "シャドーダイブ"])
def test_かくれる_1ターン目に揮発状態が付与される(hidden_move_name):
    """技を使った1ターン目に対応する揮発状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[hidden_move_name])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile(hidden_move_name)


@pytest.mark.parametrize("hidden_move_name,defender_name", [
    ("あなをほる", "カビゴン"),
    ("そらをとぶ", "カビゴン"),
    ("ダイビング", "カビゴン"),
    ("シャドーダイブ", "ドガース"),  # ノーマルタイプはゴースト無効なのでどくタイプを使用
])
def test_かくれる_2ターン目に技が発動して揮発状態が解除される(hidden_move_name, defender_name):
    """2ターン目に技が発動し、揮発状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[hidden_move_name])],
        team1=[Pokemon(defender_name)],
    )
    attacker = battle.actives[0]
    # 1ターン目: 揮発状態が付与される
    t.run_move(battle, 0)
    assert attacker.has_volatile(hidden_move_name)
    # 2ターン目: 技が発動して揮発状態が解除される
    t.run_move(battle, 0)
    assert not attacker.has_volatile(hidden_move_name)
    assert battle.move_executor.move_success


@pytest.mark.parametrize("hidden_move_name", ["あなをほる", "そらをとぶ", "ダイビング", "シャドーダイブ"])
def test_かくれる_強制行動ターンはPPを消費しない(hidden_move_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=[hidden_move_name])],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, hidden_move_name, count=1)
    initial_pp = attacker.moves[0].pp
    battle.advance_turn()
    assert attacker.moves[0].pp == initial_pp


@pytest.mark.parametrize("hidden_move_name", ["あなをほる", "そらをとぶ", "ダイビング", "シャドーダイブ"])
def test_かくれる_潜伏中はコマンドが固定される(hidden_move_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=[hidden_move_name, "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, hidden_move_name, count=1)
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.FORCED]


@pytest.mark.parametrize("hidden_move_name", ["あなをほる", "そらをとぶ", "ダイビング", "シャドーダイブ"])
def test_かくれる_潜伏中は交代できない(hidden_move_name):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[hidden_move_name]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.volatile_manager.apply(battle.actives[0], hidden_move_name, count=1)
    assert not battle.can_switch(battle.players[0])


@pytest.mark.parametrize("hidden_move_name,hit_move_name", [
    ("あなをほる", "じしん"),
    ("そらをとぶ", "かみなり"),
    ("ダイビング", "なみのり"),
])
def test_かくれる_特定技は命中する(hidden_move_name, hit_move_name):
    """潜伏中でも特定技には命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[hit_move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, hidden_move_name, count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


@pytest.mark.parametrize("hidden_move_name", ["あなをほる", "そらをとぶ", "ダイビング", "シャドーダイブ"])
def test_かくれる_通常技は回避する(hidden_move_name):
    """潜伏中は通常技を回避する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, hidden_move_name, count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_かなしばり_コマンド制限():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かなしばり", move_name="たいあたり")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index != 0 for cmd in commands)


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
        t.end_turn(battle)
    assert not mon.has_volatile("かなしばり")


def test_かなしばり_交代で解除():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かなしばり": 99},
    )
    mon = battle.actives[0]
    mon.volatiles["かなしばり"].move_name = "たいあたり"
    t.run_switch(battle, 0, 1)
    assert not battle.actives[0].has_volatile("かなしばり")
    t.run_switch(battle, 0, 1)
    assert not battle.actives[0].has_volatile("かなしばり")


def test_かなしばり_実行ブロック():
    """かなしばり: 封じた技の実行をブロックする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(attacker, "かなしばり", move_name="たいあたり")
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success


def test_きゅうしょアップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"きゅうしょアップ": 1}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 1


def test_キングシールド_接触技で攻撃を下げる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["A"] == -1


def test_キングシールド_非接触では攻撃が下がらない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["A"] == 0


def test_こだわり():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こだわり", move_name="なきごえ")
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index == 1 for cmd in commands)


def test_こだわり_交代で解除():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こだわり": 1},
    )
    mon = battle.actives[0]
    mon.volatiles["こだわり"].move_name = "たいあたり"
    t.run_switch(battle, 0, 1)
    assert not battle.actives[0].has_volatile("こだわり")
    t.run_switch(battle, 0, 1)
    assert not battle.actives[0].has_volatile("こだわり")


def test_こだわり_固定技がかなしばりで使えないとわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こだわり", move_name="たいあたり")
    battle.volatile_manager.apply(mon, "かなしばり", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_こだわり_固定技のPPが0だとわるあがきになる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.moves[0].pp = 0
    battle.volatile_manager.apply(mon, "こだわり", move_name="たいあたり")
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_こんらん_カウント満了で解除():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 1}
    )
    attacker, defender = battle.actives
    assert attacker.has_volatile("こんらん")
    t.run_move(battle, 0)
    assert not attacker.has_volatile("こんらん")


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
    t.run_move(battle, 0)
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
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert attacker.hp == attacker.max_hp


def test_さわぐ_技固定():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "さわぐ", count=2, move_name="さわぐ")
    assert battle.get_available_action_commands(battle.players[0]) == [Command.FORCED]


@pytest.mark.parametrize("volatile_name", ["さわぐ", "さわがしい"])
def test_さわぐさわがしい_ねむけを防ぐ(volatile_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={volatile_name: 2}
    )
    assert not battle.volatile_manager.apply(battle.actives[0], "ねむけ", count=2)


@pytest.mark.parametrize("volatile_name", ["さわぐ", "さわがしい"])
def test_さわぐさわがしい_ねむりを防ぐ(volatile_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={volatile_name: 2}
    )
    assert not battle.ailment_manager.apply(battle.actives[0], "ねむり")


def test_さわぐ交代時_さわがしいを解除する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"さわぐ": 2},
        volatile1={"さわがしい": 2},
    )
    t.run_switch(battle, 0, 1)
    assert not battle.actives[1].has_volatile("さわがしい")


def test_さわぐ終了時_さわがしいを解除する():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")],
        volatile0={"さわぐ": 1},
        volatile1={"さわがしい": 2},
    )
    t.end_turn(battle)
    assert not battle.actives[0].has_volatile("さわぐ")
    assert not battle.actives[1].has_volatile("さわがしい")


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
    t.end_turn(battle)
    assert mon.max_hp - mon.hp == mon.max_hp // expected_frac


def test_じごくづき_コマンド制限():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    player = battle.players[0]
    commands = battle.get_available_action_commands(player)
    assert all(cmd.index != 0 for cmd in commands)


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
        t.end_turn(battle)
    assert not mon.has_volatile("じごくづき")


def test_じごくづき_実行ブロック():
    """じごくづき: 音技の実行をブロックする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success


def test_じゅうでん_でんき技強化():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        volatile0={"じゅうでん": 1}
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.power_modifier
    assert not battle.actives[0].has_volatile("じゅうでん")


def test_じゅうでん_非でんき技では残る():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile0={"じゅうでん": 1}
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier
    assert battle.actives[0].has_volatile("じゅうでん")


def test_スレッドトラップ_接触技で素早さを下げる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["S"] == -1


def test_スレッドトラップ_非接触では素早さが下がらない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["S"] == 0


def test_タールショット_ほのお以外は変化しない():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
                            volatile1={"タールショット": 1}
                            )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_タールショット_ほのお弱点付与():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        volatile1={"タールショット": 1}
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.def_type_modifier


@pytest.mark.parametrize("move_name", minimize_enhance_moves)
def test_ちいさくなる_minimize技が必中化して威力2倍(move_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        volatile1={"ちいさくなる": 1}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None
    assert 8192 == battle.damage_calculator.power_modifier


def test_ちいさくなる_対象外技には影響しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        volatile1={"ちいさくなる": 1}
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy
    assert 4096 == battle.damage_calculator.power_modifier


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
        t.end_turn(battle)
    assert not mon.has_volatile("ちょうはつ")


def test_ちょうはつ_変化技は使えない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["ひかりのかべ"])],
        volatile0={"ちょうはつ": 3},
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success


def test_ちょうはつ_攻撃技は使える():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile0={"ちょうはつ": 3},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success


def test_でんじふゆう_じめん技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
        volatile0={"でんじふゆう": 5},
    )
    assert battle.query.is_floating(battle.actives[0])

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
        t.end_turn(battle)
    assert not mon.has_volatile("でんじふゆう")


def test_とくせいなし_特性が無効になる():
    """とくせいなし: 特性が無効になり技が効く"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="ちくでん")],
        volatile1={"とくせいなし": 5},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_とくせいなし_解除後は特性が有効になる():
    """とくせいなし: 解除後は特性が有効に戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="ちくでん")],
        volatile1={"とくせいなし": 5},
    )
    defender = battle.actives[1]
    battle.volatile_manager.remove(defender, "とくせいなし")
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp


def test_トーチカ_接触技で毒を付与():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].has_ailment("どく")


def test_トーチカ_非接触では毒にならない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    t.run_move(battle, 0)
    assert not battle.actives[0].ailment.is_active


def test_にげられない_交代不可():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    assert not battle.can_switch(battle.players[0])


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
        t.end_turn(battle)
    assert not mon.has_volatile("ねむけ")
    assert mon.has_ailment("ねむり")


def test_ねをはる_交代不可():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1},
    )
    assert not battle.can_switch(battle.players[0])


def test_ねをはる_回復():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1}
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16


def test_ねをはる_浮遊無効():
    battle = t.start_battle(
        team0=[Pokemon("ポッポ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1},
    )
    assert not battle.query.is_floating(battle.actives[0])


def test_のろい_ダメージ():
    """のろい: ターン終了時ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"のろい": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 4


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
    t.end_turn(battle)
    assert mon.has_volatile("バインド")
    assert mon.hp == mon.max_hp - expected_damage

    # 解除されるターンにはダメージを受けない
    t.end_turn(battle)
    assert not mon.has_volatile("バインド")
    assert mon.hp == mon.max_hp - expected_damage


def test_バインド_交代不可():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"バインド": 99},
    )
    assert not battle.can_switch(battle.players[0])


def test_バインド_発生源が交代すると解除():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"バインド": 99},
    )
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 1)
    assert not battle.actives[1].has_volatile("バインド")


def test_ひるみ_行動不能():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ひるみ": 1}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False


def test_ふういん_共通技は使えない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"ふういん": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False


def test_ふういん_非共通技は使える():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"ふういん": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is True


def test_ほろびのうた_ターン経過で瀕死():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 2}
    )
    mon = battle.actives[0]

    t.end_turn(battle)
    assert mon.volatiles["ほろびのうた"].count == 1
    assert mon.alive

    t.end_turn(battle)
    assert not mon.has_volatile("ほろびのうた")
    assert mon.fainted


def test_まもる_相手自身が対象の技は無効化しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


@pytest.mark.parametrize("volatile_name", [
    "まもる", "トーチカ", "キングシールド", "スレッドトラップ", "かえんのまもり"
])
def test_まもる系_ターン終了で解除(volatile_name):
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, volatile_name, count=1)
    t.end_turn(battle)
    assert not mon.has_volatile(volatile_name)


@pytest.mark.parametrize("volatile_name", [
    "まもる", "トーチカ", "キングシールド", "スレッドトラップ", "かえんのまもり"
])
def test_まもる系_攻撃技を無効化(volatile_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], volatile_name, count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


@pytest.mark.parametrize("volatile_name,blocks_status", [
    ("まもる", True),
    ("トーチカ", True),
    ("キングシールド", True),
    ("スレッドトラップ", True),
    ("かえんのまもり", False),
])
def test_まもる系_相手対象変化技への反応(volatile_name, blocks_status):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
    )
    battle.volatile_manager.apply(battle.actives[1], volatile_name, count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success == (not blocks_status)


def test_まるくなる():
    """まるくなる: ころがる・アイスボールの威力が2倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ころがる"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"まるくなる": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.power_modifier


def test_まるくなる_他技は倍にならない():
    """まるくなる: ころがる以外では威力変化なし"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile0={"まるくなる": 1}
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_みがわり_攻撃によりみがわりのHPが減る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=100)
    volatile = defender.volatiles["みがわり"]
    t.fix_damage(battle, 30)
    t.run_move(battle, 1)
    assert volatile.hp == 100 - 30
    assert defender.hp == defender.max_hp


def test_みがわり_無効化():
    """みがわり: 技を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みがわり": 1},
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.move_applied


def test_みがわり_破壊():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=1)
    t.run_move(battle, 1)
    assert not defender.has_volatile("みがわり")


def test_みちづれ_倒しきれなければ不発():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 1)
    assert attacker.alive
    assert defender.alive


def test_みちづれ_発動条件を満たせば両者ひんし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    defender.hp = 1  # 確実にひんしになるようにHPを1にする
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.fainted
    assert battle.judge_winner() is battle.players[0]


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


def test_やどりぎのタネ():
    """やどりぎのタネ: ターン終了時ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"やどりぎのタネ": 1}
    )
    from_mon, to_mon = battle.actives
    to_mon.hp = 1
    t.end_turn(battle)
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
    t.end_turn(battle)
    assert target_mon.hp == target_mon.max_hp - target_mon.max_hp // 8
    assert heal_mon.hp == heal_hp


def test_ロックオン_必中化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ロックオン": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


def test_使える技がなければわるあがきになる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    commands = battle.get_available_action_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
