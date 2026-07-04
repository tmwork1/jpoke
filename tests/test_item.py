"""アイテムハンドラの単体テスト"""
import copy
import math
from typing import cast
import pytest
from jpoke import Pokemon
from jpoke.enums import Command, Interrupt
from jpoke.model import Move
from jpoke.types import Type
from . import test_utils as t

def _dummy_move(type_name: str) -> Move:
    """指定タイプの技オブジェクトを返す（たいあたりのデータをコピーしてタイプを上書き）。"""
    t_name = cast(Type, type_name)
    move = Move("たいあたり")
    move.data = copy.copy(move.data)
    move.data.type = t_name
    move.type = t_name
    return move


@pytest.mark.parametrize("item_name, stat, amount",
                         [
                             ("チイラのみ", "atk", 1),
                             ("カムラのみ", "spe", 1),
                             ("ヤタピのみ", "spa", 1),
                             ("リュガのみ", "def", 1),
                             ("ズアのみ", "spd", 1),
                         ]
                         )
def test_HP25以下でランク上昇するきのみ(item_name, stat, amount):
    """HP1/4以下になった瞬間に能力ランクを上昇させる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.rank[stat] == amount
    assert not mon.has_item()


@pytest.mark.parametrize("item_name, stat, amount",
                         [
                             ("チイラのみ", "atk", 1),
                             ("カムラのみ", "spe", 1),
                             ("ヤタピのみ", "spa", 1),
                             ("リュガのみ", "def", 1),
                             ("ズアのみ", "spd", 1),
                         ]
                         )
def test_HP25以下でランク上昇するきのみ_こんらんの自傷では発動しない(item_name, stat, amount):
    """こんらんの自傷ダメージ(reason=self_attack)でHPが1/4以下になっても発動しない
    （第五世代以降の仕様）。その後、自傷以外のダメージを受けると発動する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")
    assert mon.hp == mon.max_hp // 4
    assert mon.has_item(), "こんらんの自傷ダメージでアイテムが消費された"

    battle.modify_hp(mon, v=-1)
    assert mon.rank[stat] == amount
    assert not mon.has_item()


@pytest.mark.parametrize(
    "item_name",
    ["ウイのみ", "イアのみ", "フィラのみ", "マゴのみ", "バンジのみ"]
)
def test_HP4分の1より多いときは発動しない(item_name):
    """HP1/4以下になった瞬間に最大HPの1/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 2
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + 1
    assert mon.has_item()


@pytest.mark.parametrize(
    "item_name",
    ["ウイのみ", "イアのみ", "フィラのみ", "マゴのみ", "バンジのみ"]
)
def test_HP4分の1以下で回復するきのみ(item_name):
    """HP1/4以下になった瞬間に最大HPの1/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()


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


def test_かいがらのすず_ちからずくの対象技では回復しない():
    """かいがらのすず: ちからずく所持者が追加効果ありの技を使った場合は回復効果が無くなる"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ニドキング", ability_name="ちからずく",
            item_name="かいがらのすず", move_names=["10まんボルト"],
        )],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.fix_damage(battle, 80)
    t.run_move(battle, 0)
    assert attacker.hp == 1


def test_かいがらのすず_みがわりへの与ダメージでも回復する():
    """かいがらのすず: みがわりに阻まれた場合、みがわりへの与ダメージから回復量を算出する（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="かいがらのすず", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.hp = 1
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.fix_damage(battle, 50)
    t.run_move(battle, 0)
    assert attacker.hp == 1 + 50 // 8
    assert defender.hp == defender.max_hp


def test_かいがらのすず_与ダメージの1割8回復():
    """かいがらのすず: ダメージ技命中時に与ダメージの1/8を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="かいがらのすず", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.fix_damage(battle, 80)
    t.run_move(battle, 0)
    assert attacker.hp == 1 + 80 // 8


def test_かいがらのすず_連続攻撃技は合計ダメージから最後にまとめて回復する():
    """かいがらのすず: 連続攻撃技（ダブルアタック=2回固定）は最後のヒットの後に合計ダメージの1/8がまとめて回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="かいがらのすず", move_names=["ダブルアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.fix_damage(battle, 30)
    t.run_move(battle, 0)
    assert attacker.hp == 1 + (30 * 2) // 8


def test_かえんだま_ねむけと重なった場合ねむり優先():
    """かえんだま: ねむけからねむり状態になるターンと発動ターンが重なった場合、
    ねむけ(priority110)が先に処理されるためねむり状態が優先されやけどは付与されない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="かえんだま")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねむけ": 1},
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name == "ねむり"


def test_かえんだま_ミストフィールド解除ターンから発動():
    """かえんだま: ミストフィールドはやけどの付与を防ぐが、
    フィールドの継続終了(priority140)がかえんだまの発動(priority150)より先に処理されるため、
    ミストフィールドが解除されたそのターンからかえんだまが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="かえんだま")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", 1),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert battle.terrain.name != "ミストフィールド"
    assert mon.ailment.name == "やけど"


