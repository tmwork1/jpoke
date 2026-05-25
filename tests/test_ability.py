"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle

import pytest


from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event, Interrupt, Command
from jpoke.utils.type_defs import Stat, AilmentName, VolatileName
from jpoke.model import Move

import test_utils as t


# ──────────────────────────────────────────────────────────────────
# ARシステム
# ──────────────────────────────────────────────────────────────────


def test_ARシステム_フェアリーメモリでフェアリータイプになる():
    # TODO : パラメタライズで全アイテムをテストする
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability="ARシステム", item="フェアリーメモリ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == "フェアリー"
    assert mon.ability.revealed is False  # ARシステムは開示されない


def test_ARシステム_メモリなしでタイプ変更なし():
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability="ARシステム")],
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

# TODO アイスボディもパラメタライズでまとめてテストする

@pytest.mark.parametrize(
    "weather_name,weather_count",
    [
        ("あめ", 5),
        ("おおあめ", 999),
    ]
)
def test_あめうけざら_あめ中に回復(weather_name: str, weather_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability="あめうけざら")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.emit_turn_end_events(battle)
    assert mon.hp == 1 + mon.max_hp // 16


def test_あめうけざら_あめ以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability="あめうけざら")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    t.emit_turn_end_events(battle)
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
        team0=[Pokemon("ピカチュウ", moves=[move_name])],
        team1=[Pokemon("ピカチュウ", ability=ability_name)],
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
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=[move_name])],
        team1=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier

# ──────────────────────────────────────────────────────────────────
#  あとだし
# ──────────────────────────────────────────────────────────────────


def test_あとだし_同優先度で最後に行動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="あとだし")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle)
    order = battle.calc_action_order()
    assert order[-1] == battle.actives[0]


def test_あとだし_高優先度技は先攻():
    """あとだし: 相手より優先度が高い技を使用した場合は先攻になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="あとだし", moves=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    t.reserve_command(battle)
    order = battle.calc_action_order()
    assert order[0] == battle.actives[0]


def test_あとだし_トリックルームでも後攻():
    """あとだし: トリックルーム状態でも最後に行動する（素早さ逆転の影響を受けない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="あとだし")],
        team1=[Pokemon("ピカチュウ")],
        field={"トリックルーム": 5},
    )
    t.reserve_command(battle)
    order = battle.calc_action_order()
    assert order[-1] == battle.actives[0]

# ──────────────────────────────────────────────────────────────────
#  アナライズ
# ──────────────────────────────────────────────────────────────────
# TODO : テスト実装

# ──────────────────────────────────────────────────────────────────
#  あまのじゃく
# ──────────────────────────────────────────────────────────────────
# TODO : テスト実装。たんじゅんを参考にするとよい

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
        team0=[Pokemon("ピカチュウ", ability=ability_name)],
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
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="あめふらし")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "あめ"


@pytest.mark.parametrize(
    "initial_weather", strong_weathers
)
def test_あめふらし_強天候は上書き不可(initial_weather: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="あめふらし")],
        team1=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 99),
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == initial_weather


@pytest.mark.parametrize(
    "weather_name",
    normal_weathers + ["おおあめ"]
)
def test_おわりのだいち_らんきりゅう以外上書きする(weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="おわりのだいち")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "おおひでり"


def test_おわりのだいち_らんきりゅうは上書きできない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="おわりのだいち")],
        team1=[Pokemon("ピカチュウ")],
        weather=("らんきりゅう", 1),
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "らんきりゅう"


@pytest.mark.parametrize(
    "weather_name",
    weathers
)
def test_らんきりゅう_すべての天候を上書きする(weather_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="デルタストリーム")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 99)
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
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
        team0=[Pokemon("ピカチュウ", ability=ability_name), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
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
        team0=[Pokemon("ピカチュウ", ability=ability_name), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == weather_name


# ──────────────────────────────────────────────────────────────────
# 交代抑制
# ありじごく、かげふみ、じりょく
# ──────────────────────────────────────────────────────────────────

# TODO : 3特性の交代不可条件をリスト化してパラメタライズでまとめてテストする
# TODO : 3特性の交代可能条件をリスト化してパラメタライズでまとめてテストする

def test_ありじごく_交代不可():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="ありじごく")],
    )
    assert not t.can_switch(battle, 0)


def test_ありじごく_飛行タイプは交代可能():
    battle = t.start_battle(
        team0=[Pokemon("ピジョン"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="ありじごく")],
    )
    assert t.can_switch(battle, 0)


def test_ありじごく_ふゆうは交代可能():
    # TODO : 実装
    pass


def test_かげふみ_かげふみ持ち以外は交代不可():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="かげふみ")],
    )
    assert not t.can_switch(battle, 0)


def test_かげふみ_かげふみ持ちは交代可能():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かげふみ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="かげふみ"), Pokemon("ピカチュウ")],
    )
    assert t.can_switch(battle, 0)
    assert t.can_switch(battle, 1)


def test_じりょく_はがねタイプは交代不可():
    battle = t.start_battle(
        team0=[Pokemon("コイル"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="じりょく")],
    )
    assert not t.can_switch(battle, 0)


def test_じりょく_はがねタイプ以外は交代可能():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="じりょく")],
    )
    assert t.can_switch(battle, 0)


def test_ゴーストタイプは交代可能():
    # TODO ありじごく、かげふみ、じりょくをまとめてパラメタライズでテスト実装
    # 相手役はギルガルド
    pass


# ──────────────────────────────────────────────────────────────────
# 状態異常・揮発状態耐性
# アロマベール、スイートベール、どんかん、マイペース
# ──────────────────────────────────────────────────────────────────
# 特性と耐性のある揮発状態をリスト化し、パラメタライズでまとめてテストする

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
        team0=[Pokemon("ピカチュウ", ability=ability)],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.volatile_manager.apply(battle.actives[0], volatile) == result


# TODO : かたやぶりで無効化されるテストを追加 (技実装後)

# ──────────────────────────────────────────────────────────────────
#  いかく
# ──────────────────────────────────────────────────────────────────


def test_いかく_登場時に相手攻撃1段階ダウン():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="いかく")],
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
        team0=[Pokemon("ゴンベ", ability="いしあたま", moves=["すてみタックル"])],
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
        team0=[Pokemon("ピカチュウ", ability="いたずらごころ", moves=["でんじは"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    assert attacker.moves[0].priority == 0
    assert battle.speed_calculator.calc_move_priority(attacker, attacker.moves[0]) == 1


def test_いたずらごころ_あくタイプ相手には変化技が無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="いたずらごころ", moves=["でんじは"])],
        team1=[Pokemon("ヘルガー")],
    )
    ctx = t.build_context(battle, atk_idx=0)
    assert not battle.events.emit(Event.ON_BEFORE_APPLY_MOVE, ctx, True)


# TODO : 無効判定をするイベントを発火して、戻り値を直接検証するようにテストを修正
def test_いたずらごころ_自己対象の変化技はあくタイプ相手でも成功する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="いたずらごころ", moves=["かえんのまもり"])],
        team1=[Pokemon("ヘルガー")],
    )
    attacker = battle.actives[0]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert attacker.has_volatile("かえんのまもり")


