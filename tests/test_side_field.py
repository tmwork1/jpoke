"""フィールド効果ハンドラの単体テスト（天候・地形・サイドフィールド・グローバルフィールド）"""
import math
from jpoke import Battle, Pokemon
from jpoke.core import Event, BattleContext
from jpoke.model.move import Move
import test_utils as t

# 定数定義
DEFAULT_DURATION = 999  # フィールド効果のデフォルト継続ターン数

# 威力補正の期待値（4096基準）
BASE_MODIFIER = 4096  # 補正計算の基準値
DAMAGE_WALL_MODIFIER = 0.5  # 壁によるダメージ軽減


def test_リフレクター_ダメージ軽減():
    """リフレクター: 物理技ダメージ軽減"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        ally_side_field={"リフレクター": 5},
    )
    ctx = BattleContext(
        attacker=battle.actives[1],
        defender=battle.actives[0],
        move=battle.actives[1].moves[0]
    )
    modifier = battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, BASE_MODIFIER)
    expected = BASE_MODIFIER * DAMAGE_WALL_MODIFIER
    assert modifier == expected, "reflector damage wall modifier is incorrect"

# TODO: リフレクター　特殊技が軽減されないことを確認するテスト追加


def test_ひかりのかべ_ダメージ軽減():
    """ひかりのかべ: 特殊技ダメージ軽減"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        ally_side_field={"ひかりのかべ": 5},
    )
    ctx = BattleContext(
        attacker=battle.actives[1],
        defender=battle.actives[0],
        move=battle.actives[1].moves[0]
    )
    modifier = battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, BASE_MODIFIER)
    expected = BASE_MODIFIER * DAMAGE_WALL_MODIFIER
    assert modifier == expected, "light screen damage wall modifier is incorrect"

# TODO: ひかりのかべ　物理技が軽減されないことを確認するテスト追加


def test_オーロラベール_ダメージ軽減():
    """オーロラベール: ダメージ0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        ally_side_field={"オーロラベール": 1},
    )
    ctx = BattleContext(
        attacker=battle.actives[1],
        defender=battle.actives[0],
        move=battle.actives[1].moves[0]
    )
    modifier = battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, BASE_MODIFIER)
    expected = BASE_MODIFIER * DAMAGE_WALL_MODIFIER
    assert modifier == expected, "aurora veil damage wall modifier is incorrect"

# TODO: オーロラベール　特殊技も半減されることを確認するテスト追加


def test_しんぴのまもり():
    """しんぴのまもり: 状態異常防止"""
    # TODO: テスト実装
    pass


def test_しろいきり_能力低下防止():
    # TODO: 相手による能力低下を防ぐから確認するテストに修正
    """しろいきり: 能力ランク低下を防ぐ"""
    battle = t.start_battle(ally_side_field={"しろいきり": 1})
    target = battle.actives[0]
    before_rank = target.rank["A"]
    battle.modify_stat(target, "A", -1, source=battle.actives[1])
    after_rank = target.rank["A"]

    assert before_rank == after_rank, "Stat rank decreased"

# TODO: しろいきり 自発的な能力低下は防げないことを確認するテスト追加


def test_おいかぜ():
    """おいかぜ: 実効すばやさ2倍"""
    # TODO: テスト実装
    pass


def test_ねがいごと_回復と解除():
    """ねがいごと: ターン終了時回復と解除"""
    battle = t.start_battle(ally_side_field={"ねがいごと": 2})
    field = battle.side_manager[0].fields["ねがいごと"]
    target = battle.actives[0]

    # HPを減らして回復確認
    target._hp = 1
    initial_hp = target.hp

    battle.events.emit(Event.ON_TURN_END_3)
    assert target.hp == initial_hp, "No wish heal occurred"
    assert field.count == 1, "Wish field count did not decrease"

    battle.events.emit(Event.ON_TURN_END_3)
    expected_hp = initial_hp + target.max_hp // 2
    assert target.hp == expected_hp, "Wish heal amount is incorrect"
    assert not field.is_active, "Wish field did not deactivate"


def test_まきびし_1層():
    """まきびし: 交代時1/8ダメージ（1層）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"まきびし": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    active = player.active
    expected_damage = active.max_hp // 8
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Damage is incorrect"


def test_まきびし_2層():
    """まきびし: 交代時1/6ダメージ（2層）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"まきびし": 2},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    active = player.active
    expected_damage = active.max_hp // 6
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Makibishi x2 damage is incorrect"


def test_まきびし_3層():
    """まきびし: 3層で1/4ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"まきびし": 3},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    active = player.active
    expected_damage = active.max_hp // 4
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Damage is incorrect"

# TODO: まきびしで浮いているポケモンがダメージを受けないことを確認するテスト追加


def test_どくびし_1層():
    """どくびし: 交代時どく状態付与（1層）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"どくびし": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert player.active.ailment.name == "どく", "Poison status not applied"


def test_どくびし_2層():
    """どくびし: 2層でもうどく状態付与"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"どくびし": 2},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert player.active.ailment.name == "もうどく", "Badly poison status not applied"

# TODO: どくびしで浮いているポケモンが状態異常にならないことを確認するテスト追加
# TODO: どくタイプのポケモンが着地したときにどくびしが解除されることを確認するテスト追加


def test_ステルスロック_x1():
    """ステルスロック: 1倍ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"ステルスロック": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    active = player.active
    expected_damage = active.max_hp // 8
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Stealth Rock damage is incorrect"


def test_ステルスロック_x4():
    """ステルスロック: 交代時タイプ相性ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("リザードン")],
        ally_side_field={"ステルスロック": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    active = player.active
    expected_damage = active.max_hp // 2  # 4倍弱点なので1/2ダメージ
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Stealth Rock damage is incorrect"


def test_ねばねばネット():
    """ねばねばネット: 交代時素早さ-1"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"ねばねばネット": 1},
    )
    before_rank = battle.players[0].team[1].rank["S"]
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    after_rank = player.active.rank["S"]
    assert after_rank == before_rank - 1, "Speed rank not decreased"

# TODO: ねばねばネットで浮いているポケモンの素早さが下がらないことを確認するテスト追加


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
