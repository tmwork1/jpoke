"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle

import pytest


from jpoke import Pokemon
from jpoke.core import EventContext
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import MEMORY_TO_TYPE, PLATE_TO_TYPE
from jpoke.enums import Event, Interrupt, Command
from jpoke.utils.type_defs import Type, Stat, AilmentName, VolatileName, Weather
from jpoke.model import Move

import test_utils as t


AR_SYSTEM_MEMORY_CASES = [
    (memory_item_name, expected_type)
    for memory_item_name, expected_type in MEMORY_TO_TYPE.items()
    if memory_item_name in ITEMS
]


# ──────────────────────────────────────────────────────────────────
# ARシステム
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "memory_item_name, expected_type",
    AR_SYSTEM_MEMORY_CASES,
)
def test_ARシステム_メモリで対応タイプになる(memory_item_name: str, expected_type: str):
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム", item_name=memory_item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == expected_type
    assert mon.ability.revealed is False  # ARシステムは開示されない


def test_ARシステム_メモリなしでタイプ変更なし():
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None
    assert mon.ability.revealed is False  # メモリなしは不発なので False


# ──────────────────────────────────────────────────────────────────
# アイスフェイス
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# アイスボディ、あめうけざら
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ability_name,weather_name,weather_count",
    [
        ("あめうけざら", "あめ", 5),
        ("あめうけざら", "おおあめ", 999),
        ("アイスボディ", "ゆき", 5),
    ]
)
def test_天候回復特性_対応天候中に回復(ability_name: str, weather_name: str, weather_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16


def test_あめうけざら_あめ以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="あめうけざら")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    t.end_turn(battle)
    assert mon.hp == before


# ──────────────────────────────────────────────────────────────────
#  あくしゅう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  あついしぼう、たいねつ
# ──────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────
#  あとだし
# ──────────────────────────────────────────────────────────────────


def test_あとだし_同優先度で最後に行動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle)
    order = battle.resolve_action_order()
    assert order[-1] == battle.actives[0]


def test_あとだし_高優先度技は先攻():
    """あとだし: 相手より優先度が高い技を使用した場合は先攻になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    t.reserve_command(battle)
    order = battle.resolve_action_order()
    assert order[0] == battle.actives[0]


def test_あとだし_トリックルームでも後攻():
    """あとだし: トリックルーム状態でも最後に行動する（素早さ逆転の影響を受けない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし")],
        team1=[Pokemon("ピカチュウ")],
        field={"トリックルーム": 5},
    )
    t.reserve_command(battle)
    order = battle.resolve_action_order()
    assert order[-1] == battle.actives[0]

# ──────────────────────────────────────────────────────────────────
#  アナライズ
# ──────────────────────────────────────────────────────────────────


def test_アナライズ_確定行動順で後攻なら威力上昇():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    attacker, defender = battle.actives
    state0 = battle.player_states[battle.players[0]]
    state1 = battle.player_states[battle.players[1]]

    # defender(先攻) -> attacker(後攻) の順で確定したケース
    state1.action_order_index = 0
    state0.action_order_index = 1

    result = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert result == 5325


def test_アナライズ_確定行動順で先攻なら威力据え置き():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    attacker, defender = battle.actives
    state0 = battle.player_states[battle.players[0]]
    state1 = battle.player_states[battle.players[1]]

    # attacker(先攻) -> defender(後攻) の順で確定したケース
    state0.action_order_index = 0
    state1.action_order_index = 1

    result = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert result == 4096


def test_アナライズ_行動順未記録時は従来フォールバックで判定():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    attacker, defender = battle.actives
    defender_player = battle.get_player(defender)
    battle.player_states[defender_player].has_switched = True

    result = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert result == 5325


# ──────────────────────────────────────────────────────────────────
#  あまのじゃく
# ──────────────────────────────────────────────────────────────────


def test_あまのじゃく_能力変化量の符号を反転する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"A": 1, "B": -2, "C": 3, "D": -4, "S": 1, "ACC": -2, "EVA": 3}
    battle.modify_stats(target, stats, source=source)
    for stat, change in stats.items():
        assert target.rank[stat] == max(-6, min(6, -change))


def test_あまのじゃく_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1

# ──────────────────────────────────────────────────────────────────
# 天候始動
# あめふらし、ひでり、すなおこし、ゆきふらし
# おわりのだいち、はじまりのうみ、デルタストリーム
# ──────────────────────────────────────────────────────────────────


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


@pytest.mark.parametrize(
    "ability_name, weather_name, default_count",
    ability_weather_defaultcount
)
def test_天候始動特性_登場時に発動(ability_name: str, weather_name: str, default_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == weather_name
    assert battle.weather.count == default_count
    assert battle.actives[0].ability.revealed is True


@pytest.mark.parametrize(
    "initial_weather", ["はれ", "すなあらし", "ゆき"]
)
def test_あめふらし_通常天候を上書きする(initial_weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="あめふらし")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "あめ"


@pytest.mark.parametrize(
    "initial_weather", strong_weathers
)
def test_あめふらし_強天候は上書き不可(initial_weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="あめふらし")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == initial_weather


@pytest.mark.parametrize(
    "weather_name",
    normal_weathers + ["おおあめ"]
)
def test_おわりのだいち_らんきりゅう以外上書きする(weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="おわりのだいち")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "おおひでり"


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
    weathers
)
def test_らんきりゅう_すべての天候を上書きする(weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="デルタストリーム")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "らんきりゅう"


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


# ──────────────────────────────────────────────────────────────────
# 交代抑制
# ありじごく、かげふみ、じりょく
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ability_name, attacker_name, attacker_ability, expected_can_switch",
    [
        ("ありじごく", "ピカチュウ", "", False),
        ("ありじごく", "ピジョン", "", True),
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


# ──────────────────────────────────────────────────────────────────
# 状態異常・揮発状態耐性
# アロマベール、スイートベール、どんかん、マイペース
# ──────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────
#  いかく
# ──────────────────────────────────────────────────────────────────


def test_いかく_登場時に相手攻撃1段階ダウン():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == -1


# ──────────────────────────────────────────────────────────────────
#  いかりのこうら
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  いかりのつぼ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  いしあたま
# ──────────────────────────────────────────────────────────────────


def test_いしあたま_反動技を使っても反動ダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["すてみタックル"])],
        team1=[Pokemon("ヤドン")],
    )
    attacker = battle.actives[0]
    battle.advance_turn()
    assert attacker.hp == attacker.max_hp

# ──────────────────────────────────────────────────────────────────
#  いたずらごころ
# ──────────────────────────────────────────────────────────────────


def test_いたずらごころ_変化技の優先度が1上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["でんじは"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    assert attacker.moves[0].priority == 0
    assert battle.speed_calculator.calc_move_priority(attacker, attacker.moves[0]) == 1


def test_いたずらごころ_あくタイプ相手には変化技が無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["でんじは"])],
        team1=[Pokemon("ヘルガー")],
    )
    ctx = t.build_context(battle, atk_idx=0)
    assert not battle.events.emit(Event.ON_BEFORE_APPLY_MOVE, ctx, True)


def test_いたずらごころ_自己対象の変化技はあくタイプ相手でも成功する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["かえんのまもり"])],
        team1=[Pokemon("ヘルガー")],
    )
    ctx = t.build_context(battle, atk_idx=0)
    assert battle.events.emit(Event.ON_BEFORE_APPLY_MOVE, ctx, True)


# ──────────────────────────────────────────────────────────────────
#  いろめがね
# ──────────────────────────────────────────────────────────────────


def test_いろめがね_いまひとつのダメージが2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いろめがね", move_names=["むしのていこう"])],
        team1=[Pokemon("ピジョン")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.damage_modifier

# ──────────────────────────────────────────────────────────────────
# タイプ威力強化
# いわはこび、トランジスタ、はがねつかい、はがねのせいしん、りゅうのあぎと
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ability_name, move_name, expected",
    [
        ("いわはこび", "いわなだれ", 6144),
        ("はがねつかい", "アイアンヘッド", 6144),
        ("りゅうのあぎと", "りゅうのはどう", 6144),
        ("トランジスタ", "でんきショック", 5325),
    ],
)
def test_タイプ依存攻撃補正特性(ability_name: str, move_name: str, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert expected == battle.damage_calculator.atk_modifier

# ──────────────────────────────────────────────────────────────────
#  うのミサイル
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  うるおいボイス
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  うるおいボディ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# 天候無効
# エアロック
# ノーてんきはエアロックと共通実装のためテスト不要
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("weather_name", weathers)
def test_エアロック_天候と強天候を無効化する(weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="エアロック")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 5),
    )
    assert battle.weather.name == ""


def test_エアロック_すなあらしのターン終了ダメージが無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="エアロック")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END, None, None)
    assert mon.hp == mon.max_hp


# ──────────────────────────────────────────────────────────────────
# フィールド始動
# エレキメイカー、グラスメイカー、サイコメイカー、ミストメイカー
# ──────────────────────────────────────────────────────────────────

