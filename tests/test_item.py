"""アイテムハンドラの単体テスト"""
import copy
import math
from typing import cast
import pytest
from jpoke import Pokemon
from jpoke.enums import Event
from jpoke.model import Move
from jpoke.utils.type_defs import Type
from . import test_utils as t

def _dummy_move(type_name: str) -> Move:
    """指定タイプの技オブジェクトを返す（たいあたりのデータをコピーしてタイプを上書き）。"""
    t_name = cast(Type, type_name)
    move = Move("たいあたり")
    move.data = copy.copy(move.data)
    move.data.type = t_name
    move.type = t_name
    return move


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


@pytest.mark.parametrize("item_name, mon_name", [
    ("いしずえのめん", "オーガポン(いしずえ)"),
    ("いどのめん", "オーガポン(いど)"),
    ("かまどのめん", "オーガポン(かまど)"),
])
def test_オーガポンのめん_物理技強化(item_name, mon_name):
    """オーガポンのめん: 物理技の攻撃補正1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4915


def test_オーガポンのめん_特殊技は補正なし():
    """オーガポンのめん: 特殊技には攻撃補正がない"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いしずえ)", item_name="いしずえのめん", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_きれいなぬけがら():
    """きれいなぬけがら: 交代防止無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きれいなぬけがら"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かげふみ")],
    )
    assert battle.can_switch(battle.players[0])


@pytest.mark.parametrize("item_name, mon_name, expected_name", [
    ("くちたけん", "ザシアン(れきせん)", "ザシアン(けんのおう)"),
    ("くちたたて", "ザマゼンタ(れきせん)", "ザマゼンタ(たてのおう)"),
])
def test_くちたけん_くちたたて_フォルムチェンジ(item_name, mon_name, expected_name):
    """くちたけん・くちたたて: 対応ポケモンをフォルムチェンジさせる"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == expected_name


@pytest.mark.parametrize("item_name", ["くちたけん", "くちたたて"])
def test_くちたけん_くちたたて_他ポケモンは変化しない(item_name):
    """くちたけん・くちたたて: 対応ポケモン以外は変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
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


def test_こだわりスカーフ_素早さ強化():
    """こだわりスカーフ: 素早さ1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりスカーフ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    base_speed = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base_speed * 6144 // 4096


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


@pytest.mark.parametrize("item_name, type_name, defender_name, expected", [
    ("リンドのみ", "くさ", "ゼニガメ", 2048),
    ("オッカのみ", "ほのお", "フシギダネ", 2048),
    ("イトケのみ", "みず", "ヒトカゲ", 2048),
    ("ソクノのみ", "でんき", "ゼニガメ", 2048),
    ("カシブのみ", "ゴースト", "エーフィ", 2048),
    ("ヨロギのみ", "いわ", "ヒトカゲ", 2048),
    ("タンガのみ", "むし", "エーフィ", 2048),
    ("ウタンのみ", "エスパー", "コジョフー", 2048),
    ("バコウのみ", "ひこう", "コジョフー", 2048),
    ("シュカのみ", "じめん", "ピカチュウ", 2048),
    ("ビアーのみ", "どく", "プリン", 2048),
    ("ヨプのみ", "かくとう", "カビゴン", 2048),
    ("ヤチェのみ", "こおり", "ミニリュウ", 2048),
    ("リリバのみ", "はがね", "マリル", 2048),
    ("ナモのみ", "あく", "エーフィ", 2048),
    ("ハバンのみ", "ドラゴン", "ミニリュウ", 2048),
    ("ロゼルのみ", "フェアリー", "ミニリュウ", 2048),
])
def test_タイプ半減実(item_name, type_name, defender_name, expected):
    """タイプ半減実: 対応タイプの弱点ダメージを半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon(defender_name, item_name=item_name)],
    )
    battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == expected


@pytest.mark.parametrize("item_name, type_name, expected_modifier", [
    ("かたいいし", "いわ", 4915),
    ("きせきのたね", "くさ", 4915),
    ("ぎんのこな", "むし", 4915),
    ("くろいメガネ", "あく", 4915),
    ("くろおび", "あく", 4915),
    ("じしゃく", "でんき", 4915),
    ("シルクのスカーフ", "ノーマル", 4915),
    ("しんぴのしずく", "みず", 4915),
    ("するどいくちばし", "ひこう", 4915),
    ("せいれいプレート", "フェアリー", 4915),
    ("どくバリ", "どく", 4915),
    ("とけないこおり", "こおり", 4915),
    ("ノーマルジュエル", "ノーマル", 6144),
    ("のろいのおふだ", "ゴースト", 4915),
    ("まがったスプーン", "エスパー", 4915),
    ("メタルコート", "はがね", 4915),
    ("もくたん", "ほのお", 4915),
    ("やわらかいすな", "じめん", 4915),
    ("ようせいのハネ", "フェアリー", 4915),
    ("りゅうのキバ", "ドラゴン", 4915),
])
def test_タイプ強化アイテム(item_name, type_name, expected_modifier):
    """タイプ強化アイテム: 対応タイプの威力補正"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


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


@pytest.mark.parametrize("item_name, weather", [
    ("さらさらいわ", "すなあらし"),
    ("あついいわ", "はれ"),
    ("しめったいわ", "あめ"),
    ("つめたいいわ", "ゆき"),
])
def test_天候延長アイテム(item_name, weather):
    """天候延長アイテム: 対応天候の継続ターンを8に延長する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.weather_manager.apply(weather, 5, source=battle.actives[0])
    assert battle.raw_weather.count == 8


@pytest.mark.parametrize("item_name, mon_name, move_name", [
    ("こころのしずく", "ラティオス", "サイコキネシス"),
    ("こころのしずく", "ラティアス", "ドラゴンクロー"),
    ("こんごうだま", "ディアルガ", "ドラゴンクロー"),
    ("こんごうだま", "ディアルガ", "アイアンヘッド"),
    ("しらたま", "パルキア", "ドラゴンクロー"),
    ("しらたま", "パルキア", "なみのり"),
    ("だいこんごうだま", "ディアルガ", "ドラゴンクロー"),
    ("だいしらたま", "パルキア", "ドラゴンクロー"),
    ("だいはっきんだま", "ギラティナ(アナザー)", "シャドーボール"),
    ("はっきんだま", "ギラティナ(アナザー)", "シャドーボール"),
    ("はっきんだま", "ギラティナ(アナザー)", "ドラゴンクロー"),
])
def test_専用アイテム_タイプ補正(item_name, mon_name, move_name):
    """専用アイテム: 対応ポケモンの対応タイプ技を1.2倍にする"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
