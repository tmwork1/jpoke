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
from jpoke.core.event_logger import FailureLogPayload, VolatilePayload, StatChangePayload
from jpoke.utils.math import apply_fixed_modifier
from jpoke.data import TYPE_MODIFIER
from .move import (
    apply_ailment_to_defender,
    apply_confusion_to_defender,
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
    if battle.command_manager.get_available_switch_commands(player):
        battle.player_states[player].interrupt = Interrupt.PIVOT
    return HandlerReturn(value=value)

def ohko_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """一撃必殺技の確定ダメージを計算する。"""
    return HandlerReturn(value=ctx.defender.hp)

def half_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """対象の現在HPの半分を与える固定ダメージを計算する。"""
    return HandlerReturn(value=max(1, ctx.defender.hp // 2))


def アイアンテール_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1}, chance=0.3)


def _3ぼんのや_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)

def _3ぼんのや_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1}, chance=0.5)


def アイアンヘッド_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def アイアンローラー_check_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アイアンローラーの使用可否: フィールドが存在しない場合に失敗させる。"""
    if not battle.terrain.is_active:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="アイアンローラー_フィールドなし")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def アイアンローラー_clear_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アイアンローラー: ダメージ後にフィールドを解除する。"""
    battle.terrain_manager.remove()
    return HandlerReturn(value=value)


def アイススピナー_clear_terrain(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アイススピナー: ダメージ後にフィールドを解除する。"""
    battle.terrain_manager.remove()
    return HandlerReturn(value=value)


def アイスハンマー_lower_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": -1})


def あおいほのお_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.2)


def アクアステップ_boost_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 1})


def アクアブレイク_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1}, chance=0.2)


def あくのはどう_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def アシストパワー_boost_power_by_rank(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アシストパワー: 使用者のランク上昇合計1段階ごとに威力が20増加する（基本威力20）。

    威力 = 20 + 20 * rank_sum = 20 * (1 + rank_sum)
    ON_CALC_POWER_MODIFIER は 4096 = 1.0 倍基準のため
    modifier = 4096 * (1 + rank_sum) を apply_fixed_modifier に渡す。
    """
    attacker = ctx.attacker
    # 正のランク変化の合計を計算（A/B/C/D/S のみ対象、ACC/EVA を除く）
    rank_sum = sum(max(0, v) for k, v in attacker.rank.items() if k in ("atk", "def", "spa", "spd", "spe"))
    if rank_sum > 0:
        modifier = 4096 * (1 + rank_sum)
        value = apply_fixed_modifier(value, modifier)
    return HandlerReturn(value=value)


def アシッドボム_sharply_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2})


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
        attacker, "あばれる", count=count, source=attacker, move_name=ctx.move.name
    )
    return HandlerReturn(value=value)


def アフロブレイク_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/4)


def あやしいかぜ_boost_all_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1, "spa": 1, "spd": 1, "spe": 1}, chance=0.1)


def Gのちから_gravity_boost(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうりょく中にGのちからの威力が1.5倍になる"""
    if battle.get_global_field("じゅうりょく").is_active:
        return HandlerReturn(value=apply_fixed_modifier(value, 6144))  # 1.5倍
    return HandlerReturn(value=value)

def Gのちから_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1})


def あわ_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1}, chance=0.1)


def アーマーキャノン_lower_attacker_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1, "spd": -1})


def アームハンマー_lower_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": -1})


def いじげんホール_remove_protect(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いじげんホールの追加効果: 相手のまもる系揮発性状態を解除する。"""
    defender = ctx.defender
    for volatile in _FAINT_REMOVE_VOLATILES:
        if defender.has_volatile(volatile):
            battle.volatile_manager.remove(defender, volatile)
            battle.add_event_log(
                defender,
                LogCode.VOLATILE_REMOVED,
                payload=VolatilePayload(volatile=volatile, display_reason="いじげんホール")
            )
    return HandlerReturn(value=value)


def いじげんラッシュ_lower_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1})


def いじげんラッシュ_remove_protect(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いじげんラッシュの追加効果: 相手のまもる系揮発性状態を解除する。"""
    defender = ctx.defender
    for volatile in _FAINT_REMOVE_VOLATILES:
        if defender.has_volatile(volatile):
            battle.volatile_manager.remove(defender, volatile)
            battle.add_event_log(
                defender,
                LogCode.VOLATILE_REMOVED,
                payload=VolatilePayload(volatile=volatile, display_reason="いじげんラッシュ")
            )
    return HandlerReturn(value=value)


def いてつくしせん_apply_freeze_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いてつくしせんの追加効果: 10%の確率で相手をこおり状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def いにしえのうた_apply_sleep_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いにしえのうたの追加効果: 10%の確率で相手をねむり状態にする。"""
    return apply_ailment_to_defender(battle, ctx, value, ailment="ねむり", chance=0.1)


def いのちがけ_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちがけ: 現在HPを固定ダメージとして与え、使用者のHPを0にする（命中時のみ発生）。

    ON_MODIFY_MOVE_DAMAGE は命中判定・まもる等を通過した後にのみ発火するため、
    技が外れた場合やまもるで防がれた場合はHPを消費しない。
    """
    hp_cost = ctx.attacker.hp
    battle.modify_hp(ctx.attacker, v=-hp_cost, reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=hp_cost)


def いびき_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def いびき_check_sleep(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いびきの発動条件チェック: 自分がねむり状態（ゆめうつつ含む）でない場合に失敗させる。"""
    if not ctx.attacker.ailment.is_sleep:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="いびき_ねむり状態でない"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def いわくだき_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1}, chance=0.5)


def いわなだれ_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def インファイト_lower_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1, "spd": -1})


def ウェザーボール_modify_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ウェザーボール: 天候に応じてタイプを変化させる。

    天候が有効な場合（エアロック・ノーてんき・ばんのうがさで無効化されていない）、
    天候ごとに対応するタイプに変換する。
    """
    weather = battle.weather_for(ctx.attacker)
    type_map = {
        "はれ": "ほのお",
        "おおひでり": "ほのお",
        "あめ": "みず",
        "おおあめ": "みず",
        "すなあらし": "いわ",
        "ゆき": "こおり",
    }
    new_type = type_map.get(weather.name)
    if new_type is not None:
        value = new_type
    return HandlerReturn(value=value)


def ウェザーボール_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ウェザーボール: 天候が有効なとき威力を2倍にする。"""
    weather = battle.weather_for(ctx.attacker)
    if weather.name != "":
        value = apply_fixed_modifier(value, 8192)  # ×2倍
    return HandlerReturn(value=value)


def ウェーブタックル_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/3)


def うたかたのアリア_cure_defender_burn(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うたかたのアリア: 追加効果として、命中時に防御側のやけどを治す。

    やけど以外の状態異常は治さない。ちからずくで無効化され威力が上がる代わりに発動しなくなる。
    りんぷん・おんみつマントを持つ相手には発動しない（`resolve_secondary_chance` 経由で判定）。
    """
    chance = battle.resolve_secondary_chance(ctx, 1)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    mon = ctx.defender
    if mon.ailment.name == "やけど":
        battle.ailment_manager.remove(mon)
    return HandlerReturn(value=value)


def うちおとす_apply_grounded(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うちおとす: 命中時に相手にうちおとす揮発性状態を付与する。

    ひこうタイプ・ふゆう特性による浮遊状態を無効化する。
    元々地面にいる相手には付与しない。
    「追加効果」には該当しないため、ちからずく/りんぷん/おんみつマントの影響を受けない
    （resolve_secondary_chance を経由しないよう volatile_manager.apply を直接呼ぶ）。
    """
    if not battle.query.is_floating(ctx.defender):
        return HandlerReturn(value=value)
    battle.volatile_manager.apply(ctx.defender, "うちおとす", source=ctx.attacker)
    return HandlerReturn(value=value)


def ウッドハンマー_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/3)


def ウッドホーン_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ウッドホーンの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def うっぷんばらし_double_power_when_rank_dropped(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うっぷんばらし: そのターン中に使用者の能力ランクが下げられていたら威力が2倍になる。"""
    if ctx.attacker.stat_lowered_this_turn:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def うらみつらみ_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def エアスラッシュ_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def エナジーボール_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.1)


def エレキネット_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1})


def エレキボール_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """エレキボール: 自分の素早さ / 相手の素早さ の比率で威力を決定する。

    比率 = floor(自分のすばやさ / 相手のすばやさ)
    比率が 0 または相手の素早さが 0 の場合は威力 40。
    0: 40 / 1: 60 / 2: 80 / 3: 120 / 4以上: 150
    """
    atk_speed = ctx.attacker.stats["spe"]
    def_speed = ctx.defender.stats["spe"]
    if def_speed <= 0:
        ratio = 0
    else:
        ratio = atk_speed // def_speed
    if ratio >= 4:
        power = 150
    elif ratio == 3:
        power = 120
    elif ratio == 2:
        power = 80
    elif ratio == 1:
        power = 60
    else:
        power = 40
    return HandlerReturn(value=power * 4096)


def エレクトロビーム_boost_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """エレクトロビーム: とくこうを1段階上げる（追加効果ではないため必ず発動）。

    仕様:
    - ちからずくの追加効果ではないため、battle.modify_stats を直接呼ぶ。
    - パワフルハーブ使用時・あめでスキップ時もこのハンドラ（priority=50）が
      先に実行されるため、とくこう上昇は必ず発動する。
    """
    battle.modify_stats(ctx.attacker, {"spa": 1}, source=ctx.attacker)
    return HandlerReturn(value=value)


def エレクトロビーム_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """エレクトロビーム: 1ターン目に溜め状態へ移行、2ターン目は通過する。

    仕様:
    - あめ/おおあめによる自動スキップは エレクトロビーム_weather_skip（priority=90）で
      先に判定されるため、ここに到達するのは非あめ天候（あるいは2ターン目）の場合のみ。
    - 揮発状態なし（1ターン目）: 揮発状態を付与して攻撃を停止する
      （パワフルハーブがあれば同priority内で先に消費され、即攻撃に切り替わる）。
    - 揮発状態あり（2ターン目）: そのまま通過して攻撃に進む。
    - とくこう上昇は エレクトロビーム_boost_spa（priority=50）で先に処理される。
    """
    attacker = ctx.attacker
    if not attacker.has_volatile("エレクトロビーム"):
        battle.volatile_manager.apply(attacker, "エレクトロビーム", count=1, source=attacker)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def エレクトロビーム_weather_skip(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """エレクトロビーム: あめ/おおあめ下では溜めずにそのターンに攻撃する。

    仕様:
    - 揮発状態なし + あめ/おおあめ（1ターン目）: 溜めをスキップして攻撃に進む
      （stop_event=True で以降のハンドラ、特にパワフルハーブを実行させない）。
    - ばんのうがさを持つ場合は weather_for により あめ の恩恵を受けない。
    - priority=90 とし、パワフルハーブ（priority=100、item は先に登録されるため通常は
      同priority内でも先に実行される）より先に判定することで、天候による自動スキップが
      パワフルハーブの消費に優先されるようにする。
    """
    attacker = ctx.attacker
    if not attacker.has_volatile("エレクトロビーム") and battle.weather_for(attacker).rainy:
        return HandlerReturn(value=value, stop_event=True)
    return HandlerReturn(value=value)


def オクタンほう_lower_acc(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1}, chance=0.5)


def おしゃべり_apply_confusion(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おしゃべりの追加効果: 相手をこんらん状態にする（確率100%）。"""
    return apply_confusion_to_defender(battle, ctx, value)


def おどろかす_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def おはかまいり_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """おはかまいり: ひんしになった味方の数に応じて威力が増加する。

    基本威力 50 に対して (1 + ひんし味方数) 倍の modifier を掛ける。
    ひんし味方数は控えポケモン（bench）のうちひんしのもの。
    場に出ている自分自身はひんしでないため bench に含まれない。
    """
    player = battle.get_player(ctx.attacker)
    state = battle.player_states[player]
    fainted_count = sum(1 for p in state.bench if p.fainted)
    return HandlerReturn(value=apply_fixed_modifier(value, 4096 * (1 + fainted_count)))


def オーバーヒート_lower_attacker_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": -2})


def オーラウイング_boost_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 1})


