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

    source_type="move" をデフォルトとして設定します。
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
        super().__init__(func, subject_spec, "move", priority)


def consume_pp(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """技のPPを消費する。

    技を使用した際にPPを減らします。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue（成功）を返す
    """
    v = battle.events.emit(Event.ON_CHECK_PP_CONSUMED, ctx, 1)
    ctx.move.pp = max(0, ctx.move.pp - v)
    battle.add_event_log(ctx.attacker,  LogCode.CONSUME_PP,
                         payload={"move": ctx.move.name, "value": v})
    return HandlerReturn()


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
    player = battle.find_player(ctx.attacker)
    success = bool(battle.get_available_switch_commands(player))
    if success:
        player.interrupt = Interrupt.PIVOT
    return HandlerReturn(value=success)


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
    player = battle.find_player(ctx.defender)
    commands = battle.get_available_switch_commands(player)
    success = bool(commands)
    if success:
        command = battle.random.choice(commands)
        battle.run_switch(player, player.team[command.idx])
    return HandlerReturn(value=success)


# ===== 技個別のハンドラ =====


def _is_type_immune(battle: Battle, ctx: BattleContext) -> bool:
    """タイプ相性で無効化されるかどうかを判定する。"""
    type_modifier = battle.damage_calculator.calc_def_type_modifier(ctx=ctx)
    if type_modifier == 0:
        battle.add_event_log(
            ctx.defender,
            LogCode.MOVE_IMMUNE,
            payload={"move": ctx.move.name, "reason": "タイプ"},
        )
        return True
    return False


def HP_ratio_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """対象の現在HPの半分を与える固定ダメージを計算する。"""
    if _is_type_immune(battle, ctx):
        return HandlerReturn(value=0)

    return HandlerReturn(value=max(1, ctx.defender.hp // 2))


def いのちがけ_modify_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """いのちがけの固定ダメージを計算する。"""
    if _is_type_immune(battle, ctx):
        return HandlerReturn(value=0)

    return HandlerReturn(value=ctx.attacker.hp)


def いのちがけ_hit(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """いのちがけ命中時に使用者をひんしにする。"""
    substitute_damage = getattr(ctx, "substitute_damage", 0)
    if ctx.damage > 0 or substitute_damage > 0:
        battle.modify_hp(ctx.attacker, v=-ctx.attacker.hp, reason="いのちがけ")
    return HandlerReturn()


def level_fixed_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """使用者レベルと同値の固定ダメージを計算する。"""
    if _is_type_immune(battle, ctx):
        return HandlerReturn(value=0)

    return HandlerReturn(value=ctx.attacker.level)


def がむしゃら_modify_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """がむしゃらの固定ダメージを計算する。"""
    if _is_type_immune(battle, ctx):
        return HandlerReturn(value=0)

    return HandlerReturn(value=max(0, ctx.defender.hp - ctx.attacker.hp))


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
    weather = battle.weather_manager.current.name
    if weather == "あめ":
        return HandlerReturn(value=None)  # 必中
    elif weather == "はれ":
        return HandlerReturn(value=50)
    return HandlerReturn(value=value)


def きあいパンチ_check_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """きあいパンチの発動可否を判定する。

    行動前に実際の攻撃ダメージを受けていた場合は不発になる。
    """
    if ctx.attacker.hits_taken > 0:
        battle.add_event_log(
            ctx.attacker,
            LogCode.ACTION_BLOCKED,
            payload={"reason": "きあいパンチ"},
        )
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
    weather = battle.weather_manager.current.name
    if weather == "あめ":
        return HandlerReturn(value=None)  # 必中
    elif weather == "はれ":
        return HandlerReturn(value=50)
    return HandlerReturn(value=value)


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


def はやてがえし_check_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """はやてがえしの発動条件を判定する。

    相手が未行動かつ優先攻撃技を選択している時のみ成功する。
    """
    defender_player = battle.find_player(ctx.defender)

    # 相手が既に行動済み（予約コマンドが消費済み）なら失敗。
    if not defender_player.reserved_commands:
        return HandlerReturn(value=False, stop_event=True)

    defender_command = defender_player.reserved_commands[0]
    is_move_command = defender_command.is_move_execution()
    if not is_move_command:
        return HandlerReturn(value=False, stop_event=True)

    defender_move = battle.command_to_move(defender_player, defender_command)

    # 優先度が上がっていても変化技には失敗する。
    if not defender_move.is_attack:
        return HandlerReturn(value=False, stop_event=True)

    priority = battle.speed_calculator.calc_move_priority(ctx.defender, defender_move)
    if priority <= 0:
        return HandlerReturn(value=False, stop_event=True)

    return HandlerReturn(value=value)
