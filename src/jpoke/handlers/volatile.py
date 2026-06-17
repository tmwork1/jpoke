"""揮発状態ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.utils.type_defs import RoleSpec, Stat, AilmentName, VolatileName

from jpoke.enums import Event, Command, LogCode
from jpoke.core import Handler, HandlerReturn


HIDDEN_MOVE_ALLOWED_MOVES: dict[str, list[str]] = {
    "あなをほる": ["じしん", "マグニチュード"],
    "そらをとぶ": ["かぜおこし", "たつまき", "かみなり"],
    "ダイビング": ["なみのり", "うずしお"],
    "シャドーダイブ": [],
}


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


def check_trapped_not_ghost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ゴーストタイプでなければ交代を禁止する。"""
    source = ctx.source
    return HandlerReturn(value=source is not None and not source.has_type("ゴースト"))


def tick_volatile(battle: Battle,
                  ctx: EventContext,
                  value: Any,
                  volatile: VolatileName) -> HandlerReturn:
    """揮発状態のターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        volatile: 対象の揮発状態名
    """
    mon = getattr(ctx, "source", None) or getattr(ctx, "attacker", None)
    battle.volatile_manager.tick(mon, volatile)
    return HandlerReturn(value=value)


def remove_volatile(battle: Battle,
                    ctx: EventContext,
                    value: Any,
                    volatile: VolatileName,
                    reason: str = "") -> HandlerReturn:
    """揮発状態の解除処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        volatile: 対象の揮発状態名
        reason: 解除理由
    """
    mon = getattr(ctx, "source", None) or getattr(ctx, "attacker", None)
    if battle.volatile_manager.remove(mon, volatile):
        battle.add_event_log(
            mon,
            LogCode.VOLATILE_REMOVED,
            payload={"volatile": volatile, "reason": reason}
        )
    return HandlerReturn(value=value)