def test_かえんだま_発動するターンにやけどダメージは受けない():
    """かえんだま: priority150でやけどダメージ(100)より後に発動するため、
    発動したそのターンにやけどダメージは発生しない（翌ターンから発生する）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="かえんだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    hp_before = mon.hp
    t.end_turn(battle)
    assert mon.ailment.name == "やけど"
    assert mon.hp == hp_before  # このターンはやけどダメージを受けない

    t.end_turn(battle)
    assert mon.hp == hp_before - hp_before // 16  # 翌ターンからやけどダメージを受ける


def test_カゴのみ_ねむり付与直後に即時回復する():
    """カゴのみ: ねむり付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
        team1=[Pokemon("カビゴン", item_name="カゴのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert not defender.has_item()


def test_カシブのみ_ポルターガイストは成功しダメージ半減():
    """カシブのみ: ポルターガイストのアイテム所持チェックはダメージ計算より先に行われるため、
    効果バツグンで受けてもポルターガイストは成功し、カシブのみでダメージが半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ポルターガイスト"])],
        team1=[Pokemon("エーフィ", item_name="カシブのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before  # 技は成功する
    assert battle.damage_calculator.damage_modifier == 2048  # ダメージ半減
    assert not defender.has_item()  # カシブのみは消費される


def test_カムラのみ_すばやさランクが最大のとき発動しない():
    """カムラのみ: すでにすばやさランクが最大まで上がっているときはHP1/4以下でも発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="カムラのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.rank["spe"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.rank["spe"] == 6
    assert mon.has_item()


def test_からぶりほけん_すばやさランクが最大のときは発動しない():
    """からぶりほけん: すでにすばやさランクが最大(+6)のときは発動しない（アイテムも消費されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="からぶりほけん", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    mon = battle.actives[0]
    mon.rank["spe"] = 6
    t.run_move(battle, 0)
    assert mon.rank["spe"] == 6
    assert mon.has_item()


def test_からぶりほけん_一撃必殺技を外したときは発動しない():
    """からぶりほけん: 一撃必殺技を外したときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="からぶりほけん", move_names=["じわれ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["spe"] == 0
    assert mon.has_item()


def test_からぶりほけん_技が命中したときは発動しない():
    """からぶりほけん: 技が命中したときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="からぶりほけん", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["spe"] == 0
    assert mon.has_item()


def test_からぶりほけん_技が外れたときS上昇():
    """からぶりほけん: 技が外れたときすばやさ+2"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="からぶりほけん", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["spe"] == 2
    assert not mon.has_item()


def test_からぶりほけん_連続技は1発目が外れると発動する():
    """からぶりほけん: check_hit_each_time技は最初の1発が外れたときは発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", item_name="からぶりほけん", move_names=["トリプルキック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["spe"] == 2
    assert not mon.has_item()


def test_からぶりほけん_連続技は2発目以降が外れても発動しない():
    """からぶりほけん: check_hit_each_time技は最初の1発が外れたときのみ発動する。
    1発目が命中し2発目以降が外れても発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", item_name="からぶりほけん", move_names=["トリプルキック"])],
        team1=[Pokemon("カビゴン")],
    )
    battle.move_executor._check_hit = lambda ctx: ctx.hit_index == 1
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["spe"] == 0
    assert mon.has_item()


def test_かるいし_体重の最低値は0_1kg():
    """かるいし: 半減した結果0.1kgを下回る場合は0.1kgになる（ゴースは体重0.1kg）"""
    battle = t.start_battle(
        team0=[Pokemon("ゴース", item_name="かるいし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.data.weight == pytest.approx(0.1)
    assert mon.weight == pytest.approx(0.1)


def test_かるいし_体重半減():
    """かるいし: 持ち主の体重を半分にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="かるいし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.weight == pytest.approx(mon.data.weight * 0.5, abs=0.1)


def test_きあいのタスキ_一撃必殺技を耐える():
    """きあいのタスキ: 一撃必殺技のダメージもHP1で耐える。

    防御側（ピカチュウ、素早さ110）が攻撃側（カビゴン、素早さ50）より速いケースで検証する。
    かつては ha.ohko_damage と本ハンドラが同一 priority=100 で登録されており、
    ソート時のタイブレークが素早さ依存になっていたため、防御側が速いと
    一撃必殺技の確定ダメージが未設定のまま判定されて発動しない不具合があった
    （ha.ohko_damage の priority=90 化で修正、素早さに依存せず必ず発動する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのタスキ")],
        team1=[Pokemon("カビゴン", move_names=["じわれ"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp == 1
    assert not mon.has_item()


def test_きあいのタスキ_満タンからひんしにならない():
    """きあいのタスキ: HPが満タンのとき一撃ひんしダメージをHP1で耐える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのタスキ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.fix_damage(battle, mon.max_hp)
    t.run_move(battle, 1)
    assert mon.hp == 1
    assert not mon.has_item()


def test_きあいのタスキ_満タンでなければ無効():
    """きあいのタスキ: HPが満タンでないとき発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのタスキ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp - 1
    t.fix_damage(battle, mon.max_hp)
    t.run_move(battle, 1)
    assert not mon.alive


def test_きあいのハチマキ_発動しても消費されない():
    """きあいのハチマキ: きあいのタスキと異なり発動してもアイテムが消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのハチマキ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)  # < 0.1 → 発動
    t.run_move(battle, 1)
    assert mon.hp == 1
    assert mon.has_item()
    assert mon.item.name == "きあいのハチマキ"


def test_きあいのハチマキ_確率でひんしにならない():
    """きあいのハチマキ: 10%の確率でひんし以上のダメージをHP1で耐える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのハチマキ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)  # < 0.1 → 発動
    t.run_move(battle, 1)
    assert mon.hp == 1


def test_きあいのハチマキ_確率外は耐えない():
    """きあいのハチマキ: 発動しないとき耐えない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのハチマキ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.5)  # >= 0.1 → 発動しない
    t.run_move(battle, 1)
    assert mon.hp == 0


def test_きれいなぬけがら():
    """きれいなぬけがら: 交代防止無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きれいなぬけがら"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かげふみ")],
    )
    assert battle.query.can_switch(battle.players[0])


def test_きれいなぬけがら_自身のにげられない状態でも交代できる():
    """きれいなぬけがら: くろいまなざし等による自身のにげられない状態も無視して交代できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きれいなぬけがら"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"にげられない": 1},
    )
    assert battle.query.can_switch(battle.players[0])


def test_キーのみ_こんらん付与直後に即時回復する():
    """キーのみ: こんらん付与直後（ON_VOLATILE_START）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="キーのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon, "こんらん", source=foe)
    assert not mon.has_volatile("こんらん")
    assert not mon.has_item()


def test_キーのみ_ターン終了でこんらん回復():
    """キーのみ: ターン終了時にこんらんを回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="キーのみ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 3},
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.has_volatile("こんらん")
    assert not mon.has_item()


@pytest.mark.parametrize("mon_name", ["ザシアン(れきせん)", "ザシアン(けんのおう)"])
@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_くちたけん_ザシアンから奪えない(move_name, mon_name):
    """くちたけん: ザシアンが持っている間ははたきおとす・どろぼう等で奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon(mon_name, item_name="くちたけん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_item("くちたけん")


def test_くちたけん_ザシアン以外は奪われる():
    """くちたけん: ザシアン以外が持っている場合ははたきおとす等で通常通り奪われる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("カビゴン", item_name="くちたけん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.has_item()


def test_くちたけん_トリックでザシアンから奪えない():
    """くちたけん: ザシアンが持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("ザシアン(けんのおう)", item_name="くちたけん")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "くちたけん"


def test_くちたけん_れきせんのゆうしゃザシアンへ渡せない():
    """くちたけん: れきせんのゆうしゃザシアンへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="くちたけん")],
        team1=[Pokemon("ザシアン(れきせん)")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "くちたけん"
    assert not defender.has_item()
    assert defender.name == "ザシアン(れきせん)"


@pytest.mark.parametrize("mon_name", ["ザマゼンタ(れきせん)", "ザマゼンタ(たてのおう)"])
@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_くちたたて_ザマゼンタから奪えない(move_name, mon_name):
    """くちたたて: ザマゼンタが持っている間ははたきおとす・どろぼう等で奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon(mon_name, item_name="くちたたて")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_item("くちたたて")


def test_くちたたて_ザマゼンタ以外は奪われる():
    """くちたたて: ザマゼンタ以外が持っている場合ははたきおとす等で通常通り奪われる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("カビゴン", item_name="くちたたて")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.has_item()


def test_くちたたて_トリックでザマゼンタから奪えない():
    """くちたたて: ザマゼンタが持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("ザマゼンタ(たてのおう)", item_name="くちたたて")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "くちたたて"


def test_くちたたて_れきせんのゆうしゃザマゼンタへ渡せない():
    """くちたたて: れきせんのゆうしゃザマゼンタへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="くちたたて")],
        team1=[Pokemon("ザマゼンタ(れきせん)")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "くちたたて"
    assert not defender.has_item()
    assert defender.name == "ザマゼンタ(れきせん)"


@pytest.mark.parametrize(
    "item_name, mon_name, expected_name",
    [
        ("くちたけん", "ザシアン(れきせん)", "ザシアン(けんのおう)"),
        ("くちたたて", "ザマゼンタ(れきせん)", "ザマゼンタ(たてのおう)"),
    ]
)
def test_くちた系_フォルムチェンジ(item_name, mon_name, expected_name):
    """くちたけん・くちたたて: 対応ポケモンをフォルムチェンジさせる"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == expected_name


@pytest.mark.parametrize(
    "item_name",
    ["くちたけん", "くちたたて"]
)
def test_くちた系_他ポケモンは変化しない(item_name):
    """くちたけん・くちたたて: 対応ポケモン以外は変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ピカチュウ"


def test_くっつきバリ_ターン終了にダメージ():
    """くっつきバリ: ターン終了時に最大HPの1/8ダメージを受ける"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="くっつきバリ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp - mon.max_hp // 8


def test_くっつきバリ_接触技でアイテム転送():
    """くっつきバリ: 接触技で攻撃した相手がアイテムなしのとき転送する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="くっつきバリ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "くっつきバリ"
    assert not defender.has_item()


def test_くっつきバリ_攻撃者がアイテム持ちのとき転送しない():
    """くっつきバリ: 接触技でも攻撃者がアイテムを持っていれば転送しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのタスキ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="くっつきバリ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "きあいのタスキ"
    assert defender.item.name == "くっつきバリ"


def test_くっつきバリ_転送後に転送先がダメージを受ける():
    """くっつきバリ: 転送されたポケモンもターン終了時にダメージを受ける"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="くっつきバリ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.item.name == "くっつきバリ"
    t.end_turn(battle)
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 8


def test_くっつきバリ_非接触技では転送しない():
    """くっつきバリ: 非接触技では転送しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="くっつきバリ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not attacker.has_item()
    assert defender.item.name == "くっつきバリ"


def test_クラボのみ_まひ付与直後に即時回復する():
    """クラボのみ: まひ付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        team1=[Pokemon("カビゴン", item_name="クラボのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert not defender.has_item()


def test_クリアチャーム_いかくを防ぐ():
    """クリアチャーム: 相手のいかくによる能力ランク低下を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="クリアチャーム")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.rank["atk"] == 0


def test_クリアチャーム_ミラーアーマーとの併用では反射されない():
    """クリアチャーム: 特性ミラーアーマーを持っていても、クリアチャームの無効化が先に発動し反射できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー", item_name="クリアチャーム")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    assert mon.rank["atk"] == 0
    assert foe.rank["atk"] == 0


def test_クリアチャーム_自分の技の低下は防げない():
    """クリアチャーム: 自分の技によるランク低下（リーフストームのC-2）は防げない"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", item_name="クリアチャーム", move_names=["リーフストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.rank["spa"] == -2


def test_くろいてっきゅう_浮遊を無効化():
    """くろいてっきゅう: 浮遊状態を無効化してじめん技が当たる"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", ability_name="ふゆう", item_name="くろいてっきゅう")],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp < mon.max_hp


def test_くろいてっきゅう_素早さ半分():
    """くろいてっきゅう: 素早さを1/2にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="くろいてっきゅう")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    base_speed = mon.stats["spe"]
    assert battle.speed_calculator.calc_effective_speed(mon) == base_speed * 2048 // 4096


def test_くろいヘドロ_どくタイプは回復():
    """くろいヘドロ: どくタイプはターン終了時に1/16回復"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", item_name="くろいヘドロ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16


def test_くろいヘドロ_非どくタイプはダメージ():
    """くろいヘドロ: どくタイプでないときターン終了時に1/8ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="くろいヘドロ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    initial_hp = mon.max_hp
    t.end_turn(battle)
    assert mon.hp == initial_hp - initial_hp // 8


def test_くろいメガネ_イカサマでも威力補正がかかる():
    """くろいメガネ: 所有者が使用するイカサマにも威力補正がかかる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="くろいメガネ", move_names=["イカサマ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_くろいメガネ_イカサマを受けるときは補正なし():
    """くろいメガネ: 所有者がイカサマを受ける場合は補正がかからない（威力補正は攻撃側の持ち物にのみ依存）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="くろいメガネ")],
        team1=[Pokemon("ピカチュウ", move_names=["イカサマ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.damage_calculator.power_modifier == 4096


def test_グラスシード_展開済みグラスフィールドに登場して発動():
    """グラスシード: すでにグラスフィールドが展開されている場に登場（交代）してもぼうぎょ+1して消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", item_name="グラスシード")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("グラスフィールド", 5),
    )
    raichu = battle._player_states[0].team[1]
    t.run_switch(battle, 0, 1)
    assert raichu.rank["def"] == 1
    assert not raichu.has_item()


@pytest.mark.parametrize("terrain", ["エレキフィールド", "グラスフィールド", "ミストフィールド", "サイコフィールド"])
def test_グランドコート_フィールドを8ターンに延長(terrain):
    """グランドコート: 4種フィールドを展開すると持続ターンが8になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="グランドコート")],
        team1=[Pokemon("ピカチュウ")],
    )
    # グランドコート所持者をsourceとしてフィールドを展開すると8ターンに延長される
    battle.terrain_manager.apply(terrain, 5, source=battle.actives[0])
    assert battle.terrain.count == 8


def test_グランドコート_非所持ではフィールドが5ターンのまま():
    """グランドコート: 所持していない場合はフィールドは5ターンで終了する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    # グランドコートなしでフィールドを展開すると5ターンのまま
    battle.terrain_manager.apply("グラスフィールド", 5, source=battle.actives[0])
    assert battle.terrain.count == 5


def test_こうかくレンズ_命中率が1_1倍になる():
    """こうかくレンズ: 使う技の命中率が1.1倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こうかくレンズ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン")],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 4506 // 4096


def test_こうかくレンズ_非所持では命中率が変化しない():
    """こうかくレンズ: 持っていない場合は命中率が変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン")],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_こうこうのしっぽ_クイックドロウ発動時は道具の効果が無視される():
    """こうこうのしっぽ: 特性クイックドロウが発動した場合、道具の効果は無視されて先攻になる"""
    battle = t.start_battle(
        team0=[Pokemon(
            "コイル", ability_name="クイックドロウ", item_name="こうこうのしっぽ", move_names=["たいあたり"]
        )],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.fix_random(battle, 0.0)  # クイックドロウを必ず発動させる
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]  # こうこうのしっぽ所持でもクイックドロウ発動で先攻


def test_こうこうのしっぽ_行動が後になる():
    """こうこうのしっぽ: 行動順を1段階後ろにする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こうこうのしっぽ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[1]  # カビゴンが先攻


def test_こだわりスカーフ_素早さ強化():
    """こだわりスカーフ: 素早さ1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりスカーフ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    base_speed = mon.stats["spe"]
    assert battle.speed_calculator.calc_effective_speed(mon) == base_speed * 6144 // 4096


def test_こだわりハチマキ_イカサマで攻撃するときも1_5倍():
    """こだわりハチマキ: イカサマ使用時も相手の攻撃実数値を1.5倍にしてダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ", move_names=["イカサマ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_こだわりハチマキ_イカサマを受けるときは補正なし():
    """こだわりハチマキ: 所持者がイカサマを受ける場合は補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ")],
        team1=[Pokemon("ピカチュウ", move_names=["イカサマ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.damage_calculator.atk_modifier == 4096


def test_こだわりハチマキ_こんらん自傷ダメージには補正なし():
    """こだわりハチマキ: こんらんの自傷ダメージには攻撃補正がかからない（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096
    assert attacker.hp < attacker.max_hp


@pytest.mark.parametrize(
    "item_name",
    ["こだわりスカーフ", "こだわりハチマキ", "こだわりメガネ"]
)
def test_こだわり系_交代でロック解除(item_name):
    """こだわり系アイテム: 交代するとこだわりロックが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("こだわり")


@pytest.mark.parametrize(
    "item_name",
    ["こだわりスカーフ", "こだわりハチマキ", "こだわりメガネ"]
)
def test_こだわり系_技ロック(item_name):
    """こだわり系アイテム: 技使用後にこだわりロック"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    assert mon.volatiles["こだわり"].move_name == "たいあたり"


@pytest.mark.parametrize("item_name, move_name, expected", [
    ("こだわりハチマキ", "たいあたり", 6144),
    ("こだわりハチマキ", "でんきショック", 4096),
    ("こだわりメガネ", "たいあたり", 4096),
    ("こだわりメガネ", "でんきショック", 6144),
])
def test_こだわり系_火力補正(item_name, move_name, expected):
    """こだわり系アイテム: 物理・特殊技それぞれの攻撃補正"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == expected


def test_こんごうだま_ディアルガ以外が持っても効果がない():
    """こんごうだま: ディアルガ以外が持っていてもドラゴン・はがね技に補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="こんごうだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_こんごうだま_なげつけるで威力60になる():
    """こんごうだま: 通常の道具でありなげつけるで使用でき、威力60でダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="こんごうだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_こんごうだま_対象外タイプの技には効果がない():
    """こんごうだま: ディアルガが持っていてもドラゴン・はがね以外の技には補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", item_name="こんごうだま", move_names=["はかいこうせん"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize("ability_name", ["さめはだ", "てつのトゲ"])
def test_ゴツゴツメット_さめはだ等特性と併用すると合計ダメージになる(ability_name):
    """ゴツゴツメット: さめはだ/てつのトゲと併用すると特性ダメージの後にアイテムダメージが発生し、
    合計で最大HPの7/24分のダメージとなる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name=ability_name, item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    ability_chip = min(-1, int(max_hp * -(1 / 8)))
    item_chip = min(-1, int(max_hp * -(1 / 6)))
    t.run_move(battle, 0)
    assert attacker.hp == max_hp + ability_chip + item_chip


def test_ゴツゴツメット_マジックガードには発動しない():
    """ゴツゴツメット: 攻撃してきた相手がマジックガード持ちの場合はダメージを与えない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"], ability_name="マジックガード")],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ゴツゴツメット_接触攻撃で反撃ダメージ():
    """ゴツゴツメット: 接触技で攻撃してきた相手に1/6ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 6


def test_ゴツゴツメット_攻撃側のみがわりを貫通してダメージを与える():
    """ゴツゴツメット: 攻撃側がみがわり状態でも、みがわりを貫通して本体にダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "みがわり", hp=100)
    hp_before = attacker.hp
    expected_chip = min(-1, int(attacker.max_hp * -(1 / 6)))
    t.run_move(battle, 0)
    assert attacker.hp == hp_before + expected_chip


def test_ゴツゴツメット_自分のみがわりで防いだときは発動しない():
    """ゴツゴツメット: 自身がみがわり状態で攻撃を防いだときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=100)
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ゴツゴツメット_連続攻撃技ではヒットごとに発動する():
    """ゴツゴツメット: 連続攻撃技を受けた場合、1発ダメージを受けるたびに発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ダブルアタック"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    single_chip = min(-1, int(max_hp * -(1 / 6)))
    t.run_move(battle, 0)
    assert attacker.hp == max_hp + single_chip * 2


def test_ゴツゴツメット_非接触技では発動しない():
    """ゴツゴツメット: 非接触技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    initial_hp = attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == initial_hp


def test_サイコシード_展開済みサイコフィールドに登場して発動():
    """サイコシード: すでにサイコフィールドが展開されている場に登場（交代）してもとくぼう+1して消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", item_name="サイコシード")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", 5),
    )
    raichu = battle._player_states[0].team[1]
    t.run_switch(battle, 0, 1)
    assert raichu.rank["spd"] == 1
    assert not raichu.has_item()


def test_サンのみ_HP25以下できゅうしょアップ状態():
    """サンのみ: HP1/4以下になった瞬間にきゅうしょアップ状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="サンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.has_volatile("きゅうしょアップ")
    assert not mon.has_item()


def test_サンのみ_すでにきゅうしょアップ状態のときは発動しない():
    """サンのみ: すでにきゅうしょアップ状態のときはHPが1/4以下でも発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="サンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "きゅうしょアップ", count=2)
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.has_item()


def test_サンのみ_ほおばるでHPに関わらず発動する():
    """サンのみ: ほおばるで消費するときは残りHPに関わらず発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="サンのみ", move_names=["ほおばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp
    t.run_move(battle, 0)
    assert mon.has_volatile("きゅうしょアップ")
    assert not mon.has_item()


def test_しめつけバンド_バインドダメージ増加():
    """しめつけバンド: バインドダメージを最大HPの1/6に増加する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="しめつけバンド", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    hp_before = foe.hp
    t.end_turn(battle)
    assert foe.hp == hp_before - foe.max_hp // 6


def test_しめつけバンド_付与後の入手では増加しない():
    """しめつけバンド: バインド付与後に入手してもダメージ倍率は増加しない（付与時に確定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    t.change_item(battle, mon, "しめつけバンド")
    hp_before = foe.hp
    t.end_turn(battle)
    assert foe.hp == hp_before - foe.max_hp // 8


def test_しめつけバンド_付与後の喪失では減少しない():
    """しめつけバンド: バインド付与後にアイテムを失ってもダメージ倍率は減少しない（付与時に確定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="しめつけバンド", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    t.change_item(battle, mon, "")
    hp_before = foe.hp
    t.end_turn(battle)
    assert foe.hp == hp_before - foe.max_hp // 6


