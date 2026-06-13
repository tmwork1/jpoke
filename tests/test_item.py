"""アイテムハンドラの単体テスト"""
import copy
import math
from typing import cast
import pytest
from jpoke import Pokemon
from jpoke.core.context import EventContext
from jpoke.enums import Event
from jpoke.model import Move
from jpoke.utils.type_defs import Type
from . import test_utils as t

# TODO : 複数アイテムをパラメタライズでまとめたテストはモジュール最下部に配置する。

def _dummy_move(type_name: str) -> Move:
    """指定タイプの技オブジェクトを返す（たいあたりのデータをコピーしてタイプを上書き）。"""
    t_name = cast(Type, type_name)
    move = Move("たいあたり")
    move.data = copy.copy(move.data)
    move.data.type = t_name
    move.type = t_name
    return move

# TODO : メトロノームのテストでは、実際にrun_moveで指定回数だけ技を使用したときの補正係数を検証すべき。
# 使用回数と補正係数の組み合わせはパラメタライズでまとめる。


@pytest.mark.parametrize("item_name, stat, amount", [
    ("チイラのみ", "A", 1),
    ("カムラのみ", "S", 1),
    ("ヤタピのみ", "C", 1),
    ("リュガのみ", "B", 1),
    ("ズアのみ", "D", 1),
])
def test_HP25以下でランク上昇するきのみ(item_name, stat, amount):
    """HP1/4以下になった瞬間に能力ランクを上昇させる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.rank[stat] == amount
    assert not mon.has_item()


@pytest.mark.parametrize("item_name", ["ウイのみ", "イアのみ", "フィラのみ", "マゴのみ", "バンジのみ"])
def test_HP25以下で回復するきのみ(item_name):
    """HP1/4以下になった瞬間に最大HPの1/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()


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


def test_アッキのみ_物理技でB上昇():
    """アッキのみ: 物理技ダメージを受けたときぼうぎょ+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゼニガメ", item_name="アッキのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["B"] == 1
    assert not foe.has_item()


def test_アッキのみ_特殊技では発動しない():
    """アッキのみ: 特殊技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="アッキのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["B"] == 0


def test_あつぞこブーツ_ステルスロック無効():
    """あつぞこブーツ: ステルスロックダメージを無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", item_name="あつぞこブーツ")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    raichu = battle._player_states[0].team[1]
    initial_hp = raichu.max_hp
    t.run_switch(battle, 0, 1)
    assert raichu.hp == initial_hp


def test_いかさまダイス_ヒット数4():
    """いかさまダイス: 2-5回技のヒット数を4か5に固定する（4ヒット側）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="いかさまダイス", move_names=["みだれひっかき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)  # < 0.5 → 4ヒット
    foe = battle.actives[1]
    initial_hp = foe.max_hp
    t.run_move(battle, 0)
    assert foe.hp == initial_hp - 4


def test_いかさまダイス_ヒット数5():
    """いかさまダイス: 2-5回技のヒット数を4か5に固定する（5ヒット側）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="いかさまダイス", move_names=["みだれひっかき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.9)  # >= 0.5 → 5ヒット
    foe = battle.actives[1]
    initial_hp = foe.max_hp
    t.run_move(battle, 0)
    assert foe.hp == initial_hp - 5


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


def test_ウイのみ_HP25超では発動しない():
    """ウイのみ: HPが25%を超えているときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ウイのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 2
    battle.modify_hp(mon, v=-1)
    assert mon.has_item()


def test_エレキシード_エレキフィールドで防御上昇():
    """エレキシード: エレキフィールド展開時に登場してぼうぎょ+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="エレキシード")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.rank["B"] == 1
    assert not mon.has_item()


def test_エレキシード_フィールドなしでは発動しない():
    """エレキシード: エレキフィールドがないとき発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="エレキシード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["B"] == 0
    assert mon.has_item()


def test_おうじゃのしるし_ひるまない確率():
    """おうじゃのしるし: 乱数が0.1以上のときひるまない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="おうじゃのしるし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_おうじゃのしるし_ひるみ付与():
    """おうじゃのしるし: 攻撃命中時10%の確率でひるみ付与"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="おうじゃのしるし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_おおきなねっこ_吸収技の回復量増加():
    """おおきなねっこ: 吸収技の回収量を1.3倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="おおきなねっこ", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.fix_damage(battle, 100)
    t.run_move(battle, 0)
    expected_hp = min(1 + 65, attacker.max_hp)  # 100 * 50% * 1.3 = 65
    assert attacker.hp == expected_hp


def test_オボンのみ_HP50以下で回復():
    """オボンのみ: HP1/2以下になった瞬間に最大HPの1/4を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + mon.max_hp // 4
    assert not mon.has_item()


def test_オボンのみ_HP50超では発動しない():
    """オボンのみ: HPが50%より多いときは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 2
    battle.modify_hp(mon, v=-1)
    assert mon.has_item()


def test_オレンのみ_HP50以下で10回復():
    """オレンのみ: HP1/2以下になった瞬間に10HP回復する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="オレンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 2 + 10
    assert not mon.has_item()


def test_おんみつマント_追加効果を無効化():
    """おんみつマント: 相手の技の追加効果を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン", item_name="おんみつマント")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name != "まひ"


def test_オーガポンのめん_特殊技には補正なし():
    """オーガポンのめん: 特殊技（物理以外）には攻撃補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いしずえ)", item_name="いしずえのめん", move_names=["エナジーボール"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_かいがらのすず_攻撃後HP回復():
    """かいがらのすず: 攻撃技命中時に最大HPの1/8を回復"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="かいがらのすず", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + attacker.max_hp // 8


def test_かえんだま_ターン終了でやけど():
    """かえんだま: ターン終了時にやけどを付与する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="かえんだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name == "やけど"


