"""攻撃技関連のイベントハンドラ関数を提供するモジュール。

物理・特殊攻撃技の実行に関連するハンドラ関数を提供します。

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

def pivot(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """交代技の効果を発動する。

    とんぼがえり、ボルトチェンジなどの交代技で、攻撃後に交代を行います。

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: イベント値（未使用）

    Returns:
        HandlerReturn: 交代が可能な場合はTrue、不可能な場合はFalse
    """
    player = battle.get_player(ctx.attacker)
    if battle.get_available_switch_commands(player):
        battle.player_states[player].interrupt = Interrupt.PIVOT
    return HandlerReturn(value=value)

def ohko_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """一撃必殺技の確定ダメージを計算する。"""
    return HandlerReturn(value=ctx.defender.hp)

def hp_ratio_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """対象の現在HPの半分を与える固定ダメージを計算する。"""
    return HandlerReturn(value=max(1, ctx.defender.hp // 2))


def アイアンテール_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.3)


def _3ぼんのや_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def アイアンヘッド_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def アイスハンマー_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": -1})


def アクアステップ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 1})


def アクアブレイク_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.2)


def あくのはどう_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def アシッドボム_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def あばれる_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """あばれる系技の初回命中時に揮発性状態を付与する。

    あばれる・げきりん・はなびらのまい・だいふんげきで共用。
    すでにあばれる状態の場合（強制行動の2ターン目以降）は何もしない。

    ターン数は 2〜3 ターンのランダム（最初の使用時に決定）。
    """
    attacker = ctx.attacker
    if attacker.has_volatile("あばれる"):
        return HandlerReturn(value=value)
    count = battle.random.randint(2, 3)
    battle.volatile_manager.apply(
        attacker, "あばれる", count=count, source=attacker,
        move_name=ctx.move.name
    )
    return HandlerReturn(value=value)


def あやしいかぜ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "B": 1, "C": 1, "D": 1, "S": 1}, chance=0.1)


def _check_はやてがえし_condition(battle: Battle, ctx: AttackContext) -> bool:
    """はやてがえしの発動条件を判定する。

    相手が未行動かつ優先攻撃技を選択している時のみ成功する。
    """
    def_player = battle.get_player(ctx.defender)
    def_state = battle.player_states[def_player]

    # 相手が既に行動済み（予約コマンドが消費済み）なら失敗。
    if def_state.next_command is None:
        return False

    defender_command = def_state.next_command
    defender_move = battle.command_to_move(def_player, defender_command)

    # 優先度が上がっていても変化技には失敗する。
    if not defender_move.is_attack:
        return False

    priority = battle.speed_calculator.calc_move_priority(ctx.defender, defender_move)

    # 先制技でないまたはより優先度が高い技には失敗する。
    if priority <= 0 or priority > ctx.move.priority:
        return False

    return True

def Gのちから_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def あわ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1}, chance=0.1)


def アーマーキャノン_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1})


def アームハンマー_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": -1})


def いじげんラッシュ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1})


def いてつくしせん_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def いてつくしせん_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1}, chance=0.1)


def いのちがけ_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちがけの固定ダメージを計算する（支払い前のHPを使用）。"""
    return HandlerReturn(value=getattr(ctx, "hp_cost", 0))


def いのちがけ_pay_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちがけ発動前にHPを支払い、元のHPをコンテキストに保存する。"""
    ctx.hp_cost = ctx.attacker.hp
    battle.modify_hp(ctx.attacker, v=-ctx.attacker.hp, reason="self_cost")
    return HandlerReturn(value=value)


def いびき_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def いわくだき_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.5)


def いわなだれ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def インファイト_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1})


def うらみつらみ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def エアスラッシュ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def エナジーボール_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def エレキネット_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def オクタンほう_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1}, chance=0.5)


def おしゃべり_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おしゃべりの追加効果: 相手をこんらん状態にする（確率100%）。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def おどろかす_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def オーバーヒート_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def オーラウイング_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 1})


def オーラぐるま_check_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーラぐるまのタイプを判定する。"""
    if ctx.attacker and ctx.attacker.ability.is_hangry:
        return HandlerReturn(value="あく")
    return HandlerReturn(value=value)


def オーロラビーム_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1}, chance=0.1)


def かえんぐるま_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def かえんだん_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def かえんほうしゃ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def かえんボール_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def かかとおとし_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かかとおとしの追加効果: 30%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.3)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def かみくだく_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.2)


