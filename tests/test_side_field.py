"""フィールド効果ハンドラの単体テスト（天候・地形・サイドフィールド・グローバルフィールド）"""
import math

from jpoke.enums import Event
from jpoke.core import BattleContext
from jpoke.model import Pokemon
import test_utils as t

# 定数定義
DEFAULT_DURATION = 999  # フィールド効果のデフォルト継続ターン数


def test_リフレクター_物理半減():
    """リフレクター: 物理技ダメージ軽減"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_side_field={"リフレクター": 5},
    )
    2048 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_リフレクター_特殊軽減なし():
    """リフレクター: 特殊技が軽減されないことを確認"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe_side_field={"リフレクター": 5},
    )
    4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_ひかりのかべ_特殊半減():
    """ひかりのかべ: 特殊技ダメージ軽減"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe_side_field={"ひかりのかべ": 5},
    )
    2048 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_ひかりのかべ_物理軽減なし():
    """ひかりのかべ: 物理技が軽減されないことを確認"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_side_field={"ひかりのかべ": 5},
    )
    4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_オーロラベール_物理半減():
    """オーロラベール: ダメージ0.5倍"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_side_field={"オーロラベール": 1},
    )
    2048 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_オーロラベール_特殊半減():
    """オーロラベール: ダメージ0.5倍"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe_side_field={"オーロラベール": 1},
    )
    2048 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_リフレクター_急所では軽減されない():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_side_field={"リフレクター": 5},
    )
    ctx = BattleContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0],
    )
    ctx.critical = True
    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 4096


def test_ひかりのかべ_急所では軽減されない():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe_side_field={"ひかりのかべ": 5},
    )
    ctx = BattleContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0],
    )
    ctx.critical = True
    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 4096


def test_オーロラベール_急所では軽減されない():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe_side_field={"オーロラベール": 1},
    )
    ctx = BattleContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0],
    )
    ctx.critical = True
    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 4096


def test_しんぴのまもり():
    """しんぴのまもり: 状態異常防止"""
    battle = t.start_default_battle(ally_side_field={"しんぴのまもり": 1})
    target = battle.actives[0]

    assert not battle.ailment_manager.apply(target, "どく")
    assert not target.ailment.is_active
    assert not battle.volatile_manager.apply(target, "こんらん", count=3)
    assert not target.has_volatile("こんらん")


def test_しろいきり_能力低下防止():
    """しろいきり: 能力ランク低下を防ぐ"""
    battle = t.start_default_battle(ally_side_field={"しろいきり": 1})
    target, source = battle.actives
    assert not battle.modify_stat(target, "A", -1, source=source)


def test_しろいきり_自発的な能力低下は防げない():
    battle = t.start_default_battle(ally_side_field={"しろいきり": 1})
    target = battle.actives[0]
    assert battle.modify_stat(target, "A", -1, source=target)
    assert target.rank["A"] == -1


def test_おいかぜ():
    """おいかぜ: 実効すばやさ2倍"""
    battle = t.start_default_battle(
        ally_side_field={"おいかぜ": 1},
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == 2 * mon.stats["S"]


def test_ねがいごと_回復と解除():
    """ねがいごと: ターン終了時回復と解除"""
    battle = t.start_default_battle(ally_side_field={"ねがいごと": 2})
    field = battle.get_side_field(battle.players[0], "ねがいごと")

    # HPを減らして回復確認
    mon = battle.actives[0]
    mon._hp = 1

    heal = 20
    field.heal = heal

    battle.events.emit(Event.ON_TURN_END_2)
    assert mon.hp == 1, "No wish heal occurred"
    assert field.count == 1, "Wish field count did not decrease"

    battle.events.emit(Event.ON_TURN_END_2)
    assert mon.hp == 1 + heal, "Wish heal amount is incorrect"
    assert not field.is_active, "Wish field did not deactivate"


def test_ねがいごと_回復量未設定時は最大HP半分で回復する():
    battle = t.start_default_battle(ally_side_field={"ねがいごと": 1})
    mon = battle.actives[0]
    mon._hp = 1

    battle.events.emit(Event.ON_TURN_END_2)

    expected_hp = 1 + mon.max_hp // 2
    assert mon.hp == expected_hp


def test_まきびし_1層():
    """まきびし: 交代時1/8ダメージ（1層）"""
    battle = t.start_default_battle(
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
    battle = t.start_default_battle(
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
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"まきびし": 3},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    active = player.active
    expected_damage = active.max_hp // 4
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Damage is incorrect"


def test_まきびし_浮いているポケモンはダメージを受けない():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        ally_side_field={"まきびし": 3},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert player.active.hp == player.active.max_hp


def test_どくびし_1層():
    """どくびし: 交代時どく状態付与（1層）"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"どくびし": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert player.active.ailment.name == "どく", "Poison status not applied"


def test_どくびし_2層():
    """どくびし: 2層でもうどく状態付与"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"どくびし": 2},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert player.active.ailment.name == "もうどく", "Badly poison status not applied"


def test_どくびし_浮いているポケモンには効かない():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        ally_side_field={"どくびし": 2},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert not player.active.ailment.is_active


def test_どくびし_どくタイプが着地すると解除される():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("フシギダネ")],
        ally_side_field={"どくびし": 2},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    field = battle.get_side_field(player, "どくびし")
    assert not field.is_active
    assert field.count == 0
    assert not player.active.ailment.is_active


def test_ステルスロック_x1():
    """ステルスロック: 1倍ダメージ"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"ステルスロック": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    mon = player.active
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == mon.max_hp // 8


def test_ステルスロック_x4():
    """ステルスロック: 交代時タイプ相性ダメージ"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("リザードン")],
        ally_side_field={"ステルスロック": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    mon = player.active
    actual_damage = mon.max_hp - mon.hp
    assert actual_damage == mon.max_hp // 2


def test_ねばねばネット():
    """ねばねばネット: 交代時素早さ-1"""
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"ねばねばネット": 1},
    )
    before_rank = battle.players[0].team[1].rank["S"]
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    after_rank = player.active.rank["S"]
    assert after_rank == before_rank - 1, "Speed rank not decreased"


def test_ねばねばネット_浮いているポケモンには効かない():
    battle = t.start_default_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        ally_side_field={"ねばねばネット": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert player.active.rank["S"] == 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

