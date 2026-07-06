"""アイテムハンドラの単体テスト"""
import math
import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_あかいいと_アイテム消費されない():
    """あかいいと: 発動しても消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="female")],
        team1=[Pokemon("カビゴン", gender="male")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "メロメロ", source=foe)
    assert mon0.has_item()
    assert mon0.item.name == "あかいいと"


def test_あかいいと_アロマベール持ちには付与されない():
    """あかいいと: 相手がアロマベールならメロメロを付与しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="female")],
        team1=[Pokemon("カビゴン", ability_name="アロマベール", gender="male")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "メロメロ", source=foe)
    assert mon0.has_volatile("メロメロ")
    assert not foe.has_volatile("メロメロ")


def test_あかいいと_どんかん持ちには付与されない():
    """あかいいと: 相手がどんかんならメロメロを付与しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="female")],
        team1=[Pokemon("カビゴン", ability_name="どんかん", gender="male")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "メロメロ", source=foe)
    assert mon0.has_volatile("メロメロ")
    assert not foe.has_volatile("メロメロ")


def test_あかいいと_メロメロ被弾で相手もメロメロ():
    """あかいいと: 持ち主がメロメロになったとき相手にもメロメロを付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="female")],
        team1=[Pokemon("カビゴン", gender="male")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "メロメロ", source=foe)
    assert mon0.has_volatile("メロメロ")
    assert foe.has_volatile("メロメロ")


def test_あかいいと_他の揮発状態では発動しない():
    """あかいいと: メロメロ以外の揮発状態では相手に付与しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="female")],
        team1=[Pokemon("カビゴン", gender="male")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "こんらん", source=foe)
    assert mon0.has_volatile("こんらん")
    assert not foe.has_volatile("メロメロ")


def test_アッキのみ_あまのじゃくによる下降はしろいきりで防げない():
    """アッキのみ: あまのじゃくで反転した下降は自発的な変化とみなされ、しろいきりでも防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゼニガメ", item_name="アッキのみ", ability_name="あまのじゃく")],
        accuracy=100,
        side1={"しろいきり": 1},
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["def"] == -1
    assert not foe.has_item()


def test_アッキのみ_ぼうぎょランクが最大のとき発動しない():
    """アッキのみ: すでにぼうぎょランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゼニガメ", item_name="アッキのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["def"] = 6
    t.run_move(battle, 0)
    assert foe.rank["def"] == 6
    assert foe.has_item()


def test_アッキのみ_物理技でB上昇():
    """アッキのみ: 物理技ダメージを受けたときぼうぎょ+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゼニガメ", item_name="アッキのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["def"] == 1
    assert not foe.has_item()


def test_あつぞこブーツ_ねばねばネット無効():
    """あつぞこブーツ: ねばねばネットによるすばやさ低下を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", item_name="あつぞこブーツ")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ねばねばネット": 1},
    )
    raichu = battle._player_states[0].team[1]
    t.run_switch(battle, 0, 1)
    assert raichu.rank["spe"] == 0


@pytest.mark.parametrize("side_name", ["ステルスロック", "まきびし", "どくびし"])
def test_あつぞこブーツ_まきびし系ハザード無効(side_name):
    """あつぞこブーツ: ステルスロック・まきびし・どくびしを無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", item_name="あつぞこブーツ")],
        team1=[Pokemon("ピカチュウ")],
        side0={side_name: 1},
    )
    raichu = battle._player_states[0].team[1]
    initial_hp = raichu.max_hp
    t.run_switch(battle, 0, 1)
    assert raichu.hp == initial_hp
    assert not raichu.ailment.is_active


