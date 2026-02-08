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
DAMAGE_WALL_MODIFIER = 0.5  # 壁によるダメージ軽減


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

# TODO: リフレクター　特殊技が軽減されないことを確認するテスト追加


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

# TODO: ひかりのかべ　物理技が軽減されないことを確認するテスト追加


def test_オーロラベール_ダメージ軽減():
    """オーロラベール: ダメージ0.5倍"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        ally_side_field={"オーロラベール": 1},
    )
    ctx = EventContext(
        attacker=battle.actives[1],
        defender=battle.actives[0],
        move=battle.actives[1].moves[0]
    )
    modifier = battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, BASE_MODIFIER)
    expected = int(BASE_MODIFIER * DAMAGE_WALL_MODIFIER)
    assert abs(modifier - expected) < 0.01, f"オーロラベールの補正値が不正: expected {expected}, got {modifier}"

# TODO: オーロラベール　特殊技も半減されることを確認するテスト追加


def test_しんぴのまもり():
    """しんぴのまもり: 状態異常防止"""
    # TODO: テスト実装
    pass


def test_おいかぜ():
    """おいかぜ: 実効すばやさ2倍"""
    # TODO: テスト実装
    pass


def test_しろいきり_能力低下防止():
    # TODO: 相手による能力低下を防ぐから確認するテストに修正
    """しろいきり: 能力ランク低下を防ぐ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ライチュウ")],
        ally_side_field={"しろいきり": 1},
    )
    target = battle.actives[0]
    before_rank = target.rank["A"]
    success = battle.modify_stat(target, "A", -1, source=battle.actives[1])
    after_rank = target.rank["A"]

    assert not success, "しろいきり有効時に能力低下が成功した"
    assert before_rank == after_rank, "しろいきりで能力低下が防げていない"

# TODO: しろいきり 自発的な能力低下は防げないことを確認するテスト追加


def test_ねがいごと_回復と解除():
    """ねがいごと: ターン終了時回復と解除"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_side_field={"ねがいごと": 1},
    )
    target = battle.actives[0]
    max_hp = target.max_hp

    # HPを減らして回復確認
    battle.modify_hp(target, v=-20)
    before_hp = target.hp

    # ターンを進行して回復を発動
    t.run_turn(battle)

    expected_heal = max_hp // 2
    expected_hp = min(max_hp, before_hp + expected_heal)
    assert target.hp == expected_hp, "ねがいごとの回復量が不正"
    assert not battle.side_mgrs[0].fields["ねがいごと"].is_active, "ねがいごとが解除されていない"


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

# TODO: まきびし2層のテスト実装


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

# TODO: まきびしで浮いているポケモンがダメージを受けないことを確認するテスト追加


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

# TODO: どくびしで浮いているポケモンが状態異常にならないことを確認するテスト追加
# TODO: どくタイプのポケモンが着地したときにどくびしが解除されることを確認するテスト追加

# TODO: ステルスロック タイプ補正1.0のときのダメージを検証するテスト追加


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

# TODO: ステルスロックで浮いているポケモンもダメージを受けることを確認するテスト追加


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

# TODO: ねばねばネットで浮いているポケモンの素早さが下がらないことを確認するテスト追加


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
