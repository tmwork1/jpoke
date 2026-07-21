"""致死率計算ハンドラの実装。

各関数は StateDist を受け取り、効果を適用した StateDist を返す。
data/item.py・data/ability.py などで LethalHandler として登録する。
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from jpoke.core import Battle, LethalContext, StateDist
    from jpoke.model import Pokemon

from collections import defaultdict
from jpoke.utils.lethal_dist import State, add_dist, to_dist
from jpoke.utils.math import clamp_stats

def _damage(hp_dist: StateDist, v: int) -> StateDist:
    """全状態に固定ダメージを与える（HP は 0 未満にならない）。"""
    new_dist: StateDist = defaultdict(int)
    for state, freq in hp_dist.items():
        new_state = State(
            max(0, state.value - v),
            ability_enabled=state.ability_enabled,
            item_enabled=state.item_enabled,
            attacker_boosts=state.attacker_boosts,
            attacker_ailment=state.attacker_ailment,
            defender_boosts=state.defender_boosts,
            defender_ailment=state.defender_ailment,
        )
        new_dist[new_state] += freq
    return dict(new_dist)

def _heal(hp_dist: StateDist,
          target: Pokemon,
          v: int = 0,
          r: float = 0.) -> StateDist:
    """全状態に無条件で回復を適用する（たべのこしなど）。

    r が指定された場合は target.max_hp * r（切り捨て、最低1）を回復量とする。
    v と r を両方指定した場合は r が優先される。
    target がかいふくふうじ状態の場合は回復せずそのまま返す
    （いたみわけ・さいせいりょくはこのヘルパーを経由しないため対象外）。
    """
    if "かいふくふうじ" in target.volatiles:
        return hp_dist
    max_hp = target.max_hp
    if r:
        heal = max(1, int(max_hp * r))
    else:
        heal = v
    return add_dist(hp_dist, heal, maximum=max_hp)

def _heal_at_pinch(hp_dist: StateDist,
                   target: Pokemon,
                   v: int = 0,
                   r: float = 0.,
                   threshold_rate: float = 0,
                   heal_with: Literal["ability", "item"] | None = None,
                   consume: bool = True) -> StateDist:
    """HP が閾値以下の状態にのみ回復を適用する（きのみ系アイテムなど）。

    Args:
        hp_dist: 入力 HP 分布
        target: 回復対象ポケモン（max_hp 参照に使用）
        v: 固定回復量（r が 0 の場合に使用）
        r: max_hp に対する回復割合
        threshold_rate: HP が max_hp × threshold_rate 以下の状態のみ回復する
        heal_with: 回復手段（"ability" / "item" / None）。対応フラグが False の状態は回復しない
        consume: True の場合、回復後に heal_with に対応するフラグを False にする

    target がかいふくふうじ状態の場合は回復せずそのまま返す。
    """
    if "かいふくふうじ" in target.volatiles:
        return hp_dist
    max_hp = target.max_hp
    if r:
        heal = max(1, int(max_hp * r))
    else:
        heal = v
    threshold = max(1, int(max_hp * threshold_rate))
    new_dist: StateDist = defaultdict(int)

    for state, freq in hp_dist.items():
        # 回復手段が無効化されている状態は回復せずそのまま維持
        if heal_with == "ability" and not state.ability_enabled:
            new_dist[state] += freq
            continue
        if heal_with == "item" and not state.item_enabled:
            new_dist[state] += freq
            continue

        # HP が閾値を超えている場合は回復しない
        if state.value > threshold:
            new_dist[state] += freq
            continue

        # HP が閾値以下の場合は回復し、消耗フラグを更新する
        keep_ability_enabled = not (heal_with == "ability" and consume)
        keep_item_enabled = not (heal_with == "item" and consume)
        new_state = State(
            min(state.value + heal, max_hp),
            ability_enabled=state.ability_enabled and keep_ability_enabled,
            item_enabled=state.item_enabled and keep_item_enabled,
            attacker_boosts=state.attacker_boosts,
            attacker_ailment=state.attacker_ailment,
            defender_boosts=state.defender_boosts,
            defender_ailment=state.defender_ailment,
        )
        new_dist[new_state] += freq

    return new_dist

def _apply_bind(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """バインド状態を付与する（未付与の場合のみ）。バインドダメージはON_TURN_ENDで処理される。"""
    if "バインド" not in ctx.defender.volatiles:
        from jpoke.model.volatile import Volatile
        ctx.defender.volatiles["バインド"] = Volatile("バインド", count=4)
    return hp_dist

def _survive_at_full_hp(hp_dist: StateDist, consume: Literal["ability", "item"]) -> StateDist:
    """満タン枝でHPが0になった状態をHP1に補正する（がんじょう/きあいのタスキ共通処理）。

    呼び出し側で hp_dist は「満タン枝のみ・ダメージ適用後」に絞られているため、
    ここでは value == 0 かどうかだけを見ればよい。
    consume="item" のときは補正と同時に item_enabled を False にする（きあいのタスキの消費）。
    consume="ability" のときは何度でも発動する（がんじょうは消費しない）。
    """
    new_dist: StateDist = defaultdict(int)
    for state, freq in hp_dist.items():
        flag = state.ability_enabled if consume == "ability" else state.item_enabled
        if state.value == 0 and flag:
            state = State(
                1,
                ability_enabled=state.ability_enabled,
                item_enabled=False if consume == "item" else state.item_enabled,
                attacker_boosts=state.attacker_boosts,
                attacker_ailment=state.attacker_ailment,
                defender_boosts=state.defender_boosts,
                defender_ailment=state.defender_ailment,
            )
        new_dist[state] += freq
    return dict(new_dist)


def アイスボディ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """アイスボディ: ゆき天気のとき、ターン終了時に最大HPの1/16を回復する。"""
    if battle.weather.name != "ゆき":
        return hp_dist
    return _heal(hp_dist, ctx.defender, r=1/16)


def アクアリング_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """アクアリング: ターン終了時に最大HPの1/16を回復する。"""
    return _heal(hp_dist, ctx.defender, r=1/16)


def Gのちから_lower_def(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """Gのちから: 命中後、追加効果有効時に防御側のぼうぎょを1段階下げる。"""
    if ctx.move_secondary:
        ctx.defender.boosts["def"] = clamp_stats(ctx.defender.boosts["def"] - 1)
    return hp_dist


def アシッドボム_reduce_spd(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """アシッドボム: 命中後、防御側のとくぼうを2段階下げる。"""
    ctx.defender.boosts["spd"] = clamp_stats(ctx.defender.boosts["spd"] - 2)
    return hp_dist


def アッキのみ_boost_def(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """アッキのみ: 物理技を受けた直後にぼうぎょ+1して消費する。

    ぼうぎょランクが+6のとき、またはitem_enabledがFalseのときは発動しない。
    特性ちからずくの対象技（追加効果あり技）を受けたときも発動しない。
    """
    if ctx.move.category != "physical":
        return hp_dist

    if (
        ctx.attacker.ability.name == "ちからずく"
        and ctx.move.has_flag("secondary_effect")
    ):
        return hp_dist

    # item_enabled=True の state があるか確認
    if not any(state.item_enabled for state in hp_dist):
        return hp_dist

    # ぼうぎょランクが最大なら発動しない（消費もしない）
    if ctx.defender.boosts["def"] >= 6:
        return hp_dist

    # ぼうぎょランクを+1（一度だけ）
    ctx.defender.boosts["def"] = clamp_stats(ctx.defender.boosts["def"] + 1)

    # item_enabled=True の state を消費済みに更新して新しい StateDist を返す
    new_dist: StateDist = defaultdict(int)
    for state, freq in hp_dist.items():
        if state.item_enabled:
            new_state = State(
                value=state.value,
                ability_enabled=state.ability_enabled,
                item_enabled=False,
                attacker_boosts=state.attacker_boosts,
                attacker_ailment=state.attacker_ailment,
                defender_boosts=state.defender_boosts,
                defender_ailment=state.defender_ailment,
            )
            new_dist[new_state] += freq
        else:
            new_dist[state] += freq
    return dict(new_dist)


def あめうけざら_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """あめうけざら: あめ・おおあめのとき、ターン終了時に最大HPの1/16を回復する。"""
    if not battle.weather_for(ctx.defender).rainy:
        return hp_dist
    return _heal(hp_dist, ctx.defender, r=1/16)


def イアのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """イアのみ: HP が 1/4 以下になると max_hp の 1/3 回復し、消費する。"""
    return _heal_at_pinch(hp_dist, ctx.defender, r=1/3, threshold_rate=1/4, heal_with="item", consume=True)


def Vジェネレート_lower_attacker_def_spd_spe(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """Vジェネレート: 命中後、追加効果有効時に攻撃側のぼうぎょ・とくぼう・すばやさを1段階ずつ下げる。"""
    if ctx.move_secondary:
        ctx.attacker.boosts["def"] = clamp_stats(ctx.attacker.boosts["def"] - 1)
        ctx.attacker.boosts["spd"] = clamp_stats(ctx.attacker.boosts["spd"] - 1)
        ctx.attacker.boosts["spe"] = clamp_stats(ctx.attacker.boosts["spe"] - 1)
    return hp_dist


def いじげんラッシュ_lower_attacker_def(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """いじげんラッシュ: 命中後、攻撃側のぼうぎょを1段階下げる（確定効果、ちからずくの対象外）。"""
    ctx.attacker.boosts["def"] = clamp_stats(ctx.attacker.boosts["def"] - 1)
    return hp_dist


def _type_resist_berry(battle: Battle, ctx: LethalContext, hp_dist: StateDist,
                       type_: str, super_effective_only: bool = True) -> StateDist:
    """タイプ半減きのみの共通処理。

    通常ハンドラ（ON_CALC_DAMAGE_MODIFIER）の `_modify_super_effective_damage` は
    `calc_def_type_modifier(ctx) > 4096`（効果バツグン時のみ発火）なので、タイプ一致かつ
    効果バツグンであれば calc_damages 内でダメージを半減している。よってこのlethalハンドラでは
    ctx.damage_dist は変更せず、アイテム消費と item_enabled 更新のみ行う。

    super_effective_only=True  : 17種の通常タイプ半減きのみ。効果バツグン時のみ発動する。
    super_effective_only=False : ホズのみ用。ノーマルタイプ技全般で発動する
                                 （ノーマルは抜群にならないため super_effective 判定を省く）。
    """
    if ctx.move.type != type_:
        return hp_dist
    if super_effective_only and (battle.damage_calculator.def_type_modifier or 0) <= 4096:
        return hp_dist
    if not any(state.item_enabled for state in hp_dist):
        return hp_dist

    # バトル状態のアイテムを消費して次回の calc_damages で重複適用しないようにする
    battle.item_manager.consume_item(ctx.defender)

    # StateDist の item_enabled を False に更新する
    new_dist: StateDist = defaultdict(int)
    for state, freq in hp_dist.items():
        if state.item_enabled:
            new_state = State(state.value,
                              ability_enabled=state.ability_enabled,
                              item_enabled=False,
                              attacker_boosts=state.attacker_boosts,
                              attacker_ailment=state.attacker_ailment,
                              defender_boosts=state.defender_boosts,
                              defender_ailment=state.defender_ailment)
            new_dist[new_state] += freq
        else:
            new_dist[state] += freq
    return dict(new_dist)


def イトケのみ_resist_water(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """イトケのみ: みずタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "みず")


def ウイのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ウイのみ: HP が 1/4 以下になると max_hp の 1/3 回復し、消費する。"""
    return _heal_at_pinch(hp_dist, ctx.defender, r=1/3, threshold_rate=1/4, heal_with="item", consume=True)


def うたかたのアリア_cure_defender_burn(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """うたかたのアリア: 命中後、追加効果有効時に防御側のやけど状態を治す。"""
    if ctx.move_secondary and ctx.defender.ailment.name == "やけど":
        from jpoke.model.ailment import Ailment
        ctx.defender.ailment = Ailment()
    return hp_dist


def ウタンのみ_resist_psychic(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ウタンのみ: エスパータイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "エスパー")


def エレクトロビーム_boost_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """エレクトロビーム: チャージ時に追加効果有効なら攻撃側のとくこうを1段階上げる。"""
    if ctx.move_secondary:
        ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] + 1)
    return hp_dist


def オッカのみ_resist_fire(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """オッカのみ: ほのおタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "ほのお")


def オボンのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """オボンのみ: HP が 1/2 以下になると max_hp の 1/4 回復し、消費する。"""
    return _heal_at_pinch(hp_dist, ctx.defender, r=1/4, threshold_rate=1/2, heal_with="item", consume=True)


def _add_second_hit(dist: StateDist) -> StateDist:
    """おやこあいの2ヒット目（1/4ダメージ、最低1）をダメージ分布に加算する。"""
    new_dist: StateDist = defaultdict(int)
    for state, freq in dist.items():
        second_hit = max(1, state.value // 4) if state.value > 0 else 0
        new_state = State(
            state.value + second_hit,
            ability_enabled=state.ability_enabled,
            item_enabled=state.item_enabled,
            attacker_boosts=state.attacker_boosts,
            attacker_ailment=state.attacker_ailment,
            defender_boosts=state.defender_boosts,
            defender_ailment=state.defender_ailment,
        )
        new_dist[new_state] += freq
    return dict(new_dist)


def おやこあい_boost_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """おやこあい: 単発攻撃技のダメージに2ヒット目（1/4ダメージ、最低1）を加算する。"""
    if not (ctx.move.is_attack and ctx.move.max_hits == 1):
        return hp_dist
    ctx.damage_dist = _add_second_hit(ctx.damage_dist)
    if ctx.damage_dist_full is not None:
        ctx.damage_dist_full = _add_second_hit(ctx.damage_dist_full)
    return hp_dist


def オレンのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """オレンのみ: HP が 1/2 以下になると 10 固定回復し、消費する。"""
    return _heal_at_pinch(hp_dist, ctx.defender, v=10, threshold_rate=1/2, heal_with="item", consume=True)


def オーバーヒート_lower_attacker_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """オーバーヒート: 命中後、攻撃側のとくこうを2段階下げる。"""
    ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] - 2)
    return hp_dist


