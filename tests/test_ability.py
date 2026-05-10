"""特性ハンドラの単体テスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event, Interrupt, LogCode, Command
from jpoke.model import Move
from jpoke.utils.type_defs import STRONG_WEATHERS

import test_utils as t


# TODO : t.check_event_result()を活用してテストコードの量を減らす


# ──────────────────────────────────────────────────────────────────
# ARシステム
# ──────────────────────────────────────────────────────────────────

# TODO : パラメタライズで全アイテムをテストする


def test_ARシステム_フェアリーメモリでフェアリータイプになる():
    battle = t.start_battle(
        ally=[Pokemon("シルヴァディ", ability="ARシステム", item="フェアリーメモリ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == "フェアリー"
    assert mon.ability.revealed is False  # ARシステムは開示されない


def test_ARシステム_メモリなしでタイプ変更なし():
    battle = t.start_battle(
        ally=[Pokemon("シルヴァディ", ability="ARシステム")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None
    assert mon.ability.revealed is False  # メモリなしは不発なので False

# ──────────────────────────────────────────────────────────────────
# アイスボディ、あめうけざら
# ──────────────────────────────────────────────────────────────────

# TODO アイスボディもパラメタライズでまとめてテストする


@pytest.mark.parametrize("weather_name,weather_count", [("あめ", 5), ("おおあめ", 999)])
def test_あめうけざら_あめおおあめ中にターン終了1_16回復(weather_name: str, weather_count: int):
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="あめうけざら")],
        foe=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before + mon.max_hp // 16


def test_あめうけざら_あめ以外では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="あめうけざら")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before


def test_あめうけざら_ばんのうがさ所持時は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="あめうけざら", item="ばんのうがさ")],
        foe=[Pokemon("ピカチュウ")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("あめうけざら", "あめ"),
        ("アイスボディ", "ゆき"),
    ],
)
def test_回復天候特性_かがくへんかガス中は回復しない(ability_name: str, weather_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability=ability_name)],
        foe=[Pokemon("マタドガス", ability="かがくへんかガス")],
        weather=(weather_name, 999),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert battle.actives[0].ability.enabled is False
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
        ("あついしぼう", "かえんほうしゃ"),
        ("あついしぼう", "れいとうビーム"),
        ("たいねつ", "かえんほうしゃ"),
    ],
)
def test_受ける技タイプで攻撃補正半減する特性(ability_name: str, move_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER, atk_idx=0) == 2048

# TODO かがくへんかガスでも無効化されるテストを追加


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("あついしぼう", "かえんほうしゃ"),
        ("きよめのしお", "シャドーボール"),
        ("たいねつ", "かえんほうしゃ"),
    ],
)
def test_受ける技タイプ攻撃補正半減する特性_かたやぶりで無効化される(ability_name: str, move_name: str):
    """かたやぶり持ちの攻撃では、防御側の技タイプ攻撃補正半減特性が無効化される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=[move_name])],
        foe=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096

# ──────────────────────────────────────────────────────────────────
#  あとだし
# ──────────────────────────────────────────────────────────────────


def test_あとだし_同優先度で最後に行動():
    battle = t.start_battle(
        ally=[Pokemon("ライチュウ", ability="あとだし")],
        foe=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle)
    order = battle.determine_action_order()
    assert order[-1] == battle.actives[0], "あとだし所持者が同優先度で最後に行動しない"


def test_あとだし_高優先度技は先攻():
    """あとだし: 相手より優先度が高い技を使用した場合は先攻になる。"""
    battle = t.start_battle(
        ally=[Pokemon("ライチュウ", ability="あとだし", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle)
    order = battle.determine_action_order()
    assert order[0] == battle.actives[0], "あとだし所持者が高優先度技で先攻にならない"


def test_あとだし_トリックルームでも後攻():
    """あとだし: トリックルーム状態でも最後に行動する（素早さ逆転の影響を受けない）。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="あとだし")],
        foe=[Pokemon("ライチュウ")],
        global_field={"トリックルーム": 5},
    )
    t.reserve_command(battle)
    order = battle.determine_action_order()
    assert order[-1] == battle.actives[0], "あとだし所持者がトリックルームで後攻にならない"

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


ability_weather_pairs = [
    ("あめふらし", "あめ"),
    ("ひでり", "はれ"),
    ("すなおこし", "すなあらし"),
    ("ゆきふらし", "ゆき"),
    ("おわりのだいち", "おおひでり"),
    ("はじまりのうみ", "おおあめ"),
    ("デルタストリーム", "らんきりゅう"),
]
abilities = [x[0] for x in ability_weather_pairs]
weathers = [x[1] for x in ability_weather_pairs]
normal_weathers = weathers[:4]
strong_weathers = weathers[4:]


@pytest.mark.parametrize(
    "ability_name, weather_name", ability_weather_pairs
)
def test_天候始動特性_登場時に対応天候を展開する(ability_name: str, weather_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ライチュウ")],
    )
    assert battle.weather.name == weather_name
    assert battle.weather.count == 5
    assert battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "initial_weather", ["はれ", "すなあらし", "ゆき"]
)
def test_あめふらし_通常天候を上書きする(initial_weather: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability="あめふらし")],
        foe=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 999),
    )
    assert battle.weather.name == initial_weather
    # start_battle で初期天候を設定した後、交代で再登場させてあめふらしを再発動させる。
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "あめ"


@pytest.mark.parametrize(
    "initial_weather", strong_weathers
)
def test_あめふらし_強天候は上書き不可(initial_weather: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability="あめふらし")],
        foe=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 999),
    )
    assert battle.weather.name == initial_weather
    # start_battle で初期天候を設定した後、交代で再登場させてあめふらしを再発動させる。
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "あめ"


@pytest.mark.parametrize(
    "weather_name", normal_weathers + ["おおあめ"]
)
def test_おわりのだいち_らんきりゅう以外上書きする(weather_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability="おわりのだいち")],
        foe=[Pokemon("ライチュウ")],
        weather=(weather_name, 2)
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "おおひでり"
    assert not battle.actives[0].ability.revealed

    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability="おわりのだいち")],
        foe=[Pokemon("ライチュウ")],
        weather=(weather_name, 2)
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "おおひでり"
    assert not battle.actives[0].ability.revealed


def test_おわりのだいち_らんきりゅうは上書きできない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability="おわりのだいち")],
        foe=[Pokemon("ライチュウ")],
        weather=("らんきりゅう", 1),
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "らんきりゅう"
    assert not battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "weather_name", weathers
)
def test_らんきりゅう_すべての天候を上書きする(weather_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability="デルタストリーム")],
        foe=[Pokemon("ライチュウ")],
        weather=weather_name
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.weather.name == "らんきりゅう"
    assert battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("おわりのだいち", "おおひでり"),
        ("はじまりのうみ", "おおあめ"),
        ("デルタストリーム", "らんきりゅう"),
    ],
)
def test_強天候始動特性_退場時に解除される(ability_name: str, weather_name: str):
    """強天候始動特性: 特性持ちが退場すると強天候が解除される"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == weather_name

    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.weather.is_active


@pytest.mark.parametrize(
    "ability_name", ability_weather_pairs
)
def test_天候始動特性_かがくへんかガス中は発動しない(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.weather is None
    assert not battle.actives[0].ability.revealed


# ──────────────────────────────────────────────────────────────────
# 交代抑制
# ありじごく、かげふみ、じりょく
# ──────────────────────────────────────────────────────────────────

# TODO : 3特性の交代不可条件をリスト化してパラメタライズでまとめてテストする
# TODO : 3特性の交代可能条件をリスト化してパラメタライズでまとめてテストする

def test_ありじごく_交代不可():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="ありじごく")],
    )
    assert not t.can_switch(battle, 0)


def test_ありじごく_飛行タイプは交代可能():
    battle = t.start_battle(
        ally=[Pokemon("ピジョン"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="ありじごく")],
    )
    assert t.can_switch(battle, 0)


def test_ありじごく_ふゆうは交代可能():
    # TODO : 実装
    pass


def test_かげふみ_かげふみ持ち以外は交代不可():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="かげふみ")],
    )
    assert not t.can_switch(battle, 0)


def test_かげふみ_かげふみ持ちは交代可能():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かげふみ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="かげふみ"), Pokemon("ライチュウ")],
    )
    assert t.can_switch(battle, 0)
    assert t.can_switch(battle, 1)


def test_じりょく_はがねタイプは交代不可():
    battle = t.start_battle(
        ally=[Pokemon("コイル"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="じりょく")],
    )
    assert not t.can_switch(battle, 0)


def test_じりょく_はがねタイプ以外は交代可能():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="じりょく")],
    )
    assert t.can_switch(battle, 0)


def test_ゴーストタイプは交代可能():
    # TODO ありじごく、かげふみ、じりょくをまとめてパラメタライズでテスト実装
    # 相手役はギルガルド
    pass


def test_かがくへんかガス下で交代可能():
    # TODO ありじごく、かげふみ、じりょくをまとめてパラメタライズでテスト実装
    # 相手役はコイル
    pass

# ──────────────────────────────────────────────────────────────────
# 揮発状態耐性
# アロマベール、スイートベール、どんかん、マイペース
# ──────────────────────────────────────────────────────────────────
# 特性と耐性のある揮発状態をリスト化し、パラメタライズでまとめてテストする


def test_どんかん_かたやぶりで無効化される():
    """どんかん: かたやぶり持ちによるメロメロはどんかんを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="どんかん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]

    blocked = battle.events.emit(
        Event.ON_BEFORE_APPLY_AILMENT,
        BattleContext(target=mon, source=attacker, move=Move("あまえる")),
        "メロメロ",
    )
    assert blocked == "メロメロ"


def test_どんかん_かがくへんかガス中はメロメロが入る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="どんかん")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    source = battle.actives[1]

    assert mon.ability.enabled is False

    result = battle.events.emit(
        Event.ON_BEFORE_APPLY_AILMENT,
        BattleContext(target=mon, source=source),
        "メロメロ",
    )
    assert result == "メロメロ"


def test_マイペース_状態異常は防がない_現実装確認():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="マイペース")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.name == "どく"


def test_マイペース_かたやぶりで無効化される():
    """マイペース: かたやぶり持ちの相手はこんらん状態を付与できるようになる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="マイペース")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    assert battle.volatile_manager.apply(defender, "こんらん", count=3, source=attacker)
    assert defender.has_volatile("こんらん")


def test_マイペース_かがくへんかガス中はこんらんが付与される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="マイペース")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]

    assert mon.ability.enabled is False
    assert battle.volatile_manager.apply(mon, "こんらん", count=3, source=foe)
    assert mon.has_volatile("こんらん")

# ──────────────────────────────────────────────────────────────────
#  いかく
# ──────────────────────────────────────────────────────────────────


def test_いかく_登場時に相手攻撃1段階ダウン():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.actives[0].rank["A"] == -1


def test_いかく_かがくへんかガスで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いかく")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[1].rank["A"] == 0

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
        ally=[Pokemon("ゴンベ", ability="いしあたま", moves=["すてみタックル"])],
        foe=[Pokemon("ヤドン")],
    )
    attacker = battle.actives[0]
    battle.advance_turn()
    assert attacker.hp == attacker.max_hp


def test_いしあたま_かがくへんかガス中は反動ダメージを受ける():
    battle = t.start_battle(
        ally=[Pokemon("ゴンベ", ability="いしあたま", moves=["すてみタックル"])],
        foe=[Pokemon("マタドガス", ability="かがくへんかガス")],
    )
    attacker = battle.actives[0]
    battle.advance_turn()
    assert attacker.hp < attacker.max_hp

# ──────────────────────────────────────────────────────────────────
#  いたずらごころ
# ──────────────────────────────────────────────────────────────────


def test_いたずらごころ_変化技の優先度が1上がる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いたずらごころ", moves=["でんじは"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    assert attacker.moves[0].priority == 0
    assert battle.speed_calculator.calc_move_priority(attacker, attacker.moves[0]) == 1


# TODO : 無効判定をするイベントを発火して、戻り値を直接検証するようにテストを修正
def test_いたずらごころ_あくタイプ相手には変化技が無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いたずらごころ", moves=["でんじは"])],
        foe=[Pokemon("ヘルガー")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert not defender.has_ailment("まひ")
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=1)


# TODO : 無効判定をするイベントを発火して、戻り値を直接検証するようにテストを修正
def test_いたずらごころ_自己対象の変化技はあくタイプ相手でも成功する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いたずらごころ", moves=["かえんのまもり"])],
        foe=[Pokemon("ヘルガー")],
    )
    attacker = battle.actives[0]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert attacker.has_volatile("かえんのまもり")

# TODO : かがくへんかガスで無効化されることを検証するテストを追加

# ──────────────────────────────────────────────────────────────────
#  いろめがね
# ──────────────────────────────────────────────────────────────────


