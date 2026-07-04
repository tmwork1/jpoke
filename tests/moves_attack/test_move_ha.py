"""攻撃技ハンドラの単体テスト（は行）。"""

from jpoke import Pokemon
from jpoke.data.move import MOVES
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


def test_ハイドロカノン_命中後にリチャージ状態が付与される():
    """ハイドロカノン: 命中後に使用者にリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ハイドロカノン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")


def test_ハイドロカノン_次ターン行動不能になる():
    """ハイドロカノン: 次のターンはリチャージ状態により行動不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ハイドロカノン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.step()
    assert attacker.has_volatile("リチャージ")
    defender_hp_after_t1 = defender.hp
    battle.step()
    assert not attacker.has_volatile("リチャージ")
    assert defender.hp == defender_hp_after_t1


def test_ハイドロスチーム_にほんばれで威力1_5倍():
    """ハイドロスチーム: にほんばれ中は晴れ弱体化をキャンセルし、威力が1.5倍（6144）になる。

    フィールドハンドラが0.5倍（2048）を適用後、ハイドロスチームハンドラが3倍（12288）を
    乗算して最終的に 6144（1.5x）になる。
    """
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ハイドロスチーム"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_ハイドロスチーム_攻撃側ばんのうがさのとき晴れで0_5倍():
    """ハイドロスチーム: 攻撃側がばんのうがさを持つ場合、晴れでも1.5倍効果は発動しない。

    通常みず技と同様に晴れの0.5倍弱体化（2048）のみが適用される。
    """
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ハイドロスチーム"], item_name="ばんのうがさ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 2048


