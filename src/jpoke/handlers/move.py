"""技関連のイベントハンドラ関数を提供するモジュール。

技の実行に関連するハンドラ関数を提供します。
PP消費、交代技、吹き飛ばし技などの処理を行います。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext
    from jpoke.utils.type_defs import RoleSpec, Stat, AilmentName, VolatileName

from jpoke.enums import Event, Interrupt, LogCode
from jpoke.core import Handler, HandlerReturn
from . import common


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
                          ctx: EventContext,
                          value: Any,
                          stats: dict[Stat, int],
                          chance: float = 1) -> HandlerReturn:
    """攻撃側の能力ランクを変化させる。"""
    return common.modify_stats(
        battle, ctx, value, stats,
        target_spec="attacker:self", source_spec="attacker:self", chance=chance
    )


def modify_defender_stats(battle: Battle,
                          ctx: EventContext,
                          value: Any,
                          stats: dict[Stat, int],
                          chance: float = 1) -> HandlerReturn:
    """防御側の能力ランクを変化させる。"""
    return common.modify_stats(
        battle, ctx, value, stats,
        target_spec="defender:self", source_spec="attacker:self", chance=chance
    )


def apply_ailment_to_defender(battle: Battle,
                              ctx: EventContext,
                              value: Any,
                              ailment: AilmentName,
                              count: int | None = None,
                              chance: float = 1) -> HandlerReturn:
    return common.apply_ailment(
        battle, ctx, value, target_spec="defender:self", ailment=ailment,
        count=count, source_spec="attacker:self", chance=chance
    )


def apply_volatile_to_attacker(battle: Battle,
                               ctx: EventContext,
                               value: Any,
                               volatile: VolatileName,
                               count: int | None = None,
                               chance: float = 1,
                               **kwargs) -> HandlerReturn:
    return common.apply_volatile(
        battle, ctx, value, target_spec="attacker:self", volatile=volatile,
        count=count, source_spec="attacker:self", chance=chance, **kwargs
    )


def apply_volatile_to_defender(battle: Battle,
                               ctx: EventContext,
                               value: Any,
                               volatile: VolatileName,
                               count: int | None = None,
                               chance: float = 1,
                               **kwargs) -> HandlerReturn:
    return common.apply_volatile(
        battle, ctx, value, target_spec="defender:self", volatile=volatile,
        count=count, source_spec="attacker:self", chance=chance, **kwargs
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


# ===== 技個別のハンドラ =====


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


def テラバースト_modify_move_type(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """テラバーストのタイプを判定する。"""
    mon = ctx.attacker
    if mon.terastallized:
        value = mon.active_tera_type
    return HandlerReturn(value=value)


def テラバースト_modify_move_category(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
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


def しっぽをふる_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"B": -1})


def じゅうりょく_activate_global_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return common.activate_global_field(battle, ctx, value, global_field="じゅうりょく", source_spec="attacker:self")


def すなあらし_activate_weather(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return common.activate_weather(battle, ctx, value, weather="すなあらし", source_spec="attacker:self")


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


def トーチカ_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="トーチカ")


def どくどく_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく")


def どくのこな_apply_ailment_to_defender(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def トリックルーム_activate_global_field(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return common.activate_global_field(battle, ctx, value, global_field="トリックルーム", source_spec="attacker:self", toggle=True)


def ドわすれ_modify_attacker_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"D": 2})


def なきごえ_modify_defender_stats(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"A": -1})


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
    return common.activate_global_field(battle, ctx, value, global_field="マジックルーム", source_spec="attacker:self", toggle=True)


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
    return common.activate_global_field(battle, ctx, value, global_field="ワンダールーム", source_spec="attacker:self", toggle=True)


def キングシールド_apply_volatile_to_attacker(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_attacker(battle, ctx, value, volatile="キングシールド")
