"""フィールド効果ハンドラの単体テスト（天候・地形・サイドフィールド・グローバルフィールド）"""
import math
from jpoke import Battle, Pokemon
from jpoke.core.event import Event, EventContext
from jpoke.model.move import Move
import test_utils as t

# 定数定義
DEFAULT_DURATION = 999  # フィールド効果のデフォルト継続ターン数

# 威力補正の期待値（4096基準）
BASE_MODIFIER = 4096  # 補正計算の基準値
WEATHER_BOOST = 1.5  # 天候による威力強化
WEATHER_NERF = 0.5   # 天候による威力弱化
TERRAIN_BOOST = 1.3  # 地形による威力強化
TERRAIN_NERF = 0.5   # 地形による威力弱化

# ダメージ計算
SANDSTORM_DAMAGE_RATIO = 15 / 16  # すなあらしダメージ後のHP割合


def create_power_modifier_context(battle: Battle, attacker_idx: int = 0) -> EventContext:
    """技威力補正のイベントコンテキストを作成するヘルパー関数。

    Args:
        battle: Battleインスタンス
        attacker_idx: 攻撃側のインデックス（デフォルト: 0）

    Returns:
        EventContext: イベントコンテキスト
    """
    defender_idx = 1 - attacker_idx
    return EventContext(
        attacker=battle.actives[attacker_idx],
        defender=battle.actives[defender_idx],
        move=battle.actives[attacker_idx].moves[0]
    )


def assert_power_modifier(battle: Battle, expected: float, message: str = ""):
    """技威力補正値を検証するヘルパー関数。

    Args:
        battle: Battleインスタンス
        expected: 期待される補正値（倍率）
        message: アサーション失敗時のメッセージ
    """
    ctx = create_power_modifier_context(battle)
    modifier = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, BASE_MODIFIER)
    # 4096基準の整数値として計算（value * multiplier // 4096の逆算）
    expected_value = int(BASE_MODIFIER * expected)
    assert modifier == expected_value, f"{message}: expected {expected_value} ({expected}x), got {modifier}"


def create_def_modifier_context(battle: Battle, defender_idx: int = 0) -> EventContext:
    """防御補正のイベントコンテキストを作成するヘルパー関数。"""
    attacker_idx = 1 - defender_idx
    return EventContext(
        attacker=battle.actives[attacker_idx],
        defender=battle.actives[defender_idx],
        move=battle.actives[attacker_idx].moves[0]
    )


def assert_def_modifier(battle: Battle, expected: float, message: str = ""):
    """防御補正値を検証するヘルパー関数。"""
    ctx = create_def_modifier_context(battle)
    modifier = battle.events.emit(Event.ON_CALC_DEF_MODIFIER, ctx, BASE_MODIFIER)
    expected_value = int(BASE_MODIFIER * expected)
    assert modifier == expected_value, f"{message}: expected {expected_value} ({expected}x), got {modifier}"


def test_はれ_ほのお技強化():
    """はれ: ほのお技威力1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("はれ", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, WEATHER_BOOST, "はれでほのお技が強化されない")


def test_はれ_みず技弱化():
    """はれ: みず技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("はれ", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, WEATHER_NERF, "はれでみず技が弱化されない")


def test_あめ_みず技強化():
    """あめ: みず技威力1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("あめ", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, WEATHER_BOOST, "あめでみず技が強化されない")


def test_あめ_ほのお技弱化():
    """あめ: ほのお技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("あめ", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, WEATHER_NERF, "あめでほのお技が弱化されない")


def test_すなあらし_ダメージ():
    """すなあらし: ターン終了時ダメージ"""
    battle = t.start_battle(weather=("すなあらし", DEFAULT_DURATION), turn=1)
    expected_hps = [math.ceil(mon.max_hp * SANDSTORM_DAMAGE_RATIO) for mon in battle.actives]
    assert battle.actives[0].hp == expected_hps[0], "味方がすなあらしダメージを受けていない"
    assert battle.actives[1].hp == expected_hps[1], "相手がすなあらしダメージを受けていない"


def test_すなあらし_いわタイプ無効():
    """すなあらし: いわタイプは無効"""
    battle = t.start_battle(
        ally=[Pokemon("イシツブテ")],
        weather=("すなあらし", DEFAULT_DURATION),
        turn=1,
    )
    assert battle.actives[0].hp == battle.actives[0].max_hp, "いわタイプがすなあらしダメージを受けた"


def test_すなあらし_いわタイプ特防上昇():
    """すなあらし: いわタイプ特防1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("イシツブテ")],
        foe=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        weather=("すなあらし", DEFAULT_DURATION),
    )
    assert_def_modifier(battle, WEATHER_BOOST, "すなあらしでいわタイプの防御補正が上がらない")

    battle_no_boost = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        weather=("すなあらし", DEFAULT_DURATION),
    )
    assert_def_modifier(battle_no_boost, 1.0, "すなあらしで非いわタイプの防御補正が変化した")


def test_ゆき_こおりタイプ防御上昇():
    """ゆき: こおりタイプ防御1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ユキワラシ")],
        foe=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        weather=("ゆき", DEFAULT_DURATION),
    )
    assert_def_modifier(battle, WEATHER_BOOST, "ゆきでこおりタイプの防御補正が上がらない")

    battle_no_boost = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        weather=("ゆき", DEFAULT_DURATION),
    )
    assert_def_modifier(battle_no_boost, 1.0, "ゆきで非こおりタイプの防御補正が変化した")


