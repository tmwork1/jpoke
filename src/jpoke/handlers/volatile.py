"""揮発状態ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
from functools import partial
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext
    from jpoke.model import Pokemon

from jpoke.utils.type_defs import RoleSpec, VolatileName, DisabledReason
from jpoke.utils.constants import HIDDEN_MOVE_ALLOWED_MOVES
from jpoke.enums import Event, Command, LogCode
from jpoke.core import Handler, HandlerReturn
from . import common


class VolatileHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "source:self",
                 priority: int = 100,
                 once: bool = False):
        super().__init__(
            func=func,
            source="volatile",
            subject_spec=subject_spec,
            priority=priority,
            once=once
        )


def tick_volatile(battle: Battle,
                  ctx: BattleContext,
                  value: Any,
                  name: VolatileName,
                  mon: Pokemon | None = None) -> HandlerReturn:
    """揮発状態のターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        name: 対象の揮発状態名
        mon: 対象のポケモン（Noneの場合はctx.source）
    """
    if mon is None:
        mon = ctx.source
    battle.volatile_manager.tick(mon, name)
    return HandlerReturn(value=value)


def remove_volatile(battle: Battle,
                    ctx: BattleContext,
                    value: Any,
                    name: VolatileName,
                    mon: Pokemon | None = None,
                    reason: str = "") -> HandlerReturn:
    """揮発状態の解除処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        name: 対象の揮発状態名
        mon: 対象のポケモン（Noneの場合はctx.source）
        reason: 解除理由
    """
    if mon is None:
        mon = ctx.source

    if battle.volatile_manager.remove(mon, name):
        battle.add_event_log(
            mon,
            LogCode.VOLATILE_REMOVED,
            payload={"volatile": name, "reason": reason}
        )
    return HandlerReturn(value=value)


def charge_hidden_move(battle: Battle,
                       ctx: BattleContext,
                       value: Any,
                       name: VolatileName) -> HandlerReturn:
    """かくれる技の1ターン目のためる処理を行う。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の判定値
        name: 対象の揮発状態名

    Returns:
        HandlerReturn: 続行する場合はTrue、ためるターンで停止する場合はFalse
    """
    attacker = ctx.attacker
    if ctx.move.name == name and not attacker.has_volatile("かくれる"):
        battle.volatile_manager.apply(attacker, "かくれる", count=1, move=ctx.move)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def check_hidden_move(battle: Battle,
                      ctx: BattleContext,
                      value: Any) -> HandlerReturn:
    """潜伏中の回避判定を行う。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の判定値
    Returns:
        HandlerReturn: 命中可ならTrue、回避するならFalse
    """
    defender = ctx.defender
    if defender.has_volatile("かくれる"):
        hidden_move = defender.volatiles["かくれる"].move_name
        allowed_moves = HIDDEN_MOVE_ALLOWED_MOVES.get(hidden_move, [])
        if ctx.move.name in allowed_moves:
            return HandlerReturn(value=True)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def restrict_commands(battle: Battle,
                      ctx: BattleContext,
                      value: Any,
                      name: VolatileName,
                      can_switch: bool = True) -> HandlerReturn:
    """指定揮発状態の固定技のみ選択可能にする。"""
    mon = ctx.source
    fixed_move_name = mon.volatiles[name].move_name
    new_options = []
    for cmd in value:
        if mon.moves[cmd.idx].name == fixed_move_name or \
                (can_switch and cmd.is_switch()):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def あばれる_modify_command_options(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あばれる状態では強制コマンドのみ選択可能にする。"""
    return HandlerReturn(value=[Command.FORCED], stop_event=True)

# TODO : 解除後の処理は Event.ON_VOLATILE_END に分ける。残りの処理はtick_volatileを呼び出すだけにする。


