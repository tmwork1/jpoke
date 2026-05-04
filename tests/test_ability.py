"""特性ハンドラの単体テスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import BattleContext
from jpoke.enums import Event, Interrupt, LogCode, Command
from jpoke.model import Move
from jpoke.utils.type_defs import STRONG_WEATHERS

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


def test_いたずらごころ_変化技の優先度が1上がる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いたずらごころ", moves=["でんじは"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    assert attacker.moves[0].priority == 0
    assert battle.speed_calculator.calc_move_priority(attacker, attacker.moves[0]) == 1


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


def test_いたずらごころ_自己対象の変化技はあくタイプ相手でも成功する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いたずらごころ", moves=["かえんのまもり"])],
        foe=[Pokemon("ヘルガー")],
    )
    attacker = battle.actives[0]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert attacker.has_volatile("かえんのまもり")


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
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ")],
    )
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


def test_マジックガード_かがくへんかガス中でもotherを無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="マジックガード")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    before = mon.hp

    delta = battle.modify_hp(mon, v=-10, reason="other")

    assert mon.ability.enabled is True
    assert delta == 0
    assert mon.hp == before


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


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("あめふらし", "あめ"),
        ("ひでり", "はれ"),
        ("すなおこし", "すなあらし"),
        ("ゆきふらし", "ゆき"),
    ],
)
def test_天候始動特性_登場時に対応天候を展開する(ability_name: str, weather_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ライチュウ")],
    )
    assert battle.raw_weather.name == weather_name
    assert battle.raw_weather.count == 5


@pytest.mark.parametrize("initial_weather", ["はれ", "すなあらし", "ゆき"])
def test_あめふらし_別天候をあめに上書きする(initial_weather: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="あめふらし"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
        weather=(initial_weather, 999),
    )

    # start_battle で初期天候を設定した後、交代で再登場させてあめふらしを再発動させる。
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[0])

    assert battle.raw_weather.name == "あめ"
    assert battle.raw_weather.count == 5


@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("あめふらし", "あめ"),
        ("ひでり", "はれ"),
        ("すなおこし", "すなあらし"),
        ("ゆきふらし", "ゆき"),
    ],
)
def test_天候始動特性_同一天候が有効時は継続ターンを更新しない(ability_name: str, weather_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name), Pokemon("ライチュウ")],
        foe=[Pokemon("ライチュウ")],
    )

    battle.raw_weather.count = 2
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[0])

    assert battle.raw_weather.name == weather_name
    assert battle.raw_weather.count == 2


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


@pytest.mark.parametrize("ability_name", ["ちからもち", "ヨガパワー"])
def test_ちからもち系_物理技で攻撃補正2倍(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 8192


@pytest.mark.parametrize("ability_name", ["ちからもち", "ヨガパワー"])
def test_ちからもち系_特殊技では攻撃補正なし(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096


@pytest.mark.parametrize("ability_name", ["ちからもち", "ヨガパワー"])
def test_ちからもち系_イカサマでは攻撃補正なし(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=["イカサマ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096


def test_テクニシャン_威力60以下は威力補正1_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="テクニシャン", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 6144


def test_テクニシャン_威力61以上は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="テクニシャン", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096


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


def test_テクニシャン_他の威力補正と同時に掛かる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="テクニシャン", item="じしゃく", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 7372


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


def test_ねんちゃく_相手起因の道具変更をブロックする():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
                            )
    self_mon, foe = battle.actives

    result = battle.can_change_item(foe, self_mon)

    assert result is False
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねんちゃく_道具なしでも相手起因の道具変更をブロックする():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", ability="ねんちゃく")],
                            )
    self_mon, foe = battle.actives

    result = battle.can_change_item(foe, self_mon)

    assert result is False
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねんちゃく_自己起因の道具変更は阻害しない():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", ability="ねんちゃく", item="たべのこし")],
                            )
    self_mon, _ = battle.actives

    result = battle.can_change_item(self_mon, self_mon)

    assert result is True


def test_ぶきよう_たべのこしは発動しない():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
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
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぜったいねむり")],
        foe=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ailment.name == "ねむり"


@pytest.mark.parametrize(
    "ability_name, terrain_name",
    [
        ("エレキメイカー", "エレキフィールド"),
        ("グラスメイカー", "グラスフィールド"),
        ("サイコメイカー", "サイコフィールド"),
        ("ミストメイカー", "ミストフィールド"),
    ],
)
def test_地形始動特性_登場時に対応地形を展開する(ability_name: str, terrain_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ライチュウ")],
    )
    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 5


@pytest.mark.parametrize(
    "ability_name, terrain_name",
    [
        ("エレキメイカー", "エレキフィールド"),
        ("グラスメイカー", "グラスフィールド"),
        ("サイコメイカー", "サイコフィールド"),
        ("ミストメイカー", "ミストフィールド"),
    ],
)
def test_地形始動特性_同一地形が有効時は継続ターンを更新しない(ability_name: str, terrain_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name), Pokemon("ライチュウ")],
        foe=[Pokemon("ライチュウ")],
    )

    battle.terrain.count = 2
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[0])

    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 2


@pytest.mark.parametrize(
    "ability_name, terrain_name, initial_terrain",
    [
        ("エレキメイカー", "エレキフィールド", "サイコフィールド"),
        ("グラスメイカー", "グラスフィールド", "ミストフィールド"),
        ("サイコメイカー", "サイコフィールド", "グラスフィールド"),
        ("ミストメイカー", "ミストフィールド", "エレキフィールド"),
    ],
)
def test_地形始動特性_別地形を上書きする(ability_name: str, terrain_name: str, initial_terrain: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 999),
    )

    # start_battle は初期入場後に terrain を設定するため、再登場で特性を発動させる。
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[0])

    assert battle.terrain.name == terrain_name
    assert battle.terrain.count == 5


@pytest.mark.parametrize(
    "ability_name",
    ["エレキメイカー", "サイコメイカー", "ミストメイカー", "グラスメイカー"],
)
def test_地形始動特性_かがくへんかガス中は発動しない(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )

    assert battle.actives[0].ability.enabled is False
    assert battle.terrain.name == ""

    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[0])

    assert battle.actives[0].ability.enabled is False
    assert battle.terrain.name == ""


def test_てつのこぶし_パンチ技威力補正():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["かみなりパンチ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 4915 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


def test_トレース_相手のコピー可能特性をコピーする():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="トレース")],
        foe=[Pokemon("ピカチュウ", ability="すなかき")],
    )
    assert battle.actives[0].ability.orig_name == "すなかき"


def test_トレース_いかくコピー時はいかくが即時発動する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="トレース")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.actives[0].ability.orig_name == "いかく"
    assert battle.actives[1].rank["A"] == -1


def test_トレース_uncopyable特性のみは不発():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="トレース")],
        foe=[Pokemon("ピカチュウ", ability="トレース")],
    )
    assert battle.actives[0].ability.orig_name == "トレース"


def test_トレース_かがくへんかガス中は不発():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="トレース")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled is False
    assert battle.actives[0].ability.orig_name == "トレース"


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


def test_てつのこぶし_パンチ技以外は補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのこぶし", moves=["でんきショック"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert 4096 == t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER)


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


def test_たんじゅん_能力上昇量が2倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="たんじゅん")],
        foe=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    battle.modify_stat(target, "A", +1, source=source)

    assert target.rank["A"] == 2


def test_たんじゅん_能力下降量も2倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="たんじゅん")],
        foe=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    battle.modify_stat(target, "A", -1, source=source)

    assert target.rank["A"] == -2


def test_じしんかじょう_攻撃技で相手を倒すと攻撃1段階上昇():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じしんかじょう", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.modify_hp(defender, v=-(defender.max_hp - 1), reason="other")

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.fainted
    assert attacker.rank["A"] == 1


def test_じしんかじょう_相手を倒せないと発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じしんかじょう", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert attacker.rank["A"] == 0


def test_せいでんき_接触技で被弾時に30パーセントで相手をまひ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいでんき")],
        foe=[Pokemon("イーブイ", moves=["たいあたり"])],
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
    assert attacker.has_ailment("まひ")


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


def test_どくしゅ_接触技で与ダメ時に30パーセントでどく付与():
    battle = t.start_battle(
        ally=[Pokemon("イーブイ", ability="どくしゅ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

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
    attacker = battle.actives[0]
    defender = battle.actives[1]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        battle.move_executor.run_move(attacker, attacker.moves[0])
    finally:
        battle.random.random = orig_random

    assert not defender.ailment.is_active


def test_さめはだ_接触技で被弾時に相手へ最大HPの8分の1ダメージ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="さめはだ")],
        foe=[Pokemon("イーブイ", moves=["たいあたり"])],
    )
    attacker = battle.actives[1]
    hp_before = attacker.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert attacker.hp == hp_before - attacker.max_hp // 8


def test_さめはだ_非接触技では反撃ダメージを与えない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="さめはだ")],
        foe=[Pokemon("イーブイ", moves=["はどうだん"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    hp_before = attacker.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp < defender.max_hp
    assert attacker.hp == hp_before


def test_てつのトゲ_接触技で被弾時に相手へ最大HPの8分の1ダメージ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのトゲ")],
        foe=[Pokemon("イーブイ", moves=["たいあたり"])],
    )
    attacker = battle.actives[1]
    hp_before = attacker.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert attacker.hp == hp_before - attacker.max_hp // 8


def test_てつのトゲ_非接触技では反撃ダメージを与えない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てつのトゲ")],
        foe=[Pokemon("イーブイ", moves=["はどうだん"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]
    hp_before = attacker.hp

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.hp < defender.max_hp
    assert attacker.hp == hp_before


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
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="どんかん")],
        foe=[Pokemon("ピカチュウ")],
    )
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
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
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
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
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


def test_マイティチェンジ_ナイーブで交代するとマイティへ変化する():
    battle = t.start_battle(
        ally=[Pokemon("イルカマン(ナイーブ)", ability="マイティチェンジ"), Pokemon("ピカチュウ")],
        foe=[Pokemon("コイキング")],
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
        foe=[Pokemon("コイキング", moves=["たいあたり"])],
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
        foe=[Pokemon("コイキング")],
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
        foe=[Pokemon("コイキング")],
    )
    player = battle.players[0]
    palafin = player.team[0]

    battle.switch_manager.run_switch(player, player.team[1])

    assert palafin.alias == "イルカマン(マイティ)"
    assert not t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)

# TODO かたやぶりのポケモンが技によって付与する状態異常は防げないこともテストする


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


def test_マイペース_状態異常は防がない_現実装確認():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="マイペース")],
        foe=[Pokemon("ピカチュウ")],
    )
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
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
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
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
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
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("サーフゴー", ability="おうごんのからだ")],
                            )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    # 場が対象の技「くろいきり」では無効化されない
    ctx = BattleContext(attacker=foe_mon, defender=ally_mon, move=Move("くろいきり"))
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is False


def test_ふゆう_浮遊状態になる():
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


def test_クリアボディ_いかくを防ぐ():
    """クリアボディ: いかくによる攻撃低下を防ぐ。"""
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


def test_クリアボディ_能力低下を防ぐ():
    """クリアボディ: 相手由来の能力ランク低下を防ぐ。"""
    battle = t.start_battle(ally=[Pokemon("トゲピー", ability="クリアボディ")],
                            foe=[Pokemon("ピカチュウ")])
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    # クリアボディは相手による複数の能力低下を防ぐ
    # 相手由来の能力低下なので source=foe_mon で指定
    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1, "C": -2, "D": -1},
    )
    # クリアボディにより負の能力変化がすべて除去される
    assert stat_change == {}


def test_クリアボディ_自己低下技は防げない():
    """クリアボディ: 自分の技による能力低下は防げない。"""
    battle = t.start_battle(
        ally=[Pokemon("テッポウオ", ability="クリアボディ")],
        foe=[Pokemon("ピカチュウ")]
    )
    ally_mon = battle.actives[0]

    # 自分が原因の能力低下（source == target）はクリアボディで防がれない
    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=ally_mon),
        {"B": -1},  # 自分の技による防御-1
    )
    # クリアボディは自己低下を防げない（修正値がそのまま）
    assert stat_change == {"B": -1}


def test_ノーガード_攻撃側で必中化():
    """ノーガード: 攻撃側がノーガード時に低命中技が必中になる。"""
    battle = t.start_battle(ally=[Pokemon("テッポウオ", ability="ノーガード", moves=["かみなり"])],
                            foe=[Pokemon("ピカチュウ")])

    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    # かみなりは70%命中。ノーガードで必中化される
    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        move.accuracy,
    )

    assert accuracy is None


def test_ノーガード_防御側で必中化():
    """ノーガード: 防御側がノーガード時に低命中技が必中になる。"""
    battle = t.start_battle(ally=[Pokemon("ピカチュウ", moves=["かみなり"])],
                            foe=[Pokemon("テッポウオ", ability="ノーガード")])

    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    # かみなりは70%命中。防御側がノーガードで必中化される
    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=move),
        move.accuracy,
    )

    assert accuracy is None


def test_がんじょうあご_かみつき技で威力補正1_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょうあご", moves=["かみつく"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 6144


def test_かたいツメ_接触技のみ威力補正1_3倍():
    battle_contact = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたいツメ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle_contact, Event.ON_CALC_POWER_MODIFIER) == 5325

    battle_non_contact = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたいツメ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle_non_contact, Event.ON_CALC_POWER_MODIFIER) == 4096


def test_メガランチャー_はどう技で威力補正1_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="メガランチャー", moves=["りゅうのはどう"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 6144


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


def test_こんじょう_状態異常で攻撃1_5倍かつやけど半減を無効化():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="こんじょう", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")

    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 6144
    assert t.calc_damage_modifier(battle, Event.ON_CALC_BURN_MODIFIER) == 4096


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("あついしぼう", "かえんほうしゃ"),
        ("あついしぼう", "れいとうビーム"),
        ("たいねつ", "かえんほうしゃ"),
        ("きよめのしお", "シャドーボール"),
    ],
)
def test_受ける技タイプで攻撃補正半減する特性(ability_name: str, move_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER, atk_idx=0) == 2048


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのおふだ", "でんこうせっか"),
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
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability="わざわいのおふだ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 3072


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのつるぎ", "でんこうせっか"),
        ("わざわいのたま", "１０まんボルト"),
    ],
)
def test_わざわいつるぎたま_相手防御補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name, moves=[move_name])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_MODIFIER) == 3072


def test_いろめがね_いまひとつの最終ダメージが2倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いろめがね", moves=["むしのていこう"])],
        foe=[Pokemon("ピジョン")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 8192


def test_ブレインフォース_効果抜群の最終ダメージが1_25倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ブレインフォース", moves=["１０まんボルト"])],
        foe=[Pokemon("ピジョン")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 5120


@pytest.mark.parametrize("ability_name", ["フィルター", "ハードロック", "プリズムアーマー"])
def test_防御側特性_効果抜群ダメージを0_75倍(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["じしん"])],
        foe=[Pokemon("コイル", ability=ability_name)],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 3072


@pytest.mark.parametrize("ability_name", ["マルチスケイル", "ファントムガード"])
def test_HP満タン時半減特性(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    defender = battle.actives[1]

    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 2048
    defender._hp -= 1
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 4096


@pytest.mark.parametrize("ability_name", ["マルチスケイル", "ファントムガード"])
def test_マルチスケイル系_連続技2発目以降は半減しない(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["にどげり"])],
        foe=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = attacker.moves[0]

    first_hit = battle.events.emit(
        Event.ON_CALC_DAMAGE_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=move, hit_index=1, hit_count=2),
        4096,
    )
    defender._hp -= 1
    second_hit = battle.events.emit(
        Event.ON_CALC_DAMAGE_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=move, hit_index=2, hit_count=2),
        4096,
    )

    assert first_hit == 2048
    assert second_hit == 4096


@pytest.mark.parametrize("ability_name", ["マルチスケイル", "ファントムガード"])
def test_マルチスケイル系_かたやぶりで無効化される(ability_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability=ability_name)],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 4096


def test_こおりのりんぷん_特殊技のみ被ダメ半減():
    battle_sp = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
    )
    assert t.calc_damage_modifier(battle_sp, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 2048

    battle_ph = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
    )
    assert t.calc_damage_modifier(battle_ph, Event.ON_CALC_DAMAGE_MODIFIER, atk_idx=0) == 4096


def test_こおりのりんぷん_かたやぶりで無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ", ability="こおりのりんぷん")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER) == 4096


def test_スナイパー_急所時の最終ダメージを1_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スナイパー", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    ctx.critical = True

    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 6144


def test_スロースタート_登場5ターン未満は物理攻撃補正0_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スロースタート", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 2048

    battle.turn = battle.actives[0].ability.count + 5
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 4096


def test_よわき_HP半分以下で攻撃補正0_5倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="よわき", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker._hp = attacker.max_hp // 2
    assert t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER) == 2048


# ===== 強天候始動特性 =====

@pytest.mark.parametrize(
    "ability_name, weather_name",
    [
        ("おわりのだいち", "おおひでり"),
        ("はじまりのうみ", "おおあめ"),
        ("デルタストリーム", "らんきりゅう"),
    ],
)
def test_強天候始動特性_登場時に対応天候を展開する(ability_name: str, weather_name: str):
    """強天候始動特性: 登場時に対応する強天候を展開する"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ライチュウ")],
    )
    assert battle.raw_weather.name == weather_name
    assert battle.raw_weather.name in STRONG_WEATHERS


