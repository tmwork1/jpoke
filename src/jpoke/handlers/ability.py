"""特性ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec, HPChangeReason, Type, Stat
from jpoke.utils.constants import PLATE_TO_TYPE, MEMORY_TO_TYPE
from jpoke.enums import Event, LogCode
from jpoke.core import HandlerReturn, Handler
from . import common


AEGISLASH_NAME = "ギルガルド"
AEGISLASH_SHIELD_ALIAS = "ギルガルド(シールド)"
AEGISLASH_BLADE_ALIAS = "ギルガルド(ブレード)"
PALAFIN_NAME = "イルカマン"
PALAFIN_ZERO_ALIAS = "イルカマン(ナイーブ)"
PALAFIN_HERO_ALIAS = "イルカマン(マイティ)"


class AbilityHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 once: bool = False) -> None:
        super().__init__(
            func=func,
            subject_spec=subject_spec,
            priority=priority,
            once=once,
        )


def _set_harapeko_form(mon, *, hangry: bool) -> None:
    """はらぺこスイッチ用のフォルム状態を更新する。"""
    mon.ability.is_hangry = hangry


def _toggle_harapeko_form(mon) -> None:
    """はらぺこスイッチ用のフォルム状態を反転する。"""
    mon.ability.is_hangry = not mon.ability.is_hangry


def _is_harvest_sunny_rate_100(battle: Battle) -> bool:
    active = battle.weather
    return active is not None and active.name == "はれ"


def _get_harvest_chance(battle: Battle) -> float:
    """しゅうかくの発動確率を返す。"""
    return 1.0 if _is_harvest_sunny_rate_100(battle) else 0.5


def _trigger_emergency_switch(battle: Battle, mon, ability_name: str) -> bool:
    """緊急交代を発動する。"""
    from jpoke.enums import Interrupt

    player = battle.find_player(mon)
    if player.interrupt != Interrupt.NONE:
        return False
    if not battle.get_available_switch_commands(player):
        return False

    player.interrupt = Interrupt.EMERGENCY
    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": ability_name, "success": True},
    )
    return True


def _handle_type_absorb(battle: Battle,
                        ctx: BattleContext,
                        value: bool,
                        *,
                        ability_name: str,
                        move_type: Type,
                        heal_ratio: float = 0,
                        raise_stat: Stat | None = None) -> HandlerReturn:
    """タイプ一致技を無効化し、副次効果（回復/能力上昇）を適用する。"""
    if value:
        return HandlerReturn(value=value)
    if ctx.move is None:
        return HandlerReturn(value=value)
    if not ctx.is_foe_target:
        return HandlerReturn(value=value)
    if ctx.move.type != move_type:
        return HandlerReturn(value=value)
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    target = ctx.defender

    if heal_ratio > 0:
        battle.modify_hp(target, r=heal_ratio, reason="ability")

    if raise_stat is not None:
        battle.modify_stat(
            target,
            raise_stat,
            1,
            source=ctx.attacker,
            reason=ability_name,
        )

    idx = battle.get_player_index(target)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": ability_name, "success": True},
    )
    return HandlerReturn(value=True, stop_event=True)


def あまのじゃく_modify_stat(battle: Battle, ctx: BattleContext, value: dict[str, int]) -> HandlerReturn:
    """あまのじゃく特性: 能力変化量の符号を反転する。"""
    return HandlerReturn(value={stat: -delta for stat, delta in value.items()})


def いたずらごころ_modify_move_priority(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いたずらごころ特性: 変化技の優先度を+1する。"""
    if ctx.move is None:
        return HandlerReturn(value=value)
    if ctx.move.category != "変化":
        return HandlerReturn(value=value)
    return HandlerReturn(value=value + 1)


def いたずらごころ_block_dark_target(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """いたずらごころ特性: 優先度が上がった変化技はあくタイプ相手に無効化される。"""
    if value:
        return HandlerReturn(value=value)
    if ctx.move is None or ctx.move.category != "変化":
        return HandlerReturn(value=value)
    if ctx.move.priority < 0:
        return HandlerReturn(value=value)
    if not ctx.is_foe_target:
        return HandlerReturn(value=value)
    if not ctx.defender.has_type("あく"):
        return HandlerReturn(value=value)

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "いたずらごころ", "success": True},
    )
    return HandlerReturn(value=True, stop_event=True)


def エアロック_check_weather_enabled(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """エアロック特性: 天候効果を無効化する。"""
    if not value:
        return HandlerReturn(value=value)
    return HandlerReturn(value=False, stop_event=True)


def ありじごく_check_trapped(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ありじごく特性: 浮いていないポケモンの交代を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_TRAPPED)
            - source: 交代を試みるポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: (True, 交代が制限されるかどうか)
            - 浮いていない場合はTrue（交代制限）
    """
    # ポケモンが浮いているかどうかを判定
    # 浮いている = ふゆう、でんじふゆう、テレキネシス等
    result = not battle.query_manager.is_floating(ctx.source)
    return HandlerReturn(value=result)


def かげふみ_check_trapped(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かげふみ特性: かげふみ持ち以外のポケモンの交代を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_TRAPPED)
            - source: 交代を試みるポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: (True, 交代が制限されるかどうか)
            - かげふみ持ち以外はTrue（交代制限）
    """
    result = ctx.source.ability != "かげふみ"
    return HandlerReturn(value=result)


def かがくへんかガス_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かがくへんかガス特性: 場の特性有効状態を再計算する。"""
    battle.refresh_effect_enabled_states()

    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "かがくへんかガス", "success": True}
    )
    return HandlerReturn(value=value)


def ぎゃくじょう_on_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ぎゃくじょう特性: HP が半分以下になった時、特攻が1段階上昇する。"""
    if ctx.move is None or not ctx.move.is_attack:
        return HandlerReturn(value=value)
    if ctx.attacker is None or ctx.defender is None:
        return HandlerReturn(value=value)
    if ctx.move_damage == 0:
        return HandlerReturn(value=value)
    if ctx.defender.fainted:
        return HandlerReturn(value=value)

    # マルチヒット時は全ヒットのダメージを累算し、最終ヒット後に判定する
    if not hasattr(ctx, "total_damage"):
        ctx.total_damage = 0
    ctx.total_damage += ctx.move_damage

    if ctx.hit_index != ctx.hit_count:
        return HandlerReturn(value=value)

    hp_after = ctx.defender.hp
    hp_before = hp_after + ctx.total_damage
    del ctx.total_damage

    if not common.crossed_half_hp(hp_before, hp_after, ctx.defender.max_hp):
        return HandlerReturn(value=value)

    changed = battle.modify_stat(
        ctx.defender,
        "C",
        +1,
        source=ctx.attacker,
        reason="ぎゃくじょう",
    )
    if not changed:
        return HandlerReturn(value=value)

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ぎゃくじょう", "success": True},
    )
    return HandlerReturn(value=value)