def あばれる_tick(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あばれる状態のターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    mon = ctx.attacker
    battle.volatile_manager.tick(mon, "あばれる")
    if not mon.has_volatile("あばれる"):
        count = battle.random.randint(2, 5)
        battle.volatile_manager.apply(mon, "こんらん", count=count)
    return HandlerReturn(value=value)


def あめまみれ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あめまみれのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn:
    """
    mon = ctx.source
    battle.volatile_manager.tick(mon, "あめまみれ")
    if mon.has_volatile("あめまみれ"):
        battle.modify_stat(mon, "S", -1, reason="あめまみれ")
    return HandlerReturn(value=value)


def アンコール_modify_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """アンコールによる技の固定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 固定技以外の場合は差し替える
    """
    mon = ctx.attacker
    volatile = mon.volatiles["アンコール"]
    move = mon.find_move(volatile.move_name)
    return HandlerReturn(value=move)


def いちゃもん_modify_command_options(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """いちゃもんによるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: 新しいコマンドオプションのリスト
    """
    mon = ctx.attacker
    last_move_name = mon.volatiles["いちゃもん"].move_name
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move_family()
            or mon.moves[cmd.idx].name != last_move_name
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def おんねん(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """おんねん状態のひんし時処理（相手の技PPを0にする）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if not ctx.fainted:
        return HandlerReturn(value=value)

    ctx.move.pp = 0
    battle.add_event_log(
        ctx.attacker,
        LogCode.CONSUME_PP,
        payload={"move": ctx.move.name, "reason": "おんねん", "value": 0}
    )
    return HandlerReturn(value=value)


def かいふくふうじ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """
    かいふくふうじ状態による回復無効化

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 回復量

    Returns:
        HandlerReturn: 回復無効化の場合は0、それ以外は元の回復量
    """
    if ctx.hp_change_reason in ("pain_split", "bench_heal"):
        return HandlerReturn(value=value)

    battle.add_event_log(
        ctx.target,
        LogCode.HEAL_BLOCKED,
        payload={"reason": "かいふくふうじ"})
    return HandlerReturn(value=0)


def かなしばり_modify_command_options(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かなしばりによるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: 新しいコマンドオプションのリスト
    """
    forbidden_name = ctx.attacker.volatiles["かなしばり"].move_name
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move_family()
            or ctx.attacker.moves[cmd.idx].name != forbidden_name
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def かなしばり_check_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かなしばりによる技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 禁止技の場合はvalue=None、それ以外はTrue
    """
    volatile = ctx.attacker.volatiles["かなしばり"]
    if ctx.move.name == volatile.move_name:
        battle.add_event_log(
            ctx.attacker,
            LogCode.ACTION_BLOCKED,
            payload={"reason": "かなしばり", "move": ctx.move.name}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def きゅうしょアップ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """急所ランク状態による急所補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 急所ランク

    Returns:
        HandlerReturn: 補正後の急所ランク
    """
    volatile = ctx.attacker.volatiles["きゅうしょアップ"]
    return HandlerReturn(value=value+volatile.count)


def こんらん_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """こんらん状態による自傷ダメージ判定（33%確率）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 自傷した場合はFalse（行動中断）、しなかった場合はTrue
    """
    mon = ctx.attacker
    battle.volatile_manager.tick(mon, "こんらん")

    if battle.test_option.trigger_volatile is not None:
        # テスト用に確率を固定
        confused = battle.test_option.trigger_volatile
    else:
        confused = battle.random.random() < 1/3

    if not confused:
        return HandlerReturn(value=True)

    battle.add_event_log(
        ctx.attacker,
        LogCode.ACTION_BLOCKED,
        payload={"reason": "こんらん"}
    )

    # 自傷ダメージの計算（通常のダメージ計算と同様の処理を行う）
    damage = battle.determine_damage(
        attacker=ctx.attacker,
        defender=ctx.attacker,
        move="こんらん",
    )

    # ダメージ適用
    battle.modify_hp(ctx.attacker, v=-damage, reason="self_attack")
    return HandlerReturn(value=False, stop_event=True)


def さわぐ_on_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さわぐ状態を付与し、場のねむり関連状態を解除する。"""
    # 相手にさわがしい状態を付与
    foe = battle.foe(ctx.source)

    count = ctx.source.volatiles["さわぐ"].count
    battle.volatile_manager.apply(foe, "さわがしい", count=count)

    # 場のポケモンのねむり・ねむけ状態を解除
    for mon in battle.actives:
        if mon.has_volatile("ねむけ"):
            battle.volatile_manager.remove(mon, "ねむけ")
        if mon.has_ailment("ねむり"):
            battle.ailment_manager.remove(mon)

    return HandlerReturn(value=True)


def さわぐ_on_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さわぐ状態が解除されたときの処理（相手のさわがしいも解除する）"""
    foe = battle.foe(ctx.source)
    battle.volatile_manager.remove(foe, "さわがしい")
    return HandlerReturn(value=value)


def さわぐ_modify_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さわぐ中の強制技固定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技

    Returns:
        HandlerReturn: 固定技に差し替える
    """
    mon = ctx.attacker
    volatile = mon.volatiles["さわぐ"]
    move = mon.find_move(volatile.move_name)
    return HandlerReturn(value=move)


def さわぐ_prevent_sleep(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さわぐ状態でねむりを防ぐ

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 状態異常名

    Returns:
        HandlerReturn: ねむりを防ぐ場合は空文字列
    """
    if value == "ねむり":
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def さわぐ_prevent_nemuke(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さわぐ状態でねむけを防ぐ

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 揮発状態名

    Returns:
        HandlerReturn: ねむけを防ぐ場合は空文字列
    """
    if value == "ねむけ":
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def ふういん(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ふういん状態の相手が共有技を使えないようにする。"""
    if ctx.defender.has_move(ctx.move.name):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def しおづけ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """しおづけ状態のターン終了時ダメージ

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: ダメージが発生した場合True
    """
    mon = ctx.source
    r = -1/8
    if mon.has_type("みず") or mon.has_type("はがね"):
        r *= 2
    battle.modify_hp(mon, r=r)
    return HandlerReturn(value=value)


def じごくづき_restrict_commands(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """じごくづき状態によるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: 音技以外のコマンドのみ選択可能な新しいコマンドオプションのリスト
    """
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move_family()
            or not ctx.attacker.moves[cmd.idx].has_label("sound")
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def じごくづき_check_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """じごくづき状態による技の不発"""
    if ctx.move.has_label("sound"):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def じゅうでん_boost(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """じゅうでん状態による威力補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 威力補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move.type == "でんき":
        value *= 2
        remove_volatile(battle, ctx, value, "じゅうでん")
    return HandlerReturn(value=value)


def タールショット_damage_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """タールショット状態でほのお技のダメージ補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: ダメージ補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move.type == "ほのお":
        value *= 2
    return HandlerReturn(value=value)


def ちいさくなる_guaranteed_hit(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ちいさくなる状態への必中補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 命中率

    Returns:
        HandlerReturn: 必中の場合はNoneを返す
    """
    if ctx.move.has_label("minimize"):
        return HandlerReturn(value=None, stop_event=True)
    return HandlerReturn(value=value)


def ちいさくなる_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ちいさくなる状態への威力補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 威力補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move.has_label("minimize"):
        value *= 2
    return HandlerReturn(value=value)


def ちょうはつ_check_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ちょうはつによる変化技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 変化技の場合はvalue=None（使用禁止）、攻撃技の場合はTrue
    """
    if ctx.move.category == "変化":
        battle.add_event_log(
            ctx.attacker,
            LogCode.ACTION_BLOCKED,
            payload={"reason": "ちょうはつ", "move": ctx.move.name}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def とくせいなし_on_volatile_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """とくせいなし付与時に特性有効状態を再計算する。"""
    battle.refresh_effect_enabled_states()
    return HandlerReturn(value=value)


def とくせいなし_on_volatile_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """とくせいなし終了時に特性有効状態を再計算する。"""
    battle.refresh_effect_enabled_states()
    return HandlerReturn(value=value)


def とくせいなし_check_ability_enabled(battle: Battle, ctx: BattleContext, value: set[DisabledReason]) -> HandlerReturn:
    """とくせいなし状態で特性が無効になるようにする。"""
    value.add("とくせいなし")
    return HandlerReturn(value=value)


def ねむけ_on_volatile_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねむけを解除してねむりを付与する

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    count = battle.random.randint(1, 3)
    battle.ailment_manager.apply(ctx.source, "ねむり", count=count)
    return HandlerReturn(value=True)


def のろい_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """のろい状態のターン終了時ダメージ

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: ダメージが発生した場合True
    """
    battle.modify_hp(ctx.source, r=-1/4)
    return HandlerReturn(value=value)


def バインド_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バインド状態のターン終了時ダメージ

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    mon = ctx.source

    # ターンカウント減少
    battle.volatile_manager.tick(mon, "バインド")
    if not mon.has_volatile("バインド"):
        return HandlerReturn(value=value)

    # ダメージ適用
    r = -mon.volatiles["バインド"].bind_damage_ratio
    battle.modify_hp(ctx.source, r=r, reason="バインド")
    return HandlerReturn(value=value)


def バインド_swith_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バインド状態のスイッチアウト処理（スイッチアウト時にバインドを解除する）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    foe = battle.foe(ctx.source)
    battle.volatile_manager.remove(foe, "バインド")
    return HandlerReturn(value=value)


def ひるみ_block_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ひるみ状態による行動不能判定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 行動不能の場合はFalse
    """
    battle.add_event_log(
        ctx.attacker,
        LogCode.ACTION_BLOCKED,
        payload={"reason": "ひるみ"}
    )
    remove_volatile(battle, ctx, value, "ひるみ")
    return HandlerReturn(value=False, stop_event=True)


def ほろびのうた_faint(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ほろびのうたでひんしになる処理"""
    mon = ctx.source
    battle.modify_hp(mon, v=-mon.hp)
    return HandlerReturn(value=value)


def マジックコート_reflect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マジックコートによる変化技の跳ね返し"""
    reflected = ctx.move.has_label("reflectable")
    return HandlerReturn(value=reflected)


def まるくなる_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まるくなる状態で特定技の威力補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 威力補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move.name in ["ころがる", "アイスボール"]:
        value *= 2
    return HandlerReturn(value=value)


def みがわり_immune(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりによる技の無効化判定"""
    hit_substitute = battle.move_executor.check_hit_substitute(ctx)
    immune = (
        hit_substitute
        and ctx.move.category == "変化"
    )
    if immune:
        battle.add_event_log(
            ctx.defender,
            LogCode.MOVE_IMMUNE,
            payload={"move": ctx.move.name, "reason": "みがわり"}
        )
        return HandlerReturn(value=True, stop_event=True)
    return HandlerReturn(value=False)


def みがわり_modify_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりがダメージを肩代わりする"""
    damage = value
    if not battle.move_executor.check_hit_substitute(ctx):
        return HandlerReturn(value=damage)

    battle.add_event_log(
        ctx.defender,
        LogCode.HIT_SUBSTITUTE,
        payload={"move": ctx.move.name}
    )
    volatile = ctx.defender.volatiles["みがわり"]
    damage = min(volatile.hp, damage)
    volatile.hp -= damage

    # みがわりに与えたダメージをコンテキストに保存しておく（後の処理で使用するため）
    ctx.substitute_damage = damage

    # みがわり消滅
    if volatile.hp == 0:
        battle.volatile_manager.remove(ctx.defender, "みがわり")

    # 被ダメージは0とする
    return HandlerReturn(value=0)


def みちづれ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みちづれ状態のひんし時処理（相手もひんしにする）"""
    mon = ctx.attacker
    battle.modify_hp(mon, v=-mon.hp)
    return HandlerReturn(value=value)


def メロメロ_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """メロメロ状態による行動不能判定（50%確率）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 行動不能の場合はFalse、行動可能の場合はTrue
    """
    # メロメロ状態の宣言
    battle.add_event_log(
        ctx.attacker,
        LogCode.VOLATILE_STATUS,
        payload={"volatile": "メロメロ"}
    )

    # テスト用に確率を固定できる
    if battle.test_option.trigger_volatile is not None:
        action_blocked = battle.test_option.trigger_volatile
    else:
        action_blocked = battle.random.random() < 0.5

    if action_blocked:
        battle.add_event_log(
            ctx.attacker,
            LogCode.ACTION_BLOCKED,
            payload={"reason": "メロメロ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def ロックオン_modify_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ロックオン状態による命中補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 命中率

    Returns:
        HandlerReturn: 補正後の命中率
    """
    battle.volatile_manager.remove(ctx.attacker, "ロックオン")
    return HandlerReturn(value=None, stop_event=True)


def _protect_success(battle: Battle, ctx: BattleContext) -> bool:
    if ctx.move.bypass_protect:
        return False

    success = battle.events.emit(
        Event.ON_CHECK_PROTECT,
        ctx,
        True
    )
    return success


def _run_protect(battle: Battle,
                 ctx: BattleContext,
                 value: Any,
                 *,
                 on_contact: Callable | None = None,
                 protect_non_attack: bool = True) -> HandlerReturn:
    """protect系の共通骨格。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値
        on_contact: 接触時の追加効果関数 (battle, ctx, value) -> None
        protect_non_attack: False の場合、変化技を保護しない
    """
    if not protect_non_attack and not ctx.move.is_attack:
        return HandlerReturn(value=True)

    if _protect_success(battle, ctx):
        battle.add_event_log(ctx.defender, LogCode.PROTECT_SUCCESS,
                             payload={"move": ctx.move.name})
        if on_contact is not None and battle.move_executor.is_contact(ctx):
            on_contact(battle, ctx, value)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def まもる_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まもるの保護判定"""
    return _run_protect(battle, ctx, value)


def かえんのまもり_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かえんのまもりの保護判定。接触した相手をやけど状態にする"""
    return _run_protect(
        battle,
        ctx,
        value,
        on_contact=partial(
            common.apply_ailment,
            ailment="やけど",
            target_spec="attacker:self",
            source_spec="defender:self",
        ),
        protect_non_attack=False,
    )


def キングシールド_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """キングシールドの保護判定。接触した相手の攻撃ランクを1段階下げる"""
    return _run_protect(
        battle,
        ctx,
        value,
        on_contact=partial(
            common.modify_stat,
            stat="A",
            v=-1,
            target_spec="attacker:self",
            source_spec="defender:self",
        ),
    )


def スレッドトラップ_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """スレッドトラップの保護判定。接触した相手の素早さランクを1段階下げる"""
    return _run_protect(
        battle,
        ctx,
        value,
        on_contact=partial(
            common.modify_stat,
            stat="S",
            v=-1,
            target_spec="attacker:self",
            source_spec="defender:self",
        ),
    )


def トーチカ_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トーチカの保護判定。接触した相手をどく状態にする"""
    return _run_protect(
        battle,
        ctx,
        value,
        on_contact=partial(
            common.apply_ailment,
            ailment="どく",
            target_spec="attacker:self",
            source_spec="defender:self",
        ),
    )
