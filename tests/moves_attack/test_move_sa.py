"""攻撃技ハンドラの単体テスト（さ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_10まんボルト_まひが発動する():
    """10まんボルト: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_サイケこうせん_こんらんが発動する():
    """サイケこうせん: 10%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["サイケこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_シェルアームズ_どくが発動する():
    """シェルアームズ: 20%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["シェルアームズ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_シグナルビーム_こんらんが発動する():
    """シグナルビーム: 10%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["シグナルビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_したでなめる_まひが発動する():
    """したでなめる: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["したでなめる"])],
        team1=[Pokemon("リザードン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_しんぴのちから_特攻1段階上昇が発動する():
    """しんぴのちから: 命中時に使用者のCが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["しんぴのちから"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["C"] == 1


def test_じゃどくのくさり_もうどくが発動する():
    """じゃどくのくさり: 50%でもうどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["じゃどくのくさり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_スパーク_まひが発動する():
    """スパーク: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スパーク"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_スモッグ_どくが発動する():
    """スモッグ: 40%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["スモッグ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"
