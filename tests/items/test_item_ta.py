"""アイテムハンドラの単体テスト"""
import copy
from typing import cast
import pytest
from jpoke import Pokemon
from jpoke.enums import Command
from jpoke.model import Move
from jpoke.types import Type
from .. import test_utils as t

def _dummy_move(type_name: str) -> Move:
    """指定タイプの技オブジェクトを返す（たいあたりのデータをコピーしてタイプを上書き）。"""
    t_name = cast(Type, type_name)
    move = Move("たいあたり")
    move.data = copy.copy(move.data)
    move.data.type = t_name
    move.type = t_name
    return move


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
    ("リリバのみ", "はがね", "ピッピ"),
    ("ナモのみ", "あく", "エーフィ"),
    ("ハバンのみ", "ドラゴン", "ミニリュウ"),
    ("ロゼルのみ", "フェアリー", "ミニリュウ"),
])
def test_タイプ半減実(item_name, type_name, defender_name):
    """タイプ半減実: 対応タイプの弱点ダメージを半減して消費する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon(defender_name, item_name=item_name)],
    )
    battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048
    assert not battle.actives[1].has_item()  # 1度使うと消費される


@pytest.mark.parametrize("item_name, type_name", [
    ("かたいいし", "いわ"),
    ("きせきのたね", "くさ"),
    ("ぎんのこな", "むし"),
    ("くろいメガネ", "あく"),
    ("くろおび", "かくとう"),
    ("じしゃく", "でんき"),
    ("シルクのスカーフ", "ノーマル"),
    ("しんぴのしずく", "みず"),
    ("するどいくちばし", "ひこう"),
    ("せいれいプレート", "フェアリー"),
    ("どくバリ", "どく"),
    ("とけないこおり", "こおり"),
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


def test_たつじんのおび_効果抜群で1_2倍():
    """たつじんのおび: 効果抜群技の威力を1.2倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たつじんのおび", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4915


def test_たつじんのおび_等倍では補正なし():
    """たつじんのおび: 等倍の技では補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たつじんのおび", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096


def test_たべのこし():
    """たべのこし: ターン終了時回復"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    mon = battle.actives[0]
    # HPが満タンのときは回復しない
    t.end_turn(battle)
    battle.print_logs()
    assert not mon.item.revealed

    mon.hp = 1  # テスト用に内部変数を直接変更
    t.end_turn(battle)
    assert mon.item.revealed
    assert mon.hp == 1 + mon.max_hp // 16


def test_たべのこし_かいふくふうじ中は回復しない():
    """たべのこし: かいふくふうじ状態のときは回復しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="たべのこし")],
        volatile0={"かいふくふうじ": 1},
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_タラプのみ_あまのじゃくによる下降はしろいきりで防げない():
    """タラプのみ: あまのじゃくで反転した下降は自発的な変化とみなされ、しろいきりでも防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="タラプのみ", ability_name="あまのじゃく")],
        accuracy=100,
        side1={"しろいきり": 1},
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == -1
    assert not foe.has_item()


def test_タラプのみ_ちからずくの対象技では発動しない():
    """タラプのみ: ちからずく所持者が追加効果ありの特殊技を使った場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ニドキング", ability_name="ちからずく",
            move_names=["でんきショック"],
        )],
        team1=[Pokemon("ゼニガメ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 0
    assert foe.has_item()


def test_タラプのみ_とくぼうランクが最大のとき発動しない():
    """タラプのみ: すでにとくぼうランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.rank["spd"] = 6
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 6
    assert foe.has_item()


def test_タラプのみ_物理技では発動しない():
    """タラプのみ: 物理技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 0


def test_タラプのみ_特殊技被弾でD上昇():
    """タラプのみ: 特殊技でダメージを受けたときとくぼう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["spd"] == 1
    assert not foe.has_item()


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_だいこんごうだま_ディアルガから奪えない(move_name):
    """だいこんごうだま: ディアルガ(オリジン)が持っている間ははたきおとす・どろぼう等で奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ディアルガ", item_name="だいこんごうだま")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_item("だいこんごうだま")


def test_だいこんごうだま_トリックで交換されない():
    """だいこんごうだま: ディアルガ(オリジン)が持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("ディアルガ", item_name="だいこんごうだま")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "だいこんごうだま"


