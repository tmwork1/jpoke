"""致死率計算（core/lethal.py）のテスト"""
import pytest

from jpoke import Pokemon, Move

from . import test_utils as t


def test_オボンのみで乱数2発():
    """オボンのみ所持時、HPが半分以下になった1発目で回復するため乱数2になる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="オボンのみ")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[-1].n_attack == 2
    assert results[-1].lethal_probability == pytest.approx(0.05859375, abs=0.001)


def test_たべのこしでターン終了時に回復():
    """たべのこし所持時、ターン終了時に最大HPの1/16回復した状態が次の攻撃に引き継がれる"""
    with_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カバルドン", item_name="たべのこし")],
    )
    without_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カバルドン")],
    )

    results_with_item = t.calc_lethal(
        with_item, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)], max_attack=2,
    )
    results_without_item = t.calc_lethal(
        without_item, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)], max_attack=2,
    )

    # たべのこしの回復分（最大HPの1/16）だけ2発目のHP分布が高くなる
    leftover_heal = with_item.actives[1].max_hp // 16
    assert max(results_with_item[1].hp_counter) - max(results_without_item[1].hp_counter) == leftover_heal


def test_マルチスケイルでダメージ半減():
    """マルチスケイル所持時、HP満タンの1発目のみダメージが半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[-1].n_attack == 3
    assert results[0].min_damage == 45
    assert results[0].max_damage == 54
    assert results[1].min_damage == 90
    assert results[1].max_damage == 108
    assert results[2].lethal_probability == 1.0


def test_多段技はヒットごとに分布を記録():
    """スケイルショットのような多段技は、ヒットごとに LethalResult が積まれる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("スケイルショット"), 4)])

    assert [r.hit for r in results] == [1, 2, 3, 4]
    assert all(r.n_attack == 1 for r in results)
    assert results[0].min_damage == 19
    assert results[0].max_damage == 24


def test_特性道具なし():
    """特性・道具の影響がない場合、確定数どおりに致死率が変化する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[-1].n_attack == 2
    assert results[0].min_damage == 90
    assert results[0].max_damage == 108
    assert results[0].lethal_probability == 0.0
    assert results[1].lethal_probability == 1.0


def test_複数の技を順に使用():
    """moves にリストを渡すと、1回の攻撃機会で技を順番に使用する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(
        battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1), (Move("ドラゴンクロー"), 1)],
    )

    assert len(results) == 2
    assert results[0].n_attack == 1
    assert results[1].n_attack == 1
    assert results[1].min_damage == 116
    assert results[1].max_damage == 140
