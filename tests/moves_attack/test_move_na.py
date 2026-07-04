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


def test_なげつける_かえんだまでやけどを付与する():
    """なげつける: かえんだまを投げると命中後に相手にやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="かえんだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


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