# ──────────────────────────────────────────────────────────────────
#  いろめがね
# ──────────────────────────────────────────────────────────────────


def test_いろめがね_いまひとつのダメージが2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="いろめがね", moves=["むしのていこう"])],
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
        team0=[Pokemon("ピカチュウ", ability=ability_name, moves=[move_name])],
        team1=[Pokemon("ピカチュウ")],
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
# TODO すべての天候・強天候を無効化できることを確認するようにパラメタライズ化


def test_エアロック():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="エアロック")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    assert battle.weather.name == ""


def test_エアロック_すなあらしのターン終了ダメージが無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="エアロック")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    battle.events.emit(Event.ON_TURN_END_5, None, None)
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
        team0=[Pokemon("ピカチュウ", ability=ability_name)],
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
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability=ability_name)],
        team1=[Pokemon("ピカチュウ")],
        terrain=(terrain_name, 2)
    )
    # TODO 控えのピカチュウに指定特性を付与すれば交代1回でテストできる
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
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
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="エレキメイカー")],
        team1=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 99),
    )
    mon = battle.players[0].team[1]
    battle.switch_manager.run_switch(battle.players[0], mon)
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
        team0=[Pokemon("ピカチュウ", moves=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    battle.print_logs()
    assert battle.move_executor.move_applied is False
    assert battle.actives[1].ability.revealed is True


def test_おうごんのからだ_攻撃技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        team1=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True
    assert battle.actives[1].ability.revealed is False


def test_おうごんのからだ_自分対象の変化技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["つるぎのまい"])],
        team1=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_場が対象の技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["にほんばれ"])],
        team1=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    battle.print_logs()
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability="おうごんのからだ")],
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
        team0=[Pokemon("ピカチュウ", ability="おやこあい", moves=["アクアステップ"])],
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
        team0=[Pokemon("ピカチュウ", ability="おやこあい", moves=["すいりゅうれんだ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    battle.run_move(attacker, move)
    assert defender.hits_taken == 3


# ──────────────────────────────────────────────────────────────────
#  カーリーヘア
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# かいりきバサミ、はとむね
# ──────────────────────────────────────────────────────────────────
# TODO パラメタライズで統合する
# TODO はとむねは防御低下を防ぐ


def test_かいりきバサミ_こうげき低下のみ防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability="かいりきバサミ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stat_change = battle.modify_stats(
        mon0,
        {"A": -1, "B": -1, "C": -2},
        source=mon1,
    )
    assert stat_change == {"B": -1, "C": -2}


def test_かいりきバサミ_自己低下は防げない():
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability="かいりきバサミ")],
        team1=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=ally_mon),
        {"A": -1},
    )
    assert stat_change == {"A": -1}


def test_かいりきバサミ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability="かいりきバサミ")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1


# ──────────────────────────────────────────────────────────────────
#  かがくへんかガス
# ──────────────────────────────────────────────────────────────────


def test_かがくへんかガス_登場時に相手の特性を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
        team1=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert not battle.actives[1].ability.enabled
    assert not battle.actives[1].ability.revealed
    assert battle.actives[0].rank["A"] == 0


def test_かがくへんかガス_解除後は特性が再び有効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かがくへんかガス"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="いかく")],
    )
    player = battle.players[0]
    battle.switch_manager.run_switch(player, player.team[1])
    assert battle.actives[1].ability.enabled
    assert battle.actives[1].ability.revealed
    assert battle.actives[0].rank["A"] == 0

# TODO : かがくへんかガスでかがくへんかガスを無効化できないテストを追加

# ──────────────────────────────────────────────────────────────────
#  かぜのり
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  かそく
# ──────────────────────────────────────────────────────────────────


def test_かそく_行動後のターン終了時に素早さが上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かそく")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["S"] == 0

    mon.executed_move = mon.moves[0]
    battle.events.emit(Event.ON_TURN_END_5)
    assert mon.rank["S"] == 1


def test_かそく_交代直後のターンは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="かそく", moves=["でんきショック"])],
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
# TODO パラメタライズでまとめてテストする


def test_かたいツメ_接触技のみ威力補正1_3倍():
    battle_contact = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたいツメ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle_contact, 0)
    assert 5325 == battle_contact.damage_calculator.power_modifier

    battle_non_contact = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたいツメ", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle_non_contact, 0)
    assert 4096 == battle_non_contact.damage_calculator.power_modifier


def test_がんじょうあご_かみつき技で威力補正1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="がんじょうあご", moves=["かみつく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_きれあじ_きる技は威力補正1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="きれあじ", moves=["きりさく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_きれあじ_きる技以外は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="きれあじ", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_てつのこぶし_パンチ技以外は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_てつのこぶし_パンチ技威力補正():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["かみなりパンチ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4915 == battle.damage_calculator.power_modifier


def test_パンクロック_音技で威力1_3倍かつ被ダメ0_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="パンクロック", moves=["バークアウト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier

    battle2 = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability="パンクロック", moves=["バークアウト"])],
    )
    t.run_move(battle2, 0)
    assert 2048 == battle2.damage_calculator.damage_modifier


