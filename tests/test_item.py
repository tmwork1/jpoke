"""アイテムハンドラの単体テスト"""
import math
from types import SimpleNamespace
from typing import cast
from jpoke import Pokemon
from jpoke.core import AttackContext, EventContext
from jpoke.enums import Event
from jpoke.data import ITEMS
from jpoke.model import Move
from . import test_utils as t

def _dummy_move(type_name: str) -> Move:
    return cast(Move, SimpleNamespace(type=type_name, name="ダミー"))


def test_あかいいと_アイテム消費されない():
    """あかいいと: 発動しても消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="メス")],
        team1=[Pokemon("カビゴン", gender="オス")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "メロメロ", source=foe)
    assert mon0.has_item()
    assert mon0.item.name == "あかいいと"


def test_あかいいと_どんかん持ちには付与されない():
    """あかいいと: 相手がどんかんならメロメロを付与しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="メス")],
        team1=[Pokemon("カビゴン", ability_name="どんかん", gender="オス")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "メロメロ", source=foe)
    assert mon0.has_volatile("メロメロ")
    assert not foe.has_volatile("メロメロ")


def test_あかいいと_メロメロ被弾で相手もメロメロ():
    """あかいいと: 持ち主がメロメロになったとき相手にもメロメロを付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="メス")],
        team1=[Pokemon("カビゴン", gender="オス")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "メロメロ", source=foe)
    assert mon0.has_volatile("メロメロ")
    assert foe.has_volatile("メロメロ")


def test_あかいいと_他の揮発状態では発動しない():
    """あかいいと: メロメロ以外の揮発状態では相手に付与しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="あかいいと", gender="メス")],
        team1=[Pokemon("カビゴン", gender="オス")],
    )
    mon0 = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon0, "こんらん", source=foe)
    assert mon0.has_volatile("こんらん")
    assert not foe.has_volatile("メロメロ")


def test_いしずえのめん_物理技強化():
    """いしずえのめん: 物理技の攻撃補正1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いしずえ)", item_name="いしずえのめん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4915


def test_いしずえのめん_特殊技は補正なし():
    """いしずえのめん: 特殊技には攻撃補正がない"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いしずえ)", item_name="いしずえのめん", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_いどのめん_物理技強化():
    """いどのめん: 物理技の攻撃補正1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いど)", item_name="いどのめん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4915


def test_いのちのたま():
    """いのちのたま: 攻撃技で反動ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="いのちのたま", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    attacker = battle.actives[0]
    assert attacker.hp == math.ceil(attacker.max_hp * 7/8)
    assert attacker.item.revealed


def test_いのちのたま_変化技では発動しない():
    """いのちのたま: 変化技では発動しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="いのちのたま", move_names=["はねる"])],
    )
    t.run_move(battle, 0)
    assert not battle.actives[0].item.revealed


def test_かまどのめん_物理技強化():
    """かまどのめん: 物理技の攻撃補正1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(かまど)", item_name="かまどのめん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4915


def test_きれいなぬけがら():
    """きれいなぬけがら: 交代防止無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きれいなぬけがら"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かげふみ")],
    )
    assert battle.can_switch(battle.players[0])


def test_くちたけん_フォルムチェンジ():
    """くちたけん: ザシアン(れきせん)がザシアン(けんのおう)にフォルムチェンジする"""
    battle = t.start_battle(
        team0=[Pokemon("ザシアン(れきせん)", item_name="くちたけん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ザシアン(けんのおう)"


def test_くちたけん_他ポケモンは変化しない():
    """くちたけん: ザシアン以外が持っても変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="くちたけん")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ピカチュウ"


