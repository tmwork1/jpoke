"""特性ハンドラの単体テスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event
from jpoke.model import Move

import test_utils as t


def _set_raw_stats(mon: Pokemon, a: int, b: int, c: int, d: int, s: int):
    mon._stats_manager.stats[1] = a
    mon._stats_manager.stats[2] = b
    mon._stats_manager.stats[3] = c
    mon._stats_manager.stats[4] = d
    mon._stats_manager.stats[5] = s


def test_ありじごく_非浮遊相手は交代不可():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="ありじごく")],
    )
    assert not t.can_switch(battle, 0)


def test_ありじごく_浮遊相手は交代可能():
    battle = t.start_battle(
        ally=[Pokemon("ピジョン"), Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="ありじごく")],
    )
    assert t.can_switch(battle, 0)


def test_いかく_登場時に相手攻撃1段階ダウン():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.actives[0].rank["A"] == -1


def test_かげふみ_かげふみ持ち以外は交代不可():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="かげふみ")],
    )
    assert not t.can_switch(battle, 0)


def test_かげふみ_ゴーストタイプは交代可能():
    battle = t.start_battle(
        ally=[Pokemon("ゲンガー"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="かげふみ")],
    )
    assert t.can_switch(battle, 0)


def test_かちき_相手による能力低下で特攻2段階アップ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[0].rank["C"] == 2


def test_かちき_自分由来の能力低下では発動しない():
    battle = t.start_battle(ally=[Pokemon("ピカチュウ", ability="かちき")])
    mon = battle.actives[0]
    battle.modify_stat(mon, "A", -1, source=mon)
    assert mon.rank["C"] == 0


def test_かがくへんかガス_登場中はいかくが不発():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いかく")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled is False
    assert battle.actives[1].ability.enabled is True
    assert battle.actives[1].rank["A"] == 0


def test_かがくへんかガス_解除後は特性が再び有効化される():
    battle = t.start_battle(
        ally=[
            Pokemon("ピカチュウ", ability="かがくへんかガス"),
            Pokemon("ライチュウ"),
        ],
        foe=[
            Pokemon("ピカチュウ", ability="いかく"),
            Pokemon("ライチュウ"),
        ],
    )

    # ガス発生中は相手のいかくが無効
    assert battle.actives[1].ability.enabled is False

    # ガス持ちを引っ込めると、相手の特性は有効化される
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert battle.actives[1].ability.enabled is True

    # 相手のいかく持ちが再登場すると、いかくが発動する
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[0])
    assert battle.actives[0].rank["A"] == -1


def test_かがくへんかガス_とくせいガード持ちは無効化されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いかく", item="とくせいガード")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled is True


def test_こだいかっせい_はれで発動する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こだいかっせい")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 999),
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "weather"


def test_クォークチャージ_場条件なしならブーストエナジーを消費する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="クォークチャージ", item="ブーストエナジー")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.item.enabled


def test_こだいかっせい_はれ中はブーストエナジー未消費_解除後に消費発動():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こだいかっせい", item="ブーストエナジー")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 999),
    )
    mon = battle.actives[0]

    # start_battle は初期交代後に天候を設定するため、テスト前提を再構築する。
    mon.item = "ブーストエナジー"
    mon.paradox_item_activated_once = False
    mon.paradox_boost_active = False
    mon.paradox_boost_source = ""
    mon.paradox_boost_stat = ""
    battle.refresh_paradox_boost_states()

    assert mon.paradox_boost_source == "weather"
    assert mon.item.enabled

    battle.weather_manager.deactivate()

    assert mon.paradox_boost_active
    assert mon.paradox_boost_source == "item"
    assert not mon.item.enabled


def test_こだいかっせい_同値時は攻撃優先で上昇能力を選ぶ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こだいかっせい")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 999),
    )
    mon = battle.actives[0]
    _set_raw_stats(mon, a=200, b=200, c=100, d=100, s=100)

    mon.paradox_boost_active = False
    mon.paradox_boost_source = ""
    mon.paradox_boost_stat = ""
    battle.refresh_paradox_boost_states()

    assert mon.paradox_boost_stat == "A"


def test_クォークチャージ_素早さ上昇が実効素早さに反映される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="クォークチャージ")],
        foe=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 999),
    )
    mon = battle.actives[0]
    _set_raw_stats(mon, a=100, b=100, c=100, d=100, s=220)

    mon.paradox_boost_active = False
    mon.paradox_boost_source = ""
    mon.paradox_boost_stat = ""
    battle.refresh_paradox_boost_states()

    assert mon.paradox_boost_stat == "S"
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 6144 // 4096


def test_こだいかっせい_かがくへんかガス中は補正停止_解除後に復帰する():
    battle = t.start_battle(
        ally=[
            Pokemon("ピカチュウ", ability="こだいかっせい", moves=["でんこうせっか"]),
            Pokemon("ライチュウ"),
        ],
        foe=[
            Pokemon("ピカチュウ"),
            Pokemon("ピカチュウ", ability="かがくへんかガス"),
        ],
        weather=("はれ", 999),
    )
    mon = battle.actives[0]
    _set_raw_stats(mon, a=220, b=100, c=100, d=100, s=100)
    mon.paradox_boost_active = False
    mon.paradox_boost_source = ""
    mon.paradox_boost_stat = ""
    battle.refresh_paradox_boost_states()

    assert mon.paradox_boost_stat == "A"
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 5325

    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])

    assert battle.actives[0].ability.enabled is False
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096

    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[0])

    assert battle.actives[0].ability.enabled is True
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 5325


def test_きんちょうかん_相手をきんちょうかん状態にする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="きんちょうかん")],
    )
    assert battle.query_manager.is_nervous(battle.actives[0])


def test_きんちょうかん_相手が持っていなければ無効():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    assert not battle.query_manager.is_nervous(battle.actives[0])


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


def test_すなかき_すなあらしで素早さ2倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すなかき")],
        weather=("すなあらし", 999),
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"] * 2


def test_すなかき_すなあらし以外では素早さ据え置き():
    battle = t.start_battle(ally=[Pokemon("ピカチュウ", ability="すなかき")])
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_ぜったいねむり_登場時にねむり状態になる():
    battle = t.start_battle(ally=[Pokemon("ピカチュウ", ability="ぜったいねむり")])
    assert battle.actives[0].ailment.name == "ねむり"


def test_グラスメイカー_登場時にグラスフィールド展開():
    battle = t.start_battle(ally=[Pokemon("ピカチュウ", ability="グラスメイカー")])
    assert battle.terrain.name == "グラスフィールド"


def test_てつのこぶし_パンチ技威力補正():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["かみなりパンチ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 4915 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_てつのこぶし_パンチ技以外は補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_どんかん_指定状態をイベント段階で無効化():
    battle = t.start_battle(ally=[Pokemon("ピカチュウ", ability="どんかん")])
    mon = battle.actives[0]
    blocked = battle.events.emit(
        Event.ON_BEFORE_APPLY_AILMENT,
        BattleContext(target=mon, source=battle.actives[1]),
        "メロメロ",
    )
    allowed = battle.events.emit(
        Event.ON_BEFORE_APPLY_AILMENT,
        BattleContext(target=mon, source=battle.actives[1]),
        "どく",
    )
    assert blocked == ""
    assert allowed == "どく"


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
    battle = t.start_battle(ally=[Pokemon("ピカチュウ", ability=ability_name)])
    mon = battle.actives[0]
    assert not battle.ailment_manager.apply(mon, ailment_name)
    assert not mon.ailment.is_active


def test_マイペース_状態異常は防がない_現実装確認():
    battle = t.start_battle(ally=[Pokemon("ピカチュウ", ability="マイペース")])
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく")
    assert mon.ailment.name == "どく"


def test_おうごんのからだ_相手の変化技を無効化():
    """おうごんのからだ: ON_CHECK_IMMUNE イベントで相手の変化技を無効化。"""
    battle = t.start_battle(
        ally=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    # 相手が使う変化技「あまいかおり」で判定
    ctx = BattleContext(attacker=foe_mon, defender=ally_mon, move=Move("あまいかおり"))
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is True


def test_おうごんのからだ_攻撃技は無効化しない():
    """おうごんのからだ: ON_CHECK_IMMUNE イベントで攻撃技は無効化しない。"""
    battle = t.start_battle(
        ally=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    # 攻撃技「アイアンテール」では無効化されない
    ctx = BattleContext(attacker=foe_mon, defender=ally_mon, move=Move("アイアンテール"))
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is False


def test_おうごんのからだ_自分対象の変化技は無効化しない():
    """おうごんのからだ: 自分対象の変化技は無効化しない（自分自身の技）。"""
    from jpoke.model import Move

    battle = t.start_battle(
        ally=[Pokemon("サーフゴー", ability="おうごんのからだ")],
        foe=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]

    # 自分が使う自分対象の変化技
    ctx = BattleContext(attacker=ally_mon, defender=ally_mon, move=Move("かたくなる"))
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is False


def test_おうごんのからだ_場が対象の技は無効化しない():
    """おうごんのからだ: 場が対象の技は無効化しない。"""
    battle = t.start_battle(
        ally=[Pokemon("サーフゴー", ability="おうごんのからだ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    # 場が対象の技「くろいきり」では無効化されない
    ctx = BattleContext(attacker=foe_mon, defender=ally_mon, move=Move("くろいきり"))
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
