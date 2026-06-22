"""攻撃技ハンドラの単体テスト（は行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_どろぼう_攻撃者がアイテムを得て防御者がアイテムを失う():
    """どろぼう: 命中するとattackerが相手のアイテムを奪う。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どろぼう"])],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.item.name == "たべのこし"
    assert not defender.has_item()


def test_どろぼう_攻撃者がアイテムを持っているとき失敗():
    """どろぼう: 攻撃者がすでにアイテムを持っている場合は奪取しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どろぼう"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "オボンのみ"


def test_どろぼう_防御者がアイテムを持っていないとき失敗():
    """どろぼう: 相手がアイテムを持っていない場合は奪取しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どろぼう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.has_item()


def test_はたきおとす_相手のアイテムがないとき威力補正なし():
    """はたきおとす: 相手がアイテムを持っていない場合は威力1倍のまま。"""
    battle_no_item = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle_with_item = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        accuracy=100,
    )
    defender_no = battle_no_item.actives[1]
    defender_with = battle_with_item.actives[1]

    t.run_move(battle_no_item, 0)
    t.run_move(battle_with_item, 0)

    # アイテムあり版のほうがダメージが大きい
    assert defender_with.hp < defender_no.hp


def test_はたきおとす_相手のアイテムを失わせる():
    """はたきおとす: 命中すると相手のアイテムを失わせる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_item()


def test_はやてがえし_先制変化技には失敗():
    """はやてがえし: 先制変化技（まもる）には失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["まもる"])],
    )
    before_foe_hp = battle.actives[1].hp

    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp


def test_はやてがえし_先制攻撃技に成功():
    """はやてがえし: 相手が先制攻撃技を選んだ時のみ成功し、ひるませる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    battle.advance_turn()
    assert battle.actives[0].hp == battle.actives[0].max_hp
    assert battle.actives[1].hp < battle.actives[1].max_hp


def test_はやてがえし_通常攻撃技には失敗():
    """はやてがえし: 優先度0の攻撃技を選んだ相手には失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp


def test_バリアーラッシュ_防御1段階上昇が発動する():
    """バリアーラッシュ: 命中時に使用者のBが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バリアーラッシュ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["B"] == 1


def test_はがねのつばさ_防御1段階上昇が発動する():
    """はがねのつばさ: 確率10%で使用者のBが1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("スコルピ", move_names=["はがねのつばさ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert attacker.rank["B"] == 1


def test_ぶちかまし_防御と特防が各1段階低下する():
    """ぶちかまし: 命中時に使用者のBとDが各1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ぶちかまし"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["B"] == -1
    assert attacker.rank["D"] == -1


def test_ホイールスピン_素早さ2段階低下が発動する():
    """ホイールスピン: 命中時に使用者のSが2段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ドータクン", move_names=["ホイールスピン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["S"] == -2


def test_ほのおのまい_特攻1段階上昇が発動する():
    """ほのおのまい: 確率50%で使用者のCが1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ほのおのまい"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert attacker.rank["C"] == 1


def test_フレアソング_特攻1段階上昇が発動する():
    """フレアソング: 命中時に使用者のCが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ニャオハ", move_names=["フレアソング"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["C"] == 1