def オーラぐるま_check_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーラぐるまのタイプを判定する。"""
    if ctx.attacker and ctx.attacker.ability.is_hangry:
        return HandlerReturn(value="あく")
    return HandlerReturn(value=value)


def オーロラビーム_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1}, chance=0.1)


def カウンター_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """カウンターの使用可否を判定する。

    そのターン相手から物理ダメージを受けていない場合は失敗する。
    """
    if ctx.attacker.last_physical_damage_received <= 0:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="カウンター")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def カウンター_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """カウンターの固定ダメージを計算する（物理被弾ダメージ × 2）。"""
    return HandlerReturn(value=ctx.attacker.last_physical_damage_received * 2)


def かえんぐるま_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def かえんぐるま_thaw_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かえんぐるま: こおり状態でも使用可能にし、こおりを解凍する。

    こおり_action (priority=10) より先に発火させる (priority=5) ことで、
    ailment が除去された状態で こおり_action の validity check が走り、
    こおり_action がスキップされる。
    """
    mon = ctx.attacker
    if mon.ailment.name == "こおり":
        battle.ailment_manager.remove(mon)
    return HandlerReturn(value=value)


def かえんだん_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def かえんほうしゃ_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def かえんボール_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def かえんボール_thaw_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かえんボール: こおり状態でも使用可能にし、こおりを解凍する。

    こおり_action (priority=10) より先に発火させる (priority=5) ことで、
    ailment が除去された状態で こおり_action の validity check が走り、
    こおり_action がスキップされる。
    """
    mon = ctx.attacker
    if mon.ailment.name == "こおり":
        battle.ailment_manager.remove(mon)
    return HandlerReturn(value=value)


def かかとおとし_apply_confusion(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かかとおとしの追加効果: 30%の確率で相手をこんらん状態にする。

    通常のこんらん付与技（2〜5ターン）と異なり、この技のこんらんは3〜5ターン継続する。
    """
    chance = battle.resolve_secondary_chance(ctx, 0.3)
    if chance < 1 and battle.random.random() >= chance:
        return HandlerReturn(value=value)
    count = battle.random.randint(3, 5)
    return HandlerReturn(value=battle.volatile_manager.apply(
        ctx.defender, "こんらん", count=count, source=ctx.attacker
    ))


def かかとおとし_crash(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かかとおとしが外れた場合の失敗反動ダメージ。自分の最大HPの1/2を受ける。"""
    battle.modify_hp(ctx.attacker, v=-max(1, ctx.attacker.max_hp // 2), reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def かげぬい_apply_no_escape(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かげぬいの追加効果: 相手をにげられない状態にする。

    ゴーストタイプの相手はにげられない状態の効果を無視できる
    （`にげられない`揮発性状態側のON_CHECK_TRAPPEDで判定するため、本ハンドラでの個別対応は不要）。
    追加効果のため、`apply_volatile_to_defender` 経由でちからずく・りんぷんの影響を受ける。
    """
    return apply_volatile_to_defender(battle, ctx, value, volatile="にげられない")


def かみくだく_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1}, chance=0.2)


def かみつく_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
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
def _10まんボルト_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def かみなり_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def かみなりあらし_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.2)


def かみなりのキバ_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.1)


def かみなりのキバ_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def かみなりパンチ_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def からげんき_double_power_when_ailment(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """からげんき: 使用者が状態異常のとき威力が2倍になる。"""
    if ctx.attacker.ailment.is_active:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def からげんき_ignore_burn_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """からげんき: やけど状態でも物理攻撃の威力が半減しない。

    ailment.py が ON_CALC_BURN_MODIFIER で 2048（0.5倍）を返すため、
    ここで 4096（1.0倍）で上書きして半減を打ち消す。
    """
    if ctx.attacker.ailment.name == "やけど":
        value = 4096
    return HandlerReturn(value=value)


def からみつく_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1}, chance=0.1)


def かわらわり_break_screens(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かわらわり: 相手側のリフレクター・ひかりのかべ・オーロラベールを解除する。

    壁解除は追加効果ではないため、りんぷん・おんみつマント・ちからずくの対象外。
    技が無効化されなかった場合（ON_HITに到達した場合）のみ発動する。
    """
    defender_side = battle.get_side(ctx.defender)
    for wall in ("リフレクター", "ひかりのかべ", "オーロラベール"):
        defender_side.deactivate(wall)
    return HandlerReturn(value=value)


def がむしゃら_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """がむしゃらのダメージを計算する。"""
    value = max(0, ctx.defender.hp - ctx.attacker.hp)
    return HandlerReturn(value=value)


def ガリョウテンセイ_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1, "spd": -1})


def がんせきアックス_set_stealth_rock(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """がんせきアックス: 命中後、相手陣営にステルスロックを設置する。"""
    side = battle.get_side(ctx.defender)
    side.activate("ステルスロック", 1)
    return HandlerReturn(value=value)


def がんせきふうじ_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1})


def きあいだま_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.1)


def きあいパンチ_check_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きあいパンチの発動可否を判定する。

    行動前に実際の攻撃ダメージを受けていた場合は不発になる。
    """
    if ctx.attacker.hits_taken > 0:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="きあいパンチ")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def きしかいせい_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """きしかいせい: 自分の残りHPが少ないほど威力が高くなる。

    計算式: X = floor(残りHP × 48 / 最大HP)
    X ≥ 33 → 20 / 17-32 → 40 / 10-16 → 80 / 5-9 → 100 / 2-4 → 150 / 0-1 → 200
    """
    return HandlerReturn(value=_hp_low_to_power(ctx.attacker.hp, ctx.attacker.max_hp) * 4096)


def きまぐレーザー_maybe_double_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きまぐレーザー: 30%の確率で威力が2倍になる。"""
    if battle.random.random() < 0.3:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def _hp_low_to_power(current_hp: int, max_hp: int) -> int:
    """HP割合（自HP低下依存）から威力を算出する共通関数（第5世代以降）。

    X = floor(残りHP × 48 / 最大HP)
    X ≥ 33 → 20 / 17-32 → 40 / 10-16 → 80 / 5-9 → 100 / 2-4 → 150 / 0-1 → 200
    """
    x = current_hp * 48 // max_hp
    if x >= 33:
        return 20
    elif x >= 17:
        return 40
    elif x >= 10:
        return 80
    elif x >= 5:
        return 100
    elif x >= 2:
        return 150
    else:
        return 200


def きゅうけつ_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """きゅうけつの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def キラースピン_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく")


def キラースピン_clear_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """キラースピン: バインドを解除し、自分のサイドの設置物を除去する。"""
    _clear_spin_effects(battle, ctx)
    return HandlerReturn(value=value)


def _clear_spin_effects(battle: Battle, ctx: AttackContext) -> None:
    """こうそくスピン・キラースピン共通: バインドと設置物を解除する。"""
    battle.volatile_manager.remove(ctx.attacker, "バインド")
    side = battle.get_side(ctx.attacker)
    for hazard in ("まきびし", "どくびし", "ステルスロック", "ねばねばネット"):
        side.deactivate(hazard)

def _drain_hp(battle: Battle, ctx: AttackContext, damage: int, heal_ratio: float) -> None:
    """ドレイン回収(drain)で回復するHP量を計算する。"""
    damage = damage or ctx.substitute_damage
    heal_amount = int(damage * heal_ratio)
    heal_amount = battle.events.emit(Event.ON_CALC_DRAIN, ctx, heal_amount)
    battle.modify_hp(ctx.attacker, v=heal_amount, reason="drain")

def _recoil(battle: Battle, ctx: AttackContext, value: int, ratio: float) -> HandlerReturn:
    """反動ダメージを与えるヘルパー関数。与ダメの ratio 分を攻撃側が受ける。"""
    recoil = max(1, int(value * ratio))
    battle.modify_hp(ctx.attacker, v=-recoil, reason="recoil", source=ctx.attacker)
    return HandlerReturn(value=value)


def ギガドレイン_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ギガドレインの回復量を計算する。"""
    # ダメージ計算後のHP減少量を回復する
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def ぎんいろのかぜ_boost_all_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1, "spa": 1, "spd": 1, "spe": 1}, chance=0.1)


def くさむすび_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """くさむすび: 対象の体重で威力を決定する。"""
    return HandlerReturn(value=_weight_to_power(ctx.defender.weight) * 4096)


def _weight_to_power(weight: float) -> int:
    """体重（kg）から威力を算出する共通関数。

    10kg未満: 20 / 25kg未満: 40 / 50kg未満: 60 / 100kg未満: 80 / 200kg未満: 100 / 以上: 120
    """
    if weight < 10:
        return 20
    elif weight < 25:
        return 40
    elif weight < 50:
        return 60
    elif weight < 100:
        return 80
    elif weight < 200:
        return 100
    else:
        return 120


def くさわけ_boost_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 1})


def くちばしキャノン_burn_contact_hitter(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くちばしキャノン発動前の判定: 接触技を受けていた場合は攻撃者をやけどにする。

    くちばしキャノンは優先度-3で必ず後攻となるため、技発動前に相手の接触技を受けることがある。
    ON_TRY_MOVE_1 の時点で contact_hitter が記録されていれば、その攻撃者をやけど状態にする。
    技自体はそのまま発動する。
    """
    hitter = ctx.attacker.contact_hitter
    if hitter is not None:
        battle.ailment_manager.apply(hitter, "やけど", source=ctx.attacker, ctx=ctx)
    return HandlerReturn(value=value)


