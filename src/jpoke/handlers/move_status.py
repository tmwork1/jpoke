"""変化技関連のイベントハンドラ関数を提供するモジュール。

変化技の実行に関連するハンドラ関数を提供します。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from .move import (
    apply_ailment_to_defender,
    apply_volatile_to_attacker,
    apply_volatile_to_defender,
    modify_attacker_stats,
    modify_defender_stats,
)
from jpoke.core import HandlerReturn
from typing import TYPE_CHECKING, Any, cast
if TYPE_CHECKING:
    from jpoke.core import Battle, AttackContext

from jpoke.types import Stat, Type

from jpoke.enums import Event, Interrupt, LogCode

# バトンタッチで交代先に引き継ぐ揮発性状態の名前セット
_BATON_PASS_VOLATILES: frozenset[str] = frozenset({
    "みがわり",
    "こんらん",
    "きゅうしょアップ",
    "ちいさくなる",
    "まるくなる",
    "アクアリング",
    "ねをはる",
    "やどりぎのタネ",
    "じゅうでん",
    "でんじふゆう",
    "ちょうはつ",
    "しおづけ",
    "たくわえる",
})

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
    commands = battle.command_manager.get_available_switch_commands(player)
    if commands:
        command = battle.random.choice(commands)
        battle.run_switch(player, state.team[command.index])
    return HandlerReturn(value=value)


def アクアリング_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="アクアリング")


def あくび_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あくびの効果: 相手をねむけ状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ねむけ", count=2)


def あくび_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あくびの失敗チェック: 対象がねむけ状態または状態異常を持っている場合は失敗する。"""
    mon = ctx.defender
    if mon.has_volatile("ねむけ") or mon.ailment.is_active:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "すでに状態異常になっている"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


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


def あまいかおり_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"evasion": -2})


def あまえる_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -2})


def あまごい_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("あめ", 5, source=ctx.attacker))


def あやしいひかり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あやしいひかりの効果: 相手をこんらん状態にする。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def アロマセラピー_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アロマセラピー: 使用者のパーティ全員（控えも含む）の状態異常を回復する。

    状態異常（やけど・まひ・ねむり・こおり・どく・もうどく）を持つポケモンを回復する。
    状態異常のないポケモンはスキップする。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    state = battle.player_states[player]
    for target in state.selection:
        if target.ailment.is_active:
            battle.ailment_manager.remove(target)
    return HandlerReturn(value=value)


def アンコール_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アンコールの効果を発動する。"""
    move = ctx.defender.executed_move
    return apply_volatile_to_defender(
        battle, ctx, value, volatile="アンコール", count=3, move_name=move.name
    )


def アンコール_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アンコールの失敗条件を判定する。

    - 相手がまだ技を使っていない（executed_move が None）場合は失敗する
    - 相手の最後に使った技が non_encore ラベルを持つ場合は失敗する
    """
    move = ctx.defender.executed_move
    if not move or move.has_flag("non_encore"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "アンコール失敗"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def いえき_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いえきの効果: 相手に「とくせいなし」状態を付与する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="とくせいなし")


def いえき_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いえきの失敗条件を判定する。

    対象の特性が protected フラグを持つ場合は失敗させる。
    """
    if ctx.defender.ability.has_flag("protected"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "保護された特性"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def いたみわけ_equalize_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """両者の現在HPを平均化する。"""
    shared_hp = (ctx.attacker.hp + ctx.defender.hp) // 2
    for mon in (ctx.attacker, ctx.defender):
        battle.modify_hp(mon, v=shared_hp - mon.hp, reason="pain_split")
    return HandlerReturn(value=value)


def いちゃもん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="いちゃもん")


def いとをはく_reduce_defender_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いとをはくの効果: 相手のすばやさを 2 段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"spe": -2})


def いのちのしずく_heal(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちのしずく: 最大HPの1/4を回復する。HPが満タンの場合は失敗する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/4)
    return HandlerReturn(value=value)


def いばる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いばるの効果: 相手のこうげきを2段階上げ、相手をこんらん状態にする。"""
    battle.modify_stats(ctx.defender, {"atk": 2}, source=ctx.attacker)
    battle.volatile_manager.apply_confusion(ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def いやしのすず_cure_ailment(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いやしのすず: 自分（シングルバトルでは選出チーム）の状態異常を回復する。

    音系の技のためみがわり状態でも効果が発生する。
    チームに状態異常のポケモンがいない場合は技が失敗する。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    state = battle.player_states[player]
    targets = [m for m in state.selection if m.ailment.is_active]
    if not targets:
        return HandlerReturn(value=False, stop_event=True)
    for target in targets:
        battle.ailment_manager.remove(target)
    return HandlerReturn(value=value)


def いやしのねがい_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いやしのねがい: 使用者をひんしにし、自陣営に「いやしのねがい」フィールドを設置する。

    次に場に出たポケモンの HP が全回復し、状態異常が回復する。
    PP は回復しない（みかづきのまいとの違い）。
    """
    mon = ctx.attacker
    side = battle.get_side(mon)
    side.activate("いやしのねがい", 1)
    battle.faint(mon)
    return HandlerReturn(value=value)


def いやしのはどう_heal_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いやしのはどう: 相手の最大HPの1/2を回復する。HPが満タンの場合は失敗する。"""
    mon = ctx.defender
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def いやなおと_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -2})


def うそなき_reduce_defender_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2})


def うたう_apply_sleep(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うたうの効果: 相手をねむり状態にする。音系の技のためみがわりを貫通する。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def うらみ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うらみの失敗チェック: 相手が技を使っていない場合は失敗する。"""
    if ctx.defender.executed_move is None:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "うらみ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def うらみ_deplete_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うらみの効果: 相手が直前に使った技のPPを4減らす。"""
    move = ctx.defender.executed_move
    if move is None:
        return HandlerReturn(value=False, stop_event=True)
    move.modify_pp(-4)
    return HandlerReturn(value=value)


def エレキフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """エレキフィールド: 地形をエレキフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("エレキフィールド", 5))


def えんまく_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1})


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
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "spe": 1})


def おきみやげ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おきみやげ: 使用者をひんしにし、相手のこうげき・とくこうを2段階ずつ下げる。"""
    battle.faint(ctx.attacker)
    modify_defender_stats(battle, ctx, value, stats={"atk": -2, "spa": -2})
    return HandlerReturn(value=value)


def おたけび_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おたけびの効果: 相手のこうげきととくこうを 1 段階ずつ下げる。音系の技のためみがわりを貫通する。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1, "spa": -1})