@pytest.mark.parametrize(
    "normal_weather",
    ["はれ", "あめ", "すなあらし", "ゆき"],
)
def test_強天候始動特性_通常天候を上書きする(normal_weather: str):
    """強天候始動特性: 通常天候が展開中でも強天候を展開する"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="おわりのだいち"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
        weather=(normal_weather, 999),
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[0])

    assert battle.raw_weather.name == "おおひでり"


def test_強天候始動特性_通常天候から上書きされない():
    """通常天候始動特性: 強天候展開中は発動しない"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="あめふらし"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
        weather=("おおひでり", 999),
    )
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[0])

    assert battle.raw_weather.name == "おおひでり"


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
    assert battle.raw_weather.name == weather_name

    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert not battle.raw_weather.is_active


# ===== エアロック / ノーてんき =====

def test_エアロック_すいすいの速度2倍が無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="すいすい")],
        foe=[Pokemon("ピカチュウ", ability="エアロック")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    # 天候が抑制されているので速度倍率は1倍（通常速度）のまま
    assert battle.calc_effective_speed(mon) == mon.stats["S"]


def test_エアロック_ON_CHECK_WEATHER_ENABLEDで天候効果を無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="エアロック")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    assert battle.events.emit(Event.ON_CHECK_WEATHER_ENABLED, None, True) is False