def クロスポイズン_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.1)


def クロロブラスト_pay_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """クロロブラスト: 使用前に最大HPの1/2を消費する。"""
    cost = max(1, ctx.attacker.max_hp // 2)
    battle.modify_hp(ctx.attacker, v=-cost, reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def グラスミキサー_lower_acc(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1}, chance=0.5)


def グロウパンチ_boost_attacker_A(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1})


def けたぐり_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """けたぐり: 対象の体重で威力を決定する。"""
    return HandlerReturn(value=_weight_to_power(ctx.defender.weight) * 4096)


def ゲップ_check_ate_berry(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゲップの失敗条件: きのみを食べていない場合に失敗させる。"""
    mon = ctx.attacker
    if not mon.ate_berry:
        battle.add_event_log(mon, LogCode.MOVE_FAILED,
                             payload=FailureLogPayload(move=ctx.move.name, display_reason="ゲップ_きのみ未食"))
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def げんしのちから_boost_all_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1, "def": 1, "spa": 1, "spd": 1, "spe": 1}, chance=0.1)


def こうそくスピン_boost_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 1})


def こうそくスピン_clear_field(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こうそくスピン: バインドを解除し、自分のサイドの設置物を除去する。"""
    _clear_spin_effects(battle, ctx)
    return HandlerReturn(value=value)


def 効果抜群時威力ブースト(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """効果抜群のとき威力が4/3倍（5461/4096）になる。

    アクセルブレイク（かくとう）・イナズマドライブ（でんき）が使用する。
    らんきりゅう等の ON_CALC_DEF_TYPE_MODIFIER ハンドラを経由した実効タイプ相性を参照し、
    > 4096（1.0倍超）のとき威力に 5461/4096 ≈ 4/3 をかける。
    """
    type_modifier = battle.damage_calculator.calc_def_type_modifier(ctx)
    if type_modifier > 4096:
        value = apply_fixed_modifier(value, 5461)
    return HandlerReturn(value=value)


def こおりのキバ_apply_flinch_or_freeze(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こおりのキバの追加効果: 5%でこおり、5%でひるみを付与する。

    単一乱数で判定: r < base*0.5 → こおり、r < base → ひるみ。
    """
    base = battle.resolve_secondary_chance(ctx, 0.1)
    r = battle.random.random()
    if r < base * 0.5:
        return HandlerReturn(value=battle.ailment_manager.apply(
            ctx.defender, "こおり", source=ctx.attacker, ctx=ctx
        ))
    if r < base:
        return HandlerReturn(value=battle.volatile_manager.apply(
            ctx.defender, "ひるみ", source=ctx.attacker
        ))
    return HandlerReturn(value=value)


def こがらしあらし_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1}, chance=0.3)


def こごえるかぜ_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1})


def こごえるせかい_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1})


def こなゆき_apply_freeze_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def コメットパンチ_boost_attacker_A(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1}, chance=0.2)


def コールドフレア_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ゴッドバード_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ゴールドラッシュ_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": -1})


def サイケこうせん_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サイケこうせんの追加効果: 10%の確率で相手をこんらん状態にする。"""
    return apply_confusion_to_defender(battle, ctx, value, chance=0.1)


def サイコキネシス_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.1)


def サイコファング_break_screens(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サイコファング: 相手側のリフレクター・ひかりのかべ・オーロラベールを解除する。

    壁解除は追加効果ではないため、りんぷん・おんみつマント・ちからずくの対象外。
    技が無効化されなかった場合（ON_HITに到達した場合）のみ発動する。
    """
    defender_side = battle.get_side(ctx.defender)
    for wall in ("リフレクター", "ひかりのかべ", "オーロラベール"):
        defender_side.deactivate(wall)
    return HandlerReturn(value=value)


def サイコブースト_sharply_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": -2})


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


def サンダーダイブ_crash(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """サンダーダイブが外れた場合の失敗反動ダメージ。自分の最大HPの1/2を受ける。"""
    battle.modify_hp(ctx.attacker, v=-max(1, ctx.attacker.max_hp // 2), reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def シェルアームズ_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.2)


def シェルアームズ_modify_move_category(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シェルアームズ: 補正込みAがCより高い場合は物理技として計算する。"""
    mon = ctx.attacker
    if mon.ranked_stats["atk"] > mon.ranked_stats["spa"]:
        return HandlerReturn(value="physical")
    return HandlerReturn(value=value)


def シェルブレード_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1}, chance=0.5)


def しおづけ_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しおづけの追加効果: 100%の確率で相手をしおづけ揮発状態にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="しおづけ")


def しおふき_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """しおふき: 自分のHP比率に比例して威力が決まる（最大150）。

    ON_CALC_POWER_MODIFIER では modifier = floor(HP比率 × 4096) を返す。
    final_power = round_half_down(150 × modifier / 4096) = round_half_down(150 × HP比率)
    """
    modifier = int(ctx.attacker.hp * 4096 / ctx.attacker.max_hp)
    modifier = max(1, modifier)  # 威力が最低1になるよう保証
    return HandlerReturn(value=modifier)


def シグナルビーム_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シグナルビームの追加効果: 10%の確率で相手をこんらん状態にする。"""
    return apply_confusion_to_defender(battle, ctx, value, chance=0.1)


def したでなめる_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def しっとのほのお_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しっとのほのおの追加効果: そのターンにランクが上がった相手をやけど状態にする。"""
    if not ctx.defender.stat_raised_this_turn:
        return HandlerReturn(value=value)
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど")


def しっぺがえし_double_power_when_second(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しっぺがえし: 同ターン後攻で行動する場合、威力が2倍になる。"""
    attacker_player = battle.get_player(ctx.attacker)
    if battle.query.is_second_actor(attacker_player):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def しねんのずつき_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def シャカシャカほう_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.2)


def シャカシャカほう_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """シャカシャカほうの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def シャドーボール_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.2)


def シャドーボーン_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1}, chance=0.2)


def シャドーレイ_disable_defender_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シャドーレイ: 攻撃直前に相手の特性を無効化する（かたやぶりと同様の対象特性）。"""
    mon = ctx.defender
    if mon.ability.has_flag("mold_breaker_ignorable"):
        battle.add_ability_disabled_reason(mon, "シャドーレイ")
    return HandlerReturn(value=value)


def シャドーレイ_restore_defender_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """シャドーレイ: 攻撃終了後に相手の特性の無効化を解除する。"""
    battle.remove_ability_disabled_reason(ctx.defender, "シャドーレイ")
    return HandlerReturn(value=value)


def しんぴのちから_boost_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 1})


def シードフレア_sharply_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2}, chance=0.4)


def じごくぐるま_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/4)


def じごくづき_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じごくづきの追加効果: 2ターンの間、相手が音技を使えなくなる。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="じごくづき", count=2)


def じたばた_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """じたばた: 自分の残りHPが少ないほど威力が高くなる（きしかいせいと同計算）。"""
    return HandlerReturn(value=_hp_low_to_power(ctx.attacker.hp, ctx.attacker.max_hp) * 4096)


def じだんだ_calc_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じだんだ: 自分が前のターンで動けなかったとき、または使った技が失敗していたとき、威力が2倍になる。"""
    if ctx.attacker.failed_or_immobile_last_turn:
        return HandlerReturn(value=apply_fixed_modifier(value, 8192))
    return HandlerReturn(value=value)


def じならし_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1})


def じばく_pay_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じばく: 使用前に現在HPを全消費する。"""
    battle.modify_hp(ctx.attacker, v=-ctx.attacker.hp, reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def ジャイロボール_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ジャイロボール: 自分の実効素早さが相手より遅いほど威力が高くなる。

    威力 = floor(25 × 相手の実効素早さ ÷ 自分の実効素早さ) + 1、最大150。
    実効素早さはランク補正・特性・もちもの・まひ・おいかぜ・しつげんの影響を含む。
    自分の実効素早さが 0 の場合は威力を 1 として扱う（第六世代以降の仕様）。
    """
    atk_speed = battle.speed_calculator.calc_effective_speed(ctx.attacker)
    def_speed = battle.speed_calculator.calc_effective_speed(ctx.defender)
    if atk_speed <= 0:
        power = 1
    else:
        power = min(150, 25 * def_speed // atk_speed + 1)
    return HandlerReturn(value=power * 4096)


def じゃどくのくさり_apply_toxic_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく", chance=0.5)


def じゃれつく_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1}, chance=0.1)


def じんつうりき_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.1)


def すいとる_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """すいとるの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def スケイルショット_apply_stat_change(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """スケイルショット: 最終ヒット後に攻撃側のぼうぎょ-1・すばやさ+1。"""
    if ctx.hit_index != ctx.hit_count:
        return HandlerReturn(value=value)
    battle.modify_stats(ctx.attacker, {"def": -1, "spe": 1}, source=ctx.attacker)
    return HandlerReturn(value=value)


def スケイルノイズ_lower_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1})


def スチームバースト_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def すてみタックル_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/3)


def スパーク_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def スモッグ_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.4)


def ずつき_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def DDラリアット_ignore_def_rank(battle: Battle, ctx: AttackContext, value: float) -> HandlerReturn:
    """DDラリアット: 相手のランク変化を無視してダメージ計算する（防御ランク補正を1.0に固定）。"""
    return HandlerReturn(value=1)


def せいなるつるぎ_ignore_def_rank(battle: Battle, ctx: AttackContext, value: float) -> HandlerReturn:
    """せいなるつるぎ: 相手のランク変化を無視してダメージ計算する（防御ランク補正を1.0に固定）。"""
    return HandlerReturn(value=1)


def せいなるほのお_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.5)


def ソウルクラッシュ_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1})


def ソーラービーム_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソーラービーム: 1ターン目に光を吸収して溜める（天候によるスキップは判定済み）。"""
    return ソーラービーム系_charge(battle, ctx, value, "ソーラービーム")


