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

    assert defender.rank["S"] == -1