def test_しらたま_なげつけるで威力60になる():
    """しらたま: 通常の道具でありなげつけるで使用でき、威力60でダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="しらたま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_しらたま_パルキア以外が持っても効果がない():
    """しらたま: パルキア以外が持っていてもドラゴン・みず技に補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", item_name="しらたま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_しらたま_対象外タイプの技には効果がない():
    """しらたま: パルキアが持っていてもドラゴン・みず以外の技には補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="しらたま", move_names=["はかいこうせん"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_しろいハーブ_2回目の能力低下はキャンセルされない():
    """しろいハーブ: 1回消費後は能力低下をキャンセルしない"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", item_name="しろいハーブ", move_names=["リーフストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    t.run_move(battle, 0)
    assert mon.rank["spa"] == -2


def test_しろいハーブ_すでに能力が下がっている状態でアイテムを入手すると即座にリセットする():
    """しろいハーブ: 既に能力が下がっている状態でアイテムを入手すると即座に発動する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.rank["atk"] = -2
    t.change_item(battle, mon, "しろいハーブ")
    assert mon.rank["atk"] == 0
    assert not mon.has_item()


def test_しろいハーブ_なげつけると相手の下がった能力をリセットする():
    """しろいハーブ: なげつけるで相手に投げつけると相手の下がった能力ランクをリセットする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="しろいハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    foe.rank["atk"] = -2
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 0
    assert not attacker.has_item()


def test_しろいハーブ_バトンタッチで引き継いだ下降ランクを場に出た瞬間にリセットする():
    """しろいハーブ: バトンタッチで下がった能力を引き継いだ場合、場に出た瞬間に発動する"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["バトンタッチ"]),
            Pokemon("ライチュウ", item_name="しろいハーブ"),
        ],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = -2

    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.rank["atk"] == 0
    assert not new_mon.has_item()


def test_しろいハーブ_能力低下を1度だけキャンセル():
    """しろいハーブ: 自分の技による能力低下を最初の1回キャンセルする"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", item_name="しろいハーブ", move_names=["リーフストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["spa"] == 0
    assert not mon.has_item()


def test_しんかのきせき_未進化ポケモンの防御1_5倍():
    """しんかのきせき: 未進化ポケモンのぼうぎょ・とくぼうを1.5倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゼニガメ", item_name="しんかのきせき")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 6144


def test_じゃくてんほけん_ACランク共に最大のとき発動しない():
    """じゃくてんほけん: こうげき・とくこうランクが共に最大のときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["atk"] = 6
    foe.rank["spa"] = 6
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 6
    assert foe.rank["spa"] == 6
    assert foe.has_item()


def test_じゃくてんほけん_ダメージ固定技では発動しない():
    """じゃくてんほけん: タイプ相性上は弱点でもダメージ固定技（一撃必殺技を除く）では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ちきゅうなげ"])],
        team1=[Pokemon("カビゴン", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 0
    assert foe.rank["spa"] == 0
    assert foe.has_item()


def test_じゃくてんほけん_まもるで防いだ場合は発動しない():
    """じゃくてんほけん: まもるでダメージを無効化された場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="じゃくてんほけん")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 0
    assert foe.rank["spa"] == 0
    assert foe.has_item()


def test_じゃくてんほけん_みがわりで防いだ場合は発動しない():
    """じゃくてんほけん: みがわりで攻撃を防いだ場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="じゃくてんほけん")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 0
    assert foe.rank["spa"] == 0
    assert foe.has_item()


def test_じゃくてんほけん_一撃必殺技を耐えたときは発動する():
    """じゃくてんほけん: 弱点タイプの一撃必殺技をこらえるで耐えた場合は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ゴース", move_names=["じわれ"])],
        team1=[Pokemon("ピカチュウ", item_name="じゃくてんほけん")],
        volatile1={"こらえる": 1},
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp == 1
    assert foe.rank["atk"] == 2
    assert foe.rank["spa"] == 2
    assert not foe.has_item()


def test_じゃくてんほけん_効果抜群でAC上昇():
    """じゃくてんほけん: 効果抜群の攻撃を受けたときA・C+2"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 2
    assert foe.rank["spa"] == 2
    assert not foe.has_item()


def test_じゃくてんほけん_片方のランクのみ最大のときもう片方が上昇する():
    """じゃくてんほけん: 片方のランクのみ最大の場合はもう片方だけ上昇し、アイテムは消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["atk"] = 6
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 6
    assert foe.rank["spa"] == 2
    assert not foe.has_item()


def test_じゃくてんほけん_等倍では発動しない():
    """じゃくてんほけん: 等倍の攻撃では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 0
    assert foe.has_item()


def test_ジャポのみ_マジシャンより先に発動して奪われない():
    """ジャポのみ: 特性マジシャンの物理技を受けても、ジャポのみが先に発動して消費されるため奪われない
    （攻撃側の素早さが防御側より高い場合でも、素早さに依存せずジャポのみが先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ジャポのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.hp < attacker.max_hp
    assert not foe.has_item()
    assert not attacker.has_item()


def test_ジャポのみ_マジックガードには発動しない():
    """ジャポのみ: 攻撃してきた相手がマジックガード持ちの場合はダメージを与えず消費もされない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"], ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ", item_name="ジャポのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp
    assert battle.actives[1].has_item()


def test_ジャポのみ_物理被弾で攻撃者にダメージ():
    """ジャポのみ: 物理技でダメージを受けたとき攻撃者に最大HPの1/8ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="ジャポのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 8
    assert not battle.actives[1].has_item()


def test_ジャポのみ_特殊技では発動しない():
    """ジャポのみ: 特殊技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="ジャポのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_じゅうでんち_あまのじゃくでAランクが最小のとき発動しない():
    """じゅうでんち: あまのじゃく所持者はこうげきランクがすでに最小のとき発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["atk"] = -6
    t.run_move(battle, 0)
    assert foe.rank["atk"] == -6
    assert foe.has_item()


def test_じゅうでんち_あまのじゃくでA下降():
    """じゅうでんち: あまのじゃく所持者はこうげきが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == -1
    assert not foe.has_item()


def test_じゅうでんち_かたやぶりの電気技はたんじゅん・あまのじゃくでもA上昇():
    """じゅうでんち: かたやぶりの効果があるでんき技に対してはたんじゅん・あまのじゃくは発動せず通常通り+1される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 1
    assert not foe.has_item()


def test_じゅうでんち_こうげきランクが最大のとき発動しない():
    """じゅうでんち: すでにこうげきランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["atk"] = 6
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 6
    assert foe.has_item()


def test_じゅうでんち_たんじゅんでA2段階上昇():
    """じゅうでんち: たんじゅん所持者はこうげきが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち", ability_name="たんじゅん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 2
    assert not foe.has_item()


def test_じゅうでんち_でんき以外では発動しない():
    """じゅうでんち: でんき以外の技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="じゅうでんち")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 0
    assert foe.has_item()


def test_じゅうでんち_でんき被弾でA上昇():
    """じゅうでんち: でんき技でダメージを受けたときこうげき+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 1
    assert not foe.has_item()


def test_スターのみ_HP25以下でランダム能力上昇():
    """スターのみ: HP1/4以下になった瞬間にランダムな能力+2"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="スターのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.random.choice = lambda seq: seq[0]  # A が選ばれる
    battle.modify_hp(mon, v=-1)
    assert mon.rank["atk"] == 2
    assert not mon.has_item()


def test_スターのみ_こんらんの自傷では発動しない():
    """スターのみ: こんらんの自傷ダメージ(reason=self_attack)でHPが1/4以下になっても発動しない
    （第五世代以降の仕様）。その後、自傷以外のダメージを受けると発動する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="スターのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")
    assert mon.hp == mon.max_hp // 4
    assert mon.has_item(), "こんらんの自傷ダメージでスターのみが消費された"

    battle.random.choice = lambda seq: seq[0]  # A が選ばれる
    battle.modify_hp(mon, v=-1)
    assert mon.rank["atk"] == 2
    assert not mon.has_item()


def test_スターのみ_すでに最大のランクは選ばれない():
    """スターのみ: ランクが最大(+6)の能力は選択候補から除外される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="スターのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd"):
        mon.rank[stat] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.random.choice = lambda seq: seq[0]  # 候補が1つ（すばやさ）のみになる
    battle.modify_hp(mon, v=-1)
    assert mon.rank["spe"] == 2
    assert not mon.has_item()


def test_スターのみ_ほおばるでHPに関わらず発動する():
    """スターのみ: ほおばるで消費するときは残りHPに関わらず発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="スターのみ", move_names=["ほおばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp
    battle.random.choice = lambda seq: seq[0]  # A が選ばれる
    t.run_move(battle, 0)
    assert mon.rank["atk"] == 2
    assert not mon.has_item()


def test_スターのみ_全ての能力が最大なら発動しない():
    """スターのみ: 5箇所の能力全てがすでに最大になっているときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="スターのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd", "spe"):
        mon.rank[stat] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert all(mon.rank[stat] == 6 for stat in ("atk", "def", "spa", "spd", "spe"))
    assert mon.has_item()


def test_するどいツメ_急所ランク加算():
    """するどいツメ: 急所ランクを+1する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="するどいツメ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 急所が出ない程度に固定（0.5 < 急所ランク+1の閾値以下）
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 1


def test_ズアのみ_とくぼうランクが最大のとき発動しない():
    """ズアのみ: すでにとくぼうランクが最大まで上がっているときはHP1/4以下でも発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ズアのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.rank["spd"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.rank["spd"] == 6
    assert mon.has_item()


def test_せいれいプレート_なげつけるで威力90になる():
    """せいれいプレート: なげつけるで使用すると威力90になる（フェアリー以外の技のためタイプ補正は乗らない）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="せいれいプレート", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 90
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_せんせいのツメ_きんしのちからでも攻撃技選択時は発動する():
    """せんせいのツメ: 所有者の特性がきんしのちからでも攻撃技を選んだ場合は発動し得る"""
    battle = t.start_battle(
        team0=[Pokemon(
            "カビゴン", ability_name="きんしのちから", item_name="せんせいのツメ",
            move_names=["たいあたり"],
        )],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.fix_random(battle, 0.0)  # < 0.2 → 先制
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]  # カビゴンが先攻


def test_せんせいのツメ_きんしのちからで変化技選択時は発動しない():
    """せんせいのツメ: 所有者の特性がきんしのちからで変化技を選んだ場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon(
            "カビゴン", ability_name="きんしのちから", item_name="せんせいのツメ",
            move_names=["なきごえ"],
        )],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.fix_random(battle, 0.0)  # 発動条件を満たしても無効
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]  # カビゴンは変化技選択できんしのちからにより最後に行動


def test_せんせいのツメ_先制確率で先攻():
    """せんせいのツメ: 20%の確率で行動順が1段階早くなる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="せんせいのツメ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.fix_random(battle, 0.0)  # < 0.2 → 先制
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]  # カビゴンが先攻


def test_せんせいのツメ_非発動時は通常の順番():
    """せんせいのツメ: 発動しないとき通常の行動順"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="せんせいのツメ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.fix_random(battle, 0.5)  # >= 0.2 → 発動しない
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[1]  # ピカチュウが先攻（素早さ優位）


@pytest.mark.parametrize("item_name, type_name, defender_name", [
    ("リンドのみ", "くさ", "ゼニガメ"),
    ("オッカのみ", "ほのお", "フシギダネ"),
    ("イトケのみ", "みず", "ヒトカゲ"),
    ("ソクノのみ", "でんき", "ゼニガメ"),
    ("カシブのみ", "ゴースト", "エーフィ"),
    ("ヨロギのみ", "いわ", "ヒトカゲ"),
    ("タンガのみ", "むし", "エーフィ"),
    ("ウタンのみ", "エスパー", "コジョフー"),
    ("バコウのみ", "ひこう", "コジョフー"),
    ("シュカのみ", "じめん", "ピカチュウ"),
    ("ビアーのみ", "どく", "プリン"),
    ("ヨプのみ", "かくとう", "カビゴン"),
    ("ヤチェのみ", "こおり", "ミニリュウ"),
    ("リリバのみ", "はがね", "ピッピ"),
    ("ナモのみ", "あく", "エーフィ"),
    ("ハバンのみ", "ドラゴン", "ミニリュウ"),
    ("ロゼルのみ", "フェアリー", "ミニリュウ"),
])
def test_タイプ半減実(item_name, type_name, defender_name):
    """タイプ半減実: 対応タイプの弱点ダメージを半減して消費する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon(defender_name, item_name=item_name)],
    )
    battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048
    assert not battle.actives[1].has_item()  # 1度使うと消費される


@pytest.mark.parametrize("item_name, type_name", [
    ("かたいいし", "いわ"),
    ("きせきのたね", "くさ"),
    ("ぎんのこな", "むし"),
    ("くろいメガネ", "あく"),
    ("くろおび", "かくとう"),
    ("じしゃく", "でんき"),
    ("シルクのスカーフ", "ノーマル"),
    ("しんぴのしずく", "みず"),
    ("するどいくちばし", "ひこう"),
    ("せいれいプレート", "フェアリー"),
    ("どくバリ", "どく"),
    ("とけないこおり", "こおり"),
    ("のろいのおふだ", "ゴースト"),
    ("まがったスプーン", "エスパー"),
    ("メタルコート", "はがね"),
    ("もくたん", "ほのお"),
    ("やわらかいすな", "じめん"),
    ("ようせいのハネ", "フェアリー"),
    ("りゅうのキバ", "ドラゴン"),
])
def test_タイプ強化アイテム(item_name, type_name):
    """タイプ強化アイテム: 対応タイプの威力補正"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_たつじんのおび_効果抜群で1_2倍():
    """たつじんのおび: 効果抜群技の威力を1.2倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たつじんのおび", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4915


def test_たつじんのおび_等倍では補正なし():
    """たつじんのおび: 等倍の技では補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たつじんのおび", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096


def test_たべのこし():
    """たべのこし: ターン終了時回復"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    mon = battle.actives[0]
    # HPが満タンのときは回復しない
    t.end_turn(battle)
    battle.print_logs()
    assert not mon.item.revealed

    mon.hp = 1  # テスト用に内部変数を直接変更
    t.end_turn(battle)
    assert mon.item.revealed
    assert mon.hp == 1 + mon.max_hp // 16


def test_たべのこし_かいふくふうじ中は回復しない():
    """たべのこし: かいふくふうじ状態のときは回復しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="たべのこし")],
        volatile0={"かいふくふうじ": 1},
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_タラプのみ_あまのじゃくによる下降はしろいきりで防げない():
    """タラプのみ: あまのじゃくで反転した下降は自発的な変化とみなされ、しろいきりでも防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="タラプのみ", ability_name="あまのじゃく")],
        accuracy=100,
        side1={"しろいきり": 1},
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == -1
    assert not foe.has_item()


def test_タラプのみ_ちからずくの対象技では発動しない():
    """タラプのみ: ちからずく所持者が追加効果ありの特殊技を使った場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ニドキング", ability_name="ちからずく",
            move_names=["でんきショック"],
        )],
        team1=[Pokemon("ゼニガメ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 0
    assert foe.has_item()


def test_タラプのみ_とくぼうランクが最大のとき発動しない():
    """タラプのみ: すでにとくぼうランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["spd"] = 6
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 6
    assert foe.has_item()


def test_タラプのみ_物理技では発動しない():
    """タラプのみ: 物理技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 0


def test_タラプのみ_特殊技被弾でD上昇():
    """タラプのみ: 特殊技でダメージを受けたときとくぼう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 1
    assert not foe.has_item()


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_だいこんごうだま_ディアルガから奪えない(move_name):
    """だいこんごうだま: ディアルガ(オリジン)が持っている間ははたきおとす・どろぼう等で奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ディアルガ", item_name="だいこんごうだま")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_item("だいこんごうだま")


def test_だいこんごうだま_トリックで交換されない():
    """だいこんごうだま: ディアルガ(オリジン)が持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("ディアルガ", item_name="だいこんごうだま")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "だいこんごうだま"


