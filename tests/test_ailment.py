"""状態異常ハンドラの単体テスト"""
import pytest

from jpoke.model import Pokemon
from jpoke.types import AilmentName

from . import test_utils as t


def test_faint_HPが0になる():
    """battle.faint(): 対象のHPが0になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.faint(mon)

    assert mon.hp == 0


def test_faint_faintedがTrueになる():
    """battle.faint(): 対象がひんし状態（fainted=True）になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.faint(mon)

    assert mon.fainted


def test_modify_hp_r正_最低1回復():
    """battle.modify_hp(r=1/16): max_hpが小さくint変換でゼロになっても最低1HP回復する"""
    battle = t.start_battle(
        team0=[Pokemon("コイキング")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    # max_hp=8 にすると int(8 * (1/16)) == 0 になる
    mon._stats[0] = 8
    mon.hp = 2
    result = battle.modify_hp(mon, r=1/16)
    assert result == 1, f"最低1HP回復のはずだが {result} だった"
    assert mon.hp == 3


def test_modify_hp_r負_最低1ダメージ():
    """battle.modify_hp(r=-1/16): max_hpが小さくint変換でゼロになっても最低1ダメージになる"""
    battle = t.start_battle(
        team0=[Pokemon("コイキング")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    # max_hp=8 にすると int(8 * (-1/16)) == 0 になる
    mon._stats[0] = 8
    mon.hp = 8
    result = battle.modify_hp(mon, r=-1/16)
    assert result == -1, f"最低1ダメージのはずだが {result} だった"
    assert mon.hp == 7


def test_set_ailment_既存の状態異常を上書きできる():
    """battle.set_ailment(): 既存の状態異常があっても上書きして付与できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
    )
    mon = battle.actives[1]
    assert mon.ailment.name == "まひ"

    result = battle.set_ailment(mon, "やけど")

    assert result
    assert mon.ailment.name == "やけど"


def test_set_ailment_状態異常を付与できる():
    """battle.set_ailment(): 対象に状態異常を直接付与できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[1]

    result = battle.set_ailment(mon, "どく")

    assert result
    assert mon.ailment.name == "どく"


def test_こおり_3回目行動時に強制解凍():
    """こおり: Champions仕様 - 行動不能2回の後（3回目の行動時）は必ず解凍する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "こおり")
    # 解凍しない設定で2回行動不能にする
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert mon.ailment.elapsed_turns == 1

    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert mon.ailment.elapsed_turns == 2

    # 3回目の行動時はtrigger_ailmentに関係なく必ず解凍される
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert not mon.ailment.is_active


def test_こおり_self_thaw技はこんらんの自傷判定より後に解凍される():
    """こおり: self_thawフラグを持つ技（ハイドロスチーム等）は、こんらんの自傷判定
    （Event.ON_TRY_ACTION priority=110）より後のpriority=170で解凍される。

    Champions仕様（第五世代以降）では状態変化の判定の後にこおりが治るため、
    こんらんの自傷で技が実行されなかった場合はこおりが解凍されない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ハイドロスチーム"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.ailment_manager.apply(attacker, "こおり")
    assert attacker.ailment.name == "こおり"
    # こんらんの自傷を強制
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    # こんらんの自傷で技が実行されなかったため、こおりは解凍されない
    assert attacker.ailment.name == "こおり"


def test_こおり_thaw技被弾で解凍する():
    """thawラベルを持つ技（ねっとう等）で被弾すると解凍する。

    ねっとうは30%でやけどを付与するため、secondary_chance=0.0 で副作用を無効化して
    こおりの解凍のみをテストする。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねっとう"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=0.0,
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_こおり_ほのおタイプの技全般で被弾すると解凍する():
    """こおり: 「thaw」フラグを持たないほのおタイプの攻撃技でも被弾すると解凍する。

    ほのおタイプの攻撃技（第三世代以降）はタイプ由来で全て解凍対象となるため、
    個別に「thaw」フラグが付与されていない技（オーバーヒート等）でも解凍されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["オーバーヒート"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_こおり_行動不能():
    """こおり: 状態維持（確率テスト - trigger_rate=0.0）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "こおり")
    # 解凍されない設定でテスト
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert mon.ailment.name == "こおり"


def test_こおり_行動成功():
    """こおり: 解凍（確率テスト - trigger_rate=1.0）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "こおり")
    # 必ず解凍される設定でテスト
    battle.test_option.trigger_ailment = True
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert not mon.ailment.is_active


@pytest.mark.parametrize(
    "target_name, ailment_name",
    [
        ("フシギダネ", "どく"),
        ("コイル", "もうどく"),
        ("ピカチュウ", "まひ"),
        ("ヒトカゲ", "やけど"),
        ("ラプラス", "こおり"),
    ],
)
def test_タイプ一致の状態異常は入らない(target_name: str, ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon(target_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    assert not battle.ailment_manager.apply(target, ailment_name)


def test_どく_ダメージ():
    """どく: ターン終了時ダメージ"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    t.end_turn(battle)
    assert mon.hp == mon.max_hp - mon.max_hp // 8, "Poison damage is incorrect"


def test_ねむり_いびきは行動できる():
    """ねむり: いびきを選択していれば行動不能にならない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いびき"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=3)

    # いびきはねむり中でも使える
    t.run_move(battle, 0)
    assert battle.move_executor.action_success


def test_ねむり_カウント():
    """ねむり: count=2 のとき2ターン目で回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ニャース")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=2)

    # 1ターン目: count 2 → 1
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.ailment.name == "ねむり"
    assert attacker.ailment.count == 1

    # 2ターン目: count 1 → 0 で回復
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert not attacker.ailment.is_active


def test_ねむり_カウント3_3ターン目で回復():
    """ねむり: count=3 のとき3ターン目で回復する（ねむる技 Champions 仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ニャース")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=3)

    # 1ターン目: count 3 → 2、行動不能
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.ailment.count == 2

    # 2ターン目: count 2 → 1、行動不能
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.ailment.count == 1

    # 3ターン目: count 1 → 0 で回復、行動成功
    t.run_move(battle, 0)
    assert battle.move_executor.action_success
    assert not attacker.ailment.is_active


def test_ねむり_こんらん状態では眠りカウントが消費されない():
    """ねむり: いびき・ねごと以外を選んでいる間、こんらん状態なら眠りカウントも消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ニャース")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=2)
    battle.volatile_manager.apply(attacker, "こんらん", count=5)
    battle.test_option.trigger_volatile = True  # こんらんの自傷判定が発生しないことも確認する

    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.ailment.count == 2, "こんらん状態のときは眠りカウントが消費されないはず"
    assert attacker.hp == attacker.max_hp, "こんらん状態でもねむり中は自傷しないはず"


def test_ねむり_こんらん状態でもいびきを選べば眠りカウントが消費されこんらんも判定される():
    """ねむり: いびき・ねごとを選んだ場合は眠りカウントが消費され、こんらんの自傷判定も行われる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いびき"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=3)
    battle.volatile_manager.apply(attacker, "こんらん", count=5)
    battle.test_option.trigger_volatile = True  # こんらんで必ず自傷させる

    t.run_move(battle, 0)
    assert not battle.move_executor.action_success, "こんらんの自傷で行動が中断されるはず"
    assert attacker.ailment.count == 2, "いびきを選んだ場合は眠りカウントが消費されるはず"
    assert attacker.hp < attacker.max_hp, "いびきを選んだ場合はこんらんの自傷判定が行われるはず"


def test_ねむり_はやおきはこんらん状態のとき追加消費しない():
    """ねむり: はやおき特性でもこんらん状態のときはねむりカウントの追加消費が行われない"""
    battle = t.start_battle(
        team0=[Pokemon("マリルリ", ability_name="はやおき", move_names=["たいあたり"])],
        team1=[Pokemon("ニャース")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "ねむり", count=3)
    battle.volatile_manager.apply(attacker, "こんらん", count=5)
    battle.test_option.trigger_volatile = True

    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.ailment.count == 3, "こんらん状態ではやおきの追加消費も行われないはず"


def test_ねむり_通常付与のcountは2か3():
    """ねむり: 通常付与（count省略時）のカウントは2または3（Champions仕様）"""
    results = set()
    for _ in range(100):
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ")],
            team1=[Pokemon("カビゴン")],
        )
        mon = battle.actives[0]
        battle.ailment_manager.apply(mon, "ねむり")
        results.add(mon.ailment.count)
        if results == {2, 3}:
            break
    assert results <= {2, 3}, f"count の範囲外の値が検出された: {results}"
    assert 2 in results or 3 in results, "count が 2 または 3 のどちらかしか出なかった（偏り）"


def test_まひ_すばやさ低下():
    """まひ: 素早さ半減"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("リザードン")]
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] // 2


def test_まひ_行動不能():
    """まひ: 行動不能（Champions仕様: 12.5%の確率）"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動不能になる設定（trigger_ailment=True）
    battle.test_option.trigger_ailment = True
    t.run_move(battle, 0)

    assert not battle.move_executor.action_success


def test_まひ_行動成功():
    """まひ: 行動可能（trigger_ailment=Falseで必ず行動できる）"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("リザードン")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    # 必ず行動できる設定
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)
    assert battle.move_executor.action_success, "まひでも行動不能トリガーなしなら行動できる"


def test_もうどく_15ターン上限():
    """もうどく: 16ターン以降もダメージは15/16で頭打ち"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("カビゴン")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")
    # 14ターン進める（各ターン後にHPを回復して続行）
    for _ in range(14):
        t.end_turn(battle)
        battle.modify_hp(mon, v=mon.max_hp)

    # 15ターン目: 15/16ダメージ
    hp_before = mon.hp
    t.end_turn(battle)
    damage15 = hp_before - mon.hp
    assert mon.ailment.elapsed_turns == 15
    assert damage15 == mon.max_hp * 15 // 16

    # 16ターン目: 上限15/16で頭打ち（増加しない）
    battle.modify_hp(mon, v=mon.max_hp)
    hp_before = mon.hp
    t.end_turn(battle)
    damage16 = hp_before - mon.hp
    assert mon.ailment.elapsed_turns == 16
    assert damage16 == mon.max_hp * 15 // 16  # 上限は15ターン分（15/16）


def test_もうどく_ダメージ():
    """もうどく: ターン経過でダメージ増加"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")
    # nターン目: n/16ダメージ
    for i in range(3):
        hp_before = mon.hp
        t.end_turn(battle)
        damage = hp_before - mon.hp
        assert mon.ailment.elapsed_turns == i + 1
        assert damage == mon.max_hp * (i + 1) // 16


def test_もうどく_マジックガードでもターン経過は加算される():
    """もうどく: マジックガードでダメージを受けない間もelapsed_turnsは加算され続け、
    かがくへんかガスで特性が無効化されたターンには継続していたターン数分のダメージを受ける"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("カビゴン"), Pokemon("ドガース", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")

    for _ in range(3):
        t.end_turn(battle)
    assert mon.hp == mon.max_hp, "マジックガードでダメージを受けない"
    assert mon.ailment.elapsed_turns == 3, "ダメージを受けなくてもターン経過は記録される"

    # かがくへんかガスでマジックガードを無効化
    t.run_switch(battle, 1, 1)
    hp_before = mon.hp
    t.end_turn(battle)
    damage = hp_before - mon.hp
    assert mon.ailment.elapsed_turns == 4
    assert damage == mon.max_hp * 4 // 16, "特性を失ったターンは継続していたターン数分のダメージを受ける"


def test_もうどく_交代でカウントリセット():
    """もうどく: 交代するとダメージカウントが1/16にリセット"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ニャース")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")

    # 2ターン経過（elapsed_turns=2, ダメージ2/16）
    t.end_turn(battle)
    t.end_turn(battle)
    assert mon.ailment.elapsed_turns == 2

    # 交代するとカウントリセット
    t.run_switch(battle, 0, 1)
    assert mon.ailment.elapsed_turns == 0, "交代後はelapsed_turnsが0にリセットされる"

    # 交代して戻ってきたとき、カウントが0からになる
    t.run_switch(battle, 0, 0)
    hp_before = mon.hp
    t.end_turn(battle)
    damage = hp_before - mon.hp
    assert mon.ailment.elapsed_turns == 1
    assert damage == mon.max_hp * 1 // 16  # 交代後1ターン目は1/16ダメージ


def test_やけど_こんらん自傷ダメージは半減しない():
    """やけど: こんらんの自傷ダメージ（内部技名"_こんらん"）は物理技扱いだが、
    第五世代以降はやけどによる半減の影響を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "やけど")
    # 自傷を強制
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.burn_modifier == 4096


def test_やけど_ダメージ():
    """やけど: ターン終了時ダメージ"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert mon.hp == mon.max_hp - mon.max_hp // 16


def test_やけど_物理技ダメージ半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")]
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "やけど")
    t.run_move(battle, 0)
    assert battle.damage_calculator.burn_modifier == 2048


def test_やけど_特殊技ダメージは半減しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ")]
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(attacker, "やけど")
    t.run_move(battle, 0)
    assert battle.damage_calculator.burn_modifier == 4096


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
