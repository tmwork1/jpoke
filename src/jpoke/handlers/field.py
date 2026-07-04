from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext

from jpoke.enums import LogCode
from jpoke.types import RoleSpec, GlobalFieldName, SideFieldName, VolatileName, AbilityDisabledReason
from jpoke.utils.math import apply_fixed_modifier
from jpoke.core import HandlerReturn, Handler

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

def tick_weather(battle: Battle, ctx: EventContext, value: Any):
    # 1P側でのみカウントダウンを実行
    if battle.get_player(ctx.source) is battle.players[0]:
        battle.weather_manager.tick_down()
    return HandlerReturn(value=value)

def tick_terrain(battle: Battle, ctx: EventContext, value: Any):
    # 1P側でのみカウントダウンを実行
    if battle.get_player(ctx.source) is battle.players[0]:
        battle.terrain_manager.tick_down()
    return HandlerReturn(value=value)

def _tick_global_field(battle: Battle, ctx: EventContext, value: Any, name: GlobalFieldName) -> HandlerReturn:
    # 1P側でのみカウントダウンを実行
    if battle.get_player(ctx.source) is battle.players[0]:
        battle.global_manager.tick_down(name)
    return HandlerReturn(value=value)

def _tick_side_field(battle: Battle, ctx: EventContext, value: Any, name: SideFieldName) -> HandlerReturn:
    player = battle.get_player(ctx.source)
    side = battle.get_side(player)
    side.tick_down(name)
    return HandlerReturn(value=value)


def あめ_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """雨状態での技威力補正。防御側がばんのうがさを持つ場合は無効。"""
    # 仕様: 晴れ/雨のダメージ補正は防御側の効果とみなされる
    if battle.weather_for(ctx.defender).name == "":
        return HandlerReturn(value=value)
    move_type = ctx.move.type
    if move_type == "みず":
        value = apply_fixed_modifier(value, 6144)  # 1.5倍
    elif move_type == "ほのお":
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def いやしのねがい_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いやしのねがい: 場に出たポケモンの HP を全回復し、状態異常を回復する。

    HP 満タンかつ状態異常なしのポケモンには発動せず、フィールドは保留される（第八世代以降仕様）。
    HP またはAliment に変化があった場合のみフィールドを解除する。
    """
    mon = ctx.source
    side = battle.get_side(mon)
    # HP 満タンかつ状態異常なしなら発動しない（フィールドは保留）
    if mon.hp == mon.max_hp and not mon.ailment.is_active:
        return HandlerReturn(value=value)
    battle.modify_hp(mon, v=mon.max_hp - mon.hp)
    battle.ailment_manager.remove(mon)
    side.deactivate("いやしのねがい")
    return HandlerReturn(value=value)


def エレキフィールド_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """エレキフィールドでの電気技威力1.3倍"""
    if (
        ctx.move.type == "でんき" and
        not battle.query.is_floating(ctx.attacker)
    ):
        value = apply_fixed_modifier(value, 5325)  # 1.3倍
    return HandlerReturn(value=value)


def エレキフィールド_prevent_nemuke(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """エレキフィールドでねむけ無効"""
    if (
        value == "ねむけ"
        and not battle.query.is_floating(ctx.target)
    ):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def エレキフィールド_prevent_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """エレキフィールドでねむり無効"""
    if (
        value == "ねむり"
        and not battle.query.is_floating(ctx.target)
    ):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def おいかぜ_boost_spe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """追い風で素早さ2倍"""
    return HandlerReturn(value=value * 2)


def おいかぜ_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="おいかぜ")


def おおあめ_block_fire_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おおあめ中にほのおタイプ技を失敗させる（攻撃技・変化技を問わない）"""
    if ctx.move.type == "ほのお":
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "おおあめ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おおひでり_block_water_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おおひでり中にみずタイプ技を失敗させる（攻撃技・変化技を問わない）"""
    if ctx.move.type == "みず":
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "おおひでり"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def オーロラベール_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーロラベールで物理・特殊技ダメージ軽減。

    リフレクター（物理技）またはひかりのかべ（特殊技）が同時に有効でも効果は重複しない。
    """
    if (
        not ctx.critical
        and not ctx.can_bypass_screen(battle)
    ):
        side = battle.get_side(ctx.defender)
        # リフレクター/ひかりのかべと効果は重複しない
        if (
            ctx.move.category == "physical"
            and side.get("リフレクター").is_active
        ):
            return HandlerReturn(value=value)
        if (
            ctx.move.category == "special"
            and side.get("ひかりのかべ").is_active
        ):
            return HandlerReturn(value=value)
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def オーロラベール_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="オーロラベール")


def グラスフィールド_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """グラスフィールドのターン終了時回復"""
    if not battle.query.is_floating(ctx.source):
        battle.modify_hp(ctx.source, r=1/16)
    return HandlerReturn(value=value)


def グラスフィールド_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """グラスフィールドでの草技威力1.3倍・地面技威力0.5倍"""
    # 草技威力1.3倍（攻撃側が接地している場合）
    if (
        ctx.move.type == "くさ"
        and not battle.query.is_floating(ctx.attacker)
    ):
        value = apply_fixed_modifier(value, 5325)  # 1.3倍
    # 地面範囲技威力0.5倍（じしん、じならし、マグニチュード）
    if (
        ctx.move.name in ["じしん", "じならし", "マグニチュード"]
        and not battle.query.is_floating(ctx.defender)
    ):
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def サイコフィールド_block_priority_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サイコフィールドで先制技無効"""
    if (
        ctx.move.priority > 0
        and not battle.query.is_floating(ctx.defender)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "サイコフィールド"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def サイコフィールド_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サイコフィールドでのエスパー技威力1.3倍"""
    if (
        ctx.move.type == "エスパー"
        and not battle.query.is_floating(ctx.attacker)
    ):
        value = apply_fixed_modifier(value, 5325)  # 1.3倍
    return HandlerReturn(value=value)


def しろいきり_prevent_stat_drop(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しろいきりで能力低下を防ぐ"""
    if (
        ctx.is_foe_target()
        and not ctx.can_bypass_status_guard(battle)
    ):
        value = {stat: v for stat, v in value.items() if v > 0}
    return HandlerReturn(value=value)


def しろいきり_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="しろいきり")


