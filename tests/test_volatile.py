# TODO : ファイル規模が大きいため複数モジュールに分割する

"""揮発性状態ハンドラの単体テスト"""
import pytest
from jpoke import Move, Pokemon
from jpoke.enums import Command
from . import test_utils as t

minimize_enhance_moves = [
    "ふみつけ", "のしかかり", "ドラゴンダイブ", "ヒートスタンプ", "ヘビーボンバー",
    "フライングプレス", "サンダーダイブ"
]

# TODO : ねむけ状態で交代しても眠り状態にならないことを確認するテストを追加する


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


def test_かえんのまもり_ぼうごパット持ちの接触技はやけどにならない():
    """かえんのまもり: ぼうごパットを持つ攻撃者は接触判定が無効になりやけどにならない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "かえんのまもり", count=1)
    t.run_move(battle, 0)
    assert not battle.actives[0].ailment.is_active


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


def test_かなしばり_コマンド制限で他の技は選択可能():
    """かなしばり: 封じた技以外の技は引き続き選択可能"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かなしばり", move_name="たいあたり")
    commands = battle.get_available_action_commands(player)
    move_commands = [cmd for cmd in commands if cmd.is_move_family]
    assert any(cmd.index == 1 for cmd in move_commands)


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


def test_きゅうしょアップ_交代で解除():
    """きゅうしょアップ: 交代するとリセットされる（揮発状態の共通仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ヤドラン")],
        volatile0={"きゅうしょアップ": 2}
    )
    attacker = battle.actives[0]
    assert attacker.has_volatile("きゅうしょアップ")
    t.run_switch(battle, 0, 1)
    # 交代前のポケモンが引っ込んだあとは揮発状態が消えている
    assert not attacker.has_volatile("きゅうしょアップ")


def test_きゅうしょアップ_急所ランク加算():
    """きゅうしょアップ: count値ぶん急所ランクが上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"きゅうしょアップ": 2}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 2


def test_キングシールド_変化技は防がない():
    """キングシールドは変化技（攻撃技でない）を無効化しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


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
    """こんらん: カウントが0になったときに揮発状態が解除される"""
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


def test_さわぐ_さわぎだしでねむりを起こす():
    """さわぐ: さわぎだしたとき、場のねむり状態のポケモンが目を覚ます"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3),
        accuracy=100,
    )
    foe = battle.actives[1]
    assert foe.ailment.name == "ねむり"
    t.run_move(battle, 0)
    assert not foe.ailment.is_active


