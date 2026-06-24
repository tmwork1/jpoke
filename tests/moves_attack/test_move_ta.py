"""攻撃技ハンドラの単体テスト（た行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_たきのぼり_ひるみが発動する():
    """たきのぼり: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["たきのぼり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_たつまき_ひるみが発動する():
    """たつまき: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["たつまき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


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


def test_だいもんじ_やけどが発動する():
    """だいもんじ: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["だいもんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


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


def test_ダブルパンツァー_ひるみが発動する():
    """ダブルパンツァー: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["ダブルパンツァー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ダークファイア_やけどが発動する():
    """ダークファイア: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ダークファイア"])],
        team1=[Pokemon("フーディン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ちきゅうなげ_ゴーストには無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちきゅうなげ"])],
        team1=[Pokemon("ゴース", move_names=["はねる"])],
    )
    battle.advance_turn()
    assert battle.actives[1].hp == battle.actives[1].max_hp


def test_つららおとし_ひるみが発動する():
    """つららおとし: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["つららおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_てっていこうせん_HP消費が最大HPの半分である():
    """てっていこうせん: 使用前に自分の最大HPの1/2を消費する。"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", move_names=["てっていこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    expected_cost = max(1, attacker.max_hp // 2)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_cost


def test_てっていこうせん_HP消費後HP0でも相手にダメージを与える():
    """てっていこうせん: HP消費後にHP0になっても攻撃は相手に届く。"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", move_names=["てっていこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # HP消費でちょうど0になるように設定
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert defender.hp < defender.max_hp


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


def test_デスウイング_使用後に攻撃者のHPが回復する():
    """デスウイング: 与えたダメージの3/4だけ攻撃者のHPを回復する（heal_ratio=0.75）。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["デスウイング"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_デスウイングとドレインキッスの回復量比較():
    """heal_ratio=0.75のデスウイング/ドレインキッスは0.5技より多く回復する。"""
    battle_death = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["デスウイング"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle_drain = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["ドレインパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    for b in (battle_death, battle_drain):
        b.actives[0].hp = 1
    t.run_move(battle_death, 0)
    t.run_move(battle_drain, 0)
    # デスウイング（0.75）のほうがドレインパンチ（0.5）より多く回復しているはず
    assert battle_death.actives[0].hp >= battle_drain.actives[0].hp


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


def test_とっしん_使用後に攻撃者が反動ダメージを受ける():
    """とっしん: 与えたダメージの1/4を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["とっしん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_とびげり_命中時は失敗反動ダメージを受けない():
    """とびげり: 命中したときはON_MISSが発火しないため失敗反動はない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["とびげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # 命中時は使用者のHPは変わらない（反動なし）
    assert attacker.hp == hp_before


def test_とびげり_外れたとき失敗反動ダメージを受ける():
    """とびげり: 外れたとき自分の最大HPの1/2ダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["とびげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    expected_damage = max(1, attacker.max_hp // 2)
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_damage


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


def test_とびひざげり_labelsにrecoilが含まれない():
    """とびひざげり: labelsに"recoil"が含まれないこと（失敗反動はself_costであるため）。"""
    from jpoke.data.move import MOVES
    move_data = MOVES["とびひざげり"]
    assert "recoil" not in move_data.labels


def test_とびひざげり_命中時は失敗反動ダメージを受けない():
    """とびひざげり: 命中したときはON_MISSが発火しないため失敗反動はない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["とびひざげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # 命中時は使用者のHPは変わらない（反動なし）
    assert attacker.hp == hp_before


def test_とびひざげり_外れたとき失敗反動ダメージを受ける():
    """とびひざげり: 外れたとき自分の最大HPの1/2ダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["とびひざげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    expected_damage = max(1, attacker.max_hp // 2)
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_damage


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


def test_ドラゴンダイブ_ひるみが発動する():
    """ドラゴンダイブ: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンダイブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ドレインキッス_使用後に攻撃者のHPが回復する():
    """ドレインキッス: 与えたダメージの3/4だけ攻撃者のHPを回復する（heal_ratio=0.75）。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ドレインキッス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_ドレインパンチ_使用後に攻撃者のHPが回復する():
    """ドレインパンチ: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ドレインパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before
