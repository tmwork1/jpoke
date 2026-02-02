from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.utils.type_defs import RoleSpec, LogPolicy
from jpoke.utils.enums import Event, EventControl
from jpoke.core.event import Handler, HandlerReturn
from . import common


class VolatileHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "source:self",
                 log: LogPolicy = "on_success",
                 priority: int = 100):
        super().__init__(func, subject_spec, "volatile", log, None, priority)


def こんらん_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こんらん状態による自傷ダメージ判定（33%確率）

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 自傷した場合はFalse（行動中断）、しなかった場合はTrue
    """
    # ターンカウント減少（1～4ターンで自然治癒）
    ctx.target.volatiles["こんらん"].tick_down()
    if ctx.target.volatiles["こんらん"].count <= 0:
        ctx.target.volatiles["こんらん"].unregister_handlers(battle.events, ctx.target)
        del ctx.target.volatiles["こんらん"]
        battle.add_event_log(ctx.target, f"の混乱が解けた！")
        return HandlerReturn(True)

    # テスト用に確率を固定できる
    if battle.test_option.ailment_trigger_rate is not None:
        confused = battle.test_option.ailment_trigger_rate >= 0.33
    else:
        confused = battle.random.random() < 0.33

    if confused:
        # 自傷ダメージ計算（威力40の物理技、タイプ相性なし）
        # レベル補正: (2 * level / 5 + 2)
        level_factor = (2 * ctx.target.level / 5 + 2)
        # 威力40
        power = 40
        # 攻撃と防御の比率
        attack = ctx.target.stats["A"]
        defense = ctx.target.stats["D"]
        # ベースダメージ
        base_damage = int(level_factor * power * attack / defense / 50) + 2
        # ランダム補正（85～100%）
        random_factor = battle.random.randint(85, 100) / 100
        damage = int(base_damage * random_factor)

        # ダメージ適用
        actual_damage = battle.modify_hp(ctx.target, v=-damage)
        if actual_damage:
            battle.add_event_log(ctx.target, "は混乱している！")
            battle.add_event_log(ctx.target, "は自分を攻撃した！")
        return HandlerReturn(False, control=EventControl.STOP_EVENT)

    battle.add_event_log(ctx.target, "は混乱している！")
    return HandlerReturn(True)


def ちょうはつ_before_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちょうはつによる変化技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
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
        return HandlerReturn(False, value=None, control=EventControl.STOP_EVENT)

    return HandlerReturn(True)


def ちょうはつ_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちょうはつのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["ちょうはつ"].tick_down()
    if ctx.source.volatiles["ちょうはつ"].count <= 0:
        ctx.source.volatiles["ちょうはつ"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["ちょうはつ"]
        battle.add_event_log(ctx.source, "のちょうはつが解けた！")
    return HandlerReturn(True)


def バインド_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バインド状態のターン終了時ダメージ

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
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
    # TODO: 拘束バンド判定を追加
    denom = 8
    damage = max(1, ctx.source.max_hp // denom)
    battle.modify_hp(ctx.source, v=-damage)
    battle.add_event_log(ctx.source, "はバインドのダメージを受けた！")

    return HandlerReturn(True)


def バインド_before_switch(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バインド状態による交代制限

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: 現在のtrapped値（OR演算で更新）

    Returns:
        HandlerReturn: ゴーストタイプ以外はTrue（trapped）
    """
    # ゴーストタイプは交代可能（trappedに影響しない）
    if "ゴースト" in ctx.source.types:
        return HandlerReturn(True, value)

    # ログはハンドラシステムで自動出力される
    return HandlerReturn(True, value | True)


