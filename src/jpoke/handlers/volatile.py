"""揮発状態ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle

from jpoke.utils.type_defs import RoleSpec, LogPolicy, VolatileName
from jpoke.enums import Event, Command, LogCode
from jpoke.core import Handler, HandlerReturn, BattleContext
from . import common


class VolatileHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "source:self",
                 log: LogPolicy = "never",
                 log_text: str | None = None,
                 priority: int = 100,
                 once: bool = False):
        super().__init__(func,
                         subject_spec,
                         source_type="volatile",
                         log=log,
                         log_text=log_text,
                         priority=priority,
                         once=once)


def remove_volatile(battle: Battle,
                    ctx: BattleContext,
                    value: Any,
                    name: VolatileName,
                    log: bool = True) -> HandlerReturn:
    """揮発状態の解除処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        name: 対象の揮発状態名
        log: 解除時にログを出力するか
    """
    mon = ctx.source
    if mon.remove_volatile(battle, name) and log:
        battle.add_event_log(mon, f"{name}解除")
    return HandlerReturn()


def tick_volatile(battle: Battle,
                  ctx: BattleContext,
                  value: Any,
                  name: VolatileName,
                  log: bool = True) -> HandlerReturn:
    """揮発状態のターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        name: 対象の揮発状態名
        log: 解除時にログを出力するか
    """
    mon = ctx.source
    mon.tick_down_volatile(battle, name)
    if not mon.has_volatile(name) and log:
        battle.add_event_log(mon, f"{name}解除")
    return HandlerReturn()


def restrict_commands(battle: Battle,
                      ctx: BattleContext,
                      value: Any,
                      name: VolatileName) -> HandlerReturn:
    """特定の技しか使えない揮発状態によるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: 固定技以外の技コマンドを削除したリスト
    """
    locked = ctx.attacker.volatiles[name].move_name

    # 固定技以外の技コマンドを削除
    new_options = []
    for cmd in value:
        if not cmd.is_move_family() or \
                ctx.attacker.moves[cmd.idx].name == locked:
            new_options.append(cmd)

    return HandlerReturn(value=new_options)


def あばれる_modify_command_options(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あばれる状態によるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: あばれる状態の技コマンドのみを残したリスト
    """
    return HandlerReturn(value=[Command.RAMPAGE], stop_event=True)