def test_カゴのみ_ターン終了でねむり回復():
    """カゴのみ: ターン終了時にねむりを回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="カゴのみ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("ねむり", 3),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name != "ねむり"
    assert not mon.has_item()


def test_カゴのみ_ねむり以外では発動しない():
    """カゴのみ: ねむり以外の状態異常では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="カゴのみ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("まひ", None),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.has_item()


def test_かるいし_素早さ2倍():
    """かるいし: 素早さを2倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="かるいし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    base_speed = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base_speed * 8192 // 4096


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


def test_きあいのハチマキ_確率でひんしにならない():
    """きあいのハチマキ: 11.7%の確率でひんし以上のダメージをHP1で耐える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きあいのハチマキ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)  # < 0.117 → 発動
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
    t.fix_random(battle, 0.5)  # >= 0.117 → 発動しない
    t.run_move(battle, 1)
    assert mon.hp == 0


def test_きれいなぬけがら():
    """きれいなぬけがら: 交代防止無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きれいなぬけがら"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かげふみ")],
    )
    assert battle.can_switch(battle.players[0])


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


def test_クラボのみ_ターン終了でまひ回復():
    """クラボのみ: ターン終了時にまひを回復する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="クラボのみ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("まひ", None),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name != "まひ"
    assert not mon.has_item()


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
    base_speed = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base_speed * 2048 // 4096


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


def test_グラスシード_グラスフィールドで防御上昇():
    """グラスシード: グラスフィールド展開時に登場してぼうぎょ+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="グラスシード")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("グラスフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.rank["B"] == 1
    assert not mon.has_item()


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
    base_speed = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base_speed * 6144 // 4096


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


def test_サイコシード_サイコフィールドでとくぼう上昇():
    """サイコシード: サイコフィールド展開時にとくぼう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="サイコシード")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.rank["D"] == 1
    assert not mon.has_item()


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