def test_エレキフィールド_でんき技強化():
    """エレキフィールド: でんき技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_BOOST, "エレキフィールドででんき技が強化されない")

    # TODO: 浮いているポケモンは強化されないことを確認


def test_エレキフィールド_ねむり無効():
    """エレキフィールド: ねむり無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    target = battle.actives[0]
    result = target.apply_ailment(battle.events, "ねむり")
    assert not result, "エレキフィールド下でねむりが付与された"
    assert not target.ailment.is_active, "エレキフィールド下でねむり状態が付与された"

    # TODO: 浮いているポケモンはねむりが付与されることを確認

# TODO: エレキフィールドでのねむけ(揮発状態)防止のテストを追加。浮いているポケモンは防止されないことも確認


def test_グラスフィールド_くさ技強化():
    """グラスフィールド: くさ技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("フシギダネ", moves=["はっぱカッター"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_BOOST, "グラスフィールドでくさ技が強化されない")

    # TODO: 浮いているポケモンは強化されないことを確認


def test_グラスフィールド_じしん弱化():
    """グラスフィールド: じしん威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("サンドパン", moves=["じしん"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_NERF, "グラスフィールドでじしんが弱化されない")


def test_グラスフィールド_じならし弱化():
    """グラスフィールド: じならし威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("サンドパン", moves=["じならし"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_NERF, "グラスフィールドでじならしが弱化されない")


def test_グラスフィールド_ターン終了回復():
    """グラスフィールド: ターン終了時1/16回復"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    target = battle.actives[0]
    battle.modify_hp(target, v=-20)
    before_hp = target.hp

    t.run_turn(battle)

    expected_heal = int(target.max_hp / 16)
    expected_hp = min(target.max_hp, before_hp + expected_heal)
    assert target.hp == expected_hp, "グラスフィールドの回復量が不正"

    # TODO: 浮いているポケモンは回復しないことも確認


def test_サイコフィールド_エスパー技強化():
    """サイコフィールド: エスパー技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("フーディン", moves=["サイコキネシス"])],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_BOOST, "サイコフィールドでエスパー技が強化されない")

    # TODO: 浮いているポケモンは強化されないことを確認


def test_サイコフィールド_先制技無効():
    """サイコフィールド: 先制技無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    ctx = EventContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0]
    )
    result = battle.events.emit(Event.ON_CHECK_PRIORITY_VALID, ctx, True)
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
    ctx = EventContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0]
    )
    result = battle.events.emit(Event.ON_CHECK_PRIORITY_VALID, ctx, True)
    assert result is True, "サイコフィールドで浮遊相手に先制技が無効化された"


def test_ミストフィールド_ドラゴン技弱化():
    """ミストフィールド: ドラゴン技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("カイリュー", moves=["りゅうのはどう"])],
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_NERF, "ミストフィールドでドラゴン技が弱化されない")


def test_ミストフィールド_混乱防止():
    """ミストフィールド: 混乱無効化"""
    # まずフィールドなしで混乱付与が成功することを確認
    battle_no_field = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
    )
    target = battle_no_field.actives[0]
    result = target.apply_volatile(battle_no_field.events, "こんらん", count=3)
    assert result, "フィールドなしでも混乱が付与されない"
    assert "こんらん" in target.volatiles, "混乱状態が追加されていない"

    # ミストフィールド下では混乱付与が失敗する
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    target2 = battle.actives[0]
    result = target2.apply_volatile(battle.events, "こんらん", count=3)
    assert not result, "ミストフィールド下で混乱が付与された"
    assert "こんらん" not in target2.volatiles, "混乱状態が追加されている"


def test_ミストフィールド_状態異常防止():
    """ミストフィールド: 状態異常無効化"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    target = battle.actives[0]
    result = target.apply_ailment(battle.events, "どく")
    assert not result, "ミストフィールド下で状態異常が付与された"
    assert not target.ailment.is_active, "ミストフィールド下で状態異常が付与された"


def test_じゅうりょく_命中補正():
    """じゅうりょく: 命中率5/3倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe=[Pokemon("フシギダネ")],
        global_field={"じゅうりょく": 5},
    )
    ctx = EventContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0]
    )
    result = battle.events.emit(Event.ON_CALC_ACCURACY, ctx, 30)
    assert result == 50, "じゅうりょくで命中率補正が正しく適用されない"


def test_じゅうりょく_浮遊無効():
    """じゅうりょく: 浮遊状態を無効化"""
    battle = t.start_battle(
        ally=[Pokemon("ピジョン")],
        global_field={"じゅうりょく": 5},
    )
    target = battle.actives[0]
    assert not target.is_floating(battle.events), "じゅうりょくで浮遊が無効化されない"


def test_トリックルーム():
    """トリックルーム: フィールド有効化"""
    battle = t.start_battle(
        ally=[Pokemon("ヤドン")],
        foe=[Pokemon("ピカチュウ")],
        global_field={"トリックルーム": 5},
    )
    assert battle.field_mgr.fields["トリックルーム"].is_active, "トリックルームが有効化されていない"
    assert battle.field_mgr.fields["トリックルーム"].count == 5, "トリックルームのカウントが不正"


# TODO: トリックルーム 行動順が素早さの逆順になっていることをテスト

def test_トリックルーム_優先度反転():
    # TODO: トリックルーム下でも技の優先度に従って行動順が決まることを確認
    """トリックルーム: 優先度値を反転"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        global_field={"トリックルーム": 5},
    )
    ctx = EventContext(
        target=battle.actives[0],
        move=battle.actives[0].moves[0]
    )
    result = battle.events.emit(Event.ON_CALC_ACTION_SPEED, ctx, 1)
    assert result == -1, "トリックルームで優先度が反転しない"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