def test_パンクロック_かたやぶりで音技軽減が無効化される():
    """パンクロック: かたやぶり持ちの音技はパンクロックの被ダメ軽減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["バークアウト"])],
        team1=[Pokemon("ピカチュウ", ability="パンクロック")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# かたやぶり、ターボブレイズ、テラボルテージ
# ターボブレイズ、テラボルテージはかたやぶりと共通実装のためテスト不要
# ──────────────────────────────────────────────────────────────────


def test_かたやぶり_場に出たときに特性開示():
    # TODO 実装。abilility.revealedになっているか検証
    pass


# ──────────────────────────────────────────────────────────────────
# 能力低下カウンター
# かちき、まけんき
# ──────────────────────────────────────────────────────────────────
# TODO パラメタライズしてテストを統合


def test_かちき_相手由来の能力低下で発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かちき")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon, foe = battle.actives
    battle.modify_stat(mon, "A", -1, source=foe)
    assert mon.rank["C"] == 2


def test_かちき_自分由来の能力低下では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かちき")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_stat(mon, "A", -1, source=mon)
    assert mon.rank["C"] == 0


def test_かちき_いかくで特攻2段階アップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かちき")],
        team1=[Pokemon("ピカチュウ", ability="いかく")],
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
        team0=[Pokemon("ピカチュウ", ability="カブトアーマー")],
        team1=[Pokemon("ピカチュウ", moves=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is False


def test_カブトアーマー_かたやぶり攻撃では無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="カブトアーマー")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["トリックフラワー"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.critical is True


# ──────────────────────────────────────────────────────────────────
# かるわざ
# ──────────────────────────────────────────────────────────────────


def test_かるわざ_アイテムを失うと素早さが2倍になる():
    # TODO : battle.item_manager.lose_item()で直接アイテムを失わせるように修正
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かるわざ", item="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.consume_item(mon)
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_かるわざ_アイテムを再取得すると発動しない():
    # TODO : battle.item_manager.lose_item()で直接アイテムを失わせるように修正
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かるわざ", item="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.consume_item(mon)
    battle.set_item(mon, "オボンのみ")
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_かるわざ_アイテムを失ってから再入場しても発動しない():
    # TODO : battle.item_manager.lose_item()で直接アイテムを失わせるように修正
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かるわざ", item="オボンのみ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.consume_item(mon)
    battle.run_switch(battle.players[0], battle.players[0].team[1])
    battle.run_switch(battle.players[0], battle.players[0].team[0])
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_かるわざ_入場時にアイテムなしなら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かるわざ")],
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
        team0=[Pokemon("コイル", ability="がんじょう")],
        team1=[Pokemon("ガブリアス", moves=["じしん"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == 1
    assert defender.ability.revealed


def test_がんじょう_一撃必殺技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="がんじょう")],
        team1=[Pokemon("ピカチュウ", moves=["じわれ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.move_executor.move_applied is False


# TODO : かたやぶりによる攻撃ではHP 1で耐えないことを確認するテストを追加

def test_がんじょう_かたやぶりにで一撃技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="がんじょう")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じわれ"])],
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
    # TODO : この場合は行動前に交代が発生するため、交代先のポケモンが行動できないことも確認する
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability="ききかいひ"),
            Pokemon("ピカチュウ", moves=["たいあたり"])
        ],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    damage = defender.max_hp - defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: damage

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert battle.players[0].interrupt == Interrupt.EMERGENCY

    battle.run_interrupt_switch(Interrupt.EMERGENCY)

    assert battle.players[0].active_idx == 1


def test_ききかいひ_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    defender.hp = defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: 1

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert battle.players[0].interrupt == Interrupt.NONE
    assert battle.players[0].active_idx == 0


def test_ききかいひ_やけどダメージでも発動する():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    mon.hp = mon.max_hp // 2 + 1
    battle.ailment_manager.apply(mon, "やけど")
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))

    assert battle.players[0].interrupt == Interrupt.EMERGENCY


def test_ききかいひ_こんらん自傷では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("コソクムシ", ability="ききかいひ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")

    assert battle.players[0].interrupt == Interrupt.NONE


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
        team0=[Pokemon("ピカチュウ", ability="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender, attacker = battle.actives
    defender.hp = defender.max_hp // 2 + 2
    t.run_move(battle, 1)

    assert defender.hp <= defender.max_hp // 2
    assert defender.rank["C"] == 1
    assert defender.ability.revealed is True


def test_ぎゃくじょう_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ぎゃくじょう")],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    defender.hp = defender.max_hp // 2
    battle.roll_damage = lambda *_args, **_kwargs: 1

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["C"] == 0


# ──────────────────────────────────────────────────────────────────
#  きゅうばん
# ──────────────────────────────────────────────────────────────────
# TODO : 実装

# ──────────────────────────────────────────────────────────────────
# きょううん
# ──────────────────────────────────────────────────────────────────


def test_きょううん_急所ランクが1上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="きょううん", moves=["つじぎり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=move),
        0,
    )
    assert result == 1


# ──────────────────────────────────────────────────────────────────
# ぎょぐん
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# きよめのしお
# ──────────────────────────────────────────────────────────────────
# TODO ゴーストわざ半減のテストを実装
# TODO すべての状態異常無効のテストを実装 (パラメタライズ)


# ──────────────────────────────────────────────────────────────────
# きんしのちから
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# きんちょうかん
# ──────────────────────────────────────────────────────────────────
def test_きんちょうかん_相手をきんちょうかん状態にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability="きんちょうかん")],
    )
    assert battle.query_manager.is_nervous(battle.actives[0])
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

# TODO : こだいかっせいもパラメタライズでまとめてテストする


def test_クォークチャージ_場条件なしならブーストエナジーを消費する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="クォークチャージ", item="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item("ブーストエナジー")


@pytest.mark.parametrize(
    "name, stat, modifier",
    [
        ("スピアー", "A", 5325),
        ("ゼニガメ", "B", 5325),
        ("フシギダネ", "C", 5325),
        ("カメックス", "D", 5325),
        ("ピカチュウ", "S", 6144),
    ]
)
def test_クォークチャージ_最大ステータスがバフされる(name, stat, modifier):
    battle = t.start_battle(
        team0=[Pokemon(name, ability="クォークチャージ", item="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat == stat
    # TODO : 補正量の検証を追加


def test_こだいかっせい_はれ中はブーストエナジー未消費_解除後に消費発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="こだいかっせい", item="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ", ability="ひでり")],
    )
    mon = battle.actives[0]

    assert mon.paradox_boost_source == "weather"
    assert mon.has_item("ブーストエナジー")

    battle.weather_manager.remove()

    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item("ブーストエナジー")


def test_クォークチャージ_エレキフィールド下ではブーストエナジー未消費_解除後に消費発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="クォークチャージ", item="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ", ability="エレキメイカー")],
    )
    mon = battle.actives[0]

    assert mon.paradox_boost_source == "terrain"
    assert mon.has_item("ブーストエナジー")

    battle.terrain_manager.remove()

    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item("ブーストエナジー")


# ──────────────────────────────────────────────────────────────────
# くさのけがわ
# ──────────────────────────────────────────────────────────────────


def test_くさのけがわ_():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="くさのけがわ")],
        terrain=("グラスフィールド", 5)
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_くさのけがわ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="くさのけがわ")],
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
        team0=[Pokemon("ピカチュウ", ability="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, mon1 = battle.actives
    stats = {"A": -1, "B": +1, "C": -3, "D": +3, "S": -5, "ACC": +5, "EVA": -6}
    expected = {k: v for k, v in stats.items() if v > 0}

    assert expected == battle.modify_stats(mon0, stats, source=mon1)


def test_クリアボディ_自己低下技は防げない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="クリアボディ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon0, _ = battle.actives
    stats = {"A": -1, "B": +1, "C": -3, "D": +3, "S": -5, "ACC": +5, "EVA": -6}
    expected = stats

    assert expected == battle.modify_stats(mon0, stats, source=mon0)


def test_クリアボディ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="クリアボディ")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1


def test_メタルプロテクト_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="メタルプロテクト")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == 0


# ──────────────────────────────────────────────────────────────────
# 倒すと能力上昇
# くろのいななき、しろのいななき、じしんかじょう
# ──────────────────────────────────────────────────────────────────
# TODO パラメタライズで他の特性もまとめてテストする
def test_じしんかじょう_相手を倒すと攻撃1段階上昇する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="じしんかじょう", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.fainted
    assert attacker.rank["A"] == 1


def test_じしんかじょう_相手を倒せないと発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="じしんかじょう", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert not defender.fainted
    assert attacker.rank["A"] == 0


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
        team0=[Pokemon("ピカチュウ", ability=ability_name, moves=[move_name])],
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
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_こおりのりんぷん_物理技のダメージ半減しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_こおりのりんぷん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
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
        team0=[Pokemon("ピカチュウ", moves=[move])],
        team1=[Pokemon("ピカチュウ", ability=ability)],
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
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=[move])],
        team1=[Pokemon("ピカチュウ", ability=ability)],
    )
    attacker, defender = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.hp < defender.max_hp
    assert defender.rank[stat] == 0


# ──────────────────────────────────────────────────────────────────
# こんじょう
# ──────────────────────────────────────────────────────────────────
# 全ての状態異常について、パラメタライズでまとめてテストする
def test_こんじょう_状態異常で攻撃1_5倍かつやけど半減を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="こんじょう", moves=["たいあたり"])],
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
        team0=[Pokemon("ヤドン", ability="さいせいりょく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.hp == 1 + mon.max_hp // 3


def test_さいせいりょく_かいふくふうじ中でも回復する():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability="さいせいりょく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"かいふくふうじ": 99}
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.hp == 1 + mon.max_hp // 3


# ──────────────────────────────────────────────────────────────────
# さまようたましい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# さめはだ、てつのトゲ
# てつのトゲの実装はさめはだと共通のためテスト不要
# ──────────────────────────────────────────────────────────────────


# TODO : 技と予想されるダメージをリスト化してパラメタライズで実装
def test_さめはだ_接触ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="さめはだ")],
        team1=[Pokemon("イーブイ", moves=["たいあたり"])],
    )
    defender, attacker = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 8


def test_さめはだ_非接触技では反撃ダメージを与えない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="さめはだ")],
        team1=[Pokemon("イーブイ", moves=["はどうだん"])],
    )
    defender, attacker = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert attacker.hp == attacker.max_hp


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
        team0=[Pokemon("ピカチュウ", ability="サンパワー", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_サンパワー_物理技は補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="サンパワー", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_サンパワー_はれ中にターン終了時1_8ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="サンパワー")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    t.emit_turn_end_events(battle)
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp - mon.max_hp // 8


def test_サンパワー_はれ以外ではターン終了時ダメージなし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="サンパワー")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.emit_turn_end_events(battle)
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp


# ──────────────────────────────────────────────────────────────────
# じきゅうりょく
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# しぜんかいふく
# ──────────────────────────────────────────────────────────────────

# TODO : t.start_battle()にally_ailment / foe_ailmentオプションを追加して、テストコードの再現性を上げる


def test_しぜんかいふく_交代時に状態異常回復():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="しぜんかいふく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.is_active
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert not mon.ailment.is_active


# ──────────────────────────────────────────────────────────────────
# しめりけ
# ──────────────────────────────────────────────────────────────────


def test_しめりけ_じばくを失敗させる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["じばく"])],
        team1=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_しめりけ_自分の爆発技も失敗させる():
    battle = t.start_battle(
        team0=[Pokemon("ニョロモ", ability="しめりけ", moves=["じばく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_しめりけ_爆発ラベルなし技は通す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


def test_しめりけ_かたやぶりで爆発技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じばく"])],
        team1=[Pokemon("ニョロモ", ability="しめりけ")],
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
# TODO : 上記の特性を網羅する
# TODO : パラメタライズでまとめてテストする

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
        team0=[Pokemon("ピカチュウ", ability=ability)],
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
        # ("マグマのよろい", "こおり", ""), # TODO: data/move.pyに100%で相手をこおり状態にするダミー技を追加する
    ],
)
def test_状態異常無効_かたやぶりで無効(ability: str, ailment: AilmentName, move: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability=ability)],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=[move])],
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
# TODO : パラメタライズでまとめてテストする
def test_すなかき_すなあらしで素早さ2倍():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", ability="すなかき")],
                            weather=("すなあらし", 999),
                            )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_すなかき_すなあらし以外では素早さ据え置き():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="すなかき")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_すいすい_あめで素早さ2倍():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", ability="すいすい")],
                            weather=("あめ", 999),
                            )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_すいすい_あめ以外では素早さ据え置き():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="すいすい")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_ようりょくそ_はれで素早さ2倍():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", ability="ようりょくそ")],
                            weather=("はれ", 999),
                            )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_ようりょくそ_はれ以外では素早さ据え置き():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ようりょくそ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_ゆきかき_ゆきで素早さ2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ゆきかき")],
        team1=[Pokemon("ピカチュウ")],
        weather=("ゆき", 5),
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_ゆきかき_ゆき以外では素早さ据え置き():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ゆきかき")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


# ──────────────────────────────────────────────────────────────────
# すいほう
# ──────────────────────────────────────────────────────────────────
def test_すいほう_みず技強化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="すいほう", moves=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_すいほう_ほのお技弱化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="すいほう")],
        team1=[Pokemon("ピカチュウ", moves=["ひのこ"])],
    )
    t.run_move(battle, 1)
    assert 2048 == battle.damage_calculator.atk_modifier


# ──────────────────────────────────────────────────────────────────
# スキン
# スカイスキン、フェアリースキン、フリーズスキン
# ──────────────────────────────────────────────────────────────────
# TODO : パラメタイズでまとめてテストする


def test_スカイスキン_ノーマル技をひこうタイプに変換する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.resolve_move_type(attacker, move)
    assert result == "ひこう"


def test_スカイスキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_スカイスキン_元からひこうタイプの技は威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["アクロバット"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


def test_フェアリースキン_ノーマル技をフェアリータイプに変換する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.resolve_move_type(attacker, move)
    assert result == "フェアリー"


def test_フェアリースキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_フェアリースキン_元からフェアリータイプの技は威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["じゃれつく"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


# フリーズスキン

def test_フリーズスキン_ノーマル技をこおりタイプに変換する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.resolve_move_type(attacker, move)
    assert result == "こおり"


def test_フリーズスキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_フリーズスキン_元からこおりタイプの技は威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["アイススピナー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


# ──────────────────────────────────────────────────────────────────
# スキルリンク
# ──────────────────────────────────────────────────────────────────
# TODO : テスト実装

# ──────────────────────────────────────────────────────────────────
# スナイパー
# ──────────────────────────────────────────────────────────────────
def test_スナイパー_急所時の最終ダメージを1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="スナイパー", moves=["トリックフラワー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.crit_rank == 3
    assert 6144 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# すながくれ、ゆきがくれ
# ──────────────────────────────────────────────────────────────────
# TODO : すながくれのテストもパラメタイズでまとめて実装


def test_ゆきがくれ_ゆきで命中低下():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability="ゆきがくれ")],
        weather=("ゆき", 5),
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 3277 // 4096


def test_ゆきがくれ_ゆき以外では命中率変化なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability="ゆきがくれ")],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_ゆきがくれ_かたやぶりで命中率補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability="ゆきがくれ")],
        weather=("ゆき", 5),
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy

# ──────────────────────────────────────────────────────────────────
# すなのちから
# ──────────────────────────────────────────────────────────────────
# TODO : テスト実装

# ──────────────────────────────────────────────────────────────────
# すなはき
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# すりぬけ
# ──────────────────────────────────────────────────────────────────
# TODO : 壁貫通テストはパラメタイズでまとめる


def test_すりぬけ_リフレクターを無視する():
    """すりぬけ: リフレクター中でも物理技が軽減されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        side1={"リフレクター": 5},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_すりぬけ_ひかりのかべを無視する():
    """すりぬけ: ひかりのかべ中でも特殊技が軽減されない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["でんきショック"])],
        side1={"ひかりのかべ": 5},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_すりぬけ_オーロラベールを無視する():
    """すりぬけ: オーロラベール中でも物理技が軽減されない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["たいあたり"])],
        side1={"オーロラベール": 5},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_すりぬけ_みがわりを無視する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みがわり": 1},
    )
    t.run_move(battle, 0)
    assert battle.actives[1].hp < battle.actives[1].max_hp


