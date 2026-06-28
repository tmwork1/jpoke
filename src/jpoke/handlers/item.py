"""アイテムハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext
    from jpoke.model import Pokemon, Move

from jpoke.utils.type_defs import RoleSpec, Stat, Type, MoveCategory, \
    AilmentName, WeatherName, TerrainName, SideFieldName
from jpoke.utils.math import apply_fixed_modifier
from jpoke.enums import Interrupt, LogCode, Command
from jpoke.core import HandlerReturn, Handler
from jpoke.data.pokedex import POKEDEX

# 何らかのポケモンの進化前として登録されている = 進化先が存在する（未進化）ポケモン名の集合
_HAS_EVOLUTION: frozenset[str] = frozenset(
    d.pre_evolution for d in POKEDEX.values() if d.pre_evolution
)


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
        mon, LogCode.ITEM_TRIGGERED,
        payload={"item": mon.item.name}
    )


def _announce_and_consume_item(battle: Battle, mon: Pokemon) -> None:
    _announce_item_triggered(battle, mon)
    battle.consume_item(mon)


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
                          modifier: int) -> HandlerReturn:
    if move.type == type_:
        value = apply_fixed_modifier(value, modifier)
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
                         *fields: WeatherName | TerrainName | SideFieldName,
                         additonal_count: int) -> HandlerReturn:
    """指定場状態と一致するとき継続ターン数に加算する。"""
    if value[0] in fields:
        value[1] += additonal_count
    return HandlerReturn(value=value)


def _terrain_seed_boost(battle: Battle, ctx: EventContext, value: Any,
                        terrain: TerrainName, stat: Stat) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.terrain.name == terrain:
        battle.modify_stats(mon, {stat: +1})
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


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


def _heal_berry(battle: Battle,
                ctx: EventContext,
                value: Any,
                *,
                denominator: int,
                heal_r: float | None = None,
                heal_v: int | None = None) -> HandlerReturn:
    mon = ctx.target
    assert mon is not None
    # value >= mon.max_hp はほおばる等による強制発動（HP閾値チェックを無視する）
    if mon.hp * denominator <= mon.max_hp or value >= mon.max_hp:
        if heal_r is not None:
            battle.modify_hp(mon, r=heal_r)
        else:
            battle.modify_hp(mon, v=heal_v)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def _apply_ailment_from_item(battle: Battle, ctx: EventContext, value: Any, ailment: AilmentName) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.ailment_manager.apply(mon, ailment, source=mon):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def _cure_ailment_berry(battle: Battle,
                        ctx: EventContext,
                        value: Any,
                        *ailment_names: str) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    condition = mon.ailment.name in ailment_names if ailment_names else mon.ailment.is_active
    if condition and battle.ailment_manager.remove(mon):
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def _cure_ailment_berry_on_apply(battle: Battle,
                                 ctx: EventContext,
                                 value: Any,
                                 *ailment_names: str) -> HandlerReturn:
    """ON_APPLY_AILMENT用: 状態異常付与直後に治療して消費する共通処理。"""
    mon = ctx.target
    assert mon is not None
    if not ailment_names or value in ailment_names:
        if battle.ailment_manager.remove(mon):
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # _heal_on_hp_dropを外部からも参照する関数にすれば、この関数は不要
    return _heal_berry(battle, ctx, value, denominator=4, heal_r=1/3)


def _boost_on_quarter_hp(battle: Battle,
                         ctx: EventContext,
                         value: Any,
                         stat: Stat,
                         amount: int) -> HandlerReturn:
    """1/4HP以下になった瞬間に能力を上昇させる共通処理。

    value >= mon.max_hp はほおばる等による強制発動（HP閾値チェックを無視する）。
    """
    mon = ctx.target
    assert mon is not None
    if mon.hp * 4 <= mon.max_hp or value >= mon.max_hp:
        battle.modify_stats(mon, {stat: amount})
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def _boost_on_attack_category(battle: Battle,
                              ctx: AttackContext,
                              value: Any,
                              category: MoveCategory,
                              stat: Stat,
                              amount: int) -> HandlerReturn:
    """指定カテゴリの技でダメージを受けたとき能力を上昇させる共通処理。"""
    mon = ctx.defender
    assert mon is not None
    if ctx.move.category == category:
        battle.modify_stats(mon, {stat: amount})
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def _retaliate_on_category(battle: Battle,
                           ctx: AttackContext,
                           value: Any,
                           category: MoveCategory) -> HandlerReturn:
    mon = ctx.defender
    assert mon is not None
    if ctx.move.category == category:
        battle.modify_hp(ctx.attacker, r=-1/8)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def _dedicated_item_form_change(battle: Battle,
                                ctx: EventContext,
                                value: Any,
                                base_form: str,
                                origin_form: str) -> HandlerReturn:
    mon = ctx.source
    if mon is not None and mon.name == base_form:
        mon.set_form(origin_form)
    return HandlerReturn(value=value)


def _dedicated_item_modify_power(ctx: AttackContext,
                                 value: Any,
                                 allowed_names: frozenset[str],
                                 allowed_types: tuple[Type, ...]) -> HandlerReturn:
    if (
        ctx.attacker.name in allowed_names
        and ctx.move.type in allowed_types
    ):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def _boost_stat_on_type_hit(battle: Battle,
                            ctx: AttackContext,
                            value: Any,
                            *,
                            type_: Type,
                            stats: dict[Stat, int]) -> HandlerReturn:
    mon = ctx.defender
    assert mon is not None
    if ctx.move.type == type_:
        _announce_and_consume_item(battle, mon)
        battle.modify_stats(mon, stats)
    return HandlerReturn(value=value)


def あかいいと_infatuate_foe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あかいいと: 持ち主がメロメロになったとき相手にもメロメロを付与する。"""
    if value != "メロメロ":
        return HandlerReturn(value=value)
    foe = battle.foe(ctx.source)
    battle.volatile_manager.apply(foe, "メロメロ", source=ctx.source)
    return HandlerReturn(value=value)


