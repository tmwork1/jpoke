"""技ハンドラの単体テスト"""
import math
from jpoke import Pokemon
import test_utils as t


def test_arm_hammer_speed_reduction():
    """アームハンマー: 素早さ低下"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["アームハンマー"])],
        turn=1
    )
    assert battle.actives[0].rank["S"] == -1, "アームハンマー: 素早さ低下失敗"


def test_sandstorm_weather():
    """すなあらし: 天気設定"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["すなあらし"])],
        turn=1
    )
    assert battle.weather == "すなあらし", "すなあらし: 天気設定失敗"


def test_thunderbolt_paralysis():
    """でんじほう: まひ適用"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんじほう"])],
        foe=[Pokemon("フシギバナ")],
        turn=1
    )
    assert battle.actives[1].ailment == "まひ", "でんじほう: まひ適用失敗"


def test_flinch_prevents_action():
    """いわなだれ: ひるみで後攻が行動不能"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["いわなだれ"])],
        foe=[Pokemon("フシギダネ", moves=["たいあたり"])],
        turn=0
    )
    battle.test_option.ailment_trigger_rate = 1.0
    t.run_turn(battle)

    assert battle.actives[0].hp == battle.actives[0].max_hp, "いわなだれ: ひるみで被弾してしまった"


def test_flinch_no_effect_when_target_moved_first():
    """先攻側が先に行動した場合はひるみしない"""
    battle = t.start_battle(
        ally=[Pokemon("フシギダネ", moves=["いわなだれ"])],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        turn=0
    )
    battle.test_option.ailment_trigger_rate = 1.0
    t.run_turn(battle)

    assert battle.actives[0].hp < battle.actives[0].max_hp, "先行後ひるみ: 行動が止まってしまった"


def test_flinch_blocked_by_inner_focus():
    """せいしんりょく: ひるみ無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["いわなだれ"])],
        foe=[Pokemon("フシギダネ", ability="せいしんりょく", moves=["たいあたり"])],
        turn=0
    )
    battle.test_option.ailment_trigger_rate = 1.0
    t.run_turn(battle)

    assert battle.actives[0].hp < battle.actives[0].max_hp, "せいしんりょく: ひるみ無効化に失敗"


def test_volt_switch_switch():
    """とんぼがえり: 交代"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["とんぼがえり"]) for _ in range(2)],
        turn=1
    )
    assert battle.players[0].active_idx != 0, "とんぼがえり: 交代失敗"


def test_struggle_damage():
    """わるあがき: ダメージ計算"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["わるあがき"])],
        turn=1
    )
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 3/4), "わるあがき: ダメージ計算失敗"


def test_ニトロチャージ():
    """ニトロチャージ: 自分のS+1"""
    battle = t.start_battle(
        ally=[Pokemon("リザードン", moves=["ニトロチャージ"])],
        turn=1
    )
    assert battle.actives[0].rank["S"] == 1


def test_がんせきふうじ():
    """がんせきふうじ: 相手のS-1"""
    battle = t.start_battle(
        ally=[Pokemon("イワーク", moves=["がんせきふうじ"])],
        foe=[Pokemon("ピジョン")],
        turn=1
    )
    assert battle.actives[1].rank["S"] == -1


def test_じならし():
    """じならし: 相手のS-1"""
    battle = t.start_battle(
        ally=[Pokemon("サンドパン", moves=["じならし"])],
        foe=[Pokemon("ゲンガー")],
        turn=1
    )
    assert battle.actives[1].rank["S"] == -1


def test_ドラムアタック():
    """ドラムアタック: 相手のS-1"""
    battle = t.start_battle(
        ally=[Pokemon("フシギバナ", moves=["ドラムアタック"])],
        foe=[Pokemon("ピカチュウ")],
        turn=1
    )
    assert battle.actives[1].rank["S"] == -1


def test_ソウルクラッシュ():
    """ソウルクラッシュ: 相手のC-1"""
    battle = t.start_battle(
        ally=[Pokemon("プリン", moves=["ソウルクラッシュ"])],
        foe=[Pokemon("フーディン")],
        turn=1
    )
    assert battle.actives[1].rank["C"] == -1


def test_トロピカルキック():
    """トロピカルキック: 相手のA-1"""
    battle = t.start_battle(
        ally=[Pokemon("モンジャラ", moves=["トロピカルキック"])],
        foe=[Pokemon("カイリキー")],
        turn=1
    )
    assert battle.actives[1].rank["A"] == -1


def test_オーバーヒート():
    """オーバーヒート: 自分のC-2"""
    battle = t.start_battle(
        ally=[Pokemon("キュウコン", moves=["オーバーヒート"])],
        foe=[Pokemon("ニドキング")],
        turn=1
    )
    assert battle.actives[0].rank["C"] == -2


def test_インファイト():
    """インファイト: 自分のBD-1"""
    battle = t.start_battle(
        ally=[Pokemon("サワムラー", moves=["インファイト"])],
        foe=[Pokemon("ゴローニャ")],
        turn=1
    )
    assert battle.actives[0].rank["B"] == -1
    assert battle.actives[0].rank["D"] == -1


def test_かたくなる():
    """かたくなる: 自分のB+1"""
    battle = t.start_battle(
        ally=[Pokemon("パルシェン", moves=["かたくなる"])],
        turn=1
    )
    assert battle.actives[0].rank["B"] == 1


def test_こうそくいどう():
    """こうそくいどう: 自分のS+2"""
    battle = t.start_battle(
        ally=[Pokemon("ペルシアン", moves=["こうそくいどう"])],
        turn=1
    )
    assert battle.actives[0].rank["S"] == 2


def test_なきごえ():
    """なきごえ: 相手のA-1"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["なきごえ"])],
        foe=[Pokemon("カイリキー")],
        turn=1
    )
    assert battle.actives[1].rank["A"] == -1


def test_こわいかお():
    """こわいかお: 相手のS-2"""
    battle = t.start_battle(
        ally=[Pokemon("ギャラドス", moves=["こわいかお"])],
        foe=[Pokemon("ゲンガー")],
        turn=1
    )
    assert battle.actives[1].rank["S"] == -2


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
