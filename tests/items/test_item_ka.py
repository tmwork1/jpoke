"""アイテムハンドラの単体テスト"""
import pytest
from jpoke import Pokemon
from .. import test_utils as t


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


def test_かいがらのすず_命中後に自分のランクを下げる技でも回復する():
    """かいがらのすず: アーマーキャノンのように命中後に自分のランクを下げるON_HITハンドラを
    持つ技でも、ランク変化ハンドラの戻り値（dict）に汚染されずダメージ量から正しく回復する
    （fuzzで発見されたTypeErrorの回帰テスト）"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ", item_name="かいがらのすず", move_names=["アーマーキャノン"],
        )],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.fix_damage(battle, 80)
    t.run_move(battle, 0)
    assert attacker.hp == 1 + 80 // 8
    assert attacker.boosts["def"] == -1
    assert attacker.boosts["spd"] == -1


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


def test_カムラのみ_きんちょうかんの相手がいると発動しない():
    """カムラのみ: 相手が特性きんちょうかんを持つときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="カムラのみ")],
        team1=[Pokemon("ピカチュウ", ability_name="きんちょうかん")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["spe"] == 0
    assert mon.has_item()


def test_カムラのみ_すばやさランクが最大のとき発動しない():
    """カムラのみ: すでにすばやさランクが最大まで上がっているときはHP1/4以下でも発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="カムラのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.boosts["spe"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["spe"] == 6
    assert mon.has_item()


def test_からぶりほけん_すばやさランクが最大のときは発動しない():
    """からぶりほけん: すでにすばやさランクが最大(+6)のときは発動しない（アイテムも消費されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="からぶりほけん", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    mon = battle.actives[0]
    mon.boosts["spe"] = 6
    t.run_move(battle, 0)
    assert mon.boosts["spe"] == 6
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
    assert mon.boosts["spe"] == 0
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
    assert mon.boosts["spe"] == 0
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
    assert mon.boosts["spe"] == 2
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
    assert mon.boosts["spe"] == 2
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
    assert mon.boosts["spe"] == 0
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


def test_きゅうこん_あまのじゃくでCランクが最小のとき発動しない():
    """きゅうこん: あまのじゃく所持者はとくこうランクがすでに最小のとき発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="きゅうこん", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.boosts["spa"] = -6
    t.run_move(battle, 0)
    assert foe.boosts["spa"] == -6
    assert foe.has_item()


def test_きゅうこん_あまのじゃくでC下降():
    """きゅうこん: あまのじゃく所持者はとくこうが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="きゅうこん", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spa"] == -1
    assert not foe.has_item()


def test_きゅうこん_かたやぶりのみず技はたんじゅんあまのじゃくでもC上昇():
    """きゅうこん: かたやぶりの効果があるみず技に対してはたんじゅん・あまのじゃくは発動せず通常通り+1される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="きゅうこん", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spa"] == 1
    assert not foe.has_item()


def test_きゅうこん_たんじゅんでC2段階上昇():
    """きゅうこん: たんじゅん所持者はとくこうが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="きゅうこん", ability_name="たんじゅん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spa"] == 2
    assert not foe.has_item()


def test_きゅうこん_とくこうランクが最大のとき発動しない():
    """きゅうこん: すでにとくこうランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="きゅうこん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.boosts["spa"] = 6
    t.run_move(battle, 0)
    assert foe.boosts["spa"] == 6
    assert foe.has_item()


def test_きゅうこん_マジシャンより先に発動して奪われない():
    """きゅうこん: 特性マジシャンのみず技を受けても、きゅうこんが先に発動して消費されるため奪われない
    （攻撃側の素早さが防御側より高い場合でも、素早さに依存せずきゅうこんが先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="きゅうこん")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spa"] == 1
    assert not foe.has_item()
    assert not attacker.has_item()


def test_きゅうこん_みず以外では発動しない():
    """きゅうこん: みず以外の技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="きゅうこん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spa"] == 0
    assert foe.has_item()


def test_きゅうこん_みず被弾でC上昇():
    """きゅうこん: みず技でダメージを受けたときとくこう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみのり"])],
        team1=[Pokemon("カビゴン", item_name="きゅうこん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spa"] == 1
    assert not foe.has_item()


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


def test_くっつきバリ_どろぼうで攻撃者がアイテム持ちのとき転送も奪取もしない():
    """くっつきバリ: 攻撃者がすでにアイテムを持っている場合は転送されず、
    どろぼうの効果も発動しない（攻撃者がアイテムを持っているため奪取自体が失敗する）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのタスキ", move_names=["どろぼう"])],
        team1=[Pokemon("カビゴン", item_name="くっつきバリ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "きあいのタスキ"
    assert defender.item.name == "くっつきバリ"


def test_くっつきバリ_はたきおとすで攻撃者がアイテム持ちのとき通常通りはたき落とされる():
    """くっつきバリ: 攻撃者がすでにアイテムを持っている場合は転送されず、
    はたきおとすの効果が通常通り発動して落とされる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのタスキ", move_names=["はたきおとす"])],
        team1=[Pokemon("カビゴン", item_name="くっつきバリ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "きあいのタスキ"
    assert not defender.has_item()


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_くっつきバリ_はたきおとす等でアイテムなしの攻撃者に転送される(move_name):
    """くっつきバリ: はたきおとす・どろぼうの判定より先に転送が行われ、
    アイテムなしの攻撃者に渡ったあとは技の効果自体が発動しない（何も落とされない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("カビゴン", item_name="くっつきバリ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "くっつきバリ"
    assert not defender.has_item()


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


def test_くっつきバリ_ねんちゃく持ちでも接触技で転送される():
    """くっつきバリ: 保持者がねんちゃくを持っていても、発動条件を満たせば
    通常どおり攻撃側に転送される（ねんちゃくの仕様書に明記された例外）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="ねんちゃく", item_name="くっつきバリ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "くっつきバリ"
    assert not defender.has_item()


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
    assert mon.boosts["atk"] == 0


def test_クリアチャーム_ミラーアーマーとの併用では反射されない():
    """クリアチャーム: 特性ミラーアーマーを持っていても、クリアチャームの無効化が先に発動し反射できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー", item_name="クリアチャーム")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    assert mon.boosts["atk"] == 0
    assert foe.boosts["atk"] == 0


def test_クリアチャーム_自分の技の低下は防げない():
    """クリアチャーム: 自分の技によるランク低下（リーフストームのC-2）は防げない"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", item_name="クリアチャーム", move_names=["リーフストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.boosts["spa"] == -2


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
    assert raichu.boosts["def"] == 1
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


def test_ゴツゴツメット_マジシャンより先に発動してから奪われる():
    """ゴツゴツメット: 特性マジシャンの接触技を受けても、ゴツゴツメットが先に発動してから奪われる
    （攻撃側の素早さが防御側より高い場合でも、素早さに依存せずゴツゴツメットが先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    initial_hp = attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp < initial_hp
    assert attacker.item.name == "ゴツゴツメット"
    foe = battle.actives[1]
    assert not foe.has_item()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
