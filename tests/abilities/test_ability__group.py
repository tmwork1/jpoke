"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import PLATE_TO_TYPE
from jpoke.enums import Interrupt, LogCode
from jpoke.types import Stat, AilmentName, VolatileName, \
    WeatherName, TerrainName

from .. import test_utils as t

ability_weather_defaultcount = [
    ("あめふらし", "あめ", 5),
    ("ひでり", "はれ", 5),
    ("すなおこし", "すなあらし", 5),
    ("ゆきふらし", "ゆき", 5),
    ("おわりのだいち", "おおひでり", 1),
    ("はじまりのうみ", "おおあめ", 1),
    ("デルタストリーム", "らんきりゅう", 1),
]
abilities = [x[0] for x in ability_weather_defaultcount]
weathers = [x[1] for x in ability_weather_defaultcount]
normal_weathers = weathers[:4]
strong_weathers = weathers[4:]

ability_terrain_pairs = [
    ("エレキメイカー", "エレキフィールド"),
    ("グラスメイカー", "グラスフィールド"),
    ("サイコメイカー", "サイコフィールド"),
    ("ミストメイカー", "ミストフィールド"),
]

SKIN_CASES = [
    ("スカイスキン", "ひこう"),
    ("ドラゴンスキン", "ドラゴン"),
    ("フェアリースキン", "フェアリー"),
    ("フリーズスキン", "こおり"),
]

CONTACT_AILMENT_CASES = [
    ("せいでんき", "まひ"),
    ("どくのトゲ", "どく"),
    ("ほのおのからだ", "やけど"),
]

MULTI_TYPE_PLATE_CASES = [
    (plate_item_name, expected_type)
    for plate_item_name, expected_type in PLATE_TO_TYPE.items()
    if plate_item_name in ITEMS
]


@pytest.mark.parametrize(
    "initial_weather", strong_weathers
)
def test_あめふらし_強天候は上書き不可(initial_weather: WeatherName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="あめふらし")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == initial_weather


@pytest.mark.parametrize(
    "initial_weather", ["はれ", "すなあらし", "ゆき"]
)
def test_あめふらし_通常天候を上書きする(initial_weather: WeatherName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="あめふらし")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "あめ"


def test_おわりのだいち_らんきりゅうは上書きできない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="おわりのだいち")],
        team1=[Pokemon("ピカチュウ")],
        weather=("らんきりゅう", 1),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "らんきりゅう"


@pytest.mark.parametrize(
    "weather_name",
    normal_weathers + ["おおあめ"]
)
def test_おわりのだいち_らんきりゅう以外上書きする(weather_name: WeatherName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="おわりのだいち")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "おおひでり"


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("フェアリーオーラ", "ムーンフォース"),
        ("ダークオーラ", "あくのはどう"),
    ]
)
def test_オーラ系_相手の技の威力が1_33倍になる(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert 5448 == battle.damage_calculator.power_modifier


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("フェアリーオーラ", "ムーンフォース"),
        ("ダークオーラ", "あくのはどう"),
    ]
)
def test_オーラ系_自分の技の威力が1_33倍になる(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5448 == battle.damage_calculator.power_modifier


def test_クォークチャージ_しろいハーブより先に発動判定する():
    """クォークチャージ: 設置技/入場効果より後、しろいハーブより先に発動判定がある
    (docs/spec/turn.md ON_SWITCH_IN: 140 クォークチャージ、160 しろいハーブ)。
    バトンタッチで引き継いだ下降ランクを参照して能力を選ぶため、
    しろいハーブがランクを戻す前に『とくこう』が選ばれる。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["バトンタッチ"]),
            Pokemon("ワカシャモ", ability_name="クォークチャージ", item_name="しろいハーブ"),
        ],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
    )
    attacker = battle.actives[0]
    attacker.boosts["atk"] = -2
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    mon = battle.actives[0]
    assert mon.paradox_boost_stat == "spa"
    assert mon.boosts["atk"] == 0


@pytest.mark.parametrize(
    "name, stat",
    [
        ("スピアー", "atk"),
        ("ゼニガメ", "def"),
        ("フシギダネ", "spa"),
        ("カメックス", "spd"),
        ("ピカチュウ", "spe"),
    ]
)
def test_クォークチャージ_最大ステータスがバフされる(name: str, stat: Stat):
    battle = t.start_battle(
        team0=[Pokemon(name, ability_name="クォークチャージ", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat == stat


def test_こだいかっせい_しろいハーブより先に発動判定する():
    """こだいかっせい: 設置技/入場効果より後、しろいハーブより先に発動判定がある
    (docs/spec/turn.md ON_SWITCH_IN: 140 こだいかっせい、160 しろいハーブ)。
    バトンタッチで引き継いだ下降ランクを参照して能力を選ぶため、
    しろいハーブがランクを戻す前に『とくこう』が選ばれる。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["バトンタッチ"]),
            Pokemon("ワカシャモ", ability_name="こだいかっせい", item_name="しろいハーブ"),
        ],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    attacker.boosts["atk"] = -2
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    mon = battle.actives[0]
    assert mon.paradox_boost_stat == "spa"
    assert mon.boosts["atk"] == 0