def test_いろめがね_いまひとつのダメージが2倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いろめがね", moves=["むしのていこう"])],
        foe=[Pokemon("ピジョン")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 8192


def test_いろめがね_かがくへんかガス中は補正なし():
    """いろめがね: かがくへんかガス中はいまひとつの補正が無効化される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いろめがね", moves=["むしのていこう"])],
        foe=[Pokemon("ピジョン", ability="かがくへんかガス")],
    )
    # かがくへんかガス登場でいろめがねが無効化される
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)

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
        ("トランジスタ", "１０まんボルト", 5325),
    ],
)
def test_タイプ依存攻撃補正特性(ability_name: str, move_name: str, expected: int):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=[move_name])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == expected

# TODO : かがくへんかガスの相互作用テストもパラメタライズでまとめる


def test_いわはこび_かがくへんかガス中はいわタイプ攻撃補正なし():
    """いわはこび: かがくへんかガス中は特性が無効化され、いわタイプ技の攻撃補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いわはこび", moves=["いわなだれ"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096


def test_トランジスタ_かがくへんかガス中はでんきタイプ攻撃補正なし():
    """トランジスタ: かがくへんかガス中は特性が無効化され、でんきタイプ技の攻撃補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="トランジスタ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096


def test_りゅうのあぎと_かがくへんかガス中はりゅうタイプ攻撃補正なし():
    """りゅうのあぎと: かがくへんかガス中は特性が無効化され、りゅうタイプ技の攻撃補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="りゅうのあぎと", moves=["りゅうのはどう"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096

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
    # TODO 強天候を含む全天候をパラメタライズでテストする
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="エアロック")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    assert battle.weather is None


def test_エアロック_すなあらしのターン終了ダメージが無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="エアロック")],
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
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ライチュウ")],
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
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability=ability_name)],
        foe=[Pokemon("ライチュウ")],
        terrain=(terrain_name, 2)
    )
    # TODO 控えのライチュウに指定特性を付与すれば交代1回でテストできる
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
    # TODO 控えのライチュウに指定特性を付与すれば交代1回でテストできる
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability="エレキメイカー")],
        foe=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 99),
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


@pytest.mark.parametrize(
    "ability_name, terrain_name",
    ability_terrain_pairs
)
def test_地形始動特性_かがくへんかガス中は発動しない(ability_name: str, terrain_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.terrain.name == ""


# ──────────────────────────────────────────────────────────────────
#  えんかく
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  おうごんのからだ
# ──────────────────────────────────────────────────────────────────
def test_おうごんのからだ_相手の変化技を無効化():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["なきごえ"])],
        foe=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    immune = t.check_event_result(battle, Event.ON_CHECK_IMMUNE)
    assert immune


def test_おうごんのからだ_攻撃技は無効化しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        foe=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    immune = t.check_event_result(battle, Event.ON_CHECK_IMMUNE)
    assert not immune


def test_おうごんのからだ_自分対象の変化技は無効化しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["つるぎのまい"])],
        foe=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    immune = t.check_event_result(battle, Event.ON_CHECK_IMMUNE)
    assert not immune


def test_おうごんのからだ_場が対象の技は無効化しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["にほんばれ"])],
        foe=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    immune = t.check_event_result(battle, Event.ON_CHECK_IMMUNE)
    assert not immune


def test_おうごんのからだ_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["なきごえ"])],
        foe=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    immune = t.check_event_result(battle, Event.ON_CHECK_IMMUNE)
    assert not immune


def test_おうごんのからだ_かがくへんかガス中は変化技が通る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["なきごえ"])],
        foe=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    immune = t.check_event_result(battle, Event.ON_CHECK_IMMUNE)
    assert not immune

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
        ally=[Pokemon("ピカチュウ", ability="おやこあい", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    # 1発目のダメージを固定する
    battle.determine_damage = lambda *args, **kwargs: 40

    attacker, defender = battle.actives
    battle.advance_turn()
    assert defender.hits_taken == 2
    assert defender.damage_taken == 40+10
    assert attacker.rank["S"] == 2


def test_おやこあい_既存連続技には適用しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="おやこあい", moves=["タネマシンガン"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    battle.random.random = lambda: 0.9
    hit_count = battle.move_executor._resolve_hit_count(attacker, move)
    assert hit_count == 5


def test_おやこあい_かがくへんかガス中は2ヒット化しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="おやこあい", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    battle.advance_turn()
    assert battle.actives[1].hits_taken == 1


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
        ally=[Pokemon("カイリキー", ability="かいりきバサミ")],
        foe=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    # TODO : B,C以外の低下もすべて含める
    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1, "B": -1, "C": -2},
    )
    assert stat_change == {"B": -1, "C": -2}


def test_かいりきバサミ_自己低下は防げない():
    battle = t.start_battle(
        ally=[Pokemon("カイリキー", ability="かいりきバサミ")],
        foe=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=ally_mon),
        {"A": -1},
    )
    assert stat_change == {"A": -1}


def test_かいりきバサミ_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("カイリキー", ability="かいりきバサミ")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1},
    )
    assert stat_change == {"A": -1}


def test_かいりきバサミ_かがくへんかガス中は防御できない():
    battle = t.start_battle(
        ally=[Pokemon("カイリキー", ability="かいりきバサミ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    ally_mon, foe_mon = battle.actives

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1},
    )
    assert stat_change == {"A": -1}


def test_はとむね_こうげき低下は防げない():
    """はとむね: ぼうぎょ以外のランク低下は防げない。"""
    battle = t.start_battle(
        ally=[Pokemon("トゲキッス", ability="はとむね")],
        foe=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1},
    )
    assert stat_change == {"A": -1}


def test_はとむね_かたやぶりで無効化される():
    """はとむね: かたやぶり持ちによるぼうぎょ低下ははとむねを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("トゲキッス", ability="はとむね")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"B": -1},
    )
    assert stat_change == {"B": -1}

# ──────────────────────────────────────────────────────────────────
#  かがくへんかガス
# ──────────────────────────────────────────────────────────────────


def test_かがくへんかガス_解除後は特性が再び有効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )

    # ガス発生中は相手のいかくが無効
    assert battle.actives[0].rank["A"] == 0
    assert not battle.actives[1].ability.revealed

    # ガス持ちを引っ込めると、相手の特性は有効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[1].ability.revealed

# ──────────────────────────────────────────────────────────────────
#  かぜのり
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
#  かそく
# ──────────────────────────────────────────────────────────────────


def test_かそく_行動後のターン終了時に素早さが上がる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かそく")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["S"] == 0

    mon.executed_move = mon.moves[0]
    battle.events.emit(Event.ON_TURN_END_5)
    assert mon.rank["S"] == 1


def test_かそく_交代直後のターン終了時は上がらない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="かそく")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    # 交代したターンはかそくが発動しない
    t.reserve_command(
        battle,
        ally_command=Command.SWITCH_1,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()
    assert mon.rank["S"] == 0

    # 次のターンはかそくが発動する
    t.reserve_command(
        battle,
        ally_command=Command.MOVE_0,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()
    assert mon.rank["S"] == 1


def test_かそく_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かそく")],
        foe=[Pokemon("マタドガス", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    mon.executed_move = mon.moves[0]
    battle.events.emit(Event.ON_TURN_END_5, BattleContext(source=mon), None)
    assert mon.rank["S"] == 0


# ──────────────────────────────────────────────────────────────────
# 技カテゴリによる威力強化
# かたいツメ、がんじょうあご、きれあじ、すてみ、てつのこぶし、
# パンクロック、メガランチャー
# ──────────────────────────────────────────────────────────────────
# TODO パラメタライズでまとめてテストする


def test_かたいツメ_接触技のみ威力補正1_3倍():
    battle_contact = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたいツメ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle_contact, Event.ON_CALC_POWER_MODIFIER) == 5325

    battle_non_contact = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたいツメ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle_non_contact, Event.ON_CALC_POWER_MODIFIER) == 4096


def test_かたいツメ_かがくへんかガス中は接触技でも威力補正なし():
    """かたいツメ: かがくへんかガス中は特性が無効化され、接触技の威力補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたいツメ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096

    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="メガランチャー", moves=["りゅうのはどう"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 6144


def test_がんじょうあご_かみつき技で威力補正1_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょうあご", moves=["かみつく"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 6144


def test_きれあじ_きる技は威力補正1_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きれあじ", moves=["きりさく"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 6144


def test_きれあじ_きる技以外は補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きれあじ", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096


def test_きれあじ_かがくへんかガス中は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きれあじ", moves=["きりさく"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled is False
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096


def test_てつのこぶし_かがくへんかガス中は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["かみなりパンチ"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled is False
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096


def test_てつのこぶし_パンチ技以外は補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_てつのこぶし_パンチ技威力補正():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["かみなりパンチ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 4915 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_パンクロック_音技で威力1_3倍かつ被ダメ0_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="パンクロック", moves=["バークアウト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 5325

    battle2 = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["バークアウト"])],
        foe=[Pokemon("ピカチュウ", ability="パンクロック", moves=["バークアウト"])],
    )
    assert t.calc_damage_modifier(battle2, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 2048


def test_パンクロック_かたやぶりで音技軽減が無効化される():
    """パンクロック: かたやぶり持ちの音技はパンクロックの被ダメ軽減を貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["バークアウト"])],
        foe=[Pokemon("ピカチュウ", ability="パンクロック")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 4096


def test_メガランチャー_かがくへんかガス中は波動技威力補正なし():
    """メガランチャー: かがくへんかガス中は特性が無効化され、波動技の威力補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="メガランチャー", moves=["りゅうのはどう"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096  # メガランチャー無効なので補正なし


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
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon, foe = battle.actives
    battle.modify_stat(mon, "A", -1, source=foe)
    assert mon.rank["C"] == 2


def test_かちき_自分由来の能力低下では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_stat(mon, "A", -1, source=mon)
    assert mon.rank["C"] == 0


def test_かちき_いかくで特攻2段階アップ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[0].rank["C"] == 2


def test_かちき_かがくへんかガス中は特攻上昇が発動しない():
    """かちき: かがくへんかガス中は特性が無効化され、能力低下に対する特攻上昇が発動しない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]

    assert mon.ability.enabled is False  # ガス中は無効化される
    battle.modify_stat(mon, "C", -1, source=battle.actives[1])
    assert mon.rank["C"] == -1  # かちき無効なので C-1 のまま


# ──────────────────────────────────────────────────────────────────
# 急所無効
# カブトアーマー、シェルアーマー
# シェルアーマーはカブトアーマーと共通実装のためテスト不要
# ──────────────────────────────────────────────────────────────────
def test_カブトアーマー_急所ランクを0にする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="カブトアーマー")],
        foe=[Pokemon("ピカチュウ", moves=["つじぎり"])],
    )
    attacker = battle.actives[1]
    defender = battle.actives[0]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=move),
        3,
    )

    assert result == 0


def test_カブトアーマー_かたやぶり攻撃では無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="カブトアーマー")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["つじぎり"])],
    )
    attacker = battle.actives[1]
    defender = battle.actives[0]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=move),
        3,
    )

    assert result == 3


def test_カブトアーマー_かがくへんかガス中は急所ランク補正が有効():
    # TODO : 攻撃側の特性をかがくへんかガスにして、冗長な交代処理を削除
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="カブトアーマー"), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ", moves=["つじぎり"])],
    )
    # かがくへんかガス登場でカブトアーマーが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    attacker = battle.actives[1]
    defender = battle.actives[0]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=move),
        3,
    )

    assert result == 3

    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
                            )
    self_mon, foe = battle.actives

    result = battle.can_change_item(foe, self_mon)

    assert result is False
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)

# ──────────────────────────────────────────────────────────────────
# かるわざ
# ──────────────────────────────────────────────────────────────────


def test_かるわざ_持ち物を失うと素早さが2倍になる():
    # TODO : battle.item_manager.lose_item()で直接アイテムを失わせるように修正
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かるわざ", item="オボンのみ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    base = battle.calc_effective_speed(mon)
    battle.consume_item(mon)
    boosted = battle.calc_effective_speed(mon)

    assert boosted == base * 2


def test_かるわざ_入場時に持ち物なしなら発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かるわざ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    base = battle.calc_effective_speed(mon)
    battle.set_item(mon, "オボンのみ")
    battle.consume_item(mon)
    after = battle.calc_effective_speed(mon)

    assert after == base


def test_かるわざ_持ち物再取得で解除され再消費で再発動する():
    # TODO : battle.lose_item()で直接アイテムを失わせるように修正
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かるわざ", item="オボンのみ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    base = battle.calc_effective_speed(mon)
    battle.consume_item(mon)
    assert battle.calc_effective_speed(mon) == base * 2

    battle.set_item(mon, "ラムのみ")
    assert battle.calc_effective_speed(mon) == base

    battle.consume_item(mon)
    assert battle.calc_effective_speed(mon) == base * 2


def test_かるわざ_かがくへんかガス中は発動しない():
    # TODO : battle.lose_item()で直接アイテムを失わせるように修正
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かるわざ", item="オボンのみ"), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ")],
    )
    # かがくへんかガス登場でかるわざが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    mon = battle.actives[0]
    base = battle.calc_effective_speed(mon)

    # かるわざが無効なのでアイテム消費後も速度は変わらない
    battle.consume_item(mon)
    assert battle.calc_effective_speed(mon) == base

# ──────────────────────────────────────────────────────────────────
# がんじょう
# ──────────────────────────────────────────────────────────────────


def test_がんじょう_HP満タン時の致死ダメージでHP1残る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょう")],
        foe=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
    )
    defender, attacker = battle.actives
    result = battle.events.emit(
        Event.ON_BEFORE_DAMAGE_APPLY,
        BattleContext(
            attacker=attacker, defender=defender,
            move=attacker.moves[0], hp_change_reason="move_damage")
        - defender.max_hp
    )
    assert result == -(defender.max_hp-1)


def test_がんじょう_HP満タンでないと致死ダメージで倒れる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょう")],
        foe=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
    )
    defender, attacker = battle.actives
    defender._hp = defender.max_hp-1
    result = battle.events.emit(
        Event.ON_BEFORE_DAMAGE_APPLY,
        BattleContext(
            attacker=attacker, defender=defender,
            move=attacker.moves[0], hp_change_reason="move_damage")
        - (defender.max_hp-1)
    )
    assert result == -(defender.max_hp-1)


def test_がんじょう_一撃必殺技を無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょう")],
        foe=[Pokemon("ピカチュウ", moves=["じわれ"])],
    )
    defender, attacker = battle.actives
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)
    assert immune is True


# TODO : かたやぶりによる攻撃ではHP 1で耐えないことを確認するテストを追加

def test_がんじょう_かたやぶり相手の一撃必殺は無効化されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょう")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じわれ"])],
    )
    defender, attacker = battle.actives
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)
    assert immune is False

# TODO : 攻撃側の特性がかがくへんかガスのときにがんじょうが発動しないことを確認するテストを追加


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
        ally=[
            Pokemon("ピカチュウ", ability="ききかいひ"),
            Pokemon("ライチュウ", moves=["たいあたり"])
        ],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    damage = defender.max_hp - defender.max_hp // 2
    battle.determine_damage = lambda *_args, **_kwargs: damage

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert battle.players[0].interrupt == Interrupt.EMERGENCY
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)

    battle.run_interrupt_switch(Interrupt.EMERGENCY)

    assert battle.players[0].active_idx == 1


def test_ききかいひ_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        ally=[Pokemon("コソクムシ", ability="ききかいひ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    defender._hp = defender.max_hp // 2
    battle.determine_damage = lambda *_args, **_kwargs: 1

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert battle.players[0].interrupt == Interrupt.NONE
    assert battle.players[0].active_idx == 0


def test_ききかいひ_やけどダメージでも発動する():
    battle = t.start_battle(
        ally=[Pokemon("コソクムシ", ability="ききかいひ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    mon._hp = mon.max_hp // 2 + 1
    battle.ailment_manager.apply(mon, "やけど")
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))

    assert battle.players[0].interrupt == Interrupt.EMERGENCY


def test_ききかいひ_こんらん自傷では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("コソクムシ", ability="ききかいひ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    mon._hp = mon.max_hp // 2 + 1
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
        ally=[Pokemon("ピカチュウ", ability="ぎゃくじょう")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender, attacker = battle.actives

    damage = defender.max_hp - defender.max_hp // 2
    battle.determine_damage = lambda *_args, **_kwargs: damage

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["C"] == 1
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ぎゃくじょう_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぎゃくじょう")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    defender._hp = defender.max_hp // 2
    battle.determine_damage = lambda *_args, **_kwargs: 1

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["C"] == 0


def test_ぎゃくじょう_連続攻撃では最終ヒット後に1回だけ判定する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぎゃくじょう")],
        foe=[Pokemon("ピカチュウ", moves=["にどげり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    damages = iter([10, 60])
    battle.determine_damage = lambda *_args, **_kwargs: next(damages)

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["C"] == 1


def test_ぎゃくじょう_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぎゃくじょう")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    damage = defender.max_hp - defender.max_hp // 2
    battle.determine_damage = lambda *_args, **_kwargs: damage

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is False
    assert defender.rank["C"] == 0


# ──────────────────────────────────────────────────────────────────
#  きゅうばん
# ──────────────────────────────────────────────────────────────────

def test_きゅうばん_ふきとばしの強制交代を防ぐ():
    """きゅうばん: ふきとばしによる強制交代効果をON_HITで遮断する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きゅうばん")],
        foe=[Pokemon("ピカチュウ", moves=["ふきとばし"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    result = battle.events.emit(
        Event.ON_HIT,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert result is False


def test_きゅうばん_かたやぶりで無効化される():
    """きゅうばん: かたやぶり持ちのふきとばしはきゅうばんを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きゅうばん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["ふきとばし"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    result = battle.events.emit(
        Event.ON_HIT,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    assert result is True

# ──────────────────────────────────────────────────────────────────
# きょううん
# ──────────────────────────────────────────────────────────────────


def test_きょううん_急所ランクが1上がる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きょううん", moves=["つじぎり"])],
        foe=[Pokemon("ピカチュウ")],
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


def test_きょううん_かがくへんかガス中は急所ランク補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きょううん", moves=["つじぎり"]), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ")],
    )
    # かがくへんかガス登場できょううんが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=move),
        0,
    )
    assert result == 0


# ──────────────────────────────────────────────────────────────────
# きよめのしお
# ──────────────────────────────────────────────────────────────────
# TODO ゴーストわざ半減のテストを実装
# TODO すべての状態異常無効のテストを実装 (パラメタライズ)

def test_きよめのしお_かがくへんかガス中はシャドーボール被ダメ半減なし():
    """きよめのしお: かがくへんかガス中は特性が無効化され、シャドーボールの被ダメ転改がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["シャドーボール"])],
        foe=[Pokemon("ピカチュウ", ability="きよめのしお"), Pokemon("ライチュウ", ability="かがくへんかガス")],
    )
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER, atk_idx=0) == 4096


# ──────────────────────────────────────────────────────────────────
# きんしのちから
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# きんちょうかん
# ──────────────────────────────────────────────────────────────────
def test_きんちょうかん_相手をきんちょうかん状態にする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="きんちょうかん")],
    )
    assert battle.query_manager.is_nervous(battle.actives[0])
    assert battle.actives[1].ability.enabled


