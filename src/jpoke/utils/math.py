"""バトル計算で使う共通数学関数。"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_DOWN
from collections import defaultdict, Counter


def round_half_down(v: float) -> int:
    """五捨五超入で丸める。"""
    return int(Decimal(str(v)).quantize(Decimal("0"), rounding=ROUND_HALF_DOWN))


def apply_fixed_modifier(value: int, modifier: int) -> int:
    """4096基準の固定小数点補正を適用する。"""
    return value * modifier // 4096


def clamp_stats(value: int) -> int:
    """能力ランクを-6～+6の範囲に収める。"""
    return max(-6, min(6, value))


def clamp_critic(value: int) -> int:
    """クリティカルランクを0～3の範囲に収める。"""
    return max(0, min(3, value))


def to_dist(a: list[int] | int) -> dict[int, int]:
    if isinstance(a, dict):
        return a
    elif isinstance(a, list):
        return dict(Counter(a))
    else:
        return {a: 1}


def add_dist(a: dict[int, int] | list[int] | int,
             b: dict[int, int] | list[int] | int) -> dict[int, int]:
    x = to_dist(a)
    y = to_dist(b)

    result = defaultdict(int)
    for vx, fx in x.items():
        for vy, fy in y.items():
            result[vx + vy] += fx * fy
    return dict(result)


def subtract_dist(a: dict[int, int] | list[int] | int,
                  b: dict[int, int] | list[int] | int) -> dict[int, int]:
    b_dist = to_dist(b)
    rev_b = {-k: v for k, v in b_dist.items()}
    return add_dist(a, rev_b)


def clip_dist(a: dict[int, int],
              minimum: int | None = None,
              maximum: int | None = None) -> dict[int, int]:
    result = defaultdict(int)
    for value, freq in a.items():
        if minimum is not None:
            value = max(value, minimum)
        if maximum is not None:
            value = min(value, maximum)
        result[value] += freq
    return dict(result)
