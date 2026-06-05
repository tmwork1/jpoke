"""アイテムハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.utils.type_defs import RoleSpec, Type, Weather, Terrain
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


def announce_item_triggered(battle: Battle,
                            ctx: EventContext,
                            value: Any,
                            *,
                            mon: Pokemon | None = None) -> HandlerReturn:
    if mon is None:
        mon = ctx.source

    mon.item.revealed = True
    battle.add_event_log(
        mon,
        LogCode.ITEM_TRIGGERED,
        payload={"item": mon.item.name}
    )
    return HandlerReturn(value=value)


def mega_modify_command_options(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
    """メガストーン: メガシンカコマンドを追加する。"""
    mon = ctx.source
    if not mon.can_megaevolve():
        return HandlerReturn(value=value)

    for cmd in value:
        if cmd.is_regular_move:
            value.append(Command.get_megaevol_command(cmd.index))

    return HandlerReturn(value=value)


def modify_power_by_type(battle: Battle,
                         ctx: EventContext,
                         value: Any,
                         type_: Type,
                         modifier: float) -> HandlerReturn:
    # ON_CALC_POWER_MODIFIER
    if ctx.move.type == type_:
        value = int(value * modifier)
    return HandlerReturn(value=value)


def modify_super_effective_damage(battle: Battle,
                                  ctx: EventContext,
                                  value: Any,
                                  type_: Type,
                                  modifier: float) -> HandlerReturn:
    # ON_CALC_DAMAGE_MODIFIER
    if ctx.move.type == type_ and battle.damage_calculator.calc_def_type_modifier(ctx) > 1:
        value = int(value * modifier)
    return HandlerReturn(value=value)


def resolve_field_count(battle: Battle,
                        ctx: EventContext,
                        value: list[Weather | Terrain | int],
                        *,
                        field: Weather | Terrain,
                        additonal_count: int) -> HandlerReturn:
    """指定場状態と一致するとき継続ターン数に加算する。"""
    name, count = value
    if field == name:
        count += additonal_count
    return HandlerReturn(value=[name, count])


def いかさまダイス_modify_hit_count(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """いかさまダイス: 2-5回連続技のヒット数を4回または5回へ補正する。"""
    min_hits, max_hits = ctx.move.min_hits, ctx.move.max_hits
    if (min_hits, max_hits) == (2, 5):
        value = 4 if battle.random.random() < 0.5 else 5
    return HandlerReturn(value=value)


def いのちのたま_recoil(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    if (
        ctx.move.category != "変化"
        and common.self_damage(battle, ctx, value, r=1/8)
    ):
        announce_item_triggered(battle, ctx, value, mon=ctx.attacker)
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


def だっしゅつボタン_reserve_switch(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    player = battle.get_player(ctx.defender)
    battle.player_states[player].interrupt = Interrupt.EJECTBUTTON
    return HandlerReturn(value=value)


def たべのこし_heal_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """たべのこし: ターン終了時HP回復"""
    mon = ctx.source
    if battle.modify_hp(mon, r=1/16):
        announce_item_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ちからのハチマキ_boost_physical(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """物理技1.1倍"""
    if ctx.move.category == "物理":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def とくせいガード_block_ability_disable(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """とくせいガード: 特性無効化をブロックする。"""
    ability = ctx.source.ability
    was_self_disabled = ability.consumed
    ability.reset_enable_state()
    # 自己無効化している特性はリセット後も無効状態を維持する
    if was_self_disabled:
        ability.replace_disabled_reasons("consumed")
    return HandlerReturn(value=value)


def ものしりメガネ_boost_special(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """特殊技1.1倍"""
    if ctx.move.category == "特殊":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)

# 以下、タイプ強化アイテム


def かたいいし_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="いわ", modifier=4915/4096)


def きせきのたね_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="くさ", modifier=4915/4096)


def ぎんのこな_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="むし", modifier=4915/4096)


def くろおび_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="あく", modifier=4915/4096)


def さらさらいわ_resolve_field_count(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return resolve_field_count(battle, ctx, value, field="すなあらし", additonal_count=3)


def じしゃく_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="でんき", modifier=4915/4096)


def シルクのスカーフ_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="ノーマル", modifier=4915/4096)


def しんぴのしずく_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="みず", modifier=4915/4096)


def するどいくちばし_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="ひこう", modifier=4915/4096)


def せいれいプレート_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="フェアリー", modifier=4915/4096)


def どくバリ_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="どく", modifier=4915/4096)


def とけないこおり_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="こおり", modifier=4915/4096)


def ノーマルジュエル_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="ノーマル", modifier=6144/4096)


def のろいのおふだ_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="ゴースト", modifier=4915/4096)


def まがったスプーン_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="エスパー", modifier=4915/4096)


def メタルコート_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="はがね", modifier=4915/4096)


def もくたん_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="ほのお", modifier=4915/4096)


def やわらかいすな_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="じめん", modifier=4915/4096)


def ようせいのハネ_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="フェアリー", modifier=4915/4096)


def りゅうのキバ_modify_power_by_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_power_by_type(battle, ctx, value, type_="ドラゴン", modifier=4915/4096)

# 以下、タイプ半減実


def ホズのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="ノーマル", modifier=2048/4096)


def リンドのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="くさ", modifier=2048/4096)


def オッカのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="ほのお", modifier=2048/4096)


def イトケのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="みず", modifier=2048/4096)


def ソクノのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="でんき", modifier=2048/4096)


def カシブのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="ゴースト", modifier=2048/4096)


def ヨロギのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="いわ", modifier=2048/4096)


def タンガのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="むし", modifier=2048/4096)


def ウタンのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="エスパー", modifier=2048/4096)


def バコウのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="ひこう", modifier=2048/4096)


def シュカのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="じめん", modifier=2048/4096)


def ビアーのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="どく", modifier=2048/4096)


def ヨプのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="かくとう", modifier=2048/4096)


def ヤチェのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="こおり", modifier=2048/4096)


def リリバのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="はがね", modifier=2048/4096)


def ナモのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="あく", modifier=2048/4096)


def ハバンのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="ドラゴン", modifier=2048/4096)


def ロゼルのみ_modify_super_effective_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_super_effective_damage(battle, ctx, value, type_="フェアリー", modifier=2048/4096)
