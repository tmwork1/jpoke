"""フィールド効果ハンドラの単体テスト（天候・地形・サイドフィールド・グローバルフィールド）"""
import math
from jpoke import Battle, Pokemon
from jpoke.enums import Command, Event
from jpoke.core import BattleContext
from jpoke.model.move import Move
import test_utils as t


# 定数定義
DEFAULT_DURATION = 999  # フィールド効果のデフォルト継続ターン数


def test_はれ_boost_fire():
    """はれ: ほのお技威力1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("はれ", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=6144)


def test_はれ_weaken_water():
    """はれ: みず技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("はれ", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=2048)


def test_あめ_boost_water():
    """あめ: みず技威力1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("あめ", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=6144)


def test_あめ_weaken_fire():
    """あめ: ほのお技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("あめ", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=2048)


def test_すなあらし_damage():
    """すなあらし: ターン終了時ダメージ"""
    battle = t.start_battle(weather=("すなあらし", DEFAULT_DURATION))
    battle.events.emit(Event.ON_TURN_END_1)
    actual_damages = [mon.max_hp - mon.hp for mon in battle.actives]
    expected_damages = [mon.max_hp // 16 for mon in battle.actives]
    assert actual_damages == expected_damages, "Incorrect sandstorm damage applied"


def test_すなあらし_no_damage_for_rock():
    """すなあらし: いわタイプはダメージを受けない"""
    battle = t.start_battle(
        ally=[Pokemon("イシツブテ")],
        weather=("すなあらし", DEFAULT_DURATION),
    )
    battle.events.emit(Event.ON_TURN_END_1)
    actual_damages = [mon.max_hp - mon.hp for mon in battle.actives]
    expected_damages = [0, battle.actives[1].max_hp // 16]
    assert actual_damages == expected_damages, "Incorrect sandstorm damage applied"


def test_すなあらし_rock_spdef_boost():
    """すなあらし: いわタイプ特防1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["スピードスター"])],
        foe=[Pokemon("イシツブテ")],
        weather=("すなあらし", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_DEF_MODIFIER,
                         expected=6144)


def test_ゆき_ice_def_boost():
    """ゆき: こおりタイプ防御1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ユキワラシ")],
        weather=("ゆき", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_DEF_MODIFIER,
                         expected=6144)


def test_エレキフィールド_boost_electric():
    """エレキフィールド: でんき技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=5325)

    # TODO: 浮いているポケモンは強化されないことを確認


def test_エレキフィールド_prevent_sleep():
    """エレキフィールド: ねむり無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    target = battle.actives[0]
    result = target.apply_ailment(battle, "ねむり")
    assert not result, "エレキフィールド下でねむりが付与された"
    assert not target.ailment.is_active, "エレキフィールド下でねむり状態が付与された"

    # TODO: 浮いているポケモンはねむりが付与されることを確認

# TODO: エレキフィールドでのねむけ(揮発状態)防止のテストを追加。浮いているポケモンは防止されないことも確認


def test_グラスフィールド_boost_grass():
    """グラスフィールド: くさ技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("フシギダネ", moves=["はっぱカッター"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=5325)

    # TODO: 浮いているポケモンは強化されないことを確認


def test_グラスフィールド_じしん弱化():
    """グラスフィールド: じしん威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("サンドパン", moves=["じしん"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=2048)


def test_グラスフィールド_じならし弱化():
    """グラスフィールド: じならし威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("サンドパン", moves=["じならし"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=2048)


def test_グラスフィールド_heal():
    """グラスフィールド: ターン終了時1/16回復"""
    battle = t.start_battle(
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    target = battle.actives[0]
    target._hp = 1
    expected_hp = target.hp + target.max_hp // 16
    battle.events.emit(Event.ON_TURN_END_2)
    assert target.hp == expected_hp, "グラスフィールドの回復量が不正"

    # TODO: 浮いているポケモンは回復しないことも確認


def test_サイコフィールド_boost_psychic():
    """サイコフィールド: エスパー技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("フーディン", moves=["サイコキネシス"])],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=5325)

    # TODO: 浮いているポケモンは強化されないことを確認


def test_サイコフィールド_先制技無効():
    """サイコフィールド: 先制技無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    ctx = BattleContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0]
    )
    result = battle.events.emit(Event.ON_TRY_MOVE, ctx, True)
    assert result is False, "サイコフィールドで先制技が無効化されない"

    # TODO: 対象が自分や場である場合は先制技が有効であることを確認

    # TODO: 特性いたずらごころなどにより先制技扱いになった場合も無効化されることを確認 (特性実装後に追加)


def test_サイコフィールド_浮遊は先制技有効():
    """サイコフィールド: 浮遊相手には先制技が有効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピジョン")],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    ctx = BattleContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0]
    )
    result = battle.events.emit(Event.ON_TRY_MOVE, ctx, True)
    assert result is True, "サイコフィールドで浮遊相手に先制技が無効化された"


