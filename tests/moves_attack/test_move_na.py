"""攻撃技ハンドラの単体テスト（な行）。"""

import pytest

from jpoke import Pokemon
from .. import test_utils as t


def test_ナイトバースト_命中率1段階低下が発動する():
    """ナイトバースト: 40%の確率で相手の命中率を1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゾロアーク", move_names=["ナイトバースト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["accuracy"] == -1


def test_ナイトヘッド_こらえるで1HP残る():
    """ナイトヘッド: 固定ダメージの計算がこらえるより先に行われ、瀕死を防げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ナイトヘッド"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
        volatile1={"こらえる": 1},
    )
    attacker, defender = battle.actives
    battle.modify_hp(defender, -(defender.hp - 1))
    t.run_move(battle, 0)
    assert defender.hp == 1
    assert not defender.fainted


def test_ナイトヘッド_ノーマルタイプには無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ナイトヘッド"])],
        team1=[Pokemon("カビゴン", move_names=["はねる"])],
    )
    battle.step()
    assert battle.actives[1].hp == battle.actives[1].max_hp


def test_ナイトヘッド_みがわりのHPを上限として肩代わりされる():
    """ナイトヘッド: みがわりの残りHPを上限として使用者レベル分のダメージが肩代わりされ、
    超過分は本体に持ち越されない（本体HPは変化しない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ナイトヘッド"])],
        team1=[Pokemon("ゲンガー")],
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


def test_ナイトヘッド_与ダメージは使用者レベル固定():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", level=50, move_names=["ナイトヘッド"])],
                            )
    before_hp = battle.actives[1].hp
    battle.step()
    assert before_hp - battle.actives[1].hp == 50


def test_なげつける_fling_powerゼロで失敗しアイテムを消費しない():
    """なげつける: fling_power=0のアイテムでは技が失敗し、アイテムが消費されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="だいこんごうだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_item()


def test_なげつける_アイテムなしで失敗する():
    """なげつける: アイテムを持っていない場合に技が失敗し、相手にダメージを与えない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_なげつける_アッキのみでぼうぎょランクが上がる():
    """なげつける: アッキのみを投げると命中後に相手のぼうぎょランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="アッキのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["def"] == 1


def test_なげつける_イアのみでHPを回復しこんらんしない性格の場合はこんらんしない():
    """なげつける: イアのみを投げると命中後に相手のHPを1/3回復するが、
    ぼうぎょが上がりにくくない性格（ようき）の場合はこんらんしない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="イアのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="ようき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert not defender.has_volatile("こんらん")


def test_なげつける_イアのみでHPを回復しこんらんする性格の場合はこんらんする():
    """なげつける: イアのみを投げると命中後に相手のHPを1/3回復し、
    ぼうぎょが上がりにくい性格（さみしがり）の場合はこんらんする。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="イアのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="さみしがり")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert defender.has_volatile("こんらん")


def test_なげつける_いのちのたまはダメージが1_3倍になるが反動を受けない():
    """なげつける: いのちのたまを投げるとダメージ計算には1.3倍補正が乗るが、
    投げた時点で使用者はいのちのたまを手放しているため反動ダメージは受けない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="いのちのたま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 5324
    assert attacker.hp == hp_before


def test_なげつける_ウイのみでHPを回復しこんらんしない性格の場合はこんらんしない():
    """なげつける: ウイのみを投げると命中後に相手のHPを1/3回復するが、
    とくこうが上がりにくくない性格（ようき）の場合はこんらんしない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ウイのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="ずぶとい")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert not defender.has_volatile("こんらん")


def test_なげつける_ウイのみでHPを回復しこんらんする性格の場合はこんらんする():
    """なげつける: ウイのみを投げると命中後に相手のHPを1/3回復し、
    とくこうが上がりにくい性格（いじっぱり）の場合はこんらんする。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ウイのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="いじっぱり")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert defender.has_volatile("こんらん")


def test_なげつける_オボンのみでHPを4分の1回復する():
    """なげつける: オボンのみを投げると命中後に相手のHPを最大HPの1/4回復する。

    技自体のダメージが回復量を上回らないよう、攻撃側をレベル1にしてダメージを最小限にする。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="オボンのみ", move_names=["なげつける"], level=1)],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before