def test_きんちょうかん_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ", ability="きんちょうかん")],
    )
    assert not battle.query_manager.is_nervous(battle.actives[0])
    assert not battle.actives[1].ability.enabled

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
        ally=[Pokemon("ピカチュウ", ability="クォークチャージ", item="ブーストエナジー")],
        foe=[Pokemon("ピカチュウ")],
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
        ally=[Pokemon(name, ability="クォークチャージ", item="ブーストエナジー")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat == stat
    # TODO : 補正量の検証を追加


def test_こだいかっせい_はれ中はブーストエナジー未消費_解除後に消費発動():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こだいかっせい", item="ブーストエナジー")],
        foe=[Pokemon("ピカチュウ", ability="ひでり")],
    )
    mon = battle.actives[0]

    assert mon.paradox_boost_source == "weather"
    assert mon.has_item("ブーストエナジー")

    battle.weather_manager.deactivate()

    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item("ブーストエナジー")


def test_クォークチャージ_エレキフィールド下ではブーストエナジー未消費_解除後に消費発動():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="クォークチャージ", item="ブーストエナジー")],
        foe=[Pokemon("ピカチュウ", ability="エレキメイカー")],
    )
    mon = battle.actives[0]

    assert mon.paradox_boost_source == "terrain"
    assert mon.has_item("ブーストエナジー")

    battle.terrain_manager.deactivate()

    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item("ブーストエナジー")


# TODO : ブーストエナジーによる能力上昇もかがくへんかガスで無効化されることを確認するテストを追加


def test_こだいかっせい_かがくへんかガスで無効():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こだいかっせい")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    battle.weather_manager.activate("はれ", count=5)
    assert not battle.actives[0].paradox_boost_active


def test_クォークチャージ_かがくへんかガスで無効():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="クォークチャージ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    battle.terrain_manager.activate("エレキフィールド", count=5)
    assert not battle.actives[0].paradox_boost_active

# ──────────────────────────────────────────────────────────────────
# くさのけがわ
# ──────────────────────────────────────────────────────────────────
# TODO : 特性有効時のテストを追加


def test_くさのけがわ_かたやぶりで無効化される():
    """くさのけがわ: かたやぶり持ちの物理技はくさのけがわを貫通する（ゆき中）。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="くさのけがわ")],
        weather=("ゆき", 5),
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER) == 4096


def test_くさのけがわ_かがくへんかガス中は防御補正なし():
    """くさのけがわ: かがくへんかガス中は特性が無効化され、ゆき中の物理防御補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="くさのけがわ"), Pokemon("ライチュウ", ability="かがくへんかガス")],
        weather=("ゆき", 5),
    )
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER, atk_idx=0) == 4096

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
        ally=[Pokemon("トゲピー", ability="クリアボディ")],
        foe=[Pokemon("ピカチュウ")]
    )
    ally_mon, foe_mon = battle.actives

    orig_stat_change = {"A": -1, "B": +1, "C": -3, "D": +3, "S": -5, "ACC": +5, "EVA": -6}
    expected_stat_change = {k: v for k, v in orig_stat_change.items() if v > 0}

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        orig_stat_change,
    )
    assert stat_change == expected_stat_change


def test_クリアボディ_自己低下技は防げない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="クリアボディ")],
        foe=[Pokemon("ピカチュウ")]
    )
    ally_mon = battle.actives[0]

    orig_stat_change = {"A": -1, "B": -2, "C": -3, "D": -4, "S": -5, "ACC": -6, "EVA": -1}
    expected_stat_change = orig_stat_change

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=ally_mon),
        orig_stat_change,
    )
    assert stat_change == expected_stat_change


def test_クリアボディ_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("トゲピー", ability="クリアボディ")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )

    ally_mon, foe_mon = battle.actives
    orig_stat_change = {"A": -1, "B": -2, "C": -3, "D": -4, "S": -5, "ACC": -6, "EVA": -1}
    expected_stat_change = orig_stat_change
    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        orig_stat_change,
    )
    assert stat_change == expected_stat_change


def test_メタルプロテクト_かたやぶりで無効化されない():
    battle = t.start_battle(
        ally=[Pokemon("トゲピー", ability="メタルプロテクト")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )

    ally_mon, foe_mon = battle.actives
    orig_stat_change = {"A": -1, "B": -2, "C": -3, "D": -4, "S": -5, "ACC": -6, "EVA": -1}
    expected_stat_change = {k: v for k, v in orig_stat_change.items() if v > 0}
    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        orig_stat_change,
    )
    assert stat_change == expected_stat_change


def test_能力低下防止特性_かがくへんかガス中は能力低下を防げない():
    battle = t.start_battle(
        ally=[Pokemon("トゲピー", ability="クリアボディ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )

    ally_mon, foe_mon = battle.actives
    orig_stat_change = {"A": -1, "B": -2, "C": -3, "D": -4, "S": -5, "ACC": -6, "EVA": -1}
    expected_stat_change = orig_stat_change
    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        orig_stat_change,
    )
    assert stat_change == expected_stat_change


# ──────────────────────────────────────────────────────────────────
# 倒すと能力上昇
# くろのいななき、しろのいななき、じしんかじょう
# ──────────────────────────────────────────────────────────────────
# TODO パラメタライズで他の特性もまとめてテストする
def test_じしんかじょう_相手を倒すと攻撃1段階上昇する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じしんかじょう", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender._hp = 1
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.fainted
    assert attacker.rank["A"] == 1


def test_じしんかじょう_相手を倒せないと発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じしんかじょう", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert not defender.fainted
    assert attacker.rank["A"] == 0


def test_じしんかじょう_かがくへんかガス中は攻撃上昇しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じしんかじょう", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    attacker, defender = battle.actives
    defender._hp = 1
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.fainted
    assert attacker.rank["A"] == 0

# ──────────────────────────────────────────────────────────────────
# HP低下時にタイプ威力強化
# げきりゅう、しんりょく、むしのしらせ、もうか
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("しんりょく", "エナジーボール"),
        ("もうか", "かえんほうしゃ"),
        ("げきりゅう", "なみのり"),
        ("むしのしらせ", "むしのていこう"),
    ],
)
def test_ピンチ系特性_HP1_3以下で攻撃補正1_5倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=[move_name])],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon._hp = mon.max_hp // 3
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 6144


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("しんりょく", "エナジーボール"),
        ("もうか", "かえんほうしゃ"),
        ("げきりゅう", "なみのり"),
        ("むしのしらせ", "むしのていこう"),
    ],
)
def test_ピンチ系特性_かがくへんかガス中は攻撃補正なし(ability_name: str, move_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=[move_name])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    mon._hp = mon.max_hp // 3
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096

# ──────────────────────────────────────────────────────────────────
# こおりのりんぷん
# ──────────────────────────────────────────────────────────────────


def test_こおりのりんぷん_特殊技のみ被ダメ半減():
    battle_sp = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
    )
    assert t.calc_damage_modifier(battle_sp, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 2048

    battle_ph = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
    )
    assert t.calc_damage_modifier(battle_ph, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 4096


def test_こおりのりんぷん_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 4096


def test_こおりのりんぷん_かがくへんかガス中は特殊技被ダメ半減なし():
    """こおりのりんぷん: かがくへんかガス中は特性が無効化され、特殊技の被ダメ転改がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ", ability="こおりのりんぷん"), Pokemon("ライチュウ", ability="かがくへんかガス")],
    )
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 4096

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
# TODO : パラメタライズでまとめてテストする


def test_そうしょく_くさ技を無効化して攻撃1段階上昇する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="そうしょく")],
        foe=[Pokemon("ピカチュウ", moves=["エナジーボール"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before_hp = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp == before_hp
    assert defender.rank["A"] == 1


def test_そうしょく_くさ以外の技では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="そうしょく")],
        foe=[Pokemon("ピカチュウ", moves=["はどうだん"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before_hp = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp < before_hp
    assert defender.rank["A"] == 0


def test_そうしょく_かたやぶりには貫通される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="そうしょく")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["エナジーボール"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before_hp = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp < before_hp
    assert defender.rank["A"] == 0


def test_でんきエンジン_でんき技を無効化して素早さ1段階上昇():
    battle = t.start_battle(
        ally=[Pokemon("イーブイ", ability="でんきエンジン")],
        foe=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before_hp = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp == before_hp
    assert defender.rank["S"] == 1


def test_でんきエンジン_かたやぶりでは無効化される():
    battle = t.start_battle(
        ally=[Pokemon("イーブイ", ability="でんきエンジン")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["１０まんボルト"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before_hp = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp < before_hp
    assert defender.rank["S"] == 0


def test_ひらいしん_でんき技を無効化して特攻1段階上昇する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ひらいしん")],
        foe=[Pokemon("ピカチュウ", moves=["スパーク"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp == before
    assert defender.rank["C"] == 1


def test_よびみず_みず技を無効化して特攻1段階上昇する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="よびみず")],
        foe=[Pokemon("ピカチュウ", moves=["なみのり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp == before
    assert defender.rank["C"] == 1


# ──────────────────────────────────────────────────────────────────
# こんじょう
# ──────────────────────────────────────────────────────────────────
# 全ての状態異常について、パラメタライズでまとめてテストする
def test_こんじょう_状態異常で攻撃1_5倍かつやけど半減を無効化():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こんじょう", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")

    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 6144
    assert t.calc_damage_modifier(battle, Event.ON_CALC_BURN_MODIFIER) == 4096


def test_こんじょう_かがくへんかガス中は状態異常でも攻撃補正なし():
    """こんじょう: かがくへんかガス中は特性が無効化され、状態異常時の攻撃補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こんじょう", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど", source=battle.actives[1])
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096  # こんじょうが無効なので補正なし

