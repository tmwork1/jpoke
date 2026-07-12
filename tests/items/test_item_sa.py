"""アイテムハンドラの単体テスト"""
import pytest
from jpoke import Pokemon
from jpoke.enums import Interrupt
from .. import test_utils as t


def test_サイコシード_展開済みサイコフィールドに登場して発動():
    """サイコシード: すでにサイコフィールドが展開されている場に登場（交代）してもとくぼう+1して消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", item_name="サイコシード")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", 5),
    )
    raichu = battle._player_states[0].team[1]
    t.run_switch(battle, 0, 1)
    assert raichu.boosts["spd"] == 1
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


def test_サンのみ_瀕死になったときは発動しない():
    """サンのみ: ダメージでHPが0(ひんし)になったときはきゅうしょアップ状態にならず、
    アイテムも消費されない
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="サンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == 0
    assert mon.fainted
    assert not mon.has_volatile("きゅうしょアップ")
    assert mon.has_item()


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
    assert mon.boosts["spa"] == -2


def test_しろいハーブ_すでに能力が下がっている状態でアイテムを入手すると即座にリセットする():
    """しろいハーブ: 既に能力が下がっている状態でアイテムを入手すると即座に発動する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.boosts["atk"] = -2
    t.change_item(battle, mon, "しろいハーブ")
    assert mon.boosts["atk"] == 0
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
    foe.boosts["atk"] = -2
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 0
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
    attacker.boosts["atk"] = -2

    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.boosts["atk"] == 0
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
    assert mon.boosts["spa"] == 0
    assert not mon.has_item()


def test_しんかのきせき_ボディプレスでは攻撃側の防御を1_5倍扱いしない():
    """しんかのきせき: 所有者がボディプレスを使用しても、攻撃側の防御を1.5倍扱いすることはない"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", item_name="しんかのきせき", move_names=["ボディプレス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_しんかのきせき_メルタンに持たせても効果が無い():
    """しんかのきせき: メルタンは進化先（メルメタル）を持つが例外的に効果が無い"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("メルタン", item_name="しんかのきせき")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 4096


def test_しんかのきせき_最終進化ポケモンには効果が無い():
    """しんかのきせき: 進化の余地が無い（最終進化の）ポケモンには効果が無い"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カメックス", item_name="しんかのきせき")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 4096


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
    foe.boosts["atk"] = 6
    foe.boosts["spa"] = 6
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 6
    assert foe.boosts["spa"] == 6
    assert foe.has_item()


def test_じゃくてんほけん_いのちがけでは発動しない():
    """じゃくてんほけん: いのちがけ（ダメージ固定技）はタイプ相性上弱点でも発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["いのちがけ"])],
        team1=[Pokemon("カビゴン", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 0
    assert foe.boosts["spa"] == 0
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
    assert foe.boosts["atk"] == 0
    assert foe.boosts["spa"] == 0
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
    assert foe.boosts["atk"] == 0
    assert foe.boosts["spa"] == 0
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
    assert foe.boosts["atk"] == 0
    assert foe.boosts["spa"] == 0
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
    assert foe.boosts["atk"] == 2
    assert foe.boosts["spa"] == 2
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
    assert foe.boosts["atk"] == 2
    assert foe.boosts["spa"] == 2
    assert not foe.has_item()


def test_じゃくてんほけん_片方のランクのみ最大のときもう片方が上昇する():
    """じゃくてんほけん: 片方のランクのみ最大の場合はもう片方だけ上昇し、アイテムは消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.boosts["atk"] = 6
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 6
    assert foe.boosts["spa"] == 2
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
    assert foe.boosts["atk"] == 0
    assert foe.has_item()


def test_じゃくてんほけん_マジシャンより先に発動して奪われない():
    """じゃくてんほけん: 特性マジシャンの効果抜群の技を受けても、じゃくてんほけんが先に発動して
    消費されるため奪われない（攻撃側の素早さが防御側より高い場合でも、素早さに依存せず先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", ability_name="マジシャン", move_names=["かえんほうしゃ"])],
        team1=[Pokemon("フシギダネ", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 2
    assert foe.boosts["spa"] == 2
    assert not foe.has_item()
    assert not attacker.has_item()


def test_ジャポのみ_きんちょうかんの相手がいると発動しない():
    """ジャポのみ: 相手が特性きんちょうかんを持つときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="きんちょうかん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="ジャポのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp
    assert battle.actives[1].has_item()


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
    foe.boosts["atk"] = -6
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == -6
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
    assert foe.boosts["atk"] == -1
    assert not foe.has_item()


def test_じゅうでんち_かたやぶりの電気技はたんじゅんあまのじゃくでもA上昇():
    """じゅうでんち: かたやぶりの効果があるでんき技に対してはたんじゅん・あまのじゃくは発動せず通常通り+1される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 1
    assert not foe.has_item()


def test_じゅうでんち_こうげきランクが最大のとき発動しない():
    """じゅうでんち: すでにこうげきランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.boosts["atk"] = 6
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 6
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
    assert foe.boosts["atk"] == 2
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
    assert foe.boosts["atk"] == 0
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
    assert foe.boosts["atk"] == 1
    assert not foe.has_item()


def test_じゅうでんち_マジシャンより先に発動して奪われない():
    """じゅうでんち: 特性マジシャンのでんき技を受けても、じゅうでんちが先に発動して消費されるため奪われない
    （攻撃側の素早さが防御側より高い場合でも、素早さに依存せずじゅうでんちが先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="じゅうでんち")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["atk"] == 1
    assert not foe.has_item()
    assert not attacker.has_item()


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
    assert mon.boosts["atk"] == 2
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
    assert mon.boosts["atk"] == 2
    assert not mon.has_item()


def test_スターのみ_すでに最大のランクは選ばれない():
    """スターのみ: ランクが最大(+6)の能力は選択候補から除外される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="スターのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd"):
        mon.boosts[stat] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.random.choice = lambda seq: seq[0]  # 候補が1つ（すばやさ）のみになる
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["spe"] == 2
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
    assert mon.boosts["atk"] == 2
    assert not mon.has_item()


def test_スターのみ_全ての能力が最大なら発動しない():
    """スターのみ: 5箇所の能力全てがすでに最大になっているときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="スターのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd", "spe"):
        mon.boosts[stat] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert all(mon.boosts[stat] == 6 for stat in ("atk", "def", "spa", "spd", "spe"))
    assert mon.has_item()


def test_スターのみ_瀕死になったときは発動しない():
    """スターのみ: ダメージでHPが0(ひんし)になったときは能力上昇せず、アイテムも消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="スターのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.random.choice = lambda seq: seq[0]  # A が選ばれる（発動すれば検知できる）
    battle.modify_hp(mon, v=-1)
    assert mon.hp == 0
    assert mon.fainted
    assert all(mon.boosts[stat] == 0 for stat in ("atk", "def", "spa", "spd", "spe"))
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
    mon.boosts["spd"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.boosts["spd"] == 6
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