def あばれる_tick(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あばれる状態のターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    tick_volatile(battle, ctx, value, "あばれる")
    mon = ctx.attacker
    if not mon.has_volatile("あばれる"):
        count = battle.random.randint(2, 5)
        mon.apply_volatile(battle, "こんらん", count=count)
    return HandlerReturn()


def あめまみれ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あめまみれのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn:
    """
    tick_volatile(battle, ctx, value, "あめまみれ")
    mon = ctx.source
    if mon.has_volatile("あめまみれ") and battle.modify_stat(mon, "S", -1):
        battle.add_event_log(mon, "あめまみれ")
    return HandlerReturn()


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
        if not cmd.is_move_family() or \
                mon.moves[cmd.idx].name != last_move_name:
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
    if ctx.fainted and ctx.move:
        ctx.move.pp = 0
        battle.add_event_log(ctx.attacker, f"おんねんで{ctx.move.name}のPPが0になった！")
    return HandlerReturn()


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
    if value > 0:
        battle.add_event_log(ctx.target, "失敗: かいふくふうじ")
        value = 0
    return HandlerReturn(value=value)


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
        if not cmd.is_move_family() or \
                ctx.attacker.moves[cmd.idx].name != forbidden_name:
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def かなしばり_try_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
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
        battle.add_event_log(ctx.attacker, "かなしばりで技が使えない")
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
    mon.tick_down_volatile(battle, "こんらん")

    if not mon.has_volatile("こんらん"):
        return HandlerReturn(value=True)

    battle.add_event_log(ctx.attacker, "混乱している")

    if battle.test_option.trigger_volatile is not None:
        # テスト用に確率を固定
        confused = battle.test_option.trigger_volatile
    else:
        confused = battle.random.random() < 1/3

    if not confused:
        return HandlerReturn(value=True)

    # 自傷ダメージの計算（通常のダメージ計算と同様の処理を行う）
    damage = battle.determine_damage(
        attacker=ctx.attacker,
        defender=ctx.attacker,
        move="こんらん",
    )
    # ダメージ適用
    battle.modify_hp(ctx.attacker, v=-damage)
    battle.add_event_log(ctx.attacker, "自傷")
    return HandlerReturn(value=False, stop_event=True)


def さわぐ_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さわぐ状態を付与する

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 成功時True
    """
    user = ctx.attacker
    if not user:
        return HandlerReturn(False)

    if not user.apply_volatile(battle.events, "さわぐ", count=3, source=user):
        return HandlerReturn(False)
    user.volatiles["さわぐ"].move_name = ctx.move.name if ctx.move else ""
    return HandlerReturn(True)


def さわぐ_before_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """さわぐ中の強制技固定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技

    Returns:
        HandlerReturn: 固定技に差し替える
    """
    move = value
    volatile = ctx.attacker.volatiles.get("さわぐ") if ctx.attacker else None
    if not volatile or not move:
        return HandlerReturn(True)

    locked = volatile.move_name
    if locked and move.name != locked:
        forced = ctx.attacker.find_move(locked)
        if forced:
            return HandlerReturn(True, forced)
    return HandlerReturn(True)


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
        return HandlerReturn(True, "", stop_event=True)
    return HandlerReturn(False, value)


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
    success = battle.modify_hp(mon, r=r)
    return HandlerReturn(success=success)


def じごくずき_restrict_commands(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """じごくづき状態によるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: じごくづき以外の技コマンドを削除したリスト
    """
    new_options = []
    for cmd in value:
        if not cmd.is_move_family() or \
                not ctx.attacker.moves[cmd.idx].has_label("sound"):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def じごくづき_try_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
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


def ちょうはつ_try_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ちょうはつによる変化技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 変化技の場合はvalue=None（使用禁止）、攻撃技の場合はTrue
    """
    if ctx.move.category == "変化":
        battle.add_event_log(ctx.attacker, f"ちょうはつ: {ctx.move.name}不発")
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def ねむけ_tick(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねむけのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.tick_down_volatile(battle, "ねむけ")
    if not ctx.source.has_volatile("ねむけ"):
        count = battle.random.randint(1, 3)
        ctx.source.apply_ailment(battle, "ねむり", count=count)
    return HandlerReturn()


def のろい_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """のろい状態のターン終了時ダメージ

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: ダメージが発生した場合True
    """
    mon = ctx.source
    if battle.modify_hp(mon, r=-1/4):
        battle.add_event_log(mon, "のろい")
    return HandlerReturn()


def バインド_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バインド状態のターン終了時ダメージ

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    # ターンカウント減少
    tick_volatile(battle, ctx, value, "バインド")

    if not ctx.source.has_volatile("バインド"):
        return HandlerReturn()

    # ダメージ計算のためのイベントを発行
    r = battle.events.emit(
        Event.ON_MODIFY_BIND_DAMAGE_RATIO,
        BattleContext(source=battle.foe(ctx.source)),
        -1/8
    )

    # ダメージ適用
    if battle.modify_hp(ctx.source, r=r):
        battle.add_event_log(ctx.source, "バインドダメージ")

    return HandlerReturn()


def バインド_swith_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バインド状態のスイッチアウト処理（スイッチアウト時にバインドを解除する）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    battle.foe(ctx.source).remove_volatile(battle, "バインド")
    return HandlerReturn()


def ひるみ_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ひるみ状態による行動不能判定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 行動不能の場合はFalse
    """
    remove_volatile(battle, ctx, value, "ひるみ")
    return HandlerReturn(value=False, stop_event=True)


def ふういん_(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    return HandlerReturn()


def ほろびのうた_tick(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ほろびのうたのターン経過処理"""
    tick_volatile(battle, ctx, value, "ほろびのうた")
    if not ctx.source.has_volatile("ほろびのうた"):
        battle.modify_hp(ctx.source, v=-ctx.source.hp)
        battle.add_event_log(ctx.source, "ほろびのうた")
    return HandlerReturn()


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
    if ctx.move and ctx.move.name in ["ころがる", "アイスボール"]:
        return HandlerReturn(True, value * 2)
    return HandlerReturn(False, value)


def みちづれ(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みちづれ状態のひんし時処理（相手もひんしにする）"""
    if ctx.fainted:
        mon = ctx.attacker
        battle.modify_hp(mon, v=-mon.hp)
        battle.add_event_log(mon, "みちづれ")
    return HandlerReturn()


def みがわり_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりを生成する

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 成功時True
    """
    user = ctx.attacker
    if not user or not user.has_volatile("みがわり"):
        return HandlerReturn(False)

    cost = user.max_hp // 4
    if user.hp <= cost:
        return HandlerReturn(False)

    if not battle.modify_hp(user, v=-cost):
        return HandlerReturn(False)

    if not user.apply_volatile(battle.events, "みがわり", source=user):
        return HandlerReturn(False)

    user.volatiles["みがわり"].hp = cost
    return HandlerReturn(True)


def みがわり_immune(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりによる技の無効化判定"""
    hit_substitute = battle.move_executor.hit_substitute(ctx)
    immune = hit_substitute and ctx.move.category == "変化"
    if immune:
        battle.add_event_log(ctx.defender, "みがわりにより無効")
        return HandlerReturn(value=True, stop_event=True)
    return HandlerReturn(value=False)


def みがわり_modify_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりがダメージを肩代わりする"""
    damage = value
    hit_substitute = battle.move_executor.hit_substitute(ctx)
    if not hit_substitute:
        return HandlerReturn(value=damage)

    battle.add_event_log(ctx.defender, "みがわり被弾")
    volatile = ctx.defender.volatiles["みがわり"]
    damage = min(volatile.hp, damage)
    volatile.hp -= damage

    # みがわり消滅
    if volatile.hp == 0:
        ctx.defender.remove_volatile(battle, "みがわり")
        battle.add_event_log(ctx.defender, "みがわり消滅")

    # みがわりに与えたダメージをコンテキストに保存しておく（後の処理で使用するため）
    ctx.substitute_damage = damage

    # 被ダメージは0とする
    return HandlerReturn(value=0)


def メロメロ_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """メロメロ状態による行動不能判定（50%確率）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 行動不能の場合はFalse、行動可能の場合はTrue
    """
    # テスト用に確率を固定できる
    if battle.test_option.trigger_volatile is not None:
        infatuated = battle.test_option.trigger_volatile
    else:
        infatuated = battle.random.random() < 0.5

    battle.add_event_log(ctx.attacker, "メロメロ")
    if infatuated:
        battle.add_event_log(ctx.attacker, "動けない")
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
    ctx.attacker.remove_volatile(battle, "ロックオン")
    return HandlerReturn(value=None, stop_event=True)


def _protect_success(battle: Battle, ctx: BattleContext) -> bool:
    if ctx.move.bypass_protect:
        return False

    success = battle.events.emit(
        Event.ON_CHECK_PROTECT,
        ctx,
        True
    )
    return True


def まもる_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まもるの保護判定"""
    success = _protect_success(battle, ctx)
    if success:
        battle.add_event_log(ctx.defender, LogCode.PROTECT_SUCCESS)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def かえんのまもり_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かえんのまもりの保護判定。接触した相手をやけど状態にする"""
    success = _protect_success(battle, ctx)
    if success:
        battle.add_event_log(ctx.defender, "攻撃を防いだ")
        if battle.move_executor.is_contact(ctx):
            common.apply_ailment(battle, ctx, value, "やけど", target_spec="attacker:self", source_spec="defender:self")
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def キングシールド_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """キングシールドの保護判定。接触した相手の攻撃ランクを1段階下げる"""
    success = _protect_success(battle, ctx)
    if success:
        battle.add_event_log(ctx.defender, "攻撃を防いだ")
        if battle.move_executor.is_contact(ctx):
            battle.modify_stat(ctx.attacker, "A", -1, source=ctx.defender)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def スレッドトラップ_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """スレッドトラップの保護判定。接触した相手の素早さランクを1段階下げる"""
    success = _protect_success(battle, ctx)
    if success:
        battle.add_event_log(ctx.defender, "攻撃を防いだ")
        if battle.move_executor.is_contact(ctx):
            battle.modify_stat(ctx.attacker, "S", -1, source=ctx.defender)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def トーチカ_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トーチカの保護判定。接触した相手をどく状態にする"""
    success = _protect_success(battle, ctx)
    if success:
        battle.add_event_log(ctx.defender, "攻撃を防いだ")
        if battle.move_executor.is_contact(ctx):
            common.apply_ailment(battle, ctx, value, "どく", target_spec="attacker:self", source_spec="defender:self")
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


# かくれる系


def 姿消し_check_invulnerable(battle: Battle, ctx: BattleContext, value: Any, allowed_moves: list[str]) -> HandlerReturn:
    """姿消し状態の回避判定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 判定値
        allowed_moves: 命中可能な技名

    Returns:
        HandlerReturn: 回避する場合True
    """
    if not ctx.move:
        return HandlerReturn(False, value)
    if ctx.move.name in allowed_moves:
        return HandlerReturn(False, value)
    return HandlerReturn(True, True)