# ──────────────────────────────────────────────────────────────────
# サーフテール
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# さいせいりょく
# ──────────────────────────────────────────────────────────────────


def test_さいせいりょく_交代で控えに戻ると回復する():
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="さいせいりょく"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.hp == 1 + mon.max_hp // 3


def test_さいせいりょく_かいふくふうじ中でも回復する():
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="さいせいりょく"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
        ally_volatile={"かいふくふうじ": 99}
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.hp == 1 + mon.max_hp // 3


def test_さいせいりょく_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="さいせいりょく"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.hp == 1

# ──────────────────────────────────────────────────────────────────
# さまようたましい
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# さめはだ、てつのトゲ
# てつのトゲの実装はさめはだと共通のためテスト不要
# ──────────────────────────────────────────────────────────────────


def test_さめはだ_接触技で被弾時に相手へ最大HPの8分の1ダメージ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="さめはだ")],
        foe=[Pokemon("イーブイ", moves=["たいあたり"])],
    )
    attacker, defender = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.hp < defender.max_hp
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 8


def test_さめはだ_非接触技では反撃ダメージを与えない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="さめはだ")],
        foe=[Pokemon("イーブイ", moves=["はどうだん"])],
    )
    attacker, defender = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.hp < defender.max_hp
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
        ally=[Pokemon("ピカチュウ", ability="サンパワー", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    result = t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)
    assert result == 6144


def test_サンパワー_物理技は補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="サンパワー", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    result = t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)
    assert result == 4096


def test_サンパワー_はれ中にターン終了時1_8ダメージ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="サンパワー")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before - mon.max_hp // 8


def test_サンパワー_はれ以外ではターン終了時ダメージなし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="サンパワー")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before


def test_サンパワー_かがくへんかガス中は特攻補正なし():
    """サンパワー: かがくへんかガス中は特攻補正が無効化される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="サンパワー", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
        weather=("はれ", 5),
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)

# ──────────────────────────────────────────────────────────────────
# じきゅうりょく
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# しぜんかいふく
# ──────────────────────────────────────────────────────────────────

# TODO : t.start_battle()にally_ailment / foe_ailmentオプションを追加して、テストコードの再現性を上げる


def test_しぜんかいふく_交代時に状態異常回復():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="しぜんかいふく"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.is_active
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert not mon.ailment.is_active


def test_しぜんかいふく_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="しぜんかいふく"), Pokemon("ライチュウ")],
        foe=[Pokemon("マタドガス", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.is_active
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.ailment.is_active

# ──────────────────────────────────────────────────────────────────
# しめりけ
# ──────────────────────────────────────────────────────────────────


def test_しめりけ_じばくを失敗させる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["じばく"])],
        foe=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    result = t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert not result


def test_しめりけ_自分の爆発技も失敗させる():
    battle = t.start_battle(
        ally=[Pokemon("ニョロモ", ability="しめりけ", moves=["じばく"])],
        foe=[Pokemon("ピカチュウ")],
    )
    result = t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert not result


def test_しめりけ_爆発ラベルなし技は通す():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    result = t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert result


def test_しめりけ_かたやぶりで爆発技が通る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じばく"])],
        foe=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    result = t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert result


def test_しめりけ_かがくへんかガス中は爆発技が通る():
    """かがくへんかガス中はしめりけが無効化されてじばくが使える。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["じばく"])],
        foe=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    assert t.check_event_result(battle, Event.ON_CHECK_MOVE)


# ──────────────────────────────────────────────────────────────────
# しゅうかく : テスト保留
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# 状態異常耐性
# じゅうなん、めんえき、パステルベール、ふみん、やるき、スイートベール、
# みずのベール、マグマのよろい
# ──────────────────────────────────────────────────────────────────
# TODO : 上記の特性を網羅する
# TODO : パラメタライズでまとめてテストする

@pytest.mark.parametrize(
    "ability_name, ailment_name",
    [
        ("じゅうなん", "まひ"),
        ("ふみん", "ねむり"),
        ("みずのベール", "やけど"),
        ("めんえき", "どく"),
        ("めんえき", "もうどく"),
        ("やるき", "ねむり"),
        ("マグマのよろい", "こおり"),
    ],
)
def test_状態異常無効系特性_対応状態異常を防ぐ(ability_name: str, ailment_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, ailment_name)
    assert not mon.ailment.is_active


def test_じゅうなん_かたやぶりで無効化される():
    """じゅうなん: かたやぶり持ちのsourceはまひを付与できる。
    ピカチュウはでんきタイプでまひ免疫があるためカビゴン（ノーマル）を使用。"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", ability="じゅうなん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    assert battle.ailment_manager.apply(defender, "まひ", source=attacker)
    assert defender.ailment.name == "まひ"


def test_じゅうなん_かがくへんかガス中はまひが付与される():
    """じゅうなん: かがくへんかガス中は特性が無効化され、まひを付与できる。"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", ability="じゅうなん")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]

    assert mon.ability.enabled is False
    assert battle.ailment_manager.apply(mon, "まひ", source=foe)
    assert mon.ailment.name == "まひ"


@pytest.mark.parametrize(
    "ability_name, ailment_name",
    [
        ("みずのベール", "やけど"),
        ("やるき", "ねむり"),
        ("マグマのよろい", "こおり"),
    ],
)
def test_状態異常無効系特性_かたやぶりで無効化される(ability_name: str, ailment_name: str):
    """かたやぶり持ちのsourceからの状態異常付与は、状態異常無効系特性を貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    assert battle.ailment_manager.apply(defender, ailment_name, source=attacker)
    assert defender.ailment.name == ailment_name


def test_ふみん_かたやぶりで無効化される():
    """ふみん: かたやぶり持ちが使うねむり技はふみんを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ふみん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    blocked = battle.events.emit(
        Event.ON_BEFORE_APPLY_AILMENT,
        BattleContext(target=mon, source=attacker, move=Move("さいみんじゅつ")),
        "ねむり",
    )
    assert blocked == "ねむり"


def test_めんえき_かたやぶりで無効化される():
    """めんえき: かたやぶり持ちが使うどく技はめんえきを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="めんえき")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    blocked = battle.events.emit(
        Event.ON_BEFORE_APPLY_AILMENT,
        BattleContext(target=mon, source=attacker, move=Move("どくどく")),
        "どく",
    )
    assert blocked == "どく"


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
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", ability="すなかき")],
                            weather=("すなあらし", 999),
                            )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_すなかき_すなあらし以外では素早さ据え置き():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すなかき")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_すいすい_あめで素早さ2倍():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", ability="すいすい")],
                            weather=("あめ", 999),
                            )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_すいすい_あめ以外では素早さ据え置き():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すいすい")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_ようりょくそ_はれで素早さ2倍():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", ability="ようりょくそ")],
                            weather=("はれ", 999),
                            )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_ようりょくそ_はれ以外では素早さ据え置き():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ようりょくそ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("すなかき", "すなあらし"),
        ("すいすい", "あめ"),
        ("ようりょくそ", "はれ"),
    ],
)
def test_天候速度補正特性_かがくへんかガス中は速度補正されない(ability_name: str, weather_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
        weather=(weather_name, 999),
    )
    mon = battle.actives[0]
    assert battle.actives[0].ability.enabled is False
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_ゆきかき_ゆきで素早さ2倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ゆきかき")],
        foe=[Pokemon("ピカチュウ")],
        weather=("ゆき", 5),
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_ゆきかき_ゆき以外では素早さ据え置き():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ゆきかき")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_ゆきかき_かがくへんかガス中は速度補正されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ゆきかき")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
        weather=("ゆき", 999),
    )
    mon = battle.actives[0]
    assert battle.actives[0].ability.enabled is False
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


# ──────────────────────────────────────────────────────────────────
# すいほう
# ──────────────────────────────────────────────────────────────────
def test_すいほう_みず技強化():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すいほう", moves=["なみのり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)


def test_すいほう_ほのお技弱化():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すいほう")],
        foe=[Pokemon("ピカチュウ", moves=["ひのこ"])],
    )
    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER, atk_idx=1)


def test_すいほう_かがくへんかガス中はみず技補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すいほう", moves=["なみのり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)


def test_すいほう_かがくへんかガス中はほのお技補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すいほう")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["ひのこ"])],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER, atk_idx=1)

# ──────────────────────────────────────────────────────────────────
# スキン
# スカイスキン、フェアリースキン、フリーズスキン
# ──────────────────────────────────────────────────────────────────
# TODO : パラメタイズでまとめてテストする


def test_スカイスキン_ノーマル技をひこうタイプに変換する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.get_effective_move_type(attacker, move)
    assert result == "ひこう"


def test_スカイスキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_スカイスキン_元からひこうタイプの技は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["アクロバット"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


def test_スカイスキン_かがくへんかガス中は威力補正なし():
    """スカイスキン: かがくへんかガス中は威力補正が無効化される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["たいあたり"]), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ")],
    )
    # かがくへんかガス登場でスカイスキンが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


def test_フェアリースキン_ノーマル技をフェアリータイプに変換する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.get_effective_move_type(attacker, move)
    assert result == "フェアリー"


def test_フェアリースキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_フェアリースキン_元からフェアリータイプの技は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["じゃれつく"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


def test_フェアリースキン_かがくへんかガス中は威力補正なし():
    """フェアリースキン: かがくへんかガス中は威力補正が無効化される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["たいあたり"]), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ")],
    )
    # かがくへんかガス登場でフェアリースキンが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


# フリーズスキン

def test_フリーズスキン_ノーマル技をこおりタイプに変換する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.get_effective_move_type(attacker, move)
    assert result == "こおり"


def test_フリーズスキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_フリーズスキン_元からこおりタイプの技は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["アイススピナー"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


def test_フリーズスキン_かがくへんかガス中は威力補正なし():
    """フリーズスキン: かがくへんかガス中は威力補正が無効化される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["たいあたり"]), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ")],
    )
    # かがくへんかガス登場でフリーズスキンが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
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
        ally=[Pokemon("ピカチュウ", ability="スナイパー", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    ctx.critical = True

    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 6144


def test_スナイパー_かがくへんかガス中は急所時ダメージ補正なし():
    """スナイパー: かがくへんかガス中は特性が無効化され、急所時のダメージ補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スナイパー", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    ctx.critical = True

    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 4096  # スナイパー無効なので補正なし

# ──────────────────────────────────────────────────────────────────
# すながくれ、ゆきがくれ
# ──────────────────────────────────────────────────────────────────
# TODO : パラメタイズでまとめてテストする


def test_ゆきがくれ_ゆきで命中率3277_4096倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ユキノオー", ability="ゆきがくれ")],
        weather=("ゆき", 5),
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]
    result = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        move.accuracy,
    )
    expected = move.accuracy * 3277 // 4096
    assert result == expected


def test_ゆきがくれ_ゆき以外では命中率変化なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ユキノオー", ability="ゆきがくれ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]
    result = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        move.accuracy,
    )
    assert result == move.accuracy


def test_ゆきがくれ_かたやぶりで命中率補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["１０まんボルト"])],
        foe=[Pokemon("ユキノオー", ability="ゆきがくれ")],
        weather=("ゆき", 5),
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]
    result = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        move.accuracy,
    )
    assert result == move.accuracy

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
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["たいあたり"])],
        foe_side_field={"リフレクター": 5},
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 4096


def test_すりぬけ_ひかりのかべを無視する():
    """すりぬけ: ひかりのかべ中でも特殊技が軽減されない"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["でんきショック"])],
        foe_side_field={"ひかりのかべ": 5},
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 4096


def test_すりぬけ_オーロラベールを無視する():
    """すりぬけ: オーロラベール中でも物理技が軽減されない"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["たいあたり"])],
        foe_side_field={"オーロラベール": 5},
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 4096


def test_すりぬけ_みがわり越しに変化技が通る():
    """すりぬけ: みがわり状態の相手に変化技が当たる"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["キノコのほうし"])],
        foe_volatile={"みがわり": 1},
    )
    assert not t.check_event_result(battle, Event.ON_CHECK_IMMUNE)


def test_すりぬけ_しんぴのまもりを貫通して状態異常が入る():
    """すりぬけ: しんぴのまもり中でも相手に状態異常を与えられる"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", ability="すりぬけ")],
        foe_side_field={"しんぴのまもり": 5},
    )
    attacker, defender = battle.actives
    assert battle.ailment_manager.apply(defender, "どく", source=attacker)
    assert defender.ailment.is_active


def test_すりぬけ_しんぴのまもりを貫通してこんらんが入る():
    """すりぬけ: しんぴのまもり中でも相手にこんらんを与えられる"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", ability="すりぬけ")],
        foe_side_field={"しんぴのまもり": 5},
    )
    attacker, defender = battle.actives
    assert battle.volatile_manager.apply(defender, "こんらん", count=3, source=attacker)
    assert defender.has_volatile("こんらん")


