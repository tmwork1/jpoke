"""変化技関連のイベントハンドラ関数を提供するモジュール。

変化技の実行に関連するハンドラ関数を提供します。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, AttackContext

from jpoke.enums import Event, Interrupt, LogCode
from jpoke.core import HandlerReturn
from .move import (
    apply_ailment_to_defender,
    apply_volatile_to_attacker,
    apply_volatile_to_defender,
    modify_attacker_stats,
    modify_defender_stats,
)


def on_blow_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の効果を防げるかを判定する。"""
    value = battle.events.emit(Event.ON_TRY_BLOW, ctx, value)
    if not value:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_IMMUNED)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def blow(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def アクアリング_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="アクアリング")


def アンコール_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    move = ctx.defender.executed_move
    if not move:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "対象技が存在しない"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def アンコール_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アンコールの効果を発動する。"""
    move = ctx.defender.executed_move
    return apply_volatile_to_defender(battle, ctx, value, volatile="アンコール",
                                      count=3, move_name=move.name)


def いえき_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いえきの失敗条件を判定する。

    対象の特性が protected フラグを持つ場合は失敗させる。
    """
    if ctx.defender.ability.has_flag("protected"):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "保護された特性"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def いえき_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いえきの効果: 相手に「とくせいなし」状態を付与する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="とくせいなし")


def いとをはく_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いとをはくの効果: 相手のすばやさを 2 段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"S": -2})


def いたみわけ_equalize_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def いのちのしずく_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちのしずく: 最大HPの1/4を回復する。HPが満タンの場合は失敗する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/4)
    return HandlerReturn(value=value)


def いやしのはどう_heal_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いやしのはどう: 相手の最大HPの1/2を回復する。HPが満タンの場合は失敗する。"""
    mon = ctx.defender
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def いやしのねがい_faint_and_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いやしのねがい: 使用者をひんしにし、自陣営に「いやしのねがい」フィールドを設置する。

    次に場に出たポケモンの HP が全回復し、状態異常が回復する。
    PP は回復しない（みかづきのまいとの違い）。
    """
    mon = ctx.attacker
    side = battle.get_side(mon)
    side.activate("いやしのねがい", 1)
    battle.faint(mon)
    return HandlerReturn(value=value)


def すりかえ_swap_items(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すりかえ・トリックのアイテム交換効果。"""
    success = battle.swap_items()
    return HandlerReturn(value=success)


def ちいさくなる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちいさくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"EVA": 2}, source=mon)
    battle.volatile_manager.apply(mon, "ちいさくなる")
    return HandlerReturn(value=value)


def ちょうはつ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちょうはつの効果: 相手にちょうはつ状態を付与する（3 ターン）。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ちょうはつ", count=3)


def ちょうのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちょうのまいの効果: 自分のとくこう・とくぼう・すばやさを 1 段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1, "D": 1, "S": 1})


def まるくなる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まるくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"B": 1}, source=mon)
    battle.volatile_manager.apply(mon, "まるくなる")
    return HandlerReturn(value=value)


def めいそう_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1, "D": 1})


def みがわり_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def みがわり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みがわりの効果を発動する。"""
    mon = ctx.attacker
    battle.volatile_manager.apply(mon, "みがわり", hp=mon.max_hp // 4)
    return HandlerReturn(value=value)


def あくび_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あくびの失敗チェック: 対象がねむけ状態または状態異常を持っている場合は失敗する。"""
    mon = ctx.defender
    if mon.has_volatile("ねむけ") or mon.ailment.is_active:
        battle.add_event_log(
            ctx.attacker,
            LogCode.MOVE_FAILED,
            payload={"reason": "すでに状態異常になっている"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def あくび_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あくびの効果: 相手をねむけ状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ねむけ", count=2)


def あくまのキッス_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あくまのキッスの効果: 相手をねむり状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def あさのひざし_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あさのひざし: 天候に応じた割合で自分のHPを回復する。
    攻撃側がばんのうがさを持つ場合、晴れ/雨状態でも1/2回復。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    weather = battle.weather_for(mon)
    if weather.sunny:
        r = 2 / 3
    elif weather.name in {"あめ", "おおあめ", "すなあらし", "ゆき"}:
        r = 1 / 4
    else:
        r = 1 / 2
    battle.modify_hp(mon, r=r)
    return HandlerReturn(value=value)


def あやしいひかり_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あやしいひかりの効果: 相手をこんらん状態にする（2〜5ターン）。"""
    count = battle.random.randint(2, 5)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, "こんらん", count=count, source=ctx.attacker, ctx=ctx
    ))


