"""技ハンドラの単体テスト。"""

import pytest
from jpoke import Pokemon
from jpoke.core import Handler, HandlerReturn
from jpoke.enums import Event, LogCode, Command
import test_utils as t


def test_はやてがえし_先制攻撃技に成功():
    """はやてがえし: 相手が先制攻撃技を選んだ時のみ成功し、ひるませる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp
    t.reserve_command(battle)

    battle.advance_turn()
    assert battle.actives[1].hp < before_foe_hp
    assert battle.actives[0].hp == before_ally_hp
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_はやてがえし_通常攻撃技には失敗():
    """はやてがえし: 優先度0の攻撃技を選んだ相手には失敗する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp
    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp
    assert not t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_はやてがえし_先制変化技には失敗():
    """はやてがえし: 先制変化技（まもる）には失敗する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["まもる"])],
    )
    before_foe_hp = battle.actives[1].hp
    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert not t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_きあいパンチ_行動前にダメージを受けず成功():
    """きあいパンチ: 行動前に被弾していなければ成功する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp < before_foe_hp


def test_きあいパンチ_攻撃ダメージを受けると失敗():
    """きあいパンチ: 行動前に攻撃ダメージを受けた場合は不発。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=0)


def test_きあいパンチ_みがわりへの被弾では中断しない():
    """きあいパンチ: みがわりが被弾しても使用者は中断されない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    battle.volatile_manager.apply(battle.actives[0], "みがわり", hp=999)
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp < before_foe_hp
    assert battle.actives[0].hp == before_ally_hp


def test_変化技は_ON_STATUS_HIT_のみ発火する():
    """変化技実行時は ON_HIT ではなく ON_STATUS_HIT が発火する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["まもる"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
    )

    count = {"hit": 0, "status_hit": 0}

    def on_hit(_, __, value):
        count["hit"] += 1
        return HandlerReturn(value)

    def on_status_hit(_, __, value):
        count["status_hit"] += 1
        return HandlerReturn(value)

    battle.events.on(
        Event.ON_HIT,
        Handler(on_hit, subject_spec="attacker:self"),
        battle.actives[0],
    )
    battle.events.on(
        Event.ON_STATUS_HIT,
        Handler(on_status_hit, subject_spec="attacker:self"),
        battle.actives[0],
    )

    t.reserve_command(battle, ally_command=Command.MOVE_0, foe_command=Command.MOVE_0)
    battle.advance_turn()

    assert count["status_hit"] == 1
    assert count["hit"] == 0


def test_テラスタルコマンドで技前にテラスタルする():
    """テラスタルコマンドを選ぶと技発動前にテラスタル状態になる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ほのお", moves=["ひのこ"])],
        foe=[Pokemon("コイキング", moves=["はねる"])],
    )

    t.reserve_command(
        battle,
        ally_command=Command.TERASTAL_0,
        foe_command=Command.MOVE_0,
    )

    battle.advance_turn()

    assert battle.actives[0].is_terastallized
    assert battle.actives[0].terastal == "ほのお"
    assert battle.actives[0].types == ["ほのお"]


def test_テラスタル後は再度テラスタルコマンドを選べない():
    """一度テラスタルした後は次ターンのコマンド候補にテラスタルが出ない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ほのお", moves=["ひのこ"])],
        foe=[Pokemon("コイキング", moves=["はねる"])],
    )

    t.reserve_command(
        battle,
        ally_command=Command.TERASTAL_0,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()

    commands = battle.get_available_action_commands(battle.players[0])

    assert Command.TERASTAL_0 not in commands


def test_攻撃技は_ON_HIT_のみ発火する():
    """攻撃技実行時は ON_STATUS_HIT ではなく ON_HIT が発火する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
    )

    count = {"hit": 0, "status_hit": 0}

    def on_hit(_, __, value):
        count["hit"] += 1
        return HandlerReturn(value)

    def on_status_hit(_, __, value):
        count["status_hit"] += 1
        return HandlerReturn(value)

    battle.events.on(
        Event.ON_HIT,
        Handler(on_hit, subject_spec="attacker:self"),
        battle.actives[0],
    )
    battle.events.on(
        Event.ON_STATUS_HIT,
        Handler(on_status_hit, subject_spec="attacker:self"),
        battle.actives[0],
    )

    t.reserve_command(battle, ally_command=Command.MOVE_0, foe_command=Command.MOVE_0)
    battle.advance_turn()

    assert count["hit"] == 1
    assert count["status_hit"] == 0


def test_テラバースト_ステラ時に攻撃と特攻が1段階低下():
    """ステラ テラスタル中にテラバーストを使うと攻撃・特攻が-1段階になる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ステラ", moves=["テラバースト"])],
        foe=[Pokemon("コイキング", moves=["はねる"])],
    )
    attacker = battle.actives[0]

    t.reserve_command(
        battle,
        ally_command=Command.TERASTAL_0,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()

    assert attacker.is_terastallized
    assert attacker.rank["A"] == -1
    assert attacker.rank["C"] == -1


def test_テラバースト_非ステラ時は能力低下しない():
    """通常テラスタル中のテラバーストでは能力低下は起きない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", terastal="ほのお", moves=["テラバースト"])],
        foe=[Pokemon("コイキング", moves=["はねる"])],
    )
    attacker = battle.actives[0]

    t.reserve_command(
        battle,
        ally_command=Command.TERASTAL_0,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()

    assert attacker.is_terastallized
    assert attacker.rank["A"] == 0
    assert attacker.rank["C"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