def test_イアのみ_それ以外の性格ではこんらんしない():
    """イアのみ: すっぱい味が嫌いでない性格では発動してもこんらんしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="イアのみ", nature="いじっぱり")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert not mon.has_volatile("こんらん")


@pytest.mark.parametrize(
    "nature",
    ["さみしがり", "おっとり", "おとなしい", "せっかち"]
)
def test_イアのみ_ぼうぎょが上がりにくい性格でこんらんする(nature):
    """イアのみ: すっぱい味が嫌いな性格（ぼうぎょが上がりにくい）は発動と同時にこんらんする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="イアのみ", nature=nature)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_いかさまダイス_スキルリンク所持時はスキルリンクが優先される():
    """いかさまダイス: スキルリンクと併せ持つ場合、必ず最大ヒット数になる（いかさまダイスの抽選で減らない）"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ", item_name="いかさまダイス", ability_name="スキルリンク",
            move_names=["みだれひっかき"],
        )],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)  # いかさまダイス単体なら4ヒットになる乱数
    foe = battle.actives[1]
    initial_hp = foe.max_hp
    t.run_move(battle, 0)
    assert foe.hp == initial_hp - 5  # スキルリンクの最大ヒット数が優先される


def test_いかさまダイス_ヒット数4():
    """いかさまダイス: 2-5回技のヒット数を4か5に固定する（4ヒット側）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="いかさまダイス", move_names=["みだれひっかき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)  # < 0.5 → 4ヒット
    foe = battle.actives[1]
    initial_hp = foe.max_hp
    t.run_move(battle, 0)
    assert foe.hp == initial_hp - 4


def test_いかさまダイス_ヒット数5():
    """いかさまダイス: 2-5回技のヒット数を4か5に固定する（5ヒット側）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="いかさまダイス", move_names=["みだれひっかき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.9)  # >= 0.5 → 5ヒット
    foe = battle.actives[1]
    initial_hp = foe.max_hp
    t.run_move(battle, 0)
    assert foe.hp == initial_hp - 5


@pytest.mark.parametrize("move_name", ["ダブルウイング", "にどげり"])
def test_いかさまダイス_固定回数技には効果がない(move_name):
    """いかさまダイス: 2回固定などの連続技のヒット数には影響しない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", item_name="いかさまダイス", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    foe = battle.actives[1]
    initial_hp = foe.max_hp
    t.run_move(battle, 0)
    assert foe.hp == initial_hp - 2


@pytest.mark.parametrize("move_name", ["トリプルキック", "トリプルアクセル", "ネズミざん"])
def test_いかさまダイス_毎ヒット命中判定技は初回のみ判定(move_name):
    """いかさまダイス: トリプルキック等の毎ヒット命中判定技を初回ヒットのみの判定にする。
    2発目以降は本来なら外れる状況を疑似的に発生させても、判定自体が行われず全ヒットする。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", item_name="いかさまダイス", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
    )
    t.fix_damage(battle, 1)
    # 2発目以降で呼ばれたら外れる想定の命中判定（呼ばれなければヒットし続ける）
    battle.move_executor._check_hit = lambda ctx: ctx.hit_index == 1
    foe = battle.actives[1]
    initial_hp = foe.max_hp
    move = t.run_move(battle, 0)
    assert foe.hp == initial_hp - move.max_hits


def test_いのちのたま():
    """いのちのたま: 攻撃技で反動ダメージ・火力1.3倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="いのちのたま", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    attacker = battle.actives[0]
    assert attacker.hp == math.ceil(attacker.max_hp * 9/10)
    assert attacker.item.revealed
    assert battle.damage_calculator.atk_modifier == 5324


def test_いのちのたま_ちからずくの対象技では反動が発生しない():
    """いのちのたま: ちからずく所持者が追加効果ありの技を使うと反動が発生しない（威力上昇効果はそのまま）"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ニドキング", ability_name="ちからずく",
            item_name="いのちのたま", move_names=["10まんボルト"],
        )],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    assert battle.damage_calculator.atk_modifier == 5324  # 威力上昇効果は残る


def test_いのちのたま_ちからずく所持でも対象外の技なら反動が発生する():
    """いのちのたま: ちからずく所持者でも追加効果のない技を使えば通常通り反動が発生する"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ニドキング", ability_name="ちからずく",
            item_name="いのちのたま", move_names=["たいあたり"],
        )],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    attacker = battle.actives[0]
    assert attacker.hp == math.ceil(attacker.max_hp * 9/10)


def test_いのちのたま_変化技では発動しない():
    """いのちのたま: 変化技では発動しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="いのちのたま", move_names=["はねる"])],
    )
    t.run_move(battle, 0)
    assert not battle.actives[0].item.revealed


def test_いのちのたま_連続攻撃技は反動が1回だけ発生する():
    """いのちのたま: 連続攻撃技（ダブルアタック=2回固定）を使用しても反動は最後の1回のみ発生する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="いのちのたま", move_names=["ダブルアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    attacker = battle.actives[0]
    assert attacker.hp == math.ceil(attacker.max_hp * 9/10)


def test_イバンのみ_HP25以下でなければフラグが立たない():
    """HP が 25% より多い状態で減っただけではフラグは立たない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="イバンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 0
    assert mon.has_item()


def test_イバンのみ_HP25以下でフラグが立つ():
    """HP が 25% 超から 25% 以下に下がった瞬間にフラグが立ちアイテムが revealed になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="イバンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1
    assert mon.item.revealed is True
    assert mon.has_item()  # 消費は次の攻撃時


def test_イバンのみ_きんちょうかんの相手がいると消費されない():
    """イバンのみ: 相手が特性きんちょうかんを持つときはフラグが立ってもアイテムが消費されず、
    行動順も変わらない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="イバンのみ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="きんちょうかん", move_names=["たいあたり"])],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1  # フラグは立つ

    order = t.get_action_order(battle)
    assert order[0] == battle.actives[1]  # きんちょうかんの影響で通常通りピカチュウが先攻
    assert mon.has_item()  # アイテムは消費されない


def test_イバンのみ_こんらんの自傷では発動しない():
    """イバンのみ: こんらんの自傷ダメージ(reason=self_attack)でHPが1/4以下になってもフラグが
    立たない（第五世代以降の仕様）。その後、自傷以外のダメージで改めてHPが1/4以下になると
    フラグが立つ。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="イバンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")
    assert mon.hp == mon.max_hp // 4
    assert mon.item.count == 0
    assert mon.has_item(), "こんらんの自傷ダメージでアイテムが消費された"

    # HPをthreshold超に戻し、通常ダメージで改めて1/4以下に下げるとフラグが立つ
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1


