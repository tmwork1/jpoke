"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import PLATE_TO_TYPE
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
    assert defender.rank[stat] == rank


@pytest.mark.parametrize(
    "ability, move, stat, rank",
    [
        ("こんがりボディ", "ひのこ", "def", 2),
        ("そうしょく", "このは", "atk", 1),
        ("でんきエンジン", "でんきショック", "spe", 1),
        ("ひらいしん", "でんきショック", "spa", 1),
        ("よびみず", "でんきショック", "spa", 1),
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
    assert defender.rank[stat] == 0


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
    "ability_name, volatile_name",
    [
        ("ふかしのこぶし", "まもる"),
        ("ふかしのこぶし", "トーチカ"),
        ("ふかしのこぶし", "キングシールド"),
        ("ふかしのこぶし", "スレッドトラップ"),
        ("ふかしのこぶし", "かえんのまもり"),
        ("かんつうドリル", "まもる"),
    ]
)
def test_ふかしのこぶし_接触技でまもるを貫通(ability_name: str, volatile_name: VolatileName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={volatile_name: 1},
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert battle.damage_calculator.protect_modifier == 1024


def test_ふかしのこぶし_非接触技はまもるを貫通しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふかしのこぶし", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"まもる": 1},
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


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
    assert battle.actives[0].rank[stat] == 1
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert battle.actives[0].rank[stat] == 0


@pytest.mark.parametrize(
    "ability_name, attacker_name, attacker_ability, expected_can_switch",
    [
        ("ありじごく", "ピカチュウ", "", False),
        ("ありじごく", "ピジョン", "", True),
        ("ありじごく", "ゲンガー", "", True),
        ("かげふみ", "ピカチュウ", "", False),
        ("かげふみ", "ピカチュウ", "かげふみ", True),
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
    assert attacker.rank[stat] == 1


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
    assert attacker.rank[stat] == 1


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
    assert attacker.rank[stat] == 0


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
    ["じょおうのいげん", "テイルアーマー"],
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
    ["じょおうのいげん", "テイルアーマー"],
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
    "ability, ailment, move",
    [
        ("めんえき", "どく", "どくのこな"),
        ("めんえき", "もうどく", "どくどく"),
        ("パステルベール", "どく", "どくのこな"),
        ("パステルベール", "もうどく", "どくどく"),
        ("じゅうなん", "まひ", "でんじは"),
        ("やるき", "ねむり", "ねむりごな"),
        ("スイートベール", "ねむり", "ねむりごな"),
        ("みずのベール", "やけど", "おにび"),
        # ("マグマのよろい", "こおり", ""),
    ],
)
def test_状態異常無効_かたやぶりで無効(ability: str, ailment: AilmentName, move: str):
    # カビゴン（ノーマル）はまひ・ねむり・やけど・どく全てのタイプ耐性を持たないため使用
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.actives[0].ailment.is_active


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


@pytest.mark.parametrize(
    "ability_name, stats, source_is_self, expected",
    [
        ("かいりきバサミ", {"atk": -1, "def": -1, "spa": -2}, False, {"def": -1, "spa": -2}),
        ("かいりきバサミ", {"atk": -1}, True, {"atk": -1}),
        ("はとむね", {"atk": -1, "def": -1, "spa": -2}, False, {"atk": -1, "spa": -2}),
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
    assert battle.actives[0].rank[stat] == expected


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
    assert mon.rank["spe"] == -1
    assert mon.rank[stat] == expected


@pytest.mark.parametrize(
    "defender_ability, attacker_ability, move_name, should_block",
    [
        ("ぼうおん", "", "バークアウト", True),
        ("ぼうおん", "かたやぶり", "バークアウト", False),
        ("ぼうだん", "", "かえんボール", True),
        ("ぼうだん", "かたやぶり", "かえんボール", False),
        ("ぼうだん", "", "みずあめボム", True),
        ("ぼうだん", "かたやぶり", "みずあめボム", False),
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