def test_だいこんごうだま_フォルムチェンジ():
    """だいこんごうだま: ディアルガが持って登場するとオリジンフォルムになる"""
    battle = t.start_battle(
        team0=[Pokemon("ディアルガ", item_name="だいこんごうだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ディアルガ(オリジン)"


def test_だいこんごうだま_通常のディアルガへ渡せない():
    """だいこんごうだま: 通常の姿のディアルガへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="だいこんごうだま")],
        team1=[Pokemon("ディアルガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "だいこんごうだま"
    assert not defender.has_item()
    assert defender.name == "ディアルガ"


def test_だいしらたま_トリックで交換されない():
    """だいしらたま: パルキア(オリジン)が持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("パルキア", item_name="だいしらたま")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "だいしらたま"


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_だいしらたま_パルキアから奪えない(move_name):
    """だいしらたま: パルキア(オリジン)が持っている間ははたきおとす・どろぼう等で奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("パルキア", item_name="だいしらたま")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_item("だいしらたま")


def test_だいしらたま_フォルムチェンジ():
    """だいしらたま: パルキアが持って登場するとオリジンフォルムになる"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="だいしらたま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "パルキア(オリジン)"


def test_だいしらたま_通常のパルキアへ渡せない():
    """だいしらたま: 通常の姿のパルキアへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="だいしらたま")],
        team1=[Pokemon("パルキア")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "だいしらたま"
    assert not defender.has_item()
    assert defender.name == "パルキア"


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_だいはっきんだま_ギラティナから奪えない(move_name):
    """だいはっきんだま: ギラティナ(オリジン)が持っている間ははたきおとす・どろぼう等で奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ギラティナ(アナザー)", item_name="だいはっきんだま")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_item("だいはっきんだま")


def test_だいはっきんだま_トリックで交換されない():
    """だいはっきんだま: ギラティナ(オリジン)が持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("ギラティナ(アナザー)", item_name="だいはっきんだま")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "だいはっきんだま"


def test_だいはっきんだま_フォルムチェンジ():
    """だいはっきんだま: ギラティナ(アナザー)が持って登場するとオリジンフォルムになる"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(アナザー)", item_name="だいはっきんだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ギラティナ(オリジン)"


def test_だいはっきんだま_通常のギラティナへ渡せない():
    """だいはっきんだま: アナザーフォルムのギラティナへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="だいはっきんだま")],
        team1=[Pokemon("ギラティナ(アナザー)")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "だいはっきんだま"
    assert not defender.has_item()
    assert defender.name == "ギラティナ(アナザー)"


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


def test_だっしゅつパック_すばやさが一番高いポケモンのみ発動する():
    """だっしゅつパック: 複数のポケモンが同時にランクを下げられた場合、すばやさが一番高いポケモンのみ発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いかく", item_name="だっしゅつパック", nature="ようき"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", ability_name="いかく", item_name="だっしゅつパック"), Pokemon("ゲンガー")],
    )
    state0 = battle._player_states[0]
    state1 = battle._player_states[1]
    # ピカチュウ（すばやさが高い）のだっしゅつパックのみ発動して交代する
    assert state0.active_index == 1
    assert not state0.team[0].has_item()
    # カビゴン（すばやさが低い）は場に残り、だっしゅつパックも消費されない
    assert state1.active_index == 0
    assert state1.team[0].has_item("だっしゅつパック")
    assert state1.team[0].rank["atk"] == -1


def test_だっしゅつパック_とらわれ状態でも交代できる():
    """だっしゅつパック: ねをはるなどのとらわれ状態を無視して発動する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="だっしゅつパック", move_names=["ねをはる"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", move_names=["Gのちから"])],
        accuracy=100,
    )
    battle.step()
    state0 = battle._player_states[0]
    ejected_mon = state0.team[0]
    assert state0.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_バトンタッチで引き継いだランクでは発動しない():
    """だっしゅつパック: バトンタッチで引き継いだランク低下では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ", item_name="だっしゅつパック")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].rank["atk"] == -1
    battle.step()
    state0 = battle._player_states[0]
    new_mon = state0.team[1]
    assert state0.active_index == 1
    assert new_mon.rank["atk"] == -1
    assert new_mon.has_item("だっしゅつパック")


