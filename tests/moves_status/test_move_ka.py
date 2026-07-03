"""変化技ハンドラの単体テスト（か行）。"""

import pytest
from jpoke import Move, Pokemon
from .. import test_utils as t


def test_かいでんぱ_相手の特攻が2段階下がる():
    """かいでんぱ: 通常使用で相手の特攻ランクが-2になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かいでんぱ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spa"] == -2


def test_かいふくふうじ_使用で相手にかいふくふうじ状態が付与される():
    """かいふくふうじ: 技を使うと相手に「かいふくふうじ」揮発性状態が付与される（5ターン）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かいふくふうじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("かいふくふうじ")
    assert defender.volatiles["かいふくふうじ"].count == 5


def test_かいふくふうじ_状態中はHP回復技が無効になる():
    """かいふくふうじ: 状態中はじこさいせい等のHP回復技を使っても回復できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かいふくふうじ"])],
        team1=[Pokemon("カビゴン", move_names=["じこさいせい"])],
        accuracy=100,
    )
    attacker, defender = battle.actives
    # あらかじめHPを減らしておく
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp

    # かいふくふうじを付与する
    t.run_move(battle, 0)
    assert defender.has_volatile("かいふくふうじ")

    # かいふくふうじ状態でじこさいせいを使っても回復しない
    t.run_move(battle, 1)
    assert defender.hp == hp_before


def test_かえんのまもり_技使用でかえんのまもり状態が付与される():
    """かえんのまもり: 技を使うと自分にかえんのまもり揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かえんのまもり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("かえんのまもり")


def test_かげぶんしん_回避率1段階上がる():
    """かげぶんしん: 使用すると自分の回避率ランクが1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かげぶんしん"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["evasion"] == 1


def test_かなしばり_かなしばり中の技は使用できない():
    """かなしばり: かなしばりで封じられた技を使おうとすると行動がブロックされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かなしばり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    # defenderが事前に技を使ったことを示す
    t.run_move(battle, 1)
    # attacker が かなしばり を使い defender に volatile を付与する
    t.run_move(battle, 0)

    assert defender.has_volatile("かなしばり")
    # defender がかなしばりで封じられた技（たいあたり）を使おうとするとブロックされる
    t.run_move(battle, 1)
    assert not battle.move_executor.action_success


