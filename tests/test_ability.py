"""特性ハンドラの単体テスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event, Interrupt, LogCode, Command
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


def test_ぎゃくじょう_HP半分超から半分以下で特攻1段階アップ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぎゃくじょう")],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    damage = defender.max_hp - defender.max_hp // 2
    battle.determine_damage = lambda *_args, **_kwargs: damage

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["C"] == 1
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ぎゃくじょう_被弾前HPが半分以下なら発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぎゃくじょう")],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
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
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["でんこうせっか"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    damage = defender.max_hp - defender.max_hp // 2
    battle.determine_damage = lambda *_args, **_kwargs: damage

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is False
    assert defender.rank["C"] == 0


def test_ききかいひ_HP半分超から半分以下で割り込み交代する():
    battle = t.start_battle(
        ally=[Pokemon("コソクムシ", ability="ききかいひ"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
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
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
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


def test_しゅうかく_晴れならターン終了時に必ず復活する():
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


def test_しゅうかく_持ち物があると発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="しゅうかく", item="ラムのみ")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 999),
    )
    mon = battle.actives[0]

    battle.events.emit(Event.ON_TURN_END_5, BattleContext(source=mon))

    assert mon.has_item("ラムのみ")


def test_しゅうかく_ノーてんきエアロック下は晴れでも50パーセント判定():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="しゅうかく", item="オボンのみ")],
        foe=[Pokemon("ピカチュウ", ability="エアロック")],
        weather=("はれ", 999),
    )
    mon = battle.actives[0]

    mon._hp = 1
    battle.events.emit(Event.ON_BEFORE_ACTION, BattleContext(source=mon))
    assert not mon.has_item()

    original_random = battle.random.random
    battle.random.random = lambda: 0.9
    try:
        battle.events.emit(Event.ON_TURN_END_5, BattleContext(source=mon))
    finally:
        battle.random.random = original_random

    assert not mon.has_item()


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
    mon.paradox_boost_active = False
    mon.paradox_boost_source = ""
    mon.paradox_boost_stat = None
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
    mon.paradox_boost_stat = None
    battle.refresh_paradox_boost_states()

    assert mon.paradox_boost_stat == "A"


def test_こだいかっせい_天候変化時の発動順は素早さ順():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こだいかっせい")],
        foe=[Pokemon("ピカチュウ", ability="こだいかっせい")],
    )

    _set_raw_stats(battle.actives[0], a=100, b=100, c=100, d=100, s=90)
    _set_raw_stats(battle.actives[1], a=100, b=100, c=100, d=100, s=180)
    battle.event_logger.clear()

    battle.weather_manager.activate("はれ", 999)

    logs = [
        log for log in battle.event_logger.logs
        if log.log.name == "ABILITY_TRIGGERED" and log.payload.get("ability") == "こだいかっせい"
    ]
    assert [log.idx for log in logs] == [1, 0]


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
    mon.paradox_boost_stat = None
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
    mon.paradox_boost_stat = None
    battle.refresh_paradox_boost_states()

    assert mon.paradox_boost_stat == "A"
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 5325

    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])

    assert battle.actives[0].ability.enabled is False
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096

    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[0])

    assert battle.actives[0].ability.enabled is True
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 5325


@pytest.mark.parametrize("ability_name, field", [
    ("こだいかっせい", ("weather", "はれ")),
    ("クォークチャージ", ("terrain", "エレキフィールド")),
])
def test_パラドックス特性_かがくへんかガスで無効化される(ability_name: str, field: tuple[str, str]):
    kwargs = {
        "ally": [Pokemon("ピカチュウ", ability=ability_name), Pokemon("ライチュウ")],
        "foe": [Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability="かがくへんかガス")],
    }
    if field[0] == "weather":
        kwargs["weather"] = (field[1], 999)
    else:
        kwargs["terrain"] = (field[1], 999)

    battle = t.start_battle(**kwargs)
    paradox_mon = battle.actives[0]

    # 場条件で通常発動することを確認
    battle.refresh_paradox_boost_states()
    assert paradox_mon.paradox_boost_active

    # かがくへんかガス持ちを繰り出すと、特性自体が無効化される
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    assert battle.actives[0].ability.enabled is False


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


def test_ねんちゃく_相手起因の道具変更をブロックする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
    )
    self_mon, foe = battle.actives

    result = battle.can_change_item(foe, self_mon)

    assert result is False
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねんちゃく_道具なしでも相手起因の道具変更をブロックする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねんちゃく")],
    )
    self_mon, foe = battle.actives

    result = battle.can_change_item(foe, self_mon)

    assert result is False
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねんちゃく_自己起因の道具変更は阻害しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
    )
    self_mon, _ = battle.actives

    result = battle.can_change_item(self_mon, self_mon)

    assert result is True


def test_ぶきよう_たべのこしは発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぶきよう", item="たべのこし")],
    )
    mon = battle.actives[0]

    mon._hp = mon.max_hp - 20
    before_hp = mon.hp
    battle.events.emit(Event.ON_TURN_END_2, BattleContext(source=mon))

    assert mon.hp == before_hp
    assert mon.has_item("たべのこし")


def test_ぶきよう_かがくへんかガス中はたべのこしが発動する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぶきよう", item="たべのこし")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]

    mon._hp = mon.max_hp - 20
    before_hp = mon.hp
    battle.events.emit(Event.ON_TURN_END_2, BattleContext(source=mon))

    assert mon.hp > before_hp
    assert mon.has_item("たべのこし")


def test_ぶきよう_かがくへんかガス退場後はたべのこし回復が止まる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぶきよう", item="たべのこし")],
        foe=[
            Pokemon("ピカチュウ", ability="かがくへんかガス"),
            Pokemon("ライチュウ"),
        ],
    )
    mon = battle.actives[0]

    mon._hp = mon.max_hp - 20
    before_heal = mon.hp
    battle.events.emit(Event.ON_TURN_END_2, BattleContext(source=mon))
    after_heal = mon.hp
    assert after_heal > before_heal

    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])

    mon._hp = mon.max_hp - 20
    before_block = mon.hp
    battle.events.emit(Event.ON_TURN_END_2, BattleContext(source=mon))

    assert mon.hp == before_block


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


def test_てんねん_防御側なら攻撃ランク補正を無視する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability="てんねん")],
    )
    attacker, defender = battle.actives
    attacker.rank["A"] = 2
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    rank = battle.events.emit(Event.ON_CALC_ATK_RANK_MODIFIER, ctx, 2.0)

    assert rank == 1.0


def test_てんねん_攻撃側なら防御ランク補正を無視する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てんねん", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.rank["B"] = 2
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    rank = battle.events.emit(Event.ON_CALC_DEF_RANK_MODIFIER, ctx, 2.0)

    assert rank == 1.0


def test_てんねん_かたやぶりで防御側効果は無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability="てんねん")],
    )
    attacker, defender = battle.actives
    attacker.rank["A"] = 2
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])

    rank = battle.events.emit(Event.ON_CALC_ATK_RANK_MODIFIER, ctx, 2.0)

    assert rank == 2.0


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


def test_ばけのかわ_初回の攻撃技ダメージを防ぐ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives
    before_hp = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is False
    assert defender.hp == before_hp - defender.max_hp // 8
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=1)


def test_ばけのかわ_2回目以降の攻撃は防がない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives

    battle.move_executor.run_move(attacker, attacker.moves[0])
    hp_after_first = defender.hp
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is False
    assert defender.hp < hp_after_first


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
        ally=[
            Pokemon("ピカチュウ", moves=["でんこうせっか"]),
            Pokemon("ライチュウ"),
        ],
        foe=[
            Pokemon("ピカチュウ", ability="ばけのかわ"),
            Pokemon("ライチュウ"),
        ],
    )
    attacker = battle.players[0].active
    defender = battle.players[1].active

    battle.determine_damage = (
        lambda attacker, defender, move, critical=False: 10
    )

    # 初回被弾でばけのかわを消費
    battle.move_executor.run_move(attacker, attacker.moves[0])
    assert defender.ability.enabled is False

    # 交代して戻っても per_battle_once 特性は再有効化されない
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[1])
    battle.switch_manager.run_switch(battle.players[1], battle.players[1].team[0])
    defender = battle.players[1].active
    before_hp = defender.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is False
    assert defender.hp == before_hp - 10


def test_ばけのかわ_かたやぶり系には無視される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability="ばけのかわ")],
    )
    attacker, defender = battle.actives
    before_hp = defender.hp
    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.ability.enabled is True
    assert defender.hp < before_hp


def test_ばけのかわ_かがくへんかガスで無効化されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ばけのかわ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled is True


def test_おやこあい_単発攻撃が2ヒットする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="おやこあい", moves=["アクアステップ"])],
    )
    battle.advance_turn()
    battle.print_logs()
    assert battle.actives[1].hits_taken == 2
    assert battle.actives[0].rank["S"] == 2


def test_おやこあい_2ヒット目のみダメージが減衰する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="おやこあい", moves=["でんこうせっか"])],
        foe=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.determine_damage = lambda *args, **kwargs: 100  # 100ダメージ固定
    battle.advance_turn()
    assert defender.max_hp - defender.hp == 125


def test_おやこあい_既存連続技には適用しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="おやこあい", moves=["タネマシンガン"])],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    battle.random.random = lambda: 0.9
    hit_count = battle.move_executor._resolve_hit_count(attacker, move)
    assert hit_count == 5


def test_おやこあい_かがくへんかガス中は2ヒット化しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="おやこあい", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )

    battle.determine_damage = lambda attacker, defender, move, critical=False: 8
    battle.advance_turn()

    assert battle.actives[1].hits_taken == 1


@pytest.mark.parametrize("ability_name", ["へんげんじざい", "リベロ"])
def test_へんげんじざいリベロ_技タイプへ変化して同一滞在で1回のみ発動(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=["でんこうせっか", "アイアンテール"])],
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
            Pokemon("ピカチュウ", ability=ability_name, moves=["でんこうせっか", "アイアンテール"]),
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
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=["でんこうせっか"])],
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


def test_はらぺこスイッチ_ターン終了時にフォルムが交互に切り替わる():
    battle = t.start_battle(
        ally=[Pokemon("モルペコ", ability="はらぺこスイッチ", moves=["はねる"])],
        foe=[Pokemon("コイキング", moves=["はねる"])],
    )
    morpeko = battle.actives[0]

    assert morpeko.ability.is_hangry is False

    t.reserve_command(battle)
    battle.advance_turn()
    assert morpeko.ability.is_hangry is True

    t.reserve_command(battle)
    battle.advance_turn()
    assert morpeko.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル中はターン終了時に切り替わらない():
    battle = t.start_battle(
        ally=[Pokemon("モルペコ", ability="はらぺこスイッチ", terastal="あく", moves=["はねる"])],
        foe=[Pokemon("コイキング", moves=["はねる"])],
    )
    morpeko = battle.actives[0]

    t.reserve_command(
        battle,
        ally_command=Command.TERASTAL_0,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()

    assert morpeko.is_terastallized is True
    assert morpeko.ability.is_hangry is False


def test_はらぺこスイッチ_交代時は通常まんぷくへ戻る():
    battle = t.start_battle(
        ally=[Pokemon("モルペコ", ability="はらぺこスイッチ"), Pokemon("ピカチュウ")],
        foe=[Pokemon("コイキング")],
    )
    morpeko = battle.players[0].team[0]
    morpeko.ability.is_hangry = True

    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])

    assert morpeko.ability.is_hangry is False


def test_はらぺこスイッチ_テラスタル交代時はフォルム維持する():
    battle = t.start_battle(
        ally=[Pokemon("モルペコ", ability="はらぺこスイッチ", terastal="あく"), Pokemon("ピカチュウ")],
        foe=[Pokemon("コイキング")],
    )
    morpeko = battle.players[0].team[0]
    morpeko.ability.is_hangry = True
    morpeko.terastallize()

    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])

    assert morpeko.ability.is_hangry is True


def test_バトルスイッチ_シールドで攻撃技を使うとブレードへ変化する():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(シールド)", ability="バトルスイッチ", moves=["シャドークロー"])],
        foe=[Pokemon("コイキング")],
    )
    aegislash = battle.actives[0]
    before_atk = aegislash.stats["A"]

    battle.move_executor.run_move(aegislash, aegislash.moves[0])

    assert aegislash.alias == "ギルガルド(ブレード)"
    assert aegislash.stats["A"] > before_atk
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_バトルスイッチ_シールドで変化技なら変化しない():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(シールド)", ability="バトルスイッチ", moves=["つるぎのまい"])],
        foe=[Pokemon("コイキング")],
    )
    aegislash = battle.actives[0]

    battle.move_executor.run_move(aegislash, aegislash.moves[0])

    assert aegislash.alias == "ギルガルド(シールド)"


def test_バトルスイッチ_ブレードでキングシールドを使うとシールドへ変化する():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(ブレード)", ability="バトルスイッチ", moves=["キングシールド"])],
        foe=[Pokemon("コイキング")],
    )
    aegislash = battle.actives[0]

    battle.move_executor.run_move(aegislash, aegislash.moves[0])

    assert aegislash.alias == "ギルガルド(シールド)"
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_バトルスイッチ_ブレードでまもるなら変化しない():
    battle = t.start_battle(
        ally=[Pokemon("ギルガルド(ブレード)", ability="バトルスイッチ", moves=["まもる"])],
        foe=[Pokemon("コイキング")],
    )
    aegislash = battle.actives[0]

    battle.move_executor.run_move(aegislash, aegislash.moves[0])

    assert aegislash.alias == "ギルガルド(ブレード)"


def test_バトルスイッチ_交代時はシールドへ戻る():
    battle = t.start_battle(
        ally=[
            Pokemon("ギルガルド(シールド)", ability="バトルスイッチ", moves=["シャドークロー"]),
            Pokemon("ピカチュウ"),
        ],
        foe=[Pokemon("コイキング")],
    )
    player = battle.players[0]
    aegislash = player.team[0]

    battle.move_executor.run_move(aegislash, aegislash.moves[0])
    assert aegislash.alias == "ギルガルド(ブレード)"

    battle.switch_manager.run_switch(player, player.team[1])

    assert aegislash.alias == "ギルガルド(シールド)"


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
