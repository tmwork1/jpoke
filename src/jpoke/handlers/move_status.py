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
    get_forced_switch_commands,
    modify_attacker_stats,
    modify_defender_stats,
)
from jpoke.core.handler import HandlerReturn
from jpoke.utils.math import round_half_down
from typing import TYPE_CHECKING, Any, cast
if TYPE_CHECKING:
    from jpoke.core import Battle, AttackContext
    from jpoke.model import Pokemon

from jpoke.types import AbilityName, MoveName, SideFieldName, Stat, Type
from jpoke.utils.math import round_half_up

from jpoke.enums import Event, Interrupt, LogCode
from jpoke.core.log_payload import AbilityPayload, FailureLogPayload, ItemPayload, StatChangePayload
from jpoke.data.type_chart import TYPE_MODIFIER, TYPES

# バトンタッチで交代先に引き継ぐ揮発性状態の名前セット
# .internal/wiki/moves/バトンタッチ.html「状態変化の引き継ぎ」表（第9世代列）を正とする。
# 表の凡例: ○=引き継がれる／×=引き継がれない／－=その世代に存在しない／？=判別不能。
# 対象に含めているもの（第9世代で○）:
#   みがわり・こんらん・きゅうしょアップ・やどりぎのタネ・のろい・ほろびのうた・
#   ねをはる・とくせいなし・アクアリング・かいふくふうじ・でんじふゆう
# 対象外としているもの（第9世代で×、または本プロジェクトで未実装のため到達不能）:
# - .internal/spec/volatiles/じゅうでん.md: じゅうでんはバトンタッチで引き継がれない（×）
# - .internal/spec/volatiles/ちょうはつ.md: ちょうはつはバトンタッチで引き継がれない
#   （通常はちょうはつ状態の効果でバトンタッチ自体を使用できないため実質到達不能だが、
#   原作Wikiの記載に合わせて明示的に除外している）
# - .internal/spec/volatiles/たくわえる.md: たくわえるはバトンタッチで引き継がれない（×）。
#   ただし、たくわえるで上昇したぼうぎょ・とくぼうのランク変化は能力変化として別途引き継がれる。
# - .internal/spec/volatiles/しおづけ.md: しおづけはバトンタッチで引き継がれない（×）
# - .internal/spec/volatiles/ちいさくなる.md・.internal/spec/volatiles/まるくなる.md:
#   ちいさくなる・まるくなるの揮発状態自体は第三世代以降バトンタッチで引き継がれない
#   （第9世代欄は空欄だが第3〜8世代が一貫して×のため対象外とする。まるくなる・ちいさくなるで
#   上がった防御・回避のランクは能力変化として別途引き継がれるため、揮発状態自体を
#   対象外としても影響しない）
#
# とくせいなし: volatile_manager.apply の ON_BEFORE_APPLY_VOLATILE では
# ARシステム/アイスフェイス等の protected フラグ持ち特性を防げないため、
# switch_manager 側でバトン先の特性が protected フラグを持つ場合／
# とくせいガード等で変更がブロックされる場合は個別に適用をスキップする
# （.internal/spec/volatiles/とくせいなし.md「他のポケモンがとくせいなしにならない特性を
# 持つ場合は消える」）。
_BATON_PASS_VOLATILES: frozenset[str] = frozenset({
    "みがわり",
    "こんらん",
    "きゅうしょアップ",
    "やどりぎのタネ",
    "のろい",
    "ほろびのうた",
    "ねをはる",
    "とくせいなし",
    "アクアリング",
    "かいふくふうじ",
    "でんじふゆう",
})

# さいはいで指示できない技の名前セット（.internal/spec/moves/さいはい.md「さいはいが失敗する技」節）
# 本プロジェクトの技データに存在しない技名（Zワザ・ダイマックス関連等）も
# 将来の追加に備えて含めているが、現状は該当技が存在しないため実害はない。
_INSTRUCT_BLOCKED_MOVES: frozenset[str] = frozenset({
    # さいはい自身
    "さいはい",
    # 他の技が出る技
    "オウムがえし", "さきどり", "しぜんのちから", "ねごと", "ねこのて", "まねっこ", "ゆびをふる",
    # 他者の技を覚える技
    "スケッチ", "ものまね", "へんしん",
    # 反動で次のターン動けなくなる技
    "がんせきほう", "ギガインパクト", "スターアサルト", "ときのほうこう",
    "ハードプラント", "ハイドロカノン", "はかいこうせん", "ブラストバーン",
    "プリズムレーザー", "ムゲンダイビーム",
    # 溜め技（2ターン技）
    "ソーラービーム", "ソーラーブレード", "そらをとぶ", "あなをほる", "ダイビング",
    "ゴーストダイブ", "シャドーダイブ", "ゴッドバード", "メテオビーム", "エレクトロビーム",
    "コールドフレア", "フリーズボルト", "ブラッドムーン", "デカハンマー",
    # 数ターン行動する技
    "あばれる", "げきりん", "はなびらのまい", "さわぐ", "アイスボール", "ころがる", "がまん",
    # 前ターンの状況に依存する技・特殊な反動技
    "きあいパンチ", "くちばしキャノン", "トラップシェル",
    # 連続使用で成功率が下がるまもる系のうち、指示自体が失敗する技
    "キングシールド", "ブロッキング",
    # その他の指示不可技
    "ゲップ", "わるあがき", "ダイマックスほう", "おいわい", "てをつなぐ",
    # スターモービル専用技
    "ダークアクセル", "バーンアクセル", "ファイトアクセル", "ポイズンアクセル", "マジカルアクセル",
})

def _blocked_by_ougon_no_karada(battle: Battle, mon: Pokemon) -> bool:
    """おうごんのからだ特性: 自分含む全員が対象の変化技（おちゃかい・ほろびのうたなど）に
    おける、使用者以外への効果を防ぐ。

    通常の変化技は Event.ON_BEFORE_APPLY_MOVE の時点で技全体が無効化されるが、
    自分含む全員が対象の技は使用者自身にも効果が及ぶため一律には無効化できない。
    そのため各技のハンドラ側で対象ポケモンごとに本関数を用いて免疫判定を行う
    （.internal/spec/abilities/おうごんのからだ.md「自分含む全員が対象の技」）。
    呼び出し側で使用者自身は対象から除外すること
    （自身が使用する技が自身の特性で防がれることはないため）。
    """
    if not (mon.ability.enabled and mon.ability.name == "おうごんのからだ"):
        return False
    mon.ability.revealed = True
    battle.add_event_log(
        mon,
        LogCode.ABILITY_TRIGGERED,
        payload=AbilityPayload(ability=mon.ability.name),
    )
    return True

def _blocked_by_bouon(battle: Battle, mon: Pokemon) -> bool:
    """ぼうおん特性: 自分含む全員が対象の音技（ほろびのうたなど）における、
    使用者以外への効果を防ぐ。

    通常の音技は Event.ON_BEFORE_APPLY_MOVE の時点で技全体が無効化されるが、
    自分含む全員が対象の音技は使用者自身にも効果が及ぶため一律には無効化できない
    （防いだ場合でも他の対象への効果は通常通り発動する）。
    そのため各技のハンドラ側で対象ポケモンごとに本関数を用いて免疫判定を行う
    （.internal/spec/abilities/ぼうおん.md、handlers/ability.py の _BOUON_EXCLUDED_MOVES）。
    呼び出し側で使用者自身は対象から除外すること
    （現行世代では自身のぼうおんは無視され、自身の技の効果を自身の特性で防ぐことはないため）。
    """
    if not (mon.ability.enabled and mon.ability.name == "ぼうおん"):
        return False
    mon.ability.revealed = True
    battle.add_event_log(
        mon,
        LogCode.ABILITY_TRIGGERED,
        payload=AbilityPayload(ability=mon.ability.name),
    )
    return True

def on_blow_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の効果を防げるかを判定する。"""
    value = battle.events.emit(Event.ON_TRY_BLOW, ctx, value)
    if not value:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_IMMUNED,
            payload=FailureLogPayload(move=ctx.move.name)
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)

def on_blow_check_switch_target(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """吹き飛ばし技の失敗判定を行う。

    相手に交代できる控えポケモン（生存しているベンチポケモン）がいない場合、
    技自体が失敗する（.internal/spec/turn.md の Event.ON_APPLY_MOVE priority=100
    「ほえる・ふきとばし: 交代不可・野生」に対応）。
    """
    player = battle.get_player(ctx.defender)
    if not get_forced_switch_commands(battle, player):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="交代不可"),
        )
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
    commands = get_forced_switch_commands(battle, player)
    if commands:
        command = battle.random.choice(commands)
        battle.run_switch(player, state.team[command.index])
    return HandlerReturn(value=value)


def アクアリング_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アクアリングの効果: 自分をアクアリング状態にする。"""
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="すでに状態異常になっている"),
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


def あまいかおり_lower_defender_evasion(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"evasion": -2})


def あまえる_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -2})


def あまごい_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("あめ", 5, source=ctx.attacker))


def あやしいひかり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あやしいひかりの効果: 相手をこんらん状態にする。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def アロマセラピー_cure_team_ailment(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アロマセラピー: 自分（シングルバトルでは選出チーム）の状態異常を回復する。

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


def アンコール_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アンコールの効果を発動する。

    ロックする対象は仕様（.internal/spec/moves/アンコール.md）の「最後にPPを消費した技」。
    ねごとのサブ技（PP消費0）ではなくねごと自身が対象になる。
    """
    move = ctx.defender.pp_consumed_move
    return apply_volatile_to_defender(
        battle, ctx, value, volatile="アンコール", count=3, move_name=move.name
    )


def アンコール_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アンコールの失敗条件を判定する。

    - 相手がPPを消費する行動をしていない（pp_consumed_move が None）場合は失敗する
    - 相手が最後にPPを消費した技（ねごと等でサブ技を実行した場合はねごと自身）が
      non_encore ラベルを持つ場合は失敗する
    - PP消費後に失敗した技（ねむり状態でないのに使ったねごと等）も
      「最後にPPを消費した技」として判定の対象になる
    """
    move = ctx.defender.pp_consumed_move
    if not move or move.has_flag("non_encore"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="アンコール失敗")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def いえき_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いえきの効果: 相手に「とくせいなし」状態を付与する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="とくせいなし")


def いえき_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いえきの失敗条件を判定する。

    対象の特性が protected フラグを持つ場合、
    または対象の特性変更がとくせいガード等で防がれる場合は失敗する。
    """
    if (
        ctx.defender.ability.has_flag("protected")
        or battle.ability_manager.is_change_blocked(ctx.defender)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="いえき")
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
    """いちゃもんの効果: 相手がいちゃもん状態になり、直前に選択した技を出せなくなる。

    相手が場に出てから技を使用していない場合でも付与自体は成功する
    （その場合は move_name="" となり、実質的に禁止技は発生しない）。
    """
    move = ctx.defender.selected_move
    return apply_volatile_to_defender(
        battle, ctx, value, volatile="いちゃもん", move_name=move.name if move else ""
    )


def いとをはく_lower_defender_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いとをはくの効果: 相手のすばやさを 2 段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"spe": -2})


def いのちのしずく_heal(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちのしずく: 最大HPの1/4を回復する。HPが満タンの場合は失敗する。

    端数は四捨五入で丸める（一次情報: .internal/wiki/moves/いのちのしずく.html 技の仕様節）。
    同じ1/4回復技でも `ジャングルヒール` `みかづきのいのり` は切り捨てのため、
    本技のみ `round_half_up` を使う点に注意。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, v=round_half_up(mon.max_hp / 4))
    return HandlerReturn(value=value)


def いばる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いばるの効果: 相手のこうげきを2段階上げ、相手をこんらん状態にする。"""
    battle.modify_stats(ctx.defender, {"atk": 2}, source=ctx.attacker)
    battle.volatile_manager.apply_confusion(ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def いばる_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いばるの失敗条件: 相手のこうげきランクがすでに+6、かつすでにこんらん状態なら失敗する。"""
    assert ctx.defender is not None
    if ctx.defender.boosts["atk"] == 6 and ctx.defender.has_volatile("こんらん"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="いばる")
        )
        return HandlerReturn(value=False, stop_event=True)
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
    控えのポケモンがいない場合は失敗し、使用者はひんしにならない。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    if not battle.query.can_switch(player):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="いやしのねがい_交代不可")
        )
        return HandlerReturn(value=False, stop_event=True)
    side = battle.get_side(mon)
    side.activate("いやしのねがい", 1)
    battle.faint(mon)
    return HandlerReturn(value=value)


def いやしのはどう_heal_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いやしのはどう: 相手の最大HPの1/2（メガランチャー所持時は3/4）を回復する。

    通常時の端数は切り上げ、メガランチャー所持時は五捨五超入（round_half_down）で丸める。
    HPが満タンの場合は失敗する。
    """
    mon = ctx.defender
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    if ctx.attacker.ability.name == "メガランチャー":
        heal = round_half_down(mon.max_hp * 3 / 4)
    else:
        heal = (mon.max_hp + 1) // 2
    battle.modify_hp(mon, v=heal)
    return HandlerReturn(value=value)


def いやなおと_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -2})


