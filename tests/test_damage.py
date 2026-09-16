"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke import Pokemon

from . import test_utils as t


def test_急所_ダメージ倍率():
    """急所ダメージが1.5倍になることを確認"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    normal_damages = battle.calc_damages(attacker, defender, "たいあたり", critical=False)
    critical_damages = battle.calc_damages(attacker, defender, "たいあたり", critical=True)
    ratio = critical_damages[0] / normal_damages[0]
    assert 1.4 < ratio < 1.6


def test_急所_攻撃側の能力ランク低下を無視する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    attacker.boosts["atk"] = -6
    normal_with_drop = battle.calc_damages(attacker, defender, "たいあたり", critical=False)
    critical_with_drop = battle.calc_damages(attacker, defender, "たいあたり", critical=True)

    attacker.boosts["atk"] = 0
    critical_without_drop = battle.calc_damages(attacker, defender, "たいあたり", critical=True)

    assert normal_with_drop[0] < critical_with_drop[0]
    assert critical_with_drop == critical_without_drop


def test_急所_防御側の能力ランク上昇を無視する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    defender.boosts["def"] = 6
    normal_with_boost = battle.calc_damages(attacker, defender, "たいあたり", critical=False)
    critical_with_boost = battle.calc_damages(attacker, defender, "たいあたり", critical=True)

    defender.boosts["def"] = 0
    critical_without_boost = battle.calc_damages(attacker, defender, "たいあたり", critical=True)

    assert normal_with_boost[0] < critical_with_boost[0]
    assert critical_with_boost == critical_without_boost


def test_攻撃側タイプ補正_かわりもので変身したタイプにSTABが乗る():
    """かわりもの: 変身先のタイプの技にタイプ一致補正が乗る。"""
    battle = t.start_battle(
        team0=[Pokemon("メタモン", ability_name="かわりもの", move_names=["はねる"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    attacker = battle.actives[0]
    assert attacker.types == ["でんき"]
    assert [m.name for m in attacker.moves] == ["でんきショック"]

    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == 6144


def test_攻撃側タイプ補正_へんげんじざいで変化したタイプにSTABが乗る():
    """へんげんじざい: 技タイプに変化した後のタイプでタイプ一致補正が判定される。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲッコウガ", ability_name="へんげんじざい", move_names=["れいとうビーム"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.types == ["こおり"]
    assert battle.damage_calculator.atk_type_modifier == 6144


def test_攻撃側タイプ補正_へんげんじざい後にテラスタルすると変化後タイプが元タイプになる():
    """へんげんじざい→テラスタル: 元タイプはテラスタル直前（変化後）のタイプであり、種族タイプではない。"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ゲッコウガ", ability_name="へんげんじざい", tera_type="みず",
            move_names=["れいとうビーム", "なみのり"],
        )],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0, 0)
    assert attacker.types == ["こおり"]

    attacker.terastallize()
    assert attacker.types == ["みず"]
    assert attacker.types_before_tera == ["こおり"]

    # 元タイプ（こおり）一致・テラスタイプ不一致 → 1.5倍
    t.run_move(battle, 0, 0)
    assert battle.damage_calculator.atk_type_modifier == 6144
    # 元タイプ不一致・テラスタイプ（みず）一致 → 1.5倍（種族タイプのみずは元タイプ扱いにならない）
    t.run_move(battle, 0, 1)
    assert battle.damage_calculator.atk_type_modifier == 6144


def test_攻撃側タイプ補正_へんげんじざい後のステラは変化後タイプを元タイプ一致とみなす():
    """へんげんじざい→ステラ: 変化後のタイプと一致する技は元タイプ一致技として初回2.0倍。"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ゲッコウガ", ability_name="へんげんじざい", tera_type="ステラ",
            move_names=["れいとうビーム", "なみのり"],
        )],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0, 0)
    assert attacker.types == ["こおり"]

    attacker.terastallize()
    # 元タイプ（こおり）一致技: 初回2.0倍
    t.run_move(battle, 0, 0)
    assert battle.damage_calculator.atk_type_modifier == 8192
    # 元タイプ不一致技（種族タイプのみず）: 初回1.2倍
    t.run_move(battle, 0, 1)
    assert battle.damage_calculator.atk_type_modifier == 4915


def test_攻撃側タイプ補正_みずびたしで種族タイプの技はSTABを失う():
    """みずびたし: みずタイプ単体に変化した後は種族タイプ（でんき）の技にタイプ一致補正が乗らない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", move_names=["みずびたし"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 1)
    assert attacker.types == ["みず"]

    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == 4096


def test_攻撃側タイプ補正_ミラータイプでコピーしたタイプにSTABが乗る():
    """ミラータイプ: コピーした相手のタイプの技にタイプ一致補正が乗る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ", "ひのこ"])],
        team1=[Pokemon("エンテイ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0, 0)
    assert attacker.types == ["ほのお"]

    t.run_move(battle, 0, 1)
    assert battle.damage_calculator.atk_type_modifier == 6144


def test_攻撃側タイプ補正_もりののろいで追加されたタイプにSTABが乗る():
    """もりののろい: 追加されたくさタイプの技にもタイプ一致補正が乗る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エナジーボール"])],
        team1=[Pokemon("カビゴン", move_names=["もりののろい"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 1)
    assert "くさ" in attacker.types

    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == 6144


@pytest.mark.parametrize(
    ("attacker", "expected"),
    [
        (Pokemon("ピカチュウ", move_names=["でんきショック"]), 4096*1.5),
        (Pokemon("ピカチュウ", move_names=["ひのこ"]), 4096*1.0),
    ]
)
def test_攻撃側タイプ補正計算(attacker: Pokemon, expected: int):
    battle = t.start_battle(
        team0=[attacker],
        team1=[Pokemon("ピカチュウ")],
    )
    t.build_context(battle, player_idx=0)
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == expected


@pytest.mark.parametrize(
    ("defender_name", "move", "expected"),
    [
        ("フシギダネ", "ひのこ", 4096*2),
        ("コイル", "じしん", 4096*4),
        ("ゼニガメ", "ひのこ", 4096*0.5),
        ("ピカチュウ", "でんきショック", 4096*0.5),
        ("ゴース", "たいあたり", None),
    ]
)
def test_防御側タイプ相性補正計算(defender_name: str, move: str, expected: float | None):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move])],
        team1=[Pokemon(defender_name)],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