def test_こだいかっせい_にほんばれ自然消滅でブーストエナジーへ切り替わる():
    """こだいかっせい: にほんばれ状態が持続ターン切れで自然消滅した場合も、
    交代等で明示的に解除したときと同様に一旦効果が消え、未消費のブーストエナジーが
    あれば即座に消費して再発動する
    （docs/spec/abilities/こだいかっせい.md「にほんばれ状態が消滅すると一旦特性の
    効果が消えるが、即座にブーストエナジーを消費して特性を再発動させる」）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こだいかっせい")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 1),
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_source == "field"

    t.change_item(battle, mon, "ブーストエナジー")
    t.end_turn(battle)

    assert battle.weather.name == ""
    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item("ブーストエナジー")


def test_じりょく_ゴーストタイプを併せ持つはがねタイプの相手は交代できる():
    """じりょく: ハロウィンでゴーストタイプが追加されたはがねタイプの相手は交代できる"""
    battle = t.start_battle(
        team0=[Pokemon("コイル"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="じりょく")],
        volatile0={"ハロウィン": 0},
    )
    assert "はがね" in battle.actives[0].types
    assert "ゴースト" in battle.actives[0].types
    assert t.can_switch(battle, 0) is True


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
@pytest.mark.parametrize(
    "move_name",
    ["ウェザーボール", "さばきのつぶて", "だいちのはどう"],
)
def test_スキン系_タイプが変わる技は結果がノーマルタイプでも対象外になる(
    move_name: str,
    ability_name: str,
    expected_type: str,
):
    """ウェザーボール等のタイプが変わる技は、実際のタイプがノーマルのままでもスキン系特性の対象にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン系_テラスタル後もノーマル技は対応タイプに変換される(
    ability_name: str,
    expected_type: str,
):
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ", ability_name=ability_name, tera_type="みず",
            move_names=["たいあたり"],
        )],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[0].terastallize()
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == expected_type
    assert battle.damage_calculator.power_modifier == 4915


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン系_テラバーストはテラスタルしていなければ対象になる(
    ability_name: str,
    expected_type: str,
):
    """テラバーストはテラスタルしていない間は通常のノーマル技として扱われ、スキン系特性が発動する。"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ", ability_name=ability_name, tera_type="みず",
            move_names=["テラバースト"],
        )],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == expected_type
    assert battle.damage_calculator.power_modifier == 4915


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン系_ノーマル技を対応タイプに変換する(
    ability_name: str,
    expected_type: str,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == expected_type


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン系_めざめるダンスはタイプが変わる技として対象外になる(
    ability_name: str,
    expected_type: str,
):
    """めざめるダンスは使用者がノーマルタイプのときタイプがノーマルのままでもスキン系特性の対象にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name=ability_name, move_names=["めざめるダンス"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize(
    "ability_name, expected_type, move_name",
    [
        ("スカイスキン", "ひこう", "つばさでうつ"),
        ("ドラゴンスキン", "ドラゴン", "りゅうのいぶき"),
        ("フェアリースキン", "フェアリー", "ムーンフォース"),
        ("フリーズスキン", "こおり", "れいとうビーム"),
    ],
)
def test_スキン系_もともと対応タイプの技は威力補正を受けない(
    ability_name: str,
    expected_type: str,
    move_name: str,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == expected_type
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン系_変換した技の威力が4915倍になる(
    ability_name: str,
    expected_type: str,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン系_対象外タイプの技はタイプも威力も変化しない(
    ability_name: str,
    expected_type: str,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "でんき"
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("あついしぼう", "ひのこ"),
        ("あついしぼう", "れいとうビーム"),
        ("たいねつ", "ひのこ"),
    ],
)
def test_タイプ半減系(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("あついしぼう", "ひのこ"),
        ("たいねつ", "ひのこ"),
    ],
)
def test_タイプ半減系_かたやぶりで無効(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability_name, move_name, expected",
    [
        ("いわはこび", "いわなだれ", 6144),
        ("はがねつかい", "アイアンヘッド", 6144),
        ("ほのおのたてがみ", "ひのこ", 6144),
        ("りゅうのあぎと", "りゅうのはどう", 6144),
        ("トランジスタ", "でんきショック", 5325),
    ],
)
def test_タイプ強化系(ability_name: str, move_name: str, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert expected == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability, move, stat, rank",
    [
        ("こんがりボディ", "ひのこ", "def", 2),
        ("そうしょく", "このは", "atk", 1),
        ("でんきエンジン", "でんきショック", "spe", 1),
        ("ひらいしん", "でんきショック", "spa", 1),
        ("よびみず", "みずでっぽう", "spa", 1),
    ],
)
def test_タイプ無効バフ系(ability: str, move: str, stat: Stat, rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move])],
        team1=[Pokemon("ピカチュウ", ability_name=ability)],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.hp == defender.max_hp
    assert defender.boosts[stat] == rank