ability_terrain_pairs = [
    ("エレキメイカー", "エレキフィールド"),
    ("グラスメイカー", "グラスフィールド"),
    ("サイコメイカー", "サイコフィールド"),
    ("ミストメイカー", "ミストフィールド"),
]


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
    "ability_name, terrain_name",
    ability_terrain_pairs
)
def test_地形始動特性_同一地形が有効時は継続ターンを更新しない(ability_name: str, terrain_name: str):
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
    "initial_terrain",
    [
        "グラスフィールド",
        "サイコフィールド",
        "ミストフィールド",
    ],
)
def test_エレキメイカー_別フィールドを上書きする(initial_terrain: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="エレキメイカー")],
        team1=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 99),
    )
    mon = battle.player_states[battle.players[0]].team[1]
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert mon.ability.revealed


# ──────────────────────────────────────────────────────────────────
#  えんかく
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  おうごんのからだ
# ──────────────────────────────────────────────────────────────────
def test_おうごんのからだ_相手の変化技を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    battle.print_logs()
    assert battle.move_executor.move_applied is False
    assert battle.actives[1].ability.revealed is True


def test_おうごんのからだ_攻撃技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True
    assert battle.actives[1].ability.revealed is False


def test_おうごんのからだ_自分対象の変化技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_場が対象の技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にほんばれ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    battle.print_logs()
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True

# ──────────────────────────────────────────────────────────────────
#  オーラブレイク
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  おどりこ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  おみとおし
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  おもかげやどし
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  おやこあい
# ──────────────────────────────────────────────────────────────────


def test_おやこあい_単発攻撃が2ヒットする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # ダメージ計算結果を固定
    battle.roll_damage = lambda *args, **kwargs: 40
    t.run_move(battle, 0)
    attacker, defender = battle.actives
    assert defender.hits_taken == 2
    assert defender.hp == defender.max_hp - 40 - 10
    assert attacker.rank["S"] == 2


def test_おやこあい_既存連続技には適用しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["すいりゅうれんだ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    t.run_move(battle, 0)
    assert defender.hits_taken == 3


# ──────────────────────────────────────────────────────────────────
#  カーリーヘア
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# かいりきバサミ、はとむね
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ability_name, stats, source_is_self, expected",
    [
        ("かいりきバサミ", {"A": -1, "B": -1, "C": -2}, False, {"B": -1, "C": -2}),
        ("かいりきバサミ", {"A": -1}, True, {"A": -1}),
        ("はとむね", {"A": -1, "B": -1, "C": -2}, False, {"A": -1, "C": -2}),
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


# ──────────────────────────────────────────────────────────────────
#  かがくへんかガス
# ──────────────────────────────────────────────────────────────────


def test_かがくへんかガス_登場時に相手の特性を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert not battle.actives[1].ability.enabled
    assert not battle.actives[1].ability.revealed
    assert battle.actives[0].rank["A"] == 0


def test_かがくへんかガス_解除後は特性が再び有効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    player = battle.players[0]
    t.run_switch(battle, 0, 1)
    assert battle.actives[1].ability.enabled
    assert battle.actives[1].ability.revealed
    assert battle.actives[0].rank["A"] == 0


def test_かがくへんかガス_互いのかがくへんかガスは無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled
    assert battle.actives[1].ability.enabled

# ──────────────────────────────────────────────────────────────────
#  かぜのり
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  かそく
# ──────────────────────────────────────────────────────────────────


def test_かそく_行動後のターン終了時に素早さが上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かそく")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["S"] == 0

    mon.executed_move = mon.moves[0]
    battle.events.emit(Event.ON_TURN_END)
    assert mon.rank["S"] == 1


def test_かそく_交代直後のターンは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="かそく", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # 交代したターンはかそくが発動しない
    t.reserve_command(battle,
                      command0=Command.SWITCH_1,
                      command1=Command.MOVE_0)
    battle.advance_turn()

    mon = battle.actives[0]
    assert mon.rank["S"] == 0

    # 次のターンはかそくが発動する
    t.reserve_command(battle,
                      command0=Command.MOVE_0,
                      command1=Command.MOVE_0)
    battle.advance_turn()
    assert mon.rank["S"] == 1

# ──────────────────────────────────────────────────────────────────
# 技カテゴリによる威力強化
# かたいツメ、がんじょうあご、きれあじ、すてみ、てつのこぶし、
# パンクロック、メガランチャー
# ──────────────────────────────────────────────────────────────────


def test_かたいツメ_接触技のみ威力補正1_3倍():
    battle_contact = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたいツメ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle_contact, 0)
    assert 5325 == battle_contact.damage_calculator.power_modifier

    battle_non_contact = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたいツメ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle_non_contact, 0)
    assert 4096 == battle_non_contact.damage_calculator.power_modifier


def test_がんじょうあご_かみつき技で威力補正1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょうあご", move_names=["かみつく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_きれあじ_きる技は威力補正1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きれあじ", move_names=["きりさく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_きれあじ_きる技以外は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きれあじ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_てつのこぶし_パンチ技以外は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てつのこぶし", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_てつのこぶし_パンチ技威力補正():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てつのこぶし", move_names=["かみなりパンチ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4915 == battle.damage_calculator.power_modifier


def test_パンクロック_音技で威力1_3倍かつ被ダメ0_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="パンクロック", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier

    battle2 = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability_name="パンクロック", move_names=["バークアウト"])],
    )
    t.run_move(battle2, 0)
    assert 2048 == battle2.damage_calculator.damage_modifier


