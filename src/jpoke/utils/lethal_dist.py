"""致死率計算で使うHP分布（StateDist）の演算ロジック。

Battle・Pokemon・Move に依存しない純粋な分布演算のみを提供する。
"""

from __future__ import annotations

from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    """HP分布の1要素。HP値と特性・道具の有効フラグ、攻撃側・防御側のランク補正/状態異常を保持する。

    ability_enabled / item_enabled は「消耗型アイテム使用済み」など
    一度無効になったら戻らない状態を追跡するために使う。

    attacker_boosts / attacker_ailment / defender_boosts / defender_ailment は
    「その枝が観測された時点」でのポケモンの状態を表す。値は `None` を「未同期」の
    センチネルとして扱う（`""` は「状態異常なし」という実際の値であり `None` とは区別する）。
    実際の同期は `core/lethal.py` の `_update_hp` が行い、`_convolve` は分布演算の過程で
    同期済みの側（`None` でない側）を優先して引き継ぐ。
    """
    value: int
    ability_enabled: bool = True
    item_enabled: bool = True
    attacker_boosts: tuple[tuple[str, int], ...] | None = None
    attacker_ailment: str | None = None
    defender_boosts: tuple[tuple[str, int], ...] | None = None
    defender_ailment: str | None = None


# requires-python (>=3.10) 互換のため `type` エイリアス文（3.12+）は使わない
StateDist = dict[State, int]


def to_dist(x: int | list[int] | StateDist,
            ability_enabled: bool = True,
            item_enabled: bool = True,
            attacker_boosts: tuple[tuple[str, int], ...] | None = None,
            attacker_ailment: str | None = None,
            defender_boosts: tuple[tuple[str, int], ...] | None = None,
            defender_ailment: str | None = None) -> StateDist:
    """整数・リスト・既存の StateDist を StateDist に正規化する。"""
    if isinstance(x, dict):
        return x
    elif isinstance(x, list):
        counter = Counter(x)
        return {
            State(value=k, ability_enabled=ability_enabled, item_enabled=item_enabled,
                  attacker_boosts=attacker_boosts, attacker_ailment=attacker_ailment,
                  defender_boosts=defender_boosts, defender_ailment=defender_ailment): v
            for k, v in counter.items()
        }
    else:
        key = State(value=x, ability_enabled=ability_enabled, item_enabled=item_enabled,
                    attacker_boosts=attacker_boosts, attacker_ailment=attacker_ailment,
                    defender_boosts=defender_boosts, defender_ailment=defender_ailment)
        return {key: 1}


def flip_dist(dist: StateDist) -> StateDist:
    """分布の hp 符号を反転する（subtract_dist の内部用）。フラグ・状態タグはそのまま引き継ぐ。"""
    return {
        State(value=-k.value, ability_enabled=k.ability_enabled, item_enabled=k.item_enabled,
              attacker_boosts=k.attacker_boosts, attacker_ailment=k.attacker_ailment,
              defender_boosts=k.defender_boosts, defender_ailment=k.defender_ailment): v
        for k, v in dist.items()
    }


def _clip_dist(dist: StateDist,
               minimum: int | None = None,
               maximum: int | None = None) -> StateDist:
    """HP値を [minimum, maximum] にクランプし、同一 LethalState を集約する。フラグ・状態タグはそのまま引き継ぐ。"""
    if minimum is None and maximum is None:
        return dist

    result = defaultdict(int)
    for value, freq in dist.items():
        hp = value.value
        if minimum is not None:
            hp = max(hp, minimum)
        if maximum is not None:
            hp = min(hp, maximum)
        key = State(value=hp, ability_enabled=value.ability_enabled, item_enabled=value.item_enabled,
                    attacker_boosts=value.attacker_boosts, attacker_ailment=value.attacker_ailment,
                    defender_boosts=value.defender_boosts, defender_ailment=value.defender_ailment)
        result[key] += freq
    return dict(result)


def _convolve(a: StateDist | list[int] | int,
              b: StateDist | list[int] | int) -> StateDist:
    """2つの分布の畳み込みを計算する（HP を加算、フラグは AND）。

    attacker_boosts 等の状態タグは b 側が同期済み（None でない）ならそちらを優先し、
    未同期なら a 側を引き継ぐ。ダメージ量のような「状態を持たない」オペランドは常に
    未同期（None）になるため、実質的に同期済みの側のタグがそのまま伝播する。
    """
    x = to_dist(a)
    y = to_dist(b)

    result = defaultdict(int)
    for vx, fx in x.items():
        for vy, fy in y.items():
            hp = vx.value + vy.value
            ability_enabled = vx.ability_enabled and vy.ability_enabled
            item_enabled = vx.item_enabled and vy.item_enabled
            key = State(
                value=hp,
                ability_enabled=ability_enabled,
                item_enabled=item_enabled,
                attacker_boosts=vy.attacker_boosts if vy.attacker_boosts is not None else vx.attacker_boosts,
                attacker_ailment=vy.attacker_ailment if vy.attacker_ailment is not None else vx.attacker_ailment,
                defender_boosts=vy.defender_boosts if vy.defender_boosts is not None else vx.defender_boosts,
                defender_ailment=vy.defender_ailment if vy.defender_ailment is not None else vx.defender_ailment,
            )
            result[key] += fx * fy
    return dict(result)


def add_dist(a: StateDist | list[int] | int,
             b: StateDist | list[int] | int,
             minimum: int | None = None,
             maximum: int | None = None) -> StateDist:
    """HP 分布 a に b を加算し、結果を [minimum, maximum] にクランプする。"""
    result = _convolve(a, b)
    return _clip_dist(result, minimum=minimum, maximum=maximum)


def subtract_dist(a: StateDist | list[int] | int,
                  b: StateDist | list[int] | int,
                  minimum: int | None = None,
                  maximum: int | None = None) -> StateDist:
    """HP 分布 a から b を減算し、結果を [minimum, maximum] にクランプする。"""
    y = to_dist(b)
    result = _convolve(a, flip_dist(y))
    return _clip_dist(result, minimum=minimum, maximum=maximum)