def test_なげつける_オレンのみでHPを10回復する():
    """なげつける: オレンのみを投げると命中後に相手のHPを固定10回復する。

    技自体のダメージが回復量を上回らないよう、攻撃側をレベル1にしてダメージを最小限にする。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="オレンのみ", move_names=["なげつける"], level=1)],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before


def test_なげつける_おんみつマントを持つ相手には追加効果が発動しない():
    """なげつける: 相手がおんみつマントを持つ場合、追加効果（でんきだまのまひ付与）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="でんきだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", item_name="おんみつマント")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_なげつける_オーガポンが仮面を使うと失敗する():
    """なげつける: オーガポンが仮面（いしずえのめん・いどのめん・かまどのめん）を使用すると失敗し、
    アイテムを消費しない（それ以外のポケモンが使用した場合は通常通り威力60で成功する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いど)", item_name="いどのめん", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_item()


def test_なげつける_オーガポン以外が仮面を使うと成功する():
    """なげつける: オーガポン以外が仮面を使用した場合は通常通り威力60で成功する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="いどのめん", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_なげつける_かえんだまでやけどを付与する():
    """なげつける: かえんだまを投げると命中後に相手にやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="かえんだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_なげつける_カゴのみでねむりを回復する():
    """なげつける: カゴのみを投げると命中後に相手のねむりを回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="カゴのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "ねむり", count=3)
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_なげつける_カムラのみですばやさランクが上がる():
    """なげつける: カムラのみを投げると命中後に相手のすばやさランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="カムラのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["spe"] == 1


def test_なげつける_キーのみでこんらんを解除する():
    """なげつける: キーのみを投げると命中後に相手のこんらんを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="キーのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "こんらん", source=battle.actives[0])
    t.run_move(battle, 0)
    assert not defender.has_volatile("こんらん")


def test_なげつける_クラボのみでまひを回復する():
    """なげつける: クラボのみを投げると命中後に相手のまひを回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="クラボのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "まひ")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_なげつける_クラボのみは対象外の状態異常を回復しない():
    """なげつける: クラボのみはまひ以外の状態異常（やけど）を回復しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="クラボのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "やけど")
    t.run_move(battle, 0)
    assert defender.ailment.name == "やけど"


def test_なげつける_サンのみできゅうしょアップを付与する():
    """なげつける: サンのみを投げると命中後に相手をきゅうしょアップ状態にする（count=2）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="サンのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("きゅうしょアップ")
    assert defender.volatiles["きゅうしょアップ"].count == 2


def test_なげつける_スターのみでランダムな能力ランクが2段階上がる():
    """なげつける: スターのみを投げると命中後に相手のランクが最大でない能力から
    ランダムに1つ選び+2する。ランクが最大の能力は候補から除外される。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="スターのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    for stat in ("atk", "def", "spa", "spd"):
        defender.rank[stat] = 6
    battle.random.choice = lambda seq: seq[0]  # 候補が1つ（すばやさ）のみになる
    t.run_move(battle, 0)
    assert defender.rank["spe"] == 2


def test_なげつける_ズアのみでとくぼうランクが上がる():
    """なげつける: ズアのみを投げると命中後に相手のとくぼうランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ズアのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["spd"] == 1


def test_なげつける_タラプのみでとくぼうランクが上がる():
    """なげつける: タラプのみを投げると命中後に相手のとくぼうランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="タラプのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["spd"] == 1


def test_なげつける_ダメージを与えアイテムを消費する():
    """なげつける: アイテムありで攻撃が成功し、アイテムが消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="いのちのたま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_なげつける_チイラのみでこうげきランクが上がる():
    """なげつける: チイラのみを投げると命中後に相手のこうげきランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="チイラのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["atk"] == 1