def おだてる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おだてるの効果: 相手のとくこうを1段階上げ、相手をこんらん状態にする。"""
    battle.modify_stats(ctx.defender, {"spa": 1}, source=ctx.attacker)
    battle.volatile_manager.apply_confusion(ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def おにび_apply_burn(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど")


def オーロラベール_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーロラベール: 自陣営に「オーロラベール」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.apply("オーロラベール", 5, source=ctx.attacker):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def オーロラベール_check_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーロラベールの使用条件チェック: 天気が「ゆき」でない場合は失敗する。"""
    if battle.weather.name != "ゆき":
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "オーロラベール"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def かいでんぱ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """相手の特攻を2段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"spa": -2})


def かいふくふうじ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かいふくふうじの効果: 相手に「かいふくふうじ」状態を付与する（5 ターン）。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="かいふくふうじ", count=5)


def かえんのまもり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="かえんのまもり")


def かげぶんしん_boost_attacker_evasion(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かげぶんしんの効果: 自分の回避率を 1 段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"evasion": 1})


def かたくなる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1})


def かなしばり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かなしばりの効果: 相手に「かなしばり」状態を付与する（4 ターン）。"""
    move = ctx.defender.executed_move
    return apply_volatile_to_defender(
        battle, ctx, value, volatile="かなしばり", count=4, move_name=move.name
    )


def かなしばり_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かなしばりの失敗条件を判定する。

    - 相手がまだ技を使っていない（executed_move が None）場合は失敗する
    - わるあがきに対して使うと失敗する
    """
    move = ctx.defender.executed_move
    if (
        not move
        or move.name == "わるあがき"
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "かなしばり"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def からにこもる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1})


def からをやぶる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1, "spd": -1, "atk": 2, "spa": 2, "spe": 2})


def ガードシェア_equalize_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ガードシェア: 使用者と相手のぼうぎょ・とくぼうの実数値を平均化する。

    ランク変化は行わず、実数値のみを書き換える。
    平均は切り捨て（// 2）。
    """
    atk_stats = ctx.attacker._stats_manager.stats
    def_stats = ctx.defender._stats_manager.stats
    # B=インデックス2、D=インデックス4
    for idx in (2, 4):
        avg = (atk_stats[idx] + def_stats[idx]) // 2
        atk_stats[idx] = avg
        def_stats[idx] = avg
    return HandlerReturn(value=value)


def ガードスワップ_swap_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ガードスワップ: 使用者と相手のぼうぎょ・とくぼうのランク変化を入れ替える。

    実数値は変化せず、ランク変化のみを互いに入れ替える。
    """
    atk_rank = ctx.attacker.rank
    def_rank = ctx.defender.rank
    for stat in ("def", "spd"):
        atk_rank[stat], def_rank[stat] = def_rank[stat], atk_rank[stat]
    return HandlerReturn(value=value)


def きあいだめ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    # 第9世代: 急所ランク+2。countにランク加算値を格納する
    return apply_volatile_to_attacker(battle, ctx, value, volatile="きゅうしょアップ", count=2)


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
    return modify_defender_stats(battle, ctx, value, stats={"evasion": -1})


def キングシールド_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="キングシールド")


def きんぞくおん_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2})


def くすぐる_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くすぐるの効果: 相手のこうげきとぼうぎょを 1 段階ずつ下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1, "def": -1})


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


def くろいまなざし_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くろいまなざしの効果: 相手をにげられない状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="にげられない")


def グラスフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """グラスフィールド: 地形をグラスフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("グラスフィールド", 5))


def こうそくいどう_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 2})


def コスモパワー_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1, "spd": 1})


def コットンガード_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 3})


def こらえる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こらえるの効果: 自分にこらえる状態を付与する。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="こらえる")


def こわいかお_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -2})


def サイコフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サイコフィールド: 地形をサイコフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("サイコフィールド", 5))


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

    can_switch = battle.query.can_switch(player)
    if can_switch:
        battle.player_states[player].interrupt = Interrupt.PIVOT

    # ゆき変更も交代もどちらも発動できない場合にのみ失敗
    if not weather_changed and not can_switch:
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=True)


def しっぽきり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しっぽきりの効果: HP消費・みがわり生成・ピボット交代。

    消費HPは最大HPの半分（小数点以下切り上げ）。
    みがわりのHPは最大HPの1/4（切り捨て）で通常みがわりと同じ。
    みがわり状態は交代先のポケモンに引き継がれる。
    バトンタッチの仕組み（baton_pass_data）を流用して引き継ぎを実現する。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    # 最大HPの半分を消費（切り上げ）
    cost = (mon.max_hp + 1) // 2
    battle.modify_hp(mon, -cost)
    # みがわり生成（HPは最大HPの1/4切り捨て）
    migawari_hp = mon.max_hp // 4
    battle.volatile_manager.apply(mon, "みがわり", hp=migawari_hp)
    # バトンタッチの仕組みを流用してみがわりを交代先に引き継ぐ
    # ランクは引き継がず、みがわりのみを渡す
    battle.player_states[player].baton_pass_data = {
        "rank": {},
        "volatiles": {"みがわり": {"hp": migawari_hp}},
    }
    # ピボット交代（交代先選択をプレイヤーに委ねる）
    battle.player_states[player].interrupt = Interrupt.PIVOT
    return HandlerReturn(value=value)


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
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "しっぽきり_みがわり中"}
        )
        return HandlerReturn(value=False, stop_event=True)

    # 最大HPの半分以下は失敗する（切り上げ）
    if mon.hp <= (mon.max_hp + 1) // 2:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "しっぽきり_HP不足"}
        )
        return HandlerReturn(value=False, stop_event=True)

    if not battle.query.can_switch(player):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "しっぽきり_交代不可"}
        )
        return HandlerReturn(value=False, stop_event=True)

    return HandlerReturn(value=value)


