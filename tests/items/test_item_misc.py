"""アイテムハンドラの単体テスト"""
import pytest
from jpoke import Pokemon
from .. import test_utils as t


@pytest.mark.parametrize("item_name, stat, amount",
                         [
                             ("チイラのみ", "atk", 1),
                             ("カムラのみ", "spe", 1),
                             ("ヤタピのみ", "spa", 1),
                             ("リュガのみ", "def", 1),
                             ("ズアのみ", "spd", 1),
                         ]
                         )
def test_HP25以下でランク上昇するきのみ(item_name, stat, amount):
    """HP1/4以下になった瞬間に能力ランクを上昇させる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.boosts[stat] == amount
    assert not mon.has_item()


@pytest.mark.parametrize("item_name, stat, amount",
                         [
                             ("チイラのみ", "atk", 1),
                             ("カムラのみ", "spe", 1),
                             ("ヤタピのみ", "spa", 1),
                             ("リュガのみ", "def", 1),
                             ("ズアのみ", "spd", 1),
                         ]
                         )
def test_HP25以下でランク上昇するきのみ_こんらんの自傷では発動しない(item_name, stat, amount):
    """こんらんの自傷ダメージ(reason=self_attack)でHPが1/4以下になっても発動しない
    （第五世代以降の仕様）。その後、自傷以外のダメージを受けると発動する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")
    assert mon.hp == mon.max_hp // 4
    assert mon.has_item(), "こんらんの自傷ダメージでアイテムが消費された"

    battle.modify_hp(mon, v=-1)
    assert mon.boosts[stat] == amount
    assert not mon.has_item()


@pytest.mark.parametrize("item_name, stat, amount",
                         [
                             ("チイラのみ", "atk", 1),
                             ("カムラのみ", "spe", 1),
                             ("ヤタピのみ", "spa", 1),
                             ("リュガのみ", "def", 1),
                             ("ズアのみ", "spd", 1),
                         ]
                         )
def test_HP25以下でランク上昇するきのみ_瀕死になったときは発動しない(item_name, stat, amount):
    """ダメージでHPが0(ひんし)になったときはランク上昇せず、アイテムも消費されない
    （ref: docs/spec/items/_ランク上昇ピンチきのみ.md「所持者がひんしになったときは発動しない」）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == 0
    assert mon.fainted
    assert mon.boosts[stat] == 0
    assert mon.has_item()


@pytest.mark.parametrize(
    "item_name",
    ["ウイのみ", "イアのみ", "フィラのみ", "マゴのみ", "バンジのみ"]
)
def test_HP4分の1より多いときは発動しない(item_name):
    """HP1/4以下になった瞬間に最大HPの1/3を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 2
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + 1
    assert mon.has_item()


@pytest.mark.parametrize(
    "item_name",
    ["ウイのみ", "イアのみ", "フィラのみ", "マゴのみ", "バンジのみ"]
)
def test_HP4分の1以下で回復するきのみ(item_name):
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


@pytest.mark.parametrize(
    "item_name",
    ["ウイのみ", "イアのみ", "フィラのみ", "マゴのみ", "バンジのみ"]
)
def test_HP4分の1以下で回復するきのみ_瀕死になったときは発動しない(item_name):
    """ダメージでHPが0(ひんし)になったときは回復せず、こんらんも付与されず、
    アイテムも消費されない
    （ref: docs/spec/items/_HP回復ピンチきのみ.md）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == 0
    assert mon.fainted
    assert mon.has_item()


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
    ("でんきだま", "ピカチュウ(キョダイ)", "たいあたり", 8192),
    ("いしずえのめん", "オーガポン(いしずえ)", "エナジーボール", 4915),
    ("いどのめん", "オーガポン(いど)", "エナジーボール", 4915),
    ("かまどのめん", "オーガポン(かまど)", "エナジーボール", 4915),
])
def test_専用アイテム攻撃補正(item_name, mon_name, move_name, expected_modifier):
    """オーガポンのめん・でんきだま: 攻撃補正（atk_modifier）を上昇させる
    （オーガポンのめんは物理・特殊問わず攻撃技の威力を1.2倍にする）"""
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
    """専用アイテム: 対応ポケモンの対応タイプ技を1.2倍にする"""
    battle = t.start_battle(
        team0=[Pokemon(mon_name, item_name=item_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


@pytest.mark.parametrize("item_name, expected_ailment", [
    ("かえんだま", "やけど"),
    ("どくどくだま", "もうどく"),
])
def test_状態異常だま_ターン終了で状態異常付与(item_name, expected_ailment):
    """かえんだま・どくどくだま: ターン終了時に状態異常を付与する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name == expected_ailment


@pytest.mark.parametrize("item_name, ailment_name, ailment_count", [
    ("カゴのみ", "ねむり", 3),
    ("クラボのみ", "まひ", None),
    ("チーゴのみ", "やけど", None),
    ("ナナシのみ", "こおり", None),
    ("モモンのみ", "もうどく", None),
])
def test_状態異常回復きのみ_ターン終了で回復(item_name, ailment_name, ailment_count):
    """状態異常回復きのみ: ターン終了時に対応する状態異常を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(ailment_name, ailment_count),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.ailment.name != ailment_name
    assert not mon.has_item()


@pytest.mark.parametrize("item_name, wrong_ailment, wrong_count", [
    ("カゴのみ", "まひ", None),
    ("クラボのみ", "ねむり", 3),
    ("チーゴのみ", "まひ", None),
    ("ナナシのみ", "まひ", None),
    ("モモンのみ", "まひ", None),
])
def test_状態異常回復きのみ_対象外状態では発動しない(item_name, wrong_ailment, wrong_count):
    """状態異常回復きのみ: 対応しない状態異常では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(wrong_ailment, wrong_count),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.has_item()


@pytest.mark.parametrize("item_name, move_name", [
    ("アッキのみ", "でんきショック"),
    ("レンブのみ", "たいあたり"),
])
def test_被弾反応きのみ_対応外の技ではアイテム消費しない(item_name, move_name):
    """アッキのみは特殊技で、レンブのみは物理技で発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ゼニガメ", item_name=item_name)],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.has_item()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
