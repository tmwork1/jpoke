from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.enums import LogCode
from jpoke.utils.type_defs import GlobalField, SideField, VolatileName
from jpoke.core import HandlerReturn
from jpoke.handlers import common


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
    active = battle.weather
    if active is None or active.name not in ["はれ", "おおひでり"]:
        return HandlerReturn(value=value)
    move_type = ctx.move.type
    if move_type == "ほのお":
        value = value * 6144 // 4096  # 1.5倍
    elif move_type == "みず":
        value = value * 2048 // 4096  # 0.5倍
    return HandlerReturn(value=value)


def はれ_prevent_freeze(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """晴れ状態でこおり無効"""
    active = battle.weather
    if active is None or active.name not in ["はれ", "おおひでり"]:
        return HandlerReturn(value=value)
    if value == "こおり":
        return HandlerReturn(value="")
    return HandlerReturn(value=value)


def あめ_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """雨状態での技威力補正"""
    active = battle.weather
    if active is None or active.name not in ["あめ", "おおあめ"]:
        return HandlerReturn(value=value)
    move_type = ctx.move.type
    if move_type == "みず":
        value = value * 6144 // 4096  # 1.5倍
    elif move_type == "ほのお":
        value = value * 2048 // 4096  # 0.5倍
    return HandlerReturn(value=value)


def すなあらし_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """砂嵐のダメージ"""
    tick_weather(battle, ctx, value)
    active = battle.weather
    if active is not None and active.name == "すなあらし" and \
            not any(ctx.source.has_type(t) for t in ["いわ", "じめん", "はがね"]):
        battle.modify_hp(ctx.source, r=-1/16, reason="sandstorm_damage")
    return HandlerReturn()


def すなあらし_spdef_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """砂嵐時のいわタイプ特防1.5倍"""
    active = battle.weather
    if active is not None and active.name == "すなあらし" and ctx.defender.has_type("いわ") and ctx.move.category == "特殊":
        value = value * 6144 // 4096  # 1.5倍
    return HandlerReturn(value=value)


def ゆき_def_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """雪時のこおりタイプ防御1.5倍"""
    active = battle.weather
    if active is not None and active.name == "ゆき" and ctx.defender.has_type("こおり") and ctx.move.category == "物理":
        value = value * 6144 // 4096  # 1.5倍
    return HandlerReturn(value=value)


# ===== 強天候ハンドラ =====

_FLYING_WEAK_TYPES = frozenset({"でんき", "いわ", "こおり"})


def おおひでり_block_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """おおひでり中にみずタイプ技を失敗させる（攻撃技・変化技を問わない）(ON_CHECK_MOVE priority 10)"""
    active = battle.weather
    if active is not None and active.name == "おおひでり" and ctx.move.type == "みず":
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おおあめ_block_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """おおあめ中にほのおタイプ技を失敗させる（攻撃技・変化技を問わない）(ON_CHECK_MOVE priority 10)"""
    active = battle.weather
    if active is not None and active.name == "おおあめ" and ctx.move.type == "ほのお":
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def らんきりゅう_type_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """らんきりゅう中にひこうタイプの弱点（でんき/いわ/こおり）を0.5倍に軽減する
    (ON_CALC_DEF_TYPE_MODIFIER)"""
    active = battle.weather
    if active is not None and active.name == "らんきりゅう" and ctx.defender.has_type("ひこう") and ctx.move.type in _FLYING_WEAK_TYPES:
        value = int(value * 2048 // 4096)  # ×0.5
    return HandlerReturn(value=value)


# ===== 地形ハンドラ =====


def エレキフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """エレキフィールドでの電気技威力1.3倍"""
    if ctx.move.type == "でんき" and not battle.query_manager.is_floating(ctx.attacker):
        value = value * 5325 // 4096  # 1.3倍
    return HandlerReturn(value=value)


def エレキフィールド_prevent_sleep(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """エレキフィールドでねむり無効"""
    if value == "ねむり" and not battle.query_manager.is_floating(ctx.target):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def エレキフィールド_prevent_nemuke(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """エレキフィールドでねむけ無効"""
    if value == "ねむけ" and not battle.query_manager.is_floating(ctx.target):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def グラスフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """グラスフィールドでの草技威力1.3倍・地面技威力0.5倍"""
    # 草技威力1.3倍（攻撃側が接地している場合）
    if ctx.move.type == "くさ" and not battle.query_manager.is_floating(ctx.attacker):
        value = value * 5325 // 4096  # 1.3倍
    # 地面範囲技威力0.5倍（じしん、じならし、マグニチュード）
    if ctx.move.name in ["じしん", "じならし", "マグニチュード"]:
        value = value * 2048 // 4096  # 0.5倍
    return HandlerReturn(value=value)


def グラスフィールド_heal(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """グラスフィールドのターン終了時回復"""
    if not battle.query_manager.is_floating(ctx.source):
        battle.modify_hp(ctx.source, r=1/16)
    return HandlerReturn()


def サイコフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """サイコフィールドでのエスパー技威力1.3倍"""
    if ctx.move.type == "エスパー" and not battle.query_manager.is_floating(ctx.attacker):
        value = value * 5325 // 4096  # 1.3倍
    return HandlerReturn(value=value)


def サイコフィールド_block_priority(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """サイコフィールドで先制技無効"""
    if ctx.move.priority > 0 and not battle.query_manager.is_floating(ctx.defender):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def ミストフィールド_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ミストフィールドでのドラゴン技威力0.5倍"""
    if ctx.move.type == "ドラゴン" and not battle.query_manager.is_floating(ctx.defender):
        value = value * 2048 // 4096  # 0.5倍
    return HandlerReturn(value=value)


def ミストフィールド_prevent_ailment(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ミストフィールドで状態異常無効"""
    if not battle.query_manager.is_floating(ctx.target):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def ミストフィールド_prevent_volatile(battle: Battle, ctx: BattleContext, value: VolatileName) -> HandlerReturn:
    """ミストフィールドで混乱無効"""
    if value == "こんらん" and not battle.query_manager.is_floating(ctx.target):
        return HandlerReturn(value="", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(value=value)  # 防がない


# ===== グローバルフィールドハンドラ =====

def じゅうりょく_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """重力時の命中率5/3倍"""
    return HandlerReturn(value=int(value * 5 / 3))


def じゅうりょく_grounded(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """重力時は全て地面に接地"""
    return HandlerReturn(value=False)


def トリックルーム_reverse_speed(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トリックルームで素早さ反転"""
    return HandlerReturn(value=-value)


def マジックルーム_check_item_enabled(battle: Battle, ctx: BattleContext, should_enable: bool) -> HandlerReturn:
    """マジックルーム中は持ち物効果を無効化する。"""
    field = battle.get_global_field("マジックルーム")
    if field.is_active:
        return HandlerReturn(value=False)
    return HandlerReturn(value=should_enable)


def マジックルーム_on_field_deactivate(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マジックルーム解除時に持ち物有効状態を再計算する。"""
    if value and value.orig_name == "マジックルーム":
        battle.refresh_item_enabled_states()
    return HandlerReturn()


def _rank_modifier(rank: int) -> float:
    return (2 + rank) / 2 if rank >= 0 else 2 / (2 - rank)


def ワンダールーム_def_rank_modifier(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """ワンダールーム中は物理/特殊で参照する防御ランクを入れ替える。"""
    if not ctx.defender or not ctx.move:
        return HandlerReturn(value=value)
    if ctx.move.has_label("ignore_rank"):
        return HandlerReturn(value=value)

    move_category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    swap_to_stat = "D" if move_category == "物理" or ctx.move.has_label("physical") else "B"
    return HandlerReturn(value=_rank_modifier(ctx.defender.rank[swap_to_stat]))


def ワンダールーム_def_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ワンダールーム中は防御実数値参照を入れ替える。"""
    if not ctx.defender or not ctx.move:
        return HandlerReturn(value=value)

    move_category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    base_stat = "B" if move_category == "物理" or ctx.move.has_label("physical") else "D"
    swap_to_stat = "D" if base_stat == "B" else "B"

    base_value = max(1, ctx.defender.stats[base_stat])
    swap_value = max(1, ctx.defender.stats[swap_to_stat])
    return HandlerReturn(value=value * swap_value // base_value)


# ===== サイドフィールドハンドラ =====

def リフレクター_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """リフレクターで物理技ダメージ軽減"""
    if getattr(ctx, "critical", False):
        return HandlerReturn(value=value)
    if ctx.move.category == "物理":
        # 0.5倍にするため、4096基準で 2048/4096
        return HandlerReturn(value=value * 2048 // 4096)
    return HandlerReturn(value=value)


def ひかりのかべ_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """光の壁で特殊技ダメージ軽減"""
    if getattr(ctx, "critical", False):
        return HandlerReturn(value=value)
    if ctx.move.category == "特殊":
        # 0.5倍にするため、4096基準で 2048/4096
        value = value * 2048 // 4096
    return HandlerReturn(value=value)


def オーロラベール_reduce_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """オーロラベールで物理・特殊技ダメージ軽減"""
    # オーロラベール フィールドがアクティブかチェック
    if not ctx.defender:
        return HandlerReturn(value=value)

    aurora_field = battle.get_side(ctx.defender).fields.get("オーロラベール")
    if not aurora_field or not aurora_field.is_active:
        return HandlerReturn(value=value)

    if getattr(ctx, "critical", False):
        return HandlerReturn(value=value)

    # ダメージを0.5倍に軽減（物理・特殊両対応）
    if ctx.move.category in ["物理", "特殊"]:
        return HandlerReturn(value=value * 2048 // 4096)

    return HandlerReturn(value=value)


def しんぴのまもり_prevent_ailment(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しんぴのまもりで状態異常無効"""
    return HandlerReturn(value="")


def しんぴのまもり_prevent_volatile(battle: Battle, ctx: BattleContext, value: VolatileName) -> HandlerReturn:
    """しんぴのまもりで揮発状態無効"""
    # valueは揮発状態名（VolatileName）
    if value in ["こんらん", "ねむけ"]:
        return HandlerReturn(value="")
    return HandlerReturn(value=value)


def しろいきり_prevent_stat_drop(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しろいきりで能力低下を防ぐ"""
    if ctx.target == ctx.source:
        return HandlerReturn(value=value)

    filtered = {stat: v for stat, v in value.items() if v >= 0}
    if filtered == value:
        return HandlerReturn(value=value)

    return HandlerReturn(value=filtered)


def おいかぜ_speed_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """追い風で素早さ2倍"""
    return HandlerReturn(value=value * 2)


def ねがいごと_heal(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねがいごとのターン終了時HP回復"""
    side = battle.get_side(ctx.target)
    field = side.fields["ねがいごと"]
    side.tick_down("ねがいごと")
    if field.count == 0:
        heal = field.heal if field.heal > 0 else ctx.target.max_hp // 2
        battle.modify_hp(ctx.target, v=heal)
        field.heal = 0
    return HandlerReturn()


def まきびし_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まきびしのダメージ"""
    if not ctx.source or battle.query_manager.is_floating(ctx.source):
        return HandlerReturn()

    # 対象のサイドのまきびしフィールドを取得
    makibishi_field = battle.get_side(ctx.source).fields.get("まきびし")
    if not makibishi_field or makibishi_field.count == 0:
        return HandlerReturn()

    # 層数に応じたダメージ量を決定
    damage_ratio = {
        1: -1/8,
        2: -1/6,
    }.get(makibishi_field.count, -1/4)  # 3層以上は1/4

    success = battle.modify_hp(ctx.source, r=damage_ratio)
    return HandlerReturn(value=success)


def どくびし_poison(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """どくびしの毒付与"""
    if not ctx.source:
        return HandlerReturn()

    # 対象のサイドのどくびしフィールドを取得
    side = battle.get_side(ctx.source)
    dokubishi_field = side.fields.get("どくびし")
    if not dokubishi_field or dokubishi_field.count == 0:
        return HandlerReturn()

    # どくタイプは吸収して消滅
    if ctx.source.has_type("どく"):
        dokubishi_field.count = 0
        side.deactivate("どくびし")
        return HandlerReturn()

    if battle.query_manager.is_floating(ctx.source):
        return HandlerReturn()

    # 層数に応じて「どく」または「もうどく」を付与
    ailment = "もうどく" if dokubishi_field.count >= 2 else "どく"
    battle.ailment_manager.apply(ctx.source, ailment, source=ctx.source)
    return HandlerReturn()


def ステルスロック_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ステルスロックのダメージ（岩タイプ相性依存）"""
    r = battle.damage_calculator.calc_def_type_modifier(
        defender=ctx.source, move="ステルスロック"
    )
    battle.modify_hp(ctx.source, r=-1/8*r)
    return HandlerReturn()


def ねばねばネット_speed_drop(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねばねばネットの素早さダウン"""
    if not ctx.source or battle.query_manager.is_floating(ctx.source):
        return HandlerReturn()

    # 対象のサイドのねばねばネットフィールドを取得
    nebanet_field = battle.get_side(ctx.source).fields.get("ねばねばネット")
    if not nebanet_field or nebanet_field.count == 0:
        return HandlerReturn()

    # 素早さランクを1段階下げる
    battle.modify_stat(ctx.source, "S", -1, source=ctx.source)
    return HandlerReturn()