def しっぽをふる_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1})


def しびれごな_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しびれごなの効果: 相手をまひ状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


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
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "シンプルビーム"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def シンプルビーム_change_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シンプルビームの効果: 相手の特性を「たんじゅん」に書き換える。"""
    battle.change_ability(ctx.defender, "たんじゅん")
    return HandlerReturn(value=value)


def じこあんじ_copy_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じこあんじ: 相手の能力ランク変化をすべて自分にコピーする。

    相手のランクは変化しない。direct代入により、たんじゅん・あまのじゃく・
    クリアボディ等のランク変化ハンドラを経由しない。
    """
    attacker = ctx.attacker
    defender = ctx.defender
    rank_stats: list[str] = ["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]
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


def じばそうさ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じばそうさの失敗条件: 使用者の特性がプラス/マイナスでない場合は失敗させる。"""
    if ctx.attacker.ability.name not in ("プラス", "マイナス"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "じばそうさ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def じばそうさ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じばそうさの効果: ぼうぎょ・とくぼうをそれぞれ1段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1, "spd": 1})


def じゅうでん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうでんの効果: 自分にじゅうでん状態を付与し、とくぼうを1段階上げる。"""
    mon = ctx.attacker
    battle.volatile_manager.apply(mon, "じゅうでん", source=mon)
    battle.modify_stats(mon, {"spd": 1}, source=mon)
    return HandlerReturn(value=value)


def じゅうりょく_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.global_manager.activate("じゅうりょく", 5))


def スキルスワップ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """スキルスワップの失敗条件チェック。

    使用者または対象の特性が protected フラグを持つ場合は失敗する。
    かたやぶりを持っていても、この失敗条件は回避できない。
    """
    assert ctx.defender is not None
    if (
        ctx.attacker.ability.has_flag("protected")
        or ctx.defender.ability.has_flag("protected")
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "スキルスワップ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def スキルスワップ_swap_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """スキルスワップの効果: 使用者と対象の特性を入れ替える。"""
    assert ctx.defender is not None
    battle.ability_manager.swap_ability(ctx.attacker, ctx.defender)
    return HandlerReturn(value=value)


def すてゼリフ_modify_defender_stats_and_pivot(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すてゼリフ: 相手のこうげき・とくこうを1段階下げ、自発交代する。

    ランク低下が成功した場合のみ交代が発動する。
    ランク低下が阻まれた（クリアボディ等）場合は交代も発動しない（第七世代以降）。
    控えポケモンがいない場合はランク低下のみ発動し交代は発生しない。
    """
    result = modify_defender_stats(battle, ctx, value, stats={"atk": -1, "spa": -1})

    # ランク低下が完全に阻まれた（実際の変化量が空）場合は交代しない
    if not result.value:
        return result

    player = battle.get_player(ctx.attacker)
    if battle.query.can_switch(player):
        battle.player_states[player].interrupt = Interrupt.PIVOT

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
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1})


def スピードスワップ_swap_speed(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """スピードスワップ: 使用者と相手のすばやさの実数値を入れ替える。

    ランク変化は行わず、実数値のみを入れ替える。
    インデックス 5 = すばやさ（[HP, 攻撃, 防御, 特攻, 特防, 素早さ]）。
    """
    atk_stats = ctx.attacker._stats_manager.stats
    def_stats = ctx.defender._stats_manager.stats
    atk_stats[5], def_stats[5] = def_stats[5], atk_stats[5]
    return HandlerReturn(value=value)


def すりかえ_swap_items(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すりかえ・トリックのアイテム交換効果。"""
    success = battle.item_manager.swap_items()
    return HandlerReturn(value=success)


def スレッドトラップ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="スレッドトラップ")


def せいちょう_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """せいちょう: 天候が晴れの時はこうげき・とくこうを2段階、通常時は1段階上げる。
    攻撃側がばんのうがさを持つ場合、晴れでも1段階のみ。
    """
    n = 2 if battle.weather_for(ctx.attacker).sunny else 1
    return modify_attacker_stats(battle, ctx, value, stats={"atk": n, "spa": n})


def そうでん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """そうでんの効果: 相手をそうでん状態にする（そのターン中のみ）。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="そうでん")


def ソウルビート_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソウルビートの失敗条件: HPが最大HPの1/3以下の場合は失敗。"""
    mon = ctx.attacker
    if mon.hp <= mon.max_hp // 3:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "ソウルビート_HP不足"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ソウルビート_pay_hp_and_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソウルビートの効果: 最大HPの1/3を消費し、すべての能力を1段階ずつ上げる。"""
    mon = ctx.attacker
    battle.modify_hp(mon, r=-1/3)
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1, "spa": 1, "spd": 1, "spe": 1})


def たくわえる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """たくわえるの効果: ぼうぎょ・とくぼうを1段階上げ、たくわえカウントをインクリメントする。"""
    mon = ctx.attacker
    # ぼうぎょ・とくぼうのランク上昇を試みる
    result = battle.modify_stats(mon, {"def": 1, "spd": 1}, source=mon)
    # volatile がなければ新規付与（count=1）、あればカウントを+1
    if not mon.has_volatile("たくわえる"):
        battle.volatile_manager.apply(mon, "たくわえる", count=1)
    else:
        mon.volatiles["たくわえる"].count = (mon.volatiles["たくわえる"].count or 0) + 1
    return HandlerReturn(value=result)