def test_くちたたて_フォルムチェンジ():
    """くちたたて: ザマゼンタ(れきせん)がザマゼンタ(たてのおう)にフォルムチェンジする"""
    battle = t.start_battle(
        team0=[Pokemon("ザマゼンタ(れきせん)", item_name="くちたたて")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ザマゼンタ(たてのおう)"


def test_くちたたて_他ポケモンは変化しない():
    """くちたたて: ザマゼンタ以外が持っても変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="くちたたて")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ピカチュウ"


def test_クリアチャーム_いかくを防ぐ():
    """クリアチャーム: 相手のいかくによる能力ランク低下を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="クリアチャーム")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.rank["A"] == 0


def test_クリアチャーム_自分の技の低下は防げない():
    """クリアチャーム: 自分の技によるランク低下（リーフストームのC-2）は防げない"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", item_name="クリアチャーム", move_names=["リーフストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.rank["C"] == -2


def test_こころのしずく_エスパー技補正():
    """こころのしずく: ラティオスのエスパー技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ラティオス", item_name="こころのしずく", move_names=["サイコキネシス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_こころのしずく_ドラゴン技補正():
    """こころのしずく: ラティアスのドラゴン技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ラティアス", item_name="こころのしずく", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_こころのしずく_他タイプは補正なし():
    """こころのしずく: エスパー・ドラゴン以外のタイプは補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ラティオス", item_name="こころのしずく", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_こころのしずく_他種族は補正なし():
    """こころのしずく: ラティオス・ラティアス以外は補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こころのしずく", move_names=["サイコキネシス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_こだわりスカーフ_交代でロック解除():
    """こだわりスカーフ: 交代するとこだわりロックが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりスカーフ", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("こだわり")


def test_こだわりスカーフ_技ロック():
    """こだわりスカーフ: 技使用後にこだわりロック"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりスカーフ", move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    assert mon.volatiles["こだわり"].move_name == "たいあたり"


def test_こだわりスカーフ_素早さ強化():
    """こだわりスカーフ: 素早さ1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりスカーフ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    base_speed = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base_speed * 6144 // 4096


def test_こだわりハチマキ_技ロック():
    """こだわりハチマキ: 技使用後にこだわりロック"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ", move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    assert mon.volatiles["こだわり"].move_name == "たいあたり"


def test_こだわりハチマキ_物理技強化():
    """こだわりハチマキ: 物理技の攻撃補正1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_こだわりハチマキ_特殊技は補正なし():
    """こだわりハチマキ: 特殊技には攻撃補正がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_こだわりメガネ_技ロック():
    """こだわりメガネ: 技使用後にこだわりロック"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりメガネ", move_names=["でんきショック", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    assert mon.volatiles["こだわり"].move_name == "でんきショック"


def test_こだわりメガネ_物理技は補正なし():
    """こだわりメガネ: 物理技には攻撃補正がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりメガネ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_こだわりメガネ_特殊技強化():
    """こだわりメガネ: 特殊技の攻撃補正1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりメガネ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_こんごうだま_ドラゴン技補正():
    """こんごうだま: ディアルガのドラゴン技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", item_name="こんごうだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_こんごうだま_はがね技補正():
    """こんごうだま: ディアルガのはがね技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", item_name="こんごうだま", move_names=["アイアンヘッド"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_こんごうだま_他種族は補正なし():
    """こんごうだま: ディアルガ以外は補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こんごうだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_さらさらいわ():
    """さらさらいわ: 天候延長"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="さらさらいわ")],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.weather_manager.apply("すなあらし", 5, source=battle.actives[0])
    assert battle.raw_weather.count == 8


def test_しらたま_ドラゴン技補正():
    """しらたま: パルキアのドラゴン技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="しらたま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_しらたま_みず技補正():
    """しらたま: パルキアのみず技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="しらたま", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_タイプ半減実():
    """タイプ半減実: 対応タイプの被ダメージ補正"""
    base_value = 4096
    for item_name, data in ITEMS.items():
        if not data.damage_modifier_by_type:
            continue

        type_name, modifier = next(iter(data.damage_modifier_by_type.items()))
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", item_name=item_name)],
            team1=[Pokemon("ピカチュウ")],
        )
        battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
        t.run_move(battle, 0)
        assert battle.damage_calculator.damage_modifier == 2048 * modifier


def test_タイプ強化アイテム():
    """タイプ強化アイテム: 対応タイプ威力補正"""
    base_value = 4096
    for item_name, data in ITEMS.items():
        if not data.power_modifier_by_type:
            continue

        type_, modifier = next(iter(data.power_modifier_by_type.items()))
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", item_name=item_name)],
            team1=[Pokemon("ピカチュウ")],
        )
        battle.actives[0].moves[0] = _dummy_move(type_)  # テスト用に内部変数を直接変更
        t.run_move(battle, 0)
        assert battle.damage_calculator.power_modifier == 6144