def カシブのみ_resist_ghost(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """カシブのみ: ゴーストタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "ゴースト")


def かんそうはだ_weather_hp(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """かんそうはだ: あめ・おおあめのとき1/8回復、はれ・おおひでりのとき1/8ダメージ。"""
    weather = battle.weather_for(ctx.defender)
    if weather.rainy:
        return _heal(hp_dist, ctx.defender, r=1/8)
    if weather.sunny:
        return _damage(hp_dist, max(1, ctx.defender.max_hp // 8))
    return hp_dist


def がんじょう_survive_lethal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """がんじょう: 満タン状態から瀕死になった場合、HP1で耐える。(ON_APPLY_DAMAGE / subject="defender")

    何度でも発動する。.internal/spec/abilities/がんじょう.md 参照。
    """
    return _survive_at_full_hp(hp_dist, consume="ability")


def きあいのタスキ_survive_ohko(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """きあいのタスキ: 満タン状態から瀕死になった場合、HP1で耐えて消費する。
    (ON_APPLY_DAMAGE / subject="defender")

    .internal/spec/items/きあいのタスキ.md 参照。多段技の2発目以降は item_enabled=False
    により発動しない。
    """
    return _survive_at_full_hp(hp_dist, consume="item")


def キラースピン_apply_どく(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """キラースピン: 命中後、追加効果有効時に防御側にどく状態を付与する。"""
    if ctx.move_secondary and not ctx.defender.ailment.is_active:
        from jpoke.model.ailment import Ailment
        ctx.defender.ailment = Ailment("どく")
    return hp_dist


def クリアスモッグ_reset_defender_rank(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """クリアスモッグ: 命中後、防御側の能力ランク変化を全て±0にリセットする。"""
    for stat in ctx.defender.boosts:
        ctx.defender.boosts[stat] = 0
    return hp_dist


def くろいヘドロ_recover_or_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """くろいヘドロ: どくタイプは1/16回復、それ以外は1/8ダメージ。"""
    if "どく" in ctx.defender.types:
        return _heal(hp_dist, ctx.defender, r=1/16)
    # 1/8ダメージ（最低1、HP は 0 未満にならない）
    amount = max(1, int(ctx.defender.max_hp / 8))
    return _damage(hp_dist, amount)


def グラスフィールド_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """グラスフィールド: 接地しているポケモンのターン終了時に最大HPの1/16を回復する。"""
    if battle.query.is_floating(ctx.defender):
        return hp_dist
    return _heal(hp_dist, ctx.defender, r=1/16)


def グロウパンチ_boost_attacker_atk(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """グロウパンチ: 命中後、追加効果有効時に攻撃側のこうげきを1段階上げる。"""
    if ctx.move_secondary:
        ctx.attacker.boosts["atk"] = clamp_stats(ctx.attacker.boosts["atk"] + 1)
    return hp_dist


def ゴールドラッシュ_lower_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ゴールドラッシュ: 命中後、攻撃側のとくこうを2段階下げる（Champions基準）。"""
    ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] - 2)
    return hp_dist