def test_だっしゅつパック_まけんきで直後にランクを打ち消しても発動する():
    """だっしゅつパック: まけんきで下がったランクを直後に打ち消した場合も発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="まけんき", item_name="だっしゅつパック"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    ejected_mon = state.team[0]
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_ミラーアーマーで跳ね返しても発動する():
    """だっしゅつパック: ミラーアーマーで能力低下を跳ね返した場合でも、実際のランクは変化しないが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ミラーアーマー", item_name="だっしゅつパック"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    ejected_mon = state.team[0]
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()
    assert ejected_mon.rank["atk"] == 0


def test_だっしゅつパック_ランクが下限に達しなくても発動する():
    """だっしゅつパック: +2から+1になるなど、ランクがマイナスにならなかった場合でも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["Gのちから"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつパック"), Pokemon("イーブイ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"def": 2})
    assert defender.rank["def"] == 2
    battle.step()
    state1 = battle._player_states[1]
    ejected_mon = state1.team[0]
    # ランクが-1にならず+2→+1になっただけでも発動する
    assert state1.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_わるいてぐせに奪われた場合は発動しない():
    """だっしゅつパック: 自分の能力を下げる直接攻撃でわるいてぐせに奪われた場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="だっしゅつパック", move_names=["アームハンマー"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
        accuracy=100,
    )
    battle.step()
    state0 = battle._player_states[0]
    mon = state0.team[0]
    assert state0.active_index == 0
    assert not mon.has_item()
    assert battle._player_states[1].team[0].has_item("だっしゅつパック")


def test_だっしゅつパック_交代できるポケモンがいないときは発動しない():
    """だっしゅつパック: 交代できる残りポケモンがいないときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    mon = state.team[0]
    assert state.active_index == 0
    assert not mon.item.revealed
    assert mon.has_item()


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


def test_だっしゅつパック_自分の技の自傷効果でも発動する():
    """だっしゅつパック: 自分の技で能力が下がった場合も発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック", move_names=["アーマーキャノン"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.step()
    state0 = battle._player_states[0]
    ejected_mon = state0.team[0]
    assert state0.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつボタン():
    """だっしゅつボタン: ダメージを受けて交代"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    state = battle._player_states[0]
    ejected_mon = battle.actives[0]
    battle.step()
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつボタン_こらえるでHP1のまま耐えたときも発動する():
    """だっしゅつボタン: こらえるでHP1のまま耐えた（実ダメージ0）ときも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)

    battle.step()

    state1 = battle._player_states[1]
    assert defender.hp == 1
    assert not defender.fainted
    assert state1.active_index == 1
    assert defender.item.revealed
    assert not defender.has_item()


def test_だっしゅつボタン_ちからずくの効果が発動した技を受けたときは発動しない():
    """だっしゅつボタン: 特性ちからずくの効果が発動した追加効果あり技を受けたときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ニドキング", ability_name="ちからずく", move_names=["Gのちから"])],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    battle.step()
    state1 = battle._player_states[1]
    defender = state1.team[0]
    assert state1.active_index == 0
    assert defender.has_item("だっしゅつボタン")


def test_だっしゅつボタン_とらわれ状態でも交代できる():
    """だっしゅつボタン: ねをはるなどのとらわれ状態を無視して発動する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="だっしゅつボタン", move_names=["ねをはる"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", move_names=["Gのちから"])],
        accuracy=100,
    )
    battle.step()
    state0 = battle._player_states[0]
    ejected_mon = state0.team[0]
    assert state0.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつボタン_ばけのかわで肩代わりしたときも発動する():
    """だっしゅつボタン: 特性ばけのかわでダメージを肩代わりした場合（実ダメージ0）でも発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.fix_damage(battle, 30)

    battle.step()

    state1 = battle._player_states[1]
    assert defender.ability.enabled is False
    assert state1.active_index == 1
    assert defender.item.revealed
    assert not defender.has_item()


def test_だっしゅつボタン_ひんしになったときは発動しない():
    """だっしゅつボタン: 相手の攻撃でひんしになったときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じしん"])],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    fainted_mon = battle.actives[1]
    t.fix_damage(battle, 9999)

    battle.step()

    state1 = battle._player_states[1]
    assert fainted_mon.fainted
    assert state1.active_index == 1
    assert fainted_mon.has_item("だっしゅつボタン")


