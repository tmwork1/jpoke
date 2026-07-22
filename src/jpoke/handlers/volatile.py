"""揮発状態ハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext

from jpoke.types import RoleSpec, Stat, AilmentName, VolatileName, MoveName

from jpoke.enums import Event, Command, LogCode
from jpoke.core.handler import Handler, HandlerReturn
from jpoke.core.log_payload import (
    VolatilePayload, FailureLogPayload, MoveActionPayload, AilmentPayload,
)
from jpoke.utils.math import apply_fixed_modifier

HIDDEN_MOVE_ALLOWED_MOVES: dict[VolatileName, list[MoveName]] = {
    "あなをほる": ["じしん", "マグニチュード"],
    "そらをとぶ": ["かぜおこし", "たつまき", "かみなり", "ぼうふう", "うちおとす"],
    "ダイビング": ["なみのり", "うずしお"],
    "シャドーダイブ": [],
}

class VolatileHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "source:self",
                 priority: int = 100,
                 once: bool = False,
                 allow_fainted_subject: bool = False):
        super().__init__(
            func=func,
            source="volatile",
            subject_spec=subject_spec,
            priority=priority,
            once=once,
            allow_fainted_subject=allow_fainted_subject,
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

    Note:
        ログ記録は battle.volatile_manager.remove() 内で行われるため、
        ここで重複してログを記録しない（reason はそちらへ渡す）。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）
        volatile: 対象の揮発状態名
        reason: 解除理由
    """
    mon = getattr(ctx, "source", None) or getattr(ctx, "attacker", None)
    battle.volatile_manager.remove(mon, volatile, reason=reason)
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

    攻撃側・防御側いずれかがノーガードを持つ場合は、あなをほる等の技限定の
    回避判定を経由せず必ず命中する（.internal/spec/abilities/ノーガード.md参照）。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の判定値
        volatile: 対象の揮発状態名（技名と同一）
    Returns:
        HandlerReturn: 命中可ならTrue、回避するならFalse
    """
    # AttackContext.defender は技のtargetに関わらず常にfoe(attacker)が設定されるため、
    # こらえる等のtarget="self"の技では「相手を狙っていない」のにdefenderが相手（潜伏中の
    # ポケモン）と一致してしまう。この回避判定は相手を直接狙う技（target="foe"）にのみ
    # 適用する（自分自身や場・自陣を対象とする技は潜伏による回避の対象外）。
    if ctx.move.target != "foe":
        return HandlerReturn(value=value)
    # のろいはMoveData.target="foe"固定だが、使用者がゴーストタイプでない場合（鈍い）は
    # 自分のランク変化のみで相手に直接効果を及ぼさないため、潜伏による回避判定の対象外とする
    # （ゴーストタイプののろい＝呪いは相手を対象にするため対象外にしない）。
    if ctx.move.name == "のろい" and not ctx.attacker.has_type("ゴースト"):
        return HandlerReturn(value=value)
    if ctx.attacker.ability.name == "ノーガード" or ctx.defender.ability.name == "ノーガード":
        return HandlerReturn(value=value)
    allowed_moves = HIDDEN_MOVE_ALLOWED_MOVES.get(volatile, [])
    if ctx.move.name not in allowed_moves:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_MISSED,
            payload=FailureLogPayload(move=ctx.move.name)
        )
        ctx.missed_hidden_target = True
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
            (can_switch and cmd.is_switch)
            or (cmd.is_move and mon.moves[cmd.index].name == fixed_move_name)
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def アクアリング_self_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アクアリング状態のターン終了時回復（最大HPの1/16、最小1）。"""
    mon = ctx.source
    heal = max(1, mon.max_hp // 16)
    heal = battle.events.emit(Event.ON_CALC_DRAIN, ctx, heal)
    return HandlerReturn(value=battle.modify_hp(mon, v=heal, source=mon))


def あなをほる_boost_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あなをほる状態の相手に対して じしん・マグニチュード の威力を2倍にする。"""
    if ctx.move.name in ("じしん", "マグニチュード"):
        value *= 2
    return HandlerReturn(value=value)


def あなをほる_can_hit_hidden_target(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あなをほる状態の回避判定"""
    return can_hit_hidden_target(battle, ctx, value, "あなをほる")


def あなをほる_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あなをほる状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="あなをほる")