def test_だいこんごうだま_フォルムチェンジ():
    """だいこんごうだま: ディアルガが持って登場するとオリジンフォルムになる"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", item_name="だいこんごうだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ディアルガ(オリジン)"


def test_だいこんごうだま_通常のディアルガへ渡せない():
    """だいこんごうだま: 通常の姿のディアルガへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="だいこんごうだま")],
        team1=[Pokemon("ディアルガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "だいこんごうだま"
    assert not defender.has_item()
    assert defender.name == "ディアルガ"


def test_だいしらたま_トリックで交換されない():
    """だいしらたま: パルキア(オリジン)が持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("パルキア", item_name="だいしらたま")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "だいしらたま"


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_だいしらたま_パルキアから奪えない(move_name):
    """だいしらたま: パルキア(オリジン)が持っている間ははたきおとす・どろぼう等で奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("パルキア", item_name="だいしらたま")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_item("だいしらたま")


def test_だいしらたま_フォルムチェンジ():
    """だいしらたま: パルキアが持って登場するとオリジンフォルムになる"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="だいしらたま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "パルキア(オリジン)"


def test_だいしらたま_通常のパルキアへ渡せない():
    """だいしらたま: 通常の姿のパルキアへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="だいしらたま")],
        team1=[Pokemon("パルキア")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "だいしらたま"
    assert not defender.has_item()
    assert defender.name == "パルキア"


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_だいはっきんだま_ギラティナから奪えない(move_name):
    """だいはっきんだま: ギラティナ(オリジン)が持っている間ははたきおとす・どろぼう等で奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ギラティナ(アナザー)", item_name="だいはっきんだま")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_item("だいはっきんだま")


def test_だいはっきんだま_トリックで交換されない():
    """だいはっきんだま: ギラティナ(オリジン)が持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("ギラティナ(アナザー)", item_name="だいはっきんだま")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "だいはっきんだま"


def test_だいはっきんだま_フォルムチェンジ():
    """だいはっきんだま: ギラティナ(アナザー)が持って登場するとオリジンフォルムになる"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(アナザー)", item_name="だいはっきんだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ギラティナ(オリジン)"


def test_だいはっきんだま_通常のギラティナへ渡せない():
    """だいはっきんだま: アナザーフォルムのギラティナへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="だいはっきんだま")],
        team1=[Pokemon("ギラティナ(アナザー)")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "だいはっきんだま"
    assert not defender.has_item()
    assert defender.name == "ギラティナ(アナザー)"


def test_だっしゅつパック_0ターン目にいかくで交代():
    """だっしゅつパック: 能力ダウンで交代"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    ejected_mon = state.team[0]
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_すばやさが一番高いポケモンのみ発動する():
    """だっしゅつパック: 複数のポケモンが同時にランクを下げられた場合、すばやさが一番高いポケモンのみ発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いかく", item_name="だっしゅつパック", nature="ようき"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", ability_name="いかく", item_name="だっしゅつパック"), Pokemon("ゲンガー")],
    )
    state0 = battle._player_states[0]
    state1 = battle._player_states[1]
    # ピカチュウ（すばやさが高い）のだっしゅつパックのみ発動して交代する
    assert state0.active_index == 1
    assert not state0.team[0].has_item()
    # カビゴン（すばやさが低い）は場に残り、だっしゅつパックも消費されない
    assert state1.active_index == 0
    assert state1.team[0].has_item("だっしゅつパック")
    assert state1.team[0].rank["atk"] == -1


def test_だっしゅつパック_とらわれ状態でも交代できる():
    """だっしゅつパック: ねをはるなどのとらわれ状態を無視して発動する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="だっしゅつパック", move_names=["ねをはる"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", move_names=["Gのちから"])],
        accuracy=100,
    )
    battle.step()
    state0 = battle._player_states[0]
    ejected_mon = state0.team[0]
    assert state0.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_バトンタッチで引き継いだランクでは発動しない():
    """だっしゅつパック: バトンタッチで引き継いだランク低下では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ", item_name="だっしゅつパック")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].rank["atk"] == -1
    battle.step()
    state0 = battle._player_states[0]
    new_mon = state0.team[1]
    assert state0.active_index == 1
    assert new_mon.rank["atk"] == -1
    assert new_mon.has_item("だっしゅつパック")


def test_だっしゅつパック_まけんきで直後にランクを打ち消しても発動する():
    """だっしゅつパック: まけんきで下がったランクを直後に打ち消した場合も発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="まけんき", item_name="だっしゅつパック"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    ejected_mon = state.team[0]
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_ミラーアーマーで跳ね返しても発動する():
    """だっしゅつパック: ミラーアーマーで能力低下を跳ね返した場合でも、実際のランクは変化しないが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ミラーアーマー", item_name="だっしゅつパック"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    ejected_mon = state.team[0]
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()
    assert ejected_mon.rank["atk"] == 0


def test_だっしゅつパック_ランクが下限に達しなくても発動する():
    """だっしゅつパック: +2から+1になるなど、ランクがマイナスにならなかった場合でも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["Gのちから"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつパック"), Pokemon("イーブイ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"def": 2})
    assert defender.rank["def"] == 2
    battle.step()
    state1 = battle._player_states[1]
    ejected_mon = state1.team[0]
    # ランクが-1にならず+2→+1になっただけでも発動する
    assert state1.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_わるいてぐせに奪われた場合は発動しない():
    """だっしゅつパック: 自分の能力を下げる直接攻撃でわるいてぐせに奪われた場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="だっしゅつパック", move_names=["アームハンマー"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
        accuracy=100,
    )
    battle.step()
    state0 = battle._player_states[0]
    mon = state0.team[0]
    assert state0.active_index == 0
    assert not mon.has_item()
    assert battle._player_states[1].team[0].has_item("だっしゅつパック")


def test_だっしゅつパック_交代できるポケモンがいないときは発動しない():
    """だっしゅつパック: 交代できる残りポケモンがいないときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    mon = state.team[0]
    assert state.active_index == 0
    assert not mon.item.revealed
    assert mon.has_item()


def test_だっしゅつパック_能力上昇では発動しない():
    """だっしゅつパック: 能力上昇では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック", move_names=["つるぎのまい"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    state = battle._player_states[0]
    mon = state.team[0]
    assert state.active_index == 0
    assert not mon.item.revealed
    assert mon.has_item()


def test_だっしゅつパック_自分の技の自傷効果でも発動する():
    """だっしゅつパック: 自分の技で能力が下がった場合も発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック", move_names=["アーマーキャノン"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.step()
    state0 = battle._player_states[0]
    ejected_mon = state0.team[0]
    assert state0.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつボタン():
    """だっしゅつボタン: ダメージを受けて交代"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    player = battle.players[0]
    state = battle._player_states[0]
    ejected_mon = battle.actives[0]
    battle.step()
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつボタン_こらえるでHP1のまま耐えたときも発動する():
    """だっしゅつボタン: こらえるでHP1のまま耐えた（実ダメージ0）ときも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)

    battle.step()

    state1 = battle._player_states[1]
    assert defender.hp == 1
    assert not defender.fainted
    assert state1.active_index == 1
    assert defender.item.revealed
    assert not defender.has_item()


def test_だっしゅつボタン_ちからずくの効果が発動した技を受けたときは発動しない():
    """だっしゅつボタン: 特性ちからずくの効果が発動した追加効果あり技を受けたときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ニドキング", ability_name="ちからずく", move_names=["Gのちから"])],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    battle.step()
    state1 = battle._player_states[1]
    defender = state1.team[0]
    assert state1.active_index == 0
    assert defender.has_item("だっしゅつボタン")


def test_だっしゅつボタン_とらわれ状態でも交代できる():
    """だっしゅつボタン: ねをはるなどのとらわれ状態を無視して発動する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="だっしゅつボタン", move_names=["ねをはる"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", move_names=["Gのちから"])],
        accuracy=100,
    )
    battle.step()
    state0 = battle._player_states[0]
    ejected_mon = state0.team[0]
    assert state0.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつボタン_ばけのかわで肩代わりしたときも発動する():
    """だっしゅつボタン: 特性ばけのかわでダメージを肩代わりした場合（実ダメージ0）でも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.fix_damage(battle, 30)

    battle.step()

    state1 = battle._player_states[1]
    assert defender.ability.enabled is False
    assert state1.active_index == 1
    assert defender.item.revealed
    assert not defender.has_item()


def test_だっしゅつボタン_ひんしになったときは発動しない():
    """だっしゅつボタン: 相手の攻撃でひんしになったときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じしん"])],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    fainted_mon = battle.actives[1]
    t.fix_damage(battle, 9999)

    battle.step()

    state1 = battle._player_states[1]
    assert fainted_mon.fainted
    assert state1.active_index == 1
    assert fainted_mon.has_item("だっしゅつボタン")


def test_だっしゅつボタン_みがわりに阻まれたときは発動しない():
    """だっしゅつボタン: みがわりに攻撃を防がれたとき（実ダメージ0）は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)

    battle.step()

    state1 = battle._player_states[1]
    assert state1.active_index == 0
    assert defender.has_item("だっしゅつボタン")


def test_だっしゅつボタン_控えがいないと発動しない():
    """だっしゅつボタン: 交代先の控えがいないときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつボタン")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.step()
    state0 = battle._player_states[0]
    assert state0.active_index == 0
    assert mon.has_item("だっしゅつボタン")


def test_チイラのみ_こうげきランクが最大のとき発動しない():
    """チイラのみ: すでにこうげきランクが最大まで上がっているときはHP1/4以下でも発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="チイラのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.rank["atk"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.rank["atk"] == 6
    assert mon.has_item()


def test_ちからのハチマキ_物理技1_1倍():
    """ちからのハチマキ: 物理技の威力を1.1倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ちからのハチマキ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4505


def test_ちからのハチマキ_特殊技には補正なし():
    """ちからのハチマキ: 特殊技には補正しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ちからのハチマキ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_チーゴのみ_やけど付与直後に即時回復する():
    """チーゴのみ: やけど付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("カビゴン", item_name="チーゴのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert not defender.has_item()


def test_でんきだま_こんらん自傷ダメージには補正なし():
    """でんきだま: こんらんの自傷ダメージには攻撃補正がかからない（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="でんきだま")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096
    assert attacker.hp < attacker.max_hp


@pytest.mark.parametrize("mon_name", ["ピチュー", "ライチュウ"])
def test_でんきだま_ピチューライチュウには効果なし(mon_name):
    """でんきだま: ピチュー・ライチュウが持っても攻撃補正はかからない"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name="でんきだま", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_とくせいガード_かたやぶりによる特性無効化をブロック():
    """とくせいガード: add_disabled_reasonによる特性無効化をブロックする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", item_name="とくせいガード")],
    )
    defender = battle.actives[1]
    result = battle.add_ability_disabled_reason(defender, "かたやぶり")
    assert not result
    assert defender.ability.enabled


def test_とくせいガード_かたやぶりによる特性無効化をブロックした際にアイテムが公開される():
    """とくせいガード: 特性無効化をブロックした際にアイテムが公開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", item_name="とくせいガード")],
    )
    defender = battle.actives[1]
    assert not defender.item.revealed
    battle.add_ability_disabled_reason(defender, "かたやぶり")
    assert defender.item.revealed


def test_とくせいガード_シンプルビームによる特性変更をブロック():
    """とくせいガード: 所持者に対するシンプルビームは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シンプルビーム"])],
        team1=[Pokemon("カビゴン", ability_name="せいでんき", item_name="とくせいガード")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ability.name == "せいでんき"


def test_とくせいガード_スキルスワップによる特性変更をブロック():
    """とくせいガード: 所持者に対するスキルスワップ、または所持者が使用するスキルスワップは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", ability_name="めんえき", item_name="とくせいガード")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は入れ替わらない
    assert attacker.ability.name == "せいでんき"
    assert defender.ability.name == "めんえき"


def test_とくせいガード_トレースによる特性コピーをブロック():
    """とくせいガード: 所持者のトレースは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="トレース", item_name="とくせいガード")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    tracer = battle.actives[0]
    assert tracer.ability.base_name == "トレース"


def test_とくせいガード_なかまづくりによる特性変更をブロック():
    """とくせいガード: 所持者に対するなかまづくりは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なかまづくり"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", ability_name="あついしぼう", item_name="とくせいガード")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ability.name == "あついしぼう"


def test_とくせいガード_なしの場合は特性が無効化される():
    """とくせいガード: 持っていない場合はかたやぶりで特性が無効化される（対照テスト）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    result = battle.add_ability_disabled_reason(defender, "かたやぶり")
    assert result
    assert not defender.ability.enabled


