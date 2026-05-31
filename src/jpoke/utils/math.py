"""バトル計算で使う共通数学関数。"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_DOWN


FIXED_POINT_BASE = 4096


def round_half_down(v: float) -> int:
    """五捨五超入で丸める。"""
    return int(Decimal(str(v)).quantize(Decimal("0"), rounding=ROUND_HALF_DOWN))


def apply_fixed_modifier(value: int, modifier: int) -> int:
    """4096基準の固定小数点補正を適用する。"""
    return value * modifier // FIXED_POINT_BASE


def clamp_stats(value: int) -> int:
    """能力ランクを-6～+6の範囲に収める。"""
    return max(-6, min(6, value))


def clamp_critic(value: int) -> int:
    """クリティカルランクを0～3の範囲に収める。"""
    return max(0, min(3, value))
