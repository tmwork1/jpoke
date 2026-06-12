"""アイテムハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext
    from jpoke.model import Pokemon, Move

from jpoke.utils.type_defs import RoleSpec, Stat, Type, WeatherName, TerrainName, SideFieldName
from jpoke.utils.math import apply_fixed_modifier
from jpoke.enums import Interrupt, LogCode, Command
from jpoke.core import HandlerReturn, Handler
from . import common


class ItemHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            source="item",
            subject_spec=subject_spec,
            priority=priority,
            once=once,
        )


def announce_item_triggered(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    _announce_item_triggered(battle, ctx.source)
    return HandlerReturn(value=value)


def _announce_item_triggered(battle: Battle, mon: Pokemon) -> None:
    mon.item.revealed = True
    battle.add_event_log(
        mon,
        LogCode.ITEM_TRIGGERED,
        payload={"item": mon.item.name}
    )


def mega_modify_command_options(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
    """メガストーン: メガシンカコマンドを追加する。"""
    mon = ctx.source
    if not mon.can_megaevolve():
        return HandlerReturn(value=value)

    for cmd in value:
        if cmd.is_regular_move:
            value.append(Command.get_megaevol_command(cmd.index))

    return HandlerReturn(value=value)


def _modify_power_by_type(move: Move,
                          value: Any,
                          type_: Type,
                          modifier: float) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER
    if move.type == type_:
        value = int(value * modifier)
    return HandlerReturn(value=value)


def _modify_super_effective_damage(battle: Battle,
                                   ctx: AttackContext,
                                   value: Any,
                                   type_: Type,
                                   modifier: float) -> HandlerReturn:
    # ON_CALC_DAMAGE_MODIFIER
    if (
        ctx.move.type == type_ and
        battle.damage_calculator.calc_def_type_modifier(ctx) > 1
    ):
        value = int(value * modifier)
    return HandlerReturn(value=value)


def _resolve_field_count(value: list,
                         *,
                         field: WeatherName | TerrainName | SideFieldName,
                         additonal_count: int) -> HandlerReturn:
    """指定場状態と一致するとき継続ターン数に加算する。"""
    name, count = value
    if field == name:
        count += additonal_count
    return HandlerReturn(value=[name, count])


def _apply_contact_item_chip(battle: Battle,
                              ctx: AttackContext,
                              *,
                              ratio: float) -> bool:
    """接触被弾時アイテムの固定割合ダメージを攻撃者に適用する。

    Returns:
        bool: ダメージが適用された場合True
    """
    if battle.query.is_contact(ctx):
        v = battle.modify_hp(ctx.attacker, r=-ratio)
        return bool(v)
    return False


def あついいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, field="はれ", additonal_count=3)


def apply_こだわりロック(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こだわりアイテム: 使用した技でロックする。"""
    mon = ctx.attacker
    if not mon.has_volatile("こだわり"):
        battle.volatile_manager.apply(
            mon, "こだわり", source=mon, move_name=ctx.move.name
        )
    return HandlerReturn(value=value)