def アッキのみ_boost_defense_on_physical_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アッキのみ: 物理技でダメージを受けたときぼうぎょ+1。"""
    return _boost_on_attack_category(battle, ctx, value, "物理", "B", +1)


def あついいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "はれ", additonal_count=3)


def あつぞこブーツ_check_hazard_immune(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """あつぞこブーツ: エントリーハザードを無効化する。"""
    return HandlerReturn(value=True, stop_event=True)


def いかさまダイス_modify_hit_count(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """いかさまダイス: 2-5回連続技のヒット数を4回または5回へ補正する。"""
    min_hits, max_hits = ctx.move.min_hits, ctx.move.max_hits
    if (min_hits, max_hits) == (2, 5):
        value = 4 if battle.random.random() < 0.5 else 5
    return HandlerReturn(value=value)


def イトケのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="みず", modifier=2048/4096)


def いのちのたま_boost_atk(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちのたま: 攻撃技の攻撃補正を1.3倍にする。"""
    if ctx.move.is_attack:
        value = apply_fixed_modifier(value, 5324)
    return HandlerReturn(value=value)


def いのちのたま_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    if ctx.move.is_attack:
        battle.modify_hp(ctx.attacker, r=-1/8, source=ctx.attacker)
        _announce_item_triggered(battle, ctx.attacker)
    return HandlerReturn(value=value)