def test_ミストフィールド_ドラゴン技弱化():
    """ミストフィールド: ドラゴン技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("カイリュー", moves=["りゅうのはどう"])],
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    t.assert_damage_calc(battle,
                         Event.ON_CALC_POWER_MODIFIER,
                         expected=2048)


def test_ミストフィールド_混乱防止():
    """ミストフィールド: 混乱無効化"""
    # まずフィールドなしで混乱付与が成功することを確認
    battle_no_field = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )
    target = battle_no_field.actives[0]
    result = target.apply_volatile(battle_no_field, "こんらん", count=3)
    assert result, "フィールドなしでも混乱が付与されない"
    assert "こんらん" in target.volatiles, "混乱状態が追加されていない"

    # ミストフィールド下では混乱付与が失敗する
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    target2 = battle.actives[0]
    result = target2.apply_volatile(battle, "こんらん", count=3)
    assert not result, "ミストフィールド下で混乱が付与された"
    assert "こんらん" not in target2.volatiles, "混乱状態が追加されている"


def test_ミストフィールド_状態異常防止():
    """ミストフィールド: 状態異常無効化"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    target = battle.actives[0]
    result = target.apply_ailment(battle, "どく")
    assert not result, "ミストフィールド下で状態異常が付与された"
    assert not target.ailment.is_active, "ミストフィールド下で状態異常が付与された"


def test_じゅうりょく_命中補正():
    """じゅうりょく: 命中率5/3倍"""
    battle = t.start_battle(global_field={"じゅうりょく": DEFAULT_DURATION})
    t.assert_accuracy(battle, base=30, expected=50)


def test_じゅうりょく_浮遊無効():
    """じゅうりょく: 浮遊状態を無効化"""
    battle = t.start_battle(
        ally=[Pokemon("ピジョン")],
        global_field={"じゅうりょく": DEFAULT_DURATION},
    )
    target = battle.actives[0]
    assert not target.is_floating(battle), "じゅうりょくで浮遊が無効化されない"


def test_トリックルーム_行動順反転():
    """トリックルーム: 行動順が素早さの逆順になる"""
    battle = t.start_battle(
        ally=[Pokemon("ヤドン")],
        foe=[Pokemon("ピカチュウ")],
        global_field={"トリックルーム": 5},
    )
    func = battle.speed_calculator.calc_speed_order_key
    assert func(battle.actives[0]) > func(battle.actives[1]), "トリックルームで行動順が反転しない"


def test_トリックルーム_技優先度():
    """トリックルーム: 技の優先度が優先される"""
    battle = t.start_battle(
        ally=[Pokemon("ヤドン")],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        global_field={"トリックルーム": 5},
    )
    t.reserve_command(battle)
    action_order = battle.determine_action_order()
    assert action_order[0] == battle.actives[1], "トリックルームで優先度が考慮されない"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