@pytest.mark.parametrize(
    "ability, move, stat, rank",
    [
        ("こんがりボディ", "ひのこ", "def", 2),
        ("そうしょく", "このは", "atk", 1),
        ("でんきエンジン", "でんきショック", "spe", 1),
        ("ひらいしん", "でんきショック", "spa", 1),
        ("よびみず", "みずでっぽう", "spa", 1),
    ],
)
def test_タイプ無効バフ系_かたやぶりで無効(ability: str, move: str, stat: Stat, rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
        team1=[Pokemon("ピカチュウ", ability_name=ability)],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.boosts[stat] == 0


@pytest.mark.parametrize(
    "ability, move",
    [
        ("ちくでん", "スパーク"),
        ("ちょすい", "なみのり"),
        ("どしょく", "じしん"),
    ],
)
def test_タイプ無効回復(ability, move):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", move_names=[move])],
    )
    defender, attacker = battle.actives
    defender.hp = 1
    t.run_move(battle, 1)
    assert defender.hp == 1 + defender.max_hp // 4
    assert defender.ability.revealed


@pytest.mark.parametrize(
    "ability, move",
    [
        ("ちくでん", "スパーク"),
        ("ちょすい", "なみのり"),
        ("どしょく", "じしん"),
    ],
)
def test_タイプ無効回復_かたやぶりで無効(ability, move):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp
    assert not defender.ability.revealed


def test_どんかん_かたやぶりでちょうはつ付与後は直後に回復する():
    """どんかん: かたやぶりの効果でちょうはつ状態にされても、技終了直後に特性の効果で回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どんかん")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ちょうはつ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert not battle.actives[0].has_volatile("ちょうはつ")


def test_どんかん_かたやぶりでメロメロ付与後は直後に回復する():
    """どんかん: かたやぶりの効果でメロメロ状態にされても、技終了直後に特性の効果で回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どんかん", gender="male")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["メロメロ"], gender="female")],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert not battle.actives[0].has_volatile("メロメロ")


def test_はじまりのうみ_らんきりゅうは上書きできない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="はじまりのうみ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("らんきりゅう", 1),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "らんきりゅう"


@pytest.mark.parametrize(
    "weather_name",
    normal_weathers + ["おおひでり"]
)
def test_はじまりのうみ_らんきりゅう以外上書きする(weather_name: WeatherName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="はじまりのうみ")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "おおあめ"


