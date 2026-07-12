"""アイテムハンドラの単体テスト"""
import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_ヤタピのみ_とくこうランクが最大のとき発動しない():
    """ヤタピのみ: すでにとくこうランクが最大まで上がっているときはHP1/4以下でも発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ヤタピのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.boosts["spa"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["spa"] == 6
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
    foe.boosts["atk"] = -6
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == -6
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
    assert foe.boosts["atk"] == -1
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
    assert foe.boosts["atk"] == 1
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
    assert foe.boosts["atk"] == 0
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
    assert foe.boosts["atk"] == 1
    assert not foe.has_item()


def test_ゆきだま_マジシャンより先に発動して奪われない():
    """ゆきだま: 特性マジシャンのこおり技を受けても、ゆきだまが先に発動して消費されるため奪われない
    （攻撃側の素早さが防御側より高い場合でも、素早さに依存せずゆきだまが先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 1
    assert not foe.has_item()
    assert not attacker.has_item()


def test_ゆきだま_たんじゅんで2段階上昇():
    """ゆきだま: たんじゅん所持者はこうげきランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま", ability_name="たんじゅん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 2
    assert not foe.has_item()


def test_ゆきだま_ランク上限で発動しない():
    """ゆきだま: こうげきランクが最大のとき発動しない（アイテムも消費されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.boosts["atk"] = 6
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 6
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
    mon.boosts["def"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["def"] == 6
    assert mon.has_item()


def test_ルームサービス_すばやさが下限のときは発動しない():
    """ルームサービス: すでにすばやさランクが下限のときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ルームサービス")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックルーム"])],
    )
    mon = battle.actives[0]
    mon.boosts["spe"] = -6
    t.run_move(battle, 1)
    assert mon.boosts["spe"] == -6
    assert mon.has_item()


def test_ルームサービス_トリックルームでS低下():
    """ルームサービス: トリックルーム発動時にすばやさ-1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ルームサービス")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックルーム"])],
    )
    t.run_move(battle, 1)
    mon = battle.actives[0]
    assert mon.boosts["spe"] == -1
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
    assert mon.boosts["spe"] == -1
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
    assert mon.boosts["spe"] == -1
    assert mon.boosts["atk"] == 0
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
