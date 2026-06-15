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


def アクアリング_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="アクアリング")


def アロマミスト_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"D": 1})


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


def いとをはく_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いとをはくの効果: 相手のすばやさを 2 段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"S": -2})


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


def ちょうはつ_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちょうはつの効果: 相手にちょうはつ状態を付与する（3 ターン）。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ちょうはつ")


def ちょうのまい_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ちょうのまいの効果: 自分のとくこう・とくぼう・すばやさを 1 段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1, "D": 1, "S": 1})


def まるくなる_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """まるくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"B": 1}, source=mon)
    battle.volatile_manager.apply(mon, "まるくなる")
    return HandlerReturn(value=value)


def めいそう_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1, "D": 1})


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


def あくび_can_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あくびの失敗チェック: 対象がねむけ状態または状態異常を持っている場合は失敗する。"""
    mon = ctx.defender
    if mon.has_volatile("ねむけ") or mon.ailment.is_active:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "あくび"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def あくび_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あくびの効果: 相手をねむけ状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ねむけ", count=1)


def あくまのキッス_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あくまのキッスの効果: 相手をねむり状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def あさのひざし_heal_self(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あさのひざし: 天候に応じた割合で自分のHPを回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    weather = battle.weather
    if weather.sunny:
        r = 2 / 3
    elif weather.name in {"あめ", "おおあめ", "すなあらし", "ゆき"}:
        r = 1 / 4
    else:
        r = 1 / 2
    battle.modify_hp(mon, r=r)
    return HandlerReturn(value=value)


def あやしいひかり_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あやしいひかりの効果: 相手をこんらん状態にする（2〜5ターン）。"""
    count = battle.random.randint(2, 5)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, "こんらん", count=count, source=ctx.attacker, ctx=ctx
    ))


def あまいかおり_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"EVA": -2})


def あまえる_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": -2})


def あまごい_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("あめ", 5, source=ctx.attacker))


def いちゃもん_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="いちゃもん")


def いやなおと_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -2})


def うそなき_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def うたう_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """うたうの効果: 相手をねむり状態にする。音系の技のためみがわりを貫通する。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def えんまく_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1})


def エレキフィールド_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """エレキフィールド: 地形をエレキフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("エレキフィールド", 5))


def おいかぜ_set_side_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おいかぜ: 自陣営に「おいかぜ」を4ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("おいかぜ", 4):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おたけび_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おたけびの効果: 相手のこうげきととくこうを 1 段階ずつ下げる。音系の技のためみがわりを貫通する。"""
    return modify_defender_stats(battle, ctx, value, stats={"A": -1, "C": -1})


def おにび_can_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """おにびの失敗チェック: 対象が状態異常またはほのおタイプの場合は失敗する。"""
    mon = ctx.defender
    if mon.ailment.is_active or mon.has_type("ほのお"):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "おにび"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おにび_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど")


def かいでんぱ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """相手の特攻を2段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"C": -2})


def かえんのまもり_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="かえんのまもり")


def かげぶんしん_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かげぶんしんの効果: 自分の回避率を 1 段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"EVA": 1})


def かたくなる_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1})


def からにこもる_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1})


def からをやぶる_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1, "A": 2, "C": 2, "S": 2})


def きあいだめ_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="きゅうしょアップ")


def キノコのほうし_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def きりばらい_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"EVA": -1})


def きんぞくおん_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def くすぐる_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くすぐるの効果: 相手のこうげきとぼうぎょを 1 段階ずつ下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"A": -1, "B": -1})


def グラスフィールド_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """グラスフィールド: 地形をグラスフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("グラスフィールド", 5))


def こうごうせい_heal_self(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こうごうせい: 天候に応じた割合で自分のHPを回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    weather = battle.weather
    if weather.sunny:
        r = 2 / 3
    elif weather.name in {"あめ", "おおあめ", "すなあらし", "ゆき"}:
        r = 1 / 4
    else:
        r = 1 / 2
    battle.modify_hp(mon, r=r)
    return HandlerReturn(value=value)


def こうそくいどう_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 2})


def コスモパワー_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1, "D": 1})


def コットンガード_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 3})


def こわいかお_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -2})


def さいみんじゅつ_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """さいみんじゅつの効果: 相手をねむり状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def サイコフィールド_activate_terrain(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """サイコフィールド: 地形をサイコフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("サイコフィールド", 5))


def じこさいせい_heal_self(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じこさいせい: 最大HPの1/2を回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def しびれごな_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しびれごなの効果: 相手をまひ状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def しっぽをふる_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def じゅうりょく_activate_global_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.global_manager.activate("じゅうりょく", 5))


def しんぴのまもり_set_side_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しんぴのまもり: 自陣営に「しんぴのまもり」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("しんぴのまもり", 5):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


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


def せいちょう_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """せいちょう: 天候が晴れの時はこうげき・とくこうを2段階、通常時は1段階上げる。"""
    n = 2 if battle.weather.sunny else 1
    return modify_attacker_stats(battle, ctx, value, stats={"A": n, "C": n})


def タールショット_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="タールショット")


def タールショット_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def たてこもる_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """たてこもるの効果: 自分のぼうぎょを 2 段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"B": 2})


def つきのひかり_heal_self(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """つきのひかり: 天候に応じた割合で自分のHPを回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    weather = battle.weather
    if weather.sunny:
        r = 2 / 3
    elif weather.name in {"あめ", "おおあめ", "すなあらし", "ゆき"}:
        r = 1 / 4
    else:
        r = 1 / 2
    battle.modify_hp(mon, r=r)
    return HandlerReturn(value=value)


def てっぺき_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 2})


def つるぎのまい_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 2})


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


def とぐろをまく_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "B": 1, "ACC": 1})


def とける_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 2})


def ドわすれ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"D": 2})


def なきごえ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def なまける_heal_self(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """なまける: 最大HPの1/2を回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def ねむりごな_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def なみだめ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def ねばねばネット_set_side_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ねばねばネット: 相手陣営に「ねばねばネット」を設定する（永続）。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("ねばねばネット", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def にほんばれ_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("はれ", 5, source=ctx.attacker))


def にらみつける_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def ふういん_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ふういん")


def フェザーダンス_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -2})


def ひかりのかべ_set_side_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ひかりのかべ: 自陣営に「ひかりのかべ」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("ひかりのかべ", 5):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def へびにらみ_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def ほたるび_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 3})


def ビルドアップ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "B": 1})


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


def ゆきげしき_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("ゆき", 5, source=ctx.attacker))


def リフレクター_set_side_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リフレクター: 自陣営に「リフレクター」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("リフレクター", 5):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


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
