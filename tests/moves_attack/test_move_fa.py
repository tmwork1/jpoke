"""攻撃技ハンドラの単体テスト（ふ行）。"""

import pytest
from jpoke import Pokemon
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
