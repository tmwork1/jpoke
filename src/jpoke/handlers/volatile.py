"""揮発状態ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext

from jpoke.utils.type_defs import RoleSpec, LogPolicy, VolatileName
from jpoke.enums import Event
from jpoke.core import Handler, HandlerReturn
from . import common


class VolatileHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "source:self",
                 log: LogPolicy = "on_success",
                 priority: int = 100):
        super().__init__(func, subject_spec, "volatile", log, None, priority)


def remove_volatile(battle: Battle, ctx: BattleContext, value: Any,
                    name: VolatileName, log: bool = False) -> HandlerReturn:
    """揮発状態の解除処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        name: 対象の揮発状態名
    """
    ctx.source.remove_volatile(battle, name, log=log)
    return HandlerReturn()


def tick_down_volatile(battle: Battle, ctx: BattleContext, value: Any, name: VolatileName) -> HandlerReturn:
    """揮発状態のターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        name: 対象の揮発状態名
    """
    ctx.source.tick_down_volatile(battle, name)
    return HandlerReturn()


def _protect_block(battle: Battle, ctx: BattleContext, value: Any) -> bool:
    if not ctx.move:
        return False
    if "unprotectable" in ctx.move.data.labels or "anti_protect" in ctx.move.data.labels:
        return False
    return True


def あばれる_before_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あばれる中の強制技固定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技

    Returns:
        HandlerReturn: 固定技に差し替える
    """
    move = value
    volatile = ctx.target.volatiles.get("あばれる") if ctx.target else None
    if not volatile or not move:
        return HandlerReturn(True)

    locked = volatile.locked_move_name
    if locked and move.name != locked:
        forced = ctx.target.find_move(locked)
        if forced:
            return HandlerReturn(True, forced)
    return HandlerReturn(True)


def あばれる_after_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あばれる状態のターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.tick_down_volatile(battle, "あばれる")
    if not ctx.source.has_volatile("あばれる"):
        # こんらん状態を付与 (1~4ターン)
        ctx.source.apply_volatile(battle, "こんらん", count=battle.random.randint(1, 4))
    return HandlerReturn(True)


def あめまみれ_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """あめまみれのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    tick_down_volatile(battle, ctx, value, "あめまみれ")
    if ctx.source.has_volatile("あめまみれ"):
        ctx.source.modify_stats({"S": -1}, source=battle.foe(ctx.source))
    return HandlerReturn(True)


def アンコール_check_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """アンコールによる技の固定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 固定技以外の場合は差し替える
    """
    move = value
    if move is None:
        return HandlerReturn(True)

    volatile = ctx.target.volatiles.get("アンコール") if ctx.target else None
    if not volatile:
        return HandlerReturn(True)

    if not volatile.locked_move_name:
        if ctx.target.executed_move:
            volatile.locked_move_name = ctx.target.executed_move.name
        else:
            ctx.target.remove_volatile(battle.events, "アンコール")
            return HandlerReturn(True)

    locked = volatile.locked_move_name
    if move.name != locked:
        forced = ctx.target.find_move(locked)
        if forced and forced.pp > 0:
            return HandlerReturn(True, forced)
        ctx.target.remove_volatile(battle.events, "アンコール")
    return HandlerReturn(True)


def いちゃもん_before_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """いちゃもんによる同じ技の連続使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 前回と同じ技の場合はvalue=None、それ以外はTrue
    """
    # valueはMoveオブジェクト
    move = value

    # moveがNoneの場合はスキップ
    if move is None:
        return HandlerReturn(True)

    volatile = ctx.target.volatiles.get("いちゃもん") if ctx.target else None

    if volatile and hasattr(volatile, 'last_move_name'):
        if move.name == volatile.last_move_name:
            battle.add_event_log(ctx.target, f"はいちゃもんで{move.name}が使えない！")
            return HandlerReturn(False, value=None, stop_event=True)

    return HandlerReturn(True)


def いちゃもん_record_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """いちゃもん用に直前技を記録する

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if not ctx.attacker or not ctx.move:
        return HandlerReturn(False)

    volatile = ctx.attacker.volatiles.get("いちゃもん")
    if volatile:
        volatile.last_move_name = ctx.move.name
        return HandlerReturn(True)

    return HandlerReturn(False)