def test_とくせいガード_なやみのタネによる特性変更をブロック():
    """とくせいガード: 所持者に対するなやみのタネは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なやみのタネ"])],
        team1=[Pokemon("カビゴン", ability_name="せいでんき", item_name="とくせいガード")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ability.name == "せいでんき"


def test_とくせいガード_なりきりによる特性変更をブロック():
    """とくせいガード: 所持者はなりきりを使用して自分の特性を変えることもできない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なりきり"], ability_name="せいでんき", item_name="とくせいガード")],
        team1=[Pokemon("カビゴン", ability_name="あついしぼう")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.ability.name == "せいでんき"


def test_とくせいガード_ぶきようでも特性無効化のブロックは発動する():
    """とくせいガード: 所持者の特性がぶきようであっても道具の効果は発動し、特性の無効化を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ぶきよう", item_name="とくせいガード")],
    )
    defender = battle.actives[1]
    # ぶきようの効果自体はアイテムを無効化している
    assert not defender.item.enabled
    result = battle.add_ability_disabled_reason(defender, "かたやぶり")
    assert not result
    assert defender.ability.enabled


def test_とくせいガード_使用者が持つ場合もスキルスワップは失敗する():
    """とくせいガード: 使用者側が所持している場合もスキルスワップは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき", item_name="とくせいガード")],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は入れ替わらない
    assert attacker.ability.name == "せいでんき"
    assert defender.ability.name == "めんえき"


def test_とつげきチョッキ_アンコールで変化技を強制されたターンは使用できる():
    """とつげきチョッキ: 実行時ブロックは持たないため、アンコールで変化技を強制されたターンは正常に実行できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"], item_name="とつげきチョッキ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon, "アンコール", move_name="なきごえ")
    t.run_move(battle, 0, move_idx=0)
    assert mon.executed_move.name == "なきごえ"
    assert foe.rank["atk"] == -1


def test_とつげきチョッキ_変化技しか持たない場合わるあがきのみ選択可能():
    """とつげきチョッキ: 変化技しか持たないポケモンはわるあがきのみ選択可能になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"], item_name="とつげきチョッキ")],
        team1=[Pokemon("カビゴン")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert commands == [Command.STRUGGLE]


def test_とつげきチョッキ_変化技はコマンド選択肢から除外される():
    """とつげきチョッキ: 変化技はコマンド選択肢から除外される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "なきごえ"], item_name="とつげきチョッキ")],
        team1=[Pokemon("カビゴン")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert Command.MOVE_1 not in commands
    assert Command.MOVE_0 in commands


def test_とつげきチョッキ_物理技には防御補正なし():
    """とつげきチョッキ: 物理技には防御補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="とつげきチョッキ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 4096


def test_とつげきチョッキ_特殊技にとくぼう1_5倍():
    """とつげきチョッキ: 特殊技に対してとくぼうを1.5倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="とつげきチョッキ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 6144


def test_どくどくだま_どくタイプとはがねタイプには発動しない():
    """どくどくだま: どくタイプ・はがねタイプのポケモンにはもうどくが付与されない"""
    battle = t.start_battle(
        team0=[
            Pokemon("フシギダネ", item_name="どくどくだま"),  # くさ/どくタイプ
            Pokemon("コイル", item_name="どくどくだま"),  # でんき/はがねタイプ
        ],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.ailment.is_active

    t.run_switch(battle, 0, 1)
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.ailment.is_active


def test_どくどくだま_ねむけと重なった場合ねむり優先():
    """どくどくだま: ねむけからねむり状態になるターンと発動ターンが重なった場合、
    ねむけ(priority110)が先に処理されるためねむり状態が優先されもうどくは付与されない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくどくだま")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねむけ": 1},
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name == "ねむり"


def test_どくどくだま_ミストフィールド解除ターンから発動():
    """どくどくだま: ミストフィールドはもうどくの付与を防ぐが、
    フィールドの継続終了(priority140)がどくどくだまの発動(priority150)より先に処理されるため、
    ミストフィールドが解除されたそのターンからどくどくだまが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくどくだま")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", 1),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert battle.terrain.name != "ミストフィールド"
    assert mon.ailment.name == "もうどく"


def test_どくどくだま_発動するターンにどくダメージは受けない():
    """どくどくだま: priority150でどく・もうどくダメージ(90)より後に発動するため、
    発動したそのターンにもうどくダメージは発生しない（翌ターンから発生する）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくどくだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    hp_before = mon.hp
    t.end_turn(battle)
    assert mon.ailment.name == "もうどく"
    assert mon.hp == hp_before  # このターンはもうどくダメージを受けない

    t.end_turn(battle)
    assert mon.hp == hp_before - hp_before // 16  # 翌ターンからもうどくダメージを受ける（1ターン目）


def test_ナゾのみ_効果抜群でHP回復():
    """ナゾのみ: 効果抜群のダメージを受けたときHPを25%回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="ナゾのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.fix_damage(battle, 50)
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp - 50 + foe.max_hp // 4
    assert not foe.has_item()


def test_ナゾのみ_等倍では発動しない():
    """ナゾのみ: 等倍の攻撃では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ナゾのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.fix_damage(battle, 10)
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp - 10
    assert foe.has_item()


def test_ナナシのみ_こおり付与直後に即時回復する():
    """ナナシのみ: こおり付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン", item_name="ナナシのみ")],
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり", source=battle.actives[0])
    assert not defender.ailment.is_active
    assert not defender.has_item()


def test_ナモのみ_どろぼうから奪われない():
    """ナモのみ: 効果バツグンのどろぼうを受けた場合、先に消費されるため奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どろぼう"])],
        team1=[Pokemon("エーフィ", item_name="ナモのみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_item()  # ナモのみの効果で消費済み
    assert not attacker.has_item()  # どろぼうでの奪取は失敗する


def test_ナモのみ_はたきおとすで威力補正を保ったままダメージ半減():
    """ナモのみ: 効果抜群のはたきおとすを受けても威力1.5倍は維持されたままダメージが半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("エーフィ", item_name="ナモのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144  # 威力1.5倍は維持される
    assert battle.damage_calculator.damage_modifier == 2048  # ダメージは半減される
    assert not defender.has_item()  # ナモのみの効果で消費済み（はたきおとすの除去は不発）


def test_ねばりのかぎづめ_なしでは通常ターン():
    """ねばりのかぎづめなし: まきつくでバインド状態の継続ターンが4か5になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.has_volatile("バインド")
    assert foe.volatiles["バインド"].count in {4, 5}


def test_ねばりのかぎづめ_バインドターン固定():
    """ねばりのかぎづめ: まきつくでバインド状態の継続ターンが7ターンに固定される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきつく"], item_name="ねばりのかぎづめ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.has_volatile("バインド")
    assert foe.volatiles["バインド"].count == 7


def test_ねらいのまと_タイプ免疫を無効化():
    """ねらいのまと: タイプ相性による免疫（0倍）を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー", item_name="ねらいのまと")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp < foe.max_hp


def test_ねらいのまと_ぶきようで効果が無効化される():
    """ねらいのまと: 特性ぶきようによりアイテム効果が失われ、通常どおり無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー", item_name="ねらいのまと", ability_name="ぶきよう")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp


def test_ねらいのまと_浮遊による無効化には効果がない():
    """ねらいのまと: 浮遊（特性ふゆう）によるじめん技無効化（フリーフォール）には効果が及ばない"""
    battle = t.start_battle(
        team0=[Pokemon("ダグトリオ", move_names=["じしん"])],
        team1=[Pokemon("フワンテ", item_name="ねらいのまと", ability_name="ふゆう")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp


def test_ねらいのまと_複合タイプで無効化以外の相性は維持される():
    """ねらいのまと: 複合タイプの場合、無効化タイプ以外の相性補正（弱点等）はそのまま反映される

    ノーマル・エスパータイプのキリンリキがゴーストタイプの技を受けた場合、
    ゴースト→ノーマルの無効化はなくなるが、ゴースト→エスパーの効果抜群(2倍)はそのまま活きる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["シャドーボール"])],
        team1=[Pokemon("キリンリキ", item_name="ねらいのまと")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 4096 * 2


def test_のどスプレー_いやしのすずが不発のときは発動しない():
    """のどスプレー: いやしのすずで治療対象がおらず技が不発になったときは発動・消費しない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not mon.ailment.is_active
    t.run_move(battle, 0)
    assert mon.rank["spa"] == 0
    assert mon.has_item()


def test_のどスプレー_とくこうランクが最大のとき発動しない():
    """のどスプレー: すでにとくこうランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.rank["spa"] = 6
    t.run_move(battle, 0)
    assert mon.rank["spa"] == 6
    assert mon.has_item()


def test_のどスプレー_技が外れたときは発動しない():
    """のどスプレー: 音技が外れたときは発動・消費しない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=0,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["spa"] == 0
    assert mon.has_item()


def test_のどスプレー_非音技では発動しない():
    """のどスプレー: 音技以外では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.rank["spa"] == 0
    assert mon.has_item()


def test_のどスプレー_音技使用後にC上昇():
    """のどスプレー: 音技使用後にとくこう+1"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.rank["spa"] == 1
    assert not mon.has_item()


def test_ノーマルジュエル_なげつけるが失敗しアイテムを消費しない():
    """ノーマルジュエル: なげつけるを使用しても失敗し、アイテムを消費しない（投げられないアイテム）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ノーマルジュエル", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert mon.has_item()


def test_ノーマルジュエル_ノーマル技威力1_3倍():
    """ノーマルジュエル: ノーマル技の威力を1.3倍（5325/4096倍）にする（消費）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ノーマルジュエル", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 5325
    assert not mon.has_item()


def test_はっきんだま_ギラティナオリジンでも効果がある():
    """はっきんだま: ギラティナ(オリジン)が持っていてもドラゴン・ゴースト技に補正がかかる"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(オリジン)", item_name="はっきんだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_はっきんだま_ギラティナ以外が持っても効果がない():
    """はっきんだま: ギラティナ以外が持っていてもドラゴン・ゴースト技に補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="はっきんだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_はっきんだま_なげつけるで威力60になる():
    """はっきんだま: ギラティナ以外が持っている場合は通常の道具でありなげつけるで使用でき、威力60でダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="はっきんだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_はっきんだま_はたきおとすで奪われる():
    """はっきんだま: だいはっきんだまと異なり、ギラティナが持っていても通常通りはたきおとすで奪われる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("ギラティナ(オリジン)", item_name="はっきんだま")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.has_item()


def test_はっきんだま_対象外タイプの技には効果がない():
    """はっきんだま: ギラティナが持っていてもドラゴン・ゴースト以外の技には補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(アナザー)", item_name="はっきんだま", move_names=["はかいこうせん"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_バコウのみ_ついばむで奪われる前に消費されダメージ半減():
    """バコウのみ: 効果抜群のついばむを受けた場合、技の効果よりバコウのみの効果が優先されてダメージが半減し、消費済みのため奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ついばむ"])],
        team1=[Pokemon("キモリ", item_name="バコウのみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048
    assert not defender.has_item()  # バコウのみの効果で消費済み
    assert not attacker.has_item()  # ついばむによる奪取は失敗する


def test_バコウのみ_フライングプレスでは発動しない():
    """バコウのみ: フライングプレスがひこう複合相性で抜群になっても発動するのはヨプのみでありバコウのみは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["フライングプレス"])],
        team1=[Pokemon("キモリ", item_name="バコウのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier != 2048
    assert defender.has_item()  # バコウのみは消費されない


def test_バンジのみ_それ以外の性格ではこんらんしない():
    """バンジのみ: にがい味が嫌いでない性格では発動してもこんらんしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="バンジのみ", nature="まじめ")],
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
    ["やんちゃ", "のうてんき", "うっかりや", "むじゃき"]
)
def test_バンジのみ_とくぼうが上がりにくい性格でこんらんする(nature):
    """バンジのみ: にがい味が嫌いな性格（とくぼうが上がりにくい）は発動と同時にこんらんする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="バンジのみ", nature=nature)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_ばんのうがさ_あさのひざしが晴れでも半分回復():
    """ばんのうがさ使用者: 晴れ状態でもあさのひざしの回復量が最大HPの1/2になる"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["あさのひざし"], item_name="ばんのうがさ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    max_hp = mon.max_hp
    # HPを1にして回復量を確認する
    mon.hp = 1
    t.run_move(battle, 0)
    # 晴れなら2/3回復 (int(max_hp * 2/3)) のはずだが、
    # ばんのうがさで1/2回復 (int(max_hp * 1/2)) になる
    expected_hp = 1 + int(max_hp * 0.5)
    assert mon.hp == expected_hp


def test_ばんのうがさ_すいすいが発動しない():
    """ばんのうがさ使用者: 雨状態でもすいすいによる素早さ上昇が発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すいすい", item_name="ばんのうがさ")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 99),
    )
    mon = battle.actives[0]
    # ばんのうがさがあるので素早さは2倍にならない
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_ばんのうがさ_晴れのほのお技強化が無効():
    """ばんのうがさ防御側: 晴れでほのお技の1.5倍補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("はれ", 99),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 天候補正なし (4096 = 等倍)
    assert battle.damage_calculator.power_modifier == 4096


def test_ばんのうがさ_晴れのみず技弱化が無効():
    """ばんのうがさ防御側: 晴れでみず技の0.5倍補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("はれ", 99),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 天候補正なし (4096 = 等倍)
    assert battle.damage_calculator.power_modifier == 4096


def test_ばんのうがさ_雨でかみなりが必中にならない():
    """ばんのうがさ防御側: 雨状態でもかみなりが必中にならない"""
    # test_option.accuracy を設定すると命中率判定がスキップされるため、ここでは使用しない
    # 代わりに weather_for の返り値を直接検証する
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン", item_name="ばんのうがさ")],
        weather=("あめ", 99),
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # ばんのうがさを持つ防御側に対する雨天候は「なし」として扱われる
    assert not battle.weather_for(defender).rainy
    # 攻撃側は雨天候の恩恵を受ける（必中になるはず、ばんのうがさなし）
    assert battle.weather.rainy


def test_ばんのうがさ_雨のほのお技弱化が無効():
    """ばんのうがさ防御側: 雨でほのお技の0.5倍補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("あめ", 99),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 天候補正なし (4096 = 等倍)
    assert battle.damage_calculator.power_modifier == 4096


def test_ばんのうがさ_雨のみず技強化が無効():
    """ばんのうがさ防御側: 雨でみず技の1.5倍補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("あめ", 99),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 天候補正なし (4096 = 等倍)
    assert battle.damage_calculator.power_modifier == 4096


def test_パワフルハーブ_あめ下のエレクトロビームは天候優先で消費されない():
    """パワフルハーブ: あめによる溜めスキップが優先され、アイテムは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="パワフルハーブ", move_names=["エレクトロビーム"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.has_item()
    assert foe.hp < foe.max_hp
    assert mon.rank["spa"] == 1


def test_パワフルハーブ_おおひでり下のダイビングが失敗しても消費されない():
    """パワフルハーブ: おおひでりでダイビングが失敗したときはアイテムを消費しない"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", item_name="パワフルハーブ", move_names=["ダイビング"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.has_item()
    assert foe.hp == foe.max_hp


def test_パワフルハーブ_にほんばれ下のソーラービームは天候優先で消費されない():
    """パワフルハーブ: にほんばれによる溜めスキップが優先され、アイテムは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="パワフルハーブ", move_names=["ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.has_item()
    assert foe.hp < foe.max_hp


def test_パワフルハーブ_消費後は溜め技が2ターンかかる():
    """パワフルハーブ: 消費後は溜め技が通常通り2ターンかかるようになる"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="パワフルハーブ", move_names=["ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]

    # 1回目: パワフルハーブで即発動して消費される
    t.run_move(battle, 0)
    assert not mon.has_item()
    hp_after_first = foe.hp
    assert hp_after_first < foe.max_hp

    # 2回目: アイテムがないため通常通り1ターン目は溜めるだけでダメージを与えない
    t.run_move(battle, 0)
    assert foe.hp == hp_after_first
    assert mon.has_volatile("ソーラービーム")


def test_パワフルハーブ_溜め技をスキップ():
    """パワフルハーブ: 溜め技の溜めターンをスキップして即発動"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="パワフルハーブ", move_names=["ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert not mon.has_item()
    assert foe.hp < foe.max_hp


def test_パンチグローブ_パンチ技の威力1_1倍():
    """パンチグローブ: パンチ技の威力を1.1倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パンチグローブ", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4506


def test_パンチグローブ_パンチ技の接触判定を無効化():
    """パンチグローブ: パンチ技の接触判定を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パンチグローブ", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ひかりごけ_あまのじゃくでDランクが最小のとき発動しない():
    """ひかりごけ: あまのじゃく所持者はとくぼうランクがすでに最小のとき発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["spd"] = -6
    t.run_move(battle, 0)
    assert foe.rank["spd"] == -6
    assert foe.has_item()