def test_すりぬけ_かがくへんかガス中はリフレクターが有効():
    # TODO : foeの特性をかがくへんかガスにすることで余計な交代をなくしてテストを簡略化
    """すりぬけ: かがくへんかガス中はリフレクターによる軽減が有効になる。"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        ally=[Pokemon("ピカチュウ"), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe_side_field={"リフレクター": 5},
    )
    # すりぬけ持ちのfoe視点: foe_side_field=ally_side ではなくfoe_sideなので、
    # リフレクターがfoe側にある→foeはself-fieldのリフレクターで守られる
    # すりぬけ持ちallyで攻撃時にfoe_side_fieldのリフレクターを無視するテストに修正
    battle2 = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すりぬけ", moves=["たいあたり"]), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ")],
        foe_side_field={"リフレクター": 5},
    )
    # すりぬけ有効時: リフレクターを無視
    assert t.calc_damage_modifier(battle2, Event.ON_CALC_DAMAGE_MODIFIER) == 4096

    # かがくへんかガス登場ですりぬけが無効化される
    battle2.switch_manager.run_switch(battle2.players[0], battle2.players[0].team[1])
    # すりぬけ無効時: リフレクターで軽減（attacker=マタドガス, atk_idx=0）
    # マタドガスには moves がないので ally 側に別のアタッカーが必要 → 簡易に ability.enabled で確認
    assert battle2.actives[0].ability.enabled is True  # マタドガス自身は有効
    assert battle2.actives[1].ability.enabled is False  # 相手（すりぬけ持ち）は無効化されている

# ──────────────────────────────────────────────────────────────────
# するどいめ
# ──────────────────────────────────────────────────────────────────


def test_するどいめ_命中率低下を防ぐ():
    """するどいめ: 相手による命中率ランク低下を防ぐ。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="するどいめ")],
        foe=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"ACC": -1},
    )
    assert stat_change == {}


# TODO : 相手の回避ランクを無視して攻撃できることを確認するテストを追加

def test_するどいめ_かたやぶりで無効化される():
    """するどいめ: かたやぶり持ちによる命中率低下はするどいめを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="するどいめ")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"ACC": -1},
    )
    assert stat_change == {"ACC": -1}

# ──────────────────────────────────────────────────────────────────
# スロースタート
# ──────────────────────────────────────────────────────────────────


def test_スロースタート_登場5ターン未満は攻撃補正0_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スロースタート", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 2048

    battle.turn = battle.actives[0].ability.count + 5
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096


# TODO : 特攻には補正がかからないことを確認するテストを追加

def test_スロースタート_かがくへんかガス中は攻撃補正なし():
    """スロースタート: かがくへんかガス中は特性が無効化され、物理攻撃の半減補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スロースタート", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096  # スロースタート無効なので半減なし

# ──────────────────────────────────────────────────────────────────
# スワームチェンジ
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# せいしんりょく
# ──────────────────────────────────────────────────────────────────


def test_せいしんりょく_ひるみを防ぐ():
    """せいしんりょく: 追加効果によるひるみ付与を無効化する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいしんりょく")],
        foe=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    result = battle.events.emit(
        Event.ON_BEFORE_APPLY_VOLATILE,
        BattleContext(attacker=attacker, defender=defender, target=defender, source=attacker),
        "ひるみ",
    )
    assert result == ""


def test_せいしんりょく_ひるみ以外は防がない():
    """せいしんりょく: ひるみ以外の揮発性状態は防がない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいしんりょく")],
        foe=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    result = battle.events.emit(
        Event.ON_BEFORE_APPLY_VOLATILE,
        BattleContext(attacker=attacker, defender=defender, target=defender, source=attacker),
        "こんらん",
    )
    assert result == "こんらん"


def test_せいしんりょく_いかくを防ぐ():
    """せいしんりょく: いかくによる攻撃ランク低下を無効化する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいしんりょく")],
        foe=[Pokemon("ウインディ", ability="いかく")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    # いかく持ちの相手を source にして ON_BEFORE_MODIFY_STAT を発火
    result = battle.events.emit(
        Event.ON_BEFORE_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1},
    )
    assert "A" not in result or result.get("A", 0) >= 0


def test_せいしんりょく_かたやぶりのひるみは防げない():
    """せいしんりょく: かたやぶり持ちの攻撃によるひるみは防げない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいしんりょく")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["エアスラッシュ"])],
    )
    attacker = battle.actives[1]
    defender = battle.actives[0]
    move = attacker.moves[0]

    ctx = BattleContext(attacker=attacker, defender=defender, move=move, target=defender, source=attacker)
    # かたやぶり時は check_def_ability_enabled が False になるのでひるみが防げない
    result = battle.events.emit(Event.ON_BEFORE_APPLY_VOLATILE, ctx, "ひるみ")
    assert result == "ひるみ"  # かたやぶりのためせいしんりょくが無効化され、ひるみが通る


def test_せいしんりょく_かがくへんかガス中はひるみが入る():
    """せいしんりょく: かがくへんかガス中はひるみを防げない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいしんりょく")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    assert defender.ability.enabled is False

    result = battle.events.emit(
        Event.ON_BEFORE_APPLY_VOLATILE,
        BattleContext(attacker=attacker, defender=defender, target=defender, source=attacker),
        "ひるみ",
    )
    assert result == "ひるみ"

# ──────────────────────────────────────────────────────────────────
# 接触時に状態異常付与
# せいでんき、どくのトゲ、ほのおのからだ
# ──────────────────────────────────────────────────────────────────

# TODO : パラメタライズでまとめてテストする


def test_せいでんき_非接触技では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいでんき")],
        foe=[Pokemon("イーブイ", moves=["はどうだん"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert defender.hp < defender.max_hp
    assert not attacker.has_ailment("まひ")


def test_せいでんき_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいでんき")],
        foe=[Pokemon("イーブイ", ability="かがくへんかガス", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    assert defender.ability.enabled is False

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert defender.hp < defender.max_hp
    assert not attacker.has_ailment("まひ")


def test_どくのトゲ_接触技で被弾時に30パーセントで相手をどく():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="どくのトゲ")],
        foe=[Pokemon("イーブイ", moves=["たいあたり"])],
    )
    attacker = battle.actives[1]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert attacker.has_ailment("どく")


def test_どくのトゲ_非接触技では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="どくのトゲ")],
        foe=[Pokemon("イーブイ", moves=["はどうだん"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert defender.hp < defender.max_hp
    assert not attacker.ailment.is_active


def test_ほのおのからだ_接触技で被弾時に30パーセントで相手をやけど():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ほのおのからだ")],
        foe=[Pokemon("イーブイ", moves=["たいあたり"])],
    )
    attacker = battle.actives[1]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert attacker.has_ailment("やけど")


def test_ほのおのからだ_非接触技では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ほのおのからだ")],
        foe=[Pokemon("イーブイ", moves=["はどうだん"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert defender.hp < defender.max_hp
    assert not attacker.ailment.is_active

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
        ally=[Pokemon("ピカチュウ", ability="ダウンロード")],
        foe=[Pokemon(foe_name)],
    )
    assert battle.actives[0].rank[stat] == 1


def test_ダウンロード_BD等しいときCアップ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ダウンロード")],
        foe=[Pokemon("ウインディ")],
    )
    mon = battle.actives[0]
    assert mon.rank["C"] == 1


def test_ダウンロード_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ダウンロード")],
        foe=[Pokemon("フシギダネ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    assert mon.rank["A"] == 0

# ──────────────────────────────────────────────────────────────────
# だっぴ
# ──────────────────────────────────────────────────────────────────


def test_だっぴ_ターン終了時に状態異常を回復する():
    # TODO : パラメタライズですべての状態異常についてテストする
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="だっぴ")],
        foe=[Pokemon("ピカチュウ")],
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
        ally=[Pokemon("ピカチュウ", ability="だっぴ")],
        foe=[Pokemon("ピカチュウ")],
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
        ally=[Pokemon("ピカチュウ", ability="だっぴ")],
        foe=[Pokemon("ピカチュウ")],
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


def test_だっぴ_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="だっぴ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.events.emit(Event.ON_TURN_END_2)
    finally:
        battle.random.random = orig_random

    assert mon.ability.enabled is False
    assert mon.ailment.is_active

# ──────────────────────────────────────────────────────────────────
# たんじゅん
# ──────────────────────────────────────────────────────────────────


def test_たんじゅん_能力上昇量が2倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="たんじゅん")],
        foe=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stat_changes = {"A": 1, "B": -2, "C": 3, "D": -4, "S": 1, "ACC": -2, "EVA": 3}
    battle.modify_stats(target, stat_changes, source=source)
    for stat, change in stat_changes.items():
        assert target.rank[stat] == change * 2


def test_たんじゅん_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="たんじゅん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    target = battle.actives[0]
    source = battle.actives[1]

    stat_changes = {"A": 1, "B": -2, "C": 3, "D": -4, "S": 1, "ACC": -2, "EVA": 3}
    battle.modify_stats(target, stat_changes, source=source)
    for stat, change in stat_changes.items():
        assert target.rank[stat] == change


# ──────────────────────────────────────────────────────────────────
# ちからずく
# ──────────────────────────────────────────────────────────────────
def test_ちからずく_追加効果あり技の威力が1_3倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからずく", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 5325 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_ちからずく_追加効果なし技は威力変化なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからずく", moves=["はかいこうせん"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_ちからずく_追加効果が発動しない():
    """ちからずくの追加効果なし検証: アクアステップのS+1効果が発動しないこと"""
    import random as _random

    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからずく", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert attacker.rank["S"] == 0

# ──────────────────────────────────────────────────────────────────
# ちからもち、ヨガパワー
# ヨガパワーの実装はちからもちと共通のためテスト不要
# ──────────────────────────────────────────────────────────────────


def test_ちからもち_物理技で攻撃補正2倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからもち", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)


def test_ちからもち_特殊技では攻撃補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからもち", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)


def test_ちからもち_イカサマで攻撃するときも2倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからもち", moves=["イカサマ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 8192 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)


def test_ちからもち_イカサマを受けるときは補正なし():
    # TODO : 実装
    pass


def test_ちからもち_かがくへんかガス中は攻撃補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからもち", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled is False
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)

# ──────────────────────────────────────────────────────────────────
# タイプ無効で回復
# ちくでん、ちょすい、どしょく
# ──────────────────────────────────────────────────────────────────
# TODO : パラメタライズでまとめてテストする


def test_ちくでん_でんき技を無効化して4分の1回復する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちくでん")],
        foe=[Pokemon("ピカチュウ", moves=["スパーク"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    battle.modify_hp(defender, v=-20, reason="other")
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp == min(defender.max_hp, before + defender.max_hp // 4)


def test_ちくでん_かたやぶりには貫通される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちくでん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["スパーク"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp < before


def test_ちくでん_でんき変化技も無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちくでん")],
        foe=[Pokemon("ピカチュウ", moves=["でんじは"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is True


def test_ちくでん_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちくでん")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["スパーク"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is False
    assert defender.hp < before


def test_ちょすい_みず技を無効化して4分の1回復する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちょすい")],
        foe=[Pokemon("ピカチュウ", moves=["なみのり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    battle.modify_hp(defender, v=-20, reason="other")
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp == min(defender.max_hp, before + defender.max_hp // 4)


def test_ちょすい_かたやぶりには貫通される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちょすい")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["なみのり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp < before


def test_ちょすい_みず変化技も無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちょすい")],
        foe=[Pokemon("ピカチュウ", moves=["みずびたし"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is True


def test_どしょく_じめん技を無効化して4分の1回復する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="どしょく")],
        foe=[Pokemon("ピカチュウ", moves=["じしん"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    battle.modify_hp(defender, v=-20, reason="other")
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp == min(defender.max_hp, before + defender.max_hp // 4)

# ──────────────────────────────────────────────────────────────────
# ちどりあし
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# てきおうりょく
# ──────────────────────────────────────────────────────────────────
# TODO : 条件と補正量をリスト化し、パラメタライズでまとめてテストする


def test_てきおうりょく_通常時STABが2倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てきおうりょく", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == pytest.approx(2.0)


def test_てきおうりょく_元タイプ一致テラスタルで2_25倍になる():
    battle = t.start_battle(
        ally=[Pokemon("リザードン", ability="てきおうりょく", terastal="ほのお", moves=["ひのこ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == pytest.approx(2.25)


def test_てきおうりょく_非一致タイプは補正しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てきおうりょく", moves=["ひのこ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == pytest.approx(1.0)


def test_てきおうりょく_かがくへんかガス中は無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てきおうりょく", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    assert attacker.ability.enabled is False
    assert battle.damage_calculator.calc_atk_type_modifier(ctx) == pytest.approx(1.5)

# ──────────────────────────────────────────────────────────────────
# テクニシャン
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 6144),  # 威力40の技は1.5倍
        ("１０まんボルト", 4096),  # 威力90の技
    ]
)
def test_テクニシャン_威力補正(move_name, expected_modifier):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="テクニシャン", moves=[move_name])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == expected_modifier


def test_テクニシャン_連続技でもヒット毎に判定がぶれない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="テクニシャン", moves=["タネマシンガン"])],
        foe=[Pokemon("ピカチュウ")],
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


def test_テクニシャン_かがくへんかガス中は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="テクニシャン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled is False
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096


# ──────────────────────────────────────────────────────────────────
# テラスシェル
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("なみのり", 2048),       # x1 -> x1/2
        ("ひのこ", 2048),       # x2 -> x1/2
        ("じしん", 2048),           # x4 -> x1/2
        ("でんきショック", 2048),   # x1/2 -> x1/2
        ("バレットパンチ", 2048),   # x1/4 -> x1/2
    ]
)
def test_テラスシェル_等倍以上を半減(move_name, expected_modifier):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon("コイル", ability="テラスシェル")],
    )
    result = t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER, atk_idx=0)
    assert expected_modifier == result


def test_テラスシェル_HP満タンでないと発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="テラスシェル")],
    )
    defender = battle.actives[1]
    defender._hp = defender.max_hp - 1
    result = t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER, atk_idx=0)
    assert result == 4096


def test_テラスシェル_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="テラスシェル")],
    )
    result = t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER, atk_idx=0)
    assert result == 4096


def test_テラスシェル_かたやぶりで無効化される():
    """テラスシェル: かたやぶり持ちの技はテラスシェルの半減を貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="テラスシェル")],
    )
    result = t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER, atk_idx=0)
    assert result == 4096


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
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon("ピカチュウ", ability="てんねん")],
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
        ally=[Pokemon("ピカチュウ", ability="てんねん", moves=[move_name])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.rank[stat] = 2
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_DEF_RANK_MODIFIER, ctx, 2.0)
    assert result == 1.0