def うちおとす_check_floating(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """うちおとす状態による接地判定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の浮遊判定

    Returns:
        HandlerReturn: 接地扱い（False）
    """
    return HandlerReturn(True, False)


def おんねん_on_faint(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """おんねん状態のひんし時処理（相手の技PPを0にする）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if not ctx.attacker or not ctx.move:
        return HandlerReturn(False)

    move = ctx.attacker.find_move(ctx.move.name)
    if not move:
        return HandlerReturn(False)

    move.pp = 0
    battle.add_event_log(ctx.attacker, f"{move.name}のPPが0になった！")
    return HandlerReturn(True)


def かえんのまもり_check_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かえんのまもりの保護判定とやけど付与

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 判定値

    Returns:
        HandlerReturn: 防御する場合True
    """
    if not _protect_block(battle, ctx, value):
        return HandlerReturn(False, value)

    if ctx.attacker and ctx.move and "contact" in ctx.move.data.labels and ctx.move.category != "変化":
        common.apply_ailment(battle, ctx, value, "やけど", target_spec="attacker:self", source_spec="defender:self")
    return HandlerReturn(True, True)


def かえんのまもり_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かえんのまもり状態のターン終了時解除

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if "かえんのまもり" in ctx.source.volatiles:
        ctx.source.volatiles["かえんのまもり"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["かえんのまもり"]
    return HandlerReturn(True)


def かなしばり_before_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """かなしばりによる技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 禁止技の場合はvalue=None、それ以外はTrue
    """
    # valueはMoveオブジェクト
    move = value

    # moveがNoneの場合はスキップ
    if move is None:
        return HandlerReturn(True)

    volatile = ctx.target.volatiles.get("かなしばり")

    if volatile and hasattr(volatile, 'disabled_move_name'):
        if move.name == volatile.disabled_move_name:
            battle.add_event_log(ctx.target, f"は{move.name}を使えない！")
            return HandlerReturn(False, value=None, stop_event=True)

    return HandlerReturn(True)


def こんらん_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """こんらん状態による自傷ダメージ判定（33%確率）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 自傷した場合はFalse（行動中断）、しなかった場合はTrue
    """
    # ターンカウント減少（1～4ターンで自然治癒）
    ctx.attacker.tick_down_volatile(battle, "こんらん")

    # カウントが0になったら解除
    if not ctx.attacker.has_volatile("こんらん"):
        return HandlerReturn(value=True)

    battle.add_event_log(ctx.attacker, "は混乱している！")

    # テスト用に確率を固定できる
    if battle.test_option.trigger_volatile is not None:
        confused = battle.test_option.trigger_volatile
    else:
        confused = battle.random.random() < 0.33

    if confused:
        damage = battle.determine_damage(
            attacker=ctx.attacker,
            move="こんらん",
            self_harm=True,
        )
        # ダメージ適用
        battle.modify_hp(ctx.attacker, v=-damage)
        battle.add_event_log(ctx.attacker, "は自分を攻撃した！")
        return HandlerReturn(False, stop_event=True)

    return HandlerReturn(True)


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
    user.volatiles["さわぐ"].locked_move_name = ctx.move.name if ctx.move else ""
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
    volatile = ctx.target.volatiles.get("さわぐ") if ctx.target else None
    if not volatile or not move:
        return HandlerReturn(True)

    locked = volatile.locked_move_name
    if locked and move.name != locked:
        forced = ctx.target.find_move(locked)
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


def たくわえる_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """たくわえるの蓄積処理

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

    volatile = user.volatiles.get("たくわえる")
    if volatile and volatile.count >= 3:
        return HandlerReturn(False)

    if not volatile:
        if not user.apply_volatile(battle.events, "たくわえる", source=user):
            return HandlerReturn(False)
        volatile = user.volatiles.get("たくわえる")

    volatile.tick_up()
    battle.modify_stats(user, {"B": 1, "D": 1}, source=user)
    return HandlerReturn(True)


def ちいさくなる_accuracy_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ちいさくなる状態への必中補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 命中率

    Returns:
        HandlerReturn: 必中の場合はNoneを返す
    """
    if ctx.move and ctx.move.name in ["のしかかり", "ふみつけ", "ドラゴンダイブ", "サンダープリズン"]:
        return HandlerReturn(True, None)
    return HandlerReturn(False, value)


def ちいさくなる_power_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ちいさくなる状態への威力補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 威力補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move and ctx.move.name in ["のしかかり", "ふみつけ", "ドラゴンダイブ", "サンダープリズン"]:
        return HandlerReturn(True, value * 8192 // 4096)
    return HandlerReturn(False, value)


def ちょうはつ_before_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ちょうはつによる変化技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 変化技の場合はvalue=None（使用禁止）、攻撃技の場合はTrue
    """
    # valueはMoveオブジェクト
    move = value

    # moveがNoneの場合はスキップ
    if move is None:
        return HandlerReturn(True)

    # 変化技の場合は使用失敗
    if move.data.category == "変化":
        battle.add_event_log(ctx.target, f"はちょうはつで{move.name}が使えない！")
        return HandlerReturn(False, value=None, stop_event=True)

    return HandlerReturn(True)


def にげられない_check_trapped(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """にげられない状態による交代制限

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在のtrapped値（OR演算で更新）

    Returns:
        HandlerReturn: True（trapped）
    """
    return HandlerReturn(True, value | True)


def ねむけ_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
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
        # ねむり状態を付与 (1~3ターン)
        ctx.source.apply_ailment(battle, "ねむり")
    return HandlerReturn(True)


def ねをはる_check_trapped(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ねをはる状態による交代制限

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在のtrapped値（OR演算で更新）

    Returns:
        HandlerReturn: True（trapped）
    """
    return HandlerReturn(True, value | True)


def ひるみ_action(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ひるみ状態による行動不能判定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 行動不能の場合はFalse
    """
    if not ctx.target or not ctx.target.has_volatile("ひるみ"):
        return HandlerReturn(True)

    ctx.target.remove_volatile(battle.events, "ひるみ")
    battle.add_event_log(ctx.target, "はひるんで動けない！")
    return HandlerReturn(False, stop_event=True)


def ひるみ_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ひるみのターン終了時解除

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if ctx.source and ctx.source.has_volatile("ひるみ"):
        ctx.source.remove_volatile(battle.events, "ひるみ")
    return HandlerReturn(True)


def ふういん_before_move(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ふういんによる技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 封印された技の場合はvalue=None、それ以外はTrue
    """
    move = value
    if move is None or not ctx.target:
        return HandlerReturn(True)

    owner = battle.foe(ctx.target)
    if owner and owner.has_move(move.name):
        battle.add_event_log(ctx.target, f"はふういんで{move.name}が使えない！")
        return HandlerReturn(False, value=None, stop_event=True)

    return HandlerReturn(True)


def ほろびのうた_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ほろびのうたのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.tick_down_volatile(battle, "ほろびのうた")
    if not ctx.source.has_volatile("ほろびのうた"):
        # ひんしにする
        battle.modify_hp(ctx.source, v=-ctx.source.hp)
        battle.add_event_log(ctx.source, "はほろびのうたで倒れた！")
    return HandlerReturn(True)


def まもる_check_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まもるの保護判定

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 判定値

    Returns:
        HandlerReturn: 防御する場合True
    """
    if _protect_block(battle, ctx, value):
        return HandlerReturn(True, True)
    return HandlerReturn(False, value)


def まもる_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """まもる状態のターン終了時解除

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if "まもる" in ctx.source.volatiles:
        ctx.source.volatiles["まもる"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["まもる"]
    return HandlerReturn(True)


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
        return HandlerReturn(True, value * 8192 // 4096)
    return HandlerReturn(False, value)


def みちづれ_on_faint(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みちづれ状態のひんし時処理（相手もひんしにする）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if not ctx.attacker:
        return HandlerReturn(False)

    battle.modify_hp(ctx.attacker, v=-ctx.attacker.hp)
    return HandlerReturn(True)


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

    user.volatiles["みがわり"].sub_hp = cost
    return HandlerReturn(True)


def みがわり_before_damage_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりがダメージを肩代わりする

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: ダメージ量

    Returns:
        HandlerReturn: 肩代わりした場合はダメージを0にする
    """
    if not ctx.defender or not ctx.move or not value:
        return HandlerReturn(False, value)

    if not ctx.defender.has_volatile("みがわり"):
        return HandlerReturn(False, value)

    sub_hp = ctx.defender.volatiles["みがわり"].sub_hp
    if sub_hp <= 0:
        return HandlerReturn(False, value)

    if "ignore_substitute" in ctx.move.data.labels:
        return HandlerReturn(False, value)

    ctx.defender.volatiles["みがわり"].sub_hp -= value
    if ctx.defender.volatiles["みがわり"].sub_hp <= 0:
        ctx.defender.volatiles["みがわり"].sub_hp = 0
        ctx.defender.volatiles["みがわり"].unregister_handlers(battle.events, ctx.defender)
        del ctx.defender.volatiles["みがわり"]
        battle.add_event_log(ctx.defender, "のみがわりがこわれた！")
    return HandlerReturn(True, 0)


def みがわり_check_substitute(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """みがわりが変化技と特定の技を防ぐ

    ON_TRY_IMMUNE Priority 30 として実行され、みがわり状態のポケモンを保護します。
    変化技および ignore_substitute フラグのない技は防ぎます。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト（defender: みがわり状態のポケモン）
        value: 現在の判定値（他のハンドラからの継続値）

    Returns:
        HandlerReturn: 防ぐ場合はTrue、防がない場合はvalue（False通常）
    """
    if not ctx.defender or not ctx.move:
        return HandlerReturn(False, value)

    if not ctx.defender.has_volatile("みがわり"):
        return HandlerReturn(False, value)

    sub_hp = ctx.defender.volatiles["みがわり"].sub_hp
    if sub_hp <= 0:
        return HandlerReturn(False, value)

    if "ignore_substitute" in ctx.move.data.labels:
        return HandlerReturn(False, value)

    if ctx.move.data.power == 0 or ctx.move.category == "変化":
        return HandlerReturn(True, True)

    return HandlerReturn(False, value)


def キングシールド_check_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """キングシールドの保護判定と攻撃低下

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 判定値

    Returns:
        HandlerReturn: 防御する場合True
    """
    if not _protect_block(battle, ctx, value):
        return HandlerReturn(False, value)

    if ctx.attacker and ctx.move and "contact" in ctx.move.data.labels and ctx.move.category != "変化":
        battle.modify_stat(ctx.attacker, "A", -2, source=ctx.defender)
    return HandlerReturn(True, True)


def キングシールド_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """キングシールド状態のターン終了時解除

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if "キングシールド" in ctx.source.volatiles:
        ctx.source.volatiles["キングシールド"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["キングシールド"]
    return HandlerReturn(True)


def スレッドトラップ_check_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """スレッドトラップの保護判定と素早さ低下

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 判定値

    Returns:
        HandlerReturn: 防御する場合True
    """
    if not _protect_block(battle, ctx, value):
        return HandlerReturn(False, value)

    if ctx.attacker and ctx.move and "contact" in ctx.move.data.labels and ctx.move.category != "変化":
        battle.modify_stat(ctx.attacker, "S", -1, source=ctx.defender)
    return HandlerReturn(True, True)


def スレッドトラップ_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """スレッドトラップ状態のターン終了時解除

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if "スレッドトラップ" in ctx.source.volatiles:
        ctx.source.volatiles["スレッドトラップ"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["スレッドトラップ"]
    return HandlerReturn(True)


def タールショット_damage_modifier(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """タールショット状態でほのお技のダメージ補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: ダメージ補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move and ctx.move.type == "ほのお":
        return HandlerReturn(True, value * 8192 // 4096)
    return HandlerReturn(False, value)


def トーチカ_check_protect(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トーチカの保護判定とどく付与

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 判定値

    Returns:
        HandlerReturn: 防御する場合True
    """
    if not _protect_block(battle, ctx, value):
        return HandlerReturn(False, value)

    if ctx.attacker and ctx.move and "contact" in ctx.move.data.labels and ctx.move.category != "変化":
        common.apply_ailment(battle, ctx, value, "どく", target_spec="attacker:self", source_spec="defender:self")
    return HandlerReturn(True, True)


def トーチカ_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """トーチカ状態のターン終了時解除

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if "トーチカ" in ctx.source.volatiles:
        ctx.source.volatiles["トーチカ"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["トーチカ"]
    return HandlerReturn(True)


def マジックコート_before_damage(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """マジックコートによる変化技の跳ね返し

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値

    Returns:
        HandlerReturn: 変化技を跳ね返す
    """
    if not ctx.move or ctx.move.category != "変化":
        return HandlerReturn(False)

    if "reflectable" not in ctx.move.data.labels:
        return HandlerReturn(False)

    # 簡易反射: 元の効果を無効化
    return HandlerReturn(True, None, stop_event=True)


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

    if infatuated:
        battle.add_event_log(ctx.target, "はメロメロで動けない！")
        return HandlerReturn(False, stop_event=True)

    return HandlerReturn(True)


def ロックオン_accuracy(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ロックオン状態による必中化

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 命中率

    Returns:
        HandlerReturn: 必中の場合はNoneを返す
    """
    volatile = ctx.defender.volatiles.get("ロックオン") if ctx.defender else None
    if volatile and volatile.source is ctx.attacker:
        return HandlerReturn(True, None)
    return HandlerReturn(False, value)


def ロックオン_on_hit(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ロックオン状態の消費

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if not ctx.defender:
        return HandlerReturn(False)

    volatile = ctx.defender.volatiles.get("ロックオン")
    if volatile and volatile.source is ctx.attacker:
        volatile.unregister_handlers(battle.events, ctx.defender)
        del ctx.defender.volatiles["ロックオン"]
        return HandlerReturn(True)
    return HandlerReturn(False)


def ロックオン_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """ロックオンのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["ロックオン"].tick_down()
    if ctx.source.volatiles["ロックオン"].count <= 0:
        ctx.source.volatiles["ロックオン"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["ロックオン"]
    return HandlerReturn(True)


def バインド_before_switch(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バインド状態による交代制限

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在のtrapped値（OR演算で更新）

    Returns:
        HandlerReturn: ゴーストタイプ以外はTrue（trapped）
    """
    # ゴーストタイプは交代可能（trappedに影響しない）
    if "ゴースト" in ctx.source.types:
        return HandlerReturn(True, value)

    # ログはハンドラシステムで自動出力される
    return HandlerReturn(True, value | True)


def バインド_source_switch_out(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バインド使用者の交代時に対象のバインドを解除

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    # 交代するポケモン（source）がバインドの使用者の場合、相手のバインドを解除
    # 全ポケモンのバインド状態をチェック
    for player in battle.players:
        for pokemon in player.team:
            if "バインド" in pokemon.volatiles:
                volatile = pokemon.volatiles["バインド"]
                # このバインドの使用者が交代するポケモンなら解除
                if hasattr(volatile, 'source_pokemon') and volatile.source is ctx.source:
                    volatile.unregister_handlers(battle.events, pokemon)
                    del pokemon.volatiles["バインド"]
                    battle.add_event_log(pokemon, "のバインドが解けた！")
    return HandlerReturn(True)


def バインド_turn_end(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """バインド状態のターン終了時ダメージ

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    # ターンカウント減少
    ctx.source.volatiles["バインド"].tick_down()

    if ctx.source.volatiles["バインド"].count <= 0:
        ctx.source.volatiles["バインド"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["バインド"]
        battle.add_event_log(ctx.source, "はバインド状態から解放された！")
        return HandlerReturn(True)

    # ダメージ適用（1/8、拘束バンドで1/6）
    # Note: 拘束バンドの判定はアイテム実装後に追加予定
    denom = 8
    damage = max(1, ctx.source.max_hp // denom)
    battle.modify_hp(ctx.source, v=-damage)
    battle.add_event_log(ctx.source, "はバインドのダメージを受けた！")

    return HandlerReturn(True)


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


def 急所ランク_calc_critical(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    """急所ランク状態による急所補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 急所ランク

    Returns:
        HandlerReturn: 補正後の急所ランク
    """
    volatile = ctx.attacker.volatiles.get("きゅうしょアップ") if ctx.attacker else None
    if not volatile:
        return HandlerReturn(False, value)

    bonus = max(1, volatile.count)
    return HandlerReturn(True, value + bonus)
