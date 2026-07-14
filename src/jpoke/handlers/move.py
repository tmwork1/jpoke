"""技関連のハンドラ基盤モジュール。

MoveHandler クラスと攻撃技・変化技ハンドラ共通のユーティリティ関数を提供します。
攻撃技ハンドラは move_attack.py、変化技ハンドラは move_status.py を参照してください。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, AttackContext, Player
    from jpoke.types import RoleSpec, Stat, AilmentName, VolatileName

from jpoke.core.handler import Handler, HandlerReturn
from jpoke.core.log_payload import FailureLogPayload
from jpoke.enums import Command, LogCode


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
            priority=priority,
            skip_subject_check=True,  # 技ハンドラはコンテキストの攻守を直接参照するため、主体の照合をスキップする
        )


def modify_attacker_stats(battle: Battle,
                          ctx: AttackContext,
                          value: Any,
                          stats: dict[Stat, int],
                          chance: float = 1) -> HandlerReturn:
    """攻撃側の能力ランクを変化させる。

    ON_HIT（攻撃技、value=実際のダメージ量）では value をそのまま次のハンドラへ
    引き継ぐ必要があるため、ランク変化の結果を value に反映させない。
    ON_STATUS_HIT（変化技、value=bool の成否フラグ）では、ランク変化が完全に
    阻まれた（結果が空の dict）場合に技を失敗させるため、従来通り
    battle.modify_stats() の戻り値を value として返す。

    自分自身への効果（target="attacker"）はりんぷん・おんみつマントで防げないため、
    resolve_secondary_chance に target="attacker" を指定する。
    """
    chance = battle.resolve_secondary_chance(ctx, chance, target="attacker")
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    result = battle.modify_stats(ctx.attacker, stats, source=ctx.attacker)
    if isinstance(value, bool):
        return HandlerReturn(value=result)
    return HandlerReturn(value=value)


def modify_defender_stats(battle: Battle,
                          ctx: AttackContext,
                          value: Any,
                          stats: dict[Stat, int],
                          chance: float = 1) -> HandlerReturn:
    """防御側の能力ランクを変化させる。

    modify_attacker_stats と同様、value の型（bool か否か）でON_STATUS_HITと
    ON_HITを区別し、ON_HITでは value（実際のダメージ量）を保持したまま返す。

    防御側がこの技のダメージで瀕死になった場合、能力ランク変化の追加効果は
    適用しない（実機仕様。AilmentManager.apply / VolatileManager.apply の
    瀕死ガードと同様）。
    """
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    if ctx.defender.fainted:
        result = {}
    else:
        result = battle.modify_stats(ctx.defender, stats, source=ctx.attacker)
    if isinstance(value, bool):
        return HandlerReturn(value=result)
    return HandlerReturn(value=value)


def apply_ailment_to_defender(battle: Battle,
                              ctx: AttackContext,
                              value: Any,
                              ailment: AilmentName,
                              count: int | None = None,
                              chance: float = 1) -> HandlerReturn:
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.ailment_manager.apply(
        ctx.defender, ailment, count=count, source=ctx.attacker
    ))


def apply_volatile_to_attacker(battle: Battle,
                               ctx: AttackContext,
                               value: Any,
                               volatile: VolatileName,
                               count: int | None = None,
                               chance: float = 1,
                               **kwargs) -> HandlerReturn:
    """自分自身への効果（target="attacker"）はりんぷん・おんみつマントで防げないため、
    resolve_secondary_chance に target="attacker" を指定する。
    """
    chance = battle.resolve_secondary_chance(ctx, chance, target="attacker")
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.attacker, volatile, count=count, source=ctx.attacker, **kwargs
    ))


def apply_volatile_to_defender(battle: Battle,
                               ctx: AttackContext,
                               value: Any,
                               volatile: VolatileName,
                               count: int | None = None,
                               chance: float = 1,
                               **kwargs) -> HandlerReturn:
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, volatile, count=count, source=ctx.attacker, **kwargs
    ))


def apply_confusion_to_defender(battle: Battle,
                               ctx: AttackContext,
                               value: Any,
                               chance: float = 1) -> HandlerReturn:
    """こんらん状態をランダムターン数（2〜5）で防御者に付与するヘルパー。"""
    chance = battle.resolve_secondary_chance(ctx, chance)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def get_forced_switch_commands(battle: Battle, player: Player) -> list[Command]:
    """強制交代技（ほえる・ふきとばし・ともえなげ・ドラゴンテール等）用の交代先候補を取得する。

    にげられない・バインド・フェアリーロックや特性かげふみ・ありじごく・じりょくによる
    交代制限を無視して発動するため、通常の交代可否判定
    （`CommandManager.get_available_switch_commands`）は使わず、控えの生存ポケモンから
    直接コマンドを構築する。ねをはる・きゅうばん等の無効化は呼び出し側で
    `Event.ON_TRY_BLOW` を通して別途判定する。
    """
    state = battle.player_states[player]
    bench = state.bench
    return [
        Command.get_switch_command(i)
        for i, mon in enumerate(state.team)
        if mon in bench and mon.alive
    ]


def gravity_restricted_fail(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうりょく中にこの技を失敗させる。

    gravity_restricted フラグを持つ技に登録し、
    じゅうりょくが有効な場合に技を失敗させる。
    """
    if battle.get_global_field("じゅうりょく").is_active:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="じゅうりょく")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def charge_into_volatile(battle: Battle,
                         ctx: AttackContext,
                         value: Any,
                         volatile: VolatileName) -> HandlerReturn:
    """半透明技の1ターン目：揮発状態を付与して技を停止する。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在のイベント値
        volatile: 付与する揮発状態名（技名と同一）

    Returns:
        HandlerReturn: ためターンなら False/stop_event=True、2ターン目なら value をそのまま返す
    """
    attacker = ctx.attacker
    if not attacker.has_volatile(volatile):
        # move_name には実際に使用した技名（ctx.move.name）を渡す。
        # とびはねる等、揮発状態名（volatile）と使用技名が異なるケースがあるため、
        # 2ターン目に強制実行すべき技名は volatile 引数ではなく ctx.move.name を使う。
        battle.volatile_manager.apply(
            attacker, volatile, count=1, source=attacker, move_name=ctx.move.name
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)