def test_パンクロック_かたやぶりで音技軽減が無効化される():
    """パンクロック: かたやぶり持ちの音技はパンクロックの被ダメ軽減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability_name="パンクロック")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


@pytest.mark.parametrize(
    "ability_name, move_name, expected_power, check",
    [
        ("かたいツメ", "たいあたり", 5325, "power"),
        ("かたいツメ", "でんきショック", 4096, "power"),
        ("がんじょうあご", "かみつく", 6144, "power"),
        ("きれあじ", "きりさく", 6144, "power"),
        ("てつのこぶし", "かみなりパンチ", 4915, "power"),
        ("パンクロック", "バークアウト", 5325, "power"),
    ],
)
def test_技カテゴリによる威力補正_param(ability_name: str, move_name: str, expected_power: int, check: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    if check == "power":
        assert expected_power == battle.damage_calculator.power_modifier
    else:
        assert expected_power == battle.damage_calculator.damage_modifier


@pytest.mark.parametrize(
    "ability, stats, expected",
    [
        ("かいりきバサミ", {"A": -1, "B": -1, "C": -2}, {"B": -1, "C": -2}),
        ("はとむね", {"A": -1, "B": -1, "C": -2}, {"A": -1, "C": -2}),
    ],
)
def test_防御系特性_stat_block_param(ability: str, stats: dict, expected: dict):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0 = battle.actives[0]
    mon1 = battle.actives[1]
    stat_change = battle.modify_stats(mon0, stats, source=mon1)
    assert stat_change == expected


@pytest.mark.parametrize(
    "defender_ability, attacker_ability, move_name, should_block",
    [
        ("ぼうおん", "", "バークアウト", True),
        ("ぼうおん", "かたやぶり", "バークアウト", False),
        ("ぼうだん", "", "かえんボール", True),
        ("ぼうだん", "かたやぶり", "かえんボール", False),
    ],
)
def test_音技無効系_param(defender_ability: str, attacker_ability: str, move_name: str, should_block: bool):
    # attacker_ability may be empty string for no ability
    team0 = [Pokemon("ピカチュウ", ability_name=attacker_ability or "", move_names=[move_name])]
    team1 = [Pokemon("ピカチュウ", ability_name=defender_ability)]
    battle = t.start_battle(team0=team0, team1=team1)
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


# ──────────────────────────────────────────────────────────────────
# かたやぶり、ターボブレイズ、テラボルテージ
# ターボブレイズ、テラボルテージはかたやぶりと共通実装のためテスト不要
# ──────────────────────────────────────────────────────────────────


def test_かたやぶり_場に出たときに特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed is True


# ──────────────────────────────────────────────────────────────────
# 能力低下カウンター
# かちき、まけんき
# ──────────────────────────────────────────────────────────────────


def test_かちき_相手由来の能力低下で発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かちき")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon, foe = battle.actives
    battle.modify_stats(mon, {"A": -1}, source=foe)
    assert mon.rank["C"] == 2


def test_かちき_自分由来の能力低下では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かちき")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_stats(mon, {"A": -1}, source=mon)
    assert mon.rank["C"] == 0


def test_かちき_いかくで特攻2段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かちき")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[0].rank["C"] == 2


# ──────────────────────────────────────────────────────────────────
# 急所無効
# カブトアーマー、シェルアーマー
# シェルアーマーはカブトアーマーと共通実装のためテスト不要
# ──────────────────────────────────────────────────────────────────
def test_カブトアーマー_急所ランクを0にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カブトアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is False


def test_カブトアーマー_かたやぶり攻撃では無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="カブトアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is True


# ──────────────────────────────────────────────────────────────────
# かるわざ
# ──────────────────────────────────────────────────────────────────


def test_かるわざ_アイテムを失うと素早さが2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.consume_item(mon)
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_かるわざ_アイテムを再取得すると発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.consume_item(mon)
    t.change_item(battle, mon, "オボンのみ")
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_かるわざ_アイテムを失ってから再入場しても発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ", item_name="オボンのみ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.consume_item(mon)
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_かるわざ_入場時にアイテムなしなら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かるわざ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    boosted = battle.calc_effective_speed(mon)
    assert boosted == mon.stats["S"]


# ──────────────────────────────────────────────────────────────────
# がんじょう
# ──────────────────────────────────────────────────────────────────


def test_がんじょう_HP満タン時の致死ダメージでHP1残る():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ガブリアス", move_names=["じしん"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == 1
    assert defender.ability.revealed


def test_がんじょう_一撃必殺技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["じわれ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.move_executor.move_applied is False


def test_がんじょう_かたやぶりによる致死ダメージは耐えない():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ガブリアス", ability_name="かたやぶり", move_names=["じしん"])],
    )
    battle.roll_damage = lambda *_args, **_kwargs: 999
    t.run_move(battle, 1)
    assert battle.actives[0].hp == 0


def test_がんじょう_かたやぶりにで一撃技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="がんじょう")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じわれ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.move_executor.move_applied is True


# ──────────────────────────────────────────────────────────────────
# かんそうはだ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# かんろなミツ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ききかいひ、にげごし
# ──────────────────────────────────────────────────────────────────
def test_ききかいひ_HP半分超から半分以下で割り込み交代する():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="ききかいひ"),
            Pokemon("ピカチュウ", move_names=["たいあたり"])
        ],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]

    damage = defender.max_hp - defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: damage

    t.run_move(battle, 1)

    assert battle.player_states[battle.players[0]].interrupt == Interrupt.EMERGENCY

    battle.run_interrupt_switch(Interrupt.EMERGENCY)

    assert battle.player_states[battle.players[0]].active_index == 1


def test_ききかいひ_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability_name="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]

    defender.hp = defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: 1

    t.run_move(battle, 1)

    assert battle.player_states[battle.players[0]].interrupt == Interrupt.NONE
    assert battle.player_states[battle.players[0]].active_index == 0


def test_ききかいひ_やけどダメージでも発動する():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability_name="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    mon.hp = mon.max_hp // 2 + 1
    battle.ailment_manager.apply(mon, "やけど")
    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))

    assert battle.player_states[battle.players[0]].interrupt == Interrupt.EMERGENCY


def test_ききかいひ_こんらん自傷では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability_name="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")

    assert battle.player_states[battle.players[0]].interrupt == Interrupt.NONE


# ──────────────────────────────────────────────────────────────────
# きけんよち
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ぎたい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# きもったま
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ぎゃくじょう
# ──────────────────────────────────────────────────────────────────

def test_ぎゃくじょう_HP半分超から半分以下で特攻1段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender, attacker = battle.actives
    defender.hp = defender.max_hp // 2 + 2
    t.run_move(battle, 1)

    assert defender.hp <= defender.max_hp // 2
    assert defender.rank["C"] == 1
    assert defender.ability.revealed is True


def test_ぎゃくじょう_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]

    defender.hp = defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: 1

    t.run_move(battle, 1)

    assert defender.rank["C"] == 0


# ──────────────────────────────────────────────────────────────────
#  きゅうばん
# ──────────────────────────────────────────────────────────────────
def test_きゅうばん_吹き飛ばしを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("フシギダネ")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    defender_after = battle.actives[1]
    # きゅうばんにより交代が阻止され、アクティブは変わらない
    assert defender_before is defender_after


def test_きゅうばん_かたやぶりで無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("フシギダネ")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    defender_after = battle.actives[1]
    # かたやぶりによってきゅうばんの無効化が貫通され、交代が発生する
    assert defender_before is not defender_after

# ──────────────────────────────────────────────────────────────────
# きょううん
# ──────────────────────────────────────────────────────────────────


def test_きょううん_急所ランクが1上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きょううん", move_names=["つじぎり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        EventContext(attacker=attacker, defender=defender, move=move),
        0,
    )
    assert result == 1


# ──────────────────────────────────────────────────────────────────
# ぎょぐん
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# きよめのしお
# ──────────────────────────────────────────────────────────────────
def test_きよめのしお_ゴースト半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シャドーボール"])],
        team1=[Pokemon("ピカチュウ", ability_name="きよめのしお")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 2048


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"]
)
def test_きよめのしお_状態異常無効(ailment_name):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きよめのしお")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert not t.apply_ailment(battle, 0, ailment_name)

# ──────────────────────────────────────────────────────────────────
# きんしのちから
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# きんちょうかん
# ──────────────────────────────────────────────────────────────────


def test_きんちょうかん_相手をきんちょうかん状態にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="きんちょうかん")],
    )
    assert battle.query.is_nervous(battle.actives[0])
    assert battle.actives[1].ability.enabled


# ──────────────────────────────────────────────────────────────────
# くいしんぼう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# クイックドロウ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# クォークチャージ、こだいかっせい
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ability_name, setup_kwargs, expected_source, keep_item_before_release",
    [
        ("クォークチャージ", {}, "item", False),
        ("こだいかっせい", {"weather": ("はれ", 5)}, "field", True),
        ("クォークチャージ", {"terrain": ("エレキフィールド", 5)}, "field", True),
    ],
)
def test_パラドックス特性_ブーストエナジーと場条件の優先関係(
    ability_name: str,
    setup_kwargs: dict,
    expected_source: str,
    keep_item_before_release: bool,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ", ability_name="ひでり" if setup_kwargs.get("weather") else "エレキメイカー" if setup_kwargs.get("terrain") else "")],
        **setup_kwargs,
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_source == expected_source
    assert mon.paradox_boost_active
    assert mon.has_item("ブーストエナジー") is keep_item_before_release

    if expected_source == "field":
        if setup_kwargs.get("weather"):
            battle.weather_manager.remove()
        else:
            battle.terrain_manager.remove()
        assert mon.paradox_boost_active
        assert mon.paradox_boost_source == "item"
        assert not mon.has_item("ブーストエナジー")


@pytest.mark.parametrize(
    "name, stat",
    [
        ("スピアー", "A"),
        ("ゼニガメ", "B"),
        ("フシギダネ", "C"),
        ("カメックス", "D"),
        ("ピカチュウ", "S"),
    ]
)
def test_クォークチャージ_最大ステータスがバフされる(name, stat):
    battle = t.start_battle(
        team0=[Pokemon(name, ability_name="クォークチャージ", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat == stat


# ──────────────────────────────────────────────────────────────────
# くさのけがわ
# ──────────────────────────────────────────────────────────────────


def test_くさのけがわ_():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_くさのけがわ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier

# ──────────────────────────────────────────────────────────────────
# くだけるよろい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# クリアボディ、しろいけむり、メタルプロテクト
# メタルプロテクトがかたやぶり非適用である点を除けば共通実装なので、
# 基本効果の検証はクリアボディだけでよい
# ──────────────────────────────────────────────────────────────────


def test_クリアボディ_能力低下を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stats = {"A": -1, "B": +1, "C": -3, "D": +3, "S": -5, "ACC": +5, "EVA": -6}
    expected = {k: v for k, v in stats.items() if v > 0}

    assert expected == battle.modify_stats(mon0, stats, source=mon1)


def test_クリアボディ_自己低下技は防げない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, _ = battle.actives
    stats = {"A": -1, "B": +1, "C": -3, "D": +3, "S": -5, "ACC": +5, "EVA": -6}
    expected = stats

    assert expected == battle.modify_stats(mon0, stats, source=mon0)


def test_クリアボディ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1


def test_メタルプロテクト_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メタルプロテクト")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == 0


# ──────────────────────────────────────────────────────────────────
# 倒すと能力上昇
# くろのいななき、しろのいななき、じしんかじょう
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ability_name, stat",
    [
        ("じしんかじょう", "A"),
        ("しろのいななき", "A"),
        ("くろのいななき", "C"),
    ],
)
def test_倒すと能力上昇系_相手を倒すと指定ステータスが1段階上昇する(ability_name: str, stat: str):
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
        ("じしんかじょう", "A"),
        ("しろのいななき", "A"),
        ("くろのいななき", "C"),
    ],
)
def test_倒すと能力上昇系_相手を倒せないと発動しない(ability_name: str, stat: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.fainted
    assert attacker.rank[stat] == 0


# ──────────────────────────────────────────────────────────────────
# HP低下時にタイプ威力強化
# げきりゅう、しんりょく、むしのしらせ、もうか
# ──────────────────────────────────────────────────────────────────


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


# ──────────────────────────────────────────────────────────────────
# こおりのりんぷん
# ──────────────────────────────────────────────────────────────────


def test_こおりのりんぷん_特殊技のダメージ半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_こおりのりんぷん_物理技のダメージ半減しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_こおりのりんぷん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# こぼれダネ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ごりむちゅう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# 技タイプ無効能力上昇
# こんがりボディ、そうしょく、でんきエンジン、ひらいしん、よびみず
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ability, move, stat, rank",
    [
        ("こんがりボディ", "ひのこ", "B", 2),
        ("そうしょく", "このは", "A", 1),
        ("でんきエンジン", "でんきショック", "S", 1),
        ("ひらいしん", "でんきショック", "C", 1),
        ("よびみず", "みずでっぽう", "C", 1),
    ],
)
def test_タイプ無効バフ特性(ability: str, move: str, stat: Stat, rank: int):
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
        ("こんがりボディ", "ひのこ", "B", 2),
        ("そうしょく", "このは", "A", 1),
        ("でんきエンジン", "でんきショック", "S", 1),
        ("ひらいしん", "でんきショック", "C", 1),
        ("よびみず", "でんきショック", "C", 1),
    ],
)
def test_タイプ無効特性_かたやぶりで無効(ability: str, move: str, stat: Stat, rank: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
        team1=[Pokemon("ピカチュウ", ability_name=ability)],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.rank[stat] == 0


# ──────────────────────────────────────────────────────────────────
# こんじょう
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "やけど"],
)
def test_こんじょう_行動可能な状態異常で攻撃1_5倍(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="こんじょう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, ailment_name)
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_こんじょう_やけど時はやけど半減を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="こんじょう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144
    assert battle.damage_calculator.burn_modifier == 4096


# ──────────────────────────────────────────────────────────────────
# サーフテール
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# さいせいりょく
# ──────────────────────────────────────────────────────────────────


def test_さいせいりょく_交代で控えに戻ると回復する():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="さいせいりょく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_switch(battle, 0, 1)
    assert mon.hp == 1 + mon.max_hp // 3


def test_さいせいりょく_かいふくふうじ中でも回復する():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="さいせいりょく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": 99}
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_switch(battle, 0, 1)
    assert mon.hp == 1 + mon.max_hp // 3


# ──────────────────────────────────────────────────────────────────
# さまようたましい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# さめはだ、てつのトゲ
# てつのトゲの実装はさめはだと共通のためテスト不要
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ability_name,move_name,damage_ratio",
    [
        ("さめはだ", "たいあたり", 1/8),
        ("さめはだ", "みずでっぽう", 0),
        ("てつのトゲ", "たいあたり", 1/8),
        ("てつのトゲ", "みずでっぽう", 0),
    ],
)
def test_さめはだ_接触ダメージ(ability_name: str, move_name: str, damage_ratio: float):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=[move_name])],
    )
    _, attacker = battle.actives
    t.run_move(battle, 1)
    assert attacker.hp == attacker.max_hp - int(attacker.max_hp * damage_ratio)


# ──────────────────────────────────────────────────────────────────
# サンパワー
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "weather_name,weather_count",
    [
        ("はれ", 5),
        ("おおひでり", 5)
    ]
)
def test_サンパワー_はれ中に特殊技の特攻1_5倍(weather_name: str, weather_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_サンパワー_物理技は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_サンパワー_はれ中にターン終了時1_8ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    t.end_turn(battle)
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp - mon.max_hp // 8


def test_サンパワー_はれ以外ではターン終了時ダメージなし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="サンパワー")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.end_turn(battle)
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp


# ──────────────────────────────────────────────────────────────────
# じきゅうりょく
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# しぜんかいふく
# ──────────────────────────────────────────────────────────────────


def test_しぜんかいふく_交代時に状態異常回復():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="しぜんかいふく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.is_active
    t.run_switch(battle, 0, 1)
    assert not mon.ailment.is_active


# ──────────────────────────────────────────────────────────────────
# しめりけ
# ──────────────────────────────────────────────────────────────────


def test_しめりけ_じばくを失敗させる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じばく"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_しめりけ_自分の爆発技も失敗させる():
    battle = t.start_battle(
        team0=[Pokemon("ニョロモ", ability_name="しめりけ", move_names=["じばく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_しめりけ_爆発ラベルなし技は通す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


def test_しめりけ_かたやぶりで爆発技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じばく"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


# ──────────────────────────────────────────────────────────────────
# しゅうかく : テスト保留
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# 状態異常耐性
# じゅうなん、スイートベール、めんえき、パステルベール、ふみん、やるき、
# みずのベール、マグマのよろい
# ──────────────────────────────────────────────────────────────────

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
        ("ふみん", "ねむり", "ねむりごな"),
        ("やるき", "ねむり", "ねむりごな"),
        ("スイートベール", "ねむり", "ねむりごな"),
        ("みずのベール", "やけど", "おにび"),
        # ("マグマのよろい", "こおり", ""),
    ],
)
def test_状態異常無効_かたやぶりで無効(ability: str, ailment: AilmentName, move: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move])],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, ailment)
    assert not mon.ailment.is_active


# ──────────────────────────────────────────────────────────────────
# じゅくせい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# 特定のタイプの技を受けると能力上昇
# じょうききかん、せいぎのこころ、びびり、みずがため
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# しょうりのほし
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# 先制技無効
# じょおうのいげん、テイルアーマー
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# しんがん
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# シンクロ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# じんばいったい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# 天候下でS上昇
# すいすい、すなかき、ゆきかき
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "ability, weather, expected_mult",
    [
        ("すなかき", "すなあらし", 2),
        ("すいすい", "あめ", 2),
        ("ようりょくそ", "はれ", 2),
        ("ゆきかき", "ゆき", 2),
    ],
)
def test_天候依存素早さ上昇(ability: str, weather: str, expected_mult: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability)],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 999),
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * expected_mult


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
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


# ──────────────────────────────────────────────────────────────────
# すいほう
# ──────────────────────────────────────────────────────────────────
def test_すいほう_みず技強化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すいほう", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_すいほう_ほのお技弱化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すいほう")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    t.run_move(battle, 1)
    assert 2048 == battle.damage_calculator.atk_modifier


# ──────────────────────────────────────────────────────────────────
# スキン
# スカイスキン、フェアリースキン、フリーズスキン
# ──────────────────────────────────────────────────────────────────
SKIN_CASES = [
    ("スカイスキン", "ひこう"),
    ("フェアリースキン", "フェアリー"),
    ("フリーズスキン", "こおり"),
]


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン_ノーマル技を対応タイプに変換する(
    ability_name: str,
    expected_type: str,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    move = t.run_move(battle, 0)
    assert move.type == expected_type


@pytest.mark.parametrize(
    "ability_name, expected_type",
    SKIN_CASES
)
def test_スキン_変換した技の威力が4915倍になる(
    ability_name: str,
    expected_type: str,
):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


# ──────────────────────────────────────────────────────────────────
# スキルリンク
# ──────────────────────────────────────────────────────────────────
# TODO : テスト実装

# ──────────────────────────────────────────────────────────────────
# スナイパー
# ──────────────────────────────────────────────────────────────────
def test_スナイパー_急所時の最終ダメージを1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スナイパー", move_names=["トリックフラワー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.crit_rank == 3
    assert 6144 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# すながくれ、ゆきがくれ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ability_name, weather",
    [
        ("ゆきがくれ", "ゆき"),
        ("すながくれ", "すなあらし"),
    ],
)
def test_天気がくれ系_対応天気で命中低下(ability_name: str, weather: str):
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
def test_天気がくれ系_対応天気以外では命中率変化なし(ability_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
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
def test_天気がくれ系_かたやぶりで命中率補正なし(ability_name: str, weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
        weather=(weather, 5),  # type: ignore[arg-type]
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy

# ──────────────────────────────────────────────────────────────────
# すなのちから
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "move_name, expected",
    [
        ("いわなだれ", 5325),
        ("じならし", 5325),
        ("アイアンヘッド", 5325),
        ("でんきショック", 4096),],
)
def test_すなのちから_すなあらし中に岩地面鋼技の威力が1_3倍になる(move_name: str, expected: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなのちから", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 5),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected


@pytest.mark.parametrize(
    "move_name",
    ["いわなだれ", "じならし", "アイアンヘッド"],
)
def test_すなのちから_すなあらし以外では威力補正なし(move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなのちから", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


# ──────────────────────────────────────────────────────────────────
# すなはき
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# すりぬけ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "wall_name, move_name",
    [
        ("リフレクター", "たいあたり"),
        ("ひかりのかべ", "でんきショック"),
        ("オーロラベール", "たいあたり"),
        ("オーロラベール", "でんきショック"),
    ],
)
def test_すりぬけ_壁を無視する(wall_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        side1={wall_name: 5},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_すりぬけ_みがわりを無視する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みがわり": 1},
    )
    t.run_move(battle, 0)
    assert battle.actives[1].hp < battle.actives[1].max_hp


def test_すりぬけ_しんぴのまもりを貫通して状態異常が入る():
    """すりぬけ: しんぴのまもり中でも相手に状態異常を与えられる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ")],
        side1={"しんぴのまもり": 5},
    )
    attacker, defender = battle.actives
    assert battle.ailment_manager.apply(defender, "どく", source=attacker)
    assert defender.ailment.name == "どく"