def あばれる_tick(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あばれる状態のターン経過処理

    Event.ON_HIT（「ダメージ発生後の処理。みがわりに被弾しても発動」）に
    登録する。みがわりに被弾した場合も技自体は正常に命中・実行された
    ものとして扱われるため、Event.ON_DAMAGE_HIT（みがわり等で実ダメージが
    0の場合は発火しない）ではなくこちらに登録する必要がある。

    2ターン目以降の forced continuation ターンで、この揮発性状態自身が
    登録するハンドラとして呼ばれる。初回付与ターン分のカウント消費は
    move_attack.あばれる_apply がこの関数を直接呼び出して処理する。

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
        battle.volatile_manager.apply_confusion(mon)
    return HandlerReturn(value=value)


def あめまみれ_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あめまみれのターン経過処理

    仕様: 3ターンの間、毎ターン終了時にすばやさを1段階下げる。
    S-1を先に適用し、その後カウントを減らす（count=1の最終ターンもS-1を発動させるため）。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn:
    """
    mon = ctx.source
    battle.modify_stats(mon, {"spe": -1}, source=mon, reason="あめまみれ")
    battle.volatile_manager.tick(mon, "あめまみれ")
    return HandlerReturn(value=value)


def アンコール_modify_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アンコールによる技の固定

    まねっこ・ねごと・ゆびをふる・さいはい等のサブ技実行としてネストされた
    run_move呼び出し中は固定技への強制差し替えを行わない。差し替えてしまうと、
    まねっこ等がコピー・選択した技が固定技（アンコールされた技自身）と異なる
    場合に、その技の実行中に再度このハンドラが発火して固定技へ差し戻され、
    battle.run_moveが際限なく再帰してRecursionErrorになる
    （使用者自身が新たに技を選択し直したわけではなく、既に選択済みの技の
    効果としてサブ技実行が行われているだけなので、アンコールによる固定を
    適用すべきでない）。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 固定技以外の場合は差し替える
    """
    if battle.move_executor.is_nested_move_execution:
        return HandlerReturn(value=value)
    mon = ctx.attacker
    volatile = mon.volatiles["アンコール"]
    move = mon.get_move(volatile.move_name)
    return HandlerReturn(value=move)


def アンコール_restrict_commands(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return restrict_commands(battle, ctx, value, name="アンコール")


def アンコール_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="アンコール")


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
            not cmd.is_move
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


def エレクトロビーム_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """エレクトロビーム溜め状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="エレクトロビーム")


def おんねん_deplete_attacking_move_pp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おんねん状態のひんし時処理（相手の技PPを0にする）

    発動しない条件:
    - すでにPPが0になっている技
    - non_onnen ラベルを持つ技（わるあがき等）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    if ctx.move.pp == 0 or ctx.move.has_flag("non_onnen"):
        return HandlerReturn(value=value)
    depleted_pp = ctx.move.pp
    ctx.move.pp = 0
    battle.add_event_log(
        ctx.attacker,
        LogCode.PP_CONSUMED,
        payload=MoveActionPayload(move=ctx.move.name, value=depleted_pp, display_reason="おんねん")
    )
    return HandlerReturn(value=value)


def おんねん_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="おんねん")


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
    if value <= 0:
        # ヘドロえき等により回復がダメージへ変換済みの場合はブロック対象外
        # （相手がかいふくふうじ状態であってもヘドロえきのダメージ効果は発動する）。
        return HandlerReturn(value=value)

    battle.add_event_log(
        ctx.target, LogCode.HEAL_BLOCKED,
        payload=FailureLogPayload(display_reason="かいふくふうじ")
    )
    return HandlerReturn(value=0)


def かいふくふうじ_modify_command_options(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かいふくふうじによるコマンドオプション変更

    第六世代以降、かいふくふうじ状態のポケモンは「heal」フラグを持つ技
    （じこさいせい等の回復技、ドレインキッスやギガドレイン等のHP吸収技、すなあつめ等）を
    コマンド選択レベルで除外する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: 新しいコマンドオプションのリスト
    """
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move
            or not ctx.source.moves[cmd.index].has_flag("heal")
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def かいふくふうじ_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="かいふくふうじ")


def かいふくふうじ_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かいふくふうじによる回復技・HP吸収技の使用禁止

    第六世代以降、かいふくふうじ状態のポケモンは「heal」フラグを持つ技
    （じこさいせい等の回復技、ドレインキッスやギガドレイン等のHP吸収技）を選択できない。
    行動前にかいふくふうじ状態にされた場合もその技は失敗する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: heal フラグを持つ技の場合はvalue=False（使用禁止）、それ以外はTrue
    """
    if ctx.move.has_flag("heal"):
        battle.add_event_log(
            ctx.attacker, LogCode.ACTION_BLOCKED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="かいふくふうじ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def かえんのまもり_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かえんのまもりの保護判定。接触した相手をやけど状態にする"""
    return _run_protect(battle, ctx, value, ailment_on_contact="やけど", protect_non_attack=False)


def かえんのまもり_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="かえんのまもり")


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
            not cmd.is_move
            or ctx.source.moves[cmd.index].name != forbidden_name
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def かなしばり_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="かなしばり")


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
        battle.add_event_log(
            ctx.attacker, LogCode.ACTION_BLOCKED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="かなしばり")
        )
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


def きょけんとつげき_double_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きょけんとつげき状態: 相手から受ける技のダメージを2倍にする。

    ダメージ固定技は威力計算を経由しないため対象外となる。
    """
    return HandlerReturn(value=apply_fixed_modifier(value, 8192))


def きょけんとつげき_guaranteed_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きょけんとつげき状態: 相手から受ける技が必ず命中する（一撃必殺技も含む）。"""
    return HandlerReturn(value=None, stop_event=True)


def きょけんとつげき_remove(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """きょけんとつげき状態: 自身の行動が始まるタイミングで解除する。"""
    return remove_volatile(battle, ctx, value, volatile="きょけんとつげき")


def キングシールド_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """キングシールドの保護判定。攻撃技のみ防ぎ、接触した相手の攻撃ランクを1段階下げる"""
    return _run_protect(battle, ctx, value, stats_change_on_contact={"atk": -1}, protect_non_attack=False)


def キングシールド_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="キングシールド")


def くちばしキャノン_burn_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くちばしキャノンの加熱中に接触技を受けた場合、その攻撃者を即座にやけど状態にする。

    Event.ON_DAMAGE_HIT はヒットのたびに発火するため、加熱している間（ON_TRY_ACTION で
    解除されるまで）に自分より先に行動した相手から接触技を受けた時点でやけどを付与する。
    """
    if battle.query.is_contact_reaction(ctx):
        battle.ailment_manager.apply(ctx.attacker, "やけど", source=ctx.defender)
    return HandlerReturn(value=value)


def くちばしキャノン_end_heating(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くちばしキャノンの加熱を終了する。

    使用者自身の行動開始時点（Event.ON_TRY_ACTION、まひ等の行動可否判定より前の
    priority=5）で解除することで、自分より後に行動する相手の接触技には反応しない
    （加熱は自分が行動するまでの間のみ有効）。行動開始前に交代・瀕死等で行動が
    発生しなかった場合のフォールバックとして Event.ON_TURN_END でも解除する。
    """
    return remove_volatile(battle, ctx, value, volatile="くちばしキャノン")


