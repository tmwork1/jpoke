"""致死率計算で使うHP分布（LethalDist）の演算ロジック。

Battle・Pokemon・Move に依存しない純粋な分布演算のみを提供する。
"""

from __future__ import annotations

from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class LethalState:
    """HP分布の1要素。HP値と特性・道具の有効フラグを保持する。

    ability_enabled / item_enabled は「消耗型アイテム使用済み」など
    一度無効になったら戻らない状態を追跡するために使う。
    """
    hp: int
    ability_enabled: bool = True
    item_enabled: bool = True


type LethalDist = dict[LethalState, int]


def to_dist(x: int | list[int] | LethalDist,
            ability_enabled: bool = True,
            item_enabled: bool = True) -> LethalDist:
    """整数・リスト・既存の LethalDist を LethalDist に正規化する。"""
    if isinstance(x, dict):
        return x
    elif isinstance(x, list):
        counter = Counter(x)
        return {LethalState(hp=k, ability_enabled=ability_enabled, item_enabled=item_enabled): v
                for k, v in counter.items()}
    else:
        return {LethalState(hp=x, ability_enabled=ability_enabled, item_enabled=item_enabled): 1}


def flip_dist(dist: LethalDist) -> LethalDist:
    """分布の hp 符号を反転する（subtract_dist の内部用）。"""
    return {LethalState(hp=-k.hp, ability_enabled=k.ability_enabled, item_enabled=k.item_enabled): v
            for k, v in dist.items()}


def _clip_dist(dist: LethalDist,
               minimum: int | None = None,
               maximum: int | None = None) -> LethalDist:
    """HP値を [minimum, maximum] にクランプし、同一 LethalState を集約する。"""
    if minimum is None and maximum is None:
        return dist

    result = defaultdict(int)
    for value, freq in dist.items():
        hp = value.hp
        if minimum is not None:
            hp = max(hp, minimum)
        if maximum is not None:
            hp = min(hp, maximum)
        key = LethalState(hp=hp, ability_enabled=value.ability_enabled, item_enabled=value.item_enabled)
        result[key] += freq
    return dict(result)


def _check_hp(dist: LethalDist, value: int) -> bool:
    """分布内に指定 HP 値を持つ状態が存在するか確認する。"""
    return any(state.hp == value for state in dist)


def _convolve(a: LethalDist | list[int] | int,
              b: LethalDist | list[int] | int) -> LethalDist:
    """2つの分布の畳み込みを計算する（HP を加算、フラグは AND）。"""
    x = to_dist(a)
    y = to_dist(b)

    result = defaultdict(int)
    for vx, fx in x.items():
        for vy, fy in y.items():
            hp = vx.hp + vy.hp
            ability_enabled = vx.ability_enabled and vy.ability_enabled
            item_enabled = vx.item_enabled and vy.item_enabled
            key = LethalState(hp=hp, ability_enabled=ability_enabled, item_enabled=item_enabled)
            result[key] += fx * fy
    return dict(result)


def add_dist(a: LethalDist | list[int] | int,
             b: LethalDist | list[int] | int,
             minimum: int | None = None,
             maximum: int | None = None) -> LethalDist:
    """HP 分布 a に b を加算し、結果を [minimum, maximum] にクランプする。"""
    result = _convolve(a, b)
    return _clip_dist(result, minimum=minimum, maximum=maximum)


def subtract_dist(a: LethalDist | list[int] | int,
                  b: LethalDist | list[int] | int,
                  minimum: int | None = None,
                  maximum: int | None = None) -> LethalDist:
    """HP 分布 a から b を減算し、結果を [minimum, maximum] にクランプする。"""
    y = to_dist(b)
    result = _convolve(a, flip_dist(y))
    return _clip_dist(result, minimum=minimum, maximum=maximum)
