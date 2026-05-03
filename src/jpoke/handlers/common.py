"""複数の効果実装で使い回す共通ハンドラ群。"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec, Stat, AilmentName, VolatileName, Terrain, GlobalField
from jpoke.enums import Event
from jpoke.core import HandlerReturn


def _calc_effective_chance(battle: Battle, ctx: BattleContext, chance: float) -> float:
    """追加効果補正後の実効確率を返す。"""
    effective = battle.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, chance)
    return min(1.0, max(0.0, effective))


def modify_hp(battle: Battle,
              ctx: BattleContext,
              value: Any,
              target_spec: RoleSpec,
              v: int = 0,
              r: float = 0,
              chance: float = 1,
              reason: str = "") -> HandlerReturn:
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
    effective_chance = _calc_effective_chance(battle, ctx, chance)
    if effective_chance < 1 and battle.random.random() >= effective_chance:
        return HandlerReturn()
    target = ctx.resolve_role(battle, target_spec)
    v = battle.modify_hp(target, v, r, reason=reason)
    return HandlerReturn(value=v)


def drain_hp(battle: Battle,
             ctx: BattleContext,
             value: Any,
             from_: RoleSpec,
             to_: RoleSpec | None = None,
             v: int = 0,
             r: float = 0,
             heal_rate: float = 1,
             chance: float = 1,
             reason: str = "") -> HandlerReturn:
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
    effective_chance = _calc_effective_chance(battle, ctx, chance)
    if effective_chance < 1 and battle.random.random() >= effective_chance:
        return HandlerReturn()

    # from_とto_から対象のポケモンを解決
    from_mon = ctx.resolve_role(battle, from_)
    if to_ is None:
        to_mon = battle.foe(from_mon)
    else:
        to_mon = ctx.resolve_role(battle, to_)

    v = battle.modify_hp(from_mon, -v, -r, reason=reason)
    if v:
        battle.modify_hp(to_mon, -v * heal_rate, reason=reason)

    return HandlerReturn(value=v)


def modify_stat(battle: Battle,
                ctx: BattleContext,
                value: Any,
                stat: Stat,
                v: int,
                target_spec: RoleSpec,
                source_spec: RoleSpec | None = None,
                chance: float = 1) -> HandlerReturn:
    """能力ランクを1種類だけ変更する。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント連鎖値（未使用）
        stat: 変更する能力
        v: ランク変化量
        target_spec: 変更対象のRoleSpec
        source_spec: 変化の原因となるRoleSpec
        chance: 発動確率

    Returns:
        変化が成功したかを value に持つ HandlerReturn
    """
    effective_chance = _calc_effective_chance(battle, ctx, chance)
    if effective_chance < 1 and battle.random.random() >= effective_chance:
        return HandlerReturn()
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = battle.modify_stat(target, stat, v, source=source)
    return HandlerReturn(value=success)


def modify_stats(battle: Battle,
                 ctx: BattleContext,
                 value: Any,
                 stats: dict[Stat, int],
                 target_spec: RoleSpec,
                 source_spec: RoleSpec | None = None,
                 chance: float = 1) -> HandlerReturn:
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
    effective_chance = _calc_effective_chance(battle, ctx, chance)
    if effective_chance < 1 and battle.random.random() >= effective_chance:
        return HandlerReturn()

    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)

    # battle.modify_stats()を使って一度に処理
    success = battle.modify_stats(target, stats, source=source)

    return HandlerReturn(value=success)


def apply_ailment(battle: Battle,
                  ctx: BattleContext,
                  value: Any,
                  ailment: AilmentName,
                  target_spec: RoleSpec,
                  source_spec: RoleSpec | None = None,
                  chance: float = 1,
                  reason: str = "") -> HandlerReturn:
    """状態異常を付与する。"""
    effective_chance = _calc_effective_chance(battle, ctx, chance)
    if effective_chance < 1 and battle.random.random() >= effective_chance:
        return HandlerReturn()
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = battle.ailment_manager.apply(target, ailment, source=source, origin_ctx=ctx)
    return HandlerReturn(value=success)


def apply_volatile(battle: Battle,
                   ctx: BattleContext,
                   value: Any,
                   volatile: VolatileName,
                   target_spec: RoleSpec,
                   source_spec: RoleSpec | None = None,
                   count: int | None = None,
                   chance: float = 1) -> HandlerReturn:
    """揮発状態を付与する。"""
    effective_chance = _calc_effective_chance(battle, ctx, chance)
    if effective_chance < 1 and battle.random.random() >= effective_chance:
        return HandlerReturn()
    if count is None:
        match volatile:
            case "こんらん":
                count = battle.random.randint(1, 4)
            case _:
                count = 1
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = battle.volatile_manager.apply(target, volatile, count=count, source=source, origin_ctx=ctx)
    return HandlerReturn(value=success)


def cure_ailment(battle: Battle,
                 ctx: BattleContext,
                 value: Any,
                 target_spec: RoleSpec,
                 source_spec: RoleSpec | None = None,
                 chance: float = 1) -> HandlerReturn:
    """状態異常を回復する。"""
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn()
    target = ctx.resolve_role(battle, target_spec)
    source = ctx.resolve_role(battle, source_spec)
    success = battle.ailment_manager.remove(target, source=source)
    return HandlerReturn(value=success)


def activate_weather(battle: Battle,
                     ctx: BattleContext,
                     value: Any,
                     source_spec: RoleSpec,
                     weather: Weather,
                     count: int = 5) -> HandlerReturn:
    """天候を発動する。"""
    source = ctx.resolve_role(battle, source_spec)
    success = battle.weather_manager.activate(weather, count, source=source)
    return HandlerReturn(value=success)


def deactivate_weather(battle: Battle,
                       ctx: BattleContext,
                       value: Any,
                       weather: Weather) -> HandlerReturn:
    """指定天候が現在有効な場合に解除する。"""
    if battle.raw_weather.name == weather:
        battle.weather_manager.deactivate()
    return HandlerReturn(value=value)


def activate_terrain(battle: Battle,
                     ctx: BattleContext,
                     value: Any,
                     source_spec: RoleSpec,
                     terrain: Terrain,
                     count: int = 5) -> HandlerReturn:
    """地形を発動する。"""
    source = ctx.resolve_role(battle, source_spec)
    success = battle.terrain_manager.activate(terrain, count, source=source)
    return HandlerReturn(value=success)


def activate_global_field(battle: Battle,
                          ctx: BattleContext,
                          value: Any,
                          source_spec: RoleSpec,
                          global_field: GlobalField,
                          count: int = 5,
                          toggle: bool = False) -> HandlerReturn:
    """グローバルフィールドを発動・解除する。"""
    manager = battle.field_manager
    was_active = manager.fields[global_field].is_active

    if toggle and was_active:
        success = manager.deactivate(global_field)
    else:
        success = manager.activate(global_field, count)

    if success and global_field == "マジックルーム" and not was_active:
        battle.refresh_item_enabled_states()

    return HandlerReturn(value=success)


def resolve_field_count(battle: Battle,
                        ctx: BattleContext,
                        value: Any,
                        field: Weather | Terrain,
                        additonal_count: int) -> HandlerReturn:
    """指定場状態と一致するとき継続ターン数に加算する。"""
    if ctx.field.orig_name == field:
        return HandlerReturn(value=value + additonal_count)
    else:
        return HandlerReturn(value=value)


def is_special_move(battle: Battle, ctx: BattleContext) -> bool:
    """特殊技かどうかを判定する。

    特殊技カテゴリ且つphysicalラベルなし。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト

    Returns:
        bool: 特殊技ならTrue
    """
    if ctx.move is None:
        return False
    category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    return category == "特殊" and not ctx.move.has_label("physical")


def is_physical_move(battle: Battle, ctx: BattleContext) -> bool:
    """物理技かどうかを判定する。

    物理技カテゴリまたはphysicalラベル持ち。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト

    Returns:
        bool: 物理技ならTrue
    """
    if ctx.move is None:
        return False
    category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    return category == "物理" or ctx.move.has_label("physical")


def is_super_effective(battle: Battle, ctx: BattleContext) -> bool:
    """効果抜群かどうかを判定する。

    タイプ相性補正が1より大きいかどうか。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト

    Returns:
        bool: 効果抜群ならTrue
    """
    if ctx.move is None:
        return False
    return battle.damage_calculator.calc_def_type_modifier(ctx) > 1


def is_not_very_effective(battle: Battle, ctx: BattleContext) -> bool:
    """今ひとつかどうかを判定する。

    タイプ相性補正が0より大きく1より小さいかどうか。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト

    Returns:
        bool: 今ひとつならTrue
    """
    if ctx.move is None:
        return False
    type_modifier = battle.damage_calculator.calc_def_type_modifier(ctx)
    return 0 < type_modifier < 1


def is_berry_item(item_name: str) -> bool:
    """アイテムがきのみかどうかを判定する。

    Args:
        item_name: アイテム名

    Returns:
        bool: きのみなら True
    """
    return item_name.endswith("のみ")


def apply_modifier(value: int, modifier: int) -> int:
    """4096基準の補正値を適用する。

    ポケモンの倍率計算は4096を基準とした固定小数点で実装されているため、
    この関数でまとめて補正を計算する。

    例：
        - 倍率 1.5倍 = 6144 (4096 * 1.5)
        - 倍率 0.5倍 = 2048 (4096 * 0.5)

    Args:
        value: 元の値
        modifier: 4096基準の補正値

    Returns:
        int: 補正後の値
    """
    return value * modifier // 4096


def block_stat_drop(value: dict, ctx: BattleContext, stat: str | None = None) -> dict:
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


def crossed_half_hp(hp_before: int, hp_after: int, max_hp: int) -> bool:
    """HPが最大HPの50%を跨いだかどうかを判定する。

    HPが 50% 超から 50% 以下へ移行したかを判定する。
    特性やアイテムの効果発動判定に使用。

    Args:
        hp_before: ダメージ前のHP
        hp_after: ダメージ後のHP
        max_hp: 最大HP

    Returns:
        bool: 50%を跨いだら True
    """
    return hp_before * 2 > max_hp and hp_after * 2 <= max_hp