def こだわり_restrict_commands(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return restrict_commands(battle, ctx, value, name="こだわり")


def こらえる_endure(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """こらえる状態: 致死ダメージを HP 1 残しに補正する。

    ダメージが防御側の現在 HP 以上の場合、ダメージを hp - 1 に抑えて HP 1 を残す。
    すでに HP1 の場合は実際のダメージが0になるが、攻撃自体は命中しているため
    「攻撃を無効化した」扱いにはならない（きあいパンチ不発・ダメおし威力2倍の対象）。
    """
    mon = ctx.defender
    if value >= mon.hp:
        if mon.hp <= 1:
            mon.hits_taken += 1
        value = mon.hp - 1
    return HandlerReturn(value=value)


def こらえる_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="こらえる")


def ころがる_boost_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ころがる状態: これまでの連続命中回数に応じて威力を2^count倍にする（30→60→120→240→480）。"""
    volatile = ctx.attacker.volatiles.get("ころがる")
    if volatile is not None:
        value *= 2 ** volatile.count
    return HandlerReturn(value=value)


def ころがる_check_interrupt(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ころがる状態: このターンの行動が失敗していた場合、強制行動を中断する。

    外れ・まもるによる無効化・状態異常等での不発など、いずれの場合も
    Pokemon.failed_or_immobile_last_turn が True になるため、これを判定基準にする。
    """
    mon = ctx.source
    if mon.failed_or_immobile_last_turn:
        return remove_volatile(battle, ctx, value, volatile="ころがる", reason="ミス・行動失敗")
    return HandlerReturn(value=value)


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

    if not mon.has_volatile("こんらん"):
        # このターンでこんらんが解除された場合、自傷判定を行わず通常通り行動できる
        return HandlerReturn(value=True)

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
        move="_こんらん",
    )

    # 動けない理由のログを先に記録してから自傷ダメージを適用する
    # （modify_hpが致死ダメージの場合、内部でflush_winner_logが即座に発火し
    # 勝敗確定ログがこのログを追い越してしまうため）
    battle.add_event_log(
        ctx.attacker, LogCode.ACTION_BLOCKED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="こんらん")
    )
    # 自傷ダメージの適用
    battle.modify_hp(ctx.attacker, v=-damage, reason="self_attack")
    return HandlerReturn(value=False, stop_event=True)


def コールドフレア_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """コールドフレア状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="コールドフレア")


def ゴッドバード_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ゴッドバード溜め状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="ゴッドバード")


def さわぐ_apply_to_new_opponent(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さわぐ継続中に新しく場に出た相手にもさわがしいを付与する。

    「さわぐ状態のポケモンがいる間は、場のポケモン全員がねむり状態になれない」
    （.internal/spec/volatiles/さわぐ.md）という仕様に対し、さわがしいはさわぐ開始時
    （ON_VOLATILE_START）にその時点の相手にのみ一度だけ付与される実装のため、
    さわぐ継続中に相手が瀕死交代・通常交代で入れ替わると、新しく出てきた相手に
    さわがしいが付与されないまま漏れ、ねむるが成功してしまっていた（fuzzログ
    seed=1823で発見）。
    """
    new_mon = ctx.source
    holder = battle.foe(new_mon)
    count = holder.volatiles["さわぐ"].count
    battle.volatile_manager.apply(new_mon, "さわがしい", count=count)
    return HandlerReturn(value=value)


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
        battle.add_event_log(
            ctx.target,
            LogCode.AILMENT_PREVENTED,
            payload=AilmentPayload(ailment=value, display_reason="さわぐ"),
        )
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)


def さわぐ_remove_さわがしい(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さわぐ状態が解除されたときの処理（相手のさわがしいも解除する）

    ON_VOLATILE_END は対象ポケモンの何らかの揮発性状態が解除されたことを表す共通
    イベントであり、解除された揮発性状態名が value に渡される。value がさわぐ自身
    でない場合は何もしない（無関係な揮発性状態の解除でさわぐがまだ有効なのに
    相手のさわがしいが誤って解除されるのを防ぐ）。
    """
    if value != "さわぐ":
        return HandlerReturn(value=value)
    foe = battle.foe(ctx.source)
    battle.volatile_manager.remove(foe, "さわがしい")
    return HandlerReturn(value=value)


def さわぐ_start(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さわぐ状態を付与し、場のねむり状態を解除する。

    第五世代以降: さわぎだした瞬間に場のねむり状態のポケモンが全員目を覚ます。
    ねむけ状態はさわぐでは解除されない。
    """
    # 相手にさわがしい状態を付与
    foe = battle.foe(ctx.source)
    count = ctx.source.volatiles["さわぐ"].count
    battle.volatile_manager.apply(foe, "さわがしい", count=count)

    # 場のポケモンのねむり状態を解除（ねむけは解除しない）
    for mon in battle.actives:
        if mon.fainted:
            continue
        if mon.has_ailment("ねむり"):
            battle.ailment_manager.remove(mon)

    return HandlerReturn(value=True)


def さわぐ_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="さわぐ")


def しおづけ_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しおづけ状態のターン終了時ダメージ

    Champions仕様:
    - 通常: 最大HPの 1/16（小数点以下切り捨て）
    - みず・はがねタイプ: 最大HPの 1/8（小数点以下切り捨て）

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: ダメージが発生した場合True
    """
    mon = ctx.source
    r = -1/16
    if mon.has_type("みず") or mon.has_type("はがね"):
        r *= 2
    battle.modify_hp(mon, r=r)
    return HandlerReturn(value=value)


def シャドーダイブ_can_hit_hidden_target(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """シャドーダイブ状態の回避判定"""
    return can_hit_hidden_target(battle, ctx, value, "シャドーダイブ")


def シャドーダイブ_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """シャドーダイブ状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="シャドーダイブ")


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
            not cmd.is_move
            or not ctx.source.moves[cmd.index].has_flag("sound")
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def じごくづき_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="じごくづき")


