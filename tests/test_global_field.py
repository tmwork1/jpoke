"""フィールド効果ハンドラの単体テスト（天候・地形・サイドフィールド・グローバルフィールド）"""
import math
from jpoke import Battle, Pokemon
from jpoke.enums import Command, Event
from jpoke.core import BattleContext
from jpoke.model.move import Move
import test_utils as t


# 定数定義
DEFAULT_DURATION = 999  # フィールド効果のデフォルト継続ターン数


def test_はれ_ほのお強化():
    """はれ: ほのお技威力1.5倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("はれ", DEFAULT_DURATION),
    )
    6144 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_はれ_みず弱化():
    """はれ: みず技威力0.5倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("はれ", DEFAULT_DURATION),
    )
    2048 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_あめ_みず強化():
    """あめ: みず技威力1.5倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("あめ", DEFAULT_DURATION),
    )
    6144 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_あめ_ほのお弱化():
    """あめ: ほのお技威力0.5倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("あめ", DEFAULT_DURATION),
    )
    2048 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_すなあらし_ダメージ():
    """すなあらし: ターン終了時ダメージ"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], 
        weather=("すなあらし", DEFAULT_DURATION)
    )
    battle.events.emit(Event.ON_TURN_END_1)
    actual_damages = [mon.max_hp - mon.hp for mon in battle.actives]
    expected_damages = [mon.max_hp // 16 for mon in battle.actives]
    assert actual_damages == expected_damages, "Incorrect sandstorm damage applied"


def test_すなあらし_いわ無効():
    """すなあらし: いわタイプはダメージを受けない"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("イシツブテ")],
        weather=("すなあらし", DEFAULT_DURATION),
    )
    battle.events.emit(Event.ON_TURN_END_1)
    actual_damages = [mon.max_hp - mon.hp for mon in battle.actives]
    expected_damages = [0, battle.actives[1].max_hp // 16]
    assert actual_damages == expected_damages, "Incorrect sandstorm damage applied"


def test_すなあらし_いわ特防強化():
    """すなあらし: いわタイプ特防1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["スピードスター"])],
        foe=[Pokemon("イシツブテ")],
        weather=("すなあらし", DEFAULT_DURATION),
    )
    6144 == t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER)


def test_ゆき_こおり防御強化():
    """ゆき: こおりタイプ防御1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ユキワラシ")],
        weather=("ゆき", DEFAULT_DURATION),
    )
    6144 == t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER)


def test_エレキフィールド_でんき強化():
    """エレキフィールド: でんき技威力1.3倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    assert 5325 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)

    floating_battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピジョン", moves=["でんきショック"])],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    assert 4096 == t.calc_damage_modifier(floating_battle, Event.ON_CALC_POWER_MODIFIER)


def test_エレキフィールド_ねむり防止():
    """エレキフィールド: ねむり無効"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    target = battle.actives[0]
    result = battle.ailment_manager.apply(target, "ねむり")
    assert not result, "エレキフィールド下でねむりが付与された"
    assert not target.ailment.is_active, "エレキフィールド下でねむり状態が付与された"

    floating_battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピジョン")],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    floating_target = floating_battle.actives[0]
    assert floating_battle.ailment_manager.apply(floating_target, "ねむり")
    assert floating_target.ailment.is_active


def test_エレキフィールド_ねむけ防止():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], 
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    target = battle.actives[0]
    assert not battle.volatile_manager.apply(target, "ねむけ", count=2)
    assert not target.has_volatile("ねむけ")

    floating_battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピジョン")],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    floating_target = floating_battle.actives[0]
    assert floating_battle.volatile_manager.apply(floating_target, "ねむけ", count=2)
    assert floating_target.has_volatile("ねむけ")


