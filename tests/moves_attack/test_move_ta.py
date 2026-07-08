"""攻撃技ハンドラの単体テスト（た行）。"""

import pytest
from jpoke import Pokemon
from jpoke.data.move import MOVES
from jpoke.enums import Interrupt
from .. import test_utils as t


def test_DDラリアット_相手のぼうぎょランクを無視する():
    """DDラリアット: 相手のぼうぎょランクが上がっていてもダメージが変わらない。"""
    battle1 = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["DDラリアット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle1.random.random = lambda: 0.9
    mon1 = battle1.actives[1]
    battle1.modify_stats(mon1, {"def": 6}, source=mon1)
    hp_before = mon1.hp
    t.run_move(battle1, 0)
    damage_with_b6 = hp_before - mon1.hp

    battle2 = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["DDラリアット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle2.random.random = lambda: 0.9
    mon2 = battle2.actives[1]
    hp_before2 = mon2.hp
    t.run_move(battle2, 0)
    damage_no_rank = hp_before2 - mon2.hp

    assert damage_with_b6 == damage_no_rank


def test_DDラリアット_相手のぼうぎょランク低下も無視する():
    """DDラリアット: 相手のぼうぎょランクが下がっていてもダメージが変わらない。"""
    battle1 = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["DDラリアット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle1.random.random = lambda: 0.9
    mon1 = battle1.actives[1]
    battle1.modify_stats(mon1, {"def": -6}, source=mon1)
    hp_before = mon1.hp
    t.run_move(battle1, 0)
    damage_with_neg = hp_before - mon1.hp

    battle2 = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["DDラリアット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle2.random.random = lambda: 0.9
    mon2 = battle2.actives[1]
    hp_before2 = mon2.hp
    t.run_move(battle2, 0)
    damage_no_rank = hp_before2 - mon2.hp

    assert damage_with_neg == damage_no_rank


def test_たいあたり_相手にダメージを与える():
    """たいあたり: 追加効果なしの物理ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_タキオンカッター_2回ヒットする():
    """タキオンカッター: 必ず2回ヒットする固定2回攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("メタグロス", move_names=["タキオンカッター"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


def test_タキオンカッター_きれあじ特性で威力補正1_5倍がかかる():
    """タキオンカッター: 切る技（slashフラグ）のため、特性『きれあじ』の威力補正1.5倍が発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("メタグロス", ability_name="きれあじ", move_names=["タキオンカッター"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_タキオンカッター_相手の回避率が高くても必ず命中する():
    """タキオンカッター: 自分の命中率、相手の回避率に関係なく必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("メタグロス", move_names=["タキオンカッター"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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


def test_たたきつける_相手にダメージを与える():
    """たたきつける: 追加効果なしの物理ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たたきつける"])],
        team1=[Pokemon("カメックス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_たたりめ_ぜったいねむりの相手には常に威力2倍():
    """たたりめ: 特性『ぜったいねむり』を持つ相手（ゆめうつつ状態異常）にも威力2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["たたりめ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ぜったいねむり")],
        accuracy=100,
    )
    assert battle.actives[1].ailment.name == "ゆめうつつ"
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_たたりめ_まひ状態でも威力2倍():
    """たたりめ: まひ状態の相手に対しても威力が2倍になる。
    ゴーストタイプはノーマルには無効のため、エスパータイプのミュウツーを対象とする。
    """
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["たたりめ"])],
        team1=[Pokemon("ミュウツー")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_たたりめ_状態異常なしのとき通常威力():
    """たたりめ: 対象が状態異常でないとき威力補正なし。
    ゴーストタイプはノーマルには無効のため、エスパータイプのミュウツーを対象とする。
    """
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["たたりめ"])],
        team1=[Pokemon("ミュウツー")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_たたりめ_状態異常のとき威力2倍():
    """たたりめ: 対象が状態異常のとき威力が2倍になる。
    ゴーストタイプはノーマルには無効のため、エスパータイプのミュウツーを対象とする。
    """
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["たたりめ"])],
        team1=[Pokemon("ミュウツー")],
        ailment1=("どく", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


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


def test_タネばくだん_くさタイプの物理弾技である():
    """タネばくだん: くさタイプ・物理・威力80・PP16・bulletフラグを持つ。"""
    move_data = MOVES["タネばくだん"]
    assert move_data.type == "くさ"
    assert move_data.category == "physical"
    assert move_data.power == 80
    assert move_data.pp == 16
    assert "bullet" in move_data.flags


def test_タネばくだん_相手にダメージを与える():
    """タネばくだん: 追加効果なしの物理くさ技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["タネばくだん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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
    battle.step()

    # 複数ヒット予定（min_hits=2）なのに、最初の1発で相手がひんしになったため処理が中断される
    # ダメージ計算が1回だけ実行される
    assert damage_call_count == 1
    assert defender.hp == 0


def test_だいちのちから_とくぼう1段階低下が発動しない():
    """だいちのちから: 追加効果不発時はとくぼうランクが変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["だいちのちから"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spd"] == 0


def test_だいちのちから_とくぼう1段階低下が発動する():
    """だいちのちから: 10%の確率で相手のとくぼうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["だいちのちから"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spd"] == -1


def test_だいちのちから_相手にダメージを与える():
    """だいちのちから: 特殊じめん技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["だいちのちから"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_だいちのはどう_エレキフィールドでタイプがでんきに変化する():
    """だいちのはどう: エレキフィールド発動中に使用するとタイプがでんきになる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "でんき"


def test_だいちのはどう_エレキフィールドで威力2倍かつ1_3倍ボーナスが乗る():
    """だいちのはどう: エレキフィールド時はwazaの威力×2かつでんきタイプとして1.3倍ボーナスが乗る。
    power_modifier = 4096 * (8192/4096) * (5325/4096) = 4096 * 2 * 1.3 = 10650。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    # 4096 * 8192 // 4096 = 8192 → 8192 * 5325 // 4096 = 10650
    assert battle.damage_calculator.power_modifier == 10650


def test_だいちのはどう_グラスフィールドでタイプがくさに変化する():
    """だいちのはどう: グラスフィールド発動中に使用するとタイプがくさになる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "くさ"


def test_だいちのはどう_グラスフィールドで威力2倍が乗る():
    """だいちのはどう: グラスフィールド時はくさタイプに変化し威力×2になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    # グラスフィールドはくさ技を×1.3倍: 8192 * 5325 // 4096 = 10650
    assert battle.damage_calculator.power_modifier == 10650


def test_だいちのはどう_サイコフィールドでタイプがエスパーに変化する():
    """だいちのはどう: サイコフィールド発動中に使用するとタイプがエスパーになる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("サイコフィールド", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "エスパー"


def test_だいちのはどう_サイコフィールドで威力2倍が乗る():
    """だいちのはどう: サイコフィールド時はエスパータイプに変化し威力×2になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("サイコフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    # サイコフィールドはエスパー技を×1.3倍: 8192 * 5325 // 4096 = 10650
    assert battle.damage_calculator.power_modifier == 10650


def test_だいちのはどう_フィールドなしのときノーマルタイプで通常威力():
    """だいちのはどう: フィールドがない場合はノーマルタイプのまま威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"
    assert battle.damage_calculator.power_modifier == 4096


def test_だいちのはどう_ふゆう特性持ちのときフィールド効果なし():
    """だいちのはどう: 使用者がふゆう特性を持ち浮遊状態のとき、タイプ変換・威力増加なし。"""
    battle = t.start_battle(
        team0=[Pokemon("ロトム", ability_name="ふゆう", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"
    assert battle.damage_calculator.power_modifier == 4096


def test_だいちのはどう_ミストフィールドでタイプがフェアリーに変化する():
    """だいちのはどう: ミストフィールド発動中に使用するとタイプがフェアリーになる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("ミストフィールド", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "フェアリー"


def test_だいちのはどう_ミストフィールドで威力2倍が乗る():
    """だいちのはどう: ミストフィールド時はフェアリータイプに変化し威力×2になる。
    ミストフィールドはフェアリー技のボーナスを与えないため威力補正は×2のみ。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("ミストフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    # ミストフィールドはフェアリー技ボーナスなし: ×2のみ
    assert battle.damage_calculator.power_modifier == 8192


def test_だいばくはつ_HP消費後も攻撃が相手に届く():
    """だいばくはつ: ON_PAY_HPはヒット処理より前に発火するため、HP0でも攻撃が相手に届く。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいばくはつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_だいばくはつ_しめりけ持ちには技が失敗する():
    """だいばくはつ: labels=["explosion"]のため、しめりけ持ちには技が失敗する。ON_PAY_HPは発火しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいばくはつ"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    assert attacker.hp == hp_before


def test_だいばくはつ_使用後に攻撃者がひんしになる():
    """だいばくはつ: ON_PAY_HPで現在HPを全消費し、技使用後に使用者がひんし状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいばくはつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert not attacker.alive


def test_ダイビング_1ターン目は水中に潜りHPが変わらない():
    """ダイビング: 1ターン目はチャージターンのため相手にダメージを与えず、ダイビング揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ダイビング"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert attacker.has_volatile("ダイビング")
    assert defender.hp == hp_before


def test_ダイビング_2ターン目に攻撃して揮発状態が解除される():
    """ダイビング: 2ターン目に攻撃が発動し、揮発状態が解除されて相手のHPが減る。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ダイビング"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 1ターン目: 水中に潜る
    t.run_move(battle, 0)
    assert attacker.has_volatile("ダイビング")
    hp_before = defender.hp
    # 2ターン目: 攻撃して揮発状態が解除される
    t.run_move(battle, 0)
    assert not attacker.has_volatile("ダイビング")
    assert defender.hp < hp_before


def test_ダイビング_タイプ威力命中PPが仕様通り():
    """ダイビング: みずタイプの物理直接攻撃技で、威力80・命中100・PP12を持つ（PPはチャンピオンズ仕様）。"""
    move_data = MOVES["ダイビング"]
    assert move_data.type == "みず"
    assert move_data.category == "physical"
    assert move_data.power == 80
    assert move_data.accuracy == 100
    assert move_data.pp == 12
    assert "contact" in move_data.flags


def test_ダイビング_なみのりうずしおは水中でも命中し威力2倍():
    """ダイビング: 水中のポケモンになみのり・うずしおは命中し、威力2倍になる。"""
    for move_name in ("なみのり", "うずしお"):
        battle = t.start_battle(
            team0=[Pokemon("カビゴン", move_names=[move_name])],
            team1=[Pokemon("カビゴン")],
            accuracy=100,
        )
        defender = battle.actives[1]
        battle.volatile_manager.apply(defender, "ダイビング", count=1)
        t.run_move(battle, 0)
        assert battle.move_executor.move_success
        assert battle.damage_calculator.power_modifier == 8192


def test_ダイビング_水中は通常技を回避する():
    """ダイビング: 水中にいる間は通常の攻撃技を回避する。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "ダイビング", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_だいふんげき_カウント終了後にこんらんが付与される():
    """だいふんげき: カウントが0になった後にこんらん状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["だいふんげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=1, source=attacker, move_name="だいふんげき")
    t.run_move(battle, 0)
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


def test_だいふんげき_初回命中時にあばれる揮発状態が付与される():
    """だいふんげき: 初回命中時にあばれる揮発状態（強制行動）が付与される。物理ほのお技。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["だいふんげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("あばれる")


def test_ダイマックスほう_相手にダメージを与える():
    """ダイマックスほう: 追加効果なしの特殊ドラゴン技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ボーマンダ", move_names=["ダイマックスほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_だいもんじ_こおり状態の相手に当てると解凍する():
    """だいもんじ: ほのおタイプの攻撃技のため、被弾した相手のこおりを解凍する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["だいもんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


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


def test_ダイヤストーム_ちからずくで威力が上がり追加効果が発動しない():
    """ダイヤストーム: ちからずく使用時は威力が1.3倍になる代わりにぼうぎょ上昇が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ディアンシー", ability_name="ちからずく", move_names=["ダイヤストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["def"] == 0


def test_ダイヤストーム_相手にダメージを与える():
    """ダイヤストーム: 物理いわ技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ディアンシー", move_names=["ダイヤストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ダイヤストーム_防御2段階上昇が発動しない():
    """ダイヤストーム: 追加効果不発時は自分のぼうぎょランクが変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ディアンシー", move_names=["ダイヤストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=0.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["def"] == 0


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
    assert attacker.rank["def"] == 2


def test_だくりゅう_命中率1段階低下が発動する():
    """だくりゅう: 30%の確率で相手の命中率を1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["だくりゅう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["accuracy"] == -1


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


def test_ダブルウイング_タイプ分類威力命中PPが仕様通り():
    """ダブルウイング: ひこうタイプ・物理・威力40・命中90・PP12・直接攻撃の固定2回攻撃技。"""
    move_data = MOVES["ダブルウイング"]
    assert move_data.type == "ひこう"
    assert move_data.category == "physical"
    assert move_data.power == 40
    assert move_data.accuracy == 90
    assert move_data.pp == 12
    assert "contact" in move_data.flags
    assert move_data.multi_hit == {
        "min": 2,
        "max": 2,
        "check_hit_each_time": False,
        "power_sequence": (),
    }


def test_ダメおし_ダメージを受けていないとき通常威力():
    """ダメおし: 対象がそのターン中ダメージを受けていなければ威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["ダメおし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ダメおし_同ターンにダメージを受けていたら威力2倍():
    """ダメおし: 対象が同ターンにすでにダメージを受けていたら威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["ダメおし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # hits_taken を手動で設定（すでにダメージを受けている状態）
    defender.hits_taken = 1
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_ダメおし_相手が受けたゴツゴツメットの反射ダメージも同ターンのダメージとして扱われる():
    """ダメおし: 対象が同ターン中にゴツゴツメット所持者への接触で反射ダメージを受けていれば威力2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット", move_names=["ダメおし"])],
        accuracy=100,
    )
    # team0がteam1（ゴツゴツメット所持者）に接触技を当て、反射ダメージを受ける
    t.run_move(battle, 0)
    battle.random.random = lambda: 0.9
    # team1のダメおしは、反射ダメージを受けたばかりのteam0を対象にする
    t.run_move(battle, 1)
    assert battle.damage_calculator.power_modifier == 8192


def test_ダメおし_相手のいのちのたま反動も同ターンのダメージとして扱われる():
    """ダメおし: 対象が同ターン中にいのちのたまの反動ダメージを受けていれば威力2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="いのちのたま", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", move_names=["ダメおし"])],
        accuracy=100,
    )
    t.run_move(battle, 0)
    battle.random.random = lambda: 0.9
    t.run_move(battle, 1)
    assert battle.damage_calculator.power_modifier == 8192


def test_ダメおし_相手の反動ダメージも同ターンのダメージとして扱われる():
    """ダメおし: 対象が同ターン中に自分の技の反動ダメージ（とっしん）を受けていれば威力2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["とっしん"])],
        team1=[Pokemon("カビゴン", move_names=["ダメおし"])],
        accuracy=100,
    )
    # team0（とっしんの使用者）が反動ダメージを受ける
    t.run_move(battle, 0)
    battle.random.random = lambda: 0.9
    # team1（ダメおし）がその反動を受けたばかりのteam0を対象にする
    t.run_move(battle, 1)
    assert battle.damage_calculator.power_modifier == 8192


def test_だんがいのつるぎ_相手にダメージを与える():
    """だんがいのつるぎ: 追加効果なしの物理じめん技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だんがいのつるぎ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ちきゅうなげ_こらえるで1HP残る():
    """ちきゅうなげ: 固定ダメージの計算がこらえるより先に行われ、瀕死を防げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちきゅうなげ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        volatile1={"こらえる": 1},
    )
    attacker, defender = battle.actives
    battle.modify_hp(defender, -(defender.hp - 1))
    t.run_move(battle, 0)
    assert defender.hp == 1
    assert not defender.fainted


def test_ちきゅうなげ_ゴーストには無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちきゅうなげ"])],
        team1=[Pokemon("ゴース", move_names=["はねる"])],
    )
    battle.step()
    assert battle.actives[1].hp == battle.actives[1].max_hp


def test_ちきゅうなげ_みがわりのHPを上限として肩代わりされる():
    """ちきゅうなげ: みがわりの残りHPを上限として使用者レベル分のダメージが肩代わりされ、
    超過分は本体に持ち越されない（本体HPは変化しない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちきゅうなげ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=30)
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 使用者レベル(50)分のダメージはみがわりのHP(30)を上回るため、みがわりが解除される
    assert not defender.has_volatile("みがわり")
    # 超過分は本体に持ち越されず、本体HPは変化しない
    assert defender.hp == hp_before


def test_ちきゅうなげ_与ダメージは使用者レベル固定():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", level=50, move_names=["ちきゅうなげ"])],
                            )
    before_hp = battle.actives[1].hp
    battle.step()
    assert before_hp - battle.actives[1].hp == 50


def test_チャージビーム_secondary_effectフラグを持つ():
    """チャージビーム: ちからずくとの相互作用のためsecondary_effectフラグを持つこと。"""
    move_data = MOVES["チャージビーム"]
    assert "secondary_effect" in move_data.flags


def test_チャージビーム_ちからずくで威力が上がり追加効果が発動しない():
    """チャージビーム: ちからずく使用時は威力が1.3倍になる代わりにとくこう上昇が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["チャージビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["spa"] == 0


def test_チャージビーム_とくこう1段階上昇が発動する():
    """チャージビーム: 確率70%で使用者のCが1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["チャージビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["spa"] == 1


def test_チャームボイス_タイプ分類威力が正しく反映される():
    """チャームボイス: フェアリー・特殊・威力40が正しく反映される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピクシー", move_names=["チャームボイス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    move = t.run_move(battle, 0)
    assert move.type == "フェアリー"
    assert move.category == "special"
    assert move.power == 40


def test_チャームボイス_相手の回避率が高くても必ず命中する():
    """チャームボイス: 自分の命中率、相手の回避率に関係なく必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピクシー", move_names=["チャームボイス"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ツインビーム_タイプ分類威力命中PPが仕様通り():
    """ツインビーム: エスパータイプ・特殊・威力40・命中100・PP12・非接触の固定2回攻撃技。"""
    move_data = MOVES["ツインビーム"]
    assert move_data.type == "エスパー"
    assert move_data.category == "special"
    assert move_data.power == 40
    assert move_data.accuracy == 100
    assert move_data.pp == 12
    assert "contact" not in move_data.flags
    assert move_data.multi_hit == {
        "min": 2,
        "max": 2,
        "check_hit_each_time": False,
        "power_sequence": (),
    }


def test_つけあがる_ACCランク上昇もカウントする():
    """つけあがる: ACC+1も威力に影響する（命中率・回避率もランク合計の対象）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["つけあがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"accuracy": 1}, source=attacker)
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_つけあがる_こうげきランク上昇1段階で威力40():
    """つけあがる: A+1のとき威力40（20 × (1+1)）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["つけあがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"atk": 1}, source=attacker)
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_つけあがる_ランク上昇なしのとき威力20():
    """つけあがる: ランク上昇がないとき基本威力20のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["つけあがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 20


def test_つけあがる_ランク低下はカウントしない():
    """つけあがる: A-1があっても正のランク合計がゼロならば威力は20のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["つけあがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"atk": -1}, source=attacker)
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 20


def test_つけあがる_複数ステータス上昇合計3段階のとき威力80():
    """つけあがる: A+2, B+1 の合計+3のとき威力80（20 × (1+3)）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["つけあがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"atk": 2, "def": 1}, source=attacker)
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_つじぎり_急所ランクが1():
    """つじぎり: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("アブソル", move_names=["つじぎり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_つじぎり_急所ランクが1_乱数大で急所なし():
    """つじぎり: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("アブソル", move_names=["つじぎり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


@pytest.mark.parametrize("mon_name, item_name, expected_type", [
    ("オーガポン(みどり)", None, "くさ"),
    ("オーガポン(いど)", "いどのめん", "みず"),
    ("オーガポン(かまど)", "かまどのめん", "ほのお"),
    ("オーガポン(いしずえ)", "いしずえのめん", "いわ"),
])
def test_ツタこんぼう_オーガポンのフォルムに応じてタイプが変わる(mon_name, item_name, expected_type):
    """ツタこんぼう: オーガポンが使用した場合、フォルム（仮面）に応じて技タイプが変わる。"""
    kwargs = {"item_name": item_name} if item_name is not None else {}
    battle = t.start_battle(
        team0=[Pokemon(mon_name, move_names=["ツタこんぼう"], **kwargs)],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == expected_type


def test_ツタこんぼう_オーガポン以外が使用するとくさタイプ固定():
    """ツタこんぼう: オーガポン以外が使用した場合は仮面を持っていても常にくさタイプ。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="いどのめん", move_names=["ツタこんぼう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "くさ"


def test_ツタこんぼう_マジックルームでも仮面の威力補正が無効でもタイプは変わらない():
    """ツタこんぼう: マジックルームで仮面の威力補正が無効化されていてもタイプはフォルム基準のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いど)", item_name="いどのめん", move_names=["ツタこんぼう"])],
        team1=[Pokemon("カビゴン")],
        field={"マジックルーム": 5},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "みず"


def test_つっぱり_複数ヒットする():
    """つっぱり: 2~5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["つっぱり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_つつく_相手にダメージを与える():
    """つつく: 追加効果なしの物理ひこう技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", move_names=["つつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_つのでつく_相手にダメージを与える():
    """つのでつく: 追加効果なしの物理ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["つのでつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_つばさでうつ_相手にダメージを与える():
    """つばさでうつ: 追加効果なしの物理ひこう技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", move_names=["つばさでうつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_つばめがえし_相手にダメージを与える():
    """つばめがえし: 追加効果なしの物理ひこう技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", move_names=["つばめがえし"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_つばめがえし_相手の回避ランクが高くても必ず命中する():
    """つばめがえし: 必中技のため、相手の回避ランクが高くても必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", move_names=["つばめがえし"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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


def test_つららばり_複数ヒットする():
    """つららばり: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["つららばり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_つるのムチ_相手にダメージを与える():
    """つるのムチ: 追加効果なしの物理くさ技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["つるのムチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_てっていこうせん_HP消費が最大HPの半分である():
    """てっていこうせん: 使用前に自分の最大HPの1/2(切り上げ)を消費する。"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", move_names=["てっていこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    expected_cost = max(1, (attacker.max_hp + 1) // 2)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_cost


def test_てっていこうせん_HP消費は切り上げである():
    """てっていこうせん: 最大HPが奇数の場合、消費HPは切り上げになる（切り捨てとは異なる値）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["てっていこうせん"])],
        team1=[Pokemon("ドサイドン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.max_hp % 2 == 1  # 前提: 最大HPが奇数であること
    expected_cost = (attacker.max_hp + 1) // 2
    floor_cost = attacker.max_hp // 2
    assert expected_cost != floor_cost
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
    attacker.hp = (attacker.max_hp + 1) // 2
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert defender.hp < defender.max_hp


def test_てっていこうせん_いしあたまでも反動を受ける():
    """てっていこうせん: 特性いしあたまでも反動ダメージは無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", ability_name="いしあたま", move_names=["てっていこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    expected_cost = max(1, (attacker.max_hp + 1) // 2)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_cost


def test_てっていこうせん_マジックガードで反動を受けない():
    """てっていこうせん: 特性マジックガードでは反動ダメージを受けない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", ability_name="マジックガード", move_names=["てっていこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before
    assert defender.hp < defender.max_hp


def test_テラクラスター_ステラテラスタル時にタイプがステラタイプへ変化する():
    """ステラテラスタル時のみタイプがステラタイプに変化する。威力は120のまま変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="ステラ", move_names=["テラクラスター"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.terastallize()
    t.run_move(battle, 0)

    assert battle.move_executor.move_type == "ステラ"
    assert battle.damage_calculator.final_power == 120
    # テラバーストと異なり、命中後の能力ランクダウンは発生しない
    assert attacker.rank["atk"] == 0
    assert attacker.rank["spa"] == 0


@pytest.mark.parametrize(
    ("attacker_name", "expected"),
    [
        ("カイリキー", "physical"),
        ("フーディン", "special"),
    ],
)
def test_テラクラスター_ステラテラスタル時に高い攻撃値の分類になる(attacker_name: str, expected: str):
    """ステラテラスタル時、補正込みAがCより高ければ物理技として計算される。"""
    battle = t.start_battle(
        team0=[Pokemon(attacker_name, tera_type="ステラ", move_names=["テラクラスター"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.resolve_move_category(attacker, move) == "special"
    attacker.terastallize()
    assert battle.move_executor.resolve_move_category(attacker, move) == expected

    move.unregister_handlers(battle.events, attacker)


@pytest.mark.parametrize(
    ("tera_type", "expected_type"),
    [
        ("ステラ", "ステラ"),
        ("ほのお", "ノーマル"),
    ],
)
def test_テラクラスター_ステラ以外のテラスタルではタイプが変化しない(tera_type: str, expected_type: str):
    """テラバーストと異なり、ステラ以外のテラスタイプではタイプ変化が起こらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type=tera_type, move_names=["テラクラスター"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.resolve_move_type(attacker, move) == "ノーマル"

    attacker.terastallize()
    assert battle.move_executor.resolve_move_type(attacker, move) == expected_type

    move.unregister_handlers(battle.events, attacker)


def test_テラクラスター_ステラ以外のテラスタルでは分類が変化しない():
    """こうげきがとくこうより高いポケモンでも、ステラ以外のテラスタイプでは分類が変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", tera_type="ほのお", move_names=["テラクラスター"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    attacker.terastallize()
    assert battle.move_executor.resolve_move_category(attacker, move) == "special"

    move.unregister_handlers(battle.events, attacker)


def test_テラバースト_ステラ():
    """ステラタイプ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="ステラ", move_names=["テラバースト"])],
        team1=[Pokemon("ピカチュウ", tera_type="でんき")],
    )
    attacker = battle.actives[0]
    attacker.terastallize()
    t.run_move(battle, 0)

    assert battle.move_executor.move_type == "ステラ"
    assert battle.damage_calculator.final_power == 100
    assert attacker.rank["atk"] == -1
    assert attacker.rank["spa"] == -1


def test_テラバースト_テラスタイプがノーマルでもスキン特性の対象にならない():
    """テラスタルしているときはテラスタイプがノーマルであっても、
    ノーマル技のタイプを変える特性（スキン系）の対象にならずテラスタイプ（ノーマル）のままになる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="フェアリースキン", tera_type="ノーマル", move_names=["テラバースト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.resolve_move_type(attacker, move) == "フェアリー"

    attacker.terastallize()
    assert battle.move_executor.resolve_move_type(attacker, move) == "ノーマル"

    move.unregister_handlers(battle.events, attacker)


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
        ("カイリキー", "physical"),
        ("フーディン", "special"),
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

    assert battle.move_executor.resolve_move_category(attacker, move) == "special"
    attacker.terastallize()
    assert battle.move_executor.resolve_move_category(attacker, move) == expected


def test_であいがしら_交代後の最初の行動では成功する():
    """であいがしら: 交代で場に出た直後の最初の行動では成功する。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ヘラクロス", move_names=["たいあたり"]),
            Pokemon("グソクムシャ", move_names=["であいがしら"]),
        ],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # 場に出ているポケモンの最初の行動を消費する
    t.run_move(battle, 0, 0)
    # 交代（グソクムシャにとっては場に出てから最初の行動）
    t.run_switch(battle, 0, 1)
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0, 0)
    assert defender.hp < hp_before


def test_であいがしら_場に出てから最初の行動でなければ失敗する():
    """であいがしら: 場に出てから最初の行動でなければ失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ヘラクロス", move_names=["たいあたり", "であいがしら"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # 場に出てから最初の行動として別の技を使用する
    t.run_move(battle, 0, 0)
    defender = battle.actives[1]
    hp_before = defender.hp
    # 2回目の行動としてであいがしらを使用 → 失敗する
    t.run_move(battle, 0, 1)
    assert defender.hp == hp_before


def test_であいがしら_相手にダメージを与える():
    """であいがしら: 優先度+2の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ヘラクロス", move_names=["であいがしら"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_デカハンマー_2ターン後は再び選択可能():
    """デカハンマー: 使用から2ターン後は揮発状態が解除されてデカハンマーを再び選択できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["デカハンマー", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    # デカハンマー使用
    t.run_move(battle, 0)
    # ターン終了（count: 2→1）
    t.end_turn(battle)
    assert attacker.has_volatile("デカハンマー")
    # もう1ターン終了（count: 1→0 → 揮発解除）
    t.end_turn(battle)
    assert not attacker.has_volatile("デカハンマー")
    # デカハンマーが再び選択可能
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "デカハンマー" in move_names


def test_デカハンマー_まひで行動不能だった場合はPP未消費で次のターンも選択可能():
    """デカハンマー: まひで行動できずPPが消費されなかった場合、揮発状態は付与されず次のターンも選択できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["デカハンマー", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    battle.ailment_manager.apply(attacker, "まひ")
    # 必ず行動不能になる設定
    battle.test_option.trigger_ailment = True
    pp_before = attacker.moves[0].pp
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert attacker.moves[0].pp == pp_before
    assert not attacker.has_volatile("デカハンマー")
    # 次ターンもデカハンマーを選択できる
    t.end_turn(battle)
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "デカハンマー" in move_names


def test_デカハンマー_まもるで防がれた場合も次のターンは選択不可():
    """デカハンマー: まもるで防がれてもPP消費済みなので次のターンは選択不可。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["デカハンマー", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手にまもるを付与した状態でデカハンマーを使用（防がれる）
    battle.volatile_manager.apply(defender, "まもる", count=1)
    t.run_move(battle, 0)
    # まもるで防がれてもデカハンマー揮発が付与される
    assert attacker.has_volatile("デカハンマー")
    # ターン終了（count: 2→1）
    t.end_turn(battle)
    # 次ターンの選択肢にデカハンマーが含まれない
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "デカハンマー" not in move_names


def test_デカハンマー_使用後は次のターンに選択不可():
    """デカハンマー: 使用したターンの次のターン、コマンド選択肢にデカハンマーが現れない。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["デカハンマー", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    # デカハンマー使用 → 揮発状態が付与される
    t.run_move(battle, 0)
    assert attacker.has_volatile("デカハンマー")
    # ターン終了（count: 2→1）
    t.end_turn(battle)
    assert attacker.has_volatile("デカハンマー")
    # 次ターンのコマンドにデカハンマーが含まれない
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "デカハンマー" not in move_names


def test_デカハンマー_通常使用でダメージを与える():
    """デカハンマー: 威力160の物理はがね技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["デカハンマー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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


def test_デスウイングとドレインパンチの回復量比較():
    """heal_ratio=0.75のデスウイングは0.5技のドレインパンチより多く回復する（同じ与ダメで比較）。

    デスウイングは特殊技・ドレインパンチは物理技で攻撃側／防御側のステータスが異なるため、
    与ダメージを固定（fix_damage）した上で回復量のみを比較する。
    """
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
        t.fix_damage(b, 100)
    t.run_move(battle_death, 0)
    t.run_move(battle_drain, 0)
    # デスウイング（0.75）のほうがドレインパンチ（0.5）より多く回復しているはず
    assert battle_death.actives[0].hp > battle_drain.actives[0].hp


def test_でんきショック_まひが発動しない():
    """でんきショック: secondary_chanceが0のときまひを付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


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


def test_でんげきは_タイプと分類と威力とppが正しい():
    """でんげきは: でんきタイプ・特殊・威力60・PP20であることを確認する。"""
    move_data = MOVES["でんげきは"]
    assert move_data.type == "でんき"
    assert move_data.category == "special"
    assert move_data.power == 60
    assert move_data.pp == 20
    assert move_data.accuracy is None


def test_でんげきは_相手の回避率が高くても必ず命中する():
    """でんげきは: 自分の命中率、相手の回避率に関係なく必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんげきは"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_でんこうせっか_相手にダメージを与える():
    """でんこうせっか: 優先度+1の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_でんこうそうげき_テラスタルでんき中でも成功しタイプ除去が記録される():
    """でんこうそうげき: テラスタル（でんき）中でも成功するが、タイプは消えない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうそうげき"], tera_type="でんき")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()
    assert attacker.has_type("でんき")  # テラスタルででんきタイプを持つ
    hp_before = defender.hp
    t.run_move(battle, 0)
    # テラスタル中は成功してダメージあり、除去は記録されるがテラスタル中はタイプ消失が無視される
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before
    assert "でんき" in attacker.removed_types
    assert attacker.has_type("でんき")  # テラスタル中は消失処理が無視される


def test_でんこうそうげき_でんきタイプでないポケモンが使うと技が失敗する():
    """でんこうそうげき: でんきタイプを持たないポケモンが使うと技が失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうそうげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    assert defender.hp == hp_before


def test_でんこうそうげき_でんきタイプのポケモンが使うと成功し攻撃後にでんきタイプでなくなる():
    """でんこうそうげき: でんきタイプのポケモンが使うと成功し、攻撃後にでんきタイプが除去される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうそうげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert attacker.has_type("でんき")
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before
    assert not attacker.has_type("でんき")


def test_でんじほう_タイプと分類と威力と命中率とppが正しい():
    """でんじほう: でんきタイプ・特殊・威力120・命中50・PP5であることを確認する。"""
    move_data = MOVES["でんじほう"]
    assert move_data.type == "でんき"
    assert move_data.category == "special"
    assert move_data.power == 120
    assert move_data.accuracy == 50
    assert move_data.pp == 5


def test_でんじほう_必ず相手をまひ状態にする():
    """でんじほう: 追加効果として100%の確率で相手をまひ状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_ときのほうこう_まもるで防がれた場合はリチャージ状態にならない():
    """ときのほうこう: まもるで防がれた場合はリチャージ揮発状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ときのほうこう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("リチャージ")


def test_ときのほうこう_交代するとリチャージ状態が解除される():
    """ときのほうこう: リチャージ状態中に交代するとリチャージ揮発状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ときのほうこう"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")
    t.run_switch(battle, 0, 1)
    assert not attacker.has_volatile("リチャージ")


def test_ときのほうこう_命中後にリチャージ状態が付与される():
    """ときのほうこう: 命中後に使用者にリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ときのほうこう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")


def test_ときのほうこう_外れた場合はリチャージ状態にならない():
    """ときのほうこう: 外れた場合はリチャージ揮発状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ときのほうこう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("リチャージ")


def test_ときのほうこう_次ターン行動不能になる():
    """ときのほうこう: 次のターンはリチャージ状態により行動不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ときのほうこう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 1ターン目: 技を使用してリチャージ状態を付与
    battle.step()
    assert attacker.has_volatile("リチャージ")
    defender_hp_after_t1 = defender.hp
    # 2ターン目: リチャージ状態で行動不能のため相手HPが変化しない
    battle.step()
    assert not attacker.has_volatile("リチャージ")
    assert defender.hp == defender_hp_after_t1


def test_とっしん_みがわりへの与ダメージでも反動が発生する():
    """とっしん: みがわりに阻まれた場合、みがわりへの与ダメージを基準に反動を算出する（第五世代以降の仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["とっしん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/4)) = 25
    assert attacker.hp == hp_before - 25
    assert defender.hp == defender.max_hp


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


def test_とっしん_反動ダメージが与ダメの4分の1になる():
    """とっしん: 反動量は max(1, int(与ダメ * 1/4)) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["とっしん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/4)) = 25
    assert attacker.hp == hp_before - 25


def test_とっておき_PPが消費できなかった技は使用したことにならない():
    """とっておき: まひで行動不能になった技はPPが消費されないため、使用したことにならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか", "とっておき"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
        accuracy=100,
    )
    battle.test_option.trigger_ailment = True
    t.run_move(battle, 0, 0)
    assert battle.move_executor.action_success is False

    battle.test_option.trigger_ailment = False
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0, 1)
    assert battle.move_executor.move_success is False
    assert defender.hp == hp_before


def test_とっておき_とっておきを覚えていないポケモンが使用すると失敗する():
    """とっておき: 他の技が出る技経由等でとっておきを覚えていないポケモンが使用した場合は失敗する。"""
    from jpoke.model.move import Move

    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0, 0)
    hp_before = defender.hp
    # とっておきを覚えていないポケモンが直接とっておきを実行する(未使用技無しの状態でも失敗する)
    battle.run_move(attacker, Move("とっておき"))
    assert battle.move_executor.move_success is False
    assert defender.hp == hp_before


def test_とっておき_とっておき以外の技を覚えていない場合は失敗する():
    """とっておき: とっておき以外に覚えている技が無い場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["とっておき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success is False
    assert defender.hp == hp_before


def test_とっておき_交代して戻ると再び未使用技が必要になる():
    """とっておき: 一度控えに戻ると、次に場に出たとき再びとっておき以外の技を使う必要がある。"""
    battle = t.start_battle(
        team0=[
            Pokemon("カビゴン", move_names=["でんこうせっか", "とっておき"]),
            Pokemon("ピカチュウ", move_names=["はねる"]),
        ],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0, 0)
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)

    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0, 1)
    assert battle.move_executor.move_success is False
    assert defender.hp == hp_before


def test_とっておき_他の技をすべて使用済みならダメージを与える():
    """とっておき: とっておき以外に覚えている技をすべて使用済みなら成功し、ダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか", "とっておき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0, 0)
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0, 1)
    assert battle.move_executor.move_success is not False
    assert defender.hp < hp_before


def test_とっておき_未使用技が残っている場合は失敗する():
    """とっておき: とっておき以外に覚えている技のうち未使用のものがあれば失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか", "みずでっぽう", "とっておき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0, 0)
    defender = battle.actives[1]
    hp_before = defender.hp
    # みずでっぽうは未使用のため、とっておきは失敗する
    t.run_move(battle, 0, 2)
    assert battle.move_executor.move_success is False
    assert defender.hp == hp_before


def test_とっておき_条件を満たしていない場合は選択肢に含まれない():
    """とっておき: Champions では条件を満たしていない場合、コマンド選択肢自体に現れない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか", "とっておき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "とっておき" not in move_names


def test_とっておき_条件を満たしている場合は選択肢に含まれる():
    """とっておき: とっておき以外の技をすべて使用済みならコマンド選択肢に現れる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか", "とっておき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    t.run_move(battle, 0, 0)
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "とっておき" in move_names


def test_とどめばり_ばけのかわのフォルムチェンジ消費ダメージで倒しても攻撃が上昇する():
    """とどめばり: 技自体のダメージが0でも、ばけのかわのフォルムチェンジ消費ダメージで
    相手を倒した場合はこうげきランクが3段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["とどめばり"])],
        team1=[Pokemon("ミミッキュ", ability_name="ばけのかわ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # フォルムチェンジ消費ダメージ（最大HPの1/8）で倒れるようHPを1にする
    defender.hp = 1
    t.run_move(battle, 0)
    assert not defender.alive
    assert attacker.rank["atk"] == 3


def test_とどめばり_相手のミイラで特性が変化した後に効果が発動する():
    """とどめばり: 相手を倒すと同時に自分の特性がミイラに変化した場合、
    変化後の特性でランク変化が適用される（変化前のあまのじゃくで反転しない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とどめばり"], ability_name="あまのじゃく")],
        team1=[Pokemon("カビゴン", ability_name="ミイラ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)
    assert not defender.alive
    assert attacker.ability.name == "ミイラ"
    # あまのじゃくで反転していれば-3になるが、特性変化後なので+3のまま
    assert attacker.rank["atk"] == 3


def test_とどめばり_相手を倒さないときこうげきが上昇しない():
    """とどめばり: 相手を倒さなかった場合はこうげきランクが上昇しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["とどめばり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手のHPを満タンにして確実に生き残れる状態にする
    defender.hp = defender.max_hp
    t.run_move(battle, 0)
    assert defender.alive
    assert attacker.rank["atk"] == 0


def test_とどめばり_相手を倒したときこうげきが3段階上昇する():
    """とどめばり: この技で相手を倒すとこうげきランクが3段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["とどめばり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手を確実に倒せるようHPを1にする
    defender.hp = 1
    t.run_move(battle, 0)
    assert not defender.alive
    assert attacker.rank["atk"] == 3


def test_とびかかる_secondary_effectフラグを持つ():
    """とびかかる: ちからずくとの相互作用のためsecondary_effectフラグを持つこと。"""
    move_data = MOVES["とびかかる"]
    assert "secondary_effect" in move_data.flags


def test_とびかかる_こうげき1段階低下が発動する():
    """とびかかる: 100%の確率で相手のこうげきを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("メガヤンマ", move_names=["とびかかる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["atk"] == -1


def test_とびげり_flagsにrecoilが含まれる():
    """とびげり: flagsに"recoil"が含まれること（失敗反動技もすてみの対象であるため）。"""
    move_data = MOVES["とびげり"]
    assert "recoil" in move_data.flags


def test_とびげり_いしあたまでも失敗反動ダメージを受ける():
    """とびげり: reason=fixed_recoilのためいしあたまでも防げない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["とびげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    expected_damage = max(1, attacker.max_hp // 2)
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_damage


def test_とびげり_マジックガードでは失敗反動ダメージを受けない():
    """とびげり: reason=fixed_recoilのためマジックガードでは防げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ラッキー", ability_name="マジックガード", move_names=["とびげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before


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


def test_とびげり_外れて残HPが半分未満でもひんしになる():
    """とびげり: 残HPが失敗反動ダメージ未満でもひんし処理が行われる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["とびげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    # 残HPを1にしてから外す → 失敗反動でひんしになる
    battle.modify_hp(attacker, v=-(attacker.hp - 1), reason="self_cost", source=attacker)
    assert attacker.hp == 1
    t.run_move(battle, 0)
    assert not attacker.alive


def test_とびげり_威力命中率PPが仕様通り():
    """とびげり: 威力100・命中率95・PP10（第五世代以降の値）であること。"""
    move_data = MOVES["とびげり"]
    assert move_data.power == 100
    assert move_data.accuracy == 95
    assert move_data.pp == 10


def test_とびつく_secondary_effectフラグを持つ():
    """とびつく: ちからずくとの相互作用のためsecondary_effectフラグを持つこと。"""
    move_data = MOVES["とびつく"]
    assert "secondary_effect" in move_data.flags


def test_とびつく_すばやさ1段階低下が発動する():
    """とびつく: 100%の確率で相手のすばやさを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("メガヤンマ", move_names=["とびつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spe"] == -1


def test_とびはねる_2ターンで攻撃する():
    """とびはねる: 1ターン目はダメージを与えず揮発状態を付与し、2ターン目にダメージを与えて揮発状態を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とびはねる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターン目: 揮発状態付与のみ、ダメージなし
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert "そらをとぶ" in attacker.volatiles

    # 2ターン目: ダメージあり、揮発状態解除
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert "そらをとぶ" not in attacker.volatiles


def test_とびはねる_まひが発動する():
    """とびはねる: 2ターン目の命中時、30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とびはねる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    # 1ターン目: 揮発状態付与のみ
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name != "まひ"
    # 2ターン目: 攻撃命中、まひ付与
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_とびはねる_空中は通常技を回避する():
    """とびはねる: 1ターン目の揮発状態中は通常技を受けない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とびはねる"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp

    # 1ターン目: とびはねるを使用（揮発状態付与）
    t.run_move(battle, 0)
    # 相手のたいあたりはミスする
    t.run_move(battle, 1)
    assert attacker.hp == hp_before


def test_とびひざげり_recoilフラグを持つ():
    """とびひざげり: すてみとの相互作用のためrecoilフラグを持つこと。"""
    move_data = MOVES["とびひざげり"]
    assert "recoil" in move_data.flags


def test_とびひざげり_いしあたまでも失敗反動ダメージを受ける():
    """とびひざげり: reason=fixed_recoilのためいしあたまでも防げない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["とびひざげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    expected_damage = max(1, attacker.max_hp // 2)
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_damage


def test_とびひざげり_マジックガードでは失敗反動ダメージを受けない():
    """とびひざげり: reason=fixed_recoilのためマジックガードでは防げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ラッキー", ability_name="マジックガード", move_names=["とびひざげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before


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


def test_ともえなげ_きゅうばん持ちの相手には強制交代が無効():
    """ともえなげ: きゅうばん持ちの相手には ON_TRY_BLOW で無効化されて交代しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ともえなげ"])],
        team1=[Pokemon("カビゴン", ability_name="きゅうばん"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is defender_before


def test_ともえなげ_ダメージを与える():
    """ともえなげ: かくとうタイプの物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ともえなげ"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    player1 = battle.players[1]
    # state.team[0]はカビゴン（バトル中の実体）
    original_defender = battle.player_states[player1].team[0]
    hp_before = original_defender.hp
    t.run_move(battle, 0)
    # 交代後も元ポケモンのHPが減っている
    assert original_defender.hp < hp_before


def test_ともえなげ_ねをはる状態の相手には強制交代が無効():
    """ともえなげ: ねをはる状態の相手には ON_TRY_BLOW で無効化されて交代しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ともえなげ"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "ねをはる")
    t.run_move(battle, 0)
    assert battle.actives[1] is defender


def test_ともえなげ_交代先は控えポケモンからランダムに選ばれる():
    """ともえなげ: 交代先は控えポケモンの中からランダムに選ばれる（先頭固定ではない）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ともえなげ"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン"), Pokemon("ピカチュウ")],
        accuracy=100,
    )
    player1 = battle.players[1]
    # state.team[2]はピカチュウ（バトル中の実体）。先頭のヤドンではなく末尾を選ぶことを検証する。
    expected = battle.player_states[player1].team[2]
    battle.random.choice = lambda commands: commands[-1]
    t.run_move(battle, 0)
    assert battle.actives[1] is expected


def test_ともえなげ_控えが存在しない場合は交代しない():
    """ともえなげ: 相手に控えポケモンがいない場合は交代が発生しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ともえなげ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is defender_before


def test_ともえなげ_控えが存在する場合に相手が強制交代する():
    """ともえなげ: ダメージ後に相手が控えポケモンへ強制交代させられる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ともえなげ"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is not defender_before


def test_トライアタック_PPは12():
    """トライアタック: チャンピオンズでのPPは12（docs/champions/move_list.txt準拠。Gen9本家は10）。"""
    assert MOVES["トライアタック"].pp == 12


def test_トライアタック_こおりが発動する():
    """トライアタック: 20%の確率で3択のうちこおりが発動する（base*2/3 ≤ r < base）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["トライアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # r=0.18 は 0.1333 以上かつ 0.2 未満 → こおり
    battle.random.random = lambda: 0.18
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_トライアタック_まひが発動する():
    """トライアタック: 20%の確率で3択のうちまひが発動する（r < base/3）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["トライアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # r=0 < 0.2/3 ≒ 0.0667 → まひ
    battle.random.random = lambda: 0.0
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_トライアタック_やけどが発動する():
    """トライアタック: 20%の確率で3択のうちやけどが発動する（base/3 ≤ r < base*2/3）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["トライアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # r=0.1 は 0.0667 以上かつ 0.1333 未満 → やけど
    battle.random.random = lambda: 0.1
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_トライアタック_追加効果が発動しない():
    """トライアタック: r ≥ 0.2 のとき追加効果が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["トライアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # r=0.5 は 0.2 以上 → 追加効果なし
    battle.random.random = lambda: 0.5
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_トラバサミ_バインド中は相手が交代できない():
    """トラバサミ: バインド状態の間、ゴーストタイプでない相手は交代できない。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["トラバサミ"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("バインド")
    assert not t.can_switch(battle, 1)


def test_トラバサミ_バインド中は相手が毎ターン最大HPの8分の1ダメージを受ける():
    """トラバサミ: バインド状態のターン終了時に相手が最大HPの1/8ダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["トラバサミ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    hp_after_attack = defender.hp
    t.end_turn(battle)
    expected_damage = defender.max_hp // 8
    assert defender.hp == hp_after_attack - expected_damage


def test_トラバサミ_命中後にバインド状態になる():
    """トラバサミ: 命中時に相手がバインド揮発状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["トラバサミ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("バインド")


def test_トラバサミ_攻撃者が交代するとバインドが解除される():
    """トラバサミ: 技を使った側が交代するとバインド状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["トラバサミ"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("バインド")
    t.run_switch(battle, 0, 1)
    assert not defender.has_volatile("バインド")


def test_トリックフラワー_威力命中率PPが仕様通り():
    """トリックフラワー: くさ物理70・命中は必中(accuracy=None)・PP12であること。"""
    move_data = MOVES["トリックフラワー"]
    assert move_data.type == "くさ"
    assert move_data.category == "physical"
    assert move_data.power == 70
    assert move_data.accuracy is None
    assert move_data.pp == 12


def test_トリックフラワー_相手の回避率が高くても必ず命中する():
    """トリックフラワー: 自分の命中率、相手の回避率に関係なく必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("マスカーニャ", move_names=["トリックフラワー"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_トリックフラワー_確定急所():
    """トリックフラワー: 急所ランク3のため乱数によらず常に急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、急所は確定ランク3で必ず発生
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_トリプルアクセル_タイプ威力命中PPが仕様通り():
    """トリプルアクセル: こおりタイプの物理直接攻撃技で、威力20・命中90・PP12を持つ（PPはチャンピオンズ仕様）。"""
    move_data = MOVES["トリプルアクセル"]
    assert move_data.type == "こおり"
    assert move_data.category == "physical"
    assert move_data.power == 20
    assert move_data.accuracy == 90
    assert move_data.pp == 12
    assert "contact" in move_data.flags


def test_トリプルアクセル_威力が回数ごとに上昇する():
    """トリプルアクセル: 威力が1回目20→2回目40→3回目60と上昇する（power_sequence）。"""
    move_data = MOVES["トリプルアクセル"]
    assert move_data.multi_hit is not None
    assert move_data.multi_hit["power_sequence"] == (20, 40, 60)


def test_トリプルアクセル_最大3回ヒットする():
    """トリプルアクセル: 命中判定を各回行い、最大3回ヒットする（check_hit_each_time=True）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリプルアクセル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 3


def test_トリプルキック_2発目が外れると打ち切られる():
    """トリプルキック: check_hit_each_time=Trueのため、2発目の命中判定に外れるとそこで打ち切られる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["トリプルキック"])],
        team1=[Pokemon("カビゴン")],
    )
    battle.move_executor._check_hit = lambda ctx: ctx.hit_index == 1
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 1


def test_トリプルキック_威力が回数ごとに上昇する():
    """トリプルキック: 威力が1回目10→2回目20→3回目30と上昇する（power_sequence）。"""
    move_data = MOVES["トリプルキック"]
    assert move_data.multi_hit is not None
    assert move_data.multi_hit["power_sequence"] == (10, 20, 30)


def test_トリプルキック_最大3回ヒットする():
    """トリプルキック: 命中判定を各回行い、最大3回ヒットする（check_hit_each_time=True）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["トリプルキック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 3


def test_トリプルダイブ_3回固定でヒットする():
    """トリプルダイブ: 常に3回連続でヒットする固定回数の連続攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("ウミトリオ", move_names=["トリプルダイブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert hit_count == 3


def test_トリプルダイブ_命中判定は1発目のみで残りは必ず命中する():
    """トリプルダイブ: check_hit_each_time=Falseのため、1発目が当たれば残り2発は命中判定を行わず必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("ウミトリオ", move_names=["トリプルダイブ"])],
        team1=[Pokemon("カビゴン")],
    )
    # 1発目のみ命中、2発目以降は本来なら外れる条件にしても打ち切られないことを確認する
    battle.move_executor._check_hit = lambda ctx: ctx.hit_index == 1
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 3


def test_トリプルダイブ_相手にダメージを与える():
    """トリプルダイブ: 3ヒットで相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ウミトリオ", move_names=["トリプルダイブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_トロピカルキック_secondary_effectフラグを持つ():
    """トロピカルキック: ちからずくとの相互作用のためsecondary_effectフラグを持つこと。"""
    move_data = MOVES["トロピカルキック"]
    assert "secondary_effect" in move_data.flags


def test_トロピカルキック_こうげき1段階低下が発動する():
    """トロピカルキック: 100%の確率で相手のこうげきを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("アマージョ", move_names=["トロピカルキック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["atk"] == -1


def test_とんぼがえり_ダメージを与える():
    """とんぼがえり: 通常通りダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_とんぼがえり_まもるで防がれた場合は交代しない():
    """とんぼがえり: まもるで防がれた場合、ダメージも交代も発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    player = battle.players[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_とんぼがえり_命中しなかった場合は交代しない():
    """とんぼがえり: 命中しなかった場合、交代は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    player = battle.players[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_とんぼがえり_控えがいない場合は交代しない():
    """とんぼがえり: 控えに戦えるポケモンがいない場合、ダメージは与えるが交代は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_とんぼがえり_攻撃後に交代可能状態になる():
    """とんぼがえり: 攻撃後、控えがいれば PIVOT が設定され交代できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    t.run_move(battle, 0)
    assert battle.player_states[player].interrupt == Interrupt.PIVOT

    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)
    assert battle.actives[0].name == "ライチュウ"


def test_とんぼがえり_相手を倒した場合でも交代する():
    """とんぼがえり: 相手を倒した場合でも、使用者は交代可能状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("コイキング")],
        accuracy=100,
    )
    player = battle.players[0]
    battle.actives[1].hp = 1
    t.run_move(battle, 0)
    assert battle.actives[1].fainted
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


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


def test_どくづき_どくタイプのポケモンにはどくが付与されない():
    """どくづき: どくタイプのポケモンにはどく状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくづき"])],
        team1=[Pokemon("ドガース")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_どくづき_はがねタイプのポケモンにはどくが付与されない():
    """どくづき: はがねタイプのポケモンにはどく状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくづき"])],
        team1=[Pokemon("ハガネール")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_どくづき_めんえき特性持ちにはどくが付与されない():
    """どくづき: めんえき特性を持つポケモンにはどく状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくづき"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


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


def test_どくばりセンボン_どく状態のとき威力2倍():
    """どくばりセンボン: 対象がどく状態のとき威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくばりセンボン"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("どく", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_どくばりセンボン_もうどく状態のとき威力2倍():
    """どくばりセンボン: 対象がもうどく状態のとき威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくばりセンボン"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("もうどく", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_どくばりセンボン_状態異常なしのとき通常威力():
    """どくばりセンボン: 対象が状態異常でないとき威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくばりセンボン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_どげざつき_威力命中率PPが仕様通り():
    """どげざつき: あく物理80・命中は必中(accuracy=None)・PP10であること。"""
    move_data = MOVES["どげざつき"]
    assert move_data.type == "あく"
    assert move_data.category == "physical"
    assert move_data.power == 80
    assert move_data.accuracy is None
    assert move_data.pp == 10


def test_どげざつき_相手の回避率が高くても必ず命中する():
    """どげざつき: 自分の命中率、相手の回避率に関係なく必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("オーロンゲ", move_names=["どげざつき"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ドゲザン_タイプ威力PPが仕様通り():
    """ドゲザン: あくタイプの物理直接攻撃技で、威力85・PP12を持つ（PPはチャンピオンズ仕様）。"""
    move_data = MOVES["ドゲザン"]
    assert move_data.type == "あく"
    assert move_data.category == "physical"
    assert move_data.power == 85
    assert move_data.accuracy is None
    assert move_data.pp == 12
    assert move_data.critical_rank == 1
    assert "contact" in move_data.flags
    assert "slash" in move_data.flags


def test_ドゲザン_急所ランクが1():
    """ドゲザン: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ドドゲザン", move_names=["ドゲザン"])],
        team1=[Pokemon("カビゴン")],
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_ドゲザン_急所ランクが1_乱数大で急所なし():
    """ドゲザン: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドドゲザン", move_names=["ドゲザン"])],
        team1=[Pokemon("カビゴン")],
    )
    t.fix_random(battle, 0.5)  # 0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_ドゲザン_相手の回避率が高くても必ず命中する():
    """ドゲザン: 自分の命中率、相手の回避率に関係なく必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("ドドゲザン", move_names=["ドゲザン"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ドラゴンアロー_2回ヒットする():
    """ドラゴンアロー: 必ず2回ヒットする固定2回攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンアロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


def test_ドラゴンアロー_2発とも威力が変わらない():
    """ドラゴンアロー: power_sequence が空のため、1発目・2発目とも威力50のまま変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンアロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_power == 50


def test_ドラゴンアロー_タイプ威力PPが仕様通り():
    """ドラゴンアロー: ドラゴンタイプの物理・非接触技で、威力50・PP12を持つ（PPはチャンピオンズ仕様）。"""
    move_data = MOVES["ドラゴンアロー"]
    assert move_data.type == "ドラゴン"
    assert move_data.category == "physical"
    assert move_data.power == 50
    assert move_data.accuracy == 100
    assert move_data.pp == 12
    assert "contact" not in move_data.flags
    assert move_data.multi_hit == {
        "min": 2,
        "max": 2,
        "check_hit_each_time": False,
        "power_sequence": (),
    }


def test_ドラゴンエナジー_HP半分のとき威力が低下する():
    """ドラゴンエナジー: 使用者のHPが半分のとき威力が満タン時より低下する。"""
    battle = t.start_battle(
        team0=[Pokemon("レジドラゴ", move_names=["ドラゴンエナジー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power < 150
    assert battle.damage_calculator.final_power >= 1


def test_ドラゴンエナジー_HP満タンのとき威力150():
    """ドラゴンエナジー: 使用者のHPが満タンのとき威力150（modifier=4096）。"""
    battle = t.start_battle(
        team0=[Pokemon("レジドラゴ", move_names=["ドラゴンエナジー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp  # 満タン
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 150


def test_ドラゴンクロー_PPは16():
    """ドラゴンクロー: チャンピオンズでのPPは16（docs/champions/move_list.txt準拠）。"""
    assert MOVES["ドラゴンクロー"].pp == 16


def test_ドラゴンクロー_きれあじで威力1_5倍():
    """ドラゴンクロー: slashフラグを持つため、きれあじ特性のポケモンが使用すると威力が1.5倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー", ability_name="きれあじ", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_ドラゴンクロー_急所ランクが1():
    """ドラゴンクロー: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_ドラゴンクロー_急所ランクが1_乱数大で急所なし():
    """ドラゴンクロー: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_ドラゴンクロー_相手にダメージを与える():
    """ドラゴンクロー: 追加効果なしの物理ドラゴン技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ドラゴンハンマー_相手にダメージを与える():
    """ドラゴンハンマー: 追加効果なしの物理ドラゴン技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンハンマー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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


def test_ドラゴンテール_きゅうばん持ちの相手には強制交代が無効():
    """ドラゴンテール: きゅうばん持ちの相手には ON_TRY_BLOW で無効化されて交代しない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[Pokemon("カビゴン", ability_name="きゅうばん"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is defender_before


def test_ドラゴンテール_ねをはる状態の相手には強制交代が無効():
    """ドラゴンテール: ねをはる状態の相手には ON_TRY_BLOW で無効化されて交代しない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "ねをはる")
    t.run_move(battle, 0)
    assert battle.actives[1] is defender


def test_ドラゴンテール_ばんけん持ちの相手には強制交代が無効():
    """ドラゴンテール: ばんけん持ちの相手には ON_TRY_BLOW で無効化されて交代しない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[Pokemon("カビゴン", ability_name="ばんけん"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is defender_before


def test_ドラゴンテール_交代先は控えポケモンからランダムに選ばれる():
    """ドラゴンテール: 交代先は控えポケモンの中からランダムに選ばれる（先頭固定ではない）。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン"), Pokemon("ピカチュウ")],
        accuracy=100,
    )
    player1 = battle.players[1]
    # state.team[2]はピカチュウ（バトル中の実体）。先頭のヤドンではなく末尾を選ぶことを検証する。
    expected = battle.player_states[player1].team[2]
    battle.random.choice = lambda commands: commands[-1]
    t.run_move(battle, 0)
    assert battle.actives[1] is expected


def test_ドラゴンテール_控えが存在しない場合は交代しない():
    """ドラゴンテール: 相手に控えポケモンがいない場合は交代が発生しない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is defender_before


def test_ドラゴンテール_控えが存在する場合に相手が強制交代する():
    """ドラゴンテール: ダメージ後に相手が控えポケモンへ強制交代させられる。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is not defender_before


def test_ドラムアタック_secondary_effectフラグを持つ():
    """ドラムアタック: ちからずくとの相互作用のためsecondary_effectフラグを持つこと。"""
    move_data = MOVES["ドラムアタック"]
    assert "secondary_effect" in move_data.flags


def test_ドラムアタック_相手のすばやさ1段階低下が発動する():
    """ドラムアタック: 100%の確率で相手のすばやさを1段階下げる（自分ではなく相手が対象）。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴリランダー", move_names=["ドラムアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spe"] == -1
    assert battle.actives[0].rank["spe"] == 0


def test_ドリルくちばし_相手にダメージを与える():
    """ドリルくちばし: 追加効果なしの物理ひこう技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["ドリルくちばし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ドリルライナー_急所ランクが1():
    """ドリルライナー: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ドリュウズ", move_names=["ドリルライナー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_ドリルライナー_急所ランクが1_乱数大で急所なし():
    """ドリルライナー: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドリュウズ", move_names=["ドリルライナー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


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


def test_ドレインキッス_回復量の端数は四捨五入で切り上げになる():
    """ドレインキッス: 与ダメが端数を持つとき、回復量の端数は四捨五入（0.5以上は切り上げ）になる。

    第五世代以降の仕様（公式Wiki「技の仕様」節）に基づき、
    与ダメ101のときは round_half_up(101 * 0.75) = 76 になる
    （単純な切り捨て(int())なら75になってしまうバグを検出する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ドレインキッス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 101)
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + 76


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


def test_どろかけ_命中率1段階低下が発動する():
    """どろかけ: 100%の確率で相手の命中率を1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ナマズン", move_names=["どろかけ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["accuracy"] == -1


def test_どろばくだん_命中率1段階低下が発動する():
    """どろばくだん: 30%の確率で相手の命中率を1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ナマズン", move_names=["どろばくだん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["accuracy"] == -1