def ソーラービーム_halve_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソーラービーム・ソーラーブレード共通: あめ/おおあめ/すなあらし/ゆき時に威力を半減する。

    仕様:
    - 攻撃者がばんのうがさを持つ場合は あめ でも威力が下がらない（weather_for による判定）
    - すなあらし/ゆき はばんのうがさで保護されない
    """
    weather = battle.weather_for(ctx.attacker)
    if weather.name in {"あめ", "おおあめ", "すなあらし", "ゆき"}:
        value = apply_fixed_modifier(value, 2048)  # 0.5倍
    return HandlerReturn(value=value)


def ソーラービーム_weather_skip(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソーラービーム: にほんばれ/おおひでり下では溜めずにそのターンに攻撃する。"""
    return ソーラービーム系_weather_skip(battle, ctx, value, "ソーラービーム")


def ソーラービーム系_charge(
    battle: Battle, ctx: AttackContext, value: Any, volatile_name: str
) -> HandlerReturn:
    """ソーラービーム・ソーラーブレード共通: 溜め状態へ移行する（2ターン目はそのまま通過）。

    仕様:
    - にほんばれ/おおひでりによる自動スキップは ソーラービーム系_weather_skip（priority=90）
      で先に判定されるため、ここに到達するのは非晴天候（あるいは2ターン目）の場合のみ
    - 揮発状態なし（1ターン目）: 揮発状態を付与して攻撃を停止する
      （パワフルハーブがあれば同priority内で先に消費され、即攻撃に切り替わる）
    - すでに溜め揮発状態にある場合（2ターン目）はそのまま通過する
    """
    attacker = ctx.attacker
    if not attacker.has_volatile(volatile_name):
        battle.volatile_manager.apply(attacker, volatile_name, count=1, source=attacker)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ソーラービーム系_weather_skip(
    battle: Battle, ctx: AttackContext, value: Any, volatile_name: str
) -> HandlerReturn:
    """ソーラービーム・ソーラーブレード共通: にほんばれ/おおひでり下では溜めずにそのターンに攻撃する。

    仕様:
    - 攻撃者がばんのうがさを持つ場合は にほんばれ でも溜める（weather_for による判定）
    - すでに溜め揮発状態にある場合（2ターン目）は何もしない
    - priority=90 とし、パワフルハーブ（priority=100）より先に判定することで、
      天候による自動スキップがパワフルハーブの消費に優先されるようにする
      （stop_event=True で以降のハンドラを実行させない）
    """
    attacker = ctx.attacker
    if not attacker.has_volatile(volatile_name) and battle.weather_for(attacker).sunny:
        return HandlerReturn(value=value, stop_event=True)
    return HandlerReturn(value=value)


def ソーラーブレード_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソーラーブレード: 1ターン目に光を吸収して溜める（天候によるスキップは判定済み）。"""
    return ソーラービーム系_charge(battle, ctx, value, "ソーラーブレード")


def ソーラーブレード_weather_skip(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ソーラーブレード: にほんばれ/おおひでり下では溜めずにそのターンに攻撃する。"""
    return ソーラービーム系_weather_skip(battle, ctx, value, "ソーラーブレード")


def たきのぼり_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def たたりめ_double_power_when_ailment(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """たたりめ: 対象が状態異常のとき威力が2倍になる。"""
    if ctx.defender.ailment.is_active:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def たつまき_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def だいちのちから_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.1)


def だいちのはどう_modify_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいちのはどう: 接地かつフィールドありのとき技タイプをフィールドに対応したタイプに変換する。"""
    if battle.query.is_floating(ctx.attacker):
        return HandlerReturn(value=value)
    terrain = battle.terrain.name
    type_map = {
        "エレキフィールド": "でんき",
        "グラスフィールド": "くさ",
        "ミストフィールド": "フェアリー",
        "サイコフィールド": "エスパー",
    }
    new_type = type_map.get(terrain)
    if new_type is not None:
        value = new_type
    return HandlerReturn(value=value)


def だいちのはどう_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいちのはどう: 接地かつフィールドありのとき威力を2倍にする。"""
    if battle.query.is_floating(ctx.attacker):
        return HandlerReturn(value=value)
    terrain = battle.terrain.name
    if terrain in {"エレキフィールド", "グラスフィールド", "ミストフィールド", "サイコフィールド"}:
        value = apply_fixed_modifier(value, 8192)  # ×2倍
    return HandlerReturn(value=value)


def だいばくはつ_pay_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいばくはつ: 使用前に現在HPを全消費する。"""
    battle.modify_hp(ctx.attacker, v=-ctx.attacker.hp, reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def だいもんじ_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ダイヤストーム_sharply_boost_defender_B(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2}, chance=0.5)


def だくりゅう_lower_acc(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1}, chance=0.3)


def ダストシュート_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def ダブルニードル_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.2)


def ダブルパンツァー_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ダメおし_double_power_when_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ダメおし: 同ターン中に対象が既にダメージを受けていたら威力が2倍になる。"""
    if ctx.defender.hits_taken > 0:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ダークファイア_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def チャージビーム_boost_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 1}, chance=0.7)


def つけあがる_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """つけあがる: 使用者の能力ランク上昇段階の合計1段階ごとに威力が20増加する（基本威力20）。

    基本威力 20 に対して (1 + rank_sum) 倍の modifier を掛ける。
    A/B/C/D/S の正ランク合計を使う（ACC/EVA は対象外）。
    アシストパワーと同様の計算。
    """
    attacker = ctx.attacker
    rank_sum = sum(max(0, v) for k, v in attacker.rank.items() if k in ("atk", "def", "spa", "spd", "spe"))
    return HandlerReturn(value=apply_fixed_modifier(value, 4096 * (1 + rank_sum)))


