"""能力ランク補正ハンドラの単体テスト"""

import test_utils as t
from jpoke.model import Pokemon
from jpoke.handlers.move import acc_rank_modifier, eva_rank_modifier
from jpoke.core.event import EventContext


def test_acc_rank_modifier_plus1():
    """命中率ランク+1で補正1.33倍の検証"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["アイアンテール"])],
        foe=[Pokemon("フシギダネ")],
        accuracy=None
    )

    ally = battle.actives[0]
    ally.rank["acc"] = 1

    move = ally.moves[0]
    ctx = EventContext(attacker=ally, move=move)

    # acc_rank_modifier ハンドラを直接テスト
    result = acc_rank_modifier(battle, ctx, 75)

    # 75 * (4/3) / (4/3) ≒ 100
    expected = 75 * 5461 // 4096
    assert result.success is True
    assert result.value == expected, f"期待値: {expected}, 実績: {result.value}"


def test_eva_rank_modifier_plus1():
    """回避率ランク+1で補正0.9倍の検証"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe=[Pokemon("フシギダネ")],
    )

    foe = battle.players[1].active
    foe.rank["eva"] = 1

    ally = battle.actives[0]
    move = ally.moves[0]
    ctx = EventContext(defender=foe, move=move)

    # eva_rank_modifier ハンドラを直接テスト
    result = eva_rank_modifier(battle, ctx, 100)

    # 100 * (9/10) ≒ 90
    expected = 100 * 3686 // 4096
    assert result.success is True
    assert result.value == expected, f"期待値: {expected}, 実績: {result.value}"


def test_acc_rank_modifier_zero():
    """命中率ランク0で補正なしの検証"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["アイアンテール"])],
        foe=[Pokemon("フシギダネ")],
    )

    ally = battle.actives[0]
    ally.rank["acc"] = 0

    move = ally.moves[0]
    ctx = EventContext(attacker=ally, move=move)

    # ランク0なので補正なし
    result = acc_rank_modifier(battle, ctx, 75)
    assert result.success is False
    assert result.value == 75


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