def test_すりぬけ_しんぴのまもりを貫通してこんらんが入る():
    """すりぬけ: しんぴのまもり中でも相手にこんらんを与えられる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ")],
        side1={"しんぴのまもり": 5},
    )
    attacker, defender = battle.actives
    assert battle.volatile_manager.apply(defender, "こんらん", count=3, source=attacker)
    assert defender.has_volatile("こんらん")


# ──────────────────────────────────────────────────────────────────
# するどいめ
# ──────────────────────────────────────────────────────────────────


def test_するどいめ_命中率低下を防ぐ():
    """するどいめ: 相手による命中率ランク低下を防ぐ。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ")],
        team1=[Pokemon("ピカチュウ", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["ACC"] == 0


def test_するどいめ_かたやぶりで無効():
    """するどいめ: かたやぶり持ちによる命中率低下はするどいめを貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["ACC"] == -1


def test_するどいめ_相手の回避率ランクを無視する():
    """するどいめ: 攻撃時に相手の回避率ランク上昇を無視する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="するどいめ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].rank["EVA"] = 6
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


# ──────────────────────────────────────────────────────────────────
# スロースタート
# ──────────────────────────────────────────────────────────────────


def test_スロースタート_登場5ターン未満は攻撃補正0_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スロースタート", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier

    battle.turn = battle.actives[0].ability.count + 5
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_スロースタート_特攻には補正がかからない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スロースタート", move_names=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


# ──────────────────────────────────────────────────────────────────
# スワームチェンジ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# せいしんりょく
# ──────────────────────────────────────────────────────────────────


def test_せいしんりょく_ひるみを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert not battle.volatile_manager.apply(battle.actives[0], "ひるみ", count=1)


def test_せいしんりょく_いかくを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいしんりょく")],
        team1=[Pokemon("ウインディ", ability_name="いかく")],
    )
    assert battle.actives[0].rank["A"] == 0


# ──────────────────────────────────────────────────────────────────
# 接触時に状態異常付与
# せいでんき、どくのトゲ、ほのおのからだ
# ──────────────────────────────────────────────────────────────────
CONTACT_AILMENT_CASES = [
    ("せいでんき", "まひ"),
    ("どくのトゲ", "どく"),
    ("ほのおのからだ", "やけど"),
]


@pytest.mark.parametrize(
    "ability_name, ailment_name",
    CONTACT_AILMENT_CASES
)
def test_接触時に状態異常付与_接触技で状態異常を付与する(ability_name: str, ailment_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=["たいあたり"])],
    )
    attacker = battle.actives[1]
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    assert attacker.has_ailment(ailment_name)