def あまいかおり_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"EVA": -2})


def あまえる_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -2})


def あまごい_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("あめ", 5, source=ctx.attacker))


def いちゃもん_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="いちゃもん")


def いばる_modify_defender_stats_and_apply_volatile(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いばるの効果: 相手のこうげきを2段階上げ、相手をこんらん状態にする（2〜5ターン）。"""
    battle.modify_stats(ctx.defender, {"A": 2}, source=ctx.attacker)
    count = battle.random.randint(2, 5)
    battle.volatile_manager.apply(ctx.defender, "こんらん", count=count, source=ctx.attacker, ctx=ctx)
    return HandlerReturn(value=value)


def いやしのすず_cure_team_ailment(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いやしのすず: 自分（シングルバトルでは選出チーム）の状態異常を回復する。

    音系の技のためみがわり状態でも効果が発生する。
    チームに状態異常のポケモンがいない場合は技が失敗する。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    state = battle.player_states[player]
    # シングルバトルでは selection は場にいる 1 体のみ
    targets = [m for m in state.selection if m.ailment.is_active]
    if not targets:
        return HandlerReturn(value=False, stop_event=True)
    for target in targets:
        battle.ailment_manager.remove(target)
    return HandlerReturn(value=value)


def いやなおと_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -2})


def うそなき_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def うたう_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うたうの効果: 相手をねむり状態にする。音系の技のためみがわりを貫通する。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def うらみ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うらみの失敗チェック: 相手が技を使っていない場合は失敗する。"""
    if ctx.defender.executed_move is None:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "うらみ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def うらみ_deplete_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うらみの効果: 相手が直前に使った技のPPを4減らす。"""
    move = ctx.defender.executed_move
    if move is None:
        return HandlerReturn(value=False, stop_event=True)
    move.modify_pp(-4)
    return HandlerReturn(value=value)


def えんまく_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1})


def エレキフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """エレキフィールド: 地形をエレキフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("エレキフィールド", 5))


def オーロラベール_check_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーロラベールの使用条件チェック: 天気が「ゆき」でない場合は失敗する。"""
    if battle.weather.name != "ゆき":
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "オーロラベール"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def オーロラベール_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーロラベール: 自陣営に「オーロラベール」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("オーロラベール", 5):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おいかぜ_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おいかぜ: 自陣営に「おいかぜ」を4ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("おいかぜ", 4):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おかたづけ_cleanup(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おかたづけ: 両陣営のみがわり・トラップを除去し、こうげき・すばやさを1段階上げる。"""
    for mon in battle.actives:
        if mon.has_volatile("みがわり"):
            battle.volatile_manager.remove(mon, "みがわり")
    trap_names = ["まきびし", "どくびし", "ステルスロック", "ねばねばネット"]
    for side in battle.side_managers:
        for trap in trap_names:
            side.deactivate(trap)
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "S": 1})


def おきみやげ_faint_and_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おきみやげ: 使用者をひんしにし、相手のこうげき・とくこうを2段階ずつ下げる。"""
    battle.faint(ctx.attacker)
    modify_defender_stats(battle, ctx, value, stats={"A": -2, "C": -2})
    return HandlerReturn(value=value)


def おたけび_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おたけびの効果: 相手のこうげきととくこうを 1 段階ずつ下げる。音系の技のためみがわりを貫通する。"""
    return modify_defender_stats(battle, ctx, value, stats={"A": -1, "C": -1})


def おだてる_modify_defender_stats_and_apply_volatile(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おだてるの効果: 相手のとくこうを1段階上げ、相手をこんらん状態にする（2〜5ターン）。"""
    battle.modify_stats(ctx.defender, {"C": 1}, source=ctx.attacker)
    count = battle.random.randint(2, 5)
    battle.volatile_manager.apply(ctx.defender, "こんらん", count=count, source=ctx.attacker, ctx=ctx)
    return HandlerReturn(value=value)


def おにび_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど")


def ガードシェア_equalize_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ガードシェア: 使用者と相手のぼうぎょ・とくぼうの実数値を平均化する。

    ランク変化は行わず、実数値のみを書き換える。
    平均は切り捨て（// 2）。
    """
    attacker = ctx.attacker
    defender = ctx.defender
    # B=インデックス2、D=インデックス4
    for idx in (2, 4):
        avg = (attacker._stats_manager.stats[idx] + defender._stats_manager.stats[idx]) // 2
        attacker._stats_manager.stats[idx] = avg
        defender._stats_manager.stats[idx] = avg
    return HandlerReturn(value=value)


def ガードスワップ_swap_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ガードスワップ: 使用者と相手のぼうぎょ・とくぼうのランク変化を入れ替える。

    実数値は変化せず、ランク変化のみを互いに入れ替える。
    """
    attacker = ctx.attacker
    defender = ctx.defender
    for stat in ("B", "D"):
        attacker.rank[stat], defender.rank[stat] = (
            defender.rank[stat], attacker.rank[stat]
        )
    return HandlerReturn(value=value)


def かいでんぱ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """相手の特攻を2段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"C": -2})


def かえんのまもり_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="かえんのまもり")


def かげぶんしん_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かげぶんしんの効果: 自分の回避率を 1 段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"EVA": 1})


def かたくなる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1})


def かなしばり_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かなしばりの失敗条件を判定する。

    - 相手がまだ技を使っていない（executed_move が None）場合は失敗する
    - わるあがきに対して使うと失敗する
    """
    move = ctx.defender.executed_move
    if not move or move.name == "わるあがき":
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "かなしばり"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def かなしばり_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かなしばりの効果: 相手に「かなしばり」状態を付与する（4 ターン）。"""
    move = ctx.defender.executed_move
    return apply_volatile_to_defender(battle, ctx, value, volatile="かなしばり",
                                      count=4, move_name=move.name)


def からにこもる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1})


def からをやぶる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1, "A": 2, "C": 2, "S": 2})


def きあいだめ_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="きゅうしょアップ")


def キノコのほうし_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def きりばらい_defog(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きりばらいの効果: 対象の回避率を1段階下げ、場の効果を除去する。

    対象側の場:
        ひかりのかべ・リフレクター・オーロラベール・しんぴのまもり・しろいきりを解除する。
    両側の場:
        まきびし・どくびし・ステルスロック・ねばねばネットを解除する。
    フィールド:
        エレキフィールド・グラスフィールド・サイコフィールド・ミストフィールドを解除する。

    みがわり状態でも場の効果解除は通常通り発動する（回避率下降のみ無効）。
    """
    # 対象側の壁系を解除
    defender_side = battle.get_side(ctx.defender)
    wall_names = ["ひかりのかべ", "リフレクター", "オーロラベール", "しんぴのまもり", "しろいきり"]
    for wall in wall_names:
        defender_side.deactivate(wall)

    # 両陣営のトラップを解除
    trap_names = ["まきびし", "どくびし", "ステルスロック", "ねばねばネット"]
    for side in battle.side_managers:
        for trap in trap_names:
            side.deactivate(trap)

    # フィールドを解除
    battle.terrain_manager.remove()

    # 対象の回避率を1段階下げる
    return modify_defender_stats(battle, ctx, value, stats={"EVA": -1})


def きんぞくおん_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def くすぐる_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くすぐるの効果: 相手のこうげきとぼうぎょを 1 段階ずつ下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"A": -1, "B": -1})


def くろいきり_reset_all_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くろいきりの効果: 場にいる全ポケモンの能力ランクを±0にリセットする。

    しろいきり状態でも防げない（ON_BEFORE_MODIFY_STAT を経由しない直接リセット）。
    """
    for mon in battle.actives:
        changed = {s: v for s, v in mon.rank.items() if v != 0}
        if changed:
            for s in changed:
                mon.rank[s] = 0
            battle.add_event_log(
                mon, LogCode.STAT_CHANGED,
                payload={"stats": {s: -v for s, v in changed.items()}, "reason": "くろいきり"},
            )
    return HandlerReturn(value=value)


def くろいまなざし_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くろいまなざしの効果: 相手をにげられない状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="にげられない")


def グラスフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """グラスフィールド: 地形をグラスフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("グラスフィールド", 5))