def しんぴのまもり_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しんぴのまもりで状態異常無効（他のポケモン由来のわざのみ対象）。

    自分が使うねむるのような自己付与（source == target）は防がない。
    すりぬけ特性を持つ相手からの状態異常は防げない。
    """
    if (
        ctx.is_foe_target()
        and not ctx.can_bypass_status_guard(battle)
    ):
        value = ""  # 状態異常名を空にして無効化
    return HandlerReturn(value=value)


def しんぴのまもり_prevent_confusion(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しんぴのまもりでこんらん・ねむけ無効（他のポケモン由来のわざのみ対象）。

    自己付与（source == target）は防がない。
    すりぬけ特性を持つ相手からの揮発状態は防げない。
    """
    if (
        value in ["こんらん", "ねむけ"]
        and ctx.is_foe_target()
        and not ctx.can_bypass_status_guard(battle)
    ):
        value = ""  # 揮発状態名を空にして無効化
    return HandlerReturn(value=value)


def しんぴのまもり_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="しんぴのまもり")


def じゅうりょく_grounded(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じゅうりょく中は全ポケモンを地面に接地扱いにする"""
    return HandlerReturn(value=False, stop_event=True)


def じゅうりょく_modify_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうりょく中の命中率補正（約1.67倍: 6840/4096）"""
    return HandlerReturn(value=apply_fixed_modifier(value, 6840))


def じゅうりょく_remove_volatiles(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じゅうりょく発動時にそらをとぶ・でんじふゆう揮発性状態を解除する"""
    mon = ctx.source
    for volatile_name in ["そらをとぶ", "でんじふゆう"]:
        battle.volatile_manager.remove(mon, volatile_name)
    return HandlerReturn(value=value)


def じゅうりょく_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_global_field(battle, ctx, value, name="じゅうりょく")


def ステルスロック_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ステルスロックのダメージ（岩タイプ相性依存）

    らんきりゅうの影響を受けないため ON_CALC_DEF_TYPE_MODIFIER イベントを経由せず、
    タイプ表から直接相性を計算する。
    """
    from jpoke.data import TYPE_MODIFIER

    if battle.query.is_hazard_immune(ctx.source):
        return HandlerReturn(value=value)
    # タイプ相性をイベント経由せずタイプ表から直接計算する（×1/4・×1/2も正しく処理）
    type_chart = TYPE_MODIFIER.get("いわ", {})
    base = 4096
    for def_type in ctx.source.types:
        base = int(base * type_chart.get(def_type, 1.0))
    battle.modify_hp(ctx.source, r=-base / (4096 * 8))
    return HandlerReturn(value=value)


def すなあらし_boost_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """砂嵐時のいわタイプ特防1.5倍。エアロック・ノーてんきで天候が無効化されている場合は適用しない。"""
    if (
        battle.weather.name == "すなあらし"
        and ctx.defender.has_type("いわ")
        and ctx.move.category == "special"
    ):
        value = apply_fixed_modifier(value, 6144)  # 1.5倍
    return HandlerReturn(value=value)


def すなあらし_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """すなあらしのターン終了時ダメージ（Priority 20: tick後に天候チェック）"""
    if battle.weather.name != "すなあらし":
        return HandlerReturn(value=value)
    if not (
        ctx.source.has_type("いわ")
        or ctx.source.has_type("じめん")
        or ctx.source.has_type("はがね")
    ):
        battle.modify_hp(ctx.source, r=-1/16, reason="sandstorm")
    return HandlerReturn(value=value)


def トリックルーム_reverse_spe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """トリックルームで素早さ反転"""
    return HandlerReturn(value=-value)


def トリックルーム_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_global_field(battle, ctx, value, name="トリックルーム")


def どくびし_apply_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくびしの毒付与"""
    # 対象のサイドのどくびしフィールドを取得
    side = battle.get_side(ctx.source)
    field = side.get("どくびし")

    # 浮いているポケモンは影響を受けない（地面に接地していない場合はどくタイプでも消滅させられない）
    if battle.query.is_floating(ctx.source):
        return HandlerReturn(value=value)

    # どくタイプは吸収して消滅（あつぞこブーツ装備でも消滅する）
    if ctx.source.has_type("どく"):
        side.deactivate("どくびし")
        return HandlerReturn(value=value)

    # あつぞこブーツ等のハザード無効は消滅させずに効果のみ無効化
    if battle.query.is_hazard_immune(ctx.source):
        return HandlerReturn(value=value)

    # 層数に応じて「どく」または「もうどく」を付与
    ailment = "もうどく" if field.count >= 2 else "どく"
    battle.ailment_manager.apply(ctx.source, ailment, source=ctx.source)
    return HandlerReturn(value=value)


def ねがいごと_heal(battle: Battle, ctx: EventContext, value: Field) -> HandlerReturn:
    """ねがいごとのターン終了時HP回復"""
    battle.modify_hp(ctx.source, v=value.heal)
    return HandlerReturn(value=value)


def ねがいごと_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="ねがいごと")


def ねばねばネット_reduce_spe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねばねばネットの素早さダウン"""
    if battle.query.is_hazard_immune(ctx.source):
        return HandlerReturn(value=value)
    # 浮いているポケモンは影響を受けない
    if battle.query.is_floating(ctx.source):
        return HandlerReturn(value=value)

    # 素早さランクを1段階下げる (相手由来と判定される)
    battle.modify_stats(ctx.source, {"spe": -1}, source=battle.foe(ctx.source))
    return HandlerReturn(value=value)


def はめつのねがい_damage(battle: Battle, ctx: EventContext, value: Field) -> HandlerReturn:
    """はめつのねがい: フィールド解除時に相手のポケモンへ蓄積ダメージを適用する。"""
    if not ctx.source.alive:
        return HandlerReturn(value=value)
    battle.modify_hp(ctx.source, v=-value.damage, reason="move_damage")
    return HandlerReturn(value=value)


def はめつのねがい_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """はめつのねがい: ターン終了時にカウントを減算する。"""
    return _tick_side_field(battle, ctx, value, name="はめつのねがい")


def はれ_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """晴れ状態での技威力補正。防御側がばんのうがさを持つ場合は無効。"""
    # 仕様: 晴れ/雨のダメージ補正は防御側の効果とみなされる
    if battle.weather_for(ctx.defender).name == "":
        return HandlerReturn(value=value)
    move_type = ctx.move.type
    if move_type == "ほのお":
        value = apply_fixed_modifier(value, 6144)  # 1.5倍
    elif move_type == "みず":
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def はれ_prevent_freeze(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """晴れ状態でこおり無効"""
    if value == "こおり":
        value = ""
    return HandlerReturn(value=value)


def ひかりのかべ_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """光の壁で特殊技ダメージ軽減"""
    if (
        not ctx.critical
        and not ctx.can_bypass_screen(battle)
        and ctx.move.category == "special"
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def ひかりのかべ_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="ひかりのかべ")


def フェアリーロック_check_trapped(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """フェアリーロック場の状態: ゴーストタイプを含む全ポケモンの交代を禁止する。"""
    return HandlerReturn(value=True)


def フェアリーロック_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_global_field(battle, ctx, value, name="フェアリーロック")


def まきびし_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まきびしのダメージ"""
    if battle.query.is_hazard_immune(ctx.source):
        return HandlerReturn(value=value)
    if battle.query.is_floating(ctx.source):
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


def マジックルーム_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マジックルーム適用時にアイテム無効状態を再計算する。"""
    battle.item_manager.add_disabled_reason(ctx.source, "マジックルーム")
    return HandlerReturn(value=value)


def マジックルーム_remove(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マジックルーム解除時にアイテム有効状態を再計算する。"""
    battle.item_manager.remove_disabled_reason(ctx.source, "マジックルーム")
    return HandlerReturn(value=value)


def マジックルーム_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_global_field(battle, ctx, value, name="マジックルーム")


def みかづきのまい_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みかづきのまい: 場に出たポケモンの HP を全回復し、状態異常を回復し、全ての技の PP を全回復する。

    HP 満タン・状態異常なし・全ての技の PP が満タンの場合には発動せず、フィールドは保留される。
    いずれかに変化があった場合のみフィールドを解除する。
    """
    mon = ctx.source
    side = battle.get_side(mon)
    pp_full = all(m.pp == m.data.pp for m in mon.moves)
    if mon.hp == mon.max_hp and not mon.ailment.is_active and pp_full:
        return HandlerReturn(value=value)
    battle.modify_hp(mon, v=mon.max_hp - mon.hp)
    battle.ailment_manager.remove(mon)
    for move in mon.moves:
        move.reset(reset_pp=True)
    side.deactivate("みかづきのまい")
    return HandlerReturn(value=value)


def ミストフィールド_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミストフィールドでのドラゴン技威力0.5倍"""
    if (
        ctx.move.type == "ドラゴン"
        and not battle.query.is_floating(ctx.defender)
    ):
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def ミストフィールド_prevent_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ミストフィールドで状態異常無効"""
    if not battle.query.is_floating(ctx.target):
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def ミストフィールド_prevent_confusion(battle: Battle, ctx: EventContext, value: VolatileName) -> HandlerReturn:
    """ミストフィールドで混乱無効"""
    if (
        value == "こんらん"
        and not battle.query.is_floating(ctx.target)
    ):
        return HandlerReturn(value="", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(value=value)  # 防がない


def みらいよち_damage(battle: Battle, ctx: EventContext, value: Field) -> HandlerReturn:
    """みらいよち: フィールド解除時に相手のポケモンへ蓄積ダメージを適用する。"""
    if not ctx.source.alive:
        return HandlerReturn(value=value)
    battle.modify_hp(ctx.source, v=-value.damage, reason="move_damage")
    return HandlerReturn(value=value)


def みらいよち_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みらいよち: ターン終了時にカウントを減算する。"""
    return _tick_side_field(battle, ctx, value, name="みらいよち")


def ゆき_boost_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """雪時のこおりタイプ防御1.5倍。エアロック・ノーてんきで天候が無効化されている場合は適用しない。"""
    if (
        battle.weather.name == "ゆき"
        and ctx.defender.has_type("こおり")
        and ctx.move.category == "physical"
    ):
        value = apply_fixed_modifier(value, 6144)  # 1.5倍
    return HandlerReturn(value=value)


def らんきりゅう_type_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """らんきりゅう中にひこうタイプの弱点（でんき/いわ/こおり）を0.5倍に軽減する"""
    if (
        ctx.defender.has_type("ひこう")
        and ctx.move.type in {"でんき", "いわ", "こおり"}
    ):
        value = apply_fixed_modifier(value, 2048)  # ×0.5
    return HandlerReturn(value=value)


def リフレクター_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リフレクターで物理技ダメージ軽減"""
    if (
        not ctx.critical
        and not ctx.can_bypass_screen(battle)
        and ctx.move.category == "physical"
    ):
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)


def リフレクター_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="リフレクター")


def ワンダールーム_def_modifier(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ワンダールーム中は防御実数値参照を入れ替える。"""
    base_stat = "def" if battle.query.deals_physical_damage(ctx.attacker, ctx.move) else "spd"
    swapped_stat = "spd" if base_stat == "def" else "def"
    base_value = max(1, ctx.defender.stats[base_stat])
    swap_value = max(1, ctx.defender.stats[swapped_stat])
    return HandlerReturn(value=value * swap_value // base_value)


def ワンダールーム_def_rank_modifier(battle: Battle, ctx: AttackContext, value: float) -> HandlerReturn:
    """ワンダールーム中は物理/特殊で参照する防御ランクを入れ替える。"""
    category_to_stat = {"physical": "spd", "special": "def"}
    swapped_stat = category_to_stat.get(ctx.move.category)
    value = ctx.defender.rank_modifier(swapped_stat)
    return HandlerReturn(value=value)


def ワンダールーム_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_global_field(battle, ctx, value, name="ワンダールーム")