def かみつく_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def かみなり_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かみなりの天候による命中率補正。雨: 必中、晴れ: 50%
    攻撃側がばんのうがさを持つ場合、晴れでも命中率低下なし。
    防御側がばんのうがさを持つ場合、雨でも必中にならない。
    """
    if battle.weather_for(ctx.defender).rainy:
        return HandlerReturn(value=None)  # 必中
    elif battle.weather_for(ctx.attacker).sunny:
        return HandlerReturn(value=50)
    return HandlerReturn(value=value)


# 10まんボルトは数字始まりのためプライベート関数として定義する
def _10まんボルト_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def かみなり_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def かみなりあらし_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.2)


def かみなりのキバ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def かみなりのキバ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.1)


def かみなりパンチ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def からみつく_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1}, chance=0.1)


def がむしゃら_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """がむしゃらのダメージを計算する。"""
    value = max(0, ctx.defender.hp - ctx.attacker.hp)
    return HandlerReturn(value=value)


def ガリョウテンセイ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1})


def がんせきふうじ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def きあいだま_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def きあいパンチ_check_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きあいパンチの発動可否を判定する。

    行動前に実際の攻撃ダメージを受けていた場合は不発になる。
    """
    if ctx.attacker.hits_taken > 0:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "きあいパンチ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def キラースピン_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def _drain_hp(battle: Battle, ctx: AttackContext, damage: int, heal_ratio: float) -> None:
    """ドレイン回収(drain)で回復するHP量を計算する。"""
    damage = damage or ctx.substitute_damage
    heal_amount = int(damage * heal_ratio)
    heal_amount = battle.events.emit(Event.ON_CALC_DRAIN, ctx, heal_amount)
    battle.modify_hp(ctx.attacker, v=heal_amount, reason="drain")


def ギガドレイン_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ギガドレインの回復量を計算する。"""
    # ダメージ計算後のHP減少量を回復する
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def ぎんいろのかぜ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "B": 1, "C": 1, "D": 1, "S": 1}, chance=0.1)


def くさわけ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 1})


def クロスポイズン_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.1)


def グラスミキサー_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1}, chance=0.5)


def グロウパンチ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1})


def げんしのちから_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1, "B": 1, "C": 1, "D": 1, "S": 1}, chance=0.1)


def こうそくスピン_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 1})


def こおりのキバ_apply_flinch_or_freeze(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こおりのキバの追加効果: こおりかひるみをどちらか一方を 10% で付与する。

    1回の確率判定（10%）で発動し、発動した場合はこおりかひるみをランダムに選択する。
    """
    chance = battle.resolve_secondary_chance(ctx, 0.1)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    if battle.random.random() < 0.5:
        return HandlerReturn(value=battle.ailment_manager.apply(
            ctx.defender, "こおり", source=ctx.attacker, ctx=ctx
        ))
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, "ひるみ", source=ctx.attacker
    ))


def こがらしあらし_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1}, chance=0.3)


def こごえるかぜ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def こごえるせかい_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def こなゆき_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def コメットパンチ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1}, chance=0.2)


def コールドフレア_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ゴッドバード_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ゴールドラッシュ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -1})


def サイケこうせん_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サイケこうせんの追加効果: 10%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.1)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def サイコキネシス_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def サイコブースト_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def さわぐ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """さわぐ技の初回命中時にさわぐ揮発性状態を付与する。

    すでにさわぐ状態の場合（強制行動の2・3ターン目）は何もしない。
    カウントは3ターン固定。
    """
    attacker = ctx.attacker
    if attacker.has_volatile("さわぐ"):
        return HandlerReturn(value=value)
    battle.volatile_manager.apply(
        attacker, "さわぐ", count=3, source=attacker,
        move_name=ctx.move.name
    )
    return HandlerReturn(value=value)


def シェルアームズ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.2)


def シェルブレード_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.5)


def シグナルビーム_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シグナルビームの追加効果: 10%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.1)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def したでなめる_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def しねんのずつき_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def シャカシャカほう_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.2)


def シャドーボール_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.2)


def シャドーボーン_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.2)


def しんぴのちから_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1})


def シードフレア_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2}, chance=0.4)


def じならし_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def じゃどくのくさり_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく", chance=0.5)


def じゃれつく_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1}, chance=0.1)


def じんつうりき_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.1)


def スケイルノイズ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1})