def こうそくいどう_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 2})


def コスモパワー_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1, "D": 1})


def コットンガード_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 3})


def こらえる_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こらえるの効果: 自分にこらえる状態を付与する。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="こらえる")


def こわいかお_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -2})


def さいみんじゅつ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さいみんじゅつの効果: 相手をねむり状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def さむいギャグ_activate_weather_and_pivot(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さむいギャグ: ゆきを5ターン発生させた後、自発交代する。

    すでにゆき状態の場合はゆきの変更は失敗するが交代効果は発動する。
    すでにゆき状態で交代先もいない場合にのみ技が失敗する。
    """
    weather_changed = battle.weather_manager.apply("ゆき", 5, source=ctx.attacker)

    player = battle.get_player(ctx.attacker)
    can_switch = bool(battle.get_available_switch_commands(player))
    if can_switch:
        battle.player_states[player].interrupt = Interrupt.PIVOT

    # ゆき変更も交代もどちらも発動できない場合にのみ失敗
    if not weather_changed and not can_switch:
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def すてゼリフ_modify_defender_stats_and_pivot(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すてゼリフ: 相手のこうげき・とくこうを1段階下げ、自発交代する。

    ランク低下が成功した場合のみ交代が発動する。
    ランク低下が阻まれた（クリアボディ等）場合は交代も発動しない（第七世代以降）。
    控えポケモンがいない場合はランク低下のみ発動し交代は発生しない。
    """
    result = modify_defender_stats(battle, ctx, value, stats={"A": -1, "C": -1})

    # ランク低下が完全に阻まれた（実際の変化量が空）場合は交代しない
    if not result.value:
        return result

    player = battle.get_player(ctx.attacker)
    if battle.get_available_switch_commands(player):
        battle.player_states[player].interrupt = Interrupt.PIVOT

    return HandlerReturn(value=value)


def サイコフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サイコフィールド: 地形をサイコフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("サイコフィールド", 5))


def じこあんじ_copy_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じこあんじ: 相手の能力ランク変化をすべて自分にコピーする。

    相手のランクは変化しない。direct代入により、たんじゅん・あまのじゃく・
    クリアボディ等のランク変化ハンドラを経由しない。
    """
    attacker = ctx.attacker
    defender = ctx.defender
    rank_stats: list[str] = ["A", "B", "C", "D", "S", "ACC", "EVA"]
    for stat in rank_stats:
        attacker.rank[stat] = defender.rank[stat]
    return HandlerReturn(value=value)


def じこさいせい_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じこさいせい: 最大HPの1/2を回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def しびれごな_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しびれごなの効果: 相手をまひ状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def しっぽきり_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しっぽきりの失敗条件チェック。

    以下のいずれかに該当する場合は失敗する:
    - 使用者がすでにみがわり状態
    - 使用者のHPが最大HPの半分以下
    - 交代できる控えのポケモンがいない
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    if mon.has_volatile("みがわり"):
        battle.add_event_log(mon, LogCode.MOVE_FAILED,
                             payload={"reason": "しっぽきり_みがわり中"})
        return HandlerReturn(value=False, stop_event=True)
    if mon.hp <= mon.max_hp // 2:
        battle.add_event_log(mon, LogCode.MOVE_FAILED,
                             payload={"reason": "しっぽきり_HP不足"})
        return HandlerReturn(value=False, stop_event=True)
    if not battle.get_available_switch_commands(player):
        battle.add_event_log(mon, LogCode.MOVE_FAILED,
                             payload={"reason": "しっぽきり_交代不可"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def しっぽきり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しっぽきりの効果: HP消費・みがわり生成・ピボット交代。

    消費HPは最大HPの1/2（小数点以下切り上げ）。
    みがわりのHPは最大HPの1/4（切り捨て）で通常みがわりと同じ。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    # 最大HPの1/2を消費（切り上げ）
    cost = (mon.max_hp + 1) // 2
    battle.modify_hp(mon, -cost)
    # みがわり生成
    battle.volatile_manager.apply(mon, "みがわり", hp=mon.max_hp // 4)
    # ピボット交代（交代先選択をプレイヤーに委ねる）
    battle.player_states[player].interrupt = Interrupt.PIVOT
    return HandlerReturn(value=value)


def しっぽをふる_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def じばそうさ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じばそうさの失敗条件: 使用者の特性がプラス/マイナスでない場合は失敗させる。"""
    if ctx.attacker.ability.name not in ("プラス", "マイナス"):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "じばそうさ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def じばそうさ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じばそうさの効果: ぼうぎょ・とくぼうをそれぞれ1段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1, "D": 1})