def test_すりぬけ_しんぴのまもりを貫通して状態異常が入る():
    """すりぬけ: しんぴのまもり中でも相手に状態異常を与えられる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability="すりぬけ")],
        side1={"しんぴのまもり": 5},
    )
    attacker, defender = battle.actives
    assert battle.ailment_manager.apply(defender, "どく", source=attacker)
    assert defender.ailment.name == "どく"


def test_すりぬけ_しんぴのまもりを貫通してこんらんが入る():
    """すりぬけ: しんぴのまもり中でも相手にこんらんを与えられる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability="すりぬけ")],
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
        team0=[Pokemon("ピカチュウ", ability="するどいめ")],
        team1=[Pokemon("ピカチュウ", moves=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].rank["ACC"] == 0


# TODO : 相手の回避ランクを無視して攻撃できることを確認するテストを追加

def test_するどいめ_かたやぶりで無効():
    """するどいめ: かたやぶり持ちによる命中率低下はするどいめを貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="するどいめ")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["すなかけ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["ACC"] == -1


# ──────────────────────────────────────────────────────────────────
# スロースタート
# ──────────────────────────────────────────────────────────────────


def test_スロースタート_登場5ターン未満は攻撃補正0_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="スロースタート", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier

    battle.turn = battle.actives[0].ability.count + 5
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


# TODO : 特攻には補正がかからないことを確認するテストを追加


# ──────────────────────────────────────────────────────────────────
# スワームチェンジ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# せいしんりょく
# ──────────────────────────────────────────────────────────────────


def test_せいしんりょく_ひるみを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="せいしんりょく")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert not battle.volatile_manager.apply(battle.actives[0], "ひるみ", count=1)


def test_せいしんりょく_いかくを防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="せいしんりょく")],
        team1=[Pokemon("ウインディ", ability="いかく")],
    )
    assert battle.actives[0].rank["A"] == 0

# TODO : かたやぶりで無効化するテストを追加 (ねこだまし実装後)

# ──────────────────────────────────────────────────────────────────
# 接触時に状態異常付与
# せいでんき、どくのトゲ、ほのおのからだ
# ──────────────────────────────────────────────────────────────────

# TODO : パラメタライズでまとめてテストする


def test_どくのトゲ_接触技でどく付与():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="どくのトゲ")],
        team1=[Pokemon("イーブイ", moves=["たいあたり"])],
    )
    attacker = battle.actives[1]
    battle.random.random = lambda: 0.0
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert attacker.has_ailment("どく")


def test_どくのトゲ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="どくのトゲ")],
        team1=[Pokemon("イーブイ", moves=["はどうだん"])],
    )
    attacker = battle.actives[1]
    battle.random.random = lambda: 0.0
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert not attacker.has_ailment("どく")


def test_ほのおのからだ_接触技で被弾時に30パーセントで相手をやけど():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ほのおのからだ")],
        team1=[Pokemon("イーブイ", moves=["たいあたり"])],
    )
    attacker = battle.actives[1]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert attacker.has_ailment("やけど")

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
        team0=[Pokemon("ピカチュウ", ability="ダウンロード")],
        team1=[Pokemon(foe_name)],
    )
    assert battle.actives[0].rank[stat] == 1


def test_ダウンロード_BD等しいときCアップ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ダウンロード")],
        team1=[Pokemon("ウインディ")],
    )
    mon = battle.actives[0]
    assert mon.rank["C"] == 1


# ──────────────────────────────────────────────────────────────────
# だっぴ
# ──────────────────────────────────────────────────────────────────


def test_だっぴ_ターン終了時に状態異常を回復する():
    # TODO : パラメタライズですべての状態異常についてテストする
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.events.emit(Event.ON_TURN_END_2)
    finally:
        battle.random.random = orig_random

    assert not mon.ailment.is_active


def test_だっぴ_非発動時は状態異常が残る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")

    orig_random = battle.random.random
    battle.random.random = lambda: 0.99
    try:
        battle.events.emit(Event.ON_TURN_END_2)
    finally:
        battle.random.random = orig_random

    assert mon.ailment.is_active


def test_だっぴ_発動ターンはどくダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    hp_before = mon.hp

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.events.emit(Event.ON_TURN_END_2)
        battle.events.emit(Event.ON_TURN_END_3)
    finally:
        battle.random.random = orig_random

    assert mon.hp == hp_before


# ──────────────────────────────────────────────────────────────────
# たんじゅん
# ──────────────────────────────────────────────────────────────────


def test_たんじゅん_能力上昇量が2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="たんじゅん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"A": 1, "B": -2, "C": 3, "D": -4, "S": 1, "ACC": -2, "EVA": 3}
    battle.modify_stats(target, stats, source=source)
    for stat, change in stats.items():
        assert target.rank[stat] == max(-6, min(6, change * 2))


def test_たんじゅん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="たんじゅん")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1


# ──────────────────────────────────────────────────────────────────
# ちからずく
# ──────────────────────────────────────────────────────────────────
def test_ちからずく_追加効果あり技の威力が1_3倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ちからずく", moves=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    battle.run_move(attacker, attacker.moves[0])
    assert battle.damage_calculator.power_modifier == 5325
    assert attacker.rank["S"] == 0


# ──────────────────────────────────────────────────────────────────
# ちからもち、ヨガパワー
# ヨガパワーの実装はちからもちと共通のためテスト不要
# ──────────────────────────────────────────────────────────────────


def test_ちからもち_物理技で攻撃補正2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ちからもち", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_ちからもち_特殊技では攻撃補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ちからもち", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_ちからもち_イカサマで攻撃するときも2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ちからもち", moves=["イカサマ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_ちからもち_イカサマを受けるときは補正なし():
    # TODO : 実装
    pass


# ──────────────────────────────────────────────────────────────────
# タイプ無効で回復
# ちくでん、ちょすい、どしょく
# ──────────────────────────────────────────────────────────────────
# TODO : パラメタライズでまとめてテストする

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
        team0=[Pokemon("ピカチュウ", ability=ability)],
        team1=[Pokemon("ピカチュウ", moves=[move])],
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
        team0=[Pokemon("ピカチュウ", ability=ability)],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=[move])],
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
# TODO : 条件と補正量をリスト化し、パラメタライズでまとめてテストする


def test_てきおうりょく_通常時STABが2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="てきおうりょく", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == 4096 * 2


def test_てきおうりょく_元タイプ一致テラスタルで2_25倍になる():
    battle = t.start_battle(
        team0=[Pokemon("リザードン", ability="てきおうりょく", tera_type="ほのお", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[0].terastallize()
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == 4096 * 2.25


def test_てきおうりょく_非一致タイプは補正しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="てきおうりょく", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == 4096


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
        team0=[Pokemon("ピカチュウ", ability="テクニシャン", moves=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


def test_テクニシャン_連続技でもヒット毎に判定がぶれない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="テクニシャン", moves=["タネマシンガン"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    v1 = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=move, hit_index=1, hit_count=5),
        4096,
    )
    v2 = battle.events.emit(
        Event.ON_CALC_POWER_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=move, hit_index=5, hit_count=5),
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
        team0=[Pokemon("ピカチュウ", moves=[move_name])],
        team1=[Pokemon(defender_name, ability="テラスシェル")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected


def test_テラスシェル_HP満タンでないと発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="テラスシェル")],
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp - 1
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_テラスシェル_かたやぶりで無効():
    """テラスシェル: かたやぶり持ちの技はテラスシェルの半減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="テラスシェル")],
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
        team0=[Pokemon("ピカチュウ", moves=[move_name])],
        team1=[Pokemon("ピカチュウ", ability="てんねん")],
    )
    attacker, defender = battle.actives
    attacker.rank[stat] = 2
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
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
        team0=[Pokemon("ピカチュウ", ability="てんねん", moves=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.rank[stat] = 2
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
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
        team0=[Pokemon("ピカチュウ", ability="てんのめぐみ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    ctx = BattleContext(attacker=attacker, move=attacker.moves[0])
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
        team0=[Pokemon("ピカチュウ", ability="どくしゅ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert defender.has_ailment("どく")


def test_どくしゅ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("イーブイ", ability="どくしゅ", moves=["はどうだん"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
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
        team0=[Pokemon("ピカチュウ", ability="トレース")],
        team1=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.actives[0].ability.base_name == "いかく"
    assert battle.actives[1].rank["A"] == -1


def test_トレース_uncopyable特性だと不発():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="トレース")],
        team1=[Pokemon("ピカチュウ", ability="トレース")],
    )
    assert battle.actives[0].ability.base_name == "トレース"
    assert battle.actives[0].ability.revealed is False  # 不発なので False のまま


def test_トレース_交代で元の特性に戻り再入場で再コピーする():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability="トレース"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("ピカチュウ", ability="すなかき")],
    )

    tracer = battle.players[0].team[0]
    assert tracer.ability.base_name == "すなかき"

    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert tracer.ability.base_name == "トレース"

    battle.switch_manager.run_switch(battle.players[0], tracer)
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
        team0=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        team1=[Pokemon("ピカチュウ", moves=["ひのこ"])],
    )
    defender, attacker = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["A"] == 1
    assert defender.ability.revealed


def test_ねつこうかん_やけど状態にならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[0]
    battle.ailment_manager.apply(target, "やけど")
    assert not target.ailment.is_active


# TODO : かたやぶりで無効化するテストを追加 (おにび実装後)


# ──────────────────────────────────────────────────────────────────
# ねんちゃく
# ──────────────────────────────────────────────────────────────────
def test_ねんちゃく_相手による道具変更をブロックする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.can_change_item(source=source, target=target)


def test_ねんちゃく_道具なしでも相手による道具変更をブロックする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ねんちゃく")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.can_change_item(source=source, target=target)


def test_ねんちゃく_自己起因の道具変更は阻害しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, _ = battle.actives
    assert battle.can_change_item(target, target)


# ──────────────────────────────────────────────────────────────────
# ノーガード
# ──────────────────────────────────────────────────────────────────


def test_ノーガード_攻撃側で必中化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ノーガード", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")]
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        0,
    )
    assert accuracy is None