@pytest.mark.parametrize(
    "ability_name, ailment_name",
    CONTACT_AILMENT_CASES
)
def test_接触時に状態異常付与_非接触技では発動しない(ability_name: str, ailment_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("イーブイ", move_names=["はどうだん"])],
    )
    attacker = battle.actives[1]
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    assert not attacker.has_ailment(ailment_name)

# ──────────────────────────────────────────────────────────────────
# ぜったいねむり
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ゼロフォーミング
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# そうだいしょう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ソウルハート
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# オーラ
# ダークオーラ、フェアリーオーラ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ダウンロード
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "foe_name, stat",
    [
        ("フシギダネ", "A"),
        ("ゼニガメ", "C"),
    ],
)
def test_ダウンロード_能力アップ(foe_name, stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダウンロード")],
        team1=[Pokemon(foe_name)],
    )
    assert battle.actives[0].rank[stat] == 1


def test_ダウンロード_BD等しいときCアップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダウンロード")],
        team1=[Pokemon("ウインディ")],
    )
    mon = battle.actives[0]
    assert mon.rank["C"] == 1


# ──────────────────────────────────────────────────────────────────
# だっぴ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_だっぴ_ターン終了時に状態異常を回復する(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, ailment_name)

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.events.emit(Event.ON_TURN_END)
    finally:
        battle.random.random = orig_random

    assert not mon.ailment.is_active


def test_だっぴ_非発動時は状態異常が残る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")

    orig_random = battle.random.random
    battle.random.random = lambda: 0.99
    try:
        battle.events.emit(Event.ON_TURN_END)
    finally:
        battle.random.random = orig_random

    assert mon.ailment.is_active


def test_だっぴ_発動ターンはどくダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    hp_before = mon.hp

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.events.emit(Event.ON_TURN_END)
        battle.events.emit(Event.ON_TURN_END)
    finally:
        battle.random.random = orig_random

    assert mon.hp == hp_before


# ──────────────────────────────────────────────────────────────────
# たんじゅん
# ──────────────────────────────────────────────────────────────────


def test_たんじゅん_能力上昇量が2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"A": 1, "B": -2, "C": 3, "D": -4, "S": 1, "ACC": -2, "EVA": 3}
    battle.modify_stats(target, stats, source=source)
    for stat, change in stats.items():
        assert target.rank[stat] == max(-6, min(6, change * 2))


def test_たんじゅん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1


# ──────────────────────────────────────────────────────────────────
# ちからずく
# ──────────────────────────────────────────────────────────────────
def test_ちからずく_追加効果あり技の威力が1_3倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 5325
    assert attacker.rank["S"] == 0


# ──────────────────────────────────────────────────────────────────
# ちからもち、ヨガパワー
# ヨガパワーの実装はちからもちと共通のためテスト不要
# ──────────────────────────────────────────────────────────────────


def test_ちからもち_物理技で攻撃補正2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_ちからもち_特殊技では攻撃補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_ちからもち_イカサマで攻撃するときも2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=["イカサマ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_ちからもち_イカサマを受けるときは補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち")],
        team1=[Pokemon("ピカチュウ", move_names=["イカサマ"])],
    )
    t.run_move(battle, 1)
    assert 4096 == battle.damage_calculator.atk_modifier


# ──────────────────────────────────────────────────────────────────
# タイプ無効で回復
# ちくでん、ちょすい、どしょく
# ──────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────
# ちどりあし
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# てきおうりょく
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "name, tera_type, move_name, expected_modifier",
    [
        ("ピカチュウ", "", "でんきショック", 4096 * 2),
        ("ピカチュウ", "でんき", "でんきショック", 4096 * 2.25),
        ("ピカチュウ", "", "ひのこ", 4096),
    ]
)
def test_てきおうりょく_STAB補正(
    name: str,
    tera_type: Type,
    move_name: str,
    expected_modifier: float,
):
    battle = t.start_battle(
        team0=[Pokemon(name, ability_name="てきおうりょく", tera_type=tera_type, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    if tera_type:
        battle.actives[0].terastallize()
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == expected_modifier


# ──────────────────────────────────────────────────────────────────
# テクニシャン
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 6144),  # 威力40の技は1.5倍
        ("すてみタックル", 4096),  # 威力90の技
    ]
)
def test_テクニシャン_威力補正(move_name, expected_modifier):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


def test_テクニシャン_連続技でもヒット毎に判定がぶれない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=["タネマシンガン"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    v1 = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move, hit_index=1, hit_count=5),
        4096,
    )
    v2 = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move, hit_index=5, hit_count=5),
        4096,
    )

    assert v1 == 6144
    assert v2 == 6144


# ──────────────────────────────────────────────────────────────────
# テラスシェル
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "defender_name, move_name, expected",
    [
        ("コイル", "なみのり", 4096*0.5),       # x1 -> x1/2
        ("コイル", "ひのこ", 4096*0.5),       # x2 -> x1/2
        ("コイル", "じしん", 4096*0.5),           # x4 -> x1/2
        ("コイル", "でんきショック", 4096*0.5),   # x1/2 -> x1/2
        ("コイル", "バレットパンチ", 4096*0.25),   # x1/4 -> x1/4
    ]
)
def test_テラスシェル_等倍以上を半減(defender_name, move_name, expected):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon(defender_name, ability_name="テラスシェル")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected


def test_テラスシェル_HP満タンでないと発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="テラスシェル")],
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp - 1
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_テラスシェル_かたやぶりで無効():
    """テラスシェル: かたやぶり持ちの技はテラスシェルの半減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="テラスシェル")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


# ──────────────────────────────────────────────────────────────────
# テラスチェンジ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# デルタストリーム
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# でんきにかえる
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# てんきや
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# てんねん
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "move_name, stat",
    [
        ("たいあたり", "A"),
        ("ひのこ", "C"),
    ]
)
def test_てんねん_防御側はACランク無視(move_name, stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="てんねん")],
    )
    attacker, defender = battle.actives
    attacker.rank[stat] = 2
    ctx = EventContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_ATK_RANK_MODIFIER, ctx, 2)
    assert result == 1


@pytest.mark.parametrize(
    "move_name, stat",
    [
        ("たいあたり", "B"),
        ("ひのこ", "D"),
    ]
)
def test_てんねん_攻撃側は防御ランク補正を無視する(move_name, stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんねん", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.rank[stat] = 2
    ctx = EventContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_DEF_RANK_MODIFIER, ctx, 2.0)
    assert result == 1.0


# ──────────────────────────────────────────────────────────────────
# てんのめぐみ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "chance_before, chance_after",
    [
        (0.3, 0.6),
        (0.7, 1.0),
    ]
)
def test_てんのめぐみ_追加効果確率が2倍になる(chance_before, chance_after):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんのめぐみ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    ctx = EventContext(attacker=attacker, move=attacker.moves[0])
    assert chance_after == battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, chance_before)


# ──────────────────────────────────────────────────────────────────
# とうそうしん
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# どくくぐつ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# どくげしょう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# どくしゅ
# ──────────────────────────────────────────────────────────────────

def test_どくしゅ_どく付与():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    _, defender = battle.actives

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.run_move(battle, 0)
    finally:
        battle.random.random = orig_random

    assert defender.has_ailment("どく")


def test_どくしゅ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("イーブイ", ability_name="どくしゅ", move_names=["はどうだん"])],
        team1=[Pokemon("ピカチュウ")],
    )
    _, defender = battle.actives

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.run_move(battle, 0)
    finally:
        battle.random.random = orig_random

    assert not defender.ailment.is_active


# ──────────────────────────────────────────────────────────────────
# どくのくさり
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# どくぼうそう、ねつぼうそう
# ──────────────────────────────────────────────────────────────────
# TODO : 実装


# ──────────────────────────────────────────────────────────────────
# トレース
# ──────────────────────────────────────────────────────────────────


def test_トレース_いかくをコピーすると即発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="トレース")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].ability.base_name == "いかく"
    assert battle.actives[1].rank["A"] == -1


def test_トレース_uncopyable特性だと不発():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="トレース")],
        team1=[Pokemon("ピカチュウ", ability_name="トレース")],
    )
    assert battle.actives[0].ability.base_name == "トレース"
    assert battle.actives[0].ability.revealed is False  # 不発なので False のまま


def test_トレース_交代で元の特性に戻り再入場で再コピーする():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="トレース"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("ピカチュウ", ability_name="すなかき")],
    )

    tracer = battle.player_states[battle.players[0]].team[0]
    assert tracer.ability.base_name == "すなかき"

    t.run_switch(battle, 0, 1)
    assert tracer.ability.base_name == "トレース"

    t.run_switch(battle, 0, 0)
    assert tracer.ability.base_name == "すなかき"

# ──────────────────────────────────────────────────────────────────
# とれないにおい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ナイトメア
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# なまけ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ぬめぬめ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ねつこうかん
# ──────────────────────────────────────────────────────────────────


def test_ねつこうかん_ほのお技を受けるとこうげき1段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert defender.rank["A"] == 1
    assert defender.ability.revealed


def test_ねつこうかん_やけど状態にならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねつこうかん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    battle.ailment_manager.apply(target, "やけど")
    assert not target.ailment.is_active


# ──────────────────────────────────────────────────────────────────
# ねんちゃく
# ──────────────────────────────────────────────────────────────────
def test_ねんちゃく_相手による道具変更をブロックする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.can_change_item(source=source, target=target)


def test_ねんちゃく_道具なしでも相手による道具変更をブロックする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.can_change_item(source=source, target=target)


def test_ねんちゃく_自己起因の道具変更は阻害しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ねんちゃく", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, _ = battle.actives
    assert battle.can_change_item(target, target)


# ──────────────────────────────────────────────────────────────────
# ノーガード
# ──────────────────────────────────────────────────────────────────


def test_ノーガード_攻撃側で必中化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーガード", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")]
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


def test_ノーガード_防御側で必中化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーガード")]
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


# ──────────────────────────────────────────────────────────────────
# ノーマルスキン
# ──────────────────────────────────────────────────────────────────

def test_ノーマルスキン_ノーマルタイプに変えた技は強化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    result = battle.move_executor.resolve_move_type(attacker, move)
    assert result == "ノーマル"

    ctx = EventContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_ノーマルスキン_元からノーマルタイプの技は威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    ctx = EventContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


# ──────────────────────────────────────────────────────────────────
# のろわれボディ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ハードロック、フィルター、プリズムアーマー
# フィルター、プリズムアーマーの効果処理はハードロックとほぼ共通
# ただしプリズムアーマーはかたやぶりに無効化されない
# ──────────────────────────────────────────────────────────────────
def test_ハードロック_効果抜群ダメージを0_75倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="ハードロック")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


def test_ハードロック_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="ハードロック")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_プリズムアーマー_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="プリズムアーマー")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# ばけのかわ
# ──────────────────────────────────────────────────────────────────

def test_ばけのかわ_2回目以降の攻撃は防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
    )
    _, defender = battle.actives

    # ダメージ計算結果を固定
    battle.roll_damage = lambda attacker, defender, move, critical=False: 30

    # 1回目
    t.run_move(battle, 0)
    assert defender.ability.enabled is False
    assert defender.hp == defender.max_hp - defender.max_hp // 8

    # 2回目
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before - 30


def test_ばけのかわ_連続技の2発目以降は防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にどげり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
    )
    _, defender = battle.actives
    before_hp = defender.hp

    battle.roll_damage = (
        lambda attacker, defender, move, critical=False: 10
    )
    t.run_move(battle, 0)

    assert defender.ability.enabled is False
    assert defender.hp == before_hp - defender.max_hp // 8 - 10


def test_ばけのかわ_交代しても再有効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ"), Pokemon("ピカチュウ")],
    )
    # 初回被弾でばけのかわを消費
    t.run_move(battle, 0)
    assert battle.actives[1].ability.enabled is False

    # 交代して戻っても per_battle_once 特性は再有効化されない
    t.run_switch(battle, 1, 1)
    t.run_switch(battle, 1, 0)
    assert battle.actives[1].ability.enabled is False


def test_ばけのかわ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ばけのかわ")],
    )
    _, defender = battle.actives
    battle.roll_damage = (
        lambda attacker, defender, move, critical=False: 10
    )

    t.run_move(battle, 0)

    assert defender.ability.enabled is True
    assert defender.hp == defender.max_hp - 10


def test_ばけのかわ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ミミッキュ", ability_name="ばけのかわ")],
    )
    assert battle.actives[1].ability.enabled


# ──────────────────────────────────────────────────────────────────
# はっこう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# バトルスイッチ
# ──────────────────────────────────────────────────────────────────


def test_バトルスイッチ_シールドで攻撃技を使うとブレードへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == "ギルガルド(ブレード)"


def test_バトルスイッチ_シールドで変化技なら変化しない():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ", move_names=["つるぎのまい"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ギルガルド(シールド)"


def test_バトルスイッチ_ブレードでキングシールドを使うとシールドへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability_name="バトルスイッチ", move_names=["キングシールド"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.name == "ギルガルド(シールド)"


def test_バトルスイッチ_ブレードでまもるなら変化しない():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability_name="バトルスイッチ", move_names=["まもる"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ギルガルド(ブレード)"


def test_バトルスイッチ_交代時はシールドへ戻る():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability_name="バトルスイッチ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_switch(battle, 0, 1)
    assert battle.player_states[battle.players[0]].team[0].name == "ギルガルド(シールド)"


def test_バトルスイッチ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("ギルガルド(シールド)", ability_name="バトルスイッチ")],
    )
    assert battle.actives[1].ability.enabled


# ──────────────────────────────────────────────────────────────────
# ハドロンエンジン
# ──────────────────────────────────────────────────────────────────


def test_ハドロンエンジン_登場時にエレキフィールドを展開する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "initial_terrain",
    ["グラスフィールド", "サイコフィールド", "ミストフィールド"],
)
def test_ハドロンエンジン_別フィールドをエレキフィールドで上書きする(initial_terrain: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ハドロンエンジン")],
        team1=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


def test_ハドロンエンジン_エレキフィールド中に攻撃が1_33倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5461 == battle.damage_calculator.atk_modifier


def test_ハドロンエンジン_エレキフィールド以外では補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # バトル開始後にグラスフィールドで上書き
    battle.terrain_manager.apply("グラスフィールド", 5)
    assert battle.terrain.name == "グラスフィールド"
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier

# ──────────────────────────────────────────────────────────────────
# はやあし
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "やけど", "ねむり", "こおり"],
)
def test_はやあし_状態異常で素早さ1_5倍(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はやあし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, ailment_name)
    base = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base * 3 // 2


def test_はやあし_まひ状態で素早さ低下を無視して1_5倍():
    # ピカチュウはでんきタイプでまひ免疫があるためカビゴン（ノーマル）を使用
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="はやあし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")
    base = mon.stats["S"]
    # まひによる1/2ペナルティを打ち消して1.5倍（*3）
    assert battle.calc_effective_speed(mon) == (base // 2) * 3


# ──────────────────────────────────────────────────────────────────
# はやおき
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# はやてのつばさ
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# はらぺこスイッチ
# ──────────────────────────────────────────────────────────────────
def test_はらぺこスイッチ_ターン終了時にフォルムが交互に切り替わる():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability.is_hangry is False

    battle.advance_turn()
    assert mon.ability.is_hangry is True

    battle.advance_turn()
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル中はターン終了時に切り替わらない():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ", tera_type="あく")],
        team1=[Pokemon("ピカチュウ", move_names=["はねる"])],
    )
    mon = battle.actives[0]

    t.reserve_command(battle,
                      command0=Command.TERASTAL_0,
                      command1=Command.MOVE_0)
    battle.advance_turn()

    assert mon.terastallized is True
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_交代時は通常まんぷくへ戻る():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    mon.ability.is_hangry = True
    t.run_switch(battle, 0, 1)

    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル交代時はフォルム維持する():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability_name="はらぺこスイッチ", tera_type="あく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    mon.ability.is_hangry = True
    mon.terastallize()
    t.run_switch(battle, 0, 1)

    assert mon.ability.is_hangry is True

# ──────────────────────────────────────────────────────────────────
# バリアフリー
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# はりきり
# ──────────────────────────────────────────────────────────────────


def test_はりきり_物理技の攻撃補正が1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    move = attacker.moves[0]
    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move),
        4096,
    )
    assert atk_modifier == 6144

    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100 * 3277 // 4096


def test_はりきり_特殊技には補正がかからない():
    """はりきり特性: 特殊技には攻撃補正と命中率補正がかからない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    move = attacker.moves[0]
    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move),
        4096,
    )
    assert atk_modifier == 4096

    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100