def うそなき_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うそなきの効果: 相手のとくぼうを2段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2})


def うたう_apply_sleep(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うたうの効果: 相手をねむり状態にする。音系の技のためみがわりを貫通する。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def _ability_name_to_copy(mon: Pokemon) -> AbilityName:
    """うつしえ・なりきりでコピーする際に参照する対象の特性名を返す。

    とくせいなし状態（いえき・コアパニッシャー等）の場合、無効化された
    特性の名前（空文字列）をそのままコピーする。
    かがくへんかガス等、とくせいなし以外の理由で特性が抑制されている場合は
    見た目の効果が発動していなくても内部的には元の特性が残っているため、
    base_name（元の特性名）をコピーする。
    """
    if mon.has_volatile("とくせいなし"):
        return mon.ability.name
    return mon.ability.base_name


def うつしえ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うつしえの失敗条件チェック。

    以下の場合は失敗する:
    - 対象の特性が uncopyable フラグを持つ（コピーできない特性）
    - 使用者の特性が protected フラグを持つ（上書きできない特性）
    - 使用者と対象の特性がすでに同じである
    - 使用者の特性変更がとくせいガード等で防がれる
    """
    assert ctx.defender is not None
    if (
        ctx.defender.ability.has_flag("uncopyable")
        or ctx.attacker.ability.has_flag("protected")
        or ctx.attacker.ability.base_name == ctx.defender.ability.base_name
        or battle.ability_manager.is_change_blocked(ctx.attacker)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="うつしえ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def うつしえ_change_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うつしえの効果: 使用者の特性を対象の特性と同じにする。

    対象がとくせいなし状態の場合は無効化された特性名（空文字列）を、
    かがくへんかガス等それ以外の理由で抑制されている場合は元の特性名を
    コピーする（`_ability_name_to_copy` 参照）。
    """
    assert ctx.defender is not None
    battle.change_ability(ctx.attacker, _ability_name_to_copy(ctx.defender))
    return HandlerReturn(value=value)


def うらみ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うらみの失敗チェック。

    仕様（.internal/spec/moves/うらみ.md）の「最後にPPを消費した技」を対象とするため、
    ねごとのサブ技（PP消費0）ではなくねごと自身が対象になる。
    以下のいずれかに該当する場合は失敗する。
    - 相手がPPを消費する行動をしていない（pp_consumed_move が None）
    - 相手が最後にPPを消費した技が「わるあがき」（PPが概念上無限で対象にならない）
    - 相手が最後にPPを消費した技のPPがすでに0（他の効果で0まで減っていた場合）
    """
    move = ctx.defender.pp_consumed_move
    if move is None or move.name == "わるあがき" or move.pp <= 0:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="うらみ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def うらみ_deplete_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うらみの効果: 相手が最後にPPを消費した技のPPを4減らす。

    move.modify_pp は通常のPP消費経路（move_executor._consume_pp）を経由しないため、
    ここで改めて Event.ON_PP_CONSUMED を発火し、ヒメリのみ等の「PPが0になったとき」
    反応する効果を反応させる（一次情報: ヒメリのみは「うらみ/ぶきみなじゅもんの効果で
    PPが0になったときは発動する」）。
    """
    defender = ctx.defender
    move = defender.pp_consumed_move
    move.modify_pp(-4)
    battle.events.emit(
        Event.ON_PP_CONSUMED,
        ctx.derive(attacker=defender, defender=battle.foe(defender), move=move),
        move.pp,
    )
    return HandlerReturn(value=value)


def エレキフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """エレキフィールド: 地形をエレキフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("エレキフィールド", 5))


def えんまく_lower_defender_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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


def おたけび_lower_defender_atk_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おたけびの効果: 相手のこうげきととくこうを 1 段階ずつ下げる。音系の技のためみがわりを貫通する。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1, "spa": -1})


def おだてる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おだてるの効果: 相手のとくこうを1段階上げ、相手をこんらん状態にする。"""
    battle.modify_stats(ctx.defender, {"spa": 1}, source=ctx.attacker)
    battle.volatile_manager.apply_confusion(ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def おだてる_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おだてるの失敗条件: 相手のとくこうランクがすでに+6、かつすでにこんらん状態なら失敗する。"""
    assert ctx.defender is not None
    if ctx.defender.boosts["spa"] == 6 and ctx.defender.has_volatile("こんらん"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="おだてる")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def おちゃかい_force_consume_berries(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おちゃかい: 場の全ポケモン（使用者→相手の順）が持っているきのみを、
    発動条件を無視して強制消費し、その効果を受けさせる。

    姿を隠しているポケモン（そらをとぶ・あなをほる・ダイビング）は消費しない。
    きのみを消費できるポケモンが1体もいなくても技自体は成功する
    （失敗判定は行わない）。
    """
    hidden_volatiles = ("そらをとぶ", "あなをほる", "ダイビング")
    attacker = ctx.attacker
    targets = [attacker] + [mon for mon in battle.actives if mon is not attacker]

    for mon in targets:
        if any(mon.has_volatile(v) for v in hidden_volatiles):
            continue
        if not mon.item.is_berry():
            continue
        if mon is not attacker and _blocked_by_ougon_no_karada(battle, mon):
            continue
        battle.item_manager.force_trigger_berry(mon)

    return HandlerReturn(value=value)


def おにび_apply_burn(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど")


def オーロラベール_check_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーロラベールの使用条件チェック: 天気が「ゆき」でない場合は失敗する。"""
    if battle.weather.name != "ゆき":
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="オーロラベール")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def オーロラベール_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーロラベール: 自陣営に「オーロラベール」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.apply("オーロラベール", 5, source=ctx.attacker):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def かいでんぱ_lower_defender_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """相手の特攻を2段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"spa": -2})


def かいふくふうじ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かいふくふうじの効果: 相手に「かいふくふうじ」状態を付与する（5 ターン）。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="かいふくふうじ", count=5)


def かえんのまもり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="かえんのまもり")


def かえんのまもり_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かえんのまもりの効果: そのターンの最後に行動する場合は失敗する。

    かえんのまもりはそのターンに自分より後に行動する相手の技から身を守るための
    技であるため、自分がそのターンの最後に行動する場合は守る対象がなく失敗する
    （シングルバトル想定）。
    この失敗により run_move の finally で failed_or_immobile_last_turn が True に
    なるため、まもる系の連続使用チェック（failed_or_immobile_last_turn を参照）は
    次ターン自然にリセットされる。個別のリセット処理は不要。
    """
    attacker_player = battle.get_player(ctx.attacker)
    if battle.query.is_second_actor(attacker_player):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="かえんのまもり_最終行動")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def かげぶんしん_boost_attacker_evasion(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かげぶんしんの効果: 自分の回避率を 1 段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"evasion": 1})


def かたくなる_boost_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かたくなるの効果: 自分の防御を1段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1})


def かなしばり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かなしばりの効果: 相手に「かなしばり」状態を付与する（4 ターン）。

    封じる対象は仕様（.internal/spec/moves/かなしばり.md）の「相手が最後にPPを消費した技」。
    ねごとのサブ技（PP消費0）ではなくねごと自身が封じられる。
    """
    move = ctx.defender.pp_consumed_move
    return apply_volatile_to_defender(
        battle, ctx, value, volatile="かなしばり", count=4, move_name=move.name
    )


def かなしばり_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かなしばりの失敗条件を判定する。

    - 相手がPPを消費する行動をしていない（pp_consumed_move が None）場合は失敗する
    - わるあがきに対して使うと失敗する
    """
    move = ctx.defender.pp_consumed_move
    if (
        not move
        or move.name == "わるあがき"
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="かなしばり")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def からにこもる_boost_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1})


def からをやぶる_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1, "spd": -1, "atk": 2, "spa": 2, "spe": 2})


def ガードシェア_equalize_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ガードシェア: 使用者と相手のぼうぎょ・とくぼうの実数値を平均化する。

    ランク変化は行わず、実数値のみを書き換える。
    平均は切り捨て（// 2）。
    """
    atk, df = ctx.attacker, ctx.defender
    # B=インデックス2、D=インデックス4
    for idx in (2, 4):
        avg = (atk.get_raw_stat(idx) + df.get_raw_stat(idx)) // 2
        atk.set_raw_stat(idx, avg)
        df.set_raw_stat(idx, avg)
    return HandlerReturn(value=value)


def ガードスワップ_swap_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ガードスワップ: 使用者と相手のぼうぎょ・とくぼうのランク変化を入れ替える。

    実数値は変化せず、ランク変化のみを互いに入れ替える。
    """
    atk_rank = ctx.attacker.boosts
    def_rank = ctx.defender.boosts
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

    みがわり状態では回避率変化のみ防がれ、場の効果解除は独立して発動する
    （技自体は MoveData の bypass_substitute フラグでみがわりを貫通する）。
    しろいきりも回避率変化を防いだ後に自身を含む場の効果を解除されるため、
    回避率変化を場の効果解除より先に行う（一次情報: .internal/wiki/moves/きりばらい.html
    技の仕様節）。
    """
    changed = False

    # 対象の回避率を1段階下げる（みがわり状態では防がれる）
    if not ctx.defender.has_volatile("みがわり"):
        if battle.modify_stats(ctx.defender, {"evasion": -1}, source=ctx.attacker):
            changed = True

    # 対象側の壁系を解除
    defender_side = battle.get_side(ctx.defender)
    wall_names = ["ひかりのかべ", "リフレクター", "オーロラベール", "しんぴのまもり", "しろいきり"]
    for wall in wall_names:
        if defender_side.deactivate(wall):
            changed = True

    # 両陣営のトラップを解除
    trap_names = ["まきびし", "どくびし", "ステルスロック", "ねばねばネット"]
    for side in battle.side_managers:
        for trap in trap_names:
            if side.deactivate(trap):
                changed = True

    # フィールドを解除
    if battle.terrain_manager.remove():
        changed = True

    return HandlerReturn(value=changed)


def キングシールド_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="キングシールド")


def きんぞくおん_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2})


def ギアチェンジ_boost_attacker_atk_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ギアチェンジの効果: 自分のこうげきを1段階、すばやさを2段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "spe": 2})


def くすぐる_lower_defender_atk_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くすぐるの効果: 相手のこうげきとぼうぎょを 1 段階ずつ下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1, "def": -1})


def くろいきり_reset_all_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くろいきりの効果: 場にいる全ポケモンの能力ランクを±0にリセットする。

    しろいきり状態でも防げない（ON_BEFORE_MODIFY_STAT を経由しない直接リセット）。
    """
    for mon in battle.actives:
        changed = {s: v for s, v in mon.boosts.items() if v != 0}
        if changed:
            for s in changed:
                mon.boosts[s] = 0
            battle.add_event_log(
                mon, LogCode.STAT_CHANGED,
                payload=StatChangePayload(
                    stats={s: -v for s, v in changed.items()}, display_reason="くろいきり"
                ),
            )
    return HandlerReturn(value=value)


def くろいまなざし_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くろいまなざしの効果: 相手をにげられない状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="にげられない")


def グラスフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """グラスフィールド: 地形をグラスフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("グラスフィールド", 5))