def test_ひかりごけ_あまのじゃくでD下降():
    """ひかりごけ: あまのじゃく所持者はとくぼうが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == -1
    assert not foe.has_item()


def test_ひかりごけ_かたやぶりのみず技はたんじゅん・あまのじゃくでもD上昇():
    """ひかりごけ: かたやぶりの効果があるみず技に対してはたんじゅん・あまのじゃくは発動せず通常通り+1される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 1
    assert not foe.has_item()


def test_ひかりごけ_たんじゅんでD2段階上昇():
    """ひかりごけ: たんじゅん所持者はとくぼうが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ", ability_name="たんじゅん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 2
    assert not foe.has_item()


def test_ひかりごけ_とくぼうランクが最大のとき発動しない():
    """ひかりごけ: すでにとくぼうランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["spd"] = 6
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 6
    assert foe.has_item()


def test_ひかりごけ_マジシャンより先に発動して奪われない():
    """ひかりごけ: 特性マジシャンのみず技を受けても、ひかりごけが先に発動して消費されるため奪われない
    （攻撃側の素早さが防御側より高い場合でも、素早さに依存せずひかりごけが先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 1
    assert not foe.has_item()
    assert not attacker.has_item()


def test_ひかりごけ_みず以外では発動しない():
    """ひかりごけ: みず以外の技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="ひかりごけ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 0
    assert foe.has_item()


def test_ひかりごけ_みず被弾でD上昇():
    """ひかりごけ: みず技でダメージを受けたときとくぼう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみのり"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 1
    assert not foe.has_item()


def test_ひかりのこな_一撃必殺技には適用されない():
    """ひかりのこな: 一撃必殺技の命中率には影響しない（第三世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つのドリル"])],
        team1=[Pokemon("カビゴン", item_name="ひかりのこな")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 30


def test_ひかりのこな_命中率が0_9倍になる():
    """ひかりのこな: 持たせた側に対する技の命中率が0.9倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン", item_name="ひかりのこな")],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 3686 // 4096


def test_ひかりのこな_非所持では命中率が変化しない():
    """ひかりのこな: 持っていない場合は命中率が変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン")],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_ひかりのねんど_スクリーン8ターンに延長():
    """ひかりのねんど: リフレクターを8ターンに延長する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ひかりのねんど", move_names=["リフレクター"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    # ひかりのねんどによりリフレクターが8ターンに延長されている
    side = battle.get_side(battle.players[0])
    assert side.get("リフレクター").count == 8


@pytest.mark.parametrize("field_name", ["リフレクター", "ひかりのかべ", "オーロラベール"])
def test_ひかりのねんど_対象の壁を8ターンに延長(field_name):
    """ひかりのねんど: リフレクター・ひかりのかべ・オーロラベールいずれも8ターンに延長する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ひかりのねんど")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    side = battle.get_side(mon)
    side.apply(field_name, 5, source=mon)
    assert side.get(field_name).count == 8


def test_ひかりのねんど_対象外の場は延長されない():
    """ひかりのねんど: リフレクター・ひかりのかべ・オーロラベール以外の場状態は延長されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ひかりのねんど")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    side = battle.get_side(mon)
    side.apply("しんぴのまもり", 5, source=mon)
    assert side.get("しんぴのまもり").count == 5


def test_ひかりのねんど_非所持では5ターンのまま():
    """ひかりのねんど: 所持していない場合はリフレクターが5ターンで終了する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    side = battle.get_side(mon)
    side.apply("リフレクター", 5, source=mon)
    assert side.get("リフレクター").count == 5


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_てんのめぐみで確率2倍(item_name):
    """おうじゃのしるし・するどいキバ: 特性てんのめぐみによりひるみ確率が2倍(20%)になる"""
    without_megumi = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(without_megumi, 0.15)
    t.run_move(without_megumi, 0)
    assert not without_megumi.actives[1].has_volatile("ひるみ")

    with_megumi = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ", item_name=item_name, ability_name="てんのめぐみ",
            move_names=["たいあたり"],
        )],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(with_megumi, 0.15)
    t.run_move(with_megumi, 0)
    assert with_megumi.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_なげつけるで確実にひるませる(item_name):
    """おうじゃのしるし・するどいキバ: なげつけるで使用した場合、100%の確率で相手をひるませる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["なげつける"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.99)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_ひるまない確率(item_name):
    """おうじゃのしるし・するどいキバ: 乱数が0.1以上のときひるまない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_ひるみ付与(item_name):
    """おうじゃのしるし・するどいキバ: 攻撃命中時10%の確率でひるみ付与"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_りんぷんで無効化(item_name):
    """おうじゃのしるし・するどいキバ: 特性りんぷんにより効果が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_一撃必殺技には効果がない(item_name):
    """おうじゃのしるし・するどいキバ: 一撃必殺技には効果が無い（追加の乱数判定が発生しないことで確認する）

    きあいのタスキ等で耐えた場合の挙動を直接検証したいが、現状の実装では
    一撃必殺技ときあいのタスキの組み合わせ自体に別の既知の不具合があり
    HPが1で耐えられないため、ここでは耐えるかどうかに依存しない方法で確認する。
    """
    def count_random_calls(has_item: bool) -> int:
        kwargs = {"item_name": item_name} if has_item else {}
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["じわれ"], **kwargs)],
            team1=[Pokemon("ピカチュウ")],
            accuracy=100,
        )
        count = 0

        def counting_random() -> float:
            nonlocal count
            count += 1
            return 0.5

        battle.random.random = counting_random
        t.run_move(battle, 0)
        return count

    assert count_random_calls(True) == count_random_calls(False)


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_元々ひるみ効果がある技には重複しない(item_name):
    """おうじゃのしるし・するどいキバ: 元々ひるみの追加効果がある技（エアスラッシュ等）には
    重複して効果が発動しない（追加の乱数判定が発生しないことで確認する）"""
    def count_random_calls(has_item: bool) -> int:
        kwargs = {"item_name": item_name} if has_item else {}
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["エアスラッシュ"], **kwargs)],
            team1=[Pokemon("ピカチュウ")],
            accuracy=100,
        )
        count = 0

        def counting_random() -> float:
            nonlocal count
            count += 1
            return 0.5

        battle.random.random = counting_random
        t.run_move(battle, 0)
        return count

    assert count_random_calls(True) == count_random_calls(False)


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_変化技では発動しない(item_name):
    """おうじゃのしるし・するどいキバ: 変化技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["でんじは"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_ビビリだま_あまのじゃく所持者はこうげき上昇時にすばやさが下がる():
    """ビビリだま: あまのじゃく所持者はいかくでこうげきが上昇し、ビビリだまの効果も反転してすばやさが下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.rank["atk"] == 1
    assert mon.rank["spe"] == -1
    assert not mon.has_item()


def test_ビビリだま_いかくでS上昇():
    """ビビリだま: いかくによってこうげきが下がったときすばやさ+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.rank["spe"] == 1
    assert mon.rank["atk"] == -1
    assert not mon.has_item()


def test_ビビリだま_こうげきが最低ランクで変化しない場合は発動しない():
    """ビビリだま: こうげきが既に最低ランクでいかくが不発だった場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ"), Pokemon("コラッタ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.rank["atk"] = -6
    t.run_switch(battle, 1, 1)
    assert mon.rank["atk"] == -6
    assert mon.rank["spe"] == 0
    assert mon.has_item()


def test_ビビリだま_すばやさが最大ランクの場合は発動しない():
    """ビビリだま: すばやさが既に最大ランクの場合は発動・消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ"), Pokemon("コラッタ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.rank["spe"] = 6
    t.run_switch(battle, 1, 1)
    assert mon.rank["atk"] == -1
    assert mon.rank["spe"] == 6
    assert mon.has_item()


def test_ピントレンズ_急所ランク加算():
    """ピントレンズ: 急所ランクを+1する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ピントレンズ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 急所が出ない程度に固定（0.5 < 急所ランク+1の閾値以下）
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 1


@pytest.mark.parametrize(
    "nature",
    ["ずぶとい", "ひかえめ", "おだやか", "おくびょう"]
)
def test_フィラのみ_こうげきが上がりにくい性格でこんらんする(nature):
    """フィラのみ: からい味が嫌いな性格（こうげきが上がりにくい）は発動と同時にこんらんする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="フィラのみ", nature=nature)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_フィラのみ_それ以外の性格ではこんらんしない():
    """フィラのみ: からい味が嫌いでない性格では発動してもこんらんしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="フィラのみ", nature="まじめ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert not mon.has_volatile("こんらん")


@pytest.mark.parametrize("item_name", ["エレキシード", "グラスシード", "サイコシード", "ミストシード"])
def test_フィールドシード_フィールドなしでは発動しない(item_name):
    """フィールドシード系: 対応フィールドがないとき発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["def"] == 0
    assert mon.rank["spd"] == 0
    assert mon.has_item()


@pytest.mark.parametrize("item_name, terrain, stat", [
    ("エレキシード", "エレキフィールド", "def"),
    ("グラスシード", "グラスフィールド", "def"),
    ("サイコシード", "サイコフィールド", "spd"),
    ("ミストシード", "ミストフィールド", "spd"),
])
def test_フィールドシード_ランク最大時は消費しない(item_name, terrain, stat):
    """フィールドシード系: 対応能力ランクがすでに最大のときは発動せずアイテムも消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_stats(mon, {stat: 6})
    battle.terrain_manager.apply(terrain, 5)
    assert mon.rank[stat] == 6
    assert mon.has_item()


@pytest.mark.parametrize("item_name, terrain, stat", [
    ("エレキシード", "エレキフィールド", "def"),
    ("グラスシード", "グラスフィールド", "def"),
    ("サイコシード", "サイコフィールド", "spd"),
    ("ミストシード", "ミストフィールド", "spd"),
])
def test_フィールドシード_発動(item_name, terrain, stat):
    """フィールドシード系: 対応フィールド展開時に登場してランク+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
        terrain=(terrain, 5),
    )
    mon = battle.actives[0]
    assert mon.rank[stat] == 1
    assert not mon.has_item()


def test_ふうせん_じめん技を無効化():
    """ふうせん: 浮遊状態でじめん技が当たらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ゼニガメ", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp


def test_ふうせん_じゅうりょく下では浮遊が無効になる():
    """ふうせん: じゅうりょく状態では浮遊効果が打ち消されじめん技が命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ゼニガメ", move_names=["じしん"])],
        field={"じゅうりょく": 5},
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp < mon.max_hp


def test_ふうせん_ダメージが0でも割れる():
    """ふうせん: ダメージ量が0でも攻撃技が有効に命中していれば割れる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.fix_damage(battle, 0)
    t.run_move(battle, 1)
    assert not mon.has_item()


