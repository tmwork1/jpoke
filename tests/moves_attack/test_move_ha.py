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


def test_はがねのつばさ_防御1段階上昇が発動する():
    """はがねのつばさ: 確率10%で使用者のBが1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("スコルピ", move_names=["はがねのつばさ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["B"] == 1


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


def test_はっけい_まひが発動する():
    """はっけい: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["はっけい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_はめつのひかり_使用後に攻撃者が反動ダメージを受ける():
    """はめつのひかり: 与えたダメージの1/2を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["はめつのひかり"])],
        team1=[Pokemon("フーディン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


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


def test_ハートスタンプ_ひるみが発動する():
    """ハートスタンプ: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ハートスタンプ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ハードローラー_ひるみが発動する():
    """ハードローラー: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ハードローラー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ばくれつパンチ_こんらんが発動する():
    """ばくれつパンチ: 100%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ばくれつパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


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


def test_バーンアクセル_やけどが発動する():
    """バーンアクセル: 30%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["バーンアクセル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_パラボラチャージ_使用後に攻撃者のHPが回復する():
    """パラボラチャージ: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パラボラチャージ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_ひっさつまえば_ひるみが発動する():
    """ひっさつまえば: 10%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ひっさつまえば"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ひのこ_やけどが発動する():
    """ひのこ: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ひのこ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ひゃっきやこう_やけどが発動する():
    """ひゃっきやこう: 30%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ひゃっきやこう"])],
        team1=[Pokemon("フーディン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ひょうざんおろし_ひるみが発動する():
    """ひょうざんおろし: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["ひょうざんおろし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ビックリヘッド_HP消費が最大HPの半分である():
    """ビックリヘッド: 使用前に自分の最大HPの1/2を消費する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ビックリヘッド"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    expected_cost = max(1, attacker.max_hp // 2)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_cost


def test_ビックリヘッド_HP消費後HP0でも相手にダメージを与える():
    """ビックリヘッド: HP消費後にHP0になっても攻撃は相手に届く。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ビックリヘッド"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # HP消費でちょうど0になるように設定
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert defender.hp < defender.max_hp


def test_ビックリヘッド_contactラベルを持つ():
    """ビックリヘッド: 物理接触技のためcontactラベルを持つ。"""
    from jpoke.data.move import MOVES
    move_data = MOVES["ビックリヘッド"]
    assert "contact" in move_data.labels


def test_びりびりちくちく_ひるみが発動する():
    """びりびりちくちく: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["びりびりちくちく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ピヨピヨパンチ_こんらんが発動する():
    """ピヨピヨパンチ: 20%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ピヨピヨパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_フェイタルクロー_状態異常が発動する():
    """フェイタルクロー: 50%でどく/まひ/こおりのいずれかを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["フェイタルクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name in ("どく", "まひ", "こおり")


def test_ふぶき_こおりが発動する():
    """ふぶき: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["ふぶき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_ふみつけ_ひるみが発動する():
    """ふみつけ: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ふみつけ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_フリーズドライ_こおりが発動する():
    """フリーズドライ: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["フリーズドライ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_フリーズボルト_まひが発動する():
    """フリーズボルト: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["フリーズボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


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


def test_フレアドライブ_やけどが発動する():
    """フレアドライブ: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["フレアドライブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_フレアドライブ_使用後に攻撃者が反動ダメージを受ける():
    """フレアドライブ: 与えたダメージの1/3を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["フレアドライブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_ふわふわフォール_ひるみが発動する():
    """ふわふわフォール: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("クレッフィ", move_names=["ふわふわフォール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ふんえん_やけどが発動する():
    """ふんえん: 30%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ふんえん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


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


def test_ブレイズキック_やけどが発動する():
    """ブレイズキック: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ブレイズキック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ブレイブバード_使用後に攻撃者が反動ダメージを受ける():
    """ブレイブバード: 与えたダメージの1/3を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ブレイブバード"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_ヘドロウェーブ_どくが発動する():
    """ヘドロウェーブ: 10%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ヘドロウェーブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_ヘドロこうげき_どくが発動する():
    """ヘドロこうげき: 30%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ヘドロこうげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_ヘドロばくだん_どくが発動する():
    """ヘドロばくだん: 30%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ヘドロばくだん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


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


def test_ほうでん_まひが発動する():
    """ほうでん: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほうでん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_ホネこんぼう_ひるみが発動する():
    """ホネこんぼう: 10%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カラカラ", move_names=["ホネこんぼう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ほのおのキバ_やけどかひるみが発動する():
    """ほのおのキバ: 10%でやけどかひるみのどちらかを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ほのおのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    defender = battle.actives[1]
    assert defender.ailment.name == "やけど" or defender.has_volatile("ひるみ")


def test_ほのおのパンチ_やけどが発動する():
    """ほのおのパンチ: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ほのおのまい_特攻1段階上昇が発動する():
    """ほのおのまい: 確率50%で使用者のCが1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ほのおのまい"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["C"] == 1


def test_ぼうふう_こんらんが発動する():
    """ぼうふう: 30%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["ぼうふう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_ボルテッカー_まひが発動する():
    """ボルテッカー: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ボルテッカー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_ボルテッカー_使用後に攻撃者が反動ダメージを受ける():
    """ボルテッカー: 与えたダメージの1/4を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ボルテッカー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_ポイズンアクセル_どくが発動する():
    """ポイズンアクセル: 30%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ポイズンアクセル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_ポイズンテール_どくが発動する():
    """ポイズンテール: 10%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ポイズンテール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_もろはのずつき_使用後に攻撃者が反動ダメージを受ける():
    """もろはのずつき: 与えたダメージの1/2を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["もろはのずつき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before