def test_ノーてんき_すなあらしのターン終了ダメージが無効化される():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ")],
        foe=[Pokemon("ピカチュウ", ability="ノーてんき")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    hp_before = mon.hp
    battle.events.emit(Event.ON_TURN_END_5, None, None)
    # ノーてんきで天候効果が抑制されるためダメージなし
    assert mon.hp == hp_before


def test_ノーてんき_ON_CHECK_WEATHER_ENABLEDで天候効果を無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ノーてんき")],
        foe=[Pokemon("ピカチュウ")],
        weather=("あめ", 5),
    )
    assert battle.events.emit(Event.ON_CHECK_WEATHER_ENABLED, None, True) is False


def test_エアロック_おおひでりでみず技が失敗しない():
    from jpoke.utils.type_defs import STRONG_WEATHERS
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["なみのり"])],
        foe=[Pokemon("ピカチュウ", ability="エアロック")],
        weather=("おおひでり", 5),
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    # ON_CHECK_IMMUNE が True を返さないこと（エアロックで天候効果を抑制）
    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)
    assert immune is False


# ===== がんじょう =====

def test_がんじょう_HP満タン時の致死ダメージでHP1残る():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょう")],
        foe=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    # HP満タンからダメージを多めに設定して殺意になるようにする
    battle.modify_hp(mon, v=-(mon.max_hp - 1), reason="other")  # HP=1にする
    mon._hp = mon.max_hp  # HP満タンに戻す
    # ON_BEFORE_DAMAGE_APPLYイベントを直接発火する
    ctx = BattleContext(attacker=attacker, defender=mon, move=attacker.moves[0],
                        source=attacker, target=mon, hp_change_reason="move_damage")
    # HP満タン時に致死ダメージを導入する
    lethal_damage = -mon.max_hp
    result = battle.events.emit(Event.ON_BEFORE_DAMAGE_APPLY, ctx, lethal_damage)
    # HP1残りに設定される（-(max_hp-1)）
    assert result == -(mon.max_hp - 1)


