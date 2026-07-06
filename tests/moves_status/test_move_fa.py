"""変化技ハンドラの単体テスト（ふぁ行）。"""


from jpoke import Pokemon
from .. import test_utils as t


def test_ファストガード_priority0技は通過する():
    """ファストガード: priority=0 の通常技は防がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        volatile0={"ファストガード": 1},
        accuracy=100,
    )
    defender = battle.actives[0]
    hp_before = defender.hp
    t.run_move(battle, 1)  # カビゴンがたいあたり（priority=0）を使う

    # ファストガードはpriority=0の技を防がないこと
    assert defender.hp < hp_before


def test_ファストガード_priority1技を防ぐ():
    """ファストガード: priority=1 のでんこうせっかを防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン", move_names=["でんこうせっか"])],
        volatile0={"ファストガード": 1},
        accuracy=100,
    )
    defender = battle.actives[0]
    hp_before = defender.hp
    t.run_move(battle, 1)  # カビゴンがでんこうせっかを使う

    # ファストガードがpriority=1の技を防いでいること
    assert defender.hp == hp_before


def test_ファストガード_連続使用で失敗する():
    """ファストガード: 2ターン連続で使用すると2ターン目は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ファストガード"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: ファストガード成功
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("ファストガード")

    # ターン終了でファストガードvolatileが解除される
    t.end_turn(battle)
    assert not attacker.has_volatile("ファストガード")

    # 2ターン目: 連続使用で失敗
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    assert not attacker.has_volatile("ファストガード")


def test_フラワーヒール_グラスフィールドで2_3回復する():
    """フラワーヒール: グラスフィールド展開中は相手のHPを最大HPの2/3回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フラワーヒール"])],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.hp == 1 + int(defender.max_hp * 2 / 3)


def test_フラワーヒール_満タンなら失敗する():
    """フラワーヒール: 相手のHPが満タンの場合は技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フラワーヒール"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    assert defender.hp == defender.max_hp
    t.run_move(battle, 0)

    assert defender.hp == defender.max_hp


def test_フラワーヒール_相手のHPを半分回復する():
    """フラワーヒール: 通常時、相手のHPを最大HPの1/2回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フラワーヒール"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.hp == 1 + int(defender.max_hp * 1 / 2)


def test_ふるいたてる_こうげきが上限でもとくこうは上がる():
    """ふるいたてる: こうげきがすでに+6でも、とくこうは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふるいたてる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 6
    assert attacker.rank["spa"] == 1


def test_ふるいたてる_こうげきとくこうが上がる():
    """ふるいたてる: 使用すると自分のこうげきとくこうランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふるいたてる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spa"] == 1


def test_ブレイブチャージ_とくこうとくぼうが上がり状態異常が治る():
    """ブレイブチャージ: 自分のとくこう・とくぼうが1段階ずつ上がり、状態異常が治る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ブレイブチャージ"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["spa"] == 1
    assert attacker.rank["spd"] == 1
    assert not attacker.ailment.is_active


def test_ブレイブチャージ_ランク上限でも技は失敗しない():
    """ブレイブチャージ: とくこう・とくぼうが+6でも技自体は失敗しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ブレイブチャージ"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
    )
    attacker = battle.actives[0]
    attacker.rank["spa"] = 6
    attacker.rank["spd"] = 6
    t.run_move(battle, 0)

    assert battle.move_executor.move_success
    assert attacker.rank["spa"] == 6
    assert attacker.rank["spd"] == 6
    assert not attacker.ailment.is_active


def test_ブレイブチャージ_状態異常がなくても技は失敗しない():
    """ブレイブチャージ: 状態異常がなくても技自体は失敗しない（リフレッシュとの違い）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ブレイブチャージ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert battle.move_executor.move_success
    assert attacker.rank["spa"] == 1
    assert attacker.rank["spd"] == 1
