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
            )
        new_dist[state] += freq
    return dict(new_dist)

def _is_immune(battle: Battle, ctx: LethalContext) -> bool:
    """タイプ相性・特性等によってダメージが必ず0になるか判定する（固定ダメージ技用）。

    通常のダメージ計算経路（core/move_executor.py の _check_hit_by_type、
    実戦の Event.ON_TRY_MOVE_1 相当）と同じ battle.damage_calculator.calc_def_type_modifier
    を使う。この関数が発火する Event.ON_CALC_DEF_TYPE_MODIFIER ハンドラ（きもったま・
    しんがん・テラスシェル・らんきりゅう・ねらいのまと・フライングプレス・フリーズドライ）は
    いずれも読み取り専用で副作用が無いことを確認済みのため、lethal計算中
    （deepcopy済みのbattle）で呼んでも安全。

    タイプ相性が0倍（無効）の場合に加え、ふしぎなまもり特性（効果抜群でない攻撃技を
    無効化する。実戦: ふしぎなまもり_block_non_effective, Event.ON_TRY_MOVE_1）が
    有効な場合も無効と判定する（.internal/spec/moves/_fixed_damage.md §7.2
    「無効化（0倍）は適用」にふしぎなまもり等の無効化を含める実装方針）。

    ちょすい・よびみず・そうしょく・どしょく・ひらいしん等の「技を吸収して行動自体を
    ブロックする」系や、かたやぶり等の相手特性を無視する効果は、lethal計算では
    Event.ON_BEFORE_APPLY_MOVE / Event.ON_BEGIN_MOVE 相当が一切モデル化されていない
    （lethal_handlers 未登録）既存の制約のため、本関数でも考慮しない。
    """
    from jpoke.core.context import AttackContext

    move = ctx.move
    if not move.is_attack or not move.type:
        return False

    atk_ctx = AttackContext(
        attacker=ctx.attacker, defender=ctx.defender, move=move, critical=ctx.critical)
    type_modifier = battle.damage_calculator.calc_def_type_modifier(atk_ctx)
    if type_modifier == 0:
        return True
    if (
        ctx.defender.ability.name == "ふしぎなまもり"
        and ctx.defender.ability.enabled
        and type_modifier <= 4096
    ):
        return True
    return False

def _zero_damage(ctx: LethalContext) -> None:
    """damage_dist・damage_dist_full・damage_from_hp をまとめてダメージ0にリセットする。

    ばけのかわ等、攻撃を完全に無効化するハンドラで使う共通処理。damage_from_hp が
    設定されたまま残っていると、後続の _apply_damage が damage_from_hp を優先して
    しまい、せっかくの無効化が効かなくなるため必ずクリアする。
    """
    ctx.damage_dist = to_dist(0)
    ctx.damage_dist_full = to_dist(0)
    ctx.damage_from_hp = None

