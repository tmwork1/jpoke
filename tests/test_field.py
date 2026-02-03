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
POWER_BOOST = 1.5  # 天候・地形による威力強化
POWER_NERF = 0.5   # 天候・地形による威力弱化
TERRAIN_BOOST = 1.3  # 地形による威力強化
DAMAGE_WALL_MODIFIER = 0.5  # 壁によるダメージ軽減

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


def test_すなあらし_ダメージ():
    """すなあらし: ターン終了時ダメージ"""
    battle = t.start_battle(weather=("すなあらし", DEFAULT_DURATION), turn=1)
    expected_hp = math.ceil(battle.actives[0].max_hp * SANDSTORM_DAMAGE_RATIO)
    assert battle.actives[0].hp == expected_hp, "味方がすなあらしダメージを受けていない"
    assert battle.actives[1].hp == math.ceil(battle.actives[1].max_hp * SANDSTORM_DAMAGE_RATIO), "相手がすなあらしダメージを受けていない"


def test_すなあらし_いわタイプ無効():
    """すなあらし: いわタイプは無効"""
    battle = t.start_battle(
        ally=[Pokemon("イシツブテ")],
        weather=("すなあらし", DEFAULT_DURATION),
        turn=1,
    )
    assert battle.actives[0].hp == battle.actives[0].max_hp, "いわタイプがすなあらしダメージを受けた"


def test_すなあらし_すなかき無効():
    """すなあらし: 特性すなかきで無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すなかき")],
        weather=("すなあらし", DEFAULT_DURATION),
        turn=1,
    )
    assert battle.actives[0].hp == battle.actives[0].max_hp, "すなかき特性ですなあらしダメージを受けた"


def test_ゆき_ダメージなし():
    """ゆき: ダメージ効果なし（第9世代仕様）"""
    battle = t.start_battle(weather=("ゆき", DEFAULT_DURATION), turn=1)
    assert battle.actives[0].hp == battle.actives[0].max_hp, "ゆき天候でダメージを受けた"


def test_はれ_ほのお技強化():
    """はれ: ほのお技威力1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("はれ", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, POWER_BOOST, "はれでほのお技が強化されない")


def test_はれ_みず技弱化():
    """はれ: みず技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("はれ", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, POWER_NERF, "はれでみず技が弱化されない")


def test_あめ_みず技強化():
    """あめ: みず技威力1.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("あめ", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, POWER_BOOST, "あめでみず技が強化されない")


def test_あめ_ほのお技弱化():
    """あめ: ほのお技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("あめ", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, POWER_NERF, "あめでほのお技が弱化されない")


def test_グラスフィールド_くさ技強化():
    """グラスフィールド: くさ技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("フシギダネ", moves=["はっぱカッター"])],
        terrain=("グラスフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_BOOST, "グラスフィールドでくさ技が強化されない")


def test_エレキフィールド_でんき技強化():
    """エレキフィールド: でんき技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        terrain=("エレキフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_BOOST, "エレキフィールドででんき技が強化されない")


def test_サイコフィールド_エスパー技強化():
    """サイコフィールド: エスパー技威力1.3倍"""
    battle = t.start_battle(
        ally=[Pokemon("フーディン", moves=["サイコキネシス"])],
        terrain=("サイコフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, TERRAIN_BOOST, "サイコフィールドでエスパー技が強化されない")


def test_ミストフィールド_ドラゴン技弱化():
    """ミストフィールド: ドラゴン技威力0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("カイリュー", moves=["りゅうのはどう"])],
        terrain=("ミストフィールド", DEFAULT_DURATION),
    )
    assert_power_modifier(battle, POWER_NERF, "ミストフィールドでドラゴン技が弱化されない")


