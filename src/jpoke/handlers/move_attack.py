"""攻撃技関連のイベントハンドラ関数を提供するモジュール。

物理・特殊攻撃技の実行に関連するハンドラ関数を提供します。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext

from jpoke.enums import Event, Interrupt, LogCode
from jpoke.core import HandlerReturn
from . import common
from .move import (
    apply_ailment_to_defender,
    apply_volatile_to_attacker,
    apply_volatile_to_defender,
    modify_attacker_stats,
    modify_defender_stats,
)


def pivot(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def ohko_modify_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """一撃必殺技の確定ダメージを計算する。"""
    return HandlerReturn(value=ctx.defender.hp)


def HP_ratio_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """対象の現在HPの半分を与える固定ダメージを計算する。"""
    return HandlerReturn(value=max(1, ctx.defender.hp // 2))


def オーラぐるま_check_move_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """オーラぐるまのタイプを判定する。"""
    if ctx.source and ctx.source.ability.is_hangry:
        return HandlerReturn(value="あく")
    return HandlerReturn(value=value)


def がむしゃら_modify_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """がむしゃらのダメージを計算する。"""
    value = max(0, ctx.defender.hp - ctx.attacker.hp)
    return HandlerReturn(value=value)


def きあいパンチ_check_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """きあいパンチの発動可否を判定する。

    行動前に実際の攻撃ダメージを受けていた場合は不発になる。
    """
    if ctx.attacker.hits_taken > 0:
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "きあいパンチ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def どろぼう_steal_item(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どろぼう・ほしがるのアイテム奪取効果。"""
    battle.take_item(ctx.attacker, ctx.defender, move=ctx.move)
    return HandlerReturn(value=value)


