"""`jpoke.testing` のインデックス引数名統一の回帰テスト。

以前は `build_context` / `run_move` / `calc_lethal` が `atk_idx`、
`apply_ailment` が `active_index`、`calc_move_priority` が `player_index`、
`run_switch` / `can_switch` が `player_idx` と4通りに分裂しており、覚えた
引数名を別の関数にそのまま使い回すと `TypeError` になっていた。
本テストは全関数が `player_idx` キーワード引数で統一的に呼び出せることを
固定し、将来の再分裂を検知する。
"""
from jpoke import Pokemon, Move

from . import test_utils as t


def test_apply_ailment_がplayer_idxキーワードで呼び出せる():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    ok = t.apply_ailment(battle, player_idx=1, ailment_name="どく")
    assert ok is True
    assert battle.actives[1].status == "どく"


def test_build_context_がplayer_idxキーワードで呼び出せる():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", move_names=["じしん"])],
        team1=[Pokemon("カイリュー")],
    )
    ctx = t.build_context(battle, player_idx=0, move_idx=0)
    assert ctx.attacker is battle.actives[0]
    assert ctx.defender is battle.actives[1]


def test_calc_lethal_がplayer_idxキーワードで呼び出せる():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("じしん"), max_attack=2)
    assert len(results) >= 1
    assert results[0].min_damage > 0


def test_calc_move_priority_がplayer_idxキーワードで呼び出せる():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", move_names=["じしん"])],
        team1=[Pokemon("カイリュー")],
    )
    priority = t.calc_move_priority(battle, player_idx=0, move_index=0)
    assert priority == 0


def test_can_switch_がplayer_idxキーワードで呼び出せる():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス"), Pokemon("カイリュー")],
        team1=[Pokemon("フシギダネ")],
    )
    assert t.can_switch(battle, player_idx=0) is True
    assert t.can_switch(battle, player_idx=1) is False


def test_run_move_がplayer_idxキーワードで呼び出せる():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", move_names=["じしん"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, player_idx=0, move_idx=0)
    assert defender.hp < hp_before


def test_run_switch_がplayer_idxキーワードで呼び出せる():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス"), Pokemon("カイリュー")],
        team1=[Pokemon("フシギダネ")],
    )
    mon = t.run_switch(battle, player_idx=0, new_idx=1)
    assert battle.actives[0] is mon
    assert mon.name == "カイリュー"
