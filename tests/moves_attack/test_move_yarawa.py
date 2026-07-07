"""攻撃技ハンドラの単体テスト（や行・ら行・わ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_Vジェネレート_防御特防素早さが各1段階低下する():
    """Vジェネレート: 命中時に使用者のB/D/Sが各1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ビクティニ", move_names=["Vジェネレート"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["def"] == -1
    assert attacker.rank["spd"] == -1
    assert attacker.rank["spe"] == -1


def test_もえあがるいかり_ひるみが発動する():
    """もえあがるいかり: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ヘルガー", move_names=["もえあがるいかり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_やけっぱち_まひで行動不能だった場合威力2倍になる():
    """やけっぱち: 前のターンにまひで行動できなかった場合、威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["やけっぱち"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
        accuracy=100,
    )
    battle.test_option.trigger_ailment = True
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False
    t.end_turn(battle)

    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_やけっぱち_まもるで防がれた場合威力2倍になる():
    """やけっぱち: 前のターンに相手のまもるで防がれた場合、威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["やけっぱち"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    t.end_turn(battle)

    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_やけっぱち_交代直後は前のターンの失敗を引き継がない():
    """やけっぱち: 交代して控えに下がった後、再度出てきたときは前の失敗状態を引き継がない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["やけっぱち"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.failed_or_immobile_last_turn
    t.end_turn(battle)

    # 控えに下がってから、再度出す
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert not attacker.failed_or_immobile_last_turn

    battle.test_option.accuracy = 100
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_やけっぱち_技が外れた場合威力2倍になる():
    """やけっぱち: 前のターンに技が外れた場合、威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["やけっぱち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_missed
    t.end_turn(battle)

    battle.test_option.accuracy = 100
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_やけっぱち_特性で無効化された場合威力2倍になる():
    """やけっぱち: 前のターンに相手の特性(もらいび)で技が無効化された場合も、威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["やけっぱち"])],
        team1=[Pokemon("ウインディ", ability_name="もらいび"), Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is False
    t.end_turn(battle)

    # 無効化されないポケモンに交代してから、やけっぱちを再度使用
    t.run_switch(battle, 1, 1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_やけっぱち_通常成功時は次のターン威力2倍にならない():
    """やけっぱち: 前のターンに技が通常通り成功した場合、威力補正はかからない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["やけっぱち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    t.end_turn(battle)

    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_やまあらし_確定急所():
    """やまあらし: 急所ランク3のため乱数によらず常に急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ヒノアラシ", move_names=["やまあらし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、急所は確定ランク3で必ず発生
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_ゆきなだれ_ダメージを受けていない場合通常威力():
    """ゆきなだれ: そのターン相手からダメージを受けていない場合、威力補正なし（power_modifier=4096）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ゆきなだれ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ゆきなだれ_物理ダメージを受けた場合威力が2倍():
    """ゆきなだれ: そのターン相手から物理ダメージを受けた場合、威力が2倍（power_modifier=8192）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ゆきなだれ"])],
        team1=[Pokemon("カビゴン", move_names=["ひっかく"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # 先に相手の物理技でダメージを受ける
    t.run_move(battle, 1)
    assert attacker.last_physical_damage_received > 0
    # ゆきなだれ実行: 物理被ダメあり → 威力2倍
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_ゆきなだれ_特殊ダメージを受けた場合も威力が2倍():
    """ゆきなだれ: そのターン相手から特殊ダメージを受けた場合も、威力が2倍（power_modifier=8192）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ゆきなだれ"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # 先に相手の特殊技でダメージを受ける
    t.run_move(battle, 1)
    assert attacker.last_special_damage_received > 0
    # ゆきなだれ実行: 特殊被ダメあり → 威力2倍
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_ゆめくい_ぜったいねむり特性の相手にも成功する():
    """ゆめくい: 特性ぜったいねむり（ゆめうつつ状態）の相手にも、ねむり状態と同様に成功する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ゆめくい"])],
        team1=[Pokemon("ネッコアラ", ability_name="ぜったいねむり")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.hp = 1
    hp_before_attacker = attacker.hp
    hp_before_defender = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before_defender
    assert attacker.hp > hp_before_attacker


def test_ゆめくい_ねむり状態でない相手には失敗する():
    """ゆめくい: 相手がねむり状態でない場合は失敗し、攻撃者のHPは変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ゆめくい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before_attacker = attacker.hp
    hp_before_defender = defender.hp
    t.run_move(battle, 0)
    # 失敗するので攻撃者のHPは変化なし、防御者もダメージなし
    assert attacker.hp == hp_before_attacker
    assert defender.hp == hp_before_defender


def test_ゆめくい_ねむり状態の相手にのみ命中しHPを回復する():
    """ゆめくい: 相手がねむり状態のとき命中し、与えたダメージの半分だけHPを回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ゆめくい"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3),
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_らいげき_まひが発動する():
    """らいげき: 20%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ライコウ", move_names=["らいげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_ライジングボルト_エレキフィールドかつ相手接地で威力2倍になる():
    """ライジングボルト: エレキフィールド中かつ相手が接地している場合、威力が2倍になる。
    さらにエレキフィールドのでんき技1.3倍ボーナスも別枠で乗るため、
    power_modifier = 4096 * (8192/4096) * (5325/4096) = 10650。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ライジングボルト"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    # 8192(自己ボーナス) → 8192 * 5325 // 4096 = 10650(フィールドボーナス込み)
    assert battle.damage_calculator.power_modifier == 10650


def test_ライジングボルト_フィールドなしのとき威力補正なし():
    """ライジングボルト: エレキフィールドが発動していない場合、威力補正はない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ライジングボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ライジングボルト_相手が浮遊している場合は威力2倍が乗らない():
    """ライジングボルト: エレキフィールド中でも相手が浮いている場合、自己ボーナスの威力2倍は乗らない。
    ただしエレキフィールドのでんき技1.3倍ボーナスは攻撃側の設置状況で判定するため乗る。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ライジングボルト"])],
        team1=[Pokemon("ピジョット")],
        terrain=("エレキフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 5325


def test_りゅうのいぶき_まひが発動する():
    """りゅうのいぶき: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["りゅうのいぶき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_りゅうのはどう_相手にダメージを与える():
    """りゅうのはどう: 追加効果なしの特殊ドラゴン技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["りゅうのはどう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_りんごさん_とくぼう1段階低下が発動する():
    """りんごさん: 100%の確率で相手のとくぼうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("マホイップ", move_names=["りんごさん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spd"] == -1


def test_リーフブレード_急所ランクが1():
    """リーフブレード: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ジュカイン", move_names=["リーフブレード"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_リーフブレード_急所ランクが1_乱数大で急所なし():
    """リーフブレード: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ジュカイン", move_names=["リーフブレード"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_レイジングブル_ケンタロスパルデア闘はかくとうタイプになる():
    """レイジングブル: ケンタロス（パルデア闘）が使用するとかくとうタイプになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア闘)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "かくとう"


def test_レイジングブル_ケンタロス水フォルムはみずタイプになる():
    """レイジングブル: ケンタロス（パルデア水）が使用するとみずタイプになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア水)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "みず"


def test_レイジングブル_ケンタロス炎フォルムはほのおタイプになる():
    """レイジングブル: ケンタロス（パルデア炎）が使用するとほのおタイプになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア炎)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ほのお"


def test_レイジングブル_ひかりのかべを解除する():
    """レイジングブル: 命中時に相手側のひかりのかべを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア闘)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        side1={"ひかりのかべ": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["ひかりのかべ"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["ひかりのかべ"].is_active


def test_レイジングブル_リフレクターを解除する():
    """レイジングブル: 命中時に相手側のリフレクターを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア闘)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["リフレクター"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["リフレクター"].is_active


def test_れいとうパンチ_こおりが発動する():
    """れいとうパンチ: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["れいとうパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_れいとうビーム_こおりが発動する():
    """れいとうビーム: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["れいとうビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_れんごく_やけどが発動する():
    """れんごく: 100%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["れんごく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_れんぞくぎり_初回は通常威力():
    """れんぞくぎり: 揮発状態がない初回使用時は威力補正なし（power_modifier=4096）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["れんぞくぎり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_れんぞくぎり_別の技を挟むとカウントがリセットされる():
    """れんぞくぎり: 別の技を使用した次のターンには連続使用カウントがリセットされる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["れんぞくぎり", "ひっかく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]

    # 1ターン目: れんぞくぎり命中 → count=1の揮発状態が付与される
    t.run_move(battle, 0, move_idx=0)
    assert attacker.volatiles["れんぞくぎり"].count == 1
    t.end_turn(battle)

    # 2ターン目: 別の技を使用 → ターン終了時に揮発状態が解除される
    t.run_move(battle, 0, move_idx=1)
    t.end_turn(battle)
    assert "れんぞくぎり" not in attacker.volatiles

    # 3ターン目: れんぞくぎりを再度使用 → 通常威力に戻っている
    t.run_move(battle, 0, move_idx=0)
    assert battle.damage_calculator.power_modifier == 4096


def test_れんぞくぎり_外れた場合カウントがリセットされる():
    """れんぞくぎり: 技が外れた場合は連続使用カウントがリセットされ、
    次に命中したときは通常威力に戻る。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["れんぞくぎり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]

    # 1ターン目: 命中してcount=1の揮発状態が付与される
    t.run_move(battle, 0)
    assert attacker.volatiles["れんぞくぎり"].count == 1
    t.end_turn(battle)

    # 2ターン目: 外れる → 揮発状態が解除される
    battle.test_option.accuracy = 0
    t.run_move(battle, 0)
    assert "れんぞくぎり" not in attacker.volatiles
    t.end_turn(battle)

    # 3ターン目: 命中 → 通常威力に戻っている（前回の威力倍率が引き継がれない）
    battle.test_option.accuracy = 100
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_れんぞくぎり_連続ヒットで威力が2倍から4倍に上昇する():
    """れんぞくぎり: 連続ヒットさせるとcount=1で2倍、count=2以上で4倍（上限）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["れんぞくぎり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]

    # 1ターン目: 命中してcount=1の揮発状態が付与される
    t.run_move(battle, 0)
    assert attacker.volatiles["れんぞくぎり"].count == 1
    t.end_turn(battle)

    # 2ターン目: count=1のため威力2倍(8192)、命中後count=2に増加する
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192
    assert attacker.volatiles["れんぞくぎり"].count == 2
    t.end_turn(battle)

    # 3ターン目: count=2以上のため威力4倍(16384、上限)になる
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 16384
    assert attacker.volatiles["れんぞくぎり"].count == 3


def test_ロッククライム_こんらんが発動する():
    """ロッククライム: 20%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ロッククライム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_ロックブラスト_複数ヒットする():
    """ロックブラスト: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("イワーク", move_names=["ロックブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_ワイドガード_シングルバトルでは相手の攻撃を防がない():
    """ワイドガード: シングルバトルでは複数対象技が存在しないため、通常通り技を使用でき、
    相手の攻撃を防ぐ効果は発生しない。
    """
    battle = t.start_battle(
        team0=[Pokemon("イワーク", move_names=["ワイドガード"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    t.run_move(battle, 0)
    defender = battle.actives[0]
    hp_before = defender.hp
    t.run_move(battle, 1)
    assert defender.hp < hp_before


def test_ワイドフォース_サイコフィールドかつ自分接地で威力1_5倍になる():
    """ワイドフォース: サイコフィールド中かつ自分が接地している場合、威力が1.5倍になる。
    さらにサイコフィールドのエスパー技1.3倍ボーナスも別枠で乗るため、
    power_modifier = 4096 * (6144/4096) * (5325/4096) = 7987。
    """
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ワイドフォース"])],
        team1=[Pokemon("カビゴン")],
        terrain=("サイコフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    # 6144(自己ボーナス) → 6144 * 5325 // 4096 = 7987(フィールドボーナス込み)
    assert battle.damage_calculator.power_modifier == 7987


def test_ワイドフォース_フィールドなしのとき威力補正なし():
    """ワイドフォース: サイコフィールドが発動していない場合、威力補正はない。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ワイドフォース"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ワイドフォース_自分が浮遊している場合は威力補正が乗らない():
    """ワイドフォース: サイコフィールド中でも自分が浮いている場合、自己ボーナス・
    フィールドボーナスのいずれも判定は自分の接地状況で行うため、どちらも乗らない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ロトム", ability_name="ふゆう", move_names=["ワイドフォース"])],
        team1=[Pokemon("カビゴン")],
        terrain=("サイコフィールド", 5),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ワイルドボルト_使用後に攻撃者が反動ダメージを受ける():
    """ワイルドボルト: 与えたダメージの1/4を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ワイルドボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_ワイルドボルト_反動ダメージが与ダメの4分の1になる():
    """ワイルドボルト: 反動量は max(1, int(与ダメ * 1/4)) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ワイルドボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/4)) = 25
    assert attacker.hp == hp_before - 25


def test_ワンダースチーム_こんらんが発動する():
    """ワンダースチーム: 20%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ワンダースチーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")