def test_さわぐ_技固定():
    """さわぐ: Command.FORCED が返り、解決後の技がさわぐになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "さわぐ", count=2, move_name="さわぐ")
    assert battle.get_available_action_commands(battle.players[0]) == [Command.FORCED]
    move = battle.command_manager.resolve_move_from_command(battle.players[0], Command.FORCED)
    assert move.name == "さわぐ"


@pytest.mark.parametrize("volatile_name", ["さわぐ", "さわがしい"])
def test_さわぐさわがしい_ねむけからねむりへの移行を防ぐ(volatile_name):
    """さわぐ/さわがしい: ねむけ終了時にねむり状態への移行を防ぐ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={volatile_name: 2, "ねむけ": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.has_volatile("ねむけ")
    assert not mon.ailment.is_active


@pytest.mark.parametrize("volatile_name", ["さわぐ", "さわがしい"])
def test_さわぐさわがしい_ねむけは防がない(volatile_name):
    """さわぐ/さわがしい: ねむけ状態の付与は防がない（第五世代以降）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={volatile_name: 2}
    )
    assert battle.volatile_manager.apply(battle.actives[0], "ねむけ", count=2)


@pytest.mark.parametrize("volatile_name", ["さわぐ", "さわがしい"])
def test_さわぐさわがしい_ねむりを防ぐ(volatile_name):
    """さわぐ/さわがしい: ねむり状態の付与を防ぐ"""
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


def test_さわぐ技使用_揮発性状態を付与する():
    """さわぐ: 技使用命中時にさわぐ揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert not mon.has_volatile("さわぐ")
    t.run_move(battle, 0)
    assert mon.has_volatile("さわぐ")
    assert mon.volatiles["さわぐ"].count == 3


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
        ("ピカチュウ", 16),
        ("ゼニガメ", 8),
        ("コイル", 8),
        ("エンペルト", 8),
    ]
)
def test_しおづけ_ターン終了時ダメージ(pokemon, expected_frac):
    """しおづけ: Champions仕様のターン終了時ダメージ（通常1/16、みず・はがね1/8）"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon)],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"しおづけ": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.max_hp - mon.hp == mon.max_hp // expected_frac


def test_しおづけ_マジックガードでダメージ無効():
    """しおづけ: マジックガード特性を持つポケモンはダメージを受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"しおづけ": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_しおづけ_交代で解除():
    """しおづけ: 交代するとしおづけ状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"しおづけ": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("しおづけ")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("しおづけ")


def test_シャドーダイブ_まもる中の相手にダメージを与えられる():
    """シャドーダイブはまもる状態を貫通する（unprotectable ラベル）"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", move_names=["シャドーダイブ"])],
        team1=[Pokemon("ドガース")],
    )
    defender = battle.actives[1]
    initial_hp = defender.hp
    battle.volatile_manager.apply(defender, "まもる", count=1)
    # 溜めターン
    t.run_move(battle, 0)
    assert battle.actives[0].has_volatile("シャドーダイブ")
    # 攻撃ターン（まもる状態の相手に攻撃）
    t.run_move(battle, 0)
    assert not battle.actives[0].has_volatile("シャドーダイブ")
    assert battle.move_executor.move_success
    assert defender.hp < initial_hp


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


def test_じゅうでん_交代で解除():
    """じゅうでん: 交代するとじゅうでん状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じゅうでん": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("じゅうでん")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("じゅうでん")


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


@pytest.mark.parametrize("boost_move_name", ["かぜおこし", "たつまき"])
def test_そらをとぶ_かぜおこしたつまきの威力が2倍になる(boost_move_name):
    """そらをとぶ状態の相手にかぜおこし・たつまきを使うと威力補正が2倍（8192）になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[boost_move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "そらをとぶ", count=1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_そらをとぶ_ぼうふうが命中する():
    """そらをとぶ状態でもぼうふうは命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "そらをとぶ", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


def test_タールショット_ほのお以外は変化しない():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
                            volatile1={"タールショット": 1}
                            )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_タールショット_ほのお半減ポケモンが等倍になる():
    """タールショット状態のほのおタイプポケモンに対してほのお技が等倍になる（半減→等倍）"""
    # ヒトカゲはほのおタイプ（ほのお半減）なのでタールショット後は等倍(4096)になる
    battle = t.start_battle(
        team1=[Pokemon("ヒトカゲ")],
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
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


def test_ダイビング_その他技は威力2倍にならない():
    """ダイビング状態でないときはなみのりの威力補正なし（power_modifier=4096）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["なみのり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize("boost_move_name", ["なみのり", "うずしお"])
def test_ダイビング_なみのりうずしおは威力2倍(boost_move_name):
    """ダイビング状態の相手になみのり・うずしおを使うと威力2倍"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[boost_move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "ダイビング", count=1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


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


def test_ちょうはつ_すでにちょうはつ状態の相手には効果なし():
    """ちょうはつ技: 相手がすでにちょうはつ状態の場合は効果がない（カウントが更新されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうはつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        volatile1={"ちょうはつ": 3},
    )
    # すでにちょうはつ状態（count=3）のまま変化しないことを確認
    defender = battle.actives[1]
    assert defender.has_volatile("ちょうはつ")
    t.run_move(battle, 0)
    # volatile_manager.apply は既存状態があると False を返しカウントは更新されない
    assert defender.volatiles["ちょうはつ"].count == 3


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


def test_ちょうはつ_技を使うと相手がちょうはつ状態になる():
    """ちょうはつ技: 命中すると相手にちょうはつ状態を付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうはつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("ちょうはつ")


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


def test_にげられない_ゴーストタイプは交代できる():
    # ゴーストタイプはにげられない状態の効果を無視して交代できる
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"にげられない": 1},
    )
    assert battle.can_switch(battle.players[0])


def test_にげられない_交代不可():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    assert not battle.can_switch(battle.players[0])


def test_ねむけ_ターン経過でねむりになる():
    """ねむけ: count=2 でターン終了×2回後にねむり状態になる"""
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


def test_ねをはる_かいふくふうじ中は回復しない():
    """ねをはる: かいふくふうじ状態ではターン終了時の回復がブロックされる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1, "かいふくふうじ": 1}
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_ねをはる_交代不可():
    """ねをはる: 通常ポケモンは交代できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1},
    )
    assert not battle.can_switch(battle.players[0])


def test_ねをはる_回復():
    """ねをはる: ターン終了時に最大HPの1/16回復する"""
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
    """ねをはる: 浮遊しているポケモンでも地面にいる扱いになる"""
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


def test_のろい_マジックガードでダメージ無効():
    """のろい: マジックガード特性を持つポケモンはダメージを受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"のろい": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_のろい_交代で解除():
    """のろい: 交代するとのろい状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"のろい": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("のろい")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("のろい")


def test_バインド_ゴーストタイプは交代可能():
    """バインド: ゴーストタイプは第六世代以降バインド状態でも交代できる"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"バインド": 99},
    )
    assert battle.can_switch(battle.players[0])


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