def イバンのみ_boost_priority(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """イバンのみ: 先制フラグが立っているとき行動ティアを+1する。"""
    mon = ctx.attacker
    if mon.item.count == 1:
        battle.consume_item(mon)
        return HandlerReturn(value=value + 1)
    return HandlerReturn(value=value)


def イバンのみ_set_priority_flag(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """イバンのみ: HPが1/4以下に下がった瞬間に先制フラグを立てる。"""
    mon = ctx.target
    assert mon is not None
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * 4 > mon.max_hp and hp_after * 4 <= mon.max_hp:
        mon.item.count = 1
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def ウタンのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="エスパー", modifier=2048/4096)


def エレキシード_boost_defense(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _terrain_seed_boost(battle, ctx, value, "エレキフィールド", "B")


def flinch_on_hit_10pct(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おうじゃのしるし、するどいキバ: ダメージ技命中時10%の確率で相手をひるませる。"""
    defender = ctx.defender
    if (
        ctx.move.is_attack
        and defender is not None
        and battle.random.random() < 0.1
    ):
        battle.volatile_manager.apply(defender, "ひるみ", source=ctx.attacker)
    return HandlerReturn(value=value)


def おおきなねっこ_boost_drain(_battle: Battle, _ctx: Any, value: int) -> HandlerReturn:
    """おおきなねっこ: 吸収技のHP回収量を1.3倍にする。"""
    value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def オッカのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ほのお", modifier=2048/4096)


def オボンのみ_heal_on_half_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _heal_berry(battle, ctx, value, denominator=2, heal_r=1/4)


def オレンのみ_heal_on_half_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _heal_berry(battle, ctx, value, denominator=2, heal_v=10)


def おんみつマント_negate_secondary(_battle: Battle, _ctx: AttackContext, _value: Any) -> HandlerReturn:
    """おんみつマント: 技の追加効果の確率を0にする。"""
    return HandlerReturn(value=0)


def オーガポンのめん_boost_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーガポンのめん共通: 物理技の攻撃補正を1.2倍にする。"""
    if ctx.move.category == "物理":
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def かいがらのすず_drain_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かいがらのすず: ダメージ技命中時に与ダメージの1/8を回復する。"""
    heal_amount = value // 8
    if heal_amount > 0 and battle.modify_hp(ctx.attacker, v=heal_amount):
        _announce_item_triggered(battle, ctx.attacker)
    return HandlerReturn(value=value)


def かえんだま_apply_burn(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かえんだま: ターン終了時にやけどを付与する。"""
    return _apply_ailment_from_item(battle, ctx, value, "やけど")


def カゴのみ_cure_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "ねむり")


def カゴのみ_cure_sleep_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """カゴのみ: ねむり付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "ねむり")


def カシブのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ゴースト", modifier=2048/4096)


def かたいいし_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="いわ", modifier=4915)


def カムラのみ_boost_speed(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """カムラのみ: HP1/4以下ですばやさ+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="S", amount=+1)


def からぶりほけん_boost_speed_on_miss(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """からぶりほけん: 技が外れたときすばやさ+2。"""
    mon = ctx.attacker
    assert mon is not None
    battle.modify_stats(mon, {"S": +2})
    _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def きあいのタスキ_survive_ohko(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きあいのタスキ: HPが満タンのときひんし以上のダメージをHP1で耐える。"""
    mon = ctx.defender
    assert mon is not None
    if mon.hp == mon.max_hp and value >= mon.hp:
        value = mon.hp - 1
        _announce_and_consume_item(battle, mon)
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
    return _modify_power_by_type(ctx.move, value, type_="くさ", modifier=4915)


def きゅうこん_boost_spatk_on_water_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きゅうこん: みず技でダメージを受けたときとくこう+1。"""
    return _boost_stat_on_type_hit(battle, ctx, value, type_="みず", stats={"C": +1})


def きれいなぬけがら_check_trapped(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """きれいなぬけがら: 拘束効果を無効化する。"""
    return HandlerReturn(value=False, stop_event=True)


def キーのみ_cure_confusion(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if mon.has_volatile("こんらん"):
        battle.volatile_manager.remove(mon, "こんらん")
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ぎんのこな_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="むし", modifier=4915)


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


def くっつきバリ_damage_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くっつきバリ: ターン終了時に最大HPの1/8ダメージを受ける。"""
    mon = ctx.source
    assert mon is not None
    if battle.modify_hp(mon, r=-1/8):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def くっつきバリ_transfer_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くっつきバリ: 接触攻撃者がアイテムを持っていない場合、攻撃者に転送する。"""
    mon = ctx.defender
    assert mon is not None
    if (
        battle.query.is_contact(ctx) and
        not ctx.attacker.has_item()
    ):
        _announce_item_triggered(battle, mon)
        battle.remove_item(mon)
        battle.gain_item(ctx.attacker, "くっつきバリ")
    return HandlerReturn(value=value)


def クラボのみ_cure_paralysis(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "まひ")


def クラボのみ_cure_paralysis_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """クラボのみ: まひ付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "まひ")


def クリアチャーム_block_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """クリアチャーム: 相手による能力ランク低下を無効化する。"""
    mon = ctx.target
    assert mon is not None
    blocked = value
    if ctx.source is not None and ctx.source != ctx.target:
        blocked = {s: v for s, v in value.items() if v >= 0}
    if blocked != value:
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=blocked)


def くろいてっきゅう_halve_speed(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=apply_fixed_modifier(value, 2048))


def くろいてっきゅう_negate_floating(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    return HandlerReturn(value=False, stop_event=True)


def くろいヘドロ_heal_or_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    r = 1/16 if mon.has_type("どく") else -1/8
    if battle.modify_hp(mon, r=r):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def くろいメガネ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="あく", modifier=4915)


def くろおび_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="かくとう", modifier=4915)


def グラスシード_boost_defense(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _terrain_seed_boost(battle, ctx, value, "グラスフィールド", "B")


def グランドコート_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "エレキフィールド", "グラスフィールド", "ミストフィールド", "サイコフィールド", additonal_count=3)


def こうかくレンズ_modify_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こうかくレンズ: 命中率を1.1倍にする。"""
    return HandlerReturn(value=apply_fixed_modifier(value, 4506))


def こうこうのしっぽ_back_tier(_battle: Battle, _ctx: AttackContext, value: int) -> HandlerReturn:
    """こうこうのしっぽ: 行動順を1段階後ろにする。"""
    return HandlerReturn(value=value - 1)


def こころのしずく_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こころのしずく: ラティオス・ラティアス持ちのエスパー・ドラゴン技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, {"ラティオス", "ラティアス"}, ("エスパー", "ドラゴン"))


def こだわり_lock_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こだわりアイテム: 使用した技でロックする。"""
    mon = ctx.attacker
    if not mon.has_volatile("こだわり"):
        battle.volatile_manager.apply(
            mon, "こだわり", source=mon, move_name=ctx.move.name
        )
    return HandlerReturn(value=value)


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


def こんごうだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こんごうだま: ディアルガ持ちのドラゴン・はがね技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"ディアルガ", "ディアルガ(オリジン)"}), ("ドラゴン", "はがね"))


def ゴツゴツメット_chip_contact_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.defender
    assert mon is not None
    if _apply_contact_item_chip(battle, ctx, ratio=1/6):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def サイコシード_boost_spdef(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _terrain_seed_boost(battle, ctx, value, "サイコフィールド", "D")


def さらさらいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "すなあらし", additonal_count=3)


def サンのみ_apply_focus_energy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """サンのみ: HP1/4以下できゅうしょアップ状態になる。"""
    mon = ctx.target
    assert mon is not None
    if mon.hp <= mon.max_hp // 4:
        if battle.volatile_manager.apply(mon, "きゅうしょアップ", count=2):
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def しめったいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "あめ", additonal_count=3)


def しめつけバンド_boost_bind_damage(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """しめつけバンド: バインドのダメージを最大HPの1/6に増加する。"""
    return HandlerReturn(value=1/6)


def シュカのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="じめん", modifier=2048/4096)


def しらたま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しらたま: パルキア持ちのドラゴン・みず技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"パルキア", "パルキア(オリジン)"}), ("ドラゴン", "みず"))


def シルクのスカーフ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ノーマル", modifier=4915)


def しろいハーブ_cancel_stat_drop(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # value は actual_changes ({stat: 変化量})。今回の変化で負になったランクがあるか確認する。
    mon = ctx.target
    assert mon is not None
    triggered = any(v < 0 and mon.rank[s] < 0 for s, v in value.items())
    if triggered:
        for s in list(mon.rank.keys()):
            if mon.rank[s] < 0:
                mon.rank[s] = 0
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def しんかのきせき_boost_defenses(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しんかのきせき: 未進化ポケモンのぼうぎょ・とくぼうを1.5倍にする。"""
    if ctx.defender.name in _HAS_EVOLUTION:
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def しんぴのしずく_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="みず", modifier=4915)


def じしゃく_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="でんき", modifier=4915)


def じゃくてんほけん_boost_on_super_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゃくてんほけん: 効果抜群のダメージを受けたときA・Cを+2。"""
    mon = ctx.defender
    assert mon is not None
    if not mon.alive:
        return HandlerReturn(value=value)
    if battle.query.is_super_effective(ctx):
        _announce_and_consume_item(battle, mon)
        battle.modify_stats(mon, {"A": +2, "C": +2})
    return HandlerReturn(value=value)


def ジャポのみ_retaliate_physical(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ジャポのみ: 物理技でダメージを受けたとき攻撃者に最大HPの1/8ダメージ。"""
    return _retaliate_on_category(battle, ctx, value, "物理")


def じゅうでんち_boost_atk_on_electric_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうでんち: でんき技でダメージを受けたときこうげき+1。"""
    return _boost_stat_on_type_hit(battle, ctx, value, type_="でんき", stats={"A": +1})


def スターのみ_random_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スターのみ: HP1/4以下でランダムな能力+2。"""
    mon = ctx.target
    assert mon is not None
    if mon.hp <= mon.max_hp // 4:
        stat = battle.random.choice(["A", "B", "C", "D", "S"])
        battle.modify_stats(mon, {stat: +2})
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def するどいくちばし_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ひこう", modifier=4915)


def するどいツメ_boost_critical_rank(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """するどいツメ: 急所ランクを+1する。"""
    return HandlerReturn(value=value + 1)


def ズアのみ_boost_spdef(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ズアのみ: HP1/4以下でとくぼう+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="D", amount=+1)


def せいれいプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="フェアリー", modifier=4915)


def せんせいのツメ_priority_boost(battle: Battle, _ctx: AttackContext, value: int) -> HandlerReturn:
    """せんせいのツメ: 20%の確率で先制ティアを+1する。"""
    if battle.random.random() < 0.2:
        return HandlerReturn(value=value + 1)
    return HandlerReturn(value=value)


def ソクノのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="でんき", modifier=2048/4096)


