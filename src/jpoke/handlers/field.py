from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext
    from jpoke.model import Field

from jpoke.enums import LogCode
from jpoke.types import RoleSpec, GlobalFieldName, SideFieldName, VolatileName
from jpoke.utils.math import apply_fixed_modifier
from jpoke.core.handler import HandlerReturn, Handler
from jpoke.core.log_payload import FailureLogPayload, AilmentPayload

class FieldHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 allow_fainted_subject: bool = False):
        super().__init__(
            func=func,
            source="field",
            subject_spec=subject_spec,
            priority=priority,
            allow_fainted_subject=allow_fainted_subject,
        )

def tick_weather(battle: Battle, ctx: EventContext, value: Any):
    # 1P側でのみカウントダウンを実行
    if battle.get_player(ctx.source) is battle.players[0]:
        battle.weather_manager.tick_down_current()
    return HandlerReturn(value=value)

def tick_terrain(battle: Battle, ctx: EventContext, value: Any):
    # 1P側でのみカウントダウンを実行
    if battle.get_player(ctx.source) is battle.players[0]:
        battle.terrain_manager.tick_down_current()
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

def _is_own_field(value: Field, own_field: Field) -> bool:
    """Event.ON_FIELD_DEACTIVATE 等、単一のFieldインスタンスをvalueとして受け取る
    イベントで、valueが「自分自身の効果に紐づくFieldインスタンス」と一致するかを判定する。

    EventManagerはON_FIELD_DEACTIVATEを、そのイベントに登録された全ハンドラが
    共有する単一のバケツへ発火する。そのため、あるFieldインスタンス（例:
    Player2のねがいごと）の解除で発火したemit呼び出しに、
    - 同名だが別インスタンスのフィールド（例: Player1のねがいごと。まだ解除されて
      いない）のハンドラ
    - 同じPlayerに紐づく別種のフィールド（例: マジックルーム）のハンドラ
    も、subject_spec の一致判定だけでは区別できず巻き込まれて誤発動してしまう
    （valueは解除された側のFieldインスタンスのままのため、無関係な側に誤った
    回復量・ダメージ量が適用されたり、まだ解除されていないはずの効果が解除
    されてしまったりする）。呼び出し側で「本来自分自身が対応すべきFieldインスタンス」
    （`battle.get_side(...).get(name)` や `battle.global_manager.get(name)` で
    取得したもの）と value の同一性を比較することで、無関係なemitへの巻き込みを
    防ぐ（fuzzログ seed=2946で発見。field_manager.BaseFieldManager._deactivate_field 参照）。
    """
    return value is own_field


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
        battle.add_event_log(
            ctx.target,
            LogCode.AILMENT_PREVENTED,
            payload=AilmentPayload(ailment=value, display_reason="エレキフィールド"),
        )
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="おおあめ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おおひでり_block_water_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おおひでり中にみずタイプ技を失敗させる（攻撃技・変化技を問わない）"""
    if ctx.move.type == "みず":
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="おおひでり")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def オーロラベール_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーロラベールで物理・特殊技ダメージ軽減。

    リフレクター（物理技）またはひかりのかべ（特殊技）が同時に有効でも効果は重複しない。
    こんらんの自傷ダメージ（"_こんらん"）は攻撃技扱いではないため軽減されない。
    """
    if (
        not ctx.critical
        and not ctx.can_bypass_screen(battle)
        and ctx.move.name != "_こんらん"
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
        modifier = 2732 if battle.option.double_battle else 2048
        value = apply_fixed_modifier(value, modifier)
    return HandlerReturn(value=value)


def オーロラベール_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="オーロラベール")


def グラスフィールド_boost_move_priority(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """グラスフィールド: 接地している使用者のグラススライダーの優先度を+1する。"""
    if (
        ctx.move.name == "グラススライダー"
        and not battle.query.is_floating(ctx.attacker)
    ):
        value += 1
    return HandlerReturn(value=value)


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
    """サイコフィールドで先制技無効

    技の使用者自身に対して使われた技（まもるなど）・全体の場が対象の技・
    相手の場が対象の技は無効化対象外（対象が相手単体の技のみブロックする）。
    """
    if (
        ctx.move.priority > 0
        and ctx.move.target == "foe"
        and not battle.query.is_floating(ctx.defender)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="サイコフィールド")
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
        battle.add_event_log(
            ctx.target,
            LogCode.AILMENT_PREVENTED,
            payload=AilmentPayload(ailment=value, display_reason="しんぴのまもり"),
        )
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
    """じゅうりょく中の命中率補正（約1.67倍: 6840/4096）。一撃必殺技は対象外。

    value が None の場合は既に必中状態が確定しているため、補正をかけずそのまま返す。
    """
    if value is None or ctx.move.has_flag("ohko"):
        return HandlerReturn(value=value)
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
    """どくびしの毒付与

    どくびしは付与元の特性ふしょくによるタイプ無効貫通の対象外であり、繰り出した
    ポケモン自身がふしょく持ちのはがね・どくタイプ（テラスタル含む）であっても
    どく・もうどく状態にはならない（allow_type_immunity_bypass=False）。
    """
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
    battle.ailment_manager.apply(
        ctx.source, ailment, source=ctx.source, allow_type_immunity_bypass=False
    )
    return HandlerReturn(value=value)


def ねがいごと_heal(battle: Battle, ctx: EventContext, value: Field) -> HandlerReturn:
    """ねがいごとのターン終了時HP回復"""
    if not _is_own_field(value, battle.get_side(ctx.source).get("ねがいごと")):
        return HandlerReturn(value=value)
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
    if not _is_own_field(value, battle.get_side(ctx.source).get("はめつのねがい")):
        return HandlerReturn(value=value)
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
    """晴れ状態でこおり無効。対象がばんのうがさを持つ場合は晴れの影響を受けず、こおり状態になる。"""
    if value == "こおり" and battle.weather_for(ctx.target).sunny:
        value = ""
    return HandlerReturn(value=value)


def ひかりのかべ_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """光の壁で特殊技ダメージ軽減"""
    if (
        not ctx.critical
        and not ctx.can_bypass_screen(battle)
        and ctx.move.category == "special"
    ):
        modifier = 2732 if battle.option.double_battle else 2048
        value = apply_fixed_modifier(value, modifier)
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


def マジックルーム_remove(battle: Battle, ctx: EventContext, value: Field) -> HandlerReturn:
    """マジックルーム解除時にアイテム有効状態を再計算する。

    Event.ON_FIELD_DEACTIVATE は共有ハンドラバケツで発火するため、ねがいごと等の
    無関係なフィールドの解除に巻き込まれてマジックルームがまだ有効なのに
    解除処理が走ってしまわないよう、valueが自分自身（マジックルーム）の
    Fieldインスタンスかを確認する。
    """
    if not _is_own_field(value, battle.global_manager.get("マジックルーム")):
        return HandlerReturn(value=value)
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
    """ミストフィールドで状態異常無効

    無効化対象はどく・やけど・こおり・ねむり・まひ・もうどくの6種類のみ
    （.internal/spec/fields/ミストフィールド.md）。ゆめうつつ（特性ぜったいねむり）は
    通常の状態異常付与ではなく無効化不可能な効果のため対象外
    （.internal/spec/abilities/ぜったいねむり.md: 「この特性は無効化することができない」）。
    """
    if value == "ゆめうつつ":
        return HandlerReturn(value=value)
    if not battle.query.is_floating(ctx.target):
        battle.add_event_log(
            ctx.target,
            LogCode.AILMENT_PREVENTED,
            payload=AilmentPayload(ailment=value, display_reason="ミストフィールド"),
        )
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
    if not _is_own_field(value, battle.get_side(ctx.source).get("みらいよち")):
        return HandlerReturn(value=value)
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
    """らんきりゅう中にひこうタイプの弱点（でんき/いわ/こおり）を0.5倍に軽減する。
    エアロック・ノーてんきで天候が無効化されている場合は効果を発動しない。
    """
    if battle.weather_for(ctx.defender).name == "":
        return HandlerReturn(value=value)
    if (
        ctx.defender.has_type("ひこう")
        and ctx.move.type in {"でんき", "いわ", "こおり"}
    ):
        value = apply_fixed_modifier(value, 2048)  # ×0.5
    return HandlerReturn(value=value)


def リフレクター_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リフレクターで物理技ダメージ軽減。

    こんらんの自傷ダメージ（"_こんらん"）は物理カテゴリだが攻撃技扱いではないため軽減されない。
    """
    if (
        not ctx.critical
        and not ctx.can_bypass_screen(battle)
        and ctx.move.category == "physical"
        and ctx.move.name != "_こんらん"
    ):
        modifier = 2732 if battle.option.double_battle else 2048
        value = apply_fixed_modifier(value, modifier)
    return HandlerReturn(value=value)


def リフレクター_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_side_field(battle, ctx, value, name="リフレクター")


def ワンダールーム_def_modifier(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ワンダールーム中は防御実数値参照を入れ替える。

    ランク補正は入れ替わらず、技の分類（物理/特殊）に対応する本来の
    ランク値のまま据え置かれる（本家の既知の仕様）。実数値の比率のみを
    ON_CALC_DEF_MODIFIER に掛けることで、実数値だけを入れ替えた計算結果になる。
    """
    base_stat = "def" if battle.query.deals_physical_damage(ctx.attacker, ctx.move) else "spd"
    swapped_stat = "spd" if base_stat == "def" else "def"
    base_value = max(1, ctx.defender.stats[base_stat])
    swap_value = max(1, ctx.defender.stats[swapped_stat])
    return HandlerReturn(value=value * swap_value // base_value)


def ワンダールーム_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_global_field(battle, ctx, value, name="ワンダールーム")