def スチームバースト_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def スパーク_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def スモッグ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.4)


def ずつき_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def せいなるほのお_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.5)


def ソウルクラッシュ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def たきのぼり_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def たつまき_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def だいちのちから_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def だいもんじ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ダイヤストーム_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 2}, chance=0.5)


def だくりゅう_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1}, chance=0.3)


def ダストシュート_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def ダブルニードル_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.2)


def ダブルパンツァー_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ダークファイア_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def チャージビーム_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1}, chance=0.7)


def つららおとし_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def テラバースト_modify_move_category(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テラバーストの分類（物理/特殊）を判定する。"""
    mon = ctx.attacker
    if mon.terastallized:
        atk = mon.ranked_stats["A"]
        spa = mon.ranked_stats["C"]
        value = "物理" if atk > spa else "特殊"
    return HandlerReturn(value=value)


def テラバースト_modify_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テラバーストのタイプを判定する。"""
    mon = ctx.attacker
    if mon.terastallized:
        value = mon.active_tera_type
    return HandlerReturn(value=value)


def テラバースト_stellar_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ステラテラスタル状態ではテラバーストの威力が100になる補正。"""
    if ctx.attacker.active_tera_type == 'ステラ':
        value = 5120  # = 4096 * 100 / 80
    return HandlerReturn(value=value)


def テラバースト_stellar_stat_drop(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ステラテラスタル時のテラバースト発動後の攻撃・特攻-1段階効果。"""
    mon = ctx.attacker
    if mon and mon.active_tera_type == 'ステラ':
        battle.modify_stats(mon, {"A": -1, "C": -1}, source=mon)
    return HandlerReturn(value=value)


def でんきショック_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def でんじほう_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def とびかかる_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def とびつく_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def とびはねる_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def トロピカルキック_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def どくづき_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def どくどくのキバ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく", chance=0.5)


def どくばり_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def どくばりセンボン_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.5)


def ドラゴンダイブ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def ドラムアタック_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def どろかけ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1})


def どろばくだん_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1}, chance=0.3)


def どろぼう_steal_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どろぼう・ほしがるのアイテム奪取効果。"""
    battle.take_item(ctx.defender)
    return HandlerReturn(value=value)


def ナイトバースト_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1}, chance=0.4)


def ニトロチャージ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 1})


def ニードルアーム_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ねこだまし_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ")


def ねっさのあらし_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.2)


def ねっさのだいち_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ねっとう_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ねっぷう_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ねんりき_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねんりきの追加効果: 10%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.1)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def のしかかり_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def はいよるいちげき_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def はがねのつばさ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1}, chance=0.1)


def はたきおとす_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """はたきおとすのアイテム所持時1.5倍補正。"""
    if ctx.defender.has_item():
        value = value * 6144 // 4096
    return HandlerReturn(value=value)


def level_fixed_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """使用者レベルと同値の固定ダメージを計算する。"""
    return HandlerReturn(value=ctx.attacker.level)

def apply_bind_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """バインド系技: ランダムターン数でバインド状態を付与する。ねばりのかぎづめで7ターン固定。"""
    count_pair = battle.events.emit(
        Event.ON_MODIFY_DURATION,
        ctx,
        ["バインド", battle.random.randint(4, 5)]
    )
    battle.volatile_manager.apply(ctx.defender, "バインド", count=count_pair[1], source=ctx.attacker)
    return HandlerReturn(value=value)


def はたきおとす_remove_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はたきおとすのアイテム除去効果。"""
    battle.remove_item(target=ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def はっけい_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def はやてがえし_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ")


def はやてがえし_try_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はやてがえしの発動条件を判定する。

    相手が未行動かつ優先攻撃技を選択している時のみ成功する。
    """
    if not _check_はやてがえし_condition(battle, ctx):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "はやてがえし"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はるのあらし_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1}, chance=0.3)


def ハートスタンプ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ハードローラー_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ばかぢから_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": -1, "B": -1})


def ばくれつパンチ_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ばくれつパンチの追加効果: 相手をこんらん状態にする（確率100%）。"""
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def バブルこうせん_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1}, chance=0.1)


def バリアーラッシュ_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": 1})


def バークアウト_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def バーンアクセル_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ひっさつまえば_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.1)