def こうそくいどう_boost_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 2})


def コスモパワー_boost_attacker_def_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1, "spd": 1})


def コットンガード_boost_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 3})


def こらえる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こらえるの効果: 自分にこらえる状態を付与する。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="こらえる")


def こわいかお_lower_defender_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こわいかおの効果: 相手のすばやさを2段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"spe": -2})


# コートチェンジで入れ替え対象となるサイドフィールド一覧。
# 壁3種・設置技4種（まきびし/どくびし/ステルスロック/ねばねばネット）・
# おいかぜ・しろいきり・しんぴのまもりのみが対象。
# いやしのねがい/みかづきのまい/ねがいごと/みらいよち/はめつのねがいは
# SideFieldName型には含まれるが「単体の場に発生する状態」のため対象外
# （.internal/spec/moves/コートチェンジ.md、.internal/spec/fields/ねがいごと.md参照）。
# ひのうみ/にじ/しつげん/キョダイ○○（キョダイマックス専用の場）は
# 本プロジェクト（チャンピオンズ）で未実装のダイマックス関連要素のため対象外。
_COURT_CHANGE_TARGET_FIELDS: tuple[SideFieldName, ...] = (
    "リフレクター", "ひかりのかべ", "オーロラベール",
    "まきびし", "どくびし", "ステルスロック", "ねばねばネット",
    "おいかぜ", "しろいきり", "しんぴのまもり",
)


def コートチェンジ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """コートチェンジの失敗チェック: 入れ替える場の状態がどちらの陣営にも無い場合は失敗する。"""
    attacker_side = battle.get_side(ctx.attacker)
    defender_side = battle.get_side(ctx.defender)
    has_target = any(
        attacker_side.get(name).is_active or defender_side.get(name).is_active
        for name in _COURT_CHANGE_TARGET_FIELDS
    )
    if not has_target:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="コートチェンジ_場の状態なし"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def コートチェンジ_swap_fields(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """コートチェンジの効果: お互いの場の状態（壁・設置技・おいかぜ・しろいきり・しんぴのまもり）を入れ替える。

    継続ターン数（ひかりのねんどによる延長・まきびし等の層数を含む）はそのまま
    入れ替わる。ON_FIELD_ACTIVATE/ON_FIELD_DEACTIVATE イベントは発火しないため、
    おいかぜが移動してもかぜのり・ふうりょくでんきは誤発動しない。
    """
    attacker_side = battle.get_side(ctx.attacker)
    defender_side = battle.get_side(ctx.defender)
    attacker_side.swap_fields(defender_side, _COURT_CHANGE_TARGET_FIELDS)
    return HandlerReturn(value=value)


def ごりむちゅう_release_lock_on_ability_change(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なりきり・スキルスワップの使用により自身が新たにごりむちゅうを得た場合、
    その技自体ではロックしない（次のターンのみ自由に技を選べる）。

    ごりむちゅうの `ON_MOVE_END` ハンドラ（デフォルト優先度100、`ごりむちゅう_lock_move`）
    より後に発動させ、自身の効果で入手したごりむちゅうによるロックを解除する
    （なりきり・スキルスワップ双方の登録時に priority=110 を指定する）。
    """
    mon = ctx.attacker
    if mon.ability.base_name == "ごりむちゅう" and mon.has_volatile("ごりむちゅう"):
        battle.volatile_manager.remove(mon, "ごりむちゅう")
    return HandlerReturn(value=value)


def さいきのいのり_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さいきのいのりの失敗条件: ひんし状態の味方（控え）が1体もいない場合は失敗する。"""
    player = battle.get_player(ctx.attacker)
    state = battle.player_states[player]
    if not any(mon.fainted for mon in state.bench):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="さいきのいのり_ひんしなし")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def さいきのいのり_revive(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さいきのいのりの効果: ひんし状態の味方を選出順で先頭から1体選び、
    最大HPの1/2（切り捨て）を回復して復活させる。

    実機では復活させる味方をプレイヤーが選ぶが、通信対戦で選択が時間切れに
    なった場合は選出順で最初のひんし状態のポケモンが自動的に選ばれる
    （一次情報: .internal/wiki/moves/さいきのいのり.html 技の仕様節）。本プロジェクトは
    復活対象選択のUIを持たないため、常にこの自動選択と同じ挙動（選出順で
    最初にひんし状態の味方）を採用する。`さいきのいのり_check` が呼び出し前に
    候補の存在を保証しているため、ここでは存在チェックを行わない。
    """
    player = battle.get_player(ctx.attacker)
    state = battle.player_states[player]
    target = next(mon for mon in state.bench if mon.fainted)
    battle.modify_hp(target, v=max(1, target.max_hp // 2), source=ctx.attacker)
    return HandlerReturn(value=value)


def サイコフィールド_activate_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サイコフィールド: 地形をサイコフィールドにする。"""
    return HandlerReturn(value=battle.terrain_manager.apply("サイコフィールド", 5))


def さいはい_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さいはいの失敗条件を判定する。

    仕様（.internal/spec/moves/さいはい.md「技の仕様」）では対象は「直近のPPを消費した行動」の技
    であるため、pp_consumed_move を参照する（ねごとのサブ技はPPを消費しないため対象に
    ならず、ねごと自身が対象となり指示不可技として失敗する）。
    - 相手が場に出てからPPを消費する行動を一度もしていない（pp_consumed_move が None）
      場合は失敗する
    - 相手が最後にPPを消費した技が指示できない技（_INSTRUCT_BLOCKED_MOVES）の場合は失敗する
    - 相手が最後にPPを消費した技のPPがすでに0の場合は失敗する
      （0のまま battle.run_move に渡すと わるあがき に自動置換されてしまうため、ここで弾く）
    """
    move = ctx.defender.pp_consumed_move
    if move is None or move.name in _INSTRUCT_BLOCKED_MOVES or move.pp <= 0:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="さいはい")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def さいはい_instruct(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さいはいの効果: 相手が最後にPPを消費した技を、相手のPPを消費してもう一度使わせる。

    battle.run_move(ctx.defender, move) により通常の技実行フローが走るため、
    状態異常・状態変化による行動失敗判定やPP消費、ちょうはつ等による技封じは
    通常の技実行と同様に処理される。

    さいはい自身の ON_BEFORE_APPLY_MOVE / ON_STATUS_HIT ハンドラは、この呼び出しが完了するまで
    イベントマネージャーに登録されたままになる。登録されたままだと、指示された技の実行中にも
    さいはいの使用者（ctx.attacker）に対してこれらのイベントが発火し、さいはい_can_apply が
    無関係な技（指示された技自身）に対して誤って再評価されてしまう
    （この時点で ctx.attacker.pp_consumed_move はすでにさいはい自身に更新済みのため、
    「さいはいはさいはいを指示できない」という自己参照チェックに誤って引っかかり、
    指示した技のPPだけ消費されて不発になってしまう）。これを避けるため、
    指示された技の実行中はさいはい自身の ON_BEFORE_APPLY_MOVE / ON_STATUS_HIT ハンドラを
    一時的に解除する（ねごと_select_and_execute と同じパターン）。
    """
    move = ctx.defender.pp_consumed_move
    suppressed_events = (Event.ON_BEFORE_APPLY_MOVE, Event.ON_STATUS_HIT)
    handlers_data = ctx.move.data.handlers
    for event in suppressed_events:
        handler = handlers_data.get(event)
        if handler is None:
            continue
        for h in (handler if isinstance(handler, list) else [handler]):
            battle.events.off(event, h, ctx.attacker)
    try:
        battle.run_move(ctx.defender, move)
    finally:
        for event in suppressed_events:
            handler = handlers_data.get(event)
            if handler is None:
                continue
            for h in (handler if isinstance(handler, list) else [handler]):
                battle.events.on(event, h, ctx.attacker)
    return HandlerReturn(value=value)


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
        "boosts": {},
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="しっぽきり_みがわり中")
        )
        return HandlerReturn(value=False, stop_event=True)

    # 最大HPの半分以下は失敗する（切り上げ）
    if mon.hp <= (mon.max_hp + 1) // 2:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="しっぽきり_HP不足")
        )
        return HandlerReturn(value=False, stop_event=True)

    if not battle.query.can_switch(player):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="しっぽきり_交代不可")
        )
        return HandlerReturn(value=False, stop_event=True)

    return HandlerReturn(value=value)


def しっぽをふる_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1})


def しびれごな_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しびれごなの効果: 相手をまひ状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def しょうりのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しょうりのまいの効果: 自分のこうげき・ぼうぎょ・すばやさを1段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1, "spe": 1})


def しろいきり_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しろいきり: 自陣営に「しろいきり」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.apply("しろいきり", 5, source=ctx.attacker):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def しんぴのまもり_set_side_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しんぴのまもり: 自陣営に「しんぴのまもり」を5ターン設定する。"""
    side = battle.get_side(ctx.attacker)
    if not side.activate("しんぴのまもり", 5):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def シンプルビーム_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シンプルビームの失敗条件チェック。

    以下の場合は失敗する:
    - 対象の特性が「なまけ」である（`なまけ` には `protected` フラグが
      付与されていないため、`base_name` での個別チェックが必要）
    - 対象の特性が「上書きできない特性」（`protected` フラグ）を持つ
    - 対象の特性がすでに「たんじゅん」である
    - 対象の特性変更がとくせいガード等で防がれる
    """
    defender_ability = ctx.defender.ability.base_name
    if (
        defender_ability == "なまけ"
        or ctx.defender.ability.has_flag("protected")
        or defender_ability == "たんじゅん"
        or battle.ability_manager.is_change_blocked(ctx.defender)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="シンプルビーム")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def シンプルビーム_change_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シンプルビームの効果: 相手の特性を「たんじゅん」に書き換える。"""
    battle.change_ability(ctx.defender, "たんじゅん")
    return HandlerReturn(value=value)


def じこあんじ_copy_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じこあんじ: 相手の能力ランク変化・急所ランクをすべて自分にコピーする。

    相手のランクは変化しない。direct代入により、たんじゅん・あまのじゃく・
    クリアボディ・だっしゅつパック等のランク変化に反応する特性・アイテムを
    経由しない。ただし、しろいハーブのみコピー直後にマイナスのランクを
    打ち消す特例がある（一次情報: .internal/wiki/moves/じこあんじ.html 技の仕様節）。
    """
    attacker = ctx.attacker
    defender = ctx.defender
    rank_stats: list[Stat] = ["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]
    changed = {
        stat: defender.boosts[stat] - attacker.boosts[stat]
        for stat in rank_stats
        if defender.boosts[stat] != attacker.boosts[stat]
    }
    for stat in rank_stats:
        attacker.boosts[stat] = defender.boosts[stat]
    if changed:
        battle.add_event_log(
            attacker, LogCode.STAT_CHANGED,
            payload=StatChangePayload(stats=changed, display_reason="じこあんじ"),
        )

    # 急所ランクに関する効果（きゅうしょアップ状態）も第六世代以降コピー対象。
    # Pokemon.critical_rank のセッターはテスト・デバッグ用の直接代入であり、
    # volatile_manager を経由しないためイベントハンドラの登録・解除が行われない
    # （既存のvolatileを直接delすると、登録済みハンドラが残ったまま
    # ctx.attacker.volatiles["きゅうしょアップ"] へのアクセスでKeyErrorになる）。
    # そのため付け外しは battle.volatile_manager.apply/remove を経由する。
    defender_critical_rank = defender.critical_rank
    if attacker.critical_rank != defender_critical_rank:
        if attacker.has_volatile("きゅうしょアップ"):
            battle.volatile_manager.remove(attacker, "きゅうしょアップ")
        if defender_critical_rank > 0:
            battle.volatile_manager.apply(
                attacker, "きゅうしょアップ", count=defender_critical_rank
            )

    # しろいハーブ: マイナスのランクをコピーした直後に発動する（じこあんじ固有の特例）。
    if attacker.item.name == "しろいハーブ":
        changed = {s: -v for s, v in attacker.boosts.items() if v < 0}
        if changed:
            for s in changed:
                attacker.boosts[s] = 0
            battle.add_event_log(
                attacker, LogCode.STAT_CHANGED,
                payload=StatChangePayload(stats=changed, display_reason="しろいハーブ"),
            )
            battle.add_event_log(
                attacker, LogCode.ITEM_TRIGGERED,
                payload=ItemPayload(item=attacker.item.name),
            )
            attacker.item.revealed = True
            battle.item_manager.consume_item(attacker)

    return HandlerReturn(value=value)


def じこさいせい_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じこさいせい: 最大HPの1/2を回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def じばそうさ_boost_attacker_def_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じばそうさの効果: ぼうぎょ・とくぼうをそれぞれ1段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1, "spd": 1})