def たくわえる_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """たくわえるの使用条件チェック: たくわえた回数がすでに3なら失敗する。"""
    mon = ctx.attacker
    if mon.has_volatile("たくわえる") and (mon.volatiles["たくわえる"].count or 0) >= 3:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "たくわえる"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def たてこもる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """たてこもるの効果: 自分のぼうぎょを 2 段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2})


def タールショット_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """タールショットの効果: 相手にタールショット状態を付与し、すばやさを1段階下げる。"""
    assert ctx.defender is not None
    battle.volatile_manager.apply(ctx.defender, "タールショット", source=ctx.attacker)
    return HandlerReturn(value=battle.modify_stats(ctx.defender, {"spe": -1}, source=ctx.attacker))


def ちいさくなる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちいさくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"evasion": 2}, source=mon)
    battle.volatile_manager.apply(mon, "ちいさくなる")
    return HandlerReturn(value=value)


def ちからをすいとる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちからをすいとるの効果: 相手のこうげき実数値分HPを回復し、相手のこうげきを1段階下げる。

    特性などでランクが下がらない場合は回復効果のみ発動する。
    """
    assert ctx.defender is not None
    # 相手のこうげきランク補正込みの実数値分だけ自分のHPを回復（ランク変更前に取得）
    recover_amount = ctx.defender.ranked_stats["atk"]
    recover_amount = battle.events.emit(Event.ON_CALC_DRAIN, ctx, recover_amount)
    battle.modify_hp(ctx.attacker, v=recover_amount)
    # 相手のこうげきを1段階下げる（失敗しても回復は発動済み）
    battle.modify_stats(ctx.defender, {"atk": -1}, source=ctx.attacker)
    return HandlerReturn(value=value)


def ちからをすいとる_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちからをすいとるの失敗チェック: 相手のこうげきランクがすでに -6 なら失敗する。"""
    assert ctx.defender is not None
    if ctx.defender.rank["atk"] == -6:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "こうげき最低"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ちょうのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちょうのまいの効果: 自分のとくこう・とくぼう・すばやさを 1 段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 1, "spd": 1, "spe": 1})


def ちょうはつ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちょうはつの効果: 相手にちょうはつ状態を付与する（3 ターン）。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ちょうはつ", count=3)


def つぶらなひとみ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """つぶらなひとみの効果: 相手のこうげきを1段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def つぼをつく_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """つぼをつく: 7種類の能力からランダムに1つ選んでランクを2段階上げる。"""
    stat = cast(Stat, battle.random.choice(["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]))
    return HandlerReturn(value=battle.modify_stats(ctx.attacker, {stat: 2}, source=ctx.attacker))


def つるぎのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 2})


def てっぺき_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2})


def てんしのキッス_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """てんしのキッスの効果: 相手をこんらん状態にする。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def でんじは_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def でんじふゆう_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんじふゆうの効果: 自分をでんじふゆう状態にする（5ターン）。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="でんじふゆう", count=5)


def とおせんぼう_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とおせんぼうの効果: 相手をにげられない状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="にげられない")


def とおぼえ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とおぼえの効果: 自分のこうげきを1段階上げる（シングルバトルでは自分のみ）。"""
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1})


def とぐろをまく_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1, "accuracy": 1})


def とける_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2})


def トリックルーム_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["トリックルーム"].is_active:
        return HandlerReturn(value=manager.deactivate("トリックルーム"))
    return HandlerReturn(value=manager.activate("トリックルーム", 5))


def トーチカ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="トーチカ")


def どくどく_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく")


def どくのいと_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくのいとの効果: 相手をどく状態にし、すばやさを1段階下げる。"""
    assert ctx.defender is not None
    battle.ailment_manager.apply(ctx.defender, "どく", source=ctx.attacker, ctx=ctx)
    return HandlerReturn(value=battle.modify_stats(ctx.defender, {"spe": -1}, source=ctx.attacker))


def どくのこな_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def どくびし_set_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくびし: 相手陣営に「どくびし」を1層設置する（最大2層）。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("どくびし", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ドわすれ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spd": 2})


def なかまづくり_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なかまづくりの失敗条件チェック。

    以下の場合は失敗する:
    - 対象の特性が「なまけ」である
    - 対象の特性が protected フラグを持つ（上書きできない特性）
    - 使用者の特性が uncopyable フラグを持つ（コピーできない特性）
    - 使用者と対象が同じ特性である
    """
    assert ctx.defender is not None
    attacker_ability = ctx.attacker.ability.base_name
    defender_ability = ctx.defender.ability.base_name
    if (
        defender_ability == "なまけ"
        or ctx.defender.ability.has_flag("protected")
        or ctx.attacker.ability.has_flag("uncopyable")
        or attacker_ability == defender_ability
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "なかまづくり"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def なかまづくり_change_defender_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なかまづくりの効果: 相手の特性を使用者と同じ特性に書き換える。"""
    assert ctx.defender is not None
    battle.change_ability(ctx.defender, ctx.attacker.ability.base_name)
    return HandlerReturn(value=value)


def なかよくする_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なかよくする: 相手のこうげきを2段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -2})


def なきごえ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def なまける_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なまける: 最大HPの1/2を回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def なみだめ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1})


def なやみのタネ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なやみのタネの失敗条件チェック。

    対象の特性が protected フラグを持つ場合、
    または「ふみん」「なまけ」の場合は失敗する。
    """
    assert ctx.defender is not None
    ability = ctx.defender.ability
    if (
        ability.has_flag("protected")
        or ability.name in ("ふみん", "なまけ")
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "なやみのタネ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def なやみのタネ_change_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なやみのタネの効果: 相手の特性を「ふみん」に書き換える。"""
    assert ctx.defender is not None
    battle.change_ability(ctx.defender, "ふみん")
    return HandlerReturn(value=value)


def なりきり_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なりきりの失敗条件チェック。

    対象の特性が uncopyable フラグを持つ場合は失敗する
    （ふしぎなまもり・かわりものなど固有の特性）。
    """
    if ctx.defender.ability.has_flag("uncopyable"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "なりきり"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def なりきり_change_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なりきりの効果: 自分の特性を相手の特性と同じにする。"""
    battle.change_ability(ctx.attacker, ctx.defender.ability.name)
    return HandlerReturn(value=value)


def にほんばれ_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("はれ", 5, source=ctx.attacker))


def にらみつける_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1})


def ニードルガード_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ニードルガードの効果: 自分にニードルガード状態を付与する。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ニードルガード")