def ひのこ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ひゃっきやこう_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ひやみず_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def ひょうざんおろし_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def びりびりちくちく_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ピヨピヨパンチ_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ピヨピヨパンチの追加効果: 20%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.2)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def フェイタルクロー_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フェイタルクローの追加効果: どく/まひ/こおり のいずれかをランダムに付与する。

    確率0.5で発動し、発動した場合はどく・まひ・こおりを各1/3の確率で付与する。
    """
    chance = battle.resolve_secondary_chance(ctx, 0.5)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    ailment = battle.random.choice(["どく", "まひ", "こおり"])
    return HandlerReturn(value=battle.ailment_manager.apply(
        ctx.defender, ailment, source=ctx.attacker, ctx=ctx
    ))


def ふしょくガス_remove_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふしょくガスのアイテム除去効果。"""
    battle.remove_item(target=ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def ふぶき_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふぶきの天候による命中率補正。

    雪: 必中

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather_manager.current.name
    if weather == "ゆき":
        return HandlerReturn(value=None)  # 必中
    return HandlerReturn(value=value)


def ふぶき_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def ふみつけ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def フリーズドライ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def フリーズボルト_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def フルールカノン_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def フレアソング_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1})


def フレアドライブ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ふわふわフォール_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ふんえん_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def Ｖジェネレート_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1, "S": -1})


def ぶちかまし_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1})


def ブレイククロー_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.5)


def ブレイズキック_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ヘドロウェーブ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.1)


def ヘドロこうげき_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def ヘドロばくだん_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def ホイールスピン_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": -2})


def ほうでん_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def ほっぺすりすり_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def ホネこんぼう_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.1)


def ほのおのキバ_apply_flinch_or_burn(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほのおのキバの追加効果: やけどかひるみをどちらか一方を 10% で付与する。

    1回の確率判定（10%）で発動し、発動した場合はやけどかひるみをランダムに選択する。
    """
    chance = battle.resolve_secondary_chance(ctx, 0.1)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    if battle.random.random() < 0.5:
        return HandlerReturn(value=battle.ailment_manager.apply(
            ctx.defender, "やけど", source=ctx.attacker, ctx=ctx
        ))
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, "ひるみ", source=ctx.attacker
    ))


def ほのおのパンチ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ほのおのまい_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1}, chance=0.5)


def ほのおのムチ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def ぼうふう_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ぼうふうの天候による命中率補正。雨: 必中、晴れ: 50%
    攻撃側がばんのうがさを持つ場合、晴れでも命中率低下なし。
    防御側がばんのうがさを持つ場合、雨でも必中にならない。
    """
    if battle.weather_for(ctx.defender).rainy:
        return HandlerReturn(value=None)  # 必中
    elif battle.weather_for(ctx.attacker).sunny:
        return HandlerReturn(value=50)
    return HandlerReturn(value=value)


def ぼうふう_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ぼうふうの追加効果: 30%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.3)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def ボルテッカー_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def ポイズンアクセル_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def ポイズンテール_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.1)


def マジカルアクセル_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """マジカルアクセルの追加効果: 30%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.3)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def マジカルフレイム_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def マッドショット_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def まわしげり_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ミストボール_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1}, chance=0.5)


def みずのはどう_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みずのはどうの追加効果: 20%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.2)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def ミラーショット_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"ACC": -1}, chance=0.3)


def むしのさざめき_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def むしのていこう_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def ムーンフォース_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1}, chance=0.3)


def メタルクロー_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1}, chance=0.1)


def もえあがるいかり_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def やきつくす_remove_berry(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """やきつくすのきのみ焼却効果。"""
    if ctx.defender.item.is_berry():
        battle.remove_item(target=ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def ようかいえき_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def らいげき_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.2)


def らいめいげり_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def ラスターカノン_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def ラスターパージ_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.5)


def りゅうせいぐん_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def りゅうのいぶき_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def りんごさん_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1})


def リーフストーム_modify_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def ルミナコリジョン_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def れいとうパンチ_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def れいとうビーム_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def れんごく_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど")


def ロッククライム_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ロッククライムの追加効果: 20%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.2)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))


def ローキック_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def ワイドブレイカー_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def わるあがき_self_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.modify_hp(ctx.attacker, r=-1/4, reason="recoil", source=ctx.attacker))


def ワンダースチーム_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ワンダースチームの追加効果: 20%の確率で相手をこんらん状態にする。"""
    chance = battle.resolve_secondary_chance(ctx, 0.2)
    if battle.random.random() >= chance:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.volatile_manager.apply_confusion(
        ctx.defender, source=ctx.attacker
    ))
