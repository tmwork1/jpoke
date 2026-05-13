from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.enums import LogCode
from jpoke.utils.battle_math import rank_modifier
from jpoke.utils.type_defs import RoleSpec, GlobalField, SideField, VolatileName, AbilityDisabledReason
from jpoke.utils.battle_math import rank_modifier, apply_fixed_modifier
from jpoke.core import HandlerReturn, Handler
from jpoke.handlers import common


class FieldHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100):
        super().__init__(
            func=func,
            source="field",
            subject_spec=subject_spec,
            priority=priority,
        )


# ===== カウントダウン =====

def tick_weather(battle: Battle, ctx: BattleContext, value: Any):
    # 1P側でのみカウントダウンを実行
    if battle.find_player(ctx.source) is battle.players[0]:
        battle.weather_manager.tick_down()
    return HandlerReturn(value=value)


def tick_terrain(battle: Battle, ctx: BattleContext, value: Any):
    # 1P側でのみカウントダウンを実行
    if battle.find_player(ctx.source) is battle.players[0]:
        battle.terrain_manager.tick_down()
    return HandlerReturn(value=value)


def tick_global_field(battle: Battle, ctx: BattleContext, value: Any, name: GlobalField) -> HandlerReturn:
    # 1P側でのみカウントダウンを実行
    if battle.find_player(ctx.source) is battle.players[0]:
        battle.field_manager.tick_down(name)
    return HandlerReturn(value=value)


def tick_side_field(battle: Battle, ctx: BattleContext, value: Any, name: SideField) -> HandlerReturn:
    player = battle.find_player(ctx.source)
    side = battle.get_side(player)
    side.tick_down(name)
    return HandlerReturn(value=value)


# ===== 天候ハンドラ =====


