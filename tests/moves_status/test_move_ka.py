"""変化技ハンドラの単体テスト（か行）。"""

from jpoke import Move, Pokemon
from jpoke.enums import LogCode
from .. import test_utils as t

# TODO : キノコのほうしは草タイプに無効化されることを検証する。

# TODO : くすぐるで攻撃が最低ランクでも防御が下がることを検証する


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

    assert attacker.rank["EVA"] == 1


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

    assert attacker.rank["B"] == 0
    assert attacker.rank["D"] == 0
    assert defender.rank["B"] == 0
    assert defender.rank["D"] == 0


def test_ガードシェア_使用者と相手のとくぼうが平均化される():
    """ガードシェア: 使用者と相手のとくぼう実数値が平均値（切り捨て）になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ガードシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # ピカチュウD=70、カビゴンD=130 → 平均 (70+130)//2 = 100
    expected_d = (attacker._stats_manager.stats[4] + defender._stats_manager.stats[4]) // 2
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[4] == expected_d
    assert defender._stats_manager.stats[4] == expected_d


def test_ガードシェア_使用者と相手のぼうぎょが平均化される():
    """ガードシェア: 使用者と相手のぼうぎょ実数値が平均値（切り捨て）になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ガードシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # ピカチュウB=60、カビゴンB=85 → 平均 (60+85)//2 = 72
    expected_b = (attacker._stats_manager.stats[2] + defender._stats_manager.stats[2]) // 2
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[2] == expected_b
    assert defender._stats_manager.stats[2] == expected_b


def test_ガードスワップ_ACランクは変化しない():
    """ガードスワップ: こうげき・とくこうのランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ガードスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["A"] = 3
    attacker.rank["C"] = 2
    defender.rank["A"] = -1
    defender.rank["C"] = -2
    t.run_move(battle, 0)

    # こうげき・とくこうは変化しない
    assert attacker.rank["A"] == 3
    assert attacker.rank["C"] == 2
    assert defender.rank["A"] == -1
    assert defender.rank["C"] == -2


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
    attacker.rank["B"] = 2
    attacker.rank["D"] = -1
    defender.rank["B"] = -3
    defender.rank["D"] = 1
    t.run_move(battle, 0)

    # 入れ替わった後のランクを確認
    assert attacker.rank["B"] == -3
    assert attacker.rank["D"] == 1
    assert defender.rank["B"] == 2
    assert defender.rank["D"] == -1


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

    assert attacker.rank["B"] == 0
    assert attacker.rank["D"] == 0
    assert defender.rank["B"] == 0
    assert defender.rank["D"] == 0


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
    """きあいだめ: すでにきゅうしょアップ状態なら失敗し MOVE_FAILED ログが記録される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいだめ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"きゅうしょアップ": 1},
    )
    t.run_move(battle, 0)

    logs = battle.event_logger.logs
    assert any(log.log == LogCode.MOVE_FAILED for log in logs)


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


def test_きりばらい_エレキフィールドが解除される():
    """きりばらい: エレキフィールドが展開されている場合に使用するとフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
    )
    t.run_move(battle, 0)

    assert not battle.terrain.is_active


def test_きりばらい_グラスフィールドが解除される():
    """きりばらい: グラスフィールドが展開されている場合に使用するとフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
    )
    t.run_move(battle, 0)

    assert not battle.terrain.is_active


def test_きりばらい_ステルスロックが両陣営から除去される():
    """きりばらい: 両陣営にステルスロックが設置されていても両方除去される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side0={"ステルスロック": 1},
        side1={"ステルスロック": 1},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[0].fields["ステルスロック"].is_active
    assert not battle.side_managers[1].fields["ステルスロック"].is_active


def test_きりばらい_どくびしが両陣営から除去される():
    """きりばらい: 両陣営にどくびしが設置されていても両方除去される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side0={"どくびし": 1},
        side1={"どくびし": 1},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[0].fields["どくびし"].is_active
    assert not battle.side_managers[1].fields["どくびし"].is_active


def test_きりばらい_ねばねばネットが両陣営から除去される():
    """きりばらい: 両陣営にねばねばネットが設置されていても両方除去される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side0={"ねばねばネット": 1},
        side1={"ねばねばネット": 1},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[0].fields["ねばねばネット"].is_active
    assert not battle.side_managers[1].fields["ねばねばネット"].is_active


def test_きりばらい_まきびしが両陣営から除去される():
    """きりばらい: 両陣営にまきびしが設置されていても両方除去される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side0={"まきびし": 1},
        side1={"まきびし": 1},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[0].fields["まきびし"].is_active
    assert not battle.side_managers[1].fields["まきびし"].is_active


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


def test_きりばらい_対象の回避率が1段階下がる():
    """きりばらい: 使用すると対象の回避率ランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["EVA"] == -1


def test_きりばらい_対象側のオーロラベールが解除される():
    """きりばらい: 対象側のオーロラベールが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side1={"オーロラベール": 5},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[1].fields["オーロラベール"].is_active


def test_きりばらい_対象側のひかりのかべが解除される():
    """きりばらい: 対象側のひかりのかべが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side1={"ひかりのかべ": 5},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[1].fields["ひかりのかべ"].is_active


def test_きりばらい_対象側のリフレクターが解除される():
    """きりばらい: 対象側のリフレクターが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きりばらい"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 5},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[1].fields["リフレクター"].is_active


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
    # TODO : 技が失敗することを検証する
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


def test_くろいきり_使用者のランクがゼロにリセットされる():
    """くろいきり: 使用者自身のランク変化がすべて 0 にリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くろいきり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    # 事前にランクを変化させておく
    attacker.rank["A"] = 3
    attacker.rank["B"] = -2
    attacker.rank["S"] = 1
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 0
    assert attacker.rank["B"] == 0
    assert attacker.rank["S"] == 0


def test_くろいきり_双方のランクが同時にリセットされる():
    """くろいきり: 使用者と相手の双方のランク変化が同時に 0 にリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くろいきり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["A"] = 2
    attacker.rank["S"] = -1
    defender.rank["B"] = -2
    defender.rank["ACC"] = 1
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 0
    assert attacker.rank["S"] == 0
    assert defender.rank["B"] == 0
    assert defender.rank["ACC"] == 0


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

    assert attacker.rank["D"] == 1


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


def test_こらえる_ターン終了後にvolatileが解除される():
    # TODO : これはvolatile側でテストすべき
    """こらえる: ターン終了後にこらえる揮発状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こらえる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("こらえる")

    t.end_turn(battle)

    assert not attacker.has_volatile("こらえる")


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