def ききかいひ_on_hp_change(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ききかいひ特性: HPが半分以下になったとき交代する。"""
    mon = ctx.target
    if mon is None or mon.fainted:
        return HandlerReturn(value=value)
    # こんらん自傷、いたみわけでは交代できない
    if ctx.hp_change_reason in {"self_attack", "pain_split"}:
        return HandlerReturn(value=value)

    hp_after = mon.hp
    hp_before = hp_after + value
    if not common.crossed_half_hp(hp_before, hp_after, mon.max_hp):
        return HandlerReturn(value=value)

    _trigger_emergency_switch(battle, mon, mon.ability.orig_name)
    return HandlerReturn(value=value)


def じりょく_check_trapped(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """じりょく特性: はがねタイプのポケモンの交代を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_TRAPPED)
            - source: 交代を試みるポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: (True, 交代が制限されるかどうか)
            - はがねタイプの場合はTrue（交代制限）
    """
    result = ctx.source.has_type("はがね")
    return HandlerReturn(value=result)


def しゅうかく_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しゅうかく特性: ターン終了時に消費したきのみを復活させる。"""
    mon = ctx.source

    if mon.has_item():
        return HandlerReturn(value=value)

    if not mon.item.lost or mon.item.lost_cause != "consume":
        return HandlerReturn(value=value)

    berry_name = mon.item.orig_name
    if not common.is_berry_item(berry_name):
        return HandlerReturn(value=value)

    chance = _get_harvest_chance(battle)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)

    battle.set_item(mon, berry_name)

    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "しゅうかく", "success": True},
    )

    # 復活直後に使用条件を満たすきのみは、その場で使用される。
    battle.events.emit(Event.ON_ITEM_RESTORED, ctx.__class__(source=mon))
    return HandlerReturn(value=value)


def ちょすい_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ちょすい特性: みず技を無効化し最大HPの1/4回復する。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="ちょすい",
        move_type="みず",
        heal_ratio=1 / 4,
    )


def どしょく_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """どしょく特性: じめん技を無効化し最大HPの1/4回復する。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="どしょく",
        move_type="じめん",
        heal_ratio=1 / 4,
    )


def ひらいしん_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ひらいしん特性: でんき技を無効化し特攻を1段階上げる。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="ひらいしん",
        move_type="でんき",
        raise_stat="C",
    )


def よびみず_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """よびみず特性: みず技を無効化し特攻を1段階上げる。"""
    return _handle_type_absorb(
        battle,
        ctx,
        value,
        ability_name="よびみず",
        move_type="みず",
        raise_stat="C",
    )


def もらいび_check_immune(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技を無効化し、炎技強化状態を有効化する。"""
    if value:
        return HandlerReturn(value=value)
    if ctx.move is None:
        return HandlerReturn(value=value)
    if not ctx.is_foe_target:
        return HandlerReturn(value=value)
    if ctx.move.type != "ほのお":
        return HandlerReturn(value=value)
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    ctx.defender.ability.state = "charged"

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "もらいび", "success": True},
    )
    return HandlerReturn(value=True, stop_event=True)


def もらいび_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """もらいび特性: 登場時に炎技強化状態を初期化する。"""
    ctx.source.ability.state = "idle"
    return HandlerReturn(value=value)


def もらいび_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """もらいび特性: 吸収後の最初のほのお技のみ威力を1.5倍にする。"""
    if ctx.move is None or ctx.move.type != "ほのお":
        return HandlerReturn(value=value)
    if ctx.attacker.ability.state != "active":
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 6144))