def test_ハイドロスチーム_晴れなしのとき補正なし():
    """ハイドロスチーム: 晴れ天候なしのとき威力補正は等倍（4096）のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ハイドロスチーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ハイドロスチーム_防御側ばんのうがさのとき晴れでも1_5倍():
    """ハイドロスチーム: 防御側がばんのうがさを持つ場合でも、晴れ中は1.5倍（6144）になる。

    フィールドハンドラの0.5倍は防御側ばんのうがさで無効になるが、
    ハイドロスチームハンドラは攻撃側の天候認識で発動し、直接1.5倍（6144）を適用する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ハイドロスチーム"])],
        team1=[Pokemon("カビゴン", item_name="ばんのうがさ")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_ハイドロポンプ_相手にダメージを与える():
    """ハイドロポンプ: 追加効果なしの特殊みず技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["ハイドロポンプ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ハイパードリル_まもる中の相手にダメージが入る():
    """ハイパードリル: unprotectableフラグを持つため、まもる状態の相手にもダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ハイパードリル"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ハイパーボイス_みがわりを貫通して本体にダメージを与える():
    """ハイパーボイス: soundラベルを持つため、みがわり状態の相手の本体にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ニンフィア", move_names=["ハイパーボイス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    # みがわりにHPを設定（貫通しなければこのHPが削られる）
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    # 音技はみがわりを無視して本体にダメージを与えるため、本体HPが減る
    assert defender.hp < hp_before
    # みがわりのHPは変化しない
    assert defender.volatiles["みがわり"].hp == 999


def test_はかいこうせん_まもるで防がれた場合はリチャージ状態にならない():
    """はかいこうせん: まもるで防がれた場合はリチャージ揮発状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はかいこうせん"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("リチャージ")


def test_はかいこうせん_交代するとリチャージ状態が解除される():
    """はかいこうせん: リチャージ状態中に交代するとリチャージ揮発状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はかいこうせん"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")
    t.run_switch(battle, 0, 1)
    assert not attacker.has_volatile("リチャージ")


def test_はかいこうせん_命中後にリチャージ状態が付与される():
    """はかいこうせん: 命中後に使用者にリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はかいこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")


def test_はかいこうせん_外れた場合はリチャージ状態にならない():
    """はかいこうせん: 外れた場合はリチャージ揮発状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はかいこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("リチャージ")


def test_はかいこうせん_次ターン行動不能になる():
    """はかいこうせん: 次のターンはリチャージ状態により行動不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はかいこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.step()
    assert attacker.has_volatile("リチャージ")
    defender_hp_after_t1 = defender.hp
    battle.step()
    assert not attacker.has_volatile("リチャージ")
    assert defender.hp == defender_hp_after_t1


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
    assert attacker.rank["def"] == 1


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


def test_はたく_相手にダメージを与える():
    """はたく: 追加効果なしの物理ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はたく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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


def test_はなびらのまい_カウント終了後にこんらんが付与される():
    """はなびらのまい: カウントが0になった後にこんらん状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("フラージェス", move_names=["はなびらのまい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=1, source=attacker, move_name="はなびらのまい")
    t.run_move(battle, 0)
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


def test_はなびらのまい_初回命中時にあばれる揮発状態が付与される():
    """はなびらのまい: 初回命中時にあばれる揮発状態（強制行動）が付与される。特殊くさ接触ダンス技。"""
    battle = t.start_battle(
        team0=[Pokemon("フラージェス", move_names=["はなびらのまい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("あばれる")


def test_はなふぶき_相手にダメージを与える():
    """はなふぶき: 追加効果なしの物理くさ技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["はなふぶき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_はめつのねがい_2ターン後に相手にダメージが入る():
    """はめつのねがい: 使用から2ターン後のターン終了時に相手へダメージが発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["はめつのねがい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    t.end_turn(battle)  # count: 2 → 1、まだダメージなし
    assert defender.hp == hp_before
    t.end_turn(battle)  # count: 1 → 0 → フィールド解除 → ダメージ発生
    assert defender.hp < hp_before


def test_はめつのねがい_2回連続使用で失敗する():
    """はめつのねがい: 相手陣にすでにフィールドが存在する場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["はめつのねがい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)  # 1回目: 成功してフィールド設置
    t.run_move(battle, 0)  # 2回目: フィールド存在により失敗
    assert battle.move_executor.move_success is False


def test_はめつのねがい_使用ターンには攻撃が発動しない():
    """はめつのねがい: 使用ターンには即時攻撃が発動せず、相手にダメージを与えない。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["はめつのねがい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_はめつのねがい_相手陣にフィールドが設置される():
    """はめつのねがい: 使用後に相手陣営に「はめつのねがい」サイドフィールドが設置される。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["はめつのねがい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    foe_side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)
    assert foe_side.get("はめつのねがい").is_active


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


def test_はめつのひかり_反動ダメージが与ダメの2分の1になる():
    """はめつのひかり: 反動量は max(1, int(与ダメ * 1/2)) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["はめつのひかり"])],
        team1=[Pokemon("フーディン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/2)) = 50
    assert attacker.hp == hp_before - 50


def test_はやてがえし_ひるみが発動する():
    """はやてがえし: 命中時に100%でひるみを付与し、相手は行動できない。

    ひるみは付与された同ターンに消費されるため、step 後は既に解除されている。
    ひるみにより相手（でんこうせっか）は行動できず、こちらはダメージを受けないことで検証する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    attacker_hp_before = battle.actives[0].max_hp
    battle.step()
    # ひるみにより相手（でんこうせっか）は行動できず、こちらはダメージを受けない
    assert battle.actives[0].hp == attacker_hp_before


def test_はやてがえし_先制変化技には失敗():
    """はやてがえし: 先制変化技（まもる）には失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["まもる"])],
    )
    before_foe_hp = battle.actives[1].hp

    battle.step()

    assert battle.actives[1].hp == before_foe_hp


def test_はやてがえし_先制攻撃技に成功():
    """はやてがえし: 相手が先制攻撃技を選んだ時のみ成功し、ひるませる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はやてがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    battle.step()
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

    battle.step()

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


def test_ハードプラント_命中後にリチャージ状態が付与される():
    """ハードプラント: 命中後に使用者にリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["ハードプラント"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")


def test_ハードプラント_次ターン行動不能になる():
    """ハードプラント: 次のターンはリチャージ状態により行動不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["ハードプラント"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.step()
    assert attacker.has_volatile("リチャージ")
    defender_hp_after_t1 = defender.hp
    battle.step()
    assert not attacker.has_volatile("リチャージ")
    assert defender.hp == defender_hp_after_t1


def test_ハードプレス_相手HP1のとき威力1():
    """ハードプレス: 相手のHPが1のとき威力は最低1（max(1, floor(100*1/max_hp))）。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["ハードプレス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 1


def test_ハードプレス_相手HP半分のとき威力約49():
    """ハードプレス: 相手のHPが半分のとき威力が約49になる。
    カビゴン max_hp=235, hp=117 → floor(100 * 117 / 235) = 49。
    """
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["ハードプレス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 49


def test_ハードプレス_相手HP満タンのとき威力100():
    """ハードプレス: 相手のHPが満タンのとき威力100。
    floor(100 * max_hp / max_hp) = 100。
    """
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["ハードプレス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp  # 満タン
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


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


def test_ばくおんぱ_みがわりを貫通して本体にダメージを与える():
    """ばくおんぱ: soundラベルを持つため、みがわり状態の相手の本体にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ばくおんぱ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    # みがわりにHPを設定（貫通しなければこのHPが削られる）
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    # 音技はみがわりを無視して本体にダメージを与えるため、本体HPが減る
    assert defender.hp < hp_before
    # みがわりのHPは変化しない
    assert defender.volatiles["みがわり"].hp == 999


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
    assert attacker.rank["def"] == 1


def test_バレットパンチ_相手にダメージを与える():
    """バレットパンチ: 優先度+1の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["バレットパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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


def test_パワフルエッジ_きれあじで威力1_5倍():
    """パワフルエッジ: slashフラグを持つため、きれあじ特性のポケモンが使用すると威力が1.5倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きれあじ", move_names=["パワフルエッジ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_パワフルエッジ_まもる中の相手にダメージが入る():
    """パワフルエッジ: unprotectableフラグを持つため、まもる状態の相手にもダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワフルエッジ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_パワフルエッジ_まもる状態が解除されない():
    """パワフルエッジ: まもる状態を無視してダメージを与えるが、まもる揮発状態は解除しない。

    フェイントはまもる揮発状態を解除するが、パワフルエッジは解除しない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワフルエッジ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("まもる")


def test_パワーウィップ_相手にダメージを与える():
    """パワーウィップ: 追加効果なしの物理くさ技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["パワーウィップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ひけん・ちえなみ_まきびし3層のとき設置されず攻撃は成功する():
    """ひけん・ちえなみ: まきびしが3層でも攻撃は成功し、設置数は増えない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ひけん・ちえなみ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        side1={"まきびし": 3},
    )
    defender = battle.actives[1]
    side = battle.get_side(defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 攻撃は成功してダメージを与える
    assert defender.hp < hp_before
    # まきびしは3層のまま
    assert side.fields["まきびし"].count == 3


def test_ひけん・ちえなみ_命中後まきびしが1層設置される():
    """ひけん・ちえなみ: 命中すると相手陣営にまきびしが1層設置される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ひけん・ちえなみ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)
    assert side.fields["まきびし"].is_active
    assert side.fields["まきびし"].count == 1


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


def test_ひゃっきやこう_状態異常のとき威力2倍():
    """ひゃっきやこう: 相手が状態異常のとき威力が2倍になる。
    ゴースト技はノーマルに無効のため、エスパータイプのフーディンを使用する。
    """
    battle_normal = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ひゃっきやこう"])],
        team1=[Pokemon("フーディン")],
        accuracy=100,
    )
    battle_ailment = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ひゃっきやこう"])],
        team1=[Pokemon("フーディン")],
        accuracy=100,
    )
    battle_ailment.ailment_manager.apply(battle_ailment.actives[1], "まひ")
    t.run_move(battle_normal, 0)
    t.run_move(battle_ailment, 0)
    assert battle_normal.damage_calculator.power_modifier == 4096
    assert battle_ailment.damage_calculator.power_modifier == 8192


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


def test_ヒートスタンプ_体重比2以上3未満のとき威力60():
    """ヒートスタンプ: 自分/相手の体重比が2以上3未満のとき威力60。
    バクフーン(79.5kg) vs マリルリ(28.5kg) → 比率2.79 → 威力60。
    """
    battle = t.start_battle(
        team0=[Pokemon("バクフーン", move_names=["ヒートスタンプ"])],
        team1=[Pokemon("マリルリ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 60


def test_ヒートスタンプ_体重比2未満のとき威力40():
    """ヒートスタンプ: 自分/相手の体重比が2未満のとき威力40。
    ヤドン(36kg) vs マリルリ(28.5kg) → 比率1.26 → 威力40。
    """
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["ヒートスタンプ"])],
        team1=[Pokemon("マリルリ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_ヒートスタンプ_体重比3以上4未満のとき威力80():
    """ヒートスタンプ: 自分/相手の体重比が3以上4未満のとき威力80。
    ゴリランダー(90kg) vs マリルリ(28.5kg) → 比率3.16 → 威力80。
    """
    battle = t.start_battle(
        team0=[Pokemon("ゴリランダー", move_names=["ヒートスタンプ"])],
        team1=[Pokemon("マリルリ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_ヒートスタンプ_体重比4以上5未満のとき威力100():
    """ヒートスタンプ: 自分/相手の体重比が4以上5未満のとき威力100。
    ゴリランダー(90kg) vs コダック(19.6kg) → 比率4.59 → 威力100。
    """
    battle = t.start_battle(
        team0=[Pokemon("ゴリランダー", move_names=["ヒートスタンプ"])],
        team1=[Pokemon("コダック")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_ヒートスタンプ_体重比5以上のとき威力120():
    """ヒートスタンプ: 自分/相手の体重比が5以上のとき威力120。
    カビゴン(460kg) vs ピカチュウ(6kg) → 比率76.7 → 威力120。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ヒートスタンプ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 120


def test_ヒートスタンプ_相手がちいさくなる中は体重比計算をスキップ():
    """ヒートスタンプ: 相手がちいさくなる状態のとき体重比計算をスキップする。
    ちいさくなる中は minimize ラベルの共通処理（威力2倍）のみが適用される。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ヒートスタンプ"])],
        team1=[Pokemon("マリルリ")],
        accuracy=100,
        volatile1={"ちいさくなる": 1},
    )
    t.run_move(battle, 0)
    # ちいさくなる中は元の power=1 に minimize 補正(2倍)が適用されて 2 になる
    assert battle.damage_calculator.final_power == 2


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
    move_data = MOVES["ビックリヘッド"]
    assert "contact" in move_data.flags


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


def test_ふいうち_後攻時に相手が行動済みで失敗():
    """ふいうち: 相手がすでに行動済み（後攻）の場合は失敗する。

    ゲンガー（素早さ130）がでんこうせっか（優先度+1）を使い、
    ピカチュウ（素早さ110）がふいうち（優先度+1）を使う場合、
    同優先度でゲンガーが先行するため、ゲンガー行動後にふいうちを使うと失敗する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふいうち"])],
        team1=[Pokemon("ゲンガー", move_names=["でんこうせっか"])],
        accuracy=100,
    )
    defender_hp_before = battle.actives[1].hp
    battle.step()
    # ふいうちが失敗するためゲンガーにダメージはない
    assert battle.actives[1].hp == defender_hp_before


def test_ふいうち_相手がねむり状態で攻撃技選択時に成功():
    """ふいうち: 相手がねむり状態でも攻撃技を選択していれば成功する。

    ねむり状態では攻撃技が実行されない場合があるが、
    コマンドが残っていれば攻撃技選択と判定されふいうちは成功する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふいうち"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        ailment1=("ねむり", 3),
        accuracy=100,
    )
    defender_hp_before = battle.actives[1].hp
    battle.step()
    assert battle.actives[1].hp < defender_hp_before


def test_ふいうち_相手が変化技選択時に失敗():
    """ふいうち: 相手が変化技を選択したターンは失敗してダメージを与えない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふいうち"])],
        team1=[Pokemon("カビゴン", move_names=["なきごえ"])],
        accuracy=100,
    )
    defender_hp_before = battle.actives[1].hp
    battle.step()
    assert battle.actives[1].hp == defender_hp_before


def test_ふいうち_相手が攻撃技選択時に成功():
    """ふいうち: 相手が攻撃技を選択したターンはダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふいうち"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender_hp_before = battle.actives[1].hp
    battle.step()
    assert battle.actives[1].hp < defender_hp_before


def test_フェイタルクロー_乱数によりどくが付与される():
    """フェイタルクロー: 乱数r < 1/3のとき(r=0.1)どくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["フェイタルクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.fix_random(battle, 0.1)  # 0.1 < 1/3 → どく
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_フェイタルクロー_乱数によりねむりが付与される():
    """フェイタルクロー: 乱数2/3 <= r < 1.0のとき(r=0.7)ねむりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["フェイタルクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.fix_random(battle, 0.7)  # 2/3 <= 0.7 < 1.0 → ねむり
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "ねむり"


def test_フェイタルクロー_乱数によりまひが付与される():
    """フェイタルクロー: 乱数1/3 <= r < 2/3のとき(r=0.45)まひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["フェイタルクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.fix_random(battle, 0.45)  # 1/3 <= 0.45 < 2/3 → まひ
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_フェイタルクロー_状態異常が発動する():
    """フェイタルクロー: 50%でどく/まひ/ねむりのいずれかを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["フェイタルクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name in ("どく", "まひ", "ねむり")


def test_フェイタルクロー_発動しない場合は状態異常なし():
    """フェイタルクロー: secondary_chanceが0のとき状態異常を付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["フェイタルクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_フェイント_ニードルガード状態を解除して攻撃する():
    """フェイント: ニードルガード状態の相手のニードルガード揮発状態を解除し、ダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェイント"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"ニードルガード": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert not defender.has_volatile("ニードルガード")
    assert defender.hp < hp_before


def test_フェイント_まもる状態がない場合は通常攻撃する():
    """フェイント: まもる状態がない相手には通常通りダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェイント"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_フェイント_まもる状態を解除して攻撃する():
    """フェイント: まもる状態の相手のまもる揮発状態を解除し、ダメージを与える。

    フェイントは優先度+2でunprotectable属性を持つため、
    まもる状態中の相手に命中し、まもる揮発状態を解除する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェイント"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert not defender.has_volatile("まもる")
    assert defender.hp < hp_before


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


def test_ふぶき_ゆき中は必中になる():
    """ふぶき: ゆき天候中は命中率70でも通常なら外れる乱数で命中する。

    ふぶきの命中率は70。random.random()=0.85 のとき 100*0.85=85>70 で本来は外れるが、
    ゆき中はON_MODIFY_ACCURACYでNoneが返り必中になるため、命中してHPが減る。
    """
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["ふぶき"])],
        team1=[Pokemon("カビゴン")],
        weather=("ゆき", 5),
    )
    # random.random()=0.85 は命中率70未満ではない（85>70）ので通常は外れる
    battle.random.random = lambda: 0.85
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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


def test_フライングプレス_いわタイプにかくとう2倍ひこう0倍5で等倍():
    """フライングプレス: いわタイプはかくとう2倍×ひこう0.5倍で等倍（1.0倍）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["フライングプレス"])],
        team1=[Pokemon("イワーク")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 4096


def test_フライングプレス_ゴーストタイプに無効():
    """フライングプレス: ゴーストタイプはかくとうが無効のため技が無効化される。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["フライングプレス"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    mon1 = battle.actives[1]
    hp_before = mon1.hp
    t.run_move(battle, 0)
    assert mon1.hp == hp_before


def test_フライングプレス_ノーマルタイプにかくとう2倍のみ適用():
    """フライングプレス: ノーマルタイプに対してかくとう2倍×ひこう等倍=2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["フライングプレス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 8192


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


def test_フリーズドライ_みずタイプに効果抜群():
    """フリーズドライ: みずタイプに対して効果抜群（2倍）になる。
    通常こおり技はみずに0.5倍だが、フリーズドライは2倍になる。
    """
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["フリーズドライ"])],
        team1=[Pokemon("カメックス")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 8192


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
    assert attacker.rank["spa"] == 1


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


def test_ふんか_HP半分のとき威力が低下する():
    """ふんか: 使用者のHPが半分のとき威力が満タン時より低下する。"""
    battle = t.start_battle(
        team0=[Pokemon("グラードン", move_names=["ふんか"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power < 150
    assert battle.damage_calculator.final_power >= 1


def test_ふんか_HP満タンのとき威力150():
    """ふんか: 使用者のHPが満タンのとき威力150（modifier=4096）。"""
    battle = t.start_battle(
        team0=[Pokemon("グラードン", move_names=["ふんか"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp  # 満タン
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 150


def test_ぶきみなじゅもん_相手が技未使用ならPP変化なし():
    """ぶきみなじゅもん: 相手の executed_move が None の場合はPPを変化させない。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ぶきみなじゅもん"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    pp_before = move.pp
    # カビゴンはまだ技を使っていない（executed_move=None）
    t.run_move(battle, 0)
    assert move.pp == pp_before


def test_ぶきみなじゅもん_相手の直前技PPが3減る():
    """ぶきみなじゅもん: 相手が前のターンに使った技のPPが3減る。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ぶきみなじゅもん"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    # カビゴンに技を使わせて executed_move を設定する
    t.run_move(battle, 1)
    pp_after_use = move.pp
    # ぶきみなじゅもんを使う
    t.run_move(battle, 0)
    assert move.pp == pp_after_use - 3


def test_ぶちかまし_防御と特防が各1段階低下する():
    """ぶちかまし: 命中時に使用者のBとDが各1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ぶちかまし"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["def"] == -1
    assert attacker.rank["spd"] == -1


def test_ブラストバーン_命中後にリチャージ状態が付与される():
    """ブラストバーン: 命中後に使用者にリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ブラストバーン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")


def test_ブラストバーン_次ターン行動不能になる():
    """ブラストバーン: 次のターンはリチャージ状態により行動不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ブラストバーン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.step()
    assert attacker.has_volatile("リチャージ")
    defender_hp_after_t1 = defender.hp
    battle.step()
    assert not attacker.has_volatile("リチャージ")
    assert defender.hp == defender_hp_after_t1


def test_ブラッドムーン_2ターン後は再び選択可能():
    """ブラッドムーン: 使用から2ターン後は揮発状態が解除されてブラッドムーンを再び選択できる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ブラッドムーン", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    # ブラッドムーン使用
    t.run_move(battle, 0)
    # ターン終了（count: 2→1）
    t.end_turn(battle)
    assert attacker.has_volatile("ブラッドムーン")
    # もう1ターン終了（count: 1→0 → 揮発解除）
    t.end_turn(battle)
    assert not attacker.has_volatile("ブラッドムーン")
    # ブラッドムーンが再び選択可能
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "ブラッドムーン" in move_names


def test_ブラッドムーン_デカハンマー使用後もブラッドムーンは選択可能():
    """ブラッドムーン: デカハンマーの揮発状態とは独立しており、デカハンマー使用後でもブラッドムーンは選択できる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["デカハンマー", "ブラッドムーン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    # デカハンマー使用
    t.run_move(battle, 0)
    assert attacker.has_volatile("デカハンマー")
    # ターン終了（count: 2→1）
    t.end_turn(battle)
    # ブラッドムーンは選択可能
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "ブラッドムーン" in move_names
    assert "デカハンマー" not in move_names


def test_ブラッドムーン_まもるで防がれた場合も次のターンは選択不可():
    """ブラッドムーン: まもるで防がれてもPP消費済みなので次のターンは選択不可。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ブラッドムーン", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手にまもるを付与した状態でブラッドムーンを使用（防がれる）
    battle.volatile_manager.apply(defender, "まもる", count=1)
    t.run_move(battle, 0)
    # まもるで防がれてもブラッドムーン揮発が付与される
    assert attacker.has_volatile("ブラッドムーン")
    # ターン終了（count: 2→1）
    t.end_turn(battle)
    # 次ターンの選択肢にブラッドムーンが含まれない
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "ブラッドムーン" not in move_names


def test_ブラッドムーン_使用後は次のターンに選択不可():
    """ブラッドムーン: 使用したターンの次のターン、コマンド選択肢にブラッドムーンが現れない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ブラッドムーン", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    attacker = battle.actives[0]
    # ブラッドムーン使用 → 揮発状態が付与される
    t.run_move(battle, 0)
    assert attacker.has_volatile("ブラッドムーン")
    # ターン終了（count: 2→1）
    t.end_turn(battle)
    assert attacker.has_volatile("ブラッドムーン")
    # 次ターンのコマンドにブラッドムーンが含まれない
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    move_names = [attacker.moves[cmd.index].name for cmd in commands if cmd.is_type("move")]
    assert "ブラッドムーン" not in move_names


def test_ブラッドムーン_通常使用でダメージを与える():
    """ブラッドムーン: 威力140の特殊ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ブラッドムーン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


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


def test_ぶんまわす_相手にダメージを与える():
    """ぶんまわす: 追加効果なしの物理あく技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ぶんまわす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_プリズムレーザー_命中後にリチャージ状態が付与される():
    """プリズムレーザー: 命中後に使用者にリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["プリズムレーザー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")


def test_プリズムレーザー_次ターン行動不能になる():
    """プリズムレーザー: 次のターンはリチャージ状態により行動不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["プリズムレーザー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.step()
    assert attacker.has_volatile("リチャージ")
    defender_hp_after_t1 = defender.hp
    battle.step()
    assert not attacker.has_volatile("リチャージ")
    assert defender.hp == defender_hp_after_t1


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


def test_ヘビーボンバー_体重比2未満のとき威力40():
    """ヘビーボンバー: 自分/相手の体重比が2未満のとき威力40。
    ヤドン(36kg) vs マリルリ(28.5kg) → 比率1.26 → 威力40。
    """
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["ヘビーボンバー"])],
        team1=[Pokemon("マリルリ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_ヘビーボンバー_体重比5以上のとき威力120():
    """ヘビーボンバー: 自分/相手の体重比が5以上のとき威力120。
    カビゴン(460kg) vs ピカチュウ(6kg) → 比率76.7 → 威力120。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ヘビーボンバー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 120


def test_ヘビーボンバー_相手がちいさくなる中は体重比計算をスキップ():
    """ヘビーボンバー: 相手がちいさくなる状態のとき体重比計算をスキップする。
    ちいさくなる中は minimize ラベルの共通処理（威力2倍）のみが適用される。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ヘビーボンバー"])],
        team1=[Pokemon("マリルリ")],
        accuracy=100,
        volatile1={"ちいさくなる": 1},
    )
    t.run_move(battle, 0)
    # ちいさくなる中は元の power=1 に minimize 補正(2倍)が適用されて 2 になる
    assert battle.damage_calculator.final_power == 2


def test_ベノムショック_どく状態のとき威力2倍():
    """ベノムショック: 対象がどく状態のとき威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ベノムショック"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("どく", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_ベノムショック_まひ状態でも威力補正なし():
    """ベノムショック: まひ状態（どく/もうどく以外）では威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ベノムショック"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ベノムショック_もうどく状態のとき威力2倍():
    """ベノムショック: 対象がもうどく状態のとき威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ベノムショック"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("もうどく", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_ベノムショック_状態異常なしのとき通常威力():
    """ベノムショック: 対象が状態異常でないとき威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ベノムショック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ホイールスピン_素早さ2段階低下が発動する():
    """ホイールスピン: 命中時に使用者のSが2段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ドータクン", move_names=["ホイールスピン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["spe"] == -2


def test_ほうでん_でんきタイプにはまひが付与されない():
    """ほうでん: でんきタイプの相手にはまひが付与されない（タイプ耐性）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ほうでん"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


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


def test_ほうふく_ダメージを受けていないとき失敗する():
    """ほうふく: そのターンダメージを受けていない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ほうふく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_ほうふく_物理ダメージを受けた後に1_5倍を返す():
    """ほうふく: 受けた物理ダメージの1.5倍（切り捨て）を相手に与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ほうふく"])],
        team1=[Pokemon("カビゴン", move_names=["ひっかく"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手の物理技を受ける
    t.run_move(battle, 1)
    last_dmg = attacker.last_damage_received
    assert last_dmg > 0
    hp_before = defender.hp
    # ほうふくで1.5倍返し
    t.run_move(battle, 0)
    assert defender.hp == hp_before - int(last_dmg * 1.5)


def test_ほうふく_特殊ダメージを受けた後も発動する():
    """ほうふく: 特殊ダメージを受けた場合でも発動する（物理・特殊問わず）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ほうふく"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手の特殊技を受ける
    t.run_move(battle, 1)
    last_dmg = attacker.last_damage_received
    assert last_dmg > 0
    hp_before = defender.hp
    # ほうふくで1.5倍返し
    t.run_move(battle, 0)
    assert defender.hp == hp_before - int(last_dmg * 1.5)


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


def test_ほのおのキバ_ひるみが選択される():
    """ほのおのキバ: 単一乱数で 0.5<=r<1.0 の場合はひるみを付与する（やけどとの排他制御）。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ほのおのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    # r=0.7 のとき base*0.5=0.5 を超えるのでやけどには進まず、r<base=1.0 でひるみを選択
    battle.random.random = lambda: 0.7
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")
    assert not battle.actives[1].ailment.is_active


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


def test_ほのおのキバ_やけどが選択される():
    """ほのおのキバ: 単一乱数で r<0.5 の場合はやけどを付与する（ひるみとの排他制御）。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ほのおのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    # r=0.0 のとき r < base*0.5=0.5 でやけどを選択
    battle.random.random = lambda: 0.0
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"
    assert not battle.actives[1].has_volatile("ひるみ")


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
    assert attacker.rank["spa"] == 1


def test_ほのおのムチ_ぼうぎょ1段階低下が発動する():
    """ほのおのムチ: 100%の確率で相手のぼうぎょを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["ほのおのムチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["def"] == -1


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


def test_ボディプレス_防御ランク上昇でダメージ増加する():
    """ボディプレス: ぼうぎょランクが上昇するとダメージが増加する。"""
    battle1 = t.start_battle(
        team0=[Pokemon("ナットレイ", move_names=["ボディプレス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle1.random.random = lambda: 0.9
    attacker1 = battle1.actives[0]
    battle1.modify_stats(attacker1, {"def": 2}, source=attacker1)
    mon1 = battle1.actives[1]
    hp_before = mon1.hp
    t.run_move(battle1, 0)
    damage_b_plus2 = hp_before - mon1.hp

    battle2 = t.start_battle(
        team0=[Pokemon("ナットレイ", move_names=["ボディプレス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle2.random.random = lambda: 0.9
    mon2 = battle2.actives[1]
    hp_before2 = mon2.hp
    t.run_move(battle2, 0)
    damage_no_rank = hp_before2 - mon2.hp

    assert damage_b_plus2 > damage_no_rank


def test_ボディプレス_防御実数値を攻撃として計算する():
    """ボディプレス: 使用者の防御実数値を攻撃値として計算する。"""
    battle = t.start_battle(
        team0=[Pokemon("ナットレイ", move_names=["ボディプレス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_attack == attacker.stats["def"]


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
    """ボルテッカー: 与えたダメージの1/3を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ボルテッカー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_ボルテッカー_反動ダメージが与ダメの3分の1になる():
    """ボルテッカー: 反動量は max(1, int(与ダメ * 1/3)) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ボルテッカー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/3)) = 33
    assert attacker.hp == hp_before - 33


def test_ボーンラッシュ_複数ヒットする():
    """ボーンラッシュ: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("カラカラ", move_names=["ボーンラッシュ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


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


def test_ポルターガイスト_アイテムあり_ダメージを与える():
    """ポルターガイスト: 相手がアイテムを持っているとき通常通りダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ポルターガイスト"])],
        team1=[Pokemon("ピカチュウ", item_name="たべのこし")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ポルターガイスト_アイテムなし_失敗しダメージなし():
    """ポルターガイスト: 相手がアイテムを持っていないとき技が失敗してダメージを与えない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ポルターガイスト"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert battle.move_executor.move_applied is False


def test_ミサイルばり_複数ヒットする():
    """ミサイルばり: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("ビードル", move_names=["ミサイルばり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_ミラーコート_物理ダメージのみ受けたとき失敗する():
    """ミラーコート: そのターン物理ダメージのみ受けた場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        team1=[Pokemon("カビゴン", move_names=["ひっかく"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    # 相手の物理技を受ける
    t.run_move(battle, 1)
    hp_before = defender.hp
    # ミラーコートは失敗するはず
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_ミラーコート_特殊ダメージを2倍返しする():
    """ミラーコート: 受けた特殊ダメージの2倍を相手に与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手の特殊技を受ける
    t.run_move(battle, 1)
    special_dmg = attacker.last_special_damage_received
    assert special_dmg > 0
    hp_before = defender.hp
    # ミラーコートで2倍返し
    t.run_move(battle, 0)
    assert defender.hp == hp_before - special_dmg * 2


def test_ミラーコート_特殊ダメージを受けていないとき失敗する():
    """ミラーコート: そのターン特殊ダメージを受けていない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_メタルバースト_ダメージを受けていないとき失敗する():
    """メタルバースト: そのターンダメージを受けていない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["メタルバースト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_メタルバースト_受けたダメージの1_5倍を返す():
    """メタルバースト: 受けたダメージの1.5倍（切り捨て）を相手に与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["メタルバースト"])],
        team1=[Pokemon("カビゴン", move_names=["ひっかく"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手の物理技を受ける
    t.run_move(battle, 1)
    last_dmg = attacker.last_damage_received
    assert last_dmg > 0
    hp_before = defender.hp
    # メタルバーストで1.5倍返し
    t.run_move(battle, 0)
    assert defender.hp == hp_before - int(last_dmg * 1.5)


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


def test_もろはのずつき_反動ダメージが与ダメの2分の1になる():
    """もろはのずつき: 反動量は max(1, int(与ダメ * 1/2)) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["もろはのずつき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/2)) = 50
    assert attacker.hp == hp_before - 50
