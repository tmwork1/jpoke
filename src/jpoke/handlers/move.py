"""技関連のイベントハンドラ関数を提供するモジュール。

技の実行に関連するハンドラ関数を提供します。
PP消費、交代技、吹き飛ばし技などの処理を行います。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.type_defs import RoleSpec, LogPolicy
from jpoke.utils.enums import Event, Interrupt
from jpoke.core.event import Handler, EventContext, HandlerReturn


class MoveHandler(Handler):
    """技ハンドラの派生クラス。

    source_type="move" と log="never" をデフォルトとして設定します。
    技の効果を実装する際に使用します。
    """

    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "attacker:self",
                 log: LogPolicy = "never",
                 log_text: str | None = None,
                 priority: int = 100):
        """MoveHandlerを初期化する。

        Args:
            func: イベント発生時に呼ばれる処理関数
            subject_spec: ログ出力対象のロール指定
            log: ログ出力ポリシー ("always", "on_success", "never")
            log_text: カスタムログテキスト（Noneの場合は技名を使用）
            priority: ハンドラの優先度
        """
        super().__init__(func, subject_spec, "move", log, log_text, priority)


def consume_pp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """技のPPを消費する。

    技を使用した際にPPを減らします。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue（成功）を返す
    """
    v = battle.events.emit(Event.ON_CHECK_PP_CONSUMED, ctx, 1)
    ctx.move.pp = max(0, ctx.move.pp - v)
    battle.add_event_log(ctx.attacker, f"PP -{v}")
    ctx.attacker.pp_consumed_moves.append(ctx.move)
    return HandlerReturn(True)


def pivot(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """交代技の効果を発動する。

    とんぼがえり、ボルトチェンジなどの交代技で、攻撃後に交代を行います。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 交代が可能な場合はTrue、不可能な場合はFalse
    """
    player = battle.find_player(ctx.attacker)
    success = bool(battle.get_available_switch_commands(player))
    if success:
        player.interrupt = Interrupt.PIVOT
    return HandlerReturn(success)


def blow(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の効果を発動する。

    ほえる、ふきとばしなどで、相手を強制的に交代させます。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
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
    return HandlerReturn(success)


def apply_flinch(battle: Battle, ctx: EventContext, value: Any, prob: float = 0.3) -> HandlerReturn:
    """ひるみを付与する。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）
        prob: ひるみ発動確率

    Returns:
        HandlerReturn: ひるみ付与に成功したらTrue
    """
    if prob < 1:
        if battle.test_option.ailment_trigger_rate is not None:
            triggered = battle.test_option.ailment_trigger_rate >= prob
        else:
            triggered = battle.random.random() < prob
        if not triggered:
            return HandlerReturn(False)

    target = ctx.defender
    if not target or target.hp <= 0:
        return HandlerReturn(False)

    if target.ability.orig_name == "せいしんりょく":
        return HandlerReturn(False)

    success = target.apply_volatile(battle.events, "ひるみ", source=ctx.attacker)
    return HandlerReturn(success)


def apply_hp_drain(battle: Battle, ctx: EventContext, value: Any, rate: float = 0.5) -> HandlerReturn:
    """HP吸収効果を適用する（ON_HIT イベントで呼ばれる）。

    技のダメージの指定割合分だけ、攻撃側のHPを回復する。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト（damage フィールドを使用）
        value: イベント値（未使用）
        rate: 吸収率（デフォルト50% = 0.5）

    Returns:
        HandlerReturn: 吸収成功時はTrue、失敗時はFalse
    """
    attacker = ctx.attacker
    damage = ctx.damage

    if not attacker or not damage:
        return HandlerReturn(False)

    # 吸収量を計算
    absorption = max(1, int(damage * rate))

    # HP回復
    attacker.hp = min(attacker.hp + absorption, attacker.max_hp)
    battle.add_event_log(attacker, f"HPを{absorption}回復した！")

    return HandlerReturn(True)


def apply_recoil(battle: Battle, ctx: EventContext, value: Any, rate: float = 1/3) -> HandlerReturn:
    """反動ダメージを適用する（ON_HIT イベントで呼ばれる）。

    技のダメージの指定割合分だけ、攻撃側のHPをダメージする。

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト（damage フィールドを使用）
        value: イベント値（未使用）
        rate: 反動率（デフォルト33% = 1/3）

    Returns:
        HandlerReturn: 反動適用時はTrue
    """
    attacker = ctx.attacker
    damage = ctx.damage

    if not attacker or not damage:
        return HandlerReturn(True)

    # 反動ダメージを計算（最低1）
    recoil_damage = max(1, int(damage * rate))

    # リコイルダメージを適用
    attacker.hp = max(0, attacker.hp - recoil_damage)
    battle.add_event_log(attacker, f"反動ダメージで{recoil_damage}のダメージ！")

    return HandlerReturn(True)


# ===== 命中率補正ハンドラ =====

def acc_rank_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """命中率ランクによる命中率補正。

    攻撃側の命中率ランクが命中判定に影響します。
    ランク修正値テーブル: -6: ×1/3, -5: ×3/8, ..., 0: ×1.0, +1: ×4/3, ..., +6: ×3

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト（attacker.rank['cmbなど]）
        value: 現在の命中率

    Returns:
        HandlerReturn: ランクがあれば補正値を返す、なければFalse
    """
    if not ctx.attacker:
        return HandlerReturn(False, value)

    acc_rank = ctx.attacker.rank.get("acc", 0)
    if acc_rank == 0:
        return HandlerReturn(False, value)

    # ランク補正テーブル（4096基準）
    rank_modifiers = {
        -6: 1365,    # 1/3
        -5: 1638,    # 3/8
        -4: 2048,    # 1/2
        -3: 2730,    # 2/3
        -2: 3413,    # 5/6
        -1: 3686,    # 9/10
        0:  4096,    # 1.0
        1:  5461,    # 4/3
        2:  6144,    # 1.5
        3:  5461,    # 4/3（等倍基準）
        4:  5461,    # 4/3
        5:  9830,    # 2.4（×1/5基準）
        6:  12288,   # 3.0
    }

    modified_acc_rank = max(-6, min(6, acc_rank))
    modifier = rank_modifiers.get(modified_acc_rank, 4096)
    modified_value = value * modifier // 4096

    return HandlerReturn(True, modified_value)


def eva_rank_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """回避率ランクによる命中率補正。

    防御側の回避率ランクが命中判定に影響します。
    ランク修正値テーブル: +6: ×1/3, +5: ×3/8, ..., 0: ×1.0, -1: ×4/3, ..., -6: ×3

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト（defender.rank['eva']）
        value: 現在の命中率

    Returns:
        HandlerReturn: ランクがあれば補正値を返す、なければFalse
    """
    if not ctx.defender:
        return HandlerReturn(False, value)

    eva_rank = ctx.defender.rank.get("eva", 0)
    if eva_rank == 0:
        return HandlerReturn(False, value)

    # ランク補正テーブル（回避は逆向き）
    rank_modifiers = {
        -6: 12288,   # 3.0（命中率3倍＝回避1/3のため）
        -5: 9830,    # 2.4
        -4: 5461,    # 4/3
        -3: 5461,    # 4/3
        -2: 6144,    # 1.5
        -1: 5461,    # 4/3
        0:  4096,    # 1.0
        1:  3686,    # 9/10
        2:  3413,    # 5/6
        3:  2730,    # 2/3
        4:  2048,    # 1/2
        5:  1638,    # 3/8
        6:  1365,    # 1/3
    }

    modified_eva_rank = max(-6, min(6, eva_rank))
    modifier = rank_modifiers.get(modified_eva_rank, 4096)
    modified_value = value * modifier // 4096

    return HandlerReturn(True, modified_value)


# ===== 技個別の命中率補正ハンドラ =====

def かみなり_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かみなりの天候による命中率補正。

    雨: 必中
    晴れ: 50%

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather_mgr.current.name
    if weather == "あめ":
        return HandlerReturn(True, None)  # 必中
    elif weather == "はれ":
        return HandlerReturn(True, 50)
    return HandlerReturn(False, value)


def ぼうふう_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぼうふうの天候による命中率補正。

    雨: 必中
    晴れ: 50%

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather_mgr.current.name
    if weather == "あめ":
        return HandlerReturn(True, None)  # 必中
    elif weather == "はれ":
        return HandlerReturn(True, 50)
    return HandlerReturn(False, value)


def ふぶき_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふぶきの天候による命中率補正。

    雪: 必中

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather_mgr.current.name
    if weather == "ゆき":
        return HandlerReturn(True, None)  # 必中
    return HandlerReturn(False, value)