def つららおとし_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def てっていこうせん_pay_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """てっていこうせん: 使用前に最大HPの1/2を消費する。"""
    cost = max(1, ctx.attacker.max_hp // 2)
    battle.modify_hp(ctx.attacker, v=-cost, reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def テラバースト_modify_move_category(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テラバーストの分類（物理/特殊）を判定する。"""
    mon = ctx.attacker
    if mon.terastallized:
        atk = mon.ranked_stats["atk"]
        spa = mon.ranked_stats["spa"]
        value = "physical" if atk > spa else "special"
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
        battle.modify_stats(mon, {"atk": -1, "spa": -1}, source=mon)
    return HandlerReturn(value=value)


def デカハンマー_apply_reuse_block(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """デカハンマー: PP消費確定後に「デカハンマー」揮発状態を自分に付与する。

    count=2 で付与することで、ターン終了後（count: 2→1）も揮発が残り、
    次のターンの ON_MODIFY_COMMAND_OPTIONS で選択を制限できる。
    ターンT+1 の終了時（count: 1→0）に volatile_manager が自動解除する。
    """
    return apply_volatile_to_attacker(battle, ctx, value, volatile="デカハンマー", count=2)


def デスウイング_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """デスウイングの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.75)
    return HandlerReturn(value=value)


def でんきショック_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def でんじほう_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def とっしん_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/4)


def とどめばり_boost_attacker_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とどめばりの追加効果: この技で相手を倒すとこうげきランクが3段階上がる。"""
    if not ctx.defender.alive:
        battle.modify_stats(ctx.attacker, {"atk": 3}, source=ctx.attacker)
    return HandlerReturn(value=value)


def とびかかる_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def とびげり_crash(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とびげりが外れた場合の失敗反動ダメージ。自分の最大HPの1/2を受ける。"""
    battle.modify_hp(ctx.attacker, v=-max(1, ctx.attacker.max_hp // 2), reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def とびつく_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def とびはねる_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def とびひざげり_crash(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とびひざげりが外れた場合の失敗反動ダメージ。自分の最大HPの1/2を受ける。"""
    battle.modify_hp(ctx.attacker, v=-max(1, ctx.attacker.max_hp // 2), reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def _force_switch_next(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """攻撃技型の強制交代共通ロジック（次に控えているポケモンを選択）。

    きゅうばん・ねをはる等の無効化チェックを ON_TRY_BLOW 経由で行う。
    交代先は控えポケモンのうち最初のポケモン（次の控え）。
    控えポケモンが存在しない場合は交代処理をスキップする。
    """
    result = battle.events.emit(Event.ON_TRY_BLOW, ctx, True)
    if not result:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_IMMUNED,
            payload=FailureLogPayload(move=ctx.move.name)
        )
        return HandlerReturn(value=value)
    player = battle.get_player(ctx.defender)
    state = battle.player_states[player]
    commands = battle.command_manager.get_available_switch_commands(player)
    if commands:
        command = commands[0]
        battle.run_switch(player, state.team[command.index])
    return HandlerReturn(value=value)


def ともえなげ_force_switch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ともえなげ: ダメージ後に相手を強制交代させる（次に控えているポケモン）。"""
    return _force_switch_next(battle, ctx, value)


def トライアタック_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """トライアタックの追加効果: 20%の確率でまひ/やけど/こおりのいずれかを付与する。

    単一乱数で判定: r < base/3 → まひ、r < base*2/3 → やけど、r < base → こおり。
    """
    base = battle.resolve_secondary_chance(ctx, 0.2)
    r = battle.random.random()
    if r < base / 3:
        ailment = "まひ"
    elif r < base * 2 / 3:
        ailment = "やけど"
    elif r < base:
        ailment = "こおり"
    else:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.ailment_manager.apply(
        ctx.defender, ailment, source=ctx.attacker, ctx=ctx
    ))


def トロピカルキック_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def どくづき_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def どくどくのキバ_apply_toxic_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="もうどく", chance=0.5)


def どくばり_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def どくばりセンボン_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.5)


def ドラゴンダイブ_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def ドラゴンテール_force_switch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ドラゴンテール: ダメージ後に相手を強制交代させる（次に控えているポケモン）。"""
    return _force_switch_next(battle, ctx, value)


def ドラムアタック_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1})


def ドレインキッス_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ドレインキッスの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.75)
    return HandlerReturn(value=value)


def ドレインパンチ_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ドレインパンチの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def どろかけ_lower_acc(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1})


def どろばくだん_lower_acc(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1}, chance=0.3)


def どろぼう_steal_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """どろぼう・ほしがるのアイテム奪取効果。"""
    battle.item_manager.take_item(ctx.defender)
    return HandlerReturn(value=value)


def ナイトバースト_lower_acc(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1}, chance=0.4)


def なげつける_apply_item_effect(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なげつける: アイテムに応じた追加効果を命中時に適用する。

    対象のアイテムはこの時点ではまだ消費されていない（ON_MOVE_ENDで消費）。
    でんきだま → まひ、かえんだま → やけど、どくバリ → どく、どくどくだま → もうどく、
    メンタルハーブ → メロメロ・アンコール・いちゃもん・かなしばり・ちょうはつ・かいふくふうじを解除、
    ラムのみ → 状態異常・こんらんを解除。
    クラボのみ/カゴのみ/モモンのみ/チーゴのみ/ナナシのみ → 対応する状態異常を解除、
    キーのみ → こんらんを解除、ヒメリのみ → PPが0の技を回復、
    オレンのみ → HP10回復、オボンのみ → HP1/4回復、
    フィラ/ウイ/マゴ/バンジ/イアのみ → HP1/3回復＋性格によってはこんらん付与、
    チイラ/リュガ・アッキ/カムラ/ヤタピ/ズア・タラプのみ → 対応する能力ランク+1、
    サンのみ → きゅうしょアップ付与、スターのみ → ランダムな能力ランク+2、
    ミクルのみ → 次の技の命中率を1.2倍にする。
    """
    item_name = ctx.attacker.item.base_name
    if item_name == "でんきだま":
        battle.ailment_manager.apply(ctx.defender, "まひ", source=ctx.attacker, ctx=ctx)
    elif item_name == "かえんだま":
        battle.ailment_manager.apply(ctx.defender, "やけど", source=ctx.attacker, ctx=ctx)
    elif item_name == "どくバリ":
        battle.ailment_manager.apply(ctx.defender, "どく", source=ctx.attacker, ctx=ctx)
    elif item_name == "どくどくだま":
        battle.ailment_manager.apply(ctx.defender, "もうどく", source=ctx.attacker, ctx=ctx)
    elif item_name in ("おうじゃのしるし", "するどいキバ"):
        battle.volatile_manager.apply(ctx.defender, "ひるみ", source=ctx.attacker)
    elif item_name == "しろいハーブ":
        # 相手の下がった能力ランクを全て0に戻す（対象がしろいハーブを持っている訳ではないため
        # アイテムの発動宣言・消費は行わない）。
        defender = ctx.defender
        changed = {s: -v for s, v in defender.rank.items() if v < 0}
        if changed:
            for s in changed:
                defender.rank[s] = 0
            battle.add_event_log(
                defender, LogCode.STAT_CHANGED,
                payload=StatChangePayload(stats=changed, display_reason="しろいハーブ"),
            )
    elif item_name == "メンタルハーブ":
        defender = ctx.defender
        for volatile_name in ("メロメロ", "アンコール", "いちゃもん", "かなしばり", "ちょうはつ", "かいふくふうじ"):
            battle.volatile_manager.remove(defender, volatile_name)
    elif item_name == "ラムのみ":
        defender = ctx.defender
        battle.ailment_manager.remove(defender)
        battle.volatile_manager.remove(defender, "こんらん")
    elif item_name == "クラボのみ":
        defender = ctx.defender
        if defender.ailment.name == "まひ":
            battle.ailment_manager.remove(defender)
    elif item_name == "カゴのみ":
        defender = ctx.defender
        if defender.ailment.name == "ねむり":
            battle.ailment_manager.remove(defender)
    elif item_name == "モモンのみ":
        defender = ctx.defender
        if defender.ailment.name in ("どく", "もうどく"):
            battle.ailment_manager.remove(defender)
    elif item_name == "チーゴのみ":
        defender = ctx.defender
        if defender.ailment.name == "やけど":
            battle.ailment_manager.remove(defender)
    elif item_name == "ナナシのみ":
        defender = ctx.defender
        if defender.ailment.name == "こおり":
            battle.ailment_manager.remove(defender)
    elif item_name == "キーのみ":
        battle.volatile_manager.remove(ctx.defender, "こんらん")
    elif item_name == "ヒメリのみ":
        move = next((m for m in ctx.defender.moves if m.pp == 0), None)
        if move is not None:
            move.pp = min(10, move.data.pp)
    elif item_name == "オレンのみ":
        battle.modify_hp(ctx.defender, v=10)
    elif item_name == "オボンのみ":
        battle.modify_hp(ctx.defender, r=1/4)
    elif item_name == "フィラのみ":
        defender = ctx.defender
        battle.modify_hp(defender, r=1/3)
        if defender.nature in ("ずぶとい", "ひかえめ", "おだやか", "おくびょう"):
            battle.volatile_manager.apply_confusion(defender, source=ctx.attacker)
    elif item_name == "ウイのみ":
        defender = ctx.defender
        battle.modify_hp(defender, r=1/3)
        if defender.nature in ("いじっぱり", "わんぱく", "ようき", "しんちょう"):
            battle.volatile_manager.apply_confusion(defender, source=ctx.attacker)
    elif item_name == "マゴのみ":
        defender = ctx.defender
        battle.modify_hp(defender, r=1/3)
        if defender.nature in ("ゆうかん", "のんき", "れいせい", "むじゃき"):
            battle.volatile_manager.apply_confusion(defender, source=ctx.attacker)
    elif item_name == "バンジのみ":
        defender = ctx.defender
        battle.modify_hp(defender, r=1/3)
        if defender.nature in ("やんちゃ", "のうてんき", "うっかりや", "なまいき"):
            battle.volatile_manager.apply_confusion(defender, source=ctx.attacker)
    elif item_name == "イアのみ":
        defender = ctx.defender
        battle.modify_hp(defender, r=1/3)
        if defender.nature in ("さみしがり", "おっとり", "おとなしい", "せっかち"):
            battle.volatile_manager.apply_confusion(defender, source=ctx.attacker)
    elif item_name == "チイラのみ":
        battle.modify_stats(ctx.defender, {"atk": 1}, source=ctx.attacker)
    elif item_name in ("リュガのみ", "アッキのみ"):
        battle.modify_stats(ctx.defender, {"def": 1}, source=ctx.attacker)
    elif item_name == "カムラのみ":
        battle.modify_stats(ctx.defender, {"spe": 1}, source=ctx.attacker)
    elif item_name == "ヤタピのみ":
        battle.modify_stats(ctx.defender, {"spa": 1}, source=ctx.attacker)
    elif item_name in ("ズアのみ", "タラプのみ"):
        battle.modify_stats(ctx.defender, {"spd": 1}, source=ctx.attacker)
    elif item_name == "サンのみ":
        battle.volatile_manager.apply(ctx.defender, "きゅうしょアップ", count=2, source=ctx.attacker)
    elif item_name == "スターのみ":
        defender = ctx.defender
        candidates = [s for s in ("atk", "def", "spa", "spd", "spe") if defender.rank[s] < 6]
        if candidates:
            stat = battle.random.choice(candidates)
            battle.modify_stats(defender, {stat: 2}, source=ctx.attacker)
    elif item_name == "ミクルのみ":
        battle.volatile_manager.apply(ctx.defender, "めいちゅうアップ", source=ctx.attacker)
    return HandlerReturn(value=value)


def なげつける_check_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なげつける: 使用者のアイテムを確認し、威力を設定する。

    アイテムを持っていない場合、fling_power=0の対象外アイテムの場合、
    またはno_fling=Trueの投げられないアイテム（ジュエル等）の場合は失敗する。
    はっきんだまはギラティナ(アナザー/オリジン問わず)が使用した場合のみ失敗する
    （それ以外のポケモンが使用した場合は通常通り威力60で成功する）。
    ブーストエナジーはこだいかっせい/クォークチャージ持ちが使用した場合のみ失敗する
    （それ以外のポケモンが使用した場合は通常通り威力30で成功する）。
    成功した場合はアイテムのfling_powerをctx.move.powerに設定する。
    """
    attacker = ctx.attacker
    if not attacker.has_item():
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="なげつける_アイテムなし")
        )
        return HandlerReturn(value=False, stop_event=True)

    item_data = attacker.item.data
    if (
        item_data.fling_power == 0
        or item_data.no_fling
        or (attacker.item.base_name == "はっきんだま" and attacker.name.startswith("ギラティナ"))
        or (
            attacker.item.base_name == "ブーストエナジー"
            and attacker.ability.name in ("こだいかっせい", "クォークチャージ")
        )
    ):
        battle.add_event_log(
            attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="なげつける_対象外アイテム")
        )
        return HandlerReturn(value=False, stop_event=True)

    ctx.move.power = item_data.fling_power
    return HandlerReturn(value=value)


def なげつける_consume_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """なげつける: 命中可否に関わらず使用後にアイテムを消費する。"""
    battle.item_manager.remove_item(ctx.attacker, source=ctx.attacker)
    return HandlerReturn(value=value)


def にぎりつぶす_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """にぎりつぶす: 対象の残りHP / 最大HP の比率で威力を決定する（最大120）。

    威力 = max(1, floor(120 × 現在HP / 最大HP))
    """
    power = max(1, int(120 * ctx.defender.hp / ctx.defender.max_hp))
    return HandlerReturn(value=power * 4096)


def ニトロチャージ_boost_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": 1})


def ニードルアーム_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ねこだまし_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ")


def ねっさのあらし_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.2)


def ねっさのだいち_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ねっとう_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ねっぷう_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ねんりき_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねんりきの追加効果: 10%の確率で相手をこんらん状態にする。"""
    return apply_confusion_to_defender(battle, ctx, value, chance=0.1)


def のしかかり_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def ハイドロスチーム_power_modifier(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ハイドロスチーム: 晴れ下で水タイプ弱体化を受けず、代わりに1.5倍になる。

    通常、晴れ（にほんばれ・おおひでり）下では水タイプ技の威力が0.5倍になるが、
    ハイドロスチームはその弱体化を受けない。さらに晴れ下では1.5倍の威力になる。

    実装:
    攻撃側がばんのうがさを持つ場合はこの効果が発動しない（通常みず技と同じく0.5倍になる）。
    防御側がばんのうがさを持つ場合は天候フィールドハンドラ（はれ_power_modifier）が
    0.5倍を適用しないため、直接1.5倍（6144）を乗算する。
    防御側がばんのうがさを持たない場合はフィールドハンドラが先に0.5倍を適用しているため、
    3倍（12288）を乗算して最終的に1.5倍とする。
    """
    # 攻撃側がばんのうがさを持つ場合、この効果は発動しない
    if not battle.weather_for(ctx.attacker).sunny:
        return HandlerReturn(value=value)
    if not battle.weather_for(ctx.defender).sunny:
        # 防御側ばんのうがさあり: フィールドハンドラが0.5倍を未適用のため直接1.5倍を適用
        value = apply_fixed_modifier(value, 6144)
    else:
        # 防御側ばんのうがさなし: フィールドハンドラの0.5倍をキャンセルし1.5倍にするため3倍補正を適用
        value = apply_fixed_modifier(value, 12288)
    return HandlerReturn(value=value)


def はいよるいちげき_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1})


def はがねのつばさ_boost_defender_B(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1}, chance=0.1)


def はたきおとす_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """はたきおとすのアイテム所持時1.5倍補正。

    奪う/落とすことができないアイテム（だいこんごうだま等の専用道具）の場合は補正なし。
    """
    if (
        ctx.defender.has_item()
        and battle.item_manager.can_change_item(ctx.defender, source=ctx.attacker)
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def level_fixed_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """使用者レベルと同値の固定ダメージを計算する。"""
    return HandlerReturn(value=ctx.attacker.level)

def apply_bind_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """バインド系技: ランダムターン数でバインド状態を付与する。ねばりのかぎづめで7ターン固定。

    しめつけバンドによるダメージ倍率は付与時（攻撃側の所持アイテム）で確定し、
    以降のアイテム変化（入手・喪失）による増減はない。
    """
    count = battle.query.get_volatile_duration(ctx, "バインド", battle.random.randint(4, 5))
    bind_damage_ratio = battle.events.emit(Event.ON_MODIFY_BIND_DAMAGE, ctx, 1/8)
    battle.volatile_manager.apply(
        ctx.defender, "バインド", count=count, source=ctx.attacker, bind_damage_ratio=bind_damage_ratio
    )
    return HandlerReturn(value=value)


def はたきおとす_remove_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はたきおとすのアイテム除去効果。"""
    battle.item_manager.remove_item(target=ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def はっけい_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def はめつのねがい_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はめつのねがいの溜め処理。

    相手側にまだフィールドが存在しない場合、ダメージを計算して「はめつのねがい」
    サイドフィールドを相手陣営に設置し、即時攻撃を抑制する。
    すでに存在する場合は通過して ON_TRY_MOVE_1 の失敗チェックに委ねる。
    """
    foe_side = battle.get_side(ctx.defender)
    field = foe_side.get("はめつのねがい")
    if not field.is_active:
        damage = battle.roll_damage(ctx.attacker, ctx.defender, ctx.move)
        foe_side.activate("はめつのねがい", 2)
        field.damage = damage
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はめつのねがい_fail_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はめつのねがいの失敗チェック: 相手陣営にすでに「はめつのねがい」が存在する場合に失敗する。

    ON_MOVE_CHARGE ですでに存在する場合のみ ON_TRY_MOVE_1 へ流れるため、
    このハンドラはほぼ常に失敗を返す。
    """
    foe_side = battle.get_side(ctx.defender)
    if foe_side.get("はめつのねがい").is_active:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="はめつのねがい"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はめつのひかり_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/2)


def はやてがえし_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ")


def _はやてがえし_can_apply(battle: Battle, ctx: AttackContext) -> bool:
    """はやてがえしの発動条件を判定する。

    相手が未行動かつ優先攻撃技を選択している時のみ成功する。
    """
    def_player = battle.get_player(ctx.defender)
    def_state = battle.player_states[def_player]

    # 相手が既に行動済み（予約コマンドが消費済み）なら失敗。
    if not def_state.command_reserved():
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


def はやてがえし_try_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はやてがえしの発動条件を判定する。

    相手が未行動かつ優先攻撃技を選択している時のみ成功する。
    """
    if not _はやてがえし_can_apply(battle, ctx):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="はやてがえし")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def はるのあらし_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1}, chance=0.3)


def ハートスタンプ_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ハードプレス_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ハードプレス: 対象の残りHP / 最大HP の比率で威力を決定する（最大100）。

    威力 = max(1, floor(100 × 現在HP / 最大HP))
    """
    power = max(1, int(100 * ctx.defender.hp / ctx.defender.max_hp))
    return HandlerReturn(value=power * 4096)


def ハードローラー_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ばかぢから_lower_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": -1, "def": -1})


def ばくれつパンチ_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ばくれつパンチの追加効果: 相手をこんらん状態にする（確率100%）。"""
    return apply_confusion_to_defender(battle, ctx, value)


def バブルこうせん_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1}, chance=0.1)


def バリアーラッシュ_boost_defender_B(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 1})


def バークアウト_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1})


def バーンアクセル_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def パラボラチャージ_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """パラボラチャージの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def ひけん・ちえなみ_set_spikes(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひけん・ちえなみ: 命中後、相手陣営に「まきびし」を1層設置する（最大3層）。"""
    side = battle.get_side(ctx.defender)
    side.activate("まきびし", 1)
    return HandlerReturn(value=value)


def ひっさつまえば_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.1)


def _weight_ratio_to_power(attacker_weight: float, defender_weight: float) -> int:
    """体重比率（自分 / 相手）から威力を算出する共通関数。

    相手の体重が自分の 1/5 以下（比率 5以上）: 120
    1/4 以下（比率 4以上5未満）: 100
    1/3 以下（比率 3以上4未満）: 80
    1/2 以下（比率 2以上3未満）: 60
    1/2 超（比率 2未満）: 40
    """
    if defender_weight <= 0:
        return 40
    ratio = attacker_weight / defender_weight
    if ratio >= 5:
        return 120
    elif ratio >= 4:
        return 100
    elif ratio >= 3:
        return 80
    elif ratio >= 2:
        return 60
    else:
        return 40


def ひのこ_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ひゃっきやこう_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ひゃっきやこう_double_power_when_ailment(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひゃっきやこう: 相手が状態異常のとき威力が2倍になる。"""
    if ctx.defender.ailment.is_active:
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ひやみず_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def ひょうざんおろし_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ヒートスタンプ_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ヒートスタンプ: 自分の体重 / 相手の体重 の比率で威力を決定する。

    相手がちいさくなる状態の場合は体重比率計算をスキップし、
    minimize ラベルの共通処理（威力2倍）のみが適用される。
    """
    if ctx.defender.has_volatile("ちいさくなる"):
        return HandlerReturn(value=value)
    return HandlerReturn(value=_weight_ratio_to_power(ctx.attacker.weight, ctx.defender.weight) * 4096)


def ビックリヘッド_pay_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ビックリヘッド: 使用前に最大HPの1/2を消費する。"""
    cost = max(1, ctx.attacker.max_hp // 2)
    battle.modify_hp(ctx.attacker, v=-cost, reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def びりびりちくちく_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ピヨピヨパンチ_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ピヨピヨパンチの追加効果: 20%の確率で相手をこんらん状態にする。"""
    return apply_confusion_to_defender(battle, ctx, value, chance=0.2)


def _ふいうち_can_apply(battle: Battle, ctx: AttackContext) -> bool:
    """ふいうちの発動条件を判定する。

    対象が未行動かつ攻撃技を選択している時のみ成功する。
    """
    def_player = battle.get_player(ctx.defender)
    def_state = battle.player_states[def_player]

    # 対象がすでに行動済み（コマンドが消費済み）なら失敗。
    if not def_state.command_reserved():
        return False

    defender_command = def_state.next_command
    defender_move = battle.command_to_move(def_player, defender_command)

    # 変化技（攻撃技でない）を選択している場合は失敗。
    if not defender_move.is_attack:
        return False

    return True


def ふいうち_try_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふいうちの発動条件を判定する。

    対象が未行動かつ攻撃技を選択している時のみ成功する。
    交代・テラスタル・どうぐ使用など技以外の行動を選択している場合も失敗する。
    """
    if not _ふいうち_can_apply(battle, ctx):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ふいうち")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def フェイタルクロー_apply_ailment_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フェイタルクローの追加効果: 単一乱数で どく/まひ/ねむり のいずれかを付与する。

    r < base/3 → どく、r < base*2/3 → まひ、r < base → ねむり（チャンピオンズ: 確率0.5）。
    """
    base = battle.resolve_secondary_chance(ctx, 0.5)
    r = battle.random.random()
    if r < base / 3:
        ailment = "どく"
    elif r < base * 2 / 3:
        ailment = "まひ"
    elif r < base:
        ailment = "ねむり"
    else:
        return HandlerReturn(value=value)
    return HandlerReturn(value=battle.ailment_manager.apply(
        ctx.defender, ailment, source=ctx.attacker, ctx=ctx
    ))


_FAINT_REMOVE_VOLATILES: tuple[str, ...] = (
    "まもる", "みきり", "トーチカ", "キングシールド",
    "ニードルガード", "スレッドトラップ", "かえんのまもり",
)


def フェイント_remove_protect(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フェイントの追加効果: 相手のまもる系揮発性状態を解除する。"""
    defender = ctx.defender
    for volatile in _FAINT_REMOVE_VOLATILES:
        if defender.has_volatile(volatile):
            battle.volatile_manager.remove(defender, volatile)
            battle.add_event_log(
                defender,
                LogCode.VOLATILE_REMOVED,
                payload=VolatilePayload(volatile=volatile, display_reason="フェイント")
            )
    return HandlerReturn(value=value)


def フォトンゲイザー_disable_defender_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フォトンゲイザー: 攻撃直前に相手の特性を無効化する（かたやぶりと同様の対象特性）。"""
    mon = ctx.defender
    if mon.ability.has_flag("mold_breaker_ignorable"):
        battle.add_ability_disabled_reason(mon, "フォトンゲイザー")
    return HandlerReturn(value=value)


def フォトンゲイザー_modify_move_category(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フォトンゲイザー: 補正込みAがCより高い場合は物理技として計算する。"""
    mon = ctx.attacker
    if mon.ranked_stats["atk"] > mon.ranked_stats["spa"]:
        return HandlerReturn(value="physical")
    return HandlerReturn(value=value)


def フォトンゲイザー_restore_defender_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フォトンゲイザー: 攻撃終了後に相手の特性の無効化を解除する。"""
    battle.remove_ability_disabled_reason(ctx.defender, "フォトンゲイザー")
    return HandlerReturn(value=value)


def ふくろだたき_calc_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふくろだたき: 各ヒットの威力 = 使用者の基礎こうげき種族値 / 10 + 5。"""
    power = ctx.attacker.data.base[1] // 10 + 5
    return HandlerReturn(value=power * 4096)


def ふくろだたき_hit_count(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふくろだたき: ひんしや状態異常でない選出ポケモン数がヒット回数。"""
    player = battle.get_player(ctx.attacker)
    state = battle.player_states[player]
    count = sum(1 for mon in state.selection if mon.alive and not mon.ailment.is_active)
    return HandlerReturn(value=max(1, count))


def ふしょくガス_remove_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふしょくガスのアイテム除去効果。"""
    battle.item_manager.remove_item(target=ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def ふぶき_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふぶき: ゆき状態の時は必中になる補正。"""
    weather = battle.weather_manager.current.name
    if weather == "ゆき":
        return HandlerReturn(value=None)  # 必中
    return HandlerReturn(value=value)


def ふぶき_apply_freeze_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def ふみつけ_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def フライングプレス_add_flying_type(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """フライングプレス: かくとうタイプに加えてひこうタイプとしても相性計算する。

    damage_calculator.py がすでにかくとうタイプ相性を value に計算済み。
    ここでひこうタイプの相性を追加で掛け算することで複合タイプ判定を実現する。
    """
    flying_chart = TYPE_MODIFIER.get("ひこう", {})
    for def_type in ctx.defender.types:
        rate = flying_chart.get(def_type, 1.0)
        value = int(value * rate)
    return HandlerReturn(value=value)


def フリーズドライ_apply_freeze_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def フリーズドライ_water_effectiveness(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """フリーズドライ: みずタイプに対して効果抜群（2倍）になる。
    こおりタイプはみずに0.5倍のため、最終2倍になるよう4倍補正（16384）をかける。
    """
    if "みず" in ctx.defender.types:
        value = apply_fixed_modifier(value, 16384)
    return HandlerReturn(value=value)


def フリーズボルト_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def フルールカノン_sharply_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": -2})


def フレアソング_boost_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 1})


def フレアドライブ_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def フレアドライブ_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/3)


def ふわふわフォール_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ふんえん_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.3)


def ふんか_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ふんか: 自分のHP比率に比例して威力が決まる（最大150）。しおふきと同計算。"""
    modifier = int(ctx.attacker.hp * 4096 / ctx.attacker.max_hp)
    modifier = max(1, modifier)  # 威力が最低1になるよう保証
    return HandlerReturn(value=modifier)


def ふんどのこぶし_calc_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふんどのこぶし: 倒れた選出ポケモン数だけ威力が+50される。"""
    player = battle.get_player(ctx.attacker)
    state = battle.player_states[player]
    fainted = sum(1 for mon in state.selection if not mon.alive)
    return HandlerReturn(value=value * (1 + fainted))


def Vジェネレート_lower_attacker_def_spd_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1, "spd": -1, "spe": -1})


def ぶきみなじゅもん_reduce_defender_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ぶきみなじゅもん: 相手の最後に使った技のPPを3減らす。"""
    mon = ctx.defender
    if mon.executed_move is not None:
        mon.executed_move.modify_pp(-3)
    return HandlerReturn(value=value)


def ぶちかまし_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": -1, "spd": -1})


def ブラッドムーン_apply_reuse_block(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ブラッドムーン: PP消費確定後に「ブラッドムーン」揮発状態を自分に付与する。

    count=2 で付与することで、ターン終了後（count: 2→1）も揮発が残り、
    次のターンの ON_MODIFY_COMMAND_OPTIONS で選択を制限できる。
    ターンT+1 の終了時（count: 1→0）に volatile_manager が自動解除する。
    """
    return apply_volatile_to_attacker(battle, ctx, value, volatile="ブラッドムーン", count=2)


def ブレイククロー_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1}, chance=0.5)


def ブレイズキック_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ブレイブバード_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/3)


def プレゼント_apply_heal(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """プレゼントの回復効果: 相手のHPを1/4回復する。"""
    if ctx.move.power:
        return HandlerReturn(value=value)
    battle.modify_hp(ctx.defender, r=0.25)
    return HandlerReturn(value=0)


def プレゼント_check_heal_full(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """プレゼントの回復効果: 相手のHPが満タンの場合は失敗する。"""
    if ctx.move.power:
        return HandlerReturn(value=value)
    if ctx.defender.hp >= ctx.defender.max_hp:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="プレゼント_HP満タン")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def プレゼント_roll_outcome(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """プレゼントのランダム効果を決定する。

    40%: 威力40の攻撃
    30%: 威力80の攻撃
    10%: 威力120の攻撃
    20%: 相手のHPを1/4回復（power=0のまま）
    """
    roll = battle.random.random()
    if roll < 0.40:
        ctx.move.power = 40
    elif roll < 0.70:
        ctx.move.power = 80
    elif roll < 0.80:
        ctx.move.power = 120
    # 残り20%: 回復。powerは0のまま
    return HandlerReturn(value=value)


def ヘドロウェーブ_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.1)


def ヘドロこうげき_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def ヘドロばくだん_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def ヘビーボンバー_calc_power(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ヘビーボンバー: 自分の体重 / 相手の体重 の比率で威力を決定する。

    相手がちいさくなる状態の場合は体重比率計算をスキップし、
    minimize ラベルの共通処理（威力2倍）のみが適用される。
    """
    if ctx.defender.has_volatile("ちいさくなる"):
        return HandlerReturn(value=value)
    return HandlerReturn(value=_weight_ratio_to_power(ctx.attacker.weight, ctx.defender.weight) * 4096)


def ベノムショック_double_power_when_poisoned(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ベノムショック: 対象がどく/もうどく状態のとき威力が2倍になる。"""
    if ctx.defender.ailment.name in ("どく", "もうどく"):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def ホイールスピン_sharply_lower_attacker_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spe": -2})


def ほうでん_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def ほうふく_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほうふくの使用可否を判定する。

    そのターンダメージを受けていない場合は失敗する。
    """
    if ctx.attacker.last_damage_received <= 0:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ほうふく")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ほうふく_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほうふくの固定ダメージを計算する（最後に受けたダメージ × 1.5、切り捨て）。"""
    return HandlerReturn(value=int(ctx.attacker.last_damage_received * 1.5))


def ほっぺすりすり_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ")


def ホネこんぼう_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.1)


def ほのおのキバ_apply_flinch_or_burn(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ほのおのキバの追加効果: 5%でやけど、5%でひるみを付与する。

    単一乱数で判定: r < base*0.5 → やけど、r < base → ひるみ。
    """
    base = battle.resolve_secondary_chance(ctx, 0.1)
    r = battle.random.random()
    if r < base * 0.5:
        return HandlerReturn(value=battle.ailment_manager.apply(
            ctx.defender, "やけど", source=ctx.attacker, ctx=ctx
        ))
    if r < base:
        return HandlerReturn(value=battle.volatile_manager.apply(
            ctx.defender, "ひるみ", source=ctx.attacker
        ))
    return HandlerReturn(value=value)


def ほのおのパンチ_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど", chance=0.1)


def ほのおのまい_boost_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": 1}, chance=0.5)


def ほのおのムチ_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1})


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
    return apply_confusion_to_defender(battle, ctx, value, chance=0.3)


def ボルテッカー_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.1)


def ボルテッカー_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/3)


def ポイズンアクセル_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.3)


def ポイズンテール_apply_poison_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="どく", chance=0.1)


def ポルターガイスト_check_item(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ポルターガイストの使用条件チェック: 相手がアイテムを持っていない場合は失敗する。"""
    if not ctx.defender.has_item():
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ポルターガイスト_アイテムなし")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def マジカルアクセル_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """マジカルアクセルの追加効果: 30%の確率で相手をこんらん状態にする。"""
    return apply_confusion_to_defender(battle, ctx, value, chance=0.3)


def マジカルフレイム_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1})


def マッドショット_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1})


def まわしげり_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.3)


def ミストバースト_pay_hp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミストバースト: 使用前に現在HPを全消費する。"""
    battle.modify_hp(ctx.attacker, v=-ctx.attacker.hp, reason="self_cost", source=ctx.attacker)
    return HandlerReturn(value=value)


def ミストボール_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1}, chance=0.5)


def みずあめボム_apply_volatile_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みずあめボムの追加効果: 100%の確率で相手をあめまみれ揮発状態（3ターン）にする。"""
    return apply_volatile_to_defender(battle, ctx, value, volatile="あめまみれ", count=3)


def みずのはどう_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みずのはどうの追加効果: 20%の確率で相手をこんらん状態にする。"""
    return apply_confusion_to_defender(battle, ctx, value, chance=0.2)


def みねうち_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みねうち: このわざで相手を倒すことはできない。相手のHPを必ず1以上残す。"""
    if ctx.defender.hp <= 1:
        return HandlerReturn(value=0)
    return HandlerReturn(value=min(value, ctx.defender.hp - 1))


def みらいよち_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みらいよちの溜め処理。

    相手側にまだフィールドが存在しない場合、ダメージを計算して「みらいよち」
    サイドフィールドを相手陣営に設置し、即時攻撃を抑制する。
    すでに存在する場合は通過して ON_TRY_MOVE_1 の失敗チェックに委ねる。
    """
    foe_side = battle.get_side(ctx.defender)
    field = foe_side.get("みらいよち")
    if not field.is_active:
        damage = battle.roll_damage(ctx.attacker, ctx.defender, ctx.move)
        foe_side.activate("みらいよち", 2)
        field.damage = damage
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def みらいよち_fail_check(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みらいよちの失敗チェック: 相手陣営にすでに「みらいよち」が存在する場合に失敗する。

    ON_MOVE_CHARGE ですでに存在する場合のみ ON_TRY_MOVE_1 へ流れるため、
    このハンドラはほぼ常に失敗を返す。
    """
    foe_side = battle.get_side(ctx.defender)
    if foe_side.get("みらいよち").is_active:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="みらいよち"),
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ミラーコート_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミラーコートの使用可否を判定する。

    そのターン相手から特殊ダメージを受けていない場合は失敗する。
    """
    if ctx.attacker.last_special_damage_received <= 0:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="ミラーコート")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ミラーコート_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミラーコートの固定ダメージを計算する（特殊被弾ダメージ × 2）。"""
    return HandlerReturn(value=ctx.attacker.last_special_damage_received * 2)


def ミラーショット_lower_acc(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"accuracy": -1}, chance=0.3)


def みわくのボイス_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """みわくのボイスの追加効果: そのターンにランクが上がった相手をこんらん状態にする。"""
    if not ctx.defender.stat_raised_this_turn:
        return HandlerReturn(value=value)
    return apply_confusion_to_defender(battle, ctx, value)


def むしくい_steal_and_use_berry(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """むしくい・ついばむ: 相手のバトルに効果のあるきのみを奪って自分が消費する。

    take_item はねんちゃくチェックを内包し、attacker がアイテムを
    持っている場合は失敗して何もしない。
    """
    defender = ctx.defender
    attacker = ctx.attacker
    if not defender.has_item() or not defender.item.is_berry():
        return HandlerReturn(value=value)
    # take_item でdefenderのきのみをattackerに移す（ねんちゃく等で失敗する場合あり）
    if not battle.item_manager.take_item(defender):
        return HandlerReturn(value=value)
    # attackerがきのみを得たので効果を発動して消費する
    battle.item_manager.force_trigger_berry(attacker)
    return HandlerReturn(value=value)


def むしのさざめき_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.1)


def むしのていこう_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1})


def むねんのつるぎ_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def ムーンフォース_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spa": -1}, chance=0.3)


def メガドレイン_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def めざめるダンス_modify_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """めざめるダンス: 使用者の現在のタイプ1と同じタイプになる。

    テラスタル時はテラスタイプ、ステラテラスタル時は元のタイプ1を使用する。
    """
    types = ctx.attacker.types
    if types:
        return HandlerReturn(value=types[0])
    return HandlerReturn(value=value)


def メタルクロー_boost_attacker_A(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": 1}, chance=0.1)


def メタルバースト_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メタルバーストの使用可否を判定する。

    そのターンダメージを受けていない場合は失敗する。
    """
    if ctx.attacker.last_damage_received <= 0:
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="メタルバースト")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def メタルバースト_modify_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メタルバーストの固定ダメージを計算する（最後に受けたダメージ × 1.5、切り捨て）。"""
    return HandlerReturn(value=int(ctx.attacker.last_damage_received * 1.5))


def メテオドライブ_disable_defender_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メテオドライブ: 攻撃直前に相手の特性を無効化する（かたやぶりと同様の対象特性）。"""
    mon = ctx.defender
    if mon.ability.has_flag("mold_breaker_ignorable"):
        battle.add_ability_disabled_reason(mon, "メテオドライブ")
    return HandlerReturn(value=value)


def メテオドライブ_restore_defender_ability(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メテオドライブ: 攻撃終了後に相手の特性の無効化を解除する。"""
    battle.remove_ability_disabled_reason(ctx.defender, "メテオドライブ")
    return HandlerReturn(value=value)


def メテオビーム_boost_spa(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メテオビーム: とくこうを1段階上げる（追加効果ではないため必ず発動）。

    仕様:
    - ちからずくの追加効果ではないため、battle.modify_stats を直接呼ぶ。
    - パワフルハーブ使用時もこのハンドラ（priority=50）が先に実行されるため、
      とくこう上昇は必ず発動する。
    """
    battle.modify_stats(ctx.attacker, {"spa": 1}, source=ctx.attacker)
    return HandlerReturn(value=value)


def メテオビーム_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メテオビーム: 1ターン目に溜め状態に移行、2ターン目に攻撃する。

    仕様:
    - 揮発状態なし（1ターン目）: 揮発状態を付与して攻撃を停止する。
    - 揮発状態あり（2ターン目）: そのまま通過して攻撃に進む。
    - とくこう上昇はメテオビーム_boost_spa（priority=50）で先に処理される。
    - パワフルハーブ（priority=100）が stop_event=True を返す場合、
      揮発付与後にパワフルハーブが発動して溜めをスキップし即攻撃となる。
    """
    attacker = ctx.attacker
    if not attacker.has_volatile("メテオビーム"):
        battle.volatile_manager.apply(attacker, "メテオビーム", count=1, source=attacker)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def もえあがるいかり_apply_flinch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_volatile_to_defender(battle, ctx, value, volatile="ひるみ", chance=0.2)


def もえつきる_fail_if_no_fire_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もえつきる: ほのおタイプを持たない場合に失敗させる。"""
    if not ctx.attacker.has_type("ほのお"):
        battle.add_event_log(
            ctx.attacker, LogCode.MOVE_FAILED,
            payload=FailureLogPayload(move=ctx.move.name, display_reason="もえつきる_ほのおタイプなし")
        )
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def もえつきる_remove_fire_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もえつきる: 命中後に自分のほのおタイプを除去する。

    removed_types に追加することで、交代するまでほのおタイプを持たない状態になる。
    """
    mon = ctx.attacker
    if "ほのお" not in mon.removed_types:
        mon.removed_types.append("ほのお")
    return HandlerReturn(value=value)


def もえつきる_thaw_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """もえつきる: こおり状態でも使用可能にし、こおりを解凍する。

    こおり_action (priority=10) より先に発火させる (priority=5) ことで、
    ailment が除去された状態で こおり_action の validity check が走り、
    こおり_action がスキップされる。
    """
    mon = ctx.attacker
    if mon.ailment.name == "こおり":
        battle.ailment_manager.remove(mon)
    return HandlerReturn(value=value)


def もろはのずつき_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/2)


def やきつくす_remove_berry(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """やきつくすのきのみ焼却効果。"""
    if ctx.defender.item.is_berry():
        battle.item_manager.remove_item(target=ctx.defender, source=ctx.attacker)
    return HandlerReturn(value=value)


def やけっぱち_calc_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """やけっぱち: 自分が前のターンで動けなかったとき、または使った技が失敗していたとき、威力が2倍になる。"""
    if ctx.attacker.failed_or_immobile_last_turn:
        return HandlerReturn(value=apply_fixed_modifier(value, 8192))
    return HandlerReturn(value=value)


def ゆきなだれ_calc_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆきなだれ: そのターンに相手からダメージを受けていた場合、威力が2倍になる。"""
    attacker = ctx.attacker
    if (attacker.last_physical_damage_received > 0
            or attacker.last_special_damage_received > 0):
        return HandlerReturn(value=apply_fixed_modifier(value, 8192))
    return HandlerReturn(value=value)


def ゆめくい_drain(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ゆめくいの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def ようかいえき_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.1)


def らいげき_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.2)


def ライジングボルト_calc_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ライジングボルト: エレキフィールド中かつ相手が接地している場合、威力が2倍になる。"""
    if (
        battle.terrain.name == "エレキフィールド"
        and not battle.query.is_floating(ctx.defender)
    ):
        return HandlerReturn(value=apply_fixed_modifier(value, 8192))
    return HandlerReturn(value=value)


def らいめいげり_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -1})


def ラスターカノン_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.1)


def ラスターパージ_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1}, chance=0.5)


def リチャージ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リチャージ系技: 命中後に使用者へ「リチャージ」volatile を付与する。

    がんせきほう・ギガインパクト・はかいこうせん・ブラストバーン・
    ハードプラント・ハイドロカノンで共用。
    """
    return apply_volatile_to_attacker(battle, ctx, value, volatile="リチャージ")


def りゅうせいぐん_sharply_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": -2})


def りゅうのいぶき_apply_paralysis_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="まひ", chance=0.3)


def りんごさん_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -1})


def リーフストーム_sharply_lower_spa_C(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"spa": -2})


def ルミナコリジョン_sharply_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2})


def レイジングブル_break_screens(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レイジングブル: 相手側のリフレクター・ひかりのかべ・オーロラベールを解除する。

    壁解除は追加効果ではないため、りんぷん・おんみつマント・ちからずくの対象外。
    技が無効化されなかった場合（ON_HITに到達した場合）のみ発動する。
    """
    defender_side = battle.get_side(ctx.defender)
    for wall in ("リフレクター", "ひかりのかべ", "オーロラベール"):
        defender_side.deactivate(wall)
    return HandlerReturn(value=value)


# フォルム名 → 技タイプの対応表
_RAGING_BULL_TYPE_MAP: dict[str, str] = {
    "ケンタロス":            "ノーマル",
    "ケンタロス(パルデア闘)": "かくとう",
    "ケンタロス(パルデア炎)": "ほのお",
    "ケンタロス(パルデア水)": "みず",
}


def レイジングブル_modify_move_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レイジングブルのタイプをケンタロスのフォルムで決定する。

    ケンタロス以外が使用した場合はノーマルタイプのまま変化しない。
    """
    move_type = _RAGING_BULL_TYPE_MAP.get(ctx.attacker.name)
    if move_type is not None:
        value = move_type
    return HandlerReturn(value=value)


def れいとうパンチ_apply_freeze_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def れいとうビーム_apply_freeze_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="こおり", chance=0.1)


def れんごく_apply_burn_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return apply_ailment_to_defender(battle, ctx, value, ailment="やけど")


def れんぞくぎり_apply_count(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """れんぞくぎり: 命中後に連続使用カウントを増加する。

    揮発状態がなければ count=1 で初回付与し、あれば count を最大 3 まで増加する。
    """
    mon = ctx.attacker
    if "れんぞくぎり" in mon.volatiles:
        v = mon.volatiles["れんぞくぎり"]
        if v.count is not None:
            v.count = min(v.count + 1, 3)
        return HandlerReturn(value=value)
    # 初回: count=1 で volatile を付与
    return apply_volatile_to_attacker(battle, ctx, value, volatile="れんぞくぎり", count=1)


def れんぞくぎり_calc_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """れんぞくぎり: 連続使用回数に応じて威力を倍増する（最大4倍=160）。

    count=1 → 2倍(80), count=2以上 → 4倍(160)。
    ON_CALC_POWER_MODIFIER は 4096 = 1.0 倍基準。
    """
    mon = ctx.attacker
    if "れんぞくぎり" in mon.volatiles:
        count = mon.volatiles["れんぞくぎり"].count or 0
        multiplier = 4096 * (2 ** min(count, 2))
        return HandlerReturn(value=apply_fixed_modifier(value, multiplier))
    return HandlerReturn(value=value)


def れんぞくぎり_reset_on_miss(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """れんぞくぎり: 技が外れた場合、連続使用カウントをリセットする（揮発状態を解除する）。"""
    battle.volatile_manager.remove(ctx.attacker, "れんぞくぎり")
    return HandlerReturn(value=value)


def ロッククライム_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ロッククライムの追加効果: 20%の確率で相手をこんらん状態にする。"""
    return apply_confusion_to_defender(battle, ctx, value, chance=0.2)


def ローキック_lower_defender_spd(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spe": -1})


def ワイドフォース_calc_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ワイドフォース: サイコフィールド中かつ自分が接地している場合、威力が1.5倍になる。

    サイコフィールド自体の1.3倍効果はフィールドハンドラが担当するため、
    このハンドラは1.5倍のみ担当する。
    """
    if (
        battle.terrain.name == "サイコフィールド"
        and not battle.query.is_floating(ctx.attacker)
    ):
        return HandlerReturn(value=apply_fixed_modifier(value, 6144))
    return HandlerReturn(value=value)


def ワイドブレイカー_lower_defender_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"atk": -1})


def ワイルドボルト_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _recoil(battle, ctx, value, 1/4)


def わるあがき_self_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=battle.modify_hp(ctx.attacker, r=-1/4, reason="recoil", source=ctx.attacker))


def ワンダースチーム_apply_confusion_to_defender(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ワンダースチームの追加効果: 20%の確率で相手をこんらん状態にする。"""
    return apply_confusion_to_defender(battle, ctx, value, chance=0.2)