def はたきおとす_power(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """はたきおとすのアイテム所持時1.5倍補正。"""
    if ctx.defender.has_item():
        value = value * 6144 // 4096
    return HandlerReturn(value=value)


def level_fixed_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """使用者レベルと同値の固定ダメージを計算する。"""
    return HandlerReturn(value=ctx.attacker.level)


def はたきおとす_remove_item(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """はたきおとすのアイテム除去効果。"""
    battle.remove_item(target=ctx.defender, source=ctx.attacker, move=ctx.move)
    return HandlerReturn(value=value)


def はやてがえし_try_move(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """はやてがえしの発動条件を判定する。

    相手が未行動かつ優先攻撃技を選択している時のみ成功する。
    """
    if not _check_はやてがえし_condition(battle, ctx):
        battle.add_event_log(ctx.attacker, LogCode.MOVE_FAILED,
                             payload={"reason": "はやてがえし"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def いのちがけ_pay_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いのちがけ発動前にHPを支払い、元のHPをコンテキストに保存する。"""
    ctx.hp_cost = ctx.attacker.hp
    battle.modify_hp(ctx.attacker, v=-ctx.attacker.hp, reason="self_cost")
    return HandlerReturn(value=value)


def いのちがけ_modify_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """いのちがけの固定ダメージを計算する（支払い前のHPを使用）。"""
    return HandlerReturn(value=getattr(ctx, "hp_cost", 0))


def かみなり_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かみなりの天候による命中率補正。

    雨: 必中
    晴れ: 50%

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather
    if weather is not None and weather.rainy:
        return HandlerReturn(value=None)  # 必中
    elif weather is not None and weather.sunny:
        return HandlerReturn(value=50)
    return HandlerReturn(value=value)


def _drain_hp(battle: Battle, ctx: EventContext, damage: int, heal_ratio: float) -> None:
    """ドレイン回収(drain)で回復するHP量を計算する。"""
    damage = damage or ctx.substitute_damage
    heal_amount = int(damage * heal_ratio)
    heal_amount = battle.events.emit(Event.ON_CALC_DRAIN, ctx, heal_amount)
    battle.modify_hp(ctx.attacker, v=heal_amount, reason="drain")


def ギガドレイン_heal_attacker(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """ギガドレインの回復量を計算する。"""
    # ダメージ計算後のHP減少量を回復する
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def テラバースト_modify_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テラバーストのタイプを判定する。"""
    mon = ctx.attacker
    if mon.terastallized:
        value = mon.active_tera_type
    return HandlerReturn(value=value)


def テラバースト_modify_move_category(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テラバーストの分類（物理/特殊）を判定する。"""
    mon = ctx.attacker
    if mon.terastallized:
        atk = mon.ranked_stats["A"]
        spa = mon.ranked_stats["C"]
        value = "物理" if atk > spa else "特殊"
    return HandlerReturn(value=value)


def テラバースト_stellar_power(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ステラテラスタル状態ではテラバーストの威力が100になる補正。"""
    if ctx.attacker.active_tera_type == 'ステラ':
        value = 5120  # = 4096 * 100 / 80
    return HandlerReturn(value=value)


def テラバースト_stellar_stat_drop(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ステラテラスタル時のテラバースト発動後の攻撃・特攻-1段階効果。"""
    mon = ctx.attacker
    if mon and mon.active_tera_type == 'ステラ':
        battle.modify_stats(mon, {"A": -1, "C": -1}, source=mon)
    return HandlerReturn(value=value)


def ふぶき_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def ふしょくガス_remove_item(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ふしょくガスのアイテム除去効果。"""
    battle.remove_item(target=ctx.defender, source=ctx.attacker, move=ctx.move)
    return HandlerReturn(value=value)


def ぼうふう_accuracy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぼうふうの天候による命中率補正。

    雨: 必中
    晴れ: 50%

    Args:
        battle: バトルインスタンス
        ctx: コンテキスト
        value: 現在の命中率

    Returns:
        HandlerReturn: 補正があればTrue、なければFalse
    """
    weather = battle.weather
    if weather is not None and weather.rainy:
        return HandlerReturn(value=None)  # 必中
    elif weather is not None and weather.sunny:
        return HandlerReturn(value=50)
    return HandlerReturn(value=value)


def やきつくす_remove_berry(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """やきつくすのきのみ焼却効果。"""
    if common.is_berry_item(ctx.defender.item.name):
        battle.remove_item(target=ctx.defender, source=ctx.attacker, move=ctx.move)
    return HandlerReturn(value=value)


def _check_はやてがえし_condition(battle: Battle, ctx: EventContext) -> bool:
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


def わるあがき_self_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return common.self_damage(battle, ctx, value, r=1/4, reason="recoil")


def アームハンマー_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": -1})


def アイアンテール_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.3)


def アイスハンマー_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": -1})


def アクアステップ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 1})


def アクアブレイク_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.2)


def いわくだき_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.5)


def インファイト_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1})


def ガリョウテンセイ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1})


def がんせきふうじ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def コメットパンチ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1}, chance=0.2)


def シェルブレード_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.5)


def じならし_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def ソウルクラッシュ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def とびかかる_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def とびつく_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def ドラムアタック_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def トロピカルキック_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def ニトロチャージ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"S": 1})


def はいよるいちげき_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def ばかぢから_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": -1, "B": -1})


def はやてがえし_apply_volatile_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ")


def ブレイククロー_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1}, chance=0.5)


def ほっぺすりすり_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def メタルクロー_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"A": 1}, chance=0.1)


def らいめいげり_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def ローキック_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def ワイドブレイカー_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def アーマーキャノン_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1, "D": -1})


def アシッドボム_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})


def いてつくしせん_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1}, chance=0.1)


def エナジーボール_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def エレキネット_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def オーバーヒート_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def こごえるかぜ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def こごえるせかい_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def サイコキネシス_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def サイコブースト_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def シャドーボール_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.2)


def スケイルノイズ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"B": -1})


def チャージビーム_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": 1}, chance=0.7)


def でんじほう_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def バークアウト_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def ひやみず_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


def フルールカノン_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def マジカルフレイム_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def マッドショット_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"S": -1})


def ミストボール_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1}, chance=0.5)


def むしのさざめき_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def むしのていこう_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"C": -1})


def ラスターカノン_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.1)


def ラスターパージ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -1}, chance=0.5)


def リーフストーム_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def りゅうせいぐん_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"C": -2})


def ルミナコリジョン_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"D": -2})
