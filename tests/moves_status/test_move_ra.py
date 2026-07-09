"""変化技ハンドラの単体テスト（ら行・リ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_リフレクター_すでにアクティブなら失敗():
    """リフレクター: すでにリフレクターが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リフレクター"])],
        team1=[Pokemon("カビゴン")],
        side0={"リフレクター": 4},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["リフレクター"].is_active
    assert side.fields["リフレクター"].count == 4


def test_リフレクター_自陣営に5ターン設置される():
    """リフレクター: 使用すると自陣営に5ターンのリフレクターが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リフレクター"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["リフレクター"].is_active
    assert side.fields["リフレクター"].count == 5


def test_リフレッシュ_まひを治す():
    """リフレッシュ: まひ状態のとき使用するとまひが回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["リフレッシュ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.apply_ailment(battle, 0, "まひ", by_foe=True)
    assert attacker.ailment.name == "まひ"
    # まひによる行動不能（12.5%）で技が不発になるとテストがフレーキーになるため固定する
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)
    assert not attacker.ailment.is_active


def test_リフレッシュ_やけどを治す():
    """リフレッシュ: やけど状態のとき使用するとやけどが回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["リフレッシュ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.apply_ailment(battle, 0, "やけど", by_foe=True)
    assert attacker.ailment.name == "やけど"
    t.run_move(battle, 0)
    assert not attacker.ailment.is_active


def test_リフレッシュ_状態異常がなければ失敗する():
    """リフレッシュ: 状態異常がない場合は技が失敗し、状態に変化がない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["リフレッシュ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    assert not attacker.ailment.is_active
    t.run_move(battle, 0)
    assert not attacker.ailment.is_active


def test_りゅうのまい_こうげきとすばやさ1段階ずつ上がる():
    """りゅうのまい: 使用すると自分のこうげきとすばやさランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spe"] == 1


def test_りゅうのまい_こうげき最大でもすばやさは上昇する():
    """りゅうのまい: こうげきがすでに+6でも、すばやさは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 6
    assert attacker.rank["spe"] == 1


def test_りゅうのまい_マジックコートで跳ね返されない():
    """りゅうのまい: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spe"] == 1
    assert defender.rank["atk"] == 0
    assert defender.rank["spe"] == 0


def test_りゅうのまい_自分対象のためまもるで防がれない():
    """りゅうのまい: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["りゅうのまい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spe"] == 1
