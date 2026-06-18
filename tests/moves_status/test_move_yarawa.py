"""変化技ハンドラの単体テスト（や・ら・わ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_うらみ_相手が技を使っていない場合は失敗():
    """うらみ: 相手がまだ技を使っていない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うらみ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    pp_before = move.pp
    # カビゴンはまだ技を使っていないのでうらみは失敗するはず
    t.run_move(battle, 0)

    # PPは変化しない
    assert move.pp == pp_before


def test_うらみ_相手の技のPPが4減る():
    """うらみ: 相手が前のターンに使った技のPPが4減る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うらみ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    # カビゴンに技を使わせて executed_move を設定する
    t.run_move(battle, 1)
    pp_after_use = move.pp
    # うらみを使う
    t.run_move(battle, 0)

    assert move.pp == pp_after_use - 4


def test_ねがいごと_2ターン後にHPが回復する():
    """ねがいごと: 使用2ターン後に最大HPの半分を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねがいごと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    # HPを削っておく
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp
    expected_heal = mon.max_hp // 2

    # ねがいごとを使う
    t.run_move(battle, 0)
    assert battle.get_side(mon).get("ねがいごと").is_active
    assert mon.hp == hp_before  # まだ回復しない

    # ターン終了: count 2→1
    t.end_turn(battle)
    assert mon.hp == hp_before  # まだ回復しない

    # ターン終了: count 1→0 → 回復発動
    t.end_turn(battle)
    assert mon.hp == hp_before + expected_heal


def test_ねがいごと_フィールドが解除される():
    """ねがいごと: 回復後にフィールドが解除されること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねがいごと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert battle.get_side(mon).get("ねがいごと").is_active

    t.end_turn(battle)
    t.end_turn(battle)
    assert not battle.get_side(mon).get("ねがいごと").is_active


def test_ねがいごと_交代後は現在の場のポケモンが回復する():
    """ねがいごと: 使用者が交代しても同ポジションの現在のポケモンが回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねがいごと"]), Pokemon("ヤドラン")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    user = battle.actives[0]
    teammate = battle.player_states[battle.players[0]].team[1]

    # 回復量は使用者（ピカチュウ）の最大HPの半分
    expected_heal = user.max_hp // 2

    # 交代先（ヤドラン）のHPを削っておく
    battle.modify_hp(teammate, v=-expected_heal)
    hp_teammate_before = teammate.hp

    # ねがいごとを使う
    t.run_move(battle, 0)

    # 使用者を交代させる
    t.run_switch(battle, 0, 1)
    assert battle.actives[0] is teammate

    # ターン終了 × 2
    t.end_turn(battle)
    t.end_turn(battle)

    # 交代後のポケモン（ヤドラン）が回復していること
    assert teammate.hp == hp_teammate_before + expected_heal
    # 元の使用者（ピカチュウ）は回復していないこと（控え）
    assert user.hp == user.max_hp  # ピカチュウはHP変更していないので満タン


def test_ねがいごと_重複設置は失敗する():
    """ねがいごと: すでに設置済みなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねがいごと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]

    # 1回目: 設置成功（count=2）
    t.run_move(battle, 0)
    assert battle.get_side(mon).get("ねがいごと").is_active
    count_after_first = battle.get_side(mon).get("ねがいごと").count

    # 2回目: 失敗（フィールドはまだ有効）
    t.run_move(battle, 0)
    # カウントはリセットされず変化しない（重複設置されていない）
    assert battle.get_side(mon).get("ねがいごと").count == count_after_first


def test_ハロウィン_ゴーストタイプが付与される():
    """ハロウィン: 使用後に defender が「ゴースト」タイプになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハロウィン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.has_type("ゴースト")
    t.run_move(battle, 0)

    assert defender.has_type("ゴースト")


def test_ハロウィン_すでにゴーストタイプなら失敗():
    """ハロウィン: 相手がすでにゴーストタイプなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハロウィン"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # ゴーストタイプには付与されない
    assert not defender.has_volatile("ハロウィン")


def test_ハロウィン_ハロウィン状態を付与する():
    """ハロウィン: 相手にハロウィン状態を付与する（ゴーストタイプが追加される）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハロウィン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("ハロウィン")


def test_ハロウィン_交代後にゴーストタイプがリセットされる():
    """ハロウィン: 交代後に added_types がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハロウィン"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドラン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_type("ゴースト")

    # 交代後はゴーストタイプが消えること
    t.run_switch(battle, 1, 1)
    assert not defender.has_type("ゴースト")
    assert not defender.has_volatile("ハロウィン")


def test_やどりぎのタネ_すでにやどりぎ状態なら失敗():
    """やどりぎのタネ: 相手がすでにやどりぎのタネ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["やどりぎのタネ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"やどりぎのタネ": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["やどりぎのタネ"].count
    t.run_move(battle, 0)

    # カウントは変わらない（重複付与されない）
    assert defender.has_volatile("やどりぎのタネ")
    assert defender.volatiles["やどりぎのタネ"].count == old_count


def test_やどりぎのタネ_やどりぎのタネ状態を付与する():
    """やどりぎのタネ: 相手をやどりぎのタネ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["やどりぎのタネ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("やどりぎのタネ")


def test_ゆきげしき_おおひでり中は失敗する():
    """ゆきげしき: おおひでり中は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ゆきげしき"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "おおひでり"


def test_ゆきげしき_天気がゆきになる():
    """ゆきげしき: 使用後に天気がゆきになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ゆきげしき"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "ゆき"
    assert battle.weather.count == 5


def test_わたほうし_すばやさ最低なら変化なし():
    """わたほうし: 相手のすばやさがすでに-6ならランク変化なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["わたほうし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"S": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["S"] == -6


def test_わたほうし_相手のすばやさ1段階下がる():
    """わたほうし: 使用すると相手のすばやさランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["わたほうし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["S"] == -2
