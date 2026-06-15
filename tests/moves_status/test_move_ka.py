"""変化技ハンドラの単体テスト（か行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_かいでんぱ_命中率100で当たる():
    """かいでんぱ: 命中率100%で相手に当たること（技の命中チェックを通ること）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かいでんぱ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 命中率100%のため確実にランク変化が発生する
    assert defender.rank["C"] == -2


def test_かいでんぱ_相手の特攻が2段階下がる():
    """かいでんぱ: 通常使用で相手の特攻ランクが-2になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かいでんぱ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["C"] == -2


def test_かいでんぱ_相手の特攻がすでにマイナス6なら変化なし():
    """かいでんぱ: 相手の特攻ランクがすでに-6の場合はランク変化が発生しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かいでんぱ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # 事前に特攻を-6まで下げる
    battle.modify_stats(defender, {"C": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["C"] == -6


def test_かげぶんしん_回避率1段階上がる():
    """かげぶんしん: 使用すると自分の回避率ランクが1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かげぶんしん"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["EVA"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["EVA"] == 1


def test_かげぶんしん_回避率最大なら変化なし():
    """かげぶんしん: 回避率がすでに+6なら効果がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かげぶんしん"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["EVA"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["EVA"] == 6


def test_からをやぶる_Bが最低でも他のランクは上昇する():
    """からをやぶる: ぼうぎょがすでに-6でも他のランク変化は通常通り発生する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["からをやぶる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"B": -6}, source=attacker)
    t.run_move(battle, 0)

    assert attacker.rank["B"] == -6
    assert attacker.rank["A"] == 2
    assert attacker.rank["S"] == 2


def test_からをやぶる_BとDが下がりAとCとSが上がる():
    """からをやぶる: ぼうぎょ・とくぼうが1段階ずつ下がり、こうげき・とくこう・すばやさが2段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["からをやぶる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 2
    assert attacker.rank["B"] == -1
    assert attacker.rank["C"] == 2
    assert attacker.rank["D"] == -1
    assert attacker.rank["S"] == 2


def test_きあいだめ_きゅうしょアップ付与():
    """きあいだめ: 使用すると自分にきゅうしょアップ揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいだめ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("きゅうしょアップ")


def test_きあいだめ_すでにきゅうしょアップなら失敗():
    """きあいだめ: すでにきゅうしょアップ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいだめ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"きゅうしょアップ": 1},
    )
    attacker = battle.actives[0]
    # 1回目は失敗するはず
    t.run_move(battle, 0)

    # 付与済み状態は継続
    assert attacker.has_volatile("きゅうしょアップ")


def test_くすぐる_こうげきとぼうぎょ1段階ずつ下がる():
    """くすぐる: 相手のこうげきとぼうぎょランクが1段階ずつ下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くすぐる"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["A"] == -1
    assert defender.rank["B"] == -1


def test_くすぐる_すでに最低ランクなら変化なし():
    """くすぐる: こうげき・ぼうぎょがともにすでに-6ならランク変化なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くすぐる"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"A": -6, "B": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["A"] == -6
    assert defender.rank["B"] == -6


def test_グラスフィールド_すでに同じフィールドなら失敗():
    """グラスフィールド: すでにグラスフィールド中は発動しない（失敗）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["グラスフィールド"])],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
    )
    t.run_move(battle, 0)

    # カウントは変わらない（再発動されない）
    assert battle.terrain.name == "グラスフィールド"
    assert battle.terrain.count == 5


def test_グラスフィールド_フィールドが5ターン展開される():
    """グラスフィールド: 使用すると5ターンのグラスフィールドが展開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["グラスフィールド"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.terrain.name == "グラスフィールド"
    assert battle.terrain.count == 5


def test_こうごうせい_あめで4分の1回復():
    """こうごうせい: あめ中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうごうせい"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_こうごうせい_はれで3分の2回復():
    """こうごうせい: はれ中は最大HPの2/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうごうせい"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 2 / 3)


def test_こうごうせい_まんたんなら失敗():
    """こうごうせい: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうごうせい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp


def test_こうごうせい_通常天候で2分の1回復():
    """こうごうせい: 通常天候では最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうごうせい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_コスモパワー_ぼうぎょととくぼう1段階ずつ上がる():
    """コスモパワー: 使用すると自分のぼうぎょととくぼうランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["コスモパワー"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["B"] == 0
    assert attacker.rank["D"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 1
    assert attacker.rank["D"] == 1


def test_コスモパワー_ぼうぎょ最大でもとくぼうは上昇する():
    """コスモパワー: ぼうぎょがすでに+6でも、とくぼうは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["コスモパワー"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["B"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 6
    assert attacker.rank["D"] == 1