def ねがいごと_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねがいごとの失敗チェック: すでにねがいごとフィールドが有効なら失敗する。"""
    side = battle.get_side(ctx.attacker)
    if side.get("ねがいごと").is_active:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "ねがいごと"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ねがいごと_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねがいごとの効果: 自陣営に「ねがいごと」を設置し、回復量を使用者の最大HPの半分に設定する。"""
    mon = ctx.attacker
    side = battle.get_side(mon)
    field = side.get("ねがいごと")
    side.activate("ねがいごと", 2)
    field.heal = mon.max_hp // 2
    return HandlerReturn(value=value)


def ねごと_check_sleep(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねごとの発動条件チェック: ねむり状態でない場合に失敗させる。"""
    if not ctx.attacker.has_ailment("ねむり"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "ねごと_ねむり状態でない"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ねごと_select_and_execute(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねごとで選んだ技を実行する。

    non_negoto ラベルを持たない技の中からランダムに選択し、
    そのままバトルで実行する。
    選ばれた技の PP は消費しない（ねごと自体のみ消費）。
    候補技がすべて non_negoto の場合は value=False を返して失敗する。
    """
    attacker = ctx.attacker
    candidates = [m for m in attacker.moves if not m.has_flag("non_negoto")]
    if not candidates:
        battle.add_event_log(
            attacker,
            LogCode.MOVE_FAILED,
            payload={"reason": "ねごと_候補技なし"},
        )
        return HandlerReturn(value=False, stop_event=True)
    chosen = battle.random.choice(candidates)
    # ねごとのON_MODIFY_PP_CONSUMEDハンドラがPP消費を0にするため、
    # ねむり状態でも選ばれた技が実行できるよう、サブ実行フラグを立てる
    attacker.sleep_talk_active = True
    try:
        battle.run_move(attacker, chosen)
    finally:
        attacker.sleep_talk_active = False
    return HandlerReturn(value=value)


def ねごと_suppress_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねごとのサブ実行中は選ばれた技のPP消費を0にする。"""
    if ctx.attacker.sleep_talk_active:
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def ねばねばネット_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねばねばネット: 相手陣営に「ねばねばネット」を設定する（永続）。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("ねばねばネット", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ねむりごな_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def ねむる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねむるの効果: HP全回復・状態異常全回復・3ターンのねむり付与。

    1. HP を最大HPまで回復する
    2. 現在の状態異常を解除する
    3. ねむり状態を付与する（count=3: Champions仕様固定）

    Notes:
        Champions仕様: ねむるのカウントは3固定（Wiki「ねむるによってねむり状態になったときは
        カウントは3で固定」）。説明文「技ねむるでは3度目まで回復しない」と一致。
    """
    mon = ctx.attacker
    # HP全回復
    battle.modify_hp(mon, v=mon.max_hp - mon.hp)
    # 状態異常を解除（上書きフラグで強制解除）
    battle.ailment_manager.remove(mon)
    # ねむり付与（count=3: Champions仕様固定）
    battle.ailment_manager.apply(mon, "ねむり", count=3, source=mon)
    return HandlerReturn(value=value)


def ねむる_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねむるの失敗条件チェック。

    以下のいずれかに該当する場合は失敗する:
    - HP が最大HP（すでに満タン）
    - すでにねむり状態
    - エレキフィールド下で接地している
    - ミストフィールド下で接地している
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp or mon.has_ailment("ねむり"):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "ねむる"},
        )
        return HandlerReturn(value=False, stop_event=True)
    # エレキフィールド下で接地しているポケモンのねむるは失敗する
    if (
        battle.terrain.name == "エレキフィールド"
        and not battle.query.is_floating(mon)
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "エレキフィールド"},
        )
        return HandlerReturn(value=False, stop_event=True)
    # ミストフィールド下で接地しているポケモンのねむるは失敗する
    if (
        battle.terrain.name == "ミストフィールド"
        and not battle.query.is_floating(mon)
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "ミストフィールド"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ねむる_check_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねむるのステータス無効化チェック（ON_BEFORE_APPLY_MOVE）。

    HP 満タン・ねむり状態を再チェックする。ねむる_check と同条件。
    """
    return ねむる_check(battle, ctx, value)


def ねをはる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねをはるの効果: 自分をねをはる状態にする。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ねをはる")


def のみこむ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """のみこむの効果: たくわえ回数に応じてHPを回復し、たくわえ状態をリセットする。"""
    mon = ctx.attacker
    count = mon.volatiles["たくわえる"].count or 0
    # 回復量: 1回=1/4, 2回=1/2, 3回=全回復
    _heal_ratio: dict[int, float] = {1: 1 / 4, 2: 1 / 2, 3: 1.0}
    battle.modify_hp(mon, r=_heal_ratio.get(min(count, 3), 1 / 4))
    # たくわえた回数分だけランクを戻す
    battle.modify_stats(mon, {"def": -count, "spd": -count}, source=mon)
    # volatile 削除
    battle.volatile_manager.remove(mon, "たくわえる")
    return HandlerReturn(value=value)


def のみこむ_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """のみこむの使用条件チェック: たくわえた回数が0なら失敗する。"""
    mon = ctx.attacker
    if (
        not mon.has_volatile("たくわえる")
        or mon.volatiles["たくわえる"].count == 0
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "のみこむ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def のろい_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """のろいの効果: タイプによって呪いと鈍いに分岐する。

    ゴーストタイプ: 自分のHPを最大HPの1/2（切り捨て）消費し、相手をのろい状態にする。
    ゴーストタイプ以外: こうげき・ぼうぎょを1段階上げ、すばやさを1段階下げる。
    """
    mon = ctx.attacker
    if mon.has_type("ゴースト"):
        # 呪い: HP消費 → のろい状態付与
        cost = mon.max_hp // 2
        battle.modify_hp(mon, v=-cost)
        return apply_volatile_to_defender(battle, ctx, value, volatile="のろい")
    else:
        # 鈍い: こうげき・ぼうぎょ上昇、すばやさ低下
        return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1, "spe": -1})


def のろい_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """のろいの失敗チェック（呪い版）: 対象がすでにのろい状態なら失敗する。

    ゴーストタイプ以外が使う場合（鈍い）はガードをスキップする。
    """
    if not ctx.attacker.has_type("ゴースト"):
        return HandlerReturn(value=value)
    if ctx.defender.has_volatile("のろい"):
        battle.add_event_log(
            ctx.attacker,
            LogCode.MOVE_FAILED,
            payload={"reason": "のろい_すでに状態変化"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はいすいのじん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はいすいのじんの効果: すべての能力を1段階ずつ上げる。

    すでに他の要因でにげられない状態の場合は、にげられない付与をスキップする。
    """
    mon = ctx.attacker
    # すべての能力（こうげき・ぼうぎょ・とくこう・とくぼう・すばやさ）を1段階ずつ上げる
    battle.modify_stats(mon, {"atk": 1, "def": 1, "spa": 1, "spd": 1, "spe": 1}, source=mon)
    # にげられない状態でない場合のみ付与（はいすいのじん起因をmove_nameで記録）
    if not mon.has_volatile("にげられない"):
        battle.volatile_manager.apply(mon, "にげられない", source=mon, move_name="はいすいのじん")
    return HandlerReturn(value=value)


def はいすいのじん_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はいすいのじんの失敗条件チェック（ON_TRY_MOVE_1 priority=30）。

    下記のいずれかに該当する場合は失敗する:
    1. すでにはいすいのじんによってにげられない状態になっている
    2. すべての能力ランクがすでに+6
    """
    mon = ctx.attacker
    # はいすいのじん起因でにげられない状態の場合は失敗
    if (mon.has_volatile("にげられない")
            and mon.volatiles["にげられない"].move_name == "はいすいのじん"):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "はいすいのじん_すでに状態変化"},
        )
        return HandlerReturn(value=False, stop_event=True)
    # すべての能力ランクがすでに+6の場合は失敗
    if all(mon.rank[stat] >= 6 for stat in ("atk", "def", "spa", "spd", "spe")):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "はいすいのじん_すでに状態変化"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はきだす_apply_after(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はきだすのヒット後処理（ON_HIT）: たくわえ状態をリセットし、上がったランクを戻す。"""
    mon = ctx.attacker
    count = mon.volatiles["たくわえる"].count or 0
    # ランクをたくわえた回数分だけ逆方向へ
    battle.modify_stats(mon, {"def": -count, "spd": -count}, source=mon)
    battle.volatile_manager.remove(mon, "たくわえる")
    return HandlerReturn(value=value)


def はきだす_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はきだすの使用条件チェック: たくわえた回数が0なら失敗する。"""
    mon = ctx.attacker
    if (
        not mon.has_volatile("たくわえる")
        or mon.volatiles["たくわえる"].count == 0
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "はきだす"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はきだす_set_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はきだすの効果（ON_BEGIN_MOVE）: たくわえ回数に応じて威力を設定する。"""
    mon = ctx.attacker
    count = (mon.volatiles["たくわえる"].count or 0) if mon.has_volatile("たくわえる") else 0
    power = count * 100  # 1回=100, 2回=200, 3回=300
    ctx.move.power = power
    return HandlerReturn(value=value)


def はねやすめ_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はねやすめの失敗チェック: HPが満タンの場合は失敗する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はねやすめ_heal_and_remove_flying(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はねやすめの効果: 最大HPの1/2を回復し、ひこうタイプを一時的に除去する。

    テラスタル中はタイプ除去を行わない。
    ひこうタイプを持たないポケモンはタイプ除去を行わない。
    """
    mon = ctx.attacker
    battle.modify_hp(mon, r=1/2)
    # テラスタル中はタイプ変化しない
    if mon.active_tera_type:
        return HandlerReturn(value=value)
    # ひこうタイプを持つ場合のみ除去 volatile を付与
    if mon.has_type("ひこう"):
        battle.volatile_manager.apply(mon, "はねやすめ")
    return HandlerReturn(value=value)


def ハバネロエキス_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハバネロエキスの効果: 相手のこうげきを2段階上げ、ぼうぎょを2段階下げる。"""
    battle.modify_stats(ctx.defender, {"atk": 2}, source=ctx.attacker)
    battle.modify_stats(ctx.defender, {"def": -2}, source=ctx.attacker)
    return HandlerReturn(value=value)


def はらだいこ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はらだいこの効果: こうげきランクを最大まで上げ、HPを最大HPの半分消費する。"""
    mon = ctx.attacker
    delta = 6 - mon.rank["atk"]
    battle.modify_stats(mon, {"atk": delta}, source=mon)
    battle.modify_hp(mon, r=-0.5)
    return HandlerReturn(value=value)


def はらだいこ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はらだいこの使用条件チェック: こうげきランクがすでに+6、またはHPが最大HPの半分以下ならば失敗する。"""
    mon = ctx.attacker
    if mon.rank["atk"] >= 6 or mon.hp <= mon.max_hp // 2:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "はらだいこ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ハロウィン_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハロウィンの効果: 相手にハロウィン状態を付与してゴーストタイプを追加する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ハロウィン")


def ハロウィン_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハロウィンの使用条件チェック: 相手がすでにゴーストタイプなら失敗する。"""
    if ctx.defender.has_type("ゴースト"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "ハロウィン"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ハートスワップ_swap_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハートスワップ: 使用者と相手のすべての能力ランク変化を入れ替える。

    こうげき・ぼうぎょ・とくこう・とくぼう・すばやさ・めいちゅう・かいひの
    ランク変化を互いに交換する。実数値は変化しない。
    """
    ctx.attacker.rank, ctx.defender.rank = ctx.defender.rank, ctx.attacker.rank
    return HandlerReturn(value=value)


def バトンタッチ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """バトンタッチの効果: ランク・揮発性状態を保存し、ピボット交代する。

    能力ランク変化（プラス・マイナス両方）と一部の揮発性状態を交代先に引き継ぐ。
    クリアボディ等のハンドラを経由させないため、ランクは直接代入で引き継ぐ。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)

    # 退場時にランクがリセットされるため、事前にコピーを作成
    rank_copy = dict(mon.rank)

    # 引き継ぎ対象の volatile をスナップショット
    volatile_copy: dict[str, dict] = {}
    for name, v in mon.volatiles.items():
        if name not in _BATON_PASS_VOLATILES:
            continue
        v_data: dict = {}
        if v.count is not None:
            v_data["count"] = v.count
        if name == "みがわり" and v.hp is not None:
            v_data["hp"] = v.hp
        volatile_copy[name] = v_data

    # PlayerState に引き継ぎデータを格納
    battle.player_states[player].baton_pass_data = {
        "rank": rank_copy,
        "volatiles": volatile_copy,
    }

    # ピボット交代（交代先の選択をプレイヤーに委ねる）
    battle.player_states[player].interrupt = Interrupt.PIVOT
    return HandlerReturn(value=value)


def バトンタッチ_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """バトンタッチの失敗条件チェック: 控えに生きているポケモンがいない場合は失敗する。

    とらわれ状態（にげられない・バインド・ねをはる等）でも交代可能なため、
    トラップチェックを経由せず控えポケモンの生存のみを確認する。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    state = battle.player_states[player]
    if not any(m.alive for m in state.bench):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "バトンタッチ_交代不可"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def パワーシェア_equalize_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワーシェア: 使用者と相手のこうげき・とくこうの実数値を平均化する。

    ランク変化は行わず、実数値のみを書き換える。
    平均は切り捨て（// 2）。
    """
    atk_stats = ctx.attacker._stats_manager.stats
    def_stats = ctx.defender._stats_manager.stats
    # A=インデックス1、C=インデックス3
    for idx in (1, 3):
        avg = (atk_stats[idx] + def_stats[idx]) // 2
        atk_stats[idx] = avg
        def_stats[idx] = avg
    return HandlerReturn(value=value)


def パワースワップ_swap_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワースワップ: 使用者と相手のこうげき・とくこうのランク変化を入れ替える。

    実数値は変化せず、ランク変化のみを互いに入れ替える。
    """
    atk_rank = ctx.attacker.rank
    def_rank = ctx.defender.rank
    for stat in ("atk", "spa"):
        atk_rank[stat], def_rank[stat] = def_rank[stat], atk_rank[stat]
    return HandlerReturn(value=value)


def パワートリック_swap_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワートリック: 使用者のこうげきとぼうぎょの実数値を入れ替える。

    ランク変化は行わず、実数値のみを入れ替える。
    インデックス 1 = こうげき、インデックス 2 = ぼうぎょ
    （[HP, 攻撃, 防御, 特攻, 特防, 素早さ]）。
    """
    stats = ctx.attacker._stats_manager.stats
    stats[1], stats[2] = stats[2], stats[1]
    return HandlerReturn(value=value)


def ひかりのかべ_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひかりのかべ: 自陣営に「ひかりのかべ」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.apply("ひかりのかべ", 5, source=ctx.attacker):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ひっくりかえす_invert_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひっくりかえすの効果: 相手の全能力ランク変化を反転させる。

    全ランクが0の場合は技が失敗する。
    """
    mon = ctx.defender
    if all(v == 0 for v in mon.rank.values()):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "能力ランクに変化がない"},
        )
        return HandlerReturn(value=False, stop_event=True)
    for stat in mon.rank:
        mon.rank[stat] = -mon.rank[stat]
    return HandlerReturn(value=value)