def test_だっしゅつボタン_みがわりに阻まれたときは発動しない():
    """だっしゅつボタン: みがわりに攻撃を防がれたとき（実ダメージ0）は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)

    battle.step()

    state1 = battle._player_states[1]
    assert state1.active_index == 0
    assert defender.has_item("だっしゅつボタン")


def test_だっしゅつボタン_控えがいないと発動しない():
    """だっしゅつボタン: 交代先の控えがいないときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつボタン")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.step()
    state0 = battle._player_states[0]
    assert state0.active_index == 0
    assert mon.has_item("だっしゅつボタン")


def test_チイラのみ_こうげきランクが最大のとき発動しない():
    """チイラのみ: すでにこうげきランクが最大まで上がっているときはHP1/4以下でも発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="チイラのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.rank["atk"] = 6
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.rank["atk"] == 6
    assert mon.has_item()


def test_ちからのハチマキ_物理技1_1倍():
    """ちからのハチマキ: 物理技の威力を1.1倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ちからのハチマキ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4505


def test_ちからのハチマキ_特殊技には補正なし():
    """ちからのハチマキ: 特殊技には補正しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ちからのハチマキ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_チーゴのみ_やけど付与直後に即時回復する():
    """チーゴのみ: やけど付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("カビゴン", item_name="チーゴのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert not defender.has_item()


def test_でかいきんのたま_なげつけるで威力130になる():
    """でかいきんのたま: なげつけるで使用すると威力130になる（第8世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="でかいきんのたま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 130
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_でんきだま_こんらん自傷ダメージには補正なし():
    """でんきだま: こんらんの自傷ダメージには攻撃補正がかからない（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="でんきだま")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096
    assert attacker.hp < attacker.max_hp


@pytest.mark.parametrize("mon_name", ["ピチュー", "ライチュウ"])
def test_でんきだま_ピチューライチュウには効果なし(mon_name):
    """でんきだま: ピチュー・ライチュウが持っても攻撃補正はかからない"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name="でんきだま", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


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


def test_とくせいガード_かたやぶりによる特性無効化をブロックした際にアイテムが公開される():
    """とくせいガード: 特性無効化をブロックした際にアイテムが公開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", item_name="とくせいガード")],
    )
    defender = battle.actives[1]
    assert not defender.item.revealed
    battle.add_ability_disabled_reason(defender, "かたやぶり")
    assert defender.item.revealed


def test_とくせいガード_シンプルビームによる特性変更をブロック():
    """とくせいガード: 所持者に対するシンプルビームは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シンプルビーム"])],
        team1=[Pokemon("カビゴン", ability_name="せいでんき", item_name="とくせいガード")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ability.name == "せいでんき"


def test_とくせいガード_スキルスワップによる特性変更をブロック():
    """とくせいガード: 所持者に対するスキルスワップ、または所持者が使用するスキルスワップは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", ability_name="めんえき", item_name="とくせいガード")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は入れ替わらない
    assert attacker.ability.name == "せいでんき"
    assert defender.ability.name == "めんえき"


def test_とくせいガード_トレースによる特性コピーをブロック():
    """とくせいガード: 所持者のトレースは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="トレース", item_name="とくせいガード")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    tracer = battle.actives[0]
    assert tracer.ability.base_name == "トレース"


def test_とくせいガード_なかまづくりによる特性変更をブロック():
    """とくせいガード: 所持者に対するなかまづくりは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なかまづくり"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", ability_name="あついしぼう", item_name="とくせいガード")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ability.name == "あついしぼう"


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