def test_はじまりのうみ_瀕死交代でも強制天候を解除する():
    """瀕死になったはじまりのうみ持ちが交代する際も、通常の交代と同様におおあめを
    解除する（Handler.allow_fainted_subjectの回帰テスト。fuzz_log seed=1183参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はじまりのうみ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.weather.name == "おおあめ"
    battle.modify_hp(mon, -mon.hp)
    assert mon.fainted
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == ""


@pytest.mark.parametrize("ability_name", ["クォークチャージ", "こだいかっせい"])
def test_パラドックス特性_イカサマを受けるときは対象の攻撃補正は乗らない(ability_name: str):
    """クォークチャージ/こだいかっせい: 対象（相手）自身の攻撃能力上昇は、
    イカサマを受けたときのダメージに影響しない。"""
    battle = t.start_battle(
        team0=[Pokemon("スピアー", ability_name=ability_name, item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ", move_names=["イカサマ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.damage_calculator.atk_modifier == 4096


@pytest.mark.parametrize("ability_name", ["クォークチャージ", "こだいかっせい"])
def test_パラドックス特性_イカサマ使用時は使用者自身の攻撃補正が乗る(ability_name: str):
    """クォークチャージ/こだいかっせい: イカサマは相手の実数値を攻撃として使うが、
    パラドックス補正は通常の物理技と同様に使用者自身の攻撃強化状態にのみ依存する。"""
    battle = t.start_battle(
        team0=[Pokemon(
            "スピアー", ability_name=ability_name, item_name="ブーストエナジー",
            move_names=["イカサマ"],
        )],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 5325


@pytest.mark.parametrize("ability_name", ["クォークチャージ", "こだいかっせい"])
def test_パラドックス特性_こんらんの自傷ダメージには影響しない(ability_name: str):
    """クォークチャージ/こだいかっせい: 特性で攻撃/防御が上がってもこんらんの
    自傷ダメージ（内部技"_こんらん"）には影響しない。"""
    battle = t.start_battle(
        team0=[Pokemon("スピアー", ability_name=ability_name, item_name="ブーストエナジー")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat == "atk"

    battle.test_option.trigger_volatile = True
    battle.volatile_manager.apply(mon, "こんらん", count=5)
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


@pytest.mark.parametrize("ability_name", ["クォークチャージ", "こだいかっせい"])
def test_パラドックス特性_スキルスワップは失敗する(ability_name: str):
    """クォークチャージ/こだいかっせい: 使用者か対象のどちらかがこの特性であるとき、
    スキルスワップは失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["スキルスワップ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.actives[0].ability.name == ability_name
    assert battle.actives[1].ability.name == ""


def test_パラドックス特性_ブーストエナジーのみ_アイテムが発動源():
    # 場の条件なし → アイテムが発動源、アイテムは消費される
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クォークチャージ", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_source == "item"
    assert mon.paradox_boost_active
    assert not mon.has_item("ブーストエナジー")


@pytest.mark.parametrize("ability_name", ["クォークチャージ", "こだいかっせい"])
def test_パラドックス特性_ボディプレス使用時に強化対象がぼうぎょでも補正は乗らない(ability_name: str):
    """クォークチャージ/こだいかっせい: 強化対象が『ぼうぎょ』（ボディプレスが参照する実数値）でも、
    技の分類（物理）に対応する『こうげき』スロットではないため補正は乗らない。"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ゼニガメ", ability_name=ability_name, item_name="ブーストエナジー",
            move_names=["ボディプレス"],
        )],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat == "def"
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


@pytest.mark.parametrize("ability_name", ["クォークチャージ", "こだいかっせい"])
def test_パラドックス特性_ボディプレス使用時は使用者自身のこうげき強化で補正が乗る(ability_name: str):
    """クォークチャージ/こだいかっせい: ボディプレスは自分の『ぼうぎょ』実数値を攻撃として使うが、
    パラドックス補正は技の分類（物理）に対応する『こうげき』スロットが強化対象かどうかで判定される。"""
    battle = t.start_battle(
        team0=[Pokemon(
            "スピアー", ability_name=ability_name, item_name="ブーストエナジー",
            move_names=["ボディプレス"],
        )],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat == "atk"
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 5325


@pytest.mark.parametrize("ability_name", ["クォークチャージ", "こだいかっせい"])
def test_パラドックス特性_ワンダールーム下では防御と特防の実数値を入れ替えて比較する(ability_name: str):
    """フシギダネは特攻・特防が同値で最も高い（通常なら特攻が選ばれる）。

    ワンダールーム下では防御・特防の実数値（ランク補正は含まない）が入れ替わるため、
    防御の実数値が特攻と同値になり、優先順（防御→特攻）により防御が選ばれる
    （docs/spec/abilities/こだいかっせい.md「パワーシェア/ガードシェア/パワートリック/
    スピードスワップ/ワンダールームによる実数値変動も考慮する」を参照）。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ"),
            Pokemon("フシギダネ", ability_name=ability_name, item_name="ブーストエナジー"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    battle.activate_global_field("ワンダールーム", 99)
    t.run_switch(battle, 0, 1)

    mon = battle.actives[0]
    assert mon.paradox_boost_stat == "def"


@pytest.mark.parametrize("ability_name", ["クォークチャージ", "こだいかっせい"])
def test_パラドックス特性_ワンダールーム発生で補正対象の防御特防が入れ替わる(ability_name: str):
    """ソーナンスは防御・特防が同値で最も高く（かつ他の能力より圧倒的に高いため
    ワンダールームによる実数値入れ替えの影響を受けず）、通常はぼうぎょが強化対象になる。

    ワンダールーム下では防御側の実数値参照自体が入れ替わる
    （handlers/field.py の ワンダールーム_def_modifier）ため、ぼうぎょが強化対象でも
    物理技の防御計算には補正が乗らず、特殊技の防御計算に補正が乗るようになる
    （docs/spec/abilities/こだいかっせい.md「防御か特防が上昇しているときに
    ワンダールーム状態が発生した場合や、解除された場合では、その度に補正が
    掛かっている能力も入れ替わる」を参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか", "みずのはどう"])],
        team1=[Pokemon("ソーナンス", ability_name=ability_name, item_name="ブーストエナジー")],
        accuracy=100,
    )
    mon = battle.actives[1]
    assert mon.paradox_boost_stat == "def"

    battle.activate_global_field("ワンダールーム", 99)

    t.run_move(battle, 0, 0)  # でんこうせっか（物理）
    assert battle.damage_calculator.def_modifier == 4096

    t.run_move(battle, 0, 1)  # みずのはどう（特殊）
    assert battle.damage_calculator.def_modifier == 5325


def test_パラドックス特性_地形優先_場消滅後アイテム発動():
    # エレキフィールドが発動源 → アイテムは温存、地形消滅後にアイテムが発動源に切り替わる
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クォークチャージ", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ", ability_name="エレキメイカー")],
        terrain=("エレキフィールド", 5),
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_source == "field"
    assert mon.paradox_boost_active
    assert mon.has_item("ブーストエナジー")

    battle.terrain_manager.remove()
    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item("ブーストエナジー")


def test_パラドックス特性_天候優先_場消滅後アイテム発動():
    # はれが発動源 → アイテムは温存、天候消滅後にアイテムが発動源に切り替わる
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こだいかっせい", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ", ability_name="ひでり")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_source == "field"
    assert mon.paradox_boost_active
    assert mon.has_item("ブーストエナジー")

    battle.weather_manager.remove()
    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item("ブーストエナジー")


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("しんりょく", "エナジーボール"),
        ("もうか", "ひのこ"),
        ("げきりゅう", "なみのり"),
        ("むしのしらせ", "むしのていこう"),
    ],
)
def test_ピンチ系特性_HP1_3以下で攻撃補正1_5倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability_name, volatile_name, move_name",
    [
        ("ふかしのこぶし", "まもる", "たいあたり"),
        ("ふかしのこぶし", "トーチカ", "たいあたり"),
        ("ふかしのこぶし", "キングシールド", "たいあたり"),
        ("ふかしのこぶし", "スレッドトラップ", "たいあたり"),
        ("ふかしのこぶし", "かえんのまもり", "たいあたり"),
        ("ふかしのこぶし", "ニードルガード", "たいあたり"),
        ("ふかしのこぶし", "ファストガード", "マッハパンチ"),
        ("かんつうドリル", "まもる", "たいあたり"),
    ]
)
def test_ふかしのこぶし_接触技でまもるを貫通(
    ability_name: str, volatile_name: VolatileName, move_name: str
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={volatile_name: 1},
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert battle.damage_calculator.protect_modifier == 1024


@pytest.mark.parametrize(
    "ability_name",
    ["ふかしのこぶし", "かんつうドリル"],
)
def test_ふかしのこぶし_非接触技はまもるを貫通しない(ability_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"まもる": 1},
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_ふみん_かたやぶりでねむり付与後は直後に回復する():
    """ふみん: かたやぶりの効果でねむり状態にされても、技終了直後に特性の効果で回復する"""
    # カビゴン（ノーマル）はねむりのタイプ耐性を持たないため使用
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ふみん")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ねむりごな"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert not battle.actives[0].ailment.is_active


def test_マイペース_かたやぶりでこんらん付与後は直後に回復する():
    """マイペース: かたやぶりの効果でこんらん状態にされても、技終了直後に特性の効果で回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マイペース")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["あやしいひかり"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert not battle.actives[0].has_volatile("こんらん")


def test_ゆきがくれ_一撃必殺技には命中率変化なし():
    """一撃必殺技の命中率は独自計算のため、ゆきがくれの命中率補正は適用されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じわれ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ゆきがくれ")],
        weather=("ゆき", 5),
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


@pytest.mark.parametrize(
    "weather_name",
    weathers
)
def test_らんきりゅう_すべての天候を上書きする(weather_name: WeatherName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="デルタストリーム")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "らんきりゅう"


@pytest.mark.parametrize(
    "ability_name, stat",
    [
        ("ふとうのけん", "atk"),
        ("ふくつのたて", "def"),
    ],
)
def test_一度きりの能力上昇特性(ability_name: str, stat: Stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name), Pokemon("イーブイ")],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.actives[0].boosts[stat] == 1
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert battle.actives[0].boosts[stat] == 0


@pytest.mark.parametrize(
    "ability_name, attacker_name, attacker_ability, expected_can_switch",
    [
        ("ありじごく", "ピカチュウ", "", False),
        ("ありじごく", "ピジョン", "", True),
        ("ありじごく", "ゲンガー", "", True),
        ("かげふみ", "ピカチュウ", "", False),
        ("かげふみ", "ピカチュウ", "かげふみ", True),
        ("かげふみ", "ゲンガー", "", True),
        ("じりょく", "コイル", "", False),
        ("じりょく", "ピカチュウ", "", True),
    ],
)
def test_交代抑制特性_param(ability_name: str, attacker_name: str, attacker_ability: str, expected_can_switch: bool):
    team0 = [Pokemon(attacker_name, ability_name=attacker_ability), Pokemon("ピカチュウ")]
    battle = t.start_battle(
        team0=team0,
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    assert t.can_switch(battle, 0) is expected_can_switch


@pytest.mark.parametrize(
    "ability_name, expected_modifier",
    [
        ("ライトメタル", 0.5),
        ("ヘヴィメタル", 2.0),
    ],
)
def test_体重操作系(ability_name: str, expected_modifier: float):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.weight == int(10 * mon.data.weight * expected_modifier) / 10


@pytest.mark.parametrize(
    "ability_name, stat",
    [
        ("じしんかじょう", "atk"),
        ("しろのいななき", "atk"),
        ("くろのいななき", "spa"),
    ],
)
def test_倒すと能力上昇系_ばけのかわのフォルムチェンジ消費ダメージで倒しても発動する(ability_name: str, stat: Stat):
    """技自体のダメージが0でも、ばけのかわのフォルムチェンジ消費ダメージ（最大HPの1/8）で
    相手を倒した場合は特性が発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("コイキング", ability_name="ばけのかわ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.boosts[stat] == 1


@pytest.mark.parametrize(
    "ability_name, stat",
    [
        ("じしんかじょう", "atk"),
        ("しろのいななき", "atk"),
        ("くろのいななき", "spa"),
    ],
)
def test_倒すと能力上昇系_ランクがすでに最大のときは発動しない(ability_name: str, stat: Stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.boosts[stat] = 6
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.boosts[stat] == 6


@pytest.mark.parametrize(
    "ability_name, stat",
    [
        ("じしんかじょう", "atk"),
        ("しろのいななき", "atk"),
        ("くろのいななき", "spa"),
    ],
)
def test_倒すと能力上昇系_相手を倒すと指定ステータスが1段階上昇する(ability_name: str, stat: Stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.boosts[stat] == 1


@pytest.mark.parametrize(
    "ability_name, stat",
    [
        ("じしんかじょう", "atk"),
        ("しろのいななき", "atk"),
        ("くろのいななき", "spa"),
    ],
)
def test_倒すと能力上昇系_相手を倒せないと発動しない(ability_name: str, stat: Stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.fainted
    assert attacker.boosts[stat] == 0


@pytest.mark.parametrize(
    "ability_name",
    ["じょおうのいげん", "テイルアーマー", "ビビッドボディ"],
)
def test_先制技無効系_いたずらごころで優先度が上がった変化技も無効化する(ability_name):
    """じょおうのいげん: いたずらごころで優先度+1になった変化技も無効化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["でんじは"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


@pytest.mark.parametrize(
    "ability_name",
    ["じょおうのいげん", "テイルアーマー", "ビビッドボディ"],
)
def test_先制技無効系_かたやぶりで無効化される(ability_name):
    """テイルアーマー: かたやぶり持ちには先制技が通る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


@pytest.mark.parametrize(
    "ability_name",
    ["じょおうのいげん", "テイルアーマー", "ビビッドボディ"],
)
def test_先制技無効系_優先度ゼロの技は通る(ability_name):
    """テイルアーマー: 優先度0の技は通常通り当たる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
        accuracy=100,
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


@pytest.mark.parametrize(
    "ability_name",
    ["じょおうのいげん", "テイルアーマー", "ビビッドボディ"],
)
def test_先制技無効系_優先度プラスの技を無効化する(ability_name):
    """テイルアーマー: 優先度+1の技を無効化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


@pytest.mark.parametrize(
    "ability_name",
    ["じょおうのいげん", "テイルアーマー", "ビビッドボディ"],
)
def test_先制技無効系_自己対象の技は無効化されない(ability_name):
    """じょおうのいげん: まもるなど自分（味方側）を対象とした優先度+1以上の技は無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まもる"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True
    assert "まもる" in attacker.volatiles


@pytest.mark.parametrize(
    "ability_name, terrain_name",
    ability_terrain_pairs
)
def test_地形始動特性_同一地形が有効時は継続ターンを更新しない(ability_name: str, terrain_name: TerrainName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
        terrain=(terrain_name, 2)
    )
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 2
    assert not battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "ability_name, terrain_name",
    ability_terrain_pairs
)
def test_地形始動特性_登場時に対応地形を展開する(ability_name: str, terrain_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "ability_name, weather",
    [
        ("ゆきがくれ", "ゆき"),
        ("すながくれ", "すなあらし"),
    ],
)
def test_天候がくれ系_かたやぶりで命中率補正なし(ability_name: str, weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
        weather=(weather, 5),  # type: ignore[arg-type]
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


@pytest.mark.parametrize(
    "ability_name, weather",
    [
        ("ゆきがくれ", "ゆき"),
        ("すながくれ", "すなあらし"),
    ],
)
def test_天候がくれ系_対応天候で命中低下(ability_name: str, weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
        weather=(weather, 5),  # type: ignore[arg-type]
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 3277 // 4096


@pytest.mark.parametrize(
    "ability_name",
    ["ゆきがくれ", "すながくれ"],
)
def test_天候がくれ系_対応天候以外では命中率変化なし(ability_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


@pytest.mark.parametrize(
    "ability, weather, expected_mult",
    [
        ("すなかき", "すなあらし", 2),
        ("すいすい", "あめ", 2),
        ("ようりょくそ", "はれ", 2),
        ("ゆきかき", "ゆき", 2),
    ],
)
def test_天候依存素早さ上昇(ability: str, weather: WeatherName, expected_mult: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 999),
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] * expected_mult


@pytest.mark.parametrize(
    "ability, weather",
    [
        ("すなかき", "すなあらし"),
        ("すいすい", "あめ"),
        ("ようりょくそ", "はれ"),
        ("ゆきかき", "ゆき"),
    ],
)
@pytest.mark.parametrize("suppressor_ability", ["ノーてんき", "エアロック"])
def test_天候依存素早さ上昇_ノーてんきエアロックで無効化(
    ability: str, weather: WeatherName, suppressor_ability: str
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", ability_name=suppressor_ability)],
        weather=(weather, 999),
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


@pytest.mark.parametrize(
    "ability",
    ["すなかき", "すいすい", "ようりょくそ", "ゆきかき"],
)
def test_天候依存素早さ上昇_非対応天候は据え置き(ability: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


@pytest.mark.parametrize(
    "ability_name,weather_name,weather_count",
    [
        ("あめうけざら", "あめ", 5),
        ("あめうけざら", "おおあめ", 999),
        ("アイスボディ", "ゆき", 5),
    ]
)
def test_天候回復特性_対応天候中に回復(ability_name: str, weather_name: WeatherName, weather_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16


@pytest.mark.parametrize(
    "ability_name, weather_name, default_count",
    ability_weather_defaultcount
)
def test_天候始動特性_登場時に発動(ability_name: str, weather_name: WeatherName, default_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == weather_name
    assert battle.weather.count == default_count
    assert battle.actives[0].ability.revealed is True


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("おわりのだいち", "おおひでり"),
        ("デルタストリーム", "らんきりゅう"),
    ],
)
def test_強制天候特性_瀕死交代でも強制天候を解除する(ability_name: str, weather_name: WeatherName):
    """おわりのだいち・デルタストリームも、はじまりのうみと同様に瀕死交代で
    強制天候を解除する（Handler.allow_fainted_subjectの回帰テスト。fuzz_log seed=1183参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.weather.name == weather_name
    battle.modify_hp(mon, -mon.hp)
    assert mon.fainted
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == ""


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("おわりのだいち", "おおひでり"),
        ("はじまりのうみ", "おおあめ"),
        ("デルタストリーム", "らんきりゅう"),
    ],
)
def test_強天候始動特性_相手も同じ特性だと退場しても解除されない(ability_name: str, weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == weather_name


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("おわりのだいち", "おおひでり"),
        ("はじまりのうみ", "おおあめ"),
        ("デルタストリーム", "らんきりゅう"),
    ],
)
def test_強天候始動特性_複数ターン経過しても解除されない(ability_name: str, weather_name: str):
    """強天候（おおひでり/おおあめ/らんきりゅう）はON_TURN_ENDのカウントダウン対象外
    （src/jpoke/data/field/weather.pyの各エントリにEvent.ON_TURN_ENDハンドラは登録されていない）。
    発動ポケモンが場に残っている限り、複数ターン経過しても解除されないことを確認する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == weather_name
    assert battle.weather.count == 1
    for _ in range(3):
        t.end_turn(battle)
    assert battle.weather.name == weather_name
    assert battle.weather.count == 1


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("おわりのだいち", "おおひでり"),
        ("はじまりのうみ", "おおあめ"),
        ("デルタストリーム", "らんきりゅう"),
    ],
)
def test_強天候始動特性_退場時に解除される(ability_name: str, weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_switch(battle, 0, 1)
    assert not battle.weather.is_active


@pytest.mark.parametrize(
    "ability_name, move_name, expected_power",
    [
        ("かたいツメ", "たいあたり", 5325),
        ("かたいツメ", "でんきショック", 4096),
        ("がんじょうあご", "かみつく", 6144),
        ("きれあじ", "きりさく", 6144),
        ("てつのこぶし", "かみなりパンチ", 4915),
        ("パンクロック", "バークアウト", 5325),
        ("メガランチャー", "みずのはどう", 6144),
        ("メガランチャー", "たいあたり", 4096),
    ],
)
def test_技カテゴリによる威力補正_param(ability_name: str, move_name: str, expected_power: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert expected_power == battle.damage_calculator.power_modifier


@pytest.mark.parametrize(
    "ability_name, ailment_name",
    CONTACT_AILMENT_CASES
)
def test_接触時に状態異常付与_接触技で状態異常を付与する(ability_name: str, ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=["たいあたり"])],
    )
    attacker = battle.actives[1]
    battle.random.random = lambda: 0.0  # 確率操作
    t.run_move(battle, 1)
    assert attacker.has_ailment(ailment_name)


@pytest.mark.parametrize(
    "ability_name, ailment_name",
    CONTACT_AILMENT_CASES
)
def test_接触時に状態異常付与_相手が既に状態異常のときは発動ログが出ない(ability_name: str, ailment_name: AilmentName):
    """相手が既に状態異常（やけど）であるとき、状態異常の付与に失敗し
    発動ログ（ABILITY_TRIGGERED）自体が出ないことを確認する（fuzzログ回帰）。
    やけどは移動を妨げないため前提付与に使う。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=["たいあたり"])],
    )
    attacker = battle.actives[1]
    battle.ailment_manager.apply(attacker, "やけど")
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    triggered = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED
        and log.payload is not None
        and getattr(log.payload, "ability", None) == ability_name
    ]
    assert triggered == []