def test_グラスフィールド_くさ強化():
    """グラスフィールド: くさ技威力1.3倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("フシギダネ", moves=["はっぱカッター"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    assert 5325 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)

    floating_battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピジョン", moves=["はっぱカッター"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    assert 4096 == t.calc_damage_modifier(floating_battle, Event.ON_CALC_POWER_MODIFIER)


def test_グラスフィールド_じしん弱化():
    """グラスフィールド: じしん威力0.5倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("サンドパン", moves=["じしん"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    2048 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_グラスフィールド_じならし弱化():
    """グラスフィールド: じならし威力0.5倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("サンドパン", moves=["じならし"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    2048 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_グラスフィールド_回復():
    """グラスフィールド: ターン終了時1/16回復"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], 
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.events.emit(Event.ON_TURN_END_2)
    assert mon.hp == 1 + mon.max_hp // 16, "グラスフィールドの回復量が不正"

    floating_battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピジョン")],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    floating_mon = floating_battle.actives[0]
    floating_mon._hp = 1
    floating_battle.events.emit(Event.ON_TURN_END_2)
    assert floating_mon.hp == 1


def test_サイコフィールド_エスパー強化():
    """サイコフィールド: エスパー技威力1.3倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("フーディン", moves=["サイコキネシス"])],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    assert 5325 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)

    floating_battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピジョン", moves=["サイコキネシス"])],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    assert 4096 == t.calc_damage_modifier(floating_battle, Event.ON_CALC_POWER_MODIFIER)


def test_サイコフィールド_先制技無効():
    """サイコフィールド: 先制技無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)


def test_サイコフィールド_浮遊は先制技有効():
    """サイコフィールド: 浮遊相手には先制技が有効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピジョン")],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE)


def test_ミストフィールド_ドラゴン技弱化():
    """ミストフィールド: ドラゴン技威力0.5倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("カイリュー", moves=["りゅうのはどう"])],
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_ミストフィールド_混乱防止():
    """ミストフィールド: 混乱無効化"""
    # ミストフィールド下では混乱付与が失敗する
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], 
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    mon = battle.actives[0]
    result = battle.volatile_manager.apply(mon, "こんらん", count=3)
    assert not result, "ミストフィールド下で混乱が付与された"
    assert "こんらん" not in mon.volatiles, "混乱状態が追加されている"


def test_ミストフィールド_状態異常防止():
    """ミストフィールド: 状態異常無効化"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], 
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    assert not battle.ailment_manager.apply(battle.actives[0], "どく")


def test_じゅうりょく_命中補正():
    """じゅうりょく: 命中率5/3倍"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], global_field={"じゅうりょく": DEFAULT_DURATION})
    assert 50 == t.calc_accuracy(battle, base=30)


def test_じゅうりょく_浮遊無効():
    """じゅうりょく: 浮遊状態を無効化"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピジョン")],
        global_field={"じゅうりょく": DEFAULT_DURATION},
    )
    assert not battle.query_manager.is_floating(battle.actives[0]), "じゅうりょくで浮遅が無効化されない"


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


def test_マジックルーム_道具効果無効化():
    """マジックルーム: 持ち物効果が無効化される"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ", item="じしゃく", moves=["でんきショック"])],
        global_field={"マジックルーム": DEFAULT_DURATION},
    )
    battle.refresh_item_enabled_states()
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_マジックルーム_終了で道具効果復活():
    """マジックルーム: 解除後に持ち物効果が復活する"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ", item="じしゃく", moves=["でんきショック"])],
        global_field={"マジックルーム": 1},
    )
    battle.refresh_item_enabled_states()
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)

    battle.events.emit(Event.ON_TURN_END_4)
    assert 4915 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_マジックルーム_再使用で解除():
    """マジックルーム: 効果中に再使用すると解除される"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")], 
        ally=[Pokemon("ピカチュウ", item="じしゃく", moves=["マジックルーム", "でんきショック"])],
    )
    user = battle.actives[0]

    battle.run_move(user, user.moves[0])
    assert battle.get_global_field("マジックルーム").is_active
    assert not user.item.enabled

    battle.run_move(user, user.moves[0])
    assert not battle.get_global_field("マジックルーム").is_active
    assert user.item.enabled


def test_ワンダールーム_物理技は特防側を参照():
    """ワンダールーム: 物理技の防御参照が特防側に入れ替わる"""
    normal = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    normal_defender = normal.actives[1]
    normal_defender.rank["B"] = 6
    normal_defender.rank["D"] = -6
    normal_ctx = BattleContext(attacker=normal.actives[0], defender=normal_defender, move=normal.actives[0].moves[0])
    normal_def = normal.damage_calculator.calc_final_defense(normal_ctx)

    wonder = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
        global_field={"ワンダールーム": DEFAULT_DURATION},
    )
    wonder_defender = wonder.actives[1]
    wonder_defender.rank["B"] = 6
    wonder_defender.rank["D"] = -6
    wonder_ctx = BattleContext(attacker=wonder.actives[0], defender=wonder_defender, move=wonder.actives[0].moves[0])
    wonder_def = wonder.damage_calculator.calc_final_defense(wonder_ctx)

    assert wonder_def < normal_def