def test_ふうせん_ダメージを受けると割れる():
    """ふうせん: ダメージを受けるとアイテムが消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert not mon.has_item()


def test_ふうせん_ぶきようで無効化される():
    """ふうせん: 特性ぶきようによりアイテム効果が失われ、じめん技が命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん", ability_name="ぶきよう")],
        team1=[Pokemon("ゼニガメ", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp < mon.max_hp


def test_ふうせん_みがわりが肩代わりしても割れる():
    """ふうせん: みがわりが攻撃を肩代わりした場合でも本体が有効な攻撃を受けたことになり割れる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "みがわり", hp=100)
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp
    assert not mon.has_item()


def test_ふうせん_変化技では割れない():
    """ふうせん: 変化技を受けてもアイテムは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.has_item()


def test_フォーカスレンズ_一撃必殺技には適用されない():
    """フォーカスレンズ: 一撃必殺技の命中率には影響しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="フォーカスレンズ", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.step()
    assert battle.move_executor.accuracy == 30


def test_フォーカスレンズ_交代直後の相手には効果がない():
    """フォーカスレンズ: そのターンに交代してきたばかりで技を未使用の相手には効果がない（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="フォーカスレンズ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("ピカチュウ"), Pokemon("コイル")],
    )
    t.reserve_command(battle, command0=Command.MOVE_0, command1=Command.SWITCH_1)
    battle.step()
    move = battle.actives[0].moves[0]
    assert battle.move_executor.accuracy == move.accuracy


def test_フォーカスレンズ_先攻なら命中率が変化しない():
    """フォーカスレンズ: 相手がまだそのターンに行動していない場合は命中率が変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="フォーカスレンズ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_フォーカスレンズ_後攻なら命中率が1_2倍になる():
    """フォーカスレンズ: すでに行動している相手に対して使う技の命中率が1.2倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="フォーカスレンズ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.step()
    move = battle.actives[0].moves[0]
    assert battle.move_executor.accuracy == move.accuracy * 4915 // 4096


def test_フォーカスレンズ_非所持では命中率が変化しない():
    """フォーカスレンズ: 持っていない場合は命中率が変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.step()
    move = battle.actives[0].moves[0]
    assert battle.move_executor.accuracy == move.accuracy


def test_ブーストエナジー_こだいかっせいマジックルーム解除後に発動():
    """ブーストエナジー: マジックルーム解除後にこだいかっせいブーストが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コライドン", ability_name="こだいかっせい", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # マジックルーム下ではアイテムが無効で、ブーストが発動していないはず
    battle.item_manager.add_disabled_reason(mon, "マジックルーム")
    assert mon.paradox_boost_stat is None or mon.paradox_boost_source == "item"
    # マジックルーム解除後にブーストが発動する
    battle.item_manager.remove_disabled_reason(mon, "マジックルーム")
    assert mon.paradox_boost_stat is not None
    assert mon.paradox_boost_source == "item"


def test_ブーストエナジー_こだいかっせい登場時に発動():
    """ブーストエナジー: こだいかっせい持ちが登場時にブーストを発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コライドン", ability_name="こだいかっせい", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat is not None
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item()


def test_ブーストエナジー_バトル中に取得すると即座に発動する():
    """ブーストエナジー: バトル中にアイテムを新たに取得すると即座にブーストが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コライドン", ability_name="こだいかっせい")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat is None
    battle.item_manager.gain_item(mon, "ブーストエナジー")
    assert mon.paradox_boost_stat is not None
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item()


def test_ブーストエナジー_パラドックス特性を持たないポケモンが取得しても発動しない():
    """ブーストエナジー: こだいかっせい/クォークチャージを持たないポケモンが取得しても何も起きない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.gain_item(mon, "ブーストエナジー")
    assert mon.paradox_boost_stat is None
    assert mon.has_item("ブーストエナジー")


def test_ブーストエナジー_パラドックス特性持ちからトリックで奪えない():
    """ブーストエナジー: こだいかっせい/クォークチャージ持ちが持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="エレキメイカー", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", ability_name="クォークチャージ", item_name="ブーストエナジー")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert defender.has_item("ブーストエナジー")
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "ブーストエナジー"


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_ブーストエナジー_パラドックス特性持ちから奪えない(move_name):
    """ブーストエナジー: こだいかっせい/クォークチャージ持ちが持っている間ははたきおとす・どろぼう等で奪われない。
    エレキメイカーは登場時優先度がクォークチャージの判定より先に発動するため、
    同時に登場させることでエレキフィールドを発動源にし、アイテムを未消費のまま維持できる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="エレキメイカー", move_names=[move_name])],
        team1=[Pokemon("カビゴン", ability_name="クォークチャージ", item_name="ブーストエナジー")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.has_item("ブーストエナジー")
    t.run_move(battle, 0)
    assert defender.has_item("ブーストエナジー")


def test_ブーストエナジー_パラドックス特性持ちへトリックで渡せない():
    """ブーストエナジー: こだいかっせい/クォークチャージ持ちへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="ブーストエナジー")],
        team1=[Pokemon("カビゴン", ability_name="クォークチャージ", item_name="たべのこし")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "ブーストエナジー"
    assert defender.item.name == "たべのこし"


def test_ホズのみ_あくタイプのどろぼうでは発動せず奪われる():
    """ホズのみ: どろぼうはあくタイプのため発動せず、アイテムは奪われる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どろぼう"])],
        team1=[Pokemon("エーフィ", item_name="ホズのみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_item()
    assert attacker.has_item()  # どろぼうでの奪取は成功する


def test_ホズのみ_ノーマルスキンで変化したはたきおとすで威力補正を保ったままダメージ半減():
    """ホズのみ: ノーマルスキンでノーマル化したはたきおとすを受けても、威力補正は維持されたままダメージが半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["はたきおとす"])],
        team1=[Pokemon("カビゴン", item_name="ホズのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 7372  # ノーマルスキン補正と持ち物所持による1.5倍が両方乗る
    assert battle.damage_calculator.damage_modifier == 2048  # ダメージは半減される
    assert not defender.has_item()  # ホズのみの効果で消費済み（はたきおとすの除去は不発）


def test_ホズのみ_ノーマル技のダメージを半減して消費する():
    """ホズのみ: 効果バツグンでなくてもノーマル技を受けたらダメージを半減して消費する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ホズのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048
    assert not defender.has_item()


def test_ホズのみ_ほしがるでは奪われない():
    """ホズのみ: ノーマルタイプのほしがるを受けた場合、先に消費されるため奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほしがる"])],
        team1=[Pokemon("エーフィ", item_name="ホズのみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_item()  # ホズのみの効果で消費済み
    assert not attacker.has_item()  # ほしがるでの奪取は失敗する


def test_ホズのみ_わるあがきでは発動しない():
    """ホズのみ: わるあがきはタイプを持たないため発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["わるあがき"])],
        team1=[Pokemon("カビゴン", item_name="ホズのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096
    assert defender.has_item()


def test_ぼうごパット_かたいツメの威力補正は防がない():
    """ぼうごパット: 自分の技が接触技であることに由来する効果（かたいツメ）は防がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたいツメ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier


def test_ぼうごパット_ゴツゴツメットのダメージを防ぐ():
    """ぼうごパット: 相手が接触を受けたことに反応する持ち物（ゴツゴツメット）の効果を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ぼうごパット_さめはだのダメージを防ぐ():
    """ぼうごパット: 相手が接触を受けたことに反応する特性（さめはだ）の効果を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="さめはだ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ぼうごパット_どくしゅの追加効果は防がない():
    """ぼうごパット: 自分の技が接触技であることに由来する効果（どくしゅ）は防がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    battle.random.random = lambda: 0.0
    t.run_move(battle, 0)
    assert defender.has_ailment("どく")


def test_ぼうごパット_もふもふのダメージ半減は防がない():
    """ぼうごパット: ぼうごパットの効果対象外である相手のもふもふによるダメージ半減は防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_ぼうごパット_わるいてぐせによるアイテム強奪は防げない():
    """ぼうごパット: ぼうごパットの効果対象外である相手のわるいてぐせによってぼうごパットを奪われる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_item()


def test_ぼうじんゴーグル_天候ダメージを無効化():
    """ぼうじんゴーグル: すなあらしによるターン終了ダメージを無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうじんゴーグル")],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    initial_hp = mon.max_hp
    t.end_turn(battle)
    assert mon.hp == initial_hp


def test_ぼうじんゴーグル_特性ほうしによる状態異常を無効化():
    """ぼうじんゴーグル: 接触した相手の特性ほうし(Effect Spore)による状態異常を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほうし")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"], item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    assert not battle.actives[1].ailment.is_active


def test_ぼうじんゴーグル_特性ぼうじんと同時に持つ場合は特性側が優先():
    """ぼうじんゴーグル: 特性ぼうじんを併せ持つ場合、特性側の無効化が優先されアイテムは公開されない"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ねむりごな"])],
        team1=[Pokemon("ピカチュウ", ability_name="ぼうじん", item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ailment.name != "ねむり"
    assert not defender.item.revealed


def test_ぼうじんゴーグル_粉技を無効化():
    """ぼうじんゴーグル: 粉技（ねむりごな等）を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ねむりごな"])],
        team1=[Pokemon("ピカチュウ", item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name != "ねむり"


def test_ぼうじんゴーグル_粉技を無効化した際にアイテムが公開される():
    """ぼうじんゴーグル: 粉技を無効化した際にアイテムが公開される"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ねむりごな"])],
        team1=[Pokemon("ピカチュウ", item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.item.revealed
    t.run_move(battle, 0)
    assert defender.item.revealed


def test_マゴのみ_それ以外の性格ではこんらんしない():
    """マゴのみ: あまい味が嫌いでない性格では発動してもこんらんしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="マゴのみ", nature="まじめ")],
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
    ["ゆうかん", "れいせい", "のんき", "なまいき"]
)
def test_マゴのみ_はやさが上がりにくい性格でこんらんする(nature):
    """マゴのみ: あまい味が嫌いな性格（はやさが上がりにくい）は発動と同時にこんらんする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="マゴのみ", nature=nature)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_メトロノーム_タイプ相性で無効化されるとリセット():
    """メトロノーム: タイプ相性により無効化された場合カウントは0にリセットされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0)
    assert mon.item.count == 0


def test_メトロノーム_ねむり中は行動できずカウント維持():
    """メトロノーム: ねむりなどで技が出せなかったときはカウントを維持する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.apply_ailment(battle, active_index=0, ailment_name="ねむり", count=3)
    t.run_move(battle, 0)
    assert mon.item.count == 3
    assert mon.item.move_name == "たいあたり"


def test_メトロノーム_まもるで防がれるとリセット():
    """メトロノーム: まもるで防がれた場合カウントは0にリセットされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0)
    assert mon.item.count == 0


def test_メトロノーム_ミスするとリセット():
    """メトロノーム: 技が命中しなかった場合カウントは0にリセットされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0)
    assert mon.item.count == 0


def test_メトロノーム_別技でリセット():
    """メトロノーム: 違う技を使うとカウントリセット"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0, 1)
    assert mon.item.count == 1
    assert mon.item.move_name == "でんきショック"


@pytest.mark.parametrize("uses,expected_modifier", [
    (1, 4096),  # 初回は補正なし
    (2, 4915),  # 2回目: 1.2倍
    (3, 5734),  # 3回目: 1.4倍
    (6, 8191),  # 6回目: 2倍（上限）
    (7, 8191),  # 7回目以降: 上限変わらず
])
def test_メトロノーム_連続使用_補正係数(uses, expected_modifier):
    """メトロノーム: 連続使用回数に応じた補正係数"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    for _ in range(uses):
        t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


def test_メンタルハーブ_いちゃもんを即解除():
    """メンタルハーブ: いちゃもん付与時に即解除する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メンタルハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", source=battle.actives[1])
    assert not mon.has_volatile("いちゃもん")
    assert not mon.has_item()


@pytest.mark.parametrize("volatile_name, kwargs", [
    ("メロメロ", {}),
    ("アンコール", {"move_name": "たいあたり"}),
    ("かなしばり", {"move_name": "たいあたり"}),
    ("ちょうはつ", {}),
    ("かいふくふうじ", {}),
])
def test_メンタルハーブ_対象の揮発状態を即解除(volatile_name, kwargs):
    """メンタルハーブ: メロメロ・アンコール・かなしばり・ちょうはつ・かいふくふうじ付与時に即解除する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メンタルハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, volatile_name, source=battle.actives[1], **kwargs)
    assert not mon.has_volatile(volatile_name)
    assert not mon.has_item()


def test_メンタルハーブ_対象外の揮発状態には反応しない():
    """メンタルハーブ: 対象外の揮発状態（こんらん等）では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メンタルハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こんらん", source=battle.actives[1])
    assert mon.has_volatile("こんらん")
    assert mon.has_item()


def test_ものしりメガネ_物理技には補正なし():
    """ものしりメガネ: 物理技には補正しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものしりメガネ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ものしりメガネ_特殊技1_1倍():
    """ものしりメガネ: 特殊技の威力を1.1倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものしりメガネ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4505


def test_ものまねハーブ_びんじょうでの上昇はコピーしない():
    """ものまねハーブ: 相手のびんじょうによるコピーで上がった分は再度コピーしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ", ability_name="びんじょう")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    # mon自身がランクを上げる → foeのびんじょうが発動してfoeも+2上がるが、
    # そのびんじょうによる上昇をmonのものまねハーブが再度コピーしてはいけない
    battle.modify_stats(mon, {"atk": +2})
    assert mon.rank["atk"] == 2
    assert foe.rank["atk"] == 2
    assert mon.has_item()


def test_ものまねハーブ_びんじょうで最大まで上がったときは発動しない():
    """ものまねハーブ: びんじょうによるコピーで既に最大まで上がった場合はものまねハーブは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びんじょう", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    mon.rank["atk"] = 5
    battle.modify_stats(foe, {"atk": +2})
    assert mon.rank["atk"] == 6
    assert mon.has_item()


def test_ものまねハーブ_びんじょう所持者は2回上昇する():
    """ものまねハーブ: 特性がびんじょうである場合、びんじょうの後にものまねハーブも発動して2回上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びんじょう", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.modify_stats(foe, {"atk": +1})
    assert mon.rank["atk"] == 2
    assert not mon.has_item()


def test_ものまねハーブ_ランクが最大のとき発動しない():
    """ものまねハーブ: 自分のランクが既に最大のときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    mon.rank["atk"] = 6
    battle.modify_stats(foe, {"atk": +2})
    assert mon.rank["atk"] == 6
    assert mon.has_item()


def test_ものまねハーブ_相手のランク上昇をコピー():
    """ものまねハーブ: 相手のランク上昇をそのままコピーする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.modify_stats(foe, {"atk": +2})
    assert mon.rank["atk"] == 2
    assert not mon.has_item()


def test_モモンのみ_どく付与直後に即時回復する():
    """モモンのみ: どく付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくガス"])],
        team1=[Pokemon("カビゴン", item_name="モモンのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert not defender.has_item()


def test_ヤタピのみ_とくこうランクが最大のとき発動しない():
    """ヤタピのみ: すでにとくこうランクが最大まで上がっているときはHP1/4以下でも発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ヤタピのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.rank["spa"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.rank["spa"] == 6
    assert mon.has_item()


def test_ヤチェのみ_あついしぼうの影響下でも発動する():
    """ヤチェのみ: あついしぼうはタイプ相性を変えないため発動に影響しない"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["ふぶき"])],
        team1=[Pokemon("フシギダネ", item_name="ヤチェのみ", ability_name="あついしぼう")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 8192  # 効果抜群のまま
    assert battle.damage_calculator.damage_modifier == 2048
    assert not battle.actives[1].has_item()  # 発動して消費される


def test_ヤチェのみ_フリーズドライのみずタイプに対する効果抜群でも発動する():
    """ヤチェのみ: フリーズドライがみずタイプに抜群のときも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["フリーズドライ"])],
        team1=[Pokemon("カメックス", item_name="ヤチェのみ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 8192  # みずタイプへの効果抜群
    assert battle.damage_calculator.damage_modifier == 2048
    assert not battle.actives[1].has_item()  # 発動して消費される


def test_ゆきだま_あまのじゃくでA最小のとき発動しない():
    """ゆきだま: あまのじゃく所持者のこうげきランクが最小のとき発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["atk"] = -6
    t.run_move(battle, 0)
    assert foe.rank["atk"] == -6
    assert foe.has_item()


def test_ゆきだま_あまのじゃくで下降():
    """ゆきだま: あまのじゃく所持者はこうげきランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == -1
    assert not foe.has_item()


def test_ゆきだま_かたやぶりのこおり技であまのじゃくでも上昇():
    """ゆきだま: かたやぶりの効果があるこおり技に対してはあまのじゃくでもこうげきランクが1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["こなゆき"])],
        team1=[Pokemon("ピカチュウ", item_name="ゆきだま", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 1
    assert not foe.has_item()


def test_ゆきだま_こおり以外では発動しない():
    """ゆきだま: こおり以外の技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="ゆきだま")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 0
    assert foe.has_item()


def test_ゆきだま_こおり被弾でA上昇():
    """ゆきだま: こおり技でダメージを受けたときこうげき+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 1
    assert not foe.has_item()


def test_ゆきだま_たんじゅんで2段階上昇():
    """ゆきだま: たんじゅん所持者はこうげきランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま", ability_name="たんじゅん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 2
    assert not foe.has_item()


def test_ゆきだま_ランク上限で発動しない():
    """ゆきだま: こうげきランクが最大のとき発動しない（アイテムも消費されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["atk"] = 6
    t.run_move(battle, 0)
    assert foe.rank["atk"] == 6
    assert foe.has_item()


def test_ようせいのハネ_なげつけるで威力30になる():
    """ようせいのハネ: なげつけるで使用すると威力30になる（フェアリー以外の技のためタイプ補正は乗らない）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ようせいのハネ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 30
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_ヨプのみ_フライングプレスのひこう複合相性が抜群なら発動する():
    """ヨプのみ: くさ単タイプがフライングプレス（かくとう等倍×ひこう2倍=抜群）を受けたとき発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["フライングプレス"])],
        team1=[Pokemon("キモリ", item_name="ヨプのみ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048
    assert not battle.actives[1].has_item()


def test_ヨプのみ_フライングプレスのひこう複合相性が等倍なら発動しない():
    """ヨプのみ: はがね単タイプがフライングプレス（かくとう2倍×ひこう0.5倍=等倍）を受けても発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["フライングプレス"])],
        team1=[Pokemon("ギアル", item_name="ヨプのみ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_item()


def test_ラムのみ_こんらん付与直後に即時回復する():
    """ラムのみ: こんらん付与直後（ON_VOLATILE_START）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ラムのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon, "こんらん", source=foe)
    assert not mon.has_volatile("こんらん")
    assert not mon.has_item()


def test_ラムのみ_ターン終了で状態異常回復():
    """ラムのみ: ターン終了時に状態異常を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ラムのみ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("ねむり", None),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.ailment.is_active
    assert not mon.has_item()


def test_ラムのみ_状態異常とこんらんが重複しているとき同時に回復する():
    """ラムのみ: 発動時点で状態異常とこんらんが重複していた場合、両方を同時に回復し消費は1回のみ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ラムのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # アイテムを一時的に無効化した状態で状態異常とこんらんを付与する
    battle.item_manager.add_disabled_reason(mon, "マジックルーム")
    battle.ailment_manager.apply(mon, "まひ")
    battle.volatile_manager.apply(mon, "こんらん", count=3)
    assert mon.has_item()
    # アイテムの無効化を解除すると、ON_ITEM_ENABLEDで両方まとめて回復する
    battle.item_manager.remove_disabled_reason(mon, "マジックルーム")
    assert not mon.ailment.is_active
    assert not mon.has_volatile("こんらん")
    assert not mon.has_item()


def test_ラムのみ_状態異常もこんらんもないときは発動しない():
    """ラムのみ: 状態異常・こんらんのいずれもないときはターン終了時に発動せず消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ラムのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.has_item()


def test_ラムのみ_状態異常付与直後に即時回復する():
    """ラムのみ: 状態異常付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        team1=[Pokemon("カビゴン", item_name="ラムのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert not defender.has_item()


def test_リュガのみ_ぼうぎょランクが最大のとき発動しない():
    """リュガのみ: すでにぼうぎょランクが最大まで上がっているときはHP1/4以下でも発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="リュガのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.rank["def"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.rank["def"] == 6
    assert mon.has_item()


def test_ルームサービス_すばやさが下限のときは発動しない():
    """ルームサービス: すでにすばやさランクが下限のときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ルームサービス")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックルーム"])],
    )
    mon = battle.actives[0]
    mon.rank["spe"] = -6
    t.run_move(battle, 1)
    assert mon.rank["spe"] == -6
    assert mon.has_item()


def test_ルームサービス_トリックルームでS低下():
    """ルームサービス: トリックルーム発動時にすばやさ-1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ルームサービス")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックルーム"])],
    )
    t.run_move(battle, 1)
    mon = battle.actives[0]
    assert mon.rank["spe"] == -1
    assert not mon.has_item()