def もらいび_on_move_charge(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """もらいび特性: ほのお技使用時に強化適用予約。"""
    if not value:
        return HandlerReturn(value=value)
    if ctx.move is None or ctx.move.type != "ほのお":
        return HandlerReturn(value=value)
    if ctx.source.ability.state != "charged":
        return HandlerReturn(value=value)

    ctx.source.ability.state = "active"
    return HandlerReturn(value=value)


def もらいび_on_move_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """もらいび特性: 行動終了時に強化を消費済みにする。"""
    state = ctx.source.ability.state
    if state == "active":
        ctx.source.ability.state = "idle"
    return HandlerReturn(value=value)


def はらぺこスイッチ_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """はらぺこスイッチ特性: 交代時のフォルム状態を更新する。"""
    # テラスタル中に交代した場合は現在のフォルムを維持する。
    # ただし瀕死退場時はまんぷくへ戻す。
    if ctx.source.is_terastallized and ctx.source.alive:
        return HandlerReturn(value=value)

    _set_harapeko_form(ctx.source, hangry=False)
    return HandlerReturn(value=value)


def はらぺこスイッチ_on_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """はらぺこスイッチ特性: ターン終了時にフォルムを切り替える。"""
    if ctx.source.is_terastallized:
        return HandlerReturn(value=value)

    _toggle_harapeko_form(ctx.source)
    return HandlerReturn(value=value)


def はらぺこスイッチ_modify_move_type(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """はらぺこスイッチ特性: オーラぐるまのタイプをフォルムで変える。"""
    if ctx.move is None or ctx.move.name != "オーラぐるま":
        return HandlerReturn(value=value)

    move_type = "あく" if ctx.source.ability.is_hangry else "でんき"
    return HandlerReturn(value=move_type)


def バトルスイッチ_check_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 行動前に必要なフォルムへ切り替える。"""
    mon = ctx.source
    if mon is None or mon.name != AEGISLASH_NAME or ctx.move is None:
        return HandlerReturn(value=value)

    next_alias = ""
    if mon.alias == AEGISLASH_SHIELD_ALIAS and ctx.move.is_attack:
        next_alias = AEGISLASH_BLADE_ALIAS
    elif mon.alias == AEGISLASH_BLADE_ALIAS and ctx.move.name == "キングシールド":
        next_alias = AEGISLASH_SHIELD_ALIAS

    if not next_alias:
        return HandlerReturn(value=value)

    mon.set_form(next_alias)

    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "バトルスイッチ", "success": True},
    )
    return HandlerReturn(value=value)


def バトルスイッチ_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バトルスイッチ特性: 交代時にシールドフォルムへ戻す。"""
    mon = ctx.source
    if mon is None or mon.name != AEGISLASH_NAME:
        return HandlerReturn(value=value)

    mon.set_form(AEGISLASH_SHIELD_ALIAS)
    return HandlerReturn(value=value)


def かちき_on_stat_down(battle: Battle, ctx: BattleContext, value: dict[str, int]) -> HandlerReturn:
    """かちき特性: 能力が下がると特攻が2段階上昇する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_STAT)
            - target: 能力変化の対象（自分）
            - source: 能力変化の原因
        value: 能力変化の辞書 {stat: change}

    Returns:
        HandlerReturn: (処理実行フラグ)
            - 能力が下がり、自分以外が原因の場合は特攻上昇
    """
    # いずれかの能力が下がったかチェック
    has_negative = any(v < 0 for v in value.values())
    # 自分以外が原因で能力が下がった場合、特攻を2段階上昇
    result = has_negative and \
        ctx.source != ctx.target and \
        common.modify_stat(battle, ctx, value, "C", +2, target_spec="target:self", source_spec="target:self")
    return HandlerReturn(value=result)


def カブトアーマー_on_calc_critical_rank(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """カブトアーマー特性: 防御側の急所ランクを無効化する。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    return HandlerReturn(value=0)


def すなかき_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すなかき特性: すなあらし中に素早さが2倍になる。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 元の素早さ値

    Returns:
        HandlerReturn: (True, 補正後の素早さ)
            - すなあらし中は2倍、それ以外は元の値
    """
    active = battle.weather
    if active is not None and active.name == "すなあらし":
        value *= 2
    return HandlerReturn(value=value)


def すいすい_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すいすい特性: あめ中に素早さが2倍になる。"""
    active = battle.weather
    if active is not None and active.name == "あめ":
        value *= 2
    return HandlerReturn(value=value)


def スキルリンク_modify_hit_count(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """スキルリンク特性: 連続技のヒット数を最大にする。"""
    if ctx.move.data.max_hits <= 1:
        return HandlerReturn(value=value)
    return HandlerReturn(value=ctx.move.data.max_hits)


def ねんちゃく_prevent_item_change(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ねんちゃく特性: 相手から受ける持ち物交換・奪取・除去を防ぐ。"""
    if not value:
        return HandlerReturn(value=value)

    if ctx.source == ctx.target:
        return HandlerReturn(value=value)

    if ctx.move is not None and not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ねんちゃく", "success": True},
    )
    return HandlerReturn(value=False, stop_event=True)


def マジシャン_steal_item(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マジシャン特性: 攻撃成功後に相手の持ち物を奪う。"""
    if ctx.move_damage == 0:
        return HandlerReturn(value=value)
    if ctx.attacker.has_item() or not ctx.defender.has_item():
        return HandlerReturn(value=value)

    battle.take_item(ctx.attacker, ctx.defender, move=ctx.move)
    return HandlerReturn(value=value)


def マイティチェンジ_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マイティチェンジ特性: ナイーブフォルムで引っ込むとマイティフォルムへ変化する。"""
    mon = ctx.source
    if mon is None or mon.name != PALAFIN_NAME:
        return HandlerReturn(value=value)
    if mon.alias != PALAFIN_ZERO_ALIAS:
        return HandlerReturn(value=value)
    if not mon.alive:
        return HandlerReturn(value=value)

    mon.set_form(PALAFIN_HERO_ALIAS)

    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "マイティチェンジ", "success": True},
    )
    return HandlerReturn(value=value)


def わるいてぐせ_steal_item(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """わるいてぐせ特性: 直接攻撃を受けた後に相手の持ち物を奪う。"""
    if ctx.move_damage == 0:
        return HandlerReturn(value=value)
    if ctx.defender.fainted:
        return HandlerReturn(value=value)
    if ctx.defender.has_item() or not ctx.attacker.has_item():
        return HandlerReturn(value=value)
    if not battle.move_executor.is_contact(ctx):
        return HandlerReturn(value=value)

    battle.take_item(ctx.defender, ctx.attacker, move=ctx.move)
    return HandlerReturn(value=value)


def てつのこぶし_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """てつのこぶし特性: パンチ技の威力を1.2倍にする。"""
    if ctx.move.has_label("punch"):
        value = value * 4915 // 4096
    return HandlerReturn(value=value)


def がんじょうあご_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """がんじょうあご特性: かみつき技の威力を1.5倍にする。"""
    if ctx.move is not None and ctx.move.has_label("bite"):
        value = common.apply_modifier(value, 6144)
    return HandlerReturn(value=value)


def かたいツメ_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """かたいツメ特性: 直接攻撃の威力を1.3倍にする。"""
    if ctx.move is not None and battle.move_executor.is_contact(ctx):
        value = common.apply_modifier(value, 5325)
    return HandlerReturn(value=value)


def メガランチャー_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """メガランチャー特性: はどう技の威力を1.5倍にする。"""
    if ctx.move is not None and ctx.move.has_label("pulse"):
        value = common.apply_modifier(value, 6144)
    return HandlerReturn(value=value)


def パンクロック_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """パンクロック特性: 音技の威力を1.3倍にする。"""
    if ctx.move is not None and ctx.move.has_label("sound"):
        value = common.apply_modifier(value, 5325)
    return HandlerReturn(value=value)


def すなのちから_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すなのちから特性: すなあらし中の岩/地面/鋼技の威力を1.3倍にする。"""
    if ctx.move is None:
        return HandlerReturn(value=value)
    active = battle.weather
    if active is None or active.name != "すなあらし":
        return HandlerReturn(value=value)
    if ctx.move.type not in ["いわ", "じめん", "はがね"]:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 5325))


def どくぼうそう_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """どくぼうそう特性: どく状態時のどく特殊技威力を1.5倍にする。"""
    if not (ctx.attacker.has_ailment("どく") or ctx.attacker.has_ailment("もうどく")):
        return HandlerReturn(value=value)
    if ctx.move is None or ctx.move.type != "どく":
        return HandlerReturn(value=value)
    if not common.is_special_move(battle, ctx):
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 6144))


def ねつぼうそう_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ねつぼうそう特性: やけど状態時のほのお特殊技威力を1.5倍にする。"""
    if not ctx.attacker.has_ailment("やけど"):
        return HandlerReturn(value=value)
    if ctx.move is None or ctx.move.type != "ほのお":
        return HandlerReturn(value=value)
    if not common.is_special_move(battle, ctx):
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 6144))