def じばそうさ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じばそうさの失敗条件: 使用者の特性がプラス/マイナスでない場合は失敗させる。"""
    if ctx.attacker.ability.name not in ("プラス", "マイナス"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="じばそうさ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ジャングルヒール_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ジャングルヒール: 自分のHPを最大HPの1/4回復し、状態異常を治す。

    HPが満タンかつ状態異常もない場合は失敗する。端数は切り捨て。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp and not mon.ailment.is_active:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1 / 4)
    battle.ailment_manager.remove(mon)
    return HandlerReturn(value=value)


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
    使用者または対象がとくせいガードを持ち特性の変更が防がれる場合も失敗する。

    例外: うのミサイルは上書き（いえき・なかまづくり等）には protected フラグで
    抵抗するが、SV Ver.3.0.0 以降はスキルスワップ/さまようたましいでの交換のみ
    可能になったため base_name で個別に除外する。

    かがくへんかガス/クォークチャージ/こだいかっせい/どくくぐつ/はらぺこスイッチは
    protected フラグを持たない（いえき/コアパニッシャー等による上書き・無効化は
    可能なため）が、スキルスワップ/さまようたましいでの交換だけは対象外のため
    base_name で個別に判定する。
    """
    assert ctx.defender is not None
    UNSWAPPABLE_ABILITIES = (
        "かがくへんかガス", "クォークチャージ", "こだいかっせい", "どくくぐつ", "はらぺこスイッチ",
    )
    if (
        (ctx.attacker.ability.has_flag("protected") and ctx.attacker.ability.base_name != "うのミサイル")
        or (ctx.defender.ability.has_flag("protected") and ctx.defender.ability.base_name != "うのミサイル")
        or ctx.attacker.ability.base_name in UNSWAPPABLE_ABILITIES
        or ctx.defender.ability.base_name in UNSWAPPABLE_ABILITIES
        or battle.ability_manager.is_change_blocked(ctx.attacker)
        or battle.ability_manager.is_change_blocked(ctx.defender)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="スキルスワップ")
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
    とらわれ状態（ありじごく・ねをはる・かげふみ・じりょく・バインド・にげられない・
    フェアリーロック等）を無視して交代できるため、バトンタッチと同様に
    `battle.query.can_switch` は使わず控えの生存だけを直接判定する。
    """
    result = modify_defender_stats(battle, ctx, value, stats={"atk": -1, "spa": -1})

    # ランク低下が完全に阻まれた（実際の変化量が空）場合は交代しない
    if not result.value:
        return result

    player = battle.get_player(ctx.attacker)
    state = battle.player_states[player]
    if any(mon.alive for mon in state.bench):
        state.interrupt = Interrupt.PIVOT

    return HandlerReturn(value=value)


def ステルスロック_set_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ステルスロック: 相手側のフィールドにステルスロックを設置する。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("ステルスロック", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def すなあつめ_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すなあつめ: 自分のHPを最大HPの1/2回復する。すなあらし状態のときは2732/4096(≒2/3)回復する。

    天候の有効判定は battle.weather_for() に委譲する（エアロック・ノーてんき考慮済み）。
    端数は五捨五超入（round_half_down）で丸める。HPが満タンの場合は失敗する。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    weather = battle.weather_for(mon)
    if weather.name == "すなあらし":
        heal = round_half_down(mon.max_hp * 2732 / 4096)
    else:
        heal = round_half_down(mon.max_hp / 2)
    battle.modify_hp(mon, v=heal)
    return HandlerReturn(value=value)


def すなあらし_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("すなあらし", 5, source=ctx.attacker))


def すなかけ_lower_defender_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1})


def スピードスワップ_swap_speed(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """スピードスワップ: 使用者と相手のすばやさの実数値を入れ替える。

    ランク変化は行わず、実数値のみを入れ替える。
    インデックス 5 = すばやさ（[HP, 攻撃, 防御, 特攻, 特防, 素早さ]）。
    """
    atk, df = ctx.attacker, ctx.defender
    atk_spe, def_spe = atk.get_raw_stat(5), df.get_raw_stat(5)
    atk.set_raw_stat(5, def_spe)
    df.set_raw_stat(5, atk_spe)
    return HandlerReturn(value=value)


def すりかえ_release_choice_lock(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すりかえ・トリックの使用後、こだわりロックを解除する。

    自分自身の効果でこだわり系アイテムを新たに入手した場合、通常のこだわり系
    アイテムの `ON_MOVE_END` ハンドラ（`こだわり_lock_move`）によりこの技に
    ロックされてしまうが、すりかえ・トリックはその効果自体ではロックされない
    （第五世代以降の仕様）。また、既にこだわりでロックされていた場合も、
    このすりかえ・トリックの使用でロックが解除される。
    優先度をこだわり系アイテムの `ON_MOVE_END` ハンドラ（デフォルト優先度100）
    より遅く（110）することで、先に設定されたロックを確実に解除する。
    """
    mon = ctx.attacker
    if mon.has_volatile("こだわり"):
        battle.volatile_manager.remove(mon, "こだわり")
    return HandlerReturn(value=value)


def すりかえ_swap_items(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """すりかえ・トリックのアイテム交換効果。

    source=ctx.attacker を渡すことで、この技の使用者自身が持つねんちゃくは
    発動しない（自分から道具を交換するときは防がれない）が、相手が持つ
    ねんちゃくは通常どおり交換を阻止する。
    """
    success = battle.item_manager.swap_items(source=ctx.attacker)
    return HandlerReturn(value=success)


def スレッドトラップ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="スレッドトラップ")


def せいちょう_boost_attacker_atk_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """せいちょう: 天候が晴れの時はこうげき・とくこうを2段階、通常時は1段階上げる。
    攻撃側がばんのうがさを持つ場合、晴れでも1段階のみ。
    """
    n = 2 if battle.weather_for(ctx.attacker).sunny else 1
    return modify_attacker_stats(battle, ctx, value, stats={"atk": n, "spa": n})


def そうでん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """そうでんの効果: 相手をそうでん状態にする（そのターン中のみ）。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="そうでん")


def そうでん_try_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """そうでんの発動条件を判定する。

    相手（対象）がそのターンすでに行動済み（コマンド消費済み）の場合は失敗する。
    """
    def_player = battle.get_player(ctx.defender)
    def_state = battle.player_states[def_player]
    if not def_state.command_reserved():
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="そうでん")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ソウルビート_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソウルビートの使用条件チェック: HPが最大HPの1/3以下、またはこうげき・ぼうぎょ・とくこう・とくぼう・すばやさが
    すべて+6ならば失敗する。"""
    mon = ctx.attacker
    if (
        mon.hp <= mon.max_hp // 3
        or all(mon.boosts[stat] >= 6 for stat in ("atk", "def", "spa", "spd", "spe"))
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ソウルビート")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ソウルビート_pay_hp_and_boost_all_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソウルビートの効果: 最大HPの1/3を消費し、すべての能力を1段階ずつ上げる。

    reason="self_cost": マジックガードでも防げない自己HP消費として扱う（ききかいひ不発）。
    """
    mon = ctx.attacker
    battle.modify_hp(mon, r=-1/3, reason="self_cost", source=mon)
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="たくわえる")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def たてこもる_boost_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """たてこもるの効果: 自分のぼうぎょを 2 段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2})


def タマゴうみ_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """タマゴうみ: 最大HPの1/2を回復する（じこさいせいと同一効果）。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def タールショット_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """タールショットの効果: 相手にタールショット状態を付与し、すばやさを1段階下げる。"""
    assert ctx.defender is not None
    battle.volatile_manager.apply(ctx.defender, "タールショット", source=ctx.attacker)
    return HandlerReturn(value=battle.modify_stats(ctx.defender, {"spe": -1}, source=ctx.attacker))


def ダークホール_apply_sleep(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ダークホールの効果: 相手をねむり状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり")


def ダークホール_check_species(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ダークホールの発動条件チェック。

    第七世代以降、ダークライ以外が使用すると必ず失敗する（種族制限）。
    マジックコートで跳ね返された場合はこのチェックを再度通らないため、
    跳ね返す側は種族制限を受けずに成功する。
    """
    if ctx.attacker.name != "ダークライ":
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


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
    from jpoke.core.context import EventContext  # 循環importを避けるための遅延import

    assert ctx.defender is not None
    # 相手のこうげきランク補正込みの実数値分だけ自分のHPを回復（ランク変更前に取得）
    recover_amount = ctx.defender.ranked_stats["atk"]
    # ON_CALC_DRAIN は EventContext 専用イベント（おおきなねっこ等が source:self で判定するため）。
    # AttackContext のまま渡さず、回復対象（attacker）を source に正規化して発火する。
    recover_amount = battle.events.emit(
        Event.ON_CALC_DRAIN, EventContext(source=ctx.attacker), recover_amount
    )
    battle.modify_hp(ctx.attacker, v=recover_amount, reason="drain")
    # 相手のこうげきを1段階下げる（失敗しても回復は発動済み）
    battle.modify_stats(ctx.defender, {"atk": -1}, source=ctx.attacker)
    return HandlerReturn(value=value)