def test_がんじょう_HP満タンでないと致死ダメージで倒れる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょう")],
        foe=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    # HPを満タン以下にする
    mon._hp = mon.max_hp - 1
    # ON_BEFORE_DAMAGE_APPLYイベントを直接発火する
    ctx = BattleContext(attacker=attacker, defender=mon, move=attacker.moves[0],
                        source=attacker, target=mon, hp_change_reason="move_damage")
    lethal_damage = -mon.hp
    result = battle.events.emit(Event.ON_BEFORE_DAMAGE_APPLY, ctx, lethal_damage)
    # HP満タンでないので補正なし
    assert result == lethal_damage


def test_がんじょう_一撃必殺技を無効化する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょう")],
        foe=[Pokemon("ピカチュウ", moves=["じわれ"])],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=mon, move=attacker.moves[0])

    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is True


def test_がんじょう_かたやぶり相手の一撃必殺は無効化されない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="がんじょう")],
        foe=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じわれ"])],
    )
    mon = battle.actives[0]
    attacker = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=mon, move=attacker.moves[0])

    immune = battle.events.emit(Event.ON_CHECK_IMMUNE, ctx, False)

    assert immune is False


# ===== ちからずく =====

def test_ちからずく_追加効果あり技の威力が1_3倍():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからずく", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 5325