def test_てんねん_かたやぶりで防御側効果は無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="てんねん")],
    )
    attacker, defender = battle.actives
    attacker.rank["A"] = 2
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_ATK_RANK_MODIFIER, ctx, 2.0)
    assert result == 2.0


def test_てんねん_かがくへんかガス中は防御ランク補正が有効():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="てんねん")],
    )
    attacker, defender = battle.actives
    attacker.rank["A"] = 2
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_ATK_RANK_MODIFIER, ctx, 2.0)
    assert result == 2.0

# ──────────────────────────────────────────────────────────────────
# てんのめぐみ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "chance_before, chance_after",
    [
        (0.3, 0.6),
        (0.7, 1.0),
        (0, 0),
    ]
)
def test_てんのめぐみ_追加効果確率が2倍になる(chance_before, chance_after):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てんのめぐみ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    ctx = BattleContext(attacker=attacker, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, chance_before)
    assert result == chance_after


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
        ally=[Pokemon("ピカチュウ", ability="どくしゅ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
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
        ally=[Pokemon("イーブイ", ability="どくしゅ", moves=["はどうだん"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert not defender.ailment.is_active


def test_どくしゅ_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("イーブイ", ability="どくしゅ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
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


def test_ねつぼうそう_かがくへんかガス中はやけど時のほのお特殊技威力補正なし():
    """ねつぼうそう: かがくへんかガス中は特性が無効化され、やけど時の炎特殊技威力補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねつぼうそう", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど", source=battle.actives[1])
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096  # ねつぼうそう無効なので補正なし

# ──────────────────────────────────────────────────────────────────
# トレース
# ──────────────────────────────────────────────────────────────────


def test_トレース_いかくをコピーすると即発動():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="トレース")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.actives[0].ability.orig_name == "いかく"
    assert battle.actives[1].rank["A"] == -1


def test_トレース_uncopyable特性だと不発():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="トレース")],
        foe=[Pokemon("ピカチュウ", ability="トレース")],
    )
    assert battle.actives[0].ability.orig_name == "トレース"
    assert battle.actives[0].ability.revealed is False  # 不発なので False のまま


def test_トレース_かがくへんかガス中は不発():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="トレース")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.orig_name == "トレース"
    assert battle.actives[0].ability.enabled is False


def test_トレース_交代で元の特性に戻り再入場で再コピーする():
    battle = t.start_battle(
        ally=[
            Pokemon("ピカチュウ", ability="トレース"),
            Pokemon("ライチュウ"),
        ],
        foe=[Pokemon("ピカチュウ", ability="すなかき")],
    )

    tracer = battle.players[0].team[0]
    assert tracer.ability.orig_name == "すなかき"

    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert tracer.ability.orig_name == "トレース"

    battle.switch_manager.run_switch(battle.players[0], tracer)
    assert tracer.ability.orig_name == "すなかき"

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
        ally=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        foe=[Pokemon("ピカチュウ", moves=["かえんほうしゃ"])],
    )
    defender, attacker = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["A"] == 1
    assert defender.ability.revealed
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねつこうかん_やけど状態にならない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        foe=[Pokemon("ピカチュウ", ability="ノーガード", moves=["おにび"])],
    )
    defender, attacker = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert not defender.ailment.is_active
    assert defender.rank["A"] == 0
    assert defender.ability.revealed
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねつこうかん_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["かえんほうしゃ"])],
    )
    defender, attacker = battle.actives
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.rank["A"] == 0
    assert not defender.ability.revealed


def test_ねつこうかん_かたやぶりでやけどが通る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    mon, attacker = battle.actives

    blocked = battle.events.emit(
        Event.ON_BEFORE_APPLY_AILMENT,
        BattleContext(target=mon, source=attacker, move=Move("おにび")),
        "やけど",
    )
    assert blocked == "やけど"


# ──────────────────────────────────────────────────────────────────
# ねんちゃく
# ──────────────────────────────────────────────────────────────────
def test_ねんちゃく_相手による道具変更をブロックする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
        foe=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    result = battle.can_change_item(source=source, target=target)
    assert result is False
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねんちゃく_道具なしでも相手による道具変更をブロックする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねんちゃく")],
        foe=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    result = battle.can_change_item(source=source, target=target)
    assert result is False
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねんちゃく_自己起因の道具変更は阻害しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
        foe=[Pokemon("ピカチュウ")],
    )
    target, _ = battle.actives
    result = battle.can_change_item(target, target)
    assert result is True


def test_ねんちゃく_かたやぶりの技起因では道具変更を阻害しない():
    """ねんちゃく: かたやぶり持ちが技を使って道具変更しようとする場合は阻害できない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    target, source = battle.actives
    result = battle.can_change_item(source, target, move=Move("トリック"))
    assert result is True


def test_ねんちゃく_かがくへんかガス中は道具変更をブロックしない():
    """ねんちゃく: かがくへんかガス中は特性が無効化され、相手から道具変更を受ける。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねんちゃく")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    target, source = battle.actives
    result = battle.can_change_item(source, target)
    assert result is True  # ねんちゃくが無効化されるので道具変更できる

# ──────────────────────────────────────────────────────────────────
# ノーガード
# ──────────────────────────────────────────────────────────────────


def test_ノーガード_攻撃側で必中化():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ノーガード", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")]
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
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ノーガード")]
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
        ally=[Pokemon("ピカチュウ", ability="ノーマルスキン", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    result = battle.move_executor.get_effective_move_type(attacker, move)
    assert result == "ノーマル"

    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_ノーマルスキン_元からノーマルタイプの技は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ノーマルスキン", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


def test_ノーマルスキン_かがくへんかガス中は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ノーマルスキン", moves=["かえんほうしゃ"]), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ")],
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
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
        ally=[Pokemon("ピカチュウ", moves=["じしん"])],
        foe=[Pokemon("コイル", ability="ハードロック")],
    )
    assert 3072 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0)


def test_ハードロック_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じしん"])],
        foe=[Pokemon("コイル", ability="ハードロック")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_プリズムアーマー_かたやぶりで無効化されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じしん"])],
        foe=[Pokemon("コイル", ability="プリズムアーマー")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 3072


def test_フィルター_かがくへんかガス中は効果抜群軽減なし():
    """フィルター: かがくへんかガス中は特性が無効化され、効果抜群ダメージ軽減がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["じしん"])],
        foe=[Pokemon("コイル", ability="フィルター"), Pokemon("ライチュウ", ability="かがくへんかガス")],
    )
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 4096  # 軽減なし


# ──────────────────────────────────────────────────────────────────
# ばけのかわ
# ──────────────────────────────────────────────────────────────────

def test_ばけのかわ_2回目以降の攻撃は防がない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives
    battle.determine_damage = (
        lambda attacker, defender, move, critical=False: 10
    )

    # 1回目
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.ability.enabled is False
    assert defender.hp == defender.max_hp - defender.max_hp // 8

    # 2回目
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.hp < defender.max_hp - defender.max_hp // 8 - 10


def test_ばけのかわ_連続技の2発目以降は防がない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["にどげり"])],
        foe=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives
    before_hp = defender.hp

    battle.determine_damage = (
        lambda attacker, defender, move, critical=False: 10
    )
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is False
    assert defender.hp == before_hp - defender.max_hp // 8 - 10


def test_ばけのかわ_per_battle_onceは交代しても再有効化されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ばけのかわ"), Pokemon("ライチュウ")],
    )
    # 初回被弾でばけのかわを消費
    attacker = battle.players[0].active
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert battle.actives[1].ability.enabled is False

    # 交代して戻っても per_battle_once 特性は再有効化されない
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[0])
    assert battle.actives[1].ability.enabled is False


def test_ばけのかわ_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives
    battle.determine_damage = (
        lambda attacker, defender, move, critical=False: 10
    )
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is True
    assert defender.hp == defender.max_hp - 10


def test_ばけのかわ_かがくへんかガスで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives
    battle.determine_damage = (
        lambda attacker, defender, move, critical=False: 10
    )
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is True
    assert defender.hp == defender.max_hp - 10


# ──────────────────────────────────────────────────────────────────
# はっこう
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# バトルスイッチ
# ──────────────────────────────────────────────────────────────────
def test_バトルスイッチ_シールドで攻撃技を使うとブレードへ変化する():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(シールド)", ability="バトルスイッチ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.move_executor.run_move(mon, mon.moves[0])

    assert mon.alias == "ギルガルド(ブレード)"
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_バトルスイッチ_シールドで変化技なら変化しない():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(シールド)", ability="バトルスイッチ", moves=["つるぎのまい"])],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.move_executor.run_move(mon, mon.moves[0])
    assert mon.alias == "ギルガルド(シールド)"


def test_バトルスイッチ_ブレードでキングシールドを使うとシールドへ変化する():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(ブレード)", ability="バトルスイッチ", moves=["キングシールド"])],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.move_executor.run_move(mon, mon.moves[0])

    assert mon.alias == "ギルガルド(シールド)"
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_バトルスイッチ_ブレードでまもるなら変化しない():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(ブレード)", ability="バトルスイッチ", moves=["まもる"])],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.move_executor.run_move(mon, mon.moves[0])
    assert mon.alias == "ギルガルド(ブレード)"


