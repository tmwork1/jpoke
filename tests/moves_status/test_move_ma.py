"""変化技ハンドラの単体テスト（ま行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_まきびし_すでに設置済みなら失敗():
    # TODO : まきびしはcount=3まで累積できる。countをパラメタライズでまとめてテストする。
    """まきびし: すでにまきびしが設置済みなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
        team1=[Pokemon("カビゴン")],
        side1={"まきびし": 1},
    )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["まきびし"].is_active
    assert side.fields["まきびし"].count == 1


def test_まきびし_相手陣営に設置される():
    """まきびし: 使用すると相手陣営にまきびしが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[1])
    assert side.fields["まきびし"].is_active


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
    # TODO : 初代ポケモンのギャラドスで検証する
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


def test_ミラータイプ_コピー後addedTypesがリセットされる():
    # TODO : added_typesは内部実装なのでテストで確認すべきではない。他のテストにも該当箇所があれば修正する。
    """ミラータイプ: タイプコピー後に attacker の added_types がリセットされること"""
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

    # コピー後は added_types がリセットされること
    assert attacker.added_types == []
    # エンテイ（ほのお）のタイプをコピー
    assert attacker.types == ["ほのお"]


def test_ミラータイプ_ステラテラスタル中は元のタイプをコピーする():
    # TODO : override_type は内部実装なのでテストで確認すべきではない。他のテストにも該当箇所があれば修正する。
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
    assert attacker.move_override_types == list(defender.data.types)


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
    assert attacker.move_override_types is None
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
    assert attacker.move_override_types == ["ほのお"]


def test_ミラータイプ_交代するとタイプがリセットされる():
    """ミラータイプ: 交代後に move_override_types がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"]), Pokemon("カビゴン")],
        team1=[Pokemon("ゲッコウガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.move_override_types == ["みず", "あく"]

    # 交代後はリセットされること
    t.run_switch(battle, 0, 1)
    assert attacker.move_override_types is None
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
    assert attacker.move_override_types == ["みず", "あく"]


def test_めいそう_とくこうととくぼう1段階ずつ上がる():
    # TODO : 発動前後の状態の組み合わせをパラメタライズしてまとめてテストする
    """めいそう: 使用すると自分のとくこうとぼうぎょランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["めいそう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["C"] == 0
    assert attacker.rank["D"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["C"] == 1
    assert attacker.rank["D"] == 1


def test_めいそう_とくこう最大でもとくぼうは上昇する():
    """めいそう: とくこうがすでに+6でも、とくぼうは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["めいそう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["C"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["C"] == 6
    assert attacker.rank["D"] == 1


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


def test_メロメロ_異なる性別なら付与される():
    # TODO : とりうる性別の組み合わせをパラメタライズしてまとめてテストする
    """メロメロ: 自分と異なる性別の相手をメロメロ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="オス")],
        team1=[Pokemon("カビゴン", gender="メス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("メロメロ")


def test_もりののろい_くさタイプが付与される():
    # TODO : これは揮発状態の仕様なので技側でテストすべきではない
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
    # TODO : これは揮発状態の仕様なので技側でテストすべきではない
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