def test_なげつける_チーゴのみでやけどを回復する():
    """なげつける: チーゴのみを投げると命中後に相手のやけどを回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="チーゴのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "やけど")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_なげつける_でんきだまでまひを付与する():
    """なげつける: でんきだまを投げると命中後に相手にまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="でんきだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_なげつける_どくどくだまでもうどくを付与する():
    """なげつける: どくどくだまを投げると命中後に相手にもうどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくどくだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_なげつける_どくバリでどくを付与する():
    """なげつける: どくバリを投げると命中後に相手にどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくバリ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_なげつける_ナナシのみでこおりを回復する():
    """なげつける: ナナシのみを投げると命中後に相手のこおりを回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ナナシのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


@pytest.mark.parametrize("mon_name", ["ギラティナ(アナザー)", "ギラティナ(オリジン)"])
def test_なげつける_はっきんだまをギラティナが使うと失敗する(mon_name):
    """なげつける: はっきんだまはギラティナ(アナザー/オリジン問わず)が使用すると失敗し、アイテムを消費しない。"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name="はっきんだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_item()


def test_なげつける_バンジのみでHPを回復しこんらんしない性格の場合はこんらんしない():
    """なげつける: バンジのみを投げると命中後に相手のHPを1/3回復するが、
    とくぼうが上がりにくくない性格（いじっぱり）の場合はこんらんしない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="バンジのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="いじっぱり")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert not defender.has_volatile("こんらん")


def test_なげつける_バンジのみでHPを回復しこんらんする性格の場合はこんらんする():
    """なげつける: バンジのみを投げると命中後に相手のHPを1/3回復し、
    とくぼうが上がりにくい性格（やんちゃ）の場合はこんらんする。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="バンジのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="やんちゃ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert defender.has_volatile("こんらん")


def test_なげつける_ヒメリのみでPPが0の技のPPを10回復する():
    """なげつける: ヒメリのみを投げると命中後に相手のPPが0の技のPPを10回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ヒメリのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.moves[0].pp = 0
    t.run_move(battle, 0)
    assert defender.moves[0].pp == 10


def test_なげつける_フィラのみでHPを回復しこんらんしない性格の場合はこんらんしない():
    """なげつける: フィラのみを投げると命中後に相手のHPを1/3回復するが、
    こうげきが上がりにくくない性格（ようき）の場合はこんらんしない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="フィラのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="ようき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert not defender.has_volatile("こんらん")


def test_なげつける_フィラのみでHPを回復しこんらんする性格の場合はこんらんする():
    """なげつける: フィラのみを投げると命中後に相手のHPを1/3回復し、
    こうげきが上がりにくい性格（ひかえめ）の場合はこんらんする。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="フィラのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="ひかえめ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert defender.has_volatile("こんらん")


def test_なげつける_ぶきようを持つ攻撃側は失敗する():
    """なげつける: 使用者の特性がぶきようの場合、アイテムが無効化されているため失敗し、
    アイテムを消費しない（現行世代の仕様）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ぶきよう", item_name="いのちのたま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_item()


@pytest.mark.parametrize(
    "ability_name, field_ability_name",
    [
        ("こだいかっせい", "ひでり"),
        ("クォークチャージ", "エレキメイカー"),
    ],
)
def test_なげつける_ブーストエナジーをパラドックス特性持ちが使うと失敗する(ability_name, field_ability_name):
    """なげつける: ブーストエナジーはこだいかっせい/クォークチャージ持ちが使用すると失敗し、アイテムを消費しない。
    相手の場発動特性（ひでり/エレキメイカー）は登場時優先度がパラドックス特性の判定より先に発動するため、
    同時に登場させることで場由来のブーストを先に発動させ、アイテムを未消費のまま維持できる。
    """
    battle = t.start_battle(
        team0=[Pokemon(
            "カビゴン", ability_name=ability_name, item_name="ブーストエナジー", move_names=["なげつける"]
        )],
        team1=[Pokemon("カビゴン", ability_name=field_ability_name)],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert attacker.has_item("ブーストエナジー")
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_item("ブーストエナジー")


def test_なげつける_ブーストエナジーを通常特性持ちが使うと成功する():
    """なげつける: パラドックス特性を持たないポケモンがブーストエナジーを投げると通常通り成功する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ブーストエナジー", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_なげつける_マゴのみでHPを回復しこんらんしない性格の場合はこんらんしない():
    """なげつける: マゴのみを投げると命中後に相手のHPを1/3回復するが、
    すばやさが上がりにくくない性格（いじっぱり）の場合はこんらんしない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="マゴのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="いじっぱり")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert not defender.has_volatile("こんらん")


def test_なげつける_マゴのみでHPを回復しこんらんする性格の場合はこんらんする():
    """なげつける: マゴのみを投げると命中後に相手のHPを1/3回復し、
    すばやさが上がりにくい性格（ゆうかん）の場合はこんらんする。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="マゴのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", nature="ゆうかん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp > hp_before
    assert defender.has_volatile("こんらん")


def test_なげつける_マジックルーム中は失敗する():
    """なげつける: 場がマジックルーム状態の場合、アイテムが無効化されているため失敗し、
    アイテムを消費しない（現行世代の仕様）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="いのちのたま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        field={"マジックルーム": 5},
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_item()


def test_なげつける_ミクルのみでめいちゅうアップを付与する():
    """なげつける: ミクルのみを投げると命中後に相手をめいちゅうアップ状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ミクルのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("めいちゅうアップ")


def test_なげつける_ミクルのみで付与しためいちゅうアップが命中率を1_2倍にし消費される():
    """めいちゅうアップ: 付与された状態で技を使うと命中率が1.2倍になり、効果が消費される。

    2回目の技では通常の命中率に戻ることも合わせて確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ", move_names=["ハイドロポンプ"])],
        volatile1={"めいちゅうアップ": None},
    )
    mon = battle.actives[1]
    move = t.run_move(battle, 1)
    assert battle.move_executor.accuracy == move.accuracy * 4915 // 4096
    assert not mon.has_volatile("めいちゅうアップ")

    # 消費済みのため2回目の技では通常の命中率に戻る
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == move.accuracy


