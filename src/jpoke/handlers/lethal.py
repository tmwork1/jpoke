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
from jpoke.utils.lethal_dist import State, add_dist


def _heal(hp_dist: StateDist,
          target: Pokemon,
          v: int = 0,
          r: float = 0.) -> StateDist:
    """全状態に無条件で回復を適用する（たべのこしなど）。

    r が指定された場合は target.max_hp * r（切り捨て、最低1）を回復量とする。
    v と r を両方指定した場合は r が優先される。
    """
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
    """
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
            item_enabled=state.item_enabled and keep_item_enabled
        )
        new_dist[new_state] += freq

    return new_dist


def たべのこし_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """たべのこし — ターン終了時に max_hp の 1/16 回復する。"""
    return _heal(hp_dist, ctx.defender, r=1/16)


def オボンのみ_heal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """オボンのみ — HP が 1/2 以下になると max_hp の 1/4 回復し、消費する。"""
    return _heal_at_pinch(hp_dist, ctx.defender, r=1/4, threshold_rate=1/2, heal_with="item", consume=True)