def test_ノーガード_防御側で必中化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="ノーガード")]
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        0,
    )
    assert accuracy is None


# ──────────────────────────────────────────────────────────────────
# ノーマルスキン
# ──────────────────────────────────────────────────────────────────

def test_ノーマルスキン_ノーマルタイプに変えた技は強化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ノーマルスキン", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    result = battle.move_executor.resolve_move_type(attacker, move)
    assert result == "ノーマル"

    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_ノーマルスキン_元からノーマルタイプの技は威力補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ノーマルスキン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
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
        team0=[Pokemon("ピカチュウ", moves=["じしん"])],
        team1=[Pokemon("コイル", ability="ハードロック")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


def test_ハードロック_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じしん"])],
        team1=[Pokemon("コイル", ability="ハードロック")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_プリズムアーマー_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じしん"])],
        team1=[Pokemon("コイル", ability="プリズムアーマー")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# ばけのかわ
# ──────────────────────────────────────────────────────────────────

def test_ばけのかわ_2回目以降の攻撃は防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives

    # ダメージ計算結果を固定
    battle.roll_damage = lambda attacker, defender, move, critical=False: 30

    # 1回目
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.ability.enabled is False
    assert defender.hp == defender.max_hp - defender.max_hp // 8

    # 2回目
    hp_before = defender.hp
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.hp == hp_before - 30


def test_ばけのかわ_連続技の2発目以降は防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["にどげり"])],
        team1=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives
    before_hp = defender.hp

    battle.roll_damage = (
        lambda attacker, defender, move, critical=False: 10
    )
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is False
    assert defender.hp == before_hp - defender.max_hp // 8 - 10


def test_ばけのかわ_交代しても再有効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="ばけのかわ"), Pokemon("ピカチュウ")],
    )
    # 初回被弾でばけのかわを消費
    attacker = battle.players[0].active
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert battle.actives[1].ability.enabled is False

    # 交代して戻っても per_battle_once 特性は再有効化されない
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[0])
    assert battle.actives[1].ability.enabled is False


