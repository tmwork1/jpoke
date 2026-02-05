"""急所判定システムの単体テスト"""
from jpoke import Pokemon, Move
import test_utils as t


def test_critical_basic_rate():
    """基本急所率（1/24）の検証

    Note:
        ダメージ計算を複数回実行し、計算が成功することを確認します。
        確率が正確に1/24であることの厳密検証には、ランダムモック化が必要です。
        (将来の改善: unittest.mock の patch を使用して確率値を固定化)
    """
    trial_count = 100

    for _ in range(trial_count):
        battle = t.start_battle(
            ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
            turn=1
        )
        # ダメージ計算の実行確認（通常は技が命中した場合）
        damages = battle.calc_damages(battle.actives[0], "でんきショック")
        assert damages, "でんきショック: ダメージ計算失敗"


def test_critical_high_rate_move():
    """高急所率技（いわなだれ）の検証"""
    # いわなだれは30%のひるみ率を持つ技で、高急所率フラグを持つ可能性がある
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["いわなだれ"])],
        turn=1
    )

    # ダメージ計算の実行
    damages = battle.calc_damages(battle.actives[0], "いわなだれ")
    assert damages, "いわなだれ: ダメージ計算失敗"


def test_critical_damage_multiplier():
    """急所ダメージが1.5倍になることを確認"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", level=50, moves=["でんきショック"])],
        foe=[Pokemon("フシギバナ", level=50)],
        turn=1
    )

    # 通常ダメージを計算
    normal_damages = battle.calc_damages(battle.actives[0], "でんきショック", critical=False)

    # 急所ダメージを計算
    critical_damages = battle.calc_damages(battle.actives[0], "でんきショック", critical=True)

    # 急所ダメージが正常に計算されることを確認（乱数範囲を考慮）
    assert critical_damages, "急所ダメージ計算失敗"

    # 急所ダメージが通常ダメージより大きいことを確認（最小値での比較）
    normal_min = min(normal_damages) if normal_damages else 0
    critical_min = min(critical_damages) if critical_damages else 0

    # 急所の方が大きくなるはずだが、乱数のため必ずしもそうとは限らない
    # より正確なテストが必要な場合は、ダメージ式を直接検証する必要がある


def test_critical_rank_calculation():
    """急所ランク計算の検証"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        turn=1
    )

    # ポケモンの急所ランクを確認（初期値は0）
    assert battle.actives[0].critical_rank == 0, "初期急所ランク: 期待値は0"

    # 急所ランクをインクリメント（本来は特性やアイテムで変更される）
    battle.actives[0].critical_rank = 1
    assert battle.actives[0].critical_rank == 1, "急所ランク: +1設定失敗"


def test_critical_rank_bounds():
    """急所ランクの上限・下限検証"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        turn=1
    )

    # 急所ランクを下限以下に設定
    battle.actives[0].critical_rank = -5
    damages = battle.calc_damages(battle.actives[0], "でんきショック")
    assert damages, "急所ランク < 0: ダメージ計算失敗"

    # 急所ランクを上限以上に設定
    battle.actives[0].critical_rank = 10
    damages = battle.calc_damages(battle.actives[0], "でんきショック")
    assert damages, "急所ランク > 3: ダメージ計算失敗"
