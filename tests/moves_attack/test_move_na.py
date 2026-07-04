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


def test_なげつける_かえんだまでやけどを付与する():
    """なげつける: かえんだまを投げると命中後に相手にやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="かえんだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


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


def test_なげつける_でんきだまでまひを付与する():
    """なげつける: でんきだまを投げると命中後に相手にまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="でんきだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


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
    """にぎりつぶす: 相手のHPが1のとき威力は最低1（max(1, floor(120*1/max_hp))）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["にぎりつぶす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 1


def test_にぎりつぶす_相手HP半分のとき威力59():
    """にぎりつぶす: 相手のHPが半分のとき威力が約59になる。
    カビゴン max_hp=235, hp=117 → floor(120 * 117 / 235) = 59。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["にぎりつぶす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 59


def test_にぎりつぶす_相手HP満タンのとき威力120():
    """にぎりつぶす: 相手のHPが満タンのとき威力120。
    floor(120 * max_hp / max_hp) = 120。
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