def test_ばけのかわ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives
    battle.roll_damage = (
        lambda attacker, defender, move, critical=False: 10
    )

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is True
    assert defender.hp == defender.max_hp - 10


# TODO : かがくへんかガスで無効化されないテストを追加

# ──────────────────────────────────────────────────────────────────
# はっこう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# バトルスイッチ
# ──────────────────────────────────────────────────────────────────


def test_バトルスイッチ_シールドで攻撃技を使うとブレードへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability="バトルスイッチ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.move_executor.run_move(mon, mon.moves[0])

    assert mon.name == "ギルガルド(ブレード)"


def test_バトルスイッチ_シールドで変化技なら変化しない():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(シールド)", ability="バトルスイッチ", moves=["つるぎのまい"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.move_executor.run_move(mon, mon.moves[0])
    assert mon.name == "ギルガルド(シールド)"


def test_バトルスイッチ_ブレードでキングシールドを使うとシールドへ変化する():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability="バトルスイッチ", moves=["キングシールド"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.move_executor.run_move(mon, mon.moves[0])

    assert mon.name == "ギルガルド(シールド)"


def test_バトルスイッチ_ブレードでまもるなら変化しない():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability="バトルスイッチ", moves=["まもる"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.move_executor.run_move(mon, mon.moves[0])
    assert mon.name == "ギルガルド(ブレード)"


def test_バトルスイッチ_交代時はシールドへ戻る():
    battle = t.start_battle(
        team0=[Pokemon("ギルガルド(ブレード)", ability="バトルスイッチ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_switch(battle, 0, 1)
    assert battle.players[0].team[0].name == "ギルガルド(シールド)"

# TODO : かがくへんかガスで無効化されないテストを追加

# ──────────────────────────────────────────────────────────────────
# ハドロンエンジン
# ──────────────────────────────────────────────────────────────────
# TODO : テスト実装

# ──────────────────────────────────────────────────────────────────
# はやあし
# ──────────────────────────────────────────────────────────────────
# TODO : すべての状態異常について、パラメタライズでまとめてテストする


def test_はやあし_どく状態で素早さ1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="はやあし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")

    base = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base * 3 // 2


def test_はやあし_まひ状態で素早さ低下を無視して1_5倍():
    # ピカチュウはでんきタイプでまひ免疫があるためカビゴン（ノーマル）を使用
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability="はやあし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")

    base = mon.stats["S"]
    # まひ_speed による 1/2 ペナルティを打ち消して 1.5倍（*3）
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
        team0=[Pokemon("モルペコ", ability="はらぺこスイッチ")],
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
        team0=[Pokemon("モルペコ", ability="はらぺこスイッチ", tera_type="あく")],
        team1=[Pokemon("ピカチュウ", moves=["はねる"])],
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
        team0=[Pokemon("モルペコ", ability="はらぺこスイッチ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = player.team[0]
    mon.ability.is_hangry = True
    battle.switch_manager.run_switch(player, player.team[1])

    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル交代時はフォルム維持する():
    battle = t.start_battle(
        team0=[Pokemon("モルペコ", ability="はらぺこスイッチ", tera_type="あく"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = player.team[0]
    mon.ability.is_hangry = True
    mon.terastallize()
    battle.switch_manager.run_switch(player, player.team[1])

    assert mon.ability.is_hangry is True

# ──────────────────────────────────────────────────────────────────
# バリアフリー
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# はりきり
# ──────────────────────────────────────────────────────────────────


def test_はりきり_物理技の攻撃補正が1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="はりきり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    move = attacker.moves[0]
    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=move),
        4096,
    )
    assert atk_modifier == 6144

    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, move=move),
        100,
    )
    assert accuracy == 100 * 3277 // 4096


def test_はりきり_特殊技には補正がかからない():
    """はりきり特性: 特殊技には攻撃補正と命中率補正がかからない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="はりきり", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    move = attacker.moves[0]
    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=move),
        4096,
    )
    assert atk_modifier == 4096

    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, move=move),
        100,
    )
    assert accuracy == 100


def test_はりきり_一撃必殺技の命中率は下がらない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="はりきり", moves=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    move = attacker.moves[0]
    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, move=move),
        30,
    )
    # 命中率ペナルティがかからない
    assert accuracy == 30


# ──────────────────────────────────────────────────────────────────
# はりこみ
# ──────────────────────────────────────────────────────────────────
def test_はりこみ_交代直後の相手への攻撃強化():
    # TODO : 実装
    pass

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

# TODO : どく、もうどくの両状態について、パラメタライズでまとめてテストする


def test_ひとでなし_どく状態の相手には急所ランク最大になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, "どく", source=attacker)

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank >= 3


def test_ひとでなし_非どく状態の相手には急所ランクを変更しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank == 0


# ──────────────────────────────────────────────────────────────────
# ひひいろのこどう
# ──────────────────────────────────────────────────────────────────

# TODO : テスト実装


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
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="ファーコート")],
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
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="マルチスケイル")],
    )
    attacker, defender = battle.actives

    # 1発目は半減
    battle.run_move(attacker, attacker.moves[0])
    assert 2048 == battle.damage_calculator.damage_modifier

    # 2発目は半減しない
    battle.run_move(attacker, attacker.moves[0])
    assert 4096 == battle.damage_calculator.damage_modifier


def test_マルチスケイル_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="マルチスケイル")],
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert 4096 == battle.damage_calculator.damage_modifier


def test_ファントムガード_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="ファントムガード")],
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
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
        team0=[Pokemon("ピカチュウ", ability="ぶきよう", item="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not mon.item.enabled

    mon.hp = 1
    battle.events.emit(Event.ON_TURN_END_2)
    assert mon.hp == 1


# ──────────────────────────────────────────────────────────────────
# ふくがん
# ──────────────────────────────────────────────────────────────────


def test_ふくがん_命中率を1_3倍にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ふくがん", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]
    result = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        30,
    )
    assert result == 30 * 5325 // 4096


def test_ふくがん_一撃必殺技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ふくがん", moves=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=battle.actives[1], move=move),
        30,
    )
    assert result == 30


# ──────────────────────────────────────────────────────────────────
# ふくつのこころ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ふくつのたて、ふとうのけん
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ふしぎなうろこ
# ──────────────────────────────────────────────────────────────────
# TODO : すべての状態異常について、パラメタイズでまとめてテストする
def test_ふしぎなうろこ_状態異常でB上昇():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="ふしぎなうろこ")],
    )
    battle.ailment_manager.apply(battle.actives[1], "やけど")
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_ふしぎなうろこ_かたやぶりで無効():
    """ふしぎなうろこ: かたやぶり持ちの物理技はふしぎなうろこの防御補正を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="ふしぎなうろこ")],
    )
    battle.ailment_manager.apply(battle.actives[1], "やけど")
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


# ──────────────────────────────────────────────────────────────────
# ふしょく
# ──────────────────────────────────────────────────────────────────
# TODO : はがねタイプに対するテストもパラメタライズでまとめてテストする
def test_ふしょく持ち由来ならどくタイプにもどくが入る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ふしょく")],
        team1=[Pokemon("フシギダネ")],
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
        team0=[Pokemon("ピカチュウ", ability="ふゆう")],
        team1=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]
    floating = battle.events.emit(
        Event.ON_CHECK_FLOATING,
        BattleContext(source=mon),
        False
    )
    assert floating is True

