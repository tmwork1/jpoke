from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon, Move

from jpoke.utils.type_defs import RoleSpec, PokeType, Stat, AilmentName, Weather, Terrain, Side
from jpoke.utils.enums import Event
from jpoke.core.event import EventContext, HandlerReturn


def modify_hp(battle: Battle,
              ctx: EventContext,
              value: Any,
              target_spec: RoleSpec,
              v: int = 0,
              r: float = 0,
              prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    success = battle.modify_hp(target, v, r)
    return HandlerReturn(success)


def drain_hp(battle: Battle,
             ctx: EventContext,
             value: Any,
             from_: RoleSpec,
             to_: RoleSpec | None = None,
             v: int = 0,
             r: float = 0,
             prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)

    from_mon = ctx.resolve_role(battle, from_)
    if to_ is not None:
        to_mon = ctx.resolve_role(battle, to_)
    else:
        to_mon = battle.foe(from_mon)

    success, _ = battle.drain_hp(from_mon, to_mon, v, r)
    return HandlerReturn(success)


def heal_hp(battle: Battle,
            ctx: EventContext,
            value: Any,
            from_: RoleSpec,
            v: int = 0,
            r: float = 0,
            prob: float = 1) -> HandlerReturn:
    """指定したポケモンのHPを回復する

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）
        from_: 回復対象のRoleSpec
        v: 回復する固定HP量
        r: 最大HPに対する回復割合
        prob: 発動確率（デフォルト: 1）

    Returns:
        HandlerReturn: 成功時True
    """
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)

    from_mon = ctx.resolve_role(battle, from_)

    # 回復量を計算
    if v:
        heal_amount = v
    else:
        heal_amount = max(1, int(from_mon.max_hp * r))

    # HP回復を実行
    actual_heal = battle.modify_hp(from_mon, v=heal_amount)
    return HandlerReturn(actual_heal > 0)


def modify_stat(battle: Battle,
                ctx: EventContext,
                value: Any,
                stat: Stat,
                v: int,
                target_spec: RoleSpec,
                source_spec: RoleSpec | None = None,
                prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = battle.modify_stat(target, stat, v, source=source)
    return HandlerReturn(success)


def modify_stats(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 stats: dict[Stat, int],
                 target_spec: RoleSpec,
                 source_spec: RoleSpec | None = None,
                 prob: float = 1) -> HandlerReturn:
    """複数の能力ランクを同時に変化させる

    しろいハーブなどのアイテムが正しく動作するよう、
    複数の能力変化を一度に処理します。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）
        stats: 能力とランク変化量の辞書（例: {"B": -1, "D": -1}）
        target_spec: 対象のRoleSpec
        source_spec: 変化の原因となるポケモンのRoleSpec
        prob: 発動確率（デフォルト: 1）

    Returns:
        HandlerReturn: いずれかの能力が変化した場合True
    """
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)

    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)

    # battle.modify_stats()を使って一度に処理
    success = battle.modify_stats(target, stats, source=source)

    return HandlerReturn(success)


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  value: Any,
                  ailment: AilmentName,
                  target_spec: RoleSpec,
                  source_spec: RoleSpec | None = None,
                  prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = target.apply_ailment(battle.events, ailment, source=source)
    return HandlerReturn(success)


def apply_volatile(battle: Battle,
                   ctx: EventContext,
                   value: Any,
                   volatile: str,
                   target_spec: RoleSpec,
                   source_spec: RoleSpec | None = None,
                   count: int = 1,
                   prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = target.apply_volatile(battle.events, volatile, count=count, source=source)
    return HandlerReturn(success)


def cure_ailment(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 target_spec: RoleSpec,
                 source_spec: RoleSpec | None = None,
                 prob: float = 1) -> HandlerReturn:
    if prob < 1 and battle.random.random() >= prob:
        return HandlerReturn(False)
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = target.cure_ailment(battle.events, source=source)
    return HandlerReturn(success)


def activate_weather(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     source_spec: RoleSpec,
                     weather: Weather,
                     count: int = 5) -> HandlerReturn:
    source = ctx.resolve_role(battle, source_spec)
    success = battle.weather_mgr.activate(weather, count, source=source)
    return HandlerReturn(success)


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     source_spec: RoleSpec,
                     terrain: Terrain,
                     count: int = 5) -> HandlerReturn:
    source = ctx.resolve_role(battle, source_spec)
    success = battle.terrain_mgr.activate(terrain, count, source=source)
    return HandlerReturn(success)


def resolve_field_count(battle: Battle,
                        ctx: EventContext,
                        value: Any,
                        field: Weather | Terrain,
                        additonal_count: int) -> HandlerReturn:
    if ctx.field.orig_name == field:
        return HandlerReturn(True, value + additonal_count)
    else:
        return HandlerReturn(False, value)


def calc_effectiveness(battle: Battle,
                       attacker: Pokemon,
                       defender: Pokemon,
                       move: Move) -> float:
    """技のタイプ相性を計算する"""
    value = battle.events.emit(
        Event.ON_CALC_DEF_TYPE_MODIFIER,
        EventContext(attacker=attacker, defender=defender, move=move),
        4096
    ).value > 4096
    return value / 4096