def ちからをすいとる_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちからをすいとるの失敗チェック: 相手のこうげきランクがすでに -6 なら失敗する。"""
    assert ctx.defender is not None
    if ctx.defender.boosts["atk"] == -6:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="こうげき最低"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ちょうおんぱ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちょうおんぱの効果: 相手をこんらん状態にする。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def ちょうのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちょうのまいの効果: 自分のとくこう・とくぼう・すばやさを 1 段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 1, "spd": 1, "spe": 1})


def ちょうはつ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ちょうはつの効果: 相手にちょうはつ状態を付与する（3 ターン）。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ちょうはつ", count=3)


def つぶらなひとみ_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """つぶらなひとみの効果: 相手のこうげきを1段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def つぼをつく_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """つぼをつく: ランクが最大でない能力からランダムに1つ選んでランクを2段階上げる。

    すでに+6まで上がっている能力は候補から除外し、全能力が最大の場合は失敗する。
    """
    stats: list[Stat] = ["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]
    candidates = [s for s in stats if ctx.attacker.boosts[s] < 6]
    if not candidates:
        return HandlerReturn(value=False)
    stat = cast(Stat, battle.random.choice(candidates))
    return HandlerReturn(value=battle.modify_stats(ctx.attacker, {stat: 2}, source=ctx.attacker))


def つめとぎ_boost_attacker_atk_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """つめとぎ: 自分のこうげき・命中率ランクをそれぞれ1段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "accuracy": 1})


def つるぎのまい_boost_attacker_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 2})


def テクスチャー2_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テクスチャー2の効果: 自分のタイプを、相手が直前に使った技を半減か無効にする
    タイプ（現在持っていないもの）にランダムに変更する。

    候補が複数ある場合はランダムに1つ選ばれる。タイプを2つ持つポケモンが使った場合でも、
    変更後のタイプは1つだけになる。変更後は、もりののろい・ハロウィンによる追加タイプ効果は
    リセットされる（ミラータイプと同仕様）。
    """
    candidates = テクスチャー2_取得_変更候補タイプ(ctx.attacker, ctx.defender)
    chosen = battle.random.choice(candidates)
    ctx.attacker.move_override_types = [chosen]
    ctx.attacker.added_types = []
    return HandlerReturn(value=value)


def テクスチャー2_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テクスチャー2の失敗条件を判定する。

    - 自分がテラスタル中の場合は失敗する。
    - 相手が場に出てからまだ技を使用していない場合は失敗する。
    - 相手の技タイプを半減か無効にできるタイプのうち、自分が現在持っていないものが
      存在しない場合は失敗する（わるあがき・ステラタイプ技等、抵抗できるタイプが
      存在しない技を含む）。
    """
    attacker = ctx.attacker
    defender = ctx.defender
    if attacker.is_terastallized:
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="テクスチャー2_テラスタル中"),
        )
        return HandlerReturn(value=False, stop_event=True)
    if defender.last_move is None:
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="テクスチャー2_相手未行動"),
        )
        return HandlerReturn(value=False, stop_event=True)
    if not テクスチャー2_取得_変更候補タイプ(attacker, defender):
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="テクスチャー2_変更先タイプなし"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


# テクスチャー2: 内部的な判定タイプがゲーム内バグにより実際の技タイプと異なる技。
# フリーズドライ・フライングプレス・サウザンアローは技の効果（水4倍弱点付与・
# ひこう複合弱点付与）を考慮せず、それぞれ固定のタイプとして扱われる。
テクスチャー2_判定タイプ上書き: dict[MoveName, Type] = {
    "フリーズドライ": "みず",
    "フライングプレス": "むし",
    "サウザンアロー": "ひこう",
}


def テクスチャー2_取得_変更候補タイプ(attacker: Pokemon, defender: Pokemon) -> list[Type]:
    """テクスチャー2で変更可能なタイプ（相手の技を半減か無効にでき、
    かつ自分が現在持っていないタイプ）の一覧を返す。

    「相手が直前に使った技」は、ねごと等のサブ技実行も含めて実際に発動した
    技を参照すべきため last_move を使う（selected_move はトップレベルの
    選択技のみ、pp_consumed_move はPP消費を伴わないと更新されないため
    いずれも不適）。
    """
    if defender.last_move is None:
        return []
    move_type = テクスチャー2_判定タイプ上書き.get(
        cast(MoveName, defender.last_move.name), defender.last_move.type
    )
    type_chart = TYPE_MODIFIER.get(move_type, {})
    current_types = set(attacker.types)
    return [
        t for t in TYPES
        if t not in ("", "ステラ")
        and type_chart.get(t, 1.0) < 1.0
        and t not in current_types
    ]


def テクスチャー_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テクスチャーの効果: 自分が覚えている技のうち一番上の技と同じタイプに
    自分のタイプを変更する（単一タイプになる）。

    タイプ変更後は、もりののろい・ハロウィンによる追加タイプ（added_types）はリセットされる。
    """
    attacker = ctx.attacker
    top_type = attacker.moves[0].data.type
    attacker.move_override_types = [top_type]
    attacker.added_types = []
    return HandlerReturn(value=value)


def テクスチャー_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テクスチャーの失敗チェック。

    - 自分がテラスタルしているときは失敗する。
    - 自分が覚えている技のうち一番上の技（moves[0]）のタイプが、自分の現在のタイプ
      （added_types含む）のいずれかと同じ場合は失敗する。第六世代以降の仕様であり、
      次の技へのフォールバックは行わない。
    """
    attacker = ctx.attacker
    if attacker.is_terastallized:
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="テクスチャー_テラスタル")
        )
        return HandlerReturn(value=False, stop_event=True)
    top_type = attacker.moves[0].data.type
    if top_type in attacker.types:
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="テクスチャー_タイプ同じ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def てっぺき_boost_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2})


def テレポート_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テレポートの効果: とらわれ状態を無視して控えのポケモンと交代する。

    バトンタッチと異なり、能力ランクや揮発性状態の引き継ぎは行わない。
    """
    player = battle.get_player(ctx.attacker)
    battle.player_states[player].interrupt = Interrupt.PIVOT
    return HandlerReturn(value=value)


def テレポート_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テレポートの失敗条件チェック: 控えに生きているポケモンがいない場合は失敗する。

    とらわれ状態（にげられない・バインド・フェアリーロック等）でも交代可能なため、
    トラップチェックを経由せず控えポケモンの生存のみを確認する（バトンタッチ_check と同様）。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)
    state = battle.player_states[player]
    if not any(m.alive for m in state.bench):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="テレポート_交代不可"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def てんしのキッス_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """てんしのキッスの効果: 相手をこんらん状態にする。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def デコレーション_boost_defender_atk_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """デコレーションの効果: 相手のこうげき・とくこうを2段階ずつ上げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": 2, "spa": 2})


def でんじは_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def でんじは_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんじはの失敗条件: 変化技だが例外的にタイプ相性の影響を受け、
    でんき技が無効なじめんタイプの相手には無効になる（ねらいのまと所持時は無効化解除）。"""
    if battle.damage_calculator.calc_def_type_modifier(ctx) == 0:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_IMMUNED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="タイプ無効")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def でんじふゆう_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんじふゆうの効果: 自分をでんじふゆう状態にする（5ターン）。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="でんじふゆう", count=5)


def でんじふゆう_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんじふゆうの使用条件チェック: ねをはる・うちおとす状態のポケモンは失敗する。"""
    mon = ctx.attacker
    if mon.has_volatile("ねをはる") or mon.has_volatile("うちおとす"):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="でんじふゆう_接地状態")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def とおせんぼう_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とおせんぼうの効果: 相手をにげられない状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="にげられない")


def とおぼえ_boost_attacker_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とおぼえの効果: 自分のこうげきを1段階上げる（シングルバトルでは自分のみ）。"""
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1})


def とぐろをまく_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1, "accuracy": 1})


def とける_boost_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2})


def トリックルーム_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["トリックルーム"].is_active:
        return HandlerReturn(value=manager.deactivate("トリックルーム"))
    return HandlerReturn(value=manager.activate("トリックルーム", 5))


def トーチカ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="トーチカ")


def どくガス_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def どくどく_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくどくの命中率補正。使用者がどくタイプの場合は必中になる。"""
    if "どく" in ctx.attacker.types:
        return HandlerReturn(value=None)  # 必中
    return HandlerReturn(value=value)


def どくどく_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく")


def どくのいと_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくのいとの効果: 相手のすばやさを2段階下げ、どく状態にする（Championsで1段階→2段階に変更）。

    2つの効果は互いに独立している。すばやさを下げる効果の後にどく状態にする効果が発動する。
    どちらか一方でも成功すれば技自体は成功扱いとなり、両方失敗した場合のみ技が失敗する。
    """
    assert ctx.defender is not None
    stat_changed = bool(battle.modify_stats(ctx.defender, {"spe": -2}, source=ctx.attacker))
    ailment_applied = battle.ailment_manager.apply(ctx.defender, "どく", source=ctx.attacker)
    return HandlerReturn(value=stat_changed or ailment_applied)


def どくのこな_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def どくびし_set_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どくびし: 相手陣営に「どくびし」を1層設置する（最大2層）。"""
    side = battle.get_side(ctx.defender)
    if not side.activate("どくびし", 1):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ドわすれ_boost_attacker_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spd": 2})


def ないしょばなし_lower_defender_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1})


def なかまづくり_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なかまづくりの失敗条件チェック。

    以下の場合は失敗する:
    - 対象の特性が「なまけ」である
    - 対象の特性が protected フラグを持つ（上書きできない特性）
    - 使用者の特性が uncopyable フラグを持つ（コピーできない特性）
    - 使用者と対象が同じ特性である
    - 対象の特性変更がとくせいガード等で防がれる
    """
    assert ctx.defender is not None
    attacker_ability = ctx.attacker.ability.base_name
    defender_ability = ctx.defender.ability.base_name
    if (
        defender_ability == "なまけ"
        or ctx.defender.ability.has_flag("protected")
        or ctx.attacker.ability.has_flag("uncopyable")
        or attacker_ability == defender_ability
        or battle.ability_manager.is_change_blocked(ctx.defender)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="なかまづくり")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def なかまづくり_change_defender_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なかまづくりの効果: 相手の特性を使用者と同じ特性に書き換える。"""
    assert ctx.defender is not None
    battle.change_ability(ctx.defender, ctx.attacker.ability.base_name)
    return HandlerReturn(value=value)


def なかよくする_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なかよくする: 相手のこうげきを1段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def なきごえ_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なきごえ: 相手のこうげきを1段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def なまける_heal_self(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なまける: 最大HPの1/2を回復する。"""
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def なみだめ_lower_defender_atk_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なみだめ: 相手のこうげき・とくこうをそれぞれ1段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1, "spa": -1})


def なやみのタネ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なやみのタネの失敗条件チェック。

    対象の特性が protected フラグを持つ場合、
    または「ふみん」「なまけ」の場合は失敗する。
    対象の特性変更がとくせいガード等で防がれる場合も失敗する。

    「ふみん」「なまけ」の判定には base_name（かがくへんかガス・かたやぶり等による
    無効化状態に関わらない元の特性名）を使う。特性ふみんは mold_breaker_ignorable
    フラグを持つため、かたやぶりの効果中は ability.name が空文字になり判定を
    すり抜けてしまうことを避けるため。
    """
    assert ctx.defender is not None
    ability = ctx.defender.ability
    if (
        ability.has_flag("protected")
        or ability.base_name in ("ふみん", "なまけ")
        or battle.ability_manager.is_change_blocked(ctx.defender)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="なやみのタネ")
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

    以下の場合は失敗する:
    - 対象の特性が uncopyable フラグを持つ場合（かわりもの・マルチタイプなど固有の特性）
    - 対象の特性がふしぎなまもりの場合
      （ふしぎなまもりはトレースでは有効だが、なりきりに対してのみ無効という
        例外があるため uncopyable フラグとは別に個別判定する）
    - 使用者自身の特性が protected フラグを持つ場合（上書きできない特性）
    - 使用者と対象の特性が既に同じ場合
    - 使用者自身の特性変更がとくせいガード等で防がれる場合
    """
    attacker_ability = ctx.attacker.ability
    defender_ability = ctx.defender.ability
    if (
        defender_ability.has_flag("uncopyable")
        or defender_ability.base_name == "ふしぎなまもり"
        or attacker_ability.has_flag("protected")
        or attacker_ability.base_name == defender_ability.base_name
        or battle.ability_manager.is_change_blocked(ctx.attacker)
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="なりきり")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def なりきり_change_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なりきりの効果: 自分の特性を相手の特性と同じにする。

    対象がとくせいなし状態の場合は無効化された特性名（空文字列）を、
    かがくへんかガス等それ以外の理由で抑制されている場合は元の特性名を
    コピーする（`_ability_name_to_copy` 参照）。
    """
    assert ctx.defender is not None
    battle.change_ability(ctx.attacker, _ability_name_to_copy(ctx.defender))
    return HandlerReturn(value=value)


def にほんばれ_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("はれ", 5, source=ctx.attacker))


