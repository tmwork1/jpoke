import math
from jpoke import Pokemon
from jpoke.utils.enums import Event
import test_utils as t


def test():
    print("--- やどりぎのタネ ---")
    battle = t.start_battle(
        turn=1,
        ally_volatile={"やどりぎのタネ": 1},
    )
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 7/8)

    print("--- こんらん: 自傷ダメージが発生する場合 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 2},
    )
    # 自傷を強制して動作を確認
    battle.test_option.ailment_trigger_rate = 1.0
    initial_hp = battle.actives[0].hp
    foe_initial_hp = battle.actives[1].hp
    battle.advance_turn()
    # 自傷ダメージでHPが減少（技が使えなかった）
    assert battle.actives[0].hp < initial_hp
    # 相手にダメージを与えていない（技が失敗した）
    assert battle.actives[1].hp == foe_initial_hp
    # 混乱カウントが減少
    assert battle.actives[0].volatiles["こんらん"].count == 1

    print("--- こんらん: 自傷が発生しない場合 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 2},
    )
    # 自傷を防止して通常行動を確認
    battle.test_option.ailment_trigger_rate = 0.0
    battle.advance_turn()
    # 混乱カウントが減少（技は使用できた）
    assert battle.actives[0].volatiles["こんらん"].count == 1

    print("--- こんらん: 自然治癒 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"こんらん": 1},
    )
    battle.advance_turn()
    # 混乱が解ける
    assert "こんらん" not in battle.actives[0].volatiles

    print("--- ちょうはつ: 変化技禁止 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["ひかりのかべ"])],
        ally_volatile={"ちょうはつ": 3},
    )
    # ひかりのかべ（変化技）を使おうとする
    from jpoke.utils.enums import Command
    initial_side_fields = len([f for f in battle.side_mgrs[0].fields.values() if f.is_active])
    battle.players[0].reserve_command(Command.MOVE_0)
    battle.players[1].reserve_command(Command.MOVE_0)
    battle.advance_turn()
    # ひかりのかべが発動していない（技が失敗した）
    active_side_fields = len([f for f in battle.side_mgrs[0].fields.values() if f.is_active])
    assert active_side_fields == initial_side_fields
    # ちょうはつ状態が維持
    assert battle.actives[0].check_volatile("ちょうはつ")

    print("--- ちょうはつ: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"ちょうはつ": 1},
    )
    battle.advance_turn()
    assert not battle.actives[0].check_volatile("ちょうはつ")

    print("--- バインド: ターン終了時ダメージ ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 3},
    )
    initial_hp = battle.actives[0].hp
    expected_damage = battle.actives[0].max_hp // 8
    # 1ターン進める
    battle.advance_turn()
    # バインドダメージが発生
    assert battle.actives[0].hp == initial_hp - expected_damage

    print("--- バインド: カウント減少と解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 1},
    )
    # 1ターン進めてバインドを解除
    battle.advance_turn()
    # バインドが解除される
    assert not battle.actives[0].check_volatile("バインド")

    print("--- メロメロ: 行動不能になる場合 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"メロメロ": 1},
    )
    # 行動不能を強制
    battle.test_option.ailment_trigger_rate = 1.0
    battle.advance_turn()
    # メロメロ状態が維持されていることを確認（永続効果）
    assert battle.actives[0].check_volatile("メロメロ")

    print("--- メロメロ: 行動できる場合 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"メロメロ": 1},
    )
    # 行動を許可
    battle.test_option.ailment_trigger_rate = 0.0
    battle.advance_turn()
    # メロメロ状態が維持されていることを確認（永続効果）
    assert battle.actives[0].check_volatile("メロメロ")

    print("--- かなしばり: 技使用禁止 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かなしばり": 4},
    )
    # 禁止技を設定
    battle.actives[0].volatiles["かなしばり"].disabled_move_name = "はねる"
    assert battle.actives[0].check_volatile("かなしばり")

    print("--- かなしばり: ターン経過で解除 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        ally_volatile={"かなしばり": 1},
    )
    battle.advance_turn()
    assert not battle.actives[0].check_volatile("かなしばり")

    print("--- バインド: ゴーストタイプは交代可能 ---")
    battle = t.start_battle(
        ally=[Pokemon("ゲンガー"), Pokemon("ピカチュウ")],
        ally_volatile={"バインド": 3},
    )
    # ゴーストタイプなので交代可能
    assert t.can_switch(battle, 0)

    print("--- バインド: 非ゴーストタイプは交代不可 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        ally_volatile={"バインド": 3},
    )
    # ゴーストタイプでないので交代コマンドが利用不可
    commands = battle.get_available_action_commands(battle.players[0])
    has_switch = any(c.is_switch() for c in commands)
    assert not has_switch, f"バインド状態で交代コマンドが利用可能: {[str(c) for c in commands]}"

    print("All volatile tests passed!")


if __name__ == "__main__":
    test()
