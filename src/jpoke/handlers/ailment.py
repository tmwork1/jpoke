from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext

from jpoke.types import RoleSpec
from jpoke.utils.math import apply_fixed_modifier
from jpoke.enums import LogCode
from jpoke.core.handler import Handler, HandlerReturn
from jpoke.core.log_payload import FailureLogPayload

class AilmentHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 allow_fainted_subject: bool = False):
        super().__init__(
            func=func,
            source="ailment",
            subject_spec=subject_spec,
            priority=priority,
            allow_fainted_subject=allow_fainted_subject,
        )


def こおり_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こおり状態による行動不能チェック。

    Champions仕様:
    - わざを出す直前に25%の確率で解凍（SV以前は20%）
    - 行動不能2回の後（3回目の行動時）は必ず解凍
    - self_thawフラグを持つ技（ハイドロスチーム・フレアドライブ等）を選択した場合は、
      この確率判定を行わずに素通りする。解凍自体は各技のON_TRY_ACTIONハンドラ
      （priority=170、こんらん等の行動不能判定より後）で確定的に行われる
      （.internal/spec/turn.md Event.ON_TRY_ACTION参照）。
    """
    mon = ctx.attacker

    # self_thaw技を選択した場合は確率判定をスキップし、後段のハンドラに解凍を委ねる
    if ctx.move.has_flag("self_thaw"):
        return HandlerReturn(value=value)

    # 3回目の行動時は必ず解凍（elapsed_turns >= 2 = 既に2回行動不能）
    if mon.ailment.elapsed_turns >= 2:
        battle.ailment_manager.remove(mon)
        return HandlerReturn(value=True)

    # テスト用に確率を固定できる
    if battle.test_option.trigger_ailment is not None:
        thaw = battle.test_option.trigger_ailment
    else:
        thaw = battle.random.random() < 0.25

    if thaw:
        # 解凍した：ハンドラを解除して空の状態に
        battle.ailment_manager.remove(mon)
        return HandlerReturn(value=True)

    # まだ凍っている：行動不能カウントを増やす
    battle.ailment_manager.tick(mon)
    battle.add_event_log(
        ctx.attacker, LogCode.ACTION_BLOCKED,
        payload=FailureLogPayload(move=ctx.move.name, display_reason="こおり")
    )
    return HandlerReturn(value=False, stop_event=True)


def こおり_cure_by_thaw_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほのおタイプの攻撃技、またはthawラベルを持つ技でダメージを受けたら解凍する。

    ほのおタイプの攻撃技（第三世代以降）はすべて解凍対象となるため、ctx.move.typeを
    直接判定する（ウェザーボール等、命中時点でほのおタイプに変化している技も対象になる。
    逆にそうでん状態・ノーマルスキン等で元がほのおタイプの技が別タイプに変わった場合は
    ctx.move.typeがほのお以外になるため解凍しない）。
    ほのおタイプ技による解凍はタイプ由来の効果であり追加効果に該当しないため、
    ちからずくの影響を受けない。一方、シャカシャカほう/スチームバースト/
    ねっさのだいち/ねっとう（第六世代以降）等、ほのお以外のタイプでこの効果を
    持つ技のうち「secondary_effect」フラグを持つもの（＝ちからずく対象技）は
    追加効果として扱われるため、使用者がちからずくの場合はこの効果が発動しない
    （りんぷんの影響は受けない）。
    ハイドロスチームは「secondary_effect」フラグを持たずちからずくの対象技
    ではないため、使用者がちからずくでもこの効果は常に発動する
    （.internal/spec/moves/ハイドロスチーム.md参照）。
    """
    if ctx.move.type != "ほのお" and not ctx.move.has_flag("thaw"):
        return HandlerReturn(value=value)
    if (
        ctx.move.type != "ほのお"
        and ctx.move.has_flag("secondary_effect")
        and ctx.attacker.ability.name == "ちからずく"
    ):
        return HandlerReturn(value=value)
    battle.ailment_manager.remove(ctx.defender)
    return HandlerReturn(value=value)