def test_ワンダールーム_特殊技は防御側を参照():
    """ワンダールーム: 特殊技の防御参照が防御側に入れ替わる"""
    normal = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        foe=[Pokemon("ピカチュウ")],
    )
    normal_defender = normal.actives[1]
    normal_defender.rank["B"] = -6
    normal_defender.rank["D"] = 6
    normal_ctx = BattleContext(attacker=normal.actives[0], defender=normal_defender, move=normal.actives[0].moves[0])
    normal_def = normal.damage_calculator.calc_final_defense(normal_ctx)

    wonder = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        foe=[Pokemon("ピカチュウ")],
        global_field={"ワンダールーム": DEFAULT_DURATION},
    )
    wonder_defender = wonder.actives[1]
    wonder_defender.rank["B"] = -6
    wonder_defender.rank["D"] = 6
    wonder_ctx = BattleContext(attacker=wonder.actives[0], defender=wonder_defender, move=wonder.actives[0].moves[0])
    wonder_def = wonder.damage_calculator.calc_final_defense(wonder_ctx)

    assert wonder_def < normal_def


# ===== おおひでり =====

def test_おおひでり_ほのお強化():
    """おおひでり: ほのお技威力1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおひでり", DEFAULT_DURATION),
    )
    assert 6144 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_おおひでり_みず弱化():
    """おおひでり: みず技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおひでり", DEFAULT_DURATION),
    )
    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_おおひでり_みず攻撃技を失敗させる():
    """おおひでり: みずタイプ攻撃技は失敗する"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおひでり", DEFAULT_DURATION),
    )
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)


def test_おおひでり_ほのお技はブロックされない():
    """おおひでり: ほのお技はブロックされない"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおひでり", DEFAULT_DURATION),
    )
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE)


# ===== おおあめ =====

def test_おおあめ_みず強化():
    """おおあめ: みず技威力1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおあめ", DEFAULT_DURATION),
    )
    assert 6144 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_おおあめ_ほのお弱化():
    """おおあめ: ほのお技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおあめ", DEFAULT_DURATION),
    )
    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_おおあめ_ほのお攻撃技を失敗させる():
    """おおあめ: ほのおタイプ攻撃技は失敗する"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおあめ", DEFAULT_DURATION),
    )
    assert not t.check_event_result(battle, Event.ON_CHECK_MOVE)


def test_おおあめ_みず技はブロックされない():
    """おおあめ: みず技はブロックされない"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおあめ", DEFAULT_DURATION),
    )
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE)


# ===== らんきりゅう =====

def test_らんきりゅう_ひこう弱点軽減_でんき():
    """らんきりゅう: ひこうタイプへのでんき技弱点を0.5倍軽減"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe=[Pokemon("ピジョン")],
        weather=("らんきりゅう", DEFAULT_DURATION),
    )
    # ×2弱点 → ×1相当（4096 → 2048）
    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER)


def test_らんきりゅう_ひこう以外は軽減しない():
    """らんきりゅう: ひこうタイプでなければ軽減しない"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("らんきりゅう", DEFAULT_DURATION),
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER)


# ===== 強天候 上書き制御 =====

def test_強天候中は通常天候で上書きできない():
    """おおひでり中に通常天候(はれ)を発動しようとしても上書きされない"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおひでり", DEFAULT_DURATION),
    )
    result = battle.weather_manager.activate("はれ", 5)
    assert result is False
    assert battle.weather.name == "おおひでり"


def test_強天候同士は上書きできる():
    """おおひでり中におおあめを発動すると上書きされる"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおひでり", DEFAULT_DURATION),
    )
    result = battle.weather_manager.activate("おおあめ", DEFAULT_DURATION)
    assert result is True
    assert battle.weather.name == "おおあめ"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