@pytest.mark.parametrize(
    "ability_name, ailment_name",
    CONTACT_AILMENT_CASES
)
def test_接触時に状態異常付与_非接触技では発動しない(ability_name: str, ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=["はどうだん"])],
    )
    attacker = battle.actives[1]
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    assert not attacker.has_ailment(ailment_name)


@pytest.mark.parametrize(
    "ability, volatile, result",
    [
        ("アロマベール", "アンコール", False),
        ("アロマベール", "いちゃもん", False),
        ("アロマベール", "かいふくふうじ", False),
        ("アロマベール", "かなしばり", False),
        ("アロマベール", "ちょうはつ", False),
        ("アロマベール", "メロメロ", False),
        ("スイートベール", "ねむけ", False),
        ("どんかん", "ちょうはつ", False),
        ("どんかん", "メロメロ", False),
        ("マイペース", "こんらん", False),
    ]
)
def test_揮発状態耐性(ability: str, volatile: VolatileName, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.volatile_manager.apply(battle.actives[0], volatile) == result


@pytest.mark.parametrize(
    "ability, ailment",
    [
        ("めんえき", "どく"),
        ("めんえき", "もうどく"),
        ("パステルベール", "どく"),
        ("パステルベール", "もうどく"),
        ("じゅうなん", "まひ"),
        ("ふみん", "ねむり"),
        ("やるき", "ねむり"),
        ("スイートベール", "ねむり"),
        ("みずのベール", "やけど"),
        ("マグマのよろい", "こおり"),
        ("すいほう", "やけど"),
        ("ねつこうかん", "やけど"),
    ],
)
def test_状態異常無効(ability: str, ailment: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, ailment)
    assert not mon.ailment.is_active


@pytest.mark.parametrize(
    "ability, ailment, move, still_active",
    [
        # めんえき/パステルベール/じゅうなん/やるき/みずのベールは、
        # かたやぶりの技で状態異常にされても技終了直後に特性の効果で回復する
        ("めんえき", "どく", "どくのこな", False),
        ("めんえき", "もうどく", "どくどく", False),
        ("パステルベール", "どく", "どくのこな", False),
        ("パステルベール", "もうどく", "どくどく", False),
        ("じゅうなん", "まひ", "でんじは", False),
        ("やるき", "ねむり", "ねむりごな", False),
        ("みずのベール", "やけど", "おにび", False),
        ("すいほう", "やけど", "おにび", False),
        ("ねつこうかん", "やけど", "おにび", False),
        # スイートベールは無視して状態異常にしても回復しない
        ("スイートベール", "ねむり", "ねむりごな", True),
        ("マグマのよろい", "こおり", "いてつくしせん", False),
    ],
)
def test_状態異常無効_かたやぶりで無効(ability: str, ailment: AilmentName, move: str, still_active: bool):
    # カビゴン（ノーマル）はまひ・ねむり・やけど・どく・こおり全てのタイプ耐性を持たないため使用
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 1)
    assert battle.actives[0].ailment.is_active == still_active


