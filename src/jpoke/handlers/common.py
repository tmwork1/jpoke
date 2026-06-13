# TODO : このモジュールは必要性が少ないため廃止
"""複数の効果実装で使い回す共通ハンドラ群。"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext
    from jpoke.model import Pokemon

from jpoke.utils.type_defs import RoleSpec, Stat, AilmentName, VolatileName, \
    WeatherName, TerrainName, GlobalFieldName, HPChangeReason
from jpoke.enums import Event
from jpoke.core.handler import HandlerReturn


def modify_hp(battle: Battle,
              ctx: EventContext,
              value: Any,
              target_spec: RoleSpec,
              source_spec: RoleSpec | None = None,
              v: int = 0,
              r: float = 0,
              chance: float = 1,
              reason: HPChangeReason = "") -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """対象のHPを固定値または割合で増減させる。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント連鎖値（未使用）
        target_spec: HP変更対象のRoleSpec
        v: HP増減の固定値
        r: 最大HPに対する増減割合
        chance: 発動確率
        reason: 変更理由

    Returns:
        実際に変化したHP量を value に持つ HandlerReturn
    """
    chance = battle.resolve_secondary_chance(ctx, chance)
    if not (chance < 1 and battle.random.random() >= chance):
        target = ctx.resolve_role(battle, target_spec)
        source = ctx.resolve_role(battle, source_spec)
        v = battle.modify_hp(target, v, r, reason=reason, source=source)
    return HandlerReturn(value=v)


def _self_role_spec(ctx: EventContext) -> RoleSpec:
    """コンテキストに応じた「自分自身」のRoleSpecを返す。

    AttackContext では attacker:self、それ以外では source:self を返す。
    """
    from jpoke.core.context import AttackContext
    if isinstance(ctx, AttackContext):
        return "attacker:self"
    return "source:self"


def self_heal(battle: Battle,
              ctx: EventContext,
              value: Any,
              v: int = 0,
              r: float = 0,
              chance: float = 1,
              reason: HPChangeReason = "") -> HandlerReturn:
    """自分のHPを固定値または割合で回復させる。"""
    # TODO : 共通関数化するほどの処理ではないため削除。
    spec = _self_role_spec(ctx)
    return modify_hp(
        battle, ctx, value, target_spec=spec, source_spec=spec,
        v=v, r=r, chance=chance, reason=reason
    )


def self_damage(battle: Battle,
                ctx: EventContext,
                value: Any,
                v: int = 0,
                r: float = 0,
                chance: float = 1,
                reason: HPChangeReason = "") -> HandlerReturn:
    """自分のHPを固定値または割合で減少させる。"""
    # TODO : 共通関数化するほどの処理ではないため削除。
    spec = _self_role_spec(ctx)
    return modify_hp(
        battle, ctx, value, target_spec=spec, source_spec=spec,
        v=-v, r=-r, chance=chance, reason=reason
    )


def drain_hp(battle: Battle,
             ctx: EventContext,
             value: Any,
             from_: RoleSpec,
             damage: int = 0,
             r: float = 0,
             heal_rate: float = 1,
             chance: float = 1,
             reason: HPChangeReason = "") -> HandlerReturn:
    # TODO : 必要ならBattle以下の管理クラスか個別のハンドラモジュールに実装
    """HPを奪い、奪った量に応じて回復させる。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント連鎖値（未使用）
        from_: HPを失う側のRoleSpec
        to_: 回復する側のRoleSpec。Noneなら from_ の相手
        v: 吸収する固定値
        r: 吸収する割合
        heal_rate: 回復倍率
        chance: 発動確率
        reason: 変更理由

    Returns:
        実際に吸収したHP量を value に持つ HandlerReturn
    """
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)

    from_mon = ctx.resolve_role(battle, from_)
    to_mon = battle.foe(from_mon)

    damage = battle.modify_hp(from_mon, -damage, -r, reason=reason)
    if damage:
        battle.modify_hp(to_mon, -damage * heal_rate, reason=reason)

    return HandlerReturn(value=damage)


def modify_stats(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 stats: dict[Stat, int],
                 target_spec: RoleSpec,
                 source_spec: RoleSpec | None = None,
                 chance: float = 1) -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """複数の能力ランクを同時に変化させる

    しろいハーブなどのアイテムが正しく動作するよう、
    複数の能力変化を一度に処理します。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        stats: 能力とランク変化量の辞書（例: {"B": -1, "D": -1}）
        target_spec: 対象のRoleSpec
        source_spec: 変化の原因となるポケモンのRoleSpec
        chance: 発動確率（デフォルト: 1）

    Returns:
        HandlerReturn: いずれかの能力が変化した場合True
    """
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)

    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)

    # battle.modify_stats()を使って一度に処理
    success = battle.modify_stats(target, stats, source=source)

    return HandlerReturn(value=success)


def apply_ailment(battle: Battle,
                  ctx: EventContext,
                  success: Any,
                  target_spec: RoleSpec,
                  ailment: AilmentName,
                  count: int | None = None,
                  source_spec: RoleSpec | None = None,
                  chance: float = 1) -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=success)

    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = battle.ailment_manager.apply(target, ailment, count=count, source=source, ctx=ctx)
    return HandlerReturn(value=success)


def apply_volatile(battle: Battle,
                   ctx: EventContext,
                   value: Any,
                   target_spec: RoleSpec,
                   volatile: VolatileName,
                   count: int | None = None,
                   source_spec: RoleSpec | None = None,
                   chance: float = 1,
                   **kwargs) -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """揮発状態を付与する。"""
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)

    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = battle.volatile_manager.apply(target, volatile, count=count, source=source, ctx=ctx, **kwargs)
    return HandlerReturn(value=success)


def cure_ailment(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 target_spec: RoleSpec,
                 source_spec: RoleSpec | None = None,
                 chance: float = 1) -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """状態異常を回復する。"""
    success = False
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)

    target = ctx.resolve_role(battle, target_spec)
    success = battle.ailment_manager.remove(target)
    return HandlerReturn(value=success)


def cure_self_ailment(battle: Battle, ctx: EventContext, value: Any, chance: float = 1) -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """自分の状態異常を回復する。"""
    spec = _self_role_spec(ctx)
    return cure_ailment(battle, ctx, value, target_spec=spec, source_spec=spec, chance=chance)


def activate_weather(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     weather: WeatherName,
                     count: int = 5,
                     source_spec: RoleSpec = "source:self") -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """天候を発動する。"""
    source = ctx.resolve_role(battle, source_spec)
    success = battle.weather_manager.apply(weather, count, source=source)
    return HandlerReturn(value=success)


def deactivate_weather(battle: Battle,
                       ctx: EventContext,
                       value: Any,
                       weather: WeatherName) -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """指定天候が現在有効な場合に解除する。"""
    if battle.raw_weather.name == weather:
        battle.weather_manager.remove()
    return HandlerReturn(value=value)


def activate_terrain(battle: Battle,
                     ctx: EventContext,
                     value: Any,
                     terrain: TerrainName,
                     count: int = 5,
                     source_spec: RoleSpec = "source:self") -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """地形を発動する。"""
    source = ctx.resolve_role(battle, source_spec)
    success = battle.terrain_manager.apply(terrain, count, source=source)
    return HandlerReturn(value=success)


def activate_global_field(battle: Battle,
                          ctx: EventContext,
                          value: Any,
                          source_spec: RoleSpec,
                          global_field: GlobalFieldName,
                          count: int = 5,
                          toggle: bool = False) -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """グローバルフィールドを発動・解除する。"""
    manager = battle.global_manager
    was_active = manager.fields[global_field].is_active

    if toggle and was_active:
        success = manager.deactivate(global_field)
    else:
        success = manager.activate(global_field, count)

    return HandlerReturn(value=success)


def deals_physical_damage(battle: Battle, ctx: AttackContext) -> bool:
    # TODO : Battle.queryの関数を直接呼び出す
    """技が物理ダメージを与えるかどうかを判定する。一部の特殊技も該当する。

    Returns:
        技が物理ダメージを与える場合True
    """
    return battle.query.deals_physical_damage(ctx.attacker, ctx.move)


def is_super_effective(battle: Battle, ctx: AttackContext) -> bool:
    # TODO : Battle.queryに実装を移す
    """効果抜群かどうかを判定する。"""
    type_modifier = battle.damage_calculator.calc_def_type_modifier(ctx)
    return type_modifier/4096 > 1


def is_not_very_effective(battle: Battle, ctx: AttackContext) -> bool:
    # TODO : Battle.queryに実装を移す
    """今ひとつかどうかを判定する。"""
    type_modifier = battle.damage_calculator.calc_def_type_modifier(ctx)
    return 0 < type_modifier/4096 < 1


def is_berry_item(item_name: str) -> bool:
    # TODO : Item.is_berry() を実装して移譲
    """アイテムがきのみかどうかを判定する。"""
    return item_name.endswith("のみ")


def block_stat_drop_by_foe(value: dict[Stat, int], ctx: EventContext, stat: Stat | None = None) -> dict[Stat, int]:
    # TODO : 個別のハンドラモジュールに実装
    """相手由来のランク低下を除去する共通処理。

    Args:
        value: ランク修正値の辞書 {stat: delta}
        ctx: コンテキスト（source/target を参照）
        stat: 対象 stat 名。None の場合は全 stat が対象（クリアボディ系）。
    """
    if ctx.source is not None and ctx.source != ctx.target:
        if stat is None:
            value = {s: v for s, v in value.items() if v >= 0}
        else:
            value = {s: v for s, v in value.items() if s != stat or v >= 0}
    return value


def ignore_damage_by_reason(battle: Battle, ctx: EventContext, value: int, *, reason: HPChangeReason) -> HandlerReturn:
    # TODO : 必要なら個別のハンドラモジュールに実装
    """指定された hp_change_reason のダメージを無効化する。

    Args:
        battle: バトルインスタンス（未使用、ハンドラ署名に合わせて受け取る）
        ctx: イベントコンテキスト
        value: HPダメージ量
        reason: 無効化対象の hp_change_reason

    Returns:
        reason が一致すれば value=0 かつ stop_event=True、それ以外は value をそのまま返す
    """
    if ctx.hp_change_reason == reason:
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)