def にらみつける_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """にらみつけるの効果: 相手のぼうぎょを1段階下げる。"""
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ねがいごと")
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
    """ねごとの発動条件チェック: ねむり状態（ゆめうつつ含む）でない場合に失敗させる。

    特性 ぜったいねむり のポケモンは「ゆめうつつ」状態を持つため、
    is_sleep で判定して対象に含める。
    """
    if not ctx.attacker.ailment.is_sleep:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ねごと_ねむり状態でない"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ねごと_select_and_execute(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねごとで選んだ技を実行する。

    non_negoto ラベルを持たない技の中からランダムに選択し、
    そのままバトルで実行する。
    選ばれた技の PP は消費しない（ねごと自体のみ消費）。
    候補技がすべて non_negoto の場合は value=False を返して失敗する。

    ねごと自身の ON_TRY_MOVE_1（ねむりチェック）・ON_STATUS_HIT（本ハンドラ）は、
    この呼び出しが完了するまでイベントマネージャーに登録されたままになる。
    選ばれた技の実行中にも同じ攻撃者に対してこれらのイベントが発火するため、
    登録されたままだと以下の問題が起きる。
    - 選ばれた技が status 技の場合、その ON_STATUS_HIT でねごと_select_and_execute
      が再度呼ばれ、実行するたびに再帰が繰り返されて無限ループになる。
    - 選ばれた技の ON_TRY_MOVE_1 でねごと_check_sleep が再度評価され、
      ねごと自身の使用条件チェックが無関係な技に対して誤って行われる。
    これを避けるため、選ばれた技の実行中はねごと自身の ON_TRY_MOVE_1 /
    ON_STATUS_HIT ハンドラのみを一時的に解除する
    （ON_MODIFY_PP_CONSUMED は選ばれた技のPP消費を抑制するために実行中も
    登録したままにする必要があるため対象外）。
    """
    attacker = ctx.attacker
    candidates = [m for m in attacker.moves if not m.has_flag("non_negoto")]
    if not candidates:
        battle.add_event_log(
            attacker,
            LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ねごと_候補技なし"),
        )
        return HandlerReturn(value=False, stop_event=True)
    chosen = battle.random.choice(candidates)
    # ねごとのON_MODIFY_PP_CONSUMEDハンドラがPP消費を0にするため、
    # ねむり状態でも選ばれた技が実行できるよう、サブ実行フラグを立てる
    attacker.sleep_talk_active = True
    suppressed_events = (Event.ON_TRY_MOVE_1, Event.ON_STATUS_HIT)
    handlers_data = ctx.move.data.handlers
    for event in suppressed_events:
        handler = handlers_data.get(event)
        if handler is None:
            continue
        for h in (handler if isinstance(handler, list) else [handler]):
            battle.events.off(event, h, ctx.attacker)
    try:
        battle.run_move(attacker, chosen)
    finally:
        for event in suppressed_events:
            handler = handlers_data.get(event)
            if handler is None:
                continue
            for h in (handler if isinstance(handler, list) else [handler]):
                battle.events.on(event, h, ctx.attacker)
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
    """ねむるの効果: 3ターンのねむり付与に成功した場合のみHPと状態異常を全回復する。

    さわぐ・特性（やるき・ふみん・スイートベール・きよめのしお・リミットシールド等）・
    にほんばれ下のリーフガードなど、ON_BEFORE_APPLY_AILMENT で寝られないと判定される
    ケースでは、状態異常の上書き付与自体が失敗する。その場合は技全体を失敗させ、
    HPも回復しない（「ステータス無効化」時にHPだけ回復してしまう不具合を避けるため、
    ねむり付与を先に試行してから回復するという順序にしている）。

    Notes:
        Champions仕様: ねむるのカウントは3固定（Wiki「ねむるによってねむり状態になったときは
        カウントは3で固定」）。説明文「技ねむるでは3度目まで回復しない」と一致。
    """
    mon = ctx.attacker
    # ねむり付与を先に試行（count=3固定、既存の状態異常は上書き）
    if not battle.ailment_manager.apply(mon, "ねむり", count=3, source=mon, overwrite=True):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ねむる"),
        )
        return HandlerReturn(value=False, stop_event=True)
    # ねむり付与に成功した場合のみHP全回復
    battle.modify_hp(mon, v=mon.max_hp - mon.hp)
    return HandlerReturn(value=value)


def ねむる_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねむるの失敗条件チェック。

    以下のいずれかに該当する場合は失敗する:
    - HP が最大HP（すでに満タン）
    - すでにねむり状態
    - エレキフィールド下で接地している
    - ミストフィールド下で接地している
    - さわぐ・さわがしい状態（場にさわぐ状態のポケモンがいる）

    特性（やるき・ふみん・スイートベール・きよめのしお・リミットシールド等）や
    にほんばれ下のリーフガードによる無効化は、ここでは判定せず ねむる_apply 内の
    ailment_manager.apply（ON_BEFORE_APPLY_AILMENT）に委ねる
    （かたやぶり等の無効化判定を含む正規の特性判定経路を再利用するため）。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp or mon.has_ailment("ねむり"):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ねむる"),
        )
        return HandlerReturn(value=False, stop_event=True)
    # エレキフィールド下で接地しているポケモンのねむるは失敗する
    if (
        battle.terrain.name == "エレキフィールド"
        and not battle.query.is_floating(mon)
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="エレキフィールド"),
        )
        return HandlerReturn(value=False, stop_event=True)
    # ミストフィールド下で接地しているポケモンのねむるは失敗する
    if (
        battle.terrain.name == "ミストフィールド"
        and not battle.query.is_floating(mon)
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ミストフィールド"),
        )
        return HandlerReturn(value=False, stop_event=True)
    # 場にさわぐ状態のポケモンがいるときのねむるは失敗する
    if mon.has_volatile("さわぐ") or mon.has_volatile("さわがしい"):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="さわぐ"),
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="のみこむ")
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
        # reason="self_cost": マジックガードでも防げない自己HP消費として扱う
        cost = mon.max_hp // 2
        battle.modify_hp(mon, v=-cost, reason="self_cost", source=mon)
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="のろい_すでに状態変化"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はいすいのじん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はいすいのじんの効果: すべての能力を1段階ずつ上げる。

    すべての能力ランクがすでに+6で1つも上げられない場合は失敗する（他の複合ランク
    変化技と同様、battle.modify_stats() の戻り値が空辞書になることで自動的に失敗
    扱いになる）。
    すでに他の要因でにげられない状態の場合は、にげられない付与をスキップする。
    """
    mon = ctx.attacker
    # すべての能力（こうげき・ぼうぎょ・とくこう・とくぼう・すばやさ）を1段階ずつ上げる
    result = battle.modify_stats(mon, {"atk": 1, "def": 1, "spa": 1, "spd": 1, "spe": 1}, source=mon)
    if not result:
        return HandlerReturn(value=False)
    # にげられない状態でない場合のみ付与（はいすいのじん起因をmove_nameで記録）
    if not mon.has_volatile("にげられない"):
        battle.volatile_manager.apply(mon, "にげられない", source=mon, move_name="はいすいのじん")
    return HandlerReturn(value=value)


def はいすいのじん_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はいすいのじんの失敗条件チェック（ON_TRY_MOVE_1 priority=30）。

    すでにはいすいのじんによってにげられない状態になっている場合は失敗する。
    """
    mon = ctx.attacker
    # はいすいのじん起因でにげられない状態の場合は失敗
    if (mon.has_volatile("にげられない")
            and mon.volatiles["にげられない"].move_name == "はいすいのじん"):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="はいすいのじん_すでに状態変化"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はねやすめ_heal_and_remove_flying(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はねやすめの効果: 最大HPの1/2を回復し、ひこうタイプを一時的に除去する。

    HPが満タンの場合は失敗する。
    テラスタル中はタイプ除去を行わない。
    ひこうタイプを持たないポケモンはタイプ除去を行わない。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    # テラスタル中はタイプ変化しない
    if mon.active_tera_type:
        return HandlerReturn(value=value)
    # ひこうタイプを持つ場合のみ除去 volatile を付与
    if mon.has_type("ひこう"):
        battle.volatile_manager.apply(mon, "はねやすめ")
    return HandlerReturn(value=value)


def ハバネロエキス_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハバネロエキスの効果: 相手のこうげきを2段階上げ、ぼうぎょを2段階下げる。

    2つのランク変化を1回のmodify_stats呼び出しにまとめることで、こうげき・ぼうぎょの
    どちらも変化できない場合（こうげき+6かつぼうぎょ-6）に戻り値が空dict（偽値）になり、
    技全体が失敗として扱われる。片方のみ変化可能な場合はそちらのみ適用され技は成功する。
    """
    return modify_defender_stats(battle, ctx, value, stats={"atk": 2, "def": -2})


def はらだいこ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はらだいこの効果: こうげきランクを最大まで上げ、HPを最大HPの半分消費する。

    reason="self_cost": マジックガードでも防げない自己HP消費として扱う（ききかいひ不発）。
    """
    mon = ctx.attacker
    delta = 6 - mon.boosts["atk"]
    battle.modify_stats(mon, {"atk": delta}, source=mon)
    battle.modify_hp(mon, r=-0.5, reason="self_cost", source=mon)
    return HandlerReturn(value=value)


def はらだいこ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はらだいこの使用条件チェック: こうげきランクがすでに+6、またはHPが最大HPの半分以下ならば失敗する。"""
    mon = ctx.attacker
    if mon.boosts["atk"] >= 6 or mon.hp <= mon.max_hp // 2:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="はらだいこ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ハロウィン_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハロウィンの効果: 相手にハロウィン状態を付与してゴーストタイプを追加する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="ハロウィン")


def ハロウィン_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハロウィンの使用条件チェック: 相手がすでにゴーストタイプ、またはテラスタル中の場合は失敗する。"""
    defender = ctx.defender
    if defender.has_type("ゴースト") or defender.is_terastallized:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ハロウィン")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ハートスワップ_swap_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハートスワップ: 使用者と相手のすべての能力ランク変化を入れ替える。

    こうげき・ぼうぎょ・とくこう・とくぼう・すばやさ・めいちゅう・かいひの
    ランク変化を互いに交換する。実数値は変化しない。
    """
    attacker, defender = ctx.attacker, ctx.defender
    attacker_changed = {
        stat: defender.boosts[stat] - attacker.boosts[stat]
        for stat in attacker.boosts
        if defender.boosts[stat] != attacker.boosts[stat]
    }
    defender_changed = {
        stat: attacker.boosts[stat] - defender.boosts[stat]
        for stat in defender.boosts
        if attacker.boosts[stat] != defender.boosts[stat]
    }
    attacker.boosts, defender.boosts = defender.boosts, attacker.boosts
    if attacker_changed:
        battle.add_event_log(
            attacker, LogCode.STAT_CHANGED,
            payload=StatChangePayload(stats=attacker_changed, display_reason="ハートスワップ"),
        )
    if defender_changed:
        battle.add_event_log(
            defender, LogCode.STAT_CHANGED,
            payload=StatChangePayload(stats=defender_changed, display_reason="ハートスワップ"),
        )
    return HandlerReturn(value=value)


def バトンタッチ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """バトンタッチの効果: ランク・揮発性状態を保存し、ピボット交代する。

    能力ランク変化（プラス・マイナス両方）と一部の揮発性状態を交代先に引き継ぐ。
    クリアボディ等のハンドラを経由させないため、ランクは直接代入で引き継ぐ。
    """
    mon = ctx.attacker
    player = battle.get_player(mon)

    # 退場時にランクがリセットされるため、事前にコピーを作成
    rank_copy = dict(mon.boosts)

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
        "boosts": rank_copy,
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="バトンタッチ_交代不可"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def パワーシェア_equalize_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワーシェア: 使用者と相手のこうげき・とくこうの実数値を平均化する。

    ランク変化は行わず、実数値のみを書き換える。
    平均は切り捨て（// 2）。
    """
    atk, df = ctx.attacker, ctx.defender
    # A=インデックス1、C=インデックス3
    for idx in (1, 3):
        avg = (atk.get_raw_stat(idx) + df.get_raw_stat(idx)) // 2
        atk.set_raw_stat(idx, avg)
        df.set_raw_stat(idx, avg)
    return HandlerReturn(value=value)


def パワースワップ_swap_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワースワップ: 使用者と相手のこうげき・とくこうのランク変化を入れ替える。

    実数値は変化せず、ランク変化のみを互いに入れ替える。
    """
    atk_rank = ctx.attacker.boosts
    def_rank = ctx.defender.boosts
    for stat in ("atk", "spa"):
        atk_rank[stat], def_rank[stat] = def_rank[stat], atk_rank[stat]
    return HandlerReturn(value=value)