def ビルドアップ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1})


def ファストガード_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ファストガード")


def ふういん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ふういん")


def フェアリーロック_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フェアリーロック: グローバルフィールドを「フェアリーロック」状態にする（次のターン終了まで）。"""
    return HandlerReturn(value=battle.global_manager.activate("フェアリーロック", 1))


def フェザーダンス_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -2})


def フラフラダンス_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フラフラダンスの効果: 相手をこんらん状態にする。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def フラワーヒール_heal_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フラワーヒール: 相手のHPを回復させる。HPが満タンの場合は失敗する。
    グラスフィールド中は最大HPの2/3、通常時は最大HPの1/2を回復する。
    """
    mon = ctx.defender
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    r = 2/3 if battle.terrain.name == "グラスフィールド" else 1/2
    battle.modify_hp(mon, r=r)
    return HandlerReturn(value=value)


def へびにらみ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def ほおばる_check_defense_max(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほおばるの失敗条件: ぼうぎょランクがすでに+6の場合に失敗させる。

    あまのじゃく持ちのポケモンは B ランクが -6 のときに失敗する。
    このチェックは battle.modify_stats の内部（ON_TRY_MOVE_2 の後）で
    行われるわけではないため、ここで明示的にガードする。
    """
    mon = ctx.attacker
    if mon.rank["def"] >= 6:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "ほおばる_ぼうぎょ最大"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ほおばる_check_has_berry(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほおばるの失敗条件: きのみを持っていない場合に失敗させる。"""
    mon = ctx.attacker
    if not mon.item.is_berry():
        battle.add_event_log(mon, LogCode.MOVE_FAILED,
                             payload={"reason": "ほおばる_きのみなし"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ほおばる_consume_berry_and_boost(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほおばるの効果: 自分のきのみを強制消費して効果を発動し、ぼうぎょを2段階上げる。

    battle.item_manager.force_trigger_berry により HP 閾値を無視してきのみ効果を発動し消費する。
    その後ぼうぎょを 2 段階上げる。
    """
    mon = ctx.attacker
    battle.item_manager.force_trigger_berry(mon)
    # ぼうぎょを2段階上げる
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2})


def ほたるび_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 3})


def ほろびのうた_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほろびのうたの効果: 場の全ポケモンにほろびのうた状態を付与する（count=3）。

    使用者自身も対象になる。音技のためみがわりを貫通する。
    すでにほろびのうた状態のポケモンには付与されない（volatile_manager.apply が False を返す）。
    """
    triggered = False
    for mon in battle.actives:
        if battle.volatile_manager.apply(
            mon,
            "ほろびのうた",
            count=3,
            source=ctx.attacker,
        ):
            triggered = True
    return HandlerReturn(value=triggered)


def ほろびのうた_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほろびのうたの失敗チェック: 全員がすでにほろびのうた状態なら失敗する。"""
    if all(mon.has_volatile("ほろびのうた") for mon in battle.actives):
        battle.add_event_log(
            ctx.attacker,
            LogCode.MOVE_FAILED,
            payload={"reason": "ほろびのうた_すでに状態"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def まきびし_set_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まきびし: 相手陣営に「まきびし」を1層設置する（最大3層）。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("まきびし", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def マジックルーム_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["マジックルーム"].is_active:
        return HandlerReturn(value=manager.deactivate("マジックルーム"))
    return HandlerReturn(value=manager.activate("マジックルーム", 5))


def まもる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="まもる")


def まもる系_連続使用失敗チェック(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """守る系技の連続使用失敗チェック。

    直前ターンに守る系の技（protect フラグを持つ技）を正常に使用していた場合、
    今ターンの守る系技を失敗させる。
    失敗時は executed_move を None にリセットして次ターンは再度使えるようにする。
    """
    mon = ctx.attacker
    if (
        mon.executed_move is not None
        and mon.executed_move.has_flag("protect")
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "まもる系_連続使用"}
        )
        mon.executed_move = None
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def まるくなる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まるくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"def": 1}, source=mon)
    battle.volatile_manager.apply(mon, "まるくなる")
    return HandlerReturn(value=value)


def みがわり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みがわりの効果を発動する。"""
    mon = ctx.attacker
    battle.volatile_manager.apply(mon, "みがわり", hp=mon.max_hp // 4)
    return HandlerReturn(value=value)


def みがわり_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みがわりが使用可能かを判定する。"""
    mon = ctx.attacker
    if (
        mon.has_volatile("みがわり")
        or mon.hp <= mon.max_hp // 4
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "みがわり"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def みきり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="まもる")


def ミストフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミストフィールド: 地形をミストフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("ミストフィールド", 5))


def みずびたし_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みずびたしの効果: 相手に「みずびたし」状態を付与してみずタイプに変える。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="みずびたし")


def みずびたし_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みずびたしの使用条件チェック: 相手がすでにみずタイプのみなら失敗する。"""
    if ctx.defender.types == ["みず"]:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "みずびたし"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def みちづれ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="みちづれ")


def ミラータイプ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミラータイプの効果: 使用者のタイプを対象のタイプに置換する。

    - テラスタル中かつステラでない: テラスタイプをコピー
    - テラスタル中かつステラ: 元のタイプ（data.types）をコピー
    - テラスタルなし: 元のタイプ（data.types）をコピー
    - タイプ置換後、もりののろい/ハロウィンによる added_types はリセットされる
    """
    attacker = ctx.attacker
    defender = ctx.defender
    target_types: list[Type]
    if defender.terastallized and defender.tera_type != "ステラ":
        target_types = [defender.tera_type]
    else:
        target_types = list(defender.data.types)
    attacker.move_override_types = target_types
    # added_types（もりののろい・ハロウィン等の追加タイプ）をリセットする
    attacker.added_types = []
    return HandlerReturn(value=value)


def ミラータイプ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミラータイプの失敗チェック: 使用者と対象のタイプが一致する場合は失敗する。"""
    attacker = ctx.attacker
    defender = ctx.defender
    target_types: list[Type]
    if defender.terastallized and defender.tera_type != "ステラ":
        target_types = [defender.tera_type]
    else:
        target_types = list(defender.data.types)
    if sorted(attacker.types) == sorted(target_types):
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload={"reason": "ミラータイプ_タイプ同じ"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def めいそう_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 1, "spd": 1})


def メロメロ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メロメロの効果: 相手をメロメロ状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="メロメロ")


def メロメロ_check_gender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メロメロの失敗条件: 相手が同性または性別不明の場合は失敗させる。"""
    attacker = ctx.attacker
    defender = ctx.defender
    # 性別不明（""）または同性の場合は失敗
    if (defender.gender == ""
            or attacker.gender == ""
            or attacker.gender == defender.gender):
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload={"reason": "メロメロ_性別不一致"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def もりののろい_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もりののろいの効果: 相手にもりののろい状態を付与してくさタイプを追加する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="もりののろい")


def もりののろい_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もりののろいの使用条件チェック: 相手がすでにくさタイプなら失敗する。"""
    if ctx.defender.has_type("くさ"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "もりののろい"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def やどりぎのタネ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """やどりぎのタネの効果: 相手をやどりぎのタネ状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="やどりぎのタネ")


def やどりぎのタネ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """やどりぎのタネの使用条件チェック: くさタイプのポケモンには失敗する。"""
    if ctx.defender.has_type("くさ"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "やどりぎのタネ"}
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ゆきげしき_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("ゆき", 5, source=ctx.attacker))


def ゆめくい_check_sleep(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆめくいの使用条件チェック: 相手がねむり状態でない場合に失敗させる。"""
    if not ctx.defender.has_ailment("ねむり"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload={"reason": "ゆめくい_ねむり状態でない"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def リサイクル_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リサイクルの失敗条件チェック。

    以下のいずれかに該当する場合は失敗する:
    - 使用者がすでにアイテムを持っている
    - 使用者がまだアイテムを失ったことがない（last_lost_item_name が空）
    """
    mon = ctx.attacker
    if mon.has_item() or not mon.last_lost_item_name:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload={"reason": "リサイクル"},
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def リサイクル_restore_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リサイクルの効果: 最後に失ったアイテムを取り戻す。"""
    mon = ctx.attacker
    battle.item_manager.gain_item(mon, mon.last_lost_item_name)
    return HandlerReturn(value=value)


def リフレクター_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リフレクター: 自陣営に「リフレクター」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.apply("リフレクター", 5, source=ctx.attacker):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def りゅうのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """りゅうのまいの効果: 自分のこうげき・すばやさを1段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "spe": 1})


def ロックオン_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ロックオン", count=2)


def ロックカット_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 2})


def わたほうし_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """わたほうしの効果: 相手のすばやさを2段階下げる。粉技のためくさタイプ・ぼうじん無効。"""
    return modify_defender_stats(battle, ctx, value, stats={"spe": -2})


def わるだくみ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 2})


def ワンダールーム_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["ワンダールーム"].is_active:
        return HandlerReturn(value=manager.deactivate("ワンダールーム"))
    return HandlerReturn(value=manager.activate("ワンダールーム", 5))
