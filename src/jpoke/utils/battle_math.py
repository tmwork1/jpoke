"""バトル計算で使う共通数学関数。"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_DOWN


FIXED_POINT_BASE = 4096


def rank_modifier(v: float) -> float:
    """ランク値（-6〜+6）から補正倍率を返す。"""
    return (2 + v) / 2 if v >= 0 else 2 / (2 - v)


def round_half_down(v: float) -> int:
    """五捨五超入で丸める。"""
    return int(Decimal(str(v)).quantize(Decimal("0"), rounding=ROUND_HALF_DOWN))


def apply_fixed_modifier(value: int, modifier: int) -> int:
    """4096基準の固定小数点補正を適用する。"""
    return value * modifier // FIXED_POINT_BASE