def パワートリック_swap_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワートリック: 使用者のこうげきとぼうぎょの実数値を入れ替える。

    ランク変化は行わず、実数値のみを入れ替える。
    インデックス 1 = こうげき、インデックス 2 = ぼうぎょ
    （[HP, 攻撃, 防御, 特攻, 特防, 素早さ]）。
    """
    atk = ctx.attacker
    atk_stat, def_stat = atk.get_raw_stat(1), atk.get_raw_stat(2)
    atk.set_raw_stat(1, def_stat)
    atk.set_raw_stat(2, atk_stat)
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
    if all(v == 0 for v in mon.boosts.values()):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="能力ランクに変化がない"),
        )
        return HandlerReturn(value=False, stop_event=True)
    changed = {stat: -2 * v for stat, v in mon.boosts.items() if v != 0}
    for stat in mon.boosts:
        mon.boosts[stat] = -mon.boosts[stat]
    battle.add_event_log(
        mon, LogCode.STAT_CHANGED,
        payload=StatChangePayload(stats=changed, display_reason="ひっくりかえす"),
    )
    return HandlerReturn(value=value)


def ビルドアップ_boost_attacker_atk_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1})


def ファストガード_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ファストガード")


def ふういん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ふういん")


def フェアリーロック_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フェアリーロック: グローバルフィールドを「フェアリーロック」状態にする（次のターン終了まで）。

    ON_TURN_END のカウントダウンは非Turn0発動時、発動ターン自身の終了フェーズでも
    即座にティックされる仕様のため、count=1では発動した同一ターンでカウントが1→0になり
    即座に終了してしまう。「使用した次のターンが終了するまで」を満たすには、
    発動ターン分＋次のターン分の count=2 が必要。
    """
    return HandlerReturn(value=battle.global_manager.activate("フェアリーロック", 2))


def フェザーダンス_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -2})


def ふしょくガス_remove_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふしょくガスのアイテム除去効果。

    場に存在したまま消滅する扱いのため、技リサイクルや特性ものひろい・しゅうかくの
    復元/拾得対象にしない（track_loss=False）。
    """
    battle.item_manager.remove_item(target=ctx.defender, source=ctx.attacker, track_loss=False)
    return HandlerReturn(value=value)


def フラフラダンス_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フラフラダンスの効果: 相手をこんらん状態にする。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def フラワーヒール_heal_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フラワーヒール: 相手のHPを回復させる。HPが満タンの場合は失敗する。

    通常時は最大HPの1/2（端数切り上げ）、グラスフィールド中は最大HPの2732/4096（≒2/3、
    端数は五捨五超入）を回復する。
    """
    mon = ctx.defender
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    if battle.terrain.name == "グラスフィールド":
        heal = round_half_down(mon.max_hp * 2732 / 4096)
    else:
        heal = (mon.max_hp + 1) // 2
    battle.modify_hp(mon, v=heal)
    return HandlerReturn(value=value)


def ふるいたてる_boost_attacker_atk_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふるいたてるの効果: 自分のこうげき・とくこうを1段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "spa": 1})


def ブレイブチャージ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ブレイブチャージ: 自分のとくこう・とくぼうを1段階ずつ上げ、状態異常を回復する。

    ランク上限・状態異常なしのいずれの場合でも技自体は失敗しない。
    """
    modify_attacker_stats(battle, ctx, value, stats={"spa": 1, "spd": 1})
    battle.ailment_manager.remove(ctx.attacker)
    return HandlerReturn(value=value)


def へびにらみ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def へんしん_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """へんしんの効果: 相手の見た目・タイプ・特性・技・実数値ステータス・能力ランク補正・
    性別・体重をコピーする（実体は共有APIのbattle.transform、かわりものと共通）。"""
    battle.transform(ctx.attacker, ctx.defender)
    return HandlerReturn(value=value)


def へんしん_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """へんしんの失敗条件を判定する。

    - 自身が既にへんしん状態の場合は失敗する。
    - 対象がみがわり状態の場合は失敗する。
    - 対象がへんしん状態の場合は失敗する。
    - 自身または対象がテラスタルしているとき、オーガポン/テラパゴスに対しては失敗する
      （お互いテラスタルしていなければオーガポンに対しても成功する）。
    - 自身がステラタイプにテラスタルしているときは失敗する。

    特性イリュージョン（本プロジェクトでは非実装特性）・スターモービル（本プロジェクトの
    ポケモンデータに未収録の専用フォルム）による失敗条件は、いずれも発生し得ないため対象外。
    """
    attacker, defender = ctx.attacker, ctx.defender
    is_special_form = defender.name.startswith(("オーガポン", "テラパゴス"))
    if (
        attacker.has_volatile("へんしん")
        or defender.has_volatile("みがわり")
        or defender.has_volatile("へんしん")
        or ((attacker.is_terastallized or defender.is_terastallized) and is_special_form)
        or attacker.active_tera_type == "ステラ"
    ):
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="へんしん")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ほおばる_check_defense_max(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほおばるの失敗条件: ぼうぎょランクがすでに上限の場合に失敗させる。

    通常はぼうぎょランク+6のときに失敗する。あまのじゃく持ちのポケモンは
    ぼうぎょの上昇効果が下降に反転するため、ぼうぎょランク-6のときに失敗する
    （.internal/spec/abilities/あまのじゃく.md）。
    このチェックは battle.modify_stats の内部（ON_TRY_MOVE_2 の後）で
    行われるわけではないため、ここで明示的にガードする。
    """
    mon = ctx.attacker
    if mon.ability.name == "あまのじゃく":
        maxed = mon.boosts["def"] <= -6
    else:
        maxed = mon.boosts["def"] >= 6
    if maxed:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ほおばる_ぼうぎょ最大")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ほおばる_check_has_berry(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほおばるの失敗条件: きのみを持っていない場合に失敗させる。"""
    mon = ctx.attacker
    if not mon.item.is_berry():
        battle.add_event_log(mon, LogCode.MOVE_FAILED,
                             payload=FailureLogPayload(move=ctx.move.name, display_reason="ほおばる_きのみなし"))
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


def ほたるび_boost_attacker_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほたるびの効果: 自分の『とくこう』ランクを3段階上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 3})


def ほろびのうた_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほろびのうたの効果: 場の全ポケモンにほろびのうた状態を付与する（count=3）。

    使用者自身も対象になる。音技のためみがわりを貫通する。
    すでにほろびのうた状態のポケモンには付与されない（volatile_manager.apply が False を返す）。
    使用者以外の対象は、おうごんのからだ・ぼうおん特性を持つ場合そのポケモンへの
    付与のみ防がれる（技全体は無効化されない）。
    """
    triggered = False
    for mon in battle.actives:
        if mon is not ctx.attacker and (
            _blocked_by_ougon_no_karada(battle, mon)
            or _blocked_by_bouon(battle, mon)
        ):
            continue
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ほろびのうた_すでに状態"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ぼうぎょしれい_boost_attacker_def_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ぼうぎょしれいの効果: 自分のぼうぎょ・とくぼうを1段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1, "spd": 1})


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


def まねっこ_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まねっこの失敗条件。

    - バトル中にまだ技が使われていない場合は失敗する。
    - 最後に使われた技が non_copycat フラグを持つ技（スターモービル専用アクセル技等）の場合は失敗する。
    - 最後に使われた技が protect フラグを持つ技（まもる・みきり・こらえる・キングシールド等の
      守る系技）の場合は失敗する。守る系技はコピー対象から一律除外されるため個別に
      non_copycat フラグを付与せず、protect フラグを流用する。
    """
    from jpoke.model import Move
    if not battle.last_used_move_name:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="まねっこ_使用技なし")
        )
        return HandlerReturn(value=False, stop_event=True)
    copied_move = Move(battle.last_used_move_name)
    if copied_move.has_flag("non_copycat") or copied_move.has_flag("protect"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="まねっこ_コピー不可技")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def まねっこ_execute(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まねっこの効果: バトルで最後に使われた技をそのまま使用する。
    コピーした技の PP は消費しない（まねっこ自体のみ消費）。

    まねっこ自身の ON_BEFORE_APPLY_MOVE（まねっこ_can_use）・ON_STATUS_HIT
    （本ハンドラ）は、この呼び出しが完了するまでイベントマネージャーに登録された
    ままになる。コピーした技の実行中にも同じ攻撃者に対してこれらのイベントが
    発火するため、登録されたままだと以下の問題が起きる。
    - コピーした技が status 技の場合、その ON_STATUS_HIT でまねっこ_execute
      が再度呼ばれ、実行するたびに再帰が繰り返されて無限ループになる。
    - コピーした技の ON_BEFORE_APPLY_MOVE でまねっこ_can_use が再度評価され、
      まねっこ自身の使用条件チェックが無関係な技に対して誤って行われる。
    これを避けるため、コピーした技の実行中はまねっこ自身の ON_BEFORE_APPLY_MOVE /
    ON_STATUS_HIT ハンドラのみを一時的に解除する
    （ON_MODIFY_PP_CONSUMED はコピーした技のPP消費を抑制するために実行中も
    登録したままにする必要があるため対象外）。
    """
    from jpoke.model import Move
    copied_move = Move(battle.last_used_move_name)
    # まねっこのON_MODIFY_PP_CONSUMEDハンドラがPP消費を0にするため、
    # サブ実行フラグを立てる
    ctx.attacker.copycat_active = True
    suppressed_events = (Event.ON_BEFORE_APPLY_MOVE, Event.ON_STATUS_HIT)
    handlers_data = ctx.move.data.handlers
    for event in suppressed_events:
        handler = handlers_data.get(event)
        if handler is None:
            continue
        for h in (handler if isinstance(handler, list) else [handler]):
            battle.events.off(event, h, ctx.attacker)
    try:
        battle.run_move(ctx.attacker, copied_move)
    finally:
        for event in suppressed_events:
            handler = handlers_data.get(event)
            if handler is None:
                continue
            for h in (handler if isinstance(handler, list) else [handler]):
                battle.events.on(event, h, ctx.attacker)
        ctx.attacker.copycat_active = False
    return HandlerReturn(value=value)


def まねっこ_suppress_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まねっこのサブ実行中はコピーした技のPP消費を0にする。"""
    if ctx.attacker.copycat_active:
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def まほうのこな_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まほうのこなの効果: 相手にまほうのこな状態を付与してエスパー単タイプに変える。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="まほうのこな")


def まほうのこな_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まほうのこなの使用条件チェック: 相手がすでにエスパー単タイプ、テラスタル中、
    またはアルセウス・シルヴァディの場合は失敗する。"""
    defender = ctx.defender
    if (
        defender.types == ["エスパー"]
        or defender.is_terastallized
        or defender.name in ("アルセウス", "シルヴァディ")
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="まほうのこな")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def まもる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="まもる")


def まもる系_連続使用失敗チェック(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """守る系技の連続使用失敗チェック。

    直前の行動が守る系の技（protect フラグを持つ技）で、かつ成功していた場合、
    今ターンの守る系技を失敗させる。failed_or_immobile_last_turn を併せて見る
    ことで、直前行動が（この連続使用チェック自身の失敗も含めて）何らかの理由で
    失敗していれば連鎖が途切れたとみなし、次ターンは再度成功しうる。
    last_move は行動の成否に関わらず run_move の finally より前に確定するが、
    このチェック自体が早期returnした場合はそのまもる系技には更新されない
    （_execute_move 内で last_move への代入より前に判定されるため）ので、
    last_move 単独では連続使用と1回休みを区別できない。
    """
    mon = ctx.attacker
    if (
        mon.last_move is not None
        and mon.last_move.has_flag("protect")
        and not mon.failed_or_immobile_last_turn
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="まもる系_連続使用")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def まるくなる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まるくなるの効果を発動する。"""
    mon = ctx.attacker
    battle.modify_stats(mon, {"def": 1}, source=mon)
    battle.volatile_manager.apply(mon, "まるくなる")
    return HandlerReturn(value=value)


