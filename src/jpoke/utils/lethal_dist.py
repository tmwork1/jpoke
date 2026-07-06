"""致死率計算で使うHP分布（StateDist）の演算ロジック。

Battle・Pokemon・Move に依存しない純粋な分布演算のみを提供する。
"""

from __future__ import annotations

from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    """HP分布の1要素。HP値と特性・道具の有効フラグを保持する。

    ability_enabled / item_enabled は「消耗型アイテム使用済み」など
    一度無効になったら戻らない状態を追跡するために使う。
    """
    value: int
    ability_enabled: bool = True
    item_enabled: bool = True


# requires-python (>=3.10) 互換のため `type` エイリアス文（3.12+）は使わない
StateDist = dict[State, int]


def to_dist(x: int | list[int] | StateDist,
            ability_enabled: bool = True,
            item_enabled: bool = True) -> StateDist:
    """整数・リスト・既存の StateDist を StateDist に正規化する。"""
    if isinstance(x, dict):
        return x
    elif isinstance(x, list):
        counter = Counter(x)
        return {
            State(value=k, ability_enabled=ability_enabled, item_enabled=item_enabled): v
            for k, v in counter.items()
        }
    else:
        key = State(value=x, ability_enabled=ability_enabled, item_enabled=item_enabled)
        return {key: 1}


def flip_dist(dist: StateDist) -> StateDist:
    """分布の hp 符号を反転する（subtract_dist の内部用）。"""
    return {
        State(value=-k.value, ability_enabled=k.ability_enabled, item_enabled=k.item_enabled): v
        for k, v in dist.items()
    }


def _clip_dist(dist: StateDist,
               minimum: int | None = None,
               maximum: int | None = None) -> StateDist:
    """HP値を [minimum, maximum] にクランプし、同一 LethalState を集約する。"""
    if minimum is None and maximum is None:
        return dist

    result = defaultdict(int)
    for value, freq in dist.items():
        hp = value.value
        if minimum is not None:
            hp = max(hp, minimum)
        if maximum is not None:
            hp = min(hp, maximum)
        key = State(value=hp, ability_enabled=value.ability_enabled, item_enabled=value.item_enabled)
        result[key] += freq
    return dict(result)


def _convolve(a: StateDist | list[int] | int,
              b: StateDist | list[int] | int) -> StateDist:
    """2つの分布の畳み込みを計算する（HP を加算、フラグは AND）。"""
    x = to_dist(a)
    y = to_dist(b)

    result = defaultdict(int)
    for vx, fx in x.items():
        for vy, fy in y.items():
            hp = vx.value + vy.value
            ability_enabled = vx.ability_enabled and vy.ability_enabled
            item_enabled = vx.item_enabled and vy.item_enabled
            key = State(value=hp, ability_enabled=ability_enabled, item_enabled=item_enabled)
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