def test_かなしばり_すでにかなしばり中の相手には失敗する():
    """かなしばり: 相手がすでにかなしばり状態の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かなしばり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    # 1回目: 成功
    t.run_move(battle, 0)
    assert defender.has_volatile("かなしばり")
    old_count = defender.volatiles["かなしばり"].count

    # 2回目: すでにかなしばり状態なので失敗（count は変わらない）
    t.run_move(battle, 0)
    assert defender.volatiles["かなしばり"].count == old_count


def test_かなしばり_わるあがきを使った相手には失敗する():
    """かなしばり: 相手の直前使用技がわるあがきの場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かなしばり"])],
        team1=[Pokemon("カビゴン", move_names=["わるあがき"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    assert defender.executed_move.name == "わるあがき"

    t.run_move(battle, 0)
    assert not defender.has_volatile("かなしばり")


def test_かなしばり_成功してかなしばり揮発状態が付与される():
    """かなしばり: 相手が技を使った後に使うとかなしばり揮発状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かなしばり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    assert defender.executed_move.name == "たいあたり"

    t.run_move(battle, 0)
    assert defender.has_volatile("かなしばり")
    assert defender.volatiles["かなしばり"].count == 4


def test_かなしばり_未行動の相手には失敗する():
    """かなしばり: 相手がまだ技を使っていない（executed_move が None）場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かなしばり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.executed_move is None

    t.run_move(battle, 0)
    assert not defender.has_volatile("かなしばり")


def test_かみつく_ひるみが発動する():
    """かみつく: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", move_names=["かみつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_からをやぶる_Bが最低でも他のランクは上昇する():
    """からをやぶる: ぼうぎょがすでに-6でも他のランク変化は通常通り発生する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["からをやぶる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"def": -6}, source=attacker)
    t.run_move(battle, 0)

    assert attacker.rank["def"] == -6
    assert attacker.rank["atk"] == 2
    assert attacker.rank["spe"] == 2


def test_からをやぶる_BとDが下がりAとCとSが上がる():
    """からをやぶる: ぼうぎょ・とくぼうが1段階ずつ下がり、こうげき・とくこう・すばやさが2段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["からをやぶる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 2
    assert attacker.rank["def"] == -1
    assert attacker.rank["spa"] == 2
    assert attacker.rank["spd"] == -1
    assert attacker.rank["spe"] == 2


def test_ガードシェア_こうげきとくこうは変化しない():
    """ガードシェア: こうげき・とくこうの実数値は変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ガードシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    atk_a_before = attacker._stats_manager.stats[1]
    atk_c_before = attacker._stats_manager.stats[3]
    def_a_before = defender._stats_manager.stats[1]
    def_c_before = defender._stats_manager.stats[3]
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[1] == atk_a_before
    assert attacker._stats_manager.stats[3] == atk_c_before
    assert defender._stats_manager.stats[1] == def_a_before
    assert defender._stats_manager.stats[3] == def_c_before


@pytest.mark.parametrize("attacker_name, defender_name", [
    # B合計奇数（切り捨てあり）、D合計偶数（切り捨てなし）
    ("ピカチュウ", "カビゴン"),
    # B合計偶数、D合計奇数
    ("フシギダネ", "ヒトカゲ"),
    # B合計奇数、D合計奇数
    ("ゼニガメ", "コイル"),
    # B合計偶数、D合計偶数
    ("イーブイ", "ラプラス"),
])
def test_ガードシェア_ぼうぎょとくぼうが平均化される(attacker_name: str, defender_name: str):
    """ガードシェア: 使用者と相手のぼうぎょ・とくぼう実数値が平均値（切り捨て）になること"""
    battle = t.start_battle(
        team0=[Pokemon(attacker_name, move_names=["ガードシェア"])],
        team1=[Pokemon(defender_name)],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 使用前の平均値を計算（B=インデックス2、D=インデックス4）
    expected_b = (attacker._stats_manager.stats[2] + defender._stats_manager.stats[2]) // 2
    expected_d = (attacker._stats_manager.stats[4] + defender._stats_manager.stats[4]) // 2
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[2] == expected_b
    assert defender._stats_manager.stats[2] == expected_b
    assert attacker._stats_manager.stats[4] == expected_d
    assert defender._stats_manager.stats[4] == expected_d


def test_ガードシェア_ランク変化は変更されない():
    """ガードシェア: 実数値のみを平均化し、能力ランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ガードシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 0
    assert attacker.rank["spd"] == 0
    assert defender.rank["def"] == 0
    assert defender.rank["spd"] == 0


def test_ガードスワップ_ACランクは変化しない():
    """ガードスワップ: こうげき・とくこうのランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ガードスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["atk"] = 3
    attacker.rank["spa"] = 2
    defender.rank["atk"] = -1
    defender.rank["spa"] = -2
    t.run_move(battle, 0)

    # こうげき・とくこうは変化しない
    assert attacker.rank["atk"] == 3
    assert attacker.rank["spa"] == 2
    assert defender.rank["atk"] == -1
    assert defender.rank["spa"] == -2


def test_ガードスワップ_BDランクが双方で入れ替わる():
    """ガードスワップ: 使用者と相手のぼうぎょ・とくぼうランクが互いに入れ替わること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ガードスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 事前にランクを変更しておく
    attacker.rank["def"] = 2
    attacker.rank["spd"] = -1
    defender.rank["def"] = -3
    defender.rank["spd"] = 1
    t.run_move(battle, 0)

    # 入れ替わった後のランクを確認
    assert attacker.rank["def"] == -3
    assert attacker.rank["spd"] == 1
    assert defender.rank["def"] == 2
    assert defender.rank["spd"] == -1


def test_ガードスワップ_双方ともランク0のとき変化なし():
    """ガードスワップ: 双方のぼうぎょ・とくぼうランクがともに0の場合は入れ替え後も0のまま"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ガードスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 0
    assert attacker.rank["spd"] == 0
    assert defender.rank["def"] == 0
    assert defender.rank["spd"] == 0


def test_きあいだめ_きゅうしょアップ付与():
    """きあいだめ: 使用すると自分にきゅうしょアップ揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいだめ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("きゅうしょアップ")
    assert attacker.volatiles["きゅうしょアップ"].count == 2


def test_きあいだめ_すでにきゅうしょアップなら失敗():
    """きあいだめ: すでにきゅうしょアップ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいだめ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"きゅうしょアップ": 1},
    )
    attacker = battle.actives[0]
    old_count = attacker.volatiles["きゅうしょアップ"].count
    t.run_move(battle, 0)

    # カウントは変わらない（重複付与されない）
    assert attacker.volatiles["きゅうしょアップ"].count == old_count


def test_キノコのほうし_くさタイプには無効化される():
    """キノコのほうし: 草タイプのポケモンには無効化されてねむり状態にならない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.ailment.is_active


def test_キノコのほうし_相手がねむり状態になる():
    """キノコのほうし: 使用すると相手がねむり状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.ailment.name == "ねむり"


@pytest.mark.parametrize("terrain_name", [
    "エレキフィールド",
    "グラスフィールド",
])
def test_きりばらい_フィールドが解除される(terrain_name):
    """きりばらい: フィールドが展開されている場合に使用するとフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        terrain=(terrain_name, 5),
    )
    t.run_move(battle, 0)

    assert not battle.terrain.is_active


def test_きりばらい_使用者側の壁は解除されない():
    """きりばらい: 使用者側の壁系フィールドは解除されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side0={"ひかりのかべ": 5},
    )
    t.run_move(battle, 0)

    # 使用者側の壁は解除されない
    assert battle.side_managers[0].fields["ひかりのかべ"].is_active


@pytest.mark.parametrize("field_name", [
    "ステルスロック",
    "どくびし",
    "ねばねばネット",
    "まきびし",
])
def test_きりばらい_場の設置技が両陣営から除去される(field_name):
    """きりばらい: 両陣営に設置技が置かれていても両方除去される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side0={field_name: 1},
        side1={field_name: 1},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[0].fields[field_name].is_active
    assert not battle.side_managers[1].fields[field_name].is_active


def test_きりばらい_対象の回避率が1段階下がる():
    """きりばらい: 使用すると対象の回避率ランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["evasion"] == -1


@pytest.mark.parametrize("wall_name", [
    "オーロラベール",
    "ひかりのかべ",
    "リフレクター",
])
def test_きりばらい_対象側の壁が解除される(wall_name):
    """きりばらい: 対象側の壁系フィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side1={wall_name: 5},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[1].fields[wall_name].is_active


def test_くすぐる_こうげきが最低でもぼうぎょは下がる():
    """くすぐる: こうげきランクがすでに-6でも、ぼうぎょランクは-1下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くすぐる"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"atk": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -6
    assert defender.rank["def"] == -1


def test_くすぐる_こうげきとぼうぎょ1段階ずつ下がる():
    """くすぐる: 相手のこうげきとぼうぎょランクが1段階ずつ下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くすぐる"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1
    assert defender.rank["def"] == -1


def test_くろいきり_使用者のランクがゼロにリセットされる():
    """くろいきり: 使用者自身のランク変化がすべて 0 にリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くろいきり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    # 事前にランクを変化させておく
    attacker.rank["atk"] = 3
    attacker.rank["def"] = -2
    attacker.rank["spe"] = 1
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 0
    assert attacker.rank["def"] == 0
    assert attacker.rank["spe"] == 0


def test_くろいきり_双方のランクが同時にリセットされる():
    """くろいきり: 使用者と相手の双方のランク変化が同時に 0 にリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くろいきり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["atk"] = 2
    attacker.rank["spe"] = -1
    defender.rank["def"] = -2
    defender.rank["accuracy"] = 1
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 0
    assert attacker.rank["spe"] == 0
    assert defender.rank["def"] == 0
    assert defender.rank["accuracy"] == 0


def test_くろいまなざし_すでににげられない状態なら失敗():
    """くろいまなざし: 相手がすでににげられない状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くろいまなざし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"にげられない": 1},
    )
    defender = battle.actives[1]
    # カウントが変わらないことで重複付与されないことを確認
    old_count = defender.volatiles["にげられない"].count
    t.run_move(battle, 0)

    assert defender.has_volatile("にげられない")
    assert defender.volatiles["にげられない"].count == old_count