def アナライズ_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """アナライズ特性: 行動が後になったターンの技威力を1.3倍にする。"""
    if ctx.defender is None:
        return HandlerReturn(value=value)
    defender_player = battle.find_player(ctx.defender)
    acted_before = ctx.defender.executed_move is not None or defender_player.has_switched
    if acted_before:
        return HandlerReturn(value=common.apply_modifier(value, 5325))
    return HandlerReturn(value=value)


def こんじょう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """こんじょう特性: 状態異常時に物理技の攻撃補正を1.5倍にする。"""
    if not ctx.attacker.ailment.is_active:
        return HandlerReturn(value=value)
    if not common.is_physical_move(battle, ctx):
        return HandlerReturn(value=value)
    if ctx.move.name in ["イカサマ", "ボディプレス"]:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 6144))


def こんじょう_ignore_burn_penalty(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """こんじょう特性: 状態異常時はやけどの物理半減を無効化する。"""
    if not ctx.attacker.ailment.is_active:
        return HandlerReturn(value=value)
    if not common.is_physical_move(battle, ctx):
        return HandlerReturn(value=value)
    return HandlerReturn(value=4096)


def はりこみ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はりこみ特性: 交代直後の相手に対する攻撃補正を2倍にする。"""
    if ctx.defender is None:
        return HandlerReturn(value=value)
    if battle.find_player(ctx.defender).has_switched:
        return HandlerReturn(value=common.apply_modifier(value, 8192))
    return HandlerReturn(value=value)


def しんりょくもうかげきりゅうむしのしらせ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ピンチ系特性: HP1/3以下かつ対応タイプ技で攻撃補正を1.5倍にする。"""
    if ctx.move is None:
        return HandlerReturn(value=value)
    if ctx.attacker.hp * 3 > ctx.attacker.max_hp:
        return HandlerReturn(value=value)

    required_type = {
        "しんりょく": "くさ",
        "もうか": "ほのお",
        "げきりゅう": "みず",
        "むしのしらせ": "むし",
    }.get(ctx.attacker.ability.orig_name)

    if ctx.move.type != required_type:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 6144))


def いわはこび_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いわはこび特性: いわ技の攻撃補正を1.5倍にする。"""
    if ctx.move is not None and ctx.move.type == "いわ":
        value = common.apply_modifier(value, 6144)
    return HandlerReturn(value=value)


def はがねつかい_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はがねつかい特性: はがね技の攻撃補正を1.5倍にする。"""
    if ctx.move is not None and ctx.move.type == "はがね":
        value = common.apply_modifier(value, 6144)
    return HandlerReturn(value=value)


def はがねのせいしん_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はがねのせいしん特性: はがね技の威力を1.5倍にする。"""
    if ctx.move is not None and ctx.move.type == "はがね":
        return HandlerReturn(value=common.apply_modifier(value, 6144))
    return HandlerReturn(value=value)


def りゅうのあぎと_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """りゅうのあぎと特性: ドラゴン技の攻撃補正を1.5倍にする。"""
    if ctx.move is not None and ctx.move.type == "ドラゴン":
        value = common.apply_modifier(value, 6144)
    return HandlerReturn(value=value)


def ごりむちゅう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ごりむちゅう特性: 物理技の攻撃補正を1.5倍にする。"""
    if not common.is_physical_move(battle, ctx):
        return HandlerReturn(value=value)
    if ctx.move.name in ["イカサマ", "ボディプレス"]:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 6144))


def トランジスタ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """トランジスタ特性: でんき技の攻撃補正を1.3倍にする。"""
    if ctx.move is not None and ctx.move.type == "でんき":
        return HandlerReturn(value=common.apply_modifier(value, 5325))
    return HandlerReturn(value=value)


def ひひいろのこどう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ひひいろのこどう特性: はれ中の攻撃補正を1.33倍にする。"""
    active = battle.weather
    if active is not None and active.name == "はれ":
        return HandlerReturn(value=common.apply_modifier(value, 5461))
    return HandlerReturn(value=value)


def ハドロンエンジン_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ハドロンエンジン特性: エレキフィールド中の攻撃補正を1.33倍にする。"""
    if battle.terrain.name == "エレキフィールド":
        return HandlerReturn(value=common.apply_modifier(value, 5461))
    return HandlerReturn(value=value)


def スロースタート_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """スロースタート特性: 登場ターンを記録する。"""
    ctx.source.ability.count = battle.turn
    return HandlerReturn(value=value)


def スロースタート_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """スロースタート特性: 登場から5ターンの物理攻撃補正を0.5倍にする。"""
    if battle.turn - ctx.attacker.ability.count >= 5:
        return HandlerReturn(value=value)
    if not common.is_physical_move(battle, ctx):
        return HandlerReturn(value=value)
    if ctx.move.name in ["イカサマ", "ボディプレス"]:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 2048))


def よわき_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """よわき特性: HP半分以下で攻撃補正を0.5倍にする。"""
    if ctx.attacker.hp * 2 <= ctx.attacker.max_hp:
        return HandlerReturn(value=common.apply_modifier(value, 2048))
    return HandlerReturn(value=value)


def あついしぼう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """あついしぼう特性: 炎/氷技を受けるとき攻撃補正を0.5倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if ctx.move is not None and ctx.move.type in ["ほのお", "こおり"]:
        value = common.apply_modifier(value, 2048)
    return HandlerReturn(value=value)


def たいねつ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """たいねつ特性: 炎技を受けるとき攻撃補正を0.5倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if ctx.move is not None and ctx.move.type == "ほのお":
        value = common.apply_modifier(value, 2048)
    return HandlerReturn(value=value)