def じごくづき_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じごくづき状態による技の不発"""
    if ctx.move.has_flag("sound"):
        battle.add_event_log(
            ctx.attacker, LogCode.ACTION_BLOCKED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="じごくづき")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def じゅうでん_boost_electric(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def スレッドトラップ_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スレッドトラップの保護判定。攻撃技のみ防ぎ、接触した相手の素早さランクを1段階下げる"""
    return _run_protect(battle, ctx, value, stats_change_on_contact={"spe": -1}, protect_non_attack=False)


def スレッドトラップ_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="スレッドトラップ")


def そうでん_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """そうでん状態による技タイプ変換: 攻撃側の使う技をでんきタイプに変換する。

    わるあがきはでんきタイプに変換されない。
    """
    if ctx.move and ctx.move.name != "わるあがき":
        return HandlerReturn(value="でんき")
    return HandlerReturn(value=value)


def そうでん_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """そうでん状態のターン終了処理: ターン終了時に無条件で解除する。"""
    battle.volatile_manager.remove(ctx.source, "そうでん")
    return HandlerReturn(value=value)


def そらをとぶ_boost_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """そらをとぶ状態の相手に対して かぜおこし・たつまき の威力を2倍にする。"""
    if ctx.move.name in ("かぜおこし", "たつまき"):
        value *= 2
    return HandlerReturn(value=value)


def そらをとぶ_can_hit_hidden_target(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """そらをとぶ状態の回避判定"""
    return can_hit_hidden_target(battle, ctx, value, "そらをとぶ")


def そらをとぶ_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """そらをとぶ状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="そらをとぶ")


def ソーラービーム_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ソーラービーム溜め状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="ソーラービーム")


def ソーラーブレード_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ソーラーブレード溜め状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="ソーラーブレード")


def タールショット_boost_fire(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """タールショット状態でほのお技のタイプ相性補正を2倍にする。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト（AttackContext）
        value: タイプ相性補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move.type == "ほのお":
        value *= 2
    return HandlerReturn(value=value)


def ダイビング_boost_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ダイビング状態の相手に対して なみのり・うずしお の威力を2倍にする。"""
    if ctx.move.name in ("なみのり", "うずしお"):
        value *= 2
    return HandlerReturn(value=value)


def ダイビング_can_hit_hidden_target(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ダイビング状態の回避判定"""
    return can_hit_hidden_target(battle, ctx, value, "ダイビング")


def ダイビング_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ダイビング状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="ダイビング")


def ちいさくなる_boost_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちいさくなる状態への威力補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 威力補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move.has_flag("minimize"):
        value *= 2
    return HandlerReturn(value=value)


def ちいさくなる_guaranteed_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちいさくなる状態への必中補正

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 命中率

    Returns:
        HandlerReturn: 必中の場合はNoneを返す
    """
    if ctx.move.has_flag("minimize"):
        return HandlerReturn(value=None, stop_event=True)
    return HandlerReturn(value=value)


def ちょうはつ_modify_command_options(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちょうはつによるコマンドオプション変更

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: コマンドオプションのリスト

    Returns:
        HandlerReturn: 新しいコマンドオプションのリスト
    """
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move
            or ctx.source.moves[cmd.index].category != "status"
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def ちょうはつ_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="ちょうはつ")


def ちょうはつ_try_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちょうはつによる変化技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 使用しようとしている技（Move）

    Returns:
        HandlerReturn: 変化技の場合はvalue=None（使用禁止）、攻撃技の場合はTrue
    """
    if ctx.move.category == "status":
        battle.add_event_log(
            ctx.attacker, LogCode.ACTION_BLOCKED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ちょうはつ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def デカハンマー_modify_command_options(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
    """デカハンマー揮発状態: 前のターンにデカハンマーのPPを消費していた場合、
    コマンド選択肢からデカハンマーを除外する。
    """
    mon = ctx.source
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move
            or mon.moves[cmd.index].name != "デカハンマー"
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def デカハンマー_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """デカハンマー揮発状態のターン経過処理（count: 2→1→0 で自動解除）。"""
    return tick_volatile(battle, ctx, value, volatile="デカハンマー")


def でんじふゆう_check_floating(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """でんじふゆう状態での浮遊判定（常に浮遊）"""
    return HandlerReturn(value=True)


def でんじふゆう_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="でんじふゆう")


def とくせいなし_disable_ability(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """とくせいなし付与時に特性を無効化する。"""
    battle.add_ability_disabled_reason(ctx.source, "とくせいなし")
    return HandlerReturn(value=value)


def とくせいなし_enable_ability(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """とくせいなし終了時に特性有効状態を再計算する。

    ON_VOLATILE_END は対象ポケモンの何らかの揮発性状態が解除されたことを表す共通
    イベントであり、解除された揮発性状態名が value に渡される。value がとくせいなし
    自身でない場合は何もしない（無関係な揮発性状態の解除でとくせいなしがまだ有効な
    のに特性が誤って再有効化されるのを防ぐ）。

    交代退場処理中（remove_all_volatiles によるとくせいなしの強制解除）は特性を
    再有効化しない。デルタストリーム等のON_ABILITY_ENABLEDで発動する天候形成特性が、
    退場処理の途中（ON_SWITCH_OUTでの解除機会をとくせいなしで無効化されたまま
    逃した後）に一時的に再発動し、天候が解除されないまま残留してしまうのを防ぐ
    （ほろびのうた・ねむけと同じ switching_out_mon ガードの考え方。fuzzログ
    seed=1730で発見: デルタストリーム持ちがとくせいなし状態のまま退場すると
    らんきりゅうが解除されなくなっていた）。
    """
    if value != "とくせいなし":
        return HandlerReturn(value=value)
    if battle.switch_manager.switching_out_mon is ctx.source:
        return HandlerReturn(value=value)
    battle.remove_ability_disabled_reason(ctx.source, "とくせいなし")
    return HandlerReturn(value=value)


def トーチカ_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """トーチカの保護判定。接触した相手をどく状態にする"""
    return _run_protect(battle, ctx, value, ailment_on_contact="どく")


def トーチカ_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="トーチカ")


def にげられない_remove_on_foe_switch(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """にげられない状態の解除処理（にげられない状態を与えた相手が場を離れたときに解除する）

    バインド状態の`バインド_remove`と同じパターン。シングルバトルでは「foe」が
    常に対戦相手の場のポケモン1体のみを指すため、くらいつくの相互付与（自分・相手の
    双方が『にげられない』状態を持つ場合）でも、片方が場を離れればもう片方の
    『にげられない』状態が正しく解除される。

    はいすいのじんによる自己付与（source=自分）の場合は、相手が場を離れても解除されない
    （使用時に相手だったポケモンが場を離れても、この技によるにげられない状態は継続する）。
    move_name で自己付与かどうかを判定する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    foe = battle.foe(ctx.source)
    if not foe.has_volatile("にげられない"):
        return HandlerReturn(value=value)
    if foe.volatiles["にげられない"].move_name == "はいすいのじん":
        return HandlerReturn(value=value)
    battle.volatile_manager.remove(foe, "にげられない")
    return HandlerReturn(value=value)


