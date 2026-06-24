"""攻撃技ハンドラの単体テスト（や行・ら行・わ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_Ｖジェネレート_防御特防素早さが各1段階低下する():
    """Ｖジェネレート: 命中時に使用者のB/D/Sが各1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ビクティニ", move_names=["Ｖジェネレート"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["B"] == -1
    assert attacker.rank["D"] == -1
    assert attacker.rank["S"] == -1


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
