"""攻撃技ハンドラの単体テスト（ふ行）。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import Event
from .. import test_utils as t


@pytest.mark.parametrize(("attacker_name", "expected"), [
    ("カイリキー", "physical"),
    ("フーディン", "special"),
])
def test_フォトンゲイザー_こうげき高い場合物理技になる(attacker_name: str, expected: str):
    """フォトンゲイザー: 補正込みAがCより高いとき物理技、そうでなければ特殊技として計算する。"""
    battle = t.start_battle(
        team0=[Pokemon(attacker_name, move_names=["フォトンゲイザー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)
    assert battle.move_executor.resolve_move_category(attacker, move) == expected
    move.unregister_handlers(battle.events, attacker)


def test_フォトンゲイザー_とくこう高い場合特殊技のまま():
    """フォトンゲイザー: とくこうがこうげき以上のとき特殊技のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["フォトンゲイザー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)
    assert battle.move_executor.resolve_move_category(attacker, move) == "special"
    move.unregister_handlers(battle.events, attacker)


def test_ふくろだたき_威力は基礎こうげきから計算される():
    """ふくろだたき: 各ヒットの威力 = 基礎こうげき種族値 / 10 + 5（ガブリアスA=130 → 威力18）。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", move_names=["ふくろだたき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    # ガブリアス基礎こうげき=130 → 130//10+5=18
    assert battle.damage_calculator.final_power == 18


def test_ふくろだたき_状態異常ポケモンはカウントされない():
    """ふくろだたき: やけど状態のポケモンはカウントから除外され、3体中1体やけどなら2ヒットする。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ガブリアス", move_names=["ふくろだたき"]),
            Pokemon("ピカチュウ"),
            Pokemon("カビゴン"),
        ],
        team1=[Pokemon("ピカチュウ")],
    )
    # 控えのポケモンにやけどを適用
    player = battle.players[0]
    bench_mon = battle.player_states[player].bench[0]
    battle.ailment_manager.apply(bench_mon, "やけど")
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    move.unregister_handlers(battle.events, attacker)
    assert hit_count == 2


def test_ふくろだたき_選出3体健康ならば3ヒット():
    """ふくろだたき: 3体選出でひんし・状態異常なしのとき3ヒットする。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ガブリアス", move_names=["ふくろだたき"]),
            Pokemon("ピカチュウ"),
            Pokemon("カビゴン"),
        ],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    move.unregister_handlers(battle.events, attacker)
    assert hit_count == 3