def じゅうでん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうでんの効果: 自分にじゅうでん状態を付与し、とくぼうを1段階上げる。"""
    mon = ctx.attacker
    battle.volatile_manager.apply(mon, "じゅうでん", source=mon)
    battle.modify_stats(mon, {"D": 1}, source=mon)
    return HandlerReturn(value=value)


def じゅうりょく_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.global_manager.activate("じゅうりょく", 5))


def しんぴのまもり_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しんぴのまもり: 自陣営に「しんぴのまもり」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("しんぴのまもり", 5):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def シンプルビーム_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シンプルビームの失敗条件チェック。

    対象の特性が protected フラグを持つ場合は失敗する。
    """
    if ctx.defender.ability.has_flag("protected"):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "シンプルビーム"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def シンプルビーム_change_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シンプルビームの効果: 相手の特性を「シンプル」に書き換える。"""
    battle.change_ability(ctx.defender, "シンプル")
    return HandlerReturn(value=value)


def ステルスロック_set_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ステルスロック: 相手側のフィールドにステルスロックを設置する。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("ステルスロック", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def すなあらし_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("すなあらし", 5, source=ctx.attacker))


def すなかけ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1})


def スレッドトラップ_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="スレッドトラップ")


def ソウルビート_pay_hp_and_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソウルビートの効果: 最大HPの1/3を消費し、すべての能力を1段階ずつ上げる。"""
    mon = ctx.attacker
    battle.modify_hp(mon, r=-1/3)
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "B": 1, "C": 1, "D": 1, "S": 1})


def せいちょう_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """せいちょう: 天候が晴れの時はこうげき・とくこうを2段階、通常時は1段階上げる。
    攻撃側がばんのうがさを持つ場合、晴れでも1段階のみ。
    """
    n = 2 if battle.weather_for(ctx.attacker).sunny else 1
    return modify_attacker_stats(battle, ctx, value, stats={"A": n, "C": n})


def タールショット_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="タールショット")


def タールショット_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def たてこもる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """たてこもるの効果: 自分のぼうぎょを 2 段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"B": 2})


def つきのひかり_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """つきのひかり: 天候に応じた割合で自分のHPを回復する。
    攻撃側がばんのうがさを持つ場合、晴れ/雨状態でも1/2回復。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    weather = battle.weather_for(mon)
    if weather.sunny:
        r = 2 / 3
    elif weather.name in {"あめ", "おおあめ", "すなあらし", "ゆき"}:
        r = 1 / 4
    else:
        r = 1 / 2
    battle.modify_hp(mon, r=r)
    return HandlerReturn(value=value)


def つぶらなひとみ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """つぶらなひとみの効果: 相手のこうげきを1段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def てっぺき_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 2})


def てんしのキッス_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """てんしのキッスの効果: 相手をこんらん状態にする（2〜5ターン）。"""
    count = battle.random.randint(2, 5)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, "こんらん", count=count, source=ctx.attacker, ctx=ctx
    ))


def つるぎのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 2})


def でんじは_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def でんじふゆう_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんじふゆうの効果: 自分をでんじふゆう状態にする（5ターン）。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="でんじふゆう", count=5)


def トーチカ_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="トーチカ")


def とおぼえ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とおぼえの効果: 自分のこうげきを1段階上げる（シングルバトルでは自分のみ）。"""
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1})


def どくどく_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく")