def test_なげつける_ミクルのみで付与しためいちゅうアップは外れても消費される():
    """めいちゅうアップ: 技が外れた場合でも効果は消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ", move_names=["ハイドロポンプ"])],
        volatile1={"めいちゅうアップ": None},
    )
    mon = battle.actives[1]
    t.fix_random(battle, 0.97)  # 補正後命中率95に対し97で外れる
    t.run_move(battle, 1)
    assert battle.move_executor.move_missed
    assert not mon.has_volatile("めいちゅうアップ")


def test_なげつける_メンタルハーブでアンコールを解除する():
    """なげつける: メンタルハーブを投げると命中後に相手のアンコールを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メンタルハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "アンコール", move_name="たいあたり")
    t.run_move(battle, 0)
    assert not defender.has_volatile("アンコール")


def test_なげつける_メンタルハーブでいちゃもんを解除する():
    """なげつける: メンタルハーブを投げると命中後に相手のいちゃもんを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メンタルハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "いちゃもん", source=battle.actives[0])
    t.run_move(battle, 0)
    assert not defender.has_volatile("いちゃもん")


def test_なげつける_メンタルハーブでかいふくふうじを解除する():
    """なげつける: メンタルハーブを投げると命中後に相手のかいふくふうじを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メンタルハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "かいふくふうじ", source=battle.actives[0])
    t.run_move(battle, 0)
    assert not defender.has_volatile("かいふくふうじ")


def test_なげつける_メンタルハーブでかなしばりを解除する():
    """なげつける: メンタルハーブを投げると命中後に相手のかなしばりを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メンタルハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "かなしばり", count=4, move_name="たいあたり")
    t.run_move(battle, 0)
    assert not defender.has_volatile("かなしばり")


def test_なげつける_メンタルハーブでこんらんは解除しない():
    """なげつける: メンタルハーブを投げても対象外の揮発性状態（こんらん）は解除しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メンタルハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "こんらん", source=battle.actives[0])
    t.run_move(battle, 0)
    assert defender.has_volatile("こんらん")


def test_なげつける_メンタルハーブでちょうはつを解除する():
    """なげつける: メンタルハーブを投げると命中後に相手のちょうはつを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メンタルハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "ちょうはつ", count=3)
    t.run_move(battle, 0)
    assert not defender.has_volatile("ちょうはつ")


def test_なげつける_メンタルハーブでメロメロを解除する():
    """なげつける: メンタルハーブを投げると命中後に相手のメロメロを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メンタルハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "メロメロ", source=battle.actives[0])
    t.run_move(battle, 0)
    assert not defender.has_volatile("メロメロ")