def ニードルガード_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ニードルガードの保護判定。接触した相手の最大HPの1/8ダメージを与える。"""
    return _run_protect(battle, ctx, value, chip_on_contact=1/8)


def ニードルガード_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="ニードルガード")


def ねむけ_remove_and_apply_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねむけを解除してねむりを付与する。

    Champions 仕様: count=2（確率1/3）または count=3（確率2/3）。
    交代によるねむけ解除の場合はねむりを付与しない。

    ON_VOLATILE_END は対象ポケモンの何らかの揮発性状態が解除されたことを表す共通
    イベントであり、解除された揮発性状態名が value に渡される。value がねむけ自身
    でない場合は何もしない（無関係な揮発性状態の解除に反応してねむけがまだ有効な
    のに眠らせてしまうのを防ぐ）。あわせて value をそのまま返し、同じ
    ON_VOLATILE_END チェーンにある他ハンドラ（value を参照するもの）に誤った値が
    伝播しないようにする。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 解除された揮発性状態名

    Returns:
        HandlerReturn: value をそのまま返す
    """
    if value != "ねむけ":
        return HandlerReturn(value=value)
    # 交代退場処理中のポケモンはねむりを付与しない
    if battle.switch_manager.switching_out_mon is ctx.source:
        return HandlerReturn(value=value)
    # Champions仕様: count=2が1/3、count=3が2/3
    # AilmentManager.apply でも同じ分布で自動決定されるが、ねむけ→ねむり移行は明示指定
    count = 2 if battle.random.random() < 1 / 3 else 3
    battle.ailment_manager.apply(ctx.source, "ねむり", count=count)
    return HandlerReturn(value=value)


def ねむけ_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="ねむけ")