def どく_damage(battle: Battle, ctx: EventContext, value: Any):
    """どく状態によるターン終了時ダメージ（最大HPの1/8、最小1）。"""
    mon = ctx.source
    damage = max(1, mon.max_hp // 8)
    battle.modify_hp(mon, v=-damage, reason="poison")
    return HandlerReturn(value=value)


def ねむり_check_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねむり状態による行動不能チェック"""
    mon = ctx.attacker
    if mon.sleep_talk_active:
        # ねごとのサブ実行中は、選ばれた技の ON_TRY_ACTION でも本ハンドラが
        # 再度発火するが、ねむりのカウント消費は1ターンに1回のみで良いため
        # （ねごと自身の ON_TRY_ACTION 時点ですでに消費済み）、ここでは何もしない。
        return HandlerReturn(value=True)

    if ctx.move.name not in ["いびき", "ねごと"] and mon.has_volatile("こんらん"):
        # こんらん状態のポケモンが眠っている間は、いびき・ねごと以外を選んでも
        # こんらんの自傷判定が行われない代わりに、ねむりのカウントも消費されない
        # （Wiki: 「眠っている間はこんらんで自傷することはなく、眠りカウントも
        # 消費されない。ただし、いびき・ねごとを使用したときはこんらんの判定が
        # 行われる」）。
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload=FailureLogPayload(move=ctx.move.name, display_reason="ねむり"))
        return HandlerReturn(value=False, stop_event=True)

    battle.ailment_manager.tick(mon)
    if not mon.has_ailment("ねむり"):
        # 眠りから覚めた：ハンドラを解除して空の状態に
        battle.ailment_manager.remove(mon)
        return HandlerReturn(value=True)

    if ctx.move.name in ["いびき", "ねごと"]:
        return HandlerReturn(value=True)

    # まだ眠っている
    battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                         payload=FailureLogPayload(move=ctx.move.name, display_reason="ねむり"))

    return HandlerReturn(value=False, stop_event=True)


def まひ_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（12.5%確率）。

    Champions仕様: 行動不能率は12.5%（SV以前の25%から変更）。
    """
    # テスト用に確率を固定できる
    if battle.test_option.trigger_ailment is not None:
        trigger = battle.test_option.trigger_ailment
    else:
        trigger = battle.random.random() < 0.125

    if trigger:
        battle.add_event_log(ctx.attacker, LogCode.ACTION_BLOCKED,
                             payload=FailureLogPayload(move=ctx.move.name, display_reason="まひ"))
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def まひ_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """まひ状態による素早さ半減"""
    return HandlerReturn(value=value // 2)


def もうどく_damage(battle: Battle, ctx: EventContext, value: Any):
    """もうどく状態によるターン終了時ダメージ（経過ターンに比例して増加）。

    ダメージ量: max(1, 最大HP × min(15, 経過ターン数) // 16)
    経過ターン数の上限は15（最大ダメージは最大HP × 15/16）。
    """
    mon = ctx.source
    battle.ailment_manager.tick(mon)
    turns = min(15, mon.ailment.elapsed_turns)
    damage = max(1, mon.max_hp * turns // 16)
    battle.modify_hp(mon, v=-damage, reason="poison")
    return HandlerReturn(value=value)


def やけど_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """やけど状態によるターン終了時ダメージ（最大HPの1/16、最小1）。"""
    mon = ctx.source
    damage = max(1, mon.max_hp // 16)
    battle.modify_hp(mon, v=-damage, reason="burn")
    return HandlerReturn(value=value)


def やけど_modifier(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """やけど状態による物理技ダメージ半減。

    こんらんの自傷ダメージ（内部技名"_こんらん"）は物理技扱いだが、
    第五世代以降はやけどによる半減の影響を受けないため対象外とする。
    """
    if ctx.move.name == "_こんらん":
        return HandlerReturn(value=value)
    if battle.query.resolve_move_category(ctx.attacker, ctx.move) == "physical":
        value = apply_fixed_modifier(value, 2048)
    return HandlerReturn(value=value)