def level_fixed_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ナイトヘッド・ちきゅうなげ: 使用者レベル固定ダメージ（一律、防御側HPに依存しない）。

    実戦: level_fixed_damage（handlers/move_attack.py）。
    タイプ無効（ちきゅうなげ⇔ゴースト、ナイトヘッド⇔ノーマル等）の場合はダメージ0にする。
    """
    if _is_immune(battle, ctx):
        ctx.damage_dist = to_dist(0)
    else:
        ctx.damage_dist = to_dist(ctx.attacker.level)
    return hp_dist

def half_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """いかりのまえば・カタストロフィ: 防御側の現在HP×1/2（切り捨て、最低1）。枝依存。

    実戦: half_damage（handlers/move_attack.py）。タイプ無効の場合はダメージ0にする。
    """
    if _is_immune(battle, ctx):
        ctx.damage_from_hp = lambda hp: 0
    else:
        ctx.damage_from_hp = lambda hp: max(1, hp // 2)
    return hp_dist

def ohko_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """一撃必殺技（つのドリル・ハサミギロチン・じわれ・ぜったいれいど）: 防御側の現在HP
    そのものを与える（＝命中すれば必ずHP0にする）。枝依存。

    実戦: ohko_damage（handlers/move_attack.py）。lethal計算では命中率は考慮しない
    （他の技と同じ扱い）。タイプ無効（じわれ⇔ひこう/ふゆう等）の場合はダメージ0にする。

    ぜったいれいど⇔こおりタイプは通常のタイプ相性表では0.5倍でしかなく
    calc_def_type_modifier（_is_immune）では検出できないため、実戦の
    ぜったいれいど_check_ice_immunity（handlers/move_attack.py, Event.ON_TRY_MOVE_2）と
    同じ「対象がこおりタイプなら本技専用に無効化する」ロジックを個別に追加する。
    """
    ice_blocked = (
        ctx.move.name == "ぜったいれいど"
        and ctx.defender.has_type("こおり")
    )
    if ice_blocked or _is_immune(battle, ctx):
        ctx.damage_from_hp = lambda hp: 0
    else:
        ctx.damage_from_hp = lambda hp: hp
    return hp_dist


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
                              item_enabled=False)
            new_dist[new_state] += freq
        else:
            new_dist[state] += freq
    return dict(new_dist)


def イトケのみ_resist_water(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """イトケのみ: みずタイプの効果バツグン技のダメージを1/2にして消費する。"""
    return _type_resist_berry(battle, ctx, hp_dist, "みず")


def いのちがけ_modify_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """いのちがけ: 使用者の現在HPを固定ダメージとして与える（一律、防御側HPに依存しない）。

    実戦: いのちがけ_modify_damage（handlers/move_attack.py）。使用者は必ずひんしに
    なるため、lethal.py の既存慣行（_update_hp が ctx.defender.hp を直接代入している
    のと同様）に倣い、ここでも ctx.attacker.hp を直接0に代入する
    （battle.modify_hp を経由すると実戦の副作用付きイベントが発火してしまうため、
    lethal計算専用のこの代入で十分）。これにより2回目以降の攻撃では hp_cost が0になり、
    自然にダメージ0になる。タイプ無効の場合もダメージは0にするが、使用者のHPは
    どのみち0にする（実戦でも命中・まもる等を通過した後のHPコストのため、
    タイプ無効時点で技自体が届いていない場合は本来HPコストも発生しないが、
    lethal計算は命中前提で進むため区別しない）。
    """
    hp_cost = ctx.attacker.hp
    ctx.attacker.hp = 0
    if _is_immune(battle, ctx):
        ctx.damage_dist = to_dist(0)
    else:
        ctx.damage_dist = to_dist(hp_cost)
    return hp_dist


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
        )
        new_dist[new_state] += freq
    return dict(new_dist)


def おやこあい_boost_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """おやこあい: 単発攻撃技のダメージに2ヒット目（1/4ダメージ、最低1）を加算する。

    実戦の おやこあい_modify_hit_count（handlers/ability.py）はがむしゃら・ころがる・
    アイスボールを2ヒット化の対象外としているため、lethal側でも同じ技名で除外する。
    加えて いのちがけ も除外する: いのちがけは1ヒット目で使用者が必ずひんしになるため、
    実戦では2ヒット目のループ自体が「攻撃側が瀕死になったら打ち切る」チェックで
    実行されず、おやこあいの2ヒット目は発生しない。

    ctx.damage_from_hp が設定されている技（固定ダメージ技・割合ダメージ技・一撃必殺技・
    みねうち等）は、その関数をラップして「1ヒット目と同じ式で得たダメージ値の1/4
    （最低1、0以下ならそのまま0）」を加算する。通常攻撃技向けの _add_second_hit と
    同じ近似方針（2ヒット目をHP変化後に独立再計算するのではなく、1ヒット目の値を
    基準に減衰させる）を、枝依存のダメージにもそのまま適用する。
    ただし みねうち は「このわざで相手を瀕死にさせない」という絶対制約があるため、
    合成後のダメージをさらに hp-1 でキャップし直す（キャップし直さないと2ヒット分の
    合計がHP1のガードを超えてしまう）。一撃必殺技は合成後もどのみち0にクランプされる
    （core/lethal.py の subtract_dist(..., minimum=0)）ため、追加のガードは不要
    （数値的に無害）。
    """
    if ctx.move.name in ("がむしゃら", "いのちがけ", "ころがる", "アイスボール"):
        return hp_dist
    if not (ctx.move.is_attack and ctx.move.max_hits == 1):
        return hp_dist

    if ctx.damage_from_hp is not None:
        original = ctx.damage_from_hp
        never_kills = ctx.move.name == "みねうち"

        def _with_second_hit(hp: int, _original=original, _never_kills=never_kills) -> list[int]:
            base = _original(hp)
            values = base if isinstance(base, list) else [base]
            boosted = [v + (max(1, v // 4) if v > 0 else 0) for v in values]
            if _never_kills:
                cap = hp - 1 if hp > 1 else 0
                boosted = [min(v, cap) for v in boosted]
            return boosted
        ctx.damage_from_hp = _with_second_hit
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


def カウンター_modify_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """カウンター: 直近に受けた物理ダメージ×2を固定ダメージとして与える（一律）。

    実戦: カウンター_modify_damage（handlers/move_attack.py）。
    ctx.attacker.last_physical_damage_received は calc_lethal 呼び出し時点
    （バトルのdeepcopy時点）の記録であり、lethal計算は相手の攻撃をシミュレートしない
    ため、複数回の攻撃回数（attack_count）を通じて動的には変化しない
    （＝「計算時点の被弾記録に基づく」固定値として扱う）。
    被弾記録が無い場合（0以下）は実戦のカウンター_can_use相当のガードにより技が
    失敗するため、ダメージ0にする。タイプ無効の場合もダメージ0にする。
    """
    if ctx.attacker.last_physical_damage_received <= 0 or _is_immune(battle, ctx):
        ctx.damage_dist = to_dist(0)
    else:
        ctx.damage_dist = to_dist(ctx.attacker.last_physical_damage_received * 2)
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


def がむしゃら_modify_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """がむしゃら: 防御側HP−攻撃側HP（最低0）を与える。枝依存。

    実戦: がむしゃら_modify_damage（handlers/move_attack.py）。lethal計算では
    がむしゃら_can_use（使用可否: 相手の残りHPが自分以下だと失敗）に相当するチェックは
    行わない（他の使用可否ハンドラと同様、lethal計算は命中・成否を考慮しない）ため、
    式の max(0, ...) がその代わりに下限を保証する。タイプ無効の場合はダメージ0にする。
    """
    if _is_immune(battle, ctx):
        ctx.damage_from_hp = lambda hp: 0
    else:
        attacker_hp = ctx.attacker.hp
        ctx.damage_from_hp = lambda hp, _atk=attacker_hp: max(0, hp - _atk)
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

    # 攻撃ダメージをゼロにして無効化する（subtract_dist が何も引かないようにする）。
    # damage_from_hp（固定ダメージ技等）が設定されている場合も併せてクリアしないと、
    # 後続の _apply_damage が damage_from_hp を優先してしまい無効化が効かなくなる。
    _zero_damage(ctx)

    # 変身解除ダメージを与えて ability_enabled を False にする
    damage = max(1, int(ctx.defender.max_hp / 8))
    new_dist: StateDist = defaultdict(int)
    for state, freq in hp_dist.items():
        if state.ability_enabled:
            new_state = State(
                value=max(0, state.value - damage),
                ability_enabled=False,
                item_enabled=state.item_enabled,
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


def ほうふく_modify_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ほうふく: 直近に受けたダメージ×1.5（切り捨て）を固定ダメージとして与える（一律）。

    実戦: ほうふく_modify_damage（handlers/move_attack.py）。
    ctx.attacker.last_damage_received は calc_lethal 呼び出し時点（バトルのdeepcopy
    時点）の記録に基づく固定値として扱う（カウンター同様、lethal計算中は動的に変化しない）。
    被弾記録が無い場合（0以下）は実戦のほうふく_check_can_use相当のガードにより技が
    失敗するため、ダメージ0にする。タイプ無効の場合もダメージ0にする。
    """
    if ctx.attacker.last_damage_received <= 0 or _is_immune(battle, ctx):
        ctx.damage_dist = to_dist(0)
    else:
        ctx.damage_dist = to_dist(int(ctx.attacker.last_damage_received * 1.5))
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


