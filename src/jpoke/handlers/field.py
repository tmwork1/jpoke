from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.type_defs import GlobalField, SideField, VolatileName
from jpoke.core import BattleContext, HandlerReturn


# ===== カウントダウン =====

def tick_weather(battle: Battle, ctx: BattleContext, value: Any):
    # 1P側でのみカウントダウンを実行
    if battle.find_player(ctx.source) is battle.players[0]:
        battle.weather_manager.tick_down()
    return HandlerReturn()


def tick_terrain(battle: Battle, ctx: BattleContext, value: Any):
    # 1P側でのみカウントダウンを実行
    if battle.find_player(ctx.source) is battle.players[0]:
        battle.terrain_manager.tick_down()
    return HandlerReturn()


def tick_global_field(battle: Battle, ctx: BattleContext, value: Any, name: GlobalField) -> HandlerReturn:
    # 1P側でのみカウントダウンを実行
    if battle.find_player(ctx.source) is battle.players[0]:
        battle.field_manager.tick_down(name)
    return HandlerReturn()


def tick_side_field(battle: Battle, ctx: BattleContext, value: Any, name: SideField) -> HandlerReturn:
    player = battle.find_player(ctx.source)
    side = battle.get_side(player)
    side.tick_down(name)
    return HandlerReturn()


# ===== 天候ハンドラ =====