def ねをはる_block_blow(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねをはる状態: 強制交代技（ほえる・ふきとばし・ともえなげ・ドラゴンテール等）の効果を防ぐ。"""
    return HandlerReturn(value=False, stop_event=True)


def ねをはる_check_floating(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねをはる状態では浮遊しない（地面に根を張っているため）"""
    return HandlerReturn(value=False, stop_event=True)


def ねをはる_self_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねをはる状態のターン終了時回復（最大HPの1/16、切り捨て）。

    かいふくふうじ状態では ON_MODIFY_HEAL 経由でブロックされる。
    """
    heal = max(1, ctx.source.max_hp // 16)
    heal = battle.events.emit(Event.ON_CALC_DRAIN, ctx, heal)
    return HandlerReturn(value=battle.modify_hp(ctx.source, v=heal, source=ctx.source))


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


def はねやすめ_remove_flying(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """はねやすめ volatile 付与時: ひこうタイプを removed_types に追加する。"""
    mon = ctx.source
    if "ひこう" not in mon.removed_types:
        mon.removed_types.append("ひこう")
    return HandlerReturn(value=value)


def はねやすめ_restore_flying(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """はねやすめ volatile 解除時 (ターン終了): ひこうタイプを復帰する。"""
    mon = ctx.source
    if "ひこう" in mon.removed_types:
        mon.removed_types.remove("ひこう")
    battle.volatile_manager.remove(mon, "はねやすめ")
    return HandlerReturn(value=value)


def ハロウィン_add_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ハロウィン付与時: ゴーストタイプを added_types に追加する。"""
    if "ゴースト" not in ctx.source.added_types:
        ctx.source.added_types.append("ゴースト")
    return HandlerReturn(value=value)


def ハロウィン_remove_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ハロウィン解除時: added_types からゴーストタイプを除去する。

    ON_VOLATILE_END は対象ポケモンの何らかの揮発性状態が解除されたことを表す共通
    イベントであり、解除された揮発性状態名が value に渡される。value がハロウィン
    自身でない場合は何もしない（無関係な揮発性状態の解除でハロウィンがまだ有効なのに
    ゴーストタイプが誤って外れるのを防ぐ）。
    """
    if value != "ハロウィン":
        return HandlerReturn(value=value)
    if "ゴースト" in ctx.source.added_types:
        ctx.source.added_types.remove("ゴースト")
    return HandlerReturn(value=value)


def バインド_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バインド状態のターン終了時ダメージ

    ダメージ倍率はバインド付与時に確定済み（`bind_damage_ratio`）のため、ここでは
    しめつけバンド等の再判定は行わない。

    バインドを付与した側（現在の相手）が既に瀕死になっている場合はダメージを
    与えずそのまま解除する。瀕死交代（`SwitchManager.run_faint_switch`）は
    `Event.ON_TURN_END`より後に実行される実装のため、同ターンの行動フェーズで
    トラッパーが瀕死になっていても、このイベント時点ではまだ
    `Event.ON_SWITCH_OUT`経由の正規の解除処理（`バインド_remove`）が走っていない
    （fuzzログ seed=1750で発見: トラッパーが瀕死になった同じターンにもう1回分の
    残りダメージが適用されていた）。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    mon = ctx.source

    if battle.foe(mon).fainted:
        battle.volatile_manager.remove(mon, "バインド")
        return HandlerReturn(value=value)

    # ターンカウント減少
    battle.volatile_manager.tick(mon, "バインド")
    if not mon.has_volatile("バインド"):
        return HandlerReturn(value=value)

    # ダメージ適用
    r = mon.volatiles["バインド"].bind_damage_ratio
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
    battle.add_event_log(
        ctx.attacker, LogCode.ACTION_BLOCKED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="ひるみ")
    )
    return HandlerReturn(value=False, stop_event=True)


def ひるみ_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="ひるみ")


def _is_protect_candidate(ctx: EventContext, protect_non_attack: bool, is_blocked: bool) -> bool:
    """技がそもそもまもる系の保護判定の対象になり得るかを判定する。

    自分自身・味方・場を対象とする技（例: ねむる・つるぎのまい）は、実際の対戦でも
    まもる側の保護判定自体が発生せず、関連するログも一切表示されない。ここで False を
    返した場合、`_run_protect` はログを出さずに技をそのまま継続させる
    （「まもるは失敗した」等の紛らわしいログを防ぐ）。

    is_blocked: 対象となる技かどうかの判定結果（まもるは`ctx.move.is_blocked_by_protect`、
    ワイドガードは`ctx.move.is_blocked_by_wide_guard`を呼び出し側が渡す）。
    """
    return (
        (protect_non_attack or ctx.move.is_attack)
        and is_blocked
    )

def _run_protect(battle: Battle,
                 ctx: EventContext,
                 value: Any,
                 stats_change_on_contact: dict[Stat, int] | None = None,
                 ailment_on_contact: AilmentName | None = None,
                 chip_on_contact: float | None = None,
                 protect_non_attack: bool = True,
                 is_blocked: bool | None = None) -> HandlerReturn:
    """protect系の共通骨格。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値
        stats_change_on_contact: 接触時に攻撃者に与えるランク変化（例: {"atk": -1}）
        ailment_on_contact: 接触時に攻撃者に付与する状態異常名
        chip_on_contact: 接触時に攻撃者の最大HPから削る割合（例: 1/8）
        protect_non_attack: False の場合、変化技を保護しない
        is_blocked: 対象技かどうかの判定結果。省略時は`ctx.move.is_blocked_by_protect`
            （target=="foe"の技）を使う。ワイドガードは`ctx.move.is_blocked_by_wide_guard`
            （"spread"フラグを持つ技）を明示的に渡す。
    """
    if is_blocked is None:
        is_blocked = ctx.move.is_blocked_by_protect

    if not _is_protect_candidate(ctx, protect_non_attack, is_blocked):
        # 保護判定の対象外の技（自分・味方・場対象の技等）はログを出さずスルーする
        return HandlerReturn(value=value)

    if not battle.events.emit(Event.ON_CHECK_PROTECT, ctx, True):
        battle.add_event_log(
            ctx.defender, LogCode.PROTECT_FAILED,
            payload=MoveActionPayload(move=ctx.move.name)
        )
        return HandlerReturn(value=value)

    battle.add_event_log(
        ctx.defender, LogCode.PROTECT_SUCCEEDED,
        payload=MoveActionPayload(move=ctx.move.name)
    )

    if battle.query.is_contact_reaction(ctx):
        if stats_change_on_contact:
            battle.modify_stats(ctx.attacker, stats_change_on_contact, source=ctx.defender)
        if ailment_on_contact:
            battle.ailment_manager.apply(ctx.attacker, ailment_on_contact, source=ctx.defender)
        if chip_on_contact is not None:
            battle.modify_hp(ctx.attacker, r=-chip_on_contact, reason="")

    # だいばくはつ等の自爆技はまもる系にブロックされてもHPコストを支払い必ずひんしになる
    # 必要がある（.internal/spec/moves/だいばくはつ.md）。しめりけによる失敗（HPコスト
    # 支払い前に失敗すべき）と区別するため、move_executor が参照するフラグを立てる。
    ctx.blocked_by_protect = True

    return HandlerReturn(value=False, stop_event=True)


def ファストガード_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ファストガードの保護判定。priority≥1の先制技のみブロックする。

    いたずらごころ・はやてのつばさ等による動的な優先度変化も考慮するため、
    技データの静的な priority ではなく `speed_calculator.calc_move_priority` で
    実効優先度を算出して判定する（`じょおうのいげん_block_priority` と同じパターン）。
    """
    effective_priority = battle.speed_calculator.calc_move_priority(ctx.attacker, ctx.move)
    if effective_priority < 1:
        return HandlerReturn(value=value)
    return _run_protect(battle, ctx, value)


def ファストガード_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="ファストガード")


def ふういん_try_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふういん状態のポケモンと共通する技を相手が使えないようにする。"""
    if ctx.defender.has_move(ctx.move.name):
        battle.add_event_log(
            ctx.attacker, LogCode.ACTION_BLOCKED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ふういん")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def フリーズボルト_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """フリーズボルト状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="フリーズボルト")


