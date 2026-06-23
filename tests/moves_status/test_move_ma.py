"""変化技ハンドラの単体テスト（ま行）。"""

import pytest

from jpoke import Pokemon
from .. import test_utils as t


@pytest.mark.parametrize("initial_count,expected_count", [
    (0, 1),  # 未設置 → 1層目
    (1, 2),  # 1層 → 2層
    (2, 3),  # 2層 → 3層（最大）
    (3, 3),  # 最大層では変化なし（失敗）
])
def test_まきびし_カウント累積(initial_count: int, expected_count: int):
    """まきびし: count=0~3の各状態から使用したときのカウント変化を検証する"""
    if initial_count == 0:
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
            team1=[Pokemon("カビゴン")],
        )
    else:
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
            team1=[Pokemon("カビゴン")],
            side1={"まきびし": initial_count},
        )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)
    assert side.fields["まきびし"].count == expected_count


def test_まきびし_相手陣営に設置される():
    """まきびし: 使用すると相手陣営にまきびしが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[1])
    assert side.fields["まきびし"].is_active


def test_まわしげり_ひるみが発動する():
    """まわしげり: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["まわしげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_みずびたし_すでにみずタイプのみなら失敗():
    """みずびたし: 相手がすでにみずタイプのみなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.types == ["みず"]
    t.run_move(battle, 0)

    # volatile が付与されないこと
    assert not defender.has_volatile("みずびたし")


def test_みずびたし_テラスタル中はタイプが変わらない():
    """みずびたし: テラスタル中の相手には volatile が付与されてもタイプが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン", tera_type="ほのお")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # テラスタル状態にする
    defender.terastallized = True
    assert defender.active_tera_type == "ほのお"
    t.run_move(battle, 0)

    # volatile は付与されるが、タイプはテラスタルタイプが優先される
    assert defender.has_volatile("みずびたし")
    assert defender.types == ["ほのお"]


def test_みずびたし_ハロウィン後の相手に使うとaddedTypesがクリアされみずのみになる():
    """みずびたし: ハロウィン後の相手に使うと added_types がクリアされてみずタイプのみになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"ハロウィン": 0},
        accuracy=100,
    )
    defender = battle.actives[1]
    # ハロウィン付与後はゴーストタイプが追加されている
    assert defender.has_type("ゴースト")
    t.run_move(battle, 0)

    # みずびたし後は added_types がクリアされてみずのみになること
    assert defender.types == ["みず"]
    assert not defender.has_type("ゴースト")


def test_みずびたし_みずタイプに変える():
    """みずびたし: 使用後に defender がみずタイプのみになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.has_type("みず")
    t.run_move(battle, 0)

    assert defender.types == ["みず"]
    assert defender.has_volatile("みずびたし")


def test_みずびたし_交代すると元のタイプに戻る():
    """みずびたし: 交代後に volatile_override_type がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドラン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.types == ["みず"]

    # 交代後は元のタイプに戻ること
    t.run_switch(battle, 1, 1)
    assert not defender.has_volatile("みずびたし")
    assert defender.volatile_override_type is None
    # カビゴンはノーマルタイプ
    assert defender.types == ["ノーマル"]


def test_みずびたし_複合タイプに使うと成功しみずのみになる():
    """みずびたし: みず+ほのおの複合タイプを持つ相手にもみずのみになること"""
    # シャワーズはみずタイプのみなので、カメックス（みず）ではなく
    # ボルケニオン（みず+ほのお）を使う
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("ボルケニオン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert "みず" in defender.types
    assert "ほのお" in defender.types
    t.run_move(battle, 0)

    # みずタイプのみになること
    assert defender.types == ["みず"]
    assert defender.has_volatile("みずびたし")


def test_ミラータイプ_コピー後元のタイプが消える():
    """ミラータイプ: タイプコピー後にゴースト追加前のタイプがリセットされること"""
    # ハロウィンでゴーストが追加されたピカチュウがミラータイプを使った場合
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("エンテイ")],
        volatile0={"ハロウィン": 0},
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert "ゴースト" in attacker.types
    t.run_move(battle, 0)

    # エンテイ（ほのお）のタイプのみになること
    assert attacker.types == ["ほのお"]


def test_ミラータイプ_ステラテラスタル中は元のタイプをコピーする():
    """ミラータイプ: 相手がステラテラスタル中なら data.types をコピーする"""
    # ゲッコウガがステラテラスタルしている場合は元のタイプ（みず・あく）をコピー
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ", tera_type="ステラ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.terastallized = True
    assert defender.active_tera_type == "ステラ"
    t.run_move(battle, 0)

    # data.types をコピー（みず・あく）
    assert "みず" in attacker.types
    assert "あく" in attacker.types


def test_ミラータイプ_タイプが同じなら失敗する():
    """ミラータイプ: 使用者のタイプが対象のタイプと同じなら失敗する"""
    # ピカチュウ（でんき）→ ピカチュウ（でんき）なら失敗
    # ただし使用者はすでにミラータイプ後でないとタイプが同じにならないので
    # カビゴン（ノーマル）対カビゴン（ノーマル）で試す
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラータイプ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.types == ["ノーマル"]
    t.run_move(battle, 0)

    # 失敗するためタイプ変化なし
    assert attacker.types == ["ノーマル"]


def test_ミラータイプ_テラスタル中はテラタイプをコピーする():
    """ミラータイプ: 相手がテラスタル中（ステラ以外）ならテラタイプのみをコピーする"""
    # ゲッコウガ（みず・あく）がほのおテラスタルしている場合はほのおをコピー
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ", tera_type="ほのお")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.terastallized = True
    assert defender.active_tera_type == "ほのお"
    t.run_move(battle, 0)

    # テラタイプのみをコピー
    assert attacker.types == ["ほのお"]


def test_ミラータイプ_交代するとタイプがリセットされる():
    """ミラータイプ: 交代後にコピーされたタイプがリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"]), Pokemon("カビゴン")],
        team1=[Pokemon("ゲッコウガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.types == ["みず", "あく"]

    # 交代後はリセットされること
    t.run_switch(battle, 0, 1)
    # ピカチュウのタイプは元に戻る
    assert attacker.types == ["でんき"]


def test_ミラータイプ_相手のタイプをコピーする():
    """ミラータイプ: 使用後に attacker のタイプが defender のタイプと同じになること"""
    # ピカチュウ（でんき）→ ゲッコウガ（みず・あく）のタイプをコピー
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.types == ["でんき"]
    t.run_move(battle, 0)

    assert "みず" in attacker.types
    assert "あく" in attacker.types


@pytest.mark.parametrize(
    "spa_init,spd_init,spa_exp,spd_exp",
    [
        # 通常: C+1、D+1
        (0, 0, 1, 1),
        # とくこう上限: Cはキャップ、Dは+1
        (6, 0, 6, 1),
        # とくぼう上限: Dはキャップ、Cは+1
        (0, 6, 1, 6),
        # 両方上限: どちらも変化できないので失敗（変化なし）
        (6, 6, 6, 6),
        # 両方上限まで1段階: どちらも上限ぴったりになる
        (5, 5, 6, 6),
        # 最低ランクから上昇
        (-6, -6, -5, -5),
    ],
)
def test_めいそう_発動前後のランク変化(spa_init, spd_init, spa_exp, spd_exp):
    """めいそう: 発動前後のとくこう・とくぼうランクの変化を網羅的に確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["めいそう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["C"] = spa_init
    attacker.rank["D"] = spd_init
    t.run_move(battle, 0)

    assert attacker.rank["C"] == spa_exp
    assert attacker.rank["D"] == spd_exp


def test_メロメロ_すでにメロメロ状態なら失敗():
    """メロメロ: 相手がすでにメロメロ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="オス")],
        team1=[Pokemon("カビゴン", gender="メス")],
        volatile1={"メロメロ": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["メロメロ"].count
    t.run_move(battle, 0)

    assert defender.has_volatile("メロメロ")
    assert defender.volatiles["メロメロ"].count == old_count


@pytest.mark.parametrize("a_gender,d_gender,expected", [
    ("オス", "メス", True),   # 異性→成功
    ("メス", "オス", True),   # 異性→成功
    ("オス", "オス", False),  # 同性→失敗
    ("メス", "メス", False),  # 同性→失敗
    ("オス", "",    False),  # 相手が無性→失敗
    ("",    "メス", False),  # 使用者が無性→失敗
])
def test_メロメロ_性別の組み合わせ(a_gender, d_gender, expected):
    """メロメロ: 異性なら付与、同性・無性なら失敗"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender=a_gender)],
        team1=[Pokemon("カビゴン", gender=d_gender)],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("メロメロ") == expected


def test_もえあがるいかり_ひるみが発動する():
    """もえあがるいかり: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゾロアーク", move_names=["もえあがるいかり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_もりののろい_くさタイプが付与される():
    """もりののろい: 使用後に defender が「くさ」タイプになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.has_type("くさ")
    t.run_move(battle, 0)

    assert defender.has_type("くさ")


def test_もりののろい_すでにくさタイプなら失敗():
    """もりののろい: 相手がすでにくさタイプなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("フシギバナ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # くさタイプには付与されない
    assert not defender.has_volatile("もりののろい")


def test_もりののろい_もりののろい状態を付与する():
    """もりののろい: 相手にもりののろい状態を付与する（くさタイプが追加される）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("もりののろい")


def test_もりののろい_交代後にくさタイプがリセットされる():
    """もりののろい: 交代後に added_types がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドラン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_type("くさ")

    # 交代後はくさタイプが消えること
    t.run_switch(battle, 1, 1)
    assert not defender.has_type("くさ")
    assert not defender.has_volatile("もりののろい")