def いかさまダイス_modify_hit_count(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """いかさまダイス: 2-5回連続技のヒット数を4回または5回へ補正する。"""
    min_hits, max_hits = ctx.move.min_hits, ctx.move.max_hits
    if (min_hits, max_hits) == (2, 5):
        value = 4 if battle.random.random() < 0.5 else 5
    return HandlerReturn(value=value)


def オーガポンのめん_boost_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーガポンのめん共通: 物理技の攻撃補正を1.2倍にする。"""
    if ctx.move.category == "物理":
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def エレキシード_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == "エレキフィールド":
        battle.modify_stats(mon, {"B": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def エレキシード_on_field_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == "エレキフィールド":
        battle.modify_stats(mon, {"B": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def オボンのみ_heal_on_half_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.target
    assert mon is not None
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * 2 > mon.max_hp and hp_after * 2 <= mon.max_hp:
        battle.modify_hp(mon, r=1/4)
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def オレンのみ_heal_on_half_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.target
    assert mon is not None
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * 2 > mon.max_hp and hp_after * 2 <= mon.max_hp:
        battle.modify_hp(mon, v=10)
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def いのちのたま_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    if (
        ctx.move.category != "変化"
        and common.self_damage(battle, ctx, value, r=1/8)
    ):
        _announce_item_triggered(battle, ctx.attacker)
    return HandlerReturn(value=value)


def だっしゅつパック_reserve_switch(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # valueは{stat: change}の辞書
    player = battle.get_player(ctx.target)
    if (
        any(v < 0 for v in value.values())
        and battle.get_available_switch_commands(player)
    ):
        battle.player_states[player].interrupt = Interrupt.EJECTPACK_REQUESTED
    return HandlerReturn(value=value)


def だっしゅつボタン_reserve_switch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    player = battle.get_player(ctx.defender)
    battle.player_states[player].interrupt = Interrupt.EJECTBUTTON
    return HandlerReturn(value=value)


def たべのこし_heal_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """たべのこし: ターン終了時HP回復"""
    mon = ctx.source
    if battle.modify_hp(mon, r=1/16):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def ちからのハチマキ_boost_physical(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """物理技1.1倍"""
    if ctx.move.category == "物理":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def ものしりメガネ_boost_special(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """特殊技1.1倍"""
    if ctx.move.category == "特殊":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def かえんだま_apply_burn(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かえんだま: ターン終了時にやけどを付与する。"""
    mon = ctx.source
    assert mon is not None
    if battle.ailment_manager.apply(mon, "やけど", source=mon):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def かたいいし_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="いわ", modifier=4915/4096)


def きあいのタスキ_survive_ohko(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きあいのタスキ: HPが満タンのときひんし以上のダメージをHP1で耐える。"""
    mon = ctx.defender
    assert mon is not None
    if mon.hp == mon.max_hp and value >= mon.hp:
        value = mon.hp - 1
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def きあいのハチマキ_survive_by_chance(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きあいのハチマキ: ひんし以上のダメージを11.7%の確率でHP1で耐える。"""
    mon = ctx.defender
    assert mon is not None
    if value >= mon.hp and battle.random.random() < 0.117:
        value = mon.hp - 1
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def きせきのたね_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="くさ", modifier=4915/4096)


def ぎんのこな_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="むし", modifier=4915/4096)


def くろいメガネ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="あく", modifier=4915/4096)


def くろおび_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="あく", modifier=4915/4096)