def みねうち_modify_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """みねうち: 通常ダメージ計算の結果を「HP-1」でキャップする（相手を瀕死にしない）。枝依存。

    実戦: みねうち_modify_damage（handlers/move_attack.py）。みねうちは実際の base_power
    を持つ通常攻撃技のため、_calc_damage_dist が通常どおり calc_damages を使って
    ctx.damage_dist（16通りのダメージロールに対応する分布）を計算済み。ここではその
    ctx.damage_dist をそのまま使い、枝ごとのHPに応じてキャップする関数に閉じ込めて
    damage_from_hp として設定する。hp<=1 のときは実際のダメージは必ず0になる
    （攻撃自体は命中しているため「無効化」ではなく、きあいパンチ不発の対象にはならない
    ——この区別はダメージ量にのみ関わるためlethal計算上は考慮不要）。

    ctx.damage_dist はこの時点の値をクロージャに束縛せず、呼び出し時（_apply_damage_by_branch
    が ON_BEFORE_HIT の全ハンドラ実行後に damage_from_hp を呼ぶタイミング）に都度 ctx.damage_dist
    を読みに行く（遅延参照）。priority=15 より後に走る他のハンドラが ctx.damage_dist を
    直接書き換えるケースは現状存在しないが、将来そのようなハンドラが追加された場合でも
    取りこぼさないための保険。
    """
    def _capped(hp: int, _ctx: LethalContext = ctx) -> list[int]:
        if hp <= 1:
            return [0]
        cap = hp - 1
        result: list[int] = []
        for state, freq in _ctx.damage_dist.items():
            result.extend([min(state.value, cap)] * freq)
        return result
    ctx.damage_from_hp = _capped
    return hp_dist


