"""パラドックス特性（こだいかっせい / クォークチャージ）専用ハンドラー。"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext
    from jpoke.model import Pokemon

from jpoke.core.handler import HandlerReturn
from jpoke.utils.math import apply_fixed_modifier
from jpoke.types import BoostSource, Stat

from .ability import _announce_ability_triggered, _announce_ability_effect_ended


def _select_paradox_boost_stat(battle: Battle, mon: Pokemon) -> Stat:
    """パラドックス補正の対象能力を選ぶ。
    実数値(ランク補正込み)が最も高い能力を選ぶ。同値時は A>B>C>D>S の順で先勝ち。

    ワンダールーム状態では、ぼうぎょ/とくぼうの実数値（ランク補正を除く）が
    入れ替わった状態で比較する。ランク補正は技の分類に対応する本来の区分のまま
    据え置く（handlers/field.py の ワンダールーム_def_modifier と同じ仕様。
    .internal/spec/abilities/こだいかっせい.md「パワーシェア/ガードシェア/パワートリック/
    スピードスワップ/ワンダールームによる実数値変動も考慮する」
    「実数値の変動はステータスの比較より先に考慮する」を参照）。
    """
    stat_order: tuple[Stat, ...] = ("atk", "def", "spa", "spd", "spe")
    wonder_room = battle.get_global_field("ワンダールーム").is_active

    def value_of(stat: Stat) -> int:
        raw_stat = stat
        if wonder_room and stat in ("def", "spd"):
            raw_stat = "spd" if stat == "def" else "def"
        return int(mon.stats[raw_stat] * mon.rank_modifier(stat))

    best_stat: Stat = stat_order[0]
    best_value = value_of(best_stat)
    for stat in stat_order[1:]:
        value = value_of(stat)
        if value > best_value:
            best_stat = stat
            best_value = value
    return best_stat


def _deactivate_paradox_boost(mon: Pokemon) -> None:
    """パラドックス補正状態を解除する。"""
    mon.paradox_boost_stat = None
    mon.paradox_boost_source = ""


def _announce_paradox_boost_ended(battle: Battle, mon: Pokemon) -> None:
    """こだいかっせい/クォークチャージの補正終了アナウンスを記録する。

    「<ポケモンは> <特性>の 効果が 切れた!」という特性共通の言い回しのため、
    特性名から動的に組み立てる
    （.internal/spec/abilities/こだいかっせい.md 25行目、クォークチャージ.md 25行目）。
    """
    _announce_ability_effect_ended(battle, mon, f"{mon.ability.base_name}の効果が切れた")


def _activate_paradox_boost(battle: Battle,
                            mon: Pokemon,
                            source: BoostSource) -> None:
    """パラドックス補正を有効化し、必要なら消費ログを記録する。"""
    mon.paradox_boost_stat = _select_paradox_boost_stat(battle, mon)
    mon.paradox_boost_source = source
    _announce_ability_triggered(battle, mon)

    # ブーストエナジーを消費する
    if source == "item" and mon.has_item("ブーストエナジー", consider_enabled=True):
        battle.item_manager.consume_item(mon)


def refresh_paradox_charge_state(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こだいかっせい/クォークチャージの補正状態を更新する。

    アイテム側（ON_ITEM_ENABLED/ON_ITEM_GAINED）からも呼ばれるため、
    こだいかっせい/クォークチャージを持たないポケモンに対しては何もしない
    （ブーストエナジーを持たせても効果が無いことに対応）。
    """
    mon = ctx.source
    if mon is None:
        return HandlerReturn(value=value)

    if mon.ability.name not in ("こだいかっせい", "クォークチャージ"):
        return HandlerReturn(value=value)

    # 能力ごとに参照する場の状態が異なる。
    if mon.ability.name == "こだいかっせい":
        field_active = battle.weather.sunny
    else:
        field_active = battle.terrain.name == "エレキフィールド"

    can_consume_item = mon.item.name == "ブーストエナジー"

    # すでにブーストが有効な場合は、場の状態とアイテム消費の両方を考慮して解除の要否を判定する。
    if mon.paradox_boost_stat is not None:
        # アイテム由来のブーストは場の変化で解除されない。
        if mon.paradox_boost_source == "item":
            return HandlerReturn(value=value)

        # 場由来のブーストで場が継続しているなら解除されない。
        if mon.paradox_boost_source == "field" and field_active:
            return HandlerReturn(value=value)

        _deactivate_paradox_boost(mon)
        _announce_paradox_boost_ended(battle, mon)
        if can_consume_item:
            _activate_paradox_boost(battle, mon, "item")
        return HandlerReturn(value=value)

    # ブーストが有効でない場合は、場の状態とアイテム消費の両方を考慮して発動の要否を判定する。
    # 場条件が成立している場合は、アイテムより場由来を優先する。
    if field_active:
        _activate_paradox_boost(battle, mon, "field")
    elif can_consume_item:
        _activate_paradox_boost(battle, mon, "item")

    return HandlerReturn(value=value)


