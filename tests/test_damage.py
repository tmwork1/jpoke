"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import BattleContext

import test_utils as t


# ──────────────────────────────────────────────────────────────────
# 攻撃側タイプ補正
# ──────────────────────────────────────────────────────────────────

# TODO : テラスタルのテストは別モジュールに分けたので、terastallizeフラグは削除
@pytest.mark.parametrize(
    ("attacker", "terastallize", "expected"),
    [
        (Pokemon("ピカチュウ", moves=["でんきショック"]), False, 1.5),
        (Pokemon("ピカチュウ", moves=["ひのこ"]), False, 1.0),
    ]
)
def test_攻撃側タイプ補正計算(attacker: Pokemon, terastallize: bool, expected: int):
    battle = t.start_battle(
        ally=[attacker],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    if terastallize:
        attacker.terastallize()

    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == expected


# ──────────────────────────────────────────────────────────────────
# 防御側タイプ相性補正
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("move_name", "defender_name", "expected"),
    [
        ("ひのこ", "フシギダネ", 2.0),
        ("ひのこ", "ゼニガメ", 0.5),
        ("でんきショック", "ピカチュウ", 0.5),
        ("たいあたり", "ゴース", 0.0),
    ]
)
def test_防御側タイプ相性補正計算(move_name: str, defender_name: str, expected: float):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon(defender_name)],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert battle.damage_calculator.calc_def_type_modifier(ctx) == pytest.approx(expected)


# ──────────────────────────────────────────────────────────────────
# 急所
# ──────────────────────────────────────────────────────────────────

def test_急所_ダメージ倍率():
    """急所ダメージが1.5倍になることを確認"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")])
    attacker, defender = battle.actives
    normal_damages = battle.calc_damage_range(attacker, defender, "たいあたり", critical=False)
    critical_damages = battle.calc_damage_range(attacker, defender, "たいあたり", critical=True)
    ratio = critical_damages[0] / normal_damages[0]
    assert 1.4 < ratio < 1.6

# TODO : 急所時に攻撃側の能力ランク低下を無視するテストを追加
# TODO : 急所時に防御側の能力ランク上昇を無視するテストを追加


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