def たつじんのおび_boost_super_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    if battle.query.is_super_effective(ctx):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def たべのこし_heal_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """たべのこし: ターン終了時HP回復"""
    mon = ctx.source
    if battle.modify_hp(mon, r=1/16):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def タラプのみ_boost_spdef(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """タラプのみ: 特殊技でダメージを受けたときとくぼう+1。"""
    return _boost_on_attack_category(battle, ctx, value, "特殊", "D", +1)


def タンガのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="むし", modifier=2048/4096)


def だいこんごうだま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいこんごうだま: ディアルガをオリジンフォルムにフォルムチェンジする。"""
    return _dedicated_item_form_change(battle, ctx, value, "ディアルガ", "ディアルガ(オリジン)")


def だいこんごうだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいこんごうだま: ディアルガ(オリジン)持ちのドラゴン・はがね技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"ディアルガ(オリジン)"}), ("ドラゴン", "はがね"))


def だいしらたま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいしらたま: パルキアをオリジンフォルムにフォルムチェンジする。"""
    return _dedicated_item_form_change(battle, ctx, value, "パルキア", "パルキア(オリジン)")


def だいしらたま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいしらたま: パルキア(オリジン)持ちのドラゴン・みず技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"パルキア(オリジン)"}), ("ドラゴン", "みず"))