def サイコノイズ_apply_volatile(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """サイコノイズ: 命中後、追加効果有効時に相手にかいふくふうじ状態（2ターン）を付与する。"""
    if ctx.move_secondary and "かいふくふうじ" not in ctx.defender.volatiles:
        from jpoke.model.volatile import Volatile
        ctx.defender.volatiles["かいふくふうじ"] = Volatile("かいふくふうじ", count=2)
    return hp_dist


def サイコブースト_lower_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """サイコブースト: 命中後、攻撃側のとくこうを2段階下げる。"""
    ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] - 2)
    return hp_dist


def サンパワー_take_sun_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """サンパワー: はれ・おおひでりのとき、ターン終了時に最大HPの1/8ダメージを受ける（defender側のみ追跡対象）。"""
    if battle.weather_for(ctx.defender).sunny:
        return _damage(hp_dist, max(1, ctx.defender.max_hp // 8))
    return hp_dist


def しおづけ_apply_volatile(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """しおづけ（技）: 命中後、追加効果有効時にしおづけ状態を付与する。しおづけダメージはON_TURN_ENDで処理。"""
    if ctx.move_secondary and "しおづけ" not in ctx.defender.volatiles:
        from jpoke.model.volatile import Volatile
        ctx.defender.volatiles["しおづけ"] = Volatile("しおづけ")
    return hp_dist


def しおづけ_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """しおづけ: ターン終了時ダメージ（みず・はがねタイプは1/8、それ以外は1/16）。"""
    if ctx.defender.has_type("みず") or ctx.defender.has_type("はがね"):
        damage = max(1, ctx.defender.max_hp // 8)
    else:
        damage = max(1, ctx.defender.max_hp // 16)
    return _damage(hp_dist, damage)


def しっとのほのお_apply_burn_to_defender(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """しっとのほのお: 追加効果有効時、そのターンにランクが上がった相手をやけど状態にする。"""
    if ctx.move_secondary and ctx.defender.stat_raised_this_turn and not ctx.defender.ailment.is_active:
        from jpoke.model.ailment import Ailment
        ctx.defender.ailment = Ailment("やけど")
    return hp_dist


def シュカのみ_resist_ground(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """シュカのみ: じめんタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "じめん")


def しんぴのちから_boost_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """しんぴのちから: 命中後、追加効果有効時に攻撃側のとくこうを1段階上げる。"""
    if ctx.move_secondary:
        ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] + 1)
    return hp_dist


def じきゅうりょく_boost_def(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """じきゅうりょく: 攻撃を受けるとぼうぎょが1段階上がる。"""
    if ctx.defender.boosts["def"] >= 6:
        return hp_dist
    ctx.defender.boosts["def"] = clamp_stats(ctx.defender.boosts["def"] + 1)
    return hp_dist


def すなあらし_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """すなあらし: いわ・じめん・はがね以外のポケモンに最大HPの1/16のダメージを与える。"""
    if (
        ctx.defender.has_type("いわ")
        or ctx.defender.has_type("じめん")
        or ctx.defender.has_type("はがね")
    ):
        return hp_dist
    damage = max(1, ctx.defender.max_hp // 16)
    return _damage(hp_dist, damage)


def ソクノのみ_resist_electric(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ソクノのみ: でんきタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "でんき")


def たべのこし_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """たべのこし: max_hp の 1/16 回復する。"""
    return _heal(hp_dist, ctx.defender, r=1/16)


def タラプのみ_boost_spd(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """タラプのみ: 特殊技を受けた直後にとくぼう+1して消費する。

    とくぼうランクが+6のとき、またはitem_enabledがFalseのときは発動しない。
    特性ちからずくの対象技（追加効果あり技）を受けたときも発動しない。
    """
    if ctx.move.category != "special":
        return hp_dist

    if (
        ctx.attacker.ability.name == "ちからずく"
        and ctx.move.has_flag("secondary_effect")
    ):
        return hp_dist

    # item_enabled=True の state があるか確認
    if not any(state.item_enabled for state in hp_dist):
        return hp_dist

    # とくぼうランクが最大なら発動しない（消費もしない）
    if ctx.defender.boosts["spd"] >= 6:
        return hp_dist

    # とくぼうランクを+1（一度だけ）
    ctx.defender.boosts["spd"] = clamp_stats(ctx.defender.boosts["spd"] + 1)

    # item_enabled=True の state を消費済みに更新して新しい StateDist を返す
    new_dist: StateDist = defaultdict(int)
    for state, freq in hp_dist.items():
        if state.item_enabled:
            new_state = State(
                value=state.value,
                ability_enabled=state.ability_enabled,
                item_enabled=False,
                attacker_boosts=state.attacker_boosts,
                attacker_ailment=state.attacker_ailment,
                defender_boosts=state.defender_boosts,
                defender_ailment=state.defender_ailment,
            )
            new_dist[new_state] += freq
        else:
            new_dist[state] += freq
    return dict(new_dist)


def タンガのみ_resist_bug(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """タンガのみ: むしタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "むし")


def チャージビーム_boost_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """チャージビーム: 命中後、追加効果有効時に攻撃側のとくこうを1段階上げる。"""
    if ctx.move_secondary:
        ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] + 1)
    return hp_dist


def テラバースト_lower_attacker_atk_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """テラバースト: ステラタイプにテラスタルして命中した場合、こうげき・とくこうを1段階ずつ下げる。"""
    if ctx.attacker.active_tera_type != "ステラ":
        return hp_dist
    ctx.attacker.boosts["atk"] = clamp_stats(ctx.attacker.boosts["atk"] - 1)
    ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] - 1)
    return hp_dist


def どく_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """どく: ターン終了時に最大HPの1/8ダメージを受ける。

    ポイズンヒール所持時はダメージを与えない（ポイズンヒール側で回復処理する）。
    """
    if ctx.defender.ability.base_name == "ポイズンヒール":
        return hp_dist
    damage = max(1, ctx.defender.max_hp // 8)
    return _damage(hp_dist, damage)


def なげつける_apply_item_effect(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """なげつける: 追加効果有効時、投げたアイテムに応じた効果を防御側に適用する。

    HP分布や以降のダメージ計算に影響する効果（状態異常の付与・回復・能力ランク変化）のみを
    対象とする。ひるみ・きゅうしょアップ・めいちゅうアップ・PP回復は、防御側が行動しない
    この致死率計算モデル上ではHP分布に影響しないため対象外とする。
    """
    if not ctx.move_secondary:
        return hp_dist

    from jpoke.model.ailment import Ailment
    from jpoke.model.volatile import Volatile
    from jpoke.handlers.item import is_ripen, berry_heal_amount

    item_name = ctx.attacker.item.base_name
    defender = ctx.defender

    if item_name == "でんきだま":
        if not defender.ailment.is_active:
            defender.ailment = Ailment("まひ")
    elif item_name == "かえんだま":
        if not defender.ailment.is_active:
            defender.ailment = Ailment("やけど")
    elif item_name == "どくバリ":
        if not defender.ailment.is_active:
            defender.ailment = Ailment("どく")
    elif item_name == "どくどくだま":
        if not defender.ailment.is_active:
            defender.ailment = Ailment("もうどく")
    elif item_name == "しろいハーブ":
        for stat, v in list(defender.boosts.items()):
            if v < 0:
                defender.boosts[stat] = 0
    elif item_name == "メンタルハーブ":
        for volatile_name in ("メロメロ", "アンコール", "いちゃもん", "かなしばり", "ちょうはつ", "かいふくふうじ"):
            defender.volatiles.pop(volatile_name, None)
    elif item_name == "ラムのみ":
        if defender.ailment.is_active:
            defender.ailment = Ailment()
        defender.volatiles.pop("こんらん", None)
    elif item_name == "クラボのみ" and defender.ailment.name == "まひ":
        defender.ailment = Ailment()
    elif item_name == "カゴのみ" and defender.ailment.name == "ねむり":
        defender.ailment = Ailment()
    elif item_name == "モモンのみ" and defender.ailment.name in ("どく", "もうどく"):
        defender.ailment = Ailment()
    elif item_name == "チーゴのみ" and defender.ailment.name == "やけど":
        defender.ailment = Ailment()
    elif item_name == "ナナシのみ" and defender.ailment.name == "こおり":
        defender.ailment = Ailment()
    elif item_name == "キーのみ":
        defender.volatiles.pop("こんらん", None)
    elif item_name == "オレンのみ":
        hp_dist = _heal(hp_dist, defender, v=berry_heal_amount(defender, v=10))
    elif item_name == "オボンのみ":
        hp_dist = _heal(hp_dist, defender, v=berry_heal_amount(defender, r=1/4))
    elif item_name in ("フィラのみ", "ウイのみ", "マゴのみ", "バンジのみ", "イアのみ"):
        hp_dist = _heal(hp_dist, defender, v=berry_heal_amount(defender, r=1/3))
        confuse_natures = {
            "フィラのみ": ("ずぶとい", "ひかえめ", "おだやか", "おくびょう"),
            "ウイのみ": ("いじっぱり", "わんぱく", "ようき", "しんちょう"),
            "マゴのみ": ("ゆうかん", "のんき", "れいせい", "なまいき"),
            "バンジのみ": ("やんちゃ", "のうてんき", "うっかりや", "むじゃき"),
            "イアのみ": ("さみしがり", "おっとり", "おとなしい", "せっかち"),
        }[item_name]
        if defender.nature in confuse_natures and "こんらん" not in defender.volatiles:
            defender.volatiles["こんらん"] = Volatile("こんらん", count=2)
    elif item_name == "チイラのみ":
        defender.boosts["atk"] = clamp_stats(defender.boosts["atk"] + (2 if is_ripen(defender) else 1))
    elif item_name in ("リュガのみ", "アッキのみ"):
        defender.boosts["def"] = clamp_stats(defender.boosts["def"] + (2 if is_ripen(defender) else 1))
    elif item_name == "カムラのみ":
        defender.boosts["spe"] = clamp_stats(defender.boosts["spe"] + (2 if is_ripen(defender) else 1))
    elif item_name == "ヤタピのみ":
        defender.boosts["spa"] = clamp_stats(defender.boosts["spa"] + (2 if is_ripen(defender) else 1))
    elif item_name in ("ズアのみ", "タラプのみ"):
        defender.boosts["spd"] = clamp_stats(defender.boosts["spd"] + (2 if is_ripen(defender) else 1))
    elif item_name == "スターのみ":
        candidates = [s for s in ("atk", "def", "spa", "spd", "spe") if defender.boosts[s] < 6]
        if candidates:
            stat = battle.random.choice(candidates)
            defender.boosts[stat] = clamp_stats(defender.boosts[stat] + (4 if is_ripen(defender) else 2))

    return hp_dist


def ナモのみ_resist_dark(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ナモのみ: あくタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "あく")


def ねをはる_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ねをはる: ターン終了時に最大HPの1/16を回復する。"""
    return _heal(hp_dist, ctx.defender, r=1/16)


def のろい_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """のろい: ターン終了時に最大HPの1/4ダメージを受ける。"""
    damage = max(1, ctx.defender.max_hp // 4)
    return _damage(hp_dist, damage)


def はきだす_reset_stockpile(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """はきだす: 使用後、たくわえるで上がったぼうぎょ・とくぼうランク分を戻し、たくわえる状態を解除する。

    2回目以降の使用（複数回攻撃のリーサル計算）で威力が正しく0（たくわえ無し）に
    戻るようにするための後処理。はきだす_apply_after（ON_END_MOVE）と同じ効果。
    """
    mon = ctx.attacker
    volatile = mon.volatiles.get("たくわえる")
    if volatile is None:
        return hp_dist
    count = volatile.count or 0
    if count == 0:
        return hp_dist
    mon.boosts["def"] = clamp_stats(mon.boosts["def"] - count)
    mon.boosts["spd"] = clamp_stats(mon.boosts["spd"] - count)
    del mon.volatiles["たくわえる"]
    return hp_dist


def ハバンのみ_resist_dragon(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ハバンのみ: ドラゴンタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "ドラゴン")


def バインド_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """バインド: ターン終了時に bind_damage_ratio に応じたダメージを受ける（デフォルト1/8）。"""
    volatile = ctx.defender.volatiles.get("バインド")
    if volatile is None:
        return hp_dist
    damage = max(1, int(ctx.defender.max_hp * volatile.bind_damage_ratio))
    return _damage(hp_dist, damage)


def ばかぢから_lower_atk_def(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ばかぢから: 命中後、攻撃側のこうげき・ぼうぎょを1段階下げる。"""
    ctx.attacker.boosts["atk"] = clamp_stats(ctx.attacker.boosts["atk"] - 1)
    ctx.attacker.boosts["def"] = clamp_stats(ctx.attacker.boosts["def"] - 1)
    return hp_dist


def ばけのかわ_block_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ばけのかわ: 攻撃を無効化し、変身解除ダメージ(max_hp/8)を与える。

    ON_BEFORE_HIT で発火する。ctx.damage_dist をゼロに上書きして subtract_dist による
    攻撃ダメージをキャンセルし、代わりに変身解除ダメージ(max_hp/8)を与える。
    """
    if not any(state.ability_enabled for state in hp_dist):
        return hp_dist

    # 攻撃ダメージをゼロにして無効化する（subtract_dist が何も引かないようにする）
    ctx.damage_dist = to_dist(0)
    if ctx.damage_dist_full is not None:
        ctx.damage_dist_full = to_dist(0)

    # 変身解除ダメージを与えて ability_enabled を False にする
    damage = max(1, int(ctx.defender.max_hp / 8))
    new_dist: StateDist = defaultdict(int)
    for state, freq in hp_dist.items():
        if state.ability_enabled:
            new_state = State(
                value=max(0, state.value - damage),
                ability_enabled=False,
                item_enabled=state.item_enabled,
                attacker_boosts=state.attacker_boosts,
                attacker_ailment=state.attacker_ailment,
                defender_boosts=state.defender_boosts,
                defender_ailment=state.defender_ailment,
            )
            new_dist[new_state] += freq
        else:
            new_dist[state] += freq
    return dict(new_dist)


def バコウのみ_resist_flying(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """バコウのみ: ひこうタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "ひこう")


def バンジのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """バンジのみ: HP が 1/4 以下になると max_hp の 1/3 回復し、消費する。"""
    return _heal_at_pinch(hp_dist, ctx.defender, r=1/3, threshold_rate=1/4, heal_with="item", consume=True)


def ビアーのみ_resist_poison(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ビアーのみ: どくタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "どく")


def フィラのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """フィラのみ: HP が 1/4 以下になると max_hp の 1/3 回復し、消費する。"""
    return _heal_at_pinch(hp_dist, ctx.defender, r=1/3, threshold_rate=1/4, heal_with="item", consume=True)


def フルールカノン_lower_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """フルールカノン: 命中後、攻撃側のとくこうを2段階下げる。"""
    ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] - 2)
    return hp_dist


def フレアソング_boost_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """フレアソング: 命中後、追加効果有効時に攻撃側のとくこうを1段階上げる。"""
    if ctx.move_secondary:
        ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] + 1)
    return hp_dist