def test_なげつける_メンタルハーブで複数のメンタル系状態を同時に解除する():
    """なげつける: メンタルハーブを投げると命中後に相手の複数のメンタル系状態を同時に解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メンタルハーブ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "いちゃもん", source=battle.actives[0])
    battle.volatile_manager.apply(defender, "ちょうはつ", count=3)
    t.run_move(battle, 0)
    assert not defender.has_volatile("いちゃもん")
    assert not defender.has_volatile("ちょうはつ")


def test_なげつける_モモンのみでどくを回復する():
    """なげつける: モモンのみを投げると命中後に相手のどくを回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="モモンのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "どく")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_なげつける_モモンのみでもうどくを回復する():
    """なげつける: モモンのみを投げると命中後に相手のもうどくを回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="モモンのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "もうどく")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_なげつける_ヤタピのみでとくこうランクが上がる():
    """なげつける: ヤタピのみを投げると命中後に相手のとくこうランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ヤタピのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["spa"] == 1


def test_なげつける_ラムのみでこんらんを解除する():
    """なげつける: ラムのみを投げると命中後に相手のこんらんを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ラムのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "こんらん", source=battle.actives[0])
    t.run_move(battle, 0)
    assert not defender.has_volatile("こんらん")


def test_なげつける_ラムのみで状態異常とこんらんを同時に解除する():
    """なげつける: ラムのみを投げると命中後に相手の状態異常とこんらんを同時に解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ラムのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "まひ")
    battle.volatile_manager.apply(defender, "こんらん", source=battle.actives[0])
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert not defender.has_volatile("こんらん")


def test_なげつける_ラムのみで状態異常を解除する():
    """なげつける: ラムのみを投げると命中後に相手の状態異常を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ラムのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "やけど")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_なげつける_リュガのみでぼうぎょランクが上がる():
    """なげつける: リュガのみを投げると命中後に相手のぼうぎょランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="リュガのみ", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["def"] == 1


def test_なげつける_りんぷんを持つ相手には追加効果が発動しない():
    """なげつける: 相手の特性がりんぷんの場合、追加効果（でんきだまのまひ付与）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="でんきだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", ability_name="りんぷん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_なげつける_外れてもアイテムを消費する():
    """なげつける: 命中しなかった場合でもON_MOVE_ENDが発火してアイテムが消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="いのちのたま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_item()