def test_しめつけバンド_バインドダメージ増加():
    """しめつけバンド: バインドダメージを最大HPの1/6に増加する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="しめつけバンド")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.volatile_manager.apply(foe, "バインド", count=3, source=mon)
    hp_before = foe.hp
    t.end_turn(battle)
    assert foe.hp == hp_before - foe.max_hp // 6


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
    assert mon.rank["C"] == -2


def test_しろいハーブ_能力低下を1度だけキャンセル():
    """しろいハーブ: 自分の技による能力低下を最初の1回キャンセルする"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", item_name="しろいハーブ", move_names=["リーフストーム"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["C"] == 0
    assert not mon.has_item()


def test_しんかのきせき_未進化ポケモンの防御1_5倍():
    """しんかのきせき: 未進化ポケモンのぼうぎょ・とくぼうを1.5倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゼニガメ", item_name="しんかのきせき")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_modifier == 6144


def test_じゃくてんほけん_効果抜群でAC上昇():
    """じゃくてんほけん: 効果抜群の攻撃を受けたときA・C+2"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="じゃくてんほけん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["A"] == 2
    assert foe.rank["C"] == 2
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
    assert foe.rank["A"] == 0
    assert foe.has_item()


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


def test_じゅうでんち_でんき以外では発動しない():
    """じゅうでんち: でんき以外の技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="じゅうでんち")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["A"] == 0
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
    assert foe.rank["A"] == 1
    assert not foe.has_item()


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
    assert mon.rank["A"] == 2
    assert not mon.has_item()


def test_するどいキバ_ひるみ付与():
    """するどいキバ: 攻撃命中時10%の確率でひるみ付与"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="するどいキバ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


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


def test_せんせいのツメ_先制確率で先攻():
    """せんせいのツメ: 23.4%の確率で行動順が1段階早くなる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="せんせいのツメ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.fix_random(battle, 0.0)  # < 0.234 → 先制
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]  # カビゴンが先攻


def test_せんせいのツメ_非発動時は通常の順番():
    """せんせいのツメ: 発動しないとき通常の行動順"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="せんせいのツメ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.fix_random(battle, 0.5)  # >= 0.234 → 発動しない
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[1]  # ピカチュウが先攻（素早さ優位）


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
    battle.events.emit(Event.ON_TURN_END)
    battle.print_logs()
    assert not mon.item.revealed

    mon.hp = 1  # テスト用に内部変数を直接変更
    battle.events.emit(Event.ON_TURN_END)
    assert mon.item.revealed
    assert mon.hp == 1 + mon.max_hp // 16


def test_タラプのみ_物理技では発動しない():
    """タラプのみ: 物理技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["D"] == 0


def test_タラプのみ_特殊技被弾でD上昇():
    """タラプのみ: 特殊技でダメージを受けたときとくぼう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", item_name="タラプのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["D"] == 1
    assert not foe.has_item()


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


def test_チーゴのみ_ターン終了でやけど回復():
    """チーゴのみ: ターン終了時にやけどを回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="チーゴのみ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("やけど", None),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name != "やけど"
    assert not mon.has_item()


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


def test_どくどくだま_ターン終了でもうどく():
    """どくどくだま: ターン終了時にもうどくを付与する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="どくどくだま")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name == "もうどく"


def test_ナナシのみ_ターン終了でこおり回復():
    """ナナシのみ: ターン終了時にこおりを回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ナナシのみ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("こおり", None),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name != "こおり"
    assert not mon.has_item()


def test_ねらいのまと_タイプ免疫を無効化():
    """ねらいのまと: タイプ相性による免疫（0倍）を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー", item_name="ねらいのまと")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp < foe.max_hp


def test_のどスプレー_非音技では発動しない():
    """のどスプレー: 音技以外では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.rank["C"] == 0
    assert mon.has_item()


def test_のどスプレー_音技使用後にC上昇():
    """のどスプレー: 音技使用後にとくこう+1"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.rank["C"] == 1
    assert not mon.has_item()


def test_ノーマルジュエル_ノーマル技威力1_5倍():
    """ノーマルジュエル: ノーマル技の威力を1.5倍にする（消費）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ノーマルジュエル", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144
    assert not mon.has_item()


def test_パワフルハーブ_溜め技をスキップ():
    """パワフルハーブ: 溜め技の溜めターンをスキップして即発動"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="パワフルハーブ", move_names=["ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert not mon.has_item()
    assert foe.hp < foe.max_hp


def test_パンチグローブ_パンチ技の威力1_1倍():
    """パンチグローブ: パンチ技の威力を1.1倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パンチグローブ", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4506


def test_パンチグローブ_パンチ技の接触判定を無効化():
    """パンチグローブ: パンチ技の接触判定を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パンチグローブ", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ひかりごけ_みず以外では発動しない():
    """ひかりごけ: みず以外の技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="ひかりごけ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["D"] == 0
    assert foe.has_item()


def test_ひかりごけ_みず被弾でD上昇():
    """ひかりごけ: みず技でダメージを受けたときとくぼう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみのり"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["D"] == 1
    assert not foe.has_item()


def test_ひかりのねんど_スクリーン8ターンに延長():
    """ひかりのねんど: リフレクターを8ターンに延長する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ひかりのねんど")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    result = battle.events.emit(
        Event.ON_MODIFY_DURATION,
        EventContext(source=mon),
        ["リフレクター", 5],
    )
    assert result == ["リフレクター", 8]


def test_ビビリだま_いかくでS上昇():
    """ビビリだま: いかくによってこうげきが下がったときすばやさ+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.rank["S"] == 1
    assert mon.rank["A"] == -1
    assert not mon.has_item()


def test_ピントレンズ_急所ランク加算():
    """ピントレンズ: 急所ランクを+1する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ピントレンズ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 急所が出ない程度に固定（0.5 < 急所ランク+1の閾値以下）
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 1


def test_ふうせん_じめん技を無効化():
    """ふうせん: 浮遊状態でじめん技が当たらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ゼニガメ", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp


