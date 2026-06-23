"""攻撃技ハンドラの単体テスト（た行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


@pytest.mark.parametrize(
    "roll, expected",
    [
        (0.0, 2),
        (0.3749, 2),
        (0.375, 3),
        (0.7499, 3),
        (0.75, 4),
        (0.8749, 4),
        (0.875, 5),
        (0.9999, 5),
    ],
)
def test_タネマシンガン_ヒット数が2から5の範囲で決まる(roll: float, expected: int):
    """タネマシンガン: 乱数ロールに応じて2~5ヒットが決まる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["タネマシンガン"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.random.random = lambda: roll
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert hit_count == expected


def test_タネマシンガン_相手HP1で最初の1発で処理中断():
    """タネマシンガン: 相手の初期HPが1のときに、最初の1発で相手がひんしになり処理が中断される。"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["タネマシンガン"])],
    )

    # 相手のHPを1に設定（最大HPから現在HPを1に減らす処理）
    defender = battle.actives[1]
    defender.hp = 1

    # ダメージ計算の呼び出し回数をカウント
    damage_call_count = 0

    def counting_determine_damage(attacker, defender, move, critical=False):
        nonlocal damage_call_count
        damage_call_count += 1
        return 1  # 常に1ダメージ

    battle.roll_damage = counting_determine_damage
    battle.advance_turn()

    # 複数ヒット予定（min_hits=2）なのに、最初の1発で相手がひんしになったため処理が中断される
    # ダメージ計算が1回だけ実行される
    assert damage_call_count == 1
    assert defender.hp == 0


def test_ダイヤストーム_防御2段階上昇が発動する():
    """ダイヤストーム: 確率50%で使用者のBが2段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("ディアンシー", move_names=["ダイヤストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["B"] == 2


def test_ダストシュート_どくが発動する():
    """ダストシュート: 30%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ダストシュート"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_ダブルニードル_どくが発動する():
    """ダブルニードル: 20%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ダブルニードル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_ちきゅうなげ_ゴーストには無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちきゅうなげ"])],
        team1=[Pokemon("ゴース", move_names=["はねる"])],
    )
    battle.advance_turn()
    assert battle.actives[1].hp == battle.actives[1].max_hp


def test_テラバースト_ステラ():
    """ステラタイプ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="ステラ", move_names=["テラバースト"])],
        team1=[Pokemon("ピカチュウ", tera_type="でんき")],
    )
    attacker = battle.actives[0]
    attacker.terastallize()
    move = t.run_move(battle, 0)

    assert battle.move_executor.move_type == "ステラ"
    assert battle.damage_calculator.final_power == 100
    assert attacker.rank["A"] == -1
    assert attacker.rank["C"] == -1


def test_テラバースト_テラスタル時にタイプがテラスタイプへ変化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="ほのお", move_names=["テラバースト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.resolve_move_type(attacker, move) == "ノーマル"

    attacker.terastallize()
    assert battle.move_executor.resolve_move_type(attacker, move) == "ほのお"

    move.unregister_handlers(battle.events, attacker)


@pytest.mark.parametrize(
    ("attacker_name", "expected"),
    [
        ("カイリキー", "物理"),
        ("フーディン", "特殊"),
    ],
)
def test_テラバースト_テラスタル時に高い攻撃値の分類になる(attacker_name: str, expected: str):
    battle = t.start_battle(
        team0=[Pokemon(attacker_name, tera_type="でんき", move_names=["テラバースト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.resolve_move_category(attacker, move) == "特殊"
    attacker.terastallize()
    assert battle.move_executor.resolve_move_category(attacker, move) == expected


def test_でんきショック_まひが発動する():
    """でんきショック: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_とびはねる_まひが発動する():
    """とびはねる: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とびはねる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_どくづき_どくが発動する():
    """どくづき: 30%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくづき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_どくどくのキバ_もうどくが発動する():
    """どくどくのキバ: 50%でもうどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくどくのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_どくばり_どくが発動する():
    """どくばり: 30%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくばり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_どくばりセンボン_どくが発動する():
    """どくばりセンボン: 50%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくばりセンボン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"