# TODO : run_move()でダメージを受けているか確認する方式にする


def test_ふゆう_じめん技が通らない():
    """ふゆう: ふゆう持ちはじめん技を無効化できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ふゆう")],
        team1=[Pokemon("ピカチュウ", moves=["じしん"])],
    )
    defender, attacker = battle.actives
    damages = battle.calc_damage_range(
        attacker=attacker,
        defender=defender,
        move=attacker.moves[0],
    )
    assert damages[-1] == 0

# TODO : run_move()でダメージを受けているか確認する方式にする


def test_ふゆう_かたやぶりでじめん技が通る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ふゆう")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じしん"])],
    )
    defender, attacker = battle.actives
    battle.run_move(attacker, attacker.moves[0])
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
        team0=[Pokemon("ピカチュウ", ability="ブレインフォース", moves=["でんきショック"])],
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
        team0=[Pokemon("ピカチュウ", ability="へんげんじざい", moves=["たいあたり", "ひのこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert attacker.types == ["ノーマル"]

    battle.move_executor.run_move(attacker, attacker.moves[1])
    assert attacker.types == ["ノーマル"]


def test_へんげんじざい_交代でリセットされ再発動できる():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability="へんげんじざい", moves=["たいあたり", "ひのこ"]),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    player = battle.players[0]
    mon = player.team[0]

    battle.move_executor.run_move(mon, mon.moves[0])
    assert mon.types == ["ノーマル"]

    battle.switch_manager.run_switch(player, player.team[1])
    battle.switch_manager.run_switch(player, mon)
    battle.move_executor.run_move(mon, mon.moves[1])

    assert mon.types == ["ほのお"]


# ──────────────────────────────────────────────────────────────────
# へんしょく
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ポイズンヒール
# ──────────────────────────────────────────────────────────────────

# TODO : どく・もうどくのテストはパラメタライズでまとめる
def test_ポイズンヒール_どく状態で1_8回復する():
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability="ポイズンヒール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == before + mon.max_hp // 8


def test_ポイズンヒール_もうどく状態でも固定1_8回復する():
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability="ポイズンヒール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    # もうどくのターン数を5にしてもダメージではなく1/8回復
    for _ in range(5):
        battle.ailment_manager.tick(mon)
    battle.events.emit(Event.ON_TURN_END_3)
    assert mon.hp == before + mon.max_hp // 8


def test_ポイズンヒール_かいふくふうじ中は回復もダメージも受けない():
    battle = t.start_battle(
        team0=[Pokemon("グライオン", ability="ポイズンヒール")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    battle.volatile_manager.apply(mon, "かいふくふうじ")
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before


# ──────────────────────────────────────────────────────────────────
# ぼうおん、ぼうだん
# ──────────────────────────────────────────────────────────────────
# TODO : ぼうおんとぼうだんのテストをパラメタライズでまとめる


def test_ぼうおん_音技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ぼうおん")],
        team1=[Pokemon("ピカチュウ", moves=["バークアウト"])],
    )
    defender, attacker = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert defender.hp == defender.max_hp
    assert defender.ability.revealed is True


def test_ぼうおん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ぼうおん")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["バークアウト"])],
    )
    defender, attacker = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert defender.hp < defender.max_hp
    assert defender.ability.revealed is False


# ──────────────────────────────────────────────────────────────────
# ぼうじん
# ──────────────────────────────────────────────────────────────────


def test_ぼうじん_粉技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ぼうじん")],
        team1=[Pokemon("ピカチュウ", moves=["キノコのほうし"])],
    )
    defender, attacker = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert not defender.ailment.is_active
    assert defender.ability.revealed is True


def test_ぼうじん_かたやぶりで無効():
    pass
    # TODO : キノコのほうしのハンドラ実装後に実装


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
        team0=[Pokemon("イルカマン(ナイーブ)", ability="マイティチェンジ"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = player.team[0]
    battle.switch_manager.run_switch(player, player.team[1])
    assert mon.name == "イルカマン(マイティ)"


# TODO : かがくへんかガスで無効化されないテストを追加

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
        team0=[Pokemon("ピカチュウ", ability="マジックガード")],
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
        team0=[Pokemon("ピカチュウ", moves=["なきごえ"])],
        team1=[Pokemon("ニャース", ability="マジックミラー")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.rank["A"] == -1
    assert defender.rank["A"] == 0

# TODO かたやぶりで無効化されるテストを追加

# ──────────────────────────────────────────────────────────────────
# マルチタイプ
# ──────────────────────────────────────────────────────────────────

# TODO : すべてのプレートをパラメタライズでまとめてテストする


def test_マルチタイプ_せいれいプレートでフェアリータイプになる():
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability="マルチタイプ", item="せいれいプレート")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == "フェアリー"
    assert mon.ability.revealed is False  # マルチタイプは開示されない


def test_マルチタイプ_プレートなしでタイプ変更なし():
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability="マルチタイプ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None
    assert mon.ability.revealed is False  # プレートなしは不発なので False


def test_マルチタイプ_プレートの奪取を阻止する():
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", ability="マルチタイプ", item="せいれいプレート")],
        team1=[Pokemon("ピカチュウ", moves=["はたきおとす"])],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    # ON_CHECK_ITEM_CHANGE: target=アルセウス, source=ピカチュウ → 奪取を阻止
    ctx = BattleContext(attacker=attacker, defender=mon, move=attacker.moves[0],
                        source=attacker, target=mon)
    result = battle.events.emit(Event.ON_CHECK_ITEM_CHANGE, ctx, True)
    assert result is False

# TODO : かがくへんかガスで無効化されないテストを追加

# ──────────────────────────────────────────────────────────────────
# ミイラ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ミラーアーマー
# ──────────────────────────────────────────────────────────────────


def test_ミラーアーマー_能力低下のみ反射する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ミラーアーマー")],
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
        team0=[Pokemon("ピカチュウ", ability="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", moves=["なきごえ"])],
    )
    target, source = battle.actives
    battle.modify_stats(target, {"A": -1}, source=target)
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[1].rank["A"] == 0


def test_ミラーアーマー_かたやぶりで反射されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ミラーアーマー")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[1].rank["A"] == 0


def test_ミラーアーマー_反射により相手のかちきが発動する():
    # TODO : 実装
    pass


# ──────────────────────────────────────────────────────────────────
# ミラクルスキン
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# ムラっけ
# ──────────────────────────────────────────────────────────────────


def test_ムラっけ_ターン終了時に別々の能力が上昇と下降する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    choices = iter(["A", "B"])
    battle.random.choice = lambda seq: next(choices)

    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))

    assert mon.rank["A"] == 2
    assert mon.rank["B"] == -1


def test_ムラっけ_全能力が最大なら下降のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("A", "B", "C", "D", "S"):
        mon.rank[stat] = 6
    battle.random.choice = lambda seq: seq[0]

    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))

    assert mon.rank["A"] == 5
    assert mon.rank["B"] == 6


def test_ムラっけ_全能力が最小なら上昇のみ発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="ムラっけ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("A", "B", "C", "D", "S"):
        mon.rank[stat] = -6
    battle.random.choice = lambda seq: seq[0]

    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))

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
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_もふもふ_ほのお技を倍加():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", ability="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.damage_modifier


def test_もふもふ_ほのお接触技は等倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ", ability="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


# ──────────────────────────────────────────────────────────────────
# もらいび
# ──────────────────────────────────────────────────────────────────

def test_もらいび_吸収後は最初の炎技のみ1_5倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="もらいび", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", moves=["ひのこ"])],
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
        team0=[Pokemon("ピカチュウ", moves=["かえんのまもり"])],
        team1=[Pokemon("ピカチュウ", ability="もらいび")],
    )
    attacker, defender = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert attacker.has_volatile("かえんのまもり")
    assert defender.ability.state == "idle"


def test_もらいび_かたやぶりには貫通される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="もらいび")],
        team1=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["ひのこ"])],
    )
    defender, attacker = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
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

# TODO : 攻撃と特攻の両方が半減することを確認するように、技をパラメタライズで複数テストする
def test_よわき_HP半分以下で攻撃補正0_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="よわき", moves=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier


# ──────────────────────────────────────────────────────────────────
# リーフガード
# ──────────────────────────────────────────────────────────────────

# TODO : すべての天候について、パラメタライズでまとめてテストする
def test_リーフガード_はれ以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.is_active


# TODO : すべての状態異常について、パラメタライズでまとめてテストする
# 天候ははれのみでよい
@pytest.mark.parametrize("weather_name,weather_count", [("はれ", 5), ("おおひでり", 999)])
def test_リーフガード_はれおおひでり中に状態異常を防ぐ(weather_name: str, weather_count: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, "どく")
    assert not mon.ailment.is_active


# ──────────────────────────────────────────────────────────────────
# リミットシールド
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# りんぷん
# ──────────────────────────────────────────────────────────────────


def test_りんぷん_追加効果確率を0にする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability="りんぷん")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.is_active is False


def test_りんぷん_かたやぶりで無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability="りんぷん")],
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
        team0=[Pokemon("ピカチュウ", moves=[move_name])],
        team1=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.atk_modifier


def test_わざわいのおふだ_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability="わざわいのおふだ")],
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
        team0=[Pokemon("ピカチュウ", ability=ability_name, moves=[move_name])],
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
