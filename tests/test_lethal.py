"""致死率計算（core/lethal.py）のテスト

ダメージ計算の参考値
1. A150 ガブリアス -> H166/B115 カイリュー
1.1 ドラゴンテール 90~108 (確定2発)
1.2 スケイルショット 38~48/hit (4hit: 乱数1発 81.91%, 5hit: 確定1発)

2. A150 ガブリアス -> H166/B115 カイリュー 特性マルチスケイル
2.1 ドラゴンテール 45~54 (確定2発)
2.2 スケイルショット 19~24/hit (4hit: 乱数1発 0.01%, 5hit: 確定1発)
"""
import pytest

from jpoke import Pokemon, Move

from . import test_utils as t


def test_オボンのみ_乱数2発():
    """オボンのみ所持時、HPが半分以下になった1発目で回復するため乱数2になる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="オボンのみ")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[0].min_damage == 90
    assert results[0].max_damage == 108
    assert results[-1].n_attack == 2
    assert results[-1].lethal_probability == pytest.approx(0.0585, abs=0.001)


def test_たべのこし_ターン終了時に回復():
    # TODO : 防御側をカイリューにする
    """たべのこし所持時、ターン終了時に最大HPの1/16回復した状態が次の攻撃に引き継がれる"""
    with_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カバルドン", item_name="たべのこし")]
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


def test_マルチスケイル_ダメージ半減():
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


def test_多段技_ヒットごとに分布を記録():
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

# TODO : 多段技 + マルチスケイルの場合、1ヒット目のみマルチスケイルが発動することをテストする

# TODO : オボンのみがあればスケイルショット5発で乱数1発 (80.31%) になることをテストする


def test_特性道具なし():
    """特性・道具の影響がない場合、確定数どおりに致死率が変化する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[-1].n_attack == 2
    assert results[-1].lethal_probability == 1.0
    assert results[0].min_damage == 90
    assert results[0].max_damage == 108


def test_複数技_順に使用():
    """moves にリストを渡すと、1回の攻撃機会で技を順番に使用する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(
        battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1), (Move("ドラゴンクロー"), 1)],
    )

    assert results[0].n_attack == 1
    assert results[0].move.name == "ドラゴンテール"
    assert results[1].n_attack == 1
    assert results[1].move.name == "ドラゴンクロー"
    assert results[-1].n_attack == 1
    assert results[-1].lethal_probability == pytest.approx(0.9453, abs=0.001)