def test_なみのり_相手にダメージを与える():
    """なみのり: 追加効果なしの特殊みず技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["なみのり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_にぎりつぶす_相手HP1のとき威力1():
    """にぎりつぶす: 相手のHPが1のとき威力は最低1（max(1, round_half_down(120*1/max_hp))）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["にぎりつぶす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 1


def test_にぎりつぶす_相手HP半分のとき威力60():
    """にぎりつぶす: 相手のHPが半分のとき威力が約60になる（端数は五捨五超入で丸める）。
    カビゴン max_hp=235, hp=117 → round_half_down(120 * 117 / 235) = round_half_down(59.744...) = 60。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["にぎりつぶす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 60


def test_にぎりつぶす_相手HP満タンのとき威力120():
    """にぎりつぶす: 相手のHPが満タンのとき威力120。
    round_half_down(120 * max_hp / max_hp) = 120。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["にぎりつぶす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp  # 満タン
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 120


def test_にどげり_命中判定1回で2回ヒットする():
    """にどげり: 命中判定は1回だけで、2ヒットする。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にどげり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


def test_ニードルアーム_ひるみが発動する():
    """ニードルアーム: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ニードルアーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ねこだまし_ひるみが発動する():
    """ねこだまし: 100%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ニャース", move_names=["ねこだまし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ねこだまし_交代後の最初の行動では成功する():
    """ねこだまし: 交代で場に出た直後の最初の行動では成功する。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ヘラクロス", move_names=["たいあたり"]),
            Pokemon("ニャース", move_names=["ねこだまし"]),
        ],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # 場に出ているポケモンの最初の行動を消費する
    t.run_move(battle, 0, 0)
    # 交代（ニャースにとっては場に出てから最初の行動）
    t.run_switch(battle, 0, 1)
    t.run_move(battle, 0, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ねこだまし_場に出てから最初の行動でなければ失敗する():
    """ねこだまし: 場に出てから最初の行動でなければ失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ニャース", move_names=["たいあたり", "ねこだまし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # 場に出てから最初の行動として別の技を使用する
    t.run_move(battle, 0, 0)
    # 2回目の行動としてねこだましを使用 → 失敗する
    t.run_move(battle, 0, 1)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_ネズミざん_命中率0で全て外れる():
    """ネズミざん: check_hit_each_time=Trueのため、命中率0では1発目から外れ、0回ヒットする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ネズミざん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 0


def test_ネズミざん_最大10回ヒットする():
    """ネズミざん: 命中判定を各回行い、最大10回ヒットする（check_hit_each_time=True）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ネズミざん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 10


def test_ねっさのあらし_あめ中は必中になる():
    """ねっさのあらし: あめ天候中は命中率80でも通常なら外れる乱数で命中する。

    ねっさのあらしの命中率は80。random.random()=0.9 のとき 100*0.9=90>80 で本来は外れるが、
    あめ中はON_MODIFY_ACCURACYでNoneが返り必中になるため、命中してHPが減る。
    """
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっさのあらし"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    # random.random()=0.9 は命中率80未満ではない（90>80）ので通常は外れる
    battle.random.random = lambda: 0.9
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ねっさのあらし_やけどが発動する():
    """ねっさのあらし: 20%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっさのあらし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ねっさのだいち_こおり状態で使うと解凍されて攻撃できる():
    """ねっさのだいち: こおり状態でも使用でき、使うと解凍される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっさのだいち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # こおり状態を付与してから使用
    t.apply_ailment(battle, 0, "こおり")
    assert attacker.ailment.name == "こおり"
    hp_before = defender.hp
    t.run_move(battle, 0)
    # こおりが解除されてダメージを与えられる
    assert not attacker.ailment.is_active
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before


def test_ねっさのだいち_こおり状態の相手に当てると解凍する():
    """ねっさのだいち: じめんタイプだが、被弾した相手のこおりを解凍する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっさのだいち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_ねっさのだいち_やけどが発動する():
    """ねっさのだいち: 30%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっさのだいち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ねっとう_こおり状態で使うと解凍されて攻撃できる():
    """ねっとう: こおり状態でも使用でき、使うと解凍される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっとう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # こおり状態を付与してから使用
    t.apply_ailment(battle, 0, "こおり")
    assert attacker.ailment.name == "こおり"
    hp_before = defender.hp
    t.run_move(battle, 0)
    # こおりが解除されてダメージを与えられる
    assert not attacker.ailment.is_active
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before


def test_ねっとう_こおり状態の相手に命中しても同一ヒットではやけどにならない():
    """ねっとう: こおりを解凍する処理はやけど付与判定の後に発動するため、
    こおり状態の相手に命中した瞬間はやけどが付与されない
    （こおりが残っているため『やけど』を重ねて付与できない）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっとう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert defender.ailment.name != "やけど"


def test_ねっとう_こおり状態の相手に当てると解凍する():
    """ねっとう: みずタイプだが、被弾した相手のこおりを解凍する（第六世代以降）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっとう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_ねっとう_やけどが発動する():
    """ねっとう: 30%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねっとう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ねっぷう_やけどが発動する():
    """ねっぷう: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ねっぷう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ねらいうち_よびみずに直接使用すると無効化される():
    """ねらいうち: 引き寄せ無効化はダブル専用で対象外だが、よびみずに直接使用した場合は
    通常のみず技と同様に無効化されとくこうが上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ねらいうち"])],
        team1=[Pokemon("ラプラス", ability_name="よびみず")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert defender.rank["spa"] == 1


def test_ねらいうち_急所ランクが1():
    """ねらいうち: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ねらいうち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_ねらいうち_急所ランクが1_乱数大で急所なし():
    """ねらいうち: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ねらいうち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_ねらいうち_相手にダメージを与える():
    """ねらいうち: 追加効果なしの特殊みず技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ねらいうち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ねんりき_こんらんが発動する():
    """ねんりき: 10%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ねんりき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_のしかかり_まひが発動しない():
    """のしかかり: secondary_chanceが0のときまひを付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["のしかかり"])],
        team1=[Pokemon("リザードン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_のしかかり_まひが発動する():
    """のしかかり: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["のしかかり"])],
        team1=[Pokemon("リザードン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"
