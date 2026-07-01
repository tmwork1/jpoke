"""揮発性状態ハンドラの単体テスト（カ〜コ行）"""
import pytest
from jpoke import Move, Pokemon
from jpoke.enums import Command
from .. import test_utils as t


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
        accuracy=100,
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
    battle.step()
    assert attacker.moves[0].pp == initial_pp


@pytest.mark.parametrize("hidden_move_name", ["あなをほる", "そらをとぶ", "ダイビング", "シャドーダイブ"])
def test_かくれる_潜伏中はコマンドが固定される(hidden_move_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=[hidden_move_name, "なきごえ"])],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, hidden_move_name, count=1)
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
    assert commands == [Command.FORCED]


@pytest.mark.parametrize("hidden_move_name", ["あなをほる", "そらをとぶ", "ダイビング", "シャドーダイブ"])
def test_かくれる_潜伏中は交代できない(hidden_move_name):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[hidden_move_name]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.volatile_manager.apply(battle.actives[0], hidden_move_name, count=1)
    assert not battle.query.can_switch(battle.players[0])


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
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
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
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_commands = [cmd for cmd in commands if cmd.is_type("move")]
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
    assert battle.actives[0].rank["atk"] == -1


def test_キングシールド_非接触では攻撃が下がらない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "キングシールド", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["atk"] == 0


def test_こだわり():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こだわり", move_name="なきごえ")
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
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
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_こだわり_固定技のPPが0だとわるあがきになる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.moves[0].pp = 0
    battle.volatile_manager.apply(mon, "こだわり", move_name="たいあたり")
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


def test_こらえる_ターン終了後にvolatileが解除される():
    """こらえる: ターン終了後にこらえる揮発状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こらえる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("こらえる")

    t.end_turn(battle)

    assert not attacker.has_volatile("こらえる")


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
