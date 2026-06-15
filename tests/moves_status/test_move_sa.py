"""変化技ハンドラの単体テスト（さ行・サ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_サイコフィールド_すでに同じフィールドなら失敗():
    """サイコフィールド: すでにサイコフィールド中は発動しない（失敗）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["サイコフィールド"])],
        team1=[Pokemon("カビゴン")],
        terrain=("サイコフィールド", 5),
    )
    t.run_move(battle, 0)

    # カウントは変わらない（再発動されない）
    assert battle.terrain.name == "サイコフィールド"
    assert battle.terrain.count == 5


def test_サイコフィールド_フィールドが5ターン展開される():
    """サイコフィールド: 使用すると5ターンのサイコフィールドが展開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["サイコフィールド"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.terrain.name == "サイコフィールド"
    assert battle.terrain.count == 5


def test_さいみんじゅつ_すでに状態異常なら失敗():
    """さいみんじゅつ: 対象がすでに状態異常を持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("まひ")
    assert not defender.has_ailment("ねむり")


def test_さいみんじゅつ_ねむり付与():
    """さいみんじゅつ: 相手をねむり状態にする（accuracy=100で固定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")


def test_しびれごな_すでに状態異常なら失敗():
    """しびれごな: 対象がすでに状態異常を持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しびれごな"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3),
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")
    assert not defender.has_ailment("まひ")


def test_しびれごな_まひ付与():
    """しびれごな: 相手をまひ状態にする（accuracy=100で固定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しびれごな"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("まひ")


def test_しんぴのまもり_すでにアクティブなら失敗():
    """しんぴのまもり: すでにしんぴのまもりが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しんぴのまもり"])],
        team1=[Pokemon("カビゴン")],
        side0={"しんぴのまもり": 4},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["しんぴのまもり"].is_active
    assert side.fields["しんぴのまもり"].count == 4


def test_しんぴのまもり_自陣営に5ターン設置される():
    """しんぴのまもり: 使用すると自陣営に5ターンのしんぴのまもりが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しんぴのまもり"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["しんぴのまもり"].is_active
    assert side.fields["しんぴのまもり"].count == 5


def test_せいちょう_おおひでり時こうげきととくこう2段階上がる():
    """せいちょう: おおひでり中もこうげきととくこうランクが2段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 2
    assert attacker.rank["C"] == 2


def test_せいちょう_はれ時こうげきととくこう2段階上がる():
    """せいちょう: はれ中はこうげきととくこうランクが2段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 2
    assert attacker.rank["C"] == 2


def test_せいちょう_通常時こうげきととくこう1段階上がる():
    """せいちょう: 通常天候ではこうげきととくこうランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["C"] == 1


def test_ソウルビート_全能力1段階上がりHP3分の1消費():
    """ソウルビート: 使用すると全能力が1段階ずつ上がり最大HPの1/3が消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ソウルビート"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["B"] == 1
    assert attacker.rank["C"] == 1
    assert attacker.rank["D"] == 1
    assert attacker.rank["S"] == 1
    assert attacker.hp == max_hp - (max_hp // 3)


def test_ソウルビート_全能力最大なら能力は変化しない():
    """ソウルビート: 全能力がすでに+6なら能力ランクは変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ソウルビート"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"A": 6, "B": 6, "C": 6, "D": 6, "S": 6}, source=attacker)
    t.run_move(battle, 0)

    # 全能力は変化しない
    assert attacker.rank["A"] == 6
    assert attacker.rank["B"] == 6
    assert attacker.rank["C"] == 6
    assert attacker.rank["D"] == 6
    assert attacker.rank["S"] == 6


def test_ミストフィールド_すでに同じフィールドなら失敗():
    """ミストフィールド: すでにミストフィールド中は発動しない（失敗）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミストフィールド"])],
        team1=[Pokemon("カビゴン")],
        terrain=("ミストフィールド", 5),
    )
    t.run_move(battle, 0)

    assert battle.terrain.name == "ミストフィールド"
    assert battle.terrain.count == 5


def test_ミストフィールド_フィールドが5ターン展開される():
    """ミストフィールド: 使用すると5ターンのミストフィールドが展開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミストフィールド"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.terrain.name == "ミストフィールド"
    assert battle.terrain.count == 5