def test_はりきり_一撃必殺技の命中率は下がらない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりきり", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    # 命中率ペナルティがかからない
    assert battle.move_executor.accuracy == 30


# ──────────────────────────────────────────────────────────────────
# はりこみ
# ──────────────────────────────────────────────────────────────────
def test_はりこみ_交代直後の相手への攻撃強化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="はりこみ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender_player = battle.get_player(defender)
    battle.player_states[defender_player].has_switched = True

    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        4096,
    )
    assert atk_modifier == 8192

# ──────────────────────────────────────────────────────────────────
# ばんけん
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# はんすう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ビーストブースト
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ヒーリングシフト
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ひとでなし
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("ailment_name", ["どく", "もうどく"])
def test_ひとでなし_どく系状態の相手には急所ランク最大になる(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひとでなし", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, ailment_name, source=attacker)

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        EventContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank >= 3


def test_ひとでなし_非どく状態の相手には急所ランクを変更しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひとでなし", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        EventContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank == 0


# ──────────────────────────────────────────────────────────────────
# ひひいろのこどう
# ──────────────────────────────────────────────────────────────────


def test_ひひいろのこどう_登場時にはれを展開する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == "はれ"
    assert battle.weather.count == 5
    assert battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "initial_weather", ["あめ", "すなあらし", "ゆき"]
)
def test_ひひいろのこどう_通常天候をはれで上書きする(initial_weather: Weather):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ひひいろのこどう")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == "はれ"


@pytest.mark.parametrize(
    "initial_weather", strong_weathers
)
def test_ひひいろのこどう_強天候は上書き不可(initial_weather: Weather):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="ひひいろのこどう")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    t.run_switch(battle, 0, 1)
    assert battle.weather.name == initial_weather


def test_ひひいろのこどう_はれ中に攻撃が1_33倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5461 == battle.damage_calculator.atk_modifier


def test_ひひいろのこどう_はれ以外では補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ひひいろのこどう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # バトル開始後にあめで上書き
    battle.weather_manager.apply("あめ", 5)
    assert battle.weather.name == "あめ"
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


# ──────────────────────────────────────────────────────────────────
# ビビッドボディ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# びんじょう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ファーコート
# ──────────────────────────────────────────────────────────────────

# TODO : ぼうぎょを2倍に補正することを確認するテストを追加


def test_ファーコート_かたやぶりで無効():
    """ファーコート: かたやぶり持ちの物理技はファーコートの防御補正を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ファーコート")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


# ──────────────────────────────────────────────────────────────────
# ファントムガード、マルチスケイル
# 基本的な実装は共通なため、マルチスケイルのみテストすればよい
# ファントムガードはかたやぶりに無効化されないことも検証する
# ──────────────────────────────────────────────────────────────────


def test_マルチスケイル_HP満タンのとき半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="マルチスケイル")],
    )
    attacker, defender = battle.actives

    # 1発目は半減
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier

    # 2発目は半減しない
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_マルチスケイル_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="マルチスケイル")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_ファントムガード_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ファントムガード")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# ふうりょくでんき
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ふかしのこぶし
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ぶきよう
# ──────────────────────────────────────────────────────────────────

def test_ぶきよう_アイテムが無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぶきよう", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not mon.item.enabled

    mon.hp = 1
    battle.events.emit(Event.ON_TURN_END)
    assert mon.hp == 1


# ──────────────────────────────────────────────────────────────────
# ふくがん
# ──────────────────────────────────────────────────────────────────


def test_ふくがん_命中率を1_3倍にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくがん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 100 * 5325 // 4096


def test_ふくがん_一撃必殺技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふくがん", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 30


# ──────────────────────────────────────────────────────────────────
# ふくつのこころ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ふくつのたて、ふとうのけん
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ふしぎなうろこ
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_ふしぎなうろこ_状態異常でB上昇(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("コラッタ", ability_name="ふしぎなうろこ")],
    )
    battle.ailment_manager.apply(battle.actives[1], ailment_name)
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_ふしぎなうろこ_かたやぶりで無効():
    """ふしぎなうろこ: かたやぶり持ちの物理技はふしぎなうろこの防御補正を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="ふしぎなうろこ")],
    )
    battle.ailment_manager.apply(battle.actives[1], "やけど")
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


# ──────────────────────────────────────────────────────────────────
# ふしょく
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "target_name",
    ["フシギダネ", "コイル"],  # くさ/どくタイプ、でんき/はがねタイプ
)
def test_ふしょく持ち由来ならどく免疫タイプにもどくが入る(target_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふしょく")],
        team1=[Pokemon(target_name)],
    )
    source = battle.actives[0]
    target = battle.actives[1]

    assert battle.ailment_manager.apply(target, "どく", source=source)
    assert target.ailment.name == "どく"


# ──────────────────────────────────────────────────────────────────
# ふゆう
# ──────────────────────────────────────────────────────────────────


def test_ふゆう_floating():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]
    floating = battle.events.emit(
        Event.ON_CHECK_FLOATING,
        EventContext(source=mon),
        False
    )
    assert floating is True