def はれ_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """晴れ状態での技威力補正"""
    move_type = ctx.move.type
    if move_type == "ほのお":
        return HandlerReturn(True, value * 6144 // 4096)  # 1.5倍
    elif move_type == "みず":
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def あめ_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """雨状態での技威力補正"""
    move_type = ctx.move.type
    if move_type == "みず":
        return HandlerReturn(True, value * 6144 // 4096)  # 1.5倍
    elif move_type == "ほのお":
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def すなあらし_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """砂嵐のダメージ"""
    tick_weather(battle, ctx, value)
    if battle.weather.count == 0:
        return HandlerReturn(False)
    success = ctx.source and \
        not any(ctx.source.has_type(t) for t in ["いわ", "じめん", "はがね"]) and \
        ctx.source.ability.name not in ["すなかき", "すながくれ", "すなのちから", "ぼうじん"] and \
        battle.modify_hp(ctx.source, r=-1/16)
    return HandlerReturn(success)


def すなあらし_spdef_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """砂嵐時のいわタイプ特防1.5倍"""
    if ctx.defender.has_type("いわ") and ctx.move.category == "特殊":
        value = value * 6144 // 4096  # 1.5倍
    return HandlerReturn(value=value)


def ゆき_def_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """雪時のこおりタイプ防御1.5倍"""
    if ctx.defender.has_type("こおり") and ctx.move.category == "物理":
        value = value * 6144 // 4096  # 1.5倍
    return HandlerReturn(value=value)

# ===== 地形ハンドラ =====


def エレキフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """エレキフィールドでの電気技威力1.3倍"""
    if ctx.move.type == "でんき" and not ctx.attacker.is_floating(battle):
        return HandlerReturn(True, value * 5325 // 4096)  # 1.3倍
    return HandlerReturn(False, value)


def エレキフィールド_prevent_sleep(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """エレキフィールドでねむり無効"""
    if value == "ねむり" and not ctx.target.is_floating(battle):
        return HandlerReturn(True, "", stop_event=True)
    return HandlerReturn(False, value)


# TODO: エレキフィールドでのねむけ(揮発状態)防止のハンドラ実装

def グラスフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """グラスフィールドでの草技威力1.3倍・地面技威力0.5倍"""
    # 草技威力1.3倍（攻撃側が接地している場合）
    if ctx.move.type == "くさ" and not ctx.attacker.is_floating(battle):
        return HandlerReturn(True, value * 5325 // 4096)  # 1.3倍
    # 地面範囲技威力0.5倍（じしん、じならし、マグニチュード）
    if ctx.move.name in ["じしん", "じならし", "マグニチュード"]:
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def グラスフィールド_heal(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """グラスフィールドのターン終了時回復"""
    success = ctx.source and \
        not ctx.source.is_floating(battle) and \
        battle.modify_hp(ctx.source, r=1/16)
    return HandlerReturn(success)


def サイコフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """サイコフィールドでのエスパー技威力1.3倍"""
    if ctx.move.type == "エスパー" and not ctx.attacker.is_floating(battle):
        return HandlerReturn(True, value * 5325 // 4096)  # 1.3倍
    return HandlerReturn(False, value)


def サイコフィールド_block_priority(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """サイコフィールドで先制技無効"""
    if ctx.move.priority > 0 and not ctx.defender.is_floating(battle):
        return HandlerReturn(True, False, stop_event=True)
    return HandlerReturn(False, value)


def ミストフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ミストフィールドでのドラゴン技威力0.5倍"""
    if ctx.move.type == "ドラゴン" and not ctx.defender.is_floating(battle):
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def ミストフィールド_prevent_ailment(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ミストフィールドで状態異常無効"""
    if not ctx.target.is_floating(battle):
        return HandlerReturn(True, "", stop_event=True)
    return HandlerReturn(False, value)


def ミストフィールド_prevent_volatile(battle: Battle, ctx: BattleContext, value: VolatileName) -> HandlerReturn:
    """ミストフィールドで混乱無効"""
    # valueは揮発状態名（VolatileName）
    if value == "こんらん" and not ctx.target.is_floating(battle):
        return HandlerReturn(True, "", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(False, value)  # 防がない


# ===== グローバルフィールドハンドラ =====

def じゅうりょく_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """重力時の命中率5/3倍"""
    return HandlerReturn(True, int(value * 5 / 3))


def じゅうりょく_grounded(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """重力時は全て地面に接地"""
    return HandlerReturn(True, False)


def トリックルーム_reverse_speed(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トリックルームで素早さ反転"""
    return HandlerReturn(value=-value)


# ===== サイドフィールドハンドラ =====

def リフレクター_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """リフレクターで物理技ダメージ軽減"""
    if ctx.move.category == "物理":
        # 0.5倍にするため、4096基準で 2048/4096
        return HandlerReturn(True, value * 2048 // 4096)
    return HandlerReturn(False, value)


def ひかりのかべ_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """光の壁で特殊技ダメージ軽減"""
    if ctx.move.category == "特殊":
        # 0.5倍にするため、4096基準で 2048/4096
        return HandlerReturn(True, value * 2048 // 4096)
    return HandlerReturn(False, value)


def オーロラベール_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """オーロラベールで物理・特殊技ダメージ軽減"""
    # オーロラベール フィールドがアクティブかチェック
    if not ctx.defender:
        return HandlerReturn(False, value)

    aurora_field = battle.get_side(ctx.defender).fields.get("オーロラベール")
    if not aurora_field or not aurora_field.is_active:
        return HandlerReturn(False, value)

    # ダメージを0.5倍に軽減（物理・特殊両対応）
    if ctx.move.category in ["物理", "特殊"]:
        return HandlerReturn(True, value * 2048 // 4096)

    return HandlerReturn(False, value)


def しんぴのまもり_prevent_ailment(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """神秘の守りで状態異常無効"""
    return HandlerReturn(True)


def しろいきり_prevent_stat_drop(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # TODO: 自分以外のポケモンによる能力低下だけ防ぐように修正
    """しろいきりで能力低下を防ぐ"""
    if not value:
        return HandlerReturn(False, value)

    filtered = {stat: v for stat, v in value.items() if v >= 0}
    if filtered == value:
        return HandlerReturn(False, value)

    return HandlerReturn(True, filtered)


def おいかぜ_speed_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """追い風で素早さ2倍"""
    return HandlerReturn(True, value * 2)


def ねがいごと_heal(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねがいごとのターン終了時HP回復"""
    side = battle.get_side(ctx.target)
    field = side.fields["ねがいごと"]
    side.tick_down("ねがいごと")
    if field.count == 0 and battle.modify_hp(ctx.target, v=field.heal):
        battle.add_event_log(ctx.target, "ねがいごとで回復")
        field.heal = 0
    return HandlerReturn()


def まきびし_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まきびしのダメージ"""
    if not ctx.source or ctx.source.is_floating(battle):
        return HandlerReturn(False)

    # 対象のサイドのまきびしフィールドを取得
    makibishi_field = battle.get_side(ctx.source).fields.get("まきびし")
    if not makibishi_field or makibishi_field.count == 0:
        return HandlerReturn(False)

    # 層数に応じたダメージ量を決定
    damage_ratio = {
        1: -1/8,
        2: -1/6,
    }.get(makibishi_field.count, -1/4)  # 3層以上は1/4

    success = battle.modify_hp(ctx.source, r=damage_ratio)
    return HandlerReturn(success)


def どくびし_poison(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """どくびしの毒付与"""
    if not ctx.source:
        return HandlerReturn(False)

    # 対象のサイドのどくびしフィールドを取得
    side = battle.get_side(ctx.source)
    dokubishi_field = side.fields.get("どくびし")
    if not dokubishi_field or dokubishi_field.count == 0:
        return HandlerReturn(False)

    # どくタイプは吸収して消滅
    if ctx.source.has_type("どく"):
        dokubishi_field.count = 0
        side.deactivate("どくびし")
        return HandlerReturn(True)

    if ctx.source.is_floating(battle):
        return HandlerReturn(False)

    # 層数に応じて「どく」または「もうどく」を付与
    ailment = "もうどく" if dokubishi_field.count >= 2 else "どく"
    success = ctx.source.apply_ailment(battle, ailment, source=ctx.source)
    return HandlerReturn(success)


def ステルスロック_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # TODO: common.calc_effectivenessを使うように修正
    """ステルスロックのダメージ（岩タイプ相性依存）"""
    from jpoke.utils.constants import TYPE_MODIFIER

    if not ctx.source:
        return HandlerReturn(False)

    effectiveness = 1.0

    # 岩タイプとの相性計算
    for poke_type in ctx.source.types:
        effectiveness *= TYPE_MODIFIER["いわ"][poke_type]

    # ダメージ倍率を決定
    damage_ratio = {
        4.0: -1/2,
        2.0: -1/4,
        1.0: -1/8,
        0.5: -1/16,
        0.25: -1/32,
    }.get(effectiveness, -1/8)

    success = battle.modify_hp(ctx.source, r=damage_ratio)
    return HandlerReturn(success)


def ねばねばネット_speed_drop(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねばねばネットの素早さダウン"""
    if not ctx.source or ctx.source.is_floating(battle):
        return HandlerReturn(False)

    # 対象のサイドのねばねばネットフィールドを取得
    nebanet_field = battle.get_side(ctx.source).fields.get("ねばねばネット")
    if not nebanet_field or nebanet_field.count == 0:
        return HandlerReturn(False)

    # 素早さランクを1段階下げる
    success = battle.modify_stat(ctx.source, "S", -1, source=ctx.source)
    return HandlerReturn(success)