def force_command(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
    """強制コマンドを返すハンドラーの共通処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にCommand.FORCEDを返す
    """
    return HandlerReturn(value=[Command.FORCED], stop_event=True)


def can_hit_hidden_target(battle: Battle,
                          ctx: EventContext,
                          value: Any,
                          volatile: VolatileName) -> HandlerReturn:
    """潜伏中の回避判定を行う。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の判定値
        volatile: 対象の揮発状態名（技名と同一）
    Returns:
        HandlerReturn: 命中可ならTrue、回避するならFalse
    """
    allowed_moves = HIDDEN_MOVE_ALLOWED_MOVES.get(volatile, [])
    if ctx.move.name not in allowed_moves:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_MISSED)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def restrict_commands(battle: Battle,
                      ctx: EventContext,
                      value: Any,
                      name: VolatileName,
                      can_switch: bool = True) -> HandlerReturn:
    """指定揮発状態の固定技のみ選択可能にする。"""
    mon = ctx.source
    fixed_move_name = mon.volatiles[name].move_name
    new_options = []
    for cmd in value:
        if (
            mon.moves[cmd.index].name == fixed_move_name
            or (can_switch and cmd.is_switch)
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def あばれる_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def あめまみれ_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
        battle.modify_stats(mon, {"S": -1}, reason="あめまみれ")
    return HandlerReturn(value=value)


def アンコール_modify_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
    move = mon.get_move(volatile.move_name)
    return HandlerReturn(value=move)


def いちゃもん_modify_command_options(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
    """いちゃもんによるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: 新しいコマンドオプションのリスト
    """
    mon = ctx.source
    last_move_name = mon.volatiles["いちゃもん"].move_name
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move_family
            or mon.moves[cmd.index].name != last_move_name
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def うちおとす_check_floating(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """うちおとすによる浮遊状態の無効化

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 浮遊状態の有無を表すブール値

    Returns:
        HandlerReturn: False（浮遊状態を無効化）
    """
    return HandlerReturn(value=False, stop_event=True)


def おんねん_deplete_attacking_move_pp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おんねん状態のひんし時処理（相手の技PPを0にする）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.move.pp = 0
    battle.add_event_log(
        ctx.attacker,
        LogCode.TEXT_LOG,
        payload={"text": f"おんねんで{ctx.move.name}のPPを0にした"}
    )
    return HandlerReturn(value=value)


def かいふくふうじ_block_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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

    battle.add_event_log(ctx.target, LogCode.HEAL_BLOCKED,
                         payload={"reason": "かいふくふうじ"})
    return HandlerReturn(value=0)


def かなしばり_modify_command_options(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かなしばりによるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: 新しいコマンドオプションのリスト
    """
    forbidden_name = ctx.source.volatiles["かなしばり"].move_name
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move_family
            or ctx.source.moves[cmd.index].name != forbidden_name
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def かなしばり_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload={"reason": "かなしばり"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def きゅうしょアップ_boost_critical_rank(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """急所ランク状態による急所補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 急所ランク

    Returns:
        HandlerReturn: 補正後の急所ランク
    """
    value += ctx.attacker.volatiles["きゅうしょアップ"].count
    return HandlerReturn(value=value)


def こらえる_endure(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """こらえる状態: 致死ダメージを HP 1 残しに補正する。

    ダメージが防御側の現在 HP 以上の場合、ダメージを hp - 1 に抑えて HP 1 を残す。
    """
    mon = ctx.defender
    if value >= mon.hp:
        value = mon.hp - 1
    return HandlerReturn(value=value)


def こらえる_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="こらえる")


def こんらん_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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

    # 自傷ダメージの計算（通常のダメージ計算と同様の処理を行う）
    damage = battle.roll_damage(
        attacker=ctx.attacker,
        defender=ctx.attacker,
        move="こんらん",
    )

    # ダメージ適用
    battle.modify_hp(ctx.attacker, v=-damage, reason="self_attack")
    battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                         payload={"reason": "こんらん"})
    return HandlerReturn(value=False, stop_event=True)


def さわぐ_start(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def さわぐ_remove_さわがしい(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さわぐ状態が解除されたときの処理（相手のさわがしいも解除する）"""
    foe = battle.foe(ctx.source)
    battle.volatile_manager.remove(foe, "さわがしい")
    return HandlerReturn(value=value)


def さわぐ_modify_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
    move = mon.get_move(volatile.move_name)
    return HandlerReturn(value=move)


def さわぐ_prevent_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def さわぐ_prevent_nemuke(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def しおづけ_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def じごくづき_restrict_commands(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
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
            not cmd.is_move_family
            or not ctx.source.moves[cmd.index].has_label("sound")
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def じごくづき_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じごくづき状態による技の不発"""
    if ctx.move.has_label("sound"):
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload={"reason": "じごくづき"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def じゅうでん_boost_electric(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def タールショット_boost_fire(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def ちいさくなる_guaranteed_hit(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def ちいさくなる_boost_power(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def ちょうはつ_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちょうはつによる変化技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 変化技の場合はvalue=None（使用禁止）、攻撃技の場合はTrue
    """
    if ctx.move.category == "変化":
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload={"reason": "ちょうはつ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def とくせいなし_disable_ability(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    battle.add_ability_disabled_reason(ctx.source, "とくせいなし")
    return HandlerReturn(value=value)


def とくせいなし_enable_ability(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """とくせいなし終了時に特性有効状態を再計算する。"""
    battle.remove_ability_disabled_reason(ctx.source, "とくせいなし")
    return HandlerReturn(value=value)


def ねむけ_remove_and_apply_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def のろい_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def バインド_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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
    r = battle.events.emit(Event.ON_MODIFY_BIND_DAMAGE, ctx, mon.volatiles["バインド"].bind_damage_ratio)
    battle.modify_hp(ctx.source, r=-r)
    return HandlerReturn(value=value)


def バインド_remove(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def ひるみ_block_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ひるみ状態による行動不能判定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 行動不能の場合はFalse
    """
    battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                         payload={"reason": "ひるみ"})
    return HandlerReturn(value=False, stop_event=True)


def ふういん_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふういん状態の相手が共有技を使えないようにする。"""
    if ctx.defender.has_move(ctx.move.name):
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload={"reason": "ふういん"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ほろびのうた_faint(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ほろびのうたでひんしになる処理"""
    mon = ctx.source
    battle.modify_hp(mon, v=-mon.hp)
    return HandlerReturn(value=value)


def マジックコート_reflect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マジックコートによる変化技の跳ね返し"""
    value = (
        ctx.move.category == "変化"
        and ctx.move.target in {"foe", "foe_side"}
    )

    return HandlerReturn(value=value)


def まるくなる_boost_power(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def みがわり_immune(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みがわりによる技の無効化判定"""
    hit_substitute = battle.move_executor.check_hit_substitute(ctx)
    if (
        hit_substitute
        and ctx.move.category == "変化"
    ):
        battle.add_event_log(ctx.defender, LogCode.MOVE_IMMUNED,
                             payload={"reason": "みがわり"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def みがわり_block_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みがわりがダメージを肩代わりする"""
    damage = value
    if not battle.move_executor.check_hit_substitute(ctx):
        return HandlerReturn(value=damage)

    battle.add_event_log(
        ctx.defender,
        LogCode.SUBSTITUTE_HIT,
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


def みちづれ_faint(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みちづれ状態のひんし時処理（相手もひんしにする）"""
    mon = ctx.attacker
    battle.modify_hp(mon, v=-mon.hp)
    battle.add_event_log(
        mon,
        LogCode.VOLATILE_DISPLAY,
        payload={"volatile": "みちづれ"}
    )
    return HandlerReturn(value=value)


def メロメロ_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メロメロ状態による行動不能判定（50%確率）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 行動不能の場合はFalse、行動可能の場合はTrue
    """
    # メロメロ状態の宣言
    battle.add_event_log(ctx.attacker, LogCode.VOLATILE_DISPLAY,
                         payload={"volatile": "メロメロ"})

    # テスト用に確率を固定できる
    if battle.test_option.trigger_volatile is not None:
        action_blocked = battle.test_option.trigger_volatile
    else:
        action_blocked = battle.random.random() < 0.5

    if action_blocked:
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload={"reason": "メロメロ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def ロックオン_guarantee_hit(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ロックオン状態による命中補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 命中率

    Returns:
        HandlerReturn: 補正後の命中率
    """
    return HandlerReturn(value=None, stop_event=True)


def _check_protect_success(battle: Battle, ctx: EventContext, protect_non_attack: bool) -> bool:
    if (
        (not protect_non_attack and not ctx.move.is_attack)
        or not ctx.move.is_blocked_by_protect
    ):
        return False
    return battle.events.emit(Event.ON_CHECK_PROTECT, ctx, True)


def _run_protect(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 stats_change_on_contact: dict[Stat, int] | None = None,
                 ailment_on_contact: AilmentName | None = None,
                 protect_non_attack: bool = True) -> HandlerReturn:
    """protect系の共通骨格。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値
        on_contact: 接触時の追加効果関数 (battle, ctx, value) -> None
        protect_non_attack: False の場合、変化技を保護しない
    """
    if not _check_protect_success(battle, ctx, protect_non_attack):
        battle.add_event_log(ctx.defender, LogCode.PROTECT_FAILED)
        return HandlerReturn(value=value)

    battle.add_event_log(ctx.defender, LogCode.PROTECT_SUCCEEDED)

    if battle.query.is_contact(ctx):
        if stats_change_on_contact:
            battle.modify_stats(ctx.attacker, stats_change_on_contact, source=ctx.defender)
        if ailment_on_contact:
            battle.ailment_manager.apply(ctx.attacker, ailment_on_contact, source=ctx.defender)

    return HandlerReturn(value=False, stop_event=True)


def まもる_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まもるの保護判定"""
    return _run_protect(battle, ctx, value)


def かえんのまもり_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かえんのまもりの保護判定。接触した相手をやけど状態にする"""
    return _run_protect(battle, ctx, value, ailment_on_contact="やけど", protect_non_attack=False)


def キングシールド_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """キングシールドの保護判定。接触した相手の攻撃ランクを1段階下げる"""
    return _run_protect(battle, ctx, value, stats_change_on_contact={"A": -1})


def スレッドトラップ_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スレッドトラップの保護判定。接触した相手の素早さランクを1段階下げる"""
    return _run_protect(battle, ctx, value, stats_change_on_contact={"S": -1})


def トーチカ_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """トーチカの保護判定。接触した相手をどく状態にする"""
    return _run_protect(battle, ctx, value, ailment_on_contact="どく")


def アクアリング_self_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.modify_hp(ctx.source, r=1/16, source=ctx.source))


def アンコール_restrict_commands(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return restrict_commands(battle, ctx, value, name="アンコール")


def アンコール_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="アンコール")


def おんねん_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="おんねん")


def かいふくふうじ_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="かいふくふうじ")


def かなしばり_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="かなしばり")


def こだわり_restrict_commands(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return restrict_commands(battle, ctx, value, name="こだわり")


def さわぐ_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="さわぐ")


def じごくづき_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="じごくづき")


def ちょうはつ_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="ちょうはつ")


def でんじふゆう_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="でんじふゆう")


def ねむけ_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="ねむけ")


def ねをはる_self_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.modify_hp(ctx.source, r=1/16, source=ctx.source))


def ひるみ_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="ひるみ")


def ほろびのうた_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="ほろびのうた")


def やどりぎのタネ_drain_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    from_mon = ctx.source
    to_mon = battle.foe(from_mon)
    damage = battle.modify_hp(from_mon, r=-1/8, reason="drain")
    if damage:
        battle.modify_hp(to_mon, -damage, reason="drain")
    return HandlerReturn(value=damage)


def ロックオン_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="ロックオン")


def ロックオン_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="ロックオン")


def まもる_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="まもる")


def かえんのまもり_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="かえんのまもり")


def キングシールド_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="キングシールド")


def スレッドトラップ_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="スレッドトラップ")


def トーチカ_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="トーチカ")


def ハロウィン_add_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ハロウィン付与時: ゴーストタイプを added_types に追加する。"""
    if "ゴースト" not in ctx.source.added_types:
        ctx.source.added_types.append("ゴースト")
    return HandlerReturn(value=value)


def ハロウィン_remove_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ハロウィン解除時: added_types からゴーストタイプを除去する。"""
    if "ゴースト" in ctx.source.added_types:
        ctx.source.added_types.remove("ゴースト")
    return HandlerReturn(value=value)


def もりののろい_add_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """もりののろい付与時: くさタイプを added_types に追加する。"""
    if "くさ" not in ctx.source.added_types:
        ctx.source.added_types.append("くさ")
    return HandlerReturn(value=value)


def もりののろい_remove_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """もりののろい解除時: added_types からくさタイプを除去する。"""
    if "くさ" in ctx.source.added_types:
        ctx.source.added_types.remove("くさ")
    return HandlerReturn(value=value)