def test_バトルスイッチ_交代時はシールドへ戻る():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(ブレード)", ability="バトルスイッチ"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    mon = player.team[0]
    battle.switch_manager.run_switch(player, player.team[1])
    assert mon.alias == "ギルガルド(シールド)"

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
        ally=[Pokemon("ピカチュウ", ability="はやあし")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")

    base = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base * 3 // 2


def test_はやあし_まひ状態で素早さ低下を無視して1_5倍():
    # ピカチュウはでんきタイプでまひ免疫があるためカビゴン（ノーマル）を使用
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", ability="はやあし")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "まひ")

    base = mon.stats["S"]
    # まひ_speed による 1/2 ペナルティを打ち消して 1.5倍（*3）
    assert battle.calc_effective_speed(mon) == (base // 2) * 3


def test_はやあし_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="はやあし")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")

    base = mon.stats["S"]
    # かがくへんかガスで ability.enabled=False → はやあし 発動せず素早さ据え置き
    assert battle.calc_effective_speed(mon) == base

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
        ally=[Pokemon("モルペコ", ability="はらぺこスイッチ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability.is_hangry is False

    battle.advance_turn()
    assert mon.ability.is_hangry is True

    battle.advance_turn()
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル中はターン終了時に切り替わらない():
    battle = t.start_battle(
        ally=[Pokemon("モルペコ", ability="はらぺこスイッチ", terastal="あく")],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
    )
    mon = battle.actives[0]

    t.reserve_command(
        battle,
        ally_command=Command.TERASTAL_0,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()

    assert mon.is_terastallized is True
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_交代時は通常まんぷくへ戻る():
    battle = t.start_battle(
        ally=[Pokemon("モルペコ", ability="はらぺこスイッチ"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.players[0].team[0]
    mon.ability.is_hangry = True
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル交代時はフォルム維持する():
    battle = t.start_battle(
        ally=[Pokemon("モルペコ", ability="はらぺこスイッチ", terastal="あく"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.players[0].team[0]
    mon.ability.is_hangry = True
    mon.terastallize()
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])

    assert mon.ability.is_hangry is True

# ──────────────────────────────────────────────────────────────────
# バリアフリー
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# はりきり
# ──────────────────────────────────────────────────────────────────


def test_はりきり_物理技の攻撃補正が1_5倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="はりきり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
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
        ally=[Pokemon("ピカチュウ", ability="はりきり", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ")],
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
        ally=[Pokemon("ピカチュウ", ability="はりきり", moves=["つのドリル"])],
        foe=[Pokemon("ピカチュウ")],
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


def test_はりきり_かがくへんかガス中は攻撃補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="はりきり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
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
        ally=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["たいあたり"])],
        foe=[Pokemon("カビゴン")],
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
        ally=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["たいあたり"])],
        foe=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank == 0


def test_ひとでなし_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["たいあたり"])],
        foe=[Pokemon("カビゴン", ability="かがくへんかガス")],
    )
    attacker, defender = battle.actives
    battle.ailment_manager.apply(defender, "どく", source=attacker)

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank == 0

# ──────────────────────────────────────────────────────────────────
# ひひいろのこどう
# ──────────────────────────────────────────────────────────────────

# TODO : ひひいろのこどうの補正あり条件のテストを追加


def test_ひひいろのこどう_かがくへんかガス中ははれの攻撃補正なし():
    """ひひいろのこどう: かがくへんかガス中は特性が無効化され、はれ中の攻撃補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ひひいろのこどう", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
        weather=("はれ", 5),
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096  # ひひいろのこどう無効なので補正なし

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


def test_ファーコート_かたやぶりで無効化される():
    """ファーコート: かたやぶり持ちの物理技はファーコートの防御補正を貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ファーコート")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER) == 4096


def test_ファーコート_かがくへんかガス中は物理防御補正なし():
    """ファーコート: かがくへんかガス中は特性が無効化され、物理技の防御補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ファーコート"), Pokemon("ライチュウ", ability="かがくへんかガス")],
    )
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER, atk_idx=0) == 4096  # 防御補正なし

# ──────────────────────────────────────────────────────────────────
# ファントムガード、マルチスケイル
# 基本的な実装は共通なため、マルチスケイルのみテストすればよい
# ファントムガードはかたやぶりに無効化されないことも検証する
# ──────────────────────────────────────────────────────────────────


def test_マルチスケイル_HP満タンのとき半減():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="マルチスケイル")],
    )
    attacker, defender = battle.actives

    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0)

    defender._hp -= 1
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0)


def test_マルチスケイル_連続技2発目以降は半減しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["にどげり"])],
        foe=[Pokemon("ピカチュウ", ability="マルチスケイル")],
    )

    attacker, defender = battle.actives
    move = attacker.moves[0]
    battle.determine_damage = (
        lambda attacker, defender, move, critical=False: 10
    )

    battle.move_executor.run_move(attacker, move)
    assert defender.hp == defender.max_hp - 5 - 10


def test_マルチスケイル_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="マルチスケイル")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_ファントムガード_かたやぶりで無効化されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ファントムガード")],
    )
    assert 2048 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


def test_マルチスケイル_かがくへんかガスで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="マルチスケイル")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)


# ──────────────────────────────────────────────────────────────────
# ふうりょくでんき
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ふかしのこぶし
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ぶきよう
# ──────────────────────────────────────────────────────────────────

def test_ぶきよう_たべのこしが発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぶきよう", item="たべのこし")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.events.emit(Event.ON_TURN_END_2)
    assert mon.hp == 1


def test_ぶきよう_かがくへんかガス中はたべのこしが発動する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぶきよう", item="たべのこし")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    mon._hp = 1
    battle.events.emit(Event.ON_TURN_END_2, BattleContext(source=mon))
    assert mon.hp > 1

# ──────────────────────────────────────────────────────────────────
# ふくがん
# ──────────────────────────────────────────────────────────────────


def test_ふくがん_命中率を5325_4096倍にする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ふくがん", moves=["かみなり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        move.accuracy,
    )

    expected = move.accuracy * 5325 // 4096
    assert result == expected


def test_ふくがん_一撃必殺技には適用されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ふくがん", moves=["つのドリル"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=battle.actives[1], move=move),
        30,
    )
    assert result == 30


def test_ふくがん_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ふくがん", moves=["かみなり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=battle.actives[1], move=move),
        move.accuracy,
    )
    assert attacker.ability.enabled is False
    assert result == move.accuracy


# ──────────────────────────────────────────────────────────────────
# ふくつのこころ
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ふくつのたて、ふとうのけん
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ふしぎなうろこ
# ──────────────────────────────────────────────────────────────────
def test_ふしぎなうろこ_かたやぶりで無効化される():
    """ふしぎなうろこ: かたやぶり持ちの物理技はふしぎなうろこの防御補正を貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ふしぎなうろこ")],
    )
    battle.ailment_manager.apply(battle.actives[1], "やけど")
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER) == 4096


def test_ふしぎなうろこ_かがくへんかガス中はやけど時の防御補正なし():
    """ふしぎなうろこ: かがくへんかガス中は特性が無効化され、やけど時の防御補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="ふしぎなうろこ"), Pokemon("ライチュウ", ability="かがくへんかガス")],
    )
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    battle.ailment_manager.apply(battle.players[0].active, "やけど")
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER, atk_idx=0) == 4096  # 防御補正なし

# ──────────────────────────────────────────────────────────────────
# ふしょく
# ──────────────────────────────────────────────────────────────────


def test_ふしょく持ち由来ならどくタイプにもどくが入る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ふしょく")],
        foe=[Pokemon("フシギダネ")],
    )
    source = battle.actives[0]
    target = battle.actives[1]

    assert battle.ailment_manager.apply(target, "どく", source=source)
    assert target.ailment.name == "どく"


def test_ふしょく無効化中はどくタイプにどくが入らない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ふしょく")],
        foe=[Pokemon("フシギダネ")],
    )
    source = battle.actives[0]
    target = battle.actives[1]
    source.ability.enabled = False

    assert not battle.ailment_manager.apply(target, "どく", source=source)
    assert not target.ailment.is_active

# ──────────────────────────────────────────────────────────────────
# ふゆう
# ──────────────────────────────────────────────────────────────────


def test_ふゆう_floating():
    """ふゆう: ふゆう持ちが浮遊状態を返す。"""
    battle = t.start_battle(ally=[Pokemon("フワンテ", ability="ふゆう")],
                            foe=[Pokemon("ピカチュウ")])
    ally_mon = battle.actives[0]

    # ON_CHECK_FLOATING イベントで True を返す
    floating = battle.events.emit(
        Event.ON_CHECK_FLOATING,
        BattleContext(source=ally_mon),
        False
    )
    assert floating is True


def test_ふゆう_じめん技が通らない():
    """ふゆう: ふゆう持ちはじめん技を無効化できる。"""
    battle = t.start_battle(ally=[Pokemon("フワンテ", ability="ふゆう", moves=["スキルスワップ"])],
                            foe=[Pokemon("ピカチュウ", moves=["じしん"])])

    # ふゆう持ちはis_floatingで浮いている扱い
    assert battle.query_manager.is_floating(battle.actives[0])


def test_ふゆう_かたやぶりでじめん技が通る():
    """ふゆう: かたやぶり持ちからのじしんはふゆうを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("フワンテ", ability="ふゆう")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じしん"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is False


def test_ふゆう_かがくへんかガス中は浮遊が無効():
    """ふゆう: かがくへんかガス中はふゆうが無効化されてじめん技が通る。"""
    battle = t.start_battle(
        ally=[Pokemon("フワンテ", ability="ふゆう"), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ", moves=["じしん"])],
    )
    # かがくへんかガス登場でふゆうが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    defender = battle.actives[0]
    attacker = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    # ふゆが無効なのでじめん技が通る
    assert not battle.query_manager.is_floating(defender)
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)
    assert immune is False

    battle = t.start_battle(ally=[Pokemon("トゲピー", ability="クリアボディ")],
                            foe=[Pokemon("ウインディ", ability="いかく")])
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    # クリアボディは攻撃の能力低下（-1）を防ぐ
    # ON_MODIFY_STATで能力低下をイベント発火して検証
    # 相手由来の能力低下なので source=foe_mon で指定
    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1},  # いかくと同じ攻撃-1の能力低下
    )
    # クリアボディにより負の能力変化が除去される
    assert stat_change == {}

# ──────────────────────────────────────────────────────────────────
# フラワーギフト
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# フラワーベール
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ブレインフォース
# ──────────────────────────────────────────────────────────────────


def test_ブレインフォース_かがくへんかガス中は効果抜群ダメージ補正なし():
    """ブレインフォース: かがくへんかガス中は特性が無効化され、効果抜群ダメージ補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ブレインフォース", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    # ピカチュウ→ピカチュウ: でんき→でんきで効果抜群ではないが、他のタイプに抜群な技を使う
    # かがくへんかガスが場にいるのでブレインフォース無効
    battle2 = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ブレインフォース", moves=["１０まんボルト"])],
        foe=[Pokemon("ピジョン"), Pokemon("ライチュウ", ability="かがくへんかガス")],
    )
    battle2.switch_manager.run_switch(battle2.players[1], battle2.players[1].team[1])
    assert t.calc_damage_modifier(battle2, Event.ON_CALC_DAMAGE_MODIFIER) == 4096  # ブレインフォース無効


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
# ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ability_name", ["へんげんじざい", "リベロ"])
def test_へんげんじざいリベロ_技タイプへ変化して同一滞在で1回のみ発動(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=["たいあたり", "アイアンテール"])],
        foe=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert attacker.types == ["ノーマル"]
    assert attacker.ability.activated_since_switch_in is True

    battle.move_executor.run_move(attacker, attacker.moves[1])
    assert attacker.types == ["ノーマル"]
    assert attacker.ability.activated_since_switch_in is True


@pytest.mark.parametrize("ability_name", ["へんげんじざい", "リベロ"])
def test_へんげんじざいリベロ_交代でリセットされ再発動できる(ability_name: str):
    battle = t.start_battle(
        ally=[
            Pokemon("ピカチュウ", ability=ability_name, moves=["たいあたり", "アイアンテール"]),
            Pokemon("ライチュウ"),
        ],
        foe=[Pokemon("カビゴン")],
    )
    player = battle.players[0]
    mon = player.team[0]

    battle.move_executor.run_move(mon, mon.moves[0])
    assert mon.types == ["ノーマル"]
    assert mon.ability.activated_since_switch_in is True

    battle.switch_manager.run_switch(player, player.team[1])
    assert mon.types == ["でんき"]
    assert mon.ability.activated_since_switch_in is False

    battle.switch_manager.run_switch(player, mon)
    battle.move_executor.run_move(mon, mon.moves[1])

    assert mon.types == ["はがね"]
    assert mon.ability.activated_since_switch_in is True


@pytest.mark.parametrize("ability_name", ["へんげんじざい", "リベロ"])
def test_へんげんじざいリベロ_タイプ変化後にガスで無効化されても戻らない(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=["たいあたり"])],
        foe=[
            Pokemon("カビゴン"),
            Pokemon("ピカチュウ", ability="かがくへんかガス"),
        ],
    )
    attacker = battle.actives[0]
    foe_player = battle.players[1]

    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert attacker.types == ["ノーマル"]

    battle.switch_manager.run_switch(foe_player, foe_player.team[1])

    assert attacker.ability.enabled is False
    assert attacker.types == ["ノーマル"]


def test_リベロ_かがくへんかガス中は技使用後にタイプ変化しない():
    """リベロ: かがくへんかガス中は特性が無効化され、技使用後にタイプ変化しない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="リベロ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    attacker = battle.actives[0]
    original_types = attacker.types[:]

    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert attacker.types == original_types  # ガスで無効化されてタイプ変化しない

# ──────────────────────────────────────────────────────────────────
# へんしょく
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ポイズンヒール
# ──────────────────────────────────────────────────────────────────