def test_イバンのみ_先制で行動する():
    """イバンのみ: フラグが立った後は相手より遅くても先に行動できる。"""
    # カビゴン（遅い）にイバンのみを持たせ、ピカチュウ（速い）より先に行動することを確認
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="イバンのみ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    mon = battle.actives[0]
    # HPを25%以下にしてフラグを立てる
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1  # フラグが立っていることを確認

    # 行動順を確認: イバンのみ発動でカビゴンが先攻になるはず
    order = t.get_action_order(battle)
    assert order[0] == mon
    assert not mon.has_item()  # アイテムが消費されている


def test_イバンのみ_先制後は通常行動順になる():
    """イバンのみ: 先制発動後は通常の行動順に戻る（カビゴンが後攻）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="イバンのみ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    mon = battle.actives[0]
    # HPを25%以下にしてフラグを立てる
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)

    # 1回目: イバンのみ発動でカビゴン先攻
    order1 = t.get_action_order(battle)
    assert order1[0] == mon
    assert not mon.has_item()  # アイテム消費済み

    # 2回目: フラグが解除されてピカチュウが先攻（通常順）
    order2 = t.get_action_order(battle)
    assert order2[0] == battle.actives[1]  # ピカチュウが先攻


def test_ウイのみ_それ以外の性格ではこんらんしない():
    """ウイのみ: しぶい味が嫌いでない性格では発動してもこんらんしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ウイのみ", nature="まじめ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert not mon.has_volatile("こんらん")


@pytest.mark.parametrize(
    "nature",
    ["いじっぱり", "わんぱく", "ようき", "しんちょう"]
)
def test_ウイのみ_とくこうが上がりにくい性格でこんらんする(nature):
    """ウイのみ: しぶい味が嫌いな性格（とくこうが上がりにくい）は発動と同時にこんらんする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ウイのみ", nature=nature)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_おおきなねっこ_アクアリングの回復量増加():
    """おおきなねっこ: アクアリング状態のターン終了時回復も1.3倍になる"""
    from jpoke.utils.math import round_half_down
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="おおきなねっこ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"アクアリング": 1},
    )
    mon = battle.actives[0]
    mon.hp = 1
    heal_base = max(1, mon.max_hp // 16)
    expected_heal = round_half_down(heal_base * 5324 / 4096)
    t.end_turn(battle)
    assert mon.hp == 1 + expected_heal


def test_おおきなねっこ_ちからをすいとるの回復量増加():
    """おおきなねっこ: ちからをすいとるの回復量も1.3倍になる"""
    from jpoke.utils.math import round_half_down
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="おおきなねっこ", move_names=["ちからをすいとる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    expected_recovery = round_half_down(defender.ranked_stats["atk"] * 5324 / 4096)
    t.run_move(battle, 0)
    assert attacker.hp == 1 + expected_recovery


def test_おおきなねっこ_ねをはるの回復量増加():
    """おおきなねっこ: ねをはる状態のターン終了時回復も1.3倍になる"""
    from jpoke.utils.math import round_half_down
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="おおきなねっこ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1},
    )
    mon = battle.actives[0]
    mon.hp = 1
    heal_base = max(1, mon.max_hp // 16)
    expected_heal = round_half_down(heal_base * 5324 / 4096)
    t.end_turn(battle)
    assert mon.hp == 1 + expected_heal


def test_おおきなねっこ_やどりぎのタネで回復側が持つと回復量増加():
    """おおきなねっこ: やどりぎのタネによる回復量は、回復するポケモン自身の所持で1.3倍になる"""
    from jpoke.utils.math import round_half_down
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", item_name="おおきなねっこ")],
        volatile0={"やどりぎのタネ": 1},
    )
    from_mon, to_mon = battle.actives
    to_mon.hp = 1
    t.end_turn(battle)
    damage = from_mon.max_hp - from_mon.hp
    expected_heal = round_half_down(damage * 5324 / 4096)
    assert to_mon.hp == 1 + expected_heal


def test_おおきなねっこ_やどりぎのタネの使用者側だけが持っていても回復量は増えない():
    """おおきなねっこ: やどりぎのタネを受けている側（設置された側）だけが持っていても影響しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="おおきなねっこ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"やどりぎのタネ": 1},
    )
    from_mon, to_mon = battle.actives
    to_mon.hp = 1
    t.end_turn(battle)
    damage = from_mon.max_hp - from_mon.hp
    assert to_mon.hp == 1 + damage


