"""連続技ハンドラの単体テスト。"""

import pytest
from jpoke import Pokemon
import test_utils as t


def test_にどげり_命中判定1回で2回ヒットする():
    """にどげり: 命中判定は1回だけで、2ヒットする。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["にどげり"])],
    )
    call_count = 0
    original_check_hit = battle.move_executor.check_hit

    def wrapped_check_hit(attacker, move):
        nonlocal call_count
        call_count += 1
        return original_check_hit(attacker, move)

    battle.move_executor.check_hit = wrapped_check_hit

    battle.advance_turn()

    assert call_count == 1
    assert battle.actives[1].hits_taken == 2


def test_タネマシンガン_スキルリンクで5回ヒットする():
    """タネマシンガン: スキルリンクなら5ヒット固定になる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スキルリンク", moves=["タネマシンガン"])],
    )
    battle.advance_turn()
    assert battle.actives[1].hits_taken == 5


@pytest.mark.parametrize(
    "roll, expected",
    [
        (0.0, 2),
        (0.3749, 2),
        (0.375, 3),
        (0.7499, 3),
        (0.75, 4),
        (0.8749, 4),
        (0.875, 5),
        (0.9999, 5),
    ],
)
def test_タネマシンガン_ヒット数が2から5の範囲で決まる(roll: float, expected: int):
    """タネマシンガン: 乱数ロールに応じて2~5ヒットが決まる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["タネマシンガン"])],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    original_random = battle.random.random
    battle.random.random = lambda: roll
    try:
        hit_count = battle.move_executor._resolve_hit_count(attacker, move)
    finally:
        battle.random.random = original_random

    assert hit_count == expected


def test_タネマシンガン_相手HP1で最初の1発で処理中断():
    """タネマシンガン: 相手の初期HPが1のときに、最初の1発で相手がひんしになり処理が中断される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["タネマシンガン"])],
    )

    # 相手のHPを1に設定（最大HPから現在HPを1に減らす処理）
    defender = battle.actives[1]
    defender._hp = 1

    # ダメージ計算の呼び出し回数をカウント
    damage_call_count = 0

    def counting_determine_damage(attacker, defender, move, critical=False):
        nonlocal damage_call_count
        damage_call_count += 1
        return 1  # 常に1ダメージ

    battle.determine_damage = counting_determine_damage
    battle.advance_turn()

    # 複数ヒット予定（min_hits=2）なのに、最初の1発で相手がひんしになったため処理が中断される
    # ダメージ計算が1回だけ実行される
    assert damage_call_count == 1
    assert defender.hp == 0


def test_トリプルアクセル_各ヒットで命中判定と威力更新を行う():
    """トリプルアクセル: 各ヒットで命中判定し、威力が20→40→60で更新される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["トリプルアクセル"])],
    )
    call_count = 0
    powers = []

    def fake_check_hit(attacker, move):
        nonlocal call_count
        call_count += 1
        return True

    def fake_determine_damage(attacker, defender, move, critical=False):
        powers.append(move.power)
        return 1

    battle.move_executor.check_hit = fake_check_hit
    battle.move_executor.check_critical = lambda ctx: False
    battle.move_executor._resolve_hit_count = lambda attacker, move: 3  # 必ず3ヒット
    battle.determine_damage = fake_determine_damage

    t.reserve_command(battle)
    battle.advance_turn()

    assert call_count == 3
    assert powers == [20, 40, 60]
    assert battle.actives[1].hits_taken == 3
    assert battle.actives[0].moves[0].power == battle.actives[0].moves[0].data.power


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
