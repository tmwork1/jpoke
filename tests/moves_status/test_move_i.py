"""変化技ハンドラの単体テスト（い行）。"""

from jpoke import Pokemon
from jpoke.enums import LogCode
from .. import test_utils as t


def test_いえき_protectedフラグ持ちに失敗():
    """いえき: アイスフェイス（protectedフラグ持ち）の相手には失敗してMOVE_FAILEDログが出る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[Pokemon("カビゴン", ability_name="アイスフェイス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("とくせいなし")
    logs = battle.event_logger.logs
    assert any(
        log.log == LogCode.MOVE_FAILED
        and log.payload is not None
        and log.payload.get("reason") == "いえき"
        for log in logs
    )


def test_いえき_すでにとくせいなし状態なら失敗():
    """いえき: 対象がすでに「とくせいなし」状態なら失敗する（volatile_manager 内部チェック）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"とくせいなし": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # すでに付与されているため「とくせいなし」は変化なし（count も変わらない）
    assert defender.volatiles["とくせいなし"].count == 1


def test_いえき_とくせいなし解除後に特性が復活():
    """いえき: 「とくせいなし」状態の相手が交代すると特性が復活する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[
            Pokemon("カビゴン", ability_name="めんえき"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert defender_before.has_volatile("とくせいなし")
    assert not defender_before.ability.enabled

    # 交代でとくせいなしが解除され特性が復活することを確認
    t.run_switch(battle, 1, 1)
    assert not defender_before.has_volatile("とくせいなし")
    assert defender_before.ability.enabled


def test_いえき_通常特性を持つ相手に成功():
    """いえき: 通常特性（せいでんき等）の相手に使うと「とくせいなし」揮発状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("とくせいなし")


def test_いとをはく_すでに最低ランクなら変化なし():
    """いとをはく: 相手のすばやさがすでに-6ならランク変化なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いとをはく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"S": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["S"] == -6


def test_いとをはく_すばやさ2段階下がる():
    """いとをはく: 相手のすばやさランクが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いとをはく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["S"] == -2


def test_いのちのしずく_HPが4分の1回復する():
    """いのちのしずく: HPが減っているとき最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_いのちのしずく_HP満タンなら失敗してMOVE_FAILEDログが出る():
    """いのちのしずく: HPが満タンのとき技が失敗し MOVE_FAILED ログが記録される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp
    logs = battle.event_logger.logs
    assert any(log.log == LogCode.MOVE_FAILED for log in logs)


def test_いのちのしずく_かいふくふうじ中は回復が無効化される():
    """いのちのしずく: かいふくふうじ状態のとき回復が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"かいふくふうじ": 3},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1


def test_いばる_こうげき2段階上がりこんらん付与():
    """いばる: 相手のこうげきが2段階上がり、こんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["A"] == 2
    assert defender.has_volatile("こんらん")


def test_いばる_こうげき最大でもこんらん未付与なら成功():
    """いばる: こうげきが+6でもこんらん状態でなければ技は成功しこんらんを付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"A": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["A"] == 6
    assert defender.has_volatile("こんらん")


def test_いばる_すでにこんらんかつこうげき最大なら失敗():
    """いばる: こうげきが+6かつこんらん済みなら技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    # こうげきを+6にする
    battle.modify_stats(defender, {"A": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    # こうげきは変化せず、こんらんも新たに付与されない
    assert defender.rank["A"] == 6
    assert defender.volatiles["こんらん"].count == 3  # カウント変わらず


def test_いやしのすず_どくを回復する():
    """いやしのすず: 使用者がどく状態のとき回復される"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_いやしのすず_まひを回復する():
    """いやしのすず: 使用者がまひ状態のとき回復される（でんきタイプ以外で確認）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("まひ", None),
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_いやしのすず_やけどを回復する():
    """いやしのすず: 使用者がやけど状態のとき回復される"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("やけど", None),
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_いやしのすず_状態異常なしなら失敗():
    """いやしのすず: チームに状態異常がいない場合は技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    assert not attacker.ailment.is_active
    t.run_move(battle, 0)

    # 状態異常なし → 技が失敗 → 状態に変化なし
    assert not attacker.ailment.is_active
    logs = battle.event_logger.logs
    assert any(log.log == LogCode.MOVE_FAILED for log in logs)


def test_いやしのねがい_使用者がひんしになりサイドフィールドが設置される():
    """いやしのねがい: 使用後に使用者がひんし状態になり、自陣営にサイドフィールドが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.fainted
    side = battle.get_side(attacker)
    assert side.get("いやしのねがい").is_active


def test_いやしのねがい_死に出しポケモンのHPが全回復される():
    """いやしのねがい: 死に出しのポケモンのHPが全回復される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    # battle 内部の PlayerState のチームからベンチポケモンを取得する
    bench = battle.player_states[battle.players[0]].team[1]
    bench.hp = 1
    battle.run_faint_switch()

    assert bench.hp == bench.max_hp
    side = battle.get_side(bench)
    assert not side.get("いやしのねがい").is_active


def test_いやしのねがい_死に出しポケモンの状態異常が回復される():
    """いやしのねがい: 死に出しのポケモンの状態異常（まひ）が回復される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
    )
    t.run_move(battle, 0)

    bench = battle.player_states[battle.players[0]].team[1]
    battle.ailment_manager.apply(bench, "まひ")
    assert bench.ailment.is_active
    battle.run_faint_switch()

    assert not bench.ailment.is_active


def test_いやしのはどう_HPが半分回復する():
    """いやしのはどう: HPが減っているとき最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_いやしのはどう_HP満タンなら失敗してMOVE_FAILEDログが出る():
    """いやしのはどう: HPが満タンのとき技が失敗し MOVE_FAILED ログが記録される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp
    logs = battle.event_logger.logs
    assert any(log.log == LogCode.MOVE_FAILED for log in logs)


def test_いやしのはどう_かいふくふうじ中は回復が無効化される():
    """いやしのはどう: かいふくふうじ状態のとき回復が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"かいふくふうじ": 3},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1
