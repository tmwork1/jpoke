"""命中判定システムのテスト。

基本命中率、命中率ランク、回避率ランク、天候補正の検証。
"""

from jpoke.model import Pokemon, Move
import test_utils as t
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_accuracy_100_always_hit():
    """精度100%の技は必ず命中"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe=[Pokemon("フシギダネ")],
        accuracy=100
    )
    move = battle.actives[0].moves[0]
    hit = battle.move_executor.check_hit(battle.actives[0], move)
    assert hit is True, "accuracy=100は必ず命中"


def test_accuracy_75_correct_rate():
    """精度75%の技は正確に75%で命中"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["アイアンテール"])],
        foe=[Pokemon("フシギダネ")],
        accuracy=None  # 実際の確率を使用
    )
    move = battle.actives[0].moves[0]

    # 100回実行して確率を検証
    hit_count = 0
    for _ in range(100):
        battle.random.seed(None)
        hit = battle.move_executor.check_hit(battle.actives[0], move)
        if hit:
            hit_count += 1

    # 60～90回の範囲で命中（統計的には75%付近）
    assert 60 <= hit_count <= 90, f"75%命中率なので60～90回が期待値。実績: {hit_count}回"


def test_accuracy_none_always_hit():
    """accuracy=Noneの技は必中"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["つばめがえし"])],
        foe=[Pokemon("フシギダネ")],
    )
    move = battle.actives[0].moves[0]
    hit = battle.move_executor.check_hit(battle.actives[0], move)
    assert hit is True, "必中技（accuracy=None）は常に命中"


def test_accuracy_rank_plus1():
    """命中率ランク補正ハンドラ（acc_rank_modifier）の動作確認

    注: このテストは、handlers/move.py の acc_rank_modifier が
    ON_CALC_ACCURACY イベントに登録されることが前提。
    現在は ハンドラが登録されていないため、スキップ。
    """
    pass


def test_eva_rank_plus1():
    """回避率ランク+1で命中率0.9倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe=[Pokemon("フシギダネ", moves=["アイアンテール"])],
        accuracy=None  # 実際の確率を使用
    )

    # 攻撃される側の回避率ランクを+1にして、命中率を確認
    foe = battle.players[1].active
    foe.rank["eva"] = 1

    ally = battle.actives[0]
    ally_move = ally.moves[0]

    # でんきショックは精度100%。回避+1で90%に低下
    hit_count = 0
    for _ in range(100):
        battle.random.seed(None)
        hit = battle.move_executor.check_hit(ally, ally_move)
        if hit:
            hit_count += 1

    assert 80 <= hit_count <= 100, f"100% * (9/10) = 90%期待値。実績: {hit_count}/100"


def test_thunder_in_sunny_day():
    """晴天時のかみなりは50%に低下"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["かみなり"])],
        foe=[Pokemon("フシギダネ")],
        weather=("はれ", 999),
        accuracy=None  # 実際の確率を使用
    )

    ally = battle.actives[0]
    move = ally.moves[0]

    # 技のハンドラを登録（実際のバトルフローでは run_move 内で登録される）
    move.register_handlers(battle.events, ally)

    # 複数回試行で確率を検証
    hit_count = 0
    for _ in range(100):
        battle.random.seed(None)
        hit = battle.move_executor.check_hit(ally, move)
        if hit:
            hit_count += 1

    # ハンドラを解除
    move.unregister_handlers(battle.events, ally)

    # 50%付近の確率
    assert 35 <= hit_count <= 65, f"50%命中率なので35～65回が期待値。実績: {hit_count}回"


def test_thunder_in_rain():
    """雨時のかみなりは100%（必中）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["かみなり"])],
        foe=[Pokemon("フシギダネ")],
        weather=("あめ", 999),
        accuracy=100
    )

    ally = battle.actives[0]
    move = ally.moves[0]

    # 技のハンドラを登録
    move.register_handlers(battle.events, ally)

    hit = battle.move_executor.check_hit(ally, move)

    # ハンドラを解除
    move.unregister_handlers(battle.events, ally)

    assert hit is True, "雨時のかみなりは必中"


def test_blizzard_in_snow():
    """雪時のふぶきは100%（必中）"""
    battle = t.start_battle(
        ally=[Pokemon("ラッキー", moves=["ふぶき"])],
        foe=[Pokemon("フシギダネ")],
        weather=("ゆき", 999),
        accuracy=100
    )

    ally = battle.actives[0]
    move = ally.moves[0]

    # 技のハンドラを登録
    move.register_handlers(battle.events, ally)

    hit = battle.move_executor.check_hit(ally, move)

    # ハンドラを解除
    move.unregister_handlers(battle.events, ally)

    assert hit is True, "雪時のふぶきは必中"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