def ブラッドムーン_modify_command_options(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
    """ブラッドムーン揮発状態: 前のターンにブラッドムーンのPPを消費していた場合、
    コマンド選択肢からブラッドムーンを除外する。
    """
    mon = ctx.source
    new_options = []
    for cmd in value:
        if (
            not cmd.is_move
            or mon.moves[cmd.index].name != "ブラッドムーン"
        ):
            new_options.append(cmd)
    return HandlerReturn(value=new_options)


def ブラッドムーン_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ブラッドムーン揮発状態のターン経過処理（count: 2→1→0 で自動解除）。"""
    return tick_volatile(battle, ctx, value, volatile="ブラッドムーン")


def ほろびのうた_faint(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ほろびのうたでひんしになる処理。マジックガードでも防げない。

    ON_VOLATILE_END は「対象ポケモンの何らかの揮発性状態が解除された」ことを表す
    共通イベントであり、解除された揮発性状態名が value に渡される。対象ポケモンが
    ほろびのうた以外の揮発性状態（ちょうはつ・ころがる等）を同ターン中に解除した
    場合にもこのハンドラは呼ばれるため、value がほろびのうた自身でない場合は
    何もしない（そうしないと無関係な揮発性状態の解除に反応して即座にひんしに
    なってしまう）。

    ON_VOLATILE_END はカウント0による自然解除だけでなく、交代（remove_all_volatiles）
    による強制解除でも発火する。交代退場処理中はひんしにせず、状態変化を消滅させるのみとする
    （.internal/spec/volatiles/ほろびのうた.md「交代によって解除される」「バトンタッチによって
    引き継がれる」）。
    """
    if value != "ほろびのうた":
        return HandlerReturn(value=value)
    mon = ctx.source
    if battle.switch_manager.switching_out_mon is mon:
        return HandlerReturn(value=value)
    battle.modify_hp(mon, v=-mon.hp, reason="perish")
    return HandlerReturn(value=value)


def ほろびのうた_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="ほろびのうた")


def マジックコート_reflect(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """マジックコートによる変化技の跳ね返し"""
    return HandlerReturn(value=ctx.move.is_reflectable)


def マジックコート_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マジックコート状態のターン終了時解除"""
    return remove_volatile(battle, ctx, value, volatile="マジックコート")


def まほうのこな_clear_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まほうのこな解除時: volatile_override_type を None に戻す。

    ON_VOLATILE_END は対象ポケモンの何らかの揮発性状態が解除されたことを表す共通
    イベントであり、解除された揮発性状態名が value に渡される。value がまほうのこな
    自身でない場合は何もしない（みずびたし_clear_type と同様、無関係な揮発性状態の
    解除でタイプ変更が誤って巻き戻るのを防ぐ）。
    """
    if value != "まほうのこな":
        return HandlerReturn(value=value)
    ctx.source.volatile_override_type = None
    return HandlerReturn(value=value)


def まほうのこな_set_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まほうのこな付与時: volatile_override_type をエスパーに設定し added_types をクリアする。"""
    ctx.source.volatile_override_type = "エスパー"
    ctx.source.added_types.clear()
    return HandlerReturn(value=value)


def まもる_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まもるの保護判定"""
    return _run_protect(battle, ctx, value)


def まもる_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="まもる")


def まるくなる_boost_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まるくなる状態で特定技の威力補正

    まるくなる状態のポケモンが ころがる・アイスボール を使うと威力が2倍になる。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 威力補正値（4096基準）

    Returns:
        HandlerReturn: 補正後の値
    """
    if ctx.move.name in ("ころがる", "アイスボール"):
        value *= 2
    return HandlerReturn(value=value)


def みがわり_block_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みがわりがダメージを肩代わりする"""
    damage = value
    if not battle.move_executor.check_hit_substitute(ctx):
        return HandlerReturn(value=damage)

    battle.add_event_log(
        ctx.defender, LogCode.SUBSTITUTE_HIT,
        payload=MoveActionPayload(move=ctx.move.name)
    )
    volatile = ctx.defender.volatiles["みがわり"]
    damage = min(volatile.hp, damage)
    volatile.hp -= damage
    assert volatile.hp >= 0, f"みがわりHPが負値: {volatile.hp}"

    # みがわりに与えたダメージをコンテキストに保存しておく（後の処理で使用するため）
    ctx.substitute_damage = damage

    # みがわり消滅
    if volatile.hp == 0:
        battle.volatile_manager.remove(ctx.defender, "みがわり")

    # 被ダメージは0とする
    return HandlerReturn(value=0)