def test_ルームサービス_トリックルーム中に交代で場に出るとS低下():
    """ルームサービス: トリックルーム状態の場に繰り出したときもすばやさ-1が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コラッタ"), Pokemon("ピカチュウ", item_name="ルームサービス")],
        team1=[Pokemon("ピカチュウ")],
        field={"トリックルーム": 5},
    )
    t.run_switch(battle, 0, 1)
    mon = battle.actives[0]
    assert mon.rank["spe"] == -1
    assert not mon.has_item()


def test_ルームサービス_相手のトリックルームでもまけんきは発動しない():
    """ルームサービス: 相手が発動させたトリックルームによる低下では、まけんきなどの
    「相手による能力低下」を条件とする効果は発動しない（所持者自身の低下として扱われる）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="まけんき", item_name="ルームサービス")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックルーム"])],
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.rank["spe"] == -1
    assert mon.rank["atk"] == 0
    assert not mon.has_item()


def test_レッドカード_きゅうばんの相手は交代させられない():
    """レッドカード: 特性きゅうばんの相手は交代させられないが、アイテムは消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    attacker_name = battle.actives[1].name
    t.run_move(battle, 1)
    assert battle.actives[1].name == attacker_name
    assert not battle.actives[0].has_item()


def test_レッドカード_こらえるでHP1のまま耐えたときも発動する():
    """レッドカード: こらえるでHP1のまま耐えた（実ダメージ0）ときも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    holder = battle.actives[0]
    holder.hp = 1
    battle.volatile_manager.apply(holder, "こらえる")
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert holder.hp == 1
    assert not holder.fainted
    assert battle.actives[1].name == "ライチュウ"
    assert not holder.has_item()


def test_レッドカード_ちからずくの効果が発動した技を受けたときは発動しない():
    """レッドカード: 特性ちからずくの効果が発動した追加効果あり技を受けたときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("ニドキング", ability_name="ちからずく", move_names=["Gのちから"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    attacker_name = battle.actives[1].name
    t.run_move(battle, 1)
    assert battle.actives[1].name == attacker_name
    assert battle.actives[0].has_item("レッドカード")


def test_レッドカード_とらわれ状態でも交代できる():
    """レッドカード: バインドなどのとらわれ状態を無視して発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[1]
    battle.volatile_manager.apply(attacker, "バインド", count=4)

    t.run_move(battle, 1)

    assert battle.actives[1].name == "ライチュウ"
    assert not battle.actives[0].has_item()


def test_レッドカード_ねをはる状態の相手は交代させられない():
    """レッドカード: ねをはる状態の相手は交代させられないが、アイテムは消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("フシギダネ", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[1]
    battle.volatile_manager.apply(attacker, "ねをはる")

    t.run_move(battle, 1)

    assert battle.actives[1] is attacker
    assert not battle.actives[0].has_item()


def test_レッドカード_ばけのかわで肩代わりしたときも発動する():
    """レッドカード: 特性ばけのかわでダメージを肩代わりした場合（実ダメージ0）でも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばけのかわ", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    holder = battle.actives[0]
    t.fix_damage(battle, 30)

    t.run_move(battle, 1)

    assert holder.ability.enabled is False
    assert battle.actives[1].name == "ライチュウ"
    assert not holder.has_item()


def test_レッドカード_みがわりに阻まれたときは発動しない():
    """レッドカード: 持たせたポケモンがみがわりで攻撃を防いだときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    holder = battle.actives[0]
    battle.volatile_manager.apply(holder, "みがわり", hp=999)
    attacker_name = battle.actives[1].name

    t.run_move(battle, 1)

    assert battle.actives[1].name == attacker_name
    assert holder.has_item("レッドカード")


def test_レッドカード_交代先がいなければ発動しない():
    """レッドカード: 攻撃側に交代先がなければ強制交代しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    attacker_name = battle.actives[1].name
    t.run_move(battle, 1)
    assert battle.actives[1].name == attacker_name


def test_レッドカード_反動でひんしになった攻撃者には発動しない():
    """レッドカード: 攻撃者が反動技の反動でひんしになった場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["とっしん"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    holder = battle.actives[0]
    attacker = battle.actives[1]
    attacker.hp = 1
    t.fix_damage(battle, 50)

    t.run_move(battle, 1)

    assert attacker.fainted
    assert holder.has_item("レッドカード")


def test_レッドカード_持たせたポケモンがひんしになったときは発動しない():
    """レッドカード: 持たせたポケモンがひんしになった場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("カビゴン", move_names=["じしん"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    attacker_name = battle.actives[1].name
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert battle.actives[0].fainted
    assert battle.actives[1].name == attacker_name


def test_レッドカード_攻撃側のみがわりも交代させる():
    """レッドカード: 攻撃側がみがわり状態でも交代させることができる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[1]
    battle.volatile_manager.apply(attacker, "みがわり", hp=999)

    t.run_move(battle, 1)

    assert battle.actives[1].name == "ライチュウ"
    assert not battle.actives[0].has_item()


def test_レッドカード_攻撃側を強制交代():
    """レッドカード: ダメージを受けたとき攻撃者を強制交代させる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.actives[1].name == "ライチュウ"
    assert not battle.actives[0].has_item()


def test_レッドカード_自滅技でひんしになった攻撃者には発動しない():
    """レッドカード: 攻撃者が自滅技(だいばくはつ)でひんしになった場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["だいばくはつ"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    holder = battle.actives[0]
    t.fix_damage(battle, 50)

    t.run_move(battle, 1)

    assert battle.actives[1].fainted
    assert holder.has_item("レッドカード")


def test_レッドカード_連続攻撃技は最後のヒットの後に発動する():
    """レッドカード: 連続攻撃技は全ヒットが終わってから発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="レッドカード")],
        team1=[Pokemon("ピカチュウ", move_names=["ダブルアタック"]), Pokemon("ライチュウ")],
        accuracy=100,
    )
    holder = battle.actives[0]
    t.fix_damage(battle, 10)

    t.run_move(battle, 1)

    # 2ヒットとも通ったうえで、最後のヒットの後に交代する
    assert holder.hp == holder.max_hp - 20
    assert battle.actives[1].name == "ライチュウ"
    assert not holder.has_item()


def test_レンブのみ_マジシャンより先に発動して奪われない():
    """レンブのみ: 特性マジシャンの特殊技を受けても、レンブのみが先に発動して消費されるため奪われない
    （攻撃側の素早さが防御側より高い場合でも、素早さに依存せずレンブのみが先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="レンブのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.hp < attacker.max_hp
    assert not foe.has_item()
    assert not attacker.has_item()


def test_レンブのみ_マジックガードには発動しない():
    """レンブのみ: 攻撃してきた相手がマジックガード持ちの場合はダメージを与えず消費もされない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"], ability_name="マジックガード")],
        team1=[Pokemon("カビゴン", item_name="レンブのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp
    assert battle.actives[1].has_item()


def test_レンブのみ_特殊被弾で攻撃者にダメージ():
    """レンブのみ: 特殊技でダメージを受けたとき攻撃者に最大HPの1/8ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="レンブのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 8
    assert not battle.actives[1].has_item()


@pytest.mark.parametrize(
    "item_name, weather",
    [
        ("さらさらいわ", "すなあらし"),
        ("あついいわ", "はれ"),
        ("しめったいわ", "あめ"),
        ("つめたいいわ", "ゆき"),
    ]
)
def test_天候延長アイテム(item_name, weather):
    """天候延長アイテム: 対応天候の継続ターンを8に延長する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.weather_manager.apply(weather, 5, source=battle.actives[0])
    assert battle.raw_weather.count == 8


@pytest.mark.parametrize("item_name, mon_name, move_name, expected_modifier", [
    ("いしずえのめん", "オーガポン(いしずえ)", "たいあたり", 4915),
    ("いどのめん", "オーガポン(いど)", "たいあたり", 4915),
    ("かまどのめん", "オーガポン(かまど)", "たいあたり", 4915),
    ("でんきだま", "ピカチュウ", "たいあたり", 8192),
    ("でんきだま", "ピカチュウ", "でんきショック", 8192),
    ("でんきだま", "ピカチュウ(キョダイ)", "たいあたり", 8192),
    ("いしずえのめん", "オーガポン(いしずえ)", "エナジーボール", 4915),
    ("いどのめん", "オーガポン(いど)", "エナジーボール", 4915),
    ("かまどのめん", "オーガポン(かまど)", "エナジーボール", 4915),
])
def test_専用アイテム攻撃補正(item_name, mon_name, move_name, expected_modifier):
    """オーガポンのめん・でんきだま: 攻撃補正（atk_modifier）を上昇させる
    （オーガポンのめんは物理・特殊問わず攻撃技の威力を1.2倍にする）"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == expected_modifier


@pytest.mark.parametrize(
    "item_name, mon_name, move_name, expected_modifier",
    [
        ("こころのしずく", "ラティオス", "サイコキネシス", 4915),
        ("こころのしずく", "ラティアス", "ドラゴンクロー", 4915),
        ("こんごうだま", "ディアルガ", "ドラゴンクロー", 4915),
        ("こんごうだま", "ディアルガ", "アイアンヘッド", 4915),
        ("しらたま", "パルキア", "ドラゴンクロー", 4915),
        ("しらたま", "パルキア", "なみのり", 4915),
        ("だいこんごうだま", "ディアルガ", "ドラゴンクロー", 4915),
        ("だいしらたま", "パルキア", "ドラゴンクロー", 4915),
        ("だいはっきんだま", "ギラティナ(アナザー)", "シャドーボール", 4915),
        ("はっきんだま", "ギラティナ(アナザー)", "シャドーボール", 4915),
        ("はっきんだま", "ギラティナ(アナザー)", "ドラゴンクロー", 4915),
    ]
)
def test_専用アイテム補正(item_name, mon_name, move_name, expected_modifier):
    """専用アイテム: 対応ポケモンの対応タイプ技を1.2倍にする"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


@pytest.mark.parametrize("item_name, expected_ailment", [
    ("かえんだま", "やけど"),
    ("どくどくだま", "もうどく"),
])
def test_状態異常だま_ターン終了で状態異常付与(item_name, expected_ailment):
    """かえんだま・どくどくだま: ターン終了時に状態異常を付与する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name == expected_ailment


@pytest.mark.parametrize("item_name, ailment_name, ailment_count", [
    ("カゴのみ", "ねむり", 3),
    ("クラボのみ", "まひ", None),
    ("チーゴのみ", "やけど", None),
    ("ナナシのみ", "こおり", None),
    ("モモンのみ", "もうどく", None),
])
def test_状態異常回復きのみ_ターン終了で回復(item_name, ailment_name, ailment_count):
    """状態異常回復きのみ: ターン終了時に対応する状態異常を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(ailment_name, ailment_count),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name != ailment_name
    assert not mon.has_item()


@pytest.mark.parametrize("item_name, wrong_ailment, wrong_count", [
    ("カゴのみ", "まひ", None),
    ("クラボのみ", "ねむり", 3),
    ("チーゴのみ", "まひ", None),
    ("ナナシのみ", "まひ", None),
    ("モモンのみ", "まひ", None),
])
def test_状態異常回復きのみ_対象外状態では発動しない(item_name, wrong_ailment, wrong_count):
    """状態異常回復きのみ: 対応しない状態異常では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(wrong_ailment, wrong_count),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.has_item()


@pytest.mark.parametrize("item_name, move_name", [
    ("アッキのみ", "でんきショック"),
    ("レンブのみ", "たいあたり"),
])
def test_被弾反応きのみ_対応外の技ではアイテム消費しない(item_name, move_name):
    """アッキのみは特殊技で、レンブのみは物理技で発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ゼニガメ", item_name=item_name)],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.has_item()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