def test_ちからずく_追加効果なし技は威力変化なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからずく", moves=["はかいこうせん"])],
        foe=[Pokemon("ピカチュウ")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_POWER_MODIFIER) == 4096


def test_ちからずく_追加効果が発動しない():
    """ちからずくの追加効果なし検証: アクアステップのS+1効果が発動しないこと"""
    import random as _random

    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ちからずく", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    # ランダムを常に0（必ず発動）に固定しても追加効果は発動しないはず
    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    rank_before = attacker.rank["S"]
    battle.move_executor.run_move(attacker, attacker.moves[0])
    battle.random.random = orig_random
    # ちからずくで追加効果なし
    assert attacker.rank["S"] == rank_before


# ===== てんのめぐみ =====

def test_てんのめぐみ_追加効果対象技の確率が2倍になる():
    """move_secondary=True の技に対して ON_MOVE_SECONDARY が確率を2倍にすること"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てんのめぐみ", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    ctx = BattleContext(attacker=attacker, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, 0.3)
    assert result == 0.6


def test_てんのめぐみ_確率が1を超えないようにクランプされる():
    """2倍にすると1.0を超える場合は1.0にクランプされること"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="てんのめぐみ", moves=["アクアステップ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    ctx = BattleContext(attacker=attacker, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, 0.7)
    assert result == 1.0


# ===== マルチタイプ =====

