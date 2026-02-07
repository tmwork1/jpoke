from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.core.event import EventContext, HandlerReturn


# ===== 天候ハンドラ =====

def はれ_power_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """晴れ状態での技威力補正"""
    move_type = ctx.move.type
    if move_type == "ほのお":
        return HandlerReturn(True, value * 6144 // 4096)  # 1.5倍
    elif move_type == "みず":
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def あめ_power_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """雨状態での技威力補正"""
    move_type = ctx.move.type
    if move_type == "みず":
        return HandlerReturn(True, value * 6144 // 4096)  # 1.5倍
    elif move_type == "ほのお":
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def すなあらし_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # ON_TURN_END ハンドラ
    success = ctx.target and \
        not any(ctx.target.has_type(t) for t in ["いわ", "じめん", "はがね"]) and \
        ctx.target.ability.name not in ["すなかき", "すながくれ", "すなのちから", "ぼうじん"] and \
        battle.modify_hp(ctx.target, r=-1/16)
    return HandlerReturn(success)


def すなあらし_spdef_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """砂嵐時のいわタイプ特防1.5倍"""
    if ctx.target.has_type("いわ"):
        return HandlerReturn(True, value * 6144 // 4096)  # 1.5倍
    return HandlerReturn(False, value)


def ゆき_def_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """雪時のこおりタイプ防御1.5倍"""
    if ctx.target.has_type("こおり"):
        return HandlerReturn(True, value * 6144 // 4096)  # 1.5倍
    return HandlerReturn(False, value)


# ===== 地形ハンドラ =====

def エレキフィールド_power_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """エレキフィールドでの電気技威力1.3倍"""
    if ctx.move.type == "でんき" and not ctx.attacker.is_floating(battle.events):
        return HandlerReturn(True, value * 5324 // 4096)  # 1.3倍
    return HandlerReturn(False, value)


def エレキフィールド_prevent_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """エレキフィールドでねむり無効"""
    if value == "ねむり" and not ctx.target.is_floating(battle.events):
        return HandlerReturn(True, "", stop_event=True)
    return HandlerReturn(False, value)


def エレキフィールド_cure_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """エレキフィールド上に出た時のねむり回復"""
    mon = ctx.source
    if mon.ailment.name == "ねむり" and not mon.is_floating(battle.events):
        success = mon.cure_ailment(battle.events)
        return HandlerReturn(success)
    return HandlerReturn(False)


def グラスフィールド_power_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """グラスフィールドでの草技威力1.3倍・地面技威力0.5倍"""
    # 草技威力1.3倍（攻撃側が接地している場合）
    if ctx.move.type == "くさ" and not ctx.attacker.is_floating(battle.events):
        return HandlerReturn(True, value * 5324 // 4096)  # 1.3倍
    # 地面範囲技威力0.5倍（じしん、じならし、マグニチュード）
    if ctx.move.name in ["じしん", "じならし", "マグニチュード"]:
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def グラスフィールド_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """グラスフィールドのターン終了時回復"""
    success = ctx.target and \
        not ctx.target.is_floating(battle.events) and \
        battle.modify_hp(ctx.target, r=1/16)
    return HandlerReturn(success)


def サイコフィールド_power_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """サイコフィールドでのエスパー技威力1.3倍"""
    if ctx.move.type == "エスパー" and not ctx.attacker.is_floating(battle.events):
        return HandlerReturn(True, value * 5324 // 4096)  # 1.3倍
    return HandlerReturn(False, value)


def サイコフィールド_block_priority(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """サイコフィールドで先制技無効"""
    if ctx.move.priority > 0 and not ctx.defender.is_floating(battle.events):
        return HandlerReturn(True, False)
    return HandlerReturn(False, value)


def ミストフィールド_power_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ミストフィールドでのドラゴン技威力0.5倍"""
    if ctx.move.type == "ドラゴン" and not ctx.defender.is_floating(battle.events):
        return HandlerReturn(True, value * 2048 // 4096)  # 0.5倍
    return HandlerReturn(False, value)


def ミストフィールド_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ミストフィールドで状態異常無効"""
    if not ctx.target.is_floating(battle.events):
        return HandlerReturn(True, "", stop_event=True)
    return HandlerReturn(False, value)


def ミストフィールド_prevent_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ミストフィールドで混乱無効"""
    # valueは揮発状態名（VolatileName）
    if value == "こんらん" and not ctx.target.is_floating(battle.events):
        return HandlerReturn(True, "", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(False, value)  # 防がない


# ===== グローバルフィールドハンドラ =====

def じゅうりょく_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """重力時の命中率5/3倍"""
    return HandlerReturn(True, int(value * 5 / 3))


def じゅうりょく_grounded(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """重力時は全て地面に接地"""
    return HandlerReturn(True, False)


def トリックルーム_reverse_speed(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """トリックルームで素早さ反転"""
    return HandlerReturn(True, -value)


# ===== サイドフィールドハンドラ =====

def リフレクター_reduce_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リフレクターで物理技ダメージ軽減"""
    if ctx.move.category == "物理":
        # 0.5倍にするため、4096基準で 2048/4096
        return HandlerReturn(True, value * 2048 // 4096)
    return HandlerReturn(False, value)


def ひかりのかべ_reduce_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """光の壁で特殊技ダメージ軽減"""
    if ctx.move.category == "特殊":
        # 0.5倍にするため、4096基準で 2048/4096
        return HandlerReturn(True, value * 2048 // 4096)
    return HandlerReturn(False, value)


def しんぴのまもり_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """神秘の守りで状態異常無効"""
    return HandlerReturn(True)


def しろいきり_prevent_stat_drop(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しろいきりで能力低下を防ぐ"""
    if not value:
        return HandlerReturn(False, value)

    filtered = {stat: v for stat, v in value.items() if v >= 0}
    if filtered == value:
        return HandlerReturn(False, value)

    return HandlerReturn(True, filtered)


def おいかぜ_speed_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """追い風で素早さ2倍"""
    return HandlerReturn(True, value * 2)


def まきびし_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まきびしのダメージ"""
    if not ctx.source or ctx.source.is_floating(battle.events):
        return HandlerReturn(False)

    # 対象のサイドのまきびしフィールドを取得
    makibishi_field = battle.get_side(ctx.source).fields.get("まきびし")
    if not makibishi_field or makibishi_field.layers == 0:
        return HandlerReturn(False)

    # 層数に応じたダメージ量を決定
    damage_ratio = {
        1: -1/8,
        2: -1/6,
    }.get(makibishi_field.layers, -1/4)  # 3層以上は1/4

    success = battle.modify_hp(ctx.source, r=damage_ratio)
    return HandlerReturn(success)


def どくびし_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくびしの毒付与"""
    if not ctx.source:
        return HandlerReturn(False)

    # 対象のサイドのどくびしフィールドを取得
    dokubishi_field = battle.get_side(ctx.source).fields.get("どくびし")
    if not dokubishi_field or dokubishi_field.layers == 0:
        return HandlerReturn(False)

    # どくタイプは吸収して消滅
    if ctx.source.has_type("どく"):
        dokubishi_field.layers = 0
        dokubishi_field.deactivate(battle.events)
        return HandlerReturn(True)

    if ctx.source.is_floating(battle.events):
        return HandlerReturn(False)

    # 層数に応じて「どく」または「もうどく」を付与
    ailment = "もうどく" if dokubishi_field.layers >= 2 else "どく"
    success = ctx.source.apply_ailment(battle.events, ailment, source=ctx.source)
    return HandlerReturn(success)


def ステルスロック_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def ねばねばネット_speed_drop(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねばねばネットの素早さダウン"""
    if not ctx.source or ctx.source.is_floating(battle.events):
        return HandlerReturn(False)

    # 対象のサイドのねばねばネットフィールドを取得
    nebanet_field = battle.get_side(ctx.source).fields.get("ねばねばネット")
    if not nebanet_field or nebanet_field.layers == 0:
        return HandlerReturn(False)

    # 素早さランクを1段階下げる
    success = battle.modify_stat(ctx.source, "S", -1, source=ctx.source)
    return HandlerReturn(success)


def ねがいごと_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねがいごとのターン終了時HP回復"""
    if not ctx.target:
        return HandlerReturn(False)

    # 対象のサイドのねがいごとフィールドを取得
    negai_field = battle.get_side(ctx.target).fields.get("ねがいごと")
    if not negai_field or not negai_field.is_active:
        return HandlerReturn(False)

    # HP を1/2回復
    success = battle.modify_hp(ctx.target, r=1/2)

    # 回復結果に関わらず解除（1回限りの効果）
    negai_field.deactivate(battle.events)

    return HandlerReturn(success)


def オーロラベール_reduce_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
