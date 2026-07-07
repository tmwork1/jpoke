"""揮発性状態ハンドラの単体テスト（ア〜オ行）"""
import pytest
from jpoke import Move, Pokemon
from jpoke.data.move import MOVES
from jpoke.enums import Command
from .. import test_utils as t


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
    battle.step()
    assert attacker.has_volatile("あばれる")
    battle.step()
    assert attacker.has_volatile("あばれる")
    battle.step()
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
    battle.step()
    assert attacker.has_volatile("あばれる")
    assert not attacker.has_volatile("こんらん")
    battle.step()
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
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
    assert commands == [Command.FORCED]

    initial_pp = attacker.moves[0].pp
    battle.step()  # 1ターン進める
    assert attacker.moves[0].pp == initial_pp, "あばれるで技のPPが消費されている"


def test_あめまみれ_1ターン経過でSマイナス1():
    """あめまみれ: ターン終了時にすばやさランクが1段階下がる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"あめまみれ": 2}
    )
    t.end_turn(battle)
    assert battle.actives[0].boosts["spe"] == -1


def test_あめまみれ_3ターンで合計3回Sが下がる():
    """あめまみれ: count=3の場合、3ターン連続でSランクが下がる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"あめまみれ": 3}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.boosts["spe"] == -1
    t.end_turn(battle)
    assert mon.boosts["spe"] == -2
    t.end_turn(battle)
    assert mon.boosts["spe"] == -3
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


def test_あめまみれ_ミラーアーマーでも反射されず自分のSのみ下がる():
    """あめまみれ: 自傷によるランク低下のため、ミラーアーマーを持っていても
    相手へ反射されない（AttributeErrorの回帰テスト）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"あめまみれ": 2}
    )
    mon, foe = battle.actives
    t.end_turn(battle)
    assert mon.rank["spe"] == -1
    assert foe.rank["spe"] == 0


def test_アンコール():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "アンコール", move_name="なきごえ")
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert all(cmd.index == 1 for cmd in commands)


def test_アンコール_non_encoreラベルの技を使った相手には失敗する():
    """アンコール技: 相手がnon_encoreラベルを持つ技を最後に使っていた場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アンコール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # わるあがき（non_encoreラベル）を最後にPPを消費した技にする
    defender.pp_consumed_move = Move("わるあがき")
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


def test_アンコール_バーンアクセルを使った相手には失敗する():
    """アンコール技: 相手がnon_encoreラベルを持つバーンアクセルを最後に使っていた場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アンコール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.pp_consumed_move = Move("バーンアクセル")
    t.run_move(battle, 0)
    assert not defender.has_volatile("アンコール")


def test_アンコール_実行時も技固定():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "アンコール", move_name="なきごえ")
    t.run_move(battle, 0, move_idx=0)
    assert attacker.last_move.name == "なきごえ"


def test_アンコール_対象技がかなしばりで使えないとわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "アンコール", move_name="たいあたり")
    battle.volatile_manager.apply(mon, "かなしばり", move_name="たいあたり")
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
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
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_アンコール_未行動の相手には失敗する():
    """アンコール技: 相手がまだPPを消費する行動をしていない場合
    （pp_consumed_moveがNone）はアンコール状態が付与されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アンコール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # pp_consumed_move は None のまま（デフォルト）
    assert defender.pp_consumed_move is None
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
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
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
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
    move_indices = {cmd.index for cmd in commands if cmd.is_type("move")}
    assert move_indices == {1, 2}


def test_いちゃもん_技が1つしかない場合はわるあがきになる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", move_name="たいあたり")
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
