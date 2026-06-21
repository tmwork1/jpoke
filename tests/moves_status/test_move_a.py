"""変化技ハンドラの単体テスト（あ行）。"""

from jpoke import Pokemon
from jpoke.enums import LogCode
from .. import test_utils as t

# TODO : いやしのねがい：HP満タンのポケモンでも状態異常だけ回復するテストを追加
# TODO : いやしのねがい：HP満タンで状態異常なしのポケモンに対しては発動しないテストを追加

# TODO : おだてる：とくこうが+6でもこんらん未付与なら成功するテストを追加


def test_アクアリング_すでに付与済みなら失敗する():
    # TODO : 同一Volatileの重複付与は失敗する仕様のためテスト不要。他も同様
    """アクアリング: すでにアクアリング状態なら効果を上書きしない（失敗扱い）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アクアリング"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"アクアリング": 1},
    )
    attacker = battle.actives[0]
    result = t.run_move(battle, 0)

    # 状態は維持されたまま（重複付与されない）
    assert attacker.has_volatile("アクアリング")


def test_アクアリング_揮発性状態が付与される():
    """アクアリング: 使用するとアクアリング揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アクアリング"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("アクアリング")


def test_あくび_すでにねむけ状態なら失敗():
    """あくび: 対象がすでにねむけ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"ねむけ": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    # ねむけは継続したまま（2つ目のねむけは付かない）
    assert defender.has_volatile("ねむけ")


def test_あくび_すでに状態異常なら失敗():
    """あくび: 対象がすでに状態異常を持っているなら失敗する。
    状態異常による揮発状態のブロックなので追加検証している。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert not defender.has_volatile("ねむけ")
    assert defender.has_ailment("まひ")


def test_あくび_ねむけ付与():
    """あくび: 相手をねむけ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_volatile("ねむけ")
    assert defender.volatiles["ねむけ"].count == 2
    assert not defender.has_ailment("ねむり")


def test_あくまのキッス_すでに状態異常なら失敗():
    # TODO : Ailmentの重複付与は失敗する仕様のため、強制上書きする効果以外はテスト不要。他も同様
    """あくまのキッス: 対象がすでに状態異常を持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくまのキッス"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_ailment("まひ")
    assert not defender.has_ailment("ねむり")


def test_あくまのキッス_ねむり付与():
    """あくまのキッス: 相手をねむり状態に直接する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくまのキッス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")


def test_あさのひざし_あめで4分の1回復():
    # TODO : 天候による効果変動はパラメタライズでまとめる
    """あさのひざし: あめ中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_あさのひざし_おおあめで4分の1回復():
    """あさのひざし: おおあめ中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおあめ", 99),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_あさのひざし_おおひでりで3分の2回復():
    """あさのひざし: おおひでり中は最大HPの2/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 2 / 3)


def test_あさのひざし_すなあらしで4分の1回復():
    """あさのひざし: すなあらし中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("すなあらし", 99),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_あさのひざし_はれで3分の2回復():
    """あさのひざし: はれ中は最大HPの2/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 2 / 3)