def test_ふうせん_ダメージを受けると割れる():
    """ふうせん: ダメージを受けるとアイテムが消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert not mon.has_item()


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


def test_ぼうごパット_接触判定を無効化():
    """ぼうごパット: 攻撃技の接触判定を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ぼうじんゴーグル_天候ダメージを無効化():
    """ぼうじんゴーグル: すなあらしによるターン終了ダメージを無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうじんゴーグル")],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    initial_hp = mon.max_hp
    t.end_turn(battle)
    assert mon.hp == initial_hp


def test_ぼうじんゴーグル_粉技を無効化():
    """ぼうじんゴーグル: 粉技（ねむりごな等）を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ねむりごな"])],
        team1=[Pokemon("ピカチュウ", item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name != "ねむり"


def test_ミストシード_ミストフィールドでとくぼう上昇():
    """ミストシード: ミストフィールド展開時にとくぼう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミストシード")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.rank["D"] == 1
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


def test_メンタルハーブ_いちゃもんを即解除():
    """メンタルハーブ: いちゃもん付与時に即解除する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メンタルハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", source=battle.actives[1])
    assert not mon.has_volatile("いちゃもん")
    assert not mon.has_item()


def test_メンタルハーブ_対象外の揮発状態には反応しない():
    """メンタルハーブ: 対象外の揮発状態（こんらん等）では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メンタルハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こんらん", source=battle.actives[1])
    assert mon.has_volatile("こんらん")
    assert mon.has_item()


def test_ものしりメガネ_物理技には補正なし():
    """ものしりメガネ: 物理技には補正しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものしりメガネ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ものしりメガネ_特殊技1_1倍():
    """ものしりメガネ: 特殊技の威力を1.1倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものしりメガネ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4505


def test_ものまねハーブ_相手のランク上昇をコピー():
    """ものまねハーブ: 相手のランク上昇をそのままコピーする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.modify_stats(foe, {"A": +2})
    assert mon.rank["A"] == 2
    assert not mon.has_item()


def test_モモンのみ_ターン終了でどく回復():
    """モモンのみ: ターン終了時にどく・もうどくを回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="モモンのみ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("もうどく", None),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name not in ("どく", "もうどく")
    assert not mon.has_item()


def test_ゆきだま_こおり以外では発動しない():
    """ゆきだま: こおり以外の技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="ゆきだま")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["B"] == 0
    assert foe.has_item()


def test_ゆきだま_こおり被弾でB上昇():
    """ゆきだま: こおり技でダメージを受けたときぼうぎょ+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン", item_name="ゆきだま")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.rank["B"] == 1
    assert not foe.has_item()


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


def test_ルームサービス_トリックルームでS低下():
    """ルームサービス: トリックルーム発動時にすばやさ-1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ルームサービス")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックルーム"])],
    )
    t.run_move(battle, 1)
    mon = battle.actives[0]
    assert mon.rank["S"] == -1
    assert not mon.has_item()


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


def test_レンブのみ_物理技では発動しない():
    """レンブのみ: 物理技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="レンブのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


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


@pytest.mark.parametrize("item_name, mon_name, move_name, expected_modifier", [
    ("いしずえのめん", "オーガポン(いしずえ)", "たいあたり", 4915),
    ("いどのめん", "オーガポン(いど)", "たいあたり", 4915),
    ("かまどのめん", "オーガポン(かまど)", "たいあたり", 4915),
    ("でんきだま", "ピカチュウ", "たいあたり", 8192),
    ("でんきだま", "ピカチュウ", "でんきショック", 8192),
])
def test_専用アイテム攻撃補正(item_name, mon_name, move_name, expected_modifier):
    """オーガポンのめん・でんきだま: 攻撃補正（atk_modifier）を上昇させる"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == expected_modifier


@pytest.mark.parametrize(
    "item_name, mon_name, move_name, expected_modifier",
    [
        ("こころのしずく", "ラティオス", "サイコキネシス", 4915),
        ("こころのしずく", "ラティアス", "ドラゴンクロー", 4915),
        ("こんごうだま", "ディアルガ", "ドラゴンクロー", 4915),
        ("こんごうだま", "ディアルガ", "アイアンヘッド", 4915),
        ("しらたま", "パルキア", "ドラゴンクロー", 4915),
        ("しらたま", "パルキア", "なみのり", 4915),
        ("だいこんごうだま", "ディアルガ", "ドラゴンクロー", 4915),
        ("だいしらたま", "パルキア", "ドラゴンクロー", 4915),
        ("だいはっきんだま", "ギラティナ(アナザー)", "シャドーボール", 4915),
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