def はれ_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """晴れ状態での技威力補正"""
    move_type = ctx.move.type
    if move_type == "ほのお":
        value = apply_fixed_modifier(value, 6144)  # 1.5倍
    elif move_type == "みず":
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def はれ_prevent_freeze(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """晴れ状態でこおり無効"""
    if value == "こおり":
        value = ""
    return HandlerReturn(value=value)


def あめ_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """雨状態での技威力補正"""
    move_type = ctx.move.type
    if move_type == "みず":
        value = apply_fixed_modifier(value, 6144)  # 1.5倍
    elif move_type == "ほのお":
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def すなあらし_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """すなあらしのターン終了時ダメージ"""
    tick_weather(battle, ctx, value)
    if (
        battle.weather.name == "すなあらし"
        and not any(ctx.source.has_type(t) for t in ["いわ", "じめん", "はがね"])
    ):
        battle.modify_hp(ctx.source, r=-1/16, reason="sandstorm")
    return HandlerReturn(value=value)


def すなあらし_spdef_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """砂嵐時のいわタイプ特防1.5倍"""
    if (
        battle.weather.name == "すなあらし"
        and ctx.defender.has_type("いわ")
        and ctx.move.category == "特殊"
    ):
        value = apply_fixed_modifier(value, 6144)  # 1.5倍
    return HandlerReturn(value=value)


def ゆき_def_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """雪時のこおりタイプ防御1.5倍"""
    if (
        battle.weather.name == "ゆき"
        and ctx.defender.has_type("こおり")
        and ctx.move.category == "物理"
    ):
        value = apply_fixed_modifier(value, 6144)  # 1.5倍
    return HandlerReturn(value=value)


# ===== 強天候ハンドラ =====

_FLYING_WEAK_TYPES = frozenset({"でんき", "いわ", "こおり"})


def おおひでり_block_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """おおひでり中にみずタイプ技を失敗させる（攻撃技・変化技を問わない）"""
    if ctx.move.type == "みず":
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おおあめ_block_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """おおあめ中にほのおタイプ技を失敗させる（攻撃技・変化技を問わない）"""
    if ctx.move.type == "ほのお":
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def らんきりゅう_type_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """らんきりゅう中にひこうタイプの弱点（でんき/いわ/こおり）を0.5倍に軽減する"""
    if (
        battle.weather.name == "らんきりゅう"
        and ctx.defender.has_type("ひこう")
        and ctx.move.type in _FLYING_WEAK_TYPES
    ):
        value = apply_fixed_modifier(value, 2048)  # ×0.5
    return HandlerReturn(value=value)


# ===== 地形ハンドラ =====


def エレキフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """エレキフィールドでの電気技威力1.3倍"""
    if (
        ctx.move.type == "でんき" and
        not battle.query_manager.is_floating(ctx.attacker)
    ):
        value = apply_fixed_modifier(value, 5325)  # 1.3倍
    return HandlerReturn(value=value)


def エレキフィールド_prevent_sleep(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """エレキフィールドでねむり無効"""
    if (
        value == "ねむり"
        and not battle.query_manager.is_floating(ctx.target)
    ):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def エレキフィールド_prevent_nemuke(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """エレキフィールドでねむけ無効"""
    if (
        value == "ねむけ"
        and not battle.query_manager.is_floating(ctx.target)
    ):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def グラスフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """グラスフィールドでの草技威力1.3倍・地面技威力0.5倍"""
    # 草技威力1.3倍（攻撃側が接地している場合）
    if (
        ctx.move.type == "くさ"
        and not battle.query_manager.is_floating(ctx.attacker)
    ):
        value = apply_fixed_modifier(value, 5325)  # 1.3倍
    # 地面範囲技威力0.5倍（じしん、じならし、マグニチュード）
    if (
        ctx.move.name in ["じしん", "じならし", "マグニチュード"]
        and not battle.query_manager.is_floating(ctx.defender)
    ):
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def グラスフィールド_heal(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """グラスフィールドのターン終了時回復"""
    if not battle.query_manager.is_floating(ctx.source):
        battle.modify_hp(ctx.source, r=1/16)
    return HandlerReturn(value=value)


def サイコフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """サイコフィールドでのエスパー技威力1.3倍"""
    if (
        ctx.move.type == "エスパー"
        and not battle.query_manager.is_floating(ctx.attacker)
    ):
        value = apply_fixed_modifier(value, 5325)  # 1.3倍
    return HandlerReturn(value=value)


def サイコフィールド_block_priority(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """サイコフィールドで先制技無効"""
    if (
        ctx.move.priority > 0
        and not battle.query_manager.is_floating(ctx.defender)
    ):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def ミストフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ミストフィールドでのドラゴン技威力0.5倍"""
    if (
        ctx.move.type == "ドラゴン"
        and not battle.query_manager.is_floating(ctx.defender)
    ):
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def ミストフィールド_prevent_ailment(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ミストフィールドで状態異常無効"""
    if not battle.query_manager.is_floating(ctx.target):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def ミストフィールド_prevent_volatile(battle: Battle, ctx: BattleContext, value: VolatileName) -> HandlerReturn:
    """ミストフィールドで混乱無効"""
    if (
        value == "こんらん"
        and not battle.query_manager.is_floating(ctx.target)
    ):
        return HandlerReturn(value="", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(value=value)  # 防がない


# ===== グローバルフィールドハンドラ =====

def じゅうりょく_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """重力時の命中率5/3倍"""
    return HandlerReturn(value=apply_fixed_modifier(value, 6840))  # 5/3倍


def じゅうりょく_grounded(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """重力時は全て地面に接地"""
    return HandlerReturn(value=False, stop_event=True)


def トリックルーム_reverse_speed(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トリックルームで素早さ反転"""
    return HandlerReturn(value=-value)


def マジックルーム_check_item_enabled(battle: Battle, ctx: BattleContext, value: set[AbilityDisabledReason]) -> HandlerReturn:
    """マジックルーム中は持ち物効果を無効化する。"""
    value.add("マジックルーム")
    return HandlerReturn(value=value)


def マジックルーム_on_field_deactivate(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マジックルーム解除時に持ち物有効状態を再計算する。"""
    battle.refresh_effect_enabled_states()
    return HandlerReturn(value=value)


def ワンダールーム_def_rank_modifier(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """ワンダールーム中は物理/特殊で参照する防御ランクを入れ替える。"""
    category_to_stat = {"物理": "D", "特殊": "B"}
    move_category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    swapped_stat = category_to_stat.get(move_category)
    rank = ctx.defender.rank[swapped_stat]
    value = rank_modifier(rank)
    return HandlerReturn(value=value)


def ワンダールーム_def_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ワンダールーム中は防御実数値参照を入れ替える。"""
    catergory_to_stat = {"物理": "D", "特殊": "B"}
    move_category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    base_stat = "B" if move_category == "物理" or ctx.move.has_label("physical") else "D"
    swapped_stat = catergory_to_stat.get(base_stat, base_stat)
    base_value = max(1, ctx.defender.stats[base_stat])
    swap_value = max(1, ctx.defender.stats[swapped_stat])
    return HandlerReturn(value=value * swap_value // base_value)


# ===== サイドフィールドハンドラ =====

def リフレクター_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """リフレクターで物理技ダメージ軽減"""
    if (
        not ctx.critical
        and not ctx.check_bypass_screen(battle)
        and ctx.move.category == "物理"
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def ひかりのかべ_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """光の壁で特殊技ダメージ軽減"""
    if (
        not ctx.critical
        and not ctx.check_bypass_screen(battle)
        and ctx.move.category == "特殊"
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def オーロラベール_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """オーロラベールで物理・特殊技ダメージ軽減"""
    if (
        not ctx.critical
        and not ctx.check_bypass_screen(battle)
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def しんぴのまもり_prevent_ailment(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しんぴのまもりで状態異常無効"""
    if not ctx.check_bypass_screen(battle):
        value = ""  # 状態異常名を空にして無効化
    return HandlerReturn(value=value)


def しんぴのまもり_prevent_volatile(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しんぴのまもりで揮発状態無効"""
    if (
        not ctx.check_bypass_screen(battle)
        and value in ["こんらん", "ねむけ"]
    ):
        value = ""  # 揮発状態名を空にして無効化
    return HandlerReturn(value=value)


def しろいきり_prevent_stat_drop(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しろいきりで能力低下を防ぐ"""
    if (
        ctx.is_foe_target
        and not ctx.check_bypass_screen(battle)
    ):
        value = {stat: v for stat, v in value.items() if v > 0}
    return HandlerReturn(value=value)


def おいかぜ_speed_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """追い風で素早さ2倍"""
    return HandlerReturn(value=value * 2)


def ねがいごと_heal(battle: Battle, ctx: BattleContext, value: Field) -> HandlerReturn:
    """ねがいごとのターン終了時HP回復"""
    battle.modify_hp(ctx.source, v=value.heal)
    return HandlerReturn(value=value)


def まきびし_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まきびしのダメージ"""
    if battle.query_manager.is_floating(ctx.source):
        return HandlerReturn(value=value)

    # 対象のサイドのまきびしフィールドを取得
    field = battle.get_side(ctx.source).get("まきびし")

    # 層数に応じたダメージ量を決定
    damage_ratio = {
        1: -1/8,
        2: -1/6,
    }.get(field.count, -1/4)  # 3層以上は1/4

    success = battle.modify_hp(ctx.source, r=damage_ratio)
    return HandlerReturn(value=success)


def どくびし_poison(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """どくびしの毒付与"""
    # 対象のサイドのどくびしフィールドを取得
    side = battle.get_side(ctx.source)
    field = side.get("どくびし")

    # 浮いているポケモンは影響を受けない
    if battle.query_manager.is_floating(ctx.source):
        return HandlerReturn(value=value)

    # どくタイプは吸収して消滅
    if ctx.source.has_type("どく"):
        side.deactivate("どくびし")
        return HandlerReturn(value=value)

    # 層数に応じて「どく」または「もうどく」を付与
    ailment = "もうどく" if field.count >= 2 else "どく"
    battle.ailment_manager.apply(ctx.source, ailment, source=ctx.source)
    return HandlerReturn(value=value)


def ステルスロック_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ステルスロックのダメージ（岩タイプ相性依存）"""
    ctx = BattleContext(defender=ctx.source)
    def_type_modifier = common.calc_def_type_modifier(battle, ctx.source, "ステルスロック")
    battle.modify_hp(ctx.source, r=-1/8*def_type_modifier)
    return HandlerReturn(value=value)


def ねばねばネット_speed_drop(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねばねばネットの素早さダウン"""
    # 浮いているポケモンは影響を受けない
    if battle.query_manager.is_floating(ctx.source):
        return HandlerReturn(value=value)

    # 素早さランクを1段階下げる (相手由来と判定される)
    battle.modify_stat(ctx.source, "S", -1, source=battle.foe(ctx.source))
    return HandlerReturn(value=value)