def test_あさのひざし_まんたんなら失敗():
    """あさのひざし: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_あさのひざし_ゆきで4分の1回復():
    """あさのひざし: ゆき中は最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        weather=("ゆき", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_あさのひざし_通常天候で2分の1回復():
    """あさのひざし: 通常天候では最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_あまえる_attacker_のこうげきは変化しない():
    # TODO : 効果対象の検証までは冗長なので不要
    """あまえる: 使用者（attacker）のこうげきは変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまえる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["A"] == 0


def test_あまえる_defenderのこうげきが2段階下がる():
    """あまえる: 相手（defender）のこうげきが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまえる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["A"] == -2


def test_あまえる_すでに最低ランクなら変化なし():
    """あまえる: 相手のこうげきランクがすでに-6なら変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまえる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["A"] = -6
    t.run_move(battle, 0)
    assert defender.rank["A"] == -6


def test_あまごい_おおひでり中は失敗する():
    """あまごい: おおひでり中は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "おおひでり"


def test_あまごい_天気があめになる():
    """あまごい: 使用後に天気があめになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "あめ"
    assert battle.weather.count == 5


def test_あやしいひかり_こんらん付与():
    # TODO : こんらんのカウント数は検証不要。他ハンドラも同様。
    """あやしいひかり: 相手をこんらん状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あやしいひかり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.random.randint = lambda a, b: 3
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")
    assert defender.volatiles["こんらん"].count == 3


def test_いえき_protectedフラグ持ちに失敗():
    """いえき: アイスフェイス（protectedフラグ持ち）の相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[Pokemon("カビゴン", ability_name="アイスフェイス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("とくせいなし")


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
    # TODO : 能力ランクのクリップはシステム仕様であり、個別技のテストで検証する必要はない。他も同様。
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
    # TODO : 技が不発になるため、開示されるがPPが消費されないことも検証する。
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
    # TODO : HP回復テストと統合する。
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
    """いやしのはどう: 相手のHPが減っているとき相手の最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.hp == 1 + int(defender.max_hp * 1 / 2)


def test_いやしのはどう_HP満タンなら失敗してMOVE_FAILEDログが出る():
    """いやしのはどう: 相手のHPが満タンのとき技が失敗し MOVE_FAILED ログが記録される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    assert defender.hp == defender.max_hp
    t.run_move(battle, 0)

    assert defender.hp == defender.max_hp
    logs = battle.event_logger.logs
    assert any(log.log == LogCode.MOVE_FAILED for log in logs)


def test_いやしのはどう_かいふくふうじ中は回復が無効化される():
    """いやしのはどう: かいふくふうじ状態の相手には回復が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"かいふくふうじ": 3},
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.hp == 1


def test_うたう_ねむり付与():
    """うたう: 相手をねむり状態にする（accuracy=100で固定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")


def test_エレキフィールド_すでに同じフィールドなら失敗():
    # TODO : フィールド展開技のテストはtest_move__grouped.pyにまとめる。
    """エレキフィールド: すでにエレキフィールド中は発動しない（失敗）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキフィールド"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
    )
    t.run_move(battle, 0)

    # カウントは変わらない（再発動されない）
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5


def test_エレキフィールド_フィールドが5ターン展開される():
    """エレキフィールド: 使用すると5ターンのエレキフィールドが展開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキフィールド"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5


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


def test_おかたづけ_みがわりを除去する():
    """おかたづけ: 相手のみがわりを除去する"""
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
        log.log == LogCode.VOLATILE_REMOVED
        and log.payload is not None
        and log.payload.get("volatile") == "みがわり"
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
        volatile1={"まもる": 1}
    )
    attacker, defender = battle.actives
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
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.fainted
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


def test_おにび_すでに状態異常なら失敗():
    """おにび: 対象がすでに状態異常を持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # まひのまま変わっていないことを確認
    assert battle.actives[1].ailment.name == "まひ"


def test_おにび_ほのおタイプには無効():
    # TODO : タイプ無効テストはailmentの仕様なのでailmentのテストで検証する。他の技でも同様。
    """おにび: ほのおタイプの相手には無効（単タイプ）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("ヒトカゲ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_おにび_やけど付与():
    """おにび: 相手をやけど状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_オーロラベール_ゆき中なら自陣営に設置される():
    """オーロラベール: ゆき天候中に使用すると自陣営に5ターンのオーロラベールが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["オーロラベール"])],
        team1=[Pokemon("カビゴン")],
        weather=("ゆき", 5),
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["オーロラベール"].is_active
    assert side.fields["オーロラベール"].count == 5


def test_オーロラベール_ゆき以外では失敗():
    """オーロラベール: ゆき天候でない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["オーロラベール"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert not side.fields["オーロラベール"].is_active