def ミラーコート_modify_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ミラーコート: 直近に受けた特殊ダメージ×2を固定ダメージとして与える（一律）。

    実戦: ミラーコート_modify_damage（handlers/move_attack.py）。
    ctx.attacker.last_special_damage_received は calc_lethal 呼び出し時点
    （バトルのdeepcopy時点）の記録に基づく固定値として扱う（カウンター同様）。
    被弾記録が無い場合（0以下）は実戦のミラーコート_check_can_use相当のガードにより
    技が失敗するため、ダメージ0にする。タイプ無効の場合もダメージ0にする。
    """
    if ctx.attacker.last_special_damage_received <= 0 or _is_immune(battle, ctx):
        ctx.damage_dist = to_dist(0)
    else:
        ctx.damage_dist = to_dist(ctx.attacker.last_special_damage_received * 2)
    return hp_dist


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


def メタルバースト_modify_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """メタルバースト: 直近に受けたダメージ×1.5（切り捨て）を固定ダメージとして与える（一律）。

    実戦: メタルバースト_modify_damage（handlers/move_attack.py）。式はほうふくと同じ
    （ctx.attacker.last_damage_received × 1.5、切り捨て）。ほうふく_modify_damage の
    docstring を参照。
    """
    if ctx.attacker.last_damage_received <= 0 or _is_immune(battle, ctx):
        ctx.damage_dist = to_dist(0)
    else:
        ctx.damage_dist = to_dist(int(ctx.attacker.last_damage_received * 1.5))
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