def ホイールスピン_sharply_lower_attacker_spe(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ホイールスピン: 命中後、攻撃側のすばやさを2段階下げる（確定効果、ちからずくの対象外）。"""
    ctx.attacker.boosts["spe"] = clamp_stats(ctx.attacker.boosts["spe"] - 2)
    return hp_dist


def ホズのみ_resist_normal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ホズのみ: ノーマルタイプの技のダメージを1/2にして消費する（抜群不要）。"""
    return _type_resist_berry(battle, ctx, hp_dist, "ノーマル", super_effective_only=False)


def ほのおのまい_boost_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ほのおのまい: 命中後、追加効果有効時に攻撃側のとくこうを1段階上げる。"""
    if ctx.move_secondary:
        ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] + 1)
    return hp_dist


def ほのおのムチ_lower_def(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ほのおのムチ: 命中後、追加効果有効時に防御側のぼうぎょを1段階下げる。"""
    if ctx.move_secondary:
        ctx.defender.boosts["def"] = clamp_stats(ctx.defender.boosts["def"] - 1)
    return hp_dist


def ポイズンヒール_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ポイズンヒール: どく・もうどく状態のとき、ターン終了時に最大HPの1/8を回復する。"""
    if ctx.defender.ailment.name not in ("どく", "もうどく"):
        return hp_dist
    return _heal(hp_dist, ctx.defender, r=1/8)


def マゴのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """マゴのみ: HP が 1/4 以下になると max_hp の 1/3 回復し、消費する。"""
    return _heal_at_pinch(hp_dist, ctx.defender, r=1/3, threshold_rate=1/4, heal_with="item", consume=True)


def みわくのボイス_apply_confusion_to_defender(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """みわくのボイス: 追加効果有効時、そのターンにランクが上がった相手をこんらん状態にする。"""
    if (
        ctx.move_secondary
        and ctx.defender.stat_raised_this_turn
        and "こんらん" not in ctx.defender.volatiles
    ):
        from jpoke.model.volatile import Volatile
        ctx.defender.volatiles["こんらん"] = Volatile("こんらん", count=2)
    return hp_dist


def メテオビーム_boost_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """メテオビーム: C+1する"""
    if ctx.move_secondary:
        ctx.attacker.boosts["spa"] += 1
    return hp_dist


def もうどく_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """もうどく: ターン終了時に経過ターンに応じて増加するダメージを受ける。

    ダメージ: max(1, 最大HP × min(15, 経過ターン数) // 16)
    ポイズンヒール所持時はダメージを与えない（ポイズンヒール側で回復処理する）が、
    経過ターン数の加算は実際にダメージを受けたかどうかに関わらず常に行う
    （もうどく状態でいるターン自体は継続してカウントされ続けるため）。
    """
    ctx.defender.ailment.tick()
    turns = min(15, ctx.defender.ailment.elapsed_turns)
    if ctx.defender.ability.base_name == "ポイズンヒール":
        return hp_dist
    damage = max(1, ctx.defender.max_hp * turns // 16)
    return _damage(hp_dist, damage)


def やけど_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """やけど: ターン終了時に最大HPの1/16ダメージを受ける。"""
    damage = max(1, ctx.defender.max_hp // 16)
    return _damage(hp_dist, damage)


def ヤチェのみ_resist_ice(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ヤチェのみ: こおりタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "こおり")


def やどりぎのタネ_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """やどりぎのタネ: ターン終了時に最大HPの1/8ダメージを受ける（相手への回復は考慮外）。"""
    damage = max(1, ctx.defender.max_hp // 8)
    return _damage(hp_dist, damage)


def ヨプのみ_resist_fighting(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ヨプのみ: かくとうタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "かくとう")


def ヨロギのみ_resist_rock(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ヨロギのみ: いわタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "いわ")


def りゅうせいぐん_lower_spa(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """りゅうせいぐん: 命中後、攻撃側のとくこうを2段階下げる。"""
    ctx.attacker.boosts["spa"] = clamp_stats(ctx.attacker.boosts["spa"] - 2)
    return hp_dist


def リリバのみ_resist_steel(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """リリバのみ: はがねタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "はがね")


def りんごさん_lower_spd(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """りんごさん: 命中後、追加効果有効時に防御側のとくぼうを1段階下げる。"""
    if ctx.move_secondary:
        ctx.defender.boosts["spd"] = clamp_stats(ctx.defender.boosts["spd"] - 1)
    return hp_dist


def リンドのみ_resist_grass(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """リンドのみ: くさタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "くさ")


def ルミナコリジョン_lower_spd(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ルミナコリジョン: 命中後、追加効果有効時に防御側のとくぼうを2段階下げる。"""
    if ctx.move_secondary:
        ctx.defender.boosts["spd"] = clamp_stats(ctx.defender.boosts["spd"] - 2)
    return hp_dist


def れんごく_apply_やけど(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """れんごく: 命中後、追加効果有効時に防御側にやけど状態を付与する。"""
    if ctx.move_secondary and not ctx.defender.ailment.is_active:
        from jpoke.model.ailment import Ailment
        ctx.defender.ailment = Ailment("やけど")
    return hp_dist


def ロゼルのみ_resist_fairy(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ロゼルのみ: フェアリータイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "フェアリー")