def modify_speed(battle: Battle, ctx: EventContext, value: int) -> HandlerReturn:
    """素早さ補正時: S が強化対象なら 1.5 倍補正を適用する。"""
    mon = ctx.source
    if mon.paradox_boost_stat == "spe":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def apply_atk_modifier(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """攻撃側補正時: 強化対象能力と参照能力が一致すれば 1.3 倍補正を適用する。

    イカサマ（相手の実数値を借りる）やボディプレス（自分の『ぼうぎょ』を攻撃として使う）のように
    ダメージ計算で参照する実数値が通常と異なる技でも、パラドックス特性の補正はあくまで
    「使用者自身」の攻撃側スロット（物理技なら攻撃、特殊技なら特攻）に対してのみ適用される。
    どの実数値が計算に使われているかは影響しない
    （.internal/spec/abilities/クォークチャージ.md 「特性の効果はランク補正上昇とは異なる」の項を参照）。

    こんらんの自傷ダメージ（"_こんらん"）には影響しない
    （同項「特性で攻撃/防御が上がってもこんらんのダメージには影響しない」を参照）。
    """
    if ctx.move.name == "_こんらん":
        return HandlerReturn(value=value)

    attacker = ctx.attacker
    stat = "atk" if ctx.move.category == "physical" else "spa"

    if attacker.paradox_boost_stat == stat:
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)


def apply_def_modifier(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """防御側補正時: 強化対象能力と参照能力が一致すれば 1.3 倍補正を適用する。

    こんらんの自傷ダメージ（"_こんらん"）には影響しない
    （.internal/spec/abilities/クォークチャージ.md 「特性で攻撃/防御が上がってもこんらんの
    ダメージには影響しない」を参照）。

    ワンダールーム状態では、防御側の実数値参照そのものが入れ替わる
    （handlers/field.py の ワンダールーム_def_modifier）ため、パラドックス補正の
    対象判定も入れ替えて追従させる。これにより、ぼうぎょ/とくぼうが強化対象のとき
    ワンダールームの発生・解除に応じて補正が掛かる能力（物理/特殊いずれの防御計算に
    乗るか）が入れ替わる
    （.internal/spec/abilities/こだいかっせい.md「防御か特防が上昇しているときに
    ワンダールーム状態が発生した場合や、解除された場合では、その度に補正が
    掛かっている能力も入れ替わる」を参照）。
    """
    if ctx.attacker is None or ctx.move is None or ctx.defender is None:
        return HandlerReturn(value=value)
    if ctx.move.name == "_こんらん":
        return HandlerReturn(value=value)

    stat = "def" if battle.query.deals_physical_damage(ctx.attacker, ctx.move) else "spd"
    if battle.get_global_field("ワンダールーム").is_active:
        stat = "spd" if stat == "def" else "def"
    if ctx.defender.paradox_boost_stat == stat:
        value = apply_fixed_modifier(value, 5325)
    return HandlerReturn(value=value)