def test_リフレクター_ダメージ軽減():
    """リフレクター: 物理技ダメージ軽減"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        ally_side_field={"リフレクター": 5},
    )
    ctx = EventContext(
        attacker=battle.actives[1],
        defender=battle.actives[0],
        move=battle.actives[1].moves[0]
    )
    modifier = battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, BASE_MODIFIER)
    expected = int(BASE_MODIFIER * DAMAGE_WALL_MODIFIER)
    assert abs(modifier - expected) < 0.01, f"リフレクターの補正値が不正: expected {expected}, got {modifier}"


def test_ひかりのかべ_ダメージ軽減():
    """ひかりのかべ: 特殊技ダメージ軽減"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        ally_side_field={"ひかりのかべ": 5},
    )
    ctx = EventContext(
        attacker=battle.actives[1],
        defender=battle.actives[0],
        move=battle.actives[1].moves[0]
    )
    modifier = battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, BASE_MODIFIER)
    expected = int(BASE_MODIFIER * DAMAGE_WALL_MODIFIER)
    assert abs(modifier - expected) < 0.01, f"ひかりのかべの補正値が不正: expected {expected}, got {modifier}"


def test_まきびし_1層():
    """まきびし: 交代時1/8ダメージ（1層）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"まきびし": 1},
    )
    initial_hp = battle.players[0].team[1].hp
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    expected_damage = math.floor(battle.players[0].team[1].max_hp / 8)
    actual_damage = initial_hp - battle.players[0].active.hp
    assert actual_damage >= expected_damage, f"まきびしダメージ不足: expected>={expected_damage}, got {actual_damage}"


def test_まきびし_3層():
    """まきびし: 3層で1/4ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"まきびし": 3},
    )
    initial_hp = battle.players[0].team[1].hp
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    expected_damage = math.floor(battle.players[0].team[1].max_hp / 4)
    actual_damage = initial_hp - battle.players[0].active.hp
    assert actual_damage == expected_damage, f"まきびし3層ダメージ不正: expected {expected_damage}, got {actual_damage}"


def test_ステルスロック():
    """ステルスロック: 交代時タイプ相性ダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("リザードン")],
        ally_side_field={"ステルスロック": 1},
    )
    initial_hp = battle.players[0].team[1].hp
    max_hp = battle.players[0].team[1].max_hp
    player = battle.players[0]
    battle.run_switch(player, player.team[1])

    # リザードンはいわ技4倍弱点なので最大1/2ダメージ（2倍弱点は1/4）
    damage_2x = math.floor(max_hp / 4)
    actual_damage = initial_hp - battle.players[0].active.hp
    assert actual_damage >= damage_2x, f"ステルスロックダメージ不足: expected>={damage_2x}, got {actual_damage}"


def test_どくびし_1層():
    """どくびし: 交代時どく状態付与（1層）"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"どくびし": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert battle.players[0].active.ailment.name == "どく", "どくびしでどく状態にならない"


def test_どくびし_2層():
    """どくびし: 2層でもうどく状態付与"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"どくびし": 2},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert battle.players[0].active.ailment.name == "もうどく", "どくびし2層でもうどくにならない"


def test_ねばねばネット():
    """ねばねばネット: 交代時素早さ-1"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_side_field={"ねばねばネット": 1},
    )
    initial_rank = battle.players[0].team[1].rank["S"]
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert battle.players[0].active.rank["S"] == initial_rank - 1, "ねばねばネットで素早さが下がらない"


def test_しんぴのまもり():
    """しんぴのまもり: フィールド有効化"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_side_field={"しんぴのまもり": 1},
    )
    assert battle.side_mgrs[0].fields["しんぴのまもり"].is_active, "しんぴのまもりが有効化されていない"


def test_おいかぜ():
    """おいかぜ: フィールド有効化"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_side_field={"おいかぜ": 1},
    )
    assert battle.side_mgrs[0].fields["おいかぜ"].is_active, "おいかぜが有効化されていない"


def test_トリックルーム():
    """トリックルーム: フィールド有効化"""
    battle = t.start_battle(
        ally=[Pokemon("ヤドン")],
        foe=[Pokemon("ピカチュウ")],
        global_field={"トリックルーム": 5},
    )
    assert battle.field_mgr.fields["トリックルーム"].is_active, "トリックルームが有効化されていない"
    assert battle.field_mgr.fields["トリックルーム"].count == 5, "トリックルームのカウントが不正"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