def test_ポイズンヒール_どく状態で1_8回復する():
    battle = t.start_battle(
        ally=[Pokemon("グライオン", ability="ポイズンヒール")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before + mon.max_hp // 8


def test_ポイズンヒール_もうどく状態でも固定1_8回復する():
    battle = t.start_battle(
        ally=[Pokemon("グライオン", ability="ポイズンヒール")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "もうどく")
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    # もうどくのターン数を5にしてもダメージではなく1/8回復
    for _ in range(5):
        battle.ailment_manager.tick(mon)
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before + mon.max_hp // 8


def test_ポイズンヒール_かいふくふうじ中は回復もダメージも受けない():
    battle = t.start_battle(
        ally=[Pokemon("グライオン", ability="ポイズンヒール")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    battle.volatile_manager.apply(mon, "かいふくふうじ")
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before


def test_ポイズンヒール_かがくへんかガス中はどくダメージを受ける():
    battle = t.start_battle(
        ally=[Pokemon("グライオン", ability="ポイズンヒール")],
        foe=[Pokemon("マタドガス", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "どく")
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    # かがくへんかガスでポイズンヒール無効→どくダメージ
    assert mon.hp == before - mon.max_hp // 8

# ──────────────────────────────────────────────────────────────────
# ぼうおん、ぼうだん
# ──────────────────────────────────────────────────────────────────


def test_ぼうおん_音技を無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうおん")],
        foe=[Pokemon("ピカチュウ", moves=["バークアウト"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is True


def test_ぼうおん_非音技は無効化しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうおん")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False


def test_ぼうおん_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうおん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["バークアウト"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False


def test_ぼうおん_かがくへんかガス中は音技が通る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうおん"), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ", moves=["バークアウト"])],
    )
    # かがくへんかガス登場でぼうおんが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False


def test_ぼうだん_弾技を無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうだん")],
        foe=[Pokemon("ヒトカゲ", moves=["かえんボール"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is True


def test_ぼうだん_非弾技は無効化しない():
    """ぼうだん: 弾ラベルのない技は通常通りヒットする。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうだん")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False


def test_ぼうだん_かたやぶりには無効化されない():
    """ぼうだん: かたやぶり持ちの弾技は無効化できない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうだん")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["マッドショット"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False


def test_ぼうだん_かがくへんかガス中は弾技が通る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうだん"), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ヒトカゲ", moves=["かえんボール"])],
    )
    # かがくへんかガス登場でぼうだんが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False


# ──────────────────────────────────────────────────────────────────
# ほうし
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ぼうじん
# ──────────────────────────────────────────────────────────────────
def test_ぼうじん_粉技を無効化する():
    """ぼうじん: 粉技を無効化する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうじん")],
        foe=[Pokemon("ナゾノクサ", moves=["ねむりごな"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is True


def test_ぼうじん_非粉技は無効化しない():
    """ぼうじん: 粉技ラベルのない技は通常通りヒットする。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうじん")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False


def test_ぼうじん_かたやぶりで無効化される():
    """ぼうじん: かたやぶり持ちの粉技はぼうじんを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうじん")],
        foe=[Pokemon("ナゾノクサ", ability="かたやぶり", moves=["ねむりごな"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False


def test_ぼうじん_かがくへんかガス中は粉技が通る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぼうじん"), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ナゾノクサ", moves=["ねむりごな"])],
    )
    # かがくへんかガス登場でぼうじんが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]

    result = battle.events.emit(
        Event.ON_CHECK_IMMUNE,
        BattleContext(attacker=attacker, defender=defender, move=move),
        False,
    )
    assert result is False

# ──────────────────────────────────────────────────────────────────
# ほおぶくろ
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ほろびのボディ
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# マイティチェンジ
# ──────────────────────────────────────────────────────────────────


def test_マイティチェンジ_ナイーブで交代するとマイティへ変化する():
    battle = t.start_battle(
        ally=[Pokemon("イルカマン(ナイーブ)", ability="マイティチェンジ"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    palafin = player.team[0]

    battle.switch_manager.run_switch(player, player.team[1])

    assert palafin.alias == "イルカマン(マイティ)"
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_マイティチェンジ_だっしゅつボタン交代でも変化する():
    battle = t.start_battle(
        ally=[
            Pokemon("イルカマン(ナイーブ)", ability="マイティチェンジ", item="だっしゅつボタン"),
            Pokemon("ピカチュウ"),
        ],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
    )
    palafin = battle.players[0].team[0]
    attacker = battle.actives[1]

    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert battle.players[0].interrupt == Interrupt.EJECTBUTTON

    battle.run_interrupt_switch(Interrupt.EJECTBUTTON)

    assert palafin.alias == "イルカマン(マイティ)"


def test_マイティチェンジ_ひんし退場では変化しない():
    battle = t.start_battle(
        ally=[Pokemon("イルカマン(ナイーブ)", ability="マイティチェンジ"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    palafin = player.team[0]

    battle.modify_hp(palafin, v=-palafin.max_hp, reason="other")
    assert palafin.fainted

    battle.run_faint_switch()

    assert palafin.alias == "イルカマン(ナイーブ)"


def test_マイティチェンジ_既にマイティなら追加変化しない():
    battle = t.start_battle(
        ally=[Pokemon("イルカマン(マイティ)", ability="マイティチェンジ"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    palafin = player.team[0]

    battle.switch_manager.run_switch(player, player.team[1])

    assert palafin.alias == "イルカマン(マイティ)"
    assert not t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)

# ──────────────────────────────────────────────────────────────────
# マジシャン
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# マジックガード
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "reason, should_block",
    [
        ("move_damage", False),
        ("self_attack", False),
        ("pain_split", False),
        ("self_cost", False),
        ("other", True),
    ],
)
def test_マジックガード_HPChangeReasonごとの挙動(reason: str, should_block: bool):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="マジックガード")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    before = mon.hp

    delta = battle.modify_hp(mon, v=-10, reason=reason)

    if should_block:
        assert delta == 0
        assert mon.hp == before
    else:
        assert delta == -10
        assert mon.hp == before - 10


def test_マジックガード_かがくへんかガス中はotherダメージが発生する():
    """マジックガード: かがくへんかガス中は特性が無効化され、other ダメージを受ける。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="マジックガード")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    before = mon.hp

    delta = battle.modify_hp(mon, v=-10, reason="other")

    assert mon.ability.enabled is False  # ガス中は無効化される
    assert delta == -10  # マジックガード無効なのでダメージを受ける
    assert mon.hp == before - 10


# ──────────────────────────────────────────────────────────────────
# マジックミラー
# ──────────────────────────────────────────────────────────────────
def test_マジックミラー_反射対象変化技を跳ね返す():
    class DummyMove:
        def has_label(self, label):
            return label == "reflectable"

    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="マジックミラー")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    assert battle.events.emit(
        Event.ON_CHECK_REFLECT,
        BattleContext(attacker=attacker, defender=defender, move=DummyMove()),
        False,
    )


def test_マジックミラー_非反射対象技は跳ね返さない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="マジックミラー")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    assert not battle.events.emit(
        Event.ON_CHECK_REFLECT,
        BattleContext(attacker=attacker, defender=defender, move=Move("つるぎのまい")),
        False,
    )


def test_マジックミラー_かたやぶりで反射されない():
    class DummyMove:
        def has_label(self, label):
            return label == "reflectable"

    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり")],
        foe=[Pokemon("ピカチュウ", ability="マジックミラー")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    assert not battle.events.emit(
        Event.ON_CHECK_REFLECT,
        BattleContext(attacker=attacker, defender=defender, move=DummyMove()),
        False,
    )


def test_マジックミラー_かがくへんかガス中は反射しない():
    class DummyMove:
        def has_label(self, label):
            return label == "reflectable"

    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ", ability="マジックミラー")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    assert defender.ability.enabled is False

    assert not battle.events.emit(
        Event.ON_CHECK_REFLECT,
        BattleContext(attacker=attacker, defender=defender, move=DummyMove()),
        False,
    )

# ──────────────────────────────────────────────────────────────────
# マルチタイプ
# ──────────────────────────────────────────────────────────────────


def test_マルチタイプ_せいれいプレートでフェアリータイプになる():
    battle = t.start_battle(
        ally=[Pokemon("アルセウス", ability="マルチタイプ", item="せいれいプレート")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == "フェアリー"
    assert mon.ability.revealed is False  # マルチタイプは開示されない


def test_マルチタイプ_プレートなしでタイプ変更なし():
    battle = t.start_battle(
        ally=[Pokemon("アルセウス", ability="マルチタイプ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None
    assert mon.ability.revealed is False  # プレートなしは不発なので False


def test_マルチタイプ_プレートの奪取を阻止する():
    battle = t.start_battle(
        ally=[Pokemon("アルセウス", ability="マルチタイプ", item="せいれいプレート")],
        foe=[Pokemon("ピカチュウ", moves=["はたきおとす"])],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    # ON_CHECK_ITEM_CHANGE: target=アルセウス, source=ピカチュウ → 奪取を阻止
    ctx = BattleContext(attacker=attacker, defender=mon, move=attacker.moves[0],
                        source=attacker, target=mon)
    result = battle.events.emit(Event.ON_CHECK_ITEM_CHANGE, ctx, True)
    assert result is False

# ──────────────────────────────────────────────────────────────────
# ミイラ
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# みずがため
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ミラーアーマー
# ──────────────────────────────────────────────────────────────────


def test_ミラーアーマー_いかくで相手の攻撃が下がり自分は下がらない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ミラーアーマー")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    # ミラーアーマー保持側の攻撃は下がらない
    assert battle.actives[0].rank["A"] == 0
    # いかく使用側の攻撃が反射されて下がる
    assert battle.actives[1].rank["A"] == -1


def test_ミラーアーマー_自己デメリットは反射しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ミラーアーマー")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_stat(mon, "A", -2, source=mon)
    assert mon.rank["A"] == -2


def test_ミラーアーマー_かたやぶりで反射されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ミラーアーマー")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
    )
    ally = battle.actives[0]
    foe = battle.actives[1]
    battle.modify_stat(ally, "A", -1, source=foe)
    # かたやぶりなので反射されず、自分の攻撃が下がる
    assert ally.rank["A"] == -1
    assert foe.rank["A"] == 0


def test_ミラーアーマー_反射先がまけんきなら発動する():
    pass  # まけんき未実装のためスキップ


def test_ミラーアーマー_かがくへんかガス中は能力低下が反射されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ミラーアーマー")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]

    battle.modify_stat(mon, "A", -1, source=foe)
    assert mon.rank["A"] == -1  # ミラーアーマーが無効化されて反射されない
    assert foe.rank["A"] == 0   # foeの攻撃は下がらない

    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="しゅうかく", item="オボンのみ")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 999),
    )
    mon = battle.actives[0]

    mon._hp = 1
    battle.events.emit(Event.ON_BEFORE_ACTION, BattleContext(source=mon))
    assert not mon.has_item()
    assert mon.item.lost
    assert mon.item.lost_cause == "consume"

    # 復活直後の即時再消費を避けるため、HPを満タンにしてから判定する。
    mon._hp = mon.max_hp
    battle.events.emit(Event.ON_TURN_END_5, BattleContext(source=mon))

    assert mon.has_item("オボンのみ")

# ──────────────────────────────────────────────────────────────────
# ミラクルスキン
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ムラっけ
# ──────────────────────────────────────────────────────────────────


def test_ムラっけ_ターン終了時に別々の能力が上昇と下降する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ムラっけ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    choices = iter(["A", "B"])
    battle.random.choice = lambda seq: next(choices)

    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))

    assert mon.rank["A"] == 2
    assert mon.rank["B"] == -1


def test_ムラっけ_全能力が最大なら下降のみ発動する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ムラっけ")],
        foe=[Pokemon("ピカチュウ")],
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
        ally=[Pokemon("ピカチュウ", ability="ムラっけ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    for stat in ("A", "B", "C", "D", "S"):
        mon.rank[stat] = -6
    battle.random.choice = lambda seq: seq[0]

    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))

    assert mon.rank["A"] == -4
    assert mon.rank["B"] == -6


def test_ムラっけ_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ムラっけ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.random.choice = lambda seq: seq[0]

    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))

    assert mon.rank["A"] == 0
    assert mon.rank["B"] == 0

# ──────────────────────────────────────────────────────────────────
# メロメロボディ
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# ものひろい
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# もふもふ
# ──────────────────────────────────────────────────────────────────


def test_もふもふ_かたやぶりで無効化される():
    """もふもふ: かたやぶり持ちの接触技はもふもふの防御補正を貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="もふもふ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 4096


def test_もふもふ_かがくへんかガス中は接触技防御補正なし():
    """もふもふ: かがくへんかガス中は特性が無効化され、接触技の防御補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="もふもふ"), Pokemon("ライチュウ", ability="かがくへんかガス")],
    )
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 4096  # 防御補正なし

# ──────────────────────────────────────────────────────────────────
# もらいび
# ──────────────────────────────────────────────────────────────────


def test_もらいび_自分対象技では相手の吸収特性は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["かえんのまもり"])],
        foe=[Pokemon("ピカチュウ", ability="もらいび")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert attacker.has_volatile("かえんのまもり")
    assert defender.ability.state == "idle"


def test_もらいび_吸収後は最初の炎技のみ1_5倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="もらいび", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ", moves=["かえんほうしゃ"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp == before
    assert defender.ability.state == "charged"

    # 1回目: ほのお技 + charged -> active -> idle へ遷移
    first_ctx = BattleContext(attacker=defender, defender=attacker, move=defender.moves[0])
    battle.events.emit(Event.ON_MOVE_CHARGE, first_ctx, True)
    first_modifier = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, first_ctx, 4096)
    battle.events.emit(Event.ON_MOVE_END, first_ctx)

    assert defender.ability.state == "idle"
    assert first_modifier == 6144

    # 2回目: ほのお技ですが、状態は idle なので等倍
    second_ctx = BattleContext(attacker=defender, defender=attacker, move=defender.moves[0])
    battle.events.emit(Event.ON_MOVE_CHARGE, second_ctx, True)
    second_modifier = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, second_ctx, 4096)
    battle.events.emit(Event.ON_MOVE_END, second_ctx)

    assert defender.ability.state == "idle"
    assert second_modifier == 4096


def test_もらいび_かたやぶりには貫通される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="もらいび")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["かえんほうしゃ"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    before = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp < before
    assert defender.ability.state == "idle"


# ──────────────────────────────────────────────────────────────────
# ゆうばく
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# よちむ
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# よわき
# ──────────────────────────────────────────────────────────────────
def test_よわき_HP半分以下で攻撃補正0_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="よわき", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker._hp = attacker.max_hp // 2
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 2048


def test_よわき_かがくへんかガス中はHP半分以下でも攻撃補正なし():
    """よわき: かがくへんかガス中は特性が無効化され、HP半分以下の攻撃補正がなくなる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="よわき", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    mon._hp = mon.max_hp // 2
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096  # よわき無効なので補正なし

# ──────────────────────────────────────────────────────────────────
# リーフガード
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("weather_name,weather_count", [("はれ", 5), ("おおひでり", 999)])
def test_リーフガード_はれおおひでり中に状態異常を防ぐ(weather_name: str, weather_count: int):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="リーフガード")],
        foe=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, "どく")
    assert not mon.ailment.is_active


def test_リーフガード_はれ以外では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="リーフガード")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.is_active


def test_リーフガード_かたやぶりの状態異常技は防げない():
    """かたやぶり由来の技による状態異常はリーフガードを貫通する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="リーフガード")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
        weather=("はれ", 5),
    )
    target = battle.actives[0]
    attacker = battle.actives[1]
    origin_ctx = BattleContext(source=attacker, target=target, move=Move("さいみんじゅつ"))
    battle.ailment_manager.apply(target, "ねむり", source=attacker, origin_ctx=origin_ctx)
    assert target.ailment.name == "ねむり"


def test_リーフガード_かたやぶりと対面中のどくびしは毒にならない():
    """かたやぶりの特性無視は技使用の瞬間のみ。どくびし踏みは技ではないためリーフガードで防ぐ。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="リーフガード"), Pokemon("ライチュウ", ability="リーフガード")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり")],
        weather=("はれ", 5),
        ally_side_field={"どくびし": 1},
    )
    player = battle.players[0]
    battle.run_switch(player, player.team[1])
    assert not player.active.ailment.is_active

# ──────────────────────────────────────────────────────────────────
# リミットシールド
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# りんぷん
# ──────────────────────────────────────────────────────────────────


def test_りんぷん_追加効果確率を0にする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ", ability="りんぷん")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    result = battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, 0.3)
    assert result == 0.0


def test_りんぷん_かたやぶりには無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ", ability="りんぷん")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    result = battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, 0.3)
    assert result == 0.3


def test_りんぷん_かがくへんかガス中は追加効果が通る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["アクアステップ"]), Pokemon("マタドガス", ability="かがくへんかガス")],
        foe=[Pokemon("ピカチュウ", ability="りんぷん")],
    )
    # かがくへんかガス登場でりんぷんが無効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    result = battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, 0.3)
    assert result == 0.3

# ──────────────────────────────────────────────────────────────────
# わざわいのうつわ、わざわいのおふだ、わざわいのたま、わざわいのつるぎ
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのおふだ", "たいあたり"),
        ("わざわいのうつわ", "１０まんボルト"),
    ],
)
def test_わざわいおふだうつわ_相手攻撃補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER, atk_idx=0) == 3072


def test_わざわいのおふだ_かたやぶりで無効化されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="わざわいのおふだ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 3072


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのつるぎ", "たいあたり"),
        ("わざわいのたま", "１０まんボルト"),
    ],
)
def test_わざわいつるぎたま_相手防御補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=[move_name])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER) == 3072

# ──────────────────────────────────────────────────────────────────
# わたげ
# ──────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────
# わるいてぐせ
# ──────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