def test_おおきなねっこ_吸収技の回復量の端数処理は五捨五超入かつ5324_4096倍():
    """おおきなねっこ: 端数処理は切り捨てではなく五捨五超入。正確な倍率は5324/4096倍。

    通常時の回収量32に対して、旧実装(int(32*1.3)=41 または floor(32*5325/4096)=41)
    ではなく、round_half_down(32*5324/4096)=42 になることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="おおきなねっこ", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.fix_damage(battle, 64)  # 通常回収量 = 64 * 50% = 32
    t.run_move(battle, 0)
    assert attacker.hp == 1 + 42


def test_おおきなねっこ_吸収技の回復量増加():
    """おおきなねっこ: 吸収技の回収量を1.3倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="おおきなねっこ", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.fix_damage(battle, 100)
    t.run_move(battle, 0)
    expected_hp = min(1 + 65, attacker.max_hp)  # 100 * 50% * 1.3 = 65
    assert attacker.hp == expected_hp


def test_オッカのみ_あついしぼうの影響下でも発動する():
    """オッカのみ: あついしぼうはタイプ相性を変えないため発動に影響しない"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["だいもんじ"])],
        team1=[Pokemon("フシギダネ", item_name="オッカのみ", ability_name="あついしぼう")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 8192  # 効果抜群のまま
    assert battle.damage_calculator.damage_modifier == 2048
    assert not battle.actives[1].has_item()  # 発動して消費される


def test_オッカのみ_タールショットで抜群になったほのお技でも発動する():
    """オッカのみ: タールショットの効果で抜群になったほのお技を受けたときも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", item_name="オッカのみ")],  # でんきタイプはほのお等倍
        volatile1={"タールショット": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)  # ゼニガメがひのこで攻撃
    assert battle.damage_calculator.def_type_modifier == 8192  # タールショットで効果抜群に
    assert battle.damage_calculator.damage_modifier == 2048
    assert not battle.actives[1].has_item()  # 発動して消費される


def test_オッカのみ_やきつくすを抜群で受けてもダメージが半減する():
    """オッカのみ: やきつくすを抜群で受けた場合、技の効果よりオッカのみの効果が優先されダメージを半減できる"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", move_names=["やきつくす"])],
        team1=[Pokemon("フシギダネ", item_name="オッカのみ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048
    assert not battle.actives[1].has_item()  # オッカのみの効果で消費される


def test_オボンのみ_HP50以下で回復():
    """オボンのみ: HP1/2以下になった瞬間に最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + mon.max_hp // 4
    assert not mon.has_item()


def test_オボンのみ_HP50超では発動しない():
    """オボンのみ: HPが50%より多いときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 2
    battle.modify_hp(mon, v=-1)
    assert mon.has_item()


def test_オボンのみ_かいふくふうじ中は発動せず消費されない():
    """オボンのみ: かいふくふうじ状態のときは発動せず、アイテムも消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": 3},
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2
    assert mon.has_item(), "かいふくふうじ状態でオボンのみが消費された"


def test_オボンのみ_きんちょうかんの相手がいると発動しない():
    """オボンのみ: 相手が特性きんちょうかんを持つときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ", ability_name="きんちょうかん")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2
    assert mon.has_item()


def test_オボンのみ_こんらんの自傷では発動しない():
    """オボンのみ: こんらんの自傷ダメージ(reason=self_attack)でHPが1/2以下になっても発動しない
    （第五世代以降の仕様）。その後、自傷以外のダメージを受けると発動する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")
    assert mon.hp == mon.max_hp // 2
    assert mon.has_item(), "こんらんの自傷ダメージでオボンのみが消費された"

    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 - 1 + mon.max_hp // 4
    assert not mon.has_item()


def test_オレンのみ_HP50以下で10回復():
    """オレンのみ: HP1/2以下になった瞬間に10HP回復する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="オレンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + 10
    assert not mon.has_item()


def test_オレンのみ_HP50超では発動しない():
    """オレンのみ: HPが50%より多いときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="オレンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 2
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + 1
    assert mon.has_item()


def test_おんみつマント_あくしゅうのひるみを防ぐ():
    """おんみつマント: 特性あくしゅうによるひるみ効果も防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あくしゅう", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="おんみつマント")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_おんみつマント_どくしゅのどく状態を防ぐ():
    """おんみつマント: 特性どくしゅによるどく状態も防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="おんみつマント")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name != "どく"


def test_おんみつマント_追加効果を無効化():
    """おんみつマント: 相手の技の追加効果を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="おんみつマント")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name != "まひ"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
