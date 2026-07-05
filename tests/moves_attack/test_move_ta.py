"""攻撃技ハンドラの単体テスト（た行）。"""

import pytest
from jpoke import Pokemon
from jpoke.data.move import MOVES
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


def test_ダークファイア_やけどが発動する():
    """ダークファイア: 10%でやけどを付与する。ゴーストタイプはノーマルには無効のため、エスパータイプのミュウツーを対象とする。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ダークファイア"])],
        team1=[Pokemon("ミュウツー")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


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
    assert attacker.rank["atk"] == -1
    assert attacker.rank["spa"] == -1


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
    move_data = MOVES["とびひざげり"]
    assert "recoil" not in move_data.flags


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
    """ともえなげ: ダメージ後に相手の次の控えポケモンへ強制交代させる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ともえなげ"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is not defender_before


def test_ともえなげ_次の控えポケモンが交代先になる():
    """ともえなげ: 交代先は次に控えているポケモン（controls[0]）に固定される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ともえなげ"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン"), Pokemon("ピカチュウ")],
        accuracy=100,
    )
    player1 = battle.players[1]
    # state.team[1]はヤドン（バトル中の実体）
    expected_next = battle.player_states[player1].team[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is expected_next


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
    """ドラゴンテール: ダメージ後に相手の次の控えポケモンへ強制交代させる。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is not defender_before


def test_ドラゴンテール_次の控えポケモンが交代先になる():
    """ドラゴンテール: 交代先は次に控えているポケモン（controls[0]）に固定される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ドラゴンテール"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン"), Pokemon("ピカチュウ")],
        accuracy=100,
    )
    player1 = battle.players[1]
    # state.team[1]はヤドン（バトル中の実体）
    expected_next = battle.player_states[player1].team[1]
    t.run_move(battle, 0)
    assert battle.actives[1] is expected_next


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