def どくのこな_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def どくのいと_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくのいとの効果（毒）: 相手をどく状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def どくのいと_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくのいとの効果（速度低下）: 相手のすばやさを1段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def どくびし_set_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくびし: 相手陣営に「どくびし」を1層設置する（最大2層）。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("どくびし", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def トリックルーム_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["トリックルーム"].is_active:
        return HandlerReturn(value=manager.deactivate("トリックルーム"))
    return HandlerReturn(value=manager.activate("トリックルーム", 5))


def とぐろをまく_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "B": 1, "ACC": 1})


def とける_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 2})


def とおせんぼう_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とおせんぼうの効果: 相手をにげられない状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="にげられない")


def ドわすれ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"D": 2})


def なきごえ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def なまける_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なまける: 最大HPの1/2を回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def ねむりごな_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def なみだめ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def ねばねばネット_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねばねばネット: 相手陣営に「ねばねばネット」を設定する（永続）。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("ねばねばネット", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def にほんばれ_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("はれ", 5, source=ctx.attacker))


def にらみつける_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def ねをはる_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねをはるの効果: 自分をねをはる状態にする。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ねをはる")


def ふういん_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ふういん")


def フェザーダンス_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -2})


def フラフラダンス_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フラフラダンスの効果: 相手をこんらん状態にする（2〜5ターン）。"""
    count = battle.random.randint(2, 5)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, "こんらん", count=count, source=ctx.attacker, ctx=ctx
    ))


def ひかりのかべ_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひかりのかべ: 自陣営に「ひかりのかべ」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("ひかりのかべ", 5):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def へびにらみ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def ほたるび_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 3})


def はらだいこ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はらだいこの使用条件チェック: こうげきランクがすでに+6ならば失敗する。"""
    if ctx.attacker.rank["A"] >= 6:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "はらだいこ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はらだいこ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はらだいこの効果: こうげきランクを最大まで上げ、HPを最大HPの半分消費する。"""
    mon = ctx.attacker
    delta = 6 - mon.rank["A"]
    battle.modify_stats(mon, {"A": delta}, source=mon)
    battle.modify_hp(mon, -(mon.max_hp // 2))
    return HandlerReturn(value=value)


def ハロウィン_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハロウィンの使用条件チェック: 相手がすでにゴーストタイプなら失敗する。"""
    if ctx.defender.has_type("ゴースト"):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "ハロウィン"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ハロウィン_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハロウィンの効果: 相手にハロウィン状態を付与してゴーストタイプを追加する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ハロウィン")


def ビルドアップ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "B": 1})


def マジックルーム_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["マジックルーム"].is_active:
        return HandlerReturn(value=manager.deactivate("マジックルーム"))
    return HandlerReturn(value=manager.activate("マジックルーム", 5))


def まきびし_set_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まきびし: 相手陣営に「まきびし」を1層設置する（最大3層）。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("まきびし", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def まもる_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="まもる")


def みきり_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="まもる")


def ミストフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミストフィールド: 地形をミストフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("ミストフィールド", 5))


def みちづれ_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="みちづれ")


def メロメロ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メロメロの効果: 相手をメロメロ状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="メロメロ")


def もりののろい_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もりののろいの使用条件チェック: 相手がすでにくさタイプなら失敗する。"""
    if ctx.defender.has_type("くさ"):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "もりののろい"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def もりののろい_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もりののろいの効果: 相手にもりののろい状態を付与してくさタイプを追加する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="もりののろい")


def やどりぎのタネ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """やどりぎのタネの効果: 相手をやどりぎのタネ状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="やどりぎのタネ")


def ゆきげしき_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("ゆき", 5, source=ctx.attacker))


def リフレクター_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リフレクター: 自陣営に「リフレクター」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("リフレクター", 5):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ロックオン_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ロックオン", count=2)


def りゅうのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """りゅうのまいの効果: 自分のこうげき・すばやさを1段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "S": 1})


def ロックカット_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 2})


def わたほうし_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """わたほうしの効果: 相手のすばやさを1段階下げる。粉技のためくさタイプ・ぼうじん無効。"""
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def わるだくみ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 2})


def ワンダールーム_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["ワンダールーム"].is_active:
        return HandlerReturn(value=manager.deactivate("ワンダールーム"))
    return HandlerReturn(value=manager.activate("ワンダールーム", 5))


def キングシールド_apply_volatile_to_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="キングシールド")
