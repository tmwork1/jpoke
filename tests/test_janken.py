"""エビワラーじゃんけんのテスト。"""

import pytest

from jpoke import Pokemon
from jpoke.enums import LogCode
import test_utils as t


def _hitmonchan(move: str) -> Pokemon:
    """じゃんけん検証用のエビワラーを作る。"""
    mon = Pokemon("エビワラー", ability="てつのこぶし", nature="いじっぱり", moves=[move])
    mon.effort = [0, 0, 0, 0, 0, 0]
    mon.indiv = [31, 31, 31, 31, 31, 31]
    return mon


def test_マッハパンチのダメージ範囲():
    battle = t.start_battle(
        ally=[_hitmonchan("マッハパンチ")],
        foe=[_hitmonchan("はねる")],
    )
    attacker, defender = battle.actives
    damages = battle.determine_damage_range(attacker, defender, "マッハパンチ")

    assert min(damages) == 39
    assert max(damages) == 46


def test_はやてがえしのダメージ範囲():
    battle = t.start_battle(
        ally=[_hitmonchan("はやてがえし")],
        foe=[_hitmonchan("はねる")],
    )
    attacker, defender = battle.actives
    damages = battle.determine_damage_range(attacker, defender, "はやてがえし")

    assert min(damages) == 51
    assert max(damages) == 61


def test_きあいパンチのダメージ範囲():
    battle = t.start_battle(
        ally=[_hitmonchan("きあいパンチ")],
        foe=[_hitmonchan("はねる")],
    )
    attacker, defender = battle.actives
    damages = battle.determine_damage_range(attacker, defender, "きあいパンチ")

    assert min(damages) == 141
    assert max(damages) == 166


def test_はやてがえしがマッハパンチに勝つ():
    battle = t.start_battle(
        ally=[_hitmonchan("はやてがえし")],
        foe=[_hitmonchan("マッハパンチ")],
    )
    battle.advance_turn()

    max_hp = battle.actives[0].max_hp
    assert battle.actives[0].hp == max_hp
    assert battle.actives[1].hp < max_hp
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_きあいパンチがはやてがえしに勝つ():
    battle = t.start_battle(
        ally=[_hitmonchan("きあいパンチ")],
        foe=[_hitmonchan("はやてがえし")],
    )
    battle.advance_turn()

    max_hp = battle.actives[0].max_hp
    assert battle.actives[0].hp == max_hp
    assert battle.actives[1].hp < max_hp


def test_マッハパンチがきあいパンチに勝つ():
    battle = t.start_battle(
        ally=[_hitmonchan("マッハパンチ")],
        foe=[_hitmonchan("きあいパンチ")],
    )
    battle.advance_turn()

    max_hp = battle.actives[0].max_hp
    assert battle.actives[1].hp < max_hp
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_きあいパンチ同士はどちらか一方のみ成功する():
    """同速同条件のきあいパンチ同士は、片方だけが行動成功する想定。"""
    battle = t.start_battle(
        ally=[_hitmonchan("きあいパンチ")],
        foe=[_hitmonchan("きあいパンチ")],
    )
    battle.advance_turn()
    assert battle.judge_winner() is not None


def test_はやてがえし同士はどちらか一方のみ成功する():
    battle = t.start_battle(
        ally=[_hitmonchan("はやてがえし")],
        foe=[_hitmonchan("はやてがえし")],
    )
    battle.advance_turn()

    max_hp = battle.actives[0].max_hp
    hps = sorted(mon.hp for mon in battle.actives)
    assert hps[0] < max_hp
    assert hps[1] == max_hp


def test_マッハパンチ同士は両者がダメージを受ける():
    battle = t.start_battle(
        ally=[_hitmonchan("マッハパンチ")],
        foe=[_hitmonchan("マッハパンチ")],
    )
    battle.advance_turn()

    max_hp = battle.actives[0].max_hp
    assert battle.actives[0].hp < max_hp
    assert battle.actives[1].hp < max_hp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