def test_くろいまなざし_にげられない状態を付与する():
    """くろいまなざし: 相手をにげられない状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くろいまなざし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("にげられない")


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


def test_こおりのキバ_ひるみが発動する():
    """こおりのキバ: 10%でこおりかひるみのどちらかを付与する。乱数が0.5以上のときひるみが選択される。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", move_names=["こおりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.fix_random(battle, 0.9)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize(
    "def_init,spd_init,def_exp,spd_exp",
    [
        # 通常: B+1、D+1
        (0, 0, 1, 1),
        # ぼうぎょ上限: Bはキャップ、Dは+1
        (6, 0, 6, 1),
        # とくぼう上限: Dはキャップ、Bは+1
        (0, 6, 1, 6),
        # 両方上限: どちらも変化できないので失敗（変化なし）
        (6, 6, 6, 6),
        # 両方上限まで1段階: どちらも上限ぴったりになる
        (5, 5, 6, 6),
        # 最低ランクから上昇
        (-6, -6, -5, -5),
    ],
)
def test_コスモパワー_発動前後のランク変化(def_init, spd_init, def_exp, spd_exp):
    """コスモパワー: 発動前後のぼうぎょ・とくぼうランクの変化を網羅的に確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["コスモパワー"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["def"] = def_init
    attacker.rank["spd"] = spd_init
    t.run_move(battle, 0)

    assert attacker.rank["def"] == def_exp
    assert attacker.rank["spd"] == spd_exp


def test_こらえる_HP1のとき致死ダメージでHP1残る():
    """こらえる: HP が 1 のとき致死ダメージを受けても HP 1 が残る"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["こらえる"])],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)

    t.run_move(battle, 0)

    assert defender.hp == 1
    assert not defender.fainted