@pytest.mark.parametrize(
    "ability_name, stats, source_is_self, expected",
    [
        ("かいりきバサミ", {"atk": -1, "def": -1, "spa": -2}, False, {"def": -1, "spa": -2}),
        ("かいりきバサミ", {"atk": -1}, True, {"atk": -1}),
        ("はとむね", {"atk": -1, "def": -1, "spa": -2}, False, {"atk": -1, "spa": -2}),
        ("はとむね", {"def": -1}, True, {"def": -1}),
    ],
)
def test_能力低下防止特性_param(ability_name: str, stats: dict, source_is_self: bool, expected: dict):
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    target, foe = battle.actives
    source = target if source_is_self else foe
    result = battle.modify_stats(target, stats, source=source)
    assert result == expected


@pytest.mark.parametrize(
    "ability_name, stat, expected",
    [
        ("かちき", "spa", 2),
        ("まけんき", "atk", 1),
    ],
)
def test_能力反発系_相手による能力低下で発動(ability_name: str, stat: Stat, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].boosts[stat] == expected


@pytest.mark.parametrize(
    "ability_name, stat, expected",
    [
        ("かちき", "spa", 0),
        ("まけんき", "atk", 0),
    ],
)
def test_能力反発系_自己能力低下では発動しない(ability_name: str, stat: Stat, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["アームハンマー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.boosts["spe"] == -1
    assert mon.boosts[stat] == expected


@pytest.mark.parametrize(
    "defender_ability, attacker_ability, move_name, should_block",
    [
        ("ぼうおん", "", "バークアウト", True),
        ("ぼうおん", "かたやぶり", "バークアウト", False),
        ("ぼうだん", "", "かえんボール", True),
        ("ぼうだん", "かたやぶり", "かえんボール", False),
        ("ぼうだん", "", "みずあめボム", True),
        ("ぼうだん", "かたやぶり", "みずあめボム", False),
        ("ぼうだん", "", "じばく", False),
    ],
)
def test_音ラベル無効系_param(defender_ability: str, attacker_ability: str, move_name: str, should_block: bool):
    # attacker_ability may be empty string for no ability
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=attacker_ability, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=defender_ability)],
        accuracy=100,
    )
    # attacker is index 0 or 1 depending on order
    # attacker chosen is battle.actives[0] when team0 provided
    t.run_move(battle, 0)
    defender = battle.actives[1]
    if should_block:
        # damage should be unchanged (no hit)
        assert defender.hp == defender.max_hp
        assert defender.ability.revealed is True
    else:
        assert defender.hp < defender.max_hp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
