"""技関連のイベントハンドラ関数を提供するモジュール。

技の実行に関連するハンドラ関数を提供します。
PP消費、交代技、吹き飛ばし技などの処理を行います。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext
    from jpoke.utils.type_defs import RoleSpec, AilmentName, Stat

from functools import partial

from jpoke.enums import Event, Interrupt, LogCode
from jpoke.core import Handler, HandlerReturn
from . import common


class MoveHandler(Handler):
    """技ハンドラの派生クラス。

    技の効果を実装する際に使用します。
    """

    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "attacker:self",
                 priority: int = 100):
        """MoveHandlerを初期化する。

        Args:
            func: イベント発生時に呼ばれる処理関数
            subject_spec: ハンドラの対象を指定するロール
            priority: ハンドラの優先度
        """
        super().__init__(
            func=func,
            source="move",
            subject_spec=subject_spec,
            priority=priority
        )


def pivot(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """交代技の効果を発動する。

    とんぼがえり、ボルトチェンジなどの交代技で、攻撃後に交代を行います。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 交代が可能な場合はTrue、不可能な場合はFalse
    """
    player = battle.get_player(ctx.attacker)
    success = bool(battle.get_available_switch_commands(player))
    if success:
        player.interrupt = Interrupt.PIVOT
    return HandlerReturn(value=success)


def on_blow_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の効果を防げるかを判定する。"""
    value = battle.events.emit(Event.ON_TRY_BLOW, ctx, value)
    if not value:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload={"reason": "強制交代無効"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def blow(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の効果を発動する。

    ほえる、ふきとばしなどで、相手を強制的に交代させます。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 吹き飛ばしが成功した場合はTrue、失敗した場合はFalse
    """
    player = battle.get_player(ctx.defender)
    commands = battle.get_available_switch_commands(player)
    success = bool(commands)
    if success:
        command = battle.random.choice(commands)
        battle.run_switch(player, player.team[command.index])
    return HandlerReturn(value=success)


# ===== 技個別のハンドラ =====


def ohko_modify_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """一撃必殺技の確定ダメージを計算する。"""
    return HandlerReturn(value=ctx.defender.hp)


def HP_ratio_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """対象の現在HPの半分を与える固定ダメージを計算する。"""
    return HandlerReturn(value=max(1, ctx.defender.hp // 2))


def いたみわけ_equalize_hp(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """両者の現在HPを平均化する。"""
    shared_hp = (ctx.attacker.hp + ctx.defender.hp) // 2

    battle.modify_hp(
        ctx.attacker,
        v=shared_hp - ctx.attacker.hp,
        reason="pain_split",
    )
    battle.modify_hp(
        ctx.defender,
        v=shared_hp - ctx.defender.hp,
        reason="pain_split",
    )
    return HandlerReturn(value=value)


def いのちがけ_pay_hp(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """いのちがけ発動前にHPを支払い、元のHPをコンテキストに保存する。"""
    ctx.hp_cost = ctx.attacker.hp
    battle.modify_hp(ctx.attacker, v=-ctx.attacker.hp, reason="self_cost")
    return HandlerReturn(value=value)


def いのちがけ_modify_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """いのちがけの固定ダメージを計算する（支払い前のHPを使用）。"""
    return HandlerReturn(value=getattr(ctx, "hp_cost", 0))


def level_fixed_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """使用者レベルと同値の固定ダメージを計算する。"""
    return HandlerReturn(value=ctx.attacker.level)


def がむしゃら_modify_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """がむしゃらのダメージを計算する。"""
    value = max(0, ctx.defender.hp - ctx.attacker.hp)
    return HandlerReturn(value=value)


def かみなり_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かみなりの天候による命中率補正。

    雨: 必中
    晴れ: 50%

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather
    if weather is not None and weather.rainy:
        return HandlerReturn(value=None)  # 必中
    elif weather is not None and weather.sunny:
        return HandlerReturn(value=50)
    return HandlerReturn(value=value)


def きあいパンチ_check_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """きあいパンチの発動可否を判定する。

    行動前に実際の攻撃ダメージを受けていた場合は不発になる。
    """
    if ctx.attacker.hits_taken > 0:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "きあいパンチ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ぼうふう_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ぼうふうの天候による命中率補正。

    雨: 必中
    晴れ: 50%

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather
    if weather is not None and weather.rainy:
        return HandlerReturn(value=None)  # 必中
    elif weather is not None and weather.sunny:
        return HandlerReturn(value=50)
    return HandlerReturn(value=value)


def _can_apply_item_hit_effect(ctx: BattleContext) -> bool:
    """命中後の持ち物操作効果が適用可能かを判定する。"""
    return ctx.move_damage > 0


def すりかえ_swap_items(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """すりかえ・トリックの持ち物交換効果。"""
    success = battle.swap_items(ctx.attacker, ctx.defender, move=ctx.move)
    return HandlerReturn(value=success)


def ついばむ_berry_steal(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ついばむ・むしくいのきのみ奪取効果。"""
    if not _can_apply_item_hit_effect(ctx):
        return HandlerReturn(value=False)
    if ctx.attacker.has_item():
        return HandlerReturn(value=False)
    if not common.is_berry_item(ctx.defender.item.name):
        return HandlerReturn(value=False)

    success = battle.take_item(ctx.attacker, ctx.defender, move=ctx.move)
    return HandlerReturn(value=success)


def どろぼう_steal_item(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """どろぼう・ほしがるの持ち物奪取効果。"""
    if not _can_apply_item_hit_effect(ctx):
        return HandlerReturn(value=False)
    if ctx.attacker.has_item():
        return HandlerReturn(value=False)

    success = battle.take_item(ctx.attacker, ctx.defender, move=ctx.move)
    return HandlerReturn(value=success)


def はたきおとす_power(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """はたきおとすの持ち物所持時1.5倍補正。"""
    if ctx.defender.has_item():
        value = value * 6144 // 4096
    return HandlerReturn(value=value)


def はたきおとす_remove_item(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """はたきおとすの持ち物除去効果。"""
    if not _can_apply_item_hit_effect(ctx):
        return HandlerReturn(value=False)

    success = battle.remove_item(ctx.attacker, ctx.defender, move=ctx.move)
    return HandlerReturn(value=success)


def やきつくす_remove_berry(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """やきつくすのきのみ焼却効果。"""
    if ctx.move_damage <= 0:
        return HandlerReturn(value=False)
    if not common.is_berry_item(ctx.defender.item.name):
        return HandlerReturn(value=False)

    success = battle.remove_item(ctx.attacker, ctx.defender, move=ctx.move, reason="burn")
    return HandlerReturn(value=success)


def ふしょくガス_remove_item(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ふしょくガスの持ち物除去効果。"""
    success = battle.remove_item(
        ctx.attacker,
        ctx.defender,
        move=ctx.move,
        reason="gas",
        check_on_empty=True,
    )
    return HandlerReturn(value=success)


def ふぶき_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ふぶきの天候による命中率補正。

    雪: 必中

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather_manager.current.name
    if weather == "ゆき":
        return HandlerReturn(value=None)  # 必中
    return HandlerReturn(value=value)


def オーラぐるま_check_move_type(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """オーラぐるまのタイプを判定する。"""
    if ctx.source and ctx.source.ability.is_hangry:
        return HandlerReturn(value="あく")
    return HandlerReturn(value=value)


def ちいさくなる_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ちいさくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"EVA": 2}, source=mon)
    battle.volatile_manager.apply(mon, "ちいさくなる")
    return HandlerReturn(value=value)


def テラバースト_modify_move_type(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """テラバーストのタイプを判定する。"""
    mon = ctx.attacker
    if mon.terastallized:
        value = mon.active_tera_type
    return HandlerReturn(value=value)


def テラバースト_modify_move_category(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """テラバーストの分類（物理/特殊）を判定する。"""
    mon = ctx.attacker
    if mon.terastallized:
        atk = mon.ranked_stats["A"]
        spa = mon.ranked_stats["C"]
        value = "物理" if atk > spa else "特殊"
    return HandlerReturn(value=value)


def テラバースト_stellar_power(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ステラテラスタル状態ではテラバーストの威力が100になる補正。"""
    if ctx.attacker.active_tera_type == 'ステラ':
        value = 5120  # = 4096 * 100 / 80
    return HandlerReturn(value=value)


def テラバースト_stellar_stat_drop(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ステラテラスタル時のテラバースト発動後の攻撃・特攻-1段階効果。"""
    mon = ctx.attacker
    if mon and mon.active_tera_type == 'ステラ':
        battle.modify_stats(mon, {"A": -1, "C": -1}, source=mon)
    return HandlerReturn(value=value)


def _check_はやてがえし_condition(battle: Battle, ctx: BattleContext) -> bool:
    """はやてがえしの発動条件を判定する。

    相手が未行動かつ優先攻撃技を選択している時のみ成功する。
    """
    defender_player = battle.get_player(ctx.defender)

    # 相手が既に行動済み（予約コマンドが消費済み）なら失敗。
    if not defender_player.reserved_commands:
        return False

    defender_command = defender_player.reserved_commands[0]
    defender_move = battle.command_to_move(defender_player, defender_command)

    # 優先度が上がっていても変化技には失敗する。
    if not defender_move.is_attack:
        return False

    priority = battle.speed_calculator.calc_move_priority(ctx.defender, defender_move)
    if priority <= 0:
        return False

    return True


def はやてがえし_try_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """はやてがえしの発動条件を判定する。

    相手が未行動かつ優先攻撃技を選択している時のみ成功する。
    """
    if not _check_はやてがえし_condition(battle, ctx):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "はやてがえし"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def まるくなる_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まるくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"B": 1}, source=mon)
    battle.volatile_manager.apply(mon, "まるくなる")
    return HandlerReturn(value=value)


def みがわり_check(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりが使用可能かを判定する。"""
    mon = ctx.attacker
    if (
        mon.has_volatile("みがわり")
        or mon.hp <= mon.max_hp // 4
    ):
        battle.add_event_log(mon, LogCode.MOVE_FAILED,
                             payload={"reason": "みがわり"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def みがわり_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりの効果を発動する。"""
    mon = ctx.attacker
    battle.volatile_manager.apply(mon, "みがわり", hp=mon.max_hp // 4)
    return HandlerReturn(value=value)
