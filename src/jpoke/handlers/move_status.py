"""変化技関連のイベントハンドラ関数を提供するモジュール。

変化技の実行に関連するハンドラ関数を提供します。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.enums import Event, LogCode
from jpoke.core import HandlerReturn
from .move import (
    apply_ailment_to_defender,
    apply_volatile_to_attacker,
    apply_volatile_to_defender,
    modify_attacker_stats,
    modify_defender_stats,
)


def on_blow_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の効果を防げるかを判定する。"""
    value = battle.events.emit(Event.ON_TRY_BLOW, ctx, value)
    if not value:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED,
                             payload={"reason": "強制交代無効"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def blow(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の効果を発動する。

    ほえる、ふきとばしなどで、相手を強制的に交代させます。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 吹き飛ばしが成功した場合はTrue、失敗した場合はFalse
    """
    player = battle.get_player(ctx.defender)
    state = battle.player_states[player]
    commands = battle.get_available_switch_commands(player)
    success = bool(commands)
    if success:
        command = battle.random.choice(commands)
        battle.run_switch(player, state.team[command.index])
    return HandlerReturn(value=success)


def アンコール_can_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    move = ctx.defender.executed_move
    if not move:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "アンコール"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def アンコール_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """アンコールの効果を発動する。"""
    move = ctx.defender.executed_move
    return apply_volatile_to_defender(battle, ctx, value, volatile="アンコール",
                                      count=3, move_name=move.name)


def いたみわけ_equalize_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """両者の現在HPを平均化する。"""
    shared_hp = (ctx.attacker.hp + ctx.defender.hp) // 2

    battle.modify_hp(
        ctx.attacker,
        v=shared_hp - ctx.attacker.hp,
        reason="pain_split",
    )
    battle.modify_hp(
        ctx.defender,
        v=shared_hp - ctx.defender.hp,
        reason="pain_split",
    )
    return HandlerReturn(value=value)


def すりかえ_swap_items(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """すりかえ・トリックのアイテム交換効果。"""
    success = battle.swap_items(move=ctx.move)
    return HandlerReturn(value=success)


def ちいさくなる_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちいさくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"EVA": 2}, source=mon)
    battle.volatile_manager.apply(mon, "ちいさくなる")
    return HandlerReturn(value=value)


def まるくなる_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まるくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"B": 1}, source=mon)
    battle.volatile_manager.apply(mon, "まるくなる")
    return HandlerReturn(value=value)


def みがわり_check(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みがわりが使用可能かを判定する。"""
    mon = ctx.attacker
    if (
        mon.has_volatile("みがわり")
        or mon.hp <= mon.max_hp // 4
    ):
        battle.add_event_log(mon, LogCode.MOVE_FAILED,
                             payload={"reason": "みがわり"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def みがわり_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """みがわりの効果を発動する。"""
    mon = ctx.attacker
    battle.volatile_manager.apply(mon, "みがわり", hp=mon.max_hp // 4)
    return HandlerReturn(value=value)


def あまいかおり_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"EVA": -2})


def あまえる_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": -2})


def いちゃもん_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="いちゃもん")


def いやなおと_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -2})


def うそなき_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def えんまく_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1})


def おにび_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど")


def かえんのまもり_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="かえんのまもり")


def かたくなる_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1})


def からにこもる_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1})


def キノコのほうし_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def きりばらい_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"EVA": -1})


def きんぞくおん_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def こうそくいどう_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 2})


def コットンガード_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 3})


def こわいかお_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -2})


def じこさいせい_heal_self(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じこさいせい: 最大HPの1/2を回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def しっぽをふる_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def じゅうりょく_activate_global_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.global_manager.activate("じゅうりょく", 5))


def ステルスロック_set_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ステルスロック: 相手側のフィールドにステルスロックを設置する。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("ステルスロック", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def すなあらし_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("すなあらし", 5, source=ctx.attacker))


def すなかけ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1})


def スレッドトラップ_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="スレッドトラップ")


def タールショット_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="タールショット")


def タールショット_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def てっぺき_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 2})


def でんじは_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def トーチカ_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="トーチカ")


def どくどく_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく")


def どくのこな_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def トリックルーム_activate_global_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["トリックルーム"].is_active:
        return HandlerReturn(value=manager.deactivate("トリックルーム"))
    return HandlerReturn(value=manager.activate("トリックルーム", 5))


def ドわすれ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"D": 2})


def なきごえ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def ねむりごな_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def なみだめ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def にらみつける_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def ふういん_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ふういん")


def フェザーダンス_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -2})


def へびにらみ_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def ほたるび_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 3})


def マジックルーム_activate_global_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["マジックルーム"].is_active:
        return HandlerReturn(value=manager.deactivate("マジックルーム"))
    return HandlerReturn(value=manager.activate("マジックルーム", 5))


def まもる_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="まもる")


def みきり_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="まもる")


def みちづれ_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="みちづれ")


def ロックオン_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ロックオン", count=2)


def ロックカット_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 2})


def わるだくみ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 2})


def ワンダールーム_activate_global_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["ワンダールーム"].is_active:
        return HandlerReturn(value=manager.deactivate("ワンダールーム"))
    return HandlerReturn(value=manager.activate("ワンダールーム", 5))


def キングシールド_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="キングシールド")
