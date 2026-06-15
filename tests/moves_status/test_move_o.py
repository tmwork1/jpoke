"""変化技ハンドラの単体テスト（お行）。"""

from jpoke import Pokemon
from jpoke.enums import LogCode
from .. import test_utils as t


def test_おいかぜ_すでにおいかぜなら失敗():
    """おいかぜ: すでにおいかぜが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいかぜ"])],
        team1=[Pokemon("カビゴン")],
        side0={"おいかぜ": 3},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["おいかぜ"].is_active
    assert side.fields["おいかぜ"].count == 3


def test_おいかぜ_自陣営に4ターン設置される():
    """おいかぜ: 使用すると自陣営に4ターンのおいかぜが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいかぜ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["おいかぜ"].is_active
    assert side.fields["おいかぜ"].count == 4


def test_おかたづけ_こうげきとすばやさが1段階ずつ上がる():
    """おかたづけ: 使用するとこうげきとすばやさが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["S"] == 1


def test_おかたづけ_みがわりを除去してかたづけおわりログが出る():
    """おかたづけ: 相手のみがわりを除去すると「かたづけ おわり!」TEXT_LOGが記録される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"みがわり": 1},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("みがわり")
    logs = battle.event_logger.logs
    assert any(
        log.log == LogCode.TEXT_LOG
        and log.payload is not None
        and log.payload.get("text") == "かたづけ おわり!"
        for log in logs
    )


def test_おかたづけ_相手陣営のまきびしを除去する():
    """おかたづけ: 相手陣営のまきびしを除去する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
        side1={"まきびし": 1},
    )
    foe_side = battle.get_side(battle.actives[1])
    assert foe_side.get("まきびし").is_active
    t.run_move(battle, 0)

    assert not foe_side.get("まきびし").is_active


def test_おきみやげ_まもるで防がれると使用者はひんしにならない():
    """おきみやげ: 相手にまもるがかかっている場合、使用者はひんしにならない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おきみやげ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手にまもるを付与する
    battle.volatile_manager.apply(defender, "まもる", count=1)
    t.run_move(battle, 0)

    assert not attacker.fainted
    assert defender.rank["A"] == 0
    assert defender.rank["C"] == 0


def test_おきみやげ_使用者がひんしになる():
    """おきみやげ: 使用者がひんしになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おきみやげ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.fainted


def test_おきみやげ_相手のこうげきとくこうが2段階下がる():
    """おきみやげ: 相手のこうげきととくこうが2段階ずつ下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おきみやげ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["A"] == -2
    assert defender.rank["C"] == -2


def test_おたけび_こうげきとくこう1段階ずつ下がる():
    """おたけび: 相手のこうげきととくこうランクが1段階ずつ下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おたけび"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["A"] == -1
    assert defender.rank["C"] == -1


def test_おたけび_すでに最低ランクなら変化なし():
    """おたけび: こうげき・とくこうがともにすでに-6ならランク変化なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おたけび"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"A": -6, "C": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["A"] == -6
    assert defender.rank["C"] == -6


def test_おだてる_すでにこんらんかつとくこう最大なら失敗():
    """おだてる: とくこうが+6かつこんらん済みなら技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"C": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    # とくこうは変化せず、こんらんも新たに付与されない
    assert defender.rank["C"] == 6
    assert defender.volatiles["こんらん"].count == 3


def test_おだてる_とくこう1段階上がりこんらん付与():
    """おだてる: 相手のとくこうが1段階上がり、こんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["C"] == 1
    assert defender.has_volatile("こんらん")