def test_バインド_マジックガードでダメージ無効():
    """バインド: マジックガード特性を持つポケモンはターン終了ダメージを受けない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        volatile0={"バインド": 2},
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


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


def test_ひるみ_ターン終了で解除():
    """ひるみ: ターン終了後にひるみ状態が解除される（1ターン限り）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ひるみ": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ひるみ")
    t.end_turn(battle)
    assert not mon.has_volatile("ひるみ")


def test_ひるみ_行動不能():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ひるみ": 1}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False


def test_ふういん_交代で解除される():
    """ふういん状態のポケモンが交代すると封印が解除され、相手は共通技を使える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"]), Pokemon("カビゴン")],
        volatile1={"ふういん": 1},
    )
    # 交代前: 共通技は使えない
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False
    # ふういん状態のポケモン（team1）を交代する
    t.run_switch(battle, 1, 1)
    # 交代後: ふういん状態は解除されているので共通技を使える
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is True


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


def test_ほろびのうた_マジックガードでも瀕死():
    """ほろびのうた: マジックガード特性を持つポケモンも瀕死になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.fainted


def test_ほろびのうた_交代で解除():
    """ほろびのうた: 交代するとほろびのうた状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 3}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ほろびのうた")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("ほろびのうた")


def test_マジックコート_ターン終了で解除():
    """マジックコート: ターン終了時に解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"マジックコート": 1},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("マジックコート")
    t.end_turn(battle)
    assert not mon.has_volatile("マジックコート")


def test_マジックコート_交代で解除():
    """マジックコート: 交代時に解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"マジックコート": 1},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("マジックコート")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("マジックコート")


def test_マジックコート_変化技を跳ね返す():
    """マジックコート: 相手に向けた変化技（にらみつける）を跳ね返す"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にらみつける"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 技使用前のランク確認
    assert attacker.rank["B"] == 0
    assert defender.rank["B"] == 0
    # 0番（ピカチュウ側）がにらみつけるを使う
    t.run_move(battle, 0)
    # マジックコートで跳ね返されるため、attacker（技使用者）の防御が下がる
    assert attacker.rank["B"] == -1
    assert defender.rank["B"] == 0


def test_マジックコート_攻撃技は跳ね返さない():
    """マジックコート: 攻撃技は跳ね返さない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 攻撃技なので跳ね返されず defender にダメージが入る
    assert defender.hp < hp_before


def test_まもる_みきりでもまもる状態になる():
    """みきり: 使用するとまもる揮発性状態が付与され、攻撃を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["みきり"])],
    )
    _, defender = battle.actives
    # みきりでまもる volatileが付与されることを確認
    t.run_move(battle, 1)
    assert defender.has_volatile("まもる")
    # まもる状態なので攻撃技が通らない
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


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
    ("キングシールド", False),
    ("スレッドトラップ", False),
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