def みがわり_immune(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みがわりによる技の無効化判定"""
    hit_substitute = battle.move_executor.check_hit_substitute(ctx)
    if (
        hit_substitute
        and ctx.move.category == "status"
    ):
        battle.add_event_log(
            ctx.defender, LogCode.MOVE_IMMUNED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="みがわり")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def みずびたし_clear_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みずびたし解除時: volatile_override_type を None に戻す。

    ON_VOLATILE_END は「対象ポケモンの何らかの揮発性状態が解除された」ことを表す
    共通イベントであり、解除された揮発性状態名が value に渡される。value がみずびたし
    自身でない場合（リチャージ等、無関係な揮発性状態が同ターン中に解除された場合）に
    このハンドラが反応すると、みずびたしがまだ有効なのに volatile_override_type が
    誤って解除され、本来の水タイプ判定（すなあらし免疫の再計算等）が壊れてしまう。
    seed=205 (LogInconsistency@handlers/field.py:すなあらし_turn_end) の原因。
    """
    if value != "みずびたし":
        return HandlerReturn(value=value)
    ctx.source.volatile_override_type = None
    return HandlerReturn(value=value)


def みずびたし_set_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みずびたし付与時: volatile_override_type をみずに設定し added_types をクリアする。"""
    ctx.source.volatile_override_type = "みず"
    ctx.source.added_types.clear()
    return HandlerReturn(value=value)


def みちづれ_faint(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みちづれ状態のひんし時処理（相手もひんしにする）。マジックガードでも防げない。"""
    mon = ctx.attacker
    battle.modify_hp(mon, v=-mon.hp, reason="perish")
    battle.add_event_log(
        mon, LogCode.VOLATILE_DISPLAY,
        payload=VolatilePayload(volatile="みちづれ")
    )
    return HandlerReturn(value=value)


def みちづれ_remove(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みちづれ状態の解除（自身の行動時に解除）。"""
    return remove_volatile(battle, ctx, value, volatile="みちづれ")


def めいちゅうアップ_boost_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """めいちゅうアップ: 次の技の命中率を1.2倍にし、効果を消費する。

    value が None の場合は既に必中状態が確定しているため、補正をかけずに効果のみ消費する。
    """
    mon = ctx.attacker
    battle.volatile_manager.remove(mon, "めいちゅうアップ")
    if value is None:
        return HandlerReturn(value=value)
    return HandlerReturn(value=apply_fixed_modifier(value, 4915))


def めいちゅうアップ_clear_after_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """めいちゅうアップ: 命中判定のない技を使ったときなど、
    ON_MODIFY_ACCURACYで消費されなかった場合でも行動完了時に効果を消す
    （ノーガード等のstop_eventでON_MODIFY_ACCURACY自体が発火しなかった場合を含む）。

    行動不能（状態異常・ひるみ等）や溜め技の溜めターンでは効果を維持する。
    """
    mon = ctx.attacker
    if not mon.has_volatile("めいちゅうアップ"):
        return HandlerReturn(value=value)
    executor = battle.move_executor
    if executor.action_success is False:
        return HandlerReturn(value=value)
    if (
        executor.move_success is None
        and executor.move_applied is None
        and not executor.move_missed
    ):
        return HandlerReturn(value=value)
    battle.volatile_manager.remove(mon, "めいちゅうアップ")
    return HandlerReturn(value=value)


def メテオビーム_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メテオビーム溜め状態の解除"""
    return remove_volatile(battle, ctx, value, volatile="メテオビーム")


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
    battle.add_event_log(
        ctx.attacker, LogCode.VOLATILE_DISPLAY,
        payload=VolatilePayload(volatile="メロメロ")
    )

    # テスト用に確率を固定できる
    if battle.test_option.trigger_volatile is not None:
        action_blocked = battle.test_option.trigger_volatile
    else:
        action_blocked = battle.random.random() < 0.5

    if action_blocked:
        battle.add_event_log(
            ctx.attacker, LogCode.ACTION_BLOCKED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="メロメロ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def もりののろい_add_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """もりののろい付与時: くさタイプを added_types に追加する。"""
    if "くさ" not in ctx.source.added_types:
        ctx.source.added_types.append("くさ")
    return HandlerReturn(value=value)


def もりののろい_remove_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """もりののろい解除時: added_types からくさタイプを除去する。

    ON_VOLATILE_END は対象ポケモンの何らかの揮発性状態が解除されたことを表す共通
    イベントであり、解除された揮発性状態名が value に渡される。value がもりののろい
    自身でない場合は何もしない（無関係な揮発性状態の解除でもりののろいがまだ有効な
    のにくさタイプが誤って外れるのを防ぐ）。
    """
    if value != "もりののろい":
        return HandlerReturn(value=value)
    if "くさ" in ctx.source.added_types:
        ctx.source.added_types.remove("くさ")
    return HandlerReturn(value=value)


def やどりぎのタネ_drain_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    from_mon = ctx.source
    to_mon = battle.foe(from_mon)
    damage = battle.modify_hp(from_mon, r=-1/8, reason="drain")
    # 吸収の受益者（to_mon）が同ターン内の別要因で既に瀕死になっている場合、
    # 回復を適用しない（ひんし後に回復してしまう不整合を防ぐ）
    if damage and not to_mon.fainted:
        # 回復量へのおおきなねっこ補正は、回復するポケモン（to_mon）の所持アイテムで判定する
        heal = battle.events.emit(Event.ON_CALC_DRAIN, ctx.derive(source=to_mon), -damage)
        battle.modify_hp(to_mon, v=heal, reason="drain")
    return HandlerReturn(value=damage)


def リチャージ_block_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リチャージ状態による次ターン行動不能。行動不能を示してから状態を解除する。"""
    mon = ctx.attacker
    battle.add_event_log(
        mon, LogCode.ACTION_BLOCKED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="リチャージ")
    )
    battle.volatile_manager.remove(mon, "リチャージ")
    return HandlerReturn(value=False, stop_event=True)


def れんぞくぎり_reset_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """れんぞくぎり揮発状態: ターン終了時に前ターンの技がれんぞくぎり以外なら揮発を解除する。"""
    mon = ctx.source
    if mon.last_move is None or mon.last_move.name != "れんぞくぎり":
        battle.volatile_manager.remove(mon, "れんぞくぎり")
    return HandlerReturn(value=value)


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


def ロックオン_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """相手が交代したときに自分のロックオン状態を解除する。"""
    mon = battle.foe(ctx.source)
    battle.volatile_manager.remove(mon, "ロックオン")
    return HandlerReturn(value=value)


def ロックオン_tick_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return tick_volatile(battle, ctx, value, volatile="ロックオン")


def ワイドガード_protect(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ワイドガードの保護判定。

    まもるは`target=="foe"`の技（is_blocked_by_protect）を防ぐが、ワイドガードは
    技データ上「複数のポケモンが対象になる技」であることを示す`"spread"`フラグ
    （is_blocked_by_wide_guard）を持つ技を防ぐ。判定基準が異なる点以外は
    まもる_protectと同じ`_run_protect`骨格を使う（ON_CHECK_PROTECTでの
    ふかしのこぶし等の貫通判定も共通）。
    """
    return _run_protect(battle, ctx, value, is_blocked=ctx.move.is_blocked_by_wide_guard)


def ワイドガード_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return remove_volatile(battle, ctx, value, volatile="ワイドガード")