def みかづきのいのり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みかづきのいのり: 自分のHPを最大HPの1/4回復し、状態異常を治す。

    HPが満タンかつ状態異常もない場合は失敗する（ジャングルヒールと同様の判定。
    .internal/spec/turn.md Event.ON_APPLY_MOVE「ジャングルヒール: HP満タン・状態異常無」参照）。
    端数は切り捨て。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp and not mon.ailment.is_active:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1 / 4)
    battle.ailment_manager.remove(mon)
    return HandlerReturn(value=value)


def みかづきのまい_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みかづきのまい: 使用者をひんしにし、自陣営に「みかづきのまい」フィールドを設置する。

    次に場に出たポケモンの HP が全回復し、状態異常が回復し、全ての技の PP も全回復する。
    """
    mon = ctx.attacker
    side = battle.get_side(mon)
    side.activate("みかづきのまい", 1)
    battle.faint(mon)
    return HandlerReturn(value=value)


def みかづきのまい_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みかづきのまいの失敗チェック: 控えのポケモンがいない場合は失敗し、使用者はひんしにならない。"""
    player = battle.get_player(ctx.attacker)
    if not battle.query.has_available_bench(player):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="みかづきのまい")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def みがわり_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みがわりの効果を発動する。

    最大HPの1/4（切り捨て）を消費し、消費量と同じHPのみがわりを生成する。
    技の成功に伴い、自分のバインド状態を解除する（第三世代以降の仕様）。
    reason="self_cost": マジックガードでも防げない自己HP消費として扱う（ききかいひ不発）。
    """
    mon = ctx.attacker
    migawari_hp = mon.max_hp // 4
    battle.modify_hp(mon, -migawari_hp, reason="self_cost", source=mon)
    battle.volatile_manager.apply(mon, "みがわり", hp=migawari_hp)
    battle.volatile_manager.remove(mon, "バインド")
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="みがわり")
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
    """みずびたしの使用条件チェック: 相手がすでにみずタイプのみ、テラスタル中、
    またはアルセウス・シルヴァディの場合は失敗する。"""
    defender = ctx.defender
    if (
        defender.types == ["みず"]
        or defender.is_terastallized
        or defender.name in ("アルセウス", "シルヴァディ")
    ):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="みずびたし")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def みちづれ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="みちづれ")


def みちづれ_連続使用失敗チェック(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みちづれの連続使用失敗チェック（第七世代以降）。

    直前の自分の行動で成功裏にみちづれを使用していた場合、今回のみちづれは失敗する
    （まもる系_連続使用失敗チェックと同じパターン。failed_or_immobile_last_turn を
    併せて見る理由もそちらのdocstring参照）。
    """
    mon = ctx.attacker
    if (
        mon.last_move is not None
        and mon.last_move.name == "みちづれ"
        and not mon.failed_or_immobile_last_turn
    ):
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="みちづれ_連続使用")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ミラータイプ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミラータイプの効果: 使用者のタイプを対象の現在のタイプに置換する。

    - `defender.types`（テラスタル・特性等によるタイプ変更・追加/除去タイプを反映した
      現在のタイプ）をそのままコピーする
    - 対象のタイプが完全に無い場合（例: ひこう単タイプがはねやすめでタイプを消している場合）は
      ノーマルタイプとして扱う
    - タイプ置換後、もりののろい/ハロウィンによる自分の added_types はリセットされる
    """
    attacker = ctx.attacker
    defender = ctx.defender
    attacker.move_override_types = ミラータイプ_取得_対象タイプ(defender)
    # added_types（もりののろい・ハロウィン等の追加タイプ）をリセットする
    attacker.added_types = []
    return HandlerReturn(value=value)


def ミラータイプ_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミラータイプの失敗チェック。

    - 使用者がテラスタル中の場合は失敗する
    - 使用者と対象のタイプが一致する場合は失敗する
    """
    attacker = ctx.attacker
    defender = ctx.defender
    if attacker.is_terastallized:
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ミラータイプ_テラスタル中"),
        )
        return HandlerReturn(value=False, stop_event=True)
    target_types = ミラータイプ_取得_対象タイプ(defender)
    if sorted(attacker.types) == sorted(target_types):
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ミラータイプ_タイプ同じ"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ミラータイプ_取得_対象タイプ(defender: Pokemon) -> list[Type]:
    """ミラータイプでコピーする対象の現在のタイプを返す。

    `defender.types` はテラスタル・特性によるタイプ変更・もりののろい/ハロウィンによる
    追加タイプ・はねやすめ等による除去タイプをすべて反映済みのため、そのまま使用する。
    対象のタイプが完全に無くなっている場合はノーマルタイプとして扱う。
    """
    return list(defender.types) or ["ノーマル"]


def ミルクのみ_self_heal(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミルクのみ: 自分のHPを最大HPの1/2回復する（じこさいせい・タマゴうみと同一効果）。
    HPが満タンの場合は失敗する。
    """
    mon = ctx.attacker
    if mon.hp == mon.max_hp:
        return HandlerReturn(value=False, stop_event=True)
    battle.modify_hp(mon, r=1/2)
    return HandlerReturn(value=value)


def みをけずる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みをけずるの効果: こうげき・とくこう・すばやさを2段階ずつ上げる。
    いずれかのランクが実際に変化した場合のみ、最大HPの半分（切り捨て）を消費する。
    3ランクすべてが上限で変化しなかった場合はHPを消費せず、技自体も失敗扱いになる。"""
    result = modify_attacker_stats(battle, ctx, value, stats={"atk": 2, "spa": 2, "spe": 2})
    if result.value:
        battle.modify_hp(ctx.attacker, r=-0.5)
    return result


def みをけずる_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みをけずるの使用条件チェック: HPが最大HPの半分以下ならば失敗する。"""
    mon = ctx.attacker
    if mon.hp <= mon.max_hp // 2:
        battle.add_event_log(
            mon, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="みをけずる")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def めいそう_boost_attacker_spa_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="メロメロ_性別不一致")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def もりののろい_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もりののろいの効果: 相手にもりののろい状態を付与してくさタイプを追加する。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="もりののろい")


def もりののろい_can_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もりののろいの使用条件チェック: 相手がすでにくさタイプ、またはテラスタル中の場合は失敗する。"""
    defender = ctx.defender
    if defender.has_type("くさ") or defender.is_terastallized:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="もりののろい")
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="やどりぎのタネ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ゆきげしき_activate_weather(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.weather_manager.apply("ゆき", 5, source=ctx.attacker))


# ゆびをふるで選ばれない技の名前セット（.internal/spec/moves/ゆびをふる.md「選ばれる技の範囲」参照）。
# 実機Wikiの代表的な分類のみを反映した非網羅的な一覧であり、第五世代以降の伝説・幻ポケモンの
# 専用技の一部・第八世代以降の一般ポケモン専用技の一部（原作仕様が「一部、全てではない」と
# 明記する区分）は対象外とする（詳細は.internal/plan/moves/ゆびをふる.md）。
# まもる系統の技は個別に列挙せず、protectフラグ（MoveData.flags）で動的に判定する。
_METRONOME_EXCLUDED_MOVES: frozenset[str] = frozenset({
    # ゆびをふる自身
    "ゆびをふる",
    # 他の技が出る技
    "オウムがえし", "さきどり", "しぜんのちから", "ねごと", "ねこのて", "まねっこ",
    "へんしん", "ものまね", "スケッチ",
    # 行動順・反撃に関する技
    "きあいパンチ", "カウンター", "ミラーコート", "みちづれ", "このゆびとまれ",
    "でんこうそうげき", "フェイント",
    # だいばくはつ・こらえる等、わるあがき
    "だいばくはつ", "じばく", "こらえる", "わるあがき",
})


def ゆびをふる_select_and_execute(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆびをふるで選んだ技を実行する。

    「一部を除いたほぼ全ての技」の中からランダムに1つを選び、その場で実行する
    （.internal/spec/moves/ゆびをふる.md「選ばれる技の範囲」。除外の scope は
    _METRONOME_EXCLUDED_MOVES のコメント参照）。選ばれた技のPPは消費しない
    （ゆびをふる自体のみ消費）。

    選ばれた技の優先度に関係なくゆびをふる自体の優先度で繰り出される点・じゅうりょく状態や
    かいふくふうじ等による選ばれた技自体の失敗は、battle.run_moveの通常の技実行フローに
    そのまま乗せることで自然に処理される（ゆびをふるは既にターン制御の行動順解決で自身の
    優先度に基づき実行されており、本関数はその場で選んだ技を同期的に実行するだけのため）。

    ゆびをふる自身のON_STATUS_HIT（本ハンドラ）は、この呼び出しが完了するまで
    イベントマネージャーに登録されたままになる。選ばれた技がstatus技の場合、その
    ON_STATUS_HITで本ハンドラが再度呼ばれ無限ループになるのを避けるため、
    ねごと_select_and_executeと同じパターンで実行中だけ一時的に解除する
    （ON_MODIFY_PP_CONSUMEDは選ばれた技のPP消費を抑制するために実行中も
    登録したままにする必要があるため対象外）。
    """
    from jpoke.model import Move
    from jpoke.data.move import MOVES

    attacker = ctx.attacker
    candidates = [
        name for name, data in MOVES.items()
        if name not in _METRONOME_EXCLUDED_MOVES and "protect" not in data.flags
    ]
    chosen = Move(battle.random.choice(candidates))

    attacker.metronome_active = True
    suppressed_events = (Event.ON_STATUS_HIT,)
    handlers_data = ctx.move.data.handlers
    for event in suppressed_events:
        handler = handlers_data.get(event)
        if handler is None:
            continue
        for hd in (handler if isinstance(handler, list) else [handler]):
            battle.events.off(event, hd, attacker)
    try:
        battle.run_move(attacker, chosen)
    finally:
        for event in suppressed_events:
            handler = handlers_data.get(event)
            if handler is None:
                continue
            for hd in (handler if isinstance(handler, list) else [handler]):
                battle.events.on(event, hd, attacker)
        attacker.metronome_active = False
    return HandlerReturn(value=value)


def ゆびをふる_suppress_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆびをふるのサブ実行中は選ばれた技のPP消費を0にする。"""
    if ctx.attacker.metronome_active:
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def ゆめくい_check_sleep(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆめくいの使用条件チェック: 相手がねむり状態（ゆめうつつ含む）でない場合に失敗させる。

    特性 ぜったいねむり のポケモンは「ゆめうつつ」状態を持つため、
    is_sleep で判定して対象に含める。
    """
    if not ctx.defender.ailment.is_sleep:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ゆめくい_ねむり状態でない"),
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
            payload=FailureLogPayload(move=ctx.move.name, display_reason="リサイクル"),
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


def りゅうのまい_boost_attacker_atk_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """りゅうのまいの効果: 自分のこうげき・すばやさを1段階ずつ上げる。"""
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "spe": 1})


def ロックオン_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ロックオンの効果: 自分をロックオン状態にし、次のターンの自分の技を相手に必中させる。"""
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ロックオン", count=2)


def ロックカット_boost_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 2})


def ワイドガード_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ワイドガードの効果: 自分を「ワイドガード」状態にする（まもる_applyと同じ骨格）。

    実際の保護判定（"spread"フラグを持つ技のブロック）は、まもる系と同様に
    ワイドガード状態自体が持つON_TRY_MOVE_1ハンドラ（handlers/volatile.pyの
    ワイドガード_protect）で行う。
    """
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ワイドガード")


def わたほうし_lower_defender_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """わたほうしの効果: 相手のすばやさを2段階下げる。粉技のためくさタイプ・ぼうじん無効。"""
    return modify_defender_stats(battle, ctx, value, stats={"spe": -2})


def わるだくみ_boost_attacker_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 2})


def ワンダールーム_activate_global_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    manager = battle.global_manager
    if manager.fields["ワンダールーム"].is_active:
        return HandlerReturn(value=manager.deactivate("ワンダールーム"))
    return HandlerReturn(value=manager.activate("ワンダールーム", 5))