def すいほう_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """すいほう特性: 水技の攻撃補正2倍、炎技被ダメ計算時の攻撃補正0.5倍。"""
    if ctx.move is None:
        return HandlerReturn(value=value)

    if ctx.attacker.ability.orig_name == "すいほう" and ctx.move.type == "みず":
        value = common.apply_modifier(value, 8192)

    if ctx.defender.ability.orig_name == "すいほう" and ctx.move.type == "ほのお" and ctx.check_def_ability_enabled(battle):
        value = common.apply_modifier(value, 2048)

    return HandlerReturn(value=value)


def きよめのしお_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """きよめのしお特性: ゴースト技を受けるとき攻撃補正を0.5倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if ctx.move is not None and ctx.move.type == "ゴースト":
        value = common.apply_modifier(value, 2048)
    return HandlerReturn(value=value)


def わざわいのおふだ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """わざわいのおふだ特性: 自分以外の攻撃補正を0.75倍にする。"""
    if ctx.attacker is ctx.defender:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 3072))


def わざわいのうつわ_modify_atk(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """わざわいのうつわ特性: 自分以外の特攻補正を0.75倍にする。"""
    if ctx.attacker is ctx.defender:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 3072))


def ファーコート_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ファーコート特性: 物理技に対する防御補正を2倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if common.is_physical_move(battle, ctx):
        return HandlerReturn(value=common.apply_modifier(value, 8192))
    return HandlerReturn(value=value)


def ふしぎなうろこ_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ふしぎなうろこ特性: 状態異常時に物理技への防御補正を1.5倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if not ctx.defender.ailment.is_active:
        return HandlerReturn(value=value)
    if common.is_physical_move(battle, ctx):
        return HandlerReturn(value=common.apply_modifier(value, 6144))
    return HandlerReturn(value=value)


def くさのけがわ_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """くさのけがわ特性: ゆき中の物理技への防御補正を1.5倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    active = battle.weather
    if active is None or active.name != "ゆき":
        return HandlerReturn(value=value)
    if common.is_physical_move(battle, ctx):
        return HandlerReturn(value=common.apply_modifier(value, 6144))
    return HandlerReturn(value=value)


def わざわいのつるぎ_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """わざわいのつるぎ特性: 自分以外の防御補正を0.75倍にする。"""
    if ctx.attacker is ctx.defender:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 3072))


def わざわいのたま_modify_def(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """わざわいのたま特性: 自分以外の特防補正を0.75倍にする。"""
    if ctx.attacker is ctx.defender:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 3072))


def いろめがね_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """いろめがね特性: いまひとつの技の最終ダメージ補正を2倍にする。"""
    if common.is_not_very_effective(battle, ctx):
        return HandlerReturn(value=common.apply_modifier(value, 8192))
    return HandlerReturn(value=value)


def スナイパー_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """スナイパー特性: 急所時の最終ダメージ補正を1.5倍にする。"""
    if getattr(ctx, "critical", False):
        return HandlerReturn(value=common.apply_modifier(value, 6144))
    return HandlerReturn(value=value)


def ブレインフォース_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ブレインフォース特性: 効果抜群時の最終ダメージ補正を1.25倍にする。"""
    if common.is_super_effective(battle, ctx):
        return HandlerReturn(value=common.apply_modifier(value, 5120))
    return HandlerReturn(value=value)


def フィルターハードロックプリズムアーマー_modify_damage(
    battle: Battle,
    ctx: BattleContext,
    value: int,
) -> HandlerReturn:
    """防御側特性: 効果抜群の技ダメージを0.75倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if common.is_super_effective(battle, ctx):
        return HandlerReturn(value=common.apply_modifier(value, 3072))
    return HandlerReturn(value=value)


def マルチスケイルファントムガード_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """防御側特性: HP満タン時の被ダメージを0.5倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if ctx.defender.hp == ctx.defender.max_hp:
        return HandlerReturn(value=common.apply_modifier(value, 2048))
    return HandlerReturn(value=value)


def こおりのりんぷん_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """こおりのりんぷん特性: 特殊技で受けるダメージを0.5倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if common.is_special_move(battle, ctx):
        return HandlerReturn(value=common.apply_modifier(value, 2048))
    return HandlerReturn(value=value)


def パンクロック_reduce_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """パンクロック特性: 音技で受けるダメージを0.5倍にする。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    if ctx.move is not None and ctx.move.has_label("sound"):
        return HandlerReturn(value=common.apply_modifier(value, 2048))
    return HandlerReturn(value=value)


def もふもふ_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """もふもふ特性: 接触技被ダメ0.5倍・炎技被ダメ2倍を適用する。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    if ctx.move is not None and battle.move_executor.is_contact(ctx):
        value = common.apply_modifier(value, 2048)
    if ctx.move is not None and ctx.move.type == "ほのお":
        value = common.apply_modifier(value, 8192)
    return HandlerReturn(value=value)


def ちからもちヨガパワー_on_calc_atk_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ちからもち・ヨガパワー特性: 物理技時の攻撃補正を2.0倍にする。"""
    move_category = battle.move_executor.get_effective_move_category(ctx.attacker, ctx.move)
    if move_category != "物理":
        return HandlerReturn(value=value)
    if ctx.move.name in ["イカサマ", "ボディプレス"]:
        return HandlerReturn(value=value)
    return HandlerReturn(value=value * 8192 // 4096)


def テクニシャン_on_calc_power_modifier(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """テクニシャン特性: 元威力60以下の技威力補正を1.5倍にする。"""
    if ctx.move.data.power is None:
        return HandlerReturn(value=value)
    if ctx.move.data.power > 60:
        return HandlerReturn(value=value)
    return HandlerReturn(value=value * 6144 // 4096)


def トレース_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トレース特性: 入場時に相手のコピー可能な特性へ変更する。"""
    mon = ctx.source
    foe = battle.foe(mon)

    copied_ability = foe.ability.name
    if not copied_ability:
        return HandlerReturn(value=value)
    if "uncopyable" in foe.ability.data.flags:
        return HandlerReturn(value=value)

    battle.set_ability(mon, copied_ability)

    idx = battle.get_player_index(mon)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "トレース", "success": True},
    )

    # コピー直後に入場時処理を再評価し、いかく等の登場時効果を即時反映する。
    battle.events.emit(Event.ON_SWITCH_IN, ctx.__class__(source=mon))
    return HandlerReturn(value=value)