def test_みがわり_音技は貫通する():
    """みがわり: 音技はみがわりを貫通して本体にダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エコーボイス"])],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    # みがわりにHPを設定（貫通しなければこのHPが削られる）
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    # 音技はみがわりを無視して本体にダメージを与えるため、本体HPが減る
    assert defender.hp < hp_before
    # みがわりのHPは変化しない
    assert defender.volatiles["みがわり"].hp == 999


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


def test_みちづれ_次ターン行動で解除():
    """みちづれ状態は自身が行動すると解除され、その後は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    # 1ターン目: みちづれ持ち（ピカチュウ）が技を使う → ON_TRY_ACTION で解除
    t.run_move(battle, 1)
    # みちづれ状態が解除されていることを確認
    assert not defender.has_volatile("みちづれ")
    # 2ターン目: カビゴンがたいあたりでピカチュウをひんしにしても、みちづれは発動しない
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.alive


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


def test_メロメロ_同性に効かない():
    """メロメロ技: 同性ポケモンには効かない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="オス")],
        team1=[Pokemon("ピカチュウ", gender="オス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_volatile("メロメロ")


def test_メロメロ_性別不明に効かない():
    """メロメロ技: 性別不明ポケモンには効かない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="オス")],
        team1=[Pokemon("ピカチュウ", gender="")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_volatile("メロメロ")


def test_メロメロ_異性に効く():
    """メロメロ技: 異性ポケモンにはメロメロ状態を付与できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="オス")],
        team1=[Pokemon("ピカチュウ", gender="メス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.has_volatile("メロメロ")


def test_メロメロ_行動不能():
    """メロメロ: 50%で行動不能になる"""
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


def test_やどりぎのタネ_くさタイプに失敗():
    """やどりぎのタネ技: くさタイプのポケモンには失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["やどりぎのタネ"])],
        team1=[Pokemon("フシギダネ")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_volatile("やどりぎのタネ")


def test_やどりぎのタネ_ヘドロえきで回復がダメージに変換():
    """やどりぎのタネ: ヘドロえき持ちがやどりぎ状態のとき、回復側がダメージを受ける"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="ヘドロえき")],
        volatile0={"やどりぎのタネ": 1},
    )
    from_mon, to_mon = battle.actives
    to_hp_before = to_mon.hp
    t.end_turn(battle)
    expected_drain = from_mon.max_hp // 8
    # やどりぎ状態のポケモンはダメージを受ける
    assert from_mon.hp == from_mon.max_hp - expected_drain
    # ヘドロえきにより回復がダメージに変換される
    assert to_mon.hp == to_hp_before - expected_drain


def test_やどりぎのタネ_マジックガードでダメージ無効():
    """やどりぎのタネ: マジックガード特性を持つポケモンはダメージを受けない。回復も発生しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        volatile0={"やどりぎのタネ": 1},
    )
    from_mon, to_mon = battle.actives
    to_hp_before = to_mon.hp
    t.end_turn(battle)
    # マジックガード持ちはダメージなし
    assert from_mon.hp == from_mon.max_hp
    # 回復も発生しない
    assert to_mon.hp == to_hp_before


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


def test_ロックオン_ターン経過で解除():
    """ロックオン: count=1 でターン終了後に揮発状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ロックオン": 1},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ロックオン")
    t.end_turn(battle)
    assert not mon.has_volatile("ロックオン")


def test_ロックオン_交代で解除():
    """ロックオン: 相手が交代するとロックオン状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        volatile0={"ロックオン": 2},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ロックオン")
    # 相手が交代するとロックオン状態が解除される
    t.run_switch(battle, 1, 1)
    assert not mon.has_volatile("ロックオン")


def test_ロックオン_必中化():
    """ロックオン状態で技を使うと命中率が None（必中）になる"""
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