def test_マルチタイプ_せいれいプレートでフェアリータイプになる():
    battle = t.start_battle(
        ally=[Pokemon("アルセウス", ability="マルチタイプ", item="せいれいプレート")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == "フェアリー"


def test_マルチタイプ_プレートなしでタイプ変更なし():
    battle = t.start_battle(
        ally=[Pokemon("アルセウス", ability="マルチタイプ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None


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


# ===== ARシステム =====

def test_ARシステム_フェアリーメモリでフェアリータイプになる():
    battle = t.start_battle(
        ally=[Pokemon("シルヴァディ", ability="ARシステム", item="フェアリーメモリ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == "フェアリー"


def test_ARシステム_メモリなしでタイプ変更なし():
    battle = t.start_battle(
        ally=[Pokemon("シルヴァディ", ability="ARシステム")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None


# ===== あめうけざら =====

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


# ===== アイスボディ =====

def test_アイスボディ_ゆき中にターン終了時1_16回復():
    battle = t.start_battle(
        ally=[Pokemon("ユキノオー", ability="アイスボディ")],
        foe=[Pokemon("ピカチュウ")],
        weather=("ゆき", 5),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before + mon.max_hp // 16


def test_アイスボディ_ゆき以外では発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ユキノオー", ability="アイスボディ")],
        foe=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="other")
    before = mon.hp
    battle.events.emit(Event.ON_TURN_END_3, BattleContext(source=mon))
    assert mon.hp == before


# ===== ポイズンヒール =====

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


# ===== さいせいりょく =====

def test_さいせいりょく_交代で控えに戻った時1_3回復する():
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="さいせいりょく"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-60, reason="other")
    before = mon.hp
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.hp == min(mon.max_hp, before + mon.max_hp // 3)


def test_さいせいりょく_かいふくふうじ中でも回復する():
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="さいせいりょく"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "かいふくふうじ")
    battle.modify_hp(mon, v=-60, reason="other")
    before = mon.hp
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.hp == min(mon.max_hp, before + mon.max_hp // 3)


def test_さいせいりょく_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ヤドン", ability="さいせいりょく"), Pokemon("ライチュウ")],
        foe=[Pokemon("マタドガス", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-60, reason="other")
    before = mon.hp
    battle.switch_manager.run_switch(battle.players[0], battle.players[0].team[1])
    assert mon.hp == before


def test_いしあたま_反動技を使っても反動ダメージを受けない():
    battle = t.start_battle(
        ally=[Pokemon("ゴンベ", ability="いしあたま", moves=["すてみタックル"])],
        foe=[Pokemon("ヤドン")],
    )
    attacker = battle.actives[0]
    before = attacker.hp
    t.reserve_command(battle, Command.MOVE_0)
    battle.advance_turn()
    assert attacker.hp == before


def test_いしあたま_かがくへんかガス中は反動ダメージを受ける():
    battle = t.start_battle(
        ally=[Pokemon("ゴンベ", ability="いしあたま", moves=["すてみタックル"])],
        foe=[Pokemon("マタドガス", ability="かがくへんかガス")],
    )
    attacker = battle.actives[0]
    before = attacker.hp
    t.reserve_command(battle, Command.MOVE_0)
    battle.advance_turn()
    assert attacker.hp < before


def test_かそく_行動後のターン終了時に素早さが上がる():
    battle = t.start_battle(
        ally=[Pokemon("テッポウオ", ability="かそく", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.rank["S"] == 0
    mon.executed_move = Move("たいあたり")

    battle.events.emit(Event.ON_TURN_END_5, BattleContext(source=mon), None)

    assert mon.rank["S"] == 1


def test_かそく_交代直後のターン終了時は上がらない():
    battle = t.start_battle(
        ally=[
            Pokemon("ピカチュウ", ability="せいでんき", moves=["まもる"]),
            Pokemon("テッポウオ", ability="かそく", moves=["たいあたり"]),
        ],
        foe=[Pokemon("ピカチュウ", moves=["まもる"])],
    )
    p0 = battle.players[0]
    speed_boost_mon = p0.team[1]

    battle.switch_manager.run_switch(p0, speed_boost_mon)
    battle.events.emit(Event.ON_TURN_END_5, BattleContext(source=speed_boost_mon), None)

    assert speed_boost_mon.rank["S"] == 0


def test_かそく_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("テッポウオ", ability="かそく", moves=["たいあたり"])],
        foe=[Pokemon("マタドガス", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    mon.executed_move = Move("たいあたり")

    battle.events.emit(Event.ON_TURN_END_5, BattleContext(source=mon), None)

    assert mon.rank["S"] == 0


def test_かそく_素早さ最大では上昇しない():
    battle = t.start_battle(
        ally=[Pokemon("テッポウオ", ability="かそく")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.rank["S"] = 6
    mon.executed_move = Move("たいあたり")

    battle.events.emit(Event.ON_TURN_END_5, BattleContext(source=mon), None)

    assert mon.rank["S"] == 6


def test_かるわざ_持ち物を失うと素早さが2倍になる():
    battle = t.start_battle(
        ally=[Pokemon("テッポウオ", ability="かるわざ", item="オボンのみ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    base = battle.calc_effective_speed(mon)
    battle.consume_item(mon)
    boosted = battle.calc_effective_speed(mon)

    assert boosted == base * 2


def test_かるわざ_入場時に持ち物なしなら発動しない():
    battle = t.start_battle(
        ally=[Pokemon("テッポウオ", ability="かるわざ")],
        foe=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    base = battle.calc_effective_speed(mon)
    battle.set_item(mon, "オボンのみ")
    battle.consume_item(mon)
    after = battle.calc_effective_speed(mon)

    assert after == base


def test_かるわざ_持ち物再取得で解除され再消費で再発動する():
    battle = t.start_battle(
        ally=[Pokemon("テッポウオ", ability="かるわざ", item="オボンのみ")],
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


def test_かいりきバサミ_いかくでこうげきが下がらない():
    """かいりきバサミ: 相手のいかくによるこうげき低下を防ぐ。"""
    battle = t.start_battle(
        ally=[Pokemon("カイリキー", ability="かいりきバサミ")],
        foe=[Pokemon("ウインディ", ability="いかく")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1},
    )
    assert stat_change == {}


def test_かいりきバサミ_こうげき以外の低下は防げない():
    """かいりきバサミ: こうげき以外のランク低下は防げない。"""
    battle = t.start_battle(
        ally=[Pokemon("カイリキー", ability="かいりきバサミ")],
        foe=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"B": -1, "C": -2},
    )
    assert stat_change == {"B": -1, "C": -2}


def test_かいりきバサミ_自己低下は防げない():
    """かいりきバサミ: 自分の技によるこうげき低下は防げない（ばかぢから等）。"""
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


def test_はとむね_ぼうぎょ低下を防ぐ():
    """はとむね: 相手によるぼうぎょランク低下を防ぐ。"""
    battle = t.start_battle(
        ally=[Pokemon("トゲキッス", ability="はとむね")],
        foe=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"B": -2},
    )
    assert stat_change == {}


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


def test_しろいけむり_全能力低下を防ぐ():
    """しろいけむり: 相手による全能力ランク低下を防ぐ（クリアボディ同効果）。"""
    battle = t.start_battle(
        ally=[Pokemon("コータス", ability="しろいけむり")],
        foe=[Pokemon("ピカチュウ")],
    )
    ally_mon = battle.actives[0]
    foe_mon = battle.actives[1]

    stat_change = battle.events.emit(
        Event.ON_MODIFY_STAT,
        BattleContext(target=ally_mon, source=foe_mon),
        {"A": -1, "C": -2, "D": -1},
    )
    assert stat_change == {}


# ===== きょううん =====

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


# ===== ぼうおん =====

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
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
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


def test_ぼうおん_かたやぶりには無効化されない():
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


# ===== りんぷん =====

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


# ===== スカイスキン =====

def test_スカイスキン_ノーマル技をひこうタイプに変換する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.get_effective_move_type(attacker, move)
    assert result == "ひこう"


def test_スカイスキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="スカイスキン", moves=["でんこうせっか"])],
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


# ===== ノーマルスキン =====

def test_ノーマルスキン_ほのお技をノーマルタイプに変換する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ノーマルスキン", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.get_effective_move_type(attacker, move)
    assert result == "ノーマル"


def test_ノーマルスキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ノーマルスキン", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4915


def test_ノーマルスキン_元からノーマルタイプの技は威力補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ノーマルスキン", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    ctx = BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0])
    result = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
    assert result == 4096


# ===== フェアリースキン =====

def test_フェアリースキン_ノーマル技をフェアリータイプに変換する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.get_effective_move_type(attacker, move)
    assert result == "フェアリー"


def test_フェアリースキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フェアリースキン", moves=["でんこうせっか"])],
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


# ===== フリーズスキン =====

def test_フリーズスキン_ノーマル技をこおりタイプに変換する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    result = battle.move_executor.get_effective_move_type(attacker, move)
    assert result == "こおり"


def test_フリーズスキン_変換した技の威力が4915倍になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="フリーズスキン", moves=["でんこうせっか"])],
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


# ===== サンパワー =====

@pytest.mark.parametrize("weather_name,weather_count", [("はれ", 5), ("おおひでり", 999)])
def test_サンパワー_はれおおひでり中に特殊技の特攻1_5倍(weather_name: str, weather_count: int):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="サンパワー", moves=["１０まんボルト"])],
        foe=[Pokemon("ピカチュウ")],
        weather=(weather_name, weather_count),
    )
    result = t.calc_damage_modifier(battle, Event.ON_CALC_ATK_MODIFIER)
    assert result == 6144


def test_サンパワー_はれ中でも物理技は補正なし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="サンパワー", moves=["でんこうせっか"])],
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


# ===== しぜんかいふく =====

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


# ===== しめりけ =====

def test_しめりけ_じばくを失敗させる():
    """しめりけ持ちが防御側のとき、相手のじばくを失敗させる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["じばく"])],
        foe=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    result = t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert not result


def test_しめりけ_自分の爆発技も失敗させる():
    """しめりけ持ちが自分でじばくを使おうとしても失敗する。"""
    battle = t.start_battle(
        ally=[Pokemon("ニョロモ", ability="しめりけ", moves=["じばく"])],
        foe=[Pokemon("ピカチュウ")],
    )
    result = t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert not result


def test_しめりけ_爆発ラベルなし技は通す():
    """しめりけ持ちでも爆発技でなければ通す。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        foe=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    result = t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert result


def test_しめりけ_かたやぶりで爆発技が通る():
    """かたやぶり持ちはしめりけを無視してじばくを使える。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かたやぶり", moves=["じばく"])],
        foe=[Pokemon("ニョロモ", ability="しめりけ")],
    )
    result = t.check_event_result(battle, Event.ON_CHECK_MOVE)
    assert result


# ===== ゆきかき =====

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


# ===== ゆきがくれ =====

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


# ===== リーフガード =====

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


# ===== せいしんりょく =====

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


# ===== ぼうじん =====

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
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
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


# ===== ぼうだん =====

def test_ぼうだん_弾技を無効化する():
    """ぼうだん: 弾技を無効化する。"""
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
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
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


@pytest.mark.parametrize("ability_name", ["すなかき", "すながくれ", "すなのちから", "ぼうじん"])
def test_sandstorm_damage_immunity_direct(ability_name):
    """各特性: すなあらしダメージを受けない（ON_BEFORE_DAMAGE_APPLY 直接テスト）。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 999),
    )
    ally_mon = battle.actives[0]

    # ON_BEFORE_DAMAGE_APPLY で直接テスト
    result = battle.events.emit(
        Event.ON_BEFORE_DAMAGE_APPLY,
        BattleContext(target=ally_mon, hp_change_reason="sandstorm_damage"),
        -6,  # すなあらしダメージ（max_hp 110 の 1/16 ≈ 6）
    )
    assert result == 0


@pytest.mark.parametrize("ability_name", ["すなかき", "すながくれ", "すなのちから", "ぼうじん"])
def test_sandstorm_damage_immunity_full_flow(ability_name):
    """各特性: ON_TURN_END_1 の完全フローでダメージが免除される。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability=ability_name)],
        foe=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 999),
    )
    ally_hp_before = battle.actives[0].hp
    battle.events.emit(Event.ON_TURN_END_1)
    assert battle.actives[0].hp == ally_hp_before


def test_はりきり_物理技の攻撃補正が1_5倍になる():
    """はりきり特性: 物理技の攻撃補正を1.5倍にする。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="はりきり", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    # 物理技の場合: 攻撃補正が1.5倍（6144/4096）
    move = attacker.moves[0]  # でんこうせっか（物理）
    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=move),
        4096,
    )
    expected = 4096 * 6144 // 4096  # 6144
    assert atk_modifier == expected


def test_はりきり_物理技の命中率が0_8倍になる():
    """はりきり特性: 物理技の命中率を0.8倍にする。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="はりきり", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    move = attacker.moves[0]  # でんこうせっか（物理）
    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, move=move),
        100,
    )
    expected = 100 * 3277 // 4096  # 約80
    assert accuracy == expected


def test_はりきり_特殊技には補正がかからない():
    """はりきり特性: 特殊技には攻撃補正と命中率補正がかからない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="はりきり", moves=["かえんほうしゃ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    move = attacker.moves[0]  # かえんほうしゃ（特殊）

    # 攻撃補正
    atk_modifier = battle.events.emit(
        Event.ON_CALC_ATK_MODIFIER,
        BattleContext(attacker=attacker, defender=defender, move=move),
        4096,
    )
    assert atk_modifier == 4096

    # 命中率
    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, move=move),
        100,
    )
    assert accuracy == 100


def test_はりきり_一撃必殺技の命中率は下がらない():
    """はりきり特性: 一撃必殺技（accuracy=-1）の命中率は下がらない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="はりきり", moves=["つのドリル"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    move = attacker.moves[0]  # つのドリル（一撃必殺）
    accuracy = battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, move=move),
        30,
    )
    # 命中率ペナルティがかからない
    assert accuracy == 30


def test_だっぴ_ターン終了時に30パーセントで状態異常を回復する():
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
# ねつこうかん
# ──────────────────────────────────────────────────────────────────

def test_ねつこうかん_ほのお技でこうげき1段階アップ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        foe=[Pokemon("ピカチュウ", moves=["かえんほうしゃ"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["A"] == 1
    assert t.log_contains(battle, LogCode.ABILITY_TRIGGERED, player_idx=0)


def test_ねつこうかん_やけど状態にならない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        foe=[Pokemon("ピカチュウ", moves=["おにび"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert not defender.ailment.is_active


def test_ねつこうかん_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ねつこうかん")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["かえんほうしゃ"])],
    )
    defender = battle.actives[0]
    attacker = battle.actives[1]

    battle.move_executor.run_move(attacker, attacker.moves[0])

    assert defender.rank["A"] == 0


# ──────────────────────────────────────────────────────────────────
# はやあし
# ──────────────────────────────────────────────────────────────────

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
# ダウンロード
# ──────────────────────────────────────────────────────────────────

def test_ダウンロード_相手防御が特防より低い場合攻撃アップ():
    foe = Pokemon("ピカチュウ")
    _set_raw_stats(foe, a=100, b=50, c=100, d=100, s=100)  # B=50 < D=100 → 攻撃+1
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ダウンロード")],
        foe=[foe],
    )
    mon = battle.actives[0]
    assert mon.rank["A"] == 1
    assert mon.rank["C"] == 0


def test_ダウンロード_相手防御が特防以上の場合特攻アップ():
    foe = Pokemon("ピカチュウ")
    _set_raw_stats(foe, a=100, b=100, c=100, d=50, s=100)  # B=100 > D=50 → 特攻+1
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ダウンロード")],
        foe=[foe],
    )
    mon = battle.actives[0]
    assert mon.rank["A"] == 0
    assert mon.rank["C"] == 1


def test_ダウンロード_防御と特防が等しい場合特攻アップ():
    foe = Pokemon("ピカチュウ")
    _set_raw_stats(foe, a=100, b=100, c=100, d=100, s=100)  # B=D=100 → 特攻+1
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ダウンロード")],
        foe=[foe],
    )
    mon = battle.actives[0]
    assert mon.rank["A"] == 0
    assert mon.rank["C"] == 1


def test_ダウンロード_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ダウンロード")],
        foe=[Pokemon("ピカチュウ", ability="かがくへんかガス")],
    )
    mon = battle.actives[0]
    assert mon.rank["A"] == 0
    assert mon.rank["C"] == 0


# ──────────────────────────────────────────────────────────────────
# ひとでなし
# ──────────────────────────────────────────────────────────────────

def test_ひとでなし_どく状態の相手には急所ランク最大相当になる():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["つじぎり"])],
        foe=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "どく", source=attacker)

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank == 10


def test_ひとでなし_非どく状態の相手には急所ランクを変更しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["つじぎり"])],
        foe=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        1,
    )
    assert rank == 1


def test_ひとでなし_カブトアーマー相手には急所化しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["つじぎり"])],
        foe=[Pokemon("カビゴン", ability="カブトアーマー")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "どく", source=attacker)

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank == 0


def test_ひとでなし_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ひとでなし", moves=["つじぎり"])],
        foe=[Pokemon("カビゴン", ability="かがくへんかガス")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "どく", source=attacker)

    rank = battle.events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        0,
    )
    assert rank == 0


# ──────────────────────────────────────────────────────────────────
# テラスシェル
# ──────────────────────────────────────────────────────────────────

def test_テラスシェル_HP満タンで等倍技を半減する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="テラスシェル")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER, atk_idx=0) == 2048


def test_テラスシェル_HP満タンで抜群技を半減する():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["じしん"])],
        foe=[Pokemon("コイル", ability="テラスシェル")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER, base=16384, atk_idx=0) == 8192


def test_テラスシェル_HP満タンでないと発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="テラスシェル")],
    )
    defender = battle.actives[1]
    battle.modify_hp(defender, v=-1, reason="test")
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER, atk_idx=0) == 4096


def test_テラスシェル_かがくへんかガス中は発動しない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かがくへんかガス", moves=["たいあたり"])],
        foe=[Pokemon("ピカチュウ", ability="テラスシェル")],
    )
    assert t.calc_damage_modifier(battle, Event.ON_CALC_DEF_TYPE_MODIFIER, atk_idx=0) == 4096


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