def test_たべのこし():
    """たべのこし: ターン終了時回復"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    mon = battle.actives[0]
    # HPが満タンのときは回復しない
    battle.events.emit(Event.ON_TURN_END)
    battle.print_logs()
    assert not mon.item.revealed

    mon.hp = 1  # テスト用に内部変数を直接変更
    battle.events.emit(Event.ON_TURN_END)
    assert mon.item.revealed
    assert mon.hp == 1 + mon.max_hp // 16


def test_だいこんごうだま_ドラゴン技補正():
    """だいこんごうだま: ディアルガ(オリジン)のドラゴン技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", item_name="だいこんごうだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_だいこんごうだま_フォルムチェンジ():
    """だいこんごうだま: ディアルガをオリジンフォルムにフォルムチェンジする"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", item_name="だいこんごうだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ディアルガ(オリジン)"


def test_だいしらたま_ドラゴン技補正():
    """だいしらたま: パルキア(オリジン)のドラゴン技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="だいしらたま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_だいしらたま_フォルムチェンジ():
    """だいしらたま: パルキアをオリジンフォルムにフォルムチェンジする"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="だいしらたま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "パルキア(オリジン)"


def test_だいはっきんだま_ゴースト技補正():
    """だいはっきんだま: ギラティナ(オリジン)のゴースト技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(アナザー)", item_name="だいはっきんだま", move_names=["シャドーボール"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_だいはっきんだま_フォルムチェンジ():
    """だいはっきんだま: ギラティナ(アナザー)をオリジンフォルムにフォルムチェンジする"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(アナザー)", item_name="だいはっきんだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ギラティナ(オリジン)"


def test_だっしゅつパック_0ターン目にいかくで交代():
    """だっしゅつパック: 能力ダウンで交代"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    ejected_mon = state.team[0]
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_能力上昇では発動しない():
    """だっしゅつパック: 能力上昇では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック", move_names=["つるぎのまい"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    state = battle._player_states[0]
    mon = state.team[0]
    assert state.active_index == 0
    assert not mon.item.revealed
    assert mon.has_item()


def test_だっしゅつボタン():
    """だっしゅつボタン: ダメージを受けて交代"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    player = battle.players[0]
    print(battle.get_available_switch_commands(player))
    state = battle._player_states[0]
    ejected_mon = battle.actives[0]
    battle.advance_turn()
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_でんきだま_他種族は補正なし():
    """でんきだま: ピカチュウ以外は補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ライチュウ", item_name="でんきだま", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_でんきだま_物理技こうげき2倍():
    """でんきだま: ピカチュウの物理技こうげき2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="でんきだま", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 8192


def test_でんきだま_特殊技とくこう2倍():
    """でんきだま: ピカチュウの特殊技とくこう2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="でんきだま", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 8192


def test_とくせいガード_かたやぶりによる特性無効化をブロック():
    """とくせいガード: add_disabled_reasonによる特性無効化をブロックする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", item_name="とくせいガード")],
    )
    defender = battle.actives[1]
    result = battle.add_ability_disabled_reason(defender, "かたやぶり")
    assert not result
    assert defender.ability.enabled


def test_とくせいガード_なしの場合は特性が無効化される():
    """とくせいガード: 持っていない場合はかたやぶりで特性が無効化される（対照テスト）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    result = battle.add_ability_disabled_reason(defender, "かたやぶり")
    assert result
    assert not defender.ability.enabled


def test_はっきんだま_ゴースト技補正():
    """はっきんだま: ギラティナのゴースト技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(アナザー)", item_name="はっきんだま", move_names=["シャドーボール"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_はっきんだま_ドラゴン技補正():
    """はっきんだま: ギラティナのドラゴン技1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(アナザー)", item_name="はっきんだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_はっきんだま_他種族は補正なし():
    """はっきんだま: ギラティナ以外は補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="はっきんだま", move_names=["シャドーボール"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ブーストエナジー_こだいかっせいマジックルーム解除後に発動():
    """ブーストエナジー: マジックルーム解除後にこだいかっせいブーストが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コライドン", ability_name="こだいかっせい", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # マジックルーム下ではアイテムが無効で、ブーストが発動していないはず
    battle.add_item_disabled_reason(mon, "マジックルーム")
    assert mon.paradox_boost_stat is None or mon.paradox_boost_source == "item"
    # マジックルーム解除後にブーストが発動する
    battle.remove_item_disabled_reason(mon, "マジックルーム")
    assert mon.paradox_boost_stat is not None
    assert mon.paradox_boost_source == "item"


def test_ブーストエナジー_こだいかっせい登場時に発動():
    """ブーストエナジー: こだいかっせい持ちが登場時にブーストを発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コライドン", ability_name="こだいかっせい", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat is not None
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item()


def test_メトロノーム_初回は補正なし():
    """メトロノーム: 同じ技の初回使用は威力補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_メトロノーム_別技でリセット():
    """メトロノーム: 違う技を使うとカウントリセット"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0, 1)
    assert mon.item.count == 1
    assert mon.item.move_name == "でんきショック"


def test_メトロノーム_最大2倍():
    """メトロノーム: 6回目以降は威力2倍（上限）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 5
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8191


def test_メトロノーム_連続使用で威力増加():
    """メトロノーム: 2回目連続使用で威力1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 1
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
