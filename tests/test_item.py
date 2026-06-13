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


def test_きれいなぬけがら():
    """きれいなぬけがら: 交代防止無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きれいなぬけがら"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かげふみ")],
    )
    assert battle.can_switch(battle.players[0])


@pytest.mark.parametrize(
    "item_name, mon_name, expected_name",
    [
        ("くちたけん", "ザシアン(れきせん)", "ザシアン(けんのおう)"),
        ("くちたたて", "ザマゼンタ(れきせん)", "ザマゼンタ(たてのおう)"),
    ]
)
def test_くちたけん_くちたたて_フォルムチェンジ(item_name, mon_name, expected_name):
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


@pytest.mark.parametrize("item_name, type_name, defender_name", [
    ("リンドのみ", "くさ", "ゼニガメ"),
    ("オッカのみ", "ほのお", "フシギダネ"),
    ("イトケのみ", "みず", "ヒトカゲ"),
    ("ソクノのみ", "でんき", "ゼニガメ"),
    ("カシブのみ", "ゴースト", "エーフィ"),
    ("ヨロギのみ", "いわ", "ヒトカゲ"),
    ("タンガのみ", "むし", "エーフィ"),
    ("ウタンのみ", "エスパー", "コジョフー"),
    ("バコウのみ", "ひこう", "コジョフー"),
    ("シュカのみ", "じめん", "ピカチュウ"),
    ("ビアーのみ", "どく", "プリン"),
    ("ヨプのみ", "かくとう", "カビゴン"),
    ("ヤチェのみ", "こおり", "ミニリュウ"),
    ("リリバのみ", "はがね", "マリル"),
    ("ナモのみ", "あく", "エーフィ"),
    ("ハバンのみ", "ドラゴン", "ミニリュウ"),
    ("ロゼルのみ", "フェアリー", "ミニリュウ"),
])
def test_タイプ半減実(item_name, type_name, defender_name):
    """タイプ半減実: 対応タイプの弱点ダメージを半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon(defender_name, item_name=item_name)],
    )
    battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048


@pytest.mark.parametrize("item_name, type_name", [
    ("かたいいし", "いわ"),
    ("きせきのたね", "くさ"),
    ("ぎんのこな", "むし"),
    ("くろいメガネ", "あく"),
    ("くろおび", "あく"),
    ("じしゃく", "でんき"),
    ("シルクのスカーフ", "ノーマル"),
    ("しんぴのしずく", "みず"),
    ("するどいくちばし", "ひこう"),
    ("せいれいプレート", "フェアリー"),
    ("どくバリ", "どく"),
    ("とけないこおり", "こおり"),
    ("ノーマルジュエル", "ノーマル"),
    ("のろいのおふだ", "ゴースト"),
    ("まがったスプーン", "エスパー"),
    ("メタルコート", "はがね"),
    ("もくたん", "ほのお"),
    ("やわらかいすな", "じめん"),
    ("ようせいのハネ", "フェアリー"),
    ("りゅうのキバ", "ドラゴン"),
])
def test_タイプ強化アイテム(item_name, type_name):
    """タイプ強化アイテム: 対応タイプの威力補正"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


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

# TODO : メトロノームのテストでは、実際にrun_moveで指定回数だけ技を使用したときの補正係数を検証すべき。
# 使用回数と補正係数の組み合わせはパラメタライズでまとめる。


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


@pytest.mark.parametrize(
    "item_name, weather",
    [
        ("さらさらいわ", "すなあらし"),
        ("あついいわ", "はれ"),
        ("しめったいわ", "あめ"),
        ("つめたいいわ", "ゆき"),
    ]
)
def test_天候延長アイテム(item_name, weather):
    """天候延長アイテム: 対応天候の継続ターンを8に延長する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.weather_manager.apply(weather, 5, source=battle.actives[0])
    assert battle.raw_weather.count == 8


@pytest.mark.parametrize(
    "item_name, mon_name, move_name, expected_modifier",
    [
        ("いしずえのめん", "オーガポン(いしずえ)", "たいあたり", 4915),
        ("いどのめん", "オーガポン(いど)", "たいあたり", 4915),
        ("かまどのめん", "オーガポン(かまど)", "たいあたり", 4915),
        ("こころのしずく", "ラティオス", "サイコキネシス", 4915),
        ("こころのしずく", "ラティアス", "ドラゴンクロー", 4915),
        ("こんごうだま", "ディアルガ", "ドラゴンクロー", 4915),
        ("こんごうだま", "ディアルガ", "アイアンヘッド", 4915),
        ("しらたま", "パルキア", "ドラゴンクロー", 4915),
        ("しらたま", "パルキア", "なみのり", 4915),
        ("だいこんごうだま", "ディアルガ", "ドラゴンクロー", 4915),
        ("だいしらたま", "パルキア", "ドラゴンクロー", 4915),
        ("だいはっきんだま", "ギラティナ(アナザー)", "シャドーボール", 4915),
        ("でんきだま", "ピカチュウ", "たいあたり", 8192),
        ("でんきだま", "ピカチュウ", "でんきショック", 8192),
        ("はっきんだま", "ギラティナ(アナザー)", "シャドーボール", 4915),
        ("はっきんだま", "ギラティナ(アナザー)", "ドラゴンクロー", 4915),
    ]
)
def test_専用アイテム補正(item_name, mon_name, move_name, expected_modifier):
    # TODO : 補正がかからないケースも追加する
    """専用アイテム: 対応ポケモンの対応タイプ技を1.2倍にする"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