def test_ふゆう_じめん技が通らない():
    """ふゆう: ふゆう持ちはじめん技を無効化できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp


def test_ふゆう_かたやぶりでじめん技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ふゆう")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp

# ──────────────────────────────────────────────────────────────────
# フラワーギフト
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# フラワーベール
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ブレインフォース
# ──────────────────────────────────────────────────────────────────


def test_ブレインフォース_効果抜群のとき強化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ブレインフォース", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ")],
    )
    t.run_move(battle, 0)
    assert 5120 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# プレッシャー
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ヘヴィメタル、ライトメタル
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ヘドロえき
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# へんげんじざい、リベロ
# 共通実装なのでへんげんじざいのみテストすればよい
# ──────────────────────────────────────────────────────────────────

def test_へんげんじざい_同一滞在で1回のみ発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="へんげんじざい", move_names=["たいあたり", "ひのこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert attacker.types == ["ノーマル"]

    t.run_move(battle, 0, 1)
    assert attacker.types == ["ノーマル"]


def test_へんげんじざい_交代でリセットされ再発動できる():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="へんげんじざい", move_names=["たいあたり", "ひのこ"]),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert mon.types == ["ノーマル"]

    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    t.run_move(battle, 0, 1)

    assert mon.types == ["ほのお"]


# ──────────────────────────────────────────────────────────────────
# へんしょく
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ポイズンヒール
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく"]
)
def test_ポイズンヒール_どく系状態で1_8回復する(ailment_name: str):
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability_name="ポイズンヒール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, ailment_name)
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END)
    assert mon.hp == before + mon.max_hp // 8


def test_ポイズンヒール_かいふくふうじ中は回復もダメージも受けない():
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability_name="ポイズンヒール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    battle.volatile_manager.apply(mon, "かいふくふうじ")
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))
    assert mon.hp == before


# ──────────────────────────────────────────────────────────────────
# ぼうおん、ぼうだん
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("ぼうおん", "バークアウト"),
        ("ぼうだん", "かえんボール"),
    ],
)
def test_ぼうおん系_技を無効化する(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", move_names=[move_name])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp
    assert defender.ability.revealed is True


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("ぼうおん", "バークアウト"),
        ("ぼうだん", "かえんボール"),
    ],
)
def test_ぼうおん系_かたやぶりで無効(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=[move_name])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp
    assert defender.ability.revealed is False


# ──────────────────────────────────────────────────────────────────
# ぼうじん
# ──────────────────────────────────────────────────────────────────


def test_ぼうじん_粉技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぼうじん")],
        team1=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert not defender.ailment.is_active
    assert defender.ability.revealed is True


# ──────────────────────────────────────────────────────────────────
# ほおぶくろ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ほうし
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ほろびのボディ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# マイティチェンジ
# ──────────────────────────────────────────────────────────────────


def test_マイティチェンジ_ナイーブで交代するとマイティへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = battle.player_states[player].team[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "イルカマン(マイティ)"


def test_マイティチェンジ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("イルカマン(ナイーブ)", ability_name="マイティチェンジ")],
    )
    assert battle.actives[1].ability.enabled


# ──────────────────────────────────────────────────────────────────
# マジシャン
# ──────────────────────────────────────────────────────────────────
# TODO : テスト追加

# ──────────────────────────────────────────────────────────────────
# マジックガード
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "reason, result",
    [
        ("move_damage", True),
        ("self_attack", True),
        ("pain_split", True),
        ("self_cost", True),
        ("", False),
    ],
)
def test_マジックガード_HPChangeReasonごとの挙動(reason: str, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    delta = battle.modify_hp(mon, v=-10, reason=reason)
    assert bool(delta) == result


# ──────────────────────────────────────────────────────────────────
# マジックミラー
# ──────────────────────────────────────────────────────────────────
def test_マジックミラー_変化技を跳ね返す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ニャース", ability_name="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.rank["A"] == -1
    assert defender.rank["A"] == 0


# ──────────────────────────────────────────────────────────────────
# マルチタイプ
# ──────────────────────────────────────────────────────────────────


MULTI_TYPE_PLATE_CASES = [
    (plate_item_name, expected_type)
    for plate_item_name, expected_type in PLATE_TO_TYPE.items()
    if plate_item_name in ITEMS
]


@pytest.mark.parametrize("plate_item_name, expected_type", MULTI_TYPE_PLATE_CASES)
def test_マルチタイプ_プレートで対応タイプになる(plate_item_name: str, expected_type: str):
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ", item_name=plate_item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == expected_type
    assert mon.ability.revealed is False  # マルチタイプは開示されない


def test_マルチタイプ_プレートなしでタイプ変更なし():
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None
    assert mon.ability.revealed is False  # プレートなしは不発なので False


def test_マルチタイプ_プレートの奪取を阻止する():
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability_name="マルチタイプ", item_name="せいれいプレート")],
        team1=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    # ON_CHECK_ITEM_CHANGE: target=アルセウス, source=ピカチュウ → 奪取を阻止
    ctx = EventContext(attacker=attacker, defender=mon, move=attacker.moves[0],
                       source=attacker, target=mon)
    result = battle.events.emit(Event.ON_CHECK_ITEM_CHANGE, ctx, True)
    assert result is False


def test_マルチタイプ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
        team1=[Pokemon("アルセウス", ability_name="マルチタイプ")],
    )
    assert battle.actives[1].ability.enabled


# ──────────────────────────────────────────────────────────────────
# ミイラ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ミラーアーマー
# ──────────────────────────────────────────────────────────────────


def test_ミラーアーマー_能力低下のみ反射する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ")],
    )
    ally, foe = battle.actives
    stats = {"A": -1, "B": +1, "C": -2}
    battle.modify_stats(ally, stats, source=foe)
    assert ally.rank["A"] == 0
    assert ally.rank["B"] == 1
    assert ally.rank["C"] == 0
    assert foe.rank["A"] == -1
    assert foe.rank["B"] == 0
    assert foe.rank["C"] == -2


def test_ミラーアーマー_自己能力低下は反射しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
    )
    target, source = battle.actives
    battle.modify_stats(target, {"A": -1}, source=target)
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[1].rank["A"] == 0


def test_ミラーアーマー_かたやぶりで反射されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[1].rank["A"] == 0


def test_ミラーアーマー_反射により相手のかちきが発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability_name="かちき")],
    )
    ally, foe = battle.actives
    battle.modify_stats(ally, {"A": -1}, source=foe)
    assert ally.rank["A"] == 0
    assert foe.rank["A"] == -1
    assert foe.rank["C"] == 2


# ──────────────────────────────────────────────────────────────────
# ミラクルスキン
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ムラっけ
# ──────────────────────────────────────────────────────────────────


def test_ムラっけ_ターン終了時に別々の能力が上昇と下降する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    choices = iter(["A", "B"])
    battle.random.choice = lambda seq: next(choices)

    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))

    assert mon.rank["A"] == 2
    assert mon.rank["B"] == -1


def test_ムラっけ_全能力が最大なら下降のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("A", "B", "C", "D", "S"):
        mon.rank[stat] = 6
    battle.random.choice = lambda seq: seq[0]

    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))

    assert mon.rank["A"] == 5
    assert mon.rank["B"] == 6


def test_ムラっけ_全能力が最小なら上昇のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("A", "B", "C", "D", "S"):
        mon.rank[stat] = -6
    battle.random.choice = lambda seq: seq[0]

    battle.events.emit(Event.ON_TURN_END, EventContext(source=mon))

    assert mon.rank["A"] == -4
    assert mon.rank["B"] == -6


# ──────────────────────────────────────────────────────────────────
# メロメロボディ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ものひろい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# もふもふ
# ──────────────────────────────────────────────────────────────────


def test_もふもふ_接触技を半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_もふもふ_ほのお技を倍加():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.damage_modifier


def test_もふもふ_ほのお接触技は等倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# もらいび
# ──────────────────────────────────────────────────────────────────

def test_もらいび_吸収後は最初の炎技のみ1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もらいび", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
    )
    defender, attacker = battle.actives

    # もらいびでひのこを吸収してチャージ状態へ
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp
    assert defender.ability.state == "charged"
    assert defender.ability.revealed

    # もらいびのチャージ状態でひのこを使うと1.5倍
    t.run_move(battle, 0)
    assert defender.ability.state == "idle"
    assert battle.damage_calculator.power_modifier == 6144

    # 2回目: idle なので等倍
    t.run_move(battle, 0)
    assert defender.ability.state == "idle"
    assert battle.damage_calculator.power_modifier == 4096


def test_もらいび_自分対象技では相手の吸収特性は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かえんのまもり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もらいび")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.has_volatile("かえんのまもり")
    assert defender.ability.state == "idle"


def test_もらいび_かたやぶりには貫通される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="もらいび")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ひのこ"])],
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp
    assert defender.ability.state == "idle"
    assert defender.ability.revealed is False


# ──────────────────────────────────────────────────────────────────
# ゆうばく
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# よちむ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# よわき
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("move_name", ["でんきショック", "たいあたり"])
def test_よわき_HP半分以下で攻撃補正0_5倍(move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よわき", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier


# ──────────────────────────────────────────────────────────────────
# リーフガード
# ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "weather",
    [None, ("あめ", 5), ("すなあらし", 5), ("ゆき", 5)],
)
def test_リーフガード_はれ以外では発動しない(weather):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=weather,
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.is_active


@pytest.mark.parametrize("weather_name,weather_count", [("はれ", 5), ("おおひでり", 999)])
@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_リーフガード_はれおおひでり中に状態異常を防ぐ(weather_name: str, weather_count: int, ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, ailment_name)
    assert not mon.ailment.is_active


# ──────────────────────────────────────────────────────────────────
# リミットシールド
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# りんぷん
# ──────────────────────────────────────────────────────────────────


def test_りんぷん_追加効果確率を0にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.is_active is False


def test_りんぷん_かたやぶりで無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


# ──────────────────────────────────────────────────────────────────
# わざわいのうつわ、わざわいのおふだ、わざわいのたま、わざわいのつるぎ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのおふだ", "たいあたり"),
        ("わざわいのうつわ", "ひのこ"),
    ],
)
def test_わざわい_相手攻撃補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.atk_modifier


def test_わざわいのおふだ_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わざわいのおふだ")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのつるぎ", "たいあたり"),
        ("わざわいのたま", "ひのこ"),
    ],
)
def test_わざわい_相手防御補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.def_modifier

# ──────────────────────────────────────────────────────────────────
# わたげ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# わるいてぐせ
# ──────────────────────────────────────────────────────────────────
# TODO : テスト実装


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