def トレース_on_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トレース特性: 交代時に元の特性へ戻す。"""
    mon = ctx.source
    battle.set_ability(mon, mon.base_ability_name, refresh_enabled_states=False)
    return HandlerReturn(value=value)


def おやこあい_modify_hit_count(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """おやこあい特性: 単発攻撃技を2ヒット化する。"""
    if not ctx.move.is_attack:
        return HandlerReturn(value=value)
    if ctx.move.data.max_hits > 1:
        return HandlerReturn(value=value)
    return HandlerReturn(value=2)


def おやこあい_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """おやこあい特性: 2ヒット目のダメージを減衰させる。"""
    if ctx.hit_count < 2:
        return HandlerReturn(value=value)
    if ctx.hit_index != 2:
        return HandlerReturn(value=value)

    reduced = value // 4
    return HandlerReturn(value=reduced)


def てんねん_on_calc_atk_rank_modifier(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """てんねん特性: 防御側のとき相手の攻撃ランク補正を無視する。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    if value != 1:
        return HandlerReturn(value=1)
    return HandlerReturn(value=value)


def てんねん_on_calc_def_rank_modifier(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """てんねん特性: 攻撃側のとき相手の防御ランク補正を無視する。"""
    if value != 1:
        return HandlerReturn(value=1)
    return HandlerReturn(value=value)


def めんえき_prevent_poison(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """めんえき特性: どく・もうどく状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - どく/もうどくの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # どく・もうどく状態を防ぐ
    if value in ["どく", "もうどく"]:
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add(battle.turn, idx, LogCode.ABILITY_TRIGGERED, payload={"ability": "めんえき", "success": True})
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def クリアボディ_modify_stat(battle: Battle, ctx: BattleContext, value: dict) -> HandlerReturn:
    """クリアボディ特性: 相手による能力ランク低下を無効化する。

    自分の技や反動による能力低下は防げない。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_STAT)
            - target: クリアボディ持ちのポケモン
            - source: 能力変更の原因となったポケモン（Noneなら相手由来）
        value: ランク修正値の辞書 {stat: delta}

    Returns:
        HandlerReturn: 相手由来の低下のみ除去した値
    """
    # 自己低下（source == target または source is None）の場合は保護しない
    # 相手由来（source != target かつ source is not None）の場合のみ低下を除去
    if ctx.source is None or ctx.source == ctx.target:
        # 自己低下：何もしない
        return HandlerReturn(value=value)

    # 相手由来の低下：低下分（v < 0）を除去して上昇分（v >= 0）のみ返す
    filtered = {stat: v for stat, v in value.items() if v >= 0}
    return HandlerReturn(value=filtered)


def ノーガード_modify_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ノーガード特性: 命中判定を必中化する。

    攻撃側がノーガード、または防御側がノーガードの場合、
    命中率を None（必中）に設定する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_MODIFY_ACCURACY)
            - attacker: 攻撃側のポケモン
            - defender: 防御側のポケモン
        value: 現在の命中率

    Returns:
        HandlerReturn: None（必中化）またはそのまま
    """
    if value is None:
        return HandlerReturn(value=None)

    attacker_no_guard = ctx.attacker.ability.name == "ノーガード"
    defender_no_guard = ctx.defender.ability.name == "ノーガード"

    if attacker_no_guard or defender_no_guard:
        return HandlerReturn(value=None)

    return HandlerReturn(value=value)


def ノーてんき_check_weather_enabled(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ノーてんき特性: 天候効果を無効化する。"""
    if not value:
        return HandlerReturn(value=value)
    return HandlerReturn(value=False, stop_event=True)


def ふみん_prevent_sleep(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ふみん特性: ねむり状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - ねむりの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # ねむり状態を防ぐ
    if value == "ねむり":
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add(battle.turn, idx, LogCode.ABILITY_TRIGGERED, payload={"ability": "ふみん", "success": True})
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def マジックガード_reduce_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """マジックガード特性: 間接ダメージを無効化する。"""
    # 直接ダメージ・自己由来の特定HP変動は無効化しない。
    if ctx.hp_change_reason in {"move_damage", "pain_split", "self_attack", "self_cost"}:
        return HandlerReturn(value=value)

    return HandlerReturn(value=0)


def マジックミラー_reflect(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """マジックミラー特性: 反射対象の変化技を跳ね返す。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    reflected = ctx.move.has_label("reflectable")
    return HandlerReturn(value=reflected)


def ミラーアーマー_reflect_stat_drop(battle: Battle, ctx: BattleContext, value: dict) -> HandlerReturn:
    """ミラーアーマー特性: 相手由来の能力ランク低下を反射する。"""
    # 反射由来の低下は再反射しない（無限反射防止）
    if ctx.stat_change_reason == "ミラーアーマー":
        return HandlerReturn(value=value)
    # 自己デメリット・source 不明は反射しない
    if ctx.source is None or ctx.source is ctx.target:
        return HandlerReturn(value=value)
    # かたやぶり系で防御側特性が無効化されている場合は反射しない
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    # 低下分のみ抽出
    drops = {stat: v for stat, v in value.items() if v < 0}
    if not drops:
        return HandlerReturn(value=value)
    # 低下を source（相手）側へ反射（source を ctx.target にすることで「相手から下げられた」扱いになりまけんき等が正常発動）
    battle.modify_stats(ctx.source, drops, source=ctx.target, reason="ミラーアーマー")
    # 自分側の低下分を除去（上昇分は残す）
    filtered = {stat: v for stat, v in value.items() if v > 0}
    return HandlerReturn(value=filtered)


def ぶきよう_check_item_enabled(battle: Battle, ctx: BattleContext, should_enable: bool) -> HandlerReturn:
    """ぶきよう特性: 所持道具の効果を無効化する。"""
    if not should_enable:
        return HandlerReturn(value=should_enable)

    if ctx.source.ability.orig_name == "ぶきよう" and ctx.source.ability.enabled:
        return HandlerReturn(value=False)

    return HandlerReturn(value=should_enable)


def へんげんじざいリベロ_on_move_charge(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """へんげんじざい・リベロ: 技実行前に技タイプへ自身のタイプを変更する。"""
    if not value:
        return HandlerReturn(value=value)
    if ctx.source is None or ctx.move is None:
        return HandlerReturn(value=value)
    if ctx.source.is_terastallized:
        return HandlerReturn(value=value)
    if ctx.source.ability.activated_since_switch_in:
        return HandlerReturn(value=value)

    move_type = ctx.move.type
    if not move_type:
        return HandlerReturn(value=value)

    # 現在タイプと同じ技では発動しない。
    if ctx.source.has_type(move_type):
        return HandlerReturn(value=value)

    ctx.source.ability_override_type = move_type
    ctx.source.ability.activated_since_switch_in = True

    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": ctx.source.ability.orig_name, "success": True},
    )
    return HandlerReturn(value=value)


def やるき_prevent_sleep(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """やるき特性: ねむり状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - ねむりの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # ねむり状態を防ぐ（ふみんと同じ効果）
    if value == "ねむり":
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add(battle.turn, idx, LogCode.ABILITY_TRIGGERED, payload={"ability": "やるき", "success": True})
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def ようりょくそ_modify_speed(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ようりょくそ特性: はれ中に素早さが2倍になる。"""
    active = battle.weather
    if active is not None and active.name == "はれ":
        value *= 2
    return HandlerReturn(value=value)


def マイペース_prevent_confusion(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """マイペース特性: こんらん状態を防ぐ（揮発状態の実装が必要）。

    Note:
        こんらんは揮発状態のため、別途ON_BEFORE_APPLY_VOLATILEイベントで実装

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (False, value) - 状態異常は防がない
    """
    # 状態異常は防がない（こんらんは揮発状態で別処理）
    return HandlerReturn(value=value)


def じゅうなん_prevent_paralysis(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """じゅうなん特性: まひ状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - まひの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # まひ状態を防ぐ
    if value == "まひ":
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def みずのベール_prevent_burn(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """みずのベール特性: やけど状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - やけどの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # やけど状態を防ぐ
    if value == "やけど":
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def マグマのよろい_prevent_freeze(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """マグマのよろい特性: こおり状態を防ぐ。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (処理実行フラグ, 状態異常名)
            - こおりの場合: (True, "", stop_event=True)
            - それ以外: (False, value)
    """
    # こおり状態を防ぐ
    if value == "こおり":
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def どんかん_prevent_volatile(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    """どんかん特性: メロメロ・ちょうはつ・ゆうわく・いかくを防ぐ。

    Note:
        メロメロ・ちょうはつ・ゆうわくは揮発状態のため、
        別途ON_BEFORE_APPLY_VOLATILEイベントで実装が必要

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名

    Returns:
        HandlerReturn: (False, value) - 状態異常は防がない
    """
    if value in ["メロメロ", "ちょうはつ", "ゆうわく", "いかく"]:
        return HandlerReturn(value="", stop_event=True)  # 防いでイベント停止
    return HandlerReturn(value=value)


def おうごんのからだ_block_status_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """おうごんのからだ特性: 他のポケモンからの変化技を無効化する。

    酸化しない丈夫な黄金の体が、相手からの変化技をすべて受けつけない。
    ただし、自分が対象の変化技や場を対象とした技は防がない。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_IMMUNE)
            - target: 防御側（自分）
            - attacker: 攻撃側（相手）
            - move: 使用する技
        value: 現在の無効化状態（初期値：False）

    Returns:
        HandlerReturn: 変化技を無効化した場合True, stop_event=True
    """
    # 変化技以外は防がない
    if ctx.move.category != "変化":
        return HandlerReturn(value=value)

    # 相手対象以外（自分対象・場対象・同一対象）は防がない。
    if not ctx.is_foe_target:
        return HandlerReturn(value=value)

    # かたやぶり系で防御側特性が無視される場合は発動しない。
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    # 自身がおうごんのからだでない場合は防がない。
    if ctx.target.ability.orig_name != "おうごんのからだ":
        return HandlerReturn(value=value)

    # ログ出力
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "おうごんのからだ", "success": True}
    )

    return HandlerReturn(value=True, stop_event=True)


def かがくへんかガス_check_enabled(battle: Battle, ctx: BattleContext, should_enable: bool) -> HandlerReturn:
    """かがくへんかガス無効化判定（priority=10）。

    かがくへんかガスが場に発動していると、以下を除く特性を無効化する：
    - かがくへんかガス自身
    - undeniable フラグを持つ特性（別ハンドラで復元）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_ABILITY_ENABLED)
            - source: 判定対象のポケモン
        should_enable: 現在の有効化状態

    Returns:
        HandlerReturn: ガス発動中で無効化対象なら False、それ以外は should_enable をそのまま返す
    """
    # 判定対象のポケモンが既に無効化されていたら、その状態を保持
    if not should_enable:
        return HandlerReturn(value=should_enable)

    # かがくへんかガスが発動中か判定
    actives = [mon for mon in battle.actives if mon is not None]
    gas_active = any(
        mon.alive and
        mon.ability.orig_name == "かがくへんかガス" and
        not mon.has_volatile("とくせいなし")
        for mon in actives
    )

    if not gas_active:
        return HandlerReturn(value=should_enable)

    # ガス発動中なので、自身がかがくへんかガスでない限り、無効化を検討
    source_ability = ctx.source.ability
    if source_ability.orig_name == "かがくへんかガス":
        # かがくへんかガス自身は無効化されない
        return HandlerReturn(value=True)

    # それ以外は無効化
    return HandlerReturn(value=False)


def undeniable_check_enabled(battle: Battle, ctx: BattleContext, should_enable: bool) -> HandlerReturn:
    """undeniable フラグ保護判定（priority=20）。

    undeniable フラグを持つ特性は、かがくへんかガスなどによる無効化を
    受けない。このハンドラはガス判定の後に評価され、該当特性を保護する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_ABILITY_ENABLED)
            - source: 判定対象のポケモン
        should_enable: 現在の有効化状態

    Returns:
        HandlerReturn: undeniable フラグ持ちなら True（保護）、それ以外は should_enable をそのまま返す
    """
    source_ability = ctx.source.ability
    if "undeniable" in source_ability.data.flags:
        return HandlerReturn(value=True)
    return HandlerReturn(value=should_enable)


def announce_ability_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """汎用: 登場時に特性発動ログを記録する (ON_SWITCH_IN)。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_SWITCH_IN)
            - source: 登場したポケモン
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 変更なし
    """
    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": ctx.source.ability.name, "success": True}
    )
    return HandlerReturn(value=value)


def かたやぶり_check_def_ability_enabled(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """かたやぶり系特性: 無視できる防御側特性の無視フラグを立てる。

    かたやぶり / ターボブレイズ / テラボルテージ で共用。
    防御側が とくせいガード を持つ場合は、とくせいガード側ハンドラ (priority=200) が
    値を元に戻すことで無視が打ち消される。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト (ON_CHECK_DEF_ABILITY_ENABLED)
            - attacker: かたやぶり系特性所持ポケモン
            - defender: 防御側のポケモン
        value: 現在の防御側特性有効フラグ

    Returns:
        HandlerReturn: 無視対象なら False、それ以外は value
    """
    if "mold_breaker_ignorable" in ctx.defender.ability.data.flags:
        return HandlerReturn(value=False)
    return HandlerReturn(value=value)


def ばけのかわ_modify_damage(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ばけのかわ特性: 初回の攻撃技ダメージを防ぐ。"""
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)

    # ばけのかわを消費して、このヒットの攻撃ダメージを0にする。
    battle.set_ability_enabled(ctx.defender, False)
    battle.modify_hp(ctx.defender, r=-1/8)

    idx = battle.get_player_index(ctx.defender)
    battle.event_logger.add(
        battle.turn,
        idx,
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ばけのかわ", "success": True},
    )
    return HandlerReturn(value=0)


# ===== がんじょう =====

def がんじょう_block_ohko(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """がんじょう特性: 一撃必殺技を無効化する。(ON_CHECK_IMMUNE / subject_spec="target:self")"""
    if ctx.move is None or not ctx.move.has_label("ohko"):
        return HandlerReturn(value=value)
    if not ctx.check_def_ability_enabled(battle):
        return HandlerReturn(value=value)
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "がんじょう", "success": True},
    )
    return HandlerReturn(value=True, stop_event=True)


def がんじょう_survive_lethal(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """がんじょう特性: HP満タン時の致死ダメージをHP1残しに補正する。(ON_BEFORE_DAMAGE_APPLY / subject_spec="target:self")"""
    if ctx.hp_change_reason != "move_damage":
        return HandlerReturn(value=value)
    target = ctx.target
    if target.hp < target.max_hp:
        return HandlerReturn(value=value)
    if target.hp + value > 0:
        return HandlerReturn(value=value)
    idx = battle.get_player_index(target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "がんじょう", "success": True},
    )
    return HandlerReturn(value=-target.hp+1)


# ===== ちからずく =====

def ちからずく_modify_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """ちからずく特性: 追加効果ありの技の威力を 1.3 倍にする。(ON_CALC_POWER_MODIFIER / subject_spec="attacker:self")"""
    if ctx.move is None:
        return HandlerReturn(value=value)
    if not ctx.move.data.move_secondary:
        return HandlerReturn(value=value)
    return HandlerReturn(value=common.apply_modifier(value, 5325))


def ちからずく_on_move_secondary(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """ちからずく特性: 追加効果対象技の追加効果確率を 0 にする。"""
    if ctx.move is None or not ctx.move.data.move_secondary:
        return HandlerReturn(value=value)
    return HandlerReturn(value=0.0)


def てんのめぐみ_on_move_secondary(battle: Battle, ctx: BattleContext, value: float) -> HandlerReturn:
    """てんのめぐみ特性: 追加効果対象技の追加効果確率を2倍にする。"""
    if ctx.move is None or not ctx.move.data.move_secondary:
        return HandlerReturn(value=value)
    return HandlerReturn(value=min(1.0, value * 2))


# ===== マルチタイプ / ARシステム 共通 =====


def _apply_multitype(mon, item_table: dict[str, str]) -> None:
    """道具に応じてポケモンのタイプを変更する共通ロジック。"""
    item_name = mon.item.orig_name if mon.has_item() else ""
    mon.ability_override_type = item_table.get(item_name)


def マルチタイプ_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マルチタイプ特性: 登場時にプレートに合わせてタイプを変更する。"""
    _apply_multitype(ctx.source, PLATE_TO_TYPE)
    idx = battle.get_player_index(ctx.source)
    if ctx.source.ability_override_type is not None:
        battle.event_logger.add(
            battle.turn, idx, LogCode.ABILITY_TRIGGERED,
            payload={"ability": "マルチタイプ", "success": True},
        )
    return HandlerReturn(value=value)


def マルチタイプ_prevent_item_change(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """マルチタイプ特性: プレートの奪取・交換を防ぐ。(ON_CHECK_ITEM_CHANGE / subject_spec="target:self")"""
    if not value:
        return HandlerReturn(value=value)
    if ctx.source == ctx.target:
        return HandlerReturn(value=value)
    # 持ち物がプレートの場合のみ保護
    item_name = ctx.target.item.orig_name if ctx.target.has_item() else ""
    if item_name not in PLATE_TO_TYPE:
        return HandlerReturn(value=value)
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "マルチタイプ", "success": True},
    )
    return HandlerReturn(value=False, stop_event=True)


def ARシステム_on_switch_in(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ARシステム特性: 登場時にメモリに合わせてタイプを変更する。"""
    _apply_multitype(ctx.source, MEMORY_TO_TYPE)
    idx = battle.get_player_index(ctx.source)
    if ctx.source.ability_override_type is not None:
        battle.event_logger.add(
            battle.turn, idx, LogCode.ABILITY_TRIGGERED,
            payload={"ability": "ARシステム", "success": True},
        )
    return HandlerReturn(value=value)


def ARシステム_prevent_item_change(battle: Battle, ctx: BattleContext, value: bool) -> HandlerReturn:
    """ARシステム特性: メモリの奪取・交換を防ぐ。(ON_CHECK_ITEM_CHANGE / subject_spec="target:self")"""
    if not value:
        return HandlerReturn(value=value)
    if ctx.source == ctx.target:
        return HandlerReturn(value=value)
    item_name = ctx.target.item.orig_name if ctx.target.has_item() else ""
    if item_name not in MEMORY_TO_TYPE:
        return HandlerReturn(value=value)
    idx = battle.get_player_index(ctx.target)
    battle.event_logger.add(
        battle.turn, idx, LogCode.ABILITY_TRIGGERED,
        payload={"ability": "ARシステム", "success": True},
    )
    return HandlerReturn(value=False, stop_event=True)