def メロメロ_action(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メロメロ状態による行動不能判定（50%確率）

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 行動不能の場合はFalse、行動可能の場合はTrue
    """
    # テスト用に確率を固定できる
    if battle.test_option.ailment_trigger_rate is not None:
        infatuated = battle.test_option.ailment_trigger_rate >= 0.5
    else:
        infatuated = battle.random.random() < 0.5

    if infatuated:
        battle.add_event_log(ctx.target, "はメロメロで動けない！")
        return HandlerReturn(False, control=EventControl.STOP_EVENT)

    return HandlerReturn(True)


def かなしばり_before_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かなしばりによる技の使用禁止

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
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
            return HandlerReturn(False, value=None, control=EventControl.STOP_EVENT)

    return HandlerReturn(True)


def かなしばり_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かなしばりのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["かなしばり"].tick_down()
    if ctx.source.volatiles["かなしばり"].count <= 0:
        ctx.source.volatiles["かなしばり"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["かなしばり"]
        battle.add_event_log(ctx.source, "のかなしばりが解けた！")
    return HandlerReturn(True)


def バインド_source_switch_out(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バインド使用者の交代時に対象のバインドを解除

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
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
                if hasattr(volatile, 'source_pokemon') and volatile.source_pokemon is ctx.source:
                    volatile.unregister_handlers(battle.events, pokemon)
                    del pokemon.volatiles["バインド"]
                    battle.add_event_log(pokemon, "のバインドが解けた！")
    return HandlerReturn(True)


def あめまみれ_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あめまみれのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["あめまみれ"].tick_down()
    if ctx.source.volatiles["あめまみれ"].count <= 0:
        ctx.source.volatiles["あめまみれ"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["あめまみれ"]
        battle.add_event_log(ctx.source, "のあめまみれが解けた！")
    return HandlerReturn(True)


def かいふくふうじ_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かいふくふうじのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["かいふくふうじ"].tick_down()
    if ctx.source.volatiles["かいふくふうじ"].count <= 0:
        ctx.source.volatiles["かいふくふうじ"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["かいふくふうじ"]
        battle.add_event_log(ctx.source, "のかいふくふうじが解けた！")
    return HandlerReturn(True)


def じごくずき_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じごくずきのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["じごくずき"].tick_down()
    if ctx.source.volatiles["じごくずき"].count <= 0:
        ctx.source.volatiles["じごくずき"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["じごくずき"]
        battle.add_event_log(ctx.source, "のじごくずきが解けた！")
    return HandlerReturn(True)


def じゅうでん_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じゅうでんのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["じゅうでん"].tick_down()
    if ctx.source.volatiles["じゅうでん"].count <= 0:
        ctx.source.volatiles["じゅうでん"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["じゅうでん"]
        battle.add_event_log(ctx.source, "のじゅうでんが解けた！")
    return HandlerReturn(True)


def でんじふゆう_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """でんじふゆうのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["でんじふゆう"].tick_down()
    if ctx.source.volatiles["でんじふゆう"].count <= 0:
        ctx.source.volatiles["でんじふゆう"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["でんじふゆう"]
        battle.add_event_log(ctx.source, "のでんじふゆうが解けた！")
    return HandlerReturn(True)


def にげられない_check_trapped(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """にげられない状態による交代制限

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: 現在のtrapped値（OR演算で更新）

    Returns:
        HandlerReturn: True（trapped）
    """
    return HandlerReturn(True, value | True)


def ねむけ_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねむけのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["ねむけ"].tick_down()
    if ctx.source.volatiles["ねむけ"].count <= 0:
        # ねむり状態に移行する処理が必要
        ctx.source.volatiles["ねむけ"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["ねむけ"]
        battle.add_event_log(ctx.source, "は眠ってしまった！")
        # TODO: ねむり状態に移行させる
    return HandlerReturn(True)


def ねをはる_check_trapped(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねをはる状態による交代制限

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: 現在のtrapped値（OR演算で更新）

    Returns:
        HandlerReturn: True（trapped）
    """
    return HandlerReturn(True, value | True)


def ほろびのうた_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ほろびのうたのターン経過処理

    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 常にTrue
    """
    ctx.source.volatiles["ほろびのうた"].tick_down()
    if ctx.source.volatiles["ほろびのうた"].count <= 0:
        ctx.source.volatiles["ほろびのうた"].unregister_handlers(battle.events, ctx.source)
        del ctx.source.volatiles["ほろびのうた"]
        # ひんしにする
        battle.modify_hp(ctx.source, v=-ctx.source.hp)
        battle.add_event_log(ctx.source, "はほろびのうたで倒れた！")
    return HandlerReturn(True)