def こうかくレンズ_modify_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こうかくレンズ: 命中率を1.1倍にする。"""
    return HandlerReturn(value=apply_fixed_modifier(value, 4506))


def こだわりスカーフ_boost_speed(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こだわりスカーフ: 素早さを1.5倍にする。"""
    value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def こだわりハチマキ_boost_physical(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こだわりハチマキ: 物理技の攻撃補正を1.5倍にする。"""
    if ctx.move.category == "物理":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def こだわりメガネ_boost_special(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こだわりメガネ: 特殊技の攻撃補正を1.5倍にする。"""
    if ctx.move.category == "特殊":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def サイコシード_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == "サイコフィールド":
        battle.modify_stats(mon, {"D": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def サイコシード_on_field_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == "サイコフィールド":
        battle.modify_stats(mon, {"D": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def さらさらいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, field="すなあらし", additonal_count=3)


def じしゃく_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="でんき", modifier=4915/4096)


def シルクのスカーフ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ノーマル", modifier=4915/4096)


def しろいハーブ_cancel_stat_drop(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    if any(v < 0 for v in value.values()):
        value = {s: max(v, 0) for s, v in value.items()}
        mon = ctx.target
        assert mon is not None
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def しんぴのしずく_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="みず", modifier=4915/4096)


def するどいキバ_flinch_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """するどいキバ: ダメージ技命中時10%の確率で相手をひるませる。"""
    defender = ctx.defender
    if (
        ctx.move.category != "変化"
        and defender is not None
        and battle.random.random() < 0.1
    ):
        battle.volatile_manager.apply(defender, "ひるみ", source=ctx.attacker, ctx=ctx)
    return HandlerReturn(value=value)


def するどいツメ_boost_critical_rank(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """するどいツメ: 急所ランクを+1する。"""
    return HandlerReturn(value=value + 1)


def するどいくちばし_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ひこう", modifier=4915/4096)


def せいれいプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="フェアリー", modifier=4915/4096)


def どくどくだま_apply_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくどくだま: ターン終了時にもうどくを付与する。"""
    mon = ctx.source
    assert mon is not None
    if battle.ailment_manager.apply(mon, "もうどく", source=mon):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def どくバリ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="どく", modifier=4915/4096)


def とけないこおり_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="こおり", modifier=4915/4096)


def ノーマルジュエル_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ノーマル", modifier=6144/4096)


def のろいのおふだ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ゴースト", modifier=4915/4096)


def まがったスプーン_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="エスパー", modifier=4915/4096)


def ミストシード_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == "ミストフィールド":
        battle.modify_stats(mon, {"D": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def ミストシード_on_field_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == "ミストフィールド":
        battle.modify_stats(mon, {"D": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def メタルコート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="はがね", modifier=4915/4096)


def メトロノーム_boost_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メトロノーム: 同じ技を連続使用するたびに威力が上がる（最大2倍）。"""
    item = ctx.attacker.item
    if item.count > 0 and item.move_name == ctx.move.name:
        value = apply_fixed_modifier(value, 4096 + item.count * 819)
    return HandlerReturn(value=value)


def メトロノーム_update_count(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メトロノーム: 技使用後に連続カウントを更新する。"""
    item = ctx.attacker.item
    if item.move_name == ctx.move.name:
        item.count = min(item.count + 1, 5)
    else:
        item.move_name = ctx.move.name
        item.count = 1
    return HandlerReturn(value=value)


def もくたん_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ほのお", modifier=4915/4096)


def やわらかいすな_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="じめん", modifier=4915/4096)


def ようせいのハネ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="フェアリー", modifier=4915/4096)


def りゅうのキバ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ドラゴン", modifier=4915/4096)


def ホズのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ノーマル", modifier=2048/4096)


def リンドのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="くさ", modifier=2048/4096)


def オッカのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ほのお", modifier=2048/4096)


def イトケのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="みず", modifier=2048/4096)


def ソクノのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="でんき", modifier=2048/4096)


def カシブのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ゴースト", modifier=2048/4096)


def ヨロギのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="いわ", modifier=2048/4096)


def タンガのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="むし", modifier=2048/4096)


def ウタンのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="エスパー", modifier=2048/4096)


def バコウのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ひこう", modifier=2048/4096)


def シュカのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="じめん", modifier=2048/4096)


def ビアーのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="どく", modifier=2048/4096)


def ヨプのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="かくとう", modifier=2048/4096)


def ヤチェのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="こおり", modifier=2048/4096)


def リリバのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="はがね", modifier=2048/4096)


def ナモのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="あく", modifier=2048/4096)


def ハバンのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ドラゴン", modifier=2048/4096)


def ロゼルのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="フェアリー", modifier=2048/4096)


def カゴのみ_cure_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.ailment.name == "ねむり":
        if battle.ailment_manager.remove(mon):
            _announce_item_triggered(battle, mon)
            battle.consume_item(mon)
    return HandlerReturn(value=value)


def キーのみ_cure_confusion(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.has_volatile("こんらん"):
        battle.volatile_manager.remove(mon, "こんらん")
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def クラボのみ_cure_paralysis(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.ailment.name == "まひ":
        if battle.ailment_manager.remove(mon):
            _announce_item_triggered(battle, mon)
            battle.consume_item(mon)
    return HandlerReturn(value=value)


def グラスシード_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == "グラスフィールド":
        battle.modify_stats(mon, {"B": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def グラスシード_on_field_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == "グラスフィールド":
        battle.modify_stats(mon, {"B": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def くろいてっきゅう_halve_speed(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=apply_fixed_modifier(value, 2048))


def くろいてっきゅう_negate_floating(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    return HandlerReturn(value=False, stop_event=True)


def くろいヘドロ_heal_or_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.has_type("どく"):
        if battle.modify_hp(mon, r=1/16):
            _announce_item_triggered(battle, mon)
    else:
        battle.modify_hp(mon, r=-1/8)
    return HandlerReturn(value=value)


def ゴツゴツメット_chip_contact_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.defender
    assert mon is not None
    if _apply_contact_item_chip(battle, ctx, ratio=1/6):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def しめったいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, field="あめ", additonal_count=3)


def チーゴのみ_cure_burn(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.ailment.name == "やけど":
        if battle.ailment_manager.remove(mon):
            _announce_item_triggered(battle, mon)
            battle.consume_item(mon)
    return HandlerReturn(value=value)


def たつじんのおび_boost_super_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    if battle.damage_calculator.calc_def_type_modifier(ctx) > 1:
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def つめたいいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, field="ゆき", additonal_count=3)


def ナナシのみ_cure_freeze(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.ailment.name == "こおり":
        if battle.ailment_manager.remove(mon):
            _announce_item_triggered(battle, mon)
            battle.consume_item(mon)
    return HandlerReturn(value=value)


def モモンのみ_cure_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.ailment.name in ("どく", "もうどく"):
        if battle.ailment_manager.remove(mon):
            _announce_item_triggered(battle, mon)
            battle.consume_item(mon)
    return HandlerReturn(value=value)


def ひかりのねんど_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    for field_name in ("リフレクター", "ひかりのかべ", "オーロラベール"):
        result = _resolve_field_count(value, field=field_name, additonal_count=3)
        if result.value != value:
            return result
    return HandlerReturn(value=value)


def ヒメリのみ_cure_disable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.has_volatile("かなしばり"):
        battle.volatile_manager.remove(mon, "かなしばり")
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def ピントレンズ_boost_critical_rank(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ピントレンズ: 急所ランクを+1する。"""
    return HandlerReturn(value=value + 1)


def ふうせん_check_floating(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    return HandlerReturn(value=True)


def ふうせん_pop_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.defender
    assert mon is not None
    battle.consume_item(mon)
    _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def かるいし_boost_speed(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=apply_fixed_modifier(value, 8192))


def ラムのみ_cure_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.ailment.is_active:
        if battle.ailment_manager.remove(mon):
            _announce_item_triggered(battle, mon)
            battle.consume_item(mon)
    return HandlerReturn(value=value)


def _heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """1/4HP以下になった瞬間に最大HPの1/3を回復する共通処理。"""
    mon = ctx.target
    assert mon is not None
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * 4 > mon.max_hp and hp_after * 4 <= mon.max_hp:
        battle.modify_hp(mon, r=1/3)
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def ウイのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ウイのみ: HP1/4以下で最大HPの1/3を回復する。"""
    return _heal_on_quarter_hp(battle, ctx, value)


def イアのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """イアのみ: HP1/4以下で最大HPの1/3を回復する。"""
    return _heal_on_quarter_hp(battle, ctx, value)


def _boost_on_quarter_hp(battle: Battle,
                          ctx: EventContext,
                          value: Any,
                          stat: Stat,
                          amount: int) -> HandlerReturn:
    """1/4HP以下になった瞬間に能力を上昇させる共通処理。"""
    mon = ctx.target
    assert mon is not None
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * 4 > mon.max_hp and hp_after * 4 <= mon.max_hp:
        battle.modify_stats(mon, {stat: amount})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def カムラのみ_boost_speed(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """カムラのみ: HP1/4以下ですばやさ+2。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="S", amount=+2)


def スターのみ_random_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スターのみ: HP1/4以下でランダムな能力+2。"""
    mon = ctx.target
    assert mon is not None
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * 4 > mon.max_hp and hp_after * 4 <= mon.max_hp:
        stat = battle.random.choice(["A", "B", "C", "D", "S"])
        battle.modify_stats(mon, {stat: +2})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def ズアのみ_boost_spdef(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ズアのみ: HP1/4以下でとくぼう+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="D", amount=+1)


def チイラのみ_boost_attack(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """チイラのみ: HP1/4以下でこうげき+2。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="A", amount=+2)


def タラプのみ_boost_spdef(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """タラプのみ: HP1/4以下でとくぼう+2。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="D", amount=+2)


def バンジのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バンジのみ: HP1/4以下で最大HPの1/3を回復する。"""
    return _heal_on_quarter_hp(battle, ctx, value)


def フィラのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """フィラのみ: HP1/4以下で最大HPの1/3を回復する。"""
    return _heal_on_quarter_hp(battle, ctx, value)


def マゴのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マゴのみ: HP1/4以下で最大HPの1/3を回復する。"""
    return _heal_on_quarter_hp(battle, ctx, value)


def ヤタピのみ_boost_spatk(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ヤタピのみ: HP1/4以下でとくこう+2。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="C", amount=+2)


def リュガのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リュガのみ: HP1/4以下で最大HPの1/3を回復する。"""
    return _heal_on_quarter_hp(battle, ctx, value)


def サンのみ_boost_spatk(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """サンのみ: HP1/4以下でとくこう+2。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="C", amount=+2)


def アッキのみ_boost_defense_on_physical_super_effective(
    battle: Battle, ctx: AttackContext, value: Any
) -> HandlerReturn:
    """アッキのみ: 物理の弱点でダメージを受けたときぼうぎょ+2。"""
    mon = ctx.defender
    assert mon is not None
    if (
        ctx.move.category == "物理"
        and battle.damage_calculator.calc_def_type_modifier(ctx) > 1
    ):
        battle.modify_stats(mon, {"B": +2})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def ジャポのみ_retaliate_physical(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ジャポのみ: 物理技でダメージを受けたとき攻撃者に最大HPの1/8ダメージ。"""
    mon = ctx.defender
    assert mon is not None
    if ctx.move.category == "物理":
        battle.modify_hp(ctx.attacker, r=-1/8)
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def あかいいと_infatuate_foe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あかいいと: 持ち主がメロメロになったとき相手にもメロメロを付与する。"""
    if value != "メロメロ":
        return HandlerReturn(value=value)
    foe = battle.foe(ctx.source)
    battle.volatile_manager.apply(foe, "メロメロ", source=ctx.source)
    return HandlerReturn(value=value)


def クリアチャーム_block_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """クリアチャーム: 相手による能力ランク低下を無効化する。"""
    value = common.block_stat_drop_by_foe(value, ctx)
    return HandlerReturn(value=value)


def くちたけん_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くちたけん: ザシアン(れきせん)をザシアン(けんのおう)にフォルムチェンジする。"""
    mon = ctx.source
    if mon.name == "ザシアン(れきせん)":
        mon.set_form("ザシアン(けんのおう)")
    return HandlerReturn(value=value)


def くちたたて_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くちたたて: ザマゼンタ(れきせん)をザマゼンタ(たてのおう)にフォルムチェンジする。"""
    mon = ctx.source
    if mon.name == "ザマゼンタ(れきせん)":
        mon.set_form("ザマゼンタ(たてのおう)")
    return HandlerReturn(value=value)


_LATIOS_LATIAS_NAMES = frozenset({"ラティオス", "ラティアス", "メガラティオス", "メガラティアス"})


def こころのしずく_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こころのしずく: ラティオス・ラティアス持ちのエスパー・ドラゴン技1.2倍。"""
    if ctx.attacker.name in _LATIOS_LATIAS_NAMES and ctx.move.type in ("エスパー", "ドラゴン"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


_DIALGA_FORMS = frozenset({"ディアルガ", "ディアルガ(オリジン)"})


def こんごうだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こんごうだま: ディアルガ持ちのドラゴン・はがね技1.2倍。"""
    if ctx.attacker.name in _DIALGA_FORMS and ctx.move.type in ("ドラゴン", "はがね"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


_PALKIA_FORMS = frozenset({"パルキア", "パルキア(オリジン)"})


def しらたま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しらたま: パルキア持ちのドラゴン・みず技1.2倍。"""
    if ctx.attacker.name in _PALKIA_FORMS and ctx.move.type in ("ドラゴン", "みず"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def だいこんごうだま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいこんごうだま: ディアルガをオリジンフォルムにフォルムチェンジする。"""
    mon = ctx.source
    if mon.name == "ディアルガ":
        mon.set_form("ディアルガ(オリジン)")
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def だいこんごうだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいこんごうだま: ディアルガ(オリジン)持ちのドラゴン・はがね技1.2倍。"""
    if ctx.attacker.name == "ディアルガ(オリジン)" and ctx.move.type in ("ドラゴン", "はがね"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def だいしらたま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいしらたま: パルキアをオリジンフォルムにフォルムチェンジする。"""
    mon = ctx.source
    if mon.name == "パルキア":
        mon.set_form("パルキア(オリジン)")
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def だいしらたま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいしらたま: パルキア(オリジン)持ちのドラゴン・みず技1.2倍。"""
    if ctx.attacker.name == "パルキア(オリジン)" and ctx.move.type in ("ドラゴン", "みず"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def だいはっきんだま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいはっきんだま: ギラティナ(アナザー)をオリジンフォルムにフォルムチェンジする。"""
    mon = ctx.source
    if mon.name == "ギラティナ(アナザー)":
        mon.set_form("ギラティナ(オリジン)")
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def だいはっきんだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいはっきんだま: ギラティナ(オリジン)持ちのドラゴン・ゴースト技1.2倍。"""
    if ctx.attacker.name == "ギラティナ(オリジン)" and ctx.move.type in ("ドラゴン", "ゴースト"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


_PIKACHU_NAMES = frozenset({"ピカチュウ"})


def でんきだま_boost_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんきだま: ピカチュウ持ちの攻撃技こうげき・とくこう2倍。"""
    if ctx.attacker.name in _PIKACHU_NAMES and ctx.move.category != "変化":
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


_GIRATINA_FORMS = frozenset({"ギラティナ(アナザー)", "ギラティナ(オリジン)"})


def はっきんだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はっきんだま: ギラティナ持ちのドラゴン・ゴースト技1.2倍。"""
    if ctx.attacker.name in _GIRATINA_FORMS and ctx.move.type in ("ドラゴン", "ゴースト"):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def ブーストエナジー_refresh_on_item_enabled(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ブーストエナジー: アイテム有効化・取得時にパラドックスブーストを再判定する。"""
    from . import ability_paradox as paradox
    return paradox.refresh_paradox_charge_state(battle, ctx, value)


def あつぞこブーツ_check_hazard_immune(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """あつぞこブーツ: エントリーハザードを無効化する。"""
    return HandlerReturn(value=True, stop_event=True)


def おうじゃのしるし_flinch_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おうじゃのしるし: ダメージ技命中時10%の確率で相手をひるませる。"""
    defender = ctx.defender
    if (
        ctx.move.category != "変化"
        and defender is not None
        and battle.random.random() < 0.1
    ):
        battle.volatile_manager.apply(defender, "ひるみ", source=ctx.attacker, ctx=ctx)
    return HandlerReturn(value=value)


def おおきなねっこ_boost_drain(_battle: Battle, _ctx: Any, value: int) -> HandlerReturn:
    """おおきなねっこ: 吸収技のHP回収量を1.3倍にする。"""
    return HandlerReturn(value=int(value * 1.3))


def おんみつマント_negate_secondary(_battle: Battle, _ctx: AttackContext, _value: Any) -> HandlerReturn:
    """おんみつマント: 技の追加効果の確率を0にする。"""
    return HandlerReturn(value=0)


def かいがらのすず_heal_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かいがらのすず: ダメージ技命中時最大HPの1/8を回復する。"""
    if ctx.move.category != "変化":
        battle.modify_hp(ctx.attacker, r=1/8)
        _announce_item_triggered(battle, ctx.attacker)
    return HandlerReturn(value=value)


def こうこうのしっぽ_back_tier(_battle: Battle, _ctx: AttackContext, value: int) -> HandlerReturn:
    """こうこうのしっぽ: 行動順を1段階後ろにする。"""
    return HandlerReturn(value=value - 1)


def じゃくてんほけん_boost_on_super_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゃくてんほけん: 効果抜群のダメージを受けたときA・Cを+2。"""
    mon = ctx.defender
    if battle.damage_calculator.calc_def_type_modifier(ctx) > 1:
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
        battle.modify_stats(mon, {"A": +2, "C": +2})
    return HandlerReturn(value=value)


def じゅうでんち_boost_atk_on_electric_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうでんち: でんき技でダメージを受けたときこうげき+1。"""
    mon = ctx.defender
    if ctx.move.type == "でんき":
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
        battle.modify_stats(mon, {"A": +1})
    return HandlerReturn(value=value)


def しめつけバンド_boost_bind_damage(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """しめつけバンド: バインドのダメージを最大HPの1/6に増加する。"""
    return HandlerReturn(value=1/6)


def せんせいのツメ_priority_boost(battle: Battle, _ctx: AttackContext, value: int) -> HandlerReturn:
    """せんせいのツメ: 23.4%の確率で先制ティアを+1する。"""
    if battle.random.random() < 0.234:
        return HandlerReturn(value=value + 1)
    return HandlerReturn(value=value)


def とつげきチョッキ_block_status_move(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とつげきチョッキ: 変化技の使用を禁止する。"""
    if ctx.move.category == "変化":
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def とつげきチョッキ_boost_spdef(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とつげきチョッキ: 特殊技に対してとくぼうを1.5倍にする。"""
    if ctx.move.category == "特殊":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def ねらいのまと_negate_immunity(_battle: Battle, _ctx: AttackContext, value: int) -> HandlerReturn:
    """ねらいのまと: タイプ相性による無効（0倍）を1倍に戻す。"""
    if value == 0:
        value = 4096
    return HandlerReturn(value=value)


def のどスプレー_boost_spatk_on_sound(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """のどスプレー: 音技使用後にとくこう+1。"""
    mon = ctx.attacker
    if ctx.move.has_label("sound"):
        battle.modify_stats(mon, {"C": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def パワフルハーブ_skip_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワフルハーブ: 溜め技の溜めターンをスキップする。"""
    mon = ctx.attacker
    _announce_item_triggered(battle, mon)
    battle.consume_item(mon)
    return HandlerReturn(value=True, stop_event=True)


def パンチグローブ_boost_punch_power(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パンチグローブ: パンチ技の威力を1.1倍にする。"""
    if ctx.move.has_label("punch"):
        value = apply_fixed_modifier(value, 4506)
    return HandlerReturn(value=value)


def パンチグローブ_negate_punch_contact(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パンチグローブ: パンチ技の接触判定を無効化する。"""
    if ctx.move.has_label("punch"):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ひかりごけ_boost_spdef_on_water_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひかりごけ: みず技でダメージを受けたときとくぼう+1。"""
    mon = ctx.defender
    if ctx.move.type == "みず":
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
        battle.modify_stats(mon, {"D": +1})
    return HandlerReturn(value=value)


def ひかりのこな_reduce_accuracy(_battle: Battle, _ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひかりのこな: 命中率を0.9倍にする。"""
    return HandlerReturn(value=apply_fixed_modifier(value, 3686))


_MENTAL_HERB_TARGETS = frozenset({
    "いちゃもん", "アンコール", "なりきり", "かなしばり", "ちょうはつ", "さしおさえ"
})


def メンタルハーブ_cure_mental_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メンタルハーブ: 特定の揮発性状態が付与されたとき即解除する。"""
    mon = ctx.source
    if value in _MENTAL_HERB_TARGETS:
        battle.volatile_manager.remove(mon, value)
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def ビビリだま_boost_speed_on_intimidate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ビビリだま: いかくによってこうげきが下がったときすばやさ+1。"""
    mon = ctx.target
    if (
        value.get("A", 0) < 0
        and ctx.stat_change_reason == "いかく"
    ):
        battle.modify_stats(mon, {"S": +1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def フォーカスレンズ_boost_accuracy_second(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フォーカスレンズ: 後攻のとき命中率を1.2倍にする。"""
    attacker_player = battle.get_player(ctx.attacker)
    if battle.query.is_second_actor(attacker_player):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def ぼうごパット_negate_contact(_battle: Battle, _ctx: AttackContext, _value: Any) -> HandlerReturn:
    """ぼうごパット: 攻撃技の接触判定を無効にする。"""
    return HandlerReturn(value=False, stop_event=True)


def ぼうじんゴーグル_block_powder_move(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ぼうじんゴーグル: 粉技を無効化する。"""
    if ctx.move.has_label("powder"):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ぼうじんゴーグル_block_weather_damage(_battle: Battle, ctx: Any, value: Any) -> HandlerReturn:
    """ぼうじんゴーグル: 天候によるターン終了ダメージを無効化する。"""
    if ctx.hp_change_reason == "weather":
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def ものまねハーブ_copy_stat_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ものまねハーブ: 相手のランク上昇を+1でコピーする。"""
    mon = battle.foe(ctx.target)
    boosts = {s: 1 for s, v in value.items() if v > 0}
    if boosts:
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
        battle.modify_stats(mon, boosts)
    return HandlerReturn(value=value)


def ゆきだま_boost_defense_on_ice_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆきだま: こおり技でダメージを受けたときぼうぎょ+1。"""
    mon = ctx.defender
    if ctx.move.type == "こおり":
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
        battle.modify_stats(mon, {"B": +1})
    return HandlerReturn(value=value)


def ルームサービス_drop_speed_on_trick_room(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ルームサービス: トリックルーム発動時にすばやさ-1。"""
    mon = ctx.source
    if value.name == "トリックルーム":
        battle.modify_stats(mon, {"S": -1})
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)


def レッドカード_force_switch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レッドカード: ダメージを受けたとき攻撃者を強制交代させる。"""
    mon = ctx.defender
    foe = ctx.attacker
    foe_player = battle.get_player(foe)
    commands = battle.get_available_switch_commands(foe_player)
    if commands:
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
        command = battle.random.choice(commands)
        battle.run_switch(foe_player, battle.player_states[foe_player].team[command.index])
    return HandlerReturn(value=value)


def レンブのみ_retaliate_special(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レンブのみ: 特殊技でダメージを受けたとき攻撃者に最大HPの1/8ダメージ。"""
    mon = ctx.defender
    if ctx.move.category == "特殊":
        battle.modify_hp(ctx.attacker, r=-1/8)
        _announce_item_triggered(battle, mon)
        battle.consume_item(mon)
    return HandlerReturn(value=value)