def test_とくせいガード_なやみのタネによる特性変更をブロック():
    """とくせいガード: 所持者に対するなやみのタネは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なやみのタネ"])],
        team1=[Pokemon("カビゴン", ability_name="せいでんき", item_name="とくせいガード")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ability.name == "せいでんき"


def test_とくせいガード_なりきりによる特性変更をブロック():
    """とくせいガード: 所持者はなりきりを使用して自分の特性を変えることもできない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なりきり"], ability_name="せいでんき", item_name="とくせいガード")],
        team1=[Pokemon("カビゴン", ability_name="あついしぼう")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.ability.name == "せいでんき"


def test_とくせいガード_ぶきようでも特性無効化のブロックは発動する():
    """とくせいガード: 所持者の特性がぶきようであっても道具の効果は発動し、特性の無効化を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="ぶきよう", item_name="とくせいガード")],
    )
    defender = battle.actives[1]
    # ぶきようの効果自体はアイテムを無効化している
    assert not defender.item.enabled
    result = battle.add_ability_disabled_reason(defender, "かたやぶり")
    assert not result
    assert defender.ability.enabled


def test_とくせいガード_使用者が持つ場合もスキルスワップは失敗する():
    """とくせいガード: 使用者側が所持している場合もスキルスワップは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき", item_name="とくせいガード")],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は入れ替わらない
    assert attacker.ability.name == "せいでんき"
    assert defender.ability.name == "めんえき"


def test_とつげきチョッキ_アンコールで変化技を強制されたターンは使用できる():
    """とつげきチョッキ: 実行時ブロックは持たないため、アンコールで変化技を強制されたターンは正常に実行できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり", "なきごえ"], item_name="とつげきチョッキ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(mon, "アンコール", move_name="なきごえ")
    t.run_move(battle, 0, move_idx=0)
    assert mon.executed_move.name == "なきごえ"
    assert foe.rank["atk"] == -1


def test_とつげきチョッキ_変化技しか持たない場合わるあがきのみ選択可能():
    """とつげきチョッキ: 変化技しか持たないポケモンはわるあがきのみ選択可能になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"], item_name="とつげきチョッキ")],
        team1=[Pokemon("カビゴン")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert commands == [Command.STRUGGLE]


def test_とつげきチョッキ_変化技はコマンド選択肢から除外される():
    """とつげきチョッキ: 変化技はコマンド選択肢から除外される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "なきごえ"], item_name="とつげきチョッキ")],
        team1=[Pokemon("カビゴン")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert Command.MOVE_1 not in commands
    assert Command.MOVE_0 in commands


def test_とつげきチョッキ_物理技には防御補正なし():
    """とつげきチョッキ: 物理技には防御補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="とつげきチョッキ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 4096


def test_とつげきチョッキ_特殊技にとくぼう1_5倍():
    """とつげきチョッキ: 特殊技に対してとくぼうを1.5倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="とつげきチョッキ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 6144


def test_どくどくだま_どくタイプとはがねタイプには発動しない():
    """どくどくだま: どくタイプ・はがねタイプのポケモンにはもうどくが付与されない"""
    battle = t.start_battle(
        team0=[
            Pokemon("フシギダネ", item_name="どくどくだま"),  # くさ/どくタイプ
            Pokemon("コイル", item_name="どくどくだま"),  # でんき/はがねタイプ
        ],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.ailment.is_active

    t.run_switch(battle, 0, 1)
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.ailment.is_active


def test_どくどくだま_ねむけと重なった場合ねむり優先():
    """どくどくだま: ねむけからねむり状態になるターンと発動ターンが重なった場合、
    ねむけ(priority110)が先に処理されるためねむり状態が優先されもうどくは付与されない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくどくだま")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねむけ": 1},
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name == "ねむり"


def test_どくどくだま_ミストフィールド解除ターンから発動():
    """どくどくだま: ミストフィールドはもうどくの付与を防ぐが、
    フィールドの継続終了(priority140)がどくどくだまの発動(priority150)より先に処理されるため、
    ミストフィールドが解除されたそのターンからどくどくだまが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくどくだま")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", 1),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert battle.terrain.name != "ミストフィールド"
    assert mon.ailment.name == "もうどく"


def test_どくどくだま_発動するターンにどくダメージは受けない():
    """どくどくだま: priority150でどく・もうどくダメージ(90)より後に発動するため、
    発動したそのターンにもうどくダメージは発生しない（翌ターンから発生する）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくどくだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    hp_before = mon.hp
    t.end_turn(battle)
    assert mon.ailment.name == "もうどく"
    assert mon.hp == hp_before  # このターンはもうどくダメージを受けない

    t.end_turn(battle)
    assert mon.hp == hp_before - hp_before // 16  # 翌ターンからもうどくダメージを受ける（1ターン目）


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