def test_こらえる_こらえる揮発状態が付与される():
    """こらえる: 使用すると自分にこらえる揮発状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こらえる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("こらえる")


def test_こらえる_すでにこらえる状態なら失敗():
    """こらえる: すでにこらえる状態なら失敗する（重複付与されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こらえる"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"こらえる": 1},
    )
    attacker = battle.actives[0]
    # すでに付与済みなので失敗するはず
    t.run_move(battle, 0)

    # カウントは変わらない（重複付与されない）
    assert attacker.has_volatile("こらえる")
    assert attacker.volatiles["こらえる"].count == 1


def test_こらえる_ターン経過ダメージには適用されない():
    """こらえる: やけどなどのターン経過ダメージはこらえるで防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こらえる"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("やけど", None),
        volatile0={"こらえる": 1},
    )
    mon = battle.actives[0]
    mon.hp = 1

    # HP=1 でやけどダメージを受けるとひんしになる（こらえるは適用されない）
    t.end_turn(battle)

    assert mon.fainted


def test_こらえる_致死ダメージを受けてもHP1残る():
    """こらえる: こらえる状態のときに致死ダメージを受けてもHP 1 が残る"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["こらえる"])],
        accuracy=100,
    )
    attacker, defender = battle.actives
    # defender にこらえる状態を付与
    battle.volatile_manager.apply(defender, "こらえる")
    # 致死ダメージを設定
    t.fix_damage(battle, defender.max_hp)

    t.run_move(battle, 0)

    assert defender.hp == 1
    assert not defender.fainted


def test_ゴッドバード_ひるみが発動する():
    """ゴッドバード: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイアロー", move_names=["ゴッドバード"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")