def だいはっきんだま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいはっきんだま: ギラティナ(アナザー)をオリジンフォルムにフォルムチェンジする。"""
    return _dedicated_item_form_change(battle, ctx, value, "ギラティナ(アナザー)", "ギラティナ(オリジン)")


def だいはっきんだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいはっきんだま: ギラティナ(オリジン)持ちのドラゴン・ゴースト技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"ギラティナ(オリジン)"}), ("ドラゴン", "ゴースト"))


def だっしゅつパック_reserve_switch(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # valueは{stat: change}の辞書
    player = battle.get_player(ctx.target)
    if (
        any(v < 0 for v in value.values())
        and battle.can_switch(player)
    ):
        battle.player_states[player].interrupt = Interrupt.EJECTPACK_REQUESTED
    return HandlerReturn(value=value)


def だっしゅつボタン_reserve_switch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    player = battle.get_player(ctx.defender)
    battle.player_states[player].interrupt = Interrupt.EJECTBUTTON
    return HandlerReturn(value=value)


def チイラのみ_boost_attack(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """チイラのみ: HP1/4以下でこうげき+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="A", amount=+1)


def ちからのハチマキ_boost_physical(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """物理技1.1倍"""
    if ctx.move.category == "物理":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def チーゴのみ_cure_burn(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "やけど")


def チーゴのみ_cure_burn_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """チーゴのみ: やけど付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "やけど")


def つめたいいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "ゆき", additonal_count=3)


def でんきだま_boost_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんきだま: ピカチュウ持ちの攻撃技こうげき・とくこう2倍。"""
    if ctx.attacker.name in {"ピカチュウ"}:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def とくせいガード_check_ability_disable(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """とくせいガード: 特性の無効化を防ぐ。"""
    return HandlerReturn(value=True, stop_event=True)


def とけないこおり_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="こおり", modifier=4915)


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


def とつげきチョッキ_modify_command_options(_battle: Battle, ctx: EventContext, value: list) -> HandlerReturn:
    """とつげきチョッキ: 変化技のコマンドを選択肢から除外する。"""
    mon = ctx.source
    return HandlerReturn(value=[
        cmd for cmd in value
        if not (cmd.is_type("move") and mon.moves[cmd.index].category == "変化")
    ])


def どくどくだま_apply_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくどくだま: ターン終了時にもうどくを付与する。"""
    return _apply_ailment_from_item(battle, ctx, value, "もうどく")


def どくバリ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="どく", modifier=4915)


def ナゾのみ_heal_on_super_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ナゾのみ: 効果抜群のダメージを受けたときHPを最大HPの25%回復する。"""
    mon = ctx.defender
    assert mon is not None
    if battle.query.is_super_effective(ctx):
        battle.modify_hp(mon, r=1/4)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ナナシのみ_cure_freeze(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "こおり")


def ナナシのみ_cure_freeze_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ナナシのみ: こおり付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "こおり")


def ナモのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="あく", modifier=2048/4096)


def ねばりのかぎづめ_fix_bind_duration(_battle: Battle, _ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねばりのかぎづめ: バインドの継続ターンを7ターンに固定する。"""
    if value[0] == "バインド":
        value[1] = 7
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
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def のろいのおふだ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ゴースト", modifier=4915)


def ノーマルジュエル_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    if ctx.move.type == "ノーマル":
        value = apply_fixed_modifier(value, 6144)
        _announce_and_consume_item(battle, ctx.attacker)
    return HandlerReturn(value=value)


def はっきんだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はっきんだま: ギラティナ持ちのドラゴン・ゴースト技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, {"ギラティナ(アナザー)"}, ("ドラゴン", "ゴースト"))


def ハバンのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ドラゴン", modifier=2048/4096)


def バコウのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ひこう", modifier=2048/4096)


def パワフルハーブ_skip_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワフルハーブ: 溜め技の溜めターンをスキップする。"""
    mon = ctx.attacker
    _announce_and_consume_item(battle, mon)
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
    return _boost_stat_on_type_hit(battle, ctx, value, type_="みず", stats={"D": +1})


def ひかりのこな_reduce_accuracy(_battle: Battle, _ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひかりのこな: 命中率を0.9倍にする。"""
    value = apply_fixed_modifier(value, 3686)
    return HandlerReturn(value=value)


def ひかりのねんど_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "リフレクター", "ひかりのかべ", "オーロラベール", additonal_count=3)


def ヒメリのみ_restore_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ヒメリのみ: 使用した技のPPが0になったときPPを回復する。"""
    mon = ctx.attacker
    if ctx.move.pp == 0:
        ctx.move.pp = min(10, ctx.move.data.pp)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ヒメリのみ_restore_pp_on_item_enabled(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アイテムが有効になったときにPPが0の技のPPを回復する"""
    mon = ctx.source
    assert mon is not None
    move = next((m for m in mon.moves if m.pp == 0), None)
    if move is not None:
        move.pp = min(10, move.data.pp)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ビアーのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="どく", modifier=2048/4096)


def ビビリだま_boost_speed_on_intimidate(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ビビリだま: いかくによってこうげきが下がったときすばやさ+1。"""
    mon = ctx.target
    assert mon is not None
    if (
        value.get("A", 0) < 0
        and ctx.stat_change_reason == "いかく"
    ):
        battle.modify_stats(mon, {"S": +1})
        _announce_and_consume_item(battle, mon)
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


def フォーカスレンズ_boost_accuracy_second(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フォーカスレンズ: 後攻のとき命中率を1.2倍にする。"""
    attacker_player = battle.get_player(ctx.attacker)
    if battle.query.is_second_actor(attacker_player):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def ブーストエナジー_refresh_paradox_charge(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ブーストエナジー: アイテム有効化・取得時にパラドックスブーストを再判定する。"""
    from . import ability_paradox as paradox
    return paradox.refresh_paradox_charge_state(battle, ctx, value)


def ホズのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ノーマル", modifier=2048/4096)


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
    if ctx.hp_change_reason == "sandstorm":
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def まがったスプーン_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="エスパー", modifier=4915)


def ミクルのみ_boost_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミクルのみ: 命中率フラグが立っているとき次の技の命中率を1.2倍にする。"""
    mon = ctx.attacker
    if mon.item.count == 1:
        battle.consume_item(mon)
        return HandlerReturn(value=apply_fixed_modifier(value, 4915))
    return HandlerReturn(value=value)


def ミクルのみ_set_accuracy_flag(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ミクルのみ: HP1/4以下に下がった瞬間に命中率アップフラグを立てる。"""
    mon = ctx.target
    assert mon is not None
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * 4 > mon.max_hp and hp_after * 4 <= mon.max_hp:
        mon.item.count = 1
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def ミストシード_boost_spdef(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _terrain_seed_boost(battle, ctx, value, "ミストフィールド", "D")


def メタルコート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="はがね", modifier=4915)


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


def メンタルハーブ_cure_mental_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メンタルハーブ: 特定の揮発性状態が付与されたとき即解除する。"""
    mon = ctx.source
    assert mon is not None
    if value in {"いちゃもん", "アンコール", "かなしばり", "ちょうはつ"}:
        battle.volatile_manager.remove(mon, value)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def もくたん_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ほのお", modifier=4915)


def ものしりメガネ_boost_special(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """特殊技1.1倍"""
    if ctx.move.category == "特殊":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def ものまねハーブ_copy_stat_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ものまねハーブ: 相手のランク上昇を+1でコピーする。"""
    mon = battle.foe(ctx.target)
    boosts = {s: v for s, v in value.items() if v > 0}
    if boosts:
        _announce_and_consume_item(battle, mon)
        battle.modify_stats(mon, boosts)
    return HandlerReturn(value=value)


def モモンのみ_cure_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "どく", "もうどく")


def モモンのみ_cure_poison_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """モモンのみ: どく・もうどく付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "どく", "もうどく")


def ヤタピのみ_boost_spatk(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ヤタピのみ: HP1/4以下でとくこう+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="C", amount=+1)


def ヤチェのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="こおり", modifier=2048/4096)


def やわらかいすな_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="じめん", modifier=4915)


def ゆきだま_boost_defense_on_ice_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆきだま: こおり技でダメージを受けたときぼうぎょ+1。"""
    return _boost_stat_on_type_hit(battle, ctx, value, type_="こおり", stats={"B": +1})


def ようせいのハネ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="フェアリー", modifier=4915)


def ヨプのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="かくとう", modifier=2048/4096)


def ヨロギのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="いわ", modifier=2048/4096)


def ラムのみ_cure_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value)


def ラムのみ_cure_ailment_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ラムのみ: 状態異常付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value)


def りゅうのキバ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ドラゴン", modifier=4915)


def リュガのみ_boost_defense(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リュガのみ: HP1/4以下でぼうぎょ+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="B", amount=+1)


def リリバのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="はがね", modifier=2048/4096)


def リンドのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="くさ", modifier=2048/4096)


def ルームサービス_drop_speed_on_trick_room(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ルームサービス: トリックルーム発動時にすばやさ-1。"""
    mon = ctx.source
    assert mon is not None
    if value.name == "トリックルーム":
        battle.modify_stats(mon, {"S": -1})
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def レッドカード_force_switch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レッドカード: ダメージを受けたとき攻撃者を強制交代させる。"""
    mon = ctx.defender
    assert mon is not None
    foe = ctx.attacker
    rival = battle.get_player(foe)

    if battle.can_switch(rival):
        _announce_and_consume_item(battle, mon)
        commands = battle.get_available_switch_commands(rival)
        command = battle.random.choice(commands)
        new_mon = battle.player_states[rival].team[command.index]
        battle.run_switch(rival, new_mon)

    return HandlerReturn(value=value)


def レンブのみ_retaliate_special(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レンブのみ: 特殊技でダメージを受けたとき攻撃者に最大HPの1/8ダメージ。"""
    return _retaliate_on_category(battle, ctx, value, "特殊")


def ロゼルのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="フェアリー", modifier=2048/4096)
